"""Bancos de preguntas de prueba para la Gamificación (práctica libre, sin nota).

Matemáticas se genera al azar cada vez: nunca se repite igual. Los demás son
listas fijas, cortas y revisadas; el docente arma las suyas pegándolas.
"""
import random

BANCOS = {
    'matematicas': 'Matemáticas (operaciones)',
    'factorizacion': 'Factorización (álgebra 8°)',
    'colombia': 'Cultura general de Colombia',
    'ingles': 'Inglés básico',
    # Banco de la olimpiada de matemáticas (40 preguntas por grado; aula/bancos/olimpiada_6_11.json)
    **{f'olimpiada{g}': f'Olimpiada de matemáticas {g}.º' for g in range(6, 12)},
}


def _opciones(correcta, distractores):
    ops = [{'texto': str(correcta), 'correcta': True}] + [{'texto': str(d), 'correcta': False} for d in distractores[:3]]
    random.shuffle(ops)
    return ops


def _matematicas(n=10):
    preguntas = []
    for _ in range(n):
        tipo = random.choice(['+', '-', '×', '÷'])
        if tipo == '+':
            a, b = random.randint(5, 60), random.randint(5, 40)
            r = a + b
        elif tipo == '-':
            a, b = random.randint(20, 90), random.randint(1, 19)
            r = a - b
        elif tipo == '×':
            a, b = random.randint(2, 12), random.randint(2, 10)
            r = a * b
        else:
            b, r = random.randint(2, 10), random.randint(2, 12)
            a = b * r
        malos = set()
        while len(malos) < 3:
            d = r + random.choice([-10, -3, -2, -1, 1, 2, 3, 10])
            if d != r and d >= 0:
                malos.add(d)
        preguntas.append({'texto': f'¿Cuánto es {a} {tipo} {b}?', 'opciones': _opciones(r, list(malos))})
    return preguntas


_COLOMBIA = [
    ('¿Cuál es la capital de Colombia?', 'Bogotá', ['Medellín', 'Cali', 'Ibagué']),
    ('¿Cuál es la capital del Tolima?', 'Ibagué', ['Neiva', 'Armenia', 'Pereira']),
    ('¿Qué río es el más largo de Colombia?', 'Magdalena', ['Cauca', 'Atrato', 'Meta']),
    ('¿En qué año fue el Grito de Independencia?', '1810', ['1819', '1830', '1492']),
    ('¿Qué colores tiene la bandera de Colombia?', 'Amarillo, azul y rojo', ['Verde, blanco y rojo', 'Azul y blanco', 'Rojo y negro']),
    ('¿Cuántos departamentos tiene Colombia?', '32', ['24', '30', '36']),
    ('¿Qué escritor colombiano ganó el Premio Nobel?', 'Gabriel García Márquez', ['Jorge Isaacs', 'Rafael Pombo', 'José Asunción Silva']),
    ('¿Cuál es el ave nacional de Colombia?', 'El cóndor de los Andes', ['El colibrí', 'El águila calva', 'El tucán']),
    ('¿En qué océanos tiene costas Colombia?', 'Pacífico y Atlántico (mar Caribe)', ['Solo Pacífico', 'Índico y Pacífico', 'Solo Atlántico']),
    ('¿Qué cordillera NO está en Colombia?', 'Los Alpes', ['Cordillera Oriental', 'Cordillera Central', 'Cordillera Occidental']),
    ('¿Cuál es el árbol nacional de Colombia?', 'La palma de cera', ['El guayacán', 'La ceiba', 'El roble']),
    ('¿Qué ciudad es conocida como «la ciudad musical de Colombia»?', 'Ibagué', ['Barranquilla', 'Popayán', 'Tunja']),
]

_INGLES = [
    ('¿Cómo se dice «perro» en inglés?', 'Dog', ['Cat', 'Bird', 'Fish']),
    ('¿Qué significa «apple»?', 'Manzana', ['Pera', 'Naranja', 'Uva']),
    ('¿Cómo se dice «rojo» en inglés?', 'Red', ['Blue', 'Green', 'Yellow']),
    ('¿Qué significa «house»?', 'Casa', ['Carro', 'Escuela', 'Calle']),
    ('Complete: «I ___ a student.»', 'am', ['is', 'are', 'be']),
    ('¿Cómo se dice «lunes» en inglés?', 'Monday', ['Sunday', 'Friday', 'Tuesday']),
    ('¿Qué significa «teacher»?', 'Profesor(a)', ['Estudiante', 'Doctor', 'Amigo']),
    ('Plural de «child»', 'children', ['childs', 'childes', 'child']),
    ('¿Cómo se dice «gracias» en inglés?', 'Thank you', ['Please', 'Sorry', 'Hello']),
    ('Complete: «She ___ to school every day.»', 'goes', ['go', 'going', 'gone']),
]


def _factorizacion():
    """Los 6 temas de factorización (del juego Tanques del Álgebra), en el formato de la plataforma."""
    import json
    import os
    ruta = os.path.join(os.path.dirname(__file__), 'bancos', 'factorizacion.json')
    with open(ruta, encoding='utf-8') as f:
        temas = json.load(f)
    return [{'texto': f"Factoriza: {it['q']}", 'opciones': _opciones(it['c'], it['d']), 'tema': t['name']}
            for t in temas for it in t['items']]


def _olimpiada(grado):
    from .planilla_preguntas import banco_olimpiada
    return [{'texto': p['texto'], 'opciones': [dict(o) for o in p['opciones']], 'tema': p['tema']} for p in banco_olimpiada() if p['grado'] == grado]


def preguntas(banco, n=10):
    if banco == 'matematicas':
        return _matematicas(n)
    if banco.startswith('olimpiada') and banco[9:].isdigit():
        todas = _olimpiada(int(banco[9:]))
        random.shuffle(todas)
        for p in todas:
            random.shuffle(p['opciones'])
        return todas[:n]
    if banco == 'factorizacion':
        todas = _factorizacion()
        return random.sample(todas, min(n, len(todas)))
    datos = {'colombia': _COLOMBIA, 'ingles': _INGLES}.get(banco, _COLOMBIA)
    elegidas = random.sample(datos, min(n, len(datos)))     # los juegos largos vuelven a barajarlas
    return [{'texto': t, 'opciones': _opciones(c, malos)} for t, c, malos in elegidas]
