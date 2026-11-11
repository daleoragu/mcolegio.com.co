"""Ecuaciones en los documentos: se guardan como \\( LaTeX \\) y se dibujan en el editor, el PDF, Word y la ficha."""
import io
import json

from django.template import Context, Template
from django.test import SimpleTestCase

from materiales import bloques as B
from materiales import ecuaciones as E
from materiales.models import Documento
from notas.tests.base import ColegioDePrueba


class Dibujo(SimpleTestCase):
    def test_normaliza_lo_del_teclado_y_dibuja(self):
        self.assertEqual(E.normalizar(r'\operatorname{sen}(x)+\text{área}'), r'\mathrm{sen}(x)+\mathrm{área}')
        self.assertEqual(E.normalizar(r'\frac{1}{2}'), r'\dfrac{1}{2}')
        self.assertIn(r'\blacksquare', E.normalizar(r'x^{\placeholder{}}'))
        for tex in (r'x=\frac{-b\pm\sqrt{b^2-4ac}}{2a}', r'\angle ABC=90\degree', r'\sum_{i=1}^{n}i', r'\lim_{x\to0}\frac{\sin x}{x}',
                    r'\mathbb{N}\subset\mathbb{Z}', r'\overline{AB}\parallel\overline{CD}', r'\int_0^1x^2\,dx'):
            self.assertTrue(E.valida(tex), tex)
        self.assertFalse(E.valida(r'\begin{pmatrix}1&2\end{pmatrix}'))          # matrices: no
        self.assertIsNone(E.dibujar(''))

    def test_en_html_y_filtro(self):
        h = E.en_html(r'Halle \(x&lt;\frac{1}{2}\) ya')
        self.assertIn('<img class="mm-eq"', h)
        self.assertIn('alt="x&lt;\\dfrac{1}{2}"', h)
        self.assertTrue(h.startswith('Halle ') and h.endswith(' ya'))
        self.assertIn('<code class="mm-eq-mala">', E.en_html(r'\(\begin{pmatrix}1\end{pmatrix}\)'))
        t = Template('{% load ecuaciones %}{{ a|eq }}|{{ b|safe|eq }}')
        r = t.render(Context({'a': r'<b>\(x^2\)</b>', 'b': r'<p>\(\sqrt{2}\)</p>'}))
        izq, der = r.split('|')
        self.assertTrue(izq.startswith('&lt;b&gt;<img'))                    # lo del usuario se escapa…
        self.assertTrue(der.startswith('<p><img'))                          # …y el HTML ya limpio se respeta
        self.assertEqual(E.partes(r'a \(x\) b'), ['a ', ('eq', 'x'), ' b'])

    def test_el_limpiador_conserva_las_ecuaciones(self):
        limpio = B.limpiar({'bloques': [{'tipo': 'texto', 'html': r'<p>Si \(x<3\) y <script>x</script></p>'},
                                        {'tipo': 'pregunta', 'modo': 'unica', 'enunciado': r'¿\(\frac{1}{2}+\frac{1}{4}\)?',
                                         'opciones': [r'\(\frac{3}{4}\)', '1'], 'correcta': 0}]}, set())
        self.assertIn(r'\(x&lt;3\)', limpio['bloques'][0]['html'])
        self.assertNotIn('script', limpio['bloques'][0]['html'])
        self.assertEqual(limpio['bloques'][1]['enunciado'], r'¿\(\frac{1}{2}+\frac{1}{4}\)?')
        self.assertIn('<img class="mm-eq"', E.en_html(limpio['bloques'][0]['html']))


class EnLosDocumentos(ColegioDePrueba):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.a.modulos_activos = list(cls.a.modulos_activos) + ['salon']
        cls.a.save(update_fields=['modulos_activos'])

    def test_editor_pdf_y_word(self):
        profe = self.cliente(self.u_docente)
        profe.post('/materiales/nuevo/', {'tipo': 'cuadernillo', 'titulo': 'Ecuaciones'})
        doc = Documento.objects.get()
        contenido = {'bloques': [
            {'id': 't1', 'tipo': 'texto', 'html': r'<p>La fórmula es \(x=\frac{-b\pm\sqrt{b^2-4ac}}{2a}\).</p>'},
            {'id': 'p1', 'tipo': 'pregunta', 'modo': 'unica', 'enunciado': r'¿Cuánto es \(\frac{1}{2}+\frac{1}{4}\)?',
             'opciones': [r'\(\frac{3}{4}\)', r'\(\frac{2}{6}\)', '1'], 'correcta': 0},
            {'id': 'tb', 'tipo': 'tabla', 'filas': [['Expresión', 'Valor'], [r'\(\sqrt{16}\)', '4']], 'encabezado': True},
        ]}
        contenido['opciones'] = dict(doc.contenido.get('opciones') or {}, portada=False)
        r = profe.post(f'/materiales/{doc.pk}/guardar/', json.dumps({'titulo': doc.titulo, 'contenido': contenido}),
                       content_type='application/json')
        self.assertTrue(r.json()['ok'])
        # El editor trae el botón, la ventana y el teclado
        r = profe.get(f'/materiales/{doc.pk}/')
        for texto in ('id="mm-ecuacion-btn"', 'id="mm-eq-modal"', 'id="mm-deshacer"', 'id="mm-rehacer"', 'data-porta="paste"',
                      'materiales/ecuaciones.js', '/materiales/ecuacion/'):
            self.assertContains(r, texto)
        # La imagen de una ecuación para el editor
        r = profe.get('/materiales/ecuacion/', {'tex': r'\frac{1}{2}'})
        self.assertEqual(r['Content-Type'], 'image/svg+xml'); self.assertIn(b'<svg', r.content)
        self.assertEqual(profe.get('/materiales/ecuacion/', {'tex': r'\begin{matrix}1\end{matrix}'}).status_code, 422)
        # PDF (sin LaTeX a la vista) y Word (las ecuaciones entran como imágenes)
        self.assertTrue(profe.get(f'/materiales/{doc.pk}/pdf/').content.startswith(b'%PDF'))
        r = profe.get(f'/materiales/{doc.pk}/word/')
        from docx import Document
        w = Document(io.BytesIO(r.content))
        self.assertGreaterEqual(len(w.inline_shapes), 5)                      # fórmula, enunciado, 2 opciones y la celda
        texto = '\n'.join(p.text for p in w.paragraphs)
        self.assertNotIn('\\(', texto); self.assertIn('La fórmula es', texto)
