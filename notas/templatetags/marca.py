# notas/templatetags/marca.py
"""El logo de la plataforma (mcolegio.com.co) para pies de página y documentos.

Archivos en static/img/: mcolegio-logo.png (horizontal), mcolegio-logo-blanco.png
(para fondos oscuros), mcolegio-logo-oscuro.png (con su caja azul) y
mcolegio-icono.png (ícono de app, también el favicon).
"""
import base64
from functools import lru_cache

from django import template
from django.contrib.staticfiles import finders

register = template.Library()


@lru_cache(maxsize=8)
def _base64(nombre):
    ruta = finders.find(f'img/{nombre}')
    if not ruta:
        return ''
    with open(ruta, 'rb') as f:
        return base64.b64encode(f.read()).decode()


@register.simple_tag
def mcolegio_icono_uri(alto=10, nombre='mcolegio-icono.png', ancho=None):
    """El logo como imagen SVG de `alto` px (data URI), para el pie de los PDF de WeasyPrint:
    en un content: url(...) el tamaño lo pone el SVG, no el CSS."""
    datos = _base64(nombre)
    if not datos:
        return ''
    ancho = ancho or alto
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
           f'width="{ancho}" height="{alto}"><image width="{ancho}" height="{alto}" '
           f'xlink:href="data:image/png;base64,{datos}"/></svg>')
    return 'data:image/svg+xml;base64,' + base64.b64encode(svg.encode()).decode()
