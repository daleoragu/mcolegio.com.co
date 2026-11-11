"""Ecuaciones en los documentos: se guardan dentro del texto como \\( LaTeX \\) y se dibujan con matplotlib
(mathtext, sin LaTeX instalado ni internet), igual en el editor, en la vista web, en el PDF y en Word.

    «Halle \\(x=\\frac{-b\\pm\\sqrt{b^2-4ac}}{2a}\\) …»

mathtext cubre fracciones, raíces, potencias, subíndices, sumatorias, integrales, límites, letras griegas,
símbolos de geometría y conjuntos; lo que no entiende (p. ej. matrices) se muestra como texto.
"""
import base64
import html
import io
import re
import threading
from functools import lru_cache

TOKEN = re.compile(r'\\\((.+?)\\\)', re.S)
MAX_TEX = 400
TAM = 12                 # puntos: las medidas se pasan a «em» para que la ecuación siga al tamaño del texto
_candado = threading.Lock()

# Lo que escribe el teclado de ecuaciones (MathLive) y mathtext no conoce
_CAMBIOS = [
    (r'\\placeholder(\[[^\]]*\])?\{[^{}]*\}', r'\\blacksquare '), (r'\\placeholder', ''), (r'\\differentialD', 'd'), (r'\\exponentialE', 'e'),
    (r'\\imaginaryI', 'i'), (r'\\operatorname\{([^{}]*)\}', r'\\mathrm{\1}'), (r'\\text\{([^{}]*)\}', r'\\mathrm{\1}'),
    (r'\\textrm\{([^{}]*)\}', r'\\mathrm{\1}'), (r'\\mathrm\{([^{}]*)\}', lambda m: r'\mathrm{' + m.group(1).replace(' ', r'\ ') + '}'),
    (r'\\[dt]?frac\b', r'\\dfrac'), (r'\\degree', r'^{\\circ}'), (r'\\le\b', r'\\leq'), (r'\\ge\b', r'\\geq'),
    (r'\\lbrack', '['), (r'\\rbrack', ']'), (r'\\mleft', r'\\left'), (r'\\mright', r'\\right'), (r'\\colon', ':'),
    (r'\\(sen|tg|ctg|cosec)\b', r'\\mathrm{\1}\\,'), (r'\\displaystyle', ''), (r'\\nonumber', ''),
]


def normalizar(tex):
    t = ' '.join(str(tex or '').split())[:MAX_TEX]
    for patron, cambio in _CAMBIOS:
        t = re.sub(patron, cambio, t)
    return t.strip()


@lru_cache(maxsize=512)
def _dibujar(tex, formato, dpi):
    """(bytes, ancho_pt, alto_pt, fondo_pt) o None si mathtext no la entiende."""
    import matplotlib
    matplotlib.use('Agg')
    from matplotlib import mathtext, rc_context
    from matplotlib.font_manager import FontProperties
    s = f'${tex}$'
    prop = FontProperties(size=TAM, math_fontfamily='cm')
    with _candado, rc_context({'mathtext.fontset': 'cm', 'svg.fonttype': 'path'}):
        try:
            ancho, alto, fondo, *_ = mathtext.MathTextParser('path').parse(s, dpi=72, prop=prop)
            salida = io.BytesIO()
            mathtext.math_to_image(s, salida, prop=prop, dpi=dpi, format=formato, color='#111111')
        except Exception:
            return None
    return salida.getvalue(), ancho, alto, fondo


def dibujar(tex, formato='svg', dpi=72):
    t = normalizar(tex)
    return _dibujar(t, formato, dpi) if t else None


def valida(tex):
    return dibujar(tex) is not None


def img_html(tex):
    """Una <img> con la ecuación (SVG en data URI), del tamaño del texto que la rodea; o el LaTeX si no se pudo."""
    r = dibujar(tex)
    alt = html.escape(normalizar(tex), quote=True)
    if r is None:
        return f'<code class="mm-eq-mala">{alt}</code>'
    datos, ancho, alto, fondo = r
    return (f'<img class="mm-eq" alt="{alt}" src="data:image/svg+xml;base64,{base64.b64encode(datos).decode()}" '
            f'style="height:{(alto + 1) / TAM:.3f}em;vertical-align:-{(fondo + .5) / TAM:.3f}em">')


def en_html(texto_html):
    """Cambia cada \\( … \\) de un HTML ya limpio (o de un texto ya escapado) por su imagen."""
    if not texto_html or '\\(' not in texto_html:
        return texto_html
    return TOKEN.sub(lambda m: img_html(html.unescape(m.group(1))), texto_html)


def partes(texto):
    """['texto', ('eq', tex), 'texto', …] para Word."""
    salida, i = [], 0
    for m in TOKEN.finditer(texto or ''):
        if m.start() > i:
            salida.append(texto[i:m.start()])
        salida.append(('eq', m.group(1)))
        i = m.end()
    if i < len(texto or ''):
        salida.append(texto[i:])
    return salida


def png(tex, puntos=11):
    """(bytes PNG a 300 dpi, alto en puntos) para pegar en Word, o None."""
    r = dibujar(tex, 'png', 300)
    if r is None:
        return None
    datos, _, alto, _ = r
    return datos, (alto + 1) * puntos / TAM
