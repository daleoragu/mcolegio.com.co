"""Genera niveles de «trancón» (6x6) y de «safari» (7x7 con hipopótamo 2x2 que se mueve en 4 direcciones).
Cada nivel se resuelve con BFS (un movimiento = mover una pieza cualquier distancia). Salida JSON."""
import json, random, sys, time
from collections import deque

def resolver(N, piezas, salida_fila, limite=400000):
    # piezas: lista de (fila, col, alto, ancho, tipo) tipo: 'h','v','4' (se mueve en 4 dir), 'fija'
    # la 0 es el carro rojo (horizontal), sale por la derecha en salida_fila
    fijas = [p for p in piezas if p[4] == 'fija']
    movil = [p for p in piezas if p[4] != 'fija']
    dims = [(p[2], p[3], p[4]) for p in movil]
    inicio = tuple((p[0], p[1]) for p in movil)
    base = [[False] * N for _ in range(N)]
    for f, c, a, w, _ in fijas:
        for i in range(a):
            for j in range(w):
                base[f + i][c + j] = True
    def ocupado(estado):
        g = [fila[:] for fila in base]
        for (f, c), (a, w, _) in zip(estado, dims):
            for i in range(a):
                for j in range(w):
                    g[f + i][c + j] = True
        return g
    visto = {inicio: 0}
    cola = deque([inicio])
    while cola:
        e = cola.popleft()
        d = visto[e]
        if e[0][1] + dims[0][1] == N:  # el rojo llegó al borde derecho
            return d
        if len(visto) > limite:
            return None
        g = ocupado(e)
        for k, ((f, c), (a, w, t)) in enumerate(zip(e, dims)):
            dirs = []
            if t in ('h', '4'): dirs += [(0, 1), (0, -1)]
            if t in ('v', '4'): dirs += [(1, 0), (-1, 0)]
            for df, dc in dirs:
                # quitar la pieza de la grilla
                for i in range(a):
                    for j in range(w):
                        g[f + i][c + j] = False
                nf, nc = f, c
                while True:
                    nf, nc = nf + df, nc + dc
                    if nf < 0 or nc < 0 or nf + a > N or nc + w > N: break
                    if any(g[nf + i][nc + j] for i in range(a) for j in range(w)): break
                    ne = e[:k] + ((nf, nc),) + e[k + 1:]
                    if ne not in visto:
                        visto[ne] = d + 1
                        cola.append(ne)
                for i in range(a):
                    for j in range(w):
                        g[f + i][c + j] = True
    return -1

def aleatorio(N, fila_rojo, safari):
    g = [['.'] * N for _ in range(N)]
    piezas = []
    def libre(f, c, a, w):
        return f + a <= N and c + w <= N and all(g[f + i][c + j] == '.' for i in range(a) for j in range(w))
    def poner(f, c, a, w, t, letra):
        for i in range(a):
            for j in range(w):
                g[f + i][c + j] = letra
        piezas.append((f, c, a, w, t))
    c0 = random.randint(0, N - 4)
    poner(fila_rojo, c0, 1, 2, 'h', 'x')
    letras = 'abcdefghijklmnopqrstuvw'
    if safari:
        for _ in range(50):
            f, c = random.randint(0, N - 2), random.randint(0, N - 2)
            if libre(f, c, 2, 2) and f not in (fila_rojo - 1, fila_rojo):
                poner(f, c, 2, 2, '4', 'H'); break
        for _ in range(random.randint(0, 2)):
            for _ in range(30):
                f, c = random.randint(0, N - 1), random.randint(0, N - 1)
                if libre(f, c, 1, 1) and f != fila_rojo:
                    poner(f, c, 1, 1, 'fija', '#'); break
    n = random.randint(8, 13) if not safari else random.randint(10, 17)
    k = 0
    for _ in range(300):
        if k >= n: break
        largo = 3 if random.random() < .3 else 2
        if random.random() < .5:
            a, w, t = 1, largo, 'h'
        else:
            a, w, t = largo, 1, 'v'
        f, c = random.randint(0, N - 1), random.randint(0, N - 1)
        if t == 'h' and f == fila_rojo: continue
        if libre(f, c, a, w):
            poner(f, c, a, w, t, letras[k]); k += 1
    return piezas, [''.join(r) for r in g]

def generar(N, fila, safari, segundos, cubetas):
    mejores = {b: [] for b in cubetas}
    fin = time.time() + segundos
    vistos = set()
    while time.time() < fin:
        piezas, g = aleatorio(N, fila, safari)
        d = resolver(N, piezas, fila)
        if not d or d < 2: continue
        clave = '/'.join(g)
        if clave in vistos: continue
        vistos.add(clave)
        for (lo, hi) in cubetas:
            if lo <= d <= hi and len(mejores[(lo, hi)]) < 60:
                mejores[(lo, hi)].append((d, g))
    return mejores

if __name__ == '__main__':
    modo = sys.argv[1]
    random.seed(int(sys.argv[3]) if len(sys.argv) > 3 else (7 if modo == 'trancon' else 11))
    if modo == 'trancon':
        cub = [(3, 5), (6, 9), (10, 14), (15, 20), (21, 60)]
        m = generar(6, 2, False, int(sys.argv[2]), cub)
    else:
        cub = [(3, 6), (7, 11), (12, 17), (18, 25), (26, 80)]
        m = generar(7, 3, True, int(sys.argv[2]), cub)
    for b, l in m.items():
        print(b, len(l), max([d for d, _ in l], default=0), file=sys.stderr)
    json.dump({f'{a}-{b}': sorted(l) for (a, b), l in m.items()}, open(f'{modo}{sys.argv[3] if len(sys.argv) > 3 else ""}.json', 'w'))
