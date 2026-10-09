# notas/views/portal_admin_views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import user_passes_test
from django.contrib import messages
from django.http import HttpResponseNotFound

# Se importan los modelos y formularios necesarios
from ..models import DocumentoPublico, FotoGaleria, Noticia, ImagenCarrusel, RecursoEducativo, VideoPortal
from ..forms import (
    DocumentoPublicoForm, FotoGaleriaForm, NoticiaForm, ImagenCarruselForm,
    ColegioPersonalizacionForm, RecursoEducativoForm, VideoPortalForm
)
from ..permisos import es_admin, es_admin_usuario

def es_admin_o_docente(user):
    return es_admin_usuario(user) or user.groups.filter(name='Docentes').exists()

@user_passes_test(es_admin_o_docente)
def personalizacion_portal_vista(request):
    colegio = request.colegio
    if not colegio:
        return HttpResponseNotFound("<h1>Colegio no configurado</h1>")

    if request.method == 'POST':
        form = ColegioPersonalizacionForm(request.POST, request.FILES, instance=colegio)
        if form.is_valid():
            form.save()
            messages.success(request, '¡La personalización del portal se ha guardado correctamente!')
            return redirect('notas:personalizacion_portal')
        else:
            # --- INICIO DE LA CORRECCIÓN ---
            # En lugar de un mensaje genérico, ahora mostramos el error de cada campo.
            for field, errors in form.errors.items():
                for error in errors:
                    # Obtenemos la etiqueta del campo para que el mensaje sea más claro.
                    # Por ejemplo, en lugar de 'nombre', dirá 'Nombre del Colegio'.
                    field_label = form.fields.get(field).label if form.fields.get(field) else field.capitalize()
                    messages.error(request, f"Error en '{field_label}': {error}")
            # --- FIN DE LA CORRECCIÓN ---
    else:
        form = ColegioPersonalizacionForm(instance=colegio)

    from ..models import Colegio
    context = {
        'form': form,
        'page_title': 'Personalizar Apariencia y Contenido del Portal',
        'colegio': colegio,
        # (valor, nombre corto, descripción) para el selector visual de diseños
        'disenos': [(v, n.split(':')[0], n.split(':', 1)[1].strip() if ':' in n else '')
                    for v, n in Colegio.LAYOUT_CHOICES],
    }
    return render(request, 'notas/admin_portal/personalizacion_portal.html', context)

@user_passes_test(es_admin_o_docente)
def configuracion_portal_vista(request):
    if not request.colegio:
        return HttpResponseNotFound("<h1>Colegio no configurado</h1>")
    return render(request, 'notas/admin_portal/configuracion_portal.html', {'colegio': request.colegio})

# --- Vistas para Documentos (CORREGIDA) ---
@user_passes_test(es_admin_o_docente)
def gestion_documentos_vista(request):
    colegio = request.colegio
    if not colegio:
        return HttpResponseNotFound("<h1>Colegio no configurado</h1>")

    if request.method == 'POST':
        form = DocumentoPublicoForm(request.POST, request.FILES)
        if form.is_valid():
            documento = form.save(commit=False)
            documento.colegio = colegio
            documento.save()
            messages.success(request, 'Documento guardado exitosamente.')
            return redirect('notas:gestion_documentos')
        else:
            # Si el formulario no es válido, se añade un mensaje de error.
            messages.error(request, 'No se pudo guardar el documento. Por favor, corrija los errores.')
    else:
        form = DocumentoPublicoForm()
    
    documentos = DocumentoPublico.objects.filter(colegio=colegio)
    # La vista ahora re-renderiza la página con el formulario inválido para mostrar los errores.
    context = {'form': form, 'documentos': documentos, 'page_title': 'Gestionar Documentos', 'colegio': colegio}
    return render(request, 'notas/admin_portal/gestion_documentos.html', context)

@user_passes_test(es_admin_o_docente)
def eliminar_documento_vista(request, pk):
    if not request.colegio:
        return HttpResponseNotFound("<h1>Colegio no configurado</h1>")
    documento = get_object_or_404(DocumentoPublico, pk=pk, colegio=request.colegio)
    if request.method == 'POST':
        documento.delete()
        messages.success(request, 'Documento eliminado exitosamente.')
    return redirect('notas:gestion_documentos')

# --- Vistas para la Galería (CORREGIDA) ---
@user_passes_test(es_admin_o_docente)
def gestion_galeria_vista(request):
    colegio = request.colegio
    if not colegio:
        return HttpResponseNotFound("<h1>Colegio no configurado</h1>")
        
    if request.method == 'POST':
        form = FotoGaleriaForm(request.POST, request.FILES)
        if form.is_valid():
            foto = form.save(commit=False)
            foto.colegio = colegio
            foto.save()
            messages.success(request, 'Foto añadida a la galería.')
            return redirect('notas:gestion_galeria')
        else:
            messages.error(request, 'No se pudo añadir la foto. Por favor, corrija los errores.')
    else:
        form = FotoGaleriaForm()

    fotos = FotoGaleria.objects.filter(colegio=colegio)
    context = {'form': form, 'fotos': fotos, 'page_title': 'Gestionar Galería', 'colegio': colegio}
    return render(request, 'notas/admin_portal/gestion_galeria.html', context)

@user_passes_test(es_admin_o_docente)
def eliminar_foto_vista(request, pk):
    if not request.colegio:
        return HttpResponseNotFound("<h1>Colegio no configurado</h1>")
    foto = get_object_or_404(FotoGaleria, pk=pk, colegio=request.colegio)
    if request.method == 'POST':
        foto.delete()
        messages.success(request, 'Foto eliminada de la galería.')
    return redirect('notas:gestion_galeria')

# --- Vistas para Noticias (MEJORADA) ---
@user_passes_test(es_admin_o_docente)
def gestion_noticias_vista(request):
    if not request.colegio:
        return HttpResponseNotFound("<h1>Colegio no configurado</h1>")
    noticias = Noticia.objects.filter(colegio=request.colegio)
    context = {'noticias': noticias, 'page_title': 'Gestionar Noticias', 'colegio': request.colegio}
    return render(request, 'notas/admin_portal/gestion_noticias.html', context)

@user_passes_test(es_admin_o_docente)
def crear_noticia_vista(request):
    if not request.colegio:
        return HttpResponseNotFound("<h1>Colegio no configurado</h1>")
        
    if request.method == 'POST':
        form = NoticiaForm(request.POST, request.FILES)
        if form.is_valid():
            noticia = form.save(commit=False)
            noticia.autor = request.user
            noticia.colegio = request.colegio
            noticia.save()
            messages.success(request, 'Noticia creada como BORRADOR. Ahora puedes publicarla desde la lista.')
            return redirect('notas:gestion_noticias')
        else:
            # Se añade un mensaje de error explícito para diagnóstico.
            messages.error(request, 'El formulario contiene errores. Por favor, revise los campos.')
    else:
        form = NoticiaForm()
    context = {'form': form, 'accion': 'Crear', 'page_title': 'Crear Noticia', 'colegio': request.colegio}
    return render(request, 'notas/admin_portal/formulario_noticia.html', context)

@user_passes_test(es_admin_o_docente)
def editar_noticia_vista(request, pk):
    if not request.colegio:
        return HttpResponseNotFound("<h1>Colegio no configurado</h1>")
    noticia = get_object_or_404(Noticia, pk=pk, colegio=request.colegio)
    if request.method == 'POST':
        form = NoticiaForm(request.POST, request.FILES, instance=noticia)
        if form.is_valid():
            form.save()
            messages.success(request, 'Noticia actualizada exitosamente.')
            return redirect('notas:gestion_noticias')
        else:
            # Se añade un mensaje de error explícito para diagnóstico.
            messages.error(request, 'El formulario contiene errores. Por favor, revise los campos.')
    else:
        form = NoticiaForm(instance=noticia)
    context = {'form': form, 'accion': 'Editar', 'page_title': f'Editando: {noticia.titulo}', 'colegio': request.colegio}
    return render(request, 'notas/admin_portal/formulario_noticia.html', context)

@user_passes_test(es_admin_o_docente)
def eliminar_noticia_vista(request, pk):
    if not request.colegio:
        return HttpResponseNotFound("<h1>Colegio no configurado</h1>")
    noticia = get_object_or_404(Noticia, pk=pk, colegio=request.colegio)
    if request.method == 'POST':
        noticia.delete()
        messages.success(request, 'Noticia eliminada exitosamente.')
    return redirect('notas:gestion_noticias')

@user_passes_test(es_admin_o_docente)
def publicar_noticia_vista(request, pk):
    if not request.colegio:
        return HttpResponseNotFound("<h1>Colegio no configurado</h1>")
    noticia = get_object_or_404(Noticia, pk=pk, colegio=request.colegio)
    if request.method == 'POST':
        if noticia.estado == 'BORRADOR':
            noticia.estado = 'PUBLICADO'
            messages.success(request, f"La noticia '{noticia.titulo}' ha sido publicada.")
        else:
            noticia.estado = 'BORRADOR'
            messages.info(request, f"La noticia '{noticia.titulo}' ha sido movida a borradores.")
        noticia.save()
    return redirect('notas:gestion_noticias')

# --- Vistas para gestionar el Carrusel (CORREGIDA) ---
@user_passes_test(es_admin_o_docente)
def gestion_carrusel_vista(request):
    colegio = request.colegio
    if not colegio:
        return HttpResponseNotFound("<h1>Colegio no configurado</h1>")
        
    if request.method == 'POST':
        form = ImagenCarruselForm(request.POST, request.FILES)
        if form.is_valid():
            imagen = form.save(commit=False)
            imagen.colegio = colegio
            imagen.save()
            messages.success(request, 'Imagen añadida al carrusel.')
            return redirect('notas:gestion_carrusel')
        else:
            messages.error(request, 'No se pudo añadir la imagen. Por favor, corrija los errores.')
    else:
        form = ImagenCarruselForm()
    
    imagenes = ImagenCarrusel.objects.filter(colegio=colegio).order_by('orden')
    context = { 
        'form': form, 
        'imagenes': imagenes, 
        'page_title': 'Gestionar Carrusel',
        'colegio': colegio
    }
    return render(request, 'notas/admin_portal/gestion_carrusel.html', context)

@user_passes_test(es_admin_o_docente)
def editar_imagen_carrusel_vista(request, pk):
    if not request.colegio:
        return HttpResponseNotFound("<h1>Colegio no configurado</h1>")
    imagen = get_object_or_404(ImagenCarrusel, pk=pk, colegio=request.colegio)
    if request.method == 'POST':
        form = ImagenCarruselForm(request.POST, request.FILES, instance=imagen)
        if form.is_valid():
            form.save()
            messages.success(request, 'Imagen del carrusel actualizada exitosamente.')
            return redirect('notas:gestion_carrusel')
        else:
            messages.error(request, 'El formulario contiene errores. Por favor, revise los campos.')
    else:
        form = ImagenCarruselForm(instance=imagen)
    
    context = {
        'form': form,
        'page_title': f'Editando Imagen: {imagen.titulo}',
        'colegio': colegio
    }
    return render(request, 'notas/admin_portal/editar_imagen_carrusel.html', context)

@user_passes_test(es_admin_o_docente)
def eliminar_imagen_carrusel_vista(request, pk):
    if not request.colegio:
        return HttpResponseNotFound("<h1>Colegio no configurado</h1>")
    imagen = get_object_or_404(ImagenCarrusel, pk=pk, colegio=request.colegio)
    if request.method == 'POST':
        imagen.delete()
        messages.success(request, 'Imagen eliminada del carrusel.')
    return redirect('notas:gestion_carrusel')


@user_passes_test(es_admin_usuario)
def elegir_diseno_portal_vista(request):
    """Guarda el diseño del portal desde la vista previa («Usar este diseño»)."""
    from ..models import Colegio
    from ..permisos import es_admin_colegio
    colegio = request.colegio
    if not colegio or request.method != 'POST' or not es_admin_colegio(request.user, colegio):
        return redirect('notas:personalizacion_portal')
    diseno = request.POST.get('diseno')
    nombres = dict(Colegio.LAYOUT_CHOICES)
    if diseno in nombres:
        colegio.layout_portal = diseno
        colegio.save(update_fields=['layout_portal'])
        messages.success(request, f'El portal ahora usa el diseño «{nombres[diseno].split(":")[0]}».')
    return redirect('notas:portal')


# --- Recursos educativos del portal ---
@user_passes_test(es_admin_o_docente)
def gestion_recursos_vista(request, pk=None):
    """Agregar, editar, ocultar y quitar los recursos de «Recursos educativos»."""
    colegio = request.colegio
    if not colegio:
        return HttpResponseNotFound("<h1>Colegio no configurado</h1>")
    recurso = get_object_or_404(RecursoEducativo, pk=pk, colegio=colegio) if pk else None

    if request.method == 'POST':
        form = RecursoEducativoForm(request.POST, request.FILES, instance=recurso)
        if form.is_valid():
            nuevo = form.save(commit=False)
            nuevo.colegio = colegio
            nuevo.save()
            messages.success(request, f'Recurso «{nuevo.titulo}» guardado. Ya sale en el portal.' if nuevo.visible
                             else f'Recurso «{nuevo.titulo}» guardado (oculto en el portal).')
            return redirect('notas:gestion_recursos')
    else:
        form = RecursoEducativoForm(instance=recurso)

    recursos = RecursoEducativo.objects.filter(colegio=colegio)
    categorias = sorted({r.categoria for r in recursos if r.categoria})
    return render(request, 'notas/admin_portal/gestion_recursos.html', {
        'form': form, 'recurso': recurso, 'recursos': recursos, 'categorias': categorias,
        'page_title': 'Recursos educativos', 'colegio': colegio})


@user_passes_test(es_admin_o_docente)
def eliminar_recurso_vista(request, pk):
    if not request.colegio:
        return HttpResponseNotFound("<h1>Colegio no configurado</h1>")
    recurso = get_object_or_404(RecursoEducativo, pk=pk, colegio=request.colegio)
    if request.method == 'POST':
        recurso.delete()
        messages.success(request, 'Recurso eliminado.')
    return redirect('notas:gestion_recursos')


# --- Videos del portal ---
def _personal_del_colegio(request):
    """Administrativos y docentes de ESTE colegio (no basta con ser docente de otro)."""
    from ..models import Docente
    if not request.user.is_authenticated or not request.colegio:
        return False
    return es_admin(request) or Docente.objects.filter(user=request.user, colegio=request.colegio).exists()


def _puede_editar_video(request, video):
    return es_admin(request) or video.autor_id == request.user.id


def gestion_videos_vista(request, pk=None):
    """Publicar videos en el portal pegando el enlace (YouTube, Vimeo, Drive o Facebook)."""
    from django.core.exceptions import PermissionDenied
    colegio = request.colegio
    if not colegio:
        return HttpResponseNotFound("<h1>Colegio no configurado</h1>")
    if not _personal_del_colegio(request):
        raise PermissionDenied
    video = get_object_or_404(VideoPortal, pk=pk, colegio=colegio) if pk else None
    if video and not _puede_editar_video(request, video):
        raise PermissionDenied

    if request.method == 'POST':
        form = VideoPortalForm(request.POST, instance=video)
        if form.is_valid():
            nuevo = form.save(commit=False)
            nuevo.colegio = colegio
            if not nuevo.autor_id:
                nuevo.autor = request.user
            nuevo.save()
            messages.success(request, f'Video «{nuevo.titulo}» guardado.' +
                             (' Ya se ve en el portal.' if nuevo.visible else ' Quedó sin publicar.'))
            return redirect('notas:gestion_videos')
    else:
        form = VideoPortalForm(instance=video)

    videos = VideoPortal.objects.filter(colegio=colegio).select_related('autor')
    for v in videos:
        v.editable = _puede_editar_video(request, v)
    return render(request, 'notas/admin_portal/gestion_videos.html', {
        'form': form, 'video': video, 'videos': videos, 'page_title': 'Videos del portal', 'colegio': colegio})


def eliminar_video_vista(request, pk):
    from django.core.exceptions import PermissionDenied
    if not request.colegio:
        return HttpResponseNotFound("<h1>Colegio no configurado</h1>")
    if not _personal_del_colegio(request):
        raise PermissionDenied
    video = get_object_or_404(VideoPortal, pk=pk, colegio=request.colegio)
    if not _puede_editar_video(request, video):
        raise PermissionDenied
    if request.method == 'POST':
        video.delete()
        messages.success(request, 'Video eliminado.')
    return redirect('notas:gestion_videos')
