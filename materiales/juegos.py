"""Sopa de letras y crucigrama: la IA (o el docente) pone las palabras; la cuadrícula la arma este código.

Todo sale de las palabras y de una semilla (el id del bloque), así que el PDF del docente, la ficha del
estudiante y la calificación ven siempre la misma cuadrícula.
"""
import random
import unicodedata

LETRAS = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
MAX_PALABRAS = 15
MIN_LARGO, MAX_LARGO = 2, 15
# Direcciones de la sopa: derecha, abajo, diagonal abajo-derecha y, en nivel alto, al revés.
DIRECCIONES = [(0, 1), (1, 0), (1, 1)]
DIRECCIONES_DIFICILES = [(0, -1), (-1, 0), (-1, -1), (1, -1), (-1, 1)]


def palabra_limpia(texto):
    """Mayúsculas, sin tildes ni espacios ni signos (la Ñ se vuelve N para no romper la cuadrícula)."""
    t = unicodedata.normalize('NFD', str(texto or '').upper())
    t = ''.join(c for c in t if unicodedata.category(c) != 'Mn')
    return ''.join(c for c in t if c in LETRAS)[:MAX_LARGO]


# ---------------------------------------------------------------------------
# Sopa de letras
# ---------------------------------------------------------------------------
def generar_sopa(palabras, semilla, dificil=False):
    """{'filas': ['ABC…', …], 'ubicaciones': [{'palabra', 'f', 'c', 'df', 'dc'}], 'fuera': [palabras que no cupieron]}"""
    palabras = [p for p in dict.fromkeys(palabra_limpia(x) for x in palabras) if len(p) >= MIN_LARGO][:MAX_PALABRAS]
    if not palabras:
        return {'filas': [], 'ubicaciones': [], 'fuera': []}
    azar = random.Random(f'sopa-{semilla}')
    largo = max(len(p) for p in palabras)
    lado = max(10, largo + 2, min(18, int((sum(len(p) for p in palabras) * 2.2) ** 0.5) + 1))
    direcciones = DIRECCIONES + (DIRECCIONES_DIFICILES if dificil else [])
    for intento in range(6):
        tablero = [[''] * lado for _ in range(lado)]
        ubicaciones, fuera = [], []
        for p in sorted(palabras, key=len, reverse=True):
            puesta = False
            opciones = [(f, c, d) for f in range(lado) for c in range(lado) for d in direcciones]
            azar.shuffle(opciones)
            for f, c, (df, dc) in opciones:
                ff, cf = f + df * (len(p) - 1), c + dc * (len(p) - 1)
                if not (0 <= ff < lado and 0 <= cf < lado):
                    continue
                if all(tablero[f + df * k][c + dc * k] in ('', p[k]) for k in range(len(p))):
                    for k in range(len(p)):
                        tablero[f + df * k][c + dc * k] = p[k]
                    ubicaciones.append({'palabra': p, 'f': f, 'c': c, 'df': df, 'dc': dc})
                    puesta = True
                    break
            if not puesta:
                fuera.append(p)
        if not fuera or intento == 5:
            break
        lado += 1
    for f in range(lado):
        for c in range(lado):
            if not tablero[f][c]:
                tablero[f][c] = azar.choice(LETRAS)
    orden = {p: i for i, p in enumerate(palabras)}
    ubicaciones.sort(key=lambda u: orden.get(u['palabra'], 99))
    return {'filas': [''.join(f) for f in tablero], 'ubicaciones': ubicaciones, 'fuera': fuera}


def celdas_de(u):
    return [(u['f'] + u['df'] * k, u['c'] + u['dc'] * k) for k in range(len(u['palabra']))]


def segmento_encuentra(seg, u):
    """¿El trazo del estudiante (fila y columna de la primera y la última letra) es esa palabra, en cualquier sentido?"""
    try:
        f1, c1, f2, c2 = (int(x) for x in seg)
    except (TypeError, ValueError):
        return False
    celdas = celdas_de(u)
    return {(f1, c1), (f2, c2)} == {celdas[0], celdas[-1]}


def calificar_sopa(b, r):
    """(encontradas, total)."""
    ubic = b.get('ubicaciones') or []
    segs = r if isinstance(r, list) else []
    encontradas = sum(1 for u in ubic if any(segmento_encuentra(s, u) for s in segs[:40]))
    return encontradas, len(ubic)


# ---------------------------------------------------------------------------
# Crucigrama
# ---------------------------------------------------------------------------
def generar_crucigrama(pares, semilla):
    """pares = [(palabra, pista)] → {'filas': n, 'columnas': m, 'palabras': [{numero, palabra, pista, f, c, dir}],
    'fuera': [palabras que no cruzaron]}. 'dir' es 'h' (horizontal) o 'v' (vertical)."""
    vistos, lista = set(), []
    for palabra, pista in pares:
        p = palabra_limpia(palabra)
        if len(p) >= MIN_LARGO and p not in vistos:
            vistos.add(p)
            lista.append((p, str(pista or '').strip()[:200]))
    lista = lista[:MAX_PALABRAS]
    if not lista:
        return {'filas': 0, 'columnas': 0, 'palabras': [], 'fuera': []}
    azar = random.Random(f'cruci-{semilla}')
    mejor = None
    for intento in range(8):
        orden = sorted(lista, key=lambda x: -len(x[0]))
        if intento:
            cabeza, cola = orden[:1], orden[1:]
            azar.shuffle(cola)
            orden = cabeza + cola
        resultado = _armar(orden)
        if mejor is None or len(resultado[0]) > len(mejor[0]):
            mejor = resultado
        if not resultado[1]:
            break
    puestas, fuera = mejor
    return _numerar(puestas, fuera)


def _armar(orden):
    celdas = {}            # (f, c) -> letra
    puestas, fuera = [], []

    def cabe(p, f, c, d):
        df, dc = (0, 1) if d == 'h' else (1, 0)
        antes = (f - df, c - dc)
        despues = (f + df * len(p), c + dc * len(p))
        if antes in celdas or despues in celdas:
            return False
        cruces = 0
        for k, letra in enumerate(p):
            pos = (f + df * k, c + dc * k)
            if pos in celdas:
                if celdas[pos] != letra:
                    return False
                cruces += 1
            else:
                # Una letra nueva no puede quedar pegada de lado a otra palabra.
                lado1 = (pos[0] + dc, pos[1] + df)
                lado2 = (pos[0] - dc, pos[1] - df)
                if lado1 in celdas or lado2 in celdas:
                    return False
        return cruces

    primera, pista = orden[0]
    for k, letra in enumerate(primera):
        celdas[(0, k)] = letra
    puestas.append({'palabra': primera, 'pista': pista, 'f': 0, 'c': 0, 'dir': 'h'})
    for p, pista in orden[1:]:
        opciones = []
        for (f, c), letra in list(celdas.items()):
            for k, lp in enumerate(p):
                if lp != letra:
                    continue
                for d in ('h', 'v'):
                    ff, cc = (f, c - k) if d == 'h' else (f - k, c)
                    n = cabe(p, ff, cc, d)
                    if n:
                        opciones.append((n, ff, cc, d))
        if not opciones:
            fuera.append(p)
            continue
        opciones.sort(key=lambda x: (-x[0], abs(x[1]) + abs(x[2])))
        _, f, c, d = opciones[0]
        df, dc = (0, 1) if d == 'h' else (1, 0)
        for k, letra in enumerate(p):
            celdas[(f + df * k, c + dc * k)] = letra
        puestas.append({'palabra': p, 'pista': pista, 'f': f, 'c': c, 'dir': d})
    return puestas, fuera


def _numerar(puestas, fuera):
    min_f = min(p['f'] for p in puestas)
    min_c = min(p['c'] for p in puestas)
    for p in puestas:
        p['f'] -= min_f
        p['c'] -= min_c
    filas = max(p['f'] + (1 if p['dir'] == 'h' else len(p['palabra'])) for p in puestas)
    columnas = max(p['c'] + (len(p['palabra']) if p['dir'] == 'h' else 1) for p in puestas)
    inicios = sorted({(p['f'], p['c']) for p in puestas})
    numero = {pos: i + 1 for i, pos in enumerate(inicios)}
    for p in puestas:
        p['numero'] = numero[(p['f'], p['c'])]
    puestas.sort(key=lambda p: (p['dir'], p['numero']))
    return {'filas': filas, 'columnas': columnas, 'palabras': puestas, 'fuera': fuera}


def celdas_crucigrama(b):
    """{(f, c): letra} de todas las palabras puestas."""
    salida = {}
    for p in b.get('palabras') or []:
        df, dc = (0, 1) if p['dir'] == 'h' else (1, 0)
        for k, letra in enumerate(p['palabra']):
            salida[(p['f'] + df * k, p['c'] + dc * k)] = letra
    return salida


def tablero_crucigrama(b, respuestas=None, mostrar=False):
    """Filas de celdas para pintar: None = negra; {'n': número o '', 'letra': lo escrito o la respuesta}."""
    celdas = celdas_crucigrama(b)
    numeros = {(p['f'], p['c']): p['numero'] for p in b.get('palabras') or []}
    respuestas = respuestas if isinstance(respuestas, dict) else {}
    filas = []
    for f in range(b.get('filas') or 0):
        fila = []
        for c in range(b.get('columnas') or 0):
            if (f, c) not in celdas:
                fila.append(None)
            else:
                fila.append({'f': f, 'c': c, 'n': numeros.get((f, c), ''),
                             'letra': celdas[(f, c)] if mostrar else str(respuestas.get(f'{f}-{c}') or '')[:1].upper()})
        filas.append(fila)
    return filas


def calificar_crucigrama(b, r):
    """(palabras completas y bien escritas, total)."""
    r = r if isinstance(r, dict) else {}
    bien = 0
    for p in b.get('palabras') or []:
        df, dc = (0, 1) if p['dir'] == 'h' else (1, 0)
        if all(palabra_limpia(r.get(f"{p['f'] + df * k}-{p['c'] + dc * k}"))[:1] == letra
               for k, letra in enumerate(p['palabra'])):
            bien += 1
    return bien, len(b.get('palabras') or [])
