"""Portal: redes sociales, recursos educativos y pie compacto."""
from django.core.files.uploadedfile import SimpleUploadedFile

from notas.models import Colegio, RecursoEducativo

from .base import ColegioDePrueba


class RedesSociales(ColegioDePrueba):

    def test_la_seccion_es_html_y_no_json(self):
        Colegio.objects.filter(pk=self.a.pk).update(url_facebook='https://facebook.com/colegio-a',
                                                    url_tiktok='https://www.tiktok.com/@colegioa')
        r = self.cliente().get('/ajax/redes-sociales/')
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r['Content-Type'].startswith('text/html'))
        self.assertContains(r, 'Conéctate con Nosotros')
        self.assertContains(r, 'href="https://www.tiktok.com/@colegioa"')
        self.assertNotContains(r, '"facebook":')

    def test_sin_redes(self):
        self.assertContains(self.cliente().get('/ajax/redes-sociales/'), 'aún no han sido configuradas')


class RecursosEducativos(ColegioDePrueba):
    URL = '/admin/portal/recursos/'

    def test_sin_recursos_salen_los_sugeridos(self):
        r = self.cliente().get('/ajax/recursos-educativos/')
        self.assertContains(r, 'Khan Academy')

    def test_el_admin_agrega_y_salen_en_el_portal(self):
        c = self.cliente(self.rectora)
        self.assertContains(c.get('/admin/portal/configuracion/'), 'Recursos Educativos')
        self.assertContains(c.get('/admin/portal/personalizacion/'), 'Recursos educativos')
        self.assertContains(c.get(self.URL), 'Agregar recurso')
        r = c.post(self.URL, {'titulo': 'GeoGebra', 'categoria': 'Matemáticas', 'descripcion': 'Geometría dinámica',
                              'enlace': 'https://www.geogebra.org', 'orden': '0', 'visible': 'on'})
        self.assertEqual(r.status_code, 302)
        c.post(self.URL, {'titulo': 'Borrador', 'enlace': 'https://ejemplo.co', 'orden': '0'})   # oculto
        guia = SimpleUploadedFile('guia.pdf', b'%PDF-1.4 prueba', content_type='application/pdf')
        c.post(self.URL, {'titulo': 'Guía de fracciones', 'categoria': 'Matemáticas', 'archivo': guia, 'orden': '1',
                          'visible': 'on'})
        self.assertEqual(RecursoEducativo.objects.filter(colegio=self.a).count(), 3)
        publico = self.cliente().get('/ajax/recursos-educativos/')
        self.assertContains(publico, 'GeoGebra')
        self.assertContains(publico, 'Guía de fracciones')
        self.assertContains(publico, 'Matemáticas', count=1)          # una sola categoría, agrupada
        self.assertNotContains(publico, 'Borrador')
        self.assertNotContains(publico, 'Khan Academy')              # ya no salen los sugeridos
        # Otro colegio no los ve.
        self.assertNotContains(self.cliente(host='b.localhost').get('/ajax/recursos-educativos/'), 'GeoGebra')

    def test_validaciones(self):
        c = self.cliente(self.rectora)
        self.assertContains(c.post(self.URL, {'titulo': 'Nada', 'orden': '0'}), 'Pegue un enlace o suba un archivo')
        self.assertEqual(c.post(self.URL, {'titulo': 'X', 'enlace': 'javascript:alert(1)', 'orden': '0'}).status_code, 200)
        malo = SimpleUploadedFile('pagina.html', b'<script>alert(1)</script>', content_type='text/html')
        self.assertContains(c.post(self.URL, {'titulo': 'X', 'archivo': malo, 'orden': '0'}), 'Tipo de archivo no permitido')
        self.assertFalse(RecursoEducativo.objects.exists())

    def test_editar_y_eliminar_solo_los_del_colegio(self):
        ajeno = RecursoEducativo.objects.create(colegio=self.b, titulo='De B', enlace='https://b.co')
        c = self.cliente(self.rectora)
        self.assertEqual(c.get(f'/admin/portal/recursos/editar/{ajeno.pk}/').status_code, 404)
        self.assertEqual(c.post(f'/admin/portal/recursos/eliminar/{ajeno.pk}/').status_code, 404)
        propio = RecursoEducativo.objects.create(colegio=self.a, titulo='Propio', enlace='https://a.co')
        c.post(f'/admin/portal/recursos/editar/{propio.pk}/', {'titulo': 'Propio 2', 'enlace': 'https://a.co',
                                                               'orden': '0', 'visible': 'on'})
        propio.refresh_from_db()
        self.assertEqual(propio.titulo, 'Propio 2')
        c.post(f'/admin/portal/recursos/eliminar/{propio.pk}/')
        self.assertFalse(RecursoEducativo.objects.filter(pk=propio.pk).exists())

    def test_estudiantes_no(self):
        r = self.cliente(self.estudiantes[0].user).get(self.URL)
        self.assertNotEqual(r.status_code, 200)


class PieYMenuLateral(ColegioDePrueba):

    def test_pie_compacto_y_lateral(self):
        Colegio.objects.filter(pk=self.a.pk).update(layout_portal='sidebar', direccion='Cl. 9 #19-53', ciudad='Honda')
        h = self.cliente().get('/').content.decode()
        self.assertIn('class="portal-footer mt-auto"', h)
        self.assertIn('pf-datos', h)
        self.assertIn('.sidebar-logo {', h)
        self.assertIn('Recursos educativos', h)
