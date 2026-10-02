# pruebas/views.py
import json
import posixpath
from pathlib import PurePosixPath

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.files.base import ContentFile
from django.db.models import Q
from django.http import Http404, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from notas.models import Colegio, Estudiante

from .forms import ClaveForm, PaginaForm, SubidaMultipleForm
from .models import Detalle, PaginaPublicada, Prueba, Sesion
from .utils import (
    ZipInvalido, analizar, borrar_sitio, extraer_sitio, generar_qr,
    ip_cliente, reescribir_endpoint,
)

SESION_PANEL = 'pruebas_panel_autorizado'


# ---------------------------------------------------------------------------
# Ayudas
# ---------------------------------------------------------------------------

def colegio_actual(request):
    """El colegio del subdominio; si no hay, el del usuario autenticado."""
    colegio = getattr(request, 'colegio', None)
    if colegio:
        return colegio
    if request.user.is_authenticated:
        docente = getattr(request.user, 'docente', None)
        if docente:
            return docente.colegio
        propio = Colegio.objects.filter(admin_general=request.user).first()
        if propio:
            return propio
    return Colegio.objects.first()


def puede_administrar(user, colegio):
    if not user.is_authenticated:
        return False
    if user.is_superuser or user.groups.filter(name='Administrador de colegio').exists():
        return True
    docente = getattr(user, 'docente', None)
    return bool(docente and colegio and docente.colegio_id == colegio.id)


def autorizado_en_panel(request, objeto):
    """True si el visitante ya escribió la clave de esta página o prueba."""
    llaves = request.session.get(SESION_PANEL, [])
    etiqueta = f'{objeto.__class__.__name__}:{objeto.pk}'
    return etiqueta in llaves or puede_administrar(request.user, objeto.colegio)


def autorizar_en_panel(request, objeto):
    llaves = request.session.get(SESION_PANEL, [])
    etiqueta = f'{objeto.__class__.__name__}:{objeto.pk}'
    if etiqueta not in llaves:
        llaves.append(etiqueta)
        request.session[SESION_PANEL] = llaves
        request.session.modified = True


def url_api(request, pagina):
    return request.build_absolute_uri(
        reverse('pruebas:api_resultados', kwargs={'slug': pagina.slug})
    )


def publicar_archivo(request, pagina, archivo):
    """Deja el archivo subido listo para servirse.

    Un .html se guarda tal cual, reescribiéndole el ENDPOINT. Un .zip se
    descomprime en el bucket y se publica como sitio completo.
    """
    endpoint = url_api(request, pagina)

    def transformar(contenido):
        if not pagina.captura_resultados:
            texto = contenido.decode('utf-8', errors='replace') if isinstance(contenido, bytes) else contenido
            return texto, False
        return reescribir_endpoint(contenido, endpoint, pagina.clave_panel)

    if (archivo.name or '').lower().endswith('.zip'):
        base_anterior = pagina.base_sitio
        base = posixpath.join(
            'paginas', 'sitios', pagina.colegio.slug or str(pagina.colegio_id),
            pagina.slug, timezone.now().strftime('%Y%m%d%H%M%S'),
        )
        cantidad, indice, reescritos = extraer_sitio(archivo, base, transformar)

        pagina.tipo = 'sitio'
        pagina.base_sitio = base
        pagina.archivos_sitio = cantidad
        pagina.indice = pagina.indice if pagina.indice in ('', None) else pagina.indice
        if not pagina.indice or pagina.indice == 'index.html':
            pagina.indice = indice
        pagina.endpoint_reescrito = reescritos > 0
        pagina.archivo = ''
        pagina.save()

        if base_anterior and base_anterior != base:
            borrar_sitio(base_anterior)
        return cantidad

    # --- un solo .html ---
    if pagina.base_sitio:
        borrar_sitio(pagina.base_sitio)
        pagina.base_sitio = ''
        pagina.archivos_sitio = 0

    pagina.tipo = 'html'
    pagina.archivo = archivo
    pagina.save()

    pagina.archivo.open('rb')
    original = pagina.archivo.read()
    pagina.archivo.close()

    texto, cambio = transformar(original)
    pagina.endpoint_reescrito = bool(cambio)
    if cambio:
        nombre = PurePosixPath(pagina.archivo.name).name
        pagina.archivo.save(nombre, ContentFile(texto.encode('utf-8')), save=False)
    pagina.save()
    return 1


# ---------------------------------------------------------------------------
# Páginas publicadas — vista pública
# ---------------------------------------------------------------------------

def ver_pagina(request, slug):
    """Muestra la página subida dentro de un marco aislado."""
    colegio = colegio_actual(request)
    pagina = get_object_or_404(PaginaPublicada, colegio=colegio, slug=slug)

    es_admin = puede_administrar(request.user, colegio)
    if not pagina.disponible and not es_admin:
        if pagina.estado == 'oculta':
            raise Http404('Esta página no está publicada.')
        return render(request, 'pruebas/cerrada.html',
                      {'pagina': pagina, 'colegio': colegio}, status=403)

    PaginaPublicada.objects.filter(pk=pagina.pk).update(visitas=pagina.visitas + 1)
    return render(request, 'pruebas/ver_pagina.html',
                  {'pagina': pagina, 'colegio': colegio, 'es_admin': es_admin})


def indice_paginas(request):
    """Lista pública de las páginas marcadas para aparecer en el portal."""
    colegio = colegio_actual(request)
    paginas = [p for p in PaginaPublicada.objects.filter(
        colegio=colegio, visible=True, listar_en_portal=True) if p.disponible]
    return render(request, 'pruebas/indice.html', {'paginas': paginas, 'colegio': colegio})


# ---------------------------------------------------------------------------
# Endpoint de resultados (compatible con los HTML ya generados)
# ---------------------------------------------------------------------------

@csrf_exempt
def api_resultados(request, slug):
    """Recibe y entrega resultados.

    POST  -> guarda una sesión (el mismo JSON que enviaba el HTML a Google).
    GET   -> con ?clave=XXXX devuelve la lista de sesiones en JSON.
    """
    colegio = colegio_actual(request)
    pagina = PaginaPublicada.objects.filter(colegio=colegio, slug=slug).first()
    prueba = None if pagina else Prueba.objects.filter(colegio=colegio, slug=slug).first()
    origen = pagina or prueba
    if not origen:
        raise Http404('No existe esa prueba.')

    if request.method == 'GET':
        clave = (request.GET.get('clave') or '').strip()
        if clave.upper() != origen.clave_panel.upper():
            return JsonResponse({'error': 'clave incorrecta'}, status=403)
        datos = [
            {
                'ape': s.apellidos, 'nom': s.nombres, 'completo': s.completo,
                'sede': s.sede, 'gru': s.grupo, 'prueba': s.clave_prueba,
                'pruebaNombre': s.prueba_nombre, 'fecha': s.fecha.isoformat(),
                'ok': s.aciertos, 'total': s.total, 'pct': s.porcentaje,
                'seg': s.segundos, 'cambios': s.cambios, 'vez': s.vez,
                'det': [
                    {
                        'n': d.numero, 'apr': d.aprendizaje, 'comp': d.competencia,
                        'ac': d.acierto, 'marcada': d.marcada, 'clave': d.clave,
                        'expl': d.explicacion, 'intentos': d.intentos, 'seg': d.segundos,
                    }
                    for d in s.detalles.all()
                ],
            }
            for s in origen.sesiones.prefetch_related('detalles')
        ]
        respuesta = JsonResponse(datos, safe=False)
        respuesta['Access-Control-Allow-Origin'] = '*'
        return respuesta

    if request.method != 'POST':
        return JsonResponse({'error': 'método no permitido'}, status=405)

    try:
        datos = json.loads(request.body.decode('utf-8'))
    except (ValueError, UnicodeDecodeError):
        return JsonResponse({'error': 'json inválido'}, status=400)

    sesion = registrar_sesion(colegio, origen, datos, ip_cliente(request))
    respuesta = JsonResponse({'estado': 'ok', 'id': sesion.pk})
    respuesta['Access-Control-Allow-Origin'] = '*'
    return respuesta


def registrar_sesion(colegio, origen, datos, ip=None):
    """Convierte el JSON del HTML en una Sesion con sus Detalles."""
    fecha = parse_datetime(datos.get('fecha') or '') or timezone.now()
    if timezone.is_naive(fecha):
        fecha = timezone.make_aware(fecha, timezone.get_current_timezone())

    completo = (datos.get('completo') or
                f"{datos.get('ape', '')} {datos.get('nom', '')}").strip()

    sesion = Sesion.objects.create(
        colegio=colegio,
        pagina=origen if isinstance(origen, PaginaPublicada) else None,
        prueba=origen if isinstance(origen, Prueba) else None,
        clave_prueba=str(datos.get('prueba') or '')[:30],
        prueba_nombre=str(datos.get('pruebaNombre') or getattr(origen, 'titulo', ''))[:200],
        apellidos=str(datos.get('ape') or '')[:120],
        nombres=str(datos.get('nom') or '')[:120],
        completo=completo[:240],
        sede=str(datos.get('sede') or '')[:120],
        grupo=str(datos.get('gru') or '')[:30],
        fecha=fecha,
        aciertos=int(datos.get('ok') or 0),
        total=int(datos.get('total') or 0),
        porcentaje=float(datos.get('pct') or 0),
        segundos=int(datos.get('seg') or 0),
        cambios=int(datos.get('cambios') or 0),
        vez=int(datos.get('vez') or 1),
        payload=datos,
        ip=ip,
    )

    detalles = []
    for i, d in enumerate(datos.get('det') or [], start=1):
        detalles.append(Detalle(
            sesion=sesion,
            orden=i,
            numero=str(d.get('n') or '')[:30],
            aprendizaje=str(d.get('apr') or ''),
            competencia=str(d.get('comp') or '')[:10],
            acierto=bool(d.get('ac')),
            marcada=str(d.get('marcada') or '')[:2],
            clave=str(d.get('clave') or '')[:2],
            explicacion=str(d.get('expl') or ''),
            intentos=int(d.get('intentos') or 0),
            segundos=int(d.get('seg') or 0),
        ))
    Detalle.objects.bulk_create(detalles)

    vincular_automatico(sesion)
    return sesion


def vincular_automatico(sesion):
    """Intenta amarrar la sesión con un estudiante matriculado, por nombre."""
    if sesion.estudiante_id or not sesion.completo:
        return
    partes = [p for p in sesion.completo.split() if len(p) > 2]
    if not partes:
        return

    consulta = Q()
    for parte in partes:
        consulta &= (Q(user__first_name__icontains=parte) | Q(user__last_name__icontains=parte))

    candidatos = Estudiante.objects.filter(colegio=sesion.colegio, is_active=True).filter(consulta)[:2]
    if len(candidatos) == 1:
        sesion.estudiante = candidatos[0]
        sesion.curso = candidatos[0].curso
        sesion.save(update_fields=['estudiante', 'curso'])


# ---------------------------------------------------------------------------
# Panel de resultados
# ---------------------------------------------------------------------------

def _buscar_origen(colegio, slug):
    origen = PaginaPublicada.objects.filter(colegio=colegio, slug=slug).first()
    if not origen:
        origen = Prueba.objects.filter(colegio=colegio, slug=slug).first()
    if not origen:
        raise Http404('No existe esa prueba.')
    return origen


def panel_clave(request, slug):
    """Pide la clave para ver los resultados, sin necesidad de iniciar sesión."""
    colegio = colegio_actual(request)
    origen = _buscar_origen(colegio, slug)

    if autorizado_en_panel(request, origen):
        return redirect('pruebas:panel_resultados', slug=slug)

    form = ClaveForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        if form.cleaned_data['clave'].strip().upper() == origen.clave_panel.upper():
            autorizar_en_panel(request, origen)
            return redirect('pruebas:panel_resultados', slug=slug)
        form.add_error('clave', 'La clave no es correcta.')

    return render(request, 'pruebas/panel_clave.html',
                  {'form': form, 'origen': origen, 'colegio': colegio})


def panel_resultados(request, slug):
    colegio = colegio_actual(request)
    origen = _buscar_origen(colegio, slug)
    if not autorizado_en_panel(request, origen):
        return redirect('pruebas:panel_clave', slug=slug)

    sesiones = origen.sesiones.select_related('estudiante', 'curso').prefetch_related('detalles')

    grupo = (request.GET.get('grupo') or '').strip()
    if grupo:
        sesiones = sesiones.filter(grupo__iexact=grupo)

    resumen = analizar(sesiones)
    grupos = sorted({s.grupo for s in origen.sesiones.all() if s.grupo})

    return render(request, 'pruebas/panel_resultados.html', {
        'origen': origen,
        'colegio': colegio,
        'sesiones': sesiones,
        'resumen': resumen,
        'grupos': grupos,
        'grupo_activo': grupo,
        'es_admin': puede_administrar(request.user, colegio),
    })


def exportar_resultados(request, slug):
    from .exports import construir_libro
    colegio = colegio_actual(request)
    origen = _buscar_origen(colegio, slug)
    if not autorizado_en_panel(request, origen):
        return redirect('pruebas:panel_clave', slug=slug)

    sesiones = list(origen.sesiones.prefetch_related('detalles').select_related('estudiante', 'curso'))
    contenido = construir_libro(origen, sesiones, analizar(sesiones))

    nombre = f'resultados-{origen.slug}-{timezone.now():%Y%m%d}.xlsx'
    respuesta = HttpResponse(
        contenido,
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    )
    respuesta['Content-Disposition'] = f'attachment; filename="{nombre}"'
    return respuesta


@require_POST
def vincular_sesion(request, sesion_id):
    """Asocia manualmente un resultado con un estudiante matriculado."""
    colegio = colegio_actual(request)
    sesion = get_object_or_404(Sesion, pk=sesion_id, colegio=colegio)
    if not autorizado_en_panel(request, sesion.origen):
        raise PermissionDenied

    estudiante_id = request.POST.get('estudiante')
    if estudiante_id:
        estudiante = get_object_or_404(Estudiante, pk=estudiante_id, colegio=colegio)
        sesion.estudiante = estudiante
        sesion.curso = estudiante.curso
    else:
        sesion.estudiante = None
        sesion.curso = None
    sesion.save(update_fields=['estudiante', 'curso'])
    messages.success(request, 'Resultado actualizado.')
    return redirect(request.META.get('HTTP_REFERER') or
                    reverse('pruebas:panel_resultados', kwargs={'slug': sesion.origen.slug}))


# ---------------------------------------------------------------------------
# Administración de páginas
# ---------------------------------------------------------------------------

@login_required
def lista_paginas(request):
    colegio = colegio_actual(request)
    if not puede_administrar(request.user, colegio):
        raise PermissionDenied

    return render(request, 'pruebas/lista_paginas.html', {
        'paginas': PaginaPublicada.objects.filter(colegio=colegio),
        'pruebas': Prueba.objects.filter(colegio=colegio),
        'colegio': colegio,
    })


@login_required
def nueva_pagina(request):
    colegio = colegio_actual(request)
    if not puede_administrar(request.user, colegio):
        raise PermissionDenied

    form = PaginaForm(request.POST or None, request.FILES or None, colegio=colegio)
    if request.method == 'POST' and form.is_valid():
        pagina = form.save(commit=False)
        pagina.colegio = colegio
        pagina.creada_por = request.user
        pagina.save()
        try:
            publicar_archivo(request, pagina, form.cleaned_data['archivo'])
        except ZipInvalido as e:
            pagina.delete()
            form.add_error('archivo', str(e))
            return render(request, 'pruebas/form_pagina.html',
                          {'form': form, 'colegio': colegio, 'titulo': 'Publicar una página'})

        if pagina.captura_resultados and not pagina.endpoint_reescrito:
            messages.warning(
                request,
                'La página quedó publicada, pero el archivo no tiene la línea "const ENDPOINT". '
                'Los resultados no se van a guardar en la plataforma.',
            )
        else:
            messages.success(request, f'Página publicada en {pagina.ruta}')
        return redirect('pruebas:lista_paginas')

    return render(request, 'pruebas/form_pagina.html',
                  {'form': form, 'colegio': colegio, 'titulo': 'Publicar una página'})


@login_required
def editar_pagina(request, slug):
    colegio = colegio_actual(request)
    if not puede_administrar(request.user, colegio):
        raise PermissionDenied

    pagina = get_object_or_404(PaginaPublicada, colegio=colegio, slug=slug)
    form = PaginaForm(request.POST or None, request.FILES or None, instance=pagina, colegio=colegio)
    if request.method == 'POST' and form.is_valid():
        pagina = form.save()
        nuevo_archivo = form.cleaned_data.get('archivo')
        if nuevo_archivo and 'archivo' in form.changed_data:
            try:
                publicar_archivo(request, pagina, nuevo_archivo)
            except ZipInvalido as e:
                form.add_error('archivo', str(e))
                return render(request, 'pruebas/form_pagina.html',
                              {'form': form, 'pagina': pagina, 'colegio': colegio,
                               'titulo': 'Editar la página'})
        messages.success(request, 'Página actualizada.')
        return redirect('pruebas:lista_paginas')

    return render(request, 'pruebas/form_pagina.html',
                  {'form': form, 'pagina': pagina, 'colegio': colegio, 'titulo': 'Editar la página'})


@login_required
@require_POST
def eliminar_pagina(request, slug):
    colegio = colegio_actual(request)
    if not puede_administrar(request.user, colegio):
        raise PermissionDenied
    pagina = get_object_or_404(PaginaPublicada, colegio=colegio, slug=slug)
    borrar_sitio(pagina.base_sitio)
    pagina.delete()
    messages.success(request, 'Página eliminada.')
    return redirect('pruebas:lista_paginas')


# ---------------------------------------------------------------------------
# Banco de preguntas: presentar una prueba importada
# ---------------------------------------------------------------------------

def presentar_prueba(request, slug):
    colegio = colegio_actual(request)
    prueba = get_object_or_404(Prueba, colegio=colegio, slug=slug)
    if not prueba.activa and not puede_administrar(request.user, colegio):
        raise Http404('Esta prueba no está abierta.')

    preguntas = []
    for p in prueba.preguntas.prefetch_related('opciones'):
        preguntas.append({
            'id': p.codigo_origen or str(p.orden),
            'comp': p.competencia,
            'compNombre': p.competencia_nombre,
            'tema': p.tema,
            'apr': p.aprendizaje,
            'enun': p.enunciado,
            'preg': p.pregunta,
            'fig': p.imagen.url if p.imagen else None,
            'tabla': p.tabla,
            'clave': p.clave,
            'expl': p.explicacion,
            'err': p.analisis_error,
            'pct': p.pct_referencia,
            'ops': [
                {'letra': o.letra, 'texto': o.texto, 'fig': o.imagen.url if o.imagen else None}
                for o in p.opciones.all()
            ],
        })

    return render(request, 'pruebas/presentar.html', {
        'prueba': prueba,
        'colegio': colegio,
        'preguntas': preguntas,
        'endpoint': reverse('pruebas:api_resultados', kwargs={'slug': prueba.slug}),
    })


# ---------------------------------------------------------------------------
# Subida de varios archivos a la vez
# ---------------------------------------------------------------------------

def titulo_desde_nombre(nombre):
    """Convierte "4. Prueba de nivelación 3° página web.html" en algo legible."""
    import re
    base = PurePosixPath(nombre).stem
    base = base.replace('_', ' ').replace('-', ' ')
    base = re.sub(r'^\s*\d+\s*[.\-)]\s*', '', base)          # numeración inicial
    base = re.sub(r'\s*(p[áa]gina\s+web|pagina_web)\s*$', '', base, flags=re.I)
    base = re.sub(r'\s+', ' ', base).strip()
    return (base or 'Página').capitalize()


@login_required
def subir_varias(request):
    colegio = colegio_actual(request)
    if not puede_administrar(request.user, colegio):
        raise PermissionDenied

    form = SubidaMultipleForm(request.POST or None, request.FILES or None)
    resultados = []

    if request.method == 'POST' and form.is_valid():
        archivos = form.cleaned_data['archivos']
        captura = form.cleaned_data.get('captura_resultados', True)
        visible = form.cleaned_data.get('visible', True)

        for archivo in archivos:
            titulo = titulo_desde_nombre(archivo.name)
            pagina = PaginaPublicada(
                colegio=colegio,
                titulo=titulo,
                captura_resultados=captura,
                visible=visible,
                creada_por=request.user,
            )
            try:
                pagina.save()
                publicar_archivo(request, pagina, archivo)
                resultados.append({'pagina': pagina, 'error': None})
            except ZipInvalido as e:
                if pagina.pk:
                    pagina.delete()
                resultados.append({'pagina': None, 'nombre': archivo.name, 'error': str(e)})
            except Exception as e:  # noqa: BLE001 - se informa archivo por archivo
                if pagina.pk:
                    pagina.delete()
                resultados.append({'pagina': None, 'nombre': archivo.name, 'error': str(e)})

        bien = sum(1 for r in resultados if r['pagina'])
        if bien:
            messages.success(request, f'{bien} de {len(archivos)} archivos quedaron publicados.')
        return render(request, 'pruebas/resumen_subida.html',
                      {'resultados': resultados, 'colegio': colegio})

    return render(request, 'pruebas/subir_varias.html', {'form': form, 'colegio': colegio})


# ---------------------------------------------------------------------------
# Código QR
# ---------------------------------------------------------------------------

def _url_publica(request, pagina):
    return request.build_absolute_uri(pagina.ruta)


@login_required
def qr_imagen(request, slug):
    colegio = colegio_actual(request)
    if not puede_administrar(request.user, colegio):
        raise PermissionDenied
    pagina = get_object_or_404(PaginaPublicada, colegio=colegio, slug=slug)

    respuesta = HttpResponse(generar_qr(_url_publica(request, pagina)), content_type='image/png')
    respuesta['Content-Disposition'] = f'inline; filename="qr-{pagina.slug}.png"'
    return respuesta


@login_required
def qr_hoja(request, slug):
    """Hoja lista para imprimir y pegar en el salón."""
    colegio = colegio_actual(request)
    if not puede_administrar(request.user, colegio):
        raise PermissionDenied
    pagina = get_object_or_404(PaginaPublicada, colegio=colegio, slug=slug)

    return render(request, 'pruebas/qr_hoja.html', {
        'pagina': pagina,
        'colegio': colegio,
        'url': _url_publica(request, pagina),
    })