from django import forms
from django.contrib import messages
from django.http import HttpResponse, HttpResponseNotFound
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from notas.models import Curso, Estudiante, FichaEstudiante, Sede
from notas.models.perfiles import GRADOS
from notas.permisos import admin_requerido

from . import codigos as C
from . import formato, importar, logica
from .models import ConfiguracionSimat, DatosSimat

SESION = 'simat_importacion'


class DatosForm(forms.ModelForm):
    tipo_documento = forms.ChoiceField(choices=[('', '—')] + C.TIPO_DOCUMENTO, required=False, label='Tipo de documento')
    numero_documento = forms.CharField(max_length=20, required=False, label='Número de documento')
    fecha_nacimiento = forms.DateField(required=False, label='Fecha de nacimiento',
                                       widget=forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'))
    nuevo = forms.NullBooleanField(required=False, label='Nuevo en la institución', widget=forms.Select(
        choices=[('unknown', 'Calcular solo'), ('true', 'Sí'), ('false', 'No')]))

    class Meta:
        model = DatosSimat
        exclude = ['estudiante', 'actualizado']

    def __init__(self, *args, estudiante=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.estudiante = estudiante
        ficha = getattr(estudiante, 'ficha', None)
        if ficha and not self.is_bound:
            self.initial.update({'tipo_documento': C.TIPO_DESDE_FICHA.get(ficha.tipo_documento, ''),
                                 'numero_documento': ficha.numero_documento or '',
                                 'fecha_nacimiento': ficha.fecha_nacimiento})
        for nombre, campo in self.fields.items():
            w = campo.widget
            if isinstance(w, forms.CheckboxInput):
                w.attrs['class'] = 'form-check-input'
            elif isinstance(w, forms.Select):
                w.attrs['class'] = 'form-select form-select-sm'
            else:
                w.attrs['class'] = 'form-control form-control-sm'
            if nombre.startswith('mpio_'):
                w.attrs.update({'placeholder': 'Código DANE (5 cifras)', 'inputmode': 'numeric', 'maxlength': 5})

    def clean_numero_documento(self):
        doc = importar.documento(self.cleaned_data.get('numero_documento'))
        if doc and FichaEstudiante.objects.filter(numero_documento=doc).exclude(estudiante=self.estudiante).exists():
            raise forms.ValidationError('Ese documento ya lo tiene otro estudiante.')
        return doc

    def save(self, commit=True):
        d = super().save(commit=False)
        d.estudiante = self.estudiante
        d.save()
        ficha, _ = FichaEstudiante.objects.get_or_create(estudiante=self.estudiante)
        cd = self.cleaned_data
        if cd.get('tipo_documento'):
            ficha.tipo_documento = C.FICHA_DESDE_TIPO.get(cd['tipo_documento'], 'OT')
        ficha.numero_documento = cd.get('numero_documento') or None
        if cd.get('fecha_nacimiento'):
            ficha.fecha_nacimiento = cd['fecha_nacimiento']
        ficha.save()
        return d


class ConfigForm(forms.ModelForm):
    class Meta:
        model = ConfiguracionSimat
        fields = ['municipio', 'oficial', 'jornada', 'metodologia', 'fuente_recursos', 'caracter', 'especialidad',
                  'separador', 'codificacion', 'columnas']
        widgets = {'columnas': forms.Textarea(attrs={'rows': 3, 'class': 'form-control form-control-sm font-monospace'}),
                   'municipio': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '73443'}),
                   'oficial': forms.CheckboxInput(attrs={'class': 'form-check-input'})}

    def __init__(self, *a, **k):
        super().__init__(*a, **k)
        for n, f in self.fields.items():
            if isinstance(f.widget, forms.Select):
                f.widget.attrs['class'] = 'form-select'


# ---------------------------------------------------------------------------
# Revisión
# ---------------------------------------------------------------------------
@admin_requerido
def panel(request):
    colegio = request.colegio
    if not colegio:
        return HttpResponseNotFound('<h1>Colegio no configurado</h1>')
    curso_id = request.GET.get('curso_id') or ''
    if request.method == 'POST' and request.POST.get('accion') == 'llenar':
        campo = request.POST.get('campo')
        valor = (request.POST.get('valor') or '').strip()
        validos = {c for c, _, _ in logica.CAMPOS_LLENABLES}
        if campo not in validos or not valor:
            messages.error(request, 'Escoja el dato y el valor.')
        elif campo.startswith('mpio_') and not (valor.isdigit() and len(valor) == 5):
            messages.error(request, 'El municipio va con el código DANE de 5 cifras.')
        else:
            n = logica.llenar_vacios(colegio, campo, valor, request.POST.get('curso_id') or None)
            messages.success(request, f'Se llenó a {n} estudiante{"s" if n != 1 else ""} que lo tenía{"n" if n != 1 else ""} vacío.')
        return redirect(f'{request.path}?curso_id={request.POST.get("curso_id") or ""}')
    ctx, filas = logica.revision(colegio, curso_id or None)
    solo = request.GET.get('ver') or 'incompletos'
    listos = sum(1 for f in filas if not f['faltan'])
    mostrar = [f for f in filas if f['faltan']] if solo == 'incompletos' else filas
    return render(request, 'simat/panel.html', {
        'colegio': colegio, 'filas': mostrar, 'total': len(filas), 'listos': listos, 'incompletos': len(filas) - listos,
        'ver': solo, 'curso_id': curso_id, 'cursos': Curso.objects.filter(colegio=colegio).order_by('orden'),
        'problemas': logica.problemas_del_colegio(colegio), 'conf': ctx.conf,
        'llenables': logica.CAMPOS_LLENABLES, 'ano': ctx.ano})


@admin_requerido
def estudiante(request, pk):
    est = get_object_or_404(Estudiante.objects.select_related('user', 'curso', 'ficha'), pk=pk, colegio=request.colegio)
    d = DatosSimat.objects.filter(estudiante=est).first()
    form = DatosForm(request.POST or None, instance=d, estudiante=est)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, f'Datos SIMAT de {est.user.get_full_name()} guardados.')
        siguiente = request.POST.get('siguiente')
        return redirect(siguiente if siguiente and siguiente.startswith('/simat/') else 'simat:panel')
    est = Estudiante.objects.select_related('user', 'curso__sede', 'ficha', 'simat').get(pk=pk)
    ctx = logica.Contexto(request.colegio)
    ef = logica.efectivos(est, ctx)
    return render(request, 'simat/estudiante.html', {
        'colegio': request.colegio, 'est': est, 'form': form, 'ef': ef, 'faltan': logica.faltantes(ef),
        'siguiente': request.GET.get('siguiente', '')})


@admin_requerido
def configuracion(request):
    conf = ConfiguracionSimat.de(request.colegio)
    sedes = list(Sede.objects.filter(colegio=request.colegio))
    form = ConfigForm(request.POST or None, instance=conf)
    if request.method == 'POST' and form.is_valid():
        conf = form.save(commit=False)
        conf.consecutivos = {str(s.id): (request.POST.get(f'sede_{s.id}') or '').strip().zfill(2)
                             for s in sedes if (request.POST.get(f'sede_{s.id}') or '').strip()}
        if (request.POST.get('sede_') or '').strip():
            conf.consecutivos[''] = request.POST['sede_'].strip().zfill(2)
        conf.discapacidad_piar = {k: request.POST.get(f'disc_{k}') for k, _ in _categorias()
                                  if request.POST.get(f'disc_{k}') and request.POST.get(f'disc_{k}') != C.DISCAPACIDAD_DESDE_PIAR.get(k)}
        conf.save()
        messages.success(request, 'Configuración SIMAT guardada.')
        return redirect('simat:panel')
    cols = formato.columnas(conf)
    return render(request, 'simat/configuracion.html', {
        'colegio': request.colegio, 'form': form, 'conf': conf,
        'sedes': [(s, conf.consecutivos.get(str(s.id), '01' if s.es_principal else '')) for s in sedes],
        'sin_sede': conf.consecutivos.get('', ''),
        'categorias': [(k, n, conf.codigo_discapacidad(k)) for k, n in _categorias()],
        'discapacidades': C.DISCAPACIDAD, 'cols': cols, 'no_reconocidas': [t for c, t in cols if c is None]})


def _categorias():
    try:
        from piar.models import CATEGORIAS
        return CATEGORIAS
    except Exception:
        return []


# ---------------------------------------------------------------------------
# Archivos
# ---------------------------------------------------------------------------
@admin_requerido
def exportar(request):
    colegio = request.colegio
    ctx, filas = logica.revision(colegio, request.GET.get('curso_id') or None)
    if request.GET.get('todos') != '1':
        filas = [f for f in filas if not f['faltan']]
    dane = ''.join(ch for ch in (colegio.dane or '') if ch.isdigit()) or colegio.slug
    nombre = f'SIMAT_{dane}_{timezone.localdate():%Y%m%d}'
    if request.GET.get('formato') == 'xlsx':
        r = HttpResponse(formato.excel_bytes(ctx.conf, filas),
                         content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        r['Content-Disposition'] = f'attachment; filename="{nombre}.xlsx"'
        return r
    r = HttpResponse(formato.zip_bytes(ctx.conf, filas, nombre), content_type='application/zip')
    r['Content-Disposition'] = f'attachment; filename="{nombre}.zip"'
    return r


@admin_requerido
def datos_excel(request):
    colegio = request.colegio
    if request.method == 'POST':
        archivo = request.FILES.get('archivo')
        if not archivo:
            messages.error(request, 'Escoja el archivo.')
            return redirect('simat:panel')
        try:
            n, errores = importar.leer_datos(archivo, colegio)
        except importar.ArchivoInvalido as e:
            messages.error(request, str(e))
            return redirect('simat:panel')
        messages.success(request, f'Se actualizaron los datos de {n} estudiante{"s" if n != 1 else ""}.')
        for e in errores[:15]:
            messages.warning(request, e)
        if len(errores) > 15:
            messages.warning(request, f'… y {len(errores) - 15} filas más con datos por corregir.')
        return redirect('simat:panel')
    _, filas = logica.revision(colegio, request.GET.get('curso_id') or None)
    r = HttpResponse(importar.plantilla_datos(colegio, filas),
                     content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    r['Content-Disposition'] = 'attachment; filename="datos_simat.xlsx"'
    return r


# ---------------------------------------------------------------------------
# Importar desde el SIMAT
# ---------------------------------------------------------------------------
@admin_requerido
def importar_simat(request):
    colegio = request.colegio
    if request.method == 'POST' and request.POST.get('accion') == 'analizar':
        archivo = request.FILES.get('archivo')
        if not archivo:
            messages.error(request, 'Escoja el archivo que descargó del SIMAT.')
            return redirect('simat:importar')
        try:
            analisis = importar.analizar(archivo, colegio)
        except importar.ArchivoInvalido as e:
            messages.error(request, str(e))
            return redirect('simat:importar')
        request.session[SESION] = analisis
        return redirect('simat:importar')
    if request.method == 'POST' and request.POST.get('accion') == 'aplicar':
        analisis = request.session.get(SESION)
        if not analisis:
            return redirect('simat:importar')
        sede = Sede.objects.filter(colegio=colegio, pk=request.POST.get('sede') or 0).first()
        hecho = importar.aplicar(analisis, colegio, crear_nuevos=bool(request.POST.get('crear_nuevos')),
                                 mover_curso=bool(request.POST.get('mover_curso')),
                                 crear_cursos=bool(request.POST.get('crear_cursos')), sede_cursos=sede)
        del request.session[SESION]
        return render(request, 'simat/importado.html', {'colegio': colegio, 'hecho': hecho})
    if request.method == 'POST' and request.POST.get('accion') == 'cancelar':
        request.session.pop(SESION, None)
        return redirect('simat:importar')
    analisis = request.session.get(SESION)
    res = importar.resumen(analisis) if analisis else None
    nombres = {n: nom for n, nom, _ in GRADOS}
    if res:
        res['cursos_faltan'] = [f'{nombres.get(g, g)} {grupo}'.strip() for g, grupo in res['cursos_faltan']]
    return render(request, 'simat/importar.html', {
        'colegio': colegio, 'analisis': analisis, 'res': res,
        'muestra': [r for r in (analisis or {}).get('filas', []) if not r['error']][:12],
        'sedes': Sede.objects.filter(colegio=colegio)})
