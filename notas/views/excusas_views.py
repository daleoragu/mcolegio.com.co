"""Excusas de las fallas: el estudiante o su familia la envía; el director de grupo o la coordinación la aprueba."""
from datetime import date, timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import Http404, HttpResponseForbidden, HttpResponseNotFound
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone

from .. import excusas as EX
from ..models import Asistencia, Docente, Estudiante, Excusa
from ..permisos import es_admin

MAX_SOPORTE_MB = 8
EXTENSIONES = ('.pdf', '.jpg', '.jpeg', '.png', '.webp', '.heic')


def _fecha(texto):
    try:
        return date.fromisoformat((texto or '').strip())
    except ValueError:
        return None


def _leer_soporte(request, excusa):
    archivo = request.FILES.get('soporte')
    if not archivo:
        return ''
    if archivo.size > MAX_SOPORTE_MB * 1024 * 1024:
        return f'El soporte pasa de {MAX_SOPORTE_MB} MB. Tómele una foto más liviana.'
    if not archivo.name.lower().endswith(EXTENSIONES):
        return 'El soporte debe ser una foto (JPG, PNG) o un PDF.'
    excusa.soporte.save(archivo.name, archivo, save=False)
    excusa.nombre_soporte = archivo.name[:150]
    return ''


def _url(request, nombre, *args):
    return request.build_absolute_uri(reverse(nombre, args=args))


def _crear(request, estudiante, con_plazo):
    """Lee el formulario y guarda la excusa. Devuelve (excusa, error)."""
    desde, hasta = _fecha(request.POST.get('desde')), _fecha(request.POST.get('hasta'))
    if hasta is None:
        hasta = desde
    error = EX.validar_fechas(request.colegio, desde, hasta, con_plazo=con_plazo)
    if error:
        return None, error
    motivo = request.POST.get('motivo')
    excusa = Excusa(colegio=request.colegio, estudiante=estudiante, enviada_por=request.user,
                    motivo=motivo if motivo in dict(Excusa.MOTIVOS) else 'OTRO', desde=desde, hasta=hasta,
                    explicacion=(request.POST.get('explicacion') or '').strip()[:1500])
    limite = EX.fecha_limite(request.colegio, desde)
    excusa.fuera_de_plazo = bool(limite and timezone.localdate() > limite)
    error = _leer_soporte(request, excusa)
    if error:
        return None, error
    if excusa.motivo == 'OTRO' and not excusa.explicacion:
        return None, 'Cuente brevemente el motivo de la falla.'
    excusa.save()
    nombre = estudiante.user.get_full_name() or estudiante.user.username
    curso = estudiante.curso.nombre if estudiante.curso_id else ''
    EX.avisar(EX.destinatarios(excusa), request.colegio,
              f'📝 Excusa para revisar: {nombre} ({curso}), {excusa.desde:%d/%m}'
              + (f' a {excusa.hasta:%d/%m}' if excusa.hasta != excusa.desde else ''),
              _url(request, 'notas:excusa', excusa.pk))
    return excusa, ''


# ---------------------------------------------------------------------------
# Estudiante (o su familia, con la cuenta del estudiante)
# ---------------------------------------------------------------------------
@login_required
def mis_excusas(request):
    if not request.colegio:
        return HttpResponseNotFound('<h1>Colegio no configurado</h1>')
    estudiante = Estudiante.objects.filter(user=request.user, colegio=request.colegio).select_related('curso').first()
    if estudiante is None:
        return HttpResponseForbidden('Esta página es para los estudiantes y sus familias.')
    if request.method == 'POST':
        excusa, error = _crear(request, estudiante, con_plazo=True)
        if error:
            messages.error(request, error)
        else:
            messages.success(request, 'Excusa enviada. El director de grupo y la coordinación la revisan y le avisamos.')
            return redirect('notas:mis_excusas')
    hoy = timezone.localdate()
    hace = hoy - timedelta(days=45)
    fallas = (Asistencia.objects.filter(estudiante=estudiante, estado='A', fecha__gte=hace)
              .select_related('asignacion__materia').order_by('-fecha'))
    por_dia = {}
    for f in fallas:
        por_dia.setdefault(f.fecha, {'fecha': f.fecha, 'materias': [], 'justificada': True})
        por_dia[f.fecha]['materias'].append(f.asignacion.materia.nombre)
        por_dia[f.fecha]['justificada'] &= f.justificada
    return render(request, 'notas/estudiante/mis_excusas.html', {
        'estudiante': estudiante, 'excusas': estudiante.excusas.select_related('revisada_por')[:30],
        'motivos': Excusa.MOTIVOS, 'hoy': hoy, 'plazo': request.colegio.dias_plazo_excusa,
        'fallas': list(por_dia.values())[:15], 'valores': request.POST if request.method == 'POST' else {}})


# ---------------------------------------------------------------------------
# Director de grupo y coordinación
# ---------------------------------------------------------------------------
def _cursos_que_revisa(request):
    """None = todos (administración); si no, los cursos que dirige el docente."""
    if es_admin(request):
        return None
    docente = Docente.objects.filter(user=request.user, colegio=request.colegio).first()
    if docente is None:
        return []
    return list(docente.cursos_dirigidos.values_list('id', flat=True))


def _excusas_visibles(request):
    qs = Excusa.objects.filter(colegio=request.colegio).select_related('estudiante__user', 'estudiante__curso',
                                                                         'revisada_por')
    cursos = _cursos_que_revisa(request)
    if cursos is not None:
        qs = qs.filter(estudiante__curso_id__in=cursos)
    return qs, cursos


def pendientes_de(request):
    """Cuántas excusas esperan a esta persona (para el globo del panel)."""
    if not getattr(request, 'colegio', None) or not request.user.is_authenticated:
        return 0
    qs, cursos = _excusas_visibles(request)
    if cursos == []:
        return 0
    return qs.filter(estado='PENDIENTE').count()


@login_required
def bandeja(request):
    if not request.colegio:
        return HttpResponseNotFound('<h1>Colegio no configurado</h1>')
    qs, cursos = _excusas_visibles(request)
    if cursos == []:
        return HttpResponseForbidden('Las excusas las revisan el director de grupo y la coordinación.')
    if request.method == 'POST' and request.POST.get('accion') == 'plazo' and es_admin(request):
        try:
            dias = max(0, min(30, int(request.POST.get('dias') or 0)))
        except ValueError:
            dias = request.colegio.dias_plazo_excusa
        request.colegio.dias_plazo_excusa = dias
        request.colegio.save(update_fields=['dias_plazo_excusa'])
        messages.success(request, f'Plazo para enviar excusas: {dias} día(s) hábil(es).' if dias else 'Las excusas ya no tienen plazo.')
        return redirect('notas:excusas')
    if request.method == 'POST' and request.POST.get('accion') == 'registrar':
        # La familia trajo la excusa en papel: la registra quien la recibe (sin plazo).
        est = Estudiante.objects.filter(pk=request.POST.get('estudiante') or 0, colegio=request.colegio,
                                        is_active=True).first()
        if est is None or (cursos is not None and est.curso_id not in cursos):
            messages.error(request, 'Escoja el estudiante.')
        else:
            excusa, error = _crear(request, est, con_plazo=False)
            if error:
                messages.error(request, error)
            else:
                messages.success(request, 'Excusa registrada. Revísela y apruébela.')
                return redirect('notas:excusa', pk=excusa.pk)
        return redirect('notas:excusas')
    estado = request.GET.get('estado') or 'PENDIENTE'
    if estado != 'TODAS':
        qs = qs.filter(estado=estado)
    q = (request.GET.get('q') or '').strip()
    if q:
        qs = qs.filter(Q(estudiante__user__first_name__icontains=q) | Q(estudiante__user__last_name__icontains=q))
    estudiantes = Estudiante.objects.filter(colegio=request.colegio, is_active=True).select_related('user', 'curso')
    if cursos is not None:
        estudiantes = estudiantes.filter(curso_id__in=cursos)
    return render(request, 'notas/excusas/bandeja.html', {
        'excusas': qs[:200], 'estado': estado, 'q': q, 'estados': Excusa.ESTADOS, 'motivos': Excusa.MOTIVOS,
        'estudiantes': estudiantes.order_by('curso__nombre', 'user__last_name', 'user__first_name'),
        'hoy': timezone.localdate(), 'n_pendientes': _excusas_visibles(request)[0].filter(estado='PENDIENTE').count(),
        'admin': es_admin(request), 'plazo': request.colegio.dias_plazo_excusa})


@login_required
def excusa(request, pk):
    e = get_object_or_404(Excusa.objects.select_related('estudiante__user', 'estudiante__curso__director_grado__user',
                                                         'enviada_por', 'revisada_por'), pk=pk, colegio=request.colegio)
    es_suya = e.estudiante.user_id == request.user.id
    puede = EX.puede_aprobar(request, e)
    if not (puede or es_suya):
        raise Http404
    if request.method == 'POST':
        accion = request.POST.get('accion')
        respuesta = (request.POST.get('respuesta') or '').strip()
        familia = [e.estudiante.user]
        if accion == 'cancelar' and es_suya and e.estado == 'PENDIENTE':
            e.delete()
            messages.info(request, 'Excusa cancelada.')
            return redirect('notas:mis_excusas')
        if not puede:
            return HttpResponseForbidden()
        if accion == 'aprobar' and e.estado in ('PENDIENTE', 'RECHAZADA'):
            desde = _fecha(request.POST.get('desde')) or e.desde
            hasta = _fecha(request.POST.get('hasta')) or desde
            error = EX.validar_fechas(request.colegio, desde, hasta, con_plazo=False)
            if error:
                messages.error(request, error)
                return redirect('notas:excusa', pk=pk)
            n = EX.aprobar(e, request.user, desde, hasta, respuesta)
            rango = f'{desde:%d/%m}' + (f' a {hasta:%d/%m}' if hasta != desde else '')
            nombre = e.estudiante.user.get_full_name() or e.estudiante.user.username
            EX.avisar(familia, request.colegio, f'✅ Excusa aprobada: {rango}.', _url(request, 'notas:mis_excusas'))
            vistos = {u.id: u for u in EX.docentes_del_curso(e)}
            EX.avisar(vistos.values(), request.colegio,
                      f'📝 {nombre} ({e.estudiante.curso.nombre if e.estudiante.curso_id else ""}) tiene excusa '
                      f'aprobada: {rango} ({e.get_motivo_display().lower()}). Tenga en cuenta sus evaluaciones.',
                      _url(request, 'notas:asistencia'))
            messages.success(request, f'Excusa aprobada: {n} falla(s) quedaron justificadas. Se avisó a la familia y a los docentes.')
        elif accion == 'rechazar' and e.estado == 'PENDIENTE':
            if not respuesta:
                messages.error(request, 'Escriba por qué no se aprueba: le llega a la familia.')
                return redirect('notas:excusa', pk=pk)
            EX.rechazar(e, request.user, respuesta)
            EX.avisar(familia, request.colegio, f'❌ Excusa no aprobada: {respuesta}', _url(request, 'notas:mis_excusas'))
            messages.info(request, 'Excusa rechazada. Se avisó a la familia.')
        elif accion == 'anular' and e.estado == 'APROBADA':
            EX.anular(e, request.user, respuesta)
            messages.info(request, 'Aprobación anulada: esas fallas vuelven a quedar sin excusa.')
        return redirect('notas:excusa', pk=pk)

    dias = EX.dias_habiles(e.aprobada_desde or e.desde, e.aprobada_hasta or e.hasta)
    registros = (Asistencia.objects.filter(estudiante=e.estudiante, fecha__in=dias)
                 .select_related('asignacion__materia').order_by('fecha', 'asignacion__materia__nombre'))
    por_dia = {d: [] for d in dias}
    for r in registros:
        por_dia.setdefault(r.fecha, []).append(r)
    otras = e.estudiante.excusas.exclude(pk=e.pk).order_by('-creada')[:8]
    return render(request, 'notas/excusas/excusa.html', {
        'e': e, 'puede': puede, 'es_suya': es_suya, 'por_dia': sorted(por_dia.items()), 'otras': otras,
        'limite': EX.fecha_limite(request.colegio, e.desde)})


@login_required
def soporte(request, pk):
    e = get_object_or_404(Excusa, pk=pk, colegio=request.colegio)
    if not (EX.puede_aprobar(request, e) or e.estudiante.user_id == request.user.id) or not e.soporte:
        raise Http404
    return redirect(e.soporte.url)
