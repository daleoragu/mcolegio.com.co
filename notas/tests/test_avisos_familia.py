# notas/tests/test_avisos_familia.py
"""Aviso a la familia al registrar una anotación en el observador."""
import datetime
from urllib.parse import unquote

from django.core import mail
from django.test import override_settings

from notas import avisos_familia as A
from notas.models import FichaEstudiante, RegistroObservador

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
    def test_al_registrar_se_envia_correo_y_se_ofrece_whatsapp(self):
        r = self.crear()
        registro = RegistroObservador.objects.get()
        self.assertRedirects(r, f'/observador/registro/{registro.id}/avisar/', fetch_redirect_response=False)
        self.assertEqual(len(mail.outbox), 1)
        cuerpo = mail.outbox[0].body
        self.assertEqual(mail.outbox[0].to, ['laura@example.com'])
        self.assertIn('anotación comportamental por mejorar', cuerpo)
        # Lo ocurrido no viaja en el mensaje.
        self.assertNotIn('pegó', cuerpo)
        h = self.c.get(f'/observador/registro/{registro.id}/avisar/').content.decode()
        self.assertIn('https://wa.me/573105551234?text=', h)
        self.assertNotIn('pegó', unquote(h.split('wa.me/')[1].split('"')[0]))

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
