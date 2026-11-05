"""Arma figuras de tangram al azar juntando las 7 piezas lado con lado (siempre tienen solución)."""
import json, random, sys
from tangram import PIEZAS, formas
from PIL import Image, ImageDraw
random.seed(int(sys.argv[1]))
N = 20; O = 8          # ventana de 20x20 celdas; la primera pieza va cerca de (8, 8)
def bit_t(x, y, q): return 1 << ((y * N + x) * 4 + q)
# aristas: horizontales (x,y)-(x+1,y) y verticales (x,y)-(x,y+1); bits aparte
def bit_h(x, y): return 1 << (y * (N + 1) + x)
def bit_v(x, y): return 1 << ((N + 1) * (N + 1) + y * (N + 1) + x)
BASE_D = 2 * (N + 1) * (N + 1)
def bit_d(x, y, k): return 1 << (BASE_D + (y * N + x) * 4 + k)   # media diagonal del centro a la esquina k
def borde(x, y, q):
    lado = [bit_h(x, y), bit_v(x + 1, y), bit_h(x, y + 1), bit_v(x, y)][q]
    return lado | bit_d(x, y, q) | bit_d(x, y, (q + 1) % 4)
OPC = {}
for n in PIEZAS:
    lista = []
    for p, c in formas(n):
        w = max(x for x, _, _ in c) + 1; h = max(y for _, y, _ in c) + 1
        for tx in range(0, N - w):
            for ty in range(0, N - h):
                m = 0; b = 0
                for x, y, q in c:
                    m |= bit_t(x + tx, y + ty, q); b |= borde(x + tx, y + ty, q)
                lista.append(([(x + tx, y + ty) for x, y in p], m, b))
    OPC[n] = lista
def armar():
    orden = list(PIEZAS); random.shuffle(orden)
    ocup = 0; bocup = 0; sol = {}
    for i, n in enumerate(orden):
        if i == 0:
            cands = [c for c in OPC[n] if 6 <= min(x for x, _ in c[0]) <= 8 and 6 <= min(y for _, y in c[0]) <= 8]
            p, m, b = random.choice(cands)
        else:
            cands = []
            for p, m, b in OPC[n]:
                if m & ocup: continue
                t = bin(b & bocup).count('1')
                if t: cands.append((t, p, m, b))
            if not cands: return None
            mx = max(c[0] for c in cands)
            cands = [c for c in cands if c[0] >= mx - random.choice([0, 1, 1, 2, 3])]
            _, p, m, b = random.choice(cands)
        sol[n] = p; ocup |= m; bocup |= b
    return sol
def dibujar(lista, ruta, cols=8):
    T = 20
    filas = (len(lista) + cols - 1) // cols
    im = Image.new('RGB', (cols * 6 * T, filas * 6 * T), 'white'); d = ImageDraw.Draw(im)
    for i, sol in enumerate(lista):
        ox, oy = (i % cols) * 6 * T, (i // cols) * 6 * T
        pts = [p for poli in sol.values() for p in poli]
        mx = min(x for x, _ in pts); my = min(y for _, y in pts); Mx = max(x for x, _ in pts); My = max(y for _, y in pts)
        e = min(5.2 * T / max(1, Mx - mx), 5.2 * T / max(1, My - my), T)
        for poli in sol.values():
            d.polygon([(ox + 8 + (x - mx) * e, oy + 8 + (My - y) * e) for x, y in poli], fill='#333')
        d.rectangle([ox, oy, ox + 6 * T - 1, oy + 6 * T - 1], outline='#ddd')
        d.text((ox + 3, oy + 2), str(i), fill='red')
    im.save(ruta)
res = []
while len(res) < int(sys.argv[3]):
    r = armar()
    if r: res.append(r)
dibujar(res, sys.argv[2])
json.dump(res, open(sys.argv[2] + '.json', 'w'))
