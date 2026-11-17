"""Familia Sudoku: genera los niveles de cada variante y verifica que cada uno tenga UNA sola solución.

    python3 sudoku.py                  todas las variantes
    python3 sudoku.py sudoku_x 7       solo una (con semilla)

Cómo se arma un nivel:
  1. Se llena una cuadrícula completa al azar que cumple las reglas de la variante (filas, columnas, cajas
     o regiones irregulares, diagonales, ventanas, sin caballo, sin rey…).
  2. Con esa solución se ponen las pistas propias de la variante (signos, puntos, termómetros, flechas,
     jaulas, sumas de sándwich, casillas par/impar).
  3. Se quitan números dados uno por uno al azar, comprobando con el solucionador que siga habiendo una
     sola solución, hasta llegar a la cantidad de la dificultad.
Los niveles quedan en aula/static/aula/logica/niveles/<variante>.json, del más fácil al más difícil.
"""
import json
import os
import random
import sys
import time

AQUI = os.path.dirname(os.path.abspath(__file__))
SALIDA = os.path.join(AQUI, '..', 'static', 'aula', 'logica', 'niveles')
CAJAS = {4: (2, 2), 6: (2, 3), 9: (3, 3)}


# ----------------------------------------------------------------------------- reglas
class Reglas:
    """Las reglas de un tablero: grupos sin repetir, vecinos prohibidos, pares de casillas y restricciones de varias."""

    def __init__(self, n, regiones=None, diagonales=False, ventanas=False, caballo=False, rey=False):
        self.n, self.N = n, n * n
        self.regiones = regiones or [((f // CAJAS[n][0]) * (n // CAJAS[n][1]) + c // CAJAS[n][1]) for f in range(n) for c in range(n)]
        self.grupos = [[f * n + c for c in range(n)] for f in range(n)] + [[f * n + c for f in range(n)] for c in range(n)]
        self.grupos += [[i for i in range(self.N) if self.regiones[i] == r] for r in range(n)]
        if diagonales:
            self.grupos += [[k * n + k for k in range(n)], [k * n + n - 1 - k for k in range(n)]]
        if ventanas and n == 9:
            for f0, c0 in ((1, 1), (1, 5), (5, 1), (5, 5)):
                self.grupos.append([(f0 + a) * n + c0 + b for a in range(3) for b in range(3)])
        self.vecinos = [set() for _ in range(self.N)]
        for g in self.grupos:
            for i in g:
                self.vecinos[i].update(x for x in g if x != i)
        saltos = []
        if caballo:
            saltos += [(1, 2), (2, 1), (-1, 2), (-2, 1), (1, -2), (2, -1), (-1, -2), (-2, -1)]
        if rey:
            saltos += [(1, 1), (1, -1), (-1, 1), (-1, -1)]
        for i in range(self.N):
            f, c = divmod(i, n)
            for df, dc in saltos:
                if 0 <= f + df < n and 0 <= c + dc < n:
                    self.vecinos[i].add((f + df) * n + c + dc)
        self.vecinos = [sorted(v) for v in self.vecinos]
        self.binarias = [[] for _ in range(self.N)]       # (j, tabla[a] = valores permitidos de j si i vale a)
        self.unarias = [0] * self.N                         # máscara de valores permitidos (0 = todos)
        self.varias = []                                    # (casillas, función(valores) → ¿todavía posible?)
        self.de_casilla = [[] for _ in range(self.N)]

    def par(self, i, j, rel):
        """Restricción entre dos casillas: rel(a, b) con a en i y b en j."""
        t1 = [0] * (self.n + 1)
        t2 = [0] * (self.n + 1)
        for a in range(1, self.n + 1):
            for b in range(1, self.n + 1):
                if rel(a, b):
                    t1[a] |= 1 << b
                    t2[b] |= 1 << a
        self.binarias[i].append((j, t1))
        self.binarias[j].append((i, t2))

    def solo(self, i, valores):
        m = 0
        for v in valores:
            m |= 1 << v
        self.unarias[i] = (self.unarias[i] or m) & m

    def varios(self, casillas, fn):
        k = len(self.varias)
        self.varias.append((casillas, fn))
        for i in casillas:
            self.de_casilla[i].append(k)

    def grupo(self, casillas):
        """Casillas que no pueden repetir (jaulas del killer)."""
        for i in casillas:
            for j in casillas:
                if i != j and j not in self.vecinos[i]:
                    self.vecinos[i].append(j)


# ----------------------------------------------------------------------------- solucionador
def resolver(R, dados, limite=2, azar=None, tope=200000):
    """Lista de hasta `limite` soluciones (cada una, lista de valores). dados: lista con 0 en las vacías."""
    n, N = R.n, R.N
    todos = sum(1 << v for v in range(1, n + 1))
    cand = [(R.unarias[i] or todos) & todos for i in range(N)]
    val = [0] * N
    sols, pasos = [], [0]

    def poner(cand, val, i, v):
        val[i] = v
        cand[i] = 1 << v
        b = 1 << v
        for j in R.vecinos[i]:
            if val[j] == v:
                return False
            if not val[j] and cand[j] & b:
                cand[j] &= ~b
                if not cand[j]:
                    return False
        for j, t in R.binarias[i]:
            if val[j]:
                if not (t[v] >> val[j]) & 1:
                    return False
            else:
                cand[j] &= t[v]
                if not cand[j]:
                    return False
        for k in R.de_casilla[i]:
            cas, fn = R.varias[k]
            if not fn([val[x] for x in cas], [cand[x] for x in cas]):
                return False
        return True

    for i, v in enumerate(dados):
        if v and not (cand[i] >> v) & 1:
            return []
    for i, v in enumerate(dados):
        if v and not poner(cand, val, i, v):
            return []

    def buscar(cand, val):
        pasos[0] += 1
        if pasos[0] > tope:
            raise TimeoutError
        mejor, cuenta = -1, 99
        for i in range(N):
            if not val[i]:
                c = bin(cand[i]).count('1')
                if c < cuenta:
                    mejor, cuenta = i, c
                    if c <= 1:
                        break
        if mejor < 0:
            sols.append(val[:])
            return len(sols) >= limite
        opciones = [v for v in range(1, n + 1) if (cand[mejor] >> v) & 1]
        if azar:
            azar.shuffle(opciones)
        for v in opciones:
            c2, v2 = cand[:], val[:]
            if poner(c2, v2, mejor, v) and buscar(c2, v2):
                return True
        return False

    buscar(cand, val)
    return sols


# ----------------------------------------------------------------------------- piezas de cada variante
def regiones_irregulares(n, rng):
    """Parte de las cajas normales e intercambia casillas del borde entre regiones vecinas (cada región sigue
    conectada y con n casillas), hasta que las regiones quedan bien torcidas."""
    reg = [((f // CAJAS[n][0]) * (n // CAJAS[n][1]) + c // CAJAS[n][1]) for f in range(n) for c in range(n)]

    def conectada(r):
        cas = [i for i in range(n * n) if reg[i] == r]
        vistos, pila = {cas[0]}, [cas[0]]
        while pila:
            for j in vecinos4(pila.pop(), n):
                if reg[j] == r and j not in vistos:
                    vistos.add(j)
                    pila.append(j)
        return len(vistos) == len(cas)
    hechos = 0
    for _ in range(n * n * 400):
        if hechos >= n * n * 3:
            break
        a = rng.randrange(n * n)
        otros = [b for b in vecinos4(a, n) if reg[b] != reg[a]]
        if not otros:
            continue
        b = rng.choice(otros)
        ra, rb = reg[a], reg[b]
        # a pasa a la región de b y una casilla de rb vecina de ra pasa a ra
        cand = [c for c in range(n * n) if reg[c] == rb and c != b and any(reg[d] == ra and d != a for d in vecinos4(c, n))]
        if not cand:
            continue
        c = rng.choice(cand)
        reg[a], reg[c] = rb, ra
        if conectada(ra) and conectada(rb):
            hechos += 1
        else:
            reg[a], reg[c] = ra, rb
    return reg


def vecinos4(i, n):
    f, c = divmod(i, n)
    return [(f + a) * n + c + b for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1)) if 0 <= f + a < n and 0 <= c + b < n]


def vecinos8(i, n):
    f, c = divmod(i, n)
    return [(f + a) * n + c + b for a in (-1, 0, 1) for b in (-1, 0, 1) if (a or b) and 0 <= f + a < n and 0 <= c + b < n]


def pares_adyacentes(n):
    for f in range(n):
        for c in range(n):
            i = f * n + c
            if c + 1 < n:
                yield i, i + 1
            if f + 1 < n:
                yield i, i + n


def poner_extras(var, R, sol, rng, x):
    """Las pistas propias de la variante (sacadas de la solución). x: dict con lo que va al nivel."""
    n = R.n
    if var == 'parimpar':
        casillas = rng.sample(range(n * n), int(n * n * .3))
        x['paridad'] = {str(i): ('p' if sol[i] % 2 == 0 else 'i') for i in casillas}
        for i in casillas:
            R.solo(i, [v for v in range(1, n + 1) if v % 2 == sol[i] % 2])
    elif var in ('consecutivo', 'kropki', 'xv'):
        marcas = {}
        for i, j in pares_adyacentes(n):
            a, b = sol[i], sol[j]
            if var == 'consecutivo' and abs(a - b) == 1:
                marcas[f'{i}-{j}'] = 'c'
            elif var == 'kropki':
                if a == 2 * b or b == 2 * a:
                    marcas[f'{i}-{j}'] = 'n'
                elif abs(a - b) == 1:
                    marcas[f'{i}-{j}'] = 'b'
            elif var == 'xv' and n == 9 and a + b in (5, 10):
                marcas[f'{i}-{j}'] = 'V' if a + b == 5 else 'X'
            elif var == 'xv' and n == 6 and a + b in (5, 7):
                marcas[f'{i}-{j}'] = 'V' if a + b == 5 else 'S'
        x['marcas'] = marcas
        for i, j in pares_adyacentes(n):
            m = marcas.get(f'{i}-{j}')
            if var == 'consecutivo':
                R.par(i, j, (lambda a, b: abs(a - b) == 1) if m else (lambda a, b: abs(a - b) != 1))
            elif var == 'kropki':
                if m == 'n':
                    R.par(i, j, lambda a, b: a == 2 * b or b == 2 * a)
                elif m == 'b':
                    R.par(i, j, lambda a, b: abs(a - b) == 1)
                else:
                    R.par(i, j, lambda a, b: abs(a - b) != 1 and a != 2 * b and b != 2 * a)
            else:
                sumas = {'V': 5, 'X': 10, 'S': 7}
                if m:
                    s = sumas[m]
                    R.par(i, j, lambda a, b, s=s: a + b == s)
                else:
                    prohibidas = (5, 10) if n == 9 else (5, 7)
                    R.par(i, j, lambda a, b, p=prohibidas: a + b not in p)
    elif var == 'mayor':
        signos = {}
        for i, j in pares_adyacentes(n):
            if R.regiones[i] == R.regiones[j]:
                signos[f'{i}-{j}'] = '<' if sol[i] < sol[j] else '>'
                R.par(i, j, (lambda a, b: a < b) if sol[i] < sol[j] else (lambda a, b: a > b))
        x['signos'] = signos
    elif var == 'termo':
        usados, termos = set(), []
        for _ in range(400):
            if len(termos) >= (4 if n == 6 else 7):
                break
            i = rng.randrange(n * n)
            if i in usados:
                continue
            camino = [i]
            while len(camino) < rng.choice((3, 4, 5)):
                sig = [j for j in vecinos8(camino[-1], n) if j not in usados and j not in camino and sol[j] > sol[camino[-1]]]
                if not sig:
                    break
                camino.append(rng.choice(sig))
            if len(camino) >= 3:
                termos.append(camino)
                usados.update(camino)
        x['termos'] = termos
        for t in termos:
            for a, b in zip(t, t[1:]):
                R.par(a, b, lambda p, q: p < q)
    elif var == 'flechas':
        usados, flechas = set(), []
        for _ in range(3000):
            if len(flechas) >= (3 if n == 6 else 6):
                break
            i = rng.randrange(n * n)
            if i in usados or sol[i] < 3:
                continue
            for _ in range(30):
                camino, suma = [], 0
                actual = i
                while suma < sol[i] and len(camino) < 3:
                    sig = [j for j in vecinos8(actual, n) if j not in usados and j != i and j not in camino]
                    if not sig:
                        break
                    actual = rng.choice(sig)
                    camino.append(actual)
                    suma += sol[actual]
                if suma == sol[i] and len(camino) >= 2:
                    flechas.append([i] + camino)
                    usados.update([i] + camino)
                    break
        x['flechas'] = flechas
        for fl in flechas:
            def fn(vals, cands, n=n):
                if vals[0] and all(vals[1:]):
                    return vals[0] == sum(vals[1:])
                if all(vals[1:]):
                    s = sum(vals[1:])
                    return (cands[0] >> s) & 1 if s <= n else False
                return sum(vals[1:]) < (vals[0] or n + 1)
            R.varios(fl, fn)
    elif var == 'sandwich':
        lineas = [[f * n + c for c in range(n)] for f in range(n)] + [[f * n + c for f in range(n)] for c in range(n)]
        sumas = []
        for li in lineas:
            v = [sol[i] for i in li]
            a, b = sorted((v.index(1), v.index(n)))
            sumas.append(sum(v[a + 1:b]))
        x['sandwich'] = sumas
        for li, s in zip(lineas, sumas):
            def fn(vals, cands, s=s, n=n):
                if 1 in vals and n in vals:
                    a, b = sorted((vals.index(1), vals.index(n)))
                    if all(vals[a + 1:b]):
                        return sum(vals[a + 1:b]) == s
                return True
            R.varios(li, fn)
    elif var == 'killer':
        libre, jaulas = set(range(n * n)), []
        while libre:
            i = min(libre)
            jaula = [i]
            libre.discard(i)
            meta = rng.choice((1, 2, 2, 3, 3, 3, 4)) if n == 9 else rng.choice((1, 2, 2, 3, 3))
            while len(jaula) < meta:
                sig = [j for k in jaula for j in vecinos4(k, n) if j in libre and sol[j] not in {sol[q] for q in jaula}]
                if not sig:
                    break
                j = rng.choice(sig)
                jaula.append(j)
                libre.discard(j)
            jaulas.append(jaula)
        x['jaulas'] = [{'c': j, 's': sum(sol[k] for k in j)} for j in jaulas]
        for j in jaulas:
            R.grupo(j)
            s = sum(sol[k] for k in j)

            def fn(vals, cands, s=s):
                t = sum(vals)
                return t == s if all(vals) else t < s
            R.varios(j, fn)


# ----------------------------------------------------------------------------- variantes
# id: (nombre, tamaños por tramo [(n, cuántos niveles, % de casillas que quedan dadas al inicio → al final)], opciones)
VARIANTES = {
    'sudoku': ('Sudoku', [(9, 30, (.52, .32))], {}),
    'sudoku_mini': ('Sudoku mini', [(4, 10, (.62, .38)), (6, 20, (.58, .36))], {}),
    'sudoku_figuras': ('Sudoku de figuras', [(4, 14, (.62, .40)), (6, 12, (.58, .40))], {}),
    'sudoku_x': ('Sudoku en X', [(6, 10, (.5, .32)), (9, 18, (.45, .28))], {'diagonales': True}),
    'sudoku_hiper': ('Sudoku de ventanas', [(9, 24, (.45, .28))], {'ventanas': True}),
    'sudoku_irregular': ('Sudoku irregular', [(6, 10, (.5, .34)), (9, 16, (.45, .3))], {'irregular': True}),
    'sudoku_parimpar': ('Sudoku par e impar', [(6, 10, (.4, .25)), (9, 16, (.36, .22))], {}),
    'sudoku_consecutivo': ('Sudoku consecutivo', [(6, 10, (.25, .08)), (9, 16, (.2, .06))], {}),
    'sudoku_mayor': ('Sudoku mayor que', [(6, 10, (.2, .04)), (9, 14, (.12, .02))], {}),
    'sudoku_kropki': ('Sudoku de puntos', [(6, 10, (.22, .06)), (9, 16, (.18, .05))], {}),
    'sudoku_xv': ('Sudoku de sumas', [(6, 10, (.3, .12)), (9, 16, (.25, .1))], {}),
    'sudoku_termo': ('Sudoku termómetro', [(6, 10, (.4, .25)), (9, 16, (.36, .24))], {}),
    'sudoku_flechas': ('Sudoku de flechas', [(6, 10, (.42, .28)), (9, 16, (.38, .26))], {}),
    'sudoku_sandwich': ('Sudoku sándwich', [(6, 10, (.3, .12)), (9, 14, (.28, .14))], {}),
    'sudoku_caballo': ('Sudoku sin caballo', [(6, 10, (.42, .28)), (9, 16, (.38, .24))], {'caballo': True}),
    'sudoku_rey': ('Sudoku sin rey', [(6, 10, (.42, .28)), (9, 16, (.38, .24))], {'rey': True}),
    'sudoku_killer': ('Sudoku asesino', [(6, 10, (.2, .04)), (9, 16, (.12, .0))], {}),
}
EXTRA = {'sudoku_parimpar': 'parimpar', 'sudoku_consecutivo': 'consecutivo', 'sudoku_mayor': 'mayor', 'sudoku_kropki': 'kropki',
         'sudoku_xv': 'xv', 'sudoku_termo': 'termo', 'sudoku_flechas': 'flechas', 'sudoku_sandwich': 'sandwich', 'sudoku_killer': 'killer'}


def un_nivel(var, n, meta, rng):
    _, _, op = VARIANTES[var]
    regiones = regiones_irregulares(n, rng) if op.get('irregular') else None
    base = dict(diagonales=op.get('diagonales', False), ventanas=op.get('ventanas', False),
                caballo=op.get('caballo', False), rey=op.get('rey', False))
    R0 = Reglas(n, regiones, **base)
    try:
        sols = resolver(R0, [0] * (n * n), limite=1, azar=rng, tope=60000)
    except TimeoutError:                    # regiones difíciles de llenar: se prueban otras
        return None
    if not sols:
        return None
    sol = sols[0]
    R = Reglas(n, regiones, **base)
    x = {}
    if var in EXTRA:
        poner_extras(EXTRA[var], R, sol, rng, x)
    dados = sol[:]
    orden = list(range(n * n))
    rng.shuffle(orden)
    quedan = n * n
    objetivo = max(0, round(meta * n * n))
    for i in orden:
        if quedan <= objetivo:
            break
        v, dados[i] = dados[i], 0
        try:
            unica = len(resolver(R, dados, limite=2)) == 1
        except TimeoutError:
            unica = False
        if unica:
            quedan -= 1
        else:
            dados[i] = v
    if quedan > objetivo + n * .6:          # no se pudo bajar a lo que pide la dificultad
        return None
    nivel = {'n': n, 'dados': ''.join(str(v) for v in dados), 'sol': ''.join(str(v) for v in sol)}
    if regiones:
        nivel['regiones'] = ''.join(str(r) for r in regiones)
    nivel.update(x)
    return nivel


def generar(var, semilla=1):
    rng = random.Random(semilla)
    niveles = []
    for n, cuantos, (desde, hasta) in VARIANTES[var][1]:
        k = 0
        intentos = 0
        while k < cuantos and intentos < cuantos * 30:
            intentos += 1
            meta = desde + (hasta - desde) * k / max(1, cuantos - 1)
            nv = un_nivel(var, n, meta, rng)
            if nv:
                niveles.append(nv)
                k += 1
                print(f'  {var} {n}x{n} nivel {len(niveles)} · dados {sum(c != "0" for c in nv["dados"])}', flush=True)
    return niveles


if __name__ == '__main__':
    lista = [sys.argv[1]] if len(sys.argv) > 1 else list(VARIANTES)
    semilla = int(sys.argv[2]) if len(sys.argv) > 2 else 11
    for var in lista:
        t = time.time()
        nv = generar(var, semilla)
        with open(os.path.join(SALIDA, var + '.json'), 'w', encoding='utf-8') as f:
            json.dump(nv, f, ensure_ascii=False, separators=(',', ':'))
        print(f'{var}: {len(nv)} niveles en {time.time() - t:.0f} s', flush=True)


# ----------------------------------------------------------------------------- verificación de los archivos
def reglas_de_nivel(var, nv):
    """Arma las reglas solo con lo que trae el nivel (lo mismo que ve el estudiante)."""
    n = nv['n']
    op = VARIANTES[var][2]
    reg = [int(c) for c in nv['regiones']] if nv.get('regiones') else None
    R = Reglas(n, reg, diagonales=op.get('diagonales', False), ventanas=op.get('ventanas', False),
               caballo=op.get('caballo', False), rey=op.get('rey', False))
    for k, p in (nv.get('paridad') or {}).items():
        R.solo(int(k), [v for v in range(1, n + 1) if v % 2 == (0 if p == 'p' else 1)])
    marcas = nv.get('marcas')
    if marcas is not None:
        for i, j in pares_adyacentes(n):
            m = marcas.get(f'{i}-{j}')
            if var == 'sudoku_consecutivo':
                R.par(i, j, (lambda a, b: abs(a - b) == 1) if m else (lambda a, b: abs(a - b) != 1))
            elif var == 'sudoku_kropki':
                R.par(i, j, {'n': lambda a, b: a == 2 * b or b == 2 * a, 'b': lambda a, b: abs(a - b) == 1}.get(
                    m, lambda a, b: abs(a - b) != 1 and a != 2 * b and b != 2 * a))
            else:
                prohibidas = (5, 10) if n == 9 else (5, 7)
                if m:
                    s = {'V': 5, 'X': 10, 'S': 7}[m]
                    R.par(i, j, lambda a, b, s=s: a + b == s)
                else:
                    R.par(i, j, lambda a, b, p=prohibidas: a + b not in p)
    for par, sg in (nv.get('signos') or {}).items():
        i, j = map(int, par.split('-'))
        R.par(i, j, (lambda a, b: a < b) if sg == '<' else (lambda a, b: a > b))
    for t in nv.get('termos') or []:
        for a, b in zip(t, t[1:]):
            R.par(a, b, lambda p, q: p < q)
    for fl in nv.get('flechas') or []:
        R.varios(fl, lambda vals, c: (vals[0] == sum(vals[1:])) if all(vals) else True)
    if nv.get('sandwich'):
        lineas = [[f * n + c for c in range(n)] for f in range(n)] + [[f * n + c for f in range(n)] for c in range(n)]
        for li, s in zip(lineas, nv['sandwich']):
            def fn(vals, cands, s=s, n=n):
                if 1 in vals and n in vals:
                    a, b = sorted((vals.index(1), vals.index(n)))
                    if all(vals[a + 1:b]):
                        return sum(vals[a + 1:b]) == s
                return True
            R.varios(li, fn)
    for j in nv.get('jaulas') or []:
        R.grupo(j['c'])
        R.varios(j['c'], lambda vals, c, s=j['s']: (sum(vals) == s) if all(vals) else sum(vals) < s)
    return R


def verificar(var):
    with open(os.path.join(SALIDA, var + '.json'), encoding='utf-8') as f:
        niveles = json.load(f)
    malos = 0
    for k, nv in enumerate(niveles):
        R = reglas_de_nivel(var, nv)
        try:
            sols = resolver(R, [int(c) for c in nv['dados']], limite=2, tope=3000000)
        except TimeoutError:
            sols = None
        bien = sols is not None and len(sols) == 1 and ''.join(map(str, sols[0])) == nv['sol']
        if not bien:
            malos += 1
            print(f'  ✗ {var} nivel {k + 1}: {"tarda mucho" if sols is None else str(len(sols)) + " soluciones"}')
    return len(niveles), malos
