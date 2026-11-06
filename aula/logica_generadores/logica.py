import json, random, itertools
from collections import deque
random.seed(5)
OUT = {}

# ---------- Tangram: figuras escogidas de las hojas generadas ----------
from tangram import resolver as resolver_tg
t3 = json.load(open('tg3.png.json')); t4 = json.load(open('tg4.png.json'))
base = json.load(open('tangram.json'))
ESCOGIDAS = [('Cuadrado', base['cuadrado']['solucion']), ('Triángulo', base['triangulo']['solucion']),
             ('Cabeza de gato', t3[28]), ('Martillo', t4[27]), ('Árbol', t3[54]), ('Pez', t3[46]),
             ('Flecha', t4[26]), ('Velero', t3[55]), ('Ballena', t3[60]), ('Gato sentado', t3[35]),
             ('Avión', t3[61]), ('Zapato', t3[1]), ('Pájaro', t3[30]), ('Perro', t3[23]), ('Bota', t4[41]), ('Ganso', t4[19])]
tg = []
for nombre, sol in ESCOGIDAS:
    pts = [p for poli in sol.values() for p in poli]
    mx = min(x for x, _ in pts); My = max(y for _, y in pts)
    tg.append({'nombre': nombre, 'piezas': {k: [[x - mx, My - y] for x, y in v] for k, v in sol.items()}})   # y hacia abajo
OUT['tangram'] = tg

# ---------- Tablero 36 (tipo Bango): 7 pentominós llenan el 6x6 menos el número del reto ----------
PENTO = {
    'I': [(0,0),(1,0),(2,0),(3,0),(4,0)], 'L': [(0,0),(1,0),(2,0),(3,0),(3,1)], 'P': [(0,0),(0,1),(1,0),(1,1),(2,0)],
    'U': [(0,0),(0,2),(1,0),(1,1),(1,2)], 'T': [(0,0),(0,1),(0,2),(1,1),(2,1)], 'X': [(0,1),(1,0),(1,1),(1,2),(2,1)],
    'N': [(0,0),(1,0),(1,1),(2,1),(3,1)], 'Y': [(0,0),(1,0),(1,1),(2,0),(3,0)], 'W': [(0,0),(1,0),(1,1),(2,1),(2,2)],
    'Z': [(0,0),(0,1),(1,1),(2,1),(2,2)], 'V': [(0,0),(1,0),(2,0),(2,1),(2,2)], 'F': [(0,1),(0,2),(1,0),(1,1),(2,1)],
}
def orient(cells):
    res = set()
    for esp in (0, 1):
        for r in range(4):
            c = [(y, -x) if False else (x, y) for x, y in cells]
            c = [(x, -y) if esp else (x, y) for x, y in cells]
            for _ in range(r): c = [(y, -x) for x, y in c]
            mx = min(x for x, _ in c); my = min(y for _, y in c)
            res.add(tuple(sorted((x - mx, y - my) for x, y in c)))
    return list(res)
def tablero36(nombres, hueco):
    libres = {(f, c) for f in range(6) for c in range(6)} - {hueco}
    ors = {n: orient(PENTO[n]) for n in nombres}
    sol = {}
    def bt(libres, quedan):
        if not quedan: return True
        f0, c0 = min(libres)
        for n in list(quedan):
            for o in ors[n]:
                # anclar la primera celda de la forma a la celda libre más arriba-izquierda
                a = min(o)
                cel = [(f0 + x - a[0], c0 + y - a[1]) for x, y in o]
                if all(p in libres for p in cel):
                    sol[n] = cel
                    if bt(libres - set(cel), quedan - {n}): return True
        return False
    return dict(sol) if bt(libres, frozenset(nombres)) else None
mejor = None
for combo in [('I','L','P','U','T','X','N'), ('I','L','P','U','X','Y','N'), ('I','L','P','U','T','Y','W'), ('I','L','P','U','X','Y','Z'), ('L','P','U','T','X','Y','N')]:
    ok = {}
    for n in range(36):
        s = tablero36(combo, (n // 6, n % 6))
        if s: ok[n + 1] = s
    print('bango', combo, len(ok))
    if not mejor or len(ok) > len(mejor[1]): mejor = (combo, ok)
OUT['bango'] = {'piezas': {n: PENTO[n] for n in mejor[0]}, 'retos': sorted(mejor[1]), 'soluciones': {k: v for k, v in mejor[1].items()}}

# ---------- Los tres cerditos (día y noche) ----------
CERD = [[(0,0,'c'),(0,1,'j'),(1,0,'j')], [(0,0,'c'),(0,1,'j'),(0,2,'j')], [(0,0,'c'),(0,1,'c'),(1,0,'j'),(1,1,'j')]]
def rots(p):
    out = []
    c = p
    for _ in range(4):
        mx = min(x for x, _, _ in c); my = min(y for _, y, _ in c)
        k = tuple(sorted((x - mx, y - my, t) for x, y, t in c))
        if k not in out: out.append(k)
        c = [(y, -x, t) for x, y, t in c]
    return out
CROT = [rots(p) for p in CERD]
def colocaciones():
    todas = []
    def bt(i, ocup, acc):
        if i == 3: todas.append(dict(acc)); return
        for o in CROT[i]:
            for f in range(4):
                for c in range(4):
                    cel = {(f + x, c + y): t for x, y, t in o}
                    if all(0 <= a < 4 and 0 <= b < 4 for a, b in cel) and not (set(cel) & ocup):
                        acc[i] = (o, f, c, cel); bt(i + 1, ocup | set(cel), acc)
        acc.pop(i, None)
    bt(0, set(), {})
    return todas
COL = colocaciones()
def cumple(col, cerditos, lobos, modo):
    tipo = {}
    for (o, f, c, cel) in col.values(): tipo.update(cel)
    for p in cerditos:
        if tipo.get(p) != ('j' if modo == 'dia' else 'c'): return False
    return all(l not in tipo for l in lobos)
retos = []
celdas = [(f, c) for f in range(4) for c in range(4)]
intentos = 0
while len(retos) < 40 and intentos < 4000:
    intentos += 1
    modo = random.choice(['dia', 'noche'])
    nc = random.choice([2, 3, 3]); nl = random.choice([1, 2, 2])
    elegidas = random.sample(celdas, nc + nl)
    cer, lob = elegidas[:nc], elegidas[nc:]
    sols = [col for col in COL if cumple(col, cer, lob, modo)]
    if 1 <= len(sols) <= 6:
        s = sols[0]
        retos.append({'modo': modo, 'cerditos': cer, 'lobos': lob, 'n': len(sols),
                      'solucion': [[i, list(map(list, o)), f, c] for i, (o, f, c, _) in s.items()]})
retos.sort(key=lambda r: (-r['n'], len(r['lobos']) + len(r['cerditos'])))
print('cerditos', len(retos), [r['n'] for r in retos][:40])
OUT['cerditos'] = {'piezas': CERD, 'retos': retos[:36]}

# ---------- Ranas saltarinas ----------
PADS = [(0,0),(0,2),(0,4),(1,1),(1,3),(2,0),(2,2),(2,4),(3,1),(3,3),(4,0),(4,2),(4,4)]
IDX = {p: i for i, p in enumerate(PADS)}
SALTOS = []
for (f, c) in PADS:
    for df, dc in [(0,2),(2,0),(1,1),(1,-1)]:
        for s in (1, -1):
            m = (f + df * s, c + dc * s); d = (f + 2 * df * s, c + 2 * dc * s)
            if m in IDX and d in IDX: SALTOS.append((IDX[(f, c)], IDX[m], IDX[d]))
def resolver_ranas(verdes, roja):
    # DFS: dejar solo la roja
    memo = set()
    def dfs(v, r):
        if not v: return []
        k = (v, r)
        if k in memo: return None
        memo.add(k)
        ocup = v | {r}
        for a, m_, d in SALTOS:
            if a in ocup and m_ in v and d not in ocup:
                if a == r: nv, nr = v - {m_}, d
                else: nv, nr = (v - {a, m_}) | {d}, r
                s = dfs(frozenset(nv), nr)
                if s is not None: return [(a, d)] + s
        return None
    return dfs(frozenset(verdes), roja)
ranas = []
vistos = set()
for n in range(1, 11):
    hechas = 0; t = 0
    while hechas < 4 and t < 3000:
        t += 1
        r = random.randrange(13); v = set()
        ok = True
        for _ in range(n):
            # salto al revés: la ranita que está en d vuelve a a y aparece una verde en m
            ops = []
            ocup = v | {r}
            for a, m_, d in SALTOS:
                if d in ocup and a not in ocup and m_ not in ocup: ops.append((a, m_, d))
            if not ops: ok = False; break
            a, m_, d = random.choice(ops)
            if d == r: r = a
            else: v = (v - {d}) | {a}
            v.add(m_)
        if not ok: continue
        k = (frozenset(v), r)
        if k in vistos: continue
        vistos.add(k)
        if resolver_ranas(v, r) is not None:
            ranas.append({'verdes': sorted(v), 'roja': r}); hechas += 1
print('ranas', len(ranas))
OUT['ranas'] = {'pads': PADS, 'retos': ranas}

# ---------- Cuatro cuadrantes (Kadogemo): ahora en kadogemo.py (tablero con puntos fijos) ----------

# ---------- Deslizables de colores (tipo Kiriku): 4x4 con un hueco, como el 15 ----------
def mezclar_desliz(obj, pasos):
    g = [r[:] for r in obj]; f, c = 0, 3
    for fi in range(4):
        for ci in range(4):
            if g[fi][ci] == '.': f, c = fi, ci
    ultimo = None
    for _ in range(pasos):
        ops = [(df, dc) for df, dc in [(0,1),(0,-1),(1,0),(-1,0)] if 0 <= f + df < 4 and 0 <= c + dc < 4 and (df, dc) != ultimo]
        df, dc = random.choice(ops)
        g[f][c], g[f + df][c + dc] = g[f + df][c + dc], g[f][c]
        f, c = f + df, c + dc; ultimo = (-df, -dc)
    return g
def bfs_desliz(ini, obj, limite=300000):
    a = ''.join(''.join(r) for r in ini); b = ''.join(''.join(r) for r in obj)
    vis = {a: 0}; q = deque([a])
    while q:
        s = q.popleft()
        if s == b: return vis[s]
        if len(vis) > limite: return None
        i = s.index('.'); f, c = divmod(i, 4)
        for df, dc in [(0,1),(0,-1),(1,0),(-1,0)]:
            if 0 <= f + df < 4 and 0 <= c + dc < 4:
                j = (f + df) * 4 + c + dc; l = list(s); l[i], l[j] = l[j], l[i]; t = ''.join(l)
                if t not in vis: vis[t] = vis[s] + 1; q.append(t)
    return None
kiriku = []
for pasos in [6, 8, 10, 12, 14, 16, 18, 22, 26, 30, 36, 44]:
    for _ in range(2):
        colores = list('RRRRAAAAVVVVNNN.'); random.shuffle(colores)
        obj = [colores[i * 4:(i + 1) * 4] for i in range(4)]
        ini = mezclar_desliz(obj, pasos)
        d = bfs_desliz(ini, obj)
        if d and d >= 3: kiriku.append({'inicio': [''.join(r) for r in ini], 'meta': [''.join(r) for r in obj], 'minimo': d})
kiriku.sort(key=lambda r: r['minimo'])
print('kiriku', [r['minimo'] for r in kiriku])
OUT['kiriku'] = {'retos': kiriku}

# ---------- Laberinto de colores: 4 columnas (caben 5) y un puesto de espera arriba ----------
def movs_lab(e):
    cols, esp = e
    res = []
    fuentes = [('c', i) for i in range(4) if cols[i]] + ([('e', 0)] if esp else [])
    for tipo, i in fuentes:
        bola = cols[i][-1] if tipo == 'c' else esp
        for j in range(4):
            if (tipo == 'e' or j != i) and len(cols[j]) < 5:
                nc = list(cols)
                if tipo == 'c': nc[i] = nc[i][:-1]
                nc[j] = nc[j] + bola
                res.append((tuple(nc), esp if tipo == 'c' else ''))
        if tipo == 'c' and not esp:
            nc = list(cols); nc[i] = nc[i][:-1]; res.append((tuple(nc), bola))
    return res
def bfs_lab(ini, obj, limite=400000):
    vis = {ini: 0}; q = deque([ini])
    while q:
        e = q.popleft()
        if e == obj: return vis[e]
        if len(vis) > limite: return None
        for n in movs_lab(e):
            if n not in vis: vis[n] = vis[e] + 1; q.append(n)
    return None
lab = []
for pasos in [4, 6, 8, 10, 12, 14, 16, 20, 24, 28, 32, 40]:
    for _ in range(2):
        bolas = list('RRRRAAAAVVVVYYYY'); random.shuffle(bolas)
        obj = (tuple(''.join(bolas[i * 4:(i + 1) * 4]) for i in range(4)), '')
        e = obj
        for _ in range(pasos): e = random.choice(movs_lab(e))
        # que el inicio quede sin bola en espera
        while e[1]:
            e = random.choice([n for n in movs_lab(e) if not n[1]] or movs_lab(e))
        d = bfs_lab(e, obj)
        if d and d >= 3: lab.append({'inicio': list(e[0]), 'meta': list(obj[0]), 'minimo': d})
lab.sort(key=lambda r: r['minimo'])
print('laberinto', [r['minimo'] for r in lab])
OUT['laberinto'] = {'retos': lab}

json.dump(OUT, open('logica.json', 'w'), ensure_ascii=False)
