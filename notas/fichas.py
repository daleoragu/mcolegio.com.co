"""Ficha del estudiante: qué puede pedir el estudiante, el antes y el después, y el registro.

* El estudiante (o su familia, con su cuenta) solo pide cambios en sus datos
  personales y de contacto. Nada se guarda hasta que lo autorice la
  administración o el director de grupo.
* Nombres, curso, «activo» e inclusión nunca los toca el estudiante.
* Todo cambio queda en CambioFicha: qué dato, de qué a qué, quién lo hizo y quién lo autorizó.
"""
from django import forms
from django.db import transaction
from django.utils import timezone

from .models import AdministradorColegio, CambioFicha, FichaEstudiante, Notificacion, SolicitudFicha

# Lo que el estudiante puede pedir que se cambie (en este orden se muestra).
CAMPOS_ESTUDIANTE = [
    'foto', 'tipo_documento', 'numero_documento', 'fecha_nacimiento', 'lugar_nacimiento',
    'eps', 'grupo_sanguineo', 'enfermedades_alergias',
    'nombre_madre', 'celular_madre', 'nombre_padre', 'celular_padre',
    'nombre_acudiente', 'celular_acudiente', 'email_acudiente',
]

# Del estudiante (no de la ficha), para el registro de lo que cambia la administración.
CAMPOS_ESTUDIANTE_PERFIL = {
    'first_name': 'Nombres', 'last_name': 'Apellidos', 'curso': 'Curso',
    'is_active': 'Estudiante activo', 'es_inclusion': 'Programa de inclusión',
}

ETIQUETAS = {
    'foto': 'Foto', 'tipo_documento': 'Tipo de documento', 'numero_documento': 'Número de documento',
    'fecha_nacimiento': 'Fecha de nacimiento', 'lugar_nacimiento': 'Lugar de nacimiento', 'eps': 'EPS',
    'grupo_sanguineo': 'Grupo sanguíneo', 'enfermedades_alergias': 'Enfermedades o alergias',
    'nombre_madre': 'Nombre de la madre', 'celular_madre': 'Celular de la madre',
    'nombre_padre': 'Nombre del padre', 'celular_padre': 'Celular del padre',
    'nombre_acudiente': 'Nombre del acudiente', 'celular_acudiente': 'Celular del acudiente',
    'email_acudiente': 'Correo del acudiente', 'espera_en_porteria': 'Espera en portería',
    'colegio_anterior': 'Colegio anterior', 'grado_anterior': 'Grado anterior',
    'compromiso_padre': 'Compromiso del acudiente', 'compromiso_estudiante': 'Compromiso del estudiante',
    **CAMPOS_ESTUDIANTE_PERFIL,
}


class SolicitudFichaForm(forms.ModelForm):
    """Lo que ve el estudiante: solo sus datos personales y de contacto."""

    class Meta:
        model = FichaEstudiante
        fields = CAMPOS_ESTUDIANTE
        widgets = {
            'fecha_nacimiento': forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date'}),
            'enfermedades_alergias': forms.Textarea(attrs={'rows': 2}),
            'foto': forms.ClearableFileInput(attrs={'accept': 'image/*'}),
        }
        labels = {k: v for k, v in ETIQUETAS.items() if k in CAMPOS_ESTUDIANTE}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for nombre, campo in self.fields.items():
            clase = 'form-select' if isinstance(campo.widget, forms.Select) else 'form-control'
            campo.widget.attrs.setdefault('class', clase)
        self.fields['foto'].widget.clear_checkbox_label = 'Quitar la foto'

    def clean_numero_documento(self):
        return (self.cleaned_data.get('numero_documento') or '').strip() or None


# ---------------------------------------------------------------------------
# Antes y después
# ---------------------------------------------------------------------------
def _texto(ficha_o_est, campo, valor):
    """Cómo se lee un valor en el registro."""
    if valor in (None, ''):
        return ''
    if isinstance(valor, bool):
        return 'Sí' if valor else 'No'
    if campo == 'foto':
        return getattr(valor, 'name', str(valor)).split('/')[-1]
    if campo == 'curso':
        return str(valor)
    modelo_campo = None
    try:
        modelo_campo = type(ficha_o_est)._meta.get_field(campo)
    except Exception:
        pass
    if modelo_campo is not None and modelo_campo.choices:
        return dict(modelo_campo.choices).get(valor, str(valor))
    if hasattr(valor, 'strftime'):
        return valor.strftime('%d/%m/%Y')
    return str(valor)


def foto_ficha(ficha, con_perfil=False):
    """{campo: (valor, texto)} de la ficha (y del estudiante, si se pide)."""
    datos = {}
    for f in FichaEstudiante._meta.get_fields():
        if not getattr(f, 'concrete', False) or f.name == 'estudiante':
            continue
        v = getattr(ficha, f.name)
        datos[f.name] = (v.name if f.name == 'foto' else v, _texto(ficha, f.name, v))
    if con_perfil:
        est = ficha.estudiante
        for campo in CAMPOS_ESTUDIANTE_PERFIL:
            v = getattr(est.user, campo) if campo in ('first_name', 'last_name') else getattr(est, campo)
            datos[campo] = (v.pk if campo == 'curso' and v else v, _texto(est, campo, v))
    return datos


def diferencias(antes, despues):
    return [c for c in despues if c in antes and (antes[c][0] or None) != (despues[c][0] or None)]


def registrar(colegio, estudiante, antes, despues, usuario, origen, autorizado_por=None, solicitud=None):
    """Guarda en el registro cada dato que cambió."""
    filas = [CambioFicha(colegio=colegio, estudiante=estudiante, campo=c, etiqueta=ETIQUETAS.get(c, c),
                         antes=antes[c][1][:2000], despues=despues[c][1][:2000], hecho_por=usuario,
                         autorizado_por=autorizado_por, origen=origen, solicitud=solicitud)
             for c in diferencias(antes, despues)]
    CambioFicha.objects.bulk_create(filas)
    return len(filas)


# ---------------------------------------------------------------------------
# Solicitudes
# ---------------------------------------------------------------------------
def autorizadores(estudiante):
    """Administración del colegio y el director de grupo del estudiante."""
    usuarios = {a.user_id: a.user for a in AdministradorColegio.objects.filter(
        colegio=estudiante.colegio, activo=True).select_related('user')}
    curso = estudiante.curso
    if curso is not None and curso.director_grado_id:
        usuarios[curso.director_grado.user_id] = curso.director_grado.user
    return list(usuarios.values())


def puede_autorizar(request, estudiante):
    from .permisos import es_admin
    if estudiante.colegio_id != getattr(request.colegio, 'id', None):
        return False
    if es_admin(request):
        return True
    curso = estudiante.curso
    return bool(curso and curso.director_grado_id and curso.director_grado.user_id == request.user.id)


def crear_solicitud(estudiante, usuario, form, foto_nueva=None):
    """Compara el formulario con la ficha y guarda lo que cambió como solicitud (sin tocar la ficha).

    Reemplaza la que estuviera pendiente. Devuelve la solicitud o None si no cambió nada."""
    ficha = FichaEstudiante.objects.get(pk=estudiante.pk)
    antes = foto_ficha(ficha)
    cambios = {}
    for campo in CAMPOS_ESTUDIANTE:
        if campo == 'foto':
            continue
        nuevo = form.cleaned_data.get(campo)
        nuevo = nuevo if nuevo not in ('',) else None
        if (antes[campo][0] or None) == (nuevo or None):
            continue
        guardar = nuevo.isoformat() if hasattr(nuevo, 'isoformat') else nuevo
        cambios[campo] = {'etiqueta': ETIQUETAS[campo], 'antes': antes[campo][1],
                          'despues': guardar, 'despues_txt': _texto(ficha, campo, nuevo)}
    if foto_nueva is not None:
        cambios['foto'] = {'etiqueta': 'Foto', 'antes': antes['foto'][1], 'despues': '(nueva)',
                           'despues_txt': 'Foto nueva'}
    if not cambios:
        return None
    for vieja in SolicitudFicha.objects.filter(estudiante=estudiante, estado='PENDIENTE'):
        if vieja.foto_nueva:
            vieja.foto_nueva.delete(save=False)
        vieja.delete()
    s = SolicitudFicha(colegio=estudiante.colegio, estudiante=estudiante, enviada_por=usuario, cambios=cambios)
    if foto_nueva is not None:
        s.foto_nueva.save(foto_nueva.name, foto_nueva, save=False)
    s.save()
    return s


@transaction.atomic
def aprobar(solicitud, usuario, campos):
    """Aplica a la ficha los campos escogidos y deja el registro. Devuelve cuántos aplicó."""
    ficha = FichaEstudiante.objects.select_for_update().get(pk=solicitud.estudiante_id)
    antes = foto_ficha(ficha)
    aplicados = []
    for campo in campos:
        cambio = solicitud.cambios.get(campo)
        if cambio is None or campo not in CAMPOS_ESTUDIANTE:
            continue
        if campo == 'foto':
            if solicitud.foto_nueva:
                ficha.foto.name = solicitud.foto_nueva.name
                aplicados.append(campo)
            continue
        modelo_campo = FichaEstudiante._meta.get_field(campo)
        setattr(ficha, campo, modelo_campo.to_python(cambio['despues']) if cambio['despues'] is not None else None)
        aplicados.append(campo)
    ficha.save()
    registrar(solicitud.colegio, solicitud.estudiante, antes, foto_ficha(ficha), solicitud.enviada_por,
              'SOLICITUD', autorizado_por=usuario, solicitud=solicitud)
    if solicitud.foto_nueva and 'foto' not in aplicados:
        solicitud.foto_nueva.delete(save=False)
    solicitud.aprobados = aplicados
    solicitud.estado = 'APROBADA' if len(aplicados) == len(solicitud.cambios) else ('PARCIAL' if aplicados else 'RECHAZADA')
    solicitud.revisada_por, solicitud.revisada_en = usuario, timezone.now()
    solicitud.save()
    return len(aplicados)


def rechazar(solicitud, usuario, respuesta):
    if solicitud.foto_nueva:
        solicitud.foto_nueva.delete(save=False)
    solicitud.estado = 'RECHAZADA'
    solicitud.revisada_por, solicitud.revisada_en = usuario, timezone.now()
    solicitud.respuesta = (respuesta or '').strip()[:500]
    solicitud.save()


def avisar(usuarios, colegio, mensaje, url):
    Notificacion.objects.bulk_create([
        Notificacion(colegio=colegio, destinatario=u, tipo='GENERAL', mensaje=mensaje[:255], url=url)
        for u in usuarios if u is not None])
