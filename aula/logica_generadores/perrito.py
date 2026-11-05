"""Perrito a su casita: rompecabezas deslizante de 4x4 con un espacio. Las fichas tienen caminos;
hay que deslizarlas hasta que cada perrito (afuera del tablero) llegue a su casita por el camino."""
import json, random, sys, time
from collections import deque
if __name__ != "__main__": pass
else: random.seed(int(sys.argv[1]))
N = 4; NB, EB, SB, WB = 1, 2, 4, 8
DIRS = {NB: (-1, 0, SB), EB: (0, 1, WB), SB: (1, 0, NB), WB: (0, -1, EB)}
def entrada(lado, k):       # celda del borde y la abertura que debe tener hacia afuera
    return {'arriba': ((0, k), NB), 'abajo': ((N - 1, k), SB), 'izq': ((k, 0), WB), 'der': ((k, N - 1), EB)}[lado]
def conectados(t, perros):
    for (pl, pk), (cl, ck) in perros:
        (f, c), m = entrada(pl, pk); (gf, gc), gm = entrada(cl, ck)
        if t[f * N + c] < 0 or not t[f * N + c] & m: return False
        vis = {(f, c)}; q = [(f, c)]; llego = False
        while q:
            a, b = q.pop(); v = t[a * N + b]
            if (a, b) == (gf, gc) and v & gm: llego = True; break
            for bit, (df, dc, opu) in DIRS.items():
                na, nb = a + df, b + dc
                if v & bit and 0 <= na < N and 0 <= nb < N and (na, nb) not in vis and t[na * N + nb] >= 0 and t[na * N + nb] & opu:
                    vis.add((na, nb)); q.append((na, nb))
        if not llego: return False
    return True
def camino(ini, fin_):
    for _ in range(200):
        p = [ini]; vis = {ini}
        while p[-1] != fin_ and len(p) < 14:
            a, b = p[-1]; ops = [(a + df, b + dc) for df, dc, _ in DIRS.values() if 0 <= a + df < N and 0 <= b + dc < N and (a + df, b + dc) not in vis]
            if not ops: break
            ops.sort(key=lambda x: abs(x[0] - fin_[0]) + abs(x[1] - fin_[1]) + random.random() * 2.5)
            n = ops[0]; p.append(n); vis.add(n)
        if p[-1] == fin_: return p
    return None
def armar(nperros):
    lados = ['arriba', 'abajo', 'izq', 'der']; t = [0] * (N * N); perros = []; usadas = set()
    for _ in range(nperros):
        pl, cl = random.sample(lados, 2); pk, ck = random.randrange(N), random.randrange(N)
        (a, am), (b, bm) = entrada(pl, pk), entrada(cl, ck)
        p = camino(a, b)
        if not p or set(p) & usadas: return None
        usadas |= set(p)
        for i, cel in enumerate(p):
            m = 0
            if i == 0: m |= am
            if i == len(p) - 1: m |= bm
            for vec in (p[i - 1] if i else None, p[i + 1] if i + 1 < len(p) else None):
                if vec:
                    for bit, (df, dc, _) in DIRS.items():
                        if (cel[0] + df, cel[1] + dc) == vec: m |= bit
            t[cel[0] * N + cel[1]] = m
        perros.append(((pl, pk), (cl, ck)))
    libres = [i for i in range(N * N) if (i // N, i % N) not in usadas]
    if not libres: return None
    hueco = random.choice(libres); t[hueco] = -1
    for i in libres:
        if i != hueco: t[i] = random.choice([0, 0, 5, 10, 3, 6, 12, 9, 7, 11])     # adornos y caminos sueltos
    return t, perros
def bfs(t, perros, limite=250000):
    ini = tuple(t); vis = {ini: 0}; q = deque([ini])
    while q:
        s = q.popleft()
        if conectados(s, perros): return vis[s]
        if len(vis) > limite: return None
        h = s.index(-1); f, c = divmod(h, N)
        for df, dc in ((0, 1), (0, -1), (1, 0), (-1, 0)):
            if 0 <= f + df < N and 0 <= c + dc < N:
                j = (f + df) * N + c + dc; l = list(s); l[h], l[j] = l[j], l[h]; n = tuple(l)
                if n not in vis: vis[n] = vis[s] + 1; q.append(n)
    return None
if __name__ == "__main__":
    cub = {(3, 6): [], (7, 11): [], (12, 16): [], (17, 40): []}
    fin = time.time() + int(sys.argv[2])
    while time.time() < fin:
        np_ = 1 if random.random() < .6 else 2
        r = armar(np_)
        if not r: continue
        t, perros = r
        s = list(t); h = s.index(-1); ult = None
        for _ in range(random.randint(8, 60)):
            f, c = divmod(h, N); ops = [(df, dc) for df, dc in ((0, 1), (0, -1), (1, 0), (-1, 0)) if 0 <= f + df < N and 0 <= c + dc < N and (-df, -dc) != ult]
            df, dc = random.choice(ops); j = (f + df) * N + c + dc; s[h], s[j] = s[j], s[h]; h = j; ult = (df, dc)
        d = bfs(s, perros)
        if not d: continue
        for (lo, hi), l in cub.items():
            if lo <= d <= hi and len(l) < 12: l.append({'minimo': d, 'fichas': s, 'perros': perros})
    out = []
    for k, l in cub.items(): print(k, len(l), file=sys.stderr); out += sorted(l, key=lambda r: (len(r['perros']), r['minimo']))[:9]
    out.sort(key=lambda r: r['minimo'])
    json.dump(out, open(sys.argv[3], 'w'))
