"""Reemplazos y clases del día, a partir del horario publicado.

Todo aquí depende de que el colegio tenga un horario PUBLICADO. Si no lo tiene,
las funciones devuelven listas vacías y el resto de la plataforma sigue igual.
"""
import datetime

from notas.models import AsignacionDocente, Docente
from notas.models.comunicaciones import Notificacion

from . import cuadricula
from .models import Reemplazo, Sesion


def _min(t):
    return t.hour * 60 + t.minute


def _cruzan(a, b):
    """¿Las dos franjas se pisan en el tiempo? (pueden ser de jornadas distintas)."""
    return _min(a.inicio) < _min(b.fin) and _min(b.inicio) < _min(a.fin)


def _sesiones_del_dia(h, fecha):
    return list(Sesion.objects.filter(horario=h, dia=fecha.isoweekday(), asignacion__isnull=False)
                .select_related('franja', 'curso', 'asignacion__materia', 'asignacion__docente__user'))


def clases_de(h, docente, fecha):
    """Las clases que el docente tiene ese día en el horario publicado (por hora)."""
    if not h:
        return []
    ses = [s for s in _sesiones_del_dia(h, fecha) if s.asignacion.docente_id == docente.id]
    return sorted(ses, key=lambda s: (s.franja.inicio, s.curso.nombre))


def ausentes(colegio, fecha):
    return set(Reemplazo.objects.filter(colegio=colegio, fecha=fecha).values_list('ausente_id', flat=True))


def candidatos(h, sesion, fecha, colegio, todas=None):
    """Docentes libres a esa hora, ordenados: primero los que mejor encajan.

    Cuenta: está en el colegio ese día (tiene otras clases), dicta la misma
    materia, conoce el curso, y tiene menos clases ese día.
    """
    todas = todas if todas is not None else _sesiones_del_dia(h, fecha)
    faltan = ausentes(colegio, fecha) | {sesion.asignacion.docente_id}
    ocupados = {s.asignacion.docente_id for s in todas if _cruzan(s.franja, sesion.franja)}
    for r in Reemplazo.objects.filter(colegio=colegio, fecha=fecha, reemplazante__isnull=False).select_related('sesion__franja'):
        if r.sesion_id != sesion.id and _cruzan(r.sesion.franja, sesion.franja):
            ocupados.add(r.reemplazante_id)
    carga = {}
    for s in todas:
        carga[s.asignacion.docente_id] = carga.get(s.asignacion.docente_id, 0) + 1
    for d in Reemplazo.objects.filter(colegio=colegio, fecha=fecha, reemplazante__isnull=False).values_list('reemplazante_id', flat=True):
        carga[d] = carga.get(d, 0) + 1
    materia, curso = sesion.asignacion.materia_id, sesion.curso_id
    misma_materia = set(AsignacionDocente.objects.filter(colegio=colegio, materia_id=materia).values_list('docente_id', flat=True))
    mismo_curso = set(AsignacionDocente.objects.filter(colegio=colegio, curso_id=curso).values_list('docente_id', flat=True))
    lista = []
    for d in Docente.objects.filter(colegio=colegio, user__is_active=True).select_related('user'):
        if d.id in faltan or d.id in ocupados:
            continue
        razones, puntos = [], 0
        if carga.get(d.id):
            razones.append(f'está en el colegio ({carga[d.id]} clase{"s" if carga[d.id] != 1 else ""} ese día)')
            puntos += 4
        if d.id in misma_materia:
            razones.append('dicta la misma materia')
            puntos += 3
        if d.id in mismo_curso:
            razones.append('conoce el curso')
            puntos += 2
        puntos -= carga.get(d.id, 0) * 0.5
        lista.append({'docente': d, 'puntos': puntos, 'razones': razones, 'carga': carga.get(d.id, 0)})
    lista.sort(key=lambda x: (-x['puntos'], x['docente'].user.last_name))
    return lista


def plan_de_ausencia(colegio, docente, fecha):
    """Las clases del docente ese día, con el reemplazo (si ya hay) y los candidatos."""
    h = cuadricula.publicado(colegio)
    if not h:
        return None, []
    todas = _sesiones_del_dia(h, fecha)
    hechos = {r.sesion_id: r for r in Reemplazo.objects.filter(colegio=colegio, fecha=fecha, ausente=docente)
              .select_related('reemplazante__user')}
    filas = []
    for s in sorted((s for s in todas if s.asignacion.docente_id == docente.id), key=lambda s: s.franja.inicio):
        filas.append({'sesion': s, 'reemplazo': hechos.get(s.id),
                      'candidatos': candidatos(h, s, fecha, colegio, todas)[:8]})
    return h, filas


def avisar(reemplazo, url):
    """Notifica al docente que va a reemplazar."""
    if not reemplazo.reemplazante:
        return
    s = reemplazo.sesion
    texto = (f'Reemplazo el {reemplazo.fecha:%d/%m}: {s.curso.nombre} · {s.asignacion.materia.nombre}, '
             f'{s.franja.inicio:%H:%M}–{s.franja.fin:%H:%M} (por {reemplazo.ausente}).')
    if reemplazo.nota:
        texto = (texto + ' ' + reemplazo.nota)[:255]
    Notificacion.objects.create(colegio=reemplazo.colegio, destinatario=reemplazo.reemplazante.user,
                                tipo='GENERAL', mensaje=texto[:255], url=url)


# ---------------------------------------------------------------------------
# Para la toma de asistencia
# ---------------------------------------------------------------------------
def clases_de_hoy(colegio, docente, fecha):
    """Lo que el docente dicta ese día: sus clases (si no faltó) + los reemplazos que le tocan.

    Cada elemento: {'asignacion', 'curso', 'materia', 'inicio', 'fin', 'reemplazo'}.
    Vacío si no hay horario publicado.
    """
    h = cuadricula.publicado(colegio)
    if not h or not docente:
        return []
    lista = []
    cubiertas = set(Reemplazo.objects.filter(colegio=colegio, fecha=fecha, ausente=docente).values_list('sesion_id', flat=True))
    for s in clases_de(h, docente, fecha):
        if s.id in cubiertas:
            continue
        lista.append({'asignacion': s.asignacion, 'curso': s.curso, 'materia': s.asignacion.materia,
                      'inicio': s.franja.inicio, 'fin': s.franja.fin, 'reemplazo': None})
    for r in (Reemplazo.objects.filter(colegio=colegio, fecha=fecha, reemplazante=docente)
              .select_related('sesion__franja', 'sesion__curso', 'sesion__asignacion__materia', 'ausente__user')):
        s = r.sesion
        lista.append({'asignacion': s.asignacion, 'curso': s.curso, 'materia': s.asignacion.materia,
                      'inicio': s.franja.inicio, 'fin': s.franja.fin, 'reemplazo': r})
    lista.sort(key=lambda c: c['inicio'])
    return lista


def clase_en_curso(clases, ahora):
    """La clase que está pasando (o empieza en menos de 10 minutos)."""
    m = _min(ahora)
    for c in clases:
        if _min(c['inicio']) - 10 <= m < _min(c['fin']):
            return c
    return None


def puede_tomar_asistencia(colegio, docente, asignacion, fecha):
    """Un reemplazante puede tomar la asistencia de la clase que cubre ese día."""
    if not docente:
        return False
    return Reemplazo.objects.filter(colegio=colegio, fecha=fecha, reemplazante=docente,
                                    sesion__asignacion=asignacion).exists()


def reemplazos_proximos(colegio, docente, desde=None, dias=7):
    from django.utils import timezone
    desde = desde or timezone.localdate()
    return list(Reemplazo.objects.filter(colegio=colegio, reemplazante=docente, fecha__gte=desde,
                                         fecha__lte=desde + datetime.timedelta(days=dias))
                .select_related('sesion__franja', 'sesion__curso', 'sesion__asignacion__materia', 'ausente__user')
                .order_by('fecha', 'sesion__franja__inicio'))
