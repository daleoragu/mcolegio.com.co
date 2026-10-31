"""Biblioteca de Mis materiales: banco libre de mcolegio, comunidad de docentes y materiales de mi colegio.

Reglas:
  · Banco libre: lo publica solo el dueño de la plataforma; lo ven todos, también la prueba gratis.
  · Comunidad: lo ve cualquier docente con cuenta; los primeros materiales de cada docente se revisan antes
    de publicarse; el autor sale con su nombre y la licencia es Creative Commons BY-NC (uso libre, sin fines
    comerciales). Tres reportes lo ocultan hasta que se revise.
  · Mi colegio: lo ven los docentes del mismo colegio; se publica de una vez.
  · «Usar una copia» la pone en mis documentos, editable y con mi encabezado; las imágenes se copian a mi nube.
"""
from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.models import User
from django.db import transaction
from django.db.models import F, Q
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.clickjacking import xframe_options_sameorigin
from django.views.decorators.http import require_POST

from . import bloques as B
from . import calificar as C
from . import creditos as K
from . import exportar
from .models import Documento, Imagen, MaterialCompartido, Reporte, Valoracion
from .views import MB, _doc, vista
from .views_banco import copiar_imagen

REVISADOS_ANTES = 3          # los primeros materiales de cada docente en la comunidad pasan por revisión
REPORTES_PARA_OCULTAR = 3
POR_PAGINA = 60


def _visibles(a):
    """Lo publicado que puede ver este docente."""
    q = Q(estado='publicado') & (Q(alcance__in=('libre', 'comunidad')))
    if a.colegio is not None:
        q |= Q(estado='publicado', alcance='colegio', colegio=a.colegio)
    return MaterialCompartido.objects.filter(q)


def _puede_ver(a, m):
    if m.autor_id == a.request.user.pk or a.request.user.is_superuser:
        return True
    if m.estado != 'publicado':
        return False
    return m.alcance in ('libre', 'comunidad') or (m.alcance == 'colegio' and m.colegio_id == getattr(a.colegio, 'pk', None))


def _insignias(autor):
    publicados = MaterialCompartido.objects.filter(autor=autor, estado='publicado')
    n = publicados.count()
    usos = sum(publicados.values_list('usos', flat=True))
    salida = []
    if n >= 1:
        salida.append('Primer material compartido')
    if n >= 10:
        salida.append('10 materiales compartidos')
    if n >= 25:
        salida.append('25 materiales compartidos')
    if usos >= 50:
        salida.append('Sus materiales se usaron 50 veces')
    return salida


@vista
def biblioteca(request, a):
    pestana = request.GET.get('ver') or 'todo'
    if pestana == 'mios':
        qs = MaterialCompartido.objects.filter(autor=request.user)
    else:
        qs = _visibles(a)
        if pestana in ('libre', 'comunidad', 'colegio'):
            qs = qs.filter(alcance=pestana)
    for palabra in B.texto_plano(request.GET.get('q'), 120).split()[:6]:
        qs = qs.filter(Q(titulo__icontains=palabra) | Q(tema__icontains=palabra) | Q(descripcion__icontains=palabra)
                       | Q(dba__icontains=palabra))
    if request.GET.get('area'):
        qs = qs.filter(area__icontains=B.texto_plano(request.GET['area'], 80))
    if request.GET.get('grado'):
        qs = qs.filter(grado__iexact=B.texto_plano(request.GET['grado'], 40))
    if request.GET.get('tipo') in dict(Documento.TIPOS):
        qs = qs.filter(tipo=request.GET['tipo'])
    orden = {'usados': '-usos', 'estrellas': '-estrellas_suma'}.get(request.GET.get('orden'), '-actualizado')
    qs = qs.select_related('autor', 'colegio').order_by(orden)
    return render(request, 'materiales/biblioteca.html', {
        'base': a.base, 'acceso': a, 'materiales': qs[:POR_PAGINA], 'total': qs.count(), 'filtro': request.GET,
        'pestana': pestana, 'tipos': Documento.TIPOS,
        'en_revision': MaterialCompartido.objects.filter(estado__in=('revision', 'oculto')).count()
        if request.user.is_superuser else 0})


@vista
def material(request, a, pk):
    m = get_object_or_404(MaterialCompartido.objects.select_related('autor', 'colegio'), pk=pk)
    if not _puede_ver(a, m):
        raise Http404
    mia = Valoracion.objects.filter(material=m, usuario=request.user).values_list('estrellas', flat=True).first()
    return render(request, 'materiales/material.html', {
        'base': a.base, 'acceso': a, 'm': m, 'mia': mia, 'es_autor': m.autor_id == request.user.pk,
        'reportado': Reporte.objects.filter(material=m, usuario=request.user).exists(),
        'autor_nombre': m.autor.get_full_name() or m.autor.username})


def _documento_de(m):
    """Un documento sin guardar con el contenido compartido, para ver su PDF con las imágenes del autor."""
    return Documento(propietario=m.autor, titulo=m.titulo, tipo=m.tipo, area=m.area, grado=m.grado,
                     contenido=m.contenido)


@xframe_options_sameorigin
@vista
def material_pdf(request, a, pk):
    m = get_object_or_404(MaterialCompartido, pk=pk)
    if not _puede_ver(a, m):
        raise Http404
    datos = exportar.pdf(request, _documento_de(m), colegio=a.colegio, encabezado=a.encabezado(),
                         docente=m.autor.get_full_name())
    r = HttpResponse(datos, content_type='application/pdf')
    r['Content-Disposition'] = f'inline; filename="{exportar.nombre_archivo(_documento_de(m), "pdf")}"'
    return r


@require_POST
@vista
def usar(request, a, pk):
    """Copia el material a mis documentos; las imágenes de otro autor se copian a mi nube."""
    m = get_object_or_404(MaterialCompartido, pk=pk)
    if not _puede_ver(a, m):
        raise Http404
    contenido = {'bloques': [dict(b) for b in m.contenido.get('bloques', [])],
                 'opciones': dict(m.contenido.get('opciones') or {})}
    usadas = B.imagenes_usadas(contenido)
    mapa = {}
    if usadas and m.autor_id != request.user.pk:
        imagenes = list(Imagen.objects.filter(pk__in=usadas, propietario=m.autor))
        peso = sum(i.peso for i in imagenes)
        if a.usado() + peso > a.cuota():
            messages.error(request, f'Su nube no tiene espacio para las imágenes de este material '
                                    f'({round(peso / MB, 1)} MB). Libere espacio o amplíe su nube.')
            return redirect('materiales:material', pk=pk)
        for img in imagenes:
            try:
                mapa[img.pk] = copiar_imagen(img, request.user).pk
            except Exception:
                continue
    elif usadas:
        mapa = {i: i for i in usadas}
    for b in contenido['bloques']:
        if b.get('imagen'):
            b['imagen'] = mapa.get(b['imagen'])
    validas = set(mapa.values())
    doc = Documento.objects.create(propietario=request.user, colegio=a.colegio, titulo=m.titulo, tipo=m.tipo,
                                   area=m.area, grado=m.grado, contenido=B.limpiar(contenido, validas))
    MaterialCompartido.objects.filter(pk=m.pk).update(usos=F('usos') + 1)
    messages.success(request, f'«{m.titulo}» quedó en sus documentos, con su encabezado. Ajústelo a su gusto.')
    return redirect('materiales:editor', pk=doc.pk)


@require_POST
@vista
def valorar(request, a, pk):
    m = get_object_or_404(MaterialCompartido, pk=pk)
    if not _puede_ver(a, m) or m.autor_id == request.user.pk:
        raise Http404
    try:
        estrellas = max(1, min(5, int(request.POST.get('estrellas'))))
    except (TypeError, ValueError):
        return redirect('materiales:material', pk=pk)
    with transaction.atomic():
        anterior = Valoracion.objects.select_for_update().filter(material=m, usuario=request.user).first()
        if anterior:
            MaterialCompartido.objects.filter(pk=m.pk).update(estrellas_suma=F('estrellas_suma') - anterior.estrellas + estrellas)
            anterior.estrellas = estrellas
            anterior.save(update_fields=['estrellas'])
        else:
            Valoracion.objects.create(material=m, usuario=request.user, estrellas=estrellas)
            MaterialCompartido.objects.filter(pk=m.pk).update(estrellas_suma=F('estrellas_suma') + estrellas,
                                                              estrellas_n=F('estrellas_n') + 1)
    messages.success(request, 'Gracias por valorar el material.')
    return redirect('materiales:material', pk=pk)


@require_POST
@vista
def reportar(request, a, pk):
    m = get_object_or_404(MaterialCompartido, pk=pk)
    if not _puede_ver(a, m) or m.autor_id == request.user.pk:
        raise Http404
    motivo = B.texto_plano(request.POST.get('motivo'), 300)
    if not motivo:
        messages.error(request, 'Cuéntenos qué tiene de malo el material.')
        return redirect('materiales:material', pk=pk)
    _, nuevo = Reporte.objects.get_or_create(material=m, usuario=request.user, defaults={'motivo': motivo})
    if nuevo and m.alcance != 'libre' and m.reportes.count() >= REPORTES_PARA_OCULTAR:
        MaterialCompartido.objects.filter(pk=m.pk).update(estado='oculto')
    messages.info(request, 'Gracias. El equipo de mcolegio lo va a revisar.')
    return redirect('materiales:biblioteca')


@require_POST
@vista
def compartir(request, a, pk):
    """Publica una copia del documento en la biblioteca (o actualiza la que ya estaba)."""
    doc = _doc(a, pk)
    alcance = request.POST.get('alcance')
    if alcance == 'libre' and not request.user.is_superuser:
        alcance = 'comunidad'
    if alcance == 'colegio' and a.colegio is None:
        alcance = 'comunidad'
    if alcance not in dict(MaterialCompartido.ALCANCES):
        messages.error(request, 'Escoja con quién lo comparte.')
        return redirect('materiales:editor', pk=pk)
    if alcance != 'colegio' and request.POST.get('acepto') != 'on':
        messages.error(request, 'Para compartir con la comunidad confirme que el material es suyo y acepta la licencia.')
        return redirect('materiales:editor', pk=pk)
    contenido = B.limpiar(doc.contenido, B.imagenes_usadas(doc.contenido))
    if not contenido['bloques']:
        messages.error(request, 'El documento está vacío.')
        return redirect('materiales:editor', pk=pk)
    m = MaterialCompartido.objects.filter(documento=doc, alcance=alcance).first()
    revisar = alcance == 'comunidad' and not request.user.is_superuser and MaterialCompartido.objects.filter(
        autor=request.user, alcance='comunidad', estado='publicado').count() < REVISADOS_ANTES
    datos = dict(titulo=doc.titulo, tipo=doc.tipo, area=doc.area, grado=doc.grado, contenido=contenido,
                 tema=B.texto_plano(request.POST.get('tema'), 120), dba=B.texto_plano(request.POST.get('dba'), 200),
                 descripcion=B.texto_plano(request.POST.get('descripcion'), 300),
                 preguntas=len([b for b in C.preguntas(contenido) if b.get('modo') != 'hoja']))
    if m is None:
        m = MaterialCompartido(documento=doc, autor=request.user, colegio=a.colegio, alcance=alcance)
    for k, v in datos.items():
        setattr(m, k, v)
    if m.estado != 'oculto':
        m.estado = 'revision' if revisar else 'publicado'
    m.motivo = ''
    m.save()
    if m.estado == 'revision':
        messages.success(request, 'Enviado a la comunidad. Sus primeros materiales los revisa el equipo de mcolegio '
                                  'antes de publicarse; le llegarán 20 créditos de IA cuando se apruebe.')
    else:
        messages.success(request, f'Publicado en {m.get_alcance_display()}.')
    return redirect('materiales:material', pk=m.pk)


@require_POST
@vista
def retirar(request, a, pk):
    m = get_object_or_404(MaterialCompartido, pk=pk, autor=request.user)
    m.delete()
    messages.info(request, 'Material retirado de la biblioteca. Su documento sigue igual.')
    return redirect('materiales:biblioteca')


@vista
def autor(request, a, uid):
    u = get_object_or_404(User, pk=uid)
    materiales = [m for m in MaterialCompartido.objects.filter(autor=u, estado='publicado').order_by('-usos')
                  if _puede_ver(a, m)]
    return render(request, 'materiales/autor.html', {'base': a.base, 'acceso': a, 'autor': u, 'materiales': materiales,
                                                     'insignias': _insignias(u),
                                                     'usos': sum(m.usos for m in materiales)})


# ---------------------------------------------------------------------------
# Revisión (dueño de la plataforma)
# ---------------------------------------------------------------------------
@user_passes_test(lambda u: u.is_authenticated and u.is_superuser, login_url='/super-admin/login/')
def revision(request):
    if request.method == 'POST':
        m = get_object_or_404(MaterialCompartido, pk=request.POST.get('material'))
        que = request.POST.get('accion')
        if que == 'aprobar':
            m.estado, m.motivo = 'publicado', ''
            if not m.regalo_dado and m.alcance == 'comunidad':
                K.regalar(m.autor, K.REGALO_COMPARTIR, f'Regalo por compartir «{m.titulo[:80]}»')
                m.regalo_dado = True
            m.reportes.all().delete()
            m.save()
            messages.success(request, f'«{m.titulo}» publicado.')
        elif que == 'rechazar':
            m.estado = 'rechazado'
            m.motivo = B.texto_plano(request.POST.get('motivo'), 300) or 'No cumple las reglas de la comunidad.'
            m.save(update_fields=['estado', 'motivo'])
            messages.info(request, f'«{m.titulo}» rechazado.')
        elif que == 'libre':
            m.alcance, m.estado = 'libre', 'publicado'
            m.save(update_fields=['alcance', 'estado'])
            messages.success(request, f'«{m.titulo}» pasó al banco libre de mcolegio.')
        return redirect('materiales:revision')
    pendientes = MaterialCompartido.objects.filter(estado__in=('revision', 'oculto')).select_related('autor', 'colegio') \
        .prefetch_related('reportes').order_by('creado')
    return render(request, 'materiales/revision.html', {'pendientes': pendientes, 'hoy': timezone.localdate()})


@vista
def ayuda(request, a):
    return render(request, 'materiales/ayuda.html', {'base': a.base, 'acceso': a})
