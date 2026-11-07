"""Planilla de preguntas en Excel (importar y exportar), la misma para los eventos, el banco de preguntas y
los juegos. Una fila por pregunta:

    Grado | Nivel | Pensamiento | Tema | Pregunta | A | B | C | D | E | F | G | H | Correcta

- Grado: 6, 7.º, Séptimo… (opcional en los juegos). Nivel: el grupo del evento (Exploradores…), opcional:
  si falta, sale del grado. Pensamiento: Euclides, Newton o Bernoulli (opcional; en el evento, si falta, Newton).
- De 2 a 8 opciones (A a H) y la letra de la correcta en «Correcta».
Se aceptan .xlsx y .csv."""
import io
import json
import os
import unicodedata

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation

from .planilla_eventos import _filas, _plano, leer_grado

LETRAS = 'ABCDEFGH'
TITULOS = ['Grado', 'Nivel', 'Pensamiento', 'Tema', 'Pregunta'] + list(LETRAS) + ['Correcta']
ANCHOS = [8, 15, 13, 18, 60] + [16] * 8 + [10]
PENSAMIENTOS = {'euclides': 'Euclides', 'newton': 'Newton', 'bernoulli': 'Bernoulli'}
BANCO_611 = os.path.join(os.path.dirname(__file__), 'bancos', 'olimpiada_6_11.json')


def banco_olimpiada():
    """Las 240 preguntas de la olimpiada de 6.º a 11.º (40 por grado, generadas y verificadas)."""
    with open(BANCO_611, encoding='utf-8') as f:
        return json.load(f)


BANCO_CALCULO = os.path.join(os.path.dirname(__file__), 'bancos', 'calculo_10_11.json')


def banco_calculo():
    """10.º y 11.º: funciones, trigonometría, límites, derivadas y conceptos, sin integrales (verificado con SymPy)."""
    with open(BANCO_CALCULO, encoding='utf-8') as f:
        return json.load(f)


def _grado_texto(g):
    return {-2: 'Prejardín', -1: 'Jardín', 0: 'Transición'}.get(g, f'{g}.º') if g is not None else ''


def descargar(preguntas, titulo='Preguntas', niveles=None):
    """El libro de Excel con las preguntas (o vacío, para llenarlo). niveles: {id: nombre} de los grupos del evento."""
    niveles = niveles or {}
    libro = Workbook()
    hoja = libro.active
    hoja.title = 'Preguntas'
    hoja.append(TITULOS)
    for i, t in enumerate(TITULOS, start=1):
        c = hoja.cell(row=1, column=i)
        c.font = Font(bold=True, color='FFFFFFFF', size=10)
        c.fill = PatternFill('solid', fgColor='FF1F3A68' if t not in ('Correcta',) else 'FF2F9E44')
        c.alignment = Alignment(horizontal='center', vertical='center')
        hoja.column_dimensions[get_column_letter(i)].width = ANCHOS[i - 1]
    hoja.freeze_panes = 'F2'
    for p in preguntas:
        ops = p.get('opciones') or []
        correcta = next((LETRAS[k] for k, o in enumerate(ops[:8]) if o.get('correcta')), '')
        hoja.append([_grado_texto(p.get('grado')), niveles.get(p.get('ciclo'), p.get('ciclo') or ''), PENSAMIENTOS.get(p.get('categoria'), ''),
                     p.get('tema', ''), p.get('texto', '')] + [o.get('texto', '') for o in ops[:8]] + [''] * (8 - len(ops[:8])) + [correcta])
    for fila in hoja.iter_rows(min_row=2, max_col=5):
        fila[4].alignment = Alignment(wrap_text=True, vertical='top')
    ultima = max(hoja.max_row, 1) + 500
    v1 = DataValidation(type='list', formula1='"Euclides,Newton,Bernoulli"', allow_blank=True)
    v2 = DataValidation(type='list', formula1='"' + ','.join(LETRAS) + '"', allow_blank=True)
    hoja.add_data_validation(v1); hoja.add_data_validation(v2)
    v1.add(f'C2:C{ultima}'); v2.add(f'N2:N{ultima}')
    ins = libro.create_sheet('Instrucciones')
    for f in [
        [f'{titulo}: planilla de preguntas'], [''],
        ['Una fila por pregunta. No cambie los títulos de la primera fila.'],
        ['Grado: el grado para el que es la pregunta (6, 7.º, Séptimo…). En los juegos de una clase puede quedar vacío.'],
        ['Nivel: el grupo del evento (por ejemplo Exploradores, Investigadores o Expertos). Si lo deja vacío, se toma del grado.'],
        ['Pensamiento: Euclides (geométrico y métrico), Newton (numérico y algebraico) o Bernoulli (aleatorio: datos y probabilidad).'],
        ['Tema: opcional (Fracciones, Pitágoras…). Sirve para buscar en el banco de preguntas.'],
        ['Pregunta y opciones: de 2 a 8 opciones (columnas A a H). En «Correcta» escriba la letra de la respuesta correcta.'],
        ['Para escribir potencias use ^ (x^2) o ², y para fracciones la barra (3/4). Para π, √, ≤, ≥… copie el símbolo.'],
    ]:
        ins.append(f)
    ins['A1'].font = Font(bold=True, size=13, color='FF1F3A68')
    ins.column_dimensions['A'].width = 120
    salida = io.BytesIO()
    libro.save(salida)
    salida.seek(0)
    return salida


def _columnas(fila):
    planos = [_plano(v) for v in fila]
    col = {}
    for i, v in enumerate(planos):
        if v in ('grado',):
            col['grado'] = i
        elif v.startswith('nivel') or v.startswith('grupo'):
            col['nivel'] = i
        elif v.startswith('pensamiento') or v.startswith('categoria') or v.startswith('competencia'):
            col['pensamiento'] = i
        elif v.startswith('tema'):
            col['tema'] = i
        elif v.startswith('pregunta') or v.startswith('enunciado'):
            col['texto'] = i
        elif v.startswith('correcta') or v.startswith('respuesta') or v.startswith('clave'):
            col['correcta'] = i
        elif len(v) == 1 and v.upper() in LETRAS:
            col['op_' + v.upper()] = i
        elif v.startswith('opcion ') and len(v) == 8 and v[-1].upper() in LETRAS:
            col['op_' + v[-1].upper()] = i
    return col


def importar(archivo, maximo=8):
    """Lee la planilla. Devuelve (preguntas, errores): cada pregunta {grado, nivel, categoria, tema, texto, opciones}."""
    try:
        filas = _filas(archivo)
    except Exception:
        return [], [(0, 'No se pudo leer el archivo. Súbalo en Excel (.xlsx) o .csv.')]
    n_tit, col = None, {}
    for n, f in enumerate(filas[:10]):
        c = _columnas(f)
        if 'texto' in c and 'op_A' in c and 'op_B' in c:
            n_tit, col = n, c
            break
    if n_tit is None:
        return [], [(0, 'No se encontraron los títulos (Pregunta, A, B… Correcta). Use la planilla descargada.')]
    preguntas, errores = [], []
    for k, f in enumerate(filas[n_tit + 1:], start=n_tit + 2):
        val = lambda clave: '' if col.get(clave) is None or col[clave] >= len(f) or f[col[clave]] is None else str(f[col[clave]]).strip()
        texto = ' '.join(val('texto').split())
        ops = [(L, val('op_' + L)) for L in LETRAS if val('op_' + L)]
        if not texto and not ops:
            continue
        correcta = _plano(val('correcta')).upper()[:1]
        if not texto:
            errores.append((k, 'Falta la pregunta.')); continue
        if len(ops) < 2:
            errores.append((k, f'«{texto[:50]}»: necesita al menos 2 opciones.')); continue
        if len(ops) > maximo:
            errores.append((k, f'«{texto[:50]}»: tiene {len(ops)} opciones y aquí caben {maximo}.')); continue
        if correcta not in [L for L, _ in ops]:
            errores.append((k, f'«{texto[:50]}»: en «Correcta» escriba la letra de una de sus opciones.')); continue
        cat = _plano(val('pensamiento'))
        cat = next((k2 for k2 in PENSAMIENTOS if cat.startswith(k2[:4])), '')
        g_val = f[col['grado']] if col.get('grado') is not None and col['grado'] < len(f) else None
        preguntas.append({'grado': leer_grado(g_val), 'nivel': val('nivel'), 'categoria': cat, 'tema': ' '.join(val('tema').split())[:80],
                          'texto': texto[:1000], 'opciones': [{'texto': t[:300], 'correcta': L == correcta} for L, t in ops]})
    return preguntas, errores


def como_texto(preguntas):
    """En el formato de pegar de los juegos (1. Pregunta / A) … / *B) …)."""
    bloques = []
    for i, p in enumerate(preguntas, 1):
        bloques.append(f"{i}. {p['texto']}\n" + '\n'.join(f"{'*' if o['correcta'] else ''}{LETRAS[k]}) {o['texto']}" for k, o in enumerate(p['opciones'])))
    return '\n\n'.join(bloques)


def normalizar_nivel(texto):
    t = unicodedata.normalize('NFKD', texto or '').encode('ascii', 'ignore').decode().lower().strip()
    return t
