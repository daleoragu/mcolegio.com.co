from django import forms
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import HttpResponse, HttpResponseForbidden, HttpResponseNotFound
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.utils import timezone
from django.views.decorators.http import require_POST

from notas.models import Curso, Docente, Estudiante, Materia, PeriodoAcademico
from notas.permisos import admin_requerido, es_admin

from . import logica
from .models import TIPOS_AJUSTE, AjustePiar, ConfiguracionPiar, Piar

_TEXTO = {'class': 'form-control', 'rows': 3}


class GeneralForm(forms.ModelForm):
    class Meta:
        model = Piar
        fields = ['fecha_elaboracion', 'elaborado_por', 'categoria', 'diagnostico', 'fuente_diagnostico',
                  'apoyos_salud', 'entorno_hogar', 'trayectoria', 'descripcion', 'fortalezas', 'barreras',
                  'apoyos_requeridos', 'expectativas_familia', 'expectativas_estudiante']
        widgets = {
            'fecha_elaboracion': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}, format='%Y-%m-%d'),
            'elaborado_por': forms.TextInput(attrs={'class': 'form-control',
                                                    'placeholder': 'Ej.: Luisa Pérez, docente de apoyo'}),
            'categoria': forms.Select(attrs={'class': 'form-select'}),
            'fuente_diagnostico': forms.TextInput(attrs={'class': 'form-control',
                                                         'placeholder': 'Ej.: Neuropediatra EPS, marzo 2025'}),
            **{c: forms.Textarea(attrs=_TEXTO) for c in ('diagnostico', 'apoyos_salud', 'entorno_hogar', 'trayectoria',
                                                         'descripcion', 'fortalezas', 'barreras', 'apoyos_requeridos',
                                                         'expectativas_familia', 'expectativas_estudiante')},
        }


class ActaForm(forms.ModelForm):
    class Meta:
        model = Piar
        fields = ['compromisos_familia', 'compromisos_colegio', 'recomendaciones', 'fecha_acta', 'compartido_familia']
        widgets = {
            'compromisos_familia': forms.Textarea(attrs=_TEXTO),
            'compromisos_colegio': forms.Textarea(attrs=_TEXTO),
            'recomendaciones': forms.Textarea(attrs=_TEXTO),
            'fecha_acta': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}, format='%Y-%m-%d'),
            'compartido_familia': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class AjusteForm(forms.ModelForm):
    tipos = forms.MultipleChoiceField(choices=TIPOS_AJUSTE, required=False,
                                      widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
                                      label='Tipo de ajuste')

    class Meta:
        model = AjustePiar
        fields = ['objetivos', 'barreras', 'tipos', 'ajustes', 'evaluacion']
        widgets = {c: forms.Textarea(attrs=_TEXTO) for c in ('objetivos', 'barreras', 'ajustes', 'evaluacion')}


def _ano(request):
    try:
        return int(request.GET.get('ano') or timezone.localdate().year)
    except ValueError:
        return timezone.localdate().year


def _piar(request, pk):
    piar = get_object_or_404(Piar.objects.select_related('estudiante__user', 'estudiante__curso', 'colegio'),
                             pk=pk, colegio=request.colegio)
    return piar


# ---------------------------------------------------------------------------
# Panel
# ---------------------------------------------------------------------------
@login_required
def panel(request):
    colegio = request.colegio
    if not colegio:
        return HttpResponseNotFound('<h1>Colegio no configurado</h1>')
    coordina = logica.coordina(request)
    docente = logica.docente_de(request)
    if not coordina and not docente:
        return HttpResponseForbidden('Esta sección es para docentes y directivos.')
    ano = _ano(request)
    if request.method == 'POST' and request.POST.get('accion') == 'crear':
        est = get_object_or_404(Estudiante, pk=request.POST.get('estudiante'), colegio=colegio)
        if not (coordina or logica.es_director(request, est)):
            return HttpResponseForbidden('Solo la administración, los docentes de apoyo o el director de grupo crean el PIAR.')
        piar, copiado = logica.crear(est, ano, request.user)
        if copiado:
            messages.success(request, 'PIAR creado con la información del año anterior: revísela y actualícela.')
        return redirect('piar:detalle', piar.pk)

    curso_id = request.GET.get('curso_id') or ''
    estudiantes = logica.estudiantes_visibles(request, ano)
    if curso_id:
        estudiantes = estudiantes.filter(curso_id=curso_id)
    piars = {p.estudiante_id: p for p in Piar.objects.filter(colegio=colegio, ano_lectivo=ano)}
    filas = []
    for est in estudiantes:
        p = piars.get(est.id)
        filas.append({'est': est, 'piar': p, 'avance': logica.avance(p) if p else None,
                      'puede_crear': coordina or logica.es_director(request, est)})

    # Buscar a alguien que todavía no está marcado como estudiante de inclusión.
    q = (request.GET.get('q') or '').strip()
    encontrados = []
    if q and coordina:
        encontrados = (Estudiante.objects.filter(colegio=colegio, is_active=True)
                       .filter(Q(user__first_name__icontains=q) | Q(user__last_name__icontains=q)
                               | Q(ficha__numero_documento__icontains=q))
                       .exclude(id__in=[f['est'].id for f in filas]).select_related('user', 'curso')[:15])
    pendientes = logica.pendientes_docente(request, ano) if docente else []
    cursos = Curso.objects.filter(colegio=colegio)
    if not coordina:
        cursos = cursos.filter(id__in=logica.cursos_del_docente(docente))
    return render(request, 'piar/panel.html', {
        'colegio': colegio, 'ano': ano, 'filas': filas, 'coordina': coordina, 'es_admin': es_admin(request),
        'cursos': cursos.order_by('orden'), 'curso_id': curso_id, 'q': q, 'encontrados': encontrados,
        'pendientes': pendientes,
        'vigentes': sum(1 for f in filas if f['piar'] and f['piar'].estado == 'VIGENTE'),
        'sin_piar': sum(1 for f in filas if not f['piar'])})


@admin_requerido
def configuracion(request):
    conf = ConfiguracionPiar.de(request.colegio)
    docentes = Docente.objects.filter(colegio=request.colegio).select_related('user')
    if request.method == 'POST':
        conf.docentes_apoyo.set(docentes.filter(pk__in=request.POST.getlist('docentes')))
        messages.success(request, 'Docentes de apoyo guardados.')
        return redirect('piar:panel')
    return render(request, 'piar/configuracion.html', {
        'colegio': request.colegio, 'docentes': docentes,
        'elegidos': set(conf.docentes_apoyo.values_list('id', flat=True))})


# ---------------------------------------------------------------------------
# Un PIAR
# ---------------------------------------------------------------------------
@login_required
def detalle(request, pk):
    piar = _piar(request, pk)
    if not logica.puede_ver(request, piar):
        return HttpResponseForbidden('Este PIAR es de un estudiante que usted no tiene a cargo.')
    general = logica.puede_editar_general(request, piar)
    form = GeneralForm(instance=piar)
    acta = ActaForm(instance=piar)
    if request.method == 'POST' and general:
        if request.POST.get('que') == 'general':
            form = GeneralForm(request.POST, instance=piar)
            if form.is_valid():
                form.save()
                messages.success(request, 'Información del estudiante guardada.')
                return redirect('piar:detalle', piar.pk)
        elif request.POST.get('que') == 'acta':
            acta = ActaForm(request.POST, instance=piar)
            if acta.is_valid():
                acta.save()
                messages.success(request, 'Acta de acuerdo guardada.' + (' El PIAR quedó vigente.' if piar.fecha_acta else ''))
                return redirect('piar:detalle', piar.pk)
    editables = logica.materias_editables(request, piar)
    otros = Piar.objects.filter(estudiante=piar.estudiante).exclude(pk=piar.pk).order_by('-ano_lectivo')
    return render(request, 'piar/detalle.html', {
        'colegio': request.colegio, 'piar': piar, 'est': piar.estudiante, 'general': general, 'form': form,
        'acta': acta, 'm': logica.matriz(piar, editables), 'otros': otros, 'es_admin': es_admin(request)})


@login_required
def ajuste(request, pk, materia_id, periodo_id):
    piar = _piar(request, pk)
    materia = get_object_or_404(Materia, pk=materia_id, colegio=request.colegio)
    periodo = get_object_or_404(PeriodoAcademico, pk=periodo_id, colegio=request.colegio, ano_lectivo=piar.ano_lectivo)
    if materia.id not in logica.materias_editables(request, piar):
        return HttpResponseForbidden('Esta asignatura no es suya en el curso del estudiante.')
    obj = AjustePiar.objects.filter(piar=piar, materia=materia, periodo=periodo).first()
    anterior = logica.ajuste_anterior(piar, materia, periodo)
    if request.method == 'POST':
        form = AjusteForm(request.POST, instance=obj or AjustePiar(piar=piar, materia=materia, periodo=periodo))
        if form.is_valid():
            a = form.save(commit=False)
            a.docente = logica.docente_de(request) or a.docente
            a.save()
            messages.success(request, f'Ajustes de {materia.nombre} · {periodo.get_nombre_display()} guardados.')
            return redirect('piar:detalle', piar.pk)
    else:
        inicial = None
        if obj is None and anterior and request.GET.get('copiar') == '1':
            inicial = {'objetivos': anterior.objetivos, 'barreras': anterior.barreras, 'tipos': anterior.tipos,
                       'ajustes': anterior.ajustes}
        form = AjusteForm(instance=obj, initial=inicial)
    return render(request, 'piar/ajuste.html', {
        'colegio': request.colegio, 'piar': piar, 'est': piar.estudiante, 'materia': materia, 'periodo': periodo,
        'form': form, 'obj': obj, 'anterior': anterior, 'copiado': request.GET.get('copiar') == '1'})


@require_POST
@admin_requerido
def eliminar(request, pk):
    piar = _piar(request, pk)
    nombre = piar.estudiante.user.get_full_name()
    piar.delete()
    messages.success(request, f'Se eliminó el PIAR {piar.ano_lectivo} de {nombre}.')
    return redirect('piar:panel')


# ---------------------------------------------------------------------------
# PDF
# ---------------------------------------------------------------------------
def _pdf(request, plantilla, contexto, nombre):
    try:
        from weasyprint import HTML
    except ImportError:
        return HttpResponse('La generación de PDF no está disponible en este servidor.', status=500)
    contexto.update({'colegio': request.colegio, 'hoy': timezone.localdate()})
    html = render_to_string(plantilla, contexto, request=request)
    r = HttpResponse(HTML(string=html, base_url=request.build_absolute_uri('/')).write_pdf(),
                     content_type='application/pdf')
    r['Content-Disposition'] = f'inline; filename="{nombre}.pdf"'
    return r


def _es_su_familia(request, piar):
    return piar.compartido_familia and piar.estudiante.user_id == request.user.id


def _contexto_pdf(piar):
    m = logica.matriz(piar, set())
    por_materia = []
    for f in m['filas']:
        hechos = [c for c in f['celdas'] if c['ajuste']]
        por_materia.append({'materia': f['materia'], 'docentes': f['docentes'], 'ajustes': [c['ajuste'] for c in hechos]})
    ficha = getattr(piar.estudiante, 'ficha', None)
    edad = None
    if ficha and ficha.fecha_nacimiento:
        hoy, n = timezone.localdate(), ficha.fecha_nacimiento
        edad = hoy.year - n.year - ((hoy.month, hoy.day) < (n.month, n.day))
    return {'piar': piar, 'est': piar.estudiante, 'ficha': ficha, 'edad': edad,
            'por_materia': por_materia, 'periodos': m['periodos']}


@login_required
def pdf(request, pk):
    piar = _piar(request, pk)
    if not (logica.puede_ver(request, piar) or _es_su_familia(request, piar)):
        return HttpResponseForbidden('No tiene acceso a este PIAR.')
    return _pdf(request, 'piar/pdf_piar.html', _contexto_pdf(piar),
                f'PIAR {piar.ano_lectivo} {piar.estudiante.user.get_full_name()}')


@login_required
def acta_pdf(request, pk):
    piar = _piar(request, pk)
    if not (logica.puede_ver(request, piar) or _es_su_familia(request, piar)):
        return HttpResponseForbidden('No tiene acceso a este PIAR.')
    return _pdf(request, 'piar/pdf_acta.html', _contexto_pdf(piar),
                f'Acta de acuerdo PIAR {piar.estudiante.user.get_full_name()}')


@login_required
def mi_piar(request):
    piars = Piar.objects.filter(colegio=request.colegio, estudiante__user=request.user, compartido_familia=True)
    return render(request, 'piar/mi_piar.html', {'colegio': request.colegio, 'piars': piars})
