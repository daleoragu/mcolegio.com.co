"""«Probar el correo» del dueño de la plataforma y el registro de los envíos que fallan."""
import smtplib
from unittest import mock

from django.core import mail
from django.test import override_settings

from notas import mensajeria
from notas.tests.base import ColegioDePrueba

CORREO = dict(EMAIL_HOST='smtp.gmail.com', EMAIL_PORT=587, EMAIL_HOST_USER='mcolegiomc@gmail.com',
              EMAIL_HOST_PASSWORD='abcd efgh ijkl mnop', DEFAULT_FROM_EMAIL='mcolegio <mcolegiomc@gmail.com>',
              EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')


class ProbarCorreo(ColegioDePrueba):

    def test_solo_el_dueno(self):
        self.assertEqual(self.cliente(self.rectora).get('/plataforma/probar-correo/').status_code, 302)

    def test_sin_configurar(self):
        with override_settings(EMAIL_HOST=''):
            r = self.cliente(self.super).post('/plataforma/probar-correo/', {'destino': 'x@y.co'})
        self.assertContains(r, 'falta EMAIL_HOST')

    def test_manda_la_prueba_y_avisa_espacios(self):
        with override_settings(**CORREO), mock.patch('socket.create_connection'):
            r = self.cliente(self.super).post('/plataforma/probar-correo/', {'destino': 'x@y.co', 'colegio': self.a.pk})
        self.assertContains(r, 'tiene espacios')
        self.assertContains(r, 'Correo entregado al servidor')
        self.assertNotContains(r, 'abcd efgh')                       # la contraseña nunca se muestra
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('Colegio A', mail.outbox[0].from_email)

    def test_error_explicado(self):
        e = smtplib.SMTPAuthenticationError(535, b'Username and Password not accepted')
        self.assertIn('contraseña de aplicación', mensajeria.explicar_error(e))
        with override_settings(**CORREO), mock.patch('socket.create_connection', side_effect=TimeoutError()):
            r = self.cliente(self.super).post('/plataforma/probar-correo/', {'destino': 'x@y.co'})
        self.assertContains(r, 'no pueda salir por ese puerto')
