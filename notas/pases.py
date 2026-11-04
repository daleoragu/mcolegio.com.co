"""Permisos de salida («pases»): dar, verificar con el carné, regreso y avisos.

* Lo da el docente del curso (o el director de grupo) o un directivo. La salida
  del colegio solo la da un directivo.
* Cualquier docente o directivo lo verifica escaneando el carné: con permiso,
  vencido o sin permiso (posible evasión, con aviso al director y a coordinación).
* Si quien lo da no es el docente que tiene al curso en ese momento (según el
  horario publicado), a ese docente le llega el aviso.
"""
from datetime import datetime, time, timedelta

from django.utils import timezone

from .models import AdministradorColegio, AsignacionDocente, Docente, Notificacion, PermisoSalida, VerificacionPermiso

MAX_MINUTOS = 120
VARIOS_FUERA = 2          # desde cuántos del mismo curso afuera se advierte


def es_personal(request):
    """Docente o directivo del colegio (los que dan y verifican permisos)."""
    from .permisos import es_admin
    return es_admin(request) or Docente.objects.filter(user=request.user, colegio=request.colegio).exists()


def puede_dar(request, estudiante, destino):
    from .permisos import es_admin
    if estudiante.colegio_id != request.colegio.id:
        return False, 'Ese estudiante no es de este colegio.'
    if es_admin(request):
        return True, ''
    if PermisoSalida.DESTINOS.get(destino, ('', 0, False))[2]:
        return False, 'La salida del colegio la autoriza un directivo.'
    docente = Docente.objects.filter(user=request.user, colegio=request.colegio).first()
    if docente is None:
        return False, 'Los permisos los dan los docentes y los directivos.'
    curso = estudiante.curso_id
    if curso and (AsignacionDocente.objects.filter(docente=docente, curso_id=curso).exists()
                  or estudiante.curso.director_grado_id == docente.id):
        return True, ''
    try:
        from horarios import reemplazos
        if any(c['curso'].id == curso for c in reemplazos.clases_de_hoy(request.colegio, docente, timezone.localdate())):
            return True, ''
    except Exception:
        pass
    return False, 'Solo el docente del curso, su director de grupo o un directivo dan este permiso.'


def abierto_de(estudiante):
    """El permiso que el estudiante tiene abierto (aunque esté vencido), o None."""
    return (PermisoSalida.objects.filter(estudiante=estudiante, regreso__isnull=True, anulado=False,
                                         inicio__date=timezone.localdate())
            .select_related('otorgado_por', 'asignacion__materia').first())


def vence_para(destino, minutos, ahora=None):
    ahora = ahora or timezone.now()
    if destino == 'SALIDA':
        fin = datetime.combine(timezone.localdate(), time(23, 59))
        return timezone.make_aware(fin) if timezone.is_naive(fin) else fin
    try:
        minutos = int(minutos)
    except (TypeError, ValueError):
        minutos = PermisoSalida.DESTINOS.get(destino, ('', 15, False))[1]
    return ahora + timedelta(minutes=max(1, min(MAX_MINUTOS, minutos)))


def clase_actual_del_curso(colegio, curso, ahora=None):
    """La clase que tiene el curso en este momento según el horario publicado: {'asignacion', 'docente', …} o None."""
    if curso is None:
        return None
    try:
        from horarios import reemplazos
        from .modulos import esta_activo
        if not esta_activo(colegio, 'horarios'):
            return None
        ahora = timezone.localtime(ahora or timezone.now())
        docentes = {a.docente for a in AsignacionDocente.objects.filter(colegio=colegio, curso=curso, docente__isnull=False)
                    .select_related('docente__user')}
        for d in docentes:
            for c in reemplazos.clases_de_hoy(colegio, d, ahora.date()):
                if c['curso'].id == curso.id and reemplazos.clase_en_curso([c], ahora.time()):
                    return dict(c, docente=c['reemplazo'].reemplazante if c['reemplazo'] else d)
    except Exception:
        return None
    return None


def fuera_del_curso(curso):
    """Los permisos abiertos hoy del curso (los que están fuera del salón)."""
    return list(PermisoSalida.objects.filter(estudiante__curso=curso, regreso__isnull=True, anulado=False,
                                             inicio__date=timezone.localdate())
                .select_related('estudiante__user', 'otorgado_por').order_by('inicio'))


def dar(request, estudiante, destino, minutos=None, nota='', asignacion=None):
    """Crea el permiso. Devuelve (permiso, advertencia)."""
    destino = destino if destino in PermisoSalida.DESTINOS else 'OTRO'
    p = PermisoSalida.objects.create(
        colegio=request.colegio, estudiante=estudiante, otorgado_por=request.user, asignacion=asignacion,
        destino=destino, nota=(nota or '').strip()[:200], vence=vence_para(destino, minutos))
    nombre = estudiante.user.get_full_name() or estudiante.user.username
    hora = timezone.localtime(p.vence).strftime('%I:%M %p')
    Notificacion.objects.create(
        colegio=request.colegio, destinatario=estudiante.user, tipo='GENERAL', url='/mi-carne/',
        mensaje=(f'🚪 Tienes permiso: {p.get_destino_display()}' +
                 ('' if destino == 'SALIDA' else f' hasta las {hora}'))[:255])
    clase = clase_actual_del_curso(request.colegio, estudiante.curso)
    if clase and clase['docente'] and clase['docente'].user_id != request.user.id:
        quien = request.user.get_full_name() or request.user.username
        Notificacion.objects.create(
            colegio=request.colegio, destinatario=clase['docente'].user, tipo='GENERAL', url='/permisos/',
            mensaje=f'🚪 {nombre} ({estudiante.curso.nombre}) salió de su clase: {p.get_destino_display()} '
                    f'(permiso de {quien})'[:255])
    otros = [x for x in fuera_del_curso(estudiante.curso) if x.pk != p.pk] if estudiante.curso_id else []
    aviso = (f'Ojo: ya hay {len(otros)} estudiante(s) de {estudiante.curso.nombre} fuera del salón.'
             if len(otros) >= VARIOS_FUERA else '')
    return p, aviso


def marcar_regreso(permiso, usuario):
    if permiso.abierto:
        permiso.regreso, permiso.regreso_marcado_por = timezone.now(), usuario
        permiso.save(update_fields=['regreso', 'regreso_marcado_por'])


def verificar(request, estudiante):
    """Lo que ve quien escanea el carné. Deja el registro. Devuelve (verificación, permiso, clase actual)."""
    p = abierto_de(estudiante)
    resultado = 'SIN_PERMISO' if p is None else ('VENCIDO' if p.vencido else 'CON_PERMISO')
    v = VerificacionPermiso.objects.create(colegio=request.colegio, estudiante=estudiante, permiso=p,
                                           verificado_por=request.user, resultado=resultado)
    return v, p, clase_actual_del_curso(request.colegio, estudiante.curso)


def reportar(request, verificacion):
    """Avisa al director de grupo y a coordinación de una posible evasión de clase."""
    est = verificacion.estudiante
    destinos = {}
    admins = AdministradorColegio.objects.filter(colegio=request.colegio, activo=True).select_related('user')
    coords = [a.user for a in admins if a.cargo == 'COORDINADOR'] or [a.user for a in admins]
    for u in coords:
        destinos[u.id] = u
    if est.curso_id and est.curso.director_grado_id:
        destinos[est.curso.director_grado.user_id] = est.curso.director_grado.user
    quien = request.user.get_full_name() or request.user.username
    hora = timezone.localtime(verificacion.momento).strftime('%I:%M %p')
    texto = ('sin permiso' if verificacion.resultado == 'SIN_PERMISO' else 'con el permiso vencido')
    Notificacion.objects.bulk_create([
        Notificacion(colegio=request.colegio, destinatario=u, tipo='GENERAL', url='/permisos/historial/',
                     mensaje=f'⚠️ Posible evasión: {est} ({est.curso.nombre if est.curso_id else ""}) estaba fuera '
                             f'de clase {texto} a las {hora}. Lo vio {quien}.'[:255])
        for uid, u in destinos.items() if uid != request.user.id])
    verificacion.reportado = True
    verificacion.save(update_fields=['reportado'])
    return len(destinos)
