"""Juegos de lógica (sin opción múltiple ni nota): rompecabezas con niveles. El progreso de cada
estudiante queda en su navegador. Los niveles se generaron y se verificaron con un solucionador."""
import json
import os

from django.http import Http404, JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_POST

from . import logica
from .models import ProgresoLogica
from .views import _ctx, _render, vista_aula

# id, nombre, descripción, archivo del juego
JUEGOS = [
    ('tangram', 'Tangram', 'Arme la figura de sombra con las 7 piezas.', 'tangram'),
    ('hanoi', 'Torres de Hanói', 'Pase la torre de discos con el menor número de movimientos.', 'hanoi'),
    ('trancon', 'Trancón', 'Mueva los carros para sacar el rojo por la salida.', 'trancon'),
    ('safari', 'Safari', 'Como el trancón, más grande: animales, rocas y un hipopótamo que va a los 4 lados.', 'trancon'),
    ('selva', 'Escape de la selva', 'Saque el jeep de los guardaparques entre jaguares, anacondas, caimanes y más fauna de Colombia.', 'trancon'),
    ('cerditos', 'Los tres cerditos', 'Retos de día (al jardín) y de noche (a la casita), con el lobo afuera.', 'cerditos'),
    ('ranas', 'Ranas saltarinas', 'Salte ranas hasta que solo quede la roja.', 'ranas'),
    ('bango', 'Tablero 36', 'Cubra el tablero con 7 piezas dejando destapado solo el número del reto.', 'bango'),
    ('kadogemo', 'Cuatro cuadrantes', 'Tape el tablero de puntos con las 4 piezas y deje a la vista solo los colores que pide la tarjeta.', 'kadogemo'),
    ('kiriku', 'Deslizables de colores', 'Deslice las fichas hasta copiar la tarjeta.', 'kiriku'),
    ('laberinto', 'Laberinto de colores', 'Lleve las fichas por el corredor hasta copiar la tarjeta.', 'laberinto_colores'),
    ('fila', 'La fila exacta', 'Ordene a las personas en la fila cumpliendo todas las pistas.', 'fila'),
    ('nonograma', 'Nonograma', 'Pinte la cuadrícula con las pistas de filas y columnas y descubra el dibujo.', 'nonograma'),
    ('geoplano', 'Geoplano', 'Tienda la banda en los clavos y forme figuras con el área que se pide.', 'geoplano'),
    ('regletas', 'Regletas en la balanza', 'Equilibre la balanza con regletas de colores y resuelva ecuaciones.', 'regletas'),
    ('speedrun', 'Cálculo veloz', '10 operaciones contra reloj.', 'speedrun'),
    ('sokoban', 'Empuja cajas', 'Empuje las cajas hasta las marcas sin dejarlas atrapadas.', 'sokoban'),
    ('bloque', 'Bloque rodante', 'Haga rodar el bloque en 3D hasta dejarlo parado sobre el hueco.', 'bloque'),
    ('cubo', 'Cubo del binomio y del trinomio', 'Arme (a + b)³ y (a + b + c)³ con las piezas Montessori en 3D.', 'cubo'),
    ('conejos', 'Conejos saltarines', 'Los conejos saltan sobre hongos y zorros hasta meterse en los huecos.', 'conejos'),
    ('perrito', 'Perrito a su casita', 'Deslice las fichas del camino hasta que cada perrito llegue a su casita.', 'perrito'),
    ('caperucita', 'Caperucita', 'Ponga las piezas de camino para llevar a Caperucita donde la abuela, esquivando al lobo.', 'caperucita'),
    ('ladron', 'Atrapa al ladrón', 'Encierre el carro del ladrón con los edificios antes de que escape.', 'ladron'),
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
    from . import instrucciones
    juegos = [(i, n, d, a, instrucciones.logica(i, a)) for i, n, d, a in JUEGOS]
    return _render(request, c, 'aula/logica_menu.html', {'juegos': juegos}, 'gamificacion')


@vista_aula
def logica_juego(request, pk, juego):
    c = _ctx(request, pk)
    if juego not in DATOS:
        raise Http404
    _, nombre, desc, archivo = DATOS[juego]
    p = _progreso(c, juego)
    return _render(request, c, 'aula/logica_juego.html', {
        'juego': juego, 'nombre': nombre, 'desc': desc, 'archivo': archivo, 'niveles': niveles(juego),
        'clave': f'mc-logica:{request.user.pk}:{juego}', 'servidor': p.niveles if p else {}, 'guarda': p is not None or _persona(c) is not None},
        'gamificacion')


def _persona(c):
    return getattr(c, 'estudiante', None) or getattr(c, 'integrante', None)


def _progreso(c, juego, crear=False):
    """El avance del estudiante en ese juego (None para el docente)."""
    persona = _persona(c)
    if persona is None or c.es_docente:
        return None
    filtro = dict(aula=c.aula, juego=juego, **logica.filtro_persona(persona))
    if crear:
        return ProgresoLogica.objects.get_or_create(**filtro)[0]
    return ProgresoLogica.objects.filter(**filtro).first()


@require_POST
@vista_aula
def logica_avance(request, pk, juego):
    """Llegan los niveles superados (uno o varios: los que estaban solo en el navegador también se suben).
    De cada nivel se guarda lo mejor: más estrellas; con las mismas, menos tiempo."""
    c = _ctx(request, pk)
    if juego not in DATOS:
        raise Http404
    p = _progreso(c, juego, crear=True)
    if p is None:
        return JsonResponse({'ok': True, 'prueba': True})
    try:
        lista = json.loads(request.body or b'{}').get('niveles') or {}
    except (ValueError, AttributeError):
        lista = {}
    try:
        p.total = max(0, min(2000, int(json.loads(request.body or b'{}').get('total') or p.total)))
    except (TypeError, ValueError, AttributeError):
        pass
    for k, v in list(lista.items())[:500]:
        try:
            n, est = int(k), max(1, min(3, int(v.get('estrellas') or 1)))
            seg = max(0, min(36000, int(float(v.get('segundos') or 0))))
            movs = max(0, min(100000, int(v.get('movs') or 0)))
            ayudas = max(0, min(999, int(v.get('ayudas') or 0)))
        except (TypeError, ValueError, AttributeError):
            continue
        if n < 0 or n > 2000:
            continue
        antes = p.niveles.get(str(n))
        if not antes or est > antes.get('estrellas', 0) or (est == antes.get('estrellas', 0) and seg and seg < (antes.get('segundos') or 10 ** 9)):
            p.niveles[str(n)] = {'estrellas': est, 'movs': movs, 'segundos': seg, 'ayudas': ayudas,
                                 'fecha': timezone.now().isoformat(timespec='minutes')}
    p.save()
    return JsonResponse({'ok': True, 'niveles': p.niveles})


@vista_aula
def logica_informe(request, pk):
    """El docente ve el avance de cada estudiante en los juegos de lógica."""
    c = _ctx(request, pk, docente=True)
    sel = request.GET.get('juego', '')
    personas = logica.estudiantes(c.aula)
    progresos = {}
    for p in ProgresoLogica.objects.filter(aula=c.aula):
        clave = f'i{p.integrante_id}' if p.integrante_id else f'e{p.estudiante_id}'
        progresos.setdefault(clave, {})[p.juego] = p
    juegos = [j for j in JUEGOS if not sel or j[0] == sel]
    filas = []
    for persona in personas:
        mios = progresos.get(logica.clave_de(persona), {})
        celdas = [mios.get(j[0]) for j in juegos]
        filas.append({'nombre': logica.nombre_de(persona), 'celdas': celdas,
                      'superados': sum(p.superados for p in mios.values()), 'estrellas': sum(p.estrellas for p in mios.values()),
                      'segundos': sum(p.segundos for p in mios.values()), 'ayudas': sum(p.ayudas for p in mios.values()),
                      'juegos': sum(1 for p in mios.values() if p.superados)})
    filas.sort(key=lambda f: (-f['superados'], -f['estrellas'], f['nombre']))
    return _render(request, c, 'aula/logica_informe.html', {
        'juegos': juegos, 'todos': JUEGOS, 'sel': sel, 'filas': filas,
        'sin_jugar': sum(1 for f in filas if not f['superados'])}, 'gamificacion')

