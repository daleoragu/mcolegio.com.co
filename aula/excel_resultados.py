"""Resultados de un evento en Excel, listos para compartir.

Hojas:
  1. Resultados: un estudiante por fila, con filtros en cada columna (grupo, grado, colegio, terminó…), encabezado fijo
     y bandas de color. Respeta los filtros que se tengan en la página al descargar.
  2. Por colegio: participantes, promedio, mejor puntaje y mejor estudiante de cada colegio.
  3. Por grado: lo mismo por grado.
  4. Podio de colegios (si el evento lo tiene activo).
Para un veedor (enlace de solo lectura) no salen el documento ni el contacto de los estudiantes."""
import io
from collections import OrderedDict

from django.utils import timezone
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.table import Table, TableStyleInfo

AZUL, ORO = 'FF1F3A68', 'FFF2B632'
MEDALLA = {1: 'FFFFE08A', 2: 'FFE5E7EB', 3: 'FFF5CBA7'}


def _titulo(ws, ev, subtitulo, filtros=''):
    ws['A1'] = ev.titulo
    ws['A1'].font = Font(bold=True, size=15, color=AZUL)
    ws['A2'] = subtitulo
    ws['A2'].font = Font(bold=True, size=11)
    ws['A3'] = f"Descargado el {timezone.localtime().strftime('%d/%m/%Y %I:%M %p')}" + (f' · {filtros}' if filtros else '')
    ws['A3'].font = Font(italic=True, size=9, color='FF64748B')


def _tabla(ws, nombre, encabezados, filas, anchos, fila0=5, estilo='TableStyleMedium2'):
    """Escribe la tabla con filtros (una «Tabla» de Excel: botón de filtro y orden en cada columna)."""
    for j, (h, w) in enumerate(zip(encabezados, anchos), 1):
        cel = ws.cell(row=fila0, column=j, value=h)
        cel.font = Font(bold=True, color='FFFFFFFF')
        cel.fill = PatternFill('solid', fgColor=AZUL)     # explícito: Google Sheets y LibreOffice no pintan el estilo de tabla
        cel.alignment = Alignment(wrap_text=True, vertical='center')
        ws.column_dimensions[get_column_letter(j)].width = w
    ws.row_dimensions[fila0].height = 46
    for i, fila in enumerate(filas, fila0 + 1):
        for j, v in enumerate(fila, 1):
            ws.cell(row=i, column=j, value=v)
    ultima = fila0 + max(len(filas), 1)
    if not filas:
        ws.cell(row=fila0 + 1, column=1, value='(sin datos)')
    ref = f'A{fila0}:{get_column_letter(len(encabezados))}{ultima}'
    t = Table(displayName=nombre, ref=ref)
    t.tableStyleInfo = TableStyleInfo(name=estilo, showRowStripes=True)
    ws.add_table(t)
    ws.freeze_panes = ws.cell(row=fila0 + 1, column=1)
    ws.sheet_view.zoomScale = 110
    ws.page_setup.orientation = 'landscape'
    ws.page_setup.fitToWidth = 1
    ws.page_setup.fitToHeight = 0
    ws.sheet_properties.pageSetUpPr.fitToPage = True
    ws.print_title_rows = f'{fila0}:{fila0}'
    return ultima


def _resumen(filas, clave):
    """filas: dicts de participantes → [(clave, n, terminaron, promedio, máximo, mejor)]."""
    grupos = OrderedDict()
    for f in sorted(filas, key=lambda f: (str(f[clave]).lower(), -f['puntos'], f['tiempo'])):
        grupos.setdefault(f[clave] or '(sin dato)', []).append(f)
    out = []
    for k, fs in grupos.items():
        mejor = min(fs, key=lambda f: (-f['puntos'], f['tiempo']))
        out.append([k, len(fs), sum(1 for f in fs if f['termino']), round(sum(f['puntos'] for f in fs) / len(fs), 1),
                    mejor['puntos'], mejor['nombre'], round(sum(f['bien'] for f in fs) / len(fs), 1)])
    return sorted(out, key=lambda r: (-r[3], -r[4], str(r[0]).lower()))


def libro(ev, tablas, podio=None, niveles=(), salidas=False, veedor=False, filtros=''):
    """tablas: [(nombre_grupo, rango, [participaciones con puesto, grupo_nombre, grado_txt, salidas, fuera])]."""
    from .views_eventos import colegio_de, grado_de
    wb = Workbook()
    ws = wb.active
    ws.title = 'Resultados'
    _titulo(ws, ev, 'Resultados por estudiante — use las flechas de cada columna para filtrar u ordenar', filtros)
    enc = ['Grupo', 'Puesto en el grupo', 'Estudiante'] + ([] if veedor else ['Documento']) + [
        'Grado', 'Colegio', 'Curso', 'Municipio', 'Puntos', 'Preguntas respondidas', 'Preguntas bien', '% de acierto',
        'Tiempo efectivo (min)', 'Terminó'] + (['Salidas de la prueba', 'Segundos fuera'] if salidas else [])
    anchos = [16, 10, 32] + ([] if veedor else [15]) + [10, 34, 12, 16, 9, 12, 10, 10, 11, 9] + ([10, 10] if salidas else [])
    filas, datos = [], []
    for _, _, ps in tablas:
        for p in ps:
            d = p.datos or {}
            resp = sum(1 for r in (p.registro or []) if r.get('tipo') == 'pregunta') or p.preguntas_hechas
            bien = p.bonos
            colegio = colegio_de(p)
            curso = p.estudiante.curso.nombre if p.estudiante_id and p.estudiante.curso_id else ''
            minutos = round(p.tiempo_efectivo / 60, 2)
            fila = [p.grupo_nombre, p.puesto, p.nombre_completo] + ([] if veedor else [d.get('documento', '')]) + [
                p.grado_txt, colegio, curso, d.get('ciudad', ''), p.puntos, resp, bien,
                round(100 * bien / resp) / 100 if resp else None, minutos, 'Sí' if p.terminada else 'No'] + (
                [p.salidas, p.fuera] if salidas else [])
            filas.append(fila)
            g = grado_de(p)
            datos.append({'colegio': colegio, 'grado': p.grado_txt or '(sin grado)', 'orden_grado': g if g is not None else 99,
                          'puntos': p.puntos, 'tiempo': p.tiempo_efectivo, 'termino': p.terminada, 'nombre': p.nombre_completo, 'bien': bien})
    # Columnas opcionales que nadie tiene (p. ej. «Curso» si todos se inscribieron desde afuera): no se muestran
    vacias = {j for j, h in enumerate(enc) if h in ('Documento', 'Curso', 'Municipio') and not any(f[j] for f in filas)}
    if vacias:
        enc = [h for j, h in enumerate(enc) if j not in vacias]
        anchos = [w for j, w in enumerate(anchos) if j not in vacias]
        filas = [[v for j, v in enumerate(f) if j not in vacias] for f in filas]
    ultima = _tabla(ws, 'Resultados', enc, filas, anchos)
    col = {h: get_column_letter(j) for j, h in enumerate(enc, 1)}
    for i in range(6, ultima + 1):
        ws[f"{col['% de acierto']}{i}"].number_format = '0%'
        ws[f"{col['Tiempo efectivo (min)']}{i}"].number_format = '0.00'
        puesto = ws[f"{col['Puesto en el grupo']}{i}"].value
        if puesto in MEDALLA:
            for j in range(1, len(enc) + 1):
                ws.cell(row=i, column=j).fill = PatternFill('solid', fgColor=MEDALLA[puesto])

    enc_r = ['Colegio', 'Participantes', 'Terminaron', 'Promedio de puntos', 'Mejor puntaje', 'Mejor estudiante', 'Promedio de preguntas bien']
    ws2 = wb.create_sheet('Por colegio')
    _titulo(ws2, ev, 'Resumen por colegio (ordenado por promedio de puntos)', filtros)
    _tabla(ws2, 'PorColegio', enc_r, _resumen(datos, 'colegio'), [36, 12, 11, 12, 11, 32, 12], estilo='TableStyleMedium9')

    ws3 = wb.create_sheet('Por grado')
    _titulo(ws3, ev, 'Resumen por grado', filtros)
    orden = {d['grado']: d['orden_grado'] for d in datos}
    por_grado = sorted(_resumen(datos, 'grado'), key=lambda r: orden.get(r[0], 99))
    _tabla(ws3, 'PorGrado', ['Grado'] + enc_r[1:], por_grado, [14, 12, 11, 12, 11, 32, 12], estilo='TableStyleMedium9')

    if podio:
        ws4 = wb.create_sheet('Podio de colegios')
        _titulo(ws4, ev, 'Podio de colegios: cuenta el mejor estudiante de cada colegio en cada nivel')
        enc_p = ['Puesto', 'Colegio', 'Puntaje', 'Tiempo efectivo sumado (min)'] + [f'{n}: representante' for n in niveles] + [f'{n}: puntos' for n in niveles]
        filas_p = []
        for x in podio:
            reps = [r for _, r in x['por_nivel']]
            filas_p.append([x['puesto'], x['colegio'], x['puntaje'], round(x['tiempo'] / 60, 2)]
                           + [r['nombre'] if r else '—' for r in reps] + [r['puntos'] if r else None for r in reps])
        _tabla(ws4, 'Podio', enc_p, filas_p, [8, 36, 10, 12] + [28] * len(niveles) + [10] * len(niveles), estilo='TableStyleMedium7')
        for i, x in enumerate(podio, 6):
            if x['puesto'] in MEDALLA:
                for j in range(1, len(enc_p) + 1):
                    ws4.cell(row=i, column=j).fill = PatternFill('solid', fgColor=MEDALLA[x['puesto']])

    salida = io.BytesIO()
    wb.save(salida)
    return salida.getvalue()
