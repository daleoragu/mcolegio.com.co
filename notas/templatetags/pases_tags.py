"""{% load pases_tags %}{% permiso_abierto as pase %}: el permiso de salida abierto del estudiante que mira."""
from django import template

register = template.Library()


@register.simple_tag(takes_context=True)
def permiso_abierto(context):
    request = context.get('request')
    if request is None or not getattr(request, 'colegio', None) or not request.user.is_authenticated:
        return None
    from notas.modulos import esta_activo
    if not esta_activo(request.colegio, 'permisos'):
        return None
    from notas.models import Estudiante
    from notas.pases import abierto_de
    est = Estudiante.objects.filter(user=request.user, colegio=request.colegio).first()
    return abierto_de(est) if est else None
