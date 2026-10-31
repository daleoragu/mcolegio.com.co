"""Mis materiales: lista, editor, imágenes, exportar a PDF y Word, y publicar en el aula."""
import io
import json

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.files.base import ContentFile
from django.db.models import Sum
from django.http import Http404, HttpResponse, HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.clickjacking import xframe_options_sameorigin
from django.views.decorators.http import require_POST

from . import bloques as B
from . import exportar, plantillas
from .models import Documento, EncabezadoDocente, Imagen

MB = 1024 * 1024
MAX_SUBIDA = 10 * MB
MAX_LADO = 1600
MAX_PIXELES = 40_000_000


# ---------------------------------------------------------------------------
# Quién entra
# ---------------------------------------------------------------------------
class Acceso:
    def __init__(self, request):
        self.request = request
        self.colegio = getattr(request, 'colegio', None)
        self.cuenta = None
        self.ok = False
        user = request.user
        if not user.is_authenticated:
            return
        if self.colegio is not None:
            from notas.permisos import es_admin
            from notas.models import Docente
            self.admin = es_admin(request)
            self.ok = self.admin or Docente.objects.filter(user=user, colegio=self.colegio).exists()
        else:
            self.admin = False
            self.cuenta = getattr(user, 'cuenta_salon', None)
            self.ok = self.cuenta is not None

    @property
    def base(self):
        return 'notas/base.html' if self.colegio is not None else 'aula/base_salon.html'

    @property
    def es_individual(self):
        return self.colegio is None

    def documentos(self):
        return Documento.objects.filter(propietario=self.request.user, colegio=self.colegio)

    def plantillas_formato(self):
        """Los documentos que sirven de formato: los del colegio, o los que el docente marcó como suyos."""
        if self.colegio is not None:
            return Documento.objects.filter(colegio=self.colegio, plantilla_colegio=True)
        return self.documentos().filter(plantilla_colegio=True)

    def cuota(self):
        if self.cuenta is not None and getattr(self.cuenta, 'plan', '') == 'prueba':
            return 200 * MB
        return 2048 * MB

    def usado(self):
        return Imagen.objects.filter(propietario=self.request.user).aggregate(t=Sum('peso'))['t'] or 0

    def encabezado(self):
        if self.colegio is not None:
            return None
        return EncabezadoDocente.objects.filter(usuario=self.request.user).first()

    def docente(self):
        u = self.request.user
        return u.get_full_name() or u.username

    def aulas(self):
        from aula.models import Aula
        if self.colegio is not None:
            return list(Aula.objects.filter(asignacion__docente__user=self.request.user, colegio=self.colegio)
                        .select_related('asignacion__materia', 'asignacion__curso'))
        if self.cuenta is not None:
            return list(Aula.objects.filter(grupo__propietario=self.cuenta).select_related('grupo'))
        return []


def vista(fn):
    @login_required
    def envoltura(request, *args, **kwargs):
        a = Acceso(request)
        if not a.ok:
            return HttpResponseForbidden('Mis materiales es para los docentes.')
        return fn(request, a, *args, **kwargs)
    envoltura.__name__ = fn.__name__
    return envoltura


def _doc(a, pk):
    return get_object_or_404(a.documentos(), pk=pk)


def _nube_docente(request):
    """Qué nubes del docente (Drive u OneDrive) están configuradas, como en el cuadernillo de PuntoExacto."""
    from puntoexacto.views import _nube_config
    datos = _nube_config(request)
    return {'google': datos['google'], 'onedrive': datos['onedrive']}


def _nube(a):
    usado, cuota = a.usado(), a.cuota()
    return {'usado_mb': round(usado / MB, 1), 'cuota_mb': round(cuota / MB),
            'porcentaje': min(100, round(usado * 100 / cuota)) if cuota else 0}


# ---------------------------------------------------------------------------
# Lista y creación
# ---------------------------------------------------------------------------
@vista
def lista(request, a):
    return render(request, 'materiales/lista.html', {
        'base': a.base, 'acceso': a, 'documentos': a.documentos(), 'nube': _nube(a),
        'formatos': a.plantillas_formato().select_related('propietario'), 'tipos': Documento.TIPOS})


@require_POST
@vista
def nuevo(request, a):
    tipo = request.POST.get('tipo') or 'libre'
    if tipo not in dict(Documento.TIPOS):
        tipo = 'libre'
    base = None
    if tipo == 'institucional':
        base = a.plantillas_formato().filter(pk=request.POST.get('base') or 0).first()
        if base is None:
            messages.warning(request, 'Todavía no hay un formato guardado. Arme una guía y márquela como formato.')
            return redirect('materiales:lista')
    titulo = (request.POST.get('titulo') or '').strip()[:150] or dict(Documento.TIPOS)[tipo]
    doc = Documento.objects.create(propietario=request.user, colegio=a.colegio, titulo=titulo, tipo=tipo,
                                   area=(request.POST.get('area') or (base.area if base else ''))[:80],
                                   grado=(request.POST.get('grado') or '')[:40],
                                   contenido=plantillas.contenido_inicial(tipo, base))
    return redirect('materiales:editor', pk=doc.pk)


@require_POST
@vista
def accion(request, a, pk):
    doc = _doc(a, pk)
    que = request.POST.get('accion')
    if que == 'eliminar':
        doc.delete()
        messages.info(request, f'«{doc.titulo}» eliminado.')
        return redirect('materiales:lista')
    if que == 'duplicar':
        copia = Documento.objects.create(propietario=request.user, colegio=a.colegio, titulo=f'{doc.titulo[:140]} (copia)',
                                         tipo=doc.tipo, area=doc.area, grado=doc.grado, periodo=doc.periodo,
                                         contenido=doc.contenido)
        return redirect('materiales:editor', pk=copia.pk)
    if que == 'formato':
        if a.colegio is not None and not a.admin:
            messages.warning(request, 'Solo el rector o el coordinador marcan el formato del colegio.')
        else:
            doc.plantilla_colegio = not doc.plantilla_colegio
            doc.save(update_fields=['plantilla_colegio'])
            messages.success(request, 'Guardado como formato.' if doc.plantilla_colegio else 'Ya no es un formato.')
        return redirect('materiales:lista')
    if que == 'publicar':
        return _publicar(request, a, doc)
    return redirect('materiales:editor', pk=pk)


def _publicar(request, a, doc):
    from aula import logica
    from aula.models import Material
    aulas = {str(x.pk): x for x in a.aulas()}
    aula = aulas.get(request.POST.get('aula') or '')
    if aula is None:
        messages.error(request, 'Escoja una de sus aulas.')
        return redirect('materiales:editor', pk=doc.pk)
    datos = exportar.pdf(request, doc, colegio=a.colegio, encabezado=a.encabezado(), docente=a.docente(),
                         modo=request.POST.get('modo'))
    m = Material(aula=aula, titulo=doc.titulo[:150], unidad='Mis materiales', tipo='archivo',
                 descripcion=' · '.join(x for x in (doc.area, doc.grado and f'Grado {doc.grado}') if x)[:300])
    nombre = exportar.nombre_archivo(doc, 'pdf')
    m.archivo.save(nombre, ContentFile(datos), save=False)
    m.nombre_archivo = nombre[:150]
    m.save()
    logica.avisar_estudiantes(aula, f'{aula.titulo}: nuevo material «{m.titulo}»',
                              request.build_absolute_uri(f'/aula/{aula.pk}/material/'))
    messages.success(request, f'Publicado en el material de {aula.titulo}.')
    return redirect('materiales:editor', pk=doc.pk)


# ---------------------------------------------------------------------------
# Editor
# ---------------------------------------------------------------------------
@vista
def editor(request, a, pk):
    doc = _doc(a, pk)
    imagenes = {i.pk: request.build_absolute_uri(f'/materiales/imagen/{i.pk}/')
                for i in Imagen.objects.filter(propietario=request.user, pk__in=B.imagenes_usadas(doc.contenido))}
    return render(request, 'materiales/editor.html', {
        'base': a.base, 'acceso': a, 'doc': doc, 'contenido': doc.contenido, 'imagenes': imagenes,
        'aulas': a.aulas(), 'nube': _nube(a), 'tipos': Documento.TIPOS, 'nube_docente': _nube_docente(request)})


@require_POST
@vista
def guardar(request, a, pk):
    doc = _doc(a, pk)
    try:
        datos = json.loads(request.body or '{}')
    except ValueError:
        return JsonResponse({'ok': False, 'error': 'Datos dañados.'}, status=400)
    validas = set(Imagen.objects.filter(propietario=request.user).values_list('pk', flat=True))
    doc.contenido = B.limpiar(datos.get('contenido'), validas)
    doc.titulo = B.texto_plano(datos.get('titulo'), 150) or doc.titulo
    doc.area = B.texto_plano(datos.get('area'), 80)
    doc.grado = B.texto_plano(datos.get('grado'), 40)
    doc.periodo = B.texto_plano(datos.get('periodo'), 40)
    doc.save()
    return JsonResponse({'ok': True, 'guardado': doc.actualizado.isoformat()})


# ---------------------------------------------------------------------------
# Imágenes
# ---------------------------------------------------------------------------
def preparar_imagen(archivo):
    """(bytes, extensión, ancho, alto) de la imagen reducida a 1600 px; ValueError si no sirve."""
    from PIL import Image, ImageOps
    datos = archivo.read(MAX_SUBIDA + 1)
    if len(datos) > MAX_SUBIDA:
        raise ValueError('La imagen pasa de 10 MB.')
    try:
        im = Image.open(io.BytesIO(datos))
        if im.size[0] * im.size[1] > MAX_PIXELES:
            raise ValueError('La imagen es demasiado grande.')
        im.load()
        im = ImageOps.exif_transpose(im)
    except ValueError:
        raise
    except Exception:
        raise ValueError('Ese archivo no es una imagen.')
    im.thumbnail((MAX_LADO, MAX_LADO * 3))
    transparente = im.mode in ('RGBA', 'LA', 'P') and (im.mode != 'P' or 'transparency' in im.info)
    salida = io.BytesIO()
    if transparente:
        im.convert('RGBA').save(salida, 'PNG', optimize=True)
        ext = '.png'
    else:
        im.convert('RGB').save(salida, 'JPEG', quality=85, optimize=True)
        ext = '.jpg'
    return salida.getvalue(), ext, im.size[0], im.size[1]


@require_POST
@vista
def imagen_subir(request, a):
    archivo = request.FILES.get('imagen')
    if archivo is None:
        return JsonResponse({'ok': False, 'error': 'No llegó ninguna imagen.'}, status=400)
    try:
        datos, ext, ancho, alto = preparar_imagen(archivo)
    except ValueError as e:
        return JsonResponse({'ok': False, 'error': str(e)}, status=400)
    if a.usado() + len(datos) > a.cuota():
        return JsonResponse({'ok': False, 'error': f'Su nube está llena ({round(a.cuota() / MB)} MB). '
                                                  'Libere espacio o amplíe su plan.'}, status=400)
    img = Imagen(propietario=request.user, ancho=ancho, alto=alto, peso=len(datos))
    img.archivo.save(f'imagen{ext}', ContentFile(datos), save=False)
    img.save()
    return JsonResponse({'ok': True, 'id': img.pk, 'url': request.build_absolute_uri(f'/materiales/imagen/{img.pk}/'),
                         'nube': _nube(a)})


@vista
def imagen_ver(request, a, pk):
    img = get_object_or_404(Imagen, pk=pk, propietario=request.user)
    return redirect(img.archivo.url)


# ---------------------------------------------------------------------------
# Exportar
# ---------------------------------------------------------------------------
@xframe_options_sameorigin
@vista
def pdf(request, a, pk):
    doc = _doc(a, pk)
    datos = exportar.pdf(request, doc, colegio=a.colegio, encabezado=a.encabezado(), docente=a.docente(),
                         modo=request.GET.get('modo'))
    r = HttpResponse(datos, content_type='application/pdf')
    disp = 'attachment' if request.GET.get('descargar') else 'inline'
    r['Content-Disposition'] = f'{disp}; filename="{exportar.nombre_archivo(doc, "pdf")}"'
    return r


@vista
def word(request, a, pk):
    doc = _doc(a, pk)
    datos = exportar.docx(doc, colegio=a.colegio, encabezado=a.encabezado(), docente=a.docente(),
                          modo=request.GET.get('modo'))
    r = HttpResponse(datos, content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document')
    r['Content-Disposition'] = f'attachment; filename="{exportar.nombre_archivo(doc, "docx")}"'
    return r


@vista
def paginas(request, a, pk):
    doc = _doc(a, pk)
    return JsonResponse(exportar.paginas(request, doc, colegio=a.colegio, encabezado=a.encabezado(),
                                         docente=a.docente()))


# ---------------------------------------------------------------------------
# Encabezado del plan individual
# ---------------------------------------------------------------------------
@vista
def encabezado(request, a):
    if not a.es_individual:
        messages.info(request, 'En el colegio, los documentos llevan el encabezado del colegio '
                               '(el de los boletines). Lo cambia el administrador.')
        return redirect('materiales:lista')
    enc, _ = EncabezadoDocente.objects.get_or_create(usuario=request.user)
    if request.method == 'POST':
        enc.linea1 = B.texto_plano(request.POST.get('linea1'), 120)
        enc.linea2 = B.texto_plano(request.POST.get('linea2'), 120)
        enc.linea3 = B.texto_plano(request.POST.get('linea3'), 120)
        logo = request.FILES.get('logo')
        if request.POST.get('quitar_logo') == 'on':
            enc.logo = ''
        elif logo:
            try:
                datos, ext, _, _ = preparar_imagen(logo)
                enc.logo.save(f'logo{ext}', ContentFile(datos), save=False)
            except ValueError as e:
                messages.error(request, str(e))
        enc.save()
        messages.success(request, 'Encabezado guardado.')
        return redirect('materiales:lista')
    return render(request, 'materiales/encabezado.html', {'base': a.base, 'acceso': a, 'enc': enc})
