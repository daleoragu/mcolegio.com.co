# notas/avisos_familia.py
"""Avisos a la familia cuando se registra algo en el observador.

Dos caminos, los dos sin costo:

* Correo al acudiente, automático, si tiene correo en la ficha y el servidor
  de correo está configurado (variables EMAIL_* en el servidor).
* WhatsApp: un enlace que abre el WhatsApp de quien registró la observación
  con el mensaje ya escrito al número del papá, la mamá o el acudiente. Solo
  falta tocar «Enviar». Cuando el colegio tenga WhatsApp Business conectado,
  el envío se vuelve automático con el mismo texto.

El mensaje NO lleva la descripción de lo ocurrido: un SMS o un WhatsApp se
reenvía y se ve en la pantalla bloqueada, y la descripción puede nombrar a
otros estudiantes. Dice que hay una anotación y dónde consultarla.
"""
import re
from urllib.parse import quote

from django.conf import settings
from django.core.mail import send_mail


def normalizar_celular(numero):
    """'310 555 1234' -> '573105551234'. None si no parece un celular colombiano.

    Se aceptan también números con indicativo de otro país si vienen con '+'.
    """
    if not numero:
        return None
    crudo = str(numero).strip()
    digitos = re.sub(r'\D', '', crudo)
    if len(digitos) == 10 and digitos.startswith('3'):
        return '57' + digitos
    if len(digitos) == 12 and digitos.startswith('573'):
        return digitos
    if crudo.startswith('+') and 8 <= len(digitos) <= 15:
        return digitos
    return None


def contactos(estudiante):
    """[{'rol', 'nombre', 'numero', 'visible'}] de la ficha, sin repetir números."""
    ficha = getattr(estudiante, 'ficha', None)
    if ficha is None:
        return []
    salida, vistos = [], set()
    for rol, nombre, cel in (('Acudiente', ficha.nombre_acudiente, ficha.celular_acudiente),
                             ('Mamá', ficha.nombre_madre, ficha.celular_madre),
                             ('Papá', ficha.nombre_padre, ficha.celular_padre)):
        numero = normalizar_celular(cel)
        if numero and numero not in vistos:
            vistos.add(numero)
            salida.append({'rol': rol, 'nombre': (nombre or '').strip(), 'numero': numero,
                           'visible': (cel or '').strip()})
    return salida


def _tipo(registro):
    texto = registro.get_tipo_display().lower()
    if registro.subtipo == 'POSITIVA':
        return f'{texto} positiva'
    if registro.subtipo == 'NEGATIVA':
        return f'{texto} por mejorar'
    return texto


def texto_aviso(registro, url_portal=''):
    colegio = registro.colegio.nombre if registro.colegio_id else 'El colegio'
    est = registro.estudiante.user
    nombre = f'{est.first_name} {est.last_name}'.strip() or est.username
    fecha = registro.fecha_suceso.strftime('%d/%m/%Y') if registro.fecha_suceso else ''
    texto = (f'{colegio}: le informamos que {nombre} tiene una nueva anotación '
             f'{_tipo(registro)} en el observador ({fecha}).')
    if registro.subtipo == 'POSITIVA':
        texto += ' ¡Felicitaciones!'
    texto += ' Puede consultarla en la plataforma'
    texto += f' ({url_portal})' if url_portal else ''
    texto += ' o comunicarse con coordinación.'
    return texto


def enlace_whatsapp(numero, texto):
    return f'https://wa.me/{numero}?text={quote(texto)}'


def correo_configurado():
    # «localhost» es el valor de fábrica de Django: no hay servidor de correo ahí.
    return getattr(settings, 'EMAIL_HOST', '') not in ('', 'localhost')


def enviar_correo(registro, url_portal=''):
    """Manda el aviso al correo del acudiente. Devuelve (enviado, motivo)."""
    ficha = getattr(registro.estudiante, 'ficha', None)
    correo = getattr(ficha, 'email_acudiente', None) if ficha else None
    if not correo:
        return False, 'el estudiante no tiene correo de acudiente en la ficha'
    if not correo_configurado():
        return False, 'el correo de la plataforma no está configurado'
    asunto = f'Observador · {registro.estudiante.user.get_full_name()}'
    try:
        send_mail(asunto, texto_aviso(registro, url_portal), settings.DEFAULT_FROM_EMAIL,
                  [correo], fail_silently=False)
    except Exception as e:      # un correo caído no debe impedir guardar la observación
        return False, f'no se pudo enviar ({type(e).__name__})'
    return True, correo
