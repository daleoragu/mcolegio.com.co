# notas/forms/observador_forms.py
from django import forms
from ..models import FichaEstudiante, RegistroObservador

class FichaEstudianteForm(forms.ModelForm):
    def clean_numero_documento(self):
        documento = self.cleaned_data.get('numero_documento')
        if not documento or str(documento).strip() == '':
            return None  # Permite nulos en BD para evitar errores de unicidad duplicada
        return documento

    class Meta:
        model = FichaEstudiante
        exclude = ['estudiante']
        widgets = {
            # 👇 CORRECCIÓN APLICADA AQUÍ 👇
            'fecha_nacimiento': forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date', 'class': 'form-control'}),
            'lugar_nacimiento': forms.TextInput(attrs={'class': 'form-control'}),
            'foto': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'eps': forms.TextInput(attrs={'class': 'form-control'}),
            'grupo_sanguineo': forms.Select(attrs={'class': 'form-select'}),
            'enfermedades_alergias': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'nombre_padre': forms.TextInput(attrs={'class': 'form-control'}),
            'celular_padre': forms.TextInput(attrs={'class': 'form-control'}),
            'nombre_madre': forms.TextInput(attrs={'class': 'form-control'}),
            'celular_madre': forms.TextInput(attrs={'class': 'form-control'}),
            'nombre_acudiente': forms.TextInput(attrs={'class': 'form-control'}),
            'celular_acudiente': forms.TextInput(attrs={'class': 'form-control'}),
            'email_acudiente': forms.EmailInput(attrs={'class': 'form-control'}),
            'colegio_anterior': forms.TextInput(attrs={'class': 'form-control'}),
            'grado_anterior': forms.TextInput(attrs={'class': 'form-control'}),
            'espera_en_porteria': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'compromiso_padre': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'compromiso_estudiante': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'tipo_documento': forms.Select(attrs={'class': 'form-select'}),
            'numero_documento': forms.TextInput(attrs={'class': 'form-control'}),
        }

class RegistroObservadorForm(forms.ModelForm):
    # El subtipo (positiva / a mejorar) ahora aplica también a las anotaciones
    # ACADÉMICAS, no solo a las de comportamiento: se trata igual de reconocer
    # lo bueno que de dejar constancia de lo que falta.
    #
    # Se deja opcional a propósito. Si el docente no lo marca en una académica,
    # las estadísticas lo deducen del promedio del estudiante en ese periodo
    # (ver notas/estadisticas_observador.py). En convivencia no se deduce nada.
    subtipo = forms.ChoiceField(
        choices=[('', '--- Seleccione (opcional) ---')] + RegistroObservador.SUBTIPO_CHOICES,
        required=False,
        label="¿Es positiva o a mejorar?",
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    class Meta:
        model = RegistroObservador
        fields = ['fecha_suceso', 'tipo', 'subtipo', 'tipo_falta', 'descripcion']
        widgets = {
            # Forzamos a Django a esperar formato de fecha estándar de navegadores modernos
            'fecha_suceso': forms.DateInput(
                format='%Y-%m-%d',
                attrs={'type': 'date', 'class': 'form-control'}
            ),
            'tipo': forms.Select(attrs={'class': 'form-select'}),
            'tipo_falta': forms.Select(attrs={'class': 'form-select'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': 'Describa detalladamente el suceso...'}),
        }
        help_texts = {
            'descripcion': 'Este texto le llega a la familia por correo y WhatsApp. '
                           'Evite escribir el nombre completo de otros estudiantes.',
        }

    falta = forms.IntegerField(required=False, widget=forms.HiddenInput(attrs={'id': 'falta_catalogo'}))

    def __init__(self, *args, colegio=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.colegio = colegio
        self.fields['tipo_falta'].label = 'Tipo de falta (manual de convivencia)'
        self.fields['tipo_falta'].choices = [('', '--- No aplica ---')] + list(RegistroObservador._meta.get_field('tipo_falta').choices)
        if self.instance and self.instance.falta_id:
            self.initial.setdefault('falta', self.instance.falta_id)

    def clean(self):
        datos = super().clean()
        from ..models import FaltaCatalogo
        fid = datos.get('falta')
        falta = None
        if fid and self.colegio is not None:
            falta = FaltaCatalogo.objects.filter(colegio=self.colegio, id=fid).first()
        self.instance.falta = falta
        if falta and not datos.get('tipo_falta'):
            datos['tipo_falta'] = falta.tipo_falta
            self.instance.tipo_falta = falta.tipo_falta
        return datos


class EstudianteCompromisoForm(forms.ModelForm):
    compromiso_estudiante = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 5}), 
        label="Mi Compromiso para este año lectivo:", 
        help_text="Describe aquí tus metas y a qué te comprometes para mejorar académicamente y como persona.", 
        required=False
    )
    class Meta:
        model = FichaEstudiante
        fields = ['compromiso_estudiante']