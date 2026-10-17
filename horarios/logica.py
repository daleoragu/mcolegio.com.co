"""Publicar un horario y avisar."""
from django.db import transaction
from django.utils import timezone

from notas.models import Estudiante
from notas.models.comunicaciones import Notificacion

from .models import Horario, Sesion


def destinatarios(horario):
    """Usuarios de los docentes y estudiantes que tienen clases en este horario."""
    ses = Sesion.objects.filter(horario=horario)
    docentes = set(ses.values_list('asignacion__docente__user_id', flat=True)) - {None}
    cursos = set(ses.values_list('curso_id', flat=True))
    estudiantes = set(Estudiante.objects.filter(curso_id__in=cursos, is_active=True).values_list('user_id', flat=True))
    return docentes, estudiantes


def publicar(horario, url_mi_horario):
    """Lo deja como el horario oficial (archiva el anterior) y avisa. Devuelve cuántos avisos."""
    colegio = horario.colegio
    anterior = Horario.objects.filter(colegio=colegio, estado='PUBLICADO').exclude(pk=horario.pk).first()
    with transaction.atomic():
        Horario.objects.filter(colegio=colegio, estado='PUBLICADO').exclude(pk=horario.pk).update(estado='ARCHIVADO')
        horario.estado = 'PUBLICADO'
        horario.publicado_en = timezone.now()
        horario.save(update_fields=['estado', 'publicado_en'])
        docentes, estudiantes = destinatarios(horario)
        if anterior:
            cambiaron = _docentes_con_cambios(anterior, horario)
            texto_doc = 'Su horario de clases cambió. Revise el nuevo horario.'
        else:
            cambiaron = docentes
            texto_doc = 'Ya está publicado su horario de clases.'
        texto_est = 'Se publicó el nuevo horario de clases.' if anterior else 'Ya está publicado el horario de clases de su curso.'
        avisos = [Notificacion(colegio=colegio, destinatario_id=u, tipo='GENERAL', mensaje=texto_doc, url=url_mi_horario)
                  for u in (cambiaron & docentes)]
        avisos += [Notificacion(colegio=colegio, destinatario_id=u, tipo='GENERAL', mensaje=texto_est, url=url_mi_horario)
                   for u in estudiantes]
        Notificacion.objects.bulk_create(avisos)
    return len(avisos)


def _docentes_con_cambios(viejo, nuevo):
    def mapa(h):
        m = {}
        for doc, curso, asig, dia, franja in Sesion.objects.filter(horario=h).values_list(
                'asignacion__docente__user_id', 'curso_id', 'asignacion_id', 'dia', 'franja_id'):
            m.setdefault(doc, set()).add((curso, asig, dia, franja))
        return m
    a, b = mapa(viejo), mapa(nuevo)
    return {u for u in set(a) | set(b) if u and a.get(u) != b.get(u)}
