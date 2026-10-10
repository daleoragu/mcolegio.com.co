# -*- coding: utf-8 -*-
from django import forms

from notas.models import Curso, PeriodoAcademico, Sede

from .models import Acta


class ActaForm(forms.ModelForm):
    class Meta:
        model = Acta
        fields = ['numero', 'titulo', 'fecha', 'hora_inicio', 'hora_fin', 'lugar', 'periodo', 'alcance', 'sede', 'cursos',
                  'mostrar_observador', 'orden_del_dia', 'desarrollo', 'decisiones', 'estilo_firma']
        widgets = {
            'fecha': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
            'hora_inicio': forms.TimeInput(attrs={'type': 'time'}, format='%H:%M'),
            'hora_fin': forms.TimeInput(attrs={'type': 'time'}, format='%H:%M'),
            'cursos': forms.CheckboxSelectMultiple,
            'alcance': forms.RadioSelect,
            'estilo_firma': forms.RadioSelect,
            'numero': forms.NumberInput(attrs={'min': 1}),
            'orden_del_dia': forms.Textarea(attrs={'rows': 5}),
            'desarrollo': forms.Textarea(attrs={'rows': 12}),
            'decisiones': forms.Textarea(attrs={'rows': 5}),
        }

    def __init__(self, *args, colegio=None, es_admin=False, **kwargs):
        super().__init__(*args, **kwargs)
        self.colegio = colegio
        # El número lo pone la plataforma; solo el administrador lo corrige.
        if not es_admin:
            del self.fields['numero']
        else:
            self.fields['numero'].required = False
        self.fields['estilo_firma'].choices = Acta.ESTILOS_FIRMA
        self.fields['estilo_firma'].required = False
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

    def asistencia_de(self, post):
        """Las filas de la tabla de asistentes: asis_nombre, asis_cargo y asis_x (índices marcados)."""
        nombres, cargos = post.getlist('asis_nombre'), post.getlist('asis_cargo')
        marcados = set(post.getlist('asis_x'))
        filas = []
        for i, (n, c) in enumerate(zip(nombres, cargos)):
            n, c = n.strip()[:150], c.strip()[:150]
            if n or c:
                filas.append({'nombre': n, 'cargo': c, 'asistio': str(i) in marcados})
        return filas[:80]

    def clean_estilo_firma(self):
        return self.cleaned_data.get('estilo_firma') or self.instance.estilo_firma or Acta.CUADRO

    def clean_numero(self):
        numero = self.cleaned_data.get('numero') or self.instance.numero
        otra = (Acta.objects.filter(colegio=self.instance.colegio, ano=self.instance.ano, numero=numero)
                .exclude(id=self.instance.id).first())
        if otra:
            raise forms.ValidationError(f'Ya existe el acta N.º {numero} de {self.instance.ano} («{otra.titulo}»).')
        return numero

    def clean(self):
        datos = super().clean()
        if self.instance.tipo == Acta.COMISION and not datos.get('cursos'):
            self.add_error('cursos', 'Escoja al menos un curso.')
        return datos
