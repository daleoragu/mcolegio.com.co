# -*- coding: utf-8 -*-
"""Las páginas subidas guardan resultados aunque se abran por otra dirección."""
import json

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, RequestFactory, TestCase, override_settings

from .models import Cuenta, PaginaPublicada, Sesion
from .utils import reescribir_endpoint
from .views import publicar_archivo

HTML = """<html><body><script>
{decl} ENDPOINT = "";
{decl} CLAVE_PANEL = '';
</script></body></html>"""


@override_settings(SALON_DOMINIO_PUBLICO='mcolegio.com.co')
class GuardarResultados(TestCase):

    @classmethod
    def setUpTestData(cls):
        u = User.objects.create_user('profe', password='x')
        cls.cuenta = Cuenta.objects.create(usuario=u, slug='profe', nombre_publico='Profe', estado='verificada',
                                           plan='ilimitado')

    def _publicar(self, decl='const'):
        pagina = PaginaPublicada.objects.create(propietario=self.cuenta, titulo='Taller', slug='taller',
                                                identificacion='libre')
        archivo = SimpleUploadedFile('taller.html', HTML.format(decl=decl).encode())
        publicar_archivo(RequestFactory().get('/', HTTP_HOST='mcolegio.com.co'), pagina, archivo)
        pagina.refresh_from_db()
        return pagina

    def test_let_y_var_tambien_se_conectan(self):
        for decl in ('let', 'var', 'const'):
            texto, ok = reescribir_endpoint(HTML.format(decl=decl), '/api/x/')
            self.assertTrue(ok, decl)
            self.assertIn("ENDPOINT = '/api/x/'", texto)

    def test_desde_otra_direccion_el_envio_va_al_mismo_sitio(self):
        pagina = self._publicar('let')
        self.assertTrue(pagina.endpoint_reescrito)
        # El estudiante entra por el subdominio de un colegio, no por mcolegio.com.co.
        c = Client(HTTP_HOST='sanfrancisco.mcolegio.com.co')
        r = c.get('/p/profe/taller/')
        texto = r.content.decode()
        self.assertIn("ENDPOINT = '/salon_digital/api/profe/taller/'", texto)
        self.assertIn('https://www.mcolegio.com.co', r['Content-Security-Policy'])
        # Y el envío (como lo hace salon.js: text/plain) se guarda.
        r = c.post('/salon_digital/api/profe/taller/', json.dumps({'ape': 'Pérez', 'nom': 'Ana', 'ok': 3, 'total': 5}),
                   content_type='text/plain;charset=utf-8')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(Sesion.objects.get().completo, 'Pérez Ana')
