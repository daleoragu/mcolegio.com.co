"""Vistas de actividades interactivas y cuestionarios (a su ritmo y en vivo)."""
import json

from django.contrib import messages
from django.http import Http404, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.template.loader import render_to_string
from django.urls import reverse
from django.views.decorators.http import require_POST

from . import juegos, logica
from .models import Actividad, Cuestionario, ResultadoActividad, SesionVivo
from .views import _Prohibido, _ctx, _guardar_archivo, _render, _url, vista_aula


def _periodos(aula):
    if not aula.colegio_id:
        return []
    from notas.models import PeriodoAcademico
    return list(PeriodoAcademico.objects.filter(colegio=aula.colegio).order_by('-ano_lectivo', 'orden')[:8])


def _leer_periodo_componente(request, obj, aula):
    periodos = _periodos(aula)
    per_id = request.POST.get('periodo') or ''
    obj.periodo = next((p for p in periodos if str(p.id) == per_id), None)
    comp = request.POST.get('componente') or ''
    obj.componente = comp if comp in {k for k, _ in logica.componentes_de(aula)} else ''


def _datos_planilla(aula):
    periodos = _periodos(aula)
    return {'periodos': periodos, 'componentes': logica.componentes_de(aula),
            'periodo_sugerido': next((p for p in periodos if p.esta_activo), periodos[0] if periodos else None)}


def _persona(c):
    return c.estudiante or c.integrante


def _clave_mejor(c):
    """La clave de juegos.mejores_notas para quien mira."""
    return (c.estudiante.id, None) if c.estudiante else (None, c.integrante.id if c.integrante else None)


# ---------------------------------------------------------------------------
# Actividades interactivas
# ---------------------------------------------------------------------------
@vista_aula
def actividades(request, pk):
    c = _ctx(request, pk)
    aula = c.aula
    if request.method == 'POST':
        if not c.es_docente:
            raise _Prohibido('Solo el docente agrega actividades.')
        archivo = request.FILES.get('archivo')
        a = Actividad(aula=aula, titulo=(request.POST.get('titulo') or '').strip()[:60],
                      descripcion=(request.POST.get('descripcion') or '').strip()[:300],
                      enlace=(request.POST.get('enlace') or '').strip()[:200],
                      califica=request.POST.get('califica') == 'on')
        _leer_periodo_componente(request, a, aula)
        a.para, error_para = logica.leer_para(request, aula)
        if not a.titulo or not (archivo or a.enlace):
            messages.warning(request, 'Escriba el título y suba el archivo HTML o pegue el enlace.')
        elif error_para:
            messages.warning(request, error_para)
        elif archivo and not archivo.name.lower().endswith(('.html', '.htm')):
            messages.error(request, 'La actividad debe ser un archivo .html (para otros archivos use «Material»).')
        elif logica.muy_grande(archivo):
            messages.error(request, f'El archivo pasa de {logica.MAX_ARCHIVO_MB} MB.')
        else:
            _guardar_archivo(a, 'archivo', archivo)
            a.save()
            logica.avisar_estudiantes(aula, f'{aula.titulo}: nueva actividad «{a.titulo}»',
                                      _url(request, 'aula:actividad', aula.pk, a.pk), a.para)
            messages.success(request, 'Actividad publicada.')
            return redirect('aula:actividad', pk=aula.pk, aid=a.pk)
        return redirect('aula:actividades', pk=aula.pk)
    lista = [a for a in (aula.actividades.all() if c.es_docente else aula.actividades.filter(publicada=True))
             if logica.para_c(a, c)]
    if not c.es_docente:
        mias = {r.actividad_id: r for r in ResultadoActividad.objects.filter(
            actividad__in=lista, **logica.filtro_persona(_persona(c)))}
        for a in lista:
            a.mio = mias.get(a.id)
    else:
        for a in lista:
            a.n_resultados = a.resultados.count()
    datos = {'actividades': lista, 'opciones_para': logica.opciones_para(aula) if c.es_docente else []}
    datos.update(_datos_planilla(aula))
    return _render(request, c, 'aula/actividades.html', datos, 'actividades')


@vista_aula
def actividad(request, pk, aid):
    c = _ctx(request, pk)
    a = get_object_or_404(Actividad, pk=aid, aula=c.aula)
    if (not a.publicada and not c.es_docente) or not logica.para_c(a, c):
        raise Http404
    datos = {'a': a, 'para_nombres': logica.nombres_para(a, c.aula) if c.es_docente else []}
    if c.es_docente:
        resultados = {(r.integrante_id if c.aula.es_salon else r.estudiante_id): r for r in a.resultados.all()}
        datos['filas'] = [{'nombre': logica.nombre_de(p), 'r': resultados.get(p.id)} for p in logica.personas_de(a, c.aula)]
        datos['puede_planilla'] = bool(c.aula.asignacion_id) and a.califica
        datos['componente_nombre'] = dict(logica.componentes_de(c.aula)).get(a.componente, '')
        datos.update(_datos_planilla(c.aula))
    else:
        datos['mio'] = ResultadoActividad.objects.filter(actividad=a, **logica.filtro_persona(_persona(c))).first()
    return _render(request, c, 'aula/actividad.html', datos, 'actividades')


@require_POST
@vista_aula
def actividad_resultado(request, pk, aid):
    """La actividad (desde el marco del aula) manda {puntaje, maximo} o {nota}."""
    c = _ctx(request, pk)
    a = get_object_or_404(Actividad, pk=aid, aula=c.aula, califica=True, publicada=True)
    if not logica.para_c(a, c):
        raise Http404
    if c.es_docente:
        return JsonResponse({'ok': False, 'mensaje': 'Vista previa del docente: no se guarda.'})
    try:
        datos = json.loads(request.body or '{}')
        if 'puntaje' in datos:
            valor = juegos.nota_de_puntaje(c.aula, datos['puntaje'], datos.get('maximo', 100))
        else:
            minima, maxima = logica.rango(c.aula)
            from decimal import Decimal
            valor = max(minima, min(maxima, Decimal(str(datos['nota'])))).quantize(Decimal('0.1'))
    except Exception:
        return JsonResponse({'ok': False, 'mensaje': 'La actividad mandó un resultado que no se entiende.'}, status=400)
    r = juegos.guardar_resultado_actividad(a, _persona(c), valor)
    return JsonResponse({'ok': True, 'nota': juegos._texto(valor), 'mejor': juegos._texto(r.nota)})


@require_POST
@vista_aula
def actividad_accion(request, pk, aid):
    c = _ctx(request, pk, docente=True)
    a = get_object_or_404(Actividad, pk=aid, aula=c.aula)
    accion = request.POST.get('accion')
    if accion == 'eliminar':
        a.delete()
        messages.info(request, 'Actividad eliminada.')
        return redirect('aula:actividades', pk=pk)
    if accion == 'planilla':
        if request.POST.get('periodo'):
            _leer_periodo_componente(request, a, c.aula)
            a.save()
        pares = [(r.estudiante, r.nota) for r in a.resultados.filter(estudiante__isnull=False).select_related('estudiante')]
        n, error = logica.pasar_notas_a_planilla(c.aula, a.periodo, a.componente, a.titulo, pares)
        if error:
            messages.error(request, error)
        else:
            from django.utils import timezone
            a.pasada_planilla = timezone.now()
            a.save(update_fields=['pasada_planilla'])
            messages.success(request, f'Se pasaron {n} nota(s) a la planilla, columna «{a.titulo}».')
    return redirect('aula:actividad', pk=pk, aid=aid)


def actividad_ejemplo(request):
    """Una actividad HTML de ejemplo que manda la nota al aula (para descargar y copiar)."""
    r = HttpResponse(render_to_string('aula/actividad_ejemplo.html'), content_type='text/html; charset=utf-8')
    r['Content-Disposition'] = 'attachment; filename="actividad-ejemplo-mcolegio.html"'
    return r


# ---------------------------------------------------------------------------
# Cuestionarios
# ---------------------------------------------------------------------------
@vista_aula
def cuestionarios(request, pk):
    c = _ctx(request, pk)
    aula = c.aula
    if request.method == 'POST':
        if not c.es_docente:
            raise _Prohibido('Solo el docente crea cuestionarios.')
        titulo = (request.POST.get('titulo') or '').strip()[:60]
        if not titulo:
            messages.warning(request, 'Escriba el título del cuestionario.')
            return redirect('aula:cuestionarios', pk=pk)
        q = Cuestionario.objects.create(aula=aula, titulo=titulo)
        texto = request.POST.get('aiken') or ''
        if texto.strip():
            preguntas = juegos.leer_aiken(texto)
            juegos.guardar_preguntas(q, preguntas)
            messages.success(request, f'Se crearon {len(preguntas)} pregunta(s). Revíselas antes de publicar.')
        return redirect('aula:cuestionario_editar', pk=pk, cid=q.pk)
    lista = list(aula.cuestionarios.all())
    for q in lista:
        q.n_preguntas = q.preguntas.count()
        q.vivo = juegos.sesion_activa(q)
        if not c.es_docente:
            q.mia = juegos.mejores_notas(q).get(_clave_mejor(c))
    if not c.es_docente:
        lista = [q for q in lista if q.n_preguntas and (q.a_su_ritmo or q.vivo or q.mia)]
    return _render(request, c, 'aula/cuestionarios.html', {'cuestionarios': lista}, 'cuestionarios')


@vista_aula
def cuestionario_editar(request, pk, cid):
    c = _ctx(request, pk, docente=True)
    aula = c.aula
    q = get_object_or_404(Cuestionario, pk=cid, aula=aula)
    usado = q.intentos.exists()
    if request.method == 'POST':
        q.titulo = (request.POST.get('titulo') or q.titulo).strip()[:60]
        q.descripcion = (request.POST.get('descripcion') or '').strip()[:300]
        try:
            q.segundos = max(5, min(240, int(request.POST.get('segundos') or 20)))
        except ValueError:
            q.segundos = 20
        q.mezclar = request.POST.get('mezclar') == 'on'
        q.reintentos = request.POST.get('reintentos') == 'on'
        q.a_su_ritmo = request.POST.get('a_su_ritmo') == 'on'
        _leer_periodo_componente(request, q, aula)
        q.save()
        if not usado:
            try:
                preguntas = json.loads(request.POST.get('preguntas_json') or '[]')
            except ValueError:
                preguntas = []
            limpias = []
            for p in preguntas:
                texto = str(p.get('texto', '')).strip()
                ops = [(str(o.get('texto', '')).strip(), bool(o.get('correcta'))) for o in p.get('opciones', [])
                       if str(o.get('texto', '')).strip()]
                if texto and len(ops) >= 2 and any(cc for _, cc in ops):
                    seg = p.get('segundos')
                    limpias.append((texto, ops, int(seg) if str(seg or '').isdigit() else None))
            descartadas = len(preguntas) - len(limpias)
            juegos.guardar_preguntas(q, limpias)
            msg = f'Guardado: {len(limpias)} pregunta(s).'
            if descartadas:
                msg += f' {descartadas} quedaron por fuera porque les faltaba texto, dos opciones o la correcta.'
            messages.success(request, msg)
        else:
            messages.success(request, 'Datos guardados. Las preguntas no cambian porque ya hay estudiantes que lo respondieron.')
        return redirect('aula:cuestionario', pk=pk, cid=q.pk)
    preguntas = [{'texto': p.texto, 'segundos': p.segundos or '',
                  'opciones': [{'texto': o.texto, 'correcta': o.correcta} for o in p.opciones.all()]}
                 for p in q.preguntas.prefetch_related('opciones')]
    datos = {'q': q, 'preguntas': preguntas, 'usado': usado}
    datos.update(_datos_planilla(aula))
    return _render(request, c, 'aula/cuestionario_form.html', datos, 'cuestionarios')


@vista_aula
def cuestionario(request, pk, cid):
    c = _ctx(request, pk)
    aula = c.aula
    q = get_object_or_404(Cuestionario, pk=cid, aula=aula)
    vivo = juegos.sesion_activa(q)
    mejores = juegos.mejores_notas(q)
    tabla = sorted(mejores.values(), key=lambda it: (-it.puntos, it.nombre))
    datos = {'q': q, 'vivo': vivo, 'tabla': tabla[:10] if not c.es_docente else tabla,
             'n_preguntas': q.preguntas.count()}
    if c.es_docente:
        datos['puede_planilla'] = bool(aula.asignacion_id)
        datos['componente_nombre'] = dict(logica.componentes_de(aula)).get(q.componente, '')
        datos['preguntas'] = list(q.preguntas.prefetch_related('opciones'))
    else:
        persona = _persona(c)
        datos['mia'] = mejores.get(_clave_mejor(c))
        datos['abierto'] = juegos.intento_abierto(q, persona)
        datos['puede'] = juegos.puede_iniciar(q, persona)
    return _render(request, c, 'aula/cuestionario.html', datos, 'cuestionarios')


@require_POST
@vista_aula
def cuestionario_accion(request, pk, cid):
    c = _ctx(request, pk, docente=True)
    q = get_object_or_404(Cuestionario, pk=cid, aula=c.aula)
    accion = request.POST.get('accion')
    if accion == 'eliminar':
        q.delete()
        messages.info(request, 'Cuestionario eliminado.')
        return redirect('aula:cuestionarios', pk=pk)
    if accion == 'duplicar':
        nuevo = Cuestionario.objects.create(aula=c.aula, titulo=f'{q.titulo[:52]} (copia)', segundos=q.segundos,
                                            mezclar=q.mezclar, reintentos=q.reintentos, a_su_ritmo=q.a_su_ritmo,
                                            periodo=q.periodo, componente=q.componente, descripcion=q.descripcion)
        juegos.guardar_preguntas(nuevo, [(p.texto, [(o.texto, o.correcta) for o in p.opciones.all()], p.segundos)
                                         for p in q.preguntas.prefetch_related('opciones')])
        return redirect('aula:cuestionario_editar', pk=pk, cid=nuevo.pk)
    if accion == 'vivo':
        if not q.preguntas.exists():
            messages.warning(request, 'El cuestionario no tiene preguntas.')
            return redirect('aula:cuestionario', pk=pk, cid=cid)
        s = juegos.nueva_sesion(q)
        logica.avisar_estudiantes(c.aula, f'{c.aula.titulo}: ¡juego en vivo «{q.titulo}»! Entre ya',
                                  _url(request, 'aula:vivo', pk, s.pk))
        return redirect('aula:vivo', pk=pk, sid=s.pk)
    if accion == 'planilla':
        mejores = juegos.mejores_notas(q)
        pares = [(it.estudiante, it.nota) for it in mejores.values() if it.estudiante_id]
        n, error = logica.pasar_notas_a_planilla(c.aula, q.periodo, q.componente, q.titulo, pares)
        if error:
            messages.error(request, error)
        else:
            from django.utils import timezone
            q.pasada_planilla = timezone.now()
            q.save(update_fields=['pasada_planilla'])
            messages.success(request, f'Se pasaron {n} nota(s) a la planilla, columna «{q.titulo}».')
    return redirect('aula:cuestionario', pk=pk, cid=cid)


# --- A su ritmo ------------------------------------------------------------
@vista_aula
def jugar(request, pk, cid):
    c = _ctx(request, pk)
    if c.es_docente or _persona(c) is None:
        raise _Prohibido('Los cuestionarios los responden los estudiantes. Use «Jugar en vivo» para proyectarlo.')
    q = get_object_or_404(Cuestionario, pk=cid, aula=c.aula)
    persona = _persona(c)
    intento = juegos.intento_abierto(q, persona)
    if request.method == 'POST':
        if intento is None and not juegos.puede_iniciar(q, persona):
            messages.info(request, 'Ya respondió este cuestionario.')
            return redirect('aula:cuestionario', pk=pk, cid=cid)
        juegos.iniciar(q, persona)
        return redirect('aula:jugar', pk=pk, cid=cid)
    if intento is None:
        return redirect('aula:cuestionario', pk=pk, cid=cid)
    return _render(request, c, 'aula/jugar.html', {'q': q, 'intento': intento}, 'cuestionarios')


@vista_aula
def jugar_estado(request, pk, cid):
    c = _ctx(request, pk)
    q = get_object_or_404(Cuestionario, pk=cid, aula=c.aula)
    persona = _persona(c)
    if persona is None:
        raise _Prohibido('Solo estudiantes.')
    intento = juegos.intento_abierto(q, persona)
    if request.method == 'POST':
        if intento is None:
            return JsonResponse({'error': 'No hay un intento abierto.'}, status=400)
        datos = json.loads(request.body or '{}')
        return JsonResponse(juegos.responder(intento, int(datos.get('pregunta', 0)),
                                             int(datos['opcion']) if datos.get('opcion') else None))
    if intento is None:
        ultimo = q.intentos.filter(sesion__isnull=True, **logica.filtro_persona(persona)).order_by('-iniciado').first()
        if ultimo is None:
            return JsonResponse({'error': 'No hay intento.'}, status=404)
        return JsonResponse(juegos.estado_intento(ultimo))
    return JsonResponse(juegos.estado_intento(intento))


# --- En vivo ---------------------------------------------------------------
@vista_aula
def vivo(request, pk, sid):
    c = _ctx(request, pk)
    s = get_object_or_404(SesionVivo.objects.select_related('cuestionario'), pk=sid, cuestionario__aula=c.aula)
    if c.es_docente:
        return _render(request, c, 'aula/vivo_docente.html', {'s': s, 'q': s.cuestionario,
                                                              'url_entrar': request.build_absolute_uri(
                                                                  reverse('aula:vivo', args=[pk, sid]))}, 'cuestionarios')
    if s.estado == 'fin' and not s.intentos.filter(**logica.filtro_persona(_persona(c))).exists():
        messages.info(request, 'Ese juego ya terminó.')
        return redirect('aula:cuestionarios', pk=pk)
    juegos.unirse(s, _persona(c))
    return _render(request, c, 'aula/vivo_estudiante.html', {'s': s, 'q': s.cuestionario}, 'cuestionarios')


@vista_aula
def vivo_estado(request, pk, sid):
    c = _ctx(request, pk)
    s = get_object_or_404(SesionVivo, pk=sid, cuestionario__aula=c.aula)
    if c.es_docente:
        if request.method == 'POST':
            juegos.avanzar(s)
        return JsonResponse(juegos.estado_sesion(s, docente=True))
    intento = juegos.unirse(s, _persona(c))
    if request.method == 'POST':
        datos = json.loads(request.body or '{}')
        r = juegos.responder_vivo(s, intento, int(datos['opcion']) if datos.get('opcion') else None)
        if r.get('error'):
            return JsonResponse(r, status=409)
    return JsonResponse(juegos.estado_sesion(s, intento=intento))
