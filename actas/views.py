# -*- coding: utf-8 -*-
"""Actas: el administrador del colegio las redacta, las cierra y las imprime para firmar."""
import datetime

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError, transaction
from django.http import HttpResponse, HttpResponseForbidden, HttpResponseNotFound, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.views.decorators.http import require_POST

from notas.models import PeriodoAcademico
from notas.permisos import es_admin

from . import logica
from .forms import ActaForm
from .models import Acta

ORDEN_COMISION = """Saludo y verificación del quórum.
Lectura y aprobación del acta anterior.
Análisis de los estudiantes con asignaturas pendientes.
Recomendaciones, estrategias de apoyo y compromisos.
Proposiciones y varios."""

ORDEN_LIBRE = """Saludo y verificación del quórum.
Lectura y aprobación del acta anterior.
Proposiciones y varios."""


def _guardia(request):
    if getattr(request, 'colegio', None) is None:
        return HttpResponseNotFound('<h1>Colegio no configurado</h1>')
    if not es_admin(request):
        return HttpResponseForbidden('Solo el administrador del colegio.')
    return None


def _acta(request, acta_id):
    return get_object_or_404(Acta, id=acta_id, colegio=request.colegio)


def _periodo_actual(colegio):
    hoy = datetime.date.today()
    qs = PeriodoAcademico.objects.filter(colegio=colegio)
    return (qs.filter(fecha_inicio__lte=hoy, fecha_fin__gte=hoy).first()
            or qs.filter(fecha_inicio__lte=hoy).order_by('-fecha_inicio').first()
            or qs.order_by('fecha_inicio').first())


@login_required
def lista(request):
    if (r := _guardia(request)):
        return r
    actas = Acta.objects.filter(colegio=request.colegio).prefetch_related('cursos')
    ano = request.GET.get('ano')
    anos = sorted(set(actas.values_list('ano', flat=True)), reverse=True)
    if ano and ano.isdigit():
        actas = actas.filter(ano=int(ano))
    return render(request, 'actas/lista.html', {'actas': actas, 'anos': anos, 'ano': ano,
                                                'page_title': 'Actas'})


@login_required
@require_POST
def nueva(request, tipo):
    if (r := _guardia(request)):
        return r
    if tipo not in (Acta.COMISION, Acta.LIBRE):
        return HttpResponseNotFound()
    periodo = _periodo_actual(request.colegio) if tipo == Acta.COMISION else None
    ano = periodo.ano_lectivo if periodo else datetime.date.today().year
    # Si dos personas crean un acta al mismo tiempo, la segunda toma el número siguiente.
    for _ in range(5):
        try:
            with transaction.atomic():
                acta = Acta.objects.create(
                    colegio=request.colegio, tipo=tipo, ano=ano, numero=logica.siguiente_numero(request.colegio, ano),
                    titulo=('Comisión de evaluación y promoción' if tipo == Acta.COMISION else 'Reunión'),
                    fecha=datetime.date.today(), periodo=periodo, creada_por=request.user,
                    orden_del_dia=ORDEN_COMISION if tipo == Acta.COMISION else ORDEN_LIBRE)
            return redirect('actas:editar', acta.id)
        except IntegrityError:
            continue
    messages.error(request, 'No se pudo numerar el acta. Intente de nuevo.')
    return redirect('actas:lista')


@login_required
def editar(request, acta_id):
    if (r := _guardia(request)):
        return r
    acta = _acta(request, acta_id)
    if acta.cerrada:
        return render(request, 'actas/ver.html', {'acta': acta, 'informe': logica.informe_de(acta),
                                                  'page_title': f'Acta {acta.numero} de {acta.ano}'})
    if request.method == 'POST':
        form = ActaForm(request.POST, instance=acta, colegio=request.colegio)
        if form.is_valid():
            acta = form.save(commit=False)
            acta.asistencia = form.asistencia_de(request.POST)
            acta.save()
            form.save_m2m()
            messages.success(request, 'Acta guardada.')
            if request.POST.get('siguiente') == 'pdf':
                return redirect('actas:pdf', acta.id)
            return redirect('actas:editar', acta.id)
    else:
        form = ActaForm(instance=acta, colegio=request.colegio)
    grados = []
    if acta.es_comision:
        if form.is_bound:
            elegidos = {int(x) for x in request.POST.getlist('cursos') if x.isdigit()}
        else:
            elegidos = set(acta.cursos.values_list('id', flat=True))
        por_grado = {}
        for c in form.fields['cursos'].queryset:
            por_grado.setdefault(c.grado, []).append(
                {'id': c.id, 'nombre': c.nombre, 'sede': c.sede_id or '', 'marcado': c.id in elegidos})
        nombres = {}
        for c in form.fields['cursos'].queryset:
            nombres.setdefault(c.grado, c.get_grado_display() if c.grado is not None else 'Sin grado')
        grados = [{'grado': g, 'nombre': nombres[g], 'cursos': cs} for g, cs in sorted(por_grado.items(), key=lambda x: (x[0] is None, x[0]))]
    return render(request, 'actas/editar.html', {
        'acta': acta, 'form': form, 'informe': logica.informe_de(acta) if acta.es_comision else None,
        'grados': grados, 'asistencia': (form.asistencia_de(request.POST) if form.is_bound else acta.lista_asistentes()),
        'page_title': f'Acta {acta.numero} de {acta.ano}'})


@login_required
def sugerir_asistentes(request, acta_id):
    if (r := _guardia(request)):
        return r
    # Los cursos marcados en pantalla, aunque todavía no se hayan guardado.
    ids = [int(x) for x in request.GET.get('cursos', '').split(',') if x.isdigit()]
    acta = _acta(request, acta_id)
    return JsonResponse({'filas': logica.asistentes_sugeridos(acta, ids if 'cursos' in request.GET else None)})


@login_required
@require_POST
def cerrar(request, acta_id):
    if (r := _guardia(request)):
        return r
    acta = _acta(request, acta_id)
    if acta.es_comision and (acta.periodo_id is None or not acta.cursos.exists()):
        messages.error(request, 'Antes de cerrar, escoja el periodo y los cursos.')
        return redirect('actas:editar', acta.id)
    logica.cerrar(acta)
    messages.success(request, 'Acta cerrada: el informe quedó como está hoy, aunque después cambien las notas.')
    return redirect('actas:editar', acta.id)


@login_required
@require_POST
def reabrir(request, acta_id):
    if (r := _guardia(request)):
        return r
    logica.reabrir(_acta(request, acta_id))
    messages.info(request, 'El acta volvió a borrador. Al cerrarla de nuevo, el informe se recalcula.')
    return redirect('actas:editar', acta_id)


@login_required
@require_POST
def eliminar(request, acta_id):
    if (r := _guardia(request)):
        return r
    acta = _acta(request, acta_id)
    if acta.cerrada:
        messages.error(request, 'Un acta cerrada no se borra. Reábrala primero si de verdad hay que eliminarla.')
        return redirect('actas:editar', acta.id)
    acta.delete()
    messages.success(request, 'Borrador eliminado.')
    return redirect('actas:lista')


@login_required
def pdf(request, acta_id):
    if (r := _guardia(request)):
        return r
    acta = _acta(request, acta_id)
    html = render_to_string('actas/acta_pdf.html', {
        'acta': acta, 'colegio': request.colegio, 'informe': logica.informe_de(acta),
        'orden': acta.lista('orden_del_dia'), 'decisiones': acta.lista('decisiones'),
        'asistentes': acta.lista_asistentes(),
    }, request=request)
    try:
        from weasyprint import HTML
    except ImportError:
        return HttpResponse('No se pudo generar el PDF (falta WeasyPrint en el servidor).', status=500)
    archivo = HTML(string=html, base_url=request.build_absolute_uri('/')).write_pdf()
    r = HttpResponse(archivo, content_type='application/pdf')
    r['Content-Disposition'] = f'inline; filename="acta_{acta.numero}_{acta.ano}.pdf"'
    return r
