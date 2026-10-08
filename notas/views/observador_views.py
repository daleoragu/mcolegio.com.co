# notas/views/observador_views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import HttpResponse, HttpResponseNotFound
from django.template.loader import render_to_string
from django.urls import reverse

try:
    from weasyprint import HTML
    PDF_SUPPORT = True
except ImportError:
    PDF_SUPPORT = False

from ..forms import RegistroObservadorForm, FichaEstudianteForm
from ..models import (
    Docente, Estudiante, Curso, FichaEstudiante, 
    AsignacionDocente, RegistroObservador, Notificacion
)
from ..permisos import es_admin, es_admin_usuario
from .. import avisos_familia

def es_docente_o_superuser(user):
    return es_admin_usuario(user) or user.groups.filter(name='Docentes').exists()

@login_required
@user_passes_test(es_docente_o_superuser)
def observador_selector_vista(request):
    if not request.colegio:
        return HttpResponseNotFound("<h1>Colegio no configurado</h1>")

    user = request.user
    cursos = []
    estudiantes = Estudiante.objects.none()

    if es_admin_usuario(user):
        cursos = Curso.objects.filter(colegio=request.colegio).order_by('nombre')
    else:
        try:
            docente = get_object_or_404(Docente, user=user, colegio=request.colegio)
            cursos_ids = AsignacionDocente.objects.filter(docente=docente, colegio=request.colegio).values_list('curso_id', flat=True).distinct()
            cursos = Curso.objects.filter(id__in=cursos_ids, colegio=request.colegio).order_by('nombre')
        except Docente.DoesNotExist:
            messages.error(request, "Su perfil no está asociado a un docente en este colegio.")
            return redirect('notas:dashboard')

    curso_seleccionado_id = request.GET.get('curso_id')
    if curso_seleccionado_id:
        estudiantes = Estudiante.objects.filter(
            curso_id=curso_seleccionado_id, colegio=request.colegio, is_active=True
        ).select_related('user', 'curso').order_by('user__last_name', 'user__first_name')

    if request.method == 'POST':
        estudiante_id = request.POST.get('estudiante_id')
        if estudiante_id:
            return redirect('notas:vista_detalle_observador', estudiante_id=estudiante_id)

    context = {
        'colegio': request.colegio,
        'cursos': cursos,
        'estudiantes': estudiantes,
        'curso_seleccionado_id': curso_seleccionado_id,
        'page_title': 'Seleccionar Estudiante para Observador'
    }
    return render(request, 'notas/observador/selector.html', context)

@login_required
@user_passes_test(es_docente_o_superuser)
def vista_detalle_observador(request, estudiante_id):
    if not request.colegio:
        return HttpResponseNotFound("<h1>Colegio no configurado</h1>")
        
    estudiante = get_object_or_404(Estudiante, id=estudiante_id, colegio=request.colegio)
    ficha, created = FichaEstudiante.objects.get_or_create(estudiante=estudiante)
    registros = RegistroObservador.objects.filter(estudiante=estudiante, colegio=request.colegio)
    
    context = {
        'colegio': request.colegio,
        'estudiante': estudiante,
        'ficha': ficha,
        'registros': registros,
        'page_title': f"Observador de {estudiante.user.get_full_name()}"
    }
    return render(request, 'notas/observador/detalle_observador.html', context)

@login_required
@user_passes_test(es_docente_o_superuser)
def crear_registro_observador_vista(request, estudiante_id):
    if not request.colegio:
        return HttpResponseNotFound("<h1>Colegio no configurado</h1>")
        
    estudiante = get_object_or_404(Estudiante, id=estudiante_id, colegio=request.colegio)
    docente = Docente.objects.filter(user=request.user, colegio=request.colegio).first()

    if request.method == 'POST':
        form = RegistroObservadorForm(request.POST)
        if form.is_valid():
            nuevo_registro = form.save(commit=False)
            nuevo_registro.colegio = request.colegio
            nuevo_registro.estudiante = estudiante
            nuevo_registro.docente_reporta = docente
            
            if nuevo_registro.tipo != 'COMPORTAMENTAL':
                nuevo_registro.subtipo = None
                
            nuevo_registro.save()
            
            try:
                url_destino = reverse('notas:mi_observador')
            except:
                url_destino = '#'

            Notificacion.objects.create(
                colegio=request.colegio,
                destinatario=estudiante.user,
                mensaje=f"Se ha registrado una nueva anotación {nuevo_registro.get_tipo_display()} en tu observador.",
                tipo='OBSERVADOR',
                url=url_destino
            )

            messages.success(request, f"Observación para {estudiante.user.get_full_name()} guardada correctamente.")
            # Aviso a la familia: el correo sale solo; el WhatsApp se envía
            # desde la pantalla siguiente con un toque.
            enviado, detalle = avisos_familia.enviar_correo(
                nuevo_registro, request.build_absolute_uri('/'), _url_respuesta(request, nuevo_registro))
            if enviado:
                messages.info(request, f"Se envió un aviso al correo del acudiente ({detalle}).")
            return redirect('notas:aviso_familia', registro_id=nuevo_registro.id)
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"Error en '{field.capitalize()}': {error}")
    else:
        form = RegistroObservadorForm()

    context = {
        'colegio': request.colegio,
        'form': form,
        'estudiante': estudiante,
        'page_title': f"Nueva Observación para {estudiante.user.get_full_name()}"
    }
    return render(request, 'notas/observador/crear_registro.html', context)


@login_required
@user_passes_test(es_docente_o_superuser)
def editar_registro_observador_vista(request, registro_id):
    if not request.colegio:
        return HttpResponseNotFound("<h1>Colegio no configurado</h1>")
        
    registro = get_object_or_404(RegistroObservador, id=registro_id, colegio=request.colegio)
    estudiante = registro.estudiante
    
    # Validar que sea el creador de la nota o un administrador
    es_autor = registro.docente_reporta and registro.docente_reporta.user == request.user
    if not (es_autor or es_admin(request)):
        messages.error(request, "No tienes permiso para editar esta observación. Solo el autor puede hacerlo.")
        return redirect('notas:vista_detalle_observador', estudiante_id=estudiante.id)

    if request.method == 'POST':
        form = RegistroObservadorForm(request.POST, instance=registro)
        if form.is_valid():
            registro_actualizado = form.save(commit=False)
            if registro_actualizado.tipo != 'COMPORTAMENTAL':
                registro_actualizado.subtipo = None
            registro_actualizado.save()
            
            messages.success(request, "Observación actualizada correctamente.")
            return redirect('notas:vista_detalle_observador', estudiante_id=estudiante.id)
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"Error en '{field.capitalize()}': {error}")
    else:
        form = RegistroObservadorForm(instance=registro)

    context = {
        'colegio': request.colegio,
        'form': form,
        'estudiante': estudiante,
        'registro': registro,
        'page_title': f"Editar Observación de {estudiante.user.get_full_name()}"
    }
    return render(request, 'notas/observador/editar_registro.html', context)

@login_required
@user_passes_test(es_docente_o_superuser)
def eliminar_registro_observador_vista(request, registro_id):
    if not request.colegio:
        return HttpResponseNotFound("<h1>Colegio no configurado</h1>")
        
    registro = get_object_or_404(RegistroObservador, id=registro_id, colegio=request.colegio)
    estudiante = registro.estudiante
    
    es_autor = registro.docente_reporta and registro.docente_reporta.user == request.user
    if not (es_autor or es_admin(request)):
        messages.error(request, "No tienes permiso para eliminar esta observación.")
        return redirect('notas:vista_detalle_observador', estudiante_id=estudiante.id)

    if request.method == 'POST':
        registro.delete()
        messages.success(request, "La observación ha sido eliminada del historial.")
        
    return redirect('notas:vista_detalle_observador', estudiante_id=estudiante.id)


@login_required
@user_passes_test(es_docente_o_superuser)
def editar_ficha_vista(request, estudiante_id):
    if not request.colegio:
        return HttpResponseNotFound("<h1>Colegio no configurado</h1>")
        
    estudiante = get_object_or_404(Estudiante, id=estudiante_id, colegio=request.colegio)
    ficha, created = FichaEstudiante.objects.get_or_create(estudiante=estudiante)

    if request.method == 'POST':
        form = FichaEstudianteForm(request.POST, request.FILES, instance=ficha)
        if form.is_valid():
            form.save()
            messages.success(request, f"Ficha de {estudiante.user.get_full_name()} actualizada correctamente.")
            return redirect('notas:vista_detalle_observador', estudiante_id=estudiante.id)
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"Error en '{field.capitalize()}': {error}")
    else:
        form = FichaEstudianteForm(instance=ficha)
    
    context = {
        'colegio': request.colegio,
        'form': form,
        'estudiante': estudiante,
        'page_title': f"Editando Ficha de {estudiante.user.get_full_name()}"
    }
    return render(request, 'notas/observador/editar_ficha.html', context)

@login_required
@user_passes_test(es_docente_o_superuser)
def generar_observador_pdf_vista(request, estudiante_id):
    if not request.colegio:
        return HttpResponseNotFound("<h1>Colegio no configurado</h1>")
    if not PDF_SUPPORT:
        return HttpResponse("Error: El servidor no tiene instalada la librería WeasyPrint para generar PDFs.", status=500)
            
    estudiante = get_object_or_404(Estudiante, id=estudiante_id, colegio=request.colegio)
    ficha, _ = FichaEstudiante.objects.get_or_create(estudiante=estudiante)
    registros = RegistroObservador.objects.filter(estudiante=estudiante, colegio=request.colegio)

    # Creamos la URL absoluta para que WeasyPrint pueda ver y exportar la foto en el PDF
    foto_url = request.build_absolute_uri(ficha.foto.url) if ficha.foto and ficha.foto.name else None

    context = {
        'colegio': request.colegio,
        'estudiante': estudiante,
        'ficha': ficha,
        'foto_url': foto_url,
        'registros': registros,
    }
    
    html_string = render_to_string('notas/observador/observador_pdf.html', context)
    base_url = request.build_absolute_uri()
    
    try:
        pdf_file = HTML(string=html_string, base_url=base_url).write_pdf()
        response = HttpResponse(pdf_file, content_type='application/pdf')
        response['Content-Disposition'] = f'inline; filename="observador_{estudiante.user.username}.pdf"'
        return response
    except Exception as e:
        return HttpResponse(f"Error técnico al generar el PDF: {str(e)}", status=500)

@login_required
@user_passes_test(es_docente_o_superuser)
def aviso_familia_vista(request, registro_id):
    """Avisar a la familia de una anotación: botones de WhatsApp y correo."""
    if not request.colegio:
        return HttpResponseNotFound("<h1>Colegio no configurado</h1>")
    registro = get_object_or_404(RegistroObservador.objects.select_related('estudiante__user', 'colegio'),
                                 id=registro_id, colegio=request.colegio)
    url_portal = request.build_absolute_uri('/')
    if request.method == 'POST' and request.POST.get('accion') == 'correo':
        enviado, detalle = avisos_familia.enviar_correo(registro, url_portal,
                                                        _url_respuesta(request, registro))
        if enviado:
            messages.success(request, f"Aviso enviado al correo {detalle}.")
        else:
            messages.warning(request, f"No se envió el correo: {detalle}.")
        return redirect('notas:aviso_familia', registro_id=registro.id)

    texto = avisos_familia.texto_aviso(registro, url_portal)
    contactos = avisos_familia.contactos(registro.estudiante)
    for c in contactos:
        c['enlace'] = avisos_familia.enlace_whatsapp(c['numero'], texto)
    ficha = getattr(registro.estudiante, 'ficha', None)
    return render(request, 'notas/observador/aviso_familia.html', {
        'colegio': request.colegio, 'registro': registro, 'estudiante': registro.estudiante,
        'texto': texto, 'contactos': contactos,
        'correo_acudiente': getattr(ficha, 'email_acudiente', '') if ficha else '',
        'correo_configurado': avisos_familia.correo_configurado(),
        'page_title': 'Avisar a la familia',
    })


def _url_respuesta(request, registro):
    return request.build_absolute_uri(
        reverse('notas:respuesta_acudiente', args=[avisos_familia.token_respuesta(registro)]))


def respuesta_acudiente_vista(request, token):
    """Página del enlace del correo: el acudiente ve la anotación, se da por
    enterado y escribe su descargo. Sin usuario: el enlace firmado es la llave.
    """
    from django.db import transaction
    from django.utils import timezone

    registro, problema = avisos_familia.registro_de_token(token)
    if registro is not None and getattr(request, 'colegio', None) and registro.colegio_id != request.colegio.id:
        registro, problema = None, 'invalido'      # el enlace es de otro colegio
    contexto = {'registro': registro, 'problema': problema,
                'colegio': registro.colegio if registro else getattr(request, 'colegio', None)}
    if registro is None:
        return render(request, 'notas/observador/respuesta_acudiente.html', contexto, status=404)

    if request.method == 'POST' and not registro.acudiente_enterado:
        firma = ' '.join((request.POST.get('firma') or '').split())[:160]
        descargo = (request.POST.get('descargo') or '').strip()[:2000]
        if len(firma) < 5:
            contexto.update(error='Escriba su nombre completo.', firma=firma, descargo=descargo)
            return render(request, 'notas/observador/respuesta_acudiente.html', contexto)
        with transaction.atomic():
            registro.acudiente_enterado = timezone.now()
            registro.firma_acudiente = firma
            registro.descargo_acudiente = descargo
            registro.save(update_fields=['acudiente_enterado', 'firma_acudiente', 'descargo_acudiente'])
            # Le avisa a quien registró la anotación.
            if registro.docente_reporta_id:
                Notificacion.objects.create(
                    colegio=registro.colegio, destinatario=registro.docente_reporta.user, tipo='OBSERVADOR',
                    mensaje=(f"El acudiente de {registro.estudiante.user.get_full_name()} "
                             f"{'respondió' if descargo else 'se dio por enterado de'} la anotación "
                             f"del {registro.fecha_suceso:%d/%m/%Y}.")[:255],
                    url=reverse('notas:vista_detalle_observador', args=[registro.estudiante_id]))
        return redirect('notas:respuesta_acudiente', token=token)
    return render(request, 'notas/observador/respuesta_acudiente.html', contexto)
