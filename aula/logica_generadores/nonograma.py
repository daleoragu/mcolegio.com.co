"""Nonogramas con solución única: se aceptan solo los que se resuelven con lógica línea por línea."""
import json, random, itertools, functools
random.seed(9)
def pistas(linea):
    r, n = [], 0
    for v in linea:
        if v: n += 1
        elif n: r.append(n); n = 0
    if n: r.append(n)
    return r or [0]
@functools.lru_cache(maxsize=None)
def opciones(p, n):
    p = list(p)
    if p == [0]: return [tuple([0] * n)]
    res = []
    def bt(i, pos, acc):
        if i == len(p):
            res.append(tuple(acc + [0] * (n - len(acc)))); return
        resto = sum(p[i + 1:]) + len(p) - i - 1
        for s in range(pos, n - resto - p[i] + 1):
            nueva = acc + [0] * (s - len(acc)) + [1] * p[i]
            if i < len(p) - 1: nueva = nueva + [0]
            bt(i + 1, len(nueva), nueva)
    bt(0, 0, [])
    return [o for o in res if len(o) == n]
def resolver(F, C, n):
    g = [[None] * n for _ in range(n)]
    cambio = True
    while cambio:
        cambio = False
        for eje in (0, 1):
            for k in range(n):
                linea = [g[k][j] for j in range(n)] if eje == 0 else [g[j][k] for j in range(n)]
                p = tuple(F[k] if eje == 0 else C[k])
                vals = [o for o in opciones(p, n) if all(l is None or l == v for l, v in zip(linea, o))]
                if not vals: return None
                for j in range(n):
                    if linea[j] is None and all(o[j] == vals[0][j] for o in vals):
                        if eje == 0: g[k][j] = vals[0][j]
                        else: g[j][k] = vals[0][j]
                        cambio = True
    return g if all(v is not None for f in g for v in f) else None
out = []
for n, cuantos, dens in [(5, 10, .6), (7, 10, .58), (10, 10, .56)]:
    hechos = 0
    while hechos < cuantos:
        g = [[1 if random.random() < dens else 0 for _ in range(n)] for _ in range(n)]
        if any(sum(f) == 0 for f in g): continue
        F = [pistas(f) for f in g]; C = [pistas([g[i][j] for i in range(n)]) for j in range(n)]
        s = resolver(F, C, n)
        if s and s == g:
            out.append({'n': n, 'filas': F, 'columnas': C, 'solucion': [''.join(map(str, f)) for f in g]}); hechos += 1
json.dump(out, open('/home/user/mcolegio.com.co/aula/static/aula/logica/niveles/nonograma.json', 'w'))
print(len(out))
