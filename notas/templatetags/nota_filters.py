# notas/templatetags/nota_filters.py
from django import template
from django.contrib.auth.models import Group
from django.contrib.staticfiles import finders
from pathlib import Path
import base64
import mimetypes
from decimal import Decimal

register = template.Library()

@register.filter(name='get_item')
def get_item(dictionary, key):
    if hasattr(dictionary, 'get'):
        return dictionary.get(key)
    return None

@register.filter(name='has_group')
def has_group(user, group_name):
    return user.groups.filter(name=group_name).exists()

@register.filter(name='get_static_path')
def get_static_path(path):
    absolute_path = finders.find(path)
    if absolute_path:
        return Path(absolute_path).as_uri()
    return ''

@register.filter(name='get_image_base64')
def get_image_base64(path: str) -> str:
    """
    Encuentra un archivo estático, lo codifica en Base64 y lo devuelve como un
    Data URI listo para ser incrustado en una etiqueta <img>.
    """
    try:
        absolute_path = finders.find(path)
        if not absolute_path:
            return ""
        mime_type, _ = mimetypes.guess_type(absolute_path)
        if not mime_type:
            mime_type = "application/octet-stream"
        with open(absolute_path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
        return f"data:{mime_type};base64,{encoded_string}"
    except (IOError, TypeError):
        return ""

@register.filter(name='get_initials')
def get_initials(user):
    """
    Genera las iniciales del usuario a partir de su nombre y apellido.
    Ej: "Rolando Ocampo" -> "RO".
    Si no tiene nombre completo, usa las dos primeras letras del username.
    """
    if user.first_name and user.last_name:
        return (user.first_name[0] + user.last_name[0]).upper()
    elif user.first_name:
        return user.first_name[:2].upper()
    else:
        return user.username[:2].upper()

# --- TAREA DE AJUSTE 2: NUEVO FILTRO PARA NOTAS ---
@register.filter(name='coma_decimal')
def coma_decimal(value):
    """
    Convierte un valor numérico a un string con una coma como separador decimal
    y mostrando siempre un decimal.
    Ejemplos: 4.5 -> "4,5" | 5 -> "5,0" | "" -> ""
    """
    if value is None or value == '':
        return ""
    try:
        # Se convierte a Decimal para un manejo preciso de los números.
        num = Decimal(value)
        # Se formatea a un solo decimal y se reemplaza el punto por la coma.
        return f"{num:.1f}".replace('.', ',')
    except (ValueError, TypeError):
        # Si el valor no puede ser convertido a número, se devuelve como está.
        return value
# --- FIN DEL NUEVO FILTRO --

@register.simple_tag
def get_unread_notification_count(user):
    """
    Este es un 'simple_tag' que cuenta las notificaciones no leídas
    para un usuario específico.
    """
    if not user.is_authenticated:
        return 0
    try:
        # Cuenta las notificaciones para el usuario que no han sido leídas
        return Notificacion.objects.filter(destinatario=user, leido=False).count()
    except:
        # Si hay algún error, simplemente retorna 0 para no romper la página.
        return 0

# ---------------------- NUEVO FILTRO: desempeNO ---------------------------
from notas.models import EscalaValoracion

@register.filter(name='desempeno')
def obtener_desempeno(nota, colegio):
    """
    Devuelve el nombre del desempeño según la escala de valoración del colegio.
    Si la nota no corresponde a ningún rango, retorna ''.
    """
    if nota is None or colegio is None:
        return ''
    try:
        escala = EscalaValoracion.objects.filter(colegio=colegio).order_by('-valor_maximo')
        nota_decimal = Decimal(str(nota))
        for rango in escala:
            if rango.valor_minimo <= nota_decimal <= rango.valor_maximo:
                return rango.nombre_desempeno.upper()
    except Exception:
        return ''
    return ''


@register.filter(name='svg_vertical')
def svg_vertical(texto, alto=80):
    """Texto girado (de abajo hacia arriba) como SVG, para encabezados angostos en PDF.

    WeasyPrint no maneja ``writing-mode``; un SVG en línea sí sale igual en el
    PDF. Los nombres largos se parten en hasta tres renglones verticales para
    que la columna no crezca.
    """
    from django.utils.html import escape
    from django.utils.safestring import mark_safe
    texto = ' '.join(str(texto or '').split())
    if not texto:
        return ''
    alto = int(alto)
    por_linea = max(4, int(alto / 4.6))
    lineas, linea = [], ''
    for palabra in texto.split(' '):
        prueba = (linea + ' ' + palabra).strip()
        if len(prueba) <= por_linea or not linea:
            linea = prueba
        else:
            lineas.append(linea)
            linea = palabra
    lineas.append(linea)
    lineas = lineas[:3]
    paso = 8.5
    ancho = round(paso * len(lineas) + 1.5, 1)
    textos = ''.join(
        f'<text x="{-alto / 2:.1f}" y="{7 + paso * i:.1f}" text-anchor="middle">{escape(l)}</text>'
        for i, l in enumerate(lineas))
    return mark_safe(
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{ancho}" height="{alto}" '
        f'viewBox="0 0 {ancho} {alto}"><g transform="rotate(-90)" '
        f'font-family="Helvetica, Arial, sans-serif" font-size="7" font-weight="bold" fill="#333">'
        f'{textos}</g></svg>')
