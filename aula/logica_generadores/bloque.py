"""Bloque rodante (tipo Bloxorz): un bloque de 1×1×2 rueda por baldosas; gana parado sobre el hueco.
Tableros al azar (rectángulos unidos) resueltos con búsqueda en anchura."""
import json, random, sys, time
from collections import deque
random.seed(int(sys.argv[1]))
def celdas(x, y, o):          # o: 0 parado, 1 acostado en x (x, x+1), 2 acostado en y (y, y+1)
    return [(x, y)] if o == 0 else [(x, y), (x + 1, y)] if o == 1 else [(x, y), (x, y + 1)]
def mover(x, y, o, d):
    if o == 0: return {'d': (x + 1, y, 1), 'i': (x - 2, y, 1), 'b': (x, y + 1, 2), 'a': (x, y - 2, 2)}[d]
    if o == 1: return {'d': (x + 2, y, 0), 'i': (x - 1, y, 0), 'b': (x, y + 1, 1), 'a': (x, y - 1, 1)}[d]
    return {'d': (x + 1, y, 2), 'i': (x - 1, y, 2), 'b': (x, y + 2, 0), 'a': (x, y - 1, 0)}[d]
def resolver(tiles, ini, meta):
    q = deque([(ini, 0, 0)]); vis = {(ini[0], ini[1], 0)}
    while q:
        (x, y), o, d = q.popleft()[0], q[0][1] if False else None, None
    return None
def bfs(tiles, ini, meta):
    s0 = (ini[0], ini[1], 0); vis = {s0: 0}; q = deque([s0])
    while q:
        s = q.popleft()
        if s[2] == 0 and (s[0], s[1]) == meta: return vis[s]
        for d in 'dibа'.replace('а', 'a'):
            n = mover(*s, d)
            if all(c in tiles for c in celdas(*n)) and n not in vis: vis[n] = vis[s] + 1; q.append(n)
    return None
cub = {(5, 10): [], (11, 17): [], (18, 26): [], (27, 80): []}
fin = time.time() + int(sys.argv[2])
while time.time() < fin:
    W, H = 12, 8
    tiles = set()
    for _ in range(random.randint(4, 8)):
        w, h = random.randint(2, 5), random.randint(2, 4)
        x, y = random.randint(0, W - w), random.randint(0, H - h)
        tiles |= {(x + i, y + j) for i in range(w) for j in range(h)}
    lista = sorted(tiles)
    ini, meta = random.choice(lista), random.choice(lista)
    if abs(ini[0] - meta[0]) + abs(ini[1] - meta[1]) < 5: continue
    d = bfs(tiles, ini, meta)
    if not d: continue
    # quitar baldosas que sobran sin cambiar la dificultad (tableros más limpios y retadores)
    for c in random.sample(lista, len(lista)):
        if c in (ini, meta): continue
        t2 = tiles - {c}; d2 = bfs(t2, ini, meta)
        if d2 and d2 >= d: tiles, d = t2, d2
    for (lo, hi), l in cub.items():
        if lo <= d <= hi and len(l) < 12:
            filas = [''.join('S' if (x, y) == ini else 'G' if (x, y) == meta else '#' if (x, y) in tiles else '.' for x in range(W)) for y in range(H)]
            l.append((d, filas))
out = []
for k, l in cub.items(): print(k, len(l), file=sys.stderr); out += sorted(l)[:9]
json.dump(out, open(sys.argv[3], 'w'))
