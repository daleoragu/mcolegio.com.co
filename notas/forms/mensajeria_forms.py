# notas/forms/mensajeria_forms.py
from django import forms
from django.contrib.auth.models import User
from django.db.models import Q

from ..models import Mensaje


def rol_de(usuario, colegio=None):
    """«Docente», «Estudiante · 601», «Rector(a)»… para mostrar al lado del nombre."""
    try:
        est = getattr(usuario, 'estudiante', None)
        if est is not None and (colegio is None or est.colegio_id == colegio.id):
            return f'Estudiante · {est.curso.nombre}' if est.curso_id else 'Estudiante'
    except Exception:
        pass
    adm = None
    try:
        adm = usuario.administraciones.filter(colegio=colegio, activo=True).first() if colegio else None
    except Exception:
        adm = None
    if adm:
        return adm.get_cargo_display()
    if getattr(usuario, 'docente', None) is not None:
        return 'Docente'
    return ''


class UserChoiceField(forms.ModelChoiceField):
    colegio = None
    cargos = {}          # {user_id: 'Rector(a)'} de los directivos, leído una sola vez

    def label_from_instance(self, obj):
        nombre = obj.get_full_name() or obj.username
        rol = self.cargos.get(obj.id)
        if not rol:
            est = getattr(obj, 'estudiante', None) if hasattr(obj, 'estudiante') else None
            if est is not None:
                rol = f'Estudiante · {est.curso.nombre}' if est.curso_id else 'Estudiante'
            elif hasattr(obj, 'docente'):
                rol = 'Docente'
        return f'{nombre} ({rol})' if rol else nombre


def destinatarios_posibles(user, colegio):
    """Docentes, estudiantes activos y directivos/administrativos del colegio (menos uno mismo)."""
    return (User.objects.filter(is_active=True)
            .filter(Q(docente__colegio=colegio) | Q(estudiante__colegio=colegio, estudiante__is_active=True)
                    | Q(administraciones__colegio=colegio, administraciones__activo=True))
            .exclude(pk=user.pk).distinct()
            .select_related('estudiante__curso', 'docente').order_by('last_name', 'first_name'))


class MensajeForm(forms.ModelForm):
    """Redactar un mensaje: el destinatario solo puede ser alguien del mismo colegio."""
    destinatario = UserChoiceField(queryset=User.objects.none(), widget=forms.Select(attrs={'class': 'form-select'}),
                                   label='Para', error_messages={'required': 'Escoja a quién le escribe.',
                                                                 'invalid_choice': 'Esa persona no está en el colegio.'})

    class Meta:
        model = Mensaje
        fields = ['destinatario', 'asunto', 'cuerpo']
        widgets = {
            'asunto': forms.TextInput(attrs={'class': 'form-control', 'maxlength': 200, 'placeholder': 'Asunto'}),
            'cuerpo': forms.Textarea(attrs={'class': 'form-control', 'rows': 10, 'placeholder': 'Escriba su mensaje…'}),
        }
        labels = {'asunto': 'Asunto', 'cuerpo': 'Mensaje'}

    def __init__(self, *args, user=None, colegio=None, borrador=False, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['asunto'].required = False
        self.fields['cuerpo'].error_messages['required'] = 'Escriba el mensaje.'
        if user and colegio:
            self.fields['destinatario'].queryset = destinatarios_posibles(user, colegio)
            self.fields['destinatario'].colegio = colegio
            from ..models import AdministradorColegio
            self.fields['destinatario'].cargos = {
                a.user_id: a.get_cargo_display()
                for a in AdministradorColegio.objects.filter(colegio=colegio, activo=True)}
        if borrador:                     # un borrador se guarda aunque todavía no tenga texto
            self.fields['cuerpo'].required = False

    def clean_cuerpo(self):
        cuerpo = (self.cleaned_data.get('cuerpo') or '').strip()
        if self.fields['cuerpo'].required and not cuerpo:
            raise forms.ValidationError('Escriba el mensaje.')
        return cuerpo
