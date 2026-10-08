"""Recuperar la contraseña: por correo (propio o del acudiente) y contraseña temporal del administrador."""
import re

from django.contrib.auth.models import User
from django.core import mail
from django.core.cache import cache
from django.test import override_settings

from notas.models import Docente, FichaEstudiante

from .base import CLAVE, ColegioDePrueba

CORREO = override_settings(EMAIL_HOST='smtp.prueba.co',
                           EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')


@CORREO
class RecuperarClave(ColegioDePrueba):

    def setUp(self):
        cache.clear()
        self.u_docente.email = 'profe@correo.co'
        self.u_docente.save()

    def _pedir(self, dato, host='a.localhost'):
        return self.cliente(host=host).post('/recuperar-clave/', {'dato': dato})

    def _enlace(self):
        return re.search(r'https?://[^/\s]+(/recuperar-clave/[^\s"<]+/)', mail.outbox[-1].body).group(1)

    def test_el_portal_tiene_el_enlace(self):
        h = self.cliente().get('/').content.decode()
        self.assertIn('/recuperar-clave/', h)

    def test_docente_recibe_enlace_y_cambia_la_clave(self):
        r = self._pedir('PROFE')                       # sin importar mayúsculas
        self.assertContains(r, 'en unos minutos le llega')
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ['profe@correo.co'])
        url = self._enlace()
        c = self.cliente()
        self.assertContains(c.get(url), 'Contraseña nueva')
        r = c.post(url, {'new_password1': 'Montaña-Azul-2026', 'new_password2': 'Montaña-Azul-2026'})
        self.assertContains(r, 'Contraseña cambiada')
        self.u_docente.refresh_from_db()
        self.assertTrue(self.u_docente.check_password('Montaña-Azul-2026'))
        # El enlace no sirve dos veces.
        self.assertContains(self.cliente().get(url), 'ya no sirve')

    def test_tambien_por_correo(self):
        self._pedir('profe@correo.co')
        self.assertEqual(len(mail.outbox), 1)

    def test_estudiante_sin_correo_va_al_acudiente(self):
        ana = self.estudiantes[0]
        FichaEstudiante.objects.create(estudiante=ana, email_acudiente='mama.ana@correo.co')
        self._pedir('ana')
        self.assertEqual(mail.outbox[0].to, ['mama.ana@correo.co'])
        self.assertIn('estudiante', mail.outbox[0].body)

    def test_misma_respuesta_si_no_existe(self):
        r = self._pedir('nadie-se-llama-asi')
        self.assertContains(r, 'en unos minutos le llega')
        self.assertEqual(len(mail.outbox), 0)

    def test_usuario_de_otro_colegio_no(self):
        u = User.objects.create_user('otro', password=CLAVE, email='otro@correo.co')
        Docente.objects.create(colegio=self.b, user=u)
        self._pedir('otro')
        self.assertEqual(len(mail.outbox), 0)
        # Y un enlace válido de otro colegio no sirve en este.
        self._pedir('otro', host='b.localhost')
        self.assertEqual(len(mail.outbox), 1)
        self.assertContains(self.cliente().get(self._enlace()), 'ya no sirve')

    def test_superusuario_no_se_recupera_por_aqui(self):
        self._pedir('dueno')
        self.assertEqual(len(mail.outbox), 0)

    def test_freno_de_intentos(self):
        for _ in range(5):
            self._pedir('profe')
        r = self._pedir('profe')
        self.assertContains(r, 'muchos intentos')
        self.assertEqual(len(mail.outbox), 5)


class SinCorreo(ColegioDePrueba):
    def test_explica_que_hable_con_el_administrador(self):
        cache.clear()
        r = self.cliente().get('/recuperar-clave/')
        self.assertContains(r, 'contraseña temporal')


class ClaveTemporal(ColegioDePrueba):

    def test_rectora_da_clave_temporal_a_un_estudiante(self):
        ana = self.estudiantes[0]
        r = self.cliente(self.rectora).post(f'/admin/restablecer-clave/{ana.user.id}/',
                                            {'volver': '/admin/gestion-estudiantes/'})
        self.assertEqual(r.status_code, 200)
        temporal = r.context['temporal']
        ana.user.refresh_from_db()
        self.assertTrue(ana.user.check_password(temporal))
        self.assertFalse(ana.user.check_password(CLAVE))
        self.assertNotRegex(temporal, '[0OlI1]')

    def test_docente_no_puede(self):
        ana = self.estudiantes[0]
        r = self.cliente(self.u_docente).post(f'/admin/restablecer-clave/{ana.user.id}/')
        self.assertEqual(r.status_code, 403)

    def test_no_a_otro_administrador_ni_a_otro_colegio(self):
        r = self.cliente(self.rectora).post(f'/admin/restablecer-clave/{self.super.id}/')
        self.assertEqual(r.status_code, 403)
        de_b = self.crear_estudiante('lejano', colegio=self.b, curso=None)
        r = self.cliente(self.rectora).post(f'/admin/restablecer-clave/{de_b.user.id}/')
        self.assertEqual(r.status_code, 403)

    def test_volver_no_acepta_otro_sitio(self):
        ana = self.estudiantes[0]
        r = self.cliente(self.rectora).post(f'/admin/restablecer-clave/{ana.user.id}/',
                                            {'volver': 'https://malo.example/'})
        self.assertEqual(r.context['volver'], '')
