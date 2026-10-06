# notas/views/consulta_views.py

from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.utils import timezone
from collections import defaultdict
from datetime import datetime
# Se añade HttpResponseNotFound para manejar el caso de un colegio no identificado
from django.http import HttpResponseNotFound, JsonResponse
from calendar import month_name
import locale

from ..models import Docente, AsignacionDocente, Estudiante, Asistencia, PeriodoAcademico, Curso
from ..permisos import es_admin, es_admin_usuario

@login_required
def consulta_asistencia_vista(request):
    """
    Permite a los docentes y administradores consultar el historial de asistencias de un curso completo
    para una fecha específica, asegurando que todos los datos correspondan al colegio actual.
    """
    # CORRECCIÓN: Verificar que se ha identificado un colegio.
    if not request.colegio:
        return HttpResponseNotFound("<h1>Colegio no configurado</h1>")

    context = {'colegio': request.colegio}
    user = request.user
    docente_seleccionado_id = request.GET.get('docente_id')
    asignacion_id = request.GET.get('asignacion_id')
    fecha_consulta_str = request.GET.get('fecha_consulta', timezone.now().strftime('%Y-%m-%d'))
    
    # Lógica para determinar qué asignaciones mostrar
    if es_admin_usuario(user):
        # CORRECCIÓN: Filtrar docentes y asignaciones por el colegio actual.
        context['todos_los_docentes'] = Docente.objects.filter(colegio=request.colegio).order_by('user__last_name', 'user__first_name')
        if docente_seleccionado_id:
            asignaciones_docente = AsignacionDocente.objects.filter(docente_id=docente_seleccionado_id, colegio=request.colegio)
        else:
            asignaciones_docente = AsignacionDocente.objects.filter(colegio=request.colegio)
    else:
        try:
            # CORRECCIÓN: Asegurar que se obtiene el docente del colegio actual.
            docente_actual = Docente.objects.get(user=user, colegio=request.colegio)
            asignaciones_docente = AsignacionDocente.objects.filter(docente=docente_actual, colegio=request.colegio)
            context['docente_actual'] = docente_actual
        except Docente.DoesNotExist:
            messages.error(request, "Acceso denegado. Su usuario no está asociado a un perfil de docente en este colegio.")
            return redirect('notas:dashboard')

    # Variables de contexto para el historial
    curso_seleccionado = None
    estudiantes_del_curso = []
    asignaturas_del_curso = []
    matriz_asistencia = defaultdict(lambda: defaultdict(str))
    
    try:
        fecha_consulta = datetime.strptime(fecha_consulta_str, '%Y-%m-%d').date()
    except ValueError:
        fecha_consulta = timezone.now().date()
        messages.warning(request, "Formato de fecha no válido, se usó la fecha de hoy.")

    if asignacion_id:
        try:
            # CORRECCIÓN: Asegurar que la asignación seleccionada pertenece al colegio actual.
            asignacion_seleccionada = AsignacionDocente.objects.select_related('curso').get(id=asignacion_id, colegio=request.colegio)
            curso_seleccionado = asignacion_seleccionada.curso
            
            # CORRECCIÓN: Filtrar estudiantes por colegio.
            estudiantes_del_curso = Estudiante.objects.filter(
                curso=curso_seleccionado, colegio=request.colegio, is_active=True
            ).order_by('user__last_name', 'user__first_name')
            
            # CORRECCIÓN: Filtrar asignaturas por colegio.
            asignaturas_del_curso = AsignacionDocente.objects.filter(
                curso=curso_seleccionado, colegio=request.colegio
            ).select_related('materia').order_by('materia__nombre')
            
            # CORRECCIÓN: Filtrar asistencias por colegio.
            asistencias_del_dia = Asistencia.objects.filter(
                estudiante__in=estudiantes_del_curso,
                fecha=fecha_consulta,
                colegio=request.colegio
            ).select_related('estudiante', 'asignacion')
            
            for asistencia in asistencias_del_dia:
                estado = 'AJ' if asistencia.justificada and asistencia.estado == 'A' else asistencia.estado
                matriz_asistencia[asistencia.estudiante_id][asistencia.asignacion_id] = estado

        except AsignacionDocente.DoesNotExist:
            messages.error(request, "La asignación seleccionada no es válida o no pertenece a este colegio.")
    
    context.update({
        'asignaciones': asignaciones_docente.select_related('curso', 'materia'),
        'asignacion_seleccionada_id': asignacion_id,
        'docente_seleccionado_id': docente_seleccionado_id,
        'curso_seleccionado': curso_seleccionado,
        'estudiantes_del_curso': estudiantes_del_curso,
        'asignaturas_del_curso': asignaturas_del_curso,
        'matriz_asistencia': matriz_asistencia,
        'fecha_consulta': fecha_consulta,
        # CORRECCIÓN: Filtrar periodos académicos por colegio.
        'periodos_academicos': PeriodoAcademico.objects.filter(colegio=request.colegio).order_by('-ano_lectivo', 'nombre'),
    })

    return render(request, 'notas/docente/consulta_asistencia.html', context)

# ==================================================================
# INICIO DE LA CORRECCIÓN
# Se añade la función que faltaba para la llamada AJAX.
# ==================================================================
def ajax_obtener_meses_vista(request):
    """
    Vista AJAX que devuelve los meses de un periodo académico en formato JSON.
    """
    periodo_id = request.GET.get('periodo_id')
    
    # Configura el idioma a español para los nombres de los meses
    try:
        # Para sistemas basados en Unix (Linux, macOS)
        locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8')
    except locale.Error:
        # Alternativa para sistemas Windows
        locale.setlocale(locale.LC_TIME, 'Spanish_Spain.1252')

    if not periodo_id:
        return JsonResponse({'error': 'No se proporcionó ID de periodo'}, status=400)

    try:
        periodo = PeriodoAcademico.objects.get(id=periodo_id, colegio=request.colegio)
        
        meses = []
        fecha_actual = periodo.fecha_inicio
        
        # Itera desde la fecha de inicio hasta la fecha de fin del periodo
        while fecha_actual <= periodo.fecha_fin:
            # Crea una tupla (numero_mes, nombre_mes)
            mes_tupla = (fecha_actual.month, month_name[fecha_actual.month].capitalize())
            
            # Añade el mes a la lista solo si no ha sido añadido antes
            if mes_tupla not in meses:
                meses.append(mes_tupla)
            
            # Avanza al primer día del siguiente mes
            # Esto evita problemas con meses de diferente duración
            if fecha_actual.month == 12:
                fecha_actual = fecha_actual.replace(year=fecha_actual.year + 1, month=1, day=1)
            else:
                fecha_actual = fecha_actual.replace(month=fecha_actual.month + 1, day=1)

        return JsonResponse({'meses': meses})

    except PeriodoAcademico.DoesNotExist:
        return JsonResponse({'error': 'Periodo no encontrado'}, status=404)
    except Exception as e:
        # Captura cualquier otro error inesperado
        return JsonResponse({'error': str(e)}, status=500)
# ==================================================================
# FIN DE LA CORRECCIÓN
# ==================================================================
