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
        self.assertEqual(mail.outbox[0].from_email, 'Colegio A <mcolegiomc@gmail.com>')
        # El nombre del colegio con tildes y el remitente con nombre no dañan la dirección
        self.a.nombre = 'INSTITUCIÓN EDUCATIVA TÉCNICA GENERAL'
        with override_settings(**CORREO):
            m = mensajeria.mensaje(self.a, 'x', 'y', ['x@y.co'])
            m.message()
            self.assertTrue(m.from_email.endswith('<mcolegiomc@gmail.com>'))
            self.assertEqual(mensajeria.remitente(None), 'mcolegio <mcolegiomc@gmail.com>')

    def test_error_explicado(self):
        e = smtplib.SMTPAuthenticationError(535, b'Username and Password not accepted')
        self.assertIn('contraseña de aplicación', mensajeria.explicar_error(e))
        with override_settings(**CORREO), mock.patch('socket.create_connection', side_effect=TimeoutError()):
            r = self.cliente(self.super).post('/plataforma/probar-correo/', {'destino': 'x@y.co'})
        self.assertContains(r, 'no pueda salir por ese puerto')


class CopiaParaElColegio(ColegioDePrueba):

    def test_copia_oculta_y_una_sola_copia_de_las_circulares(self):
        self.a.correo_copias = 'archivo@colegio.edu.co'
        self.a.save(update_fields=['correo_copias'])
        with override_settings(**CORREO):
            mensajeria.enviar_correo(self.a, 'Observador', 'Texto', ['familia@x.co'])
            self.assertEqual(mail.outbox[-1].bcc, ['archivo@colegio.edu.co'])
            self.assertEqual(mail.outbox[-1].to, ['familia@x.co'])
            # El enlace de recuperar la contraseña no se copia
            from notas.recuperar_clave import _mandar
            _mandar('Recuperar', 'enlace', 'docente@x.co', '<p>enlace</p>', self.a)
            self.assertEqual(mail.outbox[-1].bcc, [])
            # Una circular a tres familias: tres correos y UNA copia para el archivo
            antes = len(mail.outbox)
            mensajes = [mensajeria.mensaje(self.a, 'Circular N.º 1: Reunión', 'Cuerpo', [f'f{i}@x.co'], copia=False)
                        for i in range(3)]
            self.assertEqual(mensajeria.enviar_varios(mensajes, copia_de=self.a), 3)
            nuevos = mail.outbox[antes:]
            self.assertEqual(len(nuevos), 4)
            self.assertTrue(all(not m.bcc for m in nuevos))
            self.assertEqual(nuevos[-1].to, ['archivo@colegio.edu.co'])
            self.assertTrue(nuevos[-1].subject.startswith('[Copia · 3 destinatarios]'))
        # Sin correo de copias no se agrega nada
        self.a.correo_copias = ''
        with override_settings(**CORREO):
            mensajeria.enviar_correo(self.a, 'Aviso', 'Texto', ['familia@x.co'])
        self.assertEqual(mail.outbox[-1].bcc, [])

    def test_se_configura_en_la_personalizacion(self):
        from notas.forms.portal_forms import ColegioPersonalizacionForm
        self.assertIn('correo_copias', ColegioPersonalizacionForm().fields)
