# notas/views/plan_mejoramiento_views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from decimal import Decimal
from django.http import HttpResponseNotFound

from ..models import (
    Docente, AsignacionDocente, PeriodoAcademico, Estudiante,
    Calificacion, PlanDeMejoramiento, Observacion, EscalaValoracion
)
from ..permisos import es_admin, es_admin_usuario

@login_required
def plan_mejoramiento_vista(request):
    """
    Gestiona la interfaz para planes de mejoramiento, utilizando escalas de
    valoración dinámicas definidas por el colegio.
    """
    if not request.colegio:
        return HttpResponseNotFound("<h1>Colegio no configurado</h1>")

    context = {'colegio': request.colegio}
    user = request.user
    docente_seleccionado_id = request.GET.get('docente_id')
    asignacion_seleccionada_id_str = request.GET.get('asignacion_id')
    periodo_seleccionado_id_str = request.GET.get('periodo_id')

    # --- INICIO: Lógica MEJORADA para obtener umbrales de calificación dinámicos ---
    nota_maxima_desempeno_bajo = Decimal('2.9')
    nota_minima_aprobatoria = Decimal('3.0')
    
    escala_bajo_encontrada = False
    escala_basico_encontrada = False

    # Obtenemos todas las escalas del colegio de una vez para optimizar
    escalas_colegio = EscalaValoracion.objects.filter(colegio=request.colegio)

    for escala in escalas_colegio:
        # Limpiamos y normalizamos el nombre del desempeño para una comparación segura
        nombre_desempeno_limpio = escala.nombre_desempeno.strip().upper()
        
        if nombre_desempeno_limpio == 'BAJO':
            nota_maxima_desempeno_bajo = escala.valor_maximo
            escala_bajo_encontrada = True
        
        if nombre_desempeno_limpio == 'BÁSICO' or nombre_desempeno_limpio == 'BASICO':
            nota_minima_aprobatoria = escala.valor_minimo
            escala_basico_encontrada = True

    # Si después de revisar todas las escalas, alguna no se encontró, mostramos el mensaje.
    if not escala_bajo_encontrada or not escala_basico_encontrada:
        if user.is_staff:
            nombres_faltantes = []
            if not escala_bajo_encontrada: nombres_faltantes.append("'BAJO'")
            if not escala_basico_encontrada: nombres_faltantes.append("'BÁSICO'")
            
            messages.warning(request, f"No se encontró la escala de valoración { ' y '.join(nombres_faltantes) }. Se usarán valores por defecto. Por favor, revise la configuración de escalas del colegio.")

    context['nota_minima_aprobatoria'] = nota_minima_aprobatoria
    # --- FIN: Lógica MEJORADA ---

    if es_admin_usuario(user):
        context['todos_los_docentes'] = Docente.objects.filter(colegio=request.colegio).order_by('user__last_name', 'user__first_name')
        if docente_seleccionado_id:
            asignaciones_docente = AsignacionDocente.objects.filter(docente_id=docente_seleccionado_id, colegio=request.colegio)
        else:
            asignaciones_docente = AsignacionDocente.objects.filter(colegio=request.colegio)
    else:
        try:
            docente_actual = Docente.objects.get(user=user, colegio=request.colegio)
            asignaciones_docente = AsignacionDocente.objects.filter(docente=docente_actual, colegio=request.colegio)
            context['docente_actual'] = docente_actual
        except Docente.DoesNotExist:
            messages.error(request, "Acceso denegado. Su usuario no está asociado a un perfil de docente en este colegio.")
            return redirect('notas:dashboard')

    context['asignaciones'] = asignaciones_docente.select_related('curso', 'materia').order_by('curso__nombre', 'materia__nombre')
    context['periodos'] = PeriodoAcademico.objects.filter(colegio=request.colegio).order_by('-ano_lectivo', 'nombre')
    context['docente_seleccionado_id'] = docente_seleccionado_id
    context['asignacion_seleccionada_id'] = asignacion_seleccionada_id_str
    context['periodo_seleccionado_id'] = periodo_seleccionado_id_str
    context['estudiantes_para_nivelar_data'] = []
    context['plazo_nivelaciones_cerrado'] = False

    if request.method == 'POST':
        docente_que_reporta = Docente.objects.filter(user=request.user, colegio=request.colegio).first()
        asignacion_id = request.POST.get('asignacion_id')
        periodo_id = request.POST.get('periodo_id')
        
        periodo = get_object_or_404(PeriodoAcademico, id=periodo_id, colegio=request.colegio)

        if not periodo.nivelaciones_activas:
            messages.error(request, f"No se pueden guardar los cambios. El plazo para las nivelaciones de '{periodo}' está cerrado.")
            return redirect(request.get_full_path())
            
        try:
            asignacion = get_object_or_404(AsignacionDocente, id=asignacion_id, colegio=request.colegio)
            docente_asignado = asignacion.docente
            if not es_admin_usuario(user) and asignacion.docente != docente_que_reporta:
                raise Exception("Permiso denegado para esta asignación.")
            
            estudiantes_en_formulario = request.POST.getlist('estudiante_id')

            for est_id in estudiantes_en_formulario:
                estudiante = get_object_or_404(Estudiante, id=est_id, colegio=request.colegio)
                nota_str = request.POST.get(f'nota_nivelacion_{est_id}', '').strip()
                desc_plan = request.POST.get(f'descripcion_plan_{est_id}', '').strip()

                if nota_str:
                    nota_nivelacion = Decimal(nota_str.replace(',', '.'))
                    
                    if not (Decimal('1.0') <= nota_nivelacion <= Decimal('5.0')):
                        messages.warning(request, f"Nota para {estudiante} ({nota_nivelacion}) está fuera de rango y no fue guardada.")
                        continue

                    PlanDeMejoramiento.objects.update_or_create(
                        colegio=request.colegio,
                        estudiante=estudiante,
                        asignacion=asignacion,
                        periodo_recuperado=periodo,
                        defaults={'nota_recuperacion': nota_nivelacion, 'descripcion_plan': desc_plan}
                    )
                    
                    Calificacion.objects.update_or_create(
                        colegio=request.colegio,
                        estudiante=estudiante,
                        materia=asignacion.materia,
                        periodo=periodo,
                        tipo_nota='NIVELACION',
                        defaults={'valor_nota': nota_nivelacion, 'docente': docente_que_reporta or docente_asignado}
                    )
                    
                    calificacion_original = Calificacion.objects.filter(
                        colegio=request.colegio, estudiante=estudiante, materia=asignacion.materia,
                        periodo=periodo, tipo_nota='PROM_PERIODO'
                    ).first()

                    if calificacion_original:
                        calificacion_original.es_recuperada = (nota_nivelacion >= nota_minima_aprobatoria)
                        calificacion_original.save()
                    
                    resultado = "aprobó" if nota_nivelacion >= nota_minima_aprobatoria else "no aprobó"
                    descripcion_obs = (
                        f"En el plan de mejoramiento para la materia de {asignacion.materia.nombre} "
                        f"correspondiente al {periodo}, el estudiante {resultado} "
                        f"con una nota final de {nota_nivelacion}."
                    )
                    Observacion.objects.update_or_create(
                        colegio=request.colegio,
                        estudiante=estudiante, periodo=periodo, tipo_observacion='ACADEMICA',
                        asignacion=asignacion,
                        defaults={'descripcion': descripcion_obs, 'docente_reporta': docente_que_reporta or docente_asignado}
                    )
                else:
                    PlanDeMejoramiento.objects.filter(colegio=request.colegio, estudiante_id=est_id, asignacion_id=asignacion_id, periodo_recuperado_id=periodo_id).delete()
                    Calificacion.objects.filter(colegio=request.colegio, estudiante_id=est_id, materia_id=asignacion.materia.id, periodo_id=periodo_id, tipo_nota='NIVELACION').delete()
                    
                    calificacion_original = Calificacion.objects.filter(
                        colegio=request.colegio, estudiante_id=est_id, materia_id=asignacion.materia.id,
                        periodo_id=periodo_id, tipo_nota='PROM_PERIODO'
                    ).first()
                    if calificacion_original:
                        calificacion_original.es_recuperada = False
                        calificacion_original.save()
            
            messages.success(request, "Nivelaciones guardadas y registros actualizados exitosamente.")
        except Exception as e:
            messages.error(request, f"Ocurrió un error al guardar: {e}")
        
        return redirect(request.get_full_path())

    if asignacion_seleccionada_id_str and periodo_seleccionado_id_str:
        try:
            asignacion_actual = get_object_or_404(AsignacionDocente, id=asignacion_seleccionada_id_str, colegio=request.colegio)
            periodo_obj = get_object_or_404(PeriodoAcademico, id=periodo_seleccionado_id_str, colegio=request.colegio)
            
            context['plazo_nivelaciones_cerrado'] = not periodo_obj.nivelaciones_activas

            calificaciones_bajas = Calificacion.objects.filter(
                colegio=request.colegio,
                materia=asignacion_actual.materia, 
                periodo=periodo_obj,
                tipo_nota='PROM_PERIODO', 
                valor_nota__lte=nota_maxima_desempeno_bajo,
                estudiante__curso=asignacion_actual.curso,
                estudiante__is_active=True
            ).select_related('estudiante__user').order_by('estudiante__user__last_name', 'estudiante__user__first_name')
            
            for cal in calificaciones_bajas:
                estudiante = cal.estudiante
                plan_existente = PlanDeMejoramiento.objects.filter(
                    colegio=request.colegio, estudiante=estudiante, asignacion=asignacion_actual, periodo_recuperado=periodo_obj
                ).first()
                context['estudiantes_para_nivelar_data'].append({
                    'estudiante': estudiante,
                    'promedio_original': cal.valor_nota,
                    'plan': plan_existente
                })
        except Exception as e:
            messages.warning(request, f"No se pudieron cargar los datos: {e}")

    return render(request, 'notas/docente/plan_mejoramiento.html', context)
