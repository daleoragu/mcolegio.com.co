"""Conejos saltarines (tipo Jump In'): tablero 5x5 con 5 huecos (esquinas y centro). Los conejos saltan
en línea recta sobre una o más piezas seguidas (conejos, hongos o zorros) y caen en la primera casilla vacía;
los zorros (2 casillas) se deslizan a lo largo. Gana cuando todos los conejos están en huecos."""
import json, random, sys, time
from collections import deque
if __name__ != "__main__": pass
else: random.seed(int(sys.argv[1]))
N = 5; HUECOS = {(0, 0), (0, 4), (4, 0), (4, 4), (2, 2)}; D4 = [(0, 1), (0, -1), (1, 0), (-1, 0)]
def ocupadas(conejos, zorros, hongos):
    o = set(conejos) | set(hongos)
    for (f, c, h) in zorros: o |= {(f, c), (f, c + 1)} if h else {(f, c), (f + 1, c)}
    return o
def jugadas(e, hongos):
    conejos, zorros = e; o = ocupadas(conejos, zorros, hongos); res = []
    for i, (f, c) in enumerate(conejos):
        for df, dc in D4:
            k = 1
            while 0 <= f + df * k < N and 0 <= c + dc * k < N and (f + df * k, c + dc * k) in o: k += 1
            if k > 1 and 0 <= f + df * k < N and 0 <= c + dc * k < N:
                nc = list(conejos); nc[i] = (f + df * k, c + dc * k); res.append((tuple(sorted(nc)), zorros))
    for i, (f, c, h) in enumerate(zorros):
        mias = {(f, c), (f, c + 1)} if h else {(f, c), (f + 1, c)}; otras = o - mias
        for s in (1, -1):
            k = 1
            while True:
                nf, ncol = (f, c + s * k) if h else (f + s * k, c)
                celdas = {(nf, ncol), (nf, ncol + 1)} if h else {(nf, ncol), (nf + 1, ncol)}
                if any(not (0 <= a < N and 0 <= b < N) for a, b in celdas) or celdas & otras: break
                nz = list(zorros); nz[i] = (nf, ncol, h); res.append((conejos, tuple(nz))); k += 1
    return res
def bfs(conejos, zorros, hongos):
    ini = (tuple(sorted(conejos)), tuple(zorros)); vis = {ini: 0}; q = deque([ini])
    while q:
        e = q.popleft()
        if all(c in HUECOS for c in e[0]): return vis[e]
        if len(vis) > 200000: return None
        for n in jugadas(e, hongos):
            if n not in vis: vis[n] = vis[e] + 1; q.append(n)
    return None
if __name__ == "__main__":
    cub = {(2, 4): [], (5, 7): [], (8, 11): [], (12, 40): []}
    fin = time.time() + int(sys.argv[2])
    celdas = [(f, c) for f in range(N) for c in range(N)]
    while time.time() < fin:
        nc, nz, nh = random.choice([1, 2, 2, 3, 3]), random.choice([0, 1, 1, 2]), random.choice([1, 2, 2, 3])
        libres = set(celdas); zorros = []
        ok = True
        for _ in range(nz):
            h = random.random() < .5; ops = [(f, c, h) for f, c in libres if ((f, c + 1) if h else (f + 1, c)) in libres]
            if not ops: ok = False; break
            z = random.choice(ops); zorros.append(z); libres -= {(z[0], z[1]), (z[0], z[1] + 1) if h else (z[0] + 1, z[1])}
        if not ok: continue
        hongos = random.sample(sorted(libres - HUECOS), nh); libres -= set(hongos)
        conejos = random.sample(sorted(libres - HUECOS), nc)
        d = bfs(conejos, zorros, hongos)
        if not d: continue
        for (lo, hi), l in cub.items():
            if lo <= d <= hi and len(l) < 12: l.append({'minimo': d, 'conejos': conejos, 'zorros': zorros, 'hongos': hongos})
    out = []
    for k, l in cub.items(): print(k, len(l), file=sys.stderr); out += sorted(l, key=lambda r: r['minimo'])[:10]
    json.dump(out, open(sys.argv[3], 'w'))
