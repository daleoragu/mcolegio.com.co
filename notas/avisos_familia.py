# notas/avisos_familia.py
"""Avisos a la familia cuando se registra algo en el observador.

Dos caminos, los dos sin costo:

* Correo al acudiente, automático, si tiene correo en la ficha y el servidor
  de correo está configurado (variables EMAIL_* en el servidor).
* WhatsApp: un enlace que abre el WhatsApp de quien registró la observación
  con el mensaje ya escrito al número del papá, la mamá o el acudiente. Solo
  falta tocar «Enviar». Cuando el colegio tenga WhatsApp Business conectado,
  el envío se vuelve automático con el mismo texto.

El mensaje lleva el motivo de la anotación (la descripción del docente). Por
eso el formulario le recuerda al docente no escribir nombres de otros
estudiantes. El correo trae además un enlace personal y firmado para que el
acudiente se dé por enterado y escriba su descargo sin usuario ni contraseña.
"""
import re
from urllib.parse import quote

from django.conf import settings
from django.core import signing
from django.core.mail import send_mail
from django.template.loader import render_to_string


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


MAX_MOTIVO_WHATSAPP = 350
DIAS_ENLACE = 30        # el enlace del correo sirve durante un mes


def _motivo(registro, largo_max=None):
    texto = ' '.join((registro.descripcion or '').split())
    if largo_max and len(texto) > largo_max:
        texto = texto[:largo_max].rsplit(' ', 1)[0] + '…'
    return texto


def texto_aviso(registro, url_portal='', largo_motivo=MAX_MOTIVO_WHATSAPP):
    """El mensaje para la familia, con el motivo de la anotación."""
    colegio = registro.colegio.nombre if registro.colegio_id else 'El colegio'
    est = registro.estudiante.user
    nombre = f'{est.first_name} {est.last_name}'.strip() or est.username
    fecha = registro.fecha_suceso.strftime('%d/%m/%Y') if registro.fecha_suceso else ''
    texto = (f'{colegio}: le informamos que {nombre} tiene una nueva anotación '
             f'{_tipo(registro)} en el observador ({fecha}).')
    motivo = _motivo(registro, largo_motivo)
    if motivo:
        texto += f'\nMotivo: {motivo}'
    if registro.subtipo == 'POSITIVA':
        texto += '\n¡Felicitaciones!'
    texto += '\nPuede consultarla en la plataforma'
    texto += f' ({url_portal})' if url_portal else ''
    texto += ' o comunicarse con coordinación.'
    return texto


def enlace_whatsapp(numero, texto):
    return f'https://wa.me/{numero}?text={quote(texto)}'


# ---------------------------------------------------------------------------
# Enlace personal del correo: el acudiente responde sin usuario ni contraseña
# ---------------------------------------------------------------------------

SAL = 'notas.observador.respuesta-acudiente'


def _correo_de(registro):
    ficha = getattr(registro.estudiante, 'ficha', None)
    return ((getattr(ficha, 'email_acudiente', '') if ficha else '') or '').strip().lower()


def token_respuesta(registro):
    """Firmado con la clave del servidor y amarrado al correo del acudiente:
    si cambian el correo en la ficha, el enlace viejo deja de servir."""
    return signing.dumps({'r': registro.id, 'c': _correo_de(registro)}, salt=SAL, compress=True)


def registro_de_token(token):
    """El registro del enlace, o (None, motivo) si no sirve."""
    from .models import RegistroObservador
    try:
        datos = signing.loads(token, salt=SAL, max_age=DIAS_ENLACE * 24 * 3600)
    except signing.SignatureExpired:
        return None, 'vencido'
    except signing.BadSignature:
        return None, 'invalido'
    registro = (RegistroObservador.objects.select_related('estudiante__user', 'colegio',
                                                          'docente_reporta__user')
                .filter(id=datos.get('r')).first())
    if registro is None or _correo_de(registro) != datos.get('c'):
        return None, 'invalido'
    return registro, ''


def correo_configurado():
    # «localhost» es el valor de fábrica de Django: no hay servidor de correo ahí.
    return getattr(settings, 'EMAIL_HOST', '') not in ('', 'localhost')


def enviar_correo(registro, url_portal='', url_respuesta=''):
    """Manda el aviso al correo del acudiente. Devuelve (enviado, detalle).

    El correo lleva el motivo completo y, si se da url_respuesta, el botón para
    que el acudiente lo marque como leído y escriba su descargo.
    """
    correo = _correo_de(registro)
    if not correo:
        return False, 'el estudiante no tiene correo de acudiente en la ficha'
    if not correo_configurado():
        return False, 'el correo de la plataforma no está configurado'
    asunto = f'Observador · {registro.estudiante.user.get_full_name()}'
    texto = texto_aviso(registro, url_portal, largo_motivo=None)
    if url_respuesta:
        texto += (f'\n\nPara darse por enterado y escribir su descargo o comentario, '
                  f'abra este enlace (es personal y vence en {DIAS_ENLACE} días):\n{url_respuesta}')
    html = render_to_string('notas/emails/aviso_observador.html', {
        'registro': registro, 'colegio': registro.colegio, 'tipo': _tipo(registro),
        'motivo': _motivo(registro), 'url_respuesta': url_respuesta, 'url_portal': url_portal,
        'dias': DIAS_ENLACE})
    try:
        send_mail(asunto, texto, settings.DEFAULT_FROM_EMAIL, [correo],
                  html_message=html, fail_silently=False)
    except Exception as e:      # un correo caído no debe impedir guardar la observación
        return False, f'no se pudo enviar ({type(e).__name__})'
    return True, correo
