import datetime

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.http import Http404, HttpResponse, HttpResponseNotFound
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from notas.models import Curso
from notas.permisos import admin_requerido, es_admin, es_admin_colegio

from . import festivos, logica
from .models import COLORES, PARA, TIPOS, Evento

MESES = ['', 'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio', 'Agosto', 'Septiembre',
         'Octubre', 'Noviembre', 'Diciembre']


def _rol(request):
    return logica.Rol(request.user, request.colegio, es_admin(request))


@login_required
def calendario(request):
    colegio = request.colegio
    if not colegio:
        return HttpResponseNotFound('<h1>Colegio no configurado</h1>')
    hoy = timezone.localdate()
    try:
        ano = int(request.GET.get('ano', hoy.year))
        num = int(request.GET.get('mes', hoy.month))
        datetime.date(ano, num, 1)
    except ValueError:
        ano, num = hoy.year, hoy.month
    rol = _rol(request)
    previo = (ano - 1, 12) if num == 1 else (ano, num - 1)
    siguiente = (ano + 1, 1) if num == 12 else (ano, num + 1)
    proximos = logica.eventos_entre(colegio, rol, hoy, hoy + datetime.timedelta(days=45))[:12]
    for e in proximos:
        e.google = logica.enlace_google(e, colegio)
    ficha = logica.ficha_ics(request.user, colegio)
    url_ics = request.build_absolute_uri(reverse('calendario:ics', args=[ficha]))
    return render(request, 'calendario/calendario.html', {
        'colegio': colegio, 'semanas': logica.mes(colegio, rol, ano, num), 'ano': ano, 'num': num,
        'nombre_mes': MESES[num], 'previo': previo, 'siguiente': siguiente, 'hoy': hoy,
        'proximos': proximos, 'puede_editar': rol.admin, 'url_ics': url_ics,
        'url_webcal': 'webcal://' + url_ics.split('://', 1)[-1],
        'dias_semana': ['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom'],
        'leyenda': [(n, COLORES[c]) for c, n in TIPOS] + [('Periodos', COLORES['PERIODO']), ('Cierre de notas', COLORES['CIERRE'])],
    })


@login_required
def ver_evento(request, pk):
    colegio = request.colegio
    rol = _rol(request)
    e = next((x for x in logica.visibles(colegio, rol) if x.pk == pk), None)
    if e is None:
        raise Http404
    return render(request, 'calendario/evento.html', {
        'colegio': colegio, 'e': e, 'google': logica.enlace_google(e, colegio), 'puede_editar': rol.admin,
        'cuando': logica.texto_fecha(e)})


@admin_requerido
def editar(request, pk=None):
    colegio = request.colegio
    e = get_object_or_404(Evento, pk=pk, colegio=colegio) if pk else None
    cursos = Curso.objects.filter(colegio=colegio).order_by('orden', 'nombre')
    errores = []
    if request.method == 'POST':
        p = request.POST
        nuevo = e is None
        if nuevo:
            e = Evento(colegio=colegio, creado_por=request.user)
        e.titulo = (p.get('titulo') or '').strip()[:120]
        e.tipo = p.get('tipo') if p.get('tipo') in dict(TIPOS) else 'OTRO'
        e.para = p.get('para') if p.get('para') in dict(PARA) else 'TODOS'
        e.lugar = (p.get('lugar') or '').strip()[:120]
        e.descripcion = (p.get('descripcion') or '').strip()
        e.fecha = _fecha(p.get('fecha'))
        e.fecha_fin = _fecha(p.get('fecha_fin'))
        e.hora_inicio = _hora(p.get('hora_inicio'))
        e.hora_fin = _hora(p.get('hora_fin'))
        if not e.titulo:
            errores.append('Escriba el nombre del evento.')
        if not e.fecha:
            errores.append('Escoja la fecha.')
        if e.fecha and e.fecha_fin and e.fecha_fin < e.fecha:
            errores.append('La fecha final no puede ser antes de la inicial.')
        if e.fecha_fin == e.fecha:
            e.fecha_fin = None
        if e.hora_inicio and e.hora_fin and e.hora_fin <= e.hora_inicio:
            errores.append('La hora final debe ser después de la inicial.')
        if not errores:
            e.save()
            e.cursos.set(cursos.filter(id__in=[int(c) for c in p.getlist('cursos') if c.isdigit()]))
            if p.get('avisar'):
                n = logica.avisar(e, reverse('calendario:evento', args=[e.pk]), cambio=not nuevo)
                messages.success(request, f'Evento guardado. Se avisó a {n} persona(s).')
            else:
                messages.success(request, 'Evento guardado.')
            return redirect(f"{reverse('calendario:inicio')}?ano={e.fecha.year}&mes={e.fecha.month}")
    elif e is None:
        f = _fecha(request.GET.get('fecha'))
        e = Evento(colegio=colegio, fecha=f or timezone.localdate())
    elegidos = set(e.cursos.values_list('id', flat=True)) if e.pk else {
        int(c) for c in request.POST.getlist('cursos') if c.isdigit()}
    return render(request, 'calendario/editar.html', {
        'colegio': colegio, 'e': e, 'cursos': cursos, 'elegidos': elegidos, 'tipos': TIPOS, 'para': PARA,
        'errores': errores})


@admin_requerido
@require_POST
def eliminar(request, pk):
    e = get_object_or_404(Evento, pk=pk, colegio=request.colegio)
    f = e.fecha
    e.delete()
    messages.success(request, 'Evento eliminado.')
    return redirect(f"{reverse('calendario:inicio')}?ano={f.year}&mes={f.month}")


@admin_requerido
@require_POST
def agregar_festivos(request):
    colegio = request.colegio
    try:
        ano = int(request.POST.get('ano') or timezone.localdate().year)
    except ValueError:
        ano = timezone.localdate().year
    ya = set(Evento.objects.filter(colegio=colegio, tipo='FESTIVO', fecha__year=ano).values_list('fecha', flat=True))
    nuevos = [Evento(colegio=colegio, titulo=f'Festivo: {n}', tipo='FESTIVO', fecha=f, para='TODOS',
                     creado_por=request.user) for f, n in festivos.festivos(ano) if f not in ya]
    Evento.objects.bulk_create(nuevos)
    messages.success(request, f'Se agregaron {len(nuevos)} festivos de {ano}.' if nuevos
                     else f'Los festivos de {ano} ya estaban en el calendario.')
    return redirect(f"{reverse('calendario:inicio')}?ano={ano}&mes={request.POST.get('mes') or 1}")


@login_required
def descargar_ics(request):
    """Todo el año escolar en un archivo .ics (para Outlook, el celular, etc.)."""
    colegio = request.colegio
    rol = _rol(request)
    hoy = timezone.localdate()
    eventos = logica.eventos_entre(colegio, rol, hoy - datetime.timedelta(days=60), hoy + datetime.timedelta(days=400))
    r = HttpResponse(logica.ics(colegio, eventos, request.get_host()), content_type='text/calendar; charset=utf-8')
    r['Content-Disposition'] = 'attachment; filename="calendario-escolar.ics"'
    return r


def suscripcion_ics(request, ficha):
    """Dirección para suscribirse desde Google Calendar (se actualiza sola). No pide clave:
    la dirección lleva una firma que solo conoce la plataforma."""
    datos = logica.leer_ficha(ficha)
    colegio = getattr(request, 'colegio', None)
    if not datos or not colegio or datos[1] != colegio.pk:
        raise Http404
    user = get_user_model().objects.filter(pk=datos[0], is_active=True).first()
    if not user:
        raise Http404
    rol = logica.Rol(user, colegio, user.is_superuser or es_admin_colegio(user, colegio))
    if not (rol.admin or rol.docente or rol.estudiante):
        raise Http404
    hoy = timezone.localdate()
    eventos = logica.eventos_entre(colegio, rol, hoy - datetime.timedelta(days=60), hoy + datetime.timedelta(days=400))
    return HttpResponse(logica.ics(colegio, eventos, request.get_host()), content_type='text/calendar; charset=utf-8')


def _fecha(txt):
    try:
        return datetime.datetime.strptime((txt or '').strip(), '%Y-%m-%d').date()
    except ValueError:
        return None


def _hora(txt):
    try:
        return datetime.datetime.strptime((txt or '').strip(), '%H:%M').time()
    except ValueError:
        return None
