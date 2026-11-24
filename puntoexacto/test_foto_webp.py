"""La cámara manda la foto en WebP (pesa ~30 % menos que JPEG): el servidor la lee igual."""
import io

from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image

from .test_camara import UnaSolaIdaAlServidor


class FotoWebP(UnaSolaIdaAlServidor):
    test_calentar_con_get = test_sin_auto_no_guarda_pero_trae_la_nota = test_con_auto_y_todo_claro_queda_guardada = None

    def test_lee_webp_y_pesa_menos(self):
        marcadas = {n: l for n, l in zip(range(1, 9), 'ABCDABCD')}
        jpg = self.foto_llena(marcadas).read()
        im = Image.open(io.BytesIO(jpg)).convert('L')
        b = io.BytesIO(); im.save(b, 'WEBP', quality=80)
        bj = io.BytesIO(); im.save(bj, 'JPEG', quality=80)
        self.assertLess(len(b.getvalue()), len(bj.getvalue()))
        d = self.c.post(self.url('escanear/foto/'), {'foto': SimpleUploadedFile('hoja.jpg', b.getvalue(), 'image/webp')}).json()
        self.assertTrue(d['ok'], d)
        self.assertEqual(d['hoja_id'], self.hoja.id)
        self.assertEqual({int(k): v for k, v in d['respuestas'].items() if v}, marcadas)
        self.assertContains(self.c.get(self.url('escanear/')), 'barras_ancho_pt')
