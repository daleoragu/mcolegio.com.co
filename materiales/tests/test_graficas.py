"""Graficador: fórmulas como en el cuaderno (y seguras), dibujo, imagen editable y su uso en PDF y Word."""
import io
import json

from django.test import SimpleTestCase

from materiales import graficas as G
from materiales.models import Documento, Imagen
from notas.tests.base import ColegioDePrueba


class Formulas(SimpleTestCase):
    def test_como_en_el_cuaderno(self):
        casos = {'2x^2-3x+1': '2*x**2-3*x+1', 'sen x': 'sen(x)', '3(x+1)(x-2)': '3*(x+1)*(x-2)', '√(x+4)': 'sqrt(x+4)',
                 '|x-2|': 'abs(x-2)', '2pi x': '2*pi*x', '2,5x': '2.5*x', 'y = x^2': 'x**2', 'f(x)=2x': '2*x'}
        for entrada, salida in casos.items():
            self.assertEqual(G._preparar(entrada), salida, entrada)
        import numpy as np
        self.assertAlmostEqual(float(G.evaluar(G.compilar('2x^2-3x+1'), np.array([2.0]))[0]), 3.0)
        self.assertAlmostEqual(G.numero('pi/2'), 1.5708, places=4)
        self.assertEqual(G.numero('2,5'), 2.5)

    def test_nada_peligroso(self):
        for mala in ('__import__("os")', 'x.real', 'lambda: 1', 'open("x")', '[1,2]', 'x if x else 1', 'eval("1")', 'sen(x, 2)', 'foo(x)'):
            with self.assertRaises(ValueError, msg=mala):
                G.compilar(mala)
        self.assertEqual(G.numero('9^9^9^9'), 0.0)                     # se desborda sin colgar el servidor
        with self.assertRaises(ValueError):
            G.compilar('2x', variable=False)

    def test_limpiar_y_dibujar(self):
        s = G.limpiar({'x': [5, -5], 'y': ['-pi', 'pi'], 'elementos': [{'t': 'funcion', 'expr': 'x^2'}, {'t': 'virus'}, {'t': 'poligono', 'puntos': [[0, 0]]},
                                                                      {'t': 'texto', 'x': 0, 'y': 0, 'texto': ''}] + [{'t': 'punto', 'x': 1, 'y': 1}] * 40})
        self.assertEqual(s['x'], [-6.0, 6.0])                            # rango al revés: el de siempre
        self.assertAlmostEqual(s['y'][1], 3.1416, places=3)
        self.assertEqual(s['elementos'][0]['t'], 'funcion')
        self.assertEqual(len(s['elementos']), 27)                        # se miran los primeros 30; los inválidos se descartan
        png, caja, errores = G.dibujar({'elementos': [{'t': 'funcion', 'expr': 'tan(x)'}, {'t': 'funcion', 'expr': 'foo(x)'},
                                                      {'t': 'area', 'expr': 'x^2', 'desde': '0', 'hasta': '1'}, {'t': 'circulo', 'cx': 0, 'cy': 0, 'r': 2},
                                                      {'t': 'vector', 'a': [0, 0], 'b': [2, 1]}, {'t': 'vertical', 'x': '1'}]}, 'png')
        self.assertTrue(png.startswith(b'\x89PNG'))
        self.assertEqual(list(errores), [1])
        self.assertTrue(0 < caja[0] < caja[2] < 1 and 0 < caja[1] < caja[3] < 1)
        _, _, errores = G.dibujar({'pi': True, 'x': ['-2pi', '2pi'], 'elementos': [{'t': 'funcion', 'expr': 'sen x'}]}, 'svg')
        self.assertEqual(errores, {})


class EnElEditor(ColegioDePrueba):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.a.modulos_activos = list(cls.a.modulos_activos) + ['salon']
        cls.a.save(update_fields=['modulos_activos'])

    def post(self, c, url, datos):
        return c.post(url, json.dumps(datos), content_type='application/json')

    def test_insertar_editar_y_exportar(self):
        profe = self.cliente(self.u_docente)
        spec = {'x': [-5, 5], 'y': [-3, 7], 'elementos': [{'t': 'funcion', 'expr': 'x^2 - 2x - 1', 'nombre': 'f'}, {'t': 'punto', 'x': 1, 'y': -2, 'nombre': 'V'}]}
        j = self.post(profe, '/materiales/grafica/vista/', {'grafica': spec}).json()
        self.assertIn('<svg', j['svg']); self.assertEqual(j['errores'], {}); self.assertEqual(len(j['caja']), 4)
        self.assertEqual(self.post(profe, '/materiales/grafica/guardar/', {'grafica': {'elementos': []}}).status_code, 400)
        j = self.post(profe, '/materiales/grafica/guardar/', {'grafica': spec}).json()
        img = Imagen.objects.get(pk=j['id'])
        self.assertEqual(img.grafica['elementos'][0]['expr'], 'x^2 - 2x - 1')
        self.assertGreater(img.peso, 0); self.assertGreater(img.ancho, 500)
        # Editar: la misma imagen (no se duplica) con la gráfica nueva
        spec['elementos'][0]['expr'] = '-x^2 + 4'
        j2 = self.post(profe, '/materiales/grafica/guardar/', {'grafica': spec, 'imagen': img.pk}).json()
        self.assertEqual(j2['id'], img.pk)
        img.refresh_from_db()
        self.assertEqual(img.grafica['elementos'][0]['expr'], '-x^2 + 4')
        self.assertEqual(Imagen.objects.count(), 1)
        # Otro docente no puede sobrescribirla: le queda una imagen nueva suya
        otra = self.cliente(self.rectora)
        j3 = self.post(otra, '/materiales/grafica/guardar/', {'grafica': spec, 'imagen': img.pk}).json()
        self.assertNotEqual(j3['id'], img.pk)
        # En un documento: el editor la reconoce como gráfica; sale en el PDF y en Word
        profe.post('/materiales/nuevo/', {'tipo': 'cuadernillo', 'titulo': 'Funciones'})
        doc = Documento.objects.get()
        contenido = {'bloques': [{'id': 'g1', 'tipo': 'imagen', 'imagen': img.pk, 'ancho': 70, 'pie': 'Parábola'},
                                 {'id': 'p1', 'tipo': 'pregunta', 'modo': 'unica', 'enunciado': '¿Vértice?', 'opciones': ['(0,4)', '(1,2)'],
                                  'correcta': 0, 'imagen': img.pk}],
                     'opciones': dict(doc.contenido.get('opciones') or {}, portada=False)}
        self.assertTrue(self.post(profe, f'/materiales/{doc.pk}/guardar/', {'titulo': doc.titulo, 'contenido': contenido}).json()['ok'])
        r = profe.get(f'/materiales/{doc.pk}/')
        self.assertContains(r, 'id="mm-graf-modal"'); self.assertContains(r, 'materiales/graficador.js')
        self.assertEqual(r.context['graficas'][img.pk]['elementos'][0]['expr'], '-x^2 + 4')
        self.assertTrue(profe.get(f'/materiales/{doc.pk}/pdf/').content.startswith(b'%PDF'))
        from docx import Document
        self.assertGreaterEqual(len(Document(io.BytesIO(profe.get(f'/materiales/{doc.pk}/word/').content)).inline_shapes), 2)
