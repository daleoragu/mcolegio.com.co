"""{{ texto|eq }}: escapa el texto (si no venía ya limpio) y dibuja las ecuaciones \\( … \\) que tenga."""
from django import template
from django.utils.html import conditional_escape
from django.utils.safestring import mark_safe

from materiales.ecuaciones import en_html

register = template.Library()


@register.filter(is_safe=True)
def eq(valor):
    if valor is None:
        return ''
    return mark_safe(en_html(str(conditional_escape(valor))))
