"""Atrapa al ladrón (bloqueo de calles): genera los retos y los verifica con un solucionador.

Tablero: un barrio de N×N con edificios (E), calles (.) y túneles (T). El carro del ladrón está en una calle y
quiere salir por cualquier borde (una calle o un túnel del borde es una salida). El jugador tiene unas piezas de
calle de 2 a 4 cuadros, cada una con una patrulla, y debe ponerlas TODAS sobre las calles (no sobre edificios,
túneles ni el ladrón) para que el ladrón ya no pueda llegar a ningún borde. Por los túneles pasa el ladrón,
pero no se puede poner nada encima.

Cada reto se arma alrededor de una solución (cerco alrededor del ladrón), se rellena de edificios y túneles para
que queden pocas maneras, y el solucionador cuenta las soluciones: se guardan los que tienen 1 o 2.

    python3 bloqueo.py 40 > ../static/aula/logica/niveles/ladron.json
"""
import json
import random
import sys

FORMAS = {
    'I2': [(0, 0), (0, 1)],
    'I3': [(0, 0), (0, 1), (0, 2)],
    'L3': [(0, 0), (1, 0), (1, 1)],
    'I4': [(0, 0), (0, 1), (0, 2), (0, 3)],
    'L4': [(0, 0), (1, 0), (2, 0), (2, 1)],
    'T4': [(0, 0), (0, 1), (0, 2), (1, 1)],
    'S4': [(0, 1), (0, 2), (1, 0), (1, 1)],
    'O4': [(0, 0), (0, 1), (1, 0), (1, 1)],
}
V4 = [(0, 1), (0, -1), (1, 0), (-1, 0)]


def orientaciones(celdas):
    vistas, salida = set(), []
    actual = list(celdas)
    for voltear in (False, True):
        c = [(f, -k) for f, k in actual] if voltear else list(actual)
        for _ in range(4):
            c = [(k, -f) for f, k in c]
            mf, mc = min(f for f, _ in c), min(k for _, k in c)
            norm = tuple(sorted((f - mf, k - mc) for f, k in c))
            if norm not in vistas:
                vistas.add(norm)
                salida.append(norm)
    return salida


ORIENT = {k: orientaciones(v) for k, v in FORMAS.items()}


class Tablero:
    def __init__(self, N, mapa, ladron):
        self.N, self.mapa, self.ladron = N, mapa, ladron
        self.calle = [[mapa[f][c] != 'E' for c in range(N)] for f in range(N)]
        self.libre = [[mapa[f][c] == '.' and (f, c) != ladron for c in range(N)] for f in range(N)]

    def borde(self, f, c):
        return f == 0 or c == 0 or f == self.N - 1 or c == self.N - 1

    def escapa(self, ocupado):
        N, (f0, c0) = self.N, self.ladron
        vis, pila = {(f0, c0)}, [(f0, c0)]
        while pila:
            f, c = pila.pop()
            if self.borde(f, c):
                return True
            for df, dc in V4:
                F, C = f + df, c + dc
                if 0 <= F < N and 0 <= C < N and self.calle[F][C] and (F, C) not in vis and (F * N + C) not in ocupado:
                    vis.add((F, C))
                    pila.append((F, C))
        return False

    def corte_minimo(self, ocupado, tope):
        """Cuántos cuadros (donde aún se puede poner algo) hay que tapar, como mínimo, para encerrarlo.
        Devuelve tope + 1 si es más que el tope (o imposible: un camino solo por túneles)."""
        N = self.N
        INF = 10 ** 6
        # red con nodos partidos (entrada 2i, salida 2i+1); fuente = salida del ladrón; sumidero = S
        S = 2 * N * N
        cap = {}

        def arco(a, b, k):
            cap[(a, b)] = cap.get((a, b), 0) + k
            cap.setdefault((b, a), 0)
        ady = {}
        for f in range(N):
            for c in range(N):
                if not self.calle[f][c] or (f * N + c) in ocupado:
                    continue
                i = f * N + c
                k = 1 if self.libre[f][c] else INF
                if (f, c) == self.ladron:
                    k = INF
                arco(2 * i, 2 * i + 1, k)
                if self.borde(f, c):
                    arco(2 * i + 1, S, INF)
                for df, dc in V4:
                    F, C = f + df, c + dc
                    if 0 <= F < N and 0 <= C < N and self.calle[F][C] and (F * N + C) not in ocupado:
                        arco(2 * i + 1, 2 * (F * N + C), INF)
        for (a, b) in cap:
            ady.setdefault(a, []).append(b)
        fuente = 2 * (self.ladron[0] * N + self.ladron[1]) + 1
        flujo = 0
        while flujo <= tope:
            padre = {fuente: None}
            cola = [fuente]
            while cola and S not in padre:
                u = cola.pop(0)
                for v in ady.get(u, ()):
                    if v not in padre and cap[(u, v)] > 0:
                        padre[v] = u
                        cola.append(v)
            if S not in padre:
                return flujo
            v, menor = S, INF
            while padre[v] is not None:
                menor = min(menor, cap[(padre[v], v)])
                v = padre[v]
            if menor >= INF:
                return tope + 1
            v = S
            while padre[v] is not None:
                u = padre[v]
                cap[(u, v)] -= menor
                cap[(v, u)] += menor
                v = u
            flujo += menor
        return flujo


def colocaciones(tab, forma):
    N, out = tab.N, set()
    for o in ORIENT[forma]:
        for f in range(N):
            for c in range(N):
                cel = [(f + a, c + b) for a, b in o]
                if all(0 <= F < N and 0 <= C < N and tab.libre[F][C] for F, C in cel):
                    out.add(frozenset(F * N + C for F, C in cel))
    return sorted(out, key=lambda s: sorted(s))


def resolver(tab, formas, tope=3):
    """Cuenta las soluciones (hasta el tope) y cuántos nodos costó; devuelve también la primera."""
    orden = sorted(range(len(formas)), key=lambda k: -len(FORMAS[formas[k]]))
    lugares = {k: colocaciones(tab, formas[k]) for k in orden}
    sols, nodos = [], [0]
    elegido = {}

    def rec(j, ocupado, desde):
        if len(sols) >= tope:
            return
        nodos[0] += 1
        if j == len(orden):
            if not tab.escapa(ocupado):
                sols.append(dict(elegido))
            return
        area = sum(len(FORMAS[formas[k]]) for k in orden[j:])
        if tab.corte_minimo(ocupado, area) > area:
            return
        k = orden[j]
        mismo = j > 0 and formas[orden[j - 1]] == formas[k]
        lista = lugares[k]
        for n in range(desde if mismo else 0, len(lista)):
            pz = lista[n]
            if pz & ocupado:
                continue
            elegido[k] = pz
            siguiente_mismo = j + 1 < len(orden) and formas[orden[j + 1]] == formas[k]
            rec(j + 1, ocupado | pz, n + 1 if siguiente_mismo else 0)
            del elegido[k]
    rec(0, frozenset(), 0)
    return sols, nodos[0]


def generar(r, N, n_piezas, formas_ok, densidad, tuneles):
    """Un reto armado alrededor de una solución."""
    for _ in range(200):
        # zona del ladrón (no toca el borde)
        ladron = (r.randint(1, N - 2), r.randint(1, N - 2))
        zona = {ladron}
        meta = r.randint(1, 4 if N >= 6 else 2)
        while len(zona) < meta:
            f, c = r.choice(sorted(zona))
            df, dc = r.choice(V4)
            if 1 <= f + df <= N - 2 and 1 <= c + dc <= N - 2:
                zona.add((f + df, c + dc))
        muro = {(f + df, c + dc) for f, c in zona for df, dc in V4} - zona
        edificios = {m for m in muro if r.random() < 0.35}
        porTapar = set(muro) - edificios
        piezas, usados = [], set()
        ok = True
        while porTapar and ok:
            objetivo = r.choice(sorted(porTapar))
            mejor = None
            for _ in range(120):
                forma = r.choice(formas_ok)
                o = r.choice(ORIENT[forma])
                a, b = r.choice(o)
                cel = [(objetivo[0] + x - a, objetivo[1] + y - b) for x, y in o]
                if not all(0 <= F < N and 0 <= C < N for F, C in cel):
                    continue
                if any((F, C) in zona or (F, C) in edificios or (F, C) in usados for F, C in cel):
                    continue
                tapa = len(set(cel) & porTapar)
                if mejor is None or tapa > mejor[0]:
                    mejor = (tapa, forma, cel)
            if mejor is None:
                ok = False
                break
            _, forma, cel = mejor
            piezas.append((forma, cel))
            usados |= set(cel)
            porTapar -= set(cel)
        if not ok or not (n_piezas[0] <= len(piezas) <= n_piezas[1]):
            continue
        # el resto del barrio: edificios al azar; túneles en calles que no usa la solución
        mapa = [['.'] * N for _ in range(N)]
        for f in range(N):
            for c in range(N):
                p = (f, c)
                if p in edificios or (p not in zona and p not in usados and p not in muro and r.random() < densidad):
                    mapa[f][c] = 'E'
        libres = [(f, c) for f in range(N) for c in range(N)
                  if mapa[f][c] == '.' and (f, c) not in usados and (f, c) not in zona and (f, c) not in muro]
        r.shuffle(libres)
        for p in libres[:tuneles]:
            mapa[p[0]][p[1]] = 'T'
        tab = Tablero(N, [''.join(fila) for fila in mapa], ladron)
        formas = [fm for fm, _ in piezas]
        if not tab.escapa(frozenset()):
            continue              # sin piezas ya estaría encerrado: no sirve
        sols, nodos = resolver(tab, formas)
        if not sols or len(sols) > 2:
            continue
        sol = sols[0]
        sol_lista = []
        for k, fm in enumerate(formas):
            celdas = sorted(sol[k])
            sol_lista.append([[i // N, i % N] for i in celdas])
        pieza_json = []
        for k, fm in enumerate(formas):
            celdas = FORMAS[fm]
            poli = r.randrange(len(celdas))
            pieza_json.append([[a, b, 'p' if n == poli else 'c'] for n, (a, b) in enumerate(celdas)])
        return {'N': N, 'mapa': tab.mapa, 'ladron': list(ladron), 'piezas': pieza_json, 'formas': formas,
                'sol': sol_lista, 'soluciones': len(sols), 'nodos': nodos, 'tuneles': sum(fila.count('T') for fila in tab.mapa)}
    return None


ETAPAS = [
    # (cuántos, N, (mín, máx piezas), formas, densidad de edificios, túneles)
    (8, 5, (2, 2), ['I2', 'I3', 'L3'], .45, 0),
    (8, 5, (2, 3), ['I2', 'I3', 'L3', 'I4', 'L4'], .35, 1),
    (8, 6, (3, 3), ['I3', 'L3', 'I4', 'L4', 'T4'], .35, 1),
    (8, 6, (3, 4), ['L3', 'I4', 'L4', 'T4', 'S4', 'O4'], .3, 2),
    (8, 7, (4, 5), ['L3', 'I4', 'L4', 'T4', 'S4', 'O4'], .3, 3),
]


def main(total=40, semilla=7):
    r = random.Random(semilla)
    niveles = []
    por_etapa = max(1, total // len(ETAPAS))
    for cuantos, N, npz, formas, dens, tun in ETAPAS:
        lote = []
        intentos = 0
        while len(lote) < por_etapa and intentos < 4000:
            intentos += 1
            g = generar(r, N, npz, formas, dens, tun)
            if g and all(g['mapa'] != x['mapa'] for x in lote):
                lote.append(g)
        lote.sort(key=lambda g: (g['nodos'], -g['soluciones']))
        niveles.extend(lote)
        print(f'N={N}: {len(lote)} retos en {intentos} intentos', file=sys.stderr)
    return niveles


if __name__ == '__main__':
    total = int(sys.argv[1]) if len(sys.argv) > 1 else 40
    print(json.dumps(main(total), ensure_ascii=False, separators=(',', ':')))
