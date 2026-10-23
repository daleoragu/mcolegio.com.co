"""Un solo lugar para mandar correos y WhatsApp en nombre del colegio.

Correo
------
La plataforma manda por su servidor (variables EMAIL_* de DigitalOcean), pero cada
correo sale con el NOMBRE del colegio y, si el colegio escribió su correo
institucional, las respuestas le llegan a ese correo (Reply-To). Así no hay que
guardar la contraseña del correo de cada colegio.

Si el colegio verificó su dirección en el proveedor de correo de la plataforma
(Brevo, SendGrid, Amazon SES…), se marca «correo_remitente_verificado» y el
correo sale DESDE la dirección del colegio.

WhatsApp
--------
Una sola línea de WhatsApp Business (Cloud API de Meta) para toda la plataforma.
Se configura con variables de entorno, nunca en la base de datos:

    WHATSAPP_TOKEN        token permanente de la app de Meta
    WHATSAPP_PHONE_ID     id del número de la línea
    WHATSAPP_PLANTILLA    nombre de la plantilla aprobada (por defecto «aviso_mcolegio»)
    WHATSAPP_IDIOMA       idioma de la plantilla (por defecto «es»)

Meta solo deja escribir primero con una plantilla aprobada. La plantilla lleva dos
variables: {{1}} = nombre del colegio y {{2}} = el aviso. Sin estas variables no se
envía nada y los avisos siguen saliendo con el botón de «WhatsApp» (enlace wa.me).
"""
import json
import os
import re
import urllib.error
import urllib.request
from email.utils import formataddr

from django.conf import settings
from django.core.mail import EmailMultiAlternatives, get_connection

API_WHATSAPP = 'https://graph.facebook.com/v20.0/{phone_id}/messages'


# ----------------------------------------------------------------------------- correo

def correo_configurado():
    # «localhost» es el valor de fábrica de Django: no hay servidor de correo ahí.
    return getattr(settings, 'EMAIL_HOST', '') not in ('', 'localhost')


def _correo_plataforma():
    return settings.DEFAULT_FROM_EMAIL


def remitente(colegio=None):
    """«Nombre del colegio <correo>» para el From."""
    correo = _correo_plataforma()
    if colegio is None:
        return correo
    propio = (getattr(colegio, 'correo_institucional', '') or '').strip()
    if propio and getattr(colegio, 'correo_remitente_verificado', False):
        correo = propio
    nombre = re.sub(r'[\r\n"<>]+', ' ', colegio.nombre or '').strip()[:70]
    return formataddr((nombre, correo)) if nombre else correo


def responder_a(colegio=None):
    propio = (getattr(colegio, 'correo_institucional', '') or '').strip() if colegio is not None else ''
    return [propio] if propio else None


def mensaje(colegio, asunto, texto, destinatarios, html=None, adjuntos=()):
    """Un EmailMultiAlternatives listo para mandar (o para juntar con otros en una conexión)."""
    m = EmailMultiAlternatives(asunto, texto, remitente(colegio), list(destinatarios), reply_to=responder_a(colegio))
    if html:
        m.attach_alternative(html, 'text/html')
    for nombre, contenido, tipo in adjuntos:
        m.attach(nombre, contenido, tipo)
    return m


def enviar_correo(colegio, asunto, texto, destinatarios, html=None, fail_silently=False):
    """Manda un correo en nombre del colegio. Devuelve cuántos se enviaron (0 o 1)."""
    destinatarios = [d for d in (destinatarios or []) if d]
    if not destinatarios:
        return 0
    return mensaje(colegio, asunto, texto, destinatarios, html).send(fail_silently=fail_silently)


def enviar_varios(mensajes):
    """Manda varios correos por una sola conexión. Devuelve cuántos salieron."""
    if not mensajes:
        return 0
    try:
        return get_connection(fail_silently=True).send_messages(list(mensajes)) or 0
    except Exception:
        return 0


# ----------------------------------------------------------------------------- WhatsApp

def whatsapp_configurado():
    return bool(os.getenv('WHATSAPP_TOKEN') and os.getenv('WHATSAPP_PHONE_ID'))


def numero_whatsapp(numero, indicativo='57'):
    """Solo dígitos, con el indicativo del país (Colombia por defecto). '' si no sirve."""
    d = re.sub(r'\D', '', str(numero or ''))
    if len(d) == 10 and d.startswith('3'):          # celular colombiano sin indicativo
        d = indicativo + d
    return d if 11 <= len(d) <= 15 else ''


def _cuerpo_whatsapp(numero, colegio, texto):
    return {
        'messaging_product': 'whatsapp',
        'to': numero,
        'type': 'template',
        'template': {
            'name': os.getenv('WHATSAPP_PLANTILLA', 'aviso_mcolegio'),
            'language': {'code': os.getenv('WHATSAPP_IDIOMA', 'es')},
            'components': [{'type': 'body', 'parameters': [
                {'type': 'text', 'text': (getattr(colegio, 'nombre', '') or 'mcolegio')[:60]},
                # WhatsApp no deja saltos de línea ni más de 4 espacios seguidos en una variable
                {'type': 'text', 'text': re.sub(r'\s+', ' ', texto or '').strip()[:900]},
            ]}],
        },
    }


def enviar_whatsapp(colegio, numero, texto):
    """Manda el aviso por la línea de WhatsApp de la plataforma. Devuelve (enviado, detalle)."""
    if not whatsapp_configurado():
        return False, 'la línea de WhatsApp no está configurada'
    if colegio is not None and not getattr(colegio, 'whatsapp_automatico', False):
        return False, 'el colegio no tiene activados los avisos automáticos por WhatsApp'
    destino = numero_whatsapp(numero)
    if not destino:
        return False, 'el número no es un celular válido'
    datos = json.dumps(_cuerpo_whatsapp(destino, colegio, texto)).encode('utf-8')
    req = urllib.request.Request(API_WHATSAPP.format(phone_id=os.getenv('WHATSAPP_PHONE_ID')), data=datos,
                                 headers={'Authorization': f'Bearer {os.getenv("WHATSAPP_TOKEN")}',
                                          'Content-Type': 'application/json'}, method='POST')
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            ok = 200 <= r.status < 300
    except urllib.error.HTTPError as e:
        return False, f'WhatsApp respondió {e.code}'
    except Exception as e:                          # sin red, tiempo agotado…: no tumba la página
        return False, f'no se pudo enviar ({type(e).__name__})'
    return ok, destino if ok else 'WhatsApp no aceptó el mensaje'
