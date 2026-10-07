# notas/forms/admin_crud_forms.py
from django import forms
from django.contrib.auth.models import User
from django.db.models import Q
from ..models.perfiles import (
    Estudiante, FichaEstudiante, Curso, Docente, FichaDocente, Colegio, Sede
)
from ..models.academicos import (
    AreaConocimiento, Materia, EscalaValoracion
)

# --- WIDGET PERSONALIZADO PARA INPUT DE COLOR ---
class ColorInput(forms.TextInput):
    input_type = 'color'

# ==============================================================================
# FORMULARIOS PARA GESTIÓN DE DOCENTES (LÓGICA DE GUARDADO CORREGIDA)
# ==============================================================================

class AdminCrearDocenteForm(forms.Form):
    """Formulario para que el admin cree un nuevo docente."""
    nombres = forms.CharField(label="Nombres Completos", max_length=150, widget=forms.TextInput(attrs={'class': 'form-control'}))
    apellidos = forms.CharField(label="Apellidos Completos", max_length=150, widget=forms.TextInput(attrs={'class': 'form-control'}))
    email = forms.EmailField(label="Correo Electrónico (Opcional)", required=False, widget=forms.EmailInput(attrs={'class': 'form-control'}))
    numero_documento = forms.CharField(label="Número de Documento (Opcional)", required=False, max_length=20, widget=forms.TextInput(attrs={'class': 'form-control'}))

    def clean_nombres(self):
        return self.cleaned_data.get('nombres', '').strip().upper()

    def clean_apellidos(self):
        return self.cleaned_data.get('apellidos', '').strip().upper()

class AdminEditarDocenteForm(forms.ModelForm):
    """
    Formulario para que el admin edite la ficha de un docente.
    Esta versión corregida asegura que tanto los datos del usuario como la foto se guarden.
    """
    first_name = forms.CharField(label="Nombres", widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(label="Apellidos", widget=forms.TextInput(attrs={'class': 'form-control'}))
    email = forms.EmailField(label="Correo Electrónico", required=False, widget=forms.EmailInput(attrs={'class': 'form-control'}))
    is_active = forms.BooleanField(required=False, label="¿Usuario Activo?", widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}))
    
    class Meta:
        model = FichaDocente
        fields = ['numero_documento', 'telefono', 'direccion', 'titulo_profesional', 'foto']
        widgets = {
            'numero_documento': forms.TextInput(attrs={'class': 'form-control'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control'}),
            'direccion': forms.TextInput(attrs={'class': 'form-control'}),
            'titulo_profesional': forms.TextInput(attrs={'class': 'form-control'}),
            'foto': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        self.docente = kwargs.pop('docente', None)
        super().__init__(*args, **kwargs)

        if self.docente:
            self.fields['first_name'].initial = self.docente.user.first_name
            self.fields['last_name'].initial = self.docente.user.last_name
            self.fields['email'].initial = self.docente.user.email
            self.fields['is_active'].initial = self.docente.user.is_active

    def save(self, commit=True):
        ficha = super().save(commit=False)
        user = self.docente.user
        user.first_name = self.cleaned_data['first_name'].upper()
        user.last_name = self.cleaned_data['last_name'].upper()
        user.email = self.cleaned_data['email']
        user.is_active = self.cleaned_data['is_active']
        
        if commit:
            user.save()
            ficha.save()
            
        return ficha

# ==============================================================================
# FORMULARIOS PARA GESTIÓN DE ESTUDIANTES
# ==============================================================================

class AdminCrearEstudianteForm(forms.Form):
    """Formulario para que el admin cree un nuevo estudiante."""
    nombres = forms.CharField(label="Nombres Completos", max_length=150, widget=forms.TextInput(attrs={'class': 'form-control'}))
    apellidos = forms.CharField(label="Apellidos Completos", max_length=150, widget=forms.TextInput(attrs={'class': 'form-control'}))
    tipo_documento = forms.ChoiceField(label="Tipo de Documento (Opcional)", required=False, choices=FichaEstudiante.TIPO_DOCUMENTO_CHOICES, widget=forms.Select(attrs={'class': 'form-select'}))
    numero_documento = forms.CharField(label="Número de Documento (Opcional)", required=False, max_length=20, widget=forms.TextInput(attrs={'class': 'form-control'}))
    curso = forms.ModelChoiceField(label="Asignar al Curso", queryset=Curso.objects.none(), widget=forms.Select(attrs={'class': 'form-select'}))
    
    es_inclusion = forms.BooleanField(label="¿Estudiante de Inclusión?", required=False, widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}))
    
    def __init__(self, *args, **kwargs):
        colegio = kwargs.pop('colegio', None)
        super().__init__(*args, **kwargs)
        if colegio:
            self.fields['curso'].queryset = Curso.objects.filter(colegio=colegio).order_by('nombre')

    def clean_nombres(self):
        return self.cleaned_data.get('nombres', '').upper()

    def clean_apellidos(self):
        return self.cleaned_data.get('apellidos', '').upper()

class AdminEditarEstudianteForm(forms.ModelForm):
    """
    Formulario para que el admin edite la ficha de un estudiante.
    """
    first_name = forms.CharField(label="Nombres", widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(label="Apellidos", widget=forms.TextInput(attrs={'class': 'form-control'}))
    curso = forms.ModelChoiceField(queryset=Curso.objects.none(), label="Curso", widget=forms.Select(attrs={'class': 'form-select'}))
    is_active = forms.BooleanField(required=False, label="¿Estudiante Activo?", widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}))
    es_inclusion = forms.BooleanField(required=False, label="Programa de Inclusión", widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}))
    
    class Meta:
        model = FichaEstudiante
        fields = '__all__'
        exclude = ['estudiante']
        widgets = {
            'tipo_documento': forms.Select(attrs={'class': 'form-select'}),
            'numero_documento': forms.TextInput(attrs={'class': 'form-control'}),
            'grupo_sanguineo': forms.Select(attrs={'class': 'form-select'}),
            'foto': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'lugar_nacimiento': forms.TextInput(attrs={'class': 'form-control'}),
            # 👇 CORRECCIÓN APLICADA AQUÍ 👇
            'fecha_nacimiento': forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date', 'class': 'form-control'}),
            'eps': forms.TextInput(attrs={'class': 'form-control'}),
            'enfermedades_alergias': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
            'nombre_padre': forms.TextInput(attrs={'class': 'form-control'}),
            'celular_padre': forms.TextInput(attrs={'class': 'form-control'}),
            'nombre_madre': forms.TextInput(attrs={'class': 'form-control'}),
            'celular_madre': forms.TextInput(attrs={'class': 'form-control'}),
            'nombre_acudiente': forms.TextInput(attrs={'class': 'form-control'}),
            'celular_acudiente': forms.TextInput(attrs={'class': 'form-control'}),
            'email_acudiente': forms.EmailInput(attrs={'class': 'form-control'}),
            'espera_en_porteria': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'colegio_anterior': forms.TextInput(attrs={'class': 'form-control'}),
            'grado_anterior': forms.TextInput(attrs={'class': 'form-control'}),
            'compromiso_padre': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'compromiso_estudiante': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        colegio = kwargs.pop('colegio', None)
        super().__init__(*args, **kwargs)
        
        if colegio:
            self.fields['curso'].queryset = Curso.objects.filter(colegio=colegio).order_by('nombre')
        
        if self.instance and self.instance.pk:
            estudiante_profile = self.instance.estudiante
            self.fields['first_name'].initial = estudiante_profile.user.first_name
            self.fields['last_name'].initial = estudiante_profile.user.last_name
            self.fields['curso'].initial = estudiante_profile.curso
            self.fields['is_active'].initial = estudiante_profile.is_active
            self.fields['es_inclusion'].initial = estudiante_profile.es_inclusion

    def save(self, commit=True):
        ficha = super().save(commit=False)
        estudiante_profile = ficha.estudiante
        user = estudiante_profile.user

        user.first_name = self.cleaned_data['first_name'].upper()
        user.last_name = self.cleaned_data['last_name'].upper()
        estudiante_profile.curso = self.cleaned_data['curso']
        estudiante_profile.is_active = self.cleaned_data['is_active']
        estudiante_profile.es_inclusion = self.cleaned_data['es_inclusion']
        
        if commit:
            user.save()
            estudiante_profile.save()
            ficha.save()
            
        return ficha

# ==============================================================================
# OTROS FORMULARIOS DE ACADÉMICOS Y CONFIGURACIÓN
# ==============================================================================

class CursoForm(forms.ModelForm):
    """Curso con dos etiquetas: el nombre que usa el colegio y el grado.

    * Curso nuevo: el grado es obligatorio. El nivel sale solo del grado.
    * El nombre es libre (7A, 701, 71, 7-1, SÉPTIMO…). Si se deja vacío se arma
      con el grado, el subgrupo y el formato del colegio; sin subgrupo es grado
      único y se llama como el grado.
    * Curso que ya existía sin grado: se puede seguir guardando sin grado, para
      no romper nada; en la promoción se pregunta a dónde pasan sus estudiantes.
    """
    formato_nombre = forms.ChoiceField(
        label='Cómo nombra el colegio sus cursos', required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        help_text='Solo se usa para armar el nombre cuando hay subgrupo y el nombre se deja vacío. '
                  'Viene puesto el que ya usa el colegio.')

    class Meta:
        model = Curso
        fields = ['sede', 'grado', 'subgrupo', 'formato_nombre', 'nombre', 'nivel', 'director_grado']
        widgets = {
            'grado': forms.Select(attrs={'class': 'form-select'}),
            'subgrupo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '1, 2… o A, B…',
                                               'maxlength': 10, 'autocomplete': 'off'}),
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'autocomplete': 'off'}),
            'nivel': forms.Select(attrs={'class': 'form-select'}),
            'director_grado': forms.Select(attrs={'class': 'form-select'}),
            'sede': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        from ..models.perfiles import FORMATOS_NOMBRE, Sede, formato_del_colegio
        colegio = kwargs.pop('colegio', None)
        super().__init__(*args, **kwargs)
        self.colegio = colegio
        if colegio:
            self.fields['director_grado'].queryset = Docente.objects.filter(colegio=colegio).order_by('user__last_name')
        # La sede solo se pregunta si el colegio tiene sedes registradas.
        sedes = Sede.objects.filter(colegio=colegio) if colegio else Sede.objects.none()
        if self.instance.pk and self.instance.sede_id:
            sedes = sedes.filter(Q(activa=True) | Q(pk=self.instance.sede_id))
        else:
            sedes = sedes.filter(activa=True)
        if sedes.exists():
            self.fields['sede'].queryset = sedes
            self.fields['sede'].empty_label = '— Sin sede —'
            self.fields['sede'].help_text = 'En qué sede funciona este curso.'
            if not self.instance.pk and sedes.count() == 1:
                self.fields['sede'].initial = sedes.first().pk
        else:
            del self.fields['sede']

        self.fields['formato_nombre'].choices = FORMATOS_NOMBRE
        self.fields['formato_nombre'].initial = formato_del_colegio(colegio)

        es_nuevo = self.instance.pk is None
        self.fields['nombre'].required = False
        self.fields['nivel'].required = False
        self.fields['subgrupo'].help_text = ('Vacío = grado único: el curso se llama como el grado (SÉPTIMO). '
                                             'Si el grado tiene varios grupos: 1, 2… o A, B…')
        self.fields['nombre'].help_text = ('Escríbalo como lo usa el colegio: 7A, 701, 71, 7-1… '
                                           'Si lo deja vacío se usa el que aparece en gris.')
        if es_nuevo:
            self.fields['grado'].required = True
            # En un curso nuevo el nivel lo decide el grado: no se muestra.
            del self.fields['nivel']
        else:
            self.fields['grado'].required = False
            if self.instance.grado is None:
                self.fields['grado'].help_text = (
                    'Este curso todavía no tiene grado. Puede asignárselo ahora; si no, '
                    'cuando llegue la promoción se le preguntará a qué curso pasan sus estudiantes.')
                self.fields['nivel'].help_text = 'Si escoge un grado, el nivel se pone solo.'
            else:
                del self.fields['nivel']
        self.fields['grado'].choices = [('', '— Escoja el grado —')] + list(self.fields['grado'].choices)[1:]

    def clean_subgrupo(self):
        from ..models.perfiles import normalizar_subgrupo
        return normalizar_subgrupo(self.cleaned_data.get('subgrupo'))

    def clean(self):
        from ..models.perfiles import clave_subgrupo, nombre_curso_sugerido, FORMATO_POR_DEFECTO
        datos = super().clean()
        grado = datos.get('grado')
        subgrupo = datos.get('subgrupo') or ''
        nombre = (datos.get('nombre') or '').strip()
        if grado in ('', None):
            grado = None
            datos['grado'] = None

        if not nombre:
            if grado is None:
                # En un curso nuevo ya falta el grado, que es el error que importa.
                if 'grado' not in self.errors:
                    self.add_error('nombre', 'Escriba el nombre del curso o escoja un grado.')
                return datos
            nombre = nombre_curso_sugerido(grado, subgrupo,
                                           datos.get('formato_nombre') or FORMATO_POR_DEFECTO)
        datos['nombre'] = nombre.upper()

        if self.colegio:
            otros = Curso.objects.filter(colegio=self.colegio).exclude(pk=self.instance.pk)
            if otros.filter(nombre=datos['nombre']).exists():
                self.add_error('nombre', f'Ya existe un curso llamado «{datos["nombre"]}».')
            if grado is not None:
                mia = clave_subgrupo(subgrupo)
                # Grado y subgrupo se repiten entre sedes (Primero en la sede
                # Norte y Primero en la Sur); dentro de una misma sede, no.
                de_grado = otros.filter(grado=grado)
                if 'sede' in self.fields:
                    de_grado = de_grado.filter(sede=datos.get('sede'))
                for c in de_grado:
                    if clave_subgrupo(c.subgrupo) == mia:
                        if mia:
                            self.add_error('subgrupo',
                                           f'«{c.nombre}» ya es ese grado con ese subgrupo. Use otro '
                                           f'subgrupo para que la promoción sepa a cuál mandar a cada '
                                           f'estudiante.')
                        else:
                            self.add_error('subgrupo',
                                           f'Ya existe «{c.nombre}» como grado único de '
                                           f'{c.nombre_grado}. Si este grado va a tener varios grupos, '
                                           f'póngale subgrupo a los dos.')
                        break
        return datos

    def save(self, commit=True):
        curso = super().save(commit=False)
        curso.nombre = self.cleaned_data['nombre']
        if commit:
            curso.save()
        return curso

class AreaConocimientoForm(forms.ModelForm):
    class Meta:
        model = AreaConocimiento
        fields = ['nombre']
        widgets = {'nombre': forms.TextInput(attrs={'class': 'form-control'})}

class MateriaForm(forms.ModelForm):
    area = forms.ModelChoiceField(queryset=AreaConocimiento.objects.none(), required=False, label="Asignar a un Área", widget=forms.Select(attrs={'class': 'form-select'}))
    class Meta:
        model = Materia
        fields = [
            'nombre', 'abreviatura', 'area', 'usar_ponderacion_equitativa', 
            'promedia_en_boletin', 
            'etiqueta_ser', 'porcentaje_ser', 
            'etiqueta_saber', 'porcentaje_saber', 
            'etiqueta_hacer', 'porcentaje_hacer'
        ]
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'abreviatura': forms.TextInput(attrs={'class': 'form-control'}),
            'promedia_en_boletin': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'usar_ponderacion_equitativa': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'etiqueta_ser': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: SER, EXAMEN...'}),
            'etiqueta_saber': forms.TextInput(attrs={'class': 'form-control'}),
            'etiqueta_hacer': forms.TextInput(attrs={'class': 'form-control'}),
            'porcentaje_ser': forms.NumberInput(attrs={'class': 'form-control'}),
            'porcentaje_saber': forms.NumberInput(attrs={'class': 'form-control'}),
            'porcentaje_hacer': forms.NumberInput(attrs={'class': 'form-control'}),
        }
    def __init__(self, *args, **kwargs):
        colegio = kwargs.pop('colegio', None)
        super().__init__(*args, **kwargs)
        if colegio:
            self.fields['area'].queryset = AreaConocimiento.objects.filter(colegio=colegio).order_by('nombre')

class EscalaValoracionForm(forms.ModelForm):
    class Meta:
        model = EscalaValoracion
        exclude = ['colegio']
        widgets = {
            'nombre_desempeno': forms.TextInput(attrs={'class': 'form-control'}),
            'valor_minimo': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'}),
            'valor_maximo': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'}),
            'mensaje_boletin': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

# ==============================================================================
# SEDES
# ==============================================================================

class SedeForm(forms.ModelForm):
    """Datos de una sede. Jornadas y niveles se marcan con casillas."""
    jornadas = forms.MultipleChoiceField(
        label='Jornadas', required=False, widget=forms.CheckboxSelectMultiple,
        choices=[])
    niveles = forms.MultipleChoiceField(
        label='Niveles que ofrece', required=False, widget=forms.CheckboxSelectMultiple,
        choices=[])

    class Meta:
        model = Sede
        fields = ['nombre', 'es_principal', 'codigo_dane', 'encargado', 'direccion', 'barrio',
                  'telefono', 'correo', 'jornadas', 'niveles', 'descripcion', 'foto',
                  'enlace_mapa', 'activa']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'autocomplete': 'off'}),
            'codigo_dane': forms.TextInput(attrs={'class': 'form-control'}),
            'encargado': forms.TextInput(attrs={'class': 'form-control'}),
            'direccion': forms.TextInput(attrs={'class': 'form-control'}),
            'barrio': forms.TextInput(attrs={'class': 'form-control'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control'}),
            'correo': forms.EmailInput(attrs={'class': 'form-control'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'foto': forms.ClearableFileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            'enlace_mapa': forms.URLInput(attrs={'class': 'form-control',
                                                 'placeholder': 'https://maps.app.goo.gl/…'}),
        }

    def __init__(self, *args, **kwargs):
        from ..models.perfiles import Sede
        self.colegio = kwargs.pop('colegio', None)
        super().__init__(*args, **kwargs)
        self.fields['jornadas'].choices = Sede.JORNADAS
        self.fields['niveles'].choices = Sede.NIVELES
        if self.instance.pk:
            self.initial['jornadas'] = [j for j in self.instance.jornadas.split(',') if j]
            self.initial['niveles'] = [n for n in self.instance.niveles.split(',') if n]

    def clean_nombre(self):
        from ..models.perfiles import Sede
        nombre = ' '.join((self.cleaned_data.get('nombre') or '').split())
        if self.colegio and Sede.objects.filter(colegio=self.colegio, nombre__iexact=nombre) \
                .exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError(f'Ya hay una sede llamada «{nombre}».')
        return nombre

    def clean_jornadas(self):
        return ','.join(self.cleaned_data.get('jornadas') or [])

    def clean_niveles(self):
        return ','.join(self.cleaned_data.get('niveles') or [])
