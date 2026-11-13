"""{% asesoria_docente %}: el botón «Asesoría docente» (solo para docentes y administradores del colegio)."""
from django import template

from notas import asesoria

register = template.Library()


@register.inclusion_tag('notas/includes/_asesoria.html', takes_context=True)
def asesoria_docente(context):
    request = context.get('request')
    user = getattr(request, 'user', None)
    if request is None or not asesoria.es_para(user):
        return {'mostrar': False}
    return {'mostrar': True, 'datos': asesoria.datos(request)}
