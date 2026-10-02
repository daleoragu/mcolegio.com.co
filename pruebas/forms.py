# pruebas/forms.py
from django import forms

from .models import PaginaPublicada

EXTENSIONES_OK = ('.html', '.htm', '.zip')
PESO_MAXIMO = 60 * 1024 * 1024  # 60 MB


def _validar_subida(archivo):
    nombre = (archivo.name or '').lower()
    if not nombre.endswith(EXTENSIONES_OK):
        raise forms.ValidationError('El archivo debe ser .html, .htm o .zip.')
    if archivo.size > PESO_MAXIMO:
        raise forms.ValidationError(
            f'El archivo pesa {archivo.size / 1024 / 1024:.1f} MB y el máximo es 60 MB.'
        )
    return archivo


class PaginaForm(forms.ModelForm):
    class Meta:
        model = PaginaPublicada
        fields = [
            'titulo', 'slug', 'descripcion', 'archivo', 'indice',
            'area', 'grado', 'visible', 'abre_en', 'cierra_en',
            'listar_en_portal', 'captura_resultados', 'clave_panel',
        ]
        widgets = {
            'titulo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Prueba de matemáticas 7°'}),
            'slug': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'mate-7 (opcional)'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'archivo': forms.ClearableFileInput(attrs={'class': 'form-control', 'accept': '.html,.htm,.zip'}),
            'indice': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'index.html'}),
            'area': forms.Select(attrs={'class': 'form-select'}),
            'grado': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'max': 13}),
            'abre_en': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'},
                                           format='%Y-%m-%dT%H:%M'),
            'cierra_en': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'},
                                             format='%Y-%m-%dT%H:%M'),
            'clave_panel': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        self.colegio = kwargs.pop('colegio', None)
        super().__init__(*args, **kwargs)
        for campo in ('abre_en', 'cierra_en'):
            self.fields[campo].input_formats = ['%Y-%m-%dT%H:%M', '%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M']
        if self.instance.pk:
            self.fields['archivo'].required = False
            self.fields['archivo'].help_text = 'Déjalo vacío para conservar lo que ya está publicado.'
        else:
            self.fields['archivo'].required = True

    def clean_archivo(self):
        archivo = self.cleaned_data.get('archivo')
        return _validar_subida(archivo) if archivo else archivo

    def clean_slug(self):
        slug = (self.cleaned_data.get('slug') or '').strip().lower()
        reservados = {'panel', 'nueva', 'varias', 'admin', 'static', 'media', 'api'}
        if slug in reservados:
            raise forms.ValidationError(f'"{slug}" es una dirección reservada. Escoge otra.')
        return slug

    def clean(self):
        datos = super().clean()
        abre, cierra = datos.get('abre_en'), datos.get('cierra_en')
        if abre and cierra and cierra <= abre:
            self.add_error('cierra_en', 'La fecha de cierre debe ser posterior a la de apertura.')
        return datos


class SubidaMultipleWidget(forms.ClearableFileInput):
    """Django no deja poner multiple=True en ClearableFileInput sin declararlo así."""
    allow_multiple_selected = True


class SubidaMultipleField(forms.FileField):
    """Campo de archivo que acepta y valida una lista de archivos."""

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('widget', SubidaMultipleWidget(attrs={
            'class': 'form-control', 'multiple': True, 'accept': '.html,.htm,.zip',
        }))
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        limpiar = super().clean
        if isinstance(data, (list, tuple)):
            return [_validar_subida(limpiar(d, initial)) for d in data]
        return [_validar_subida(limpiar(data, initial))]


class SubidaMultipleForm(forms.Form):
    """Publica varios archivos de una sola vez."""

    archivos = SubidaMultipleField(
        label='Archivos',
        help_text='Puedes seleccionar o arrastrar varios .html a la vez. El nombre de cada archivo '
                  'se usa como título y como dirección.',
    )
    captura_resultados = forms.BooleanField(
        label='Guardar los resultados en la plataforma', initial=True, required=False,
    )
    visible = forms.BooleanField(label='Publicarlas de una vez', initial=True, required=False)


class ClaveForm(forms.Form):
    clave = forms.CharField(
        label='Clave de acceso',
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-lg text-center',
            'placeholder': 'Escribe la clave',
            'autocomplete': 'off',
        }),
    )


class DatosEstudianteForm(forms.Form):
    """Formulario público: los mismos campos del HTML original."""
    apellidos = forms.CharField(
        label='Apellidos', max_length=120,
        widget=forms.TextInput(attrs={'placeholder': 'Escribe tus dos apellidos', 'autocomplete': 'off'}),
    )
    nombres = forms.CharField(
        label='Nombres', max_length=120,
        widget=forms.TextInput(attrs={'placeholder': 'Escribe tus nombres', 'autocomplete': 'off'}),
    )
    grupo = forms.CharField(
        label='Grupo', max_length=30, required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Ejemplo: 7-01', 'autocomplete': 'off'}),
    )