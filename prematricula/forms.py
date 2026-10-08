# -*- coding: utf-8 -*-
import os

from django import forms

from notas.models import Sede

from .models import Configuracion, PreguntaEncuesta, Requisito, Solicitud

EXTENSIONES = {'.pdf', '.jpg', '.jpeg', '.png', '.webp', '.heic'}
MAX_MB = 6

CAMPOS_ESTUDIANTE = ['nombres', 'apellidos', 'tipo_documento', 'numero_documento', 'fecha_nacimiento',
                     'lugar_nacimiento', 'genero', 'direccion', 'barrio', 'telefono']
CAMPOS_PROCEDENCIA = ['colegio_procedencia', 'ultimo_grado']
CAMPOS_SALUD = ['eps', 'rh', 'alergias', 'necesita_apoyo', 'apoyo_detalle',
                'emergencia_nombre', 'emergencia_telefono', 'emergencia_parentesco']
CAMPOS_FAMILIA = ['acudiente_nombre', 'acudiente_documento', 'acudiente_parentesco', 'acudiente_celular',
                  'acudiente_correo', 'acudiente_ocupacion', 'madre_nombre', 'madre_celular',
                  'padre_nombre', 'padre_celular']


class SolicitudForm(forms.ModelForm):
    """Lo que llena la familia. Los archivos y la encuesta se agregan según el colegio."""
    acepta = forms.BooleanField(required=True, label='Acepto')

    class Meta:
        model = Solicitud
        fields = ['grado', 'sede', 'jornada'] + CAMPOS_ESTUDIANTE + CAMPOS_PROCEDENCIA + \
            CAMPOS_SALUD + CAMPOS_FAMILIA
        widgets = {
            'fecha_nacimiento': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
            'alergias': forms.Textarea(attrs={'rows': 2}),
        }
        labels = {'telefono': 'Teléfono del estudiante', 'nombres': 'Nombres del estudiante',
                  'apellidos': 'Apellidos del estudiante', 'numero_documento': 'Número de documento',
                  'colegio_procedencia': 'Colegio de donde viene', 'genero': 'Sexo'}

    def __init__(self, *args, colegio=None, tipo='NUEVO', **kwargs):
        super().__init__(*args, **kwargs)
        self.colegio, self.tipo = colegio, tipo
        sedes = Sede.objects.filter(colegio=colegio, activa=True) if colegio else Sede.objects.none()
        if sedes.count() > 1:
            self.fields['sede'].queryset = sedes
            self.fields['sede'].empty_label = 'Cualquiera'
            jornadas = sorted({j for s in sedes for j in s.lista_jornadas()})
        else:
            del self.fields['sede']
            jornadas = sorted({j for s in sedes for j in s.lista_jornadas()})
        if len(jornadas) > 1:
            self.fields['jornada'] = forms.ChoiceField(
                label='Jornada de preferencia', required=False,
                choices=[('', 'Cualquiera')] + [(j, j) for j in jornadas])
        else:
            del self.fields['jornada']
        if tipo == 'ANTIGUO':
            for c in CAMPOS_PROCEDENCIA:
                del self.fields[c]
            self.fields['numero_documento'].disabled = True
        self.fields['grado'].choices = [('', '— Escoja el grado —')] + list(self.fields['grado'].choices)[1:]
        self.fields['genero'].choices = [('', '— Seleccione —')] + list(self.fields['genero'].choices)[1:]
        self.fields['rh'].choices = [('', '— Seleccione —')] + list(self.fields['rh'].choices)[1:]
        for nombre in ('acudiente_correo',):
            self.fields[nombre].help_text = 'A este correo le llegan las novedades de la solicitud.'

        # Documentos: un campo por requisito con archivo.
        self.requisitos = [r for r in Requisito.objects.filter(colegio=colegio, activo=True)
                           if r.aplica_a(tipo)] if colegio else []
        for r in self.requisitos:
            if r.pide_archivo:
                self.fields[f'doc_{r.id}'] = forms.FileField(
                    label=r.nombre, required=r.obligatorio, help_text=r.descripcion,
                    widget=forms.ClearableFileInput(attrs={'accept': '.pdf,image/*'}))

        # Encuesta
        self.preguntas = list(PreguntaEncuesta.objects.filter(colegio=colegio, activa=True)) if colegio else []
        for p in self.preguntas:
            nombre = f'enc_{p.id}'
            opciones = [(o, o) for o in p.lista_opciones()]
            if p.tipo == 'TEXTO':
                campo = forms.CharField(widget=forms.Textarea(attrs={'rows': 2}), max_length=1000)
            elif p.tipo == 'VARIAS':
                campo = forms.MultipleChoiceField(choices=opciones, widget=forms.CheckboxSelectMultiple)
            else:
                campo = forms.ChoiceField(choices=opciones, widget=forms.RadioSelect)
            campo.label, campo.required = p.texto, p.obligatoria
            self.fields[nombre] = campo

        for nombre, campo in self.fields.items():
            if isinstance(campo.widget, (forms.CheckboxSelectMultiple, forms.RadioSelect)):
                continue
            if isinstance(campo.widget, forms.CheckboxInput):
                campo.widget.attrs.setdefault('class', 'form-check-input')
            elif isinstance(campo.widget, forms.Select):
                campo.widget.attrs.setdefault('class', 'form-select')
            else:
                campo.widget.attrs.setdefault('class', 'form-control')

    def campos(self, nombres):
        return [self[n] for n in nombres if n in self.fields]

    def campos_documentos(self):
        return [self[f'doc_{r.id}'] for r in self.requisitos if f'doc_{r.id}' in self.fields]

    def campos_encuesta(self):
        return [self[f'enc_{p.id}'] for p in self.preguntas]

    def clean(self):
        datos = super().clean()
        for r in self.requisitos:
            f = datos.get(f'doc_{r.id}')
            if not f:
                continue
            ext = os.path.splitext(f.name)[1].lower()
            if ext not in EXTENSIONES:
                self.add_error(f'doc_{r.id}', 'Suba un PDF o una foto (JPG o PNG).')
            elif f.size > MAX_MB * 1024 * 1024:
                self.add_error(f'doc_{r.id}', f'El archivo pesa más de {MAX_MB} MB.')
        if datos.get('necesita_apoyo') and not datos.get('apoyo_detalle'):
            self.add_error('apoyo_detalle', 'Cuéntenos qué apoyo necesita.')
        return datos

    def encuesta(self):
        return {str(p.id): self.cleaned_data.get(f'enc_{p.id}') for p in self.preguntas
                if self.cleaned_data.get(f'enc_{p.id}') not in (None, '', [])}

    def archivos(self):
        return [(r, self.cleaned_data[f'doc_{r.id}']) for r in self.requisitos
                if self.cleaned_data.get(f'doc_{r.id}')]


class ConfiguracionForm(forms.ModelForm):
    class Meta:
        model = Configuracion
        fields = ['abierta', 'ano_lectivo', 'fecha_cierre', 'permite_antiguos', 'mensaje', 'tratamiento_datos']
        widgets = {
            'ano_lectivo': forms.NumberInput(attrs={'class': 'form-control', 'min': 2024, 'max': 2100}),
            'fecha_cierre': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}, format='%Y-%m-%d'),
            'mensaje': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'tratamiento_datos': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }


class RequisitoForm(forms.ModelForm):
    class Meta:
        model = Requisito
        fields = ['nombre', 'descripcion', 'pide_archivo', 'obligatorio', 'para', 'orden', 'activo']
        widgets = {'nombre': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
                   'descripcion': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
                   'para': forms.Select(attrs={'class': 'form-select form-select-sm'}),
                   'orden': forms.NumberInput(attrs={'class': 'form-control form-control-sm', 'style': 'width:70px'})}


class PreguntaForm(forms.ModelForm):
    class Meta:
        model = PreguntaEncuesta
        fields = ['texto', 'tipo', 'opciones', 'obligatoria', 'orden', 'activa']
        widgets = {'texto': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
                   'tipo': forms.Select(attrs={'class': 'form-select form-select-sm'}),
                   'opciones': forms.Textarea(attrs={'class': 'form-control form-control-sm', 'rows': 3}),
                   'orden': forms.NumberInput(attrs={'class': 'form-control form-control-sm', 'style': 'width:70px'})}
