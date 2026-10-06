# notas/views/reporte_parcial_views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseNotFound
from django.db.models import Q # Importar Q para consultas OR

from ..models import Docente, AsignacionDocente, PeriodoAcademico, Estudiante, ReporteParcial, Observacion, Notificacion, Calificacion, EscalaValoracion, Materia, Curso, Colegio
from ..permisos import es_admin, es_admin_usuario

# Función de ayuda para verificar si el usuario tiene permiso para ver el reporte
def has_report_access(user, estudiante_id, colegio):
    """
    Verifica si el usuario tiene permiso para ver el acta de reporte parcial de un estudiante.
    Permite a superusuarios, al propio estudiante, y a docentes del mismo colegio.
    """
    if es_admin_usuario(user):
        return True
    
    try:
        estudiante = Estudiante.objects.get(id=estudiante_id, colegio=colegio)
    except Estudiante.DoesNotExist:
        return False # El estudiante no existe o no pertenece a este colegio

    # Si el usuario es el propio estudiante
    if hasattr(user, 'estudiante') and user.estudiante == estudiante:
        return True
    
    # Si el usuario es un docente del mismo colegio
    if hasattr(user, 'docente'):
        docente = user.docente
        if docente.colegio == colegio:
            return True
            
    return False

@login_required
def reporte_parcial_vista(request):
    """
    Gestiona la vista para el reporte parcial, asegurando que todos los datos
    y operaciones correspondan al colegio actual.
    """
    if not request.colegio:
        return HttpResponseNotFound("<h1>Colegio no configurado</h1>")

    context = {'colegio': request.colegio}
    user = request.user
    docente_seleccionado_id = request.GET.get('docente_id')
    asignacion_seleccionada_id = request.GET.get('asignacion_id')
    periodo_seleccionado_id = request.GET.get('periodo_id')

    if es_admin_usuario(user):
        # Filtrar docentes y asignaciones por el colegio actual.
        context['todos_los_docentes'] = Docente.objects.filter(colegio=request.colegio).order_by('user__last_name', 'user__first_name')
        if docente_seleccionado_id:
            asignaciones = AsignacionDocente.objects.filter(docente_id=docente_seleccionado_id, colegio=request.colegio)
        else:
            asignaciones = AsignacionDocente.objects.filter(colegio=request.colegio)
    else:
        try:
            # Asegurar que se obtiene el docente del colegio actual.
            docente_actual = Docente.objects.get(user=user, colegio=request.colegio)
            asignaciones = AsignacionDocente.objects.filter(docente=docente_actual, colegio=request.colegio)
            context['docente_actual'] = docente_actual
        except Docente.DoesNotExist:
            messages.error(request, "Acceso denegado. No tiene un perfil de docente asociado en este colegio.")
            return redirect('notas:dashboard')
            
    context['asignaciones'] = asignaciones.select_related('curso', 'materia')
    # Filtrar periodos por el colegio actual.
    context['periodos'] = PeriodoAcademico.objects.filter(colegio=request.colegio).order_by('-ano_lectivo', '-nombre')
    context['docente_seleccionado_id'] = docente_seleccionado_id
    context['asignacion_seleccionada_id'] = asignacion_seleccionada_id
    context['periodo_seleccionado_id'] = periodo_seleccionado_id
    context['mostrar_tabla_estudiantes'] = False
    context['plazo_reporte_cerrado'] = False

    if request.method == 'POST':
        docente_que_reporta = Docente.objects.filter(user=request.user, colegio=request.colegio).first()
        asignacion_id_post = request.POST.get('asignacion_id')
        periodo_id_post = request.POST.get('periodo_id')

        # Filtrar por colegio al obtener los objetos.
        asignacion = get_object_or_404(AsignacionDocente, id=asignacion_id_post, colegio=request.colegio)
        periodo = get_object_or_404(PeriodoAcademico, id=periodo_id_post, colegio=request.colegio)

        if not periodo.reporte_parcial_activo:
            messages.error(request, f"No se pueden guardar los cambios. El plazo para el reporte parcial de '{periodo}' está cerrado.")
            return redirect(request.get_full_path())

        # La consulta de estudiantes ya está segura porque depende de una 'asignacion' filtrada.
        estudiantes_del_curso = Estudiante.objects.filter(curso=asignacion.curso, is_active=True)

        for estudiante in estudiantes_del_curso:
            estado_reporte = request.POST.get(f'reporte_{estudiante.id}')
            presenta_dificultades = (estado_reporte == 'si')
            
            # Asociar el reporte al colegio actual.
            reporte, creado = ReporteParcial.objects.update_or_create(
                colegio=request.colegio,
                estudiante=estudiante, 
                asignacion=asignacion, 
                periodo=periodo,
                defaults={'presenta_dificultades': presenta_dificultades}
            )

            if presenta_dificultades and (creado or not reporte.presenta_dificultades):
                Notificacion.objects.create(
                    colegio=request.colegio,
                    destinatario=estudiante.user,
                    mensaje=f"Se ha registrado un reporte de dificultades en la materia {asignacion.materia.nombre}.",
                    tipo='RENDIMIENTO' 
                )

            if presenta_dificultades and creado:
                docente_a_registrar = docente_que_reporta or asignacion.docente
                Observacion.objects.create(
                    colegio=request.colegio,
                    estudiante=estudiante, 
                    docente_reporta=docente_a_registrar, 
                    asignacion=asignacion, 
                    periodo=periodo,
                    tipo_observacion='AUTOMATICA',
                    descripcion=f"Presenta dificultades académicas en {asignacion.materia.nombre} según el reporte parcial."
                )

        messages.success(request, "Reportes parciales guardados correctamente.")
        return redirect(request.get_full_path())

    if asignacion_seleccionada_id and periodo_seleccionado_id:
        try:
            # Filtrar por colegio al obtener los objetos.
            asignacion_seleccionada = get_object_or_404(AsignacionDocente, id=asignacion_seleccionada_id, colegio=request.colegio)
            periodo_seleccionado = get_object_or_404(PeriodoAcademico, id=periodo_seleccionado_id, colegio=request.colegio)
            
            context['plazo_reporte_cerrado'] = not periodo_seleccionado.reporte_parcial_activo

            # La consulta de estudiantes es segura porque depende de 'asignacion_seleccionada' que ya fue filtrada.
            estudiantes = Estudiante.objects.filter(
                curso=asignacion_seleccionada.curso, is_active=True
            ).order_by('user__last_name', 'user__first_name')
            
            if estudiantes.exists():
                context['mostrar_tabla_estudiantes'] = True
                context['estudiantes'] = estudiantes
                
                # Filtrar por colegio al obtener los reportes.
                reportes_existentes = ReporteParcial.objects.filter(
                    colegio=request.colegio,
                    asignacion_id=asignacion_seleccionada_id,
                    periodo_id=periodo_seleccionado_id
                )
                context['reportes_existentes_map'] = {r.estudiante_id: r.presenta_dificultades for r in reportes_existentes}
        except Exception as e:
            messages.error(request, f"No se pudo cargar la información: {e}")

    return render(request, 'notas/docente/reporte_parcial.html', context)


@login_required
def acta_reporte_parcial_estudiante(request, estudiante_id):
    """
    Muestra un acta con todas las asignaturas en las que un estudiante ha sido
    reportado con dificultades en un período específico o en todos los períodos.
    Este reporte se basa en la indicación del docente, no en la nota final del periodo.
    """
    if not request.colegio:
        return HttpResponseNotFound("<h1>Colegio no configurado</h1>")

    # Verificar que el usuario tiene permiso para ver esta acta utilizando la función has_report_access
    if not has_report_access(request.user, estudiante_id, request.colegio):
        messages.error(request, "No tiene permiso para ver este reporte.")
        return redirect('notas:dashboard') # Redirige al dashboard si no tiene permiso

    estudiante = get_object_or_404(Estudiante, id=estudiante_id, colegio=request.colegio)
    
    # Obtener el ID del período desde los parámetros GET
    periodo_seleccionado_id = request.GET.get('periodo_id')
    periodo_seleccionado = None

    # Filtrar reportes de dificultades
    reportes_query = ReporteParcial.objects.filter(
        colegio=request.colegio,
        estudiante=estudiante,
        presenta_dificultades=True
    )

    if periodo_seleccionado_id:
        try:
            periodo_seleccionado = get_object_or_404(PeriodoAcademico, id=periodo_seleccionado_id, colegio=request.colegio)
            reportes_query = reportes_query.filter(periodo=periodo_seleccionado)
        except Exception as e:
            messages.warning(request, f"El período seleccionado no es válido o no existe: {e}")
            # Si el período no es válido, no filtramos por período y mostramos todos los reportes de dificultades.
            periodo_seleccionado = None


    reportes_dificultades = reportes_query.select_related(
        'asignacion__materia', 
        'asignacion__curso', 
        'periodo', 
        'asignacion__docente__user'
    ).order_by('periodo__ano_lectivo', 'periodo__fecha_inicio', 'asignacion__materia__nombre')

    # Obtener todos los períodos para el selector
    todos_los_periodos = PeriodoAcademico.objects.filter(colegio=request.colegio).order_by('-ano_lectivo', '-fecha_inicio')

    context = {
        'colegio': request.colegio,
        'estudiante': estudiante,
        'reportes_dificultades': reportes_dificultades,
        'todos_los_periodos': todos_los_periodos, # Para el selector de períodos
        'periodo_seleccionado': periodo_seleccionado, # Para mantener la selección en el dropdown
    }

    return render(request, 'notas/estudiante/acta_reporte_parcial.html', context)


@login_required
def lista_estudiantes_reporte(request):
    """
    Muestra una lista de estudiantes para que el docente o administrador pueda seleccionar
    y ver su acta de reporte parcial, con filtros por grado.
    """
    if not request.colegio:
        return HttpResponseNotFound("<h1>Colegio no configurado</h1>")

    # Obtener todos los cursos del colegio actual para el filtro
    todos_los_cursos = Curso.objects.filter(colegio=request.colegio).order_by('nombre')
    curso_seleccionado_id = request.GET.get('curso_id')
    
    # Consulta base de estudiantes
    estudiantes_query = Estudiante.objects.filter(colegio=request.colegio, is_active=True)

    # Si el usuario es un docente, filtrar por sus cursos asignados
    if not es_admin(request):
        try:
            docente_actual = Docente.objects.get(user=request.user, colegio=request.colegio)
            cursos_del_docente = AsignacionDocente.objects.filter(docente=docente_actual, colegio=request.colegio).values_list('curso', flat=True).distinct()
            estudiantes_query = estudiantes_query.filter(curso__in=cursos_del_docente)
            # Ajustar la lista de cursos disponibles para el filtro del docente
            todos_los_cursos = todos_los_cursos.filter(id__in=cursos_del_docente)
        except Docente.DoesNotExist:
            messages.error(request, "Acceso denegado. No tiene un perfil de docente asociado en este colegio.")
            return redirect('notas:dashboard')

    # Aplicar filtro por curso si se seleccionó uno
    if curso_seleccionado_id:
        try:
            curso_seleccionado = get_object_or_404(Curso, id=curso_seleccionado_id, colegio=request.colegio)
            estudiantes_query = estudiantes_query.filter(curso=curso_seleccionado)
        except Exception as e:
            messages.warning(request, f"El grado seleccionado no es válido o no existe: {e}")
            curso_seleccionado_id = None # Resetear la selección si es inválida

    estudiantes = estudiantes_query.order_by('user__last_name', 'user__first_name')

    context = {
        'colegio': request.colegio,
        'estudiantes': estudiantes,
        'todos_los_cursos': todos_los_cursos,
        'curso_seleccionado_id': curso_seleccionado_id,
    }
    return render(request, 'notas/docente/lista_estudiantes_reporte.html', context)
