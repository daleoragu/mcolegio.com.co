"""Módulo Permisos: dar el pase de salida, verificar (carné o búsqueda), regreso e historial."""
from datetime import timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.http import HttpResponseForbidden, HttpResponseNotFound, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from .. import pases
from ..models import AsignacionDocente, Docente, Estudiante, PermisoSalida, VerificacionPermiso
from ..permisos import es_admin
from .carnet_views import codigo_leido


def _solo_personal(vista):
    @login_required
    def envoltura(request, *args, **kwargs):
        if not getattr(request, 'colegio', None):
            return HttpResponseNotFound('<h1>Colegio no configurado</h1>')
        if not pases.es_personal(request):
            return HttpResponseForbidden('Los permisos los manejan los docentes y los directivos.')
        return vista(request, *args, **kwargs)
    envoltura.__name__ = vista.__name__
    return envoltura


def _clases_del_docente(request):
    docente = Docente.objects.filter(user=request.user, colegio=request.colegio).first()
    asignaciones = list(AsignacionDocente.objects.filter(colegio=request.colegio, docente=docente)
                        .select_related('materia', 'curso').order_by('curso__nombre')) if docente else []
    ahora = None
    try:
        from horarios import reemplazos
        from ..modulos import esta_activo
        if docente and esta_activo(request.colegio, 'horarios'):
            clases = reemplazos.clases_de_hoy(request.colegio, docente, timezone.localdate())
            ahora = reemplazos.clase_en_curso(clases, timezone.localtime().time())
            if ahora and ahora['asignacion'].id not in {a.id for a in asignaciones}:
                asignaciones.append(ahora['asignacion'])
    except Exception:
        pass
    return docente, asignaciones, ahora


def _datos_permiso(p):
    return {'id': p.pk, 'destino': p.get_destino_display(), 'otorgado_por': (p.otorgado_por.get_full_name() or
                                                                            p.otorgado_por.username) if p.otorgado_por else '',
            'inicio': timezone.localtime(p.inicio).strftime('%I:%M %p'),
            'vence': '' if p.destino == 'SALIDA' else timezone.localtime(p.vence).strftime('%I:%M %p'),
            'restantes': p.minutos_restantes, 'vencido_hace': p.minutos_vencido, 'fuera': p.minutos_fuera,
            'nota': p.nota}


def _resultado(request, est):
    v, p, clase = pases.verificar(request, est)
    return {
        'verificacion': v.pk, 'resultado': v.resultado, 'nombre': est.user.get_full_name() or est.user.username,
        'curso': est.curso.nombre if est.curso_id else '', 'estudiante': est.pk,
        'permiso': _datos_permiso(p) if p else None,
        'clase': (f"{clase['materia'].nombre} con {clase['docente'].user.get_full_name()}" if clase else ''),
        'foto': est.ficha.foto.url if hasattr(est, 'ficha') and est.ficha.foto else '',
    }


@_solo_personal
def inicio(request):
    """Dar permisos (a los de su clase), verificar, y ver quién está fuera del salón."""
    admin = es_admin(request)
    docente, asignaciones, ahora = _clases_del_docente(request)
    aid = request.GET.get('asignacion') or (str(ahora['asignacion'].id) if ahora else '')
    asignacion = next((a for a in asignaciones if str(a.id) == aid), None)
    estudiantes = []
    if asignacion:
        abiertos = {p.estudiante_id: p for p in pases.fuera_del_curso(asignacion.curso)}
        for e in (Estudiante.objects.filter(colegio=request.colegio, curso=asignacion.curso, is_active=True)
                  .select_related('user').order_by('user__last_name', 'user__first_name')):
            e.permiso = abiertos.get(e.id)
            estudiantes.append(e)
    # Fuera del salón: los cursos del docente; la administración ve todo el colegio.
    hoy = PermisoSalida.objects.filter(colegio=request.colegio, regreso__isnull=True, anulado=False,
                                       inicio__date=timezone.localdate()).select_related(
        'estudiante__user', 'estudiante__curso', 'otorgado_por')
    if not admin:
        cursos = {a.curso_id for a in asignaciones} | set(docente.cursos_dirigidos.values_list('id', flat=True))
        hoy = hoy.filter(estudiante__curso_id__in=cursos)
    return render(request, 'notas/permisos/inicio.html', {
        'admin': admin, 'asignaciones': asignaciones, 'asignacion': asignacion, 'ahora': ahora,
        'estudiantes': estudiantes, 'fuera': list(hoy.order_by('vence')),
        'destinos': [(k, v[0], v[1], v[2]) for k, v in PermisoSalida.DESTINOS.items()]})


@_solo_personal
@require_POST
def dar(request):
    est = get_object_or_404(Estudiante.objects.select_related('user', 'curso'), pk=request.POST.get('estudiante') or 0,
                            colegio=request.colegio, is_active=True)
    destino = request.POST.get('destino') or 'BANO'
    volver = request.POST.get('volver') or '/permisos/'
    if not volver.startswith('/'):
        volver = '/permisos/'
    ok, error = pases.puede_dar(request, est, destino)
    if not ok:
        messages.error(request, error)
        return redirect(volver)
    if pases.abierto_de(est):
        messages.warning(request, f'{est} ya tiene un permiso abierto. Márquele el regreso antes de darle otro.')
        return redirect(volver)
    asignacion = AsignacionDocente.objects.filter(pk=request.POST.get('asignacion') or 0, colegio=request.colegio,
                                                  curso_id=est.curso_id).first()
    p, aviso = pases.dar(request, est, destino, request.POST.get('minutos'), request.POST.get('nota'), asignacion)
    texto = f'Permiso para {est}: {p.get_destino_display()}'
    if p.destino != 'SALIDA':
        texto += f' hasta las {timezone.localtime(p.vence):%I:%M %p}'
    messages.success(request, texto + '.')
    if aviso:
        messages.warning(request, aviso)
    return redirect(volver)


@_solo_personal
@require_POST
def regreso(request, pk):
    p = get_object_or_404(PermisoSalida, pk=pk, colegio=request.colegio)
    if request.POST.get('accion') == 'anular' and (es_admin(request) or p.otorgado_por_id == request.user.id):
        p.anulado = True
        p.save(update_fields=['anulado'])
        messages.info(request, 'Permiso anulado.')
    else:
        pases.marcar_regreso(p, request.user)
        messages.success(request, f'{p.estudiante} regresó ({p.minutos_fuera} min fuera).')
    volver = request.POST.get('volver') or '/permisos/'
    return redirect(volver if volver.startswith('/') else '/permisos/')


@_solo_personal
@require_POST
def verificar(request):
    """Lo que leyó la cámara (o el estudiante escogido en la búsqueda). Responde el estado del permiso."""
    est = None
    if request.POST.get('estudiante'):
        est = Estudiante.objects.filter(pk=request.POST['estudiante'], colegio=request.colegio).select_related('user', 'curso').first()
    else:
        codigo = codigo_leido(request.POST.get('texto'))
        if codigo:
            est = Estudiante.objects.filter(codigo_carnet=codigo, colegio=request.colegio).select_related('user', 'curso').first()
    if est is None:
        return JsonResponse({'resultado': 'NO_ENCONTRADO', 'mensaje': 'Ese QR no es de un carné de estudiante del colegio.'})
    return JsonResponse(_resultado(request, est))


@_solo_personal
def buscar(request):
    """Buscar al estudiante por nombre (sin carné)."""
    q = ' '.join((request.GET.get('q') or '').split())
    if len(q) < 2:
        return JsonResponse({'estudiantes': []})
    filtro = Q()
    for palabra in q.split()[:4]:
        filtro &= Q(user__first_name__icontains=palabra) | Q(user__last_name__icontains=palabra) | \
            Q(ficha__numero_documento__icontains=palabra)
    abiertos = set(PermisoSalida.objects.filter(colegio=request.colegio, regreso__isnull=True, anulado=False,
                                                inicio__date=timezone.localdate()).values_list('estudiante_id', flat=True))
    lista = (Estudiante.objects.filter(filtro, colegio=request.colegio, is_active=True).select_related('user', 'curso')
             .order_by('user__last_name', 'user__first_name')[:12])
    return JsonResponse({'estudiantes': [
        {'id': e.pk, 'nombre': f'{e.user.last_name} {e.user.first_name}'.strip() or e.user.username,
         'curso': e.curso.nombre if e.curso_id else '', 'con_permiso': e.pk in abiertos} for e in lista]})


@_solo_personal
@require_POST
def reportar(request, pk):
    v = get_object_or_404(VerificacionPermiso.objects.select_related('estudiante__curso__director_grado'),
                          pk=pk, colegio=request.colegio, verificado_por=request.user)
    if v.resultado == 'CON_PERMISO':
        return JsonResponse({'ok': False, 'mensaje': 'Tiene permiso vigente.'})
    if not v.reportado:
        pases.reportar(request, v)
    return JsonResponse({'ok': True, 'mensaje': 'Listo: se avisó al director de grupo y a coordinación.'})


@_solo_personal
def historial(request):
    """Permisos del día (o de una fecha) y quiénes salen más. Para directivos y directores de grupo."""
    admin = es_admin(request)
    docente = Docente.objects.filter(user=request.user, colegio=request.colegio).first()
    cursos = None if admin else list(docente.cursos_dirigidos.values_list('id', flat=True)) if docente else []
    if cursos == []:
        return HttpResponseForbidden('El historial lo ven los directivos y los directores de grupo.')
    try:
        from datetime import date
        dia = date.fromisoformat(request.GET.get('fecha') or '')
    except ValueError:
        dia = timezone.localdate()
    qs = PermisoSalida.objects.filter(colegio=request.colegio).select_related(
        'estudiante__user', 'estudiante__curso', 'otorgado_por', 'regreso_marcado_por')
    vs = VerificacionPermiso.objects.filter(colegio=request.colegio).exclude(resultado='CON_PERMISO').select_related(
        'estudiante__user', 'estudiante__curso', 'verificado_por')
    if cursos is not None:
        qs = qs.filter(estudiante__curso_id__in=cursos)
        vs = vs.filter(estudiante__curso_id__in=cursos)
    desde = timezone.localdate() - timedelta(days=30)
    mas = (qs.filter(inicio__date__gte=desde, anulado=False).values('estudiante', 'estudiante__user__first_name',
                                                                   'estudiante__user__last_name', 'estudiante__curso__nombre')
           .annotate(n=Count('id')).order_by('-n')[:10])
    return render(request, 'notas/permisos/historial.html', {
        'dia': dia, 'permisos': qs.filter(inicio__date=dia), 'sin_permiso': vs.filter(momento__date=dia),
        'mas': [m for m in mas if m['n'] >= 2]})


def verificacion_desde_carne(request, estudiante):
    """El docente o directivo abrió el QR del carné con la cámara del celular: ve el estado del permiso."""
    return render(request, 'notas/permisos/verificacion.html', {'r': _resultado(request, estudiante)})
