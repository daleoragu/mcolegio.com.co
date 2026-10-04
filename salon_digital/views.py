# salon_digital/views.py
import json
import os
import posixpath
from pathlib import PurePosixPath
from urllib.parse import urlparse

from django.conf import settings
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.http import FileResponse, Http404, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from django.template.loader import render_to_string

from . import identidad
from .decoradores import cuenta_activa_requerida, cuenta_requerida
from .forms import ClaveForm, PaginaForm, SubidaMultipleForm
from .models import (
    Comentario, Cuenta, Detalle, Grupo, Integrante, PaginaPublicada, Prueba, Sesion,
)
from .utils import (
    ZipInvalido, analizar, borrar_sitio, cabecera_csp, escanear_html, extraer_sitio,
    generar_qr, ip_cliente, reescribir_endpoint,
)

SESION_PANEL = 'salon_panel_autorizado'

TIPOS = {
    '.html': 'text/html; charset=utf-8', '.htm': 'text/html; charset=utf-8',
    '.css': 'text/css; charset=utf-8', '.js': 'text/javascript; charset=utf-8',
    '.json': 'application/json', '.svg': 'image/svg+xml', '.txt': 'text/plain; charset=utf-8',
}


# ---------------------------------------------------------------------------
# Ayudas
# ---------------------------------------------------------------------------

def dominio_publico():
    base = (os.getenv('SALON_DOMINIO_PUBLICO', '')
            or getattr(settings, 'SALON_DOMINIO_PUBLICO', '') or '')
    return base.strip().rstrip('/')


def origen_archivos():
    """Esquema y dominio desde donde se sirven los archivos del bucket."""
    try:
        partes = urlparse(default_storage.url('x'))
        if partes.scheme and partes.netloc:
            return f'{partes.scheme}://{partes.netloc}'
    except Exception:
        pass
    return ''


def url_api(request, pagina):
    """Dirección absoluta que se graba dentro del HTML publicado."""
    ruta = reverse('salon_digital:api_resultados', kwargs={
        'usuario': pagina.propietario.slug, 'slug': pagina.slug})
    base = dominio_publico()
    if base:
        if not base.startswith(('http://', 'https://')):
            base = 'https://' + base
        return base.rstrip('/') + ruta
    return request.build_absolute_uri(ruta)


def _pagina_publica(usuario, slug):
    cuenta = get_object_or_404(Cuenta, slug=usuario)
    return get_object_or_404(PaginaPublicada, propietario=cuenta, slug=slug)


def _origen(usuario, slug):
    """Una página publicada o una prueba del banco, por su dirección."""
    cuenta = get_object_or_404(Cuenta, slug=usuario)
    pagina = PaginaPublicada.objects.filter(propietario=cuenta, slug=slug).first()
    if pagina:
        return pagina
    prueba = Prueba.objects.filter(propietario=cuenta, slug=slug).first()
    if prueba:
        return prueba
    raise Http404('No existe esa actividad.')


def autorizado_en_panel(request, origen):
    llaves = request.session.get(SESION_PANEL, [])
    if f'{origen.__class__.__name__}:{origen.pk}' in llaves:
        return True
    cuenta = getattr(request.user, 'cuenta_salon', None)
    return bool(cuenta and cuenta.pk == origen.propietario_id) or request.user.is_staff


def autorizar_en_panel(request, origen):
    llaves = request.session.get(SESION_PANEL, [])
    etiqueta = f'{origen.__class__.__name__}:{origen.pk}'
    if etiqueta not in llaves:
        llaves.append(etiqueta)
        request.session[SESION_PANEL] = llaves
        request.session.modified = True


# ---------------------------------------------------------------------------
# Publicación de archivos
# ---------------------------------------------------------------------------

def publicar_archivo(request, pagina, archivo):
    """Deja el archivo subido listo para servirse y lo revisa."""
    endpoint = url_api(request, pagina)
    alertas = set()

    def transformar(contenido):
        texto = contenido.decode('utf-8', errors='replace') if isinstance(contenido, bytes) else contenido
        alertas.update(escanear_html(texto))
        if not pagina.captura_resultados:
            return texto, False
        return reescribir_endpoint(texto, endpoint, pagina.clave_panel)

    if (archivo.name or '').lower().endswith('.zip'):
        base_anterior = pagina.base_sitio
        base = posixpath.join(
            'salon', 'sitios', pagina.propietario.slug, pagina.slug,
            timezone.now().strftime('%Y%m%d%H%M%S'),
        )
        cantidad, indice, reescritos = extraer_sitio(archivo, base, transformar)

        pagina.tipo = 'sitio'
        pagina.base_sitio = base
        pagina.archivos_sitio = cantidad
        if not pagina.indice or pagina.indice == 'index.html':
            pagina.indice = indice
        pagina.endpoint_reescrito = reescritos > 0
        pagina.archivo = ''
        pagina.alertas = '\n'.join(sorted(alertas))
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
    pagina.alertas = '\n'.join(sorted(alertas))
    if cambio:
        nombre = PurePosixPath(pagina.archivo.name).name
        pagina.archivo.save(nombre, ContentFile(texto.encode('utf-8')), save=False)
    pagina.save()
    return 1


# ---------------------------------------------------------------------------
# Vistas públicas
# ---------------------------------------------------------------------------

def landing(request):
    cuenta = getattr(request.user, 'cuenta_salon', None)
    if cuenta:
        return redirect('salon_digital:panel')
    return render(request, 'salon_digital/landing.html', {
        'total_docentes': Cuenta.objects.filter(estado='verificada').count(),
    })


def perfil_publico(request, usuario):
    cuenta = get_object_or_404(Cuenta, slug=usuario)
    paginas = [p for p in cuenta.paginas.filter(visible=True, listar_en_perfil=True) if p.disponible]
    return render(request, 'salon_digital/perfil.html', {'cuenta': cuenta, 'paginas': paginas})


def ver_pagina(request, usuario, slug):
    """Sirve el HTML publicado con la política que impide robar datos."""
    pagina = _pagina_publica(usuario, slug)
    es_dueno = getattr(request.user, 'cuenta_salon', None) == pagina.propietario

    if not pagina.disponible and not (es_dueno or request.user.is_staff):
        if pagina.estado in ('oculta', 'suspendida'):
            raise Http404('Esta página no está publicada.')
        return render(request, 'salon_digital/cerrada.html', {'pagina': pagina}, status=403)

    # Si el docente usa grupos, primero hay que saber quién entra.
    if pagina.identificacion != 'libre' and not es_dueno:
        quien = identidad.integrante_de(request, pagina)
        salto = request.session.get('salon_sin_grupo') == pagina.pk
        if not quien and not (pagina.identificacion == 'opcional' and salto):
            return redirect('paginas:identificarse', usuario=usuario, slug=slug)

    ruta = pagina.ruta_contenido
    if not ruta or not default_storage.exists(ruta):
        raise Http404('El archivo de esta página no está disponible.')

    with default_storage.open(ruta, 'rb') as fh:
        contenido = fh.read()

    texto = contenido.decode('utf-8', errors='replace')
    extra = bloque_comentarios(request, pagina)
    if extra:
        if '</body>' in texto.lower():
            corte = texto.lower().rindex('</body>')
            texto = texto[:corte] + extra + texto[corte:]
        else:
            texto += extra

    respuesta = HttpResponse(texto, content_type='text/html; charset=utf-8')
    respuesta['Content-Security-Policy'] = cabecera_csp(origen_archivos())
    respuesta['X-Content-Type-Options'] = 'nosniff'

    PaginaPublicada.objects.filter(pk=pagina.pk).update(visitas=pagina.visitas + 1)
    return respuesta


def archivo_pagina(request, usuario, slug, ruta):
    """Entrega los archivos que acompañan a un sitio .zip.

    Los manda al bucket con una redirección para no cargar al servidor con
    imágenes y hojas de estilo; solo el HTML pasa por aquí.
    """
    pagina = _pagina_publica(usuario, slug)
    if not pagina.disponible and getattr(request.user, 'cuenta_salon', None) != pagina.propietario:
        raise Http404('No disponible.')
    if pagina.tipo != 'sitio' or not pagina.base_sitio:
        raise Http404('Esta página no tiene archivos adicionales.')
    if '..' in ruta or ruta.startswith('/'):
        raise Http404('Ruta inválida.')

    completa = posixpath.join(pagina.base_sitio, ruta)
    if not default_storage.exists(completa):
        raise Http404('Archivo no encontrado.')

    extension = posixpath.splitext(ruta)[1].lower()
    if extension in ('.html', '.htm'):
        with default_storage.open(completa, 'rb') as fh:
            contenido = fh.read()
        respuesta = HttpResponse(contenido, content_type='text/html; charset=utf-8')
        respuesta['Content-Security-Policy'] = cabecera_csp(origen_archivos())
        respuesta['X-Content-Type-Options'] = 'nosniff'
        return respuesta

    return redirect(default_storage.url(completa))


# ---------------------------------------------------------------------------
# Endpoint de resultados
# ---------------------------------------------------------------------------

@csrf_exempt
def api_resultados(request, usuario, slug):
    """POST guarda una sesión; GET con ?clave= devuelve la lista en JSON."""
    origen = _origen(usuario, slug)

    if request.method == 'GET':
        clave = (request.GET.get('clave') or '').strip()
        if clave.upper() != origen.clave_panel.upper():
            return JsonResponse({'error': 'clave incorrecta'}, status=403)
        datos = [
            {
                'ape': s.apellidos, 'nom': s.nombres, 'completo': s.completo,
                'sede': s.sede, 'gru': s.nombre_grupo, 'prueba': s.clave_prueba,
                'pruebaNombre': s.prueba_nombre, 'fecha': s.fecha.isoformat(),
                'ok': s.aciertos, 'total': s.total, 'pct': s.porcentaje,
                'seg': s.segundos, 'cambios': s.cambios, 'vez': s.vez,
                'det': [
                    {'n': d.numero, 'apr': d.aprendizaje, 'comp': d.competencia,
                     'ac': d.acierto, 'marcada': d.marcada, 'clave': d.clave,
                     'expl': d.explicacion, 'intentos': d.intentos, 'seg': d.segundos}
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

    cuenta = origen.propietario
    if not cuenta.activa:
        return JsonResponse({'error': 'cuenta inactiva'}, status=403)
    if not cuenta.puede_recibir_resultados():
        return JsonResponse({'error': 'límite de resultados del mes alcanzado'}, status=429)

    try:
        datos = json.loads(request.body.decode('utf-8'))
    except (ValueError, UnicodeDecodeError):
        return JsonResponse({'error': 'json inválido'}, status=400)

    quien = None
    if isinstance(origen, PaginaPublicada) and origen.identificacion != 'libre':
        quien = identidad.integrante_de(request, origen)

    sesion = registrar_sesion(origen, datos, ip_cliente(request), quien)
    respuesta = JsonResponse({'estado': 'ok', 'id': sesion.pk})
    respuesta['Access-Control-Allow-Origin'] = '*'
    return respuesta


def registrar_sesion(origen, datos, ip=None, quien=None):
    """Guarda un resultado. Si `quien` viene, manda sobre el nombre escrito."""
    fecha = parse_datetime(datos.get('fecha') or '') or timezone.now()
    if timezone.is_naive(fecha):
        fecha = timezone.make_aware(fecha, timezone.get_current_timezone())

    completo = (datos.get('completo') or
                f"{datos.get('ape', '')} {datos.get('nom', '')}").strip()

    apellidos = str(datos.get('ape') or '')[:120]
    nombres = str(datos.get('nom') or '')[:120]
    grupo_nombre = str(datos.get('gru') or '')[:30]

    if quien is not None:
        apellidos, nombres = quien.apellidos[:120], quien.nombres[:120]
        completo = quien.completo
        grupo_nombre = quien.grupo.nombre[:30]

    sesion = Sesion.objects.create(
        cuenta=origen.propietario,
        grupo=quien.grupo if quien else None,
        integrante=quien,
        pagina=origen if isinstance(origen, PaginaPublicada) else None,
        prueba=origen if isinstance(origen, Prueba) else None,
        clave_prueba=str(datos.get('prueba') or '')[:30],
        prueba_nombre=str(datos.get('pruebaNombre') or getattr(origen, 'titulo', ''))[:200],
        apellidos=apellidos,
        nombres=nombres,
        completo=completo[:240],
        sede=str(datos.get('sede') or '')[:120],
        grupo_texto=grupo_nombre,
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

    Detalle.objects.bulk_create([
        Detalle(
            sesion=sesion, orden=i,
            numero=str(d.get('n') or '')[:30],
            aprendizaje=str(d.get('apr') or ''),
            competencia=str(d.get('comp') or '')[:10],
            acierto=bool(d.get('ac')),
            marcada=str(d.get('marcada') or '')[:2],
            clave=str(d.get('clave') or '')[:2],
            explicacion=str(d.get('expl') or ''),
            intentos=int(d.get('intentos') or 0),
            segundos=int(d.get('seg') or 0),
        )
        for i, d in enumerate(datos.get('det') or [], start=1)
    ])
    return sesion


# ---------------------------------------------------------------------------
# Panel de resultados (acceso con clave)
# ---------------------------------------------------------------------------

def panel_clave(request, usuario, slug):
    origen = _origen(usuario, slug)
    if autorizado_en_panel(request, origen):
        return redirect('salon_digital:panel_resultados', usuario=usuario, slug=slug)

    form = ClaveForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        if form.cleaned_data['clave'].strip().upper() == origen.clave_panel.upper():
            autorizar_en_panel(request, origen)
            return redirect('salon_digital:panel_resultados', usuario=usuario, slug=slug)
        form.add_error('clave', 'La clave no es correcta.')

    return render(request, 'salon_digital/panel_clave.html', {'form': form, 'origen': origen})


def panel_resultados(request, usuario, slug):
    origen = _origen(usuario, slug)
    if not autorizado_en_panel(request, origen):
        return redirect('salon_digital:panel_clave', usuario=usuario, slug=slug)

    sesiones = origen.sesiones.select_related('grupo', 'integrante').prefetch_related('detalles')
    grupo = (request.GET.get('grupo') or '').strip()
    if grupo:
        sesiones = [s for s in sesiones if s.nombre_grupo.lower() == grupo.lower()]

    return render(request, 'salon_digital/panel_resultados.html', {
        'origen': origen,
        'sesiones': sesiones,
        'resumen': analizar(sesiones),
        'grupos': sorted({s.nombre_grupo for s in origen.sesiones.select_related('grupo')
                          if s.nombre_grupo}),
        'grupo_activo': grupo,
    })


def exportar_resultados(request, usuario, slug):
    from .exports import construir_libro
    origen = _origen(usuario, slug)
    if not autorizado_en_panel(request, origen):
        return redirect('salon_digital:panel_clave', usuario=usuario, slug=slug)

    sesiones = list(origen.sesiones.select_related('grupo', 'integrante')
                    .prefetch_related('detalles'))
    contenido = construir_libro(origen, sesiones, analizar(sesiones))

    nombre = f'resultados-{origen.slug}-{timezone.now():%Y%m%d}.xlsx'
    respuesta = HttpResponse(
        contenido,
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    )
    respuesta['Content-Disposition'] = f'attachment; filename="{nombre}"'
    return respuesta


# ---------------------------------------------------------------------------
# Panel del docente
# ---------------------------------------------------------------------------

@cuenta_requerida
def panel(request):
    cuenta = request.cuenta
    return render(request, 'salon_digital/panel.html', {
        'cuenta': cuenta,
        'paginas': cuenta.paginas.all(),
        'pruebas': cuenta.pruebas.all(),
        'resultados_mes': cuenta.resultados_del_mes,
    })


@cuenta_activa_requerida
def nueva_pagina(request):
    cuenta = request.cuenta
    if not cuenta.puede_publicar_otra():
        messages.error(
            request,
            f'Tu plan permite {cuenta.limite("paginas")} páginas y ya las tienes todas. '
            f'Borra una o amplía tu plan.',
        )
        return redirect('salon_digital:panel')

    form = PaginaForm(request.POST or None, request.FILES or None, cuenta=cuenta)
    if request.method == 'POST' and form.is_valid():
        pagina = form.save(commit=False)
        pagina.propietario = cuenta
        pagina.save()
        try:
            publicar_archivo(request, pagina, form.cleaned_data['archivo'])
        except ZipInvalido as e:
            pagina.delete()
            form.add_error('archivo', str(e))
            return render(request, 'salon_digital/form_pagina.html',
                          {'form': form, 'cuenta': cuenta, 'titulo': 'Publicar una página'})

        if pagina.alertas:
            messages.warning(
                request,
                'La página quedó publicada, pero el revisor automático encontró algo que '
                'conviene mirar: ' + pagina.alertas.replace('\n', '; '),
            )
        elif pagina.captura_resultados and not pagina.endpoint_reescrito:
            messages.warning(
                request,
                'La página quedó publicada, pero el archivo no tiene la línea "const ENDPOINT", '
                'así que los resultados no se van a guardar aquí.',
            )
        else:
            messages.success(request, f'Página publicada en {pagina.ruta}')
        return redirect('salon_digital:panel')

    return render(request, 'salon_digital/form_pagina.html',
                  {'form': form, 'cuenta': cuenta, 'titulo': 'Publicar una página'})


@cuenta_activa_requerida
def editar_pagina(request, slug):
    cuenta = request.cuenta
    pagina = get_object_or_404(PaginaPublicada, propietario=cuenta, slug=slug)
    form = PaginaForm(request.POST or None, request.FILES or None, instance=pagina, cuenta=cuenta)

    if request.method == 'POST' and form.is_valid():
        pagina = form.save()
        nuevo = form.cleaned_data.get('archivo')
        if nuevo and 'archivo' in form.changed_data:
            try:
                publicar_archivo(request, pagina, nuevo)
            except ZipInvalido as e:
                form.add_error('archivo', str(e))
                return render(request, 'salon_digital/form_pagina.html',
                              {'form': form, 'pagina': pagina, 'cuenta': cuenta,
                               'titulo': 'Editar la página'})
        messages.success(request, 'Página actualizada.')
        return redirect('salon_digital:panel')

    return render(request, 'salon_digital/form_pagina.html',
                  {'form': form, 'pagina': pagina, 'cuenta': cuenta, 'titulo': 'Editar la página'})


@cuenta_requerida
@require_POST
def eliminar_pagina(request, slug):
    pagina = get_object_or_404(PaginaPublicada, propietario=request.cuenta, slug=slug)
    borrar_sitio(pagina.base_sitio)
    pagina.delete()
    messages.success(request, 'Página eliminada.')
    return redirect('salon_digital:panel')


@cuenta_activa_requerida
def subir_varias(request):
    cuenta = request.cuenta
    form = SubidaMultipleForm(request.POST or None, request.FILES or None)
    resultados = []

    if request.method == 'POST' and form.is_valid():
        archivos = form.cleaned_data['archivos']
        captura = form.cleaned_data.get('captura_resultados', True)
        visible = form.cleaned_data.get('visible', True)

        for archivo in archivos:
            if not cuenta.puede_publicar_otra():
                resultados.append({'pagina': None, 'nombre': archivo.name,
                                   'error': 'Se alcanzó el límite de páginas de tu plan.'})
                continue
            pagina = PaginaPublicada(
                propietario=cuenta,
                titulo=titulo_desde_nombre(archivo.name),
                captura_resultados=captura,
                visible=visible,
            )
            try:
                pagina.save()
                publicar_archivo(request, pagina, archivo)
                resultados.append({'pagina': pagina, 'error': None})
            except Exception as e:  # noqa: BLE001 — se informa archivo por archivo
                if pagina.pk:
                    pagina.delete()
                resultados.append({'pagina': None, 'nombre': archivo.name, 'error': str(e)})

        bien = sum(1 for r in resultados if r['pagina'])
        if bien:
            messages.success(request, f'{bien} de {len(archivos)} archivos quedaron publicados.')
        return render(request, 'salon_digital/resumen_subida.html',
                      {'resultados': resultados, 'cuenta': cuenta})

    return render(request, 'salon_digital/subir_varias.html', {'form': form, 'cuenta': cuenta})


def titulo_desde_nombre(nombre):
    import re
    base = PurePosixPath(nombre).stem.replace('_', ' ').replace('-', ' ')
    base = re.sub(r'^\s*\d+\s*[.\-)]\s*', '', base)
    base = re.sub(r'\s*(p[áa]gina\s+web|pagina_web)\s*$', '', base, flags=re.I)
    base = re.sub(r'\s+', ' ', base).strip()
    return (base or 'Página').capitalize()


# ---------------------------------------------------------------------------
# Código QR
# ---------------------------------------------------------------------------

@cuenta_requerida
def qr_imagen(request, slug):
    pagina = get_object_or_404(PaginaPublicada, propietario=request.cuenta, slug=slug)
    url = request.build_absolute_uri(pagina.ruta)
    respuesta = HttpResponse(generar_qr(url), content_type='image/png')
    respuesta['Content-Disposition'] = f'inline; filename="qr-{pagina.slug}.png"'
    return respuesta


@cuenta_requerida
def qr_hoja(request, slug):
    pagina = get_object_or_404(PaginaPublicada, propietario=request.cuenta, slug=slug)
    return render(request, 'salon_digital/qr_hoja.html', {
        'pagina': pagina, 'cuenta': request.cuenta,
        'url': request.build_absolute_uri(pagina.ruta),
    })


# ---------------------------------------------------------------------------
# Banco de preguntas
# ---------------------------------------------------------------------------

def presentar_prueba(request, usuario, slug):
    cuenta = get_object_or_404(Cuenta, slug=usuario)
    prueba = get_object_or_404(Prueba, propietario=cuenta, slug=slug)
    if not prueba.disponible and getattr(request.user, 'cuenta_salon', None) != cuenta:
        raise Http404('Esta prueba no está abierta.')

    preguntas = [{
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
        'ops': [{'letra': o.letra, 'texto': o.texto, 'fig': o.imagen.url if o.imagen else None}
                for o in p.opciones.all()],
    } for p in prueba.preguntas.prefetch_related('opciones')]

    return render(request, 'salon_digital/presentar.html', {
        'prueba': prueba,
        'cuenta': cuenta,
        'preguntas': preguntas,
        'endpoint': reverse('salon_digital:api_resultados',
                            kwargs={'usuario': cuenta.slug, 'slug': prueba.slug}),
    })


# ---------------------------------------------------------------------------
# Ayuda para preparar los archivos
# ---------------------------------------------------------------------------

def ayuda(request):
    """Lo que necesita un docente para que su HTML mande resultados aquí."""
    return render(request, 'salon_digital/ayuda.html', {
        'cuenta': getattr(request.user, 'cuenta_salon', None),
    })


def descargar(request, cual):
    """Entrega la plantilla o el motor de envío como archivo."""
    archivos = {
        'plantilla': ('salon_digital/plantilla-prueba.html', 'plantilla-prueba.html',
                      'text/html; charset=utf-8'),
        'motor': ('salon_digital/salon.js', 'salon.js', 'text/javascript; charset=utf-8'),
    }
    if cual not in archivos:
        raise Http404('No existe ese archivo.')

    from django.contrib.staticfiles import finders
    ruta_rel, nombre, tipo = archivos[cual]
    ruta = finders.find(ruta_rel)
    if not ruta:
        raise Http404('Archivo no encontrado.')

    with open(ruta, 'rb') as fh:
        contenido = fh.read()
    respuesta = HttpResponse(contenido, content_type=tipo)
    respuesta['Content-Disposition'] = f'attachment; filename="{nombre}"'
    return respuesta


# ---------------------------------------------------------------------------
# Identificación del estudiante (opcional, por grupo)
# ---------------------------------------------------------------------------

def identificarse(request, usuario, slug):
    """Pide el código del grupo y el nombre, antes de entrar a la actividad."""
    pagina = _pagina_publica(usuario, slug)
    if pagina.identificacion == 'libre':
        return redirect(pagina.ruta)

    permitidos = pagina.grupos.all()
    grupos = permitidos if permitidos.exists() else pagina.propietario.grupos.filter(activo=True)

    grupo = None
    error = ''
    codigo = (request.POST.get('codigo') or request.GET.get('codigo') or '').strip().upper()

    if codigo:
        grupo = grupos.filter(codigo=codigo, activo=True).first()
        if not grupo:
            error = 'Ese código no corresponde a ningún grupo de esta actividad.'

    if request.method == 'POST' and request.POST.get('integrante'):
        elegido = Integrante.objects.filter(
            pk=request.POST['integrante'], activo=True, grupo__in=grupos,
        ).select_related('grupo').first()
        if elegido:
            identidad.guardar(request, elegido)
            return redirect(pagina.ruta)
        error = 'No encontramos a esa persona en el grupo.'

    return render(request, 'salon_digital/identificarse.html', {
        'pagina': pagina,
        'grupo': grupo,
        'codigo': codigo,
        'error': error,
        'actual': identidad.leer(request),
        'permite_libre': pagina.identificacion == 'opcional',
    })


def entrar_sin_grupo(request, usuario, slug):
    """El estudiante decide escribir su nombre en vez de usar un grupo."""
    pagina = _pagina_publica(usuario, slug)
    if pagina.identificacion == 'grupo':
        raise Http404('Esta actividad solo acepta estudiantes de un grupo.')
    identidad.olvidar(request)
    request.session['salon_sin_grupo'] = pagina.pk
    request.session.modified = True
    return redirect(pagina.ruta)


# ---------------------------------------------------------------------------
# Comentarios
# ---------------------------------------------------------------------------

def bloque_comentarios(request, pagina):
    """El HTML que se pega al final de la página publicada."""
    if pagina.comentarios == 'no':
        return ''

    comentarios = pagina.lista_comentarios.filter(aprobado=True, responde_a__isnull=True)
    accion = reverse('paginas:comentar', kwargs={
        'usuario': pagina.propietario.slug, 'slug': pagina.slug})

    return render_to_string('salon_digital/_comentarios.html', {
        'pagina': pagina,
        'comentarios': comentarios,
        'accion': accion,
        'moderados': pagina.comentarios == 'moderados',
        'classroom': pagina.compartir_classroom,
        'url_pagina': request.build_absolute_uri(pagina.ruta),
    }, request=request)


@require_POST
def comentar(request, usuario, slug):
    pagina = _pagina_publica(usuario, slug)
    if pagina.comentarios == 'no':
        raise Http404('Esta página no recibe comentarios.')

    nombre = (request.POST.get('nombre') or '').strip()[:120]
    texto = (request.POST.get('texto') or '').strip()[:4000]
    trampa = (request.POST.get('sitio_web') or '').strip()  # señuelo contra robots

    if trampa or not nombre or not texto:
        return redirect(pagina.ruta + '#comentarios')

    es_dueno = getattr(request.user, 'cuenta_salon', None) == pagina.propietario
    Comentario.objects.create(
        pagina=pagina,
        nombre=nombre,
        texto=texto,
        aprobado=(pagina.comentarios == 'abiertos') or es_dueno,
        del_autor=es_dueno,
        ip=ip_cliente(request),
    )
    destino = pagina.ruta + ('#comentarios' if pagina.comentarios == 'abiertos' or es_dueno else '#gracias')
    return redirect(destino)


@cuenta_requerida
def moderar_comentarios(request, slug):
    pagina = get_object_or_404(PaginaPublicada, propietario=request.cuenta, slug=slug)

    if request.method == 'POST':
        pk = request.POST.get('comentario')
        accion = request.POST.get('accion')
        comentario = pagina.lista_comentarios.filter(pk=pk).first()
        if comentario:
            if accion == 'aprobar':
                comentario.aprobado = True
                comentario.save(update_fields=['aprobado'])
            elif accion == 'borrar':
                comentario.delete()
        return redirect('salon_digital:moderar_comentarios', slug=slug)

    return render(request, 'salon_digital/moderar_comentarios.html', {
        'pagina': pagina,
        'pendientes': pagina.lista_comentarios.filter(aprobado=False),
        'publicados': pagina.lista_comentarios.filter(aprobado=True),
    })
