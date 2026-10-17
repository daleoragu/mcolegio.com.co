"""App instalable: manifiesto por colegio, iconos, service worker y botón."""
import io
import json

from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image

from notas.views.app_views import _nombre_corto

from .base import ColegioDePrueba


class AppInstalable(ColegioDePrueba):

    def setUp(self):
        cache.clear()

    def test_manifiesto_del_colegio(self):
        r = self.cliente().get('/manifest.webmanifest')
        self.assertEqual(r['Content-Type'], 'application/manifest+json; charset=utf-8')
        m = json.loads(r.content)
        self.assertEqual((m['name'], m['display'], m['start_url'], m['scope']), ('Colegio A', 'standalone', '/app/', '/'))
        self.assertEqual(len(m['icons']), 3)
        self.assertEqual(_nombre_corto('Institución Educativa Técnica General Santander'), 'IETGS')

    def test_iconos_con_y_sin_escudo(self):
        for tam in (192, 512):
            r = self.cliente().get(f'/app/icono-{tam}.png')
            self.assertEqual(r['Content-Type'], 'image/png')
            self.assertEqual(Image.open(io.BytesIO(r.content)).size, (tam, tam))
        buf = io.BytesIO()
        Image.new('RGB', (300, 150), (200, 0, 0)).save(buf, 'PNG')
        self.a.escudo = SimpleUploadedFile('escudo.png', buf.getvalue(), content_type='image/png')
        self.a.save()
        img = Image.open(io.BytesIO(self.cliente().get('/app/icono-512.png?maskable=1').content)).convert('RGB')
        self.assertEqual(img.getpixel((256, 256)), (200, 0, 0))       # el escudo en el centro
        self.assertEqual(img.getpixel((5, 5)), (255, 255, 255))       # margen blanco
        self.assertEqual(self.cliente().get('/app/icono-100.png').status_code, 404)

    def test_service_worker_y_sin_conexion(self):
        r = self.cliente().get('/sw.js')
        self.assertEqual(r['Service-Worker-Allowed'], '/')
        self.assertIn('application/javascript', r['Content-Type'])
        self.assertContains(r, "SIN_CONEXION = '/sin-conexion/'")
        self.assertContains(self.cliente().get('/sin-conexion/'), 'No hay conexión a internet')

    def test_inicio_de_la_app(self):
        self.assertRedirects(self.cliente().get('/app/'), '/', fetch_redirect_response=False)
        self.assertRedirects(self.cliente(self.rectora).get('/app/'), '/dashboard/', fetch_redirect_response=False)

    def test_las_paginas_traen_el_manifiesto(self):
        for c, url in ((self.cliente(self.rectora), '/panel-administrador/'), (self.cliente(), '/')):
            html = c.get(url).content.decode()
            self.assertIn('rel="manifest" href="/manifest.webmanifest"', html)
            self.assertIn("navigator.serviceWorker.register('/sw.js')", html)
