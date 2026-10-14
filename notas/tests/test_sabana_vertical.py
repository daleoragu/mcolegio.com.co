from django.template import Context, Template
from django.test import SimpleTestCase

from notas.templatetags.nota_filters import svg_vertical


class TextoVerticalTests(SimpleTestCase):
    def test_nombre_corto_en_un_renglon(self):
        svg = svg_vertical('MATEMÁTICAS', 76)
        self.assertIn('rotate(-90)', svg)
        self.assertEqual(svg.count('<text '), 1)
        self.assertIn('height="76"', svg)

    def test_nombre_largo_se_parte(self):
        svg = svg_vertical('TECNOLOGÍA E INFORMÁTICA', 56)
        self.assertGreater(svg.count('<text '), 1)

    def test_escapa_el_texto(self):
        self.assertIn('&lt;b&gt;', svg_vertical('<b>', 40))

    def test_vacio(self):
        self.assertEqual(svg_vertical('', 40), '')

    def test_desde_plantilla(self):
        html = Template('{% load nota_filters %}{{ n|svg_vertical:60 }}').render(Context({'n': 'DEF. ÁREA'}))
        self.assertTrue(html.startswith('<svg'))
