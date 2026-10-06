# notas/views/carnet_views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import HttpResponse, HttpResponseNotFound, HttpResponseForbidden
from django.urls import reverse
from django.contrib import messages
from django.utils import timezone
import qrcode
import base64
from io import BytesIO

from ..models.perfiles import Estudiante, Docente, Colegio, Curso
from ..models.academicos import AsignacionDocente, Asistencia
from ..permisos import es_admin, es_admin_usuario

# --- FUNCIÓN DE PERMISOS ---
def es_admin_del_colegio(user):
    """Superusuario o administrador de ESTE colegio (ver notas/permisos.py)."""
    return es_admin_usuario(user)

# ==============================================================================
# VISTA PARA GENERAR EL CARNET INDIVIDUAL
# ==============================================================================

@login_required
def generar_carnet_estudiante(request, estudiante_id):
    if not request.colegio:
        return HttpResponseNotFound("<h1>Colegio no configurado</h1>")

    estudiante = get_object_or_404(Estudiante, id=estudiante_id, colegio=request.colegio)
    
    qr_url = request.build_absolute_uri(
        reverse('registrar_asistencia_qr', args=[estudiante.id])
    )
    
    qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=10, border=4)
    qr.add_data(qr_url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    qr_img_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')

    context = {
        'colegio': request.colegio,
        'estudiante': estudiante,
        'qr_image': qr_img_base64,
    }
    return render(request, 'notas/docente/carnet_estudiante.html', context)

# ==============================================================================
# VISTA PARA IMPRESIÓN MASIVA DE CARNETS
# ==============================================================================

@login_required
@user_passes_test(es_admin_del_colegio, login_url='/admin/login/')
def impresion_masiva_carnets(request):
    if not request.colegio:
        return HttpResponseNotFound("<h1>Colegio no configurado</h1>")

    cursos = Curso.objects.filter(colegio=request.colegio).order_by('nombre')
    
    curso_seleccionado_id = request.GET.get('curso_id')
    if curso_seleccionado_id:
        estudiantes = Estudiante.objects.filter(colegio=request.colegio, curso_id=curso_seleccionado_id, is_active=True)
    else:
        estudiantes = Estudiante.objects.filter(colegio=request.colegio, is_active=True)

    for estudiante in estudiantes:
        qr_url = request.build_absolute_uri(reverse('notas:registrar_asistencia_qr', args=[estudiante.id]))
        qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=6, border=2)
        qr.add_data(qr_url)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        
        buffered = BytesIO()
        img.save(buffered, format="PNG")
        estudiante.qr_image_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')

    context = {
        'colegio': request.colegio,
        'estudiantes': estudiantes,
        'cursos': cursos,
        'curso_seleccionado_id': curso_seleccionado_id,
    }
    
    # --- INICIO: CORRECCIÓN DE RUTA ---
    # Se actualiza la ruta para que coincida con la nueva ubicación del archivo.
    return render(request, 'notas/admin_tools/impresion_masiva_carnets.html', context)
    # --- FIN: CORRECCIÓN DE RUTA ---


# ==============================================================================
# VISTAS PARA EL MODO "KIOSKO"
# ==============================================================================

@login_required
def vista_kiosko_asistencia(request):
    if not request.colegio:
        return HttpResponseNotFound("<h1>Colegio no configurado</h1>")

    if es_admin(request):
        asignaciones = AsignacionDocente.objects.filter(colegio=request.colegio)
    else:
        docente_actual = get_object_or_404(Docente, user=request.user, colegio=request.colegio)
        asignaciones = AsignacionDocente.objects.filter(docente=docente_actual, colegio=request.colegio)

    if request.method == 'POST':
        asignacion_id = request.POST.get('asignacion_id')
        if asignacion_id:
            request.session['kiosko_asignacion_id'] = asignacion_id
        elif 'finalizar' in request.POST:
            request.session.pop('kiosko_asignacion_id', None)
        return redirect('notas:vista_kiosko_asistencia')

    context = {'colegio': request.colegio, 'asignaciones': asignaciones, 'asignacion_activa': None}
    kiosko_asignacion_id = request.session.get('kiosko_asignacion_id')
    if kiosko_asignacion_id:
        try:
            asignacion_activa = AsignacionDocente.objects.get(id=kiosko_asignacion_id, colegio=request.colegio)
            context['asignacion_activa'] = asignacion_activa
            context['asistencias_recientes'] = Asistencia.objects.filter(
                asignacion=asignacion_activa, fecha=timezone.now().date()
            ).order_by('-id')[:5]
        except AsignacionDocente.DoesNotExist:
            request.session.pop('kiosko_asignacion_id', None)

    return render(request, 'notas/docente/kiosko_asistencia.html', context)


@login_required
def registrar_asistencia_qr(request, estudiante_id):
    if not request.colegio:
        messages.error(request, "Error de configuración: Colegio no identificado.")
        return redirect('notas:vista_kiosko_asistencia')

    asignacion_id = request.session.get('kiosko_asignacion_id')
    if not asignacion_id:
        messages.error(request, "No hay una clase activa para registrar la asistencia.")
        return redirect('notas:vista_kiosko_asistencia')

    try:
        estudiante = get_object_or_404(Estudiante, id=estudiante_id, colegio=request.colegio)
        asignacion = get_object_or_404(AsignacionDocente, id=asignacion_id, colegio=request.colegio)

        if estudiante.curso != asignacion.curso:
            messages.warning(request, f"Acción denegada: {estudiante} no pertenece al curso {asignacion.curso}.")
            return redirect('notas: vista_kiosko_asistencia')

        asistencia, created = Asistencia.objects.update_or_create(
            colegio=request.colegio,
            estudiante=estudiante,
            asignacion=asignacion,
            fecha=timezone.now().date(),
            defaults={'estado': 'P'}
        )

        if created:
            messages.success(request, f"Asistencia de {estudiante} registrada correctamente.")
        else:
            messages.info(request, f"La asistencia de {estudiante} ya había sido registrada hoy.")

    except (Estudiante.DoesNotExist, AsignacionDocente.DoesNotExist):
        messages.error(request, "Error: Estudiante o asignación de clase no válidos.")
    except Exception as e:
        messages.error(request, f"Ocurrió un error inesperado: {e}")

    return redirect('notas:vista_kiosko_asistencia')
