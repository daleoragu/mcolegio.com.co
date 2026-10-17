"""Quién ve qué, los eventos automáticos de los periodos, avisos y exportar a Google/iCal."""
import calendar
import datetime
from urllib.parse import urlencode

from django.core import signing
from django.db.models import Q
from django.utils import timezone

from notas.models import Docente, Estudiante, PeriodoAcademico
from notas.models.comunicaciones import Notificacion

from .models import COLORES, Evento

SAL_ICS = 'calendario-ics'


# ---------------------------------------------------------------------------
# Quién es el usuario
# ---------------------------------------------------------------------------
class Rol:
    def __init__(self, user, colegio, admin):
        self.admin = admin
        self.docente = Docente.objects.filter(user=user, colegio=colegio).first()
        est = None if self.docente else Estudiante.objects.filter(user=user, colegio=colegio).select_related('curso').first()
        self.estudiante = est
        self.curso = est.curso if est else None

    @property
    def ve_todo(self):
        return self.admin


def visibles(colegio, rol, desde=None, hasta=None):
    qs = Evento.objects.filter(colegio=colegio).prefetch_related('cursos')
    if desde:
        qs = qs.filter(Q(fecha__gte=desde) | Q(fecha_fin__gte=desde))
    if hasta:
        qs = qs.filter(fecha__lte=hasta)
    if rol.ve_todo or rol.docente:
        # Los docentes también ven lo de estudiantes: tienen que saberlo.
        return list(qs)
    # Estudiante / familia
    qs = qs.exclude(para='DOCENTES')
    lista = []
    for e in qs:
        cursos = list(e.cursos.all())
        if not cursos or (rol.curso and rol.curso in cursos):
            lista.append(e)
    return lista


# ---------------------------------------------------------------------------
# Eventos automáticos: inicio y fin de periodo, cierre de notas
# ---------------------------------------------------------------------------
class Auto:
    """Un evento que no está en la base de datos (sale de los periodos)."""
    automatico = True

    def __init__(self, titulo, fecha, tipo, descripcion='', hora=None, para='TODOS'):
        self.titulo, self.fecha, self.tipo, self.descripcion = titulo, fecha, tipo, descripcion
        self.fecha_fin, self.hora_inicio, self.hora_fin, self.lugar, self.para = None, hora, None, '', para
        self.pk = None

    ultimo_dia = property(lambda self: self.fecha)
    color = property(lambda self: COLORES.get(self.tipo, '#334155'))

    def get_tipo_display(self):
        return {'PERIODO': 'Periodo académico', 'CIERRE': 'Cierre de notas'}.get(self.tipo, '')


def automaticos(colegio, rol, desde, hasta):
    lista = []
    for p in PeriodoAcademico.objects.filter(colegio=colegio):
        nombre = p.get_nombre_display()
        if desde <= p.fecha_inicio <= hasta:
            lista.append(Auto(f'Inicia el {nombre.lower()}', p.fecha_inicio, 'PERIODO'))
        if desde <= p.fecha_fin <= hasta:
            lista.append(Auto(f'Termina el {nombre.lower()}', p.fecha_fin, 'PERIODO'))
        if p.cierre_notas and (rol.docente or rol.admin):
            c = timezone.localtime(p.cierre_notas)
            if desde <= c.date() <= hasta:
                lista.append(Auto(f'Cierre del ingreso de notas · {nombre}', c.date(), 'CIERRE',
                                  'La plataforma cierra sola el ingreso de notas a esta hora.', c.time(), 'DOCENTES'))
    return lista


def eventos_entre(colegio, rol, desde, hasta):
    todos = visibles(colegio, rol, desde, hasta) + automaticos(colegio, rol, desde, hasta)
    return sorted(todos, key=lambda e: (e.fecha, e.hora_inicio or datetime.time(0), e.titulo))


# ---------------------------------------------------------------------------
# Mes en cuadrícula
# ---------------------------------------------------------------------------
def mes(colegio, rol, ano, num_mes):
    cal = calendar.Calendar(firstweekday=0)
    semanas = cal.monthdatescalendar(ano, num_mes)
    desde, hasta = semanas[0][0], semanas[-1][-1]
    eventos = eventos_entre(colegio, rol, desde, hasta)
    por_dia = {}
    for e in eventos:
        d = max(e.fecha, desde)
        while d <= min(e.ultimo_dia, hasta):
            por_dia.setdefault(d, []).append(e)
            d += datetime.timedelta(days=1)
    hoy = timezone.localdate()
    return [[{'fecha': d, 'otro_mes': d.month != num_mes, 'hoy': d == hoy, 'eventos': por_dia.get(d, [])}
             for d in semana] for semana in semanas]


# ---------------------------------------------------------------------------
# Avisos
# ---------------------------------------------------------------------------
def destinatarios(evento):
    """Usuarios a quienes se avisa de un evento."""
    usuarios = set()
    colegio = evento.colegio
    if evento.para in ('TODOS', 'DOCENTES'):
        usuarios |= set(Docente.objects.filter(colegio=colegio, user__is_active=True).values_list('user_id', flat=True))
    if evento.para in ('TODOS', 'ESTUDIANTES'):
        est = Estudiante.objects.filter(colegio=colegio, is_active=True)
        cursos = list(evento.cursos.all())
        if cursos:
            est = est.filter(curso__in=cursos)
        usuarios |= set(est.values_list('user_id', flat=True))
    return usuarios


def texto_fecha(e):
    if e.fecha_fin and e.fecha_fin > e.fecha:
        t = f'del {e.fecha:%d/%m} al {e.fecha_fin:%d/%m}'
    else:
        t = f'el {e.fecha:%d/%m/%Y}'
    if e.hora_inicio:
        t += f' a las {e.hora_inicio:%H:%M}'
    return t


def avisar(evento, url, cambio=False):
    texto = f'{"Cambió" if cambio else "Calendario"}: {evento.titulo} {texto_fecha(evento)}'
    if evento.lugar:
        texto += f' · {evento.lugar}'
    avisos = [Notificacion(colegio=evento.colegio, destinatario_id=u, tipo='GENERAL', mensaje=texto[:255], url=url)
              for u in destinatarios(evento)]
    Notificacion.objects.bulk_create(avisos)
    return len(avisos)


# ---------------------------------------------------------------------------
# Google Calendar e iCal
# ---------------------------------------------------------------------------
def _fechas_google(e):
    if e.hora_inicio:
        ini = datetime.datetime.combine(e.fecha, e.hora_inicio)
        fin = datetime.datetime.combine(e.fecha, e.hora_fin) if e.hora_fin else ini + datetime.timedelta(hours=1)
        return f'{ini:%Y%m%dT%H%M%S}/{fin:%Y%m%dT%H%M%S}'
    fin = e.ultimo_dia + datetime.timedelta(days=1)
    return f'{e.fecha:%Y%m%d}/{fin:%Y%m%d}'


def enlace_google(e, colegio):
    datos = {'action': 'TEMPLATE', 'text': e.titulo, 'dates': _fechas_google(e),
             'details': (e.descripcion or '') + f'\n\n{colegio.nombre}', 'ctz': 'America/Bogota'}
    if e.lugar:
        datos['location'] = e.lugar
    return 'https://calendar.google.com/calendar/render?' + urlencode(datos)


def ficha_ics(user, colegio):
    return signing.Signer(salt=SAL_ICS).sign(f'{user.pk}.{colegio.pk}')


def leer_ficha(ficha):
    try:
        u, c = signing.Signer(salt=SAL_ICS).unsign(ficha).split('.')
        return int(u), int(c)
    except (signing.BadSignature, ValueError):
        return None


def _esc(t):
    return (t or '').replace('\\', '\\\\').replace(';', '\\;').replace(',', '\\,').replace('\r', '').replace('\n', '\\n')


def _linea(t):
    """Las líneas de iCal no deben pasar de 75 bytes."""
    b = t.encode('utf-8')
    if len(b) <= 75:
        return t
    partes, actual = [], b''
    for ch in t:
        cb = ch.encode('utf-8')
        if len(actual) + len(cb) > (75 if not partes else 74):
            partes.append(actual.decode('utf-8'))
            actual = b''
        actual += cb
    partes.append(actual.decode('utf-8'))
    return '\r\n '.join(partes)


def ics(colegio, eventos, host=''):
    sello = timezone.now().strftime('%Y%m%dT%H%M%SZ')
    lineas = ['BEGIN:VCALENDAR', 'VERSION:2.0', 'PRODID:-//mcolegio//Calendario escolar//ES', 'CALSCALE:GREGORIAN',
              'METHOD:PUBLISH', f'X-WR-CALNAME:{_esc(colegio.nombre)}', 'X-WR-TIMEZONE:America/Bogota']
    for i, e in enumerate(eventos):
        uid = f'evento-{e.pk}@{host or "mcolegio"}' if e.pk else f'auto-{e.tipo}-{e.fecha:%Y%m%d}-{i}@{host or "mcolegio"}'
        lineas += ['BEGIN:VEVENT', f'UID:{uid}', f'DTSTAMP:{sello}']
        if e.hora_inicio:
            ini = datetime.datetime.combine(e.fecha, e.hora_inicio)
            fin = datetime.datetime.combine(e.fecha, e.hora_fin) if e.hora_fin else ini + datetime.timedelta(hours=1)
            lineas += [f'DTSTART;TZID=America/Bogota:{ini:%Y%m%dT%H%M%S}', f'DTEND;TZID=America/Bogota:{fin:%Y%m%dT%H%M%S}']
        else:
            lineas += [f'DTSTART;VALUE=DATE:{e.fecha:%Y%m%d}',
                       f'DTEND;VALUE=DATE:{e.ultimo_dia + datetime.timedelta(days=1):%Y%m%d}']
        lineas.append(f'SUMMARY:{_esc(e.titulo)}')
        if e.descripcion:
            lineas.append(f'DESCRIPTION:{_esc(e.descripcion)}')
        if e.lugar:
            lineas.append(f'LOCATION:{_esc(e.lugar)}')
        lineas.append('END:VEVENT')
    lineas.append('END:VCALENDAR')
    return '\r\n'.join(_linea(x) for x in lineas) + '\r\n'
