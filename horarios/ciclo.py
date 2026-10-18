"""Horario por días de ciclo: qué «Día N» le toca a cada fecha.

Se cuentan solo los días con clase (los días de la semana que el colegio marcó, menos los días
sin clase: los que se anotan aquí y los festivos, recesos y días sin clase del calendario escolar).
Si un lunes no hubo clase, el Día 1 pasa al martes y todo se corre.
"""
import datetime

from .models import ConfiguracionHorario, DiaSinClase, Jornada


def largo_ciclo(colegio):
    """Cuántos días tiene el ciclo (el mayor de las jornadas por ciclo), o 0 si no hay."""
    n = 0
    for j in Jornada.objects.filter(colegio=colegio):
        n = max(n, j.dias_ciclo)
    return n


def dias_sin_clase(colegio, desde, hasta):
    fechas = set(DiaSinClase.objects.filter(colegio=colegio, fecha__gte=desde, fecha__lte=hasta)
                 .values_list('fecha', flat=True))
    try:
        from notas.modulos import esta_activo
        if esta_activo(colegio, 'calendario'):
            from calendario.models import Evento
            for e in Evento.objects.filter(colegio=colegio, tipo__in=['FESTIVO', 'RECESO', 'SIN_CLASE'],
                                           fecha__lte=hasta).exclude(para='DOCENTES'):
                if e.cursos.exists():
                    continue                     # solo para algunos cursos: no frena a todo el colegio
                d = max(e.fecha, desde)
                while d <= min(e.ultimo_dia, hasta):
                    fechas.add(d)
                    d += datetime.timedelta(days=1)
    except Exception:
        pass
    return fechas


def es_dia_de_clase(conf, fecha, sin):
    return fecha.isoweekday() in (conf.ciclo_dias_semana or [1, 2, 3, 4, 5]) and fecha not in sin


def dia_del_ciclo(colegio, fecha, n=None, conf=None):
    """1..n, o None si ese día no hay clase o el ciclo no está configurado."""
    conf = conf or ConfiguracionHorario.objects.filter(colegio=colegio).first()
    n = n or largo_ciclo(colegio)
    if not conf or not conf.ciclo_inicio or not n or fecha < conf.ciclo_inicio:
        return None
    sin = dias_sin_clase(colegio, conf.ciclo_inicio, fecha)
    if not es_dia_de_clase(conf, fecha, sin):
        return None
    cuenta = 0
    d = conf.ciclo_inicio
    while d < fecha:
        if es_dia_de_clase(conf, d, sin):
            cuenta += 1
        d += datetime.timedelta(days=1)
    return cuenta % n + 1


def proximos(colegio, desde, cuantos=15):
    """[(fecha, Día N o None)] de los próximos días (para revisar cómo va el ciclo)."""
    conf = ConfiguracionHorario.objects.filter(colegio=colegio).first()
    n = largo_ciclo(colegio)
    if not conf or not conf.ciclo_inicio or not n:
        return []
    hasta = desde + datetime.timedelta(days=cuantos * 2 + 10)
    sin = dias_sin_clase(colegio, conf.ciclo_inicio, hasta)
    cuenta = 0
    d = conf.ciclo_inicio
    out = []
    while d <= hasta and len(out) < cuantos:
        clase = es_dia_de_clase(conf, d, sin)
        if d >= desde:
            out.append((d, (cuenta % n + 1) if clase else None))
        if clase:
            cuenta += 1
        d += datetime.timedelta(days=1)
    return out


def dias_de_fecha(colegio, fecha):
    """Los números de día del horario que corresponden a esa fecha: el día de la semana (1-6) y,
    si hay horario por ciclo, el 100 + Día N."""
    out = {fecha.isoweekday()}
    n = largo_ciclo(colegio)
    if n:
        k = dia_del_ciclo(colegio, fecha, n)
        if k:
            out.add(100 + k)
    return out


def nombre_fecha(colegio, fecha):
    k = dia_del_ciclo(colegio, fecha) if largo_ciclo(colegio) else None
    return f' · Día {k} del ciclo' if k else ''
