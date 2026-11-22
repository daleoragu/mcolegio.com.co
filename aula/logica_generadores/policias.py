"""Policías y ladrón: genera los retos de los dos modos y los verifica resolviendo el juego por completo.

Un reto es un mapa (puntos unidos por caminos) con policías y un ladrón que juegan por turnos:
  · en su turno el ladrón pasa a un punto vecino libre; si no tiene a dónde ir, queda acorralado y ganan los policías;
  · en su turno UN policía pasa a un punto vecino libre (en el tablero de ajedrez, solo hacia adelante en diagonal);
  · si el ladrón llega a una salida, se escapa y gana. Si los policías no tienen ninguna jugada, también gana el ladrón.
Modo «tablero»: casillas oscuras de un tablero de ajedrez; el ladrón va en diagonal en las cuatro direcciones, los
policías solo hacia adelante (hacia abajo); las salidas son la fila de arriba (de donde salieron los policías).
Modo «mapa»: un mapa de caminos con algunas salidas en el borde.

Cada posición se resuelve con análisis retrógrado (quién gana jugando perfecto y en cuántas jugadas). Un reto de
POLICÍA tiene que ser ganable por los policías; uno de LADRÓN, ganable por el ladrón. Se ordenan por dificultad.

    python3 policias.py           escribe los cuatro archivos de niveles
"""
import itertools
import json
import os
import random
import sys
from collections import deque

POLICIA, LADRON, NADIE = 1, 2, 0


class Juego:
    def __init__(self, n, ady_l, ady_p, salidas):
        self.n, self.ady_l, self.ady_p, self.salidas = n, ady_l, ady_p, set(salidas)

    def jugadas(self, estado):
        """Estados siguientes. estado = (ladron, policias ordenados, turno)."""
        l, ps, t = estado
        ocup = set(ps)
        if t == LADRON:
            return [(v, ps, POLICIA) for v in self.ady_l[l] if v not in ocup]
        out = []
        for i, p in enumerate(ps):
            for v in self.ady_p[p]:
                if v not in ocup and v != l:
                    nuevo = tuple(sorted(ps[:i] + (v,) + ps[i + 1:]))
                    out.append((l, nuevo, LADRON))
        return out

    def resolver(self, inicio, tope=2_000_000):
        """Análisis retrógrado desde el inicio: {estado: (ganador, jugadas que faltan)}; None si es muy grande."""
        estados, pend = {inicio: None}, deque([inicio])
        hijos = {}
        while pend:
            s = pend.popleft()
            if s[0] in self.salidas:
                hijos[s] = []
                continue
            h = self.jugadas(s)
            hijos[s] = h
            for x in h:
                if x not in estados:
                    estados[x] = None
                    pend.append(x)
                    if len(estados) > tope:
                        return None
        padres = {s: [] for s in estados}
        for s, h in hijos.items():
            for x in h:
                padres[x].append(s)
        res, cuenta, cola = {}, {}, deque()
        for s, h in hijos.items():
            cuenta[s] = len(h)
            if s[0] in self.salidas:
                res[s] = (LADRON, 0)
                cola.append(s)
            elif not h:
                res[s] = (POLICIA, 0) if s[2] == LADRON else (LADRON, 0)
                cola.append(s)
        while cola:
            x = cola.popleft()
            g, d = res[x]
            for s in padres[x]:
                if s in res:
                    continue
                mueve = s[2]
                mueve_quien = POLICIA if mueve == POLICIA else LADRON
                if g == mueve_quien:
                    res[s] = (g, d + 1)
                    cola.append(s)
                else:
                    cuenta[s] -= 1
                    if cuenta[s] == 0:
                        # todas sus jugadas pierden: la más larga
                        res[s] = (g, 1 + max(res[y][1] for y in hijos[s]))
                        cola.append(s)
        return res, hijos

    def medir(self, inicio, rol, res, hijos):
        """Dificultad para quien juega el rol: jugadas propias mínimas y qué tan escasas son las buenas."""
        lado = POLICIA if rol == 'policia' else LADRON
        s, propias, decisiones, escasez = inicio, 0, 0, 0.0
        while s in res and res[s][1] > 0:
            h = hijos[s]
            if s[2] == lado:
                buenas = [x for x in h if res.get(x, (NADIE, 0))[0] == lado]
                if not buenas:
                    return None
                propias += 1
                if len(h) > 1:
                    decisiones += 1
                    escasez += 1 - len(buenas) / len(h)
                s = min(buenas, key=lambda x: res[x][1])
            else:
                s = max(h, key=lambda x: (res[x][0] != lado, res[x][1]))
        return {'jugadas': propias, 'decisiones': decisiones, 'escasez': round(escasez, 2)}


# ---------------------------------------------------------------------------------------------- tablero de ajedrez
def tablero(N):
    """Casillas oscuras: nodos (fila, col); ladrón en las 4 diagonales, policías solo hacia abajo."""
    casillas = [(f, c) for f in range(N) for c in range(N) if (f + c) % 2 == 1]
    idx = {p: i for i, p in enumerate(casillas)}
    ady_l, ady_p = [], []
    for f, c in casillas:
        ady_l.append([idx[(f + a, c + b)] for a in (-1, 1) for b in (-1, 1) if (f + a, c + b) in idx])
        ady_p.append([idx[(f + 1, c + b)] for b in (-1, 1) if (f + 1, c + b) in idx])
    salidas = [idx[p] for p in casillas if p[0] == 0]
    return casillas, ady_l, ady_p, salidas


def retos_tablero(r, N, n_pol, rol, cuantos, intentos=1500, tope=120_000):
    casillas, ady_l, ady_p, salidas = tablero(N)
    j = Juego(len(casillas), ady_l, ady_p, salidas)
    filas = {}
    for i, (f, c) in enumerate(casillas):
        filas.setdefault(f, []).append(i)
    vistos, salida = set(), []
    for _ in range(intentos):
        if len(salida) >= cuantos * 3:
            break
        # una franja de dos filas con los policías y el ladrón más abajo (posiciones de mitad de partida)
        b = r.randint(0, N - 4)
        candidatos = [i for f in (b, b + 1) for i in filas.get(f, [])]
        if len(candidatos) < n_pol:
            continue
        ps = tuple(sorted(r.sample(candidatos, n_pol)))
        abajo = [i for f in range(b + 2, min(N, b + 5)) for i in filas.get(f, []) if i not in ps]
        if not abajo:
            continue
        l = r.choice(abajo)
        turno = r.choice([LADRON, POLICIA])
        inicio = (l, ps, turno)
        if inicio in vistos:
            continue
        vistos.add(inicio)
        sol = j.resolver(inicio, tope)
        if sol is None:
            continue
        res, hijos = sol
        lado = POLICIA if rol == 'policia' else LADRON
        if res.get(inicio, (NADIE, 0))[0] != lado:
            continue
        m = j.medir(inicio, rol, res, hijos)
        if not m or m['jugadas'] < 2 or m['decisiones'] < 1 or m['escasez'] < .3:
            continue
        salida.append({'tipo': 'tablero', 'N': N, 'nodos': [list(p) for p in casillas], 'adyL': ady_l, 'adyP': ady_p,
                       'salidas': salidas, 'policias': list(ps), 'ladron': l, 'turno': 'ladron' if turno == LADRON else 'policia',
                       'rol': rol, 'estados': len(res), **m})
    salida.sort(key=lambda x: (x['jugadas'] * (1 + x['escasez']), x['decisiones']))
    if len(salida) > cuantos:
        paso = len(salida) / cuantos
        salida = [salida[int(k * paso)] for k in range(cuantos)]
    return salida


# ---------------------------------------------------------------------------------------------- mapas de caminos
def mapa(r, filas, cols, quitar):
    """Puntos en una cuadrícula unidos con sus vecinos (y una diagonal por cuadro, sin cruces)."""
    nodos = [(f, c) for f in range(filas) for c in range(cols)]
    idx = {p: i for i, p in enumerate(nodos)}
    aristas = set()
    for f in range(filas):
        for c in range(cols):
            if c + 1 < cols:
                aristas.add((idx[(f, c)], idx[(f, c + 1)]))
            if f + 1 < filas:
                aristas.add((idx[(f, c)], idx[(f + 1, c)]))
            if f + 1 < filas and c + 1 < cols and r.random() < .55:
                if r.random() < .5:
                    aristas.add((idx[(f, c)], idx[(f + 1, c + 1)]))
                else:
                    aristas.add((idx[(f, c + 1)], idx[(f + 1, c)]))
    aristas = sorted(aristas)
    r.shuffle(aristas)
    # quitar caminos sin desconectar ni dejar puntos con un solo camino
    for a, b in list(aristas):
        if quitar <= 0:
            break
        prueba = [x for x in aristas if x != (a, b)]
        grado = [0] * len(nodos)
        for x, y in prueba:
            grado[x] += 1
            grado[y] += 1
        if min(grado) < 2 or not conexo(len(nodos), prueba):
            continue
        aristas = prueba
        quitar -= 1
    ady = [[] for _ in nodos]
    for a, b in aristas:
        ady[a].append(b)
        ady[b].append(a)
    return nodos, sorted(tuple(sorted(x)) for x in aristas), ady


def conexo(n, aristas):
    ady = [[] for _ in range(n)]
    for a, b in aristas:
        ady[a].append(b)
        ady[b].append(a)
    vis, pila = {0}, [0]
    while pila:
        u = pila.pop()
        for v in ady[u]:
            if v not in vis:
                vis.add(v)
                pila.append(v)
    return len(vis) == n


def retos_mapa(r, rol, cuantos, tam, n_pol, n_sal, intentos=6000, min_jugadas=2):
    salida, vistos = [], set()
    for _ in range(intentos):
        if len(salida) >= cuantos * 3:
            break
        filas, cols = r.choice(tam)
        nodos, aristas, ady = mapa(r, filas, cols, r.randint(1, filas * cols // 3))
        borde = [i for i, (f, c) in enumerate(nodos) if f in (0, filas - 1) or c in (0, cols - 1)]
        k = r.choice(n_sal)
        sal = sorted(r.sample(borde, k)) if k else []
        libres = [i for i in range(len(nodos)) if i not in sal]
        npol = r.choice(n_pol)
        if len(libres) < npol + 2:
            continue
        ps = tuple(sorted(r.sample(libres, npol)))
        l = r.choice([i for i in libres if i not in ps])
        turno = LADRON if rol == 'policia' else r.choice([LADRON, POLICIA])
        if rol == 'policia':
            turno = r.choice([LADRON, POLICIA])
        clave = (tuple(aristas), ps, l, tuple(sal), turno)
        if clave in vistos:
            continue
        vistos.add(clave)
        j = Juego(len(nodos), ady, ady, sal)
        inicio = (l, ps, turno)
        sol = j.resolver(inicio)
        if sol is None:
            continue
        res, hijos = sol
        lado = POLICIA if rol == 'policia' else LADRON
        if res.get(inicio, (NADIE, 0))[0] != lado:
            continue
        m = j.medir(inicio, rol, res, hijos)
        if not m or m['jugadas'] < min_jugadas or m['decisiones'] < 1 or m['escasez'] < .25:
            continue
        salida.append({'tipo': 'mapa', 'filas': filas, 'cols': cols, 'nodos': [list(p) for p in nodos], 'aristas': [list(a) for a in aristas],
                       'adyL': ady, 'adyP': ady, 'salidas': sal, 'policias': list(ps), 'ladron': l,
                       'turno': 'ladron' if turno == LADRON else 'policia', 'rol': rol, 'estados': len(res), **m})
    salida.sort(key=lambda x: (x['jugadas'] * (1 + x['escasez']), x['decisiones']))
    if len(salida) > cuantos:
        paso = len(salida) / cuantos
        salida = [salida[int(k * paso)] for k in range(cuantos)]
    return salida


def main(destino):
    r = random.Random(11)
    archivos = {
        'policias': retos_mapa(r, 'policia', 30, [(3, 3), (3, 4), (4, 4), (4, 5)], [2, 2, 3], [0, 1, 1, 2]),
        'policias_fuga': retos_mapa(r, 'ladron', 25, [(4, 4), (4, 5), (5, 5)], [3, 3, 4], [1, 2], intentos=20000, min_jugadas=3),
        'policias_tablero': retos_tablero(r, 6, 3, 'policia', 10) + retos_tablero(r, 8, 4, 'policia', 15),
        'policias_tablero_fuga': retos_tablero(r, 6, 3, 'ladron', 10) + retos_tablero(r, 8, 4, 'ladron', 15),
    }
    for nombre, lista in archivos.items():
        with open(os.path.join(destino, nombre + '.json'), 'w', encoding='utf-8') as f:
            json.dump(lista, f, ensure_ascii=False, separators=(',', ':'))
        print(nombre, len(lista), 'retos · estados máx.', max((x['estados'] for x in lista), default=0), file=sys.stderr)


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'medir':
        casillas, al, ap, sal = tablero(8)
        j = Juego(len(casillas), al, ap, sal)
        ps = tuple(sorted(i for i, p in enumerate(casillas) if p[0] == 0))
        l = next(i for i, p in enumerate(casillas) if p == (7, 2))
        sol = j.resolver((l, ps, LADRON))
        print('estados 8x8 clásico:', len(sol[0]), 'ganador', sol[0][(l, ps, LADRON)])
    else:
        main(sys.argv[1] if len(sys.argv) > 1 else '../static/aula/logica/niveles')
