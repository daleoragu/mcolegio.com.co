import datetime

from django import forms
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseForbidden, HttpResponseNotFound
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from notas import avisos_familia
from notas.models import Curso, Estudiante
from notas.models.perfiles import GRADOS
from notas.permisos import admin_requerido, es_admin

from . import logica
from .models import MESES, Beca, Concepto, ConfiguracionCartera, Pago, ValorPorGrado


# ---------------------------------------------------------------------------
# Formularios
# ---------------------------------------------------------------------------
class ConfigForm(forms.ModelForm):
    meses_pension = forms.TypedMultipleChoiceField(
        choices=[(i + 1, m) for i, m in enumerate(MESES)], coerce=int, widget=forms.CheckboxSelectMultiple,
        label='Meses en que se cobra pensión')

    class Meta:
        model = ConfiguracionCartera
        fields = ['dia_vencimiento', 'meses_pension', 'datos_pago', 'familias_ven_estado', 'exigir_paz_y_salvo']
        widgets = {'dia_vencimiento': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 31}),
                   'datos_pago': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
                   'familias_ven_estado': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
                   'exigir_paz_y_salvo': forms.CheckboxInput(attrs={'class': 'form-check-input'})}


class ConceptoForm(forms.ModelForm):
    class Meta:
        model = Concepto
        fields = ['nombre', 'tipo', 'valor', 'mes_unico', 'activo', 'orden']
        widgets = {'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Pensión, Matrícula…'}),
                   'tipo': forms.Select(attrs={'class': 'form-select'}),
                   'valor': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
                   'mes_unico': forms.Select(choices=[(i + 1, m) for i, m in enumerate(MESES)],
                                             attrs={'class': 'form-select'}),
                   'activo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
                   'orden': forms.NumberInput(attrs={'class': 'form-control', 'min': 0})}


class PagoForm(forms.Form):
    valor = forms.IntegerField(min_value=1, widget=forms.NumberInput(attrs={'class': 'form-control'}))
    fecha = forms.DateField(initial=timezone.localdate, widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'},
                                                                                 format='%Y-%m-%d'))
    medio = forms.ChoiceField(choices=Pago.MEDIOS, widget=forms.Select(attrs={'class': 'form-select'}))
    referencia = forms.CharField(required=False, max_length=80, widget=forms.TextInput(
        attrs={'class': 'form-control', 'placeholder': 'N.º de transacción o comprobante'}))
    observacion = forms.CharField(required=False, max_length=200, widget=forms.TextInput(attrs={'class': 'form-control'}))


# ---------------------------------------------------------------------------
# Administración
# ---------------------------------------------------------------------------
@admin_requerido
def panel(request):
    colegio = request.colegio
    if not colegio:
        return HttpResponseNotFound('<h1>Colegio no configurado</h1>')
    conf = ConfiguracionCartera.de(colegio)
    hoy = timezone.localdate()
    if request.method == 'POST' and request.POST.get('accion') == 'generar':
        ano = int(request.POST.get('ano') or hoy.year)
        meses = [int(m) for m in request.POST.getlist('meses')] or None
        if not Concepto.objects.filter(colegio=colegio, activo=True).exists():
            messages.error(request, 'Primero cree los conceptos de cobro (pensión, matrícula…) en Configuración.')
            return redirect('cartera:configuracion')
        n = logica.generar_cargos(colegio, ano, meses)
        messages.success(request, f'Se generaron {n} cobro{"s" if n != 1 else ""} nuevo{"s" if n != 1 else ""} de {ano}.'
                         if n else 'No faltaba nada por generar: los cobros de esos meses ya estaban.')
        return redirect('cartera:panel')
    curso_id = request.GET.get('curso_id') or ''
    solo_mora = request.GET.get('mora') == '1'
    filas, tot = logica.resumen(colegio, curso_id, solo_mora, hoy)
    return render(request, 'cartera/panel.html', {
        'colegio': colegio, 'conf': conf, 'filas': filas, 'tot': tot, 'curso_id': curso_id, 'solo_mora': solo_mora,
        'cursos': Curso.objects.filter(colegio=colegio).order_by('nombre'), 'ano': hoy.year,
        'meses': [(i + 1, m) for i, m in enumerate(MESES)], 'sin_conceptos': not colegio.conceptos_cobro.exists()})


@admin_requerido
def configuracion(request, concepto_id=None):
    colegio = request.colegio
    conf = ConfiguracionCartera.de(colegio)
    concepto = get_object_or_404(Concepto, pk=concepto_id, colegio=colegio) if concepto_id else None
    grados = sorted({c.grado for c in Curso.objects.filter(colegio=colegio, grado__isnull=False)})
    nombres = dict((n, nom) for n, nom, _ in GRADOS)
    form_conf = ConfigForm(instance=conf)
    form_concepto = ConceptoForm(instance=concepto, initial=None if concepto else {'activo': True})
    if request.method == 'POST':
        if request.POST.get('que') == 'config':
            form_conf = ConfigForm(request.POST, instance=conf)
            if form_conf.is_valid():
                form_conf.save()
                messages.success(request, 'Configuración guardada.')
                return redirect('cartera:configuracion')
        elif request.POST.get('que') == 'concepto':
            form_concepto = ConceptoForm(request.POST, instance=concepto)
            if form_concepto.is_valid():
                c = form_concepto.save(commit=False)
                c.colegio = colegio
                c.save()
                for g in grados:
                    v = (request.POST.get(f'grado_{g}') or '').replace('.', '').strip()
                    if v.isdigit() and int(v) != c.valor:
                        ValorPorGrado.objects.update_or_create(concepto=c, grado=g, defaults={'valor': int(v)})
                    else:
                        ValorPorGrado.objects.filter(concepto=c, grado=g).delete()
                messages.success(request, f'Concepto «{c.nombre}» guardado.')
                return redirect('cartera:configuracion')
        elif request.POST.get('que') == 'borrar_concepto' and concepto:
            if concepto.cargos.exists():
                concepto.activo = False
                concepto.save(update_fields=['activo'])
                messages.info(request, f'«{concepto.nombre}» ya tiene cobros: quedó inactivo en vez de borrarse.')
            else:
                concepto.delete()
                messages.success(request, 'Concepto eliminado.')
            return redirect('cartera:configuracion')
    valores = {v.grado: v.valor for v in concepto.valores_grado.all()} if concepto else {}
    return render(request, 'cartera/configuracion.html', {
        'colegio': colegio, 'form_conf': form_conf, 'form_concepto': form_concepto, 'concepto': concepto,
        'conceptos': Concepto.objects.filter(colegio=colegio).prefetch_related('valores_grado'),
        'grados': [{'n': g, 'nombre': nombres.get(g, g), 'valor': valores.get(g, '')} for g in grados]})


@admin_requerido
def estudiante(request, pk):
    est = get_object_or_404(Estudiante.objects.select_related('user', 'curso'), pk=pk, colegio=request.colegio)
    form = PagoForm()
    if request.method == 'POST':
        accion = request.POST.get('accion')
        if accion == 'pago':
            form = PagoForm(request.POST)
            if form.is_valid():
                d = form.cleaned_data
                pago = logica.registrar_pago(est, d['valor'], d['fecha'], d['medio'], d['referencia'],
                                             d['observacion'], request.user)
                messages.success(request, f'Pago registrado: recibo N.º {pago.numero} por {logica.pesos(pago.valor)}.')
                return redirect(reverse('cartera:estudiante', args=[est.pk]) + f'?recibo={pago.pk}')
        elif accion == 'beca':
            try:
                pct = int(request.POST.get('porcentaje') or 0)
            except ValueError:
                pct = 0
            if 1 <= pct <= 100:
                concepto = Concepto.objects.filter(pk=request.POST.get('concepto') or 0, colegio=request.colegio).first()
                Beca.objects.create(estudiante=est, concepto=concepto, porcentaje=pct,
                                    motivo=(request.POST.get('motivo') or '')[:120])
                messages.success(request, f'Descuento del {pct} % guardado. Se aplica a los cobros que se generen de aquí en adelante.')
            else:
                messages.error(request, 'Escriba un porcentaje entre 1 y 100.')
            return redirect('cartera:estudiante', pk=est.pk)
        elif accion == 'quitar_beca':
            Beca.objects.filter(pk=request.POST.get('beca'), estudiante=est).delete()
            return redirect('cartera:estudiante', pk=est.pk)
        elif accion == 'generar':
            n = logica.generar_cargos(request.colegio, int(request.POST.get('ano') or timezone.localdate().year),
                                      estudiantes=[est])
            messages.success(request, f'{n} cobro(s) generado(s).' if n else 'No faltaba nada por generar.')
            return redirect('cartera:estudiante', pk=est.pk)
    st = logica.estado(est)
    url = request.build_absolute_uri(reverse('cartera:mi_cuenta'))
    texto = logica.texto_aviso(est, st, url)
    contactos = avisos_familia.contactos(est) if st['vencido'] else []
    for c in contactos:
        c['enlace'] = avisos_familia.enlace_whatsapp(c['numero'], texto)
    return render(request, 'cartera/estudiante.html', {
        'colegio': request.colegio, 'est': est, 'st': st, 'form': form, 'contactos': contactos, 'texto': texto,
        'becas': est.becas.select_related('concepto'), 'conceptos': Concepto.objects.filter(colegio=request.colegio),
        'recibo_nuevo': request.GET.get('recibo'), 'pesos': logica.pesos})


@admin_requerido
@require_POST
def anular(request, pago_id):
    pago = get_object_or_404(Pago, pk=pago_id, colegio=request.colegio, anulado=False)
    logica.anular_pago(pago, request.POST.get('motivo') or '')
    messages.success(request, f'Recibo N.º {pago.numero} anulado.')
    return redirect('cartera:estudiante', pk=pago.estudiante_id)


# ---------------------------------------------------------------------------
# PDF
# ---------------------------------------------------------------------------
def _puede_ver(request, est):
    return es_admin(request) or est.user_id == request.user.id


def _pdf(request, plantilla, contexto, nombre):
    try:
        from weasyprint import HTML
    except ImportError:
        return HttpResponse('La generación de PDF no está disponible en este servidor.', status=500)
    contexto.update({'colegio': request.colegio, 'hoy': timezone.localdate(), 'pesos': logica.pesos})
    html = render_to_string(plantilla, contexto, request=request)
    r = HttpResponse(HTML(string=html, base_url=request.build_absolute_uri('/')).write_pdf(), content_type='application/pdf')
    r['Content-Disposition'] = f'inline; filename="{nombre}.pdf"'
    return r


@login_required
def recibo_pdf(request, pago_id):
    pago = get_object_or_404(Pago.objects.select_related('estudiante__user', 'estudiante__curso'), pk=pago_id,
                             colegio=request.colegio)
    if not _puede_ver(request, pago.estudiante):
        return HttpResponseForbidden('Este recibo no es suyo.')
    aplicaciones = pago.aplicaciones.select_related('cargo')
    return _pdf(request, 'cartera/pdf_recibo.html', {'pago': pago, 'est': pago.estudiante, 'aplicaciones': aplicaciones,
                                                     'a_favor': pago.valor - sum(a.valor for a in aplicaciones)},
                f'Recibo {pago.numero}')


@login_required
def estado_pdf(request, pk):
    est = get_object_or_404(Estudiante.objects.select_related('user', 'curso'), pk=pk, colegio=request.colegio)
    if not _puede_ver(request, est):
        return HttpResponseForbidden('Este estado de cuenta no es suyo.')
    return _pdf(request, 'cartera/pdf_estado.html', {'est': est, 'st': logica.estado(est),
                                                     'conf': ConfiguracionCartera.de(request.colegio)},
                f'Estado de cuenta {est.user.get_full_name()}')


@login_required
def paz_y_salvo_pdf(request, pk):
    est = get_object_or_404(Estudiante.objects.select_related('user', 'curso'), pk=pk, colegio=request.colegio)
    if not _puede_ver(request, est):
        return HttpResponseForbidden('No es suyo.')
    st = logica.estado(est)
    if st['vencido']:
        messages.error(request, f'Tiene un saldo vencido de {logica.pesos(st["vencido"])}: no se puede expedir el paz y salvo.')
        return redirect('cartera:estudiante' if es_admin(request) else 'cartera:mi_cuenta',
                        **({'pk': est.pk} if es_admin(request) else {}))
    from certificados.models import ConfiguracionCertificados
    conf = ConfiguracionCertificados.de(request.colegio)
    firma = conf.firma_nombre.strip() or (request.colegio.admin_general.get_full_name()
                                          if request.colegio.admin_general_id else '')
    return _pdf(request, 'cartera/pdf_paz_y_salvo.html', {'est': est, 'st': st, 'firma': firma, 'cargo': conf.firma_cargo},
                f'Paz y salvo {est.user.get_full_name()}')


# ---------------------------------------------------------------------------
# Familia
# ---------------------------------------------------------------------------
@login_required
def mi_cuenta(request):
    est = Estudiante.objects.filter(user=request.user, colegio=request.colegio).select_related('curso').first()
    if est is None:
        return redirect('notas:dashboard')
    conf = ConfiguracionCartera.de(request.colegio)
    if not conf.familias_ven_estado:
        messages.info(request, 'Para conocer su estado de cuenta, comuníquese con la tesorería del colegio.')
        return redirect('notas:dashboard')
    return render(request, 'cartera/mi_cuenta.html', {'colegio': request.colegio, 'est': est, 'conf': conf,
                                                      'st': logica.estado(est), 'pesos': logica.pesos})
