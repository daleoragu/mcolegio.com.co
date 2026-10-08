# -*- coding: utf-8 -*-
from django import forms

from notas.models import Curso, PeriodoAcademico, Sede

from .models import Acta


class ActaForm(forms.ModelForm):
    class Meta:
        model = Acta
        fields = ['titulo', 'fecha', 'hora_inicio', 'hora_fin', 'lugar', 'periodo', 'alcance', 'sede', 'cursos',
                  'mostrar_observador', 'orden_del_dia', 'desarrollo', 'decisiones', 'asistentes']
        widgets = {
            'fecha': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
            'hora_inicio': forms.TimeInput(attrs={'type': 'time'}, format='%H:%M'),
            'hora_fin': forms.TimeInput(attrs={'type': 'time'}, format='%H:%M'),
            'cursos': forms.CheckboxSelectMultiple,
            'alcance': forms.RadioSelect,
            'orden_del_dia': forms.Textarea(attrs={'rows': 5}),
            'desarrollo': forms.Textarea(attrs={'rows': 12}),
            'decisiones': forms.Textarea(attrs={'rows': 5}),
            'asistentes': forms.Textarea(attrs={'rows': 8}),
        }

    def __init__(self, *args, colegio=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.colegio = colegio
        comision = self.instance.tipo == Acta.COMISION
        if comision:
            self.fields['periodo'].queryset = PeriodoAcademico.objects.filter(colegio=colegio).order_by(
                '-ano_lectivo', '-fecha_inicio')
            self.fields['periodo'].required = True
            self.fields['cursos'].queryset = Curso.objects.filter(colegio=colegio).order_by('grado', 'nombre')
            self.fields['sede'].queryset = Sede.objects.filter(colegio=colegio)
            self.fields['sede'].required = False
            self.fields['sede'].empty_label = 'Todas las sedes'
            self.fields['alcance'].choices = Acta.ALCANCES
        else:
            for f in ('periodo', 'alcance', 'sede', 'cursos', 'mostrar_observador'):
                del self.fields[f]
        if 'mostrar_observador' in self.fields:
            self.fields['mostrar_observador'].widget.attrs['class'] = 'form-check-input'
        for nombre, campo in self.fields.items():
            if isinstance(campo.widget, (forms.CheckboxSelectMultiple, forms.RadioSelect, forms.CheckboxInput)):
                continue
            campo.widget.attrs.setdefault('class', 'form-select' if isinstance(campo.widget, forms.Select)
                                          else 'form-control')

    def clean(self):
        datos = super().clean()
        if self.instance.tipo == Acta.COMISION and not datos.get('cursos'):
            self.add_error('cursos', 'Escoja al menos un curso.')
        return datos
