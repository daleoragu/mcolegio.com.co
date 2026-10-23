from django import forms
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import HttpResponse, HttpResponseForbidden, HttpResponseNotFound
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.template.loader import render_to_string
from django.utils import timezone
from django.views.decorators.http import require_POST

from notas.models import Curso, Docente, Estudiante, Materia, PeriodoAcademico
from notas.permisos import admin_requerido, es_admin

from . import formato as fmt
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


SECCION_DE_CAMPO = {'diagnostico': 'salud', 'fuente_diagnostico': 'salud', 'apoyos_salud': 'salud',
                    'entorno_hogar': 'hogar', 'trayectoria': 'educativo', 'descripcion': 'valoracion',
                    'fortalezas': 'valoracion', 'barreras': 'valoracion', 'apoyos_requeridos': 'valoracion',
                    'expectativas_familia': 'valoracion', 'expectativas_estudiante': 'valoracion'}


def _general_form(*args, secciones=None, **kwargs):
    form = GeneralForm(*args, **kwargs)
    for campo, sec in SECCION_DE_CAMPO.items():
        if secciones is not None and not secciones.get(sec, True):
            form.fields.pop(campo, None)
    return form


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
    """Las columnas que escogió la orientadora, con sus títulos e instrucciones."""
    tipos = forms.MultipleChoiceField(choices=TIPOS_AJUSTE, required=False,
                                      widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
                                      label='Tipo de ajuste')
    todos_los_periodos = forms.BooleanField(required=False, label='Marcar «no requiere» en todos los periodos del año')

    class Meta:
        model = AjustePiar
        fields = ['no_requiere', 'objetivos', 'barreras', 'tipos', 'ajustes', 'apoyos', 'evaluacion']
        widgets = {**{c: forms.Textarea(attrs=_TEXTO) for c in ('objetivos', 'barreras', 'ajustes', 'apoyos', 'evaluacion')},
                   'no_requiere': forms.CheckboxInput(attrs={'class': 'form-check-input'})}

    def __init__(self, *args, formato=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.formato = formato or fmt.completar({})
        self.columnas = []
        for clave, *_ in fmt.COLUMNAS:
            col = self.formato['columnas'][clave]
            if not col['activa']:
                self.fields.pop(clave, None)
                continue
            self.fields[clave].label = col['titulo']
            self.fields[clave].help_text = col['ayuda']
            self.columnas.append(self[clave])

    def clean(self):
        datos = super().clean()
        if not datos.get('no_requiere') and not (datos.get('ajustes') or '').strip() and self.data.get('exigir'):
            self.add_error('ajustes', 'Escriba los ajustes, o marque que la asignatura no los requiere.')
        return datos


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
        ya = Piar.objects.filter(estudiante=est, ano_lectivo=ano).exists()
        piar, copiado = logica.crear(est, ano, request.user)
        if copiado:
            messages.success(request, 'PIAR creado con la información del año anterior: revísela y actualícela.')
        if not ya:
            n = logica.avisar_docentes(piar, request.build_absolute_uri(reverse('piar:detalle', args=[piar.pk])))
            if n:
                messages.info(request, f'A {n} docente(s) del curso les llegó el aviso con las asignaturas que les toca llenar.')
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


@login_required
def configuracion(request):
    """La administración escoge a los docentes de apoyo; ellos (la orientadora) y la administración
    escogen el formato: secciones, columnas de los ajustes con sus instrucciones y habilidades."""
    if not request.colegio or not logica.coordina(request):
        return HttpResponseForbidden('Esta configuración es de la orientación, el docente de apoyo o la administración.')
    conf = ConfiguracionPiar.de(request.colegio)
    docentes = Docente.objects.filter(colegio=request.colegio).select_related('user')
    if request.method == 'POST':
        if request.POST.get('que') == 'docentes' and es_admin(request):
            conf.docentes_apoyo.set(docentes.filter(pk__in=request.POST.getlist('docentes')))
            messages.success(request, 'Docentes de apoyo guardados.')
        elif request.POST.get('que') == 'formato':
            p = request.POST
            if p.get('restaurar'):
                conf.formato = {}
            else:
                conf.formato = {
                    'secciones': {k: bool(p.get(f'sec_{k}')) for k, _ in fmt.SECCIONES},
                    'columnas': {k: {'activa': bool(p.get(f'col_{k}')) or not apagable,
                                     'titulo': p.get(f'tit_{k}', '').strip()[:120],
                                     'ayuda': p.get(f'ayu_{k}', '').strip()[:500]}
                                 for k, _, _, apagable in fmt.COLUMNAS},
                    'escala': p.get('escala') if p.get('escala') in fmt.ESCALAS else '1-4',
                    'habilidades': p.get('habilidades', '').strip()[:20000],
                    'instrucciones': p.get('instrucciones', '').strip()[:2000],
                    'firmas': {'estilo': p.get('estilo_firma') if p.get('estilo_firma') in dict(fmt.ESTILOS_FIRMA)
                               else 'lineas',
                               'piar': [k for k, _ in fmt.FIRMANTES if p.get(f'fp_{k}')],
                               'acta': [k for k, _ in fmt.FIRMANTES if p.get(f'fa_{k}')],
                               'otros_piar': p.get('otros_piar', '').strip()[:1000],
                               'otros_acta': p.get('otros_acta', '').strip()[:1000]},
                }
            conf.save(update_fields=['formato'])
            messages.success(request, 'Formato del PIAR guardado: así les sale a los docentes y así sale el PDF.')
        return redirect('piar:configuracion')
    f = fmt.de(request.colegio)
    return render(request, 'piar/configuracion.html', {
        'colegio': request.colegio, 'docentes': docentes, 'es_admin': es_admin(request), 'f': f,
        'secciones': [(k, t, f['secciones'][k]) for k, t in fmt.SECCIONES],
        'columnas': [(k, f['columnas'][k], apagable) for k, _, _, apagable in fmt.COLUMNAS],
        'grupos': fmt.grupos(f), 'estilos_firma': fmt.ESTILOS_FIRMA,
        'firmantes': [(k, t, k in f['firmas']['piar'], k in f['firmas']['acta']) for k, t in fmt.FIRMANTES],
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
    secciones = fmt.de(request.colegio)['secciones']
    form = _general_form(instance=piar, secciones=secciones)
    acta = ActaForm(instance=piar)
    if request.method == 'POST' and general:
        if request.POST.get('que') == 'general':
            form = _general_form(request.POST, instance=piar, secciones=secciones)
            if form.is_valid():
                form.save()
                messages.success(request, 'Información del estudiante guardada.')
                return redirect('piar:detalle', piar.pk)
        elif request.POST.get('que') == 'habilidades':
            f = fmt.de(request.colegio)
            validos = set(fmt.ESCALAS[f['escala']])
            piar.habilidades = {fila['clave']: request.POST.get(f'h_{fila["clave"]}') for g in fmt.grupos(f)
                                for fila in g['filas'] if fila['tipo'] == 'item'
                                and request.POST.get(f'h_{fila["clave"]}') in validos}
            piar.habilidades['observaciones'] = request.POST.get('hobservaciones', '').strip()
            piar.save(update_fields=['habilidades', 'actualizado'])
            messages.success(request, 'Registro de habilidades guardado.')
            return redirect('piar:detalle', piar.pk)
        elif request.POST.get('que') == 'otras':
            piar.otras_dimensiones = {k: request.POST.get(f'o_{k}', '').strip() for k in fmt.OTRAS}
            piar.recomendaciones_actores = {k: request.POST.get(f'r_{k}', '').strip() for k, _ in fmt.ACTORES}
            piar.save(update_fields=['otras_dimensiones', 'recomendaciones_actores', 'actualizado'])
            messages.success(request, 'Guardado.')
            return redirect('piar:detalle', piar.pk)
        elif request.POST.get('que') == 'acta':
            acta = ActaForm(request.POST, instance=piar)
            if acta.is_valid():
                acta.save()
                messages.success(request, 'Acta de acuerdo guardada.' + (' El PIAR quedó vigente.' if piar.fecha_acta else ''))
                return redirect('piar:detalle', piar.pk)
    editables = logica.materias_editables(request, piar)
    otros = Piar.objects.filter(estudiante=piar.estudiante).exclude(pk=piar.pk).order_by('-ano_lectivo')
    f = fmt.de(request.colegio)
    return render(request, 'piar/detalle.html', {
        'colegio': request.colegio, 'piar': piar, 'est': piar.estudiante, 'general': general, 'form': form,
        'acta': acta, 'otros': otros, 'es_admin': es_admin(request), 'f': f, 'sec': f['secciones'],
        # A cada docente le salen solo sus asignaturas; la orientación y el director ven todas.
        'm': logica.matriz(piar, editables, solo=None if general else editables),
        'habilidades': _filas_habilidades(f, piar.habilidades), 'escala': fmt.ESCALAS[f['escala']],
        'alertas': fmt.alertas_habilidades(f, piar.habilidades),
        'otras': [(k, (piar.otras_dimensiones or {}).get(k, '')) for k in fmt.OTRAS],
        'actores': [(k, t, (piar.recomendaciones_actores or {}).get(k, '')) for k, t in fmt.ACTORES],
        'estilos_firma': fmt.ESTILOS_FIRMA,
        'imprimir': [(doc, titulo, [(k, t, k in f['firmas'][doc]) for k, t in fmt.FIRMANTES], f['firmas'][f'otros_{doc}'])
                     for doc, titulo in (('piar', 'PIAR'), ('acta', 'Acta de acuerdo'))]})


def _filas_habilidades(f, respuestas):
    respuestas = respuestas or {}
    return [{'nombre': g['nombre'],
             'filas': [dict(x, valor=respuestas.get(x.get('clave'), '')) for x in g['filas']]}
            for g in fmt.grupos(f)]


@login_required
def ajuste(request, pk, materia_id, periodo_id):
    piar = _piar(request, pk)
    materia = get_object_or_404(Materia, pk=materia_id, colegio=request.colegio)
    periodo = get_object_or_404(PeriodoAcademico, pk=periodo_id, colegio=request.colegio, ano_lectivo=piar.ano_lectivo)
    if materia.id not in logica.materias_editables(request, piar):
        return HttpResponseForbidden('Esta asignatura no es suya en el curso del estudiante.')
    obj = AjustePiar.objects.filter(piar=piar, materia=materia, periodo=periodo).first()
    anterior = logica.ajuste_anterior(piar, materia, periodo)
    f = fmt.de(request.colegio)
    if request.method == 'POST':
        form = AjusteForm(request.POST, instance=obj or AjustePiar(piar=piar, materia=materia, periodo=periodo),
                          formato=f)
        if form.is_valid():
            a = form.save(commit=False)
            a.docente = logica.docente_de(request) or a.docente
            a.save()
            if a.no_requiere and form.cleaned_data.get('todos_los_periodos'):
                for per in logica.periodos(piar.colegio, piar.ano_lectivo):
                    if per.id == periodo.id:
                        continue
                    otro, _ = AjustePiar.objects.get_or_create(piar=piar, materia=materia, periodo=per)
                    if not otro.ajustes.strip():
                        otro.no_requiere = True
                        otro.docente = a.docente
                        otro.save()
            messages.success(request, f'{materia.nombre} · {periodo.get_nombre_display()}: '
                             + ('quedó como «no requiere ajustes razonables».' if a.no_requiere else 'ajustes guardados.'))
            return redirect('piar:detalle', piar.pk)
    else:
        inicial = None
        if obj is None and anterior and request.GET.get('copiar') == '1':
            inicial = {'objetivos': anterior.objetivos, 'barreras': anterior.barreras, 'tipos': anterior.tipos,
                       'ajustes': anterior.ajustes, 'apoyos': anterior.apoyos, 'no_requiere': anterior.no_requiere}
        form = AjusteForm(instance=obj, initial=inicial, formato=f)
    return render(request, 'piar/ajuste.html', {
        'colegio': request.colegio, 'piar': piar, 'est': piar.estudiante, 'materia': materia, 'periodo': periodo,
        'form': form, 'obj': obj, 'anterior': anterior, 'copiado': request.GET.get('copiar') == '1', 'f': f})


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
    f = fmt.de(piar.colegio)
    columnas = [(k, f['columnas'][k]['titulo']) for k, *_ in fmt.COLUMNAS if f['columnas'][k]['activa'] and k != 'tipos']
    firmantes = []
    for b in por_materia:
        for d in b['docentes']:
            firmantes.append((d, b['materia'].nombre))
    return {'piar': piar, 'est': piar.estudiante, 'ficha': ficha, 'edad': edad, 'f': f, 'sec': f['secciones'],
            'columnas': columnas, 'con_tipos': f['columnas']['tipos']['activa'],
            'por_materia': por_materia, 'periodos': m['periodos'],
            'habilidades': _filas_habilidades(f, piar.habilidades), 'escala': fmt.ESCALAS[f['escala']],
            'alertas': fmt.alertas_habilidades(f, piar.habilidades),
            'otras': [(k, (piar.otras_dimensiones or {}).get(k, '')) for k in fmt.OTRAS],
            'actores': [(t, (piar.recomendaciones_actores or {}).get(k, '')) for k, t in fmt.ACTORES],
            'firmantes': firmantes}


def _con_firmas(request, piar, contexto, doc):
    """Las firmas del formato; al imprimir se pueden cambiar (?estilo=cuadro&firma=…&otros=…)."""
    f = contexto['f']
    g = request.GET
    quienes = g.getlist('firma') if g.get('cambiar') else None
    otros = g.get('otros') if g.get('cambiar') else None
    estilo = g.get('estilo') if g.get('estilo') in dict(fmt.ESTILOS_FIRMA) else f['firmas']['estilo']
    contexto.update({'firmas': fmt.firmantes(piar, f, doc, quienes, otros), 'estilo_firma': estilo})
    return contexto


@login_required
def pdf(request, pk):
    piar = _piar(request, pk)
    if not (logica.puede_ver(request, piar) or _es_su_familia(request, piar)):
        return HttpResponseForbidden('No tiene acceso a este PIAR.')
    return _pdf(request, 'piar/pdf_piar.html', _con_firmas(request, piar, _contexto_pdf(piar), 'piar'),
                f'PIAR {piar.ano_lectivo} {piar.estudiante.user.get_full_name()}')


@login_required
def acta_pdf(request, pk):
    piar = _piar(request, pk)
    if not (logica.puede_ver(request, piar) or _es_su_familia(request, piar)):
        return HttpResponseForbidden('No tiene acceso a este PIAR.')
    return _pdf(request, 'piar/pdf_acta.html', _con_firmas(request, piar, _contexto_pdf(piar), 'acta'),
                f'Acta de acuerdo PIAR {piar.estudiante.user.get_full_name()}')


@login_required
def mi_piar(request):
    piars = Piar.objects.filter(colegio=request.colegio, estudiante__user=request.user, compartido_familia=True)
    return render(request, 'piar/mi_piar.html', {'colegio': request.colegio, 'piars': piars})
