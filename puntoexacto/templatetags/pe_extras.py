# -*- coding: utf-8 -*-
"""Filtros de plantilla de PuntoExacto."""
from django import template

register = template.Library()


@register.filter
def valor_de(diccionario, clave):
    """Saca un valor de un diccionario por clave. Django no deja hacerlo directo.

    Se usa para los créditos parciales, que se guardan como {'B': '0.5'}.
    """
    if not isinstance(diccionario, dict):
        return ''
    valor = diccionario.get(clave, '')
    return '' if valor in (None, 0, '0') else valor
