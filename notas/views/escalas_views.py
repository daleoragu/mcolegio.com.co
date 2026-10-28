"""Escalas especiales: una escala distinta para algunas materias y, si se quiere, solo en algunos grados."""
from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import HttpResponseForbidden, HttpResponseNotFound
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .. import escalas
from ..models import AreaConocimiento, Curso, EscalaEspecial, EscalaValoracion, Materia, NivelEscalaEspecial
from ..models.perfiles import GRADOS
from ..permisos import es_admin


def _decimal(texto):
    try:
        return Decimal(str(texto).replace(',', '.').strip()).quantize(Decimal('0.1'))
    except (InvalidOperation, ValueError):
        return None


def _grados_del_colegio(colegio):
    usados = set(Curso.objects.filter(colegio=colegio).exclude(grado__isnull=True).values_list('grado', flat=True))
    return [(n, nombre) for n, nombre, _ in GRADOS if n in usados] or [(n, nombre) for n, nombre, _ in GRADOS]


def _materias_por_area(colegio):
    """[(área, [materias])] y al final las materias sin área."""
    materias = list(Materia.objects.filter(colegio=colegio).order_by('nombre'))
    vistas, grupos = set(), []
    for area in AreaConocimiento.objects.filter(colegio=colegio).prefetch_related('materias').order_by('nombre'):
        lista = [m for m in area.materias.all() if m.colegio_id == colegio.id]
        lista.sort(key=lambda m: m.nombre)
        if lista:
            grupos.append((area.nombre, lista))
            vistas.update(m.id for m in lista)
    sueltas = [m for m in materias if m.id not in vistas]
    if sueltas:
        grupos.append(('Sin área', sueltas))
    return grupos


def _resumen(colegio):
    filas = []
    for e in EscalaEspecial.objects.filter(colegio=colegio).prefetch_related('materias', 'niveles'):
        nombres_grado = dict((n, nombre) for n, nombre, _ in GRADOS)
        filas.append({
            'escala': e,
            'materias': ', '.join(m.nombre for m in e.materias.all()) or '—',
            'grados': ', '.join(nombres_grado.get(int(g), str(g)) for g in e.grados) if e.grados else 'Todos',
            'niveles': list(e.niveles.all()),
        })
    return filas


@login_required
def escalas_especiales(request):
    if not request.colegio:
        return HttpResponseNotFound('<h1>Colegio no configurado</h1>')
    if not es_admin(request):
        return HttpResponseForbidden('Solo la administración del colegio configura las escalas.')
    return render(request, 'notas/admin_tools/escalas_especiales.html', {
        'colegio': request.colegio, 'filas': _resumen(request.colegio),
        'general': EscalaValoracion.objects.filter(colegio=request.colegio).order_by('valor_minimo'),
    })


@login_required
def editar_escala_especial(request, pk=None):
    if not request.colegio:
        return HttpResponseNotFound('<h1>Colegio no configurado</h1>')
    if not es_admin(request):
        return HttpResponseForbidden('Solo la administración del colegio configura las escalas.')
    colegio = request.colegio
    escala = get_object_or_404(EscalaEspecial, pk=pk, colegio=colegio) if pk else None

    if escala:
        niveles = [(n.nombre_desempeno, n.valor_minimo, n.valor_maximo) for n in escala.niveles.all()]
        materias_sel = set(escala.materias.values_list('id', flat=True))
        grados_sel = set(int(g) for g in escala.grados)
        nombre = escala.nombre
    else:
        # Se arranca con la escala del colegio para que solo haya que mover los rangos.
        niveles = [(n.nombre_desempeno, n.valor_minimo, n.valor_maximo)
                   for n in EscalaValoracion.objects.filter(colegio=colegio).order_by('valor_minimo')]
        materias_sel, grados_sel, nombre = set(), set(), ''

    errores = []
    if request.method == 'POST':
        nombre = (request.POST.get('nombre') or '').strip()[:80]
        validas = set(Materia.objects.filter(colegio=colegio).values_list('id', flat=True))
        materias_sel = {int(m) for m in request.POST.getlist('materias') if m.isdigit() and int(m) in validas}
        grados_validos = {n for n, _, _ in GRADOS}
        grados_sel = {int(g) for g in request.POST.getlist('grados')
                      if g.lstrip('-').isdigit() and int(g) in grados_validos}
        niveles = []
        for n, a, b in zip(request.POST.getlist('nivel_nombre'), request.POST.getlist('nivel_min'),
                           request.POST.getlist('nivel_max')):
            if not (n or '').strip() and not (a or '').strip() and not (b or '').strip():
                continue
            niveles.append(((n or '').strip().upper()[:50], _decimal(a), _decimal(b)))
        if not nombre:
            errores.append('Póngale un nombre a la escala (por ejemplo «Escala de Inglés»).')
        errores += escalas.validar_especial(colegio, sorted(materias_sel), sorted(grados_sel), niveles,
                                            excluir_pk=escala.pk if escala else None)
        if not errores:
            with transaction.atomic():
                if escala is None:
                    escala = EscalaEspecial.objects.create(colegio=colegio, nombre=nombre, grados=sorted(grados_sel))
                else:
                    escala.nombre, escala.grados = nombre, sorted(grados_sel)
                    escala.save()
                    escala.niveles.all().delete()
                escala.materias.set(materias_sel)
                for n, a, b in sorted(niveles, key=lambda x: x[1]):
                    NivelEscalaEspecial.objects.create(escala=escala, nombre_desempeno=n, valor_minimo=a, valor_maximo=b)
            messages.success(request, f'Escala «{nombre}» guardada. Ya rige en boletines, sábana, planillas y alertas.')
            return redirect('notas:escalas_especiales')

    return render(request, 'notas/admin_tools/escala_especial_form.html', {
        'colegio': colegio, 'escala': escala, 'nombre': nombre, 'errores': errores,
        'niveles': niveles + [('', None, None)] * max(0, 6 - len(niveles)),
        'grupos': _materias_por_area(colegio), 'materias_sel': materias_sel,
        'grados': _grados_del_colegio(colegio), 'grados_sel': grados_sel,
    })


@login_required
@require_POST
def eliminar_escala_especial(request, pk):
    if not request.colegio or not es_admin(request):
        return HttpResponseForbidden('Solo la administración del colegio configura las escalas.')
    escala = get_object_or_404(EscalaEspecial, pk=pk, colegio=request.colegio)
    nombre = escala.nombre
    escala.delete()
    messages.warning(request, f'Se eliminó la escala «{nombre}». Esas materias vuelven a la escala del colegio.')
    return redirect('notas:escalas_especiales')
