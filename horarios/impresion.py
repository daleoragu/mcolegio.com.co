"""Horarios en PDF: uno por curso y uno por docente (sueltos en un .zip, o todos juntos en un PDF).

Usa reportlab. Cada horario va en una hoja horizontal, con los colores por área.
"""
import io
import re
import zipfile

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import landscape, letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from . import nucleo

PALETA = ['#bfdbfe', '#bbf7d0', '#fde68a', '#fecaca', '#ddd6fe', '#a5f3fc', '#fbcfe8', '#fed7aa', '#d9f99d',
          '#c7d2fe', '#99f6e4', '#f5d0fe', '#e2e8f0', '#fef9c3', '#bae6fd', '#ffe4e6', '#dcfce7', '#e9d5ff']
AZUL = colors.HexColor('#3730a3')
GRIS = colors.HexColor('#f1f5f9')
REUNION = colors.HexColor('#fde68a')
ACTIVIDAD = colors.HexColor('#bbf7d0')

_celda = ParagraphStyle('celda', fontName='Helvetica', fontSize=9, leading=11, alignment=TA_CENTER)
_titulo = ParagraphStyle('titulo', fontName='Helvetica-Bold', fontSize=15, leading=18, textColor=AZUL)
_sub = ParagraphStyle('sub', fontName='Helvetica', fontSize=9, leading=11, textColor=colors.HexColor('#475569'))
_jornada = ParagraphStyle('jornada', fontName='Helvetica-Bold', fontSize=10, leading=12)


def _esc(t):
    return (str(t or '').replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;'))


def nombre_archivo(t):
    t = re.sub(r'[\\/:*?"<>|]+', ' ', str(t)).strip()
    return re.sub(r'\s+', ' ', t)[:80] or 'horario'


def _color_area(p, alt, x):
    if x.get('reunion'):
        return REUNION
    if x.get('actividad'):
        return ACTIVIDAD
    if x.get('i') is None:
        return GRIS
    D = p.datos
    a = D.asignaciones.get(alt['sesiones'][x['i']]['asignacion'])
    areas = sorted(D.areas)
    area = D.materias.get(a['materia'], {}).get('area') if a else None
    return colors.HexColor(PALETA[areas.index(area) % len(PALETA)]) if area in areas else GRIS


def _tabla(p, alt, t, ancho, alto=None):
    dias = t['dias']
    filas = [[Paragraph('<b>Hora</b>', _celda)] + [Paragraph(f'<b>{_esc(n)}</b>', _celda) for _, n in dias]]
    estilo = [('BACKGROUND', (0, 0), (-1, 0), AZUL), ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
              ('GRID', (0, 0), (-1, -1), 0.4, colors.HexColor('#cbd5e1')),
              ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'), ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
              ('TOPPADDING', (0, 0), (-1, -1), 2), ('BOTTOMPADDING', (0, 0), (-1, -1), 2)]
    for fr, celdas in t['filas']:
        r = len(filas)
        hora = Paragraph(f'{_esc(fr["inicio"])}<br/>{_esc(fr["fin"])}', _celda)
        if fr['descanso'] and not any(celdas):
            hora = Paragraph(f'<font size="6.5">{_esc(fr["inicio"])}-{_esc(fr["fin"])}</font>', _celda)
            filas.append([hora, Paragraph(_esc(fr.get('etiqueta') or 'Descanso'), _celda)] + [''] * (len(dias) - 1))
            estilo += [('SPAN', (1, r), (-1, r)), ('BACKGROUND', (0, r), (-1, r), GRIS)]
            continue
        fila = [hora]
        for c, xs in enumerate(celdas, start=1):
            if not xs:
                fila.append('')
                if not fr['descanso']:
                    continue
                estilo.append(('BACKGROUND', (c, r), (c, r), GRIS))
                continue
            texto = '<br/>'.join(f'<b>{_esc(x["titulo"])}</b><br/>{_esc(x.get("sub"))}' for x in xs)
            fila.append(Paragraph(texto, _celda))
            estilo.append(('BACKGROUND', (c, r), (c, r), _color_area(p, alt, xs[0])))
        filas.append(fila)
    hora_w = 58
    resto = (ancho - hora_w) / max(1, len(dias))
    alturas = None
    if alto:
        n_desc = sum(1 for fr, celdas in t['filas'] if fr['descanso'] and not any(celdas))
        n_clase = max(1, len(t['filas']) - n_desc)
        h = max(26, min(60, (alto - 20 - 18 * n_desc) / n_clase))
        alturas = [20] + [18 if (fr['descanso'] and not any(celdas)) else h for fr, celdas in t['filas']]
    tabla = Table(filas, colWidths=[hora_w] + [resto] * len(dias), rowHeights=alturas, repeatRows=1)
    tabla.setStyle(TableStyle(estilo))
    return tabla


def _hojas(p, alt, cuales):
    """[(título, [tablas de la cuadrícula])] para cada ('c', curso) o ('d', docente)."""
    D = p.datos
    out = []
    for tipo, ident in cuales:
        if tipo == 'c':
            tablas = [p.tabla_curso(alt, ident)]
            titulo = f'Curso {D.nombre_curso(ident)}'
        else:
            tablas = p.tablas_docente(alt, ident)
            titulo = D.nombre_docente(ident)
        tablas = [t for t in tablas if t]
        if tablas:
            out.append((titulo, tablas))
    return out


def pdf(p, alt, cuales, salida):
    """Escribe un PDF (ruta o archivo abierto) con una hoja por cada curso/docente de `cuales`."""
    hojas = _hojas(p, alt, cuales)
    tam = landscape(letter)
    margen = 28
    doc = SimpleDocTemplate(salida, pagesize=tam, leftMargin=margen, rightMargin=margen, topMargin=margen,
                            bottomMargin=margen, title='Horarios', author='mcolegio')
    ancho = tam[0] - 2 * margen
    colegio = (p.datos.colegio or {}).get('nombre', '')
    story = []
    for k, (titulo, tablas) in enumerate(hojas):
        if k:
            story.append(PageBreak())
        story.append(Paragraph(_esc(titulo), _titulo))
        story.append(Paragraph(_esc(f'{colegio} · {alt.get("nombre", "Horario")}'), _sub))
        story.append(Spacer(1, 8))
        alto = (tam[1] - 2 * margen - 50) / len(tablas) - (18 if len(tablas) > 1 else 0)
        for t in tablas:
            if len(tablas) > 1:
                story.append(Paragraph(_esc(t['jornada']['nombre']), _jornada))
                story.append(Spacer(1, 3))
            story.append(_tabla(p, alt, t, ancho, alto))
            story.append(Spacer(1, 8))
    if not story:
        story.append(Paragraph('No hay horarios para mostrar.', _sub))
    doc.build(story)
    return len(hojas)


def cursos_y_docentes(p):
    D = p.datos
    cursos = [('c', c['id']) for c in D.crudo['cursos'] if c['id'] in D.jornada_de_curso]
    con = {a.get('docente') for a in D.asignaciones.values() if a.get('docente')}
    docentes = [('d', d['id']) for d in sorted(D.docentes.values(), key=lambda d: d['nombre']) if d['id'] in con]
    return cursos, docentes


def zip_individuales(p, alt, ruta_zip):
    """Un .zip con un PDF por curso (carpeta Cursos) y uno por docente (carpeta Docentes)."""
    D = p.datos
    cursos, docentes = cursos_y_docentes(p)
    n = 0
    with zipfile.ZipFile(ruta_zip, 'w', zipfile.ZIP_DEFLATED) as z:
        for carpeta, lista in (('Cursos', cursos), ('Docentes', docentes)):
            usados = set()
            for item in lista:
                nombre = (f'Curso {D.nombre_curso(item[1])}' if item[0] == 'c' else D.nombre_docente(item[1]))
                nombre = nombre_archivo(nombre)
                base, k = nombre, 2
                while nombre in usados:
                    nombre, k = f'{base} ({k})', k + 1
                usados.add(nombre)
                buf = io.BytesIO()
                if pdf(p, alt, [item], buf):
                    z.writestr(f'{carpeta}/{nombre}.pdf', buf.getvalue())
                    n += 1
    return n


def todo_junto(p, alt, ruta_cursos, ruta_docentes):
    """Dos PDF: todos los cursos (una hoja cada uno) y todos los docentes."""
    cursos, docentes = cursos_y_docentes(p)
    return pdf(p, alt, cursos, ruta_cursos), pdf(p, alt, docentes, ruta_docentes)
