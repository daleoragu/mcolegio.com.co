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


@register.filter(name='foto_perfil')
def foto_perfil(user):
    """{{ user|foto_perfil }}: la foto que el docente subió en su perfil (Mis colegas / Mi Espacio) o, si no,
    la de su ficha de docente del colegio. Vacío si no tiene ninguna."""
    if not getattr(user, 'is_authenticated', False):
        return ''
    cache = '_foto_perfil'
    if not hasattr(user, cache):
        try:
            from chat.views_colegas import foto_de
            setattr(user, cache, foto_de(user))
        except Exception:
            setattr(user, cache, '')
    return getattr(user, cache)
