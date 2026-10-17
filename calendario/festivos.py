"""Festivos de Colombia (Ley 51 de 1983, «Ley Emiliani»)."""
import datetime

FIJOS = [((1, 1), 'Año Nuevo'), ((5, 1), 'Día del Trabajo'), ((7, 20), 'Día de la Independencia'),
         ((8, 7), 'Batalla de Boyacá'), ((12, 8), 'Inmaculada Concepción'), ((12, 25), 'Navidad')]

# Se pasan al lunes siguiente si no caen en lunes.
TRASLADABLES = [((1, 6), 'Reyes Magos'), ((3, 19), 'San José'), ((6, 29), 'San Pedro y San Pablo'),
                ((8, 15), 'Asunción de la Virgen'), ((10, 12), 'Día de la Raza'),
                ((11, 1), 'Todos los Santos'), ((11, 11), 'Independencia de Cartagena')]


def pascua(ano):
    """Domingo de Pascua (algoritmo de Meeus/Butcher)."""
    a, b, c = ano % 19, ano // 100, ano % 100
    d, e = b // 4, b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i, k = c // 4, c % 4
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    mes = (h + l - 7 * m + 114) // 31
    dia = ((h + l - 7 * m + 114) % 31) + 1
    return datetime.date(ano, mes, dia)


def _al_lunes(fecha):
    return fecha + datetime.timedelta(days=(7 - fecha.weekday()) % 7)


def festivos(ano):
    """Lista ordenada de (fecha, nombre)."""
    lista = [(datetime.date(ano, m, d), n) for (m, d), n in FIJOS]
    lista += [(_al_lunes(datetime.date(ano, m, d)), n) for (m, d), n in TRASLADABLES]
    p = pascua(ano)
    lista += [(p - datetime.timedelta(days=3), 'Jueves Santo'), (p - datetime.timedelta(days=2), 'Viernes Santo'),
              (_al_lunes(p + datetime.timedelta(days=39)), 'Ascensión del Señor'),
              (_al_lunes(p + datetime.timedelta(days=60)), 'Corpus Christi'),
              (_al_lunes(p + datetime.timedelta(days=68)), 'Sagrado Corazón')]
    return sorted(lista)
