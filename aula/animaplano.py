"""Animaplano: cuadrícula de puntos del 1 al 100. Cada respuesta es el número de un punto;
uniéndolos en orden aparece la figura.

El docente pega sus propias operaciones (cada respuesta correcta, un número del 1 al 100;
«(nuevo trazo)» al comienzo de una pregunta levanta el lápiz) o deja que la plataforma
las arme para una figura, con el tipo de operaciones que escoja.
"""
import random

# Cada figura: trazos de puntos (número = (fila − 1) × 10 + columna), como en la guía.
FIGURAS = {
    'casa': ('Casa', [[82, 88, 48, 42, 82], [42, 15, 48], [63, 64, 74, 73, 63], [86, 76, 77, 87]]),
    'pez': ('Pez', [[42, 25, 48, 65, 42], [48, 30, 70, 48], [34, 35]]),
    'estrella': ('Estrella', [[5, 82, 39, 31, 88, 5]]),
    'barco': ('Barco', [[61, 70, 88, 83, 61], [65, 5], [5, 59, 55]]),
    'corazon': ('Corazón', [[13, 14, 25, 16, 17, 28, 38, 75, 32, 22, 13]]),
    'flecha': ('Flecha', [[31, 36, 16, 49, 76, 56, 51, 31]]),
}
OPERACIONES = {
    'sumas': 'Sumas y restas',
    'multi': 'Multiplicaciones (como la guía)',
    'mixtas': 'Las cuatro operaciones',
}


def _suma(n):
    if n > 2 and random.random() < .5:
        a = random.randint(1, n - 1)
        return f'{a} + {n - a}'
    b = random.randint(1, 30)
    return f'{n + b} − {b}'


def _multi(n):
    pares = [(a, n // a) for a in range(2, 11) if n % a == 0 and 2 <= n // a <= 10]
    if pares and random.random() < .6:
        a, b = random.choice(pares)
        return f'{a} × {b}'
    opciones = []
    for a in range(2, 11):
        for b in range(2, 11):
            d = n - a * b
            if 1 <= d <= 20:
                opciones.append(f'({a} × {b}) + {d}')
            elif -15 <= d <= -1:
                opciones.append(f'{a} × {b} − {-d}')
    return random.choice(opciones) if opciones else _suma(n)


def _division(n):
    d = random.randint(2, 9)
    return f'{n * d} ÷ {d}'


def operacion(n, tipo):
    if tipo == 'sumas':
        return _suma(n)
    if tipo == 'multi':
        return _multi(n)
    return random.choice([_suma, _multi, _division])(n)


def _distractores(n):
    cerca = [n + d for d in (1, -1, 10, -10, 2, -2, 11, -9) if 1 <= n + d <= 100]
    random.shuffle(cerca)
    return cerca[:3]


def generar(figura, tipo):
    """El texto de las preguntas (para el cuadro del docente) de la figura con esas operaciones."""
    _, trazos = FIGURAS.get(figura) or FIGURAS['casa']
    lineas, num = [], 1
    for trazo in trazos:
        for i, n in enumerate(trazo):
            ops = [(n, True)] + [(d, False) for d in _distractores(n)]
            random.shuffle(ops)
            lineas.append(f'{num}. {"(nuevo trazo) " if i == 0 and num > 1 else ""}{operacion(n, tipo)} =')
            lineas += [f'{"*" if bien else ""}{"ABCD"[k]}) {v}' for k, (v, bien) in enumerate(ops)]
            lineas.append('')
            num += 1
    return '\n'.join(lineas)


def revisar(preguntas):
    """Las preguntas cuya respuesta correcta no es un punto de la cuadrícula (1 a 100)."""
    malas = []
    for n, p in enumerate(preguntas, 1):
        ok = next((o['texto'] for o in p.get('opciones', []) if o.get('correcta')), '')
        try:
            v = int(str(ok).strip())
        except ValueError:
            v = 0
        if not 1 <= v <= 100:
            malas.append(n)
    return malas
