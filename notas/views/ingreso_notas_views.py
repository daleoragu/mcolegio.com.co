# notas/views/ingreso_notas_views.py

import json

from ..planillas.columnas import nombre_componente
from decimal import Decimal, ROUND_HALF_UP

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.http import JsonResponse, HttpResponseNotFound
from django.shortcuts import get_object_or_404, render
from django.views import View
from django.core.exceptions import ValidationError
from django.core.serializers.json import DjangoJSONEncoder 

from ..models.academicos import (
    AsignacionDocente, PeriodoAcademico, Estudiante, Calificacion,
    NotaDetallada, InasistenciasManualesPeriodo, Asistencia, IndicadorLogroPeriodo,
    ConfiguracionCalificaciones, EscalaValoracion 
)
from ..models.perfiles import Docente
from ..planillas.columnas import columnas_del_plan, componentes_activos, guardar_plan
from ..planillas.guardar import guardar_componente, guardar_estudiante
from ..permisos import es_admin, es_admin_usuario

class IngresoNotasView(LoginRequiredMixin, View):
    template_name = 'notas/docente/ingresar_notas_periodo.html'
    login_url = '/login/'

    def get(self, request, *args, **kwargs):
        if not request.colegio:
            return HttpResponseNotFound("<h1>Colegio no configurado</h1>")

        config, _ = ConfiguracionCalificaciones.objects.get_or_create(colegio=request.colegio)
        
        asignaciones_a_mostrar = AsignacionDocente.objects.none()
        docente_seleccionado_id = request.GET.get('docente_id')
        
        context_admin = {'todos_los_docentes': None, 'docente_seleccionado_id': docente_seleccionado_id}

        if es_admin(request):
            context_admin['todos_los_docentes'] = Docente.objects.filter(colegio=request.colegio).select_related('user')
            if docente_seleccionado_id:
                asignaciones_a_mostrar = AsignacionDocente.objects.filter(docente_id=docente_seleccionado_id, colegio=request.colegio).select_related('materia', 'curso')
        else:
            try:
                docente = get_object_or_404(Docente, user=request.user, colegio=request.colegio)
                asignaciones_a_mostrar = AsignacionDocente.objects.filter(docente=docente, colegio=request.colegio).select_related('materia', 'curso')
            except Docente.DoesNotExist:
                return render(request, self.template_name, {'error_message': 'No tiene un perfil de docente asignado en este colegio.'})

        periodos = PeriodoAcademico.objects.filter(colegio=request.colegio).order_by('-ano_lectivo', 'nombre')
        asignacion_id = request.GET.get('asignacion_id')
        periodo_id = request.GET.get('periodo_id')
        
        context = {
            'colegio': request.colegio,
            'asignaciones': asignaciones_a_mostrar,
            'todos_los_periodos': periodos,
            'asignacion_seleccionada': None,
            'periodo_seleccionado': None,
            'asignacion_seleccionada_id': asignacion_id,
            'periodo_seleccionado_id': periodo_id,
            'estudiantes_data_json': '[]',
            'periodo_cerrado': False,
            'indicadores': [],
            'hay_indicadores': False,
            'permiso_modificar_porcentajes': config.docente_puede_modificar,
        }
        context.update(context_admin)

        if asignacion_id and periodo_id:
            asignacion_seleccionada = get_object_or_404(AsignacionDocente, id=asignacion_id, colegio=request.colegio)
            periodo_seleccionado = get_object_or_404(PeriodoAcademico, id=periodo_id, colegio=request.colegio)
            
            # Recolectar configuración de la materia para enviarla al Frontend
            materia = asignacion_seleccionada.materia
            config_materia = {
                'promedia': getattr(materia, 'promedia_en_boletin', True),
                # Los nombres del colegio (Componentes de evaluación), o los propios de la materia.
                'lbl_ser': nombre_componente(asignacion_seleccionada, 'SER'),
                'lbl_saber': nombre_componente(asignacion_seleccionada, 'SABER'),
                'lbl_hacer': nombre_componente(asignacion_seleccionada, 'HACER'),
            }
            context['config_materia_json'] = json.dumps(config_materia)

            estudiantes_del_curso = Estudiante.objects.filter(curso=asignacion_seleccionada.curso, colegio=request.colegio, is_active=True).select_related('user').order_by('user__last_name', 'user__first_name')
            
            estudiantes_data = []
            inclusion_data = {} 

            for estudiante in estudiantes_del_curso:
                nombre_completo = f"{estudiante.user.last_name}, {estudiante.user.first_name}".strip()
                data = {'id': estudiante.id, 'nombre_completo': nombre_completo, 'notas': {'ser': [], 'saber': [], 'hacer': []}, 'inasistencias': 0, 'observacion': ''}
                
                calificaciones = Calificacion.objects.filter(estudiante=estudiante, materia=asignacion_seleccionada.materia, periodo=periodo_seleccionado, colegio=request.colegio).prefetch_related('notas_detalladas')
                
                obs_inc = ""
                for cal in calificaciones:
                    tipo_map = {'SER': 'ser', 'SABER': 'saber', 'HACER': 'hacer'}
                    if cal.tipo_nota in tipo_map:
                        key = tipo_map[cal.tipo_nota]
                        data['notas'][key] = [{'descripcion': n.descripcion, 'valor': str(n.valor_nota)} for n in cal.notas_detalladas.all()]
                    elif cal.tipo_nota == 'PROM_PERIODO':
                        obs_inc = getattr(cal, 'observacion_inclusion', "")
                        data['observacion'] = cal.observacion or ''
                
                inasistencia_manual, _ = InasistenciasManualesPeriodo.objects.get_or_create(estudiante=estudiante, asignacion=asignacion_seleccionada, periodo=periodo_seleccionado, colegio=request.colegio, defaults={'cantidad': 0})
                data['inasistencias'] = inasistencia_manual.cantidad
                estudiantes_data.append(data)

                # CORRECCIÓN DE CÁRGA: Asegura que se empaquete la información correctamente
                # para que JavaScript reciba la observación existente y arme la lista múltiple
                es_inclu = getattr(estudiante, 'es_inclusion', False)
                inclusion_data[str(estudiante.id)] = {
                    'es_inclusion': es_inclu,
                    'obs': obs_inc if obs_inc else "",
                    'lista_obs': [s.strip() for s in (obs_inc or "").split('\n') if s.strip()]
                }
            
            # Las columnas de cada componente (el plan de notas): la tabla las
            # usa para ubicar cada nota por su nombre y no por su posición.
            plan_columnas = {}
            for codigo in ('SER', 'SABER', 'HACER'):
                plan_columnas[codigo.lower()] = columnas_del_plan(asignacion_seleccionada, periodo_seleccionado, codigo, config=config)
            context['plan_notas'] = plan_columnas

            indicadores = IndicadorLogroPeriodo.objects.filter(asignacion=asignacion_seleccionada, periodo=periodo_seleccionado, colegio=request.colegio).order_by('id')
            
            context.update({
                'asignacion_seleccionada': asignacion_seleccionada, 
                'periodo_seleccionado': periodo_seleccionado, 
                'estudiantes_data_json': json.dumps(estudiantes_data, cls=DjangoJSONEncoder), 
                'inclusion_data_json': json.dumps(inclusion_data, cls=DjangoJSONEncoder),
                'periodo_cerrado': not periodo_seleccionado.esta_activo, 
                'indicadores': indicadores, 
                'hay_indicadores': indicadores.exists()
            })

        escala_valoracion = EscalaValoracion.objects.filter(colegio=request.colegio).values(
            'nombre_desempeno', 'valor_minimo', 'valor_maximo'
        ).order_by('valor_minimo')

        context['escala_valoracion_json'] = json.dumps(list(escala_valoracion), cls=DjangoJSONEncoder)

        return render(request, self.template_name, context)

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        if not request.colegio:
            return JsonResponse({'status': 'error', 'message': 'Colegio no identificado'}, status=404)
        
        try:
            data = json.loads(request.body)
            asignacion_id = data.get('asignacion_id')
            periodo_id = data.get('periodo_id')
            estudiantes_data = data.get('estudiantes')
            porcentajes_nuevos = data.get('porcentajes')

            if not all([asignacion_id, periodo_id, isinstance(estudiantes_data, list)]):
                return JsonResponse({'status': 'error', 'message': 'Faltan datos críticos.'}, status=400)

            asignacion = get_object_or_404(AsignacionDocente, id=asignacion_id, colegio=request.colegio)
            periodo = get_object_or_404(PeriodoAcademico, id=periodo_id, colegio=request.colegio)

            if not es_admin(request) and asignacion.docente.user != request.user:
                return JsonResponse({'status': 'error', 'message': 'No tiene permiso.'}, status=403)

            if not periodo.esta_activo:
                return JsonResponse({'status': 'error', 'message': 'El periodo está cerrado.'}, status=403)

            if not IndicadorLogroPeriodo.objects.filter(asignacion=asignacion, periodo=periodo, colegio=request.colegio).exists():
                return JsonResponse({'status': 'error', 'message': 'No hay indicadores de logro definidos.'}, status=403)

            config, _ = ConfiguracionCalificaciones.objects.get_or_create(colegio=request.colegio)
            if config.docente_puede_modificar and porcentajes_nuevos:
                try:
                    asignacion.porcentaje_saber = int(porcentajes_nuevos.get('saber', 0))
                    asignacion.porcentaje_hacer = int(porcentajes_nuevos.get('hacer', 0))
                    asignacion.porcentaje_ser = int(porcentajes_nuevos.get('ser', 0))
                    asignacion.usar_ponderacion_equitativa = False
                    asignacion.full_clean()
                    asignacion.save()
                except (ValidationError, ValueError, TypeError) as e:
                    mensaje_error = e.messages[0] if hasattr(e, 'messages') else str(e)
                    return JsonResponse({'status': 'error', 'message': f"Error en porcentajes: {mensaje_error}"}, status=400)
            
            # La planilla en línea manda también sus columnas (cuántas notas y
            # cómo se llama cada una): se guardan como el plan de notas, para que
            # el Excel y la próxima vez que se abra salgan iguales.
            plan_nuevo = data.get('plan') or {}
            for codigo in ('SER', 'SABER', 'HACER'):
                columnas = plan_nuevo.get(codigo.lower())
                if isinstance(columnas, list) and columnas:
                    guardar_plan(asignacion, periodo, codigo, columnas)

            # El cálculo vive en notas/planillas/guardar.py: es el mismo que usa
            # la subida del Excel, así las dos dan la misma definitiva.
            for est_data in estudiantes_data:
                estudiante = get_object_or_404(Estudiante, id=est_data['id'], colegio=request.colegio)
                guardar_estudiante(
                    request.colegio, asignacion, periodo, estudiante, est_data.get('notas', {}),
                    inasistencias=est_data.get('inasistencias', 0),
                    observacion_inclusion=est_data.get('observacion_inclusion') if 'observacion_inclusion' in est_data else None,
                    observacion=est_data.get('observacion') if 'observacion' in est_data else None,
                )

            return JsonResponse({'status': 'success', 'message': 'Calificaciones guardadas correctamente.'})
        
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': f'Ocurrió un error inesperado: {e}'}, status=500)

    def calcular_promedio_componente(self, colegio, estudiante, asignacion, periodo, tipo_componente, notas_data):
        """Se conserva por compatibilidad: ahora delega en notas/planillas/guardar.py."""
        return guardar_componente(colegio, estudiante, asignacion, periodo, tipo_componente, notas_data)

@login_required
def ajax_get_inasistencias_auto(request):
    if not request.colegio:
        return JsonResponse({'status': 'error', 'message': 'Colegio no identificado'}, status=404)
    try:
        asignacion_id = request.GET.get('asignacion_id')
        periodo_id = request.GET.get('periodo_id')
        estudiante_id = request.GET.get('estudiante_id')
        periodo = get_object_or_404(PeriodoAcademico, id=periodo_id, colegio=request.colegio)
        
        cantidad = Asistencia.objects.filter(
            colegio=request.colegio, estudiante_id=estudiante_id, asignacion_id=asignacion_id, estado='A', 
            fecha__range=[periodo.fecha_inicio, periodo.fecha_fin]
        ).count()
        
        return JsonResponse({'status': 'success', 'inasistencias_auto': cantidad})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)