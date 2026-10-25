"""Notificaciones al celular (Web Push), gratis y sin límite diario.

Cada vez que la plataforma crea una Notificación (circular, anotación del
observador, mensaje del correo interno, plazos…), le llega también al celular
o al computador de esa persona, si allí tocó «Activar avisos». Funciona con la
app instalada o con el navegador cerrado, como las notificaciones de cualquier
app.

No usa ningún servicio de pago: el navegador de cada persona (Chrome, Safari,
Firefox, Samsung) tiene su propio servicio de notificaciones gratuito, y la
plataforma le entrega el aviso cifrado (RFC 8291) y firmado con las llaves
VAPID de la plataforma (RFC 8292).

Las llaves se crean solas la primera vez y quedan en la base de datos
(ClavePush). Si se quieren fijar a mano: variables VAPID_PRIVADA y
VAPID_PUBLICA. VAPID_CORREO es el correo de contacto que ven Google y Apple.

En iPhone solo funciona con la app agregada a la pantalla de inicio (iOS 16.4 o
más nuevo); en Android, con Chrome, con o sin instalar.
"""
import base64
import hashlib
import hmac
import json
import logging
import os
import struct
import threading
import time
import urllib.error
import urllib.request
from urllib.parse import urlparse

from django.db import close_old_connections, transaction
from django.utils import timezone

logger = logging.getLogger('mcolegio.push')

# En las pruebas se pone en False para enviar en el mismo hilo.
EN_SEGUNDO_PLANO = True
TTL = 3 * 24 * 3600            # si el celular está apagado, el aviso espera hasta 3 días


# ----------------------------------------------------------------------------- utilidades

def b64u(datos):
    return base64.urlsafe_b64encode(datos).rstrip(b'=').decode('ascii')


def de_b64u(texto):
    texto = (texto or '').strip()
    return base64.urlsafe_b64decode(texto + '=' * (-len(texto) % 4))


def disponible():
    try:
        import cryptography  # noqa: F401
        return True
    except ImportError:
        return False


# ----------------------------------------------------------------------------- llaves

def _publica_de(privada):
    from cryptography.hazmat.primitives import serialization
    return privada.public_key().public_bytes(serialization.Encoding.X962,
                                             serialization.PublicFormat.UncompressedPoint)


def _privada_de_bytes(crudo):
    from cryptography.hazmat.primitives.asymmetric import ec
    return ec.derive_private_key(int.from_bytes(crudo, 'big'), ec.SECP256R1())


def llaves():
    """(llave privada de cryptography, llave pública en base64url). Las crea si no existen."""
    from cryptography.hazmat.primitives.asymmetric import ec
    privada_env = os.getenv('VAPID_PRIVADA')
    if privada_env:
        privada = _privada_de_bytes(de_b64u(privada_env))
        return privada, os.getenv('VAPID_PUBLICA') or b64u(_publica_de(privada))
    from notas.models import ClavePush
    fila = ClavePush.objects.order_by('id').first()
    if fila is None:
        privada = ec.generate_private_key(ec.SECP256R1())
        crudo = privada.private_numbers().private_value.to_bytes(32, 'big')
        fila = ClavePush.objects.create(privada=b64u(crudo), publica=b64u(_publica_de(privada)))
        fila = ClavePush.objects.order_by('id').first()       # si dos procesos la crearon a la vez, gana la primera
    return _privada_de_bytes(de_b64u(fila.privada)), fila.publica


def clave_publica():
    return llaves()[1]


# ----------------------------------------------------------------------------- cifrado (RFC 8291)

def _hkdf(salt, ikm, info, largo):
    prk = hmac.new(salt, ikm, hashlib.sha256).digest()
    return hmac.new(prk, info + b'\x01', hashlib.sha256).digest()[:largo]


def cifrar(texto, p256dh, auth, _efimera=None, _salt=None):
    """Cuerpo aes128gcm listo para enviar al servicio del navegador."""
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric import ec
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM

    ua_publica = de_b64u(p256dh)
    secreto_auth = de_b64u(auth)
    efimera = _efimera or ec.generate_private_key(ec.SECP256R1())
    as_publica = efimera.public_key().public_bytes(serialization.Encoding.X962,
                                                   serialization.PublicFormat.UncompressedPoint)
    compartido = efimera.exchange(ec.ECDH(), ec.EllipticCurvePublicKey.from_encoded_point(ec.SECP256R1(), ua_publica))
    ikm = _hkdf(secreto_auth, compartido, b'WebPush: info\x00' + ua_publica + as_publica, 32)
    salt = _salt or os.urandom(16)
    cek = _hkdf(salt, ikm, b'Content-Encoding: aes128gcm\x00', 16)
    nonce = _hkdf(salt, ikm, b'Content-Encoding: nonce\x00', 12)
    cifrado = AESGCM(cek).encrypt(nonce, texto + b'\x02', None)
    return salt + struct.pack('!IB', 4096, len(as_publica)) + as_publica + cifrado


# ----------------------------------------------------------------------------- firma (RFC 8292)

def _jwt(endpoint, privada):
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.asymmetric import ec
    from cryptography.hazmat.primitives.asymmetric.utils import decode_dss_signature
    u = urlparse(endpoint)
    cabeza = b64u(json.dumps({'typ': 'JWT', 'alg': 'ES256'}, separators=(',', ':')).encode())
    datos = b64u(json.dumps({'aud': f'{u.scheme}://{u.netloc}', 'exp': int(time.time()) + 12 * 3600,
                             'sub': 'mailto:' + os.getenv('VAPID_CORREO', 'soporte@mcolegio.com.co')},
                            separators=(',', ':')).encode())
    firmar = f'{cabeza}.{datos}'.encode()
    r, s = decode_dss_signature(privada.sign(firmar, ec.ECDSA(hashes.SHA256())))
    return f'{cabeza}.{datos}.{b64u(r.to_bytes(32, "big") + s.to_bytes(32, "big"))}'


# ----------------------------------------------------------------------------- envío

def enviar_a(suscripcion, aviso, privada=None, publica=None):
    """Entrega un aviso a un celular. Devuelve 'ok', 'vencida' (hay que borrarla) o 'error'."""
    if privada is None:
        privada, publica = llaves()
    cuerpo = cifrar(json.dumps(aviso, ensure_ascii=False).encode('utf-8'), suscripcion.p256dh, suscripcion.auth)
    req = urllib.request.Request(suscripcion.endpoint, data=cuerpo, method='POST', headers={
        'Content-Encoding': 'aes128gcm', 'Content-Type': 'application/octet-stream',
        'TTL': str(TTL), 'Urgency': 'normal',
        'Authorization': f'vapid t={_jwt(suscripcion.endpoint, privada)}, k={publica}'})
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return 'ok' if 200 <= r.status < 300 else 'error'
    except urllib.error.HTTPError as e:
        if e.code in (404, 410):            # el usuario quitó el permiso o desinstaló la app
            return 'vencida'
        logger.warning('Push %s rechazado: %s', urlparse(suscripcion.endpoint).netloc, e.code)
        return 'error'
    except Exception as e:
        logger.warning('Push sin entregar: %s', type(e).__name__)
        return 'error'


def _aviso(n, nombres_colegio):
    return {
        'titulo': nombres_colegio.get(n.colegio_id) or 'mcolegio',
        'cuerpo': n.mensaje,
        'url': n.url or '/app/',
        'etiqueta': f'mc-{n.tipo.lower()}-{n.id or int(time.time())}',
    }


def enviar(notificaciones):
    """Manda cada notificación a todos los celulares activados de su destinatario. Devuelve cuántas salieron."""
    from notas.models import Colegio, SuscripcionPush
    notificaciones = [n for n in notificaciones if getattr(n, 'destinatario_id', None)]
    if not notificaciones or not disponible():
        return 0
    por_usuario = {}
    for s in SuscripcionPush.objects.filter(usuario_id__in={n.destinatario_id for n in notificaciones}):
        por_usuario.setdefault(s.usuario_id, []).append(s)
    if not por_usuario:
        return 0
    nombres = dict(Colegio.objects.filter(id__in={n.colegio_id for n in notificaciones if n.colegio_id})
                   .values_list('id', 'nombre'))
    privada, publica = llaves()
    salieron, vencidas, usadas = 0, [], []
    for n in notificaciones:
        for s in por_usuario.get(n.destinatario_id, ()):
            if s.id in vencidas:
                continue
            resultado = enviar_a(s, _aviso(n, nombres), privada, publica)
            if resultado == 'ok':
                salieron += 1
                usadas.append(s.id)
            elif resultado == 'vencida':
                vencidas.append(s.id)
    if vencidas:
        SuscripcionPush.objects.filter(id__in=vencidas).delete()
    if usadas:
        SuscripcionPush.objects.filter(id__in=set(usadas)).update(ultimo_envio=timezone.now())
    return salieron


def programar(notificaciones):
    """Después de guardar (on_commit) y en segundo plano: la página no espera a los celulares."""
    lista = [n for n in (notificaciones or []) if n is not None]
    if not lista:
        return

    def trabajo():
        try:
            enviar(lista)
        except Exception:
            logger.exception('Error enviando notificaciones push')
        finally:
            if EN_SEGUNDO_PLANO:
                close_old_connections()

    def lanzar():
        from notas.models import SuscripcionPush
        # La consulta va aquí, en el hilo de la página: casi nadie tiene celulares activados y así no se abre un hilo en vano.
        if not SuscripcionPush.objects.filter(usuario_id__in={n.destinatario_id for n in lista}).exists():
            return
        if EN_SEGUNDO_PLANO:
            threading.Thread(target=trabajo, daemon=True).start()
        else:
            trabajo()
    transaction.on_commit(lanzar)
