# -*- coding: utf-8 -*-
"""Tamaño de hoja del documento: carta, oficio, A4 o personalizado; se respeta en el PDF y en el Word."""
import io

from django.contrib.auth.models import User
from django.test import Client, RequestFactory, TestCase

from materiales import bloques as B
from materiales import exportar
from materiales.models import Documento
from salon_digital.models import Cuenta


class TamanoDeHoja(TestCase):

    def setUp(self):
        self.u = User.objects.create_user('profe', password='x', first_name='Ana')
        Cuenta.objects.create(usuario=self.u, slug='ana', nombre_publico='Ana', estado='verificada', plan='ilimitado')
        self.c = Client(HTTP_HOST='localhost'); self.c.force_login(self.u)

    def doc(self, papel):
        contenido = {'bloques': [{'tipo': 'texto', 'html': '<p>Hola</p>'}], 'opciones': {'papel': papel}}
        return Documento.objects.create(propietario=self.u, titulo='Guía', tipo='taller', contenido=contenido)

    def test_limpiar_papel(self):
        self.assertEqual(B.papel(None)['tipo'], 'carta')
        self.assertEqual((B.papel({'tipo': 'oficio'})['ancho_mm'], B.papel({'tipo': 'oficio'})['alto_mm']), (215.9, 330.2))
        p = B.papel({'tipo': 'personalizado', 'unidad': 'cm', 'ancho': '15,5', 'alto': 20})
        self.assertEqual((p['ancho_mm'], p['alto_mm'], p['unidad']), (155.0, 200.0, 'cm'))
        p = B.papel({'tipo': 'personalizado', 'unidad': 'in', 'ancho': 8.5, 'alto': 11})
        self.assertEqual((p['ancho_mm'], p['alto_mm']), (215.9, 279.4))
        p = B.papel({'tipo': 'personalizado', 'unidad': 'px', 'ancho': 96, 'alto': 'nada'})
        self.assertEqual(p['ancho_mm'], 70.0)                      # mínimo 7 cm
        self.assertEqual(B.papel({'tipo': 'raro'})['tipo'], 'carta')

    def test_pdf_y_word_con_el_tamano(self):
        from pypdf import PdfReader
        doc = self.doc({'tipo': 'personalizado', 'unidad': 'cm', 'ancho': 15, 'alto': 20})
        r = RequestFactory().get('/'); r.user = self.u
        pdf = exportar.pdf(r, doc)
        caja = PdfReader(io.BytesIO(pdf)).pages[0].mediabox
        self.assertAlmostEqual(float(caja.width) / 72 * 25.4, 150, delta=1)
        self.assertAlmostEqual(float(caja.height) / 72 * 25.4, 200, delta=1)
        doc = self.doc({'tipo': 'oficio'})
        from docx import Document
        w = Document(io.BytesIO(exportar.docx(doc)))
        self.assertAlmostEqual(w.sections[0].page_height.mm, 330.2, delta=0.5)

    def test_editor_trae_el_selector_y_pantalla_completa(self):
        doc = self.doc({'tipo': 'carta'})
        r = self.c.get(f'/materiales/{doc.pk}/')
        self.assertContains(r, 'id="mm-papel"')
        self.assertContains(r, 'Oficio (21,6 × 33 cm)')
        self.assertContains(r, 'id="mm-papel-unidad"')
        self.assertContains(r, 'mm-completo')
