"""Correos con el nombre del colegio y la línea única de WhatsApp."""
import json
import os
from unittest import mock

from django.core import mail
from django.test import override_settings

from notas import mensajeria

from .base import ColegioDePrueba

VARIABLES_WA = {'WHATSAPP_TOKEN': 'x', 'WHATSAPP_PHONE_ID': '123', 'WHATSAPP_PLANTILLA': 'aviso'}


@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
                   DEFAULT_FROM_EMAIL='avisos@mcolegio.com.co')
class Correos(ColegioDePrueba):

    def test_sale_con_el_nombre_del_colegio_y_responde_al_colegio(self):
        self.a.email_contacto = 'rectoria@colegioa.edu.co'
        mensajeria.enviar_correo(self.a, 'Hola', 'Texto', ['papa@example.com'])
        m = mail.outbox[0]
        self.assertEqual(m.from_email, 'Colegio A <avisos@mcolegio.com.co>')
        self.assertEqual(m.reply_to, ['rectoria@colegioa.edu.co'])

    def test_con_correo_verificado_sale_desde_el_del_colegio(self):
        self.a.email_contacto = 'rectoria@colegioa.edu.co'
        self.a.correo_remitente_verificado = True
        self.assertEqual(mensajeria.remitente(self.a), 'Colegio A <rectoria@colegioa.edu.co>')
        self.a.email_contacto = ''
        self.assertEqual(mensajeria.remitente(self.a), 'Colegio A <avisos@mcolegio.com.co>')
        self.assertIsNone(mensajeria.responder_a(self.a))
        self.assertEqual(mensajeria.enviar_correo(self.a, 'x', 'y', ['', None]), 0)


class WhatsApp(ColegioDePrueba):

    def test_numeros(self):
        self.assertEqual(mensajeria.numero_whatsapp('310 555 1234'), '573105551234')
        self.assertEqual(mensajeria.numero_whatsapp('+57 310-555-1234'), '573105551234')
        self.assertEqual(mensajeria.numero_whatsapp('12345'), '')

    def test_sin_configurar_no_envia(self):
        with mock.patch.dict(os.environ, {}, clear=False):
            os.environ.pop('WHATSAPP_TOKEN', None)
            self.assertFalse(mensajeria.enviar_whatsapp(self.a, '3105551234', 'hola')[0])

    def test_envia_la_plantilla_si_el_colegio_lo_activo(self):
        respuesta = mock.MagicMock(status=200)
        respuesta.__enter__.return_value = respuesta
        with mock.patch.dict(os.environ, VARIABLES_WA), \
                mock.patch('urllib.request.urlopen', return_value=respuesta) as abrir:
            self.assertFalse(mensajeria.enviar_whatsapp(self.a, '3105551234', 'hola')[0])   # el colegio no lo activó
            self.a.whatsapp_automatico = True
            ok, destino = mensajeria.enviar_whatsapp(self.a, '3105551234', 'Aviso\ncon   saltos')
        self.assertTrue(ok)
        self.assertEqual(destino, '573105551234')
        req = abrir.call_args[0][0]
        self.assertIn('/123/messages', req.full_url)
        cuerpo = json.loads(req.data)
        self.assertEqual(cuerpo['template']['name'], 'aviso')
        self.assertEqual([p['text'] for p in cuerpo['template']['components'][0]['parameters']],
                         ['Colegio A', 'Aviso con saltos'])
<<<<<<< HEAD
=======


class ErroresDeMeta(ColegioDePrueba):
    """Cuando Meta rechaza, el motivo queda en palabras para quien administra."""

    def test_motivo_en_palabras(self):
        import io
        import urllib.error
        cuerpo = io.BytesIO(json.dumps({'error': {'code': 132001, 'message': 'Template name does not exist'}}).encode())
        fallo = urllib.error.HTTPError('u', 404, 'Not Found', {}, cuerpo)
        self.a.whatsapp_automatico = True
        with mock.patch.dict(os.environ, VARIABLES_WA), mock.patch('urllib.request.urlopen', side_effect=fallo):
            ok, detalle = mensajeria.enviar_whatsapp(self.a, '3105551234', 'hola')
        self.assertFalse(ok)
        self.assertIn('404', detalle)
        self.assertIn('plantilla no existe', detalle)
>>>>>>> origin/mejoras-23-octubre
