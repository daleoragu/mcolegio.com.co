"""La app propia de Mi Salón Virtual: manifiesto, entrada, página de instalar y assetlinks de la APK."""
import json
import os
from unittest import mock

from django.contrib.auth.models import User
from django.test import TestCase

from .models import Cuenta


class AppMiSalon(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.u = User.objects.create_user('profe', password='x', first_name='Pedro')
        Cuenta.objects.create(usuario=cls.u, slug='profe', nombre_publico='Pedro', estado='verificada', plan='ilimitado')

    def test_manifiesto_propio(self):
        m = json.loads(self.client.get('/salon_digital/manifest.webmanifest').content)
        self.assertEqual(m['id'], '/salon_digital/app/')                 # distinta de la app de los colegios («/»)
        self.assertEqual(m['short_name'], 'Mi Salón'); self.assertEqual(m['display'], 'standalone')
        self.assertTrue(any(i['purpose'] == 'maskable' for i in m['icons']))
        self.assertEqual({s['name'] for s in m['shortcuts']}, {'Mis aulas', 'Grupos', 'Eventos', 'Colegas'})
        for i in m['icons']:                                              # los íconos existen
            self.assertTrue(os.path.exists('salon_digital/static/' + i['src'].split('/static/')[1]))

    def test_entrada_de_la_app(self):
        self.assertIn('/salon_digital/entrar/', self.client.get('/salon_digital/app/')['Location'])
        self.client.force_login(self.u)
        self.assertEqual(self.client.get('/salon_digital/app/')['Location'], '/aula/')

    def test_paginas_con_manifiesto_e_instalar(self):
        self.client.force_login(self.u)
        r = self.client.get('/salon_digital/panel/')
        self.assertContains(r, '/salon_digital/manifest.webmanifest'); self.assertContains(r, 'apple-touch-icon')
        self.assertContains(r, 'Instalar la app')
        r = self.client.get('/salon_digital/app/instalar/')
        self.assertContains(r, 'Agregar a inicio'); self.assertContains(r, '<svg'); self.assertContains(r, 'Activar avisos')
        self.assertNotContains(r, 'Descargar la APK')                     # sin APK publicada no sale el botón
        with mock.patch.dict(os.environ, {'SALON_APK_URL': 'https://ejemplo.com/MiSalon.apk', 'SALON_PLAY_URL': 'https://play.google.com/x'}):
            r = self.client.get('/salon_digital/app/instalar/')
            self.assertContains(r, 'https://ejemplo.com/MiSalon.apk'); self.assertContains(r, 'Google Play')

    def test_assetlinks(self):
        self.assertEqual(self.client.get('/.well-known/assetlinks.json').json(), [])
        with mock.patch.dict(os.environ, {'ANDROID_SHA256': 'aa:bb:cc, DD:EE'}):
            d = self.client.get('/.well-known/assetlinks.json').json()
        self.assertEqual(d[0]['target']['package_name'], 'co.com.mcolegio.misalon')
        self.assertEqual(d[0]['target']['sha256_cert_fingerprints'], ['AA:BB:CC', 'DD:EE'])
