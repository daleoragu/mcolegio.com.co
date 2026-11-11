"""Imágenes en los documentos: recortar y girar (desde la original) y dónde van (en línea, con el texto alrededor,
detrás o delante del texto, a la izquierda, centrada o a la derecha) en el editor, el PDF, Word y la ficha."""
import io
import json

from django.core.files.base import ContentFile
from django.test import SimpleTestCase

from materiales import bloques as B
from materiales.models import Documento, Imagen
from notas.tests.base import ColegioDePrueba


def foto_png(ancho=400, alto=200):
    from PIL import Image
    b = io.BytesIO()
    im = Image.new('RGB', (ancho, alto), '#bfdbfe')
    im.paste('#dc2626', (0, 0, ancho // 2, alto // 2))          # esquina de arriba a la izquierda en rojo
    im.save(b, 'PNG')
    return b.getvalue()


class Posicion(SimpleTestCase):
    def test_limpia_y_css(self):
        b = B.limpiar({'bloques': [{'tipo': 'imagen', 'imagen': 7, 'ancho': 40, 'ajuste': 'raro', 'alinear': 'arriba'},
                                   {'tipo': 'imagen', 'imagen': 7, 'ajuste': 'detras', 'x': 999, 'y': -999, 'opacidad': 1}]}, {7})['bloques']
        self.assertEqual((b[0]['ajuste'], b[0]['alinear']), ('linea', 'centro'))
        self.assertEqual((b[1]['x'], b[1]['y'], b[1]['opacidad']), (100, -150, 10))
        self.assertEqual(B.css_imagen({'ajuste': 'linea', 'alinear': 'derecha', 'ancho': 50}), ('img-linea', 'text-align:right', 'width:50%'))
        clase, caja, img = B.css_imagen({'ajuste': 'cuadrado', 'alinear': 'derecha', 'ancho': 35})
        self.assertIn('float:right', caja); self.assertIn('width:35%', caja)
        clase, caja, img = B.css_imagen({'ajuste': 'detras', 'x': 10, 'y': 20, 'ancho': 40, 'opacidad': 35}, 180)
        self.assertIn('top:36.0mm', img); self.assertIn('z-index:-1', img); self.assertIn('opacity:0.35', img)
        self.assertIn('top:20cqw', B.css_imagen({'ajuste': 'delante', 'y': 20}, None)[2])


class Recortar(ColegioDePrueba):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.a.modulos_activos = list(cls.a.modulos_activos) + ['salon']
        cls.a.save(update_fields=['modulos_activos'])

    def recortar(self, cliente, pk, **datos):
        return cliente.post(f'/materiales/imagen/{pk}/recortar/', json.dumps(datos), content_type='application/json')

    def test_recortar_girar_restaurar_y_exportar(self):
        from PIL import Image
        profe = self.cliente(self.u_docente)
        orig = Imagen(propietario=self.u_docente, ancho=400, alto=200, peso=10)
        orig.archivo.save('foto.png', ContentFile(foto_png()), save=False)
        orig.save()
        # La mitad izquierda de arriba: queda roja, de 200 × 100
        j = self.recortar(profe, orig.pk, x=0, y=0, w=.5, h=.5).json()
        self.assertTrue(j['ok'])
        nueva = Imagen.objects.get(pk=j['id'])
        self.assertEqual((nueva.ancho, nueva.alto, nueva.recorte['origen']), (200, 100, orig.pk))
        with nueva.archivo.open('rb') as f:
            pixel = Image.open(f).convert('RGB').getpixel((100, 50))
        self.assertTrue(all(abs(a - b) < 6 for a, b in zip(pixel, (220, 38, 38))), pixel)     # (JPEG: casi exacto)
        # Volver a recortar parte de la recortada: se recorta desde la original (no se pierde calidad)
        j2 = self.recortar(profe, nueva.pk, x=.5, y=0, w=.5, h=1, giro=90).json()
        otra = Imagen.objects.get(pk=j2['id'])
        self.assertEqual(otra.recorte['origen'], orig.pk)
        self.assertEqual((otra.ancho, otra.alto), (100, 400))            # girada: 200 × 400, la mitad derecha
        # Restaurar: vuelve la original
        self.assertEqual(self.recortar(profe, otra.pk, restaurar=True).json()['id'], orig.pk)
        # Muy pequeño, o de otro docente: no
        self.assertEqual(self.recortar(profe, orig.pk, x=0, y=0, w=.001, h=.001).status_code, 400)
        self.assertEqual(self.recortar(self.cliente(self.rectora), orig.pk, x=0, y=0, w=.5, h=.5).status_code, 404)
        # En un documento: texto alrededor a la derecha y otra detrás del texto
        profe.post('/materiales/nuevo/', {'tipo': 'cuadernillo', 'titulo': 'Imágenes'})
        doc = Documento.objects.get()
        contenido = {'bloques': [{'id': 'i1', 'tipo': 'imagen', 'imagen': nueva.pk, 'ancho': 35, 'ajuste': 'cuadrado', 'alinear': 'derecha', 'pie': 'Rojo'},
                                 {'id': 't1', 'tipo': 'texto', 'html': '<p>' + 'Texto que rodea la imagen. ' * 30 + '</p>'},
                                 {'id': 'i2', 'tipo': 'imagen', 'imagen': orig.pk, 'ancho': 60, 'ajuste': 'detras', 'x': 20, 'y': 5, 'opacidad': 30}],
                     'opciones': dict(doc.contenido.get('opciones') or {}, portada=False)}
        r = profe.post(f'/materiales/{doc.pk}/guardar/', json.dumps({'titulo': doc.titulo, 'contenido': contenido}), content_type='application/json')
        self.assertTrue(r.json()['ok'])
        r = profe.get(f'/materiales/{doc.pk}/')
        self.assertContains(r, 'id="mm-recorte-modal"'); self.assertContains(r, 'materiales/imagenes.js')
        self.assertIn(nueva.pk, r.context['recortes'])
        from materiales import exportar
        doc.refresh_from_db()
        ctx = exportar.contexto(doc)
        imgs = [b for b in ctx['bloques'] if b['tipo'] == 'imagen']
        self.assertIn('float:right', imgs[0]['css_caja']); self.assertIn('z-index:-1', imgs[1]['css_img'])
        self.assertTrue(profe.get(f'/materiales/{doc.pk}/pdf/').content.startswith(b'%PDF'))
        xml = __import__('docx').Document(io.BytesIO(profe.get(f'/materiales/{doc.pk}/word/').content)).element.xml
        self.assertEqual(xml.count('<wp:anchor'), 2)
        self.assertIn('wrapSquare', xml); self.assertIn('behindDoc="1"', xml); self.assertIn('alphaModFix amt="30000"', xml)
