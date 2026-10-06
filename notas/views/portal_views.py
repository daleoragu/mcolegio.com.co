# notas/views/portal_views.py

from django.http import JsonResponse, HttpResponseNotFound, HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.db.models import Prefetch
from django.urls import reverse
from django.template.loader import render_to_string


# Se importan todos los modelos necesarios
from ..models import (
    Docente, Estudiante, Curso, AsignacionDocente, 
    DocumentoPublico, FotoGaleria, Noticia, ImagenCarrusel, 
    Colegio
)
from ..permisos import pertenece_al_colegio

# Extensiones que se aceptan para las imágenes de la portada. Así da igual si
# el archivo quedó guardado como .png, .jpg o .webp: igual lo encuentra.
_EXTENSIONES_IMAGEN = ('.png', '.jpg', '.jpeg', '.webp', '.PNG', '.JPG', '.JPEG')


def _buscar_estatico(nombre_sin_extension, carpeta='img'):
    """Busca una imagen en los estáticos y devuelve (url, diagnóstico).

    Devuelve la URL si la encuentra. Si no, devuelve None y un texto que
    explica qué se buscó y dónde, para que el marcador de la portada pueda
    decirlo en vez de quedarse mudo.

    Hay dos modos y los dos importan:
      - En desarrollo los archivos se leen directo de las carpetas 'static/'.
      - En producción solo existe lo que 'collectstatic' haya recogido; pedir
        algo que no esté recogido lanza "Missing staticfiles manifest entry"
        y tumbaría la página entera, así que aquí se atrapa siempre.
    """
    from django.conf import settings
    from django.contrib.staticfiles import finders
    from django.contrib.staticfiles.storage import staticfiles_storage
    from django.templatetags.static import static

    intentados = []
    for ext in _EXTENSIONES_IMAGEN:
        ruta = f'{carpeta}/{nombre_sin_extension}{ext}'
        intentados.append(ruta)

        # ¿Está en alguna carpeta 'static/' del proyecto? (modo desarrollo)
        encontrado = finders.find(ruta) is not None
        # ¿O ya fue recogido por collectstatic? (modo producción)
        if not encontrado:
            try:
                encontrado = staticfiles_storage.exists(ruta)
            except Exception:
                encontrado = False

        if encontrado:
            try:
                return static(ruta), None
            except Exception:
                # El archivo está en disco pero no en el índice: falta collectstatic.
                return None, (
                    f'Encontré "{ruta}" en disco, pero no está recogido. '
                    f'Corre: python manage.py collectstatic'
                )

    aviso = 'Guarda la imagen como ' + intentados[0]
    if settings.DEBUG:
        aviso += f' (busqué también: {", ".join(intentados[1:4])}…)'
    return None, aviso


def portal_vista(request):
    """
    Renderiza el portal público.
    - Si el request está asociado a un colegio (middleware), muestra el portal de ese colegio.
    - Si no, muestra una página de bienvenida con la lista de todos los colegios.
    """
    colegio_actual = getattr(request, 'colegio', None)
    
    if colegio_actual:
        if request.method == 'POST':
            username = request.POST.get('username')
            password = request.POST.get('password')
            user = authenticate(request, username=username, password=password)
            if user is not None:
                # Se verifica que el usuario pertenezca al colegio correcto
                # Docente, estudiante o administrador de ESTE colegio, o el
                # superusuario. Un administrador de otro colegio no entra.
                if pertenece_al_colegio(user, colegio_actual):
                    login(request, user)
                    return redirect('notas:dashboard')
                else:
                    messages.error(request, "El usuario no pertenece a este colegio.")
            else:
                messages.error(request, "Usuario o contraseña incorrectos.")
        
        context = {'colegio': colegio_actual}
        return render(request, 'notas/portal.html', context)
    else:
        todos_los_colegios = Colegio.objects.all()
        url_hero, aviso_hero = _buscar_estatico('hero-tablero')
        url_docente, aviso_docente = _buscar_estatico('docente')
        return render(request, 'landing/index.html', {
            'colegios': todos_los_colegios,
            # Si la imagen no está, llega None y el marcador dice por qué.
            'imagen_hero': url_hero, 'aviso_hero': aviso_hero,
            'imagen_docente': url_docente, 'aviso_docente': aviso_docente,
        })

# --- VISTAS AJAX PARA CARGAR CONTENIDO DINÁMICO EN EL PORTAL ---

def ajax_galeria_vista(request):
    """
    Obtiene las fotos de la galería del colegio y las renderiza en una plantilla HTML.
    """
    if not request.colegio:
        return HttpResponseNotFound("<h1>Colegio no configurado</h1>")
    
    try:
        fotos = FotoGaleria.objects.filter(colegio=request.colegio).order_by('-fecha_subida')
        context = {'fotos': fotos, 'colegio': request.colegio}
        return render(request, 'notas/portal_components/_galeria_content.html', context)
    except Exception as e:
        return HttpResponse(f"<p class='text-center text-danger'>Error al cargar la galería: {e}</p>", status=500)

def directorio_docentes_json(request):
    """
    Devuelve en formato JSON la lista de docentes del colegio con sus asignaturas.
    """
    if not request.colegio:
        return JsonResponse({'error': 'Colegio no encontrado'}, status=404)
    
    try:
        cursos_con_director = Curso.objects.filter(colegio=request.colegio, director_grado__isnull=False).select_related('director_grado')
        directores_map = {c.director_grado.id: c.nombre for c in cursos_con_director}

        docentes = Docente.objects.filter(colegio=request.colegio, user__is_active=True).prefetch_related(
            Prefetch(
                'asignaciondocente_set',
                queryset=AsignacionDocente.objects.filter(colegio=request.colegio).select_related('curso', 'materia'),
                to_attr='asignaciones_optimizadas'
            )
        ).order_by('user__last_name', 'user__first_name')

        data_docentes = []
        for docente in docentes:
            materias_grados = {}
            if hasattr(docente, 'asignaciones_optimizadas'):
                for asignacion in docente.asignaciones_optimizadas:
                    materia_nombre = asignacion.materia.nombre
                    grado_nombre = asignacion.curso.nombre
                    if materia_nombre not in materias_grados:
                        materias_grados[materia_nombre] = set()
                    materias_grados[materia_nombre].add(grado_nombre)
            
            asignaturas_str = "; ".join([f"{materia} ({', '.join(sorted(list(grados)))})" for materia, grados in materias_grados.items()])

            data_docentes.append({
                'nombre_completo': docente.user.get_full_name() or docente.user.username,
                'asignaturas': asignaturas_str if asignaturas_str else "Sin asignaturas",
                'direccion_grupo': directores_map.get(docente.id, "No aplica")
            })

        return JsonResponse(data_docentes, safe=False)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


def documentos_publicos_json(request):
    """
    Devuelve en formato JSON los documentos públicos del colegio.
    """
    if not request.colegio:
        return JsonResponse({'error': 'Colegio no encontrado'}, status=404)
    documentos = DocumentoPublico.objects.filter(colegio=request.colegio).order_by('-fecha_publicacion')
    data = [{'titulo': doc.titulo, 'descripcion': doc.descripcion, 'url_archivo': doc.archivo.url, 'fecha': doc.fecha_publicacion.strftime('%d de %B, %Y')} for doc in documentos]
    return JsonResponse(data, safe=False)

def noticias_json(request):
    """
    Devuelve en formato JSON las últimas 5 noticias publicadas del colegio.
    """
    if not request.colegio:
        return JsonResponse({'error': 'Colegio no encontrado'}, status=404)
    noticias = Noticia.objects.filter(colegio=request.colegio, estado='PUBLICADO').order_by('-fecha_publicacion')[:5]
    data = [
        {'pk': n.pk, 'titulo': n.titulo, 'resumen': n.resumen, 'url_imagen': n.imagen_portada.url if n.imagen_portada else '', 'fecha': n.fecha_publicacion.strftime('%d de %B, %Y')}
        for n in noticias
    ]
    return JsonResponse(data, safe=False)

def carrusel_imagenes_json(request):
    """
    Devuelve en formato JSON las imágenes visibles del carrusel del colegio.
    """
    if not request.colegio:
        return JsonResponse({'error': 'Colegio no encontrado'}, status=404)
    imagenes = ImagenCarrusel.objects.filter(colegio=request.colegio, visible=True).order_by('orden')
    data = [{'url_imagen': img.imagen.url, 'titulo': img.titulo, 'subtitulo': img.subtitulo} for img in imagenes]
    return JsonResponse(data, safe=False)

def ajax_noticia_detalle(request, pk):
    """
    Renderiza el detalle de una noticia específica del colegio.
    """
    if not request.colegio:
        return HttpResponseNotFound("<h1>Colegio no configurado</h1>")
    noticia = get_object_or_404(Noticia, pk=pk, estado='PUBLICADO', colegio=request.colegio)
    return render(request, 'notas/portal_components/_contenido_noticia_detalle.html', {'noticia': noticia})

def ajax_historia(request):
    """
    Renderiza el contenido de la historia del colegio.
    """
    return render(request, 'notas/portal_components/_contenido_historia.html', {'colegio': request.colegio})

def ajax_mision_vision(request):
    """
    Renderiza el contenido de la misión y visión del colegio.
    """
    return render(request, 'notas/portal_components/_contenido_mision_vision.html', {'colegio': request.colegio})

def ajax_modelo_pedagogico(request):
    """
    Renderiza el contenido del modelo pedagógico del colegio.
    """
    return render(request, 'notas/portal_components/_contenido_modelo.html', {'colegio': request.colegio})

def ajax_recursos_educativos(request):
    """
    Placeholder para la vista de recursos educativos.
    """
    return HttpResponse("<p class='text-center'>Sección de Recursos Educativos en construcción.</p>")

def ajax_redes_sociales(request):
    """
    Devuelve las redes sociales del colegio en formato JSON para ser usadas por JS.
    """
    if not request.colegio:
        return JsonResponse({'error': 'Colegio no encontrado'}, status=404)
    data = {
        'facebook': request.colegio.url_facebook,
        'instagram': request.colegio.url_instagram,
        'tiktok': request.colegio.url_tiktok,
        'youtube': request.colegio.url_youtube,
    }
    return JsonResponse(data)
