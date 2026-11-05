"""Juegos de lógica (sin opción múltiple ni nota): rompecabezas con niveles. El progreso de cada
estudiante queda en su navegador. Los niveles se generaron y se verificaron con un solucionador."""
import json
import os

from django.http import Http404

from .views import _ctx, _render, vista_aula

# id, nombre, descripción, archivo del juego
JUEGOS = [
    ('tangram', 'Tangram', 'Arme la figura de sombra con las 7 piezas.', 'tangram'),
    ('hanoi', 'Torres de Hanói', 'Pase la torre de discos con el menor número de movimientos.', 'hanoi'),
    ('trancon', 'Trancón', 'Mueva los carros para sacar el rojo por la salida.', 'trancon'),
    ('safari', 'Safari', 'Como el trancón, más grande: animales, rocas y un hipopótamo que va a los 4 lados.', 'trancon'),
    ('cerditos', 'Los tres cerditos', 'Retos de día (al jardín) y de noche (a la casita), con el lobo afuera.', 'cerditos'),
    ('ranas', 'Ranas saltarinas', 'Salte ranas hasta que solo quede la roja.', 'ranas'),
    ('bango', 'Tablero 36', 'Cubra el tablero con 7 piezas dejando destapado solo el número del reto.', 'bango'),
    ('kadogemo', 'Cuatro cuadrantes', 'Acomode las 4 piezas para que los huecos queden como en la tarjeta.', 'kadogemo'),
    ('kiriku', 'Deslizables de colores', 'Deslice las fichas hasta copiar la tarjeta.', 'kiriku'),
    ('laberinto', 'Laberinto de colores', 'Lleve las fichas por el corredor hasta copiar la tarjeta.', 'laberinto_colores'),
    ('fila', 'La fila exacta', 'Ordene a las personas en la fila cumpliendo todas las pistas.', 'fila'),
    ('nonograma', 'Nonograma', 'Pinte la cuadrícula con las pistas de filas y columnas y descubra el dibujo.', 'nonograma'),
    ('geoplano', 'Geoplano', 'Tienda la banda en los clavos y forme figuras con el área que se pide.', 'geoplano'),
    ('regletas', 'Regletas en la balanza', 'Equilibre la balanza con regletas de colores y resuelva ecuaciones.', 'regletas'),
    ('speedrun', 'Cálculo veloz', '10 operaciones contra reloj.', 'speedrun'),
    ('fijas', 'Picas y fijas con figuras', 'Adivine el orden secreto: solo sabrá cuántas están exactas y cuántas en otro sitio. Solo o entre dos.', 'fijas'),
]
DATOS = {j[0]: j for j in JUEGOS}
NIVELES = os.path.join(os.path.dirname(__file__), 'static', 'aula', 'logica', 'niveles')


def niveles(juego):
    with open(os.path.join(NIVELES, juego + '.json'), encoding='utf-8') as f:
        return json.load(f)


@vista_aula
def logica_menu(request, pk):
    c = _ctx(request, pk)
    return _render(request, c, 'aula/logica_menu.html', {'juegos': JUEGOS}, 'gamificacion')


@vista_aula
def logica_juego(request, pk, juego):
    c = _ctx(request, pk)
    if juego not in DATOS:
        raise Http404
    _, nombre, desc, archivo = DATOS[juego]
    return _render(request, c, 'aula/logica_juego.html', {
        'juego': juego, 'nombre': nombre, 'desc': desc, 'archivo': archivo, 'niveles': niveles(juego),
        'clave': f'mc-logica:{request.user.pk}:{juego}'}, 'gamificacion')
