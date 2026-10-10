# notas/templatetags/auth_extras.py
from django import template

register = template.Library()

@register.filter(name='has_group')
def has_group(user, group_name):
    """
    Verifica si un usuario pertenece a un grupo específico.
    Uso en la plantilla: {% if user|has_group:"NombreDelGrupo" %}
    """
    return user.groups.filter(name=group_name).exists()


@register.filter(name='es_docente')
def es_docente(user):
    """{% if user|es_docente %}: grupo «Docentes» o perfil de Docente (ver permisos.es_docente_usuario)."""
    from notas.permisos import es_docente_usuario
    return es_docente_usuario(user)
