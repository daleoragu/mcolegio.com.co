"""Excusas de las fallas: plazo, quién aprueba y qué pasa con la asistencia.

Al aprobar, cada día hábil del rango queda «ausente con excusa» (Asistencia con
estado A, justificada y con la excusa) en todas las clases del curso. Si ese día
el estudiante ya había quedado presente o tarde en una clase, eso no se toca:
asistió. Mientras la excusa siga aprobada el docente no puede cambiar esos días.
"""
from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from .models import AdministradorColegio, AsignacionDocente, Asistencia, Excusa, Notificacion

MAX_DIAS = 60      # una excusa no cubre más de dos meses


def dias_habiles(desde, hasta):
    """Lunes a viernes entre las dos fechas, incluidas."""
    dia, salida = desde, []
    while dia <= hasta:
        if dia.weekday() < 5:
            salida.append(dia)
        dia += timedelta(days=1)
    return salida


def fecha_limite(colegio, desde):
    """Último día para enviar la excusa de una falla que empezó «desde» (None = sin plazo)."""
    plazo = getattr(colegio, 'dias_plazo_excusa', 3)
    if not plazo:
        return None
    dia, contados = desde, 0
    while contados < plazo:
        dia += timedelta(days=1)
        if dia.weekday() < 5:
            contados += 1
    return dia


def validar_fechas(colegio, desde, hasta, hoy=None, con_plazo=True):
    """'' si están bien; si no, el motivo."""
    hoy = hoy or timezone.localdate()
    if desde is None or hasta is None:
        return 'Escoja las fechas de la falla.'
    if hasta < desde:
        return 'La fecha «hasta» va después de «desde».'
    if (hasta - desde).days + 1 > MAX_DIAS:
        return f'Una excusa cubre máximo {MAX_DIAS} días.'
    if desde > hoy + timedelta(days=MAX_DIAS):
        return 'Esa fecha está muy lejos.'
    if not dias_habiles(desde, hasta):
        return 'Esas fechas caen en fin de semana: no hay clases.'
    if con_plazo:
        limite = fecha_limite(colegio, desde)
        if limite is not None and hoy > limite:
            return (f'El plazo para enviar esta excusa venció el {limite:%d/%m/%Y} '
                    f'({colegio.dias_plazo_excusa} días hábiles después de la falla). Comuníquese con la coordinación.')
    return ''


# ---------------------------------------------------------------------------
# Quién la recibe y quién la aprueba
# ---------------------------------------------------------------------------
def coordinadores(colegio):
    """Usuarios de la coordinación; si el colegio no tiene, toda la administración."""
    admins = AdministradorColegio.objects.filter(colegio=colegio, activo=True).select_related('user')
    coords = [a.user for a in admins if a.cargo == 'COORDINADOR']
    return coords or [a.user for a in admins]


def destinatarios(excusa):
    usuarios = {u.id: u for u in coordinadores(excusa.colegio)}
    curso = excusa.estudiante.curso
    if curso is not None and curso.director_grado_id:
        usuarios[curso.director_grado.user_id] = curso.director_grado.user
    return list(usuarios.values())


def puede_aprobar(request, excusa):
    from .permisos import es_admin
    if excusa.colegio_id != getattr(request.colegio, 'id', None):
        return False
    if es_admin(request):
        return True
    curso = excusa.estudiante.curso
    return bool(curso and curso.director_grado_id and curso.director_grado.user_id == request.user.id)


def avisar(usuarios, colegio, mensaje, url):
    Notificacion.objects.bulk_create([
        Notificacion(colegio=colegio, destinatario=u, tipo='GENERAL', mensaje=mensaje[:255], url=url)
        for u in usuarios if u is not None])


# ---------------------------------------------------------------------------
# Aprobar, rechazar, anular
# ---------------------------------------------------------------------------
@transaction.atomic
def aprobar(excusa, usuario, desde, hasta, respuesta=''):
    """Marca los días como ausente con excusa en todas las clases. Devuelve cuántas fallas quedaron justificadas."""
    est = excusa.estudiante
    asignaciones = list(AsignacionDocente.objects.filter(colegio=excusa.colegio, curso_id=est.curso_id))
    creadas, justificadas = [], 0
    for dia in dias_habiles(desde, hasta):
        for asig in asignaciones:
            a = Asistencia.objects.filter(estudiante=est, asignacion=asig, fecha=dia).first()
            if a is None:
                a = Asistencia.objects.create(colegio=excusa.colegio, estudiante=est, asignacion=asig, fecha=dia,
                                              estado='A', justificada=True, excusa=excusa)
                creadas.append(a.id)
                justificadas += 1
            elif a.estado == 'A':
                a.justificada, a.excusa = True, excusa
                a.save(update_fields=['justificada', 'excusa'])
                justificadas += 1
            # Presente o tarde: asistió a esa clase, se deja igual.
    excusa.estado = 'APROBADA'
    excusa.revisada_por, excusa.revisada_en = usuario, timezone.now()
    excusa.aprobada_desde, excusa.aprobada_hasta = desde, hasta
    excusa.respuesta = (respuesta or '').strip()[:500]
    excusa.asistencias_creadas = creadas
    excusa.save()
    return justificadas


@transaction.atomic
def rechazar(excusa, usuario, respuesta):
    excusa.estado = 'RECHAZADA'
    excusa.revisada_por, excusa.revisada_en = usuario, timezone.now()
    excusa.respuesta = (respuesta or '').strip()[:500]
    excusa.save()


@transaction.atomic
def anular(excusa, usuario, respuesta=''):
    """Deshace la aprobación: los días que creó la excusa se borran; las fallas que ya estaban vuelven a ser sin excusa."""
    Asistencia.objects.filter(id__in=excusa.asistencias_creadas or [], excusa=excusa).delete()
    Asistencia.objects.filter(excusa=excusa).update(justificada=False, excusa=None)
    excusa.estado = 'ANULADA'
    excusa.revisada_por, excusa.revisada_en = usuario, timezone.now()
    if respuesta:
        excusa.respuesta = respuesta.strip()[:500]
    excusa.asistencias_creadas = []
    excusa.save()


def docentes_del_curso(excusa):
    return [a.docente.user for a in AsignacionDocente.objects.filter(
        colegio=excusa.colegio, curso_id=excusa.estudiante.curso_id, docente__isnull=False).select_related('docente__user')
        .distinct()]
