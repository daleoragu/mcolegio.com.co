# notas/views/encabezado_views.py
"""Encabezado de los documentos (boletines, actas, planillas, certificados…), editado por el
propio colegio. Antes solo se podía desde el súper-admin.

Las líneas se imprimen tal cual en los PDF, así que aquí se guardan como TEXTO: se quitan
etiquetas HTML para que nadie pueda meter código o enlaces externos en los documentos.
"""
from django import forms
from django.contrib import messages
from django.http import HttpResponse, HttpResponseNotFound
from django.shortcuts import redirect, render
from django.template.loader import render_to_string
from django.utils.html import strip_tags

from ..models import Colegio
from ..permisos import admin_requerido

LINEAS = range(1, 6)
MAX_LOGO = 2 * 1024 * 1024


def _campos():
    campos = ['logo_izquierdo', 'logo_derecho', 'alto_logos_pdf', 'encabezado_pdf_sin_bordes']
    for k in LINEAS:
        campos += [f'linea_encabezado_{k}', f'linea_encabezado_{k}_fuente', f'linea_encabezado_{k}_tamano',
                   f'linea_encabezado_{k}_negrilla', f'linea_encabezado_{k}_cursiva', f'linea_encabezado_{k}_subrayado']
    return campos


class EncabezadoForm(forms.ModelForm):
    class Meta:
        model = Colegio
        fields = _campos()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for nombre, campo in self.fields.items():
            w = campo.widget
            if isinstance(w, forms.CheckboxInput):
                w.attrs['class'] = 'btn-check'
            elif isinstance(w, forms.Select):
                w.attrs['class'] = 'form-select form-select-sm'
            elif isinstance(w, forms.ClearableFileInput):
                w.attrs.update({'class': 'form-control form-control-sm', 'accept': 'image/png,image/jpeg,image/webp'})
            elif nombre.endswith('_tamano') or nombre == 'alto_logos_pdf':
                w.attrs.update({'class': 'form-control form-control-sm', 'min': 5, 'max': 28 if nombre != 'alto_logos_pdf' else 160})
            else:
                w.attrs.update({'class': 'form-control', 'placeholder': 'Vacía = no sale'})

    def clean(self):
        datos = super().clean()
        for k in LINEAS:
            texto = datos.get(f'linea_encabezado_{k}')
            if texto:
                datos[f'linea_encabezado_{k}'] = ' '.join(strip_tags(texto).split()) or None
            tam = datos.get(f'linea_encabezado_{k}_tamano')
            if tam is not None and not 5 <= tam <= 28:
                self.add_error(f'linea_encabezado_{k}_tamano', 'Entre 5 y 28 puntos.')
        alto = datos.get('alto_logos_pdf')
        if alto is not None and not 20 <= alto <= 160:
            self.add_error('alto_logos_pdf', 'Entre 20 y 160.')
        for logo in ('logo_izquierdo', 'logo_derecho'):
            f = self.files.get(logo)
            if f is not None and f.size > MAX_LOGO:
                self.add_error(logo, 'La imagen pesa más de 2 MB; redúzcala.')
        return datos


@admin_requerido
def encabezado_documentos(request):
    colegio = getattr(request, 'colegio', None)
    if colegio is None:
        return HttpResponseNotFound('<h1>Colegio no configurado</h1>')
    form = EncabezadoForm(request.POST or None, request.FILES or None, instance=colegio)
    if request.method == 'POST':
        if form.is_valid():
            form.save()
            messages.success(request, 'Encabezado guardado. Ya sale así en boletines, actas, planillas y certificados.')
            if request.POST.get('siguiente') == 'pdf':
                return redirect('notas:encabezado_prueba')
            return redirect('notas:encabezado_documentos')
        messages.error(request, 'Revise los campos marcados.')
    filas = [{'k': k, 'texto': form[f'linea_encabezado_{k}'], 'fuente': form[f'linea_encabezado_{k}_fuente'],
              'tamano': form[f'linea_encabezado_{k}_tamano'], 'negrilla': form[f'linea_encabezado_{k}_negrilla'],
              'cursiva': form[f'linea_encabezado_{k}_cursiva'], 'subrayado': form[f'linea_encabezado_{k}_subrayado']}
             for k in LINEAS]
    return render(request, 'notas/admin_tools/encabezado_documentos.html', {
        'form': form, 'filas': filas, 'colegio': colegio, 'page_title': 'Encabezado de documentos'})


@admin_requerido
def encabezado_prueba(request):
    """Un PDF de muestra con el encabezado guardado, tal como sale en los documentos."""
    colegio = getattr(request, 'colegio', None)
    if colegio is None:
        return HttpResponseNotFound('<h1>Colegio no configurado</h1>')
    html = render_to_string('notas/admin_tools/encabezado_prueba_pdf.html', {'colegio': colegio}, request=request)
    try:
        from weasyprint import HTML
    except ImportError:
        return HttpResponse('Falta WeasyPrint en el servidor.', status=500)
    r = HttpResponse(HTML(string=html, base_url=request.build_absolute_uri('/')).write_pdf(), content_type='application/pdf')
    r['Content-Disposition'] = 'inline; filename="encabezado_prueba.pdf"'
    return r
