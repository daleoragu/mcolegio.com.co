"""Graficador de los documentos: funciones, puntos, segmentos, polígonos, circunferencias, vectores, rectas
verticales, áreas bajo la curva y textos sobre un plano cartesiano. Se dibuja con matplotlib (sin internet) y se
guarda como una imagen del docente que además conserva la descripción de la gráfica para volver a editarla.

Las fórmulas las escribe el docente como en el cuaderno («2x^2 - 3x + 1», «sen(x)», «√(x+4)», «|x-2|») y se
leen con un lector propio: solo números, x, π, e, operaciones y una lista cerrada de funciones (nada de eval libre).
"""
import ast
import io
import math
import re
import threading

import numpy as np

MAX_ELEMENTOS = 30
MAX_TEXTO = 120
_candado = threading.Lock()

COLORES = ('#2563eb', '#dc2626', '#16a34a', '#9333ea', '#ea580c', '#0891b2', '#111827', '#db2777')
ESTILOS = {'solida': '-', 'guiones': '--', 'puntos': ':'}
TIPOS = ('funcion', 'punto', 'segmento', 'poligono', 'vector', 'vertical', 'circulo', 'area', 'texto')

# ---------------------------------------------------------------------------
# Lector de fórmulas
# ---------------------------------------------------------------------------
def _sec(x):
    return 1 / np.cos(x)


FUNCIONES = {
    'sin': np.sin, 'sen': np.sin, 'cos': np.cos, 'tan': np.tan, 'tg': np.tan,
    'asin': np.arcsin, 'arcsin': np.arcsin, 'arcsen': np.arcsin, 'acos': np.arccos, 'arccos': np.arccos,
    'atan': np.arctan, 'arctan': np.arctan, 'arctg': np.arctan,
    'sec': _sec, 'csc': lambda x: 1 / np.sin(x), 'cosec': lambda x: 1 / np.sin(x), 'cot': lambda x: 1 / np.tan(x),
    'cotg': lambda x: 1 / np.tan(x), 'sqrt': np.sqrt, 'raiz': np.sqrt, 'abs': np.abs, 'exp': np.exp, 'ln': np.log,
    'log': np.log10, 'log2': np.log2, 'cbrt': np.cbrt, 'piso': np.floor, 'floor': np.floor, 'techo': np.ceil,
    'ceil': np.ceil, 'signo': np.sign, 'sign': np.sign,
}
CONSTANTES = {'pi': math.pi, 'e': math.e}
_OPERADORES = (ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Pow, ast.USub, ast.UAdd)
_TOKEN = re.compile(r'\s*(?:(\d+\.?\d*|\.\d+)|([a-zA-Z_][a-zA-Z_0-9]*)|(\*\*|[-+*/()^,]))')


def _preparar(texto):
    t = str(texto or '').strip()[:MAX_TEXTO]
    for a, b in (('π', 'pi'), ('√', 'sqrt'), ('·', '*'), ('×', '*'), ('÷', '/'), ('−', '-'), ('²', '^2'), ('³', '^3'),
                 ('y=', ''), ('Y=', ''), ('f(x)=', ''), ('g(x)=', ''), ('h(x)=', '')):
        t = t.replace(a, b)
    t = re.sub(r'^\s*[a-zA-Z]\s*(\(\s*x\s*\))?\s*=\s*', '', t)   # «y = …», «f(x) = …»
    t = re.sub(r'(\d),(\d)', r'\1.\2', t)                 # 2,5 → 2.5
    t = re.sub(r'\|([^|]+)\|', r'abs(\1)', t)            # |x-2| → abs(x-2)
    t = re.sub(r'sqrt\s*(\d+\.?\d*|x)', r'sqrt(\1)', t)   # √x → sqrt(x)
    # Separar en partes y poner los «por» que se sobreentienden: 2x, 3(x+1), (x+1)(x-1), 2sen(x), x pi
    partes, i = [], 0
    while i < len(t):
        m = _TOKEN.match(t, i)
        if not m or m.end() == i:
            raise ValueError(f'No entiendo «{t[i:i + 8]}».')
        i = m.end()
        num, nombre, op = m.groups()
        if nombre:
            # «xsen», «2pix»: nombres pegados que se pueden partir en nombres conocidos
            partes.extend(('n', x) for x in _partir(nombre))
        elif num:
            partes.append(('#', num))
        else:
            partes.append(('o', '**' if op == '^' else op))
    # «sen x», «ln 2»: la función sin paréntesis toma lo que sigue (un número, x o π)
    arreglo, k = [], 0
    while k < len(partes):
        tipo, valor = partes[k]
        arreglo.append((tipo, valor))
        if tipo == 'n' and valor in FUNCIONES and k + 1 < len(partes) and partes[k + 1][1] != '(':
            sig = partes[k + 1]
            if sig[0] not in ('#', 'n') or sig[1] in FUNCIONES:
                raise ValueError(f'Escriba {valor}( … ) con paréntesis.')
            arreglo += [('o', '('), sig, ('o', ')')]
            k += 1
        k += 1
    salida = []
    for k, (tipo, valor) in enumerate(arreglo):
        if salida:
            ant_tipo, ant = arreglo[k - 1]
            izquierda = ant_tipo == '#' or (ant_tipo == 'n' and ant not in FUNCIONES) or ant == ')'
            derecha = tipo in ('#', 'n') or valor == '('
            if izquierda and derecha:
                salida.append('*')
        salida.append(valor)
    return ''.join(salida)


def _partir(nombre):
    if nombre in FUNCIONES or nombre in CONSTANTES or nombre == 'x':
        return [nombre]
    conocidos = sorted(list(FUNCIONES) + list(CONSTANTES) + ['x'], key=len, reverse=True)
    salida, resto = [], nombre
    while resto:
        for c in conocidos:
            if resto.startswith(c):
                salida.append(c)
                resto = resto[len(c):]
                break
        else:
            raise ValueError(f'No conozco «{nombre}». Use x, números, π y funciones como sen, cos, tan, raiz, ln, log, abs.')
    return salida


class _Validador(ast.NodeTransformer):
    def visit_Constant(self, n):
        if not isinstance(n.value, (int, float)) or isinstance(n.value, bool):
            raise ValueError('Solo números.')
        return ast.copy_location(ast.Constant(float(n.value)), n)     # en coma flotante: 9**9**9 no se cuelga

    def generic_visit(self, n):
        if isinstance(n, ast.Expression) or isinstance(n, (ast.BinOp, ast.UnaryOp)) or isinstance(n, _OPERADORES) \
                or isinstance(n, ast.Load):
            return super().generic_visit(n)
        if isinstance(n, ast.Name):
            if n.id not in CONSTANTES and n.id != 'x' and n.id not in FUNCIONES:
                raise ValueError(f'No conozco «{n.id}».')
            return n
        if isinstance(n, ast.Call):
            if not isinstance(n.func, ast.Name) or n.func.id not in FUNCIONES or n.keywords or len(n.args) != 1:
                raise ValueError('Una función se escribe así: sen(x), raiz(x+1)…')
            return super().generic_visit(n)
        raise ValueError('Esa fórmula tiene algo que no se puede graficar.')


def compilar(texto, variable=True):
    """La fórmula lista para evaluar con numpy (o ValueError con el motivo, en español)."""
    codigo = _preparar(texto)
    if not codigo:
        raise ValueError('Escriba la fórmula.')
    try:
        arbol = ast.parse(codigo, mode='eval')
    except SyntaxError:
        raise ValueError('Revise los paréntesis y los signos de la fórmula.')
    arbol = ast.fix_missing_locations(_Validador().visit(arbol))
    if not variable and any(isinstance(n, ast.Name) and n.id == 'x' for n in ast.walk(arbol)):
        raise ValueError('Aquí va un número, sin x.')
    return compile(arbol, '<formula>', 'eval')


def evaluar(codigo, x):
    entorno = dict(FUNCIONES, **CONSTANTES, x=x, __builtins__={})
    with np.errstate(all='ignore'):
        y = eval(codigo, entorno)                         # el árbol ya pasó el validador: solo lo permitido
    return np.broadcast_to(np.asarray(y, dtype=float), np.shape(x)).astype(float)


def numero(v, defecto=0.0):
    """Un número escrito como 2, -1.5, 2,5, pi/2 o √2."""
    if isinstance(v, (int, float)) and not isinstance(v, bool):
        r = float(v)
    else:
        try:
            r = float(evaluar(compilar(v, variable=False), 0.0))
        except (ValueError, ZeroDivisionError, OverflowError, TypeError):
            return defecto
    return r if math.isfinite(r) else defecto


# ---------------------------------------------------------------------------
# Limpiar lo que manda el navegador
# ---------------------------------------------------------------------------
def _color(v, k=0):
    from .bloques import _a_hex
    return _a_hex(v) or COLORES[k % len(COLORES)]


def _texto(v, n=MAX_TEXTO):
    return ' '.join(str(v or '').split())[:n]


def _punto(p):
    if not isinstance(p, (list, tuple)) or len(p) < 2:
        raise ValueError('punto inválido')
    return [round(numero(p[0]), 4), round(numero(p[1]), 4)]


def limpiar(spec):
    """La descripción de la gráfica validada (rangos sensatos, máximo 30 elementos, fórmulas como texto)."""
    spec = spec if isinstance(spec, dict) else {}
    x = [numero(v) for v in (spec.get('x') or [-6, 6])[:2]] if isinstance(spec.get('x'), list) else [-6.0, 6.0]
    y = [numero(v) for v in (spec.get('y') or [-4, 4])[:2]] if isinstance(spec.get('y'), list) else [-4.0, 4.0]
    if len(x) < 2 or x[0] >= x[1]:
        x = [-6.0, 6.0]
    if len(y) < 2 or y[0] >= y[1]:
        y = [-4.0, 4.0]
    x = [max(-1e6, x[0]), min(1e6, x[1])]
    y = [max(-1e6, y[0]), min(1e6, y[1])]
    limpio = {'x': x, 'y': y, 'cuadricula': spec.get('cuadricula', True) is not False, 'ejes': spec.get('ejes', True) is not False,
              'numeros': spec.get('numeros', True) is not False, 'escala_igual': bool(spec.get('escala_igual')),
              'pi': bool(spec.get('pi')), 'forma': spec.get('forma') if spec.get('forma') in ('ancha', 'cuadrada', 'alta') else 'ancha',
              'nombre_x': _texto(spec.get('nombre_x', 'x'), 12), 'nombre_y': _texto(spec.get('nombre_y', 'y'), 12), 'elementos': []}
    for k, e in enumerate((spec.get('elementos') or [])[:MAX_ELEMENTOS]):
        if not isinstance(e, dict) or e.get('t') not in TIPOS:
            continue
        t = e['t']
        n = {'t': t, 'color': _color(e.get('color'), k), 'nombre': _texto(e.get('nombre'), 40)}
        try:
            if t in ('funcion', 'area'):
                n['expr'] = _texto(e.get('expr'))
                n['desde'] = _texto(e.get('desde'), 20)
                n['hasta'] = _texto(e.get('hasta'), 20)
                if t == 'funcion':
                    n['estilo'] = e.get('estilo') if e.get('estilo') in ESTILOS else 'solida'
                    n['grosor'] = max(1.0, min(5.0, numero(e.get('grosor'), 2.2)))
                else:
                    n['expr2'] = _texto(e.get('expr2'))          # vacía: hasta el eje x
            elif t == 'punto':
                n['x'], n['y'] = _punto([e.get('x'), e.get('y')])
                n['proyecciones'] = bool(e.get('proyecciones'))
            elif t in ('segmento', 'vector'):
                n['a'], n['b'] = _punto(e.get('a')), _punto(e.get('b'))
                n['estilo'] = e.get('estilo') if e.get('estilo') in ESTILOS else 'solida'
            elif t == 'poligono':
                n['puntos'] = [_punto(p) for p in (e.get('puntos') or [])[:20]]
                if len(n['puntos']) < 2:
                    continue
                n['relleno'] = e.get('relleno', True) is not False
                n['vertices'] = _texto(e.get('vertices'), 40)        # «A,B,C»: nombres de los vértices
            elif t == 'vertical':
                n['x'] = round(numero(e.get('x')), 4)
                n['estilo'] = e.get('estilo') if e.get('estilo') in ESTILOS else 'guiones'
            elif t == 'circulo':
                n['cx'], n['cy'] = _punto([e.get('cx'), e.get('cy')])
                n['r'] = max(0.0, round(numero(e.get('r'), 1), 4))
                n['relleno'] = bool(e.get('relleno'))
            elif t == 'texto':
                n['x'], n['y'] = _punto([e.get('x'), e.get('y')])
                n['texto'] = _texto(e.get('texto'), 80)
                if not n['texto']:
                    continue
        except ValueError:
            continue
        limpio['elementos'].append(n)
    return limpio


# ---------------------------------------------------------------------------
# Dibujar
# ---------------------------------------------------------------------------
FORMAS = {'ancha': (6.4, 4.2), 'cuadrada': (5.0, 5.0), 'alta': (4.4, 5.6)}


def _ticks_pi(eje, lo, hi):
    from matplotlib.ticker import FuncFormatter, MultipleLocator
    paso = math.pi / 2 if (hi - lo) <= 8 * math.pi else math.pi

    def fmt(v, _):
        k = round(v / (math.pi / 2))
        if abs(v - k * math.pi / 2) > 1e-6 or k == 0:
            return ''
        if k % 2 == 0:
            m = k // 2
            return {1: 'π', -1: '−π'}.get(m, f'{m}π'.replace('-', '−'))
        return {1: 'π/2', -1: '−π/2'}.get(k, f'{k}π/2'.replace('-', '−'))
    eje.set_major_locator(MultipleLocator(paso))
    eje.set_major_formatter(FuncFormatter(fmt))


def _corte(v, lo, hi):
    if v is None or v == '':
        return None
    r = numero(v, None)
    return None if r is None else max(lo, min(hi, r))


def dibujar(spec, formato='svg', dpi=110):
    """(bytes, caja_de_los_ejes [x0, y0, x1, y1] en fracción de la imagen desde abajo, errores {índice: motivo})."""
    import matplotlib
    matplotlib.use('Agg')
    from matplotlib import rc_context
    from matplotlib.figure import Figure
    from matplotlib.backends.backend_agg import FigureCanvasAgg
    from matplotlib.ticker import MaxNLocator
    s = limpiar(spec)
    errores = {}
    (x0, x1), (y0, y1) = s['x'], s['y']
    with _candado, rc_context({'font.family': 'DejaVu Sans', 'mathtext.fontset': 'cm', 'svg.fonttype': 'path', 'axes.unicode_minus': True}):
        fig = Figure(figsize=FORMAS[s['forma']])
        FigureCanvasAgg(fig)
        fig.subplots_adjust(left=.06, right=.97, top=.96, bottom=.07)
        ax = fig.add_subplot(111)
        ax.set_xlim(x0, x1)
        ax.set_ylim(y0, y1)
        if s['escala_igual']:
            ax.set_aspect('equal', adjustable='box')
        # Ejes que pasan por el origen (si se ve), con flechas, como en el cuaderno
        for lado in ('top', 'right'):
            ax.spines[lado].set_visible(False)
        if s['ejes']:
            ax.spines['left'].set_position(('data', 0 if x0 <= 0 <= x1 else x0))
            ax.spines['bottom'].set_position(('data', 0 if y0 <= 0 <= y1 else y0))
            for lado in ('left', 'bottom'):
                ax.spines[lado].set_color('#333333')
                ax.spines[lado].set_linewidth(1.1)
                ax.spines[lado].set_zorder(2)
            ox = 0 if x0 <= 0 <= x1 else x0
            oy = 0 if y0 <= 0 <= y1 else y0
            ax.plot(1, oy, '>', color='#333333', transform=ax.get_yaxis_transform(), clip_on=False, ms=6)
            ax.plot(ox, 1, '^', color='#333333', transform=ax.get_xaxis_transform(), clip_on=False, ms=6)
            ax.annotate(s['nombre_x'], xy=(1, oy), xycoords=ax.get_yaxis_transform(), xytext=(-2, 8),
                        textcoords='offset points', ha='right', fontsize=11, style='italic')
            ax.annotate(s['nombre_y'], xy=(ox, 1), xycoords=ax.get_xaxis_transform(), xytext=(8, -4),
                        textcoords='offset points', va='top', fontsize=11, style='italic')
        else:
            for lado in ('left', 'bottom'):
                ax.spines[lado].set_visible(False)
        if s['pi']:
            _ticks_pi(ax.xaxis, x0, x1)
        else:
            ax.xaxis.set_major_locator(MaxNLocator(nbins=14, steps=[1, 2, 2.5, 5, 10]))
        ax.yaxis.set_major_locator(MaxNLocator(nbins=10, steps=[1, 2, 2.5, 5, 10]))
        if s['numeros'] and s['ejes']:
            from matplotlib.ticker import FuncFormatter
            ax.tick_params(labelsize=8.5, colors='#333333', length=3)
            if not s['pi']:
                ax.xaxis.set_major_formatter(FuncFormatter(_num_eje))
            ax.yaxis.set_major_formatter(FuncFormatter(_num_eje))
        else:
            ax.tick_params(labelbottom=False, labelleft=False, length=0 if not s['ejes'] else 3)
        if s['cuadricula']:
            ax.grid(True, color='#d0d5dd', linewidth=.6)
            ax.minorticks_on()
            ax.grid(True, which='minor', color='#eef0f3', linewidth=.4)
            ax.tick_params(which='minor', length=0)
        ax.set_axisbelow(True)
        xs = np.linspace(x0, x1, 2000)
        alto = y1 - y0
        for k, e in enumerate(s['elementos']):
            try:
                _elemento(ax, e, xs, x0, x1, y0, y1, alto)
            except (ValueError, ZeroDivisionError, OverflowError, TypeError, FloatingPointError) as error:
                errores[k] = str(error) or 'No se pudo dibujar.'
        fig.canvas.draw()
        pos = ax.get_position()
        salida = io.BytesIO()
        fig.savefig(salida, format=formato, dpi=dpi, facecolor='white')
    return salida.getvalue(), [round(float(v), 4) for v in (pos.x0, pos.y0, pos.x1, pos.y1)], errores


def _num_eje(v, pos=None):
    """Los números de los ejes como en el cuaderno: sin el 0 del origen, con coma decimal y signo menos."""
    if abs(v) < 1e-9:
        return ''
    t = f'{v:.2f}'.rstrip('0').rstrip('.') if abs(v - round(v)) > 1e-9 else str(int(round(v)))
    return t.replace('.', ',').replace('-', '−')


def _elemento(ax, e, xs, x0, x1, y0, y1, alto):
    t, c = e['t'], e['color']
    if t == 'funcion':
        cod = compilar(e['expr'])
        lo, hi = _corte(e['desde'], x0, x1), _corte(e['hasta'], x0, x1)
        x = np.linspace(lo if lo is not None else x0, hi if hi is not None else x1, 2000)
        y = evaluar(cod, x).copy()
        y[~np.isfinite(y)] = np.nan
        # saltos (tan, 1/x): no se unen los pedazos
        saltos = np.abs(np.diff(y)) > alto * 1.5
        y[1:][saltos] = np.nan
        y[(y < y0 - alto * 3) | (y > y1 + alto * 3)] = np.nan
        if np.all(np.isnan(y)):
            raise ValueError('La función no tiene puntos en esta ventana.')
        ax.plot(x, y, ESTILOS[e['estilo']], color=c, linewidth=e['grosor'], zorder=4)
        if e['nombre']:
            visibles = np.where(np.isfinite(y) & (y >= y0) & (y <= y1))[0]
            if len(visibles):
                i = visibles[int(len(visibles) * .82)]
                derecha = x[i] > x0 + .6 * (x1 - x0)          # cerca del borde: el nombre va a la izquierda del punto
                ax.annotate(e['nombre'], (x[i], y[i]), xytext=(-6 if derecha else 6, 6), textcoords='offset points', color=c, fontsize=11,
                            ha='right' if derecha else 'left',
                            fontweight='bold', zorder=6, bbox=dict(boxstyle='round,pad=.15', fc='white', ec='none', alpha=.8))
    elif t == 'area':
        cod = compilar(e['expr'])
        cod2 = compilar(e['expr2']) if e['expr2'] else None
        lo, hi = _corte(e['desde'], x0, x1), _corte(e['hasta'], x0, x1)
        if lo is None or hi is None or lo >= hi:
            raise ValueError('Escriba desde dónde y hasta dónde va el área.')
        x = np.linspace(lo, hi, 800)
        y = evaluar(cod, x)
        y2 = evaluar(cod2, x) if cod2 is not None else np.zeros_like(x)
        ax.fill_between(x, y, y2, where=np.isfinite(y) & np.isfinite(y2), color=c, alpha=.25, linewidth=0, zorder=3)
        if e['nombre']:
            ax.text((lo + hi) / 2, float(np.nanmean((y + y2) / 2)), e['nombre'], color=c, ha='center', va='center', fontsize=11,
                    fontweight='bold', zorder=6)
    elif t == 'punto':
        ax.plot([e['x']], [e['y']], 'o', color=c, ms=6.5, zorder=7, markeredgecolor='white', markeredgewidth=.8)
        if e['proyecciones']:
            ax.plot([e['x'], e['x']], [0 if y0 <= 0 <= y1 else y0, e['y']], ':', color=c, linewidth=1.2, zorder=3)
            ax.plot([0 if x0 <= 0 <= x1 else x0, e['x']], [e['y'], e['y']], ':', color=c, linewidth=1.2, zorder=3)
        if e['nombre']:
            ax.annotate(e['nombre'], (e['x'], e['y']), xytext=(5, 5), textcoords='offset points', color=c, fontsize=11,
                        fontweight='bold', zorder=8)
    elif t == 'segmento':
        (ax_, ay), (bx, by) = e['a'], e['b']
        ax.plot([ax_, bx], [ay, by], ESTILOS[e['estilo']], color=c, linewidth=2, zorder=5)
        if e['nombre']:
            ax.annotate(e['nombre'], ((ax_ + bx) / 2, (ay + by) / 2), xytext=(4, 4), textcoords='offset points', color=c, fontsize=10.5, zorder=8)
    elif t == 'vector':
        (ax_, ay), (bx, by) = e['a'], e['b']
        ax.annotate('', xy=(bx, by), xytext=(ax_, ay), zorder=6,
                    arrowprops=dict(arrowstyle='-|>', color=c, lw=2, mutation_scale=16, linestyle=ESTILOS[e['estilo']]))
        if e['nombre']:
            ax.annotate(e['nombre'], ((ax_ + bx) / 2, (ay + by) / 2), xytext=(4, 6), textcoords='offset points', color=c,
                        fontsize=11, fontweight='bold', zorder=8)
    elif t == 'poligono':
        from matplotlib.patches import Polygon
        pts = e['puntos']
        ax.add_patch(Polygon(pts, closed=len(pts) > 2, fill=e['relleno'] and len(pts) > 2, facecolor=c, alpha=.18 if e['relleno'] else 1,
                             edgecolor='none', zorder=3))
        cerrado = pts + ([pts[0]] if len(pts) > 2 else [])
        ax.plot([p[0] for p in cerrado], [p[1] for p in cerrado], '-', color=c, linewidth=2, zorder=5)
        ax.plot([p[0] for p in pts], [p[1] for p in pts], 'o', color=c, ms=4.5, zorder=6)
        nombres = [x.strip() for x in e['vertices'].split(',')] if e['vertices'] else []
        cx, cy = sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts)
        for p, nom in zip(pts, nombres):
            if nom:
                dx, dy = p[0] - cx, p[1] - cy
                d = math.hypot(dx, dy) or 1
                ax.annotate(nom, (p[0], p[1]), xytext=(9 * dx / d, 9 * dy / d), textcoords='offset points', ha='center', va='center',
                            color=c, fontsize=11, fontweight='bold', zorder=8)
        if e['nombre']:
            ax.text(cx, cy, e['nombre'], color=c, ha='center', va='center', fontsize=10.5, zorder=8)
    elif t == 'vertical':
        ax.axvline(e['x'], linestyle=ESTILOS[e['estilo']], color=c, linewidth=1.6, zorder=4)
        if e['nombre']:
            ax.annotate(e['nombre'], (e['x'], y1), xytext=(4, -14), textcoords='offset points', color=c, fontsize=10.5, zorder=8)
    elif t == 'circulo':
        from matplotlib.patches import Circle
        ax.add_patch(Circle((e['cx'], e['cy']), e['r'], fill=e['relleno'], facecolor=c, alpha=.18 if e['relleno'] else 1,
                            edgecolor='none', zorder=3))
        ax.add_patch(Circle((e['cx'], e['cy']), e['r'], fill=False, edgecolor=c, linewidth=2, zorder=5))
        if e['nombre']:
            ax.annotate(e['nombre'], (e['cx'] + e['r'] * .72, e['cy'] + e['r'] * .72), xytext=(4, 4), textcoords='offset points',
                        color=c, fontsize=11, fontweight='bold', zorder=8)
    elif t == 'texto':
        ax.text(e['x'], e['y'], e['texto'], color=c, fontsize=11, zorder=8,
                bbox=dict(boxstyle='round,pad=.2', fc='white', ec='none', alpha=.75))
