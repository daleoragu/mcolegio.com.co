# notas/tests/test_avisos_familia.py
"""Aviso a la familia al registrar una anotación en el observador."""
import datetime
import re
from urllib.parse import unquote

from django.core import mail
from django.test import override_settings

from notas import avisos_familia as A
from notas.models import FichaEstudiante, Notificacion, RegistroObservador

from .base import ColegioDePrueba


class AvisosFamilia(ColegioDePrueba):

    def setUp(self):
        self.est = self.estudiantes[0]
        FichaEstudiante.objects.update_or_create(estudiante=self.est, defaults={
            'nombre_acudiente': 'Laura Prueba', 'celular_acudiente': '310 555 1234',
            'nombre_madre': 'Laura Prueba', 'celular_madre': '3105551234',    # repetido
            'celular_padre': '601 123 4567',                                  # fijo: no sirve
            'email_acudiente': 'laura@example.com'})
        self.c = self.cliente(self.rectora)

    def test_celulares(self):
        self.assertEqual(A.normalizar_celular('310 555 1234'), '573105551234')
        self.assertEqual(A.normalizar_celular('+57 310-555-1234'), '573105551234')
        self.assertIsNone(A.normalizar_celular('601 123 4567'))
        self.assertIsNone(A.normalizar_celular(''))
        self.est.refresh_from_db()
        self.assertEqual([c['rol'] for c in A.contactos(self.est)], ['Acudiente'])

    def crear(self, **extra):
        datos = {'fecha_suceso': '2026-10-07', 'tipo': 'COMPORTAMENTAL', 'subtipo': 'NEGATIVA',
                 'descripcion': 'Le pegó a un compañero en el descanso.', **extra}
        return self.c.post(f'/observador/crear/{self.est.id}/', datos)

    @override_settings(EMAIL_HOST='smtp.example.com')
    def test_al_registrar_se_envia_correo_con_motivo_y_enlace(self):
        r = self.crear()
        registro = RegistroObservador.objects.get()
        self.assertRedirects(r, f'/observador/registro/{registro.id}/avisar/', fetch_redirect_response=False)
        self.assertEqual(len(mail.outbox), 1)
        correo = mail.outbox[0]
        self.assertEqual(correo.to, ['laura@example.com'])
        self.assertIn('anotación comportamental por mejorar', correo.body)
        self.assertIn('Motivo: Le pegó a un compañero', correo.body)
        self.assertIn('/familia/observador/', correo.body)
        html = correo.alternatives[0][0]
        self.assertIn('Ver la anotación y responder', html)
        # WhatsApp también lleva el motivo.
        h = self.c.get(f'/observador/registro/{registro.id}/avisar/').content.decode()
        self.assertIn('https://wa.me/573105551234?text=', h)
        self.assertIn('pegó', unquote(h.split('wa.me/')[1].split('"')[0]))

    @override_settings(EMAIL_HOST='smtp.example.com')
    def test_el_acudiente_responde_desde_el_enlace(self):
        self.crear()
        registro = RegistroObservador.objects.get()
        enlace = re.search(r'(/familia/observador/[^\s/]+/)', mail.outbox[0].body).group(1)
        familia = self.cliente()                       # sin iniciar sesión
        h = familia.get(enlace).content.decode()
        self.assertIn('Le pegó a un compañero', h)
        self.assertIn('Me doy por enterado', h)
        r = familia.post(enlace, {'firma': 'Laura Prueba', 'descargo': 'Hablamos en casa y se compromete.'})
        self.assertEqual(r.status_code, 302)
        registro.refresh_from_db()
        self.assertIsNotNone(registro.acudiente_enterado)
        self.assertEqual(registro.firma_acudiente, 'Laura Prueba')
        self.assertIn('Respuesta recibida', familia.get(enlace).content.decode())
        # Solo una vez.
        familia.post(enlace, {'firma': 'Otra Persona', 'descargo': 'cambio'})
        registro.refresh_from_db()
        self.assertEqual(registro.firma_acudiente, 'Laura Prueba')
        # Quien registró la anotación se entera, y el observador lo muestra.
        self.assertTrue(Notificacion.objects.filter(destinatario=self.rectora).exists() or
                        registro.docente_reporta is None)
        self.assertIn('Hablamos en casa', self.c.get(f'/observador/detalle/{self.est.id}/').content.decode())

    @override_settings(EMAIL_HOST='smtp.example.com')
    def test_enlaces_falsos_o_viejos_no_sirven(self):
        self.crear()
        registro = RegistroObservador.objects.get()
        token = A.token_respuesta(registro)
        familia = self.cliente()
        self.assertEqual(familia.get(f'/familia/observador/{token}x/').status_code, 404)
        # Si cambian el correo del acudiente, el enlace anterior deja de servir.
        FichaEstudiante.objects.filter(estudiante=self.est).update(email_acudiente='otro@example.com')
        self.assertEqual(familia.get(f'/familia/observador/{token}/').status_code, 404)
        # Y desde otro colegio tampoco.
        FichaEstudiante.objects.filter(estudiante=self.est).update(email_acudiente='laura@example.com')
        self.assertEqual(self.cliente(host='b.localhost').get(f'/familia/observador/{token}/').status_code, 404)

    def test_sin_correo_configurado_no_falla(self):
        r = self.crear(subtipo='POSITIVA')
        self.assertEqual(r.status_code, 302)
        self.assertEqual(len(mail.outbox), 0)
        registro = RegistroObservador.objects.get()
        self.assertIn('¡Felicitaciones!', A.texto_aviso(registro))
        h = self.c.get(f'/observador/registro/{registro.id}/avisar/').content.decode()
        self.assertIn('no está configurado', h)

    def test_otro_colegio_no_entra(self):
        registro = RegistroObservador.objects.create(
            colegio=self.a, estudiante=self.est, fecha_suceso=datetime.date(2026, 10, 7),
            tipo='COMPORTAMENTAL', descripcion='x')
        r = self.cliente(self.super, host='b.localhost').get(f'/observador/registro/{registro.id}/avisar/')
        self.assertEqual(r.status_code, 404)
