# notas/views/componentes_views.py
"""Componentes de evaluación: cómo se llaman en este colegio las tres columnas de nota.

No todos los colegios dicen SER, SABER y HACER. Lo que se escribe aquí es lo que
sale en el encabezado del boletín y, por defecto, en las planillas (en línea,
Excel y PDF), en el ingreso de notas y en PuntoExacto. Una asignatura puede
tener nombres propios; si los deja en SER/SABER/HACER, usa los del colegio.
"""
from django import forms
from django.contrib import messages
from django.http import HttpResponseNotFound
from django.shortcuts import redirect, render

from ..models import Materia
from ..models.academicos import ConfiguracionCalificaciones
from ..permisos import admin_requerido

CODIGOS = (('ser', 'SER'), ('saber', 'SABER'), ('hacer', 'HACER'))


class ComponentesForm(forms.ModelForm):
    class Meta:
        model = ConfiguracionCalificaciones
        fields = ['etiqueta_ser', 'abreviatura_ser', 'etiqueta_saber', 'abreviatura_saber',
                  'etiqueta_hacer', 'abreviatura_hacer']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for nombre, campo in self.fields.items():
            campo.widget.attrs.update({'class': 'form-control', 'autocomplete': 'off'})
            if nombre.startswith('abreviatura'):
                campo.widget.attrs['placeholder'] = 'Opcional'
                campo.required = False
            else:
                campo.required = True

    def clean(self):
        datos = super().clean()
        nombres = [(datos.get(f'etiqueta_{c}') or '').strip() for c, _ in CODIGOS]
        for c, _ in CODIGOS:
            datos[f'etiqueta_{c}'] = (datos.get(f'etiqueta_{c}') or '').strip()
            datos[f'abreviatura_{c}'] = (datos.get(f'abreviatura_{c}') or '').strip()
        vistos = [n.upper() for n in nombres if n]
        if len(vistos) != len(set(vistos)):
            raise forms.ValidationError('Cada componente debe tener un nombre distinto.')
        return datos


def _materias_con_nombres_propios(colegio):
    salida = []
    for m in Materia.objects.filter(colegio=colegio).order_by('nombre'):
        propios = [(getattr(m, f'etiqueta_{c}', '') or '').strip() for c, _ in CODIGOS]
        if any(p and p.upper() != cod for p, (_, cod) in zip(propios, CODIGOS)):
            salida.append({'materia': m, 'nombres': propios})
    return salida


@admin_requerido
def componentes_evaluacion(request):
    colegio = getattr(request, 'colegio', None)
    if colegio is None:
        return HttpResponseNotFound('<h1>Colegio no configurado</h1>')
    config, _ = ConfiguracionCalificaciones.objects.get_or_create(colegio=colegio)

    if request.method == 'POST' and request.POST.get('accion') == 'unificar':
        # Las asignaturas vuelven a los nombres del colegio.
        n = Materia.objects.filter(colegio=colegio).update(etiqueta_ser='SER', etiqueta_saber='SABER',
                                                           etiqueta_hacer='HACER')
        messages.success(request, f'Listo: {n} asignatura(s) usan ahora los nombres del colegio.')
        return redirect('notas:componentes_evaluacion')

    form = ComponentesForm(request.POST or None, instance=config)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Nombres guardados. Ya salen en el boletín, las planillas y el ingreso de notas.')
        return redirect('notas:componentes_evaluacion')

    filas = [{'codigo': cod, 'nombre': form[f'etiqueta_{c}'], 'abreviatura': form[f'abreviatura_{c}']}
             for c, cod in CODIGOS]
    return render(request, 'notas/admin_tools/componentes_evaluacion.html', {
        'form': form, 'filas': filas, 'propias': _materias_con_nombres_propios(colegio),
        'page_title': 'Componentes de evaluación'})
