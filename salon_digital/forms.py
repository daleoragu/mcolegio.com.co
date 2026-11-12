# salon_digital/forms.py
import re

from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User

from .models import Cuenta, Grupo, PaginaPublicada

EXTENSIONES_OK = ('.html', '.htm', '.zip')
PESO_MAXIMO = 60 * 1024 * 1024
DOCUMENTO_OK = ('.pdf', '.jpg', '.jpeg', '.png', '.webp')
DOCUMENTO_MAXIMO = 10 * 1024 * 1024

CAJA = {'class': 'form-control'}
SELECTOR = {'class': 'form-select'}

RESERVADOS = {
    'admin', 'api', 'panel', 'static', 'media', 'salon', 'salon_digital', 'p',
    'entrar', 'salir', 'registro', 'cuenta', 'ayuda', 'soporte', 'blog', 'www',
}


def _validar_subida(archivo):
    nombre = (archivo.name or '').lower()
    if not nombre.endswith(EXTENSIONES_OK):
        raise forms.ValidationError('El archivo debe ser .html, .htm o .zip.')
    if archivo.size > PESO_MAXIMO:
        raise forms.ValidationError(
            f'El archivo pesa {archivo.size / 1024 / 1024:.1f} MB y el máximo es 60 MB.')
    return archivo


def _validar_usuario(slug, pk=None):
    slug = (slug or '').strip().lower()
    if not re.fullmatch(r'[a-z0-9][a-z0-9-]{2,39}', slug):
        raise forms.ValidationError(
            'Usa entre 3 y 40 caracteres: letras sin tildes, números y guiones.')
    if slug in RESERVADOS:
        raise forms.ValidationError(f'"{slug}" está reservado. Escoge otro.')
    if Cuenta.objects.filter(slug=slug).exclude(pk=pk).exists():
        raise forms.ValidationError('Ese nombre de usuario ya está tomado.')
    return slug


# ---------------------------------------------------------------------------
# Región: País → Departamento → Municipio (DANE · DIVIPOLA)
# ---------------------------------------------------------------------------
class RegionMixin:
    """Agrega al formulario el menú encadenado de la región. En Colombia se escoge el municipio de la lista oficial
    (se guarda su código DANE y el nombre oficial); de otro país se escriben el país y la ciudad."""
    region_obligatoria = True

    def _campos_region(self, cuenta=None):
        from . import regiones as R
        datos = self.data if self.is_bound else {}
        pais = (datos.get('pais') if datos else None) or ('otro' if cuenta and cuenta.pais and cuenta.pais != R.PAIS else R.PAIS)
        mun = (datos.get('municipio_dane') if datos else None) or (cuenta.municipio_dane if cuenta else '')
        dep = (datos.get('departamento_dane') if datos else None) or (mun[:2] if mun else '')
        self.fields['pais'] = forms.ChoiceField(label='País', choices=[(R.PAIS, 'Colombia'), ('otro', 'Otro país')], initial=pais,
                                                widget=forms.Select(attrs={**CAJA, 'class': 'form-select mm-region-pais'}))
        self.fields['departamento_dane'] = forms.ChoiceField(
            label='Departamento', required=False, initial=dep,
            choices=[('', 'Escoja el departamento…')] + [(c, n) for c, n in R.departamentos()],
            widget=forms.Select(attrs={'class': 'form-select mm-region-dep'}))
        self.fields['municipio_dane'] = forms.CharField(
            label='Municipio', required=False, initial=mun,
            widget=forms.Select(attrs={'class': 'form-select mm-region-mun'},
                                choices=[('', 'Escoja primero el departamento' if not dep else 'Escoja el municipio…')]
                                + [(m['codigo'], m['nombre']) for m in R.municipios(dep)]))
        self.fields['pais_otro'] = forms.CharField(
            label='País y ciudad', required=False, max_length=100, initial=(cuenta.municipio if cuenta and pais == 'otro' else ''),
            widget=forms.TextInput(attrs={**CAJA, 'class': 'form-control mm-region-otro', 'placeholder': 'Ej.: Ecuador, Quito'}))

    def _limpiar_region(self, datos):
        from . import regiones as R
        if datos.get('pais') == 'otro':
            lugar = ' '.join((datos.get('pais_otro') or '').split())
            if self.region_obligatoria and len(lugar) < 3:
                self.add_error('pais_otro', 'Escriba su país y su ciudad.')
            pais, _, ciudad = lugar.partition(',')
            datos.update(region_pais=pais.strip()[:60] or 'Otro', region_mun='', region_nombre=(ciudad.strip() or lugar)[:100],
                         region_dep='')
            return datos
        cod = datos.get('municipio_dane') or ''
        m = R.municipio(cod)
        if not m:
            if self.region_obligatoria or cod:
                self.add_error('municipio_dane', 'Escoja su municipio de la lista.')
            datos.update(region_pais=R.PAIS, region_mun='', region_nombre='', region_dep='')
            return datos
        if datos.get('departamento_dane') and datos['departamento_dane'] != m['dep']:
            self.add_error('municipio_dane', 'Ese municipio no es del departamento escogido.')
        datos.update(region_pais=R.PAIS, region_mun=cod, region_nombre=m['nombre'], region_dep=R.nombre_departamento(cod))
        return datos

    def guardar_region(self, cuenta):
        d = self.cleaned_data
        cuenta.pais, cuenta.municipio_dane = d.get('region_pais', 'Colombia'), d.get('region_mun', '')
        cuenta.municipio, cuenta.departamento = d.get('region_nombre', ''), d.get('region_dep', '')


# ---------------------------------------------------------------------------
# Cuentas
# ---------------------------------------------------------------------------

class RegistroForm(RegionMixin, UserCreationForm):
    nombre_publico = forms.CharField(
        label='Tu nombre', max_length=120, widget=forms.TextInput(attrs=CAJA))
    slug = forms.CharField(
        label='Nombre de usuario', max_length=40, widget=forms.TextInput(
            attrs={**CAJA, 'placeholder': 'davidramos'}),
        help_text='Es lo que va en el enlace de tus páginas: mcolegio.com.co/p/<b>davidramos</b>/')
    email = forms.EmailField(label='Correo', widget=forms.EmailInput(attrs=CAJA))
    institucion = forms.CharField(
        label='Institución donde trabajas', max_length=200, required=False,
        widget=forms.TextInput(attrs=CAJA))

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']
        widgets = {'username': forms.TextInput(attrs=CAJA)}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for campo in ('username', 'password1', 'password2'):
            self.fields[campo].widget.attrs.update(CAJA)
        self.fields['username'].label = 'Usuario para entrar'
        self._campos_region()

    def clean(self):
        return self._limpiar_region(super().clean())

    def clean_slug(self):
        return _validar_usuario(self.cleaned_data.get('slug'))

    def clean_email(self):
        correo = self.cleaned_data['email'].strip().lower()
        if User.objects.filter(email__iexact=correo).exists():
            raise forms.ValidationError('Ya hay una cuenta con ese correo.')
        return correo

    def save(self, commit=True):
        usuario = super().save(commit=False)
        usuario.email = self.cleaned_data['email']
        usuario.first_name = self.cleaned_data['nombre_publico'][:150]
        if commit:
            usuario.save()
        return usuario


class EntrarForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for campo in self.fields.values():
            campo.widget.attrs.update(CAJA)
        self.fields['username'].label = 'Usuario o correo'


class CuentaForm(RegionMixin, forms.ModelForm):
    class Meta:
        model = Cuenta
        fields = ['nombre_publico', 'slug', 'institucion', 'telefono']
        widgets = {
            'nombre_publico': forms.TextInput(attrs=CAJA),
            'slug': forms.TextInput(attrs=CAJA),
            'institucion': forms.TextInput(attrs=CAJA),
            'telefono': forms.TextInput(attrs=CAJA),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._campos_region(self.instance if self.instance.pk else None)
        # el celular al final, después de la región
        self.fields['telefono'] = self.fields.pop('telefono')

    def clean_slug(self):
        return _validar_usuario(self.cleaned_data.get('slug'), self.instance.pk)

    def clean(self):
        return self._limpiar_region(super().clean())

    def save(self, commit=True):
        cuenta = super().save(commit=False)
        self.guardar_region(cuenta)
        if commit:
            cuenta.save()
        return cuenta


class VerificacionForm(forms.ModelForm):
    class Meta:
        model = Cuenta
        fields = ['tipo_documento', 'documento']
        widgets = {
            'tipo_documento': forms.Select(attrs=SELECTOR),
            'documento': forms.ClearableFileInput(
                attrs={**CAJA, 'accept': '.pdf,.jpg,.jpeg,.png,.webp'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['tipo_documento'].required = True
        self.fields['documento'].required = True

    def clean_documento(self):
        doc = self.cleaned_data.get('documento')
        if not doc:
            return doc
        if not (doc.name or '').lower().endswith(DOCUMENTO_OK):
            raise forms.ValidationError('Sube un PDF o una foto (jpg, png, webp).')
        if doc.size > DOCUMENTO_MAXIMO:
            raise forms.ValidationError('El documento no puede pasar de 10 MB.')
        return doc


# ---------------------------------------------------------------------------
# Páginas
# ---------------------------------------------------------------------------

class PaginaForm(forms.ModelForm):
    class Meta:
        model = PaginaPublicada
        fields = [
            'titulo', 'slug', 'descripcion', 'archivo', 'indice',
            'area', 'grado', 'visible', 'abre_en', 'cierra_en',
            'identificacion', 'grupos', 'comentarios', 'compartir_classroom',
            'listar_en_perfil', 'captura_resultados', 'clave_panel',
        ]
        widgets = {
            'titulo': forms.TextInput(attrs={**CAJA, 'placeholder': 'Prueba de matemáticas 7°'}),
            'slug': forms.TextInput(attrs={**CAJA, 'placeholder': 'mate-7 (opcional)'}),
            'descripcion': forms.Textarea(attrs={**CAJA, 'rows': 2}),
            'archivo': forms.ClearableFileInput(attrs={**CAJA, 'accept': '.html,.htm,.zip'}),
            'indice': forms.TextInput(attrs={**CAJA, 'placeholder': 'index.html'}),
            'area': forms.Select(attrs=SELECTOR),
            'grado': forms.NumberInput(attrs={**CAJA, 'min': 0, 'max': 13}),
            'abre_en': forms.DateTimeInput(attrs={**CAJA, 'type': 'datetime-local'},
                                           format='%Y-%m-%dT%H:%M'),
            'cierra_en': forms.DateTimeInput(attrs={**CAJA, 'type': 'datetime-local'},
                                             format='%Y-%m-%dT%H:%M'),
            'clave_panel': forms.TextInput(attrs=CAJA),
            'identificacion': forms.Select(attrs=SELECTOR),
            'comentarios': forms.Select(attrs=SELECTOR),
            'grupos': forms.CheckboxSelectMultiple(),
        }

    def __init__(self, *args, **kwargs):
        self.cuenta = kwargs.pop('cuenta', None)
        super().__init__(*args, **kwargs)
        for campo in ('abre_en', 'cierra_en'):
            self.fields[campo].input_formats = ['%Y-%m-%dT%H:%M', '%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M']
        if self.cuenta is not None:
            self.fields['grupos'].queryset = self.cuenta.grupos.filter(activo=True)
            self.fields['grupos'].required = False
        if self.instance.pk:
            self.fields['archivo'].required = False
            self.fields['archivo'].help_text = 'Déjalo vacío para conservar lo que ya está publicado.'
        else:
            self.fields['archivo'].required = True

    def clean_archivo(self):
        archivo = self.cleaned_data.get('archivo')
        if not archivo:
            return archivo
        archivo = _validar_subida(archivo)
        tope = self.cuenta.limite('mb') if self.cuenta else 60
        if tope and archivo.size > tope * 1024 * 1024:
            raise forms.ValidationError(
                f'Tu plan permite archivos de hasta {tope} MB y este pesa '
                f'{archivo.size / 1024 / 1024:.1f} MB.')
        return archivo

    def clean_slug(self):
        slug = (self.cleaned_data.get('slug') or '').strip().lower()
        if slug in {'panel', 'nueva', 'varias', 'cuenta'}:
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
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('widget', SubidaMultipleWidget(
            attrs={**CAJA, 'multiple': True, 'accept': '.html,.htm,.zip'}))
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        limpiar = super().clean
        if isinstance(data, (list, tuple)):
            return [_validar_subida(limpiar(d, initial)) for d in data]
        return [_validar_subida(limpiar(data, initial))]


class SubidaMultipleForm(forms.Form):
    archivos = SubidaMultipleField(
        label='Archivos',
        help_text='Puedes seleccionar o arrastrar varios a la vez. El nombre de cada archivo '
                  'se usa como título y como dirección.',
    )
    captura_resultados = forms.BooleanField(
        label='Guardar los resultados en Mi Salón Virtual', initial=True, required=False)
    visible = forms.BooleanField(label='Publicarlas de una vez', initial=True, required=False)


class ClaveForm(forms.Form):
    clave = forms.CharField(
        label='Clave de acceso',
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-lg text-center',
            'placeholder': 'Escribe la clave', 'autocomplete': 'off',
        }),
    )


# ---------------------------------------------------------------------------
# Grupos
# ---------------------------------------------------------------------------

class GrupoForm(forms.ModelForm):
    class Meta:
        model = Grupo
        fields = ['nombre', 'descripcion', 'activo', 'pedir_pin']
        widgets = {
            'nombre': forms.TextInput(attrs={**CAJA, 'placeholder': '7-01'}),
            'descripcion': forms.TextInput(
                attrs={**CAJA, 'placeholder': 'Matemáticas · jornada mañana'}),
        }


class ListaIntegrantesForm(forms.Form):
    lista = forms.CharField(
        label='Pega aquí la lista de estudiantes',
        widget=forms.Textarea(attrs={
            **CAJA, 'rows': 10,
            'placeholder': 'Ramos Gutiérrez, David Leonardo\nVargas Daza, Claudia Cecilia\n...',
        }),
        help_text='Uno por línea. Puedes copiarlos directo de tu planilla de Excel. '
                  'Si usas coma, lo de antes son los apellidos; si no, las dos primeras '
                  'palabras se toman como apellidos.',
    )
