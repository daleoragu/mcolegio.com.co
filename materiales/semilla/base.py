"""Piezas para escribir el material semilla: bloques del editor (texto, recuadro, preguntas…) con id propio.

Las respuestas numéricas se calculan en el código que arma cada pregunta (no se escriben a mano), y el
material se arma alrededor del DBA oficial (enunciado y evidencias tal cual del catálogo del MEN).
"""
import itertools
from fractions import Fraction

_ids = itertools.count(1)


def _id(pref='s'):
    return f'{pref}{next(_ids)}'


def num(x):
    """Un número como se escribe en Colombia: 2,5 · 1 200 · −3."""
    if isinstance(x, Fraction):
        x = x.numerator if x.denominator == 1 else float(x)
    if isinstance(x, float) and x.is_integer():
        x = int(x)
    if isinstance(x, int):
        t = f'{abs(x):,}'.replace(',', ' ')
    else:
        t = f'{abs(x):.4f}'.rstrip('0').rstrip('.').replace('.', ',')
    return ('−' if x < 0 else '') + t


def frac(f):
    f = Fraction(f)
    return num(f.numerator) if f.denominator == 1 else f'{f.numerator}/{f.denominator}'


# ---------------------------------------------------------------------------
# Bloques
# ---------------------------------------------------------------------------
def titulo(texto, nivel=1):
    return {'id': _id('t'), 'tipo': 'titulo', 'texto': texto, 'nivel': nivel}


def seccion(texto, indicacion=''):
    return {'id': _id('c'), 'tipo': 'seccion', 'titulo': texto, 'indicacion': indicacion}


def texto(*parrafos):
    return {'id': _id('x'), 'tipo': 'texto', 'html': ''.join(p if p.startswith('<') else f'<p>{p}</p>' for p in parrafos)}


def lista(*items):
    return '<ul>' + ''.join(f'<li>{i}</li>' for i in items) + '</ul>'


def recuadro(titulo_, *parrafos, estilo='recuerda'):
    return {'id': _id('r'), 'tipo': 'recuadro', 'estilo': estilo, 'titulo': titulo_,
            'html': ''.join(p if p.startswith('<') else f'<p>{p}</p>' for p in parrafos)}


def tabla(filas, encabezado=True):
    return {'id': _id('b'), 'tipo': 'tabla', 'filas': [[str(c) for c in f] for f in filas], 'encabezado': encabezado}


def lineas(n=4):
    return {'id': _id('l'), 'tipo': 'lineas', 'n': n}


def unica(enunciado, correcta, distractores, solucion='', puntos=1):
    """Selección múltiple: la correcta va de primera aquí y se ubica en una posición fija pero variada."""
    opciones = [str(correcta)] + [str(d) for d in distractores]
    assert len(set(opciones)) == len(opciones), f'opciones repetidas: {opciones}'
    k = (len(enunciado) + len(opciones)) % len(opciones)          # posición de la correcta, sin azar (reproducible)
    opciones = opciones[1:k + 1] + [opciones[0]] + opciones[k + 1:]
    return {'id': _id('p'), 'tipo': 'pregunta', 'modo': 'unica', 'enunciado': enunciado, 'opciones': opciones,
            'correcta': k, 'puntos': puntos, 'lineas': 0, 'imagen': None, 'solucion': solucion}


def numerica(enunciado, respuesta, unidad='', tolerancia='0', solucion='', puntos=1):
    return {'id': _id('p'), 'tipo': 'pregunta', 'modo': 'numerica', 'enunciado': enunciado,
            'respuesta': num(respuesta).replace('\u2212', '-').replace(' ', ''), 'tolerancia': tolerancia, 'unidad': unidad, 'puntos': puntos, 'lineas': 0,
            'imagen': None, 'solucion': solucion}


def vf(enunciado, valor, solucion=''):
    return {'id': _id('p'), 'tipo': 'pregunta', 'modo': 'vf', 'enunciado': enunciado, 'valor': bool(valor), 'puntos': 1,
            'lineas': 0, 'imagen': None, 'solucion': solucion}


def abierta(enunciado, renglones=4, solucion='', puntos=2):
    return {'id': _id('p'), 'tipo': 'pregunta', 'modo': 'abierta', 'enunciado': enunciado, 'lineas': renglones,
            'puntos': puntos, 'imagen': None, 'solucion': solucion}


def grafica(spec, ancho=60, pie=''):
    """Marcador: el comando que carga la semilla dibuja la gráfica (Graficador) y la cambia por un bloque de imagen."""
    return {'id': _id('g'), 'tipo': '_grafica', 'grafica': spec, 'ancho': ancho, 'pie': pie}


# ---------------------------------------------------------------------------
# Una unidad: guía + taller alrededor de un DBA
# ---------------------------------------------------------------------------
def guia(dba, tema, objetivo, explora, aprende, recuerda, practica):
    """dba: el del catálogo (n, enunciado, evidencias). El resto, bloques escritos para la unidad. El título va en el
    encabezado del documento (Documento.titulo), no se repite como bloque."""
    return [
        texto(f'<b>Matemáticas · Grado {dba["grado"]}.º · Guía de aprendizaje</b>'),
        recuadro(f'DBA {dba["n"]} (MEN, Matemáticas V.2)', f'<p><i>{dba["enunciado"]}</i></p>',
                 '<p><b>Evidencias de aprendizaje:</b></p>' + lista(*dba['evidencias']), estilo='nota'),
        recuadro('Lo que vas a lograr', objetivo, estilo='reto'),
        seccion('1. Exploro', 'Lee la situación y responde con tus palabras.'), *explora,
        seccion('2. Aprendo'), *aprende,
        recuadro('Recuerda', *recuerda),
        seccion('3. Practico', 'Resuelve en tu cuaderno y marca o escribe la respuesta.'), *practica,
    ]


def taller(dba, tema, preguntas):
    return [
        texto(f'<b>Matemáticas · Grado {dba["grado"]}.º</b> · DBA {dba["n"]}: {dba["enunciado"]}'),
        seccion('Preguntas', 'Lee con atención. En las de respuesta numérica escribe solo el número.'),
        *preguntas,
    ]
