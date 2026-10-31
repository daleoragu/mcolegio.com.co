"""Asistente con IA, medidor de créditos, saldo prepago y recargas con Wompi."""
import json
import secrets
from datetime import timedelta

from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.models import User
from django.db.models import Count, Q, Sum
from django.http import Http404, HttpResponse, HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from . import bloques as B
from . import creditos as K
from . import ia, wompi
from .models import Documento, Imagen, MovimientoIA, Recarga
from .views import _doc, vista


def _medidor(est):
    return {k: (v.isoformat() if hasattr(v, 'isoformat') else v) for k, v in est.items()}


def _json(request):
    try:
        datos = json.loads(request.body or '{}')
    except ValueError:
        return {}
    return datos if isinstance(datos, dict) else {}


def _entero(v, defecto=0):
    try:
        return int(v)
    except (TypeError, ValueError):
        return defecto


def _sin_creditos(e):
    pesos = e.costo * K.PESOS_POR_CREDITO
    est = e.estado
    return JsonResponse({'ok': False, 'sin_creditos': True, 'costo': e.costo, 'pesos': pesos,
                         'puede_saldo': est['saldo'] >= pesos, 'medidor': _medidor(est),
                         'error': (f'No le alcanzan los créditos: esta acción usa {e.costo}. '
                                   + (f'Puede pagarla con su saldo (${pesos:,})'.replace(',', '.')
                                      if est['saldo'] >= pesos else 'Recargue saldo o espere la recarga de mañana.'))},
                        status=402)


def _ejecutar(request, a, accion, datos, contexto, detalle=''):
    """Cobra, llama a la IA y devuelve (resultado, None) o (None, JsonResponse de error)."""
    if not ia.disponible():
        return None, JsonResponse({'ok': False, 'error': 'La IA todavía no está configurada en la plataforma.'}, status=503)
    costo = ia.creditos_de(accion, datos)
    try:
        mov = K.cobrar(request.user, a.colegio, accion, costo, usar_saldo=bool(datos.get('usar_saldo')), detalle=detalle)
    except K.SinCreditos as e:
        return None, _sin_creditos(e)
    try:
        resultado, t_in, t_out = ia.ejecutar(accion, datos, contexto)
    except ia.IAError as e:
        K.devolver(mov, 'falló la IA')
        return None, JsonResponse({'ok': False, 'error': str(e), 'medidor': _medidor(K.estado(request.user, a.colegio))},
                                  status=422)
    K.anotar_consumo(mov, t_in, t_out)
    return resultado, None


# ---------------------------------------------------------------------------
# Acciones del editor
# ---------------------------------------------------------------------------
@require_POST
@vista
def accion(request, a, accion):
    if accion not in ia.ACCIONES or accion == 'retro':
        raise Http404
    datos = _json(request)
    validas = set(Imagen.objects.filter(propietario=request.user).values_list('pk', flat=True))
    contexto = {'imagenes': validas}
    doc = None
    if accion in ('piar', 'revisar'):
        doc = _doc(a, _entero(datos.get('documento')))
        contexto['documento'] = B.limpiar(doc.contenido, validas)
        if not contexto['documento']['bloques']:
            return JsonResponse({'ok': False, 'error': 'El documento está vacío.'}, status=400)
    if accion == 'rubrica':
        from aula import logica
        contexto['niveles'] = logica.niveles_sugeridos(a.colegio, request.user)
    nombre = ia.ACCIONES[accion]['nombre']
    resultado, error = _ejecutar(request, a, accion, datos, contexto,
                                 detalle=f'{nombre}: {B.texto_plano(datos.get("tema") or (doc and doc.titulo) or datos.get("tarea"), 120)}')
    if error:
        return error
    salida = {'ok': True, 'medidor': _medidor(K.estado(request.user, a.colegio))}
    if accion == 'piar':
        nuevo = Documento.objects.create(
            propietario=request.user, colegio=a.colegio, titulo=f'{doc.titulo[:130]} (adaptado)', tipo=doc.tipo,
            area=doc.area, grado=doc.grado, periodo=doc.periodo,
            contenido={'bloques': resultado['bloques'], 'opciones': contexto['documento']['opciones']})
        salida['redirect'] = f'/materiales/{nuevo.pk}/'
        salida['mensaje'] = 'Versión adaptada creada como un documento nuevo; la original no cambió.'
    elif accion == 'rubrica':
        from aula import logica
        criterios = resultado['criterios']
        inst = logica.crear_instrumento(request.user, a.colegio, resultado['nombre'], 'rubrica',
                                        [(n, 1) for n, _ in criterios], contexto['niveles'],
                                        [desc for _, desc in criterios])
        salida['redirect'] = f'/aula/instrumentos/{inst.pk}/'
        salida['mensaje'] = 'Rúbrica creada en sus instrumentos de evaluación.'
    else:
        salida.update(resultado)
    return JsonResponse(salida)


@require_POST
@vista
def retro(request, a):
    """Retroalimentación sugerida para una respuesta abierta de una ficha (el docente decide si la usa)."""
    from aula import logica
    from aula.models import Tarea
    from aula.views import _persona
    datos = _json(request)
    aulas = {x.pk: x for x in a.aulas()}
    t = Tarea.objects.filter(pk=_entero(datos.get('tarea')), aula_id__in=list(aulas)).first()
    if t is None or not t.ficha:
        raise Http404
    bloque = next((b for b in t.ficha.get('bloques', []) if b.get('tipo') == 'pregunta'
                   and b.get('id') == datos.get('bloque') and b.get('modo') in ('abierta', 'corta')), None)
    if bloque is None:
        raise Http404
    persona = _persona(aulas[t.aula_id], str(datos.get('clave') or ''))
    e = logica.entrega_de(t, persona)
    respuesta = str((e.respuestas or {}).get(bloque['id']) or '') if e else ''
    if not respuesta.strip():
        return JsonResponse({'ok': False, 'error': 'Esa pregunta está en blanco.'}, status=400)
    contexto = {'enunciado': bloque.get('enunciado'), 'solucion': bloque.get('solucion') or ', '.join(bloque.get('aceptadas') or []),
                'posibles': bloque.get('puntos') or 1, 'respuesta': respuesta}
    resultado, error = _ejecutar(request, a, 'retro', datos, contexto, detalle=f'Retroalimentación: {t.titulo}')
    if error:
        return error
    return JsonResponse(dict(resultado, ok=True, medidor=_medidor(K.estado(request.user, a.colegio))))


@vista
def medidor(request, a):
    return JsonResponse({'ok': True, 'medidor': _medidor(K.estado(request.user, a.colegio)), 'ia': ia.disponible()})


# ---------------------------------------------------------------------------
# Mis créditos
# ---------------------------------------------------------------------------
@vista
def mis_creditos(request, a):
    est = K.estado(request.user, a.colegio)
    return render(request, 'materiales/creditos.html', {
        'base': a.base, 'acceso': a, 'est': est, 'resumen': K.resumen(est), 'ia_lista': ia.disponible(),
        'movimientos': MovimientoIA.objects.filter(usuario=request.user)[:60],
        'recargas': Recarga.objects.filter(usuario=request.user)[:10],
        'acciones': [(v['nombre'], v['creditos']) for k, v in ia.ACCIONES.items()],
        'paquete': K.PAQUETE, 'plan_ia': K.PLAN_IA, 'nube': sorted(K.NUBE.items()),
        'recargas_opciones': sorted(K.RECARGAS.items()), 'wompi': wompi.configurado(),
        'pesos_credito': K.PESOS_POR_CREDITO, 'cupos': K.CUPOS})


@require_POST
@vista
def creditos_accion(request, a):
    que = request.POST.get('accion')
    if que == 'paquete':
        ok = K.gastar_saldo(request.user, K.PAQUETE['pesos'], 'paquete',
                            f'Paquete de {K.PAQUETE["creditos"]} créditos hasta fin de mes', a.colegio, K.PAQUETE['creditos'])
        messages.success(request, f'Listo: {K.PAQUETE["creditos"]} créditos más hasta fin de mes.') if ok else \
            messages.error(request, 'No le alcanza el saldo. Recargue primero.')
    elif que == 'plan_ia' and a.es_individual:
        ok = K.gastar_saldo(request.user, K.PLAN_IA['pesos'], 'plan_ia', f'Plan con IA por {K.PLAN_IA["dias"]} días')
        messages.success(request, 'Plan con IA activo: 200 créditos al mes, 8 diarios y 5 GB de nube.') if ok else \
            messages.error(request, 'No le alcanza el saldo. Recargue primero.')
    elif que == 'nube':
        gb = _entero(request.POST.get('gb'))
        ok = K.ampliar_nube(request.user, gb)
        messages.success(request, f'Nube ampliada en {gb} GB por 30 días.') if ok else \
            messages.error(request, 'No le alcanza el saldo para esa ampliación.')
    elif que == 'ajustes':
        c = K.cuenta(request.user)
        c.saldo_sin_preguntar = request.POST.get('sin_preguntar') == 'on'
        c.tope_mes = max(0, min(200000, _entero(request.POST.get('tope_mes'), 3000)))
        c.save(update_fields=['saldo_sin_preguntar', 'tope_mes'])
        messages.success(request, 'Preferencias del saldo guardadas.')
    return redirect('materiales:creditos')


@require_POST
@vista
def recargar(request, a):
    monto = _entero(request.POST.get('monto'))
    if monto not in K.RECARGAS:
        messages.error(request, 'Escoja una de las recargas.')
        return redirect('materiales:creditos')
    if not wompi.configurado():
        messages.info(request, 'El pago en línea todavía no está activo. Escriba a la línea de mcolegio para recargar '
                               'por transferencia o Nequi.')
        return redirect('materiales:creditos')
    r = Recarga.objects.create(usuario=request.user, monto=monto, bono=K.RECARGAS[monto],
                               referencia=f'MC{request.user.pk}-{secrets.token_hex(6).upper()}')
    regreso = request.build_absolute_uri(f'/materiales/creditos/recarga/{r.referencia}/')
    return redirect(wompi.url_checkout(r, regreso, request.user.email or ''))


@vista
def recarga_vuelta(request, a, referencia):
    r = get_object_or_404(Recarga, referencia=referencia, usuario=request.user)
    tid = (request.GET.get('id') or '').strip()[:60]
    if r.estado == 'pendiente' and tid:
        datos = wompi.consultar(tid)
        if datos and datos.get('reference') == r.referencia:
            r = wompi.aplicar(r.referencia, datos.get('status'), tid, datos.get('amount_in_cents'),
                              datos.get('payment_method_type') or '')
    if r.estado == 'aprobada':
        messages.success(request, f'Recarga aprobada: ${r.monto + r.bono:,} en su saldo.'.replace(',', '.'))
    elif r.estado == 'rechazada':
        messages.error(request, 'El pago no se aprobó. No se cobró nada; puede intentarlo otra vez.')
    else:
        messages.info(request, 'El pago está en proceso. Apenas Wompi lo confirme, el saldo aparece solo.')
    return redirect('materiales:creditos')


@csrf_exempt
@require_POST
def wompi_eventos(request):
    """Aviso de Wompi cuando cambia una transacción. Siempre responde 200 si la firma es válida."""
    try:
        cuerpo = json.loads(request.body or '{}')
    except ValueError:
        return HttpResponse(status=400)
    if not wompi.evento_valido(cuerpo, request.headers.get('X-Event-Checksum', '')):
        return HttpResponse(status=401)
    if cuerpo.get('event') == 'transaction.updated':
        tr = (cuerpo.get('data') or {}).get('transaction') or {}
        wompi.aplicar(str(tr.get('reference') or ''), tr.get('status'), tr.get('id') or '', tr.get('amount_in_cents'),
                      tr.get('payment_method_type') or '')
    return HttpResponse('ok')


# ---------------------------------------------------------------------------
# Consumo: rector y dueño de la plataforma
# ---------------------------------------------------------------------------
def _inicio_mes():
    return timezone.localtime().replace(day=1, hour=0, minute=0, second=0, microsecond=0)


@vista
def consumo_colegio(request, a):
    if a.colegio is None or not a.admin:
        return HttpResponseForbidden('Solo el rector o el coordinador ven el consumo del colegio.')
    filas = (MovimientoIA.objects.filter(colegio=a.colegio, tipo='uso', devuelto=False, creado__gte=_inicio_mes())
             .values('usuario__first_name', 'usuario__last_name', 'usuario__username')
             .annotate(usos=Count('id'), creditos=Sum('creditos')).order_by('-creditos'))
    return render(request, 'materiales/consumo_colegio.html', {'base': a.base, 'acceso': a, 'filas': filas,
                                                               'mes': timezone.localdate()})


@user_passes_test(lambda u: u.is_authenticated and u.is_superuser, login_url='/super-admin/login/')
def consumo_plataforma(request):
    if request.method == 'POST':
        quien = (request.POST.get('usuario') or '').strip()
        u = User.objects.filter(Q(username__iexact=quien) | Q(email__iexact=quien)).first() if quien else None
        if u is None:
            messages.error(request, 'No encontré ese usuario (escriba el usuario o el correo exactos).')
        elif request.POST.get('accion') == 'saldo':
            pesos = _entero(request.POST.get('pesos'))
            K.abonar(u, pesos, 'ajuste', (request.POST.get('detalle') or 'Ajuste manual')[:200])
            messages.success(request, f'Saldo de {u.username} ajustado en ${pesos:,}.'.replace(',', '.'))
        elif request.POST.get('accion') == 'plan_ia':
            dias = max(1, min(400, _entero(request.POST.get('dias'), 30)))
            c = K.cuenta(u)
            hoy = timezone.localdate()
            c.ia_hasta = max(c.ia_hasta or hoy, hoy) + timedelta(days=dias)
            c.save(update_fields=['ia_hasta'])
            messages.success(request, f'Plan con IA de {u.username} activo hasta {c.ia_hasta:%d/%m/%Y}.')
        return redirect('materiales:consumo_plataforma')
    mes = _inicio_mes()
    usos = MovimientoIA.objects.filter(tipo='uso', devuelto=False, creado__gte=mes)
    por_colegio = usos.values('colegio__nombre').annotate(usos=Count('id'), creditos=Sum('creditos'),
                                                         costo=Sum('costo_usd')).order_by('-costo')
    por_docente = usos.values('usuario__username', 'usuario__first_name', 'usuario__last_name', 'colegio__nombre') \
        .annotate(usos=Count('id'), creditos=Sum('creditos'), costo=Sum('costo_usd')).order_by('-costo')[:50]
    totales = usos.aggregate(usos=Count('id'), creditos=Sum('creditos'), costo=Sum('costo_usd'),
                             entrada=Sum('tokens_entrada'), salida=Sum('tokens_salida'))
    recargas = Recarga.objects.filter(estado='aprobada', resuelta__gte=mes).aggregate(n=Count('id'), pesos=Sum('monto'))
    return render(request, 'materiales/consumo_plataforma.html', {
        'por_colegio': por_colegio, 'por_docente': por_docente, 'totales': totales, 'recargas': recargas,
        'ultimas': Recarga.objects.select_related('usuario')[:20], 'ia_lista': ia.disponible(),
        'wompi': wompi.configurado(), 'modelo': ia.MODELO})
