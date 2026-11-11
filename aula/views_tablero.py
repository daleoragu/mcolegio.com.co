"""El tablero compartido: lo que piden la pantalla del docente y la de cada estudiante (estado, operaciones, imágenes)."""
import json

from django.http import FileResponse, Http404, HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from . import logica, tablero as TB
from .models import ImagenTablero, TableroClase


def quien(request, t):
    """(autor, es_docente, puede_editar) de quien abre el tablero; None si no tiene nada que ver con él."""
    if request.user.is_authenticated and request.user.pk == t.autor_id:
        return 'd', True, True
    if t.aula_id is None:
        return None
    c = logica.contexto(request, t.aula)
    if c is None:
        return None
    if c.es_docente:
        return 'd', True, True
    persona = c.estudiante or c.integrante
    if persona is None:
        return None
    return logica.clave_de(persona), False, t.editan_estudiantes


def _tablero(request, tid):
    t = get_object_or_404(TableroClase.objects.select_related('aula'), pk=tid)
    q = quien(request, t)
    if q is None:
        raise Http404
    return t, q


def config(request, t, q, volver):
    """Lo que necesita la pantalla del tablero (docente o estudiante)."""
    autor, es_docente, puede = q
    return {'id': t.pk, 'titulo': t.titulo, 'fondo': t.fondo, 'v': t.version, 'objetos': t.objetos or [],
            'yo': autor, 'docente': es_docente, 'editar': puede, 'compartido': t.aula_id is not None,
            'urlEstado': reverse('aula:tablero_estado', args=[t.pk]), 'urlOp': reverse('aula:tablero_op', args=[t.pk]),
            'urlImagen': reverse('aula:tablero_subir', args=[t.pk]),
            'urlVerImagen': reverse('aula:tablero_imagen', args=[t.pk, 0]).replace('/0/', '/ID/'), 'volver': volver}


def estado(request, tid):
    t, q = _tablero(request, tid)
    try:
        desde = int(request.GET.get('desde'))
    except (TypeError, ValueError):
        desde = None
    datos = TB.estado(t, desde)
    datos['editar'] = q[2]
    return JsonResponse(datos)


@require_POST
def op(request, tid):
    t, (autor, es_docente, puede) = _tablero(request, tid)
    try:
        cuerpo = json.loads(request.body or b'{}')
    except ValueError:
        return JsonResponse({'ok': False, 'error': 'Datos inválidos.'}, status=400)
    try:
        v = TB.aplicar(t.pk, cuerpo, autor, es_docente, puede)
    except PermissionError as e:
        return JsonResponse({'ok': False, 'error': str(e)}, status=403)
    except ValueError as e:
        return JsonResponse({'ok': False, 'error': str(e)}, status=400)
    return JsonResponse({'ok': True, 'v': v})


@require_POST
def subir(request, tid):
    """Una imagen pegada, arrastrada o subida: se reduce (máx. 1600 px), sin datos EXIF, y queda en este tablero."""
    t, (autor, es_docente, puede) = _tablero(request, tid)
    if not puede:
        return JsonResponse({'ok': False, 'error': 'El docente no ha habilitado la escritura.'}, status=403)
    if t.imagenes.count() >= 300:
        return JsonResponse({'ok': False, 'error': 'Este tablero ya tiene 300 imágenes.'}, status=400)
    f = request.FILES.get('imagen')
    if f is None:
        return JsonResponse({'ok': False, 'error': 'Falta la imagen.'}, status=400)
    from django.core.files.base import ContentFile
    from materiales.views import cuota_nube, preparar_imagen, usado_nube
    try:
        datos, ext, ancho, alto = preparar_imagen(f)
    except ValueError as e:
        return JsonResponse({'ok': False, 'error': str(e)}, status=400)
    # Las imágenes cuentan en la nube del docente dueño del tablero (también las que pegan los estudiantes)
    if usado_nube(t.autor) + len(datos) > cuota_nube(t.autor, getattr(t.autor, 'cuenta_salon', None)):
        return JsonResponse({'ok': False, 'error': 'La nube del docente está llena: borre imágenes o tableros que ya no use, o amplíe su plan.'}, status=400)
    img = ImagenTablero(tablero=t, ancho=ancho, alto=alto, peso=len(datos))
    img.archivo.save(f'imagen.{ext}', ContentFile(datos), save=False)
    img.save()
    return JsonResponse({'ok': True, 'id': img.pk, 'w': ancho, 'h': alto,
                         'url': reverse('aula:tablero_imagen', args=[t.pk, img.pk])})


def imagen(request, tid, iid):
    t, _ = _tablero(request, tid)
    img = get_object_or_404(ImagenTablero, pk=iid, tablero=t)
    try:
        respuesta = FileResponse(img.archivo.open('rb'))
    except Exception:
        raise Http404
    respuesta['Cache-Control'] = 'private, max-age=86400'
    return respuesta


def ver(request, pk, tid):
    """El tablero compartido, desde el aula (estudiantes y docente)."""
    t = get_object_or_404(TableroClase.objects.select_related('aula'), pk=tid, aula_id=pk)
    q = quien(request, t)
    if q is None:
        return HttpResponseForbidden('Este tablero es para la clase con la que se compartió.')
    return render(request, 'salon_digital/tablero.html', {
        'cfg': config(request, t, q, reverse('aula:muro', args=[pk])), 't': t, 'aulas': [], 'es_dueno': False})
