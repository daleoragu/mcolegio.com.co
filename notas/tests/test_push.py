"""Notificaciones al celular (Web Push): cifrado, firma, registro del celular y envío."""
import hashlib
import hmac
import json
import struct
from unittest import mock

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.asymmetric.utils import encode_dss_signature
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from django.test import TestCase
from django.urls import reverse

from notas import push
from notas.models import ClavePush, Notificacion, SuscripcionPush

from .base import ColegioDePrueba


def _celular():
    """Lo que tendría el navegador: su llave privada, p256dh y auth en base64url."""
    privada = ec.generate_private_key(ec.SECP256R1())
    publica = privada.public_key().public_bytes(serialization.Encoding.X962, serialization.PublicFormat.UncompressedPoint)
    auth = b'0123456789abcdef'
    return privada, push.b64u(publica), push.b64u(auth)


def _descifrar(cuerpo, privada, p256dh, auth):
    """Lo que hace el navegador al recibir (RFC 8291), para comprobar que el cifrado sirve."""
    salt, rs, largo = cuerpo[:16], struct.unpack('!I', cuerpo[16:20])[0], cuerpo[20]
    as_publica = cuerpo[21:21 + largo]
    cifrado = cuerpo[21 + largo:]
    compartido = privada.exchange(ec.ECDH(), ec.EllipticCurvePublicKey.from_encoded_point(ec.SECP256R1(), as_publica))

    def hkdf(s, ikm, info, n):
        prk = hmac.new(s, ikm, hashlib.sha256).digest()
        return hmac.new(prk, info + b'\x01', hashlib.sha256).digest()[:n]
    ua_publica = push.de_b64u(p256dh)
    ikm = hkdf(push.de_b64u(auth), compartido, b'WebPush: info\x00' + ua_publica + as_publica, 32)
    cek = hkdf(salt, ikm, b'Content-Encoding: aes128gcm\x00', 16)
    nonce = hkdf(salt, ikm, b'Content-Encoding: nonce\x00', 12)
    claro = AESGCM(cek).decrypt(nonce, cifrado, None)
    assert rs == 4096
    return claro.rstrip(b'\x00')[:-1]                # quita el delimitador 0x02


class CifradoYFirma(TestCase):

    def test_el_celular_puede_descifrar(self):
        privada, p256dh, auth = _celular()
        cuerpo = push.cifrar('Circular N.º 3 «Reunión»'.encode(), p256dh, auth)
        self.assertEqual(_descifrar(cuerpo, privada, p256dh, auth).decode(), 'Circular N.º 3 «Reunión»')

    def test_la_firma_vapid_se_verifica_con_la_llave_publica(self):
        privada, publica = push.llaves()
        token = push._jwt('https://fcm.googleapis.com/fcm/send/abc', privada)
        cabeza, datos, firma = token.split('.')
        self.assertEqual(json.loads(push.de_b64u(datos))['aud'], 'https://fcm.googleapis.com')
        crudo = push.de_b64u(firma)
        der = encode_dss_signature(int.from_bytes(crudo[:32], 'big'), int.from_bytes(crudo[32:], 'big'))
        llave = ec.EllipticCurvePublicKey.from_encoded_point(ec.SECP256R1(), push.de_b64u(publica))
        llave.verify(der, f'{cabeza}.{datos}'.encode(), ec.ECDSA(hashes.SHA256()))   # no lanza = firma válida

    def test_las_llaves_se_crean_una_sola_vez(self):
        a = push.clave_publica()
        self.assertEqual(push.clave_publica(), a)
        self.assertEqual(ClavePush.objects.count(), 1)
        self.assertEqual(len(push.de_b64u(a)), 65)


class _Respuesta:
    status = 201

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


@mock.patch.object(push, 'EN_SEGUNDO_PLANO', False)
class AvisosAlCelular(ColegioDePrueba):

    def _suscribir(self, usuario, endpoint='https://fcm.googleapis.com/fcm/send/xyz'):
        _, p256dh, auth = _celular()
        return self.cliente(usuario).post('/app/push/suscribir/', json.dumps(
            {'endpoint': endpoint, 'keys': {'p256dh': p256dh, 'auth': auth}}), content_type='application/json')

    def test_registrar_el_celular(self):
        ana = self.estudiantes[0].user
        self.assertEqual(self._suscribir(ana).status_code, 200)
        s = SuscripcionPush.objects.get()
        self.assertEqual((s.usuario, s.colegio), (ana, self.a))
        self._suscribir(ana)                                     # el mismo celular no se repite
        self.assertEqual(SuscripcionPush.objects.count(), 1)
        self.assertEqual(self._suscribir(ana, endpoint='http://inseguro').status_code, 400)
        self.assertEqual(self.client.post('/app/push/suscribir/', '{}', content_type='application/json').status_code, 302)
        self.assertEqual(len(push.de_b64u(self.cliente(ana).get('/app/push/clave/').json()['clave'])), 65)

    def test_una_notificacion_nueva_sale_al_celular(self):
        ana = self.estudiantes[0].user
        self._suscribir(ana)
        with mock.patch('urllib.request.urlopen', return_value=_Respuesta()) as abrir, \
                self.captureOnCommitCallbacks(execute=True):
            Notificacion.objects.create(colegio=self.a, destinatario=ana, mensaje='Nueva circular N.º 1', url='/circulares/1/')
        req = abrir.call_args[0][0]
        self.assertEqual(req.full_url, 'https://fcm.googleapis.com/fcm/send/xyz')
        self.assertEqual(req.get_header('Content-encoding'), 'aes128gcm')
        self.assertTrue(req.get_header('Authorization').startswith('vapid t='))
        self.assertIsNotNone(SuscripcionPush.objects.get().ultimo_envio)

    def test_las_creadas_de_a_muchas_tambien_salen_y_solo_a_quien_activo(self):
        ana, beto = self.estudiantes[0].user, self.estudiantes[1].user
        self._suscribir(ana)
        with mock.patch('urllib.request.urlopen', return_value=_Respuesta()) as abrir, \
                self.captureOnCommitCallbacks(execute=True):
            Notificacion.objects.bulk_create([Notificacion(colegio=self.a, destinatario=u, mensaje='Plazo de notas')
                                              for u in (ana, beto)])
        self.assertEqual(abrir.call_count, 1)                   # beto no activó los avisos

    def test_celular_que_quito_el_permiso_se_borra(self):
        import urllib.error
        ana = self.estudiantes[0].user
        self._suscribir(ana)
        vencida = urllib.error.HTTPError('u', 410, 'Gone', {}, None)
        with mock.patch('urllib.request.urlopen', side_effect=vencida), self.captureOnCommitCallbacks(execute=True):
            Notificacion.objects.create(colegio=self.a, destinatario=ana, mensaje='Hola')
        self.assertFalse(SuscripcionPush.objects.exists())

    def test_sin_celulares_no_se_intenta_nada(self):
        with mock.patch('urllib.request.urlopen') as abrir, self.captureOnCommitCallbacks(execute=True):
            Notificacion.objects.create(colegio=self.a, destinatario=self.estudiantes[0].user, mensaje='Hola')
        abrir.assert_not_called()

    def test_boton_de_prueba(self):
        ana = self.estudiantes[0].user
        self.assertEqual(self.cliente(ana).post('/app/push/probar/').json()['enviados'], 0)
        self._suscribir(ana)
        with mock.patch('urllib.request.urlopen', return_value=_Respuesta()):
            self.assertEqual(self.cliente(ana).post('/app/push/probar/').json()['enviados'], 1)
        self.assertFalse(Notificacion.objects.filter(destinatario=ana).exists())   # la prueba no llena la campana

    def test_el_service_worker_muestra_las_notificaciones(self):
        r = self.client.get('/sw.js')
        self.assertContains(r, "addEventListener('push'")
        self.assertContains(r, 'notificationclick')

    def test_el_boton_activar_sale_solo_con_sesion(self):
        self.assertContains(self.cliente(self.estudiantes[0].user).get(reverse('notas:dashboard'), follow=True), 'mc-avisos')
