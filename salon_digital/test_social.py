"""Entrar o crear la cuenta de Mi Salón Virtual con Google o Facebook."""
import os
from unittest import mock
from urllib.parse import parse_qs, urlparse

from django.contrib.auth.models import User
from django.test import Client, TestCase

GOOGLE = {'GOOGLE_OAUTH_CLIENT_ID': 'id-g', 'GOOGLE_OAUTH_CLIENT_SECRET': 'sec-g'}
FACEBOOK = {'FACEBOOK_APP_ID': 'id-f', 'FACEBOOK_APP_SECRET': 'sec-f'}


def respuesta(datos):
    r = mock.Mock()
    r.json.return_value = datos
    r.raise_for_status.return_value = None
    return r


class EntrarConRedes(TestCase):

    def setUp(self):
        self.c = Client(HTTP_HOST='localhost')

    def iniciar(self, proveedor):
        r = self.c.get(f'/salon_digital/auth/{proveedor}/')
        self.assertEqual(r.status_code, 302)
        return parse_qs(urlparse(r.url).query)['state'][0], r.url

    def test_sin_claves_no_hay_botones(self):
        with mock.patch.dict(os.environ, {}, clear=False):
            for k in list(GOOGLE) + list(FACEBOOK):
                os.environ.pop(k, None)
            self.assertNotContains(self.c.get('/salon_digital/registro/'), 'Continuar con Google')
            r = self.c.get('/salon_digital/auth/google/')
            self.assertEqual(r.url, '/salon_digital/registro/')

    @mock.patch.dict(os.environ, {**GOOGLE, **FACEBOOK})
    def test_google_crea_el_usuario_y_pide_los_datos_del_salon(self):
        self.assertContains(self.c.get('/salon_digital/registro/'), 'Continuar con Google')
        self.assertContains(self.c.get('/salon_digital/'), 'Facebook')
        estado, url = self.iniciar('google')
        self.assertTrue(url.startswith('https://accounts.google.com/'))
        self.assertIn('redirect_uri=', url)
        perfil = {'email': 'Profe.Lina@Gmail.com', 'email_verified': True, 'name': 'Lina Pérez',
                  'given_name': 'Lina', 'family_name': 'Pérez'}
        with mock.patch('salon_digital.social.requests.post', return_value=respuesta({'access_token': 't'})), \
                mock.patch('salon_digital.social.requests.get', return_value=respuesta(perfil)):
            r = self.c.get('/salon_digital/auth/google/vuelta/', {'state': estado, 'code': 'abc'})
        self.assertEqual(r.url, '/salon_digital/crear-cuenta/')
        u = User.objects.get(email='profe.lina@gmail.com')
        self.assertEqual((u.first_name, u.last_name), ('Lina', 'Pérez'))
        self.assertFalse(u.has_usable_password())
        r = self.c.get('/salon_digital/crear-cuenta/')
        self.assertContains(r, 'linaperez')
        # Vuelve a entrar: mismo usuario
        estado, _ = self.iniciar('google')
        with mock.patch('salon_digital.social.requests.post', return_value=respuesta({'access_token': 't'})), \
                mock.patch('salon_digital.social.requests.get', return_value=respuesta(perfil)):
            self.c.get('/salon_digital/auth/google/vuelta/', {'state': estado, 'code': 'abc'})
        self.assertEqual(User.objects.filter(email__iexact='profe.lina@gmail.com').count(), 1)

    @mock.patch.dict(os.environ, {**GOOGLE, **FACEBOOK})
    def test_estado_falso_o_sin_correo_o_administrador(self):
        self.iniciar('google')
        r = self.c.get('/salon_digital/auth/google/vuelta/', {'state': 'falso', 'code': 'abc'})
        self.assertEqual(r.url, '/salon_digital/registro/')
        self.assertFalse(User.objects.exists())

        estado, _ = self.iniciar('facebook')
        with mock.patch('salon_digital.social.requests.get',
                        side_effect=[respuesta({'access_token': 't'}), respuesta({'id': '1', 'name': 'Sin Correo'})]):
            self.c.get('/salon_digital/auth/facebook/vuelta/', {'state': estado, 'code': 'abc'})
        self.assertFalse(User.objects.exists())

        User.objects.create_user('jefe', 'jefe@mcolegio.com.co', 'x', is_staff=True)
        estado, _ = self.iniciar('facebook')
        perfil = {'id': '2', 'name': 'Jefe', 'email': 'jefe@mcolegio.com.co'}
        with mock.patch('salon_digital.social.requests.get',
                        side_effect=[respuesta({'access_token': 't'}), respuesta(perfil)]):
            self.c.get('/salon_digital/auth/facebook/vuelta/', {'state': estado, 'code': 'abc'})
        self.assertNotIn('_auth_user_id', self.c.session)

    def test_pagina_para_eliminar_datos(self):
        self.assertContains(self.c.get('/salon_digital/eliminar-datos/'), 'eliminar tu cuenta')
