"""Kadogemo (Cuatro cuadrantes): el tablero de 6x6 (4 cuadros de 3x3) tiene puntos de colores fijos
y algunas casillas en blanco. Las 4 piezas (3x3 con 2 huecos) se ponen una en cada cuadro, giradas o
volteadas; por los huecos se ven los puntos. Cada tarjeta dice cuántos puntos de cada color deben
quedar a la vista (la forma y el lugar no importan). Se calculan todas las jugadas posibles para
saber qué tarjetas tienen solución y cuántas formas hay de lograrlas (menos formas = más difícil).

    python3 kadogemo.py      (reescribe los datos de kadogemo en aula/static/aula/logica/niveles/kadogemo.json)
"""
import itertools, json, random, collections, os

random.seed(2026)
PIEZAS = {'U': [[0, 1], [1, 1]], 'H': [[0, 1], [2, 1]], 'W': [[0, 2], [1, 1]], 'S': [[0, 0], [2, 2]]}   # los huecos
COLORES_PIEZA = {'U': '#e03131', 'H': '#f2c400', 'W': '#2f9e44', 'S': '#1971c2'}
PUNTOS = {'R': '#e03131', 'A': '#fcc419', 'V': '#2f9e44', 'Z': '#1c7ed6', 'B': '#ffffff'}
NOMBRES = {'R': 'rojo', 'A': 'amarillo', 'V': 'verde', 'Z': 'azul', 'B': 'blanco'}


def orientaciones(huecos):
    vistas, f = set(), [tuple(h) for h in huecos]
    for voltear in (False, True):
        cs = [(a, 2 - b) if voltear else (a, b) for a, b in f]
        for _ in range(4):
            cs = [(b, 2 - a) for a, b in cs]
            vistas.add(tuple(sorted(cs)))
    return sorted(vistas)


OR = {k: orientaciones(v) for k, v in PIEZAS.items()}


def tablero_al_azar():
    # 6 puntos de cada color y 6 casillas en blanco, repartidos para que cada cuadro tenga variedad
    while True:
        bolsa = [c for c in PUNTOS for _ in range(6)] + ['.'] * 6
        random.shuffle(bolsa)
        t = [bolsa[i * 6:(i + 1) * 6] for i in range(6)]
        cuadros = [{t[f][c] for f in range(qf, qf + 3) for c in range(qc, qc + 3)} for qf in (0, 3) for qc in (0, 3)]
        if all(len(q - {'.'}) >= 3 for q in cuadros):
            return [''.join(r) for r in t]


def jugadas(t):
    """cuenta de colores a la vista -> lista de soluciones (pieza: [cuadro, huecos])"""
    res = collections.defaultdict(list)
    vistos_q = {}
    for q in range(4):
        qf, qc = (q // 2) * 3, (q % 2) * 3
        for k, ors in OR.items():
            vistos_q[q, k] = [(o, [t[qf + a][qc + b] for a, b in o]) for o in ors]
    for perm in itertools.permutations(PIEZAS):
        for combo in itertools.product(*[vistos_q[q, perm[q]] for q in range(4)]):
            cuenta = collections.Counter(c for _, cs in combo for c in cs if c != '.')
            clave = tuple(sorted(cuenta.items()))
            res[clave].append({perm[q]: q for q in range(4)})
    return res


def puntaje(res):
    return sum(1 for k in res if len(k) <= 2 and 5 <= sum(n for _, n in k) <= 8) * 3 + sum(1 for k in res if len(k) == 3 and 5 <= sum(n for _, n in k) <= 8)


def main():
    # Se prueban muchos tableros y se queda el que permite más tarjetas de 1 o 2 colores
    mejor = None
    for _ in range(400):
        t = tablero_al_azar(); r = jugadas(t); p = puntaje(r)
        if not mejor or p > mejor[0]: mejor = (p, t, r)
    _, t, res = mejor
    # Tarjetas como las del juego: pocos colores (1 a 3) y de 5 a 8 puntos a la vista
    buenas = [(k, v) for k, v in res.items() if 1 <= len(k) <= 3 and 5 <= sum(n for _, n in k) <= 8]
    for k, v in buenas: random.shuffle(v)
    # primero las de 2 colores (como las tarjetas del juego), luego por dificultad
    buenas.sort(key=lambda kv: -len(kv[1]))
    dos = [kv for kv in buenas if len(kv[0]) <= 2]; tres = [kv for kv in buenas if len(kv[0]) == 3]
    buenas = dos + tres[:max(0, 50 - len(dos))] if len(dos) < 50 else dos
    buenas.sort(key=lambda kv: -len(kv[1]))
    # 50 tarjetas de fácil (muchas formas) a difícil (pocas formas), repartidas en todo el rango
    paso = max(1, len(buenas) / 50)
    elegidas = [buenas[int(i * paso)] for i in range(50) if int(i * paso) < len(buenas)]
    retos = [{'cuenta': dict(k), 'formas': len(v), 'solucion': v[0]} for k, v in elegidas]
    ruta = os.path.join(os.path.dirname(__file__), '..', 'static', 'aula', 'logica', 'niveles', 'kadogemo.json')
    json.dump({'piezas': PIEZAS, 'colores': COLORES_PIEZA, 'puntos': PUNTOS, 'nombres': NOMBRES, 'tablero': t, 'retos': retos},
              open(ruta, 'w'), ensure_ascii=False)
    print('\n'.join(t)); print(len(buenas), 'tarjetas posibles;', len(retos), 'elegidas; formas:', [r['formas'] for r in retos])
    print(retos[0], retos[-1])


main()
