# notas/views/sabana_views.py

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseNotFound
from django.contrib import messages
from decimal import Decimal, ROUND_HALF_UP

from notas.boletin.ponderacion import (
    ajustes as ajustes_colegio, definitiva_anual, nota_necesaria,
)
from django.template.loader import render_to_string
from django.utils import timezone
from itertools import groupby
from django.db.models import Prefetch
from collections import defaultdict

try:
    from weasyprint import HTML
    PDF_SUPPORT = True
except ImportError:
    PDF_SUPPORT = False

from ..models import Curso, PeriodoAcademico, Docente, AsignacionDocente, Estudiante, Materia, Calificacion, AreaConocimiento, PonderacionAreaMateria, EscalaValoracion
from .sabana_exports import generar_excel_sabana
from ..permisos import es_admin, es_admin_usuario

def _get_sabana_acumulada_data(colegio, curso, periodo_actual):
    """
    Lógica de negocio final para la sábana de notas.
    - Ranking y Cuadro de Honor se basan en notas ORIGINALES.
    - Muestra el formato 'original (recuperado)' para notas, promedios de área y promedios de periodo.
    """
    # --- 1. OBTENCIÓN DE DATOS INICIALES Y CONFIGURACIÓN ---
    escala_valoracion_qs = EscalaValoracion.objects.filter(colegio=colegio).order_by('-valor_maximo')
    if not escala_valoracion_qs.exists():
        raise ValueError("No hay una escala de valoración configurada para este colegio.")

    DESEMPENOS_NOMBRES = [e.nombre_desempeno.upper() for e in escala_valoracion_qs]
    DESEMPENOS_CON_DEFAULT = DESEMPENOS_NOMBRES + ["SIN ESCALA"]

    def get_valoracion_desempeno(nota):
        if nota is None: return None
        nota_decimal = Decimal(nota)
        for escala in escala_valoracion_qs:
            if escala.valor_minimo <= nota_decimal <= escala.valor_maximo:
                return escala.nombre_desempeno.upper()
        return "SIN ESCALA"

    periodos_del_ano = PeriodoAcademico.objects.filter(colegio=colegio, ano_lectivo=periodo_actual.ano_lectivo).order_by('fecha_inicio')
    periodos_transcurridos = periodos_del_ano.filter(fecha_inicio__lte=periodo_actual.fecha_inicio)
    
    materias_del_curso = Materia.objects.filter(colegio=colegio, asignaciondocente__curso=curso).distinct().order_by('nombre')
    
    areas_con_materias = list(AreaConocimiento.objects.filter(
        colegio=colegio, materias__in=materias_del_curso
    ).prefetch_related(
        Prefetch('materias', queryset=materias_del_curso, to_attr='materias_del_curso_ordenadas')
    ).distinct().order_by('nombre'))

    # Un área con una sola asignatura repetiría la misma nota en dos columnas.
    reglas_colegio = ajustes_colegio(colegio)
    for _area in areas_con_materias:
        _area.colapsada = (reglas_colegio.colapsar_area_unica
                           and len(_area.materias_del_curso_ordenadas) == 1)

    ultimo_periodo = periodos_del_ano.last()
    
    ponderaciones_map = {(p.area_id, p.materia_id): p.peso_porcentual for p in PonderacionAreaMateria.objects.filter(colegio=colegio, materia__in=materias_del_curso)}

    estudiantes = Estudiante.objects.filter(curso=curso, is_active=True, colegio=colegio).select_related('user')
    
    calificaciones = Calificacion.objects.filter(
        colegio=colegio, estudiante__in=estudiantes, materia__in=materias_del_curso,
        periodo__in=periodos_transcurridos, tipo_nota__in=['PROM_PERIODO', 'NIVELACION']
    ).select_related('estudiante', 'materia', 'periodo')

    calificaciones_pivot = defaultdict(lambda: {'prom': None, 'niv': None})
    for cal in calificaciones:
        key = (cal.estudiante_id, cal.materia_id, cal.periodo.id)
        if cal.tipo_nota == 'PROM_PERIODO': calificaciones_pivot[key]['prom'] = cal.valor_nota
        elif cal.tipo_nota == 'NIVELACION': calificaciones_pivot[key]['niv'] = cal.valor_nota
    
    sabana_data = []
    CERO = Decimal('0.0')
    
    notas_acumuladas_materias = defaultdict(list)
    notas_acumuladas_areas = defaultdict(list)

    # --- 2. PROCESAMIENTO DE NOTAS POR ESTUDIANTE ---
    for est in estudiantes:
        estudiante_data = {'info': est, 'filas_notas': [], 'fila_acumulada': {}, 'resumen_desempeno_acumulado': {d: 0 for d in DESEMPENOS_CON_DEFAULT}}
        
        # --- INICIO: CAMBIO para calcular promedios de periodo con y sin recuperación ---
        for p in periodos_transcurridos:
            fila_periodo = {
                'periodo_nombre': str(p.nombre.replace("PRIMERO", "1").replace("SEGUNDO", "2").replace("TERCERO", "3").replace("CUARTO", "4")),
                'celdas': [], 'resumen_desempeno_periodo': {d: 0 for d in DESEMPENOS_CON_DEFAULT}
            }
            
            def calcular_promedios_fila(usar_recuperacion):
                notas_area_para_promedio = []
                celdas_fila = []
                for area in areas_con_materias:
                    suma_ponderada_area, suma_pesos_area = CERO, CERO
                    for materia in area.materias_del_curso_ordenadas:
                        cal_data = calificaciones_pivot.get((est.id, materia.id, p.id), {})
                        nota_original = cal_data.get('prom')
                        nota_recuperacion = cal_data.get('niv')
                        
                        nota_para_calculo = (nota_recuperacion if usar_recuperacion else None) or nota_original

                        if not usar_recuperacion: # Solo construimos la celda una vez
                           celdas_fila.append({'is_area': False, 'nota_original': nota_original, 'nota_recuperacion': nota_recuperacion})

                        if nota_para_calculo is not None:
                            peso = ponderaciones_map.get((area.id, materia.id))
                            if peso is not None:
                                suma_ponderada_area += (Decimal(nota_para_calculo) * peso)
                                suma_pesos_area += peso
                    
                    nota_area = (suma_ponderada_area / suma_pesos_area).quantize(Decimal('0.1'), rounding=ROUND_HALF_UP) if suma_pesos_area > 0 else None
                    if area.colapsada:
                        pass  # la columna de la asignatura ya muestra esta misma nota
                    elif not usar_recuperacion:
                        celdas_fila.append({'is_area': True, 'nota_original': nota_area}) # Guardamos la original
                    else:
                        # Buscamos la celda del área y le añadimos la nota recuperada si es diferente
                        for celda in celdas_fila:
                            if celda.get('is_area') and celda.get('nota_original') != nota_area:
                                celda['nota_recuperacion'] = nota_area
                                break
                    
                    if nota_area: notas_area_para_promedio.append(nota_area)
                
                promedio_fila = (sum(notas_area_para_promedio) / len(notas_area_para_promedio)).quantize(Decimal('0.2'), rounding=ROUND_HALF_UP) if notas_area_para_promedio else CERO
                return promedio_fila, celdas_fila

            promedio_periodo_original, celdas_periodo = calcular_promedios_fila(usar_recuperacion=False)
            promedio_periodo_recuperado, _ = calcular_promedios_fila(usar_recuperacion=True)

            fila_periodo['celdas'] = celdas_periodo
            fila_periodo['promedio_periodo_original'] = promedio_periodo_original
            if promedio_periodo_original != promedio_periodo_recuperado:
                fila_periodo['promedio_periodo_recuperado'] = promedio_periodo_recuperado
            else:
                fila_periodo['promedio_periodo_recuperado'] = None
            # --- FIN: CAMBIO ---

            # El resumen de desempeño se calcula con la nota final (recuperada)
            for celda in celdas_periodo:
                if celda.get('is_area'):
                    nota_final_area = celda.get('nota_recuperacion') or celda.get('nota_original')
                    desempeno_area = get_valoracion_desempeno(nota_final_area)
                    if desempeno_area: fila_periodo['resumen_desempeno_periodo'][desempeno_area] += 1
            
            fila_periodo['resumen_desempeno_periodo_list'] = [fila_periodo['resumen_desempeno_periodo'][d] for d in DESEMPENOS_NOMBRES]
            estudiante_data['filas_notas'].append(fila_periodo)

        # --- Lógica para Fila Acumulada ---
        def calcular_promedio_acumulado(usar_recuperacion):
            notas_finales_areas_para_promedio = []
            celdas_acumuladas = []
            for area in areas_con_materias:
                suma_ponderada_area_final, suma_pesos_area_final = CERO, CERO
                for materia in area.materias_del_curso_ordenadas:
                    # Las notas van por periodo para que se puedan ponderar.
                    notas_materia = {}
                    for p_inner in periodos_transcurridos:
                        cal_data = calificaciones_pivot.get((est.id, materia.id, p_inner.id), {})
                        nota_valida = (cal_data.get('niv') if usar_recuperacion else None) or cal_data.get('prom')
                        notas_materia[p_inner.id] = nota_valida

                    # La columna acumulada es un avance, no la nota final del año:
                    # se calcula con lo que haya aunque falten periodos.
                    promedio_final_materia, faltan = definitiva_anual(
                        colegio, notas_materia, periodos_transcurridos, exigir=False)

                    # Qué nota necesita en el último periodo para no reprobar.
                    proyeccion = None
                    if usar_recuperacion and ultimo_periodo is not None:
                        ya_califico_el_ultimo = calificaciones_pivot.get(
                            (est.id, materia.id, ultimo_periodo.id), {}).get('prom') is not None
                        if not ya_califico_el_ultimo:
                            notas_ano = {pp.id: notas_materia.get(pp.id) for pp in periodos_del_ano}
                            proyeccion = nota_necesaria(
                                colegio, notas_ano, periodos_del_ano, ultimo_periodo)

                    celdas_acumuladas.append({
                        'is_area': False,
                        'nota': promedio_final_materia,
                        'faltantes': [p.get_nombre_display() for p in faltan],
                        'necesaria': proyeccion,
                    })

                    if promedio_final_materia is not None:
                        if usar_recuperacion: notas_acumuladas_materias[materia.id].append(promedio_final_materia)
                        peso = ponderaciones_map.get((area.id, materia.id))
                        if peso is not None:
                            suma_ponderada_area_final += (promedio_final_materia * peso)
                            suma_pesos_area_final += peso
                
                nota_area_final = (suma_ponderada_area_final / suma_pesos_area_final).quantize(Decimal('0.1'), rounding=ROUND_HALF_UP) if suma_pesos_area_final > 0 else None
                if not area.colapsada:
                    celdas_acumuladas.append({'is_area': True, 'nota': nota_area_final})
                
                if nota_area_final is not None:
                    notas_finales_areas_para_promedio.append(nota_area_final)
                    if usar_recuperacion:
                        notas_acumuladas_areas[area.id].append(nota_area_final)
                        desempeno_area_acumulado = get_valoracion_desempeno(nota_area_final)
                        if desempeno_area_acumulado: estudiante_data['resumen_desempeno_acumulado'][desempeno_area_acumulado] += 1
            
            promedio_final = (sum(notas_finales_areas_para_promedio) / len(notas_finales_areas_para_promedio)).quantize(Decimal('0.2'), rounding=ROUND_HALF_UP) if notas_finales_areas_para_promedio else CERO
            return promedio_final, celdas_acumuladas

        promedio_final_con_rec, celdas_con_rec = calcular_promedio_acumulado(usar_recuperacion=True)
        promedio_final_sin_rec, _ = calcular_promedio_acumulado(usar_recuperacion=False)
        
        fila_acumulada = {'periodo_nombre': 'Ac', 'celdas': celdas_con_rec}
        fila_acumulada['promedio_final_ranking'] = promedio_final_sin_rec # Para el ranking
        fila_acumulada['promedio_display_original'] = promedio_final_sin_rec
        
        if promedio_final_con_rec != promedio_final_sin_rec:
            fila_acumulada['promedio_display_recuperado'] = promedio_final_con_rec
        else:
            fila_acumulada['promedio_display_recuperado'] = None

        estudiante_data['resumen_desempeno_acumulado_list'] = [estudiante_data['resumen_desempeno_acumulado'][d] for d in DESEMPENOS_NOMBRES]
        estudiante_data['fila_acumulada'] = fila_acumulada
        sabana_data.append(estudiante_data)

    # --- 3. CÁLCULO DE PUESTO Y PODIO (BASADO EN NOTAS ORIGINALES) ---
    sabana_data.sort(key=lambda x: x['fila_acumulada']['promedio_final_ranking'] or CERO, reverse=True)
    mejores_estudiantes = sabana_data[:3]
    rank_counter = 1
    for k, group in groupby(sabana_data, key=lambda x: x['fila_acumulada']['promedio_final_ranking']):
        group_list = list(group)
        for item in group_list:
            item.update({'puesto_final': rank_counter})
        rank_counter += len(group_list)
    sabana_data.sort(key=lambda x: (x['info'].user.last_name, x['info'].user.first_name))
        
    # El resto de la función no necesita cambios...
    # --- 4. CÁLCULO DEL RESUMEN FINAL (CONTEOS Y PORCENTAJES) ---
    resumen_final_celdas = []
    
    def calcular_resumen_columna(notas):
        notas_validas = [n for n in notas if n is not None]
        total_validos = len(notas_validas)
        promedio = sum(notas_validas) / total_validos if total_validos > 0 else CERO
        desempenos_map = {d: {'count': 0, 'percentage': 0.0} for d in DESEMPENOS_NOMBRES}
        for nota in notas_validas:
            des = get_valoracion_desempeno(nota)
            if des and des in desempenos_map:
                desempenos_map[des]['count'] += 1
        if total_validos > 0:
            for d_nombre in DESEMPENOS_NOMBRES:
                count = desempenos_map[d_nombre]['count']
                desempenos_map[d_nombre]['percentage'] = (count / total_validos) * 100
        return {'promedio': promedio, 'desempenos': desempenos_map}

    for area in areas_con_materias:
        for materia in area.materias_del_curso_ordenadas:
            resumen_final_celdas.append(calcular_resumen_columna(notas_acumuladas_materias.get(materia.id, [])))
        resumen_final_celdas.append(calcular_resumen_columna(notas_acumuladas_areas.get(area.id, [])))

    resumen_global_niveles = []
    idx = 0
    for area in areas_con_materias:
        for materia in area.materias_del_curso_ordenadas:
            celda = resumen_final_celdas[idx]
            item = {'tipo': 'materia', 'area': area.nombre, 'materia': materia.nombre, 'desempenos': {k: v['count'] for k, v in celda['desempenos'].items()}}
            resumen_global_niveles.append(item)
            idx += 1
        celda = resumen_final_celdas[idx]
        item = {'tipo': 'area', 'area': area.nombre, 'materia': 'TOTAL ÁREA', 'desempenos': {k: v['count'] for k, v in celda['desempenos'].items()}}
        resumen_global_niveles.append(item)
        idx += 1

    return (sabana_data, areas_con_materias, DESEMPENOS_NOMBRES, 
            mejores_estudiantes, resumen_final_celdas, resumen_global_niveles)

# El resto del archivo (las vistas) no necesita cambios, ya que solo llaman a la función principal.
def _preparar_y_validar_sabana(request):
    if not request.colegio:
        return None, None, None, "Colegio no identificado.", False

    curso_id = request.GET.get('curso_id')
    if not curso_id:
        return None, None, None, "Debe seleccionar un curso.", False
    
    curso = get_object_or_404(Curso, id=curso_id, colegio=request.colegio)
    periodo_ref = None
    is_final_report = False
    tipo_reporte = request.GET.get('tipo_reporte', 'periodo')

    if tipo_reporte == 'anual':
        ano_lectivo_str = request.GET.get('ano_lectivo')
        if not ano_lectivo_str:
            return None, None, None, "Debe proporcionar un año lectivo para el reporte final.", False
        
        periodo_ref = PeriodoAcademico.objects.filter(
            colegio=request.colegio, ano_lectivo=int(ano_lectivo_str)
        ).order_by('-fecha_fin').first()
        
        if not periodo_ref:
            return None, None, None, f"No se encontraron periodos para el año lectivo {ano_lectivo_str}.", False
        is_final_report = True

    else:
        periodo_id = request.GET.get('periodo_id')
        if not periodo_id:
            return None, None, None, "Debe seleccionar un periodo.", False
        periodo_ref = get_object_or_404(PeriodoAcademico, id=periodo_id, colegio=request.colegio)

    if not es_admin(request):
        try:
            docente = Docente.objects.get(user=request.user, colegio=request.colegio)
            if not (docente.es_director_de_grupo(curso) or AsignacionDocente.objects.filter(docente=docente, curso=curso).exists()):
                return None, None, None, "No tiene permisos para ver la sábana de este curso.", False
        except Docente.DoesNotExist:
            return None, None, None, "Acceso denegado. Su usuario no está registrado como docente.", False

    try:
        (sabana, areas, desempenos, mejores, resumen_celdas, resumen_global_niveles) = _get_sabana_acumulada_data(request.colegio, curso, periodo_ref)
        datos_completos = {
            'sabana_data': sabana, 'areas_con_materias': areas, 
            'desempenos_headers': desempenos, 'mejores_estudiantes': mejores,
            'resumen_final_celdas': resumen_celdas, 'resumen_global_niveles': resumen_global_niveles,
            'total_estudiantes': len(sabana)
        }
        return curso, periodo_ref, datos_completos, None, is_final_report
    except ValueError as ve:
        return None, None, None, str(ve), False
    except Exception as e:
        return None, None, None, f"Ocurrió un error inesperado al procesar los datos: {e}", False

@login_required
def generar_sabana_vista(request):
    curso, periodo_ref, datos_completos, error, is_final_report = _preparar_y_validar_sabana(request)
    if error:
        messages.error(request, error)
        return redirect('notas:selector_sabana')
    
    context = {
        'curso': curso, 
        'periodo': periodo_ref, 
        'colegio': request.colegio,
        'is_final_report': is_final_report,
        **datos_completos
    }
    return render(request, 'notas/sabana/sabana_template.html', context)

@login_required
def generar_sabana_pdf(request):
    if not PDF_SUPPORT:
        messages.error(request, "La funcionalidad de PDF no está disponible. Contacte al administrador.")
        return redirect('notas:selector_sabana')
        
    curso, periodo_ref, datos_completos, error, is_final_report = _preparar_y_validar_sabana(request)
    if error:
        return HttpResponse(f"Error al generar el PDF: {error}", status=400)
    
    context = {
        'curso': curso, 
        'periodo': periodo_ref, 
        'colegio': request.colegio,
        'is_final_report': is_final_report,
        **datos_completos
    }
    html_string = render_to_string('notas/sabana/sabana_pdf.html', context, request=request)
    
    try:
        pdf_file = HTML(string=html_string, base_url=request.build_absolute_uri()).write_pdf()
        response = HttpResponse(pdf_file, content_type='application/pdf')
        response['Content-Disposition'] = f'inline; filename="Sabana_{curso.nombre}_{periodo_ref.get_nombre_display()}.pdf"'
        return response
    except Exception as e:
        return HttpResponse(f"No se pudo generar el PDF. Error: {e}", status=500)

@login_required
def exportar_sabana_excel(request):
    curso, periodo_ref, datos_completos, error, _ = _preparar_y_validar_sabana(request)
    if error:
        messages.error(request, error)
        return redirect('notas:selector_sabana')
    return generar_excel_sabana(curso=curso, periodo=periodo_ref, **datos_completos)

@login_required
def selector_sabana_vista(request):
    if not request.colegio:
        return HttpResponseNotFound("<h1>Colegio no configurado para este dominio.</h1>")
    
    user = request.user
    cursos = []
    if es_admin_usuario(user):
        cursos = Curso.objects.filter(colegio=request.colegio).order_by('nombre')
    else:
        try:
            docente = Docente.objects.get(user=user, colegio=request.colegio)
            cursos_ids = AsignacionDocente.objects.filter(docente=docente, colegio=request.colegio).values_list('curso_id', flat=True).distinct()
            cursos = Curso.objects.filter(id__in=cursos_ids, colegio=request.colegio).order_by('nombre')
        except Docente.DoesNotExist:
            messages.error(request, "Acceso denegado. Su usuario no está registrado como docente.")
            return redirect('notas:dashboard')
            
    ano_actual = timezone.now().year
    periodos = PeriodoAcademico.objects.filter(colegio=request.colegio, ano_lectivo=ano_actual).order_by('fecha_inicio')
    
    context = {
        'cursos': cursos, 
        'periodos': periodos, 
        'colegio': request.colegio,
        'ano_actual': ano_actual
    }
    return render(request, 'notas/sabana/selector_sabana.html', context)
