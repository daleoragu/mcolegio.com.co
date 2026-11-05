"""Verifica figuras de tangram (coordenadas enteras; cada celda 1x1 partida en 4 triángulos por sus diagonales)
y encuentra una solución. Piezas (cuadrado de 4x4 clásico): 2 grandes, 1 mediano, 2 pequeños, cuadrado, paralelogramo."""
import json, sys
PIEZAS = {
    'G1': [(0, 0), (4, 0), (2, 2)], 'G2': [(0, 0), (2, 2), (0, 4)],
    'M': [(4, 2), (4, 4), (2, 4)],
    'P1': [(3, 1), (4, 0), (4, 2)], 'P2': [(2, 2), (3, 3), (1, 3)],
    'C': [(2, 2), (3, 1), (4, 2), (3, 3)],
    'R': [(0, 4), (1, 3), (3, 3), (2, 4)],
}
def dentro(p, poli):
    x, y = p; n = len(poli); r = False
    for i in range(n):
        x1, y1 = poli[i]; x2, y2 = poli[(i + 1) % n]
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1: r = not r
    return r
CUARTOS = [(.5, .2), (.8, .5), (.5, .8), (.2, .5)]   # centroides de los 4 triángulos de una celda
def celdas(poli):
    xs = [p[0] for p in poli]; ys = [p[1] for p in poli]
    s = set()
    for x in range(int(min(xs)) - 1, int(max(xs)) + 1):
        for y in range(int(min(ys)) - 1, int(max(ys)) + 1):
            for q, (dx, dy) in enumerate(CUARTOS):
                if dentro((x + dx, y + dy), poli): s.add((x, y, q))
    return s
def transformar(poli, rot, esp):
    out = []
    for x, y in poli:
        if esp: x = -x
        for _ in range(rot): x, y = -y, x
        out.append((x, y))
    return out
def formas(nombre):
    vistas, res = set(), []
    for esp in (0, 1):
        for rot in range(4):
            p = transformar(PIEZAS[nombre], rot, esp)
            mx = min(x for x, _ in p); my = min(y for _, y in p)
            p = [(x - mx, y - my) for x, y in p]
            c = frozenset(celdas(p))
            if c not in vistas: vistas.add(c); res.append((p, c))
    return res
def resolver(figura):
    obj = celdas(figura)
    if len(obj) != 64: return None, len(obj)
    xs = [p[0] for p in figura]; ys = [p[1] for p in figura]
    opciones = {}
    for n in PIEZAS:
        lista = []
        for p, c in formas(n):
            for tx in range(int(min(xs)) - 4, int(max(xs)) + 1):
                for ty in range(int(min(ys)) - 4, int(max(ys)) + 1):
                    cc = {(x + tx, y + ty, q) for x, y, q in c}
                    if cc <= obj: lista.append(([(x + tx, y + ty) for x, y in p], cc))
        opciones[n] = lista
    orden = sorted(PIEZAS, key=lambda n: len(opciones[n]))
    sol = {}
    def bt(i, libre):
        if i == len(orden): return not libre
        n = orden[i]
        for p, cc in opciones[n]:
            if cc <= libre:
                sol[n] = p
                if bt(i + 1, libre - cc): return True
        return False
    return (dict(sol) if bt(0, obj) else None), 64

FIGURAS = {
    'cuadrado': [(0, 0), (4, 0), (4, 4), (0, 4)],
    'triangulo': [(0, 0), (8, 0), (4, 4)],
    'casa': [(0, 0), (4, 0), (4, 3), (2, 5), (0, 3)],
    'rectangulo': [(0, 0), (8, 0), (8, 2), (0, 2)],
    'trapecio': [(0, 0), (6, 0), (4, 2), (2, 4)] ,
    'barco': [(0, 2), (2, 0), (6, 0), (8, 2), (5, 2), (5, 5), (2, 2)],
    'flecha': [(2, 0), (4, 0), (4, 3), (6, 3), (3, 6), (0, 3), (2, 3)],
    'vela': [(0, 0), (6, 0), (6, 1), (4, 1), (4, 5), (0, 1)],
    'pez': [(0, 2), (2, 0), (4, 2), (6, 0), (6, 4), (4, 2), (2, 4)],
    'cohete': [(1, 0), (3, 0), (4, -1), (4, 1), (3, 2), (3, 5), (2, 6), (1, 5), (1, 2), (0, 1), (0, -1)],
    'escalera': [(0, 0), (6, 0), (6, 2), (4, 2), (4, 4), (2, 4), (2, 2), (0, 2)],
    'paraguas': [(0, 3), (3, 6), (6, 3), (4, 3), (4, 0), (2, 0), (2, 3)],
    'gato': [(0, 0), (4, 0), (4, 4), (5, 5), (5, 7), (4, 6), (3, 6), (2, 7), (2, 5), (3, 4), (0, 4)],
    'montana': [(0, 0), (8, 0), (6, 2), (4, 0), (2, 2)],
    'diamante': [(2, 0), (4, 2), (2, 4), (0, 2)],
}
if __name__ == '__main__':
    ok = {}
    for nombre, f in FIGURAS.items():
        s, area = resolver(f)
        print(nombre, 'área', area / 4, 'OK' if s else 'NO')
        if s: ok[nombre] = {'figura': f, 'solucion': s}
    json.dump(ok, open('tangram.json', 'w'))
