# Este archivo contiene toda la lógica para el panel de estadísticas,
# unificando la lógica de cálculo de los boletines con las necesidades de las gráficas.

from collections import defaultdict
from decimal import Decimal, ROUND_HALF_UP
from django.db.models import Avg, Count, Case, When

# Se usa un solo punto (.) porque este archivo y 'models.py' están en la misma carpeta ('notas/').
from .models import (
    Estudiante, Calificacion, AsignacionDocente, AreaConocimiento, Materia,
    PeriodoAcademico, PonderacionAreaMateria, EscalaValoracion, Curso
)
import statistics
import random

# ===================================================================
# LÓGICA CENTRAL DE CÁLCULO
# ===================================================================

def _get_escala_valoracion(colegio):
    """Obtiene la escala de valoración configurada para el colegio o una por defecto."""
    escala = EscalaValoracion.objects.filter(colegio=colegio).order_by('valor_minimo')
    if escala.exists():
        colores_default = [
            '#dc3545', '#ffc107', '#198754', '#0d6efd'
        ]
        return [{'nombre': e.nombre_desempeno, 'min': e.valor_minimo, 'max': e.valor_maximo, 'color': colores_default[i % len(colores_default)]} for i, e in enumerate(escala)]
    return [
        {'nombre': 'BAJO', 'min': Decimal('1.0'), 'max': Decimal('2.9'), 'color': '#dc3545'},
        {'nombre': 'BASICO', 'min': Decimal('3.0'), 'max': Decimal('3.9'), 'color': '#ffc107'},
        {'nombre': 'ALTO', 'min': Decimal('4.0'), 'max': Decimal('4.5'), 'color': '#198754'},
        {'nombre': 'SUPERIOR', 'min': Decimal('4.6'), 'max': Decimal('5.0'), 'color': '#0d6efd'}
    ]

def _get_rendimiento_estudiantes_bulk(filtros):
    """
    Función principal y optimizada que calcula el rendimiento de un grupo de estudiantes.
    """
    colegio = filtros.get('colegio')

    estudiantes_qs = Estudiante.objects.filter(curso__colegio=colegio, is_active=True)
    if filtros.get('curso_ids'):
        estudiantes_qs = estudiantes_qs.filter(curso_id__in=filtros['curso_ids'])

    if not estudiantes_qs.exists():
        return {}

    estudiante_ids = list(estudiantes_qs.values_list('id', flat=True))

    calificaciones_filter = {
        'colegio': colegio,
        'estudiante_id__in': estudiante_ids,
        'tipo_nota': 'PROM_PERIODO'
    }
    if filtros.get('periodo_id'):
        calificaciones_filter['periodo_id'] = filtros['periodo_id']
    elif filtros.get('ano_lectivo'):
        calificaciones_filter['periodo__ano_lectivo'] = filtros['ano_lectivo']

    calificaciones_qs = Calificacion.objects.filter(**calificaciones_filter)
    calificaciones_map = {(c.estudiante_id, c.materia_id): c.valor_nota for c in calificaciones_qs}

    ponderaciones_qs = PonderacionAreaMateria.objects.filter(colegio=colegio).select_related('area')
    ponderaciones_map = defaultdict(list)
    areas_info = {}
    for p in ponderaciones_qs:
        ponderaciones_map[p.area_id].append({'materia_id': p.materia_id, 'peso': p.peso_porcentual})
        if p.area_id not in areas_info:
            areas_info[p.area_id] = p.area.nombre

    resultados_finales = {}
    for estudiante in estudiantes_qs.select_related('user', 'curso'):
        promedios_area = {}
        for area_id, materias_ponderadas in ponderaciones_map.items():
            suma_ponderada_area = Decimal('0.0')
            suma_pesos_area = Decimal('0.0')

            for p_info in materias_ponderadas:
                nota = calificaciones_map.get((estudiante.id, p_info['materia_id']))
                if nota is not None:
                    suma_ponderada_area += (nota * p_info['peso'])
                    suma_pesos_area += p_info['peso']

            if suma_pesos_area > 0:
                promedio_area = (suma_ponderada_area / suma_pesos_area).quantize(Decimal('0.1'), rounding=ROUND_HALF_UP)
                promedios_area[areas_info[area_id]] = promedio_area

        promedio_general = Decimal('0.0')
        if promedios_area:
            promedio_general = (sum(promedios_area.values()) / Decimal(len(promedios_area))).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

        resultados_finales[estudiante.id] = {
            'estudiante': estudiante,
            'promedio_general': promedio_general,
            'promedios_area': promedios_area
        }

    return resultados_finales

# ===================================================================
# FUNCIONES PÚBLICAS PARA LAS ESTADÍSTICAS
# ===================================================================

_cache_rendimiento = {}

def _get_datos_rendimiento_cached(filtros):
    """Función interna para usar una caché por petición y no recalcular."""
    items_for_key = []
    for key, value in filtros.items():
        if isinstance(value, list):
            items_for_key.append((key, tuple(sorted(value))))
        else:
            items_for_key.append((key, value))

    cache_key = tuple(sorted(items_for_key, key=lambda x: str(x[0])))

    if cache_key not in _cache_rendimiento:
        _cache_rendimiento[cache_key] = _get_rendimiento_estudiantes_bulk(filtros)
    return _cache_rendimiento[cache_key]

def get_rendimiento_general(filtros=None):
    if filtros is None: filtros = {}
    datos_rendimiento_crudo = _get_datos_rendimiento_cached(filtros)

    promedios_finales = [data['promedio_general'] for data in datos_rendimiento_crudo.values() if data['promedio_general'] > 0]
    total_estudiantes = len(promedios_finales)

    escala = _get_escala_valoracion(filtros.get('colegio'))
    distribucion = []
    for nivel in escala:
        total_nivel = sum(1 for p in promedios_finales if nivel['min'] <= p <= nivel['max'])
        porcentaje = (total_nivel / total_estudiantes * 100) if total_estudiantes > 0 else 0
        distribucion.append({
            'nombre': nivel['nombre'],
            'total': total_nivel,
            'color': nivel['color'],
            'porcentaje': porcentaje
        })

    promedios_as_floats = [float(p) for p in promedios_finales]
    promedio_general_grupo = statistics.mean(promedios_as_floats) if promedios_as_floats else 0.0
    desviacion_estandar = statistics.stdev(promedios_as_floats) if len(promedios_as_floats) > 1 else 0.0

    return {
        'distribucion': distribucion,
        'promedio_general': round(promedio_general_grupo, 2),
        'desviacion_estandar': round(desviacion_estandar, 2)
    }

def get_distribucion_por_area(filtros=None):
    if filtros is None: filtros = {}
    datos_crudo = _get_datos_rendimiento_cached(filtros)
    if not datos_crudo: return []

    escala = _get_escala_valoracion(filtros.get('colegio'))
    promedios_por_area = defaultdict(list)

    for data in datos_crudo.values():
        for area_nombre, promedio in data.get('promedios_area', {}).items():
            if promedio > 0:
                promedios_por_area[area_nombre].append(promedio)
    
    resultado_final = []
    for area_nombre, promedios in sorted(promedios_por_area.items()):
        total_estudiantes_area = len(promedios)
        if total_estudiantes_area == 0: continue

        distribucion_area = []
        for nivel in escala:
            total_nivel = sum(1 for p in promedios if nivel['min'] <= p <= nivel['max'])
            porcentaje = (total_nivel / total_estudiantes_area * 100) if total_estudiantes_area > 0 else 0
            distribucion_area.append({
                'nombre': nivel['nombre'],
                'total': total_nivel,
                'porcentaje': porcentaje
            })
        
        promedio_general_area = sum(promedios) / total_estudiantes_area
        resultado_final.append({
            'area_nombre': area_nombre,
            'promedio': float(promedio_general_area),
            'total_estudiantes': total_estudiantes_area,
            'distribucion': distribucion_area
        })
    return resultado_final

def get_distribucion_por_materia(filtros=None):
    if filtros is None: filtros = {}
    base_query = _get_base_query(filtros)
    escala = _get_escala_valoracion(filtros.get('colegio'))
    
    materias_qs = Materia.objects.filter(id__in=base_query.values_list('materia_id', flat=True).distinct()).order_by('nombre')
    resultado_final = []

    for materia in materias_qs:
        notas_materia = list(base_query.filter(materia=materia).values_list('valor_nota', flat=True))
        total_estudiantes_materia = len(notas_materia)
        if total_estudiantes_materia == 0: continue

        distribucion_materia = []
        for nivel in escala:
            total_nivel = sum(1 for nota in notas_materia if nivel['min'] <= nota <= nivel['max'])
            porcentaje = (total_nivel / total_estudiantes_materia * 100) if total_estudiantes_materia > 0 else 0
            distribucion_materia.append({
                'nombre': nivel['nombre'],
                'total': total_nivel,
                'porcentaje': porcentaje
            })
        
        promedio_materia = sum(notas_materia) / total_estudiantes_materia
        resultado_final.append({
            'materia_nombre': materia.nombre,
            'promedio': float(promedio_materia),
            'total_estudiantes': total_estudiantes_materia,
            'distribucion': distribucion_materia
        })
    return resultado_final


def get_cuadro_honor(filtros=None):
    if filtros is None or not filtros.get('curso_ids'): return []
    datos_rendimiento_crudo = _get_datos_rendimiento_cached(filtros)

    ranking = [
        {'nombre': f"{data['estudiante'].user.first_name} {data['estudiante'].user.last_name}".strip(),
         'curso': data['estudiante'].curso.nombre,
         'promedio': float(data['promedio_general'])}
        for data in datos_rendimiento_crudo.values() if data['promedio_general'] > 0
    ]
    ranking.sort(key=lambda x: x['promedio'], reverse=True)
    return [{'puesto': i + 1, **item} for i, item in enumerate(ranking[:3])]

def get_ranking_cursos(filtros=None):
    if filtros is None: filtros = {}
    datos_rendimiento_crudo = _get_datos_rendimiento_cached(filtros)

    promedios_por_curso = defaultdict(list)
    for data in datos_rendimiento_crudo.values():
        if data['promedio_general'] > 0:
            promedios_por_curso[data['estudiante'].curso_id].append(data['promedio_general'])

    ranking_data = [
        {'curso_id': curso_id, 'promedio': float(sum(promedios) / len(promedios))}
        for curso_id, promedios in promedios_por_curso.items() if promedios
    ]
    ranking_data.sort(key=lambda x: x['promedio'], reverse=True)
    return {r['curso_id']: i + 1 for i, r in enumerate(ranking_data)}, len(ranking_data)

# ===================================================================
# FUNCIONES RESTANTES
# ===================================================================

def _get_base_query(filtros):
    base_query = Calificacion.objects.filter(tipo_nota='PROM_PERIODO')
    if filtros.get('colegio'):
        base_query = base_query.filter(estudiante__curso__colegio=filtros['colegio'])
    if filtros.get('ano_lectivo'):
        base_query = base_query.filter(periodo__ano_lectivo=filtros['ano_lectivo'])
    if filtros.get('curso_ids'):
        base_query = base_query.filter(estudiante__curso__id__in=filtros['curso_ids'])
    if filtros.get('periodo_id'):
        base_query = base_query.filter(periodo_id=filtros['periodo_id'])
    if filtros.get('area_id'):
        base_query = base_query.filter(materia__areas_ponderadas__id=filtros['area_id'])
    if filtros.get('materia_id'):
        base_query = base_query.filter(materia_id=filtros['materia_id'])
    return base_query

def get_promedios_por_materia(filtros=None):
    if filtros is None: filtros = {}
    base_query = _get_base_query(filtros)
    promedios = base_query.values('materia__nombre').annotate(promedio=Avg('valor_nota')).order_by('materia__nombre')
    return [{'materia_nombre': r['materia__nombre'], 'promedio': float(r['promedio'] or 0)} for r in promedios]

def get_promedios_por_area_apilado(filtros=None):
    if filtros is None: filtros = {}
    base_query = _get_base_query(filtros)

    materias_query = Materia.objects.filter(colegio=filtros.get('colegio'))
    if filtros.get('curso_ids'):
        materia_ids = AsignacionDocente.objects.filter(curso_id__in=filtros['curso_ids']).values_list('materia_id', flat=True).distinct()
        materias_query = materias_query.filter(id__in=materia_ids)

    materias_relevantes = list(materias_query.order_by('nombre'))
    nombres_materias_relevantes = [m.nombre for m in materias_relevantes]

    areas_query = AreaConocimiento.objects.filter(colegio=filtros.get('colegio'), materias__in=materias_relevantes).distinct()
    if filtros.get('area_id'):
        areas_query = areas_query.filter(id=filtros['area_id'])

    areas = areas_query.order_by('nombre')
    area_nombres = [a.nombre for a in areas]

    if not area_nombres or not nombres_materias_relevantes:
        return {'labels': [], 'datasets': []}

    ponderaciones = PonderacionAreaMateria.objects.filter(colegio=filtros.get('colegio'), area__in=areas, materia__in=materias_relevantes)
    ponderaciones_map = {(p.area.nombre, p.materia.nombre): float(p.peso_porcentual) for p in ponderaciones}

    promedios_db = base_query.filter(materia__in=materias_relevantes).values('materia__nombre').annotate(prom=Avg('valor_nota'))
    promedios_map_db = {p['materia__nombre']: float(p['prom'] or 0.0) for p in promedios_db}

    datasets = []
    colores = [f'rgba({random.randint(30,220)},{random.randint(30,220)},{random.randint(30,220)},0.8)' for _ in nombres_materias_relevantes]

    for idx, materia_nombre in enumerate(nombres_materias_relevantes):
        data, percent_map, tiene_datos_reales = [], [], False
        original_scores = []
        for area_nombre in area_nombres:
            prom = promedios_map_db.get(materia_nombre, 0.0)
            original_scores.append(round(prom, 1))

            peso = ponderaciones_map.get((area_nombre, materia_nombre), 0.0)
            segmento = (prom * peso) / 100.0 if prom and peso else 0.0
            data.append(round(segmento, 1))
            percent_map.append(peso)
            if segmento > 0: tiene_datos_reales = True

        if tiene_datos_reales:
            datasets.append({
                'label': materia_nombre,
                'data': data,
                'backgroundColor': colores[idx],
                'percentMap': percent_map,
                'originalScores': original_scores
            })

    return {'labels': area_nombres, 'datasets': datasets}

def get_histograma_distribucion(filtros=None):
    if filtros is None: filtros = {}
    base_query = _get_base_query(filtros)
    notas = [float(n) for n in base_query.values_list('valor_nota', flat=True)]
    if not notas: return {'labels': [], 'data': [], 'colors': []}

    bins = [1, 1.5, 2, 2.5, 3, 3.5, 4, 4.5, 5.1]
    hist = [0] * (len(bins) - 1)
    for n in notas:
        for i in range(len(bins) - 1):
            if bins[i] <= n < bins[i+1]:
                hist[i] += 1
                break
    labels = [f"{bins[i]:.1f}-{bins[i+1]-0.1:.1f}" for i in range(len(hist))]
    colors = [f'rgba({random.randint(100,200)}, {random.randint(100,200)}, {random.randint(100,200)}, 0.8)' for _ in hist]
    return {'labels': labels, 'data': hist, 'colors': colors}

def get_reprobados_por_docente(filtros=None):
    base_query = _get_base_query(filtros).filter(valor_nota__lt=3.0)
    docentes = base_query.values('docente__user__first_name', 'docente__user__last_name').annotate(total=Count('id')).order_by('-total')
    return [(f"{r['docente__user__first_name'] or ''} {r['docente__user__last_name'] or ''}".strip(), r['total']) for r in docentes if r['total'] > 0]

def get_materias_reprobadas(filtros=None):
    base_query = _get_base_query(filtros).filter(valor_nota__lt=3.0)
    materias = base_query.values('materia__nombre').annotate(total_reprobados=Count('id')).order_by('-total_reprobados')
    return [r for r in materias if r['total_reprobados'] > 0]

def get_reprobados_por_area_materia(filtros=None):
    reprobados = _get_base_query(filtros).filter(valor_nota__lt=3.0).values('materia__nombre', 'materia__areas_ponderadas__nombre').annotate(total=Count('id'))
    if not reprobados: return {'labels': [], 'datasets': []}

    areas = sorted(list(set(r['materia__areas_ponderadas__nombre'] for r in reprobados if r['materia__areas_ponderadas__nombre'])))
    materias = sorted(list(set(r['materia__nombre'] for r in reprobados if r['materia__nombre'])))
    if not areas or not materias: return {'labels': [], 'datasets': []}

    data_map = {m: {a: 0 for a in areas} for m in materias}
    for r in reprobados:
        if r['materia__nombre'] in data_map and r['materia__areas_ponderadas__nombre'] in data_map[r['materia__nombre']]:
            data_map[r['materia__nombre']][r['materia__areas_ponderadas__nombre']] = r['total']

    datasets = []
    for mat in materias:
        color = f'rgba({random.randint(150, 255)}, {random.randint(120, 220)}, {random.randint(120, 220)}, 0.75)'
        datasets.append({'label': mat, 'data': [data_map[mat][area] for area in areas], 'backgroundColor': color, 'stack': 'Stack 0'})
    return {'labels': areas, 'datasets': datasets}

def get_materias_reprobadas_por_docente(filtros=None):
    reprobadas = _get_base_query(filtros).filter(valor_nota__lt=3.0).values('docente__user__first_name', 'docente__user__last_name', 'materia__nombre').annotate(total_reprobados=Count('id')).order_by('docente__user__last_name', 'materia__nombre')
    return [{'docente': f"{r['docente__user__first_name'] or ''} {r['docente__user__last_name'] or ''}".strip(), 'materia': r['materia__nombre'], 'total_reprobados': r['total_reprobados']} for r in reprobadas if r['total_reprobados'] > 0]

def get_promedios_por_area(filtros=None):
    """Calcula el promedio general para cada área de conocimiento."""
    if filtros is None: filtros = {}
    datos_crudo = _get_datos_rendimiento_cached(filtros)
    if not datos_crudo:
        return []

    promedios_agregados = defaultdict(list)
    for data in datos_crudo.values():
        for area, promedio in data['promedios_area'].items():
            promedios_agregados[area].append(promedio)

    resultado_final = []
    for area, promedios in promedios_agregados.items():
        if promedios:
            promedio_final = sum(promedios) / len(promedios)
            resultado_final.append({'area_nombre': area, 'promedio': float(promedio_final)})

    return sorted(resultado_final, key=lambda x: x['area_nombre'])


# ---------------------------------------------------------------------------
# RESÚMENES SEPARADOS: ÁREA POR UN LADO, ASIGNATURA POR OTRO
# ---------------------------------------------------------------------------
# Antes área y asignatura salían mezcladas en las mismas gráficas. Estas dos
# funciones devuelven cada cosa por aparte, con las mismas columnas, para
# poder compararlas de un vistazo.
#
# Ojo: el resto del módulo da por hecho que se reprueba con menos de 3.0.
# Aquí se usa la nota de aprobación configurada en el colegio, que es lo
# correcto cuando la escala no es sobre 5.0.

def _nota_minima_aprobacion(colegio):
    from notas.boletin.ponderacion import nota_aprobacion
    return nota_aprobacion(colegio)


def get_resumen_por_asignatura(filtros=None):
    """Una fila por asignatura: promedio, evaluados, reprobados y % de pérdida."""
    if filtros is None: filtros = {}
    minima = _nota_minima_aprobacion(filtros.get('colegio'))
    base = _get_base_query(filtros)

    totales = {r['materia__nombre']: r for r in base.values('materia__nombre')
               .annotate(promedio=Avg('valor_nota'), evaluados=Count('id'))}
    perdidas = {r['materia__nombre']: r['n'] for r in base.filter(valor_nota__lt=minima)
                .values('materia__nombre').annotate(n=Count('id'))}

    filas = []
    for nombre, r in totales.items():
        evaluados = r['evaluados'] or 0
        reprobados = perdidas.get(nombre, 0)
        filas.append({
            'nombre': nombre or 'Sin nombre',
            'promedio': round(float(r['promedio'] or 0), 2),
            'evaluados': evaluados,
            'reprobados': reprobados,
            'porcentaje': round(reprobados * 100.0 / evaluados, 1) if evaluados else 0.0,
        })
    return sorted(filas, key=lambda f: f['promedio'])


def get_resumen_por_area(filtros=None):
    """Lo mismo que el anterior, pero por área.

    El promedio del área NO es el promedio simple de sus asignaturas: se toma
    el que ya calcula el módulo respetando la ponderación de cada materia
    dentro del área, para que coincida con el boletín.
    """
    if filtros is None: filtros = {}
    minima = float(_nota_minima_aprobacion(filtros.get('colegio')))
    datos = _get_datos_rendimiento_cached(filtros)
    if not datos:
        return []

    acumulado = defaultdict(list)
    for d in datos.values():
        for area, promedio in d['promedios_area'].items():
            acumulado[area].append(float(promedio))

    filas = []
    for area, valores in acumulado.items():
        reprobados = sum(1 for v in valores if v < minima)
        filas.append({
            'nombre': area,
            'promedio': round(sum(valores) / len(valores), 2) if valores else 0.0,
            'evaluados': len(valores),
            'reprobados': reprobados,
            'porcentaje': round(reprobados * 100.0 / len(valores), 1) if valores else 0.0,
        })
    return sorted(filas, key=lambda f: f['promedio'])


# ---------------------------------------------------------------------------
# CAJA Y BIGOTES
# ---------------------------------------------------------------------------
# ApexCharts espera, para cada caja: {x: 'nombre', y: [min, Q1, mediana, Q3, max]}.
# Hasta ahora al gráfico se le estaba pasando el resultado de
# get_distribucion_por_materia(), que tiene otra forma (nombre, promedio,
# distribución), así que el gráfico no podía dibujar nada.

def _caja(valores):
    """Los cinco números de una caja: mínimo, Q1, mediana, Q3, máximo."""
    datos = sorted(float(v) for v in valores if v is not None)
    if len(datos) < 2:
        return None
    mitad = len(datos) // 2
    inferior = datos[:mitad]
    superior = datos[mitad + 1:] if len(datos) % 2 else datos[mitad:]
    q1 = statistics.median(inferior) if inferior else datos[0]
    q3 = statistics.median(superior) if superior else datos[-1]
    return [round(datos[0], 2), round(q1, 2), round(statistics.median(datos), 2),
            round(q3, 2), round(datos[-1], 2)]


def get_caja_por_asignatura(filtros=None):
    """Distribución de notas de cada asignatura, lista para ApexCharts."""
    if filtros is None: filtros = {}
    base = _get_base_query(filtros)
    cajas = defaultdict(list)
    for nombre, nota in base.values_list('materia__nombre', 'valor_nota'):
        if nota is not None:
            cajas[nombre or 'Sin nombre'].append(nota)

    salida = []
    for nombre, valores in sorted(cajas.items()):
        caja = _caja(valores)
        if caja:
            salida.append({'x': nombre, 'y': caja})
    return salida


def get_caja_por_area(filtros=None):
    """Lo mismo, pero con el promedio de cada estudiante en cada área."""
    if filtros is None: filtros = {}
    datos = _get_datos_rendimiento_cached(filtros)
    if not datos:
        return []
    cajas = defaultdict(list)
    for d in datos.values():
        for area, promedio in d.get('promedios_area', {}).items():
            if promedio and promedio > 0:
                cajas[area].append(promedio)

    salida = []
    for nombre, valores in sorted(cajas.items()):
        caja = _caja(valores)
        if caja:
            salida.append({'x': nombre, 'y': caja})
    return salida


# ---------------------------------------------------------------------------
# CONCLUSIONES DE LAS VISTAS NUEVAS
# ---------------------------------------------------------------------------
# Frases cortas, en el mismo tono de las que ya genera el panel. La idea no es
# interpretar por el docente, es señalarle dónde mirar primero.

def conclusiones_resumen(filas, singular, plural):
    """Lee un resumen por área o por asignatura y señala lo que salta a la vista."""
    if not filas:
        return [f"No hay datos de {plural} para los filtros seleccionados."]

    frases = []
    peor, mejor = filas[0], filas[-1]          # vienen ordenadas por promedio
    total_eval = sum(f['evaluados'] for f in filas)
    total_rep = sum(f['reprobados'] for f in filas)

    frases.append(
        f"Se analizaron {len(filas)} {plural} con {total_eval} valoraciones en total."
    )
    frases.append(
        f"El promedio más bajo es el de <strong>{peor['nombre']}</strong> "
        f"({peor['promedio']}), y el más alto el de <strong>{mejor['nombre']}</strong> "
        f"({mejor['promedio']})."
    )
    if total_eval:
        frases.append(
            f"La pérdida general es del {round(total_rep * 100.0 / total_eval, 1)}% "
            f"({total_rep} de {total_eval})."
        )

    criticas = [f for f in filas if f['porcentaje'] >= 30]
    if criticas:
        nombres = ", ".join(f"{f['nombre']} ({f['porcentaje']}%)" for f in criticas[:4])
        frases.append(
            f"{len(criticas)} {plural if len(criticas) > 1 else singular} "
            f"con pérdida igual o superior al 30%: {nombres}."
        )
    else:
        frases.append(f"Ninguna {singular} supera el 30% de pérdida.")

    limpias = [f['nombre'] for f in filas if f['reprobados'] == 0]
    if limpias:
        frases.append(f"Sin reprobados: {', '.join(limpias[:5])}.")
    return frases


def conclusiones_anotaciones(anot, automaticas=None):
    """Lo mismo para el bloque de anotaciones del observador."""
    if not anot or not anot.get('total'):
        return ["No hay anotaciones registradas para los filtros seleccionados."]

    total = anot['total']
    pos, neg = anot['positivas'], anot['negativas']
    sin = anot['sin_clasificar']
    frases = [f"Hay {total} anotación(es) en el periodo y los cursos seleccionados."]

    if pos or neg:
        if neg > pos:
            frases.append(
                f"Predominan las negativas: {neg} frente a {pos} positivas "
                f"({round(neg * 100.0 / total)}% del total)."
            )
        elif pos > neg:
            frases.append(
                f"Predominan las positivas: {pos} frente a {neg} negativas. "
                f"Se está reconociendo lo bueno tanto como se señalan las faltas."
            )
        else:
            frases.append(f"Hay tantas positivas como negativas ({pos} de cada una).")

    acad = sum(anot['matriz']['ACADEMICA'].values())
    conv = sum(anot['matriz']['COMPORTAMENTAL'].values())
    if acad or conv:
        cual = "académicas" if acad > conv else "de convivencia"
        frases.append(f"La mayoría son {cual} ({max(acad, conv)} de {total}).")

    cursos = anot.get('por_curso') or []
    if len(cursos) > 1:
        top = max(cursos, key=lambda c: c['total'])
        frases.append(
            f"El curso con más anotaciones es <strong>{top['curso']}</strong> "
            f"({top['total']})."
        )

    if sin:
        frases.append(
            f"Quedan {sin} anotación(es) sin clasificar como positiva o negativa. "
            f"Conviene revisarlas para que el conteo quede completo."
        )
    if automaticas and automaticas.get('total'):
        frases.append(
            f"Aparte, el sistema generó {automaticas['total']} observación(es) "
            f"automáticas por bajo rendimiento, que no entran en este conteo."
        )
    return frases
