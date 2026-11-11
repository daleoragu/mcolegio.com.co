"""La comparación de planes que se muestra en la página de inicio y en «Planes y pagos» (una sola fuente)."""
from .models import PLANES, PRECIOS


def _lim(n, unidad=''):
    return 'Ilimitados' if n == 0 else f'{n:,}{unidad}'.replace(',', '.')


def _nube(mb):
    return f'{mb // 1024} GB' if mb >= 1024 else f'{mb} MB'


def tabla():
    g, e, p = PLANES['gratis'], PLANES['estandar'], PLANES['premium']
    return [
        ('Comunidad docente: muro, colegas y mensajes', 'Completa', 'Completa', 'Completa + insignia ⭐'),
        ('Grupos y aulas virtuales', _lim(g['grupos']), _lim(e['grupos']), _lim(p['grupos'])),
        ('Actividades publicadas', _lim(g['paginas']), _lim(e['paginas']), _lim(p['paginas'])),
        ('Resultados de estudiantes al mes', _lim(g['resultados_mes']), _lim(e['resultados_mes']), _lim(p['resultados_mes'])),
        ('Mis materiales (guías, ABP, trabajo en equipo)', f'Hasta {g["materiales"]}', _lim(e['materiales']), _lim(p['materiales'])),
        ('PDF y Word', 'Con pie «Hecho con mcolegio»', 'Sin marca', 'Sin marca'),
        ('Tableros de clase guardados (pantalla infinita)', f'Hasta {g["tableros"]}', f'Hasta {e["tableros"]}', _lim(p.get('tableros', 0))),
        ('Juegos y gamificación', True, True, True),
        ('Exámenes con hoja de respuestas', g['examenes'], e['examenes'], p['examenes']),
        ('Eventos y olimpiadas (inscripciones, ranking, diplomas y supervisión)', g['eventos'], e['eventos'], p['eventos']),
        ('Inteligencia artificial', '30 créditos al mes', '3 créditos al día', '200 al mes + 8 al día'),
        ('Nube', _nube(g['nube_mb']), _nube(e['nube_mb']), _nube(p['nube_mb'])),
    ]


def precios():
    out = {}
    for plan in ('estandar', 'premium'):
        mes, anio = PRECIOS[(plan, 'mes')][0], PRECIOS[(plan, 'anio')][0]
        out[plan] = {'mes': mes, 'anio': anio, 'ahorro': mes * 12 - anio, 'anio_mes': round(anio / 12 / 100) * 100}
    return out
