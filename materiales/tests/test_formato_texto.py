"""Formato del texto como en Word: alineación del párrafo, tipo y tamaño de letra y tachado (editor, PDF y Word)."""
import io
import json

from django.test import SimpleTestCase

from materiales import bloques as B
from materiales.models import Documento
from notas.tests.base import ColegioDePrueba

# Lo que deja el navegador al usar los botones del editor
DEL_EDITOR = ('<p style="text-align: center;"><span style="font-family: Georgia, &quot;DejaVu Serif&quot;, serif;">'
              '<span style="font-size: 20pt;">Primer</span></span> párrafo</p>'
              '<div style="text-align: justify;">Texto justificado <strike>tachado</strike></div>'
              '<p align="right">derecha</p>')


class Limpieza(SimpleTestCase):
    def test_se_conserva_lo_permitido(self):
        h = B.limpiar_html(DEL_EDITOR)
        self.assertIn('<p style="text-align:center">', h)
        self.assertIn("font-family:Georgia,'DejaVu Serif',serif", h)
        self.assertIn('font-size:20pt', h)
        self.assertIn('<p style="text-align:justify">', h)
        self.assertIn('<s>tachado</s>', h)
        self.assertIn('<p style="text-align:right">', h)

    def test_lo_demas_se_quita(self):
        h = B.limpiar_html('<p style="text-align:center;position:fixed" onclick="x()">a</p>'
                           '<span style="font-family:Malware;font-size:900pt;background:url(x)">b</span>'
                           '<span style="font-size:14px">c</span><span style="font-size:x-large">d</span>'
                           '<p style="text-align:evil">e</p><span style="text-decoration: line-through">f</span>')
        self.assertIn('<p style="text-align:center">a</p>', h)
        self.assertNotIn('Malware', h); self.assertNotIn('900', h); self.assertNotIn('url', h); self.assertNotIn('onclick', h)
        self.assertIn('font-size:10.5pt', h); self.assertIn('font-size:18pt', h)
        self.assertIn('<p>e</p>', h)
        self.assertIn('text-decoration:line-through', h)
        self.assertEqual(B.fuente('"Times New Roman", serif'), 'Times New Roman')
        self.assertIsNone(B.tamano_pt('3pt'))


class EnPdfYWord(ColegioDePrueba):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.a.modulos_activos = list(cls.a.modulos_activos) + ['salon']
        cls.a.save(update_fields=['modulos_activos'])

    def test_pdf_y_word(self):
        profe = self.cliente(self.u_docente)
        profe.post('/materiales/nuevo/', {'tipo': 'guia', 'titulo': 'Formato'})
        doc = Documento.objects.get()
        c = {'bloques': [{'id': 'x1', 'tipo': 'texto', 'html': DEL_EDITOR}], 'opciones': dict(doc.contenido.get('opciones') or {}, portada=False)}
        self.assertTrue(profe.post(f'/materiales/{doc.pk}/guardar/', json.dumps({'titulo': doc.titulo, 'contenido': c}),
                                   content_type='application/json').json()['ok'])
        r = profe.get(f'/materiales/{doc.pk}/')
        self.assertContains(r, 'data-alinear="justify"'); self.assertContains(r, 'id="mm-fuente"'); self.assertContains(r, 'value="Georgia"')
        self.assertTrue(profe.get(f'/materiales/{doc.pk}/pdf/').content.startswith(b'%PDF'))
        from docx import Document
        from docx.enum.text import WD_ALIGN_PARAGRAPH
        d = Document(io.BytesIO(profe.get(f'/materiales/{doc.pk}/word/').content))
        parrafos = {p.text.strip(): p for p in d.paragraphs if p.text.strip()}
        self.assertEqual(parrafos['Primer párrafo'].alignment, WD_ALIGN_PARAGRAPH.CENTER)
        self.assertEqual(parrafos['Texto justificado tachado'].alignment, WD_ALIGN_PARAGRAPH.JUSTIFY)
        self.assertEqual(parrafos['derecha'].alignment, WD_ALIGN_PARAGRAPH.RIGHT)
        primero = parrafos['Primer párrafo'].runs[0]
        self.assertEqual(primero.font.name, 'Georgia'); self.assertEqual(primero.font.size.pt, 20)
        self.assertTrue(parrafos['Texto justificado tachado'].runs[-1].font.strike)
