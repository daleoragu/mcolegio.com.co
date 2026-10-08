# -*- coding: utf-8 -*-
"""PuntoExacto · formularios."""
from django import forms

from notas.models.academicos import AsignacionDocente, PeriodoAcademico
from .models import Examen

CAJA = {'class': 'form-control'}
SELECT = {'class': 'form-select'}


def escala_del_colegio(colegio):
    """(mínima, máxima) de la escala de valoración del colegio, o None si no tiene."""
    from decimal import Decimal
    from notas.models.academicos import EscalaValoracion

    escalas = EscalaValoracion.objects.filter(colegio=colegio)
    if not escalas.exists():
        return None
    minima = min(e.valor_minimo for e in escalas)
    maxima = max(e.valor_maximo for e in escalas)
    if minima >= maxima:
        return None
    return Decimal(minima).quantize(Decimal('0.01')), Decimal(maxima).quantize(Decimal('0.01'))


class ExamenForm(forms.ModelForm):
    class Meta:
        model = Examen
        fields = ['titulo', 'asignacion', 'periodo', 'fecha', 'componente',
                  'numero_preguntas', 'numero_opciones', 'hojas_por_pagina',
                  'mostrar_docente', 'mostrar_fecha', 'metodo',
                  'nota_maxima', 'nota_minima', 'nota_todo_mal', 'nota_nada_marcado']
        widgets = {
            'titulo': forms.TextInput(attrs={**CAJA, 'placeholder': 'Números racionales'}),
            'asignacion': forms.Select(attrs=SELECT),
            'periodo': forms.Select(attrs=SELECT),
            'fecha': forms.DateInput(format='%Y-%m-%d',
                                     attrs={**CAJA, 'type': 'date'}),
            'numero_preguntas': forms.NumberInput(attrs={**CAJA, 'min': 1, 'max': 150}),
            'numero_opciones': forms.NumberInput(attrs={**CAJA, 'min': 2, 'max': 10}),
            'hojas_por_pagina': forms.Select(attrs=SELECT),
            'mostrar_docente': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'mostrar_fecha': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'componente': forms.Select(attrs=SELECT),
            'metodo': forms.Select(attrs=SELECT),
            'nota_maxima': forms.NumberInput(attrs={**CAJA, 'step': '0.01'}),
            'nota_minima': forms.NumberInput(attrs={**CAJA, 'step': '0.01'}),
            'nota_todo_mal': forms.NumberInput(attrs={**CAJA, 'step': '0.01'}),
            'nota_nada_marcado': forms.NumberInput(attrs={**CAJA, 'step': '0.01'}),
        }

    def __init__(self, *args, colegio=None, docente=None, **kwargs):
        super().__init__(*args, **kwargs)
        asignaciones = AsignacionDocente.objects.none()
        periodos = PeriodoAcademico.objects.none()
        if colegio:
            asignaciones = AsignacionDocente.objects.filter(colegio=colegio)
            if docente:
                asignaciones = asignaciones.filter(docente=docente)
            asignaciones = asignaciones.select_related('materia', 'curso').order_by(
                'curso__orden', 'materia__nombre')
            periodos = PeriodoAcademico.objects.filter(colegio=colegio).order_by(
                '-ano_lectivo', 'fecha_inicio')
        self.fields['asignacion'].queryset = asignaciones
        self.fields['periodo'].queryset = periodos
        self.fields['asignacion'].empty_label = 'Seleccione asignatura y curso'
        self.fields['periodo'].empty_label = 'Sin periodo'

        # Los componentes del colegio (pueden ser 1, 3, 5…) con sus nombres.
        from notas.componentes import componentes as componentes_colegio
        if colegio:
            opciones = [(c.codigo, c.nombre) for c in componentes_colegio(colegio)]
        else:
            opciones = [('SER', 'SER'), ('SABER', 'SABER'), ('HACER', 'HACER')]
        actual = getattr(self.instance, 'componente', '') if self.instance.pk else ''
        if actual and actual not in {c for c, _ in opciones}:
            opciones.append((actual, actual))
        self.fields['componente'].choices = opciones
        if not self.instance.pk and not self.is_bound:
            codigos = [c for c, _ in opciones]
            self.initial['componente'] = 'SABER' if 'SABER' in codigos else codigos[0]

        # En un colegio la escala ya está definida en la plataforma (escala de
        # valoración): pedirla otra vez sobra y abre la puerta a que no cuadre
        # con el boletín. Solo el docente suelto, sin colegio, la escribe.
        self.escala = escala_del_colegio(colegio) if colegio else None
        if self.escala:
            self.fields.pop('nota_maxima')
            self.fields.pop('nota_minima')

    def save(self, commit=True):
        examen = super().save(commit=False)
        if self.escala:
            examen.nota_minima, examen.nota_maxima = self.escala
        if commit:
            examen.save()
            self.save_m2m()
        return examen

    def clean(self):
        datos = super().clean()
        if self.escala:
            minima, maxima = self.escala
        else:
            maxima, minima = datos.get('nota_maxima'), datos.get('nota_minima')
        if maxima is not None and minima is not None and minima >= maxima:
            self.add_error('nota_minima', 'La nota mínima tiene que ser menor que la máxima.')
        if datos.get('metodo') == 'descuento':
            for campo in ('nota_todo_mal', 'nota_nada_marcado'):
                valor = datos.get(campo)
                if valor is None:
                    continue
                if minima is not None and valor < minima:
                    self.add_error(campo, f'No puede ser menor que la nota mínima ({minima}).')
                if maxima is not None and valor > maxima:
                    self.add_error(campo, f'No puede ser mayor que la nota máxima ({maxima}).')
        return datos
