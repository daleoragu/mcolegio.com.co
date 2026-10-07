# notas/views/asistencia_views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseNotFound
from django.utils import timezone
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
import json
from datetime import datetime

from ..models import Docente, AsignacionDocente, Estudiante, Asistencia
from ..permisos import es_admin, es_admin_usuario

def _enviar_correo_inasistencia(estudiante, asignacion, fecha):
    # Esta función auxiliar no necesita cambios, ya que recibe objetos ya filtrados.
    acudiente_email = getattr(estudiante.ficha, 'email_acudiente', None)
    if not acudiente_email:
        return

    contexto_email = {'estudiante': estudiante, 'asignacion': asignacion, 'fecha': fecha}
    asunto = f"Reporte de Inasistencia - {estudiante.user.get_full_name()}"
    try:
        # Todo dentro del try: antes la versión .txt no existía y el error
        # hacía que guardar la asistencia respondiera con error 500.
        from django.utils.html import strip_tags
        html_mensaje = render_to_string('notas/emails/inasistencia_email.html', contexto_email)
        texto_plano = strip_tags(html_mensaje)
        send_mail(asunto, texto_plano, settings.DEFAULT_FROM_EMAIL, [acudiente_email], html_message=html_mensaje)
    except Exception as e:
        print(f"ERROR al enviar correo de inasistencia para {estudiante}: {e}")

@login_required
def asistencia_vista(request):
    """
    Gestiona la interfaz para el registro de asistencia diaria, asegurando
    que los datos correspondan al colegio actual.
    """
    if not request.colegio:
        return HttpResponseNotFound("<h1>Colegio no configurado</h1>")

    docente_actual = Docente.objects.filter(user=request.user, colegio=request.colegio).first()
    if not docente_actual and not es_admin(request):
        messages.error(request, "Acceso denegado. Su usuario no está asociado a un perfil de docente en este colegio.")
        return redirect('notas:dashboard')

    if es_admin(request):
        asignaciones_docente = AsignacionDocente.objects.filter(colegio=request.colegio).select_related('curso', 'materia').order_by('curso__nombre', 'materia__nombre')
    else:
        asignaciones_docente = AsignacionDocente.objects.filter(docente=docente_actual, colegio=request.colegio).select_related('curso', 'materia').order_by('curso__nombre', 'materia__nombre')

    estudiantes_del_curso, asistencias_map, mostrar_lista = [], {}, False
    asignacion_id = request.GET.get('asignacion_id')
    fecha_str = request.GET.get('fecha', timezone.localdate().strftime('%Y-%m-%d'))
    
    try:
        fecha_obj = datetime.strptime(fecha_str, '%Y-%m-%d').date()
    except ValueError:
        fecha_obj = timezone.localdate()
        fecha_str = fecha_obj.strftime('%Y-%m-%d')
        messages.warning(request, "Fecha no válida, se ha usado la fecha de hoy.")

    if asignacion_id:
        try:
            asignacion_actual = get_object_or_404(AsignacionDocente, id=asignacion_id, colegio=request.colegio)
            if not es_admin(request) and asignacion_actual.docente != docente_actual:
                raise AsignacionDocente.DoesNotExist
            
            mostrar_lista = True
            estudiantes_del_curso = Estudiante.objects.filter(
                curso=asignacion_actual.curso, colegio=request.colegio, is_active=True
            ).order_by('user__last_name', 'user__first_name')
            
            asistencias_hoy = Asistencia.objects.filter(asignacion=asignacion_actual, fecha=fecha_obj, colegio=request.colegio)
            asistencias_map = {a.estudiante_id: a.estado for a in asistencias_hoy}
        except AsignacionDocente.DoesNotExist:
            messages.warning(request, "La asignación seleccionada no es válida.")

    context = {
        'colegio': request.colegio,
        'asignaciones': asignaciones_docente,
        'estudiantes': estudiantes_del_curso,
        'asistencias_map': asistencias_map,
        'asignacion_seleccionada_id': asignacion_id,
        'fecha_seleccionada': fecha_str,
        'mostrar_lista': mostrar_lista,
    }
    return render(request, 'notas/docente/asistencia.html', context)

@login_required
def guardar_inasistencia_ajax(request):
    """
    Guarda el estado de asistencia de un estudiante vía AJAX, asegurando
    que la operación se realice en el colegio correcto.
    """
    if not request.colegio:
        return JsonResponse({'status': 'error', 'message': 'Colegio no identificado'}, status=404)
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Método no permitido'}, status=405)

    try:
        data = json.loads(request.body)
        estudiante_id = data.get('estudiante_id')
        asignacion_id = data.get('asignacion_id')
        fecha_str = data.get('fecha')
        estado = data.get('estado')

        asignacion = get_object_or_404(AsignacionDocente, id=asignacion_id, colegio=request.colegio)
        estudiante = get_object_or_404(Estudiante, id=estudiante_id, colegio=request.colegio)
        
        docente_actual = Docente.objects.filter(user=request.user, colegio=request.colegio).first()
        if not es_admin(request) and asignacion.docente != docente_actual:
             return JsonResponse({'status': 'error', 'message': 'Permiso denegado'}, status=403)

        asistencia_obj, created = Asistencia.objects.update_or_create(
            colegio=request.colegio,
            estudiante=estudiante,
            asignacion=asignacion,
            fecha=fecha_str,
            defaults={'estado': estado}
        )

        if estado == 'A' and created:
            _enviar_correo_inasistencia(estudiante, asignacion, fecha_str)

        return JsonResponse({'status': 'success', 'message': 'Asistencia guardada.'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
