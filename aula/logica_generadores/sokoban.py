"""Empuja cajas (tipo Sokoban): cuartos al azar; las cajas se 'jalan' hacia atrás desde las metas
(así el nivel siempre tiene solución) y luego se resuelve con búsqueda en anchura para medir los empujes."""
import json, random, sys
from collections import deque
random.seed(int(sys.argv[1]) if len(sys.argv) > 1 else 4)
D4 = [(0, 1), (0, -1), (1, 0), (-1, 0)]
def cuarto(W, H):
    piso = set()
    for _ in range(random.randint(3, 5)):
        w, h = random.randint(2, 4), random.randint(2, 4)
        x, y = random.randint(1, W - w - 1), random.randint(1, H - h - 1)
        piso |= {(x + i, y + j) for i in range(w) for j in range(h)}
    # conexo
    ini = next(iter(piso)); vis = {ini}; q = [ini]
    while q:
        c = q.pop()
        for dx, dy in D4:
            n = (c[0] + dx, c[1] + dy)
            if n in piso and n not in vis: vis.add(n); q.append(n)
    return piso if len(vis) == len(piso) else None
def alcanzables(piso, cajas, p):
    vis = {p}; q = [p]
    while q:
        c = q.pop()
        for dx, dy in D4:
            n = (c[0] + dx, c[1] + dy)
            if n in piso and n not in cajas and n not in vis: vis.add(n); q.append(n)
    return vis
def jalar(piso, metas, pasos):
    cajas = set(metas)
    libres = [c for c in piso if c not in cajas]
    if not libres: return None
    p = random.choice(libres)
    for _ in range(pasos):
        reach = alcanzables(piso, cajas, p)
        ops = []
        for b in cajas:
            for dx, dy in D4:
                pp = (b[0] + dx, b[1] + dy); dest = (pp[0] + dx, pp[1] + dy)   # el jugador se para en pp y jala la caja hacia pp
                if pp in reach and dest in piso and dest not in cajas: ops.append((b, pp, dest))
        if not ops: break
        b, pp, dest = random.choice(ops)
        cajas = (cajas - {b}) | {pp}; p = dest
    return cajas, p
def resolver(piso, metas, cajas, p, limite=300000):
    """Mínimo número de empujes (BFS sobre empujes)."""
    metas = frozenset(metas)
    def norm(cajas, p):
        r = alcanzables(piso, cajas, p); return min(r)
    ini = (frozenset(cajas), norm(cajas, p)); vis = {ini: 0}; q = deque([(frozenset(cajas), p)])
    while q:
        cj, pj = q.popleft(); d = vis[(cj, norm(cj, pj))]
        if cj == metas: return d
        if len(vis) > limite: return None
        reach = alcanzables(piso, cj, pj)
        for b in cj:
            for dx, dy in D4:
                desde = (b[0] - dx, b[1] - dy); dest = (b[0] + dx, b[1] + dy)
                if desde in reach and dest in piso and dest not in cj:
                    nc = (cj - {b}) | {dest}
                    k = (nc, norm(nc, b))
                    if k not in vis: vis[k] = d + 1; q.append((nc, b))
    return -1
out = []
cubetas = {(2, 6): [], (7, 12): [], (13, 20): [], (21, 60): []}
import time
fin = time.time() + int(sys.argv[2]) if len(sys.argv) > 2 else time.time() + 200
while time.time() < fin:
    W, H = random.randint(7, 9), random.randint(6, 8)
    piso = cuarto(W, H)
    if not piso or len(piso) < 12: continue
    k = random.choice([1, 2, 2, 3, 3, 4])
    metas = random.sample(sorted(piso), k)
    r = jalar(piso, metas, random.randint(20, 80))
    if not r: continue
    cajas, p = r
    if cajas & set(metas) == set(metas): continue
    d = resolver(piso, metas, cajas, p)
    if not d or d < 2: continue
    filas = []
    for y in range(H):
        f = ''
        for x in range(W):
            c = (x, y)
            if c not in piso: f += '#'
            elif c == p: f += '+' if c in metas else '@'
            elif c in cajas: f += '*' if c in metas else '$'
            elif c in metas: f += '.'
            else: f += ' '
        filas.append(f)
    for (lo, hi), l in cubetas.items():
        if lo <= d <= hi and len(l) < 15: l.append((d, filas))
out = []
for (lo, hi), l in cubetas.items():
    print((lo, hi), len(l), file=sys.stderr); out += sorted(l)[:12 if hi < 60 else 12]
json.dump(out, open(sys.argv[3] if len(sys.argv) > 3 else 'sokoban.json', 'w'))
