"""Quién puede hablar con quién en el chat del colegio y quién está en cada grupo.

  · Directivos (administradores del colegio): con todos los del colegio.
  · Docentes: con los demás docentes, los directivos y los estudiantes (y sus acudientes) de los cursos donde
    dictan clase o son directores de grupo.
  · Estudiante / acudiente (la misma cuenta): con los docentes de su curso, su director de grupo y los
    directivos. Nunca con otros estudiantes en privado.
"""
from django.contrib.auth.models import User
from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from notas.models import AdministradorColegio, AsignacionDocente, Curso, Docente, Estudiante

from .models import AjustesChat, Conversacion, Participante


def rol(user, colegio):
    """'admin', 'docente', 'estudiante' o None."""
    if user is None or not user.is_authenticated or colegio is None:
        return None
    if user.is_superuser or AdministradorColegio.objects.filter(user=user, colegio=colegio, activo=True).exists():
        return 'admin'
    if Docente.objects.filter(user=user, colegio=colegio).exists():
        return 'docente'
    if Estudiante.objects.filter(user=user, colegio=colegio, is_active=True).exists():
        return 'estudiante'
    return None


def _adultos(colegio):
    return User.objects.filter(Q(docente__colegio=colegio)
                               | Q(administraciones__colegio=colegio, administraciones__activo=True),
                               is_active=True, is_superuser=False)


def _cursos_del_docente(user, colegio):
    return Curso.objects.filter(Q(asignaciondocente__docente__user=user) | Q(director_grado__user=user),
                                colegio=colegio).distinct()


def contactos(user, colegio):
    """Usuarios con los que esta persona puede abrir una conversación uno a uno."""
    r = rol(user, colegio)
    if r is None:
        return User.objects.none()
    if r == 'admin':
        qs = _adultos(colegio) | User.objects.filter(estudiante__colegio=colegio, estudiante__is_active=True,
                                                     is_active=True)
    elif r == 'docente':
        cursos = _cursos_del_docente(user, colegio)
        qs = _adultos(colegio) | User.objects.filter(estudiante__colegio=colegio, estudiante__is_active=True,
                                                     estudiante__curso__in=cursos, is_active=True)
    else:
        est = Estudiante.objects.select_related('curso').get(user=user, colegio=colegio)
        qs = User.objects.filter(Q(administraciones__colegio=colegio, administraciones__activo=True)
                                 | Q(docente__asignaciondocente__curso=est.curso, docente__colegio=colegio)
                                 | Q(docente__cursos_dirigidos=est.curso, docente__colegio=colegio),
                                 is_active=True, is_superuser=False) if est.curso_id else \
            User.objects.filter(administraciones__colegio=colegio, administraciones__activo=True, is_active=True)
    return qs.exclude(pk=user.pk).distinct()


def puede_hablar(a, b, colegio):
    return contactos(a, colegio).filter(pk=b.pk).exists()


def nombre_de(user):
    return user.get_full_name() or user.username


def etiqueta(user, colegio):
    """Cómo se presenta alguien en el chat: «Docente», «Coordinación», «Estudiante · 601»."""
    adm = AdministradorColegio.objects.filter(user=user, colegio=colegio, activo=True).first()
    if adm:
        return adm.get_cargo_display()
    if Docente.objects.filter(user=user, colegio=colegio).exists():
        return 'Docente'
    est = Estudiante.objects.filter(user=user, colegio=colegio).select_related('curso').first()
    if est:
        return f'Estudiante o acudiente · {est.curso.nombre}' if est.curso_id else 'Estudiante o acudiente'
    return ''


# ---------------------------------------------------------------------------
# Conversaciones
# ---------------------------------------------------------------------------
@transaction.atomic
def directa(colegio, a, b):
    menor, mayor = sorted([a.pk, b.pk])
    conv, nueva = Conversacion.objects.get_or_create(colegio=colegio, clave=f'd:{menor}-{mayor}',
                                                     defaults={'tipo': 'directa', 'creada_por': a})
    if nueva:
        Participante.objects.bulk_create([Participante(conversacion=conv, usuario=a),
                                          Participante(conversacion=conv, usuario=b)])
    return conv


def _miembros_esperados(conv):
    """{user_id: moderador} de los grupos que se arman solos."""
    colegio = conv.colegio
    salida = {}
    if conv.tipo == 'curso' and conv.curso_id:
        for uid in Estudiante.objects.filter(curso=conv.curso, colegio=colegio, is_active=True,
                                             user__is_active=True).values_list('user_id', flat=True):
            salida[uid] = False
        for uid in AsignacionDocente.objects.filter(curso=conv.curso, colegio=colegio).values_list('docente__user_id', flat=True):
            salida[uid] = True
        if conv.curso.director_grado_id:
            salida[conv.curso.director_grado.user_id] = True
    elif conv.tipo == 'asignatura' and conv.asignacion_id:
        a = conv.asignacion
        for uid in Estudiante.objects.filter(curso=a.curso, colegio=colegio, is_active=True,
                                             user__is_active=True).values_list('user_id', flat=True):
            salida[uid] = False
        salida[a.docente.user_id] = True
    elif conv.tipo == 'profesores':
        for uid in _adultos(colegio).values_list('pk', flat=True):
            salida[uid] = False
        for uid in AdministradorColegio.objects.filter(colegio=colegio, activo=True).values_list('user_id', flat=True):
            salida[uid] = True
    return salida


@transaction.atomic
def sincronizar(conv):
    """Pone al día los grupos automáticos: entran los estudiantes nuevos del curso y salen los que se fueron."""
    if conv.tipo not in ('curso', 'asignatura', 'profesores'):
        return
    esperados = _miembros_esperados(conv)
    actuales = {p.usuario_id: p for p in conv.participantes.all()}
    nuevos = []
    for uid, mod in esperados.items():
        p = actuales.get(uid)
        if p is None:
            nuevos.append(Participante(conversacion=conv, usuario_id=uid, moderador=mod, ultimo_leido=timezone.now()))
        elif not p.activo or p.moderador != mod:
            p.activo, p.moderador = True, mod
            p.save(update_fields=['activo', 'moderador'])
    Participante.objects.bulk_create(nuevos)
    Participante.objects.filter(conversacion=conv, activo=True).exclude(usuario_id__in=list(esperados)) \
        .update(activo=False)


def grupo_curso(colegio, curso, quien):
    conv, _ = Conversacion.objects.get_or_create(colegio=colegio, clave=f'c:{curso.pk}', defaults={
        'tipo': 'curso', 'curso': curso, 'nombre': f'Curso {curso.nombre}', 'creada_por': quien})
    sincronizar(conv)
    return conv


def grupo_asignatura(colegio, asignacion, quien):
    conv, _ = Conversacion.objects.get_or_create(colegio=colegio, clave=f'a:{asignacion.pk}', defaults={
        'tipo': 'asignatura', 'asignacion': asignacion, 'curso': asignacion.curso, 'creada_por': quien,
        'nombre': f'{asignacion.materia.nombre} · {asignacion.curso.nombre}'[:80]})
    sincronizar(conv)
    return conv


def sala_profesores(colegio, quien):
    conv, _ = Conversacion.objects.get_or_create(colegio=colegio, clave='p', defaults={
        'tipo': 'profesores', 'nombre': 'Sala de profesores', 'creada_por': quien})
    sincronizar(conv)
    return conv


def grupos_disponibles(user, colegio):
    """Los grupos automáticos que esta persona puede abrir: [(tipo, objeto, nombre)]."""
    r = rol(user, colegio)
    salida = []
    if r in ('admin', 'docente'):
        salida.append(('profesores', None, 'Sala de profesores'))
        cursos = Curso.objects.filter(colegio=colegio).order_by('nombre') if r == 'admin' else \
            _cursos_del_docente(user, colegio).order_by('nombre')
        for c in cursos:
            salida.append(('curso', c, f'Curso {c.nombre}'))
        for a in AsignacionDocente.objects.filter(colegio=colegio, docente__user=user).select_related('materia', 'curso') \
                .order_by('curso__nombre', 'materia__nombre'):
            salida.append(('asignatura', a, f'{a.materia.nombre} · {a.curso.nombre}'))
    return salida


def participante(conv, user):
    return Participante.objects.filter(conversacion=conv, usuario=user, activo=True).first()


def puede_escribir(conv, p):
    return p is not None and (not conv.solo_lectura or p.moderador)


# ---------------------------------------------------------------------------
# Silencio y avisos
# ---------------------------------------------------------------------------
def ajustes(colegio):
    return AjustesChat.objects.get_or_create(colegio=colegio)[0]


def en_silencio(colegio, momento=None):
    a = ajustes(colegio)
    ahora = timezone.localtime(momento or timezone.now())
    if a.silencio_fin_de_semana and ahora.weekday() >= 5:
        return True
    hora = ahora.time()
    desde, hasta = a.silencio_desde, a.silencio_hasta
    if desde == hasta:
        return False
    if desde < hasta:
        return desde <= hora < hasta
    return hora >= desde or hora < hasta


def avisar(mensaje):
    """Una notificación por conversación (no una por mensaje) a quien no la tenga silenciada.
    En el horario de silencio no se avisa: el mensaje queda en el chat con su número rojo."""
    from notas.models import Notificacion
    conv = mensaje.conversacion
    if en_silencio(conv.colegio):
        return 0
    url = f'/chat/c/{conv.pk}/'
    destinos = list(Participante.objects.filter(conversacion=conv, activo=True, silenciada=False)
                    .exclude(usuario=mensaje.autor).values_list('usuario_id', flat=True))
    ya = set(Notificacion.objects.filter(destinatario_id__in=destinos, url=url, leido=False)
             .values_list('destinatario_id', flat=True))
    autor = nombre_de(mensaje.autor)
    icono = {'foto': '📷', 'voz': '🎤', 'doc': '📄'}.get(mensaje.tipo)
    contenido = (mensaje.nombre_archivo if mensaje.tipo == 'doc' else mensaje.texto) or \
        {'foto': 'Foto', 'voz': 'Nota de voz', 'doc': 'Documento'}.get(mensaje.tipo, '')
    if icono:
        contenido = f'{icono} {contenido}'
    texto = f'{autor}: {contenido}' if conv.tipo == 'directa' else f'{conv.nombre} · {autor}: {contenido}'
    nuevas = [Notificacion(colegio=conv.colegio, destinatario_id=uid, tipo='MENSAJE', url=url, mensaje=texto[:255])
              for uid in destinos if uid not in ya]
    Notificacion.objects.bulk_create(nuevas)
    return len(nuevas)
