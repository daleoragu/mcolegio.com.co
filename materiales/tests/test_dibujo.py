"""Dibujo a mano alzada en el editor: se guarda como imagen PNG del docente con sus trazos (para volver a editarlo)."""
import base64
import io
import json

from PIL import Image as PILImage

from materiales.models import Documento, Imagen
from notas.tests.base import ColegioDePrueba


def png(ancho=300, alto=200, color=(255, 255, 255)):
    b = io.BytesIO()
    PILImage.new('RGB', (ancho, alto), color).save(b, 'PNG')
    return 'data:image/png;base64,' + base64.b64encode(b.getvalue()).decode()


TRAZOS = [{'h': 'lapiz', 'c': '#2563eb', 'g': 6, 'p': [[10, 10], [40, 30], [80, 20]]},
          {'h': 'texto', 'c': '#dc2626', 'g': 3, 'p': [[50, 60]], 'texto': 'Hola'},
          {'h': 'rect', 'c': '#16a34a', 'g': 3, 'p': [[5, 5], [90, 90]], 'relleno': True}]


class DibujoEnElEditor(ColegioDePrueba):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.a.modulos_activos = list(cls.a.modulos_activos) + ['salon']
        cls.a.save(update_fields=['modulos_activos'])

    def post(self, c, datos):
        return c.post('/materiales/dibujo/guardar/', json.dumps(datos), content_type='application/json')

    def test_guardar_editar_y_usar(self):
        profe = self.cliente(self.u_docente)
        dib = {'trazos': TRAZOS, 'fondo': 'cuadros', 'ancho': 1200, 'alto': 800}
        j = self.post(profe, {'png': png(), 'dibujo': dib}).json()
        self.assertTrue(j['ok'])
        img = Imagen.objects.get(pk=j['id'])
        self.assertEqual(img.propietario, self.u_docente)
        self.assertEqual((img.ancho, img.alto), (300, 200))
        self.assertEqual(img.dibujo['fondo'], 'cuadros')
        self.assertEqual([t['h'] for t in img.dibujo['trazos']], ['lapiz', 'texto', 'rect'])
        self.assertEqual(img.dibujo['trazos'][1]['texto'], 'Hola')
        self.assertTrue(img.dibujo['trazos'][2]['relleno'])
        # Editar: la misma imagen, con los trazos nuevos
        j2 = self.post(profe, {'png': png(400, 300), 'imagen': img.pk, 'dibujo': dict(dib, trazos=TRAZOS[:1])}).json()
        self.assertEqual(j2['id'], img.pk)
        img.refresh_from_db()
        self.assertEqual(len(img.dibujo['trazos']), 1)
        self.assertEqual(img.ancho, 400)
        self.assertEqual(Imagen.objects.count(), 1)
        # Otro docente no la puede sobrescribir: le queda una nueva suya
        j3 = self.post(self.cliente(self.rectora), {'png': png(), 'imagen': img.pk, 'dibujo': dib}).json()
        self.assertNotEqual(j3['id'], img.pk)
        # En el documento: el editor la reconoce como dibujo (para «Editar dibujo») y sale en el PDF
        profe.post('/materiales/nuevo/', {'tipo': 'cuadernillo', 'titulo': 'Dibujos'})
        doc = Documento.objects.get()
        contenido = {'bloques': [{'id': 'd1', 'tipo': 'imagen', 'imagen': img.pk, 'ancho': 70, 'pie': ''}],
                     'opciones': dict(doc.contenido.get('opciones') or {}, portada=False)}
        r = profe.post(f'/materiales/{doc.pk}/guardar/', json.dumps({'titulo': doc.titulo, 'contenido': contenido}), content_type='application/json')
        self.assertTrue(r.json()['ok'])
        r = profe.get(f'/materiales/{doc.pk}/')
        self.assertContains(r, 'materiales/dibujo.js')
        self.assertContains(r, 'data-ins="dibujo"')
        self.assertContains(r, 'data-nuevo="dibujo"')
        self.assertEqual(r.context['dibujos'][img.pk]['trazos'][0]['h'], 'lapiz')
        self.assertTrue(profe.get(f'/materiales/{doc.pk}/pdf/').content.startswith(b'%PDF'))

    def test_dibujar_encima_de_una_imagen(self):
        profe = self.cliente(self.u_docente)
        foto = self.post(profe, {'png': png(), 'dibujo': {'trazos': TRAZOS}}).json()['id']
        j = self.post(profe, {'png': png(), 'dibujo': {'trazos': [], 'base': foto}}).json()
        self.assertTrue(j['ok'])
        self.assertEqual(Imagen.objects.get(pk=j['id']).dibujo['base'], foto)
        # La imagen de fondo tiene que ser del mismo docente
        j = self.post(self.cliente(self.rectora), {'png': png(), 'dibujo': {'trazos': TRAZOS, 'base': foto}}).json()
        self.assertIsNone(Imagen.objects.get(pk=j['id']).dibujo['base'])

    def test_rechaza_lo_que_no_sirve(self):
        profe = self.cliente(self.u_docente)
        self.assertEqual(self.post(profe, {'png': 'hola', 'dibujo': {'trazos': TRAZOS}}).status_code, 400)
        self.assertEqual(self.post(profe, {'png': 'data:image/png;base64,no-es-base64!!', 'dibujo': {'trazos': TRAZOS}}).status_code, 400)
        b = io.BytesIO(); PILImage.new('RGB', (50, 50)).save(b, 'JPEG')
        jpg = 'data:image/png;base64,' + base64.b64encode(b.getvalue()).decode()
        self.assertEqual(self.post(profe, {'png': jpg, 'dibujo': {'trazos': TRAZOS}}).status_code, 400)
        self.assertEqual(self.post(profe, {'png': png(), 'dibujo': {'trazos': []}}).status_code, 400)          # vacío
        # Los trazos se limpian: herramientas raras, colores inválidos y textos largos
        j = self.post(profe, {'png': png(), 'dibujo': {'trazos': [{'h': 'virus', 'p': [[1, 1]]},
                                                                {'h': 'lapiz', 'c': 'red;}', 'g': 999, 'p': [[1, 1], ['x', 2], [3, 4]]},
                                                                {'h': 'texto', 'c': '#000000', 'p': [[1, 1]], 'texto': 'a' * 900}],
                                                     'fondo': '<script>', 'ancho': 99999}}).json()
        d = Imagen.objects.get(pk=j['id']).dibujo
        self.assertEqual([t['h'] for t in d['trazos']], ['lapiz', 'texto'])
        self.assertEqual(d['trazos'][0]['c'], '#111827')
        self.assertEqual(d['trazos'][0]['g'], 60)
        self.assertEqual(len(d['trazos'][1]['texto']), 300)
        self.assertEqual((d['fondo'], d['ancho']), ('blanco', 4000))


class MarcasSobreLaHoja(DibujoEnElEditor):
    test_guardar_editar_y_usar = test_dibujar_encima_de_una_imagen = test_rechaza_lo_que_no_sirve = None

    def test_guardar_limpiar_y_pdf(self):
        from materiales import bloques as B, exportar
        profe = self.cliente(self.u_docente)
        profe.post('/materiales/nuevo/', {'tipo': 'cuadernillo', 'titulo': 'Taller calificado'})
        doc = Documento.objects.get()
        marcas = [{'b': 'p1', 'h': 'lapiz', 'c': '#dc2626', 'g': 4, 'p': [[10, 10, .5], [30, 25, .8], [60, 20, 1]]},
                  {'b': 'p1', 'h': 'sello', 's': 'bien', 'c': '#16a34a', 'g': 4, 'p': [[900, 20]]},
                  {'b': 'p1', 'h': 'texto', 'c': '#dc2626', 'g': 4, 'p': [[800, 60]], 'texto': '4,5 <b>'},
                  {'b': 'otro', 'h': 'lapiz', 'p': [[1, 1]]},                          # bloque que no existe
                  {'b': 'p1', 'h': 'virus', 'p': [[1, 1]]},
                  {'b': 'p1', 'h': 'sello', 's': 'raro', 'p': [[1, 'x'], [2, 2]]}]
        contenido = {'bloques': [{'id': 'p1', 'tipo': 'pregunta', 'modo': 'abierta', 'enunciado': '¿Cuánto es 2+2?'}],
                     'anotaciones': marcas, 'opciones': dict(doc.contenido.get('opciones') or {}, portada=False)}
        r = profe.post(f'/materiales/{doc.pk}/guardar/', json.dumps({'titulo': doc.titulo, 'contenido': contenido}), content_type='application/json')
        self.assertTrue(r.json()['ok'])
        doc.refresh_from_db()
        a = doc.contenido['anotaciones']
        self.assertEqual([x['h'] for x in a], ['lapiz', 'sello', 'texto', 'sello'])
        self.assertEqual(a[0]['p'][2], [60.0, 20.0, 1.0])                          # la presión del lápiz se guarda
        self.assertEqual(a[3]['s'], 'bien'); self.assertEqual(a[3]['p'], [[2.0, 2.0]])
        # En el PDF: una imagen SVG encima del bloque (y nada si el docente las apaga)
        ctx = exportar.contexto(doc)
        anot = ctx['bloques'][0]['anot']
        self.assertTrue(anot['src'].startswith('data:image/svg+xml;base64,'))
        svg = base64.b64decode(anot['src'].split(',')[1]).decode()
        self.assertIn('4,5 &lt;b&gt;', svg); self.assertIn('#16a34a', svg)
        self.assertTrue(profe.get(f'/materiales/{doc.pk}/pdf/').content.startswith(b'%PDF'))
        doc.contenido['opciones']['marcas_pdf'] = False
        doc.save()
        self.assertNotIn('anot', exportar.contexto(doc)['bloques'][0])
        # El editor trae el botón y el script
        r = profe.get(f'/materiales/{doc.pk}/')
        self.assertContains(r, 'id="mm-anotar-btn"'); self.assertContains(r, 'materiales/anotar.js')
        # La hoja para marcar: el mismo HTML del PDF, con cada bloque marcado por su id y el script
        r = profe.get(f'/materiales/{doc.pk}/marcar/')
        self.assertContains(r, 'data-bid="p1"'); self.assertContains(r, 'materiales/marcar.js'); self.assertContains(r, 'class="marcar"')
        self.assertNotContains(r, 'class="anot"')
        self.assertEqual(self.cliente(self.rectora).get(f'/materiales/{doc.pk}/marcar/').status_code, 404)
        self.assertEqual(B.limpiar_anotaciones('nada', {'p1'}), [])
