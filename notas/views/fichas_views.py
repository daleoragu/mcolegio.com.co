"""Ficha del estudiante: el estudiante pide los cambios; la administración o el director de grupo autoriza."""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from django.http import Http404, HttpResponseForbidden, HttpResponseNotFound
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from .. import fichas as F
from ..models import CambioFicha, Docente, Estudiante, FichaEstudiante, SolicitudFicha
from ..permisos import es_admin

MAX_FOTO_MB = 6


def _url(request, nombre, *args):
    return request.build_absolute_uri(reverse(nombre, args=args))


@login_required
def mi_ficha(request):
    """El estudiante ve su ficha y pide cambios; nada se guarda sin autorización."""
    if not request.colegio:
        return HttpResponseNotFound('<h1>Colegio no configurado</h1>')
    estudiante = Estudiante.objects.filter(user=request.user, colegio=request.colegio).select_related('curso').first()
    if estudiante is None:
        return HttpResponseForbidden('Esta página es para los estudiantes.')
    ficha, _ = FichaEstudiante.objects.get_or_create(estudiante=estudiante)
    pendiente = estudiante.solicitudes_ficha.filter(estado='PENDIENTE').first()
    if request.method == 'POST' and request.POST.get('accion') == 'cancelar' and pendiente:
        if pendiente.foto_nueva:
            pendiente.foto_nueva.delete(save=False)
        pendiente.delete()
        messages.info(request, 'Solicitud cancelada.')
        return redirect('notas:mi_ficha')
    if request.method == 'POST':
        # Se valida sobre una copia: la ficha de verdad no cambia hasta que autoricen.
        copia = FichaEstudiante.objects.get(pk=ficha.pk)
        form = F.SolicitudFichaForm(request.POST, request.FILES, instance=copia)
        foto = request.FILES.get('foto')
        if foto and foto.size > MAX_FOTO_MB * 1024 * 1024:
            form.add_error('foto', f'La foto pasa de {MAX_FOTO_MB} MB.')
        if form.is_valid():
            s = F.crear_solicitud(estudiante, request.user, form, foto_nueva=foto)
            if s is None:
                messages.info(request, 'No cambió ningún dato.')
            else:
                nombre = estudiante.user.get_full_name() or estudiante.user.username
                F.avisar(F.autorizadores(estudiante), request.colegio,
                         f'🪪 {nombre} ({estudiante.curso.nombre if estudiante.curso_id else ""}) pide cambiar '
                         f'{len(s.cambios)} dato(s) de su ficha', _url(request, 'notas:solicitud_ficha', s.pk))
                messages.success(request, 'Solicitud enviada. Cuando la administración o su director de grupo '
                                          'la autorice, se actualiza su ficha.')
            return redirect('notas:mi_ficha')
    else:
        form = F.SolicitudFichaForm(instance=ficha)
    return render(request, 'notas/estudiante/mi_ficha.html', {
        'estudiante': estudiante, 'ficha': ficha, 'form': form, 'pendiente': pendiente,
        'recientes': estudiante.solicitudes_ficha.exclude(estado='PENDIENTE')[:5]})


# ---------------------------------------------------------------------------
# Quien autoriza
# ---------------------------------------------------------------------------
def _visibles(request):
    qs = SolicitudFicha.objects.filter(colegio=request.colegio).select_related('estudiante__user', 'estudiante__curso',
                                                                               'revisada_por')
    if es_admin(request):
        return qs, True
    docente = Docente.objects.filter(user=request.user, colegio=request.colegio).first()
    if docente is None or not docente.cursos_dirigidos.exists():
        return qs.none(), False
    return qs.filter(estudiante__curso__director_grado=docente), True


@login_required
def solicitudes_ficha(request):
    if not request.colegio:
        return HttpResponseNotFound('<h1>Colegio no configurado</h1>')
    qs, puede = _visibles(request)
    if not puede:
        return HttpResponseForbidden('Las solicitudes las revisan la administración y el director de grupo.')
    estado = request.GET.get('estado') or 'PENDIENTE'
    lista = qs if estado == 'TODAS' else qs.filter(estado=estado)
    return render(request, 'notas/fichas/solicitudes.html', {
        'solicitudes': lista[:200], 'estado': estado, 'estados': SolicitudFicha.ESTADOS,
        'n_pendientes': qs.filter(estado='PENDIENTE').count()})


@login_required
def solicitud_ficha(request, pk):
    s = get_object_or_404(SolicitudFicha.objects.select_related('estudiante__user', 'estudiante__curso__director_grado'),
                          pk=pk, colegio=request.colegio)
    if not F.puede_autorizar(request, s.estudiante):
        raise Http404
    if request.method == 'POST' and s.estado == 'PENDIENTE':
        familia = [s.estudiante.user]
        if request.POST.get('accion') == 'rechazar':
            respuesta = (request.POST.get('respuesta') or '').strip()
            if not respuesta:
                messages.error(request, 'Escriba por qué no se autoriza: le llega al estudiante.')
                return redirect('notas:solicitud_ficha', pk=pk)
            F.rechazar(s, request.user, respuesta)
            F.avisar(familia, request.colegio, f'Los cambios a su ficha no se autorizaron: {respuesta}',
                     _url(request, 'notas:mi_ficha'))
            messages.info(request, 'Solicitud rechazada. Se le avisó al estudiante.')
        else:
            campos = request.POST.getlist('campos')
            s.respuesta = (request.POST.get('respuesta') or '').strip()[:500]
            try:
                n = F.aprobar(s, request.user, campos)
            except IntegrityError:
                messages.error(request, 'Ese número de documento ya lo tiene otro estudiante. Desmárquelo o revíselo.')
                return redirect('notas:solicitud_ficha', pk=pk)
            F.avisar(familia, request.colegio,
                     f'✅ Se actualizaron {n} dato(s) de su ficha.' if n else 'Los cambios a su ficha no se autorizaron.',
                     _url(request, 'notas:mi_ficha'))
            messages.success(request, f'Se aplicaron {n} de {len(s.cambios)} cambio(s) a la ficha.')
        return redirect('notas:solicitud_ficha', pk=pk)
    return render(request, 'notas/fichas/solicitud.html', {'s': s})


@login_required
def historial_ficha(request, estudiante_id):
    estudiante = get_object_or_404(Estudiante.objects.select_related('user', 'curso__director_grado'),
                                   pk=estudiante_id, colegio=request.colegio)
    if not F.puede_autorizar(request, estudiante):
        raise Http404
    return render(request, 'notas/fichas/historial.html', {
        'estudiante': estudiante,
        'cambios': CambioFicha.objects.filter(estudiante=estudiante).select_related('hecho_por', 'autorizado_por')[:300]})
