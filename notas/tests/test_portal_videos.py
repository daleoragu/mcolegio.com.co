"""Videos y fotos por enlace en el portal: se pega el enlace y el portal lo muestra."""
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import SimpleTestCase

from notas.models import Docente, FotoGaleria, VideoPortal
from notas.videos import VideoNoReconocido, analizar, analizar_foto

from .base import ColegioDePrueba
from django.contrib.auth.models import User


class ReconocerEnlaces(SimpleTestCase):

    def test_youtube_en_todas_sus_formas(self):
        for texto in ('https://www.youtube.com/watch?v=dQw4w9WgXcQ&list=x', 'youtu.be/dQw4w9WgXcQ',
                      'https://m.youtube.com/shorts/dQw4w9WgXcQ', 'https://www.youtube.com/live/dQw4w9WgXcQ?si=1',
                      '<iframe width="560" src="https://www.youtube.com/embed/dQw4w9WgXcQ?si=abc" frameborder="0"></iframe>'):
            v = analizar(texto)
            self.assertEqual((v['proveedor'], v['video_id']), ('youtube', 'dQw4w9WgXcQ'), texto)
            self.assertTrue(v['embed'].startswith('https://www.youtube-nocookie.com/embed/dQw4w9WgXcQ'))
        self.assertIn('start=90', analizar('https://youtu.be/dQw4w9WgXcQ?t=1m30s')['embed'])

    def test_vimeo_drive_facebook(self):
        self.assertEqual(analizar('https://vimeo.com/76979871')['embed'], 'https://player.vimeo.com/video/76979871')
        self.assertEqual(analizar('https://drive.google.com/file/d/1AbCdEfGhIjKlMnOp/view?usp=sharing')['embed'],
                         'https://drive.google.com/file/d/1AbCdEfGhIjKlMnOp/preview')
        fb = analizar('https://www.facebook.com/colegio/videos/1234567890/')
        self.assertTrue(fb['embed'].startswith('https://www.facebook.com/plugins/video.php?'))

    def test_lo_que_no_es_video_o_trae_trampa(self):
        for texto in ('', 'https://example.com/video.mp4', '<script>alert(1)</script>',
                      '<iframe src="https://evil.com/x"></iframe>', 'javascript:alert(1)',
                      'https://www.youtube.com/watch?v=<script>'):
            with self.assertRaises(VideoNoReconocido, msg=texto):
                analizar(texto)

    def test_fotos(self):
        d = analizar_foto('https://drive.google.com/file/d/1AbCdEfGhIjKlMnOp/view?usp=drive_link')
        self.assertEqual(d['imagen_externa'], 'https://drive.google.com/thumbnail?id=1AbCdEfGhIjKlMnOp&sz=w1600')
        ig = analizar_foto('https://www.instagram.com/p/C1a2B3c4D5e/?igsh=xyz')
        self.assertEqual(ig['embed'], 'https://www.instagram.com/p/C1a2B3c4D5e/embed/captioned/')
        codigo = ('<blockquote class="instagram-media" data-instgrm-permalink="https://www.instagram.com/reel/C1a2B3c4D5e/'
                  '?utm_source=ig_embed"></blockquote><script async src="//www.instagram.com/embed.js"></script>')
        self.assertEqual(analizar_foto(codigo)['fuente'], 'instagram')
        fb = analizar_foto('https://www.facebook.com/photo/?fbid=123456&set=a.789')
        self.assertTrue(fb['embed'].startswith('https://www.facebook.com/plugins/post.php?'))
        with self.assertRaises(VideoNoReconocido):
            analizar_foto('https://photos.app.goo.gl/abc')
        with self.assertRaises(VideoNoReconocido):
            analizar_foto('https://scontent.cdninstagram.com/v/t51/foto.jpg')


class VideosEnElPortal(ColegioDePrueba):
    URL = '/admin/portal/videos/'

    def test_docente_publica_y_sale_en_el_portal(self):
        c = self.cliente(self.u_docente)
        self.assertContains(c.get(self.URL), 'Agregar video')
        r = c.post(self.URL, {'titulo': 'Izada de bandera', 'destacado': 'on', 'visible': 'on',
                              'enlace': '<iframe src="https://www.youtube.com/embed/dQw4w9WgXcQ" onload="alert(1)"></iframe>'})
        self.assertEqual(r.status_code, 302)
        v = VideoPortal.objects.get()
        self.assertEqual((v.autor, v.proveedor), (self.u_docente, 'youtube'))
        self.assertNotIn('<', v.enlace)                       # nunca se guarda el código pegado
        seccion = self.cliente().get('/ajax/videos/')
        self.assertContains(seccion, 'Izada de bandera')
        self.assertContains(seccion, 'data-embed="https://www.youtube-nocookie.com/embed/dQw4w9WgXcQ?rel=0"')
        self.assertNotContains(seccion, 'onload')
        inicio = self.cliente().get('/').content.decode()
        self.assertIn('data-action="videos"', inicio)
        self.assertIn('Izada de bandera', inicio)

    def test_enlace_malo(self):
        r = self.cliente(self.rectora).post(self.URL, {'titulo': 'X', 'enlace': 'https://example.com/a.mp4', 'visible': 'on'})
        self.assertContains(r, 'YouTube, Vimeo, Google Drive y Facebook')
        self.assertFalse(VideoPortal.objects.exists())

    def test_permisos(self):
        v = VideoPortal.objects.create(colegio=self.a, titulo='Del rector', enlace='x', proveedor='youtube',
                                       video_id='dQw4w9WgXcQ', embed='https://www.youtube-nocookie.com/embed/dQw4w9WgXcQ',
                                       autor=self.rectora)
        # Un docente no edita ni borra el video de otro; el administrador sí.
        c = self.cliente(self.u_docente)
        self.assertEqual(c.get(f'/admin/portal/videos/editar/{v.pk}/').status_code, 403)
        self.assertEqual(c.post(f'/admin/portal/videos/eliminar/{v.pk}/').status_code, 403)
        # Un estudiante, no.
        self.assertIn(self.cliente(self.estudiantes[0].user).get(self.URL).status_code, (302, 403))
        # Un docente de otro colegio tampoco, aunque entre por este subdominio.
        otro = User.objects.create_user('otro', password='x')
        Docente.objects.create(colegio=self.b, user=otro)
        self.assertEqual(self.cliente(otro).get(self.URL).status_code, 403)
        # Video de otro colegio: no existe aquí.
        ajeno = VideoPortal.objects.create(colegio=self.b, titulo='B', enlace='x', proveedor='vimeo', video_id='1',
                                           embed='https://player.vimeo.com/video/1')
        self.assertEqual(self.cliente(self.rectora).post(f'/admin/portal/videos/eliminar/{ajeno.pk}/').status_code, 404)
        self.cliente(self.rectora).post(f'/admin/portal/videos/eliminar/{v.pk}/')
        self.assertFalse(VideoPortal.objects.filter(pk=v.pk).exists())
        self.assertNotContains(self.cliente().get('/ajax/videos/'), 'B</h3>')


class FotosPorEnlace(ColegioDePrueba):
    URL = '/admin/portal/galeria/'

    def test_drive_e_instagram_sin_subir_nada(self):
        c = self.cliente(self.rectora)
        c.post(self.URL, {'titulo': 'Feria', 'enlace': 'https://drive.google.com/file/d/1AbCdEfGhIjKlMnOp/view'})
        c.post(self.URL, {'titulo': 'Día del niño', 'enlace': 'https://www.instagram.com/p/C1a2B3c4D5e/'})
        self.assertEqual(FotoGaleria.objects.filter(colegio=self.a).count(), 2)
        galeria = self.cliente().get('/ajax/galeria-fotos/').content.decode()
        self.assertIn('https://drive.google.com/thumbnail?id=1AbCdEfGhIjKlMnOp', galeria)
        self.assertIn('https://www.instagram.com/p/C1a2B3c4D5e/embed/captioned/', galeria)
        self.assertContains(c.get(self.URL), 'Publicación de Instagram')

    def test_subir_sigue_funcionando_y_no_ambas(self):
        import io
        from PIL import Image
        b = io.BytesIO(); Image.new('RGB', (10, 10), 'red').save(b, 'PNG')
        c = self.cliente(self.rectora)
        c.post(self.URL, {'titulo': 'Subida', 'imagen': SimpleUploadedFile('f.png', b.getvalue(), 'image/png')})
        self.assertEqual(FotoGaleria.objects.get().fuente, 'archivo')
        r = c.post(self.URL, {'titulo': 'Nada'})
        self.assertContains(r, 'Suba la foto o pegue un enlace')
