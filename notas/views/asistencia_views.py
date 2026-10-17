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
    # Sin ficha no hay correo del acudiente (antes eso daba error y no se guardaba la inasistencia).
    ficha = getattr(estudiante, 'ficha', None) if hasattr(estudiante, 'ficha') else None
    acudiente_email = getattr(ficha, 'email_acudiente', None)
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

    # Asistencia por hora: solo si el colegio tiene un horario publicado.
    # Sin horario, la pantalla funciona exactamente como antes.
    clases_hoy, clase_ahora = _clases_del_horario(request, docente_actual, fecha_obj)
    if clases_hoy:
        ids = {a.id for a in asignaciones_docente}
        extra = [c['asignacion'] for c in clases_hoy if c['asignacion'].id not in ids]
        if extra:
            asignaciones_docente = list(asignaciones_docente) + extra
        if not asignacion_id and clase_ahora and 'asignacion_id' not in request.GET:
            asignacion_id = str(clase_ahora['asignacion'].id)

    if asignacion_id:
        try:
            asignacion_actual = get_object_or_404(AsignacionDocente, id=asignacion_id, colegio=request.colegio)
            if (not es_admin(request) and asignacion_actual.docente != docente_actual
                    and not _cubre_reemplazo(request, docente_actual, asignacion_actual, fecha_obj)):
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
        'clases_hoy': clases_hoy,
        'clase_ahora': clase_ahora,
    }
    return render(request, 'notas/docente/asistencia.html', context)


def _clases_del_horario(request, docente, fecha):
    """Las clases del docente ese día según el horario publicado, y la que está en curso.

    Devuelve ([], None) si el módulo de horarios está apagado, si no hay horario
    publicado o si algo falla: la toma de asistencia nunca se rompe por esto.
    """
    if not docente:
        return [], None
    try:
        from ..modulos import esta_activo
        if not esta_activo(request.colegio, 'horarios'):
            return [], None
        from horarios import reemplazos
        clases = reemplazos.clases_de_hoy(request.colegio, docente, fecha)
        ahora = None
        if clases and fecha == timezone.localdate():
            ahora = reemplazos.clase_en_curso(clases, timezone.localtime().time())
        return clases, ahora
    except Exception:
        return [], None


def _cubre_reemplazo(request, docente, asignacion, fecha):
    try:
        from horarios import reemplazos
        return reemplazos.puede_tomar_asistencia(request.colegio, docente, asignacion, fecha)
    except Exception:
        return False

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
        try:
            fecha_permiso = datetime.strptime(fecha_str, '%Y-%m-%d').date()
        except (TypeError, ValueError):
            fecha_permiso = None
        if (not es_admin(request) and asignacion.docente != docente_actual
                and not (fecha_permiso and _cubre_reemplazo(request, docente_actual, asignacion, fecha_permiso))):
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
