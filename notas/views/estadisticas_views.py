from django.shortcuts import render
from django.http import JsonResponse, HttpResponseForbidden, HttpResponseNotFound, HttpResponse
from django.contrib.auth.decorators import user_passes_test
from django.template.loader import render_to_string
import datetime
import random
from decimal import Decimal
import re # Importamos el módulo de expresiones regulares

# Asegúrate de tener WeasyPrint instalado: pip install WeasyPrint
try:
    from weasyprint import HTML
except ImportError:
    HTML = None # Manejar el caso si no está instalado

from ..models import (
    Sede, Curso, PeriodoAcademico, Docente, AsignacionDocente, Materia,
    AreaConocimiento as Area, Estudiante
)

from ..estadisticas_logic import (
    get_rendimiento_general, get_promedios_por_materia,
    get_ranking_cursos, get_histograma_distribucion,
    get_reprobados_por_docente, get_materias_reprobadas,
    get_reprobados_por_area_materia, get_promedios_por_area_apilado,
    get_materias_reprobadas_por_docente,
    get_cuadro_honor, _cache_rendimiento,
    get_distribucion_por_area, get_distribucion_por_materia, # <-- Importamos las nuevas funciones
    _get_escala_valoracion # Importamos para obtener los encabezados de la escala
)

import io
import base64
import matplotlib
matplotlib.use('Agg') # Backend no interactivo para servidores
import matplotlib.pyplot as plt
import numpy as np


def generar_grafico_reprobados_area(datos_grafico):
    """
    Genera un gráfico de barras apilado y lo devuelve como una imagen en base64.
    """
    if not datos_grafico or not datos_grafico.get('labels') or not datos_grafico.get('datasets'):
        return None

    labels = datos_grafico['labels']
    datasets = datos_grafico['datasets']
    materias = [d['label'] for d in datasets]

    data = {m: [0]*len(labels) for m in materias}
    for d in datasets:
        data[d['label']] = d['data']

    # Ajustado para layout vertical
    fig, ax = plt.subplots(figsize=(7, 5))
    bottom = np.zeros(len(labels))

    # plt.cm.get_cmap quedó obsoleta en matplotlib 3.7 y desaparece en la 3.11.
    # Esta forma funciona en las versiones nuevas y en las viejas.
    try:
        colors = matplotlib.colormaps['tab20'].resampled(len(materias))
    except AttributeError:
        colors = plt.cm.get_cmap('tab20', len(materias))

    for i, (materia, counts) in enumerate(data.items()):
        counts_np = np.array(counts)
        p = ax.bar(labels, counts_np, label=materia, bottom=bottom, color=colors(i))
        bottom += counts_np

    ax.set_title('Reprobados por Área y Materia', fontsize=12)
    ax.set_ylabel('Nº Estudiantes Reprobados', fontsize=10)
    ax.legend(title='Materias', bbox_to_anchor=(1.02, 1), loc='upper left', fontsize=8)
    fig.subplots_adjust(right=0.75) # Ajustar para dar espacio a la leyenda

    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight')
    plt.close(fig)
    image_base64 = base64.b64encode(buf.getvalue()).decode('utf-8')
    return image_base64

# --- Gráficas de las vistas nuevas, para el PDF -----------------------------
# El PDF lo arma WeasyPrint, que no ejecuta JavaScript: aquí las gráficas se
# dibujan con matplotlib y se incrustan como imagen. Los mismos colores que en
# pantalla, elegidos para que se distingan también con daltonismo y en blanco
# y negro, y cada barra lleva su número escrito.
VERDE, ROJO, AMBAR, AZUL = '#0b8a5b', '#a4161a', '#8a6d00', '#1d4ed8'


def _a_base64(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight', dpi=110)
    plt.close(fig)
    return base64.b64encode(buf.getvalue()).decode('utf-8')


def generar_grafico_barras_resumen(filas, titulo):
    """Barras horizontales con el promedio de cada área o asignatura."""
    if not filas:
        return None
    datos = sorted(filas, key=lambda f: f['promedio'])
    nombres = [f['nombre'] for f in datos]
    valores = [f['promedio'] for f in datos]
    colores = [ROJO if f['porcentaje'] >= 30 else AZUL for f in datos]

    fig, ax = plt.subplots(figsize=(7, max(2.2, 0.42 * len(datos) + 1)))
    barras = ax.barh(nombres, valores, color=colores)
    ax.set_xlim(0, 5.2)
    ax.set_xlabel('Promedio', fontsize=9)
    ax.set_title(titulo, fontsize=12)
    ax.bar_label(barras, fmt='%.2f', padding=3, fontsize=8)
    ax.spines[['top', 'right']].set_visible(False)
    return _a_base64(fig)


def generar_grafico_torta_aprobacion(filas, titulo):
    """Aprobados frente a reprobados, en total."""
    if not filas:
        return None
    evaluados = sum(f['evaluados'] for f in filas)
    reprobados = sum(f['reprobados'] for f in filas)
    if evaluados <= 0:
        return None

    fig, ax = plt.subplots(figsize=(4.2, 4.2))
    ax.pie([evaluados - reprobados, reprobados],
           labels=['Aprobados', 'Reprobados'], colors=[VERDE, ROJO],
           autopct=lambda p: f'{p:.0f}%\n({round(p * evaluados / 100)})',
           textprops={'fontsize': 9, 'color': '#222'},
           wedgeprops={'edgecolor': 'white', 'linewidth': 2})
    ax.set_title(titulo, fontsize=12)
    return _a_base64(fig)


def generar_grafico_caja(cajas, titulo):
    """Caja y bigotes a partir de los cinco números ya calculados."""
    if not cajas:
        return None
    estadisticas = [{
        'label': c['x'], 'whislo': c['y'][0], 'q1': c['y'][1],
        'med': c['y'][2], 'q3': c['y'][3], 'whishi': c['y'][4], 'fliers': [],
    } for c in cajas]

    fig, ax = plt.subplots(figsize=(7, max(2.5, 0.45 * len(cajas) + 1.5)))
    ax.bxp(estadisticas, vert=False, showfliers=False,
           boxprops={'facecolor': '#c7d7f7', 'edgecolor': '#36507e'},
           medianprops={'color': '#a4161a', 'linewidth': 2},
           patch_artist=True)
    ax.set_xlim(1, 5)
    ax.set_xlabel('Nota', fontsize=9)
    ax.set_title(titulo, fontsize=12)
    ax.spines[['top', 'right']].set_visible(False)
    return _a_base64(fig)


def generar_grafico_barras_anotaciones(anot):
    """Anotaciones por curso, apiladas en positivas / negativas / sin clasificar."""
    cursos = (anot or {}).get('por_curso') or []
    if not cursos:
        return None
    nombres = [c['curso'] for c in cursos]
    def suma(c, sub):
        return c['detalle']['ACADEMICA'][sub] + c['detalle']['COMPORTAMENTAL'][sub]

    series = [('Positivas', [suma(c, 'POSITIVA') for c in cursos], VERDE),
              ('Negativas', [suma(c, 'NEGATIVA') for c in cursos], ROJO),
              ('Sin clasificar', [suma(c, 'SIN_CLASIFICAR') for c in cursos], AMBAR)]

    fig, ax = plt.subplots(figsize=(7, max(2.5, 0.4 * len(cursos) + 1.8)))
    base = np.zeros(len(cursos))
    for etiqueta, valores, color in series:
        v = np.array(valores)
        ax.bar(nombres, v, bottom=base, label=etiqueta, color=color,
               edgecolor='white', linewidth=1.5)
        base += v
    ax.set_ylabel('Nº de anotaciones', fontsize=9)
    ax.set_title('Anotaciones por Curso', fontsize=12)
    ax.legend(fontsize=8)
    ax.spines[['top', 'right']].set_visible(False)
    return _a_base64(fig)


def generar_grafico_torta_anotaciones(anot):
    if not anot or not anot.get('total'):
        return None
    valores = [anot['positivas'], anot['negativas'], anot['sin_clasificar']]
    etiquetas = ['Positivas', 'Negativas', 'Sin clasificar']
    presentes = [(e, v) for e, v in zip(etiquetas, valores) if v > 0]
    if not presentes:
        return None
    colores = {'Positivas': VERDE, 'Negativas': ROJO, 'Sin clasificar': AMBAR}

    fig, ax = plt.subplots(figsize=(4.2, 4.2))
    ax.pie([v for _, v in presentes], labels=[e for e, _ in presentes],
           colors=[colores[e] for e, _ in presentes],
           autopct=lambda p: f'{p:.0f}%', textprops={'fontsize': 9},
           wedgeprops={'edgecolor': 'white', 'linewidth': 2})
    ax.set_title('Positivas frente a Negativas', fontsize=12)
    return _a_base64(fig)


def generar_grafico_distribucion(datos_distribucion):
    """
    Genera un gráfico de torta para la distribución de rendimiento.
    """
    data_filtrada = [d for d in datos_distribucion if d.get('total', 0) > 0]
    if not data_filtrada:
        return None

    labels = [d['nombre'] for d in data_filtrada]
    sizes = [d['total'] for d in data_filtrada]
    colors = [d['color'] for d in data_filtrada]

    # Ajustado para layout vertical
    fig, ax = plt.subplots(figsize=(5, 4))
    ax.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%',
           startangle=90, pctdistance=0.85, textprops={'fontsize': 8})

    centre_circle = plt.Circle((0,0),0.70,fc='white')
    fig.gca().add_artist(centre_circle)

    ax.axis('equal')
    plt.title('Distribución de Rendimiento', pad=10, fontsize=12)

    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight')
    plt.close(fig)
    image_base64 = base64.b64encode(buf.getvalue()).decode('utf-8')
    return image_base64

def generar_grafico_promedios_area_apilado(datos_grafico):
    """
    Genera un gráfico de barras apilado para promedios por área y lo devuelve como una imagen en base64.
    """
    if not datos_grafico or not datos_grafico.get('labels') or not datos_grafico.get('datasets'):
        return None

    labels = datos_grafico['labels']
    datasets = [d for d in datos_grafico['datasets'] if any(val > 0 for val in d.get('data', []))]
    
    if not datasets:
        return None

    def rgba_to_matplotlib(rgba_string):
        """Convierte una cadena 'rgba(r,g,b,a)' a una tupla compatible con Matplotlib (r/255, g/255, b/255, a)."""
        try:
            match = re.match(r'rgba\((\d+),(\d+),(\d+),([\d.]+)\)', rgba_string)
            if match:
                r, g, b, a = map(float, match.groups())
                return (r / 255.0, g / 255.0, b / 255.0, a)
        except (ValueError, TypeError):
            pass
        return (random.random(), random.random(), random.random(), 0.8)

    # Ajustado para layout de ancho completo
    fig, ax = plt.subplots(figsize=(8, 6)) # Más ancho y un poco más alto
    bottom = np.zeros(len(labels))

    original_colors = [d.get('backgroundColor') for d in datasets]
    colors = [rgba_to_matplotlib(c) if isinstance(c, str) else c for c in original_colors]

    for i, d in enumerate(datasets):
        materia = d['label']
        counts = np.array(d['data'])
        p = ax.bar(labels, counts, label=materia, bottom=bottom, color=colors[i])
        bottom += counts

    for i, total in enumerate(bottom):
        if total > 0:
            ax.text(i, total + 0.05, f'Σ {total:.1f}', ha='center', va='bottom', fontsize=8, weight='bold')

    ax.set_title('Promedio Ponderado por Área y Asignatura', fontsize=14, pad=15)
    ax.set_ylabel('Promedio Ponderado', fontsize=10)
    ax.set_xlabel('Áreas de Conocimiento', fontsize=10)
    ax.legend(title='Asignaturas', bbox_to_anchor=(1.02, 1), loc='upper left', fontsize=9)
    ax.set_ylim(top=max(5.5, max(bottom) * 1.15 if any(bottom) else 5.5))
    ax.set_yticks(np.arange(0, 5.1, 0.5))
    plt.xticks(rotation=20, ha="right", fontsize=9)
    ax.tick_params(axis='y', labelsize=9)
    fig.tight_layout(rect=[0, 0, 0.85, 1]) # Ajustar para dar espacio a la leyenda

    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight')
    plt.close(fig)
    return base64.b64encode(buf.getvalue()).decode('utf-8')


def generar_conclusiones_texto(
    datos_rendimiento, datos_por_materia, total_estudiantes,
    tipo_grafico=None, datos_reprobados_docente=None,
    datos_materias_reprobadas=None, datos_reprobados_area_materia=None,
    datos_promedios_area_apilado=None, colegio=None,
    datos_materias_reprobadas_por_docente=None
):
    conclusiones = []
    if total_estudiantes == 0:
        return ["No hay datos suficientes para generar conclusiones con los filtros actuales."]

    promedio = datos_rendimiento.get('promedio_general')

    if tipo_grafico == 'general' or tipo_grafico is None:
        if promedio is not None:
            conclusiones.append(f"El promedio general de los <strong>{total_estudiantes}</strong> estudiantes evaluados es de <strong>{promedio:.1f}</strong>.")
        if datos_rendimiento.get('distribucion'):
            dist = datos_rendimiento['distribucion']
            mejor = max(dist, key=lambda x: x['total']) if any(d['total'] > 0 for d in dist) else None
            peor = min([x for x in dist if x['total'] > 0], key=lambda x: x['total'], default=None)
            if mejor and mejor['total'] > 0:
                conclusiones.append(f"La mayoría de estudiantes se encuentra en el desempeño <strong>{mejor['nombre']}</strong>.")
            if peor and mejor and peor['nombre'] != mejor['nombre']:
                conclusiones.append(f"El menor porcentaje de estudiantes está en el nivel <strong>{peor['nombre']}</strong>.")

        if datos_promedios_area_apilado and datos_promedios_area_apilado.get('labels') and colegio:
            areas = datos_promedios_area_apilado['labels']
            datasets = datos_promedios_area_apilado['datasets']
            if areas and datasets:
                promedios_finales_area = []
                for i, area_nombre in enumerate(areas):
                    total_area = sum(ds['data'][i] for ds in datasets if len(ds['data']) > i)
                    if total_area > 0 or any(ds['data'][i] > 0 for ds in datasets if len(ds['data']) > i):
                        promedios_finales_area.append((area_nombre, total_area))
                if promedios_finales_area:
                    area_max = max(promedios_finales_area, key=lambda x: x[1])
                    area_min = min(promedios_finales_area, key=lambda x: x[1])
                    conclusiones.append(f"El área con mayor promedio general es <strong>{area_max[0]}</strong> ({area_max[1]:.1f}).")
                    if area_max[0] != area_min[0]:
                        conclusiones.append(f"El área con menor promedio general es <strong>{area_min[0]}</strong> ({area_min[1]:.1f}).")

    elif tipo_grafico == 'reprobados_docente':
        if datos_reprobados_docente and len(datos_reprobados_docente) > 0:
            docente_mas = max(datos_reprobados_docente, key=lambda x: x[1])
            docente_menos = min(datos_reprobados_docente, key=lambda x: x[1])
            conclusiones.append(f"El docente con más reprobados es <strong>{docente_mas[0]}</strong> con <strong>{docente_mas[1]}</strong> estudiantes.")
            if docente_mas[0] != docente_menos[0]:
                conclusiones.append(f"El docente con menos reprobados es <strong>{docente_menos[0]}</strong> con <strong>{docente_menos[1]}</strong> estudiantes.")
            total_reprobados = sum(x[1] for x in datos_reprobados_docente)
            conclusiones.append(f"En total, se registraron <strong>{total_reprobados}</strong> calificaciones reprobadas distribuidas entre {len(datos_reprobados_docente)} docentes.")
        else:
            conclusiones.append("No hay datos de reprobados por docente para los filtros seleccionados.")

    elif tipo_grafico == 'reprobados_materia':
        if datos_materias_reprobadas and len(datos_materias_reprobadas) > 0:
            mat_mas = max(datos_materias_reprobadas, key=lambda x: x['total_reprobados'])
            mat_menos = min(datos_materias_reprobadas, key=lambda x: x['total_reprobados'])
            conclusiones.append(f"La materia con más reprobados es <strong>{mat_mas['materia__nombre']}</strong> (<strong>{mat_mas['total_reprobados']}</strong>).")
            if mat_mas['materia__nombre'] != mat_menos['materia__nombre']:
                conclusiones.append(f"La materia con menos reprobados es <strong>{mat_menos['materia__nombre']}</strong> (<strong>{mat_menos['total_reprobados']}</strong>).")
        else:
            conclusiones.append("No hay datos de reprobados por materia para los filtros seleccionados.")

    elif tipo_grafico == 'reprobados_area':
        if datos_reprobados_area_materia and datos_reprobados_area_materia.get('labels'):
            totales_area = [(area, sum(d['data'][idx] for d in datos_reprobados_area_materia['datasets'])) for idx, area in enumerate(datos_reprobados_area_materia['labels'])]
            totales_area = [t for t in totales_area if t[1] > 0]
            if totales_area:
                area_mas = max(totales_area, key=lambda x: x[1])
                area_menos = min(totales_area, key=lambda x: x[1])
                conclusiones.append(f"El área con más reprobados es <strong>{area_mas[0]}</strong> (<strong>{area_mas[1]}</strong>).")
                if area_mas[0] != area_menos[0]:
                    conclusiones.append(f"El área con menos reprobados es <strong>{area_menos[0]}</strong> (<strong>{area_menos[1]}</strong>).")
        else:
            conclusiones.append("No hay datos de reprobados por área para los filtros seleccionados.")

    elif tipo_grafico == 'materias_reprobadas_por_docente':
        if datos_materias_reprobadas_por_docente and len(datos_materias_reprobadas_por_docente) > 0:
            max_item = max(datos_materias_reprobadas_por_docente, key=lambda x: x['total_reprobados'])
            min_item = min(datos_materias_reprobadas_por_docente, key=lambda x: x['total_reprobados'])
            conclusiones.append(f"La combinación docente-materia con más reprobados es <strong>{max_item['docente']}</strong> en <strong>{max_item['materia']}</strong> (<strong>{max_item['total_reprobados']}</strong>).")
            if (max_item['docente'] != min_item['docente']) or (max_item['materia'] != min_item['materia']):
                conclusiones.append(f"La combinación con menos reprobados es <strong>{min_item['docente']}</strong> en <strong>{min_item['materia']}</strong> (<strong>{min_item['total_reprobados']}</strong>).")
        else:
            conclusiones.append("No hay datos de reprobados por docente y materia para los filtros seleccionados.")

    if not conclusiones:
        conclusiones.append("No se pudieron generar conclusiones automáticas con los datos disponibles.")

    return conclusiones

from notas.estadisticas_logic import (
    get_resumen_por_area, get_resumen_por_asignatura,
    get_caja_por_area, get_caja_por_asignatura,
    conclusiones_resumen, conclusiones_anotaciones,
)
from notas.estadisticas_observador import contar_observador, contar_automaticas
from ..permisos import es_admin, es_admin_usuario, es_docente_usuario


def es_docente_o_superuser(user):
    return es_admin_usuario(user) or es_docente_usuario(user)

@user_passes_test(es_docente_o_superuser)
def panel_estadisticas_vista(request):
    if not request.colegio:
        return HttpResponseNotFound("<h1>Colegio no configurado</h1>")

    user = request.user
    cursos = []
    if es_admin_usuario(user):
        cursos = Curso.objects.filter(colegio=request.colegio).order_by('nombre')
    else:
        try:
            docente_actual = Docente.objects.get(user=user, colegio=request.colegio)
            cursos_ids = AsignacionDocente.objects.filter(docente=docente_actual, colegio=request.colegio).values_list('curso_id', flat=True).distinct()
            cursos = Curso.objects.filter(id__in=cursos_ids, colegio=request.colegio).order_by('nombre')
        except Docente.DoesNotExist:
            return HttpResponseForbidden("Acceso denegado.")

    periodos = PeriodoAcademico.objects.filter(colegio=request.colegio).order_by('-ano_lectivo', '-fecha_inicio')
    anos_lectivos = PeriodoAcademico.objects.filter(colegio=request.colegio).values_list('ano_lectivo', flat=True).distinct().order_by('-ano_lectivo')
    areas = Area.objects.filter(colegio=request.colegio).order_by('nombre')
    # Cada asignatura lleva el área a la que pertenece, para que el selector
    # de asignaturas se pueda recortar cuando el usuario elige un área.
    materias = (Materia.objects.filter(colegio=request.colegio)
                .values('id', 'nombre', 'areas_ponderadas__id')
                .order_by('nombre'))

    context = {
        'cursos': cursos,
        'sedes_filtro': list(Sede.objects.filter(colegio=request.colegio, activa=True)),
        'periodos': periodos,
        'anos_lectivos': anos_lectivos,
        'ano_actual': datetime.date.today().year,
        'colegio': request.colegio,
        'areas': areas,
        'materias': materias,
    }
    return render(request, 'notas/estadisticas/panel_estadisticas.html', context)

@user_passes_test(es_docente_o_superuser)
def datos_graficos_ajax(request):
    _cache_rendimiento.clear()
    if not request.colegio:
        return JsonResponse({'error': 'Colegio no identificado'}, status=404)

    filtros = {
        'colegio': request.colegio,
        'ano_lectivo': request.GET.get('ano_lectivo'),
        'periodo_id': request.GET.get('periodo_id'),
        'curso_ids': request.GET.getlist('curso_ids[]'),
        'area_id': request.GET.get('area_id'),
        'materia_id': request.GET.get('materia_id'),
    }

    for key in ['ano_lectivo', 'periodo_id', 'area_id', 'materia_id']:
        if filtros[key] == 'todos' or not filtros[key]:
            filtros[key] = None
    if filtros.get('periodo_id') == 'CONSOLIDADO':
        filtros['periodo_id'] = None

    datos_rendimiento = get_rendimiento_general(filtros)
    datos_por_materia = get_promedios_por_materia(filtros)
    datos_histograma = get_histograma_distribucion(filtros)
    datos_reprobados_docente = get_reprobados_por_docente(filtros)
    datos_materias_reprobadas = get_materias_reprobadas(filtros)
    datos_reprobados_area_materia = get_reprobados_por_area_materia(filtros)
    datos_promedios_area_apilado = get_promedios_por_area_apilado(filtros)
    datos_materias_reprobadas_por_docente = get_materias_reprobadas_por_docente(filtros)
    datos_cuadro_honor = get_cuadro_honor(filtros)

    total_estudiantes = sum(nivel['total'] for nivel in datos_rendimiento['distribucion'])

    filtros_ranking = {k: v for k, v in filtros.items() if k != 'curso_ids'}
    ranking, total_cursos = get_ranking_cursos(filtros_ranking)
    puesto_curso_texto = "N/A"
    if len(filtros.get('curso_ids', [])) == 1:
        try:
            puesto = ranking.get(int(filtros['curso_ids'][0]))
            if puesto:
                puesto_curso_texto = f"{puesto} de {total_cursos}"
        except (ValueError, TypeError):
            puesto_curso_texto = "N/A"

    tipo_grafico = request.GET.get('tipo_grafico', 'general')
    conclusiones = generar_conclusiones_texto(
        datos_rendimiento, datos_por_materia, total_estudiantes, tipo_grafico,
        datos_reprobados_docente, datos_materias_reprobadas, datos_reprobados_area_materia,
        datos_promedios_area_apilado, request.colegio, datos_materias_reprobadas_por_docente
    )

    rendimiento_chart_data = {
        'labels': [nivel['nombre'] for nivel in datos_rendimiento['distribucion']],
        'datasets': [{'data': [nivel['total'] for nivel in datos_rendimiento['distribucion']],
                      'backgroundColor': [nivel['color'] for nivel in datos_rendimiento['distribucion']]}]
    }

    colores_bg = [f'rgba({random.randint(50, 200)}, {random.randint(50, 200)}, {random.randint(50, 200)}, 0.7)' for _ in datos_por_materia]

    docentes_unicos = list(sorted(set(item['docente'] for item in datos_materias_reprobadas_por_docente)))
    materias_unicas = list(sorted(set(item['materia'] for item in datos_materias_reprobadas_por_docente)))
    materias_colores = [f'rgba({random.randint(50,200)},{random.randint(50,200)},{random.randint(50,200)},0.8)' for _ in materias_unicas]
    datasets_materias_reprobadas_docente = []
    for idx, materia in enumerate(materias_unicas):
        data_reprobados = []
        for docente in docentes_unicos:
            found = next((item for item in datos_materias_reprobadas_por_docente if item['docente'] == docente and item['materia'] == materia), None)
            data_reprobados.append(found['total_reprobados'] if found else 0)
        datasets_materias_reprobadas_docente.append({
            'label': materia,
            'data': data_reprobados,
            'backgroundColor': materias_colores[idx],
        })

    resumen_area = get_resumen_por_area(filtros)
    resumen_asignatura = get_resumen_por_asignatura(filtros)
    anotaciones = contar_observador(filtros)
    anot_automaticas = contar_automaticas(filtros)

    data = {
        'promedio_general': f"{datos_rendimiento.get('promedio_general', 0):.1f}",
        'desviacion_estandar': f"± {datos_rendimiento.get('desviacion_estandar', 0):.1f}",
        'puesto_curso': puesto_curso_texto,
        'totalEstudiantes': total_estudiantes,
        'conclusiones': conclusiones,
        'cuadro_honor': datos_cuadro_honor,
        'rendimiento_general_chart': rendimiento_chart_data,
        'promedios_area_apilado_chart': datos_promedios_area_apilado,
        'promedios_materia_chart': {
            'labels': [item['materia_nombre'] for item in datos_por_materia],
            'datasets': [{'label': 'Promedio', 'data': [item['promedio'] for item in datos_por_materia], 'backgroundColor': colores_bg}]
        },
        # Antes aquí iba get_distribucion_por_materia(), que devuelve otra forma
        # (nombre/promedio/distribución) y ApexCharts no podía dibujar nada.
        'distribucion_materia_chart': get_caja_por_asignatura(filtros),
        'histograma_chart': {
            'labels': datos_histograma['labels'],
            'datasets': [{'label': 'Frecuencia', 'data': datos_histograma['data'], 'backgroundColor': datos_histograma['colors']}]
        },
        'reprobados_docente_chart': {
            'labels': [item[0] for item in datos_reprobados_docente],
            'datasets': [{'label': 'Reprobados', 'data': [item[1] for item in datos_reprobados_docente], 'backgroundColor': 'rgba(220, 53, 69, 0.7)'}]
        },
        'materias_reprobadas_chart': {
            'labels': [item['materia__nombre'] for item in datos_materias_reprobadas],
            'datasets': [{'label': 'Reprobados', 'data': [item['total_reprobados'] for item in datos_materias_reprobadas], 'backgroundColor': 'rgba(255, 100, 100, 0.7)'}]
        },
        'reprobados_area_materia_chart': datos_reprobados_area_materia,
        'materias_reprobadas_por_docente_chart': {
            'labels': docentes_unicos,
            'datasets': datasets_materias_reprobadas_docente
        },
        # Bloques nuevos: área y asignatura separadas, y las anotaciones.
        'resumen_area': resumen_area,
        'resumen_asignatura': resumen_asignatura,
        'anotaciones': anotaciones,
        'anotaciones_automaticas': anot_automaticas,
        'caja_area': get_caja_por_area(filtros),
        'caja_asignatura': get_caja_por_asignatura(filtros),
        'conclusiones_area': conclusiones_resumen(resumen_area, 'área', 'áreas'),
        'conclusiones_asignatura': conclusiones_resumen(
            resumen_asignatura, 'asignatura', 'asignaturas'),
        'conclusiones_anotaciones': conclusiones_anotaciones(anotaciones, anot_automaticas),
    }
    return JsonResponse(data)

@user_passes_test(es_docente_o_superuser)
def estadisticas_pdf_vista(request):
    if not request.colegio:
        return HttpResponse("Colegio no identificado", status=404)
    if HTML is None:
        return HttpResponse("La librería WeasyPrint no está instalada.", status=500)

    filtros = {
        'colegio': request.colegio,
        'ano_lectivo': request.GET.get('ano_lectivo'),
        'periodo_id': request.GET.get('periodo_id'),
        'curso_ids': request.GET.getlist('curso_ids[]'),
        'area_id': request.GET.get('area_id'),
        'materia_id': request.GET.get('materia_id'),
    }
    for key in ['ano_lectivo', 'periodo_id', 'area_id', 'materia_id']:
        if filtros[key] == 'todos' or not filtros[key]: filtros[key] = None
    if filtros.get('periodo_id') == 'CONSOLIDADO': filtros['periodo_id'] = None

    _cache_rendimiento.clear()

    tipo_reporte = request.GET.get('tipo_grafico', 'general')
    datos_reporte = {}
    graficas_extra = {}
    grafico_base64 = None
    grafico_promedios_area_base64 = None
    conclusiones_texto = []

    if tipo_reporte == 'por_area':
        filas = get_resumen_por_area(filtros)
        datos_reporte['resumen_area'] = filas
        graficas_extra['barras'] = generar_grafico_barras_resumen(filas, 'Promedio por Área')
        graficas_extra['torta'] = generar_grafico_torta_aprobacion(filas, 'Aprobación por Área')
        graficas_extra['caja'] = generar_grafico_caja(
            get_caja_por_area(filtros), 'Dispersión de Notas por Área')
        conclusiones_texto = conclusiones_resumen(filas, 'área', 'áreas')

    elif tipo_reporte == 'por_asignatura':
        filas = get_resumen_por_asignatura(filtros)
        datos_reporte['resumen_asignatura'] = filas
        graficas_extra['barras'] = generar_grafico_barras_resumen(filas, 'Promedio por Asignatura')
        graficas_extra['torta'] = generar_grafico_torta_aprobacion(filas, 'Aprobación por Asignatura')
        graficas_extra['caja'] = generar_grafico_caja(
            get_caja_por_asignatura(filtros), 'Dispersión de Notas por Asignatura')
        conclusiones_texto = conclusiones_resumen(filas, 'asignatura', 'asignaturas')

    elif tipo_reporte == 'anotaciones':
        anot = contar_observador(filtros)
        auto = contar_automaticas(filtros)
        datos_reporte['anotaciones'] = anot
        datos_reporte['anotaciones_automaticas'] = auto
        graficas_extra['barras'] = generar_grafico_barras_anotaciones(anot)
        graficas_extra['torta'] = generar_grafico_torta_anotaciones(anot)
        conclusiones_texto = conclusiones_anotaciones(anot, auto)

    elif tipo_reporte == 'general':
        datos_rendimiento = get_rendimiento_general(filtros)
        total_estudiantes = sum(n['total'] for n in datos_rendimiento.get('distribucion', []))
        datos_promedios_area_apilado = get_promedios_por_area_apilado(filtros)
        
        filtros_ranking = {k: v for k, v in filtros.items() if k != 'curso_ids'}
        ranking, total_cursos = get_ranking_cursos(filtros_ranking)
        puesto_curso_texto = "N/A"
        if len(filtros.get('curso_ids', [])) == 1 and total_cursos > 0:
            try:
                puesto = ranking.get(int(filtros['curso_ids'][0]))
                if puesto:
                    puesto_curso_texto = f"{puesto} de {total_cursos}"
            except (ValueError, TypeError):
                puesto_curso_texto = "N/A"

        datos_reporte = {
            "tarjetas": {
                "promedio_general": datos_rendimiento.get('promedio_general'),
                "desviacion_estandar": datos_rendimiento.get('desviacion_estandar'),
                "total_estudiantes": total_estudiantes,
                "puesto_curso": puesto_curso_texto,
            },
            "cuadro_honor": get_cuadro_honor(filtros),
            "distribucion_rendimiento": datos_rendimiento.get('distribucion'),
            "distribucion_area": get_distribucion_por_area(filtros),
            "distribucion_materia": get_distribucion_por_materia(filtros),
            "escala_valoracion": _get_escala_valoracion(request.colegio)
        }
        grafico_base64 = generar_grafico_distribucion(datos_rendimiento.get('distribucion'))
        grafico_promedios_area_base64 = generar_grafico_promedios_area_apilado(datos_promedios_area_apilado)
        conclusiones_texto = generar_conclusiones_texto(
            datos_rendimiento, get_promedios_por_materia(filtros), total_estudiantes,
            tipo_grafico='general', datos_promedios_area_apilado=datos_promedios_area_apilado,
            colegio=request.colegio
        )
        
    elif tipo_reporte == 'reprobados_docente':
        datos_reporte['reprobados_por_docente'] = get_reprobados_por_docente(filtros)
    elif tipo_reporte == 'reprobados_materia':
        datos_reporte['reprobados_por_materia'] = get_materias_reprobadas(filtros)
    elif tipo_reporte == 'reprobados_area':
        datos_grafico_area = get_reprobados_por_area_materia(filtros)
        grafico_base64 = generar_grafico_reprobados_area(datos_grafico_area)
        datos_reporte['reprobados_por_area'] = datos_grafico_area

    # "por_area" -> "Por Area" queda feo y sin tilde; estos tres llevan título propio.
    TITULOS = {
        'por_area': 'Resumen por Área',
        'por_asignatura': 'Resumen por Asignatura',
        'anotaciones': 'Anotaciones del Observador',
    }
    titulo_del_reporte = TITULOS.get(tipo_reporte, tipo_reporte.replace('_', ' ').title())

    nombres_cursos = "Todos"
    if filtros.get('curso_ids'):
        lista_cursos = Curso.objects.filter(id__in=filtros['curso_ids']).values_list('nombre', flat=True)
        nombres_cursos = ", ".join(lista_cursos)

    # --- INICIO: CAMBIO REALIZADO ---
    # Obtener el nombre del periodo para mostrarlo en el PDF.
    nombre_periodo = "Consolidado"
    if filtros.get('periodo_id'):
        try:
            periodo = PeriodoAcademico.objects.get(id=filtros['periodo_id'])
            nombre_periodo = periodo.nombre
        except PeriodoAcademico.DoesNotExist:
            nombre_periodo = "No encontrado"
    # --- FIN: CAMBIO REALIZADO ---

    context = {
        'colegio': request.colegio,
        'filtros': filtros,
        'tipo_reporte': tipo_reporte,
        'titulo_reporte': titulo_del_reporte,
        'nombres_cursos': nombres_cursos,
        'nombre_periodo': nombre_periodo, # <-- Añadido al contexto
        'datos': datos_reporte,
        'fecha_generacion': datetime.date.today(),
        'grafico_base64': grafico_base64,
        'grafico_promedios_area_base64': grafico_promedios_area_base64,
        'conclusiones': conclusiones_texto,
        'graficas_extra': graficas_extra,
    }

    html_string = render_to_string('notas/estadisticas/estadisticas_pdf.html', context)
    pdf = HTML(string=html_string, base_url=request.build_absolute_uri()).write_pdf()

    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="reporte_estadistico_{tipo_reporte}.pdf"'
    return response
