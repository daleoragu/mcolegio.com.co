"""Muro académico de la comunidad docente (plan individual) y sugerencias de colegas."""
import io
import shutil
import tempfile

from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from PIL import Image

from materiales.models import Documento
from notas.models import Notificacion
from salon_digital.models import Cuenta

from .models import Colega, ComentarioMuro, PerfilColega, Publicacion, ReaccionMuro, SugerenciaDescartada
from .views_muro import grados_de, sugerencias

MEDIA = tempfile.mkdtemp(prefix='muro-')


def foto():
    b = io.BytesIO(); Image.new('RGB', (40, 30), '#3366aa').save(b, 'JPEG')
    return SimpleUploadedFile('foto.jpg', b.getvalue(), content_type='image/jpeg')


@override_settings(MEDIA_ROOT=MEDIA)
class Muro(TestCase):

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(MEDIA, ignore_errors=True)

    def docente(self, nombre, apellido, area='', municipio='', grados='', depto='Tolima'):
        u = User.objects.create_user(nombre.lower(), password='x', first_name=nombre, last_name=apellido)
        Cuenta.objects.create(usuario=u, slug=nombre.lower(), nombre_publico=f'{nombre} {apellido}', estado='verificada',
                              municipio=municipio, departamento=depto)
        PerfilColega.objects.create(usuario=u, area=area, municipio=municipio, grados=grados)
        c = Client(HTTP_HOST='localhost'); c.force_login(u)
        return u, c

    def setUp(self):
        self.luis, self.cl = self.docente('Luis', 'Libre', 'Matemáticas', 'Líbano', '10 y 11')
        self.bea, self.cb = self.docente('Beatriz', 'Bonilla', 'Matemáticas', 'Ibagué', '9.º a 11.º')
        self.carlos, self.cc = self.docente('Carlos', 'Cano', 'Ciencias naturales', 'Líbano', '6')
        self.diana, self.cd = self.docente('Diana', 'Díaz', 'Inglés', 'Neiva', '3', depto='Huila')
        Colega.objects.create(de=self.luis, para=self.bea, estado='aceptada')
        Colega.objects.create(de=self.bea, para=self.diana, estado='aceptada')

    def aceptar(self, c):
        c.post('/chat/colegas/muro/normas/')

    def test_grados(self):
        self.assertEqual(grados_de('6.º a 9.º'), {6, 7, 8, 9})
        self.assertEqual(grados_de('10 y 11'), {10, 11})
        self.assertEqual(grados_de('Transición'), {0})

    def test_sugerencias(self):
        s = {x['t']['u'].pk: x['razones'] for x in sugerencias(self.luis, 10)}
        self.assertNotIn(self.bea.pk, s)                        # ya es colega
        self.assertIn('1 colega en común', s[self.diana.pk])   # amiga de Beatriz
        self.assertIn('De Líbano', s[self.carlos.pk])
        # Desde el muro: «No me interesa» la quita
        self.cl.post('/chat/colegas/muro/descartar/', {'usuario': self.carlos.pk}, HTTP_X_REQUESTED_WITH='fetch')
        self.assertTrue(SugerenciaDescartada.objects.filter(usuario=self.luis, descartado=self.carlos).exists())
        self.assertNotIn(self.carlos.pk, {x['t']['u'].pk for x in sugerencias(self.luis, 10)})
        # Quien bloqueó o ya tiene solicitud no aparece
        Colega.objects.create(de=self.diana, para=self.luis, estado='bloqueada')
        self.assertNotIn(self.diana.pk, {x['t']['u'].pk for x in sugerencias(self.luis, 10)})

    def test_normas_publicar_y_visibilidad(self):
        r = self.cl.get('/chat/colegas/muro/')
        self.assertContains(r, 'Acepto las normas'); self.assertContains(r, 'Colegas sugeridos')
        # Sin aceptar las normas no publica
        self.cl.post('/chat/colegas/muro/', {'tipo': 'experiencia', 'titulo': 'Mi clase con Tangram'})
        self.assertFalse(Publicacion.objects.exists())
        self.aceptar(self.cl)
        self.cl.post('/chat/colegas/muro/', {'tipo': 'experiencia', 'titulo': 'Mi clase con Tangram', 'texto': 'Funcionó muy bien',
                                             'grados': '6.º', 'area': 'Matemáticas'})
        self.cl.post('/chat/colegas/muro/', {'tipo': 'consulta', 'titulo': 'Límites', 'texto': '¿Cómo enseñan límites en 11.º?',
                                             'visibilidad': 'colegas'})
        self.assertEqual(Publicacion.objects.count(), 2)
        # Beatriz (colega) ve las dos; Carlos solo la pública
        self.assertContains(self.cb.get('/chat/colegas/muro/'), 'Límites')
        r = self.cc.get('/chat/colegas/muro/')
        self.assertContains(r, 'Mi clase con Tangram'); self.assertNotContains(r, 'Límites')
        privada = Publicacion.objects.get(titulo='Límites')
        self.assertEqual(self.cc.get(f'/chat/colegas/muro/{privada.pk}/').status_code, 404)
        # Filtros
        self.assertNotContains(self.cb.get('/chat/colegas/muro/?tipo=consulta'), 'Mi clase con Tangram')
        self.assertNotContains(self.cb.get('/chat/colegas/muro/?grado=10'), 'Mi clase con Tangram')
        self.assertContains(self.cb.get('/chat/colegas/muro/?q=tangram'), 'Mi clase con Tangram')
        # Un estudiante o alguien sin plan individual no entra
        otro = User.objects.create_user('nadie', password='x'); co = Client(HTTP_HOST='localhost'); co.force_login(otro)
        self.assertEqual(co.get('/chat/colegas/muro/').status_code, 403)

    def test_imagen_exige_confirmar_sin_estudiantes(self):
        self.aceptar(self.cl)
        self.cl.post('/chat/colegas/muro/', {'tipo': 'experiencia', 'titulo': 'Feria de ciencias', 'imagen': foto()})
        self.assertFalse(Publicacion.objects.exists())
        self.cl.post('/chat/colegas/muro/', {'tipo': 'experiencia', 'titulo': 'Feria de ciencias', 'imagen': foto(), 'sin_estudiantes': 'on'})
        self.assertTrue(Publicacion.objects.get().imagen)

    def test_reacciones_comentarios_y_mejor_respuesta(self):
        self.aceptar(self.cl); self.aceptar(self.cb)
        self.cl.post('/chat/colegas/muro/', {'tipo': 'consulta', 'titulo': 'Derivadas', 'texto': '¿Qué app usan para graficar?'})
        p = Publicacion.objects.get()
        r = self.cb.post(f'/chat/colegas/muro/{p.pk}/reaccion/', {'tipo': 'util'}, HTTP_X_REQUESTED_WITH='fetch').json()
        self.assertEqual((r['activa'], r['n']), (True, 1))
        r = self.cb.post(f'/chat/colegas/muro/{p.pk}/reaccion/', {'tipo': 'util'}, HTTP_X_REQUESTED_WITH='fetch').json()
        self.assertEqual((r['activa'], r['n']), (False, 0))
        self.cb.post(f'/chat/colegas/muro/{p.pk}/reaccion/', {'tipo': 'guardar'}, HTTP_X_REQUESTED_WITH='fetch')
        self.assertContains(self.cb.get('/chat/colegas/muro/?ver=guardados'), 'Derivadas')
        self.cb.post(f'/chat/colegas/muro/{p.pk}/', {'texto': 'GeoGebra, sin duda.'})
        self.assertTrue(Notificacion.objects.filter(destinatario=self.luis, mensaje__contains='comentó').exists())
        c = ComentarioMuro.objects.get()
        self.cb.post(f'/chat/colegas/muro/{p.pk}/accion/', {'accion': 'mejor', 'comentario': c.pk})     # solo el autor
        p.refresh_from_db(); self.assertIsNone(p.mejor_respuesta)
        self.cl.post(f'/chat/colegas/muro/{p.pk}/accion/', {'accion': 'mejor', 'comentario': c.pk})
        p.refresh_from_db(); self.assertEqual(p.mejor_respuesta, c)
        self.assertContains(self.cb.get(f'/chat/colegas/muro/{p.pk}/'), 'Mejor respuesta')
        self.assertTrue(Notificacion.objects.filter(destinatario=self.bea, mensaje__contains='mejor').exists())

    def test_recurso_de_mis_materiales_ver_y_copiar(self):
        self.aceptar(self.cl)
        doc = Documento.objects.create(propietario=self.luis, colegio=None, titulo='Guía de funciones', tipo='taller',
                                       area='Matemáticas', grado='10',
                                       contenido={'bloques': [{'tipo': 'texto', 'html': '<p>Hola</p>'}]})
        self.cl.post('/chat/colegas/muro/', {'tipo': 'recurso', 'titulo': 'Guía de funciones', 'documento': doc.pk})
        p = Publicacion.objects.get()
        self.assertEqual((p.documento, p.area), (doc, 'Matemáticas'))
        self.assertTrue(self.cc.get(f'/chat/colegas/muro/{p.pk}/material/').content.startswith(b'%PDF'))
        r = self.cc.post(f'/chat/colegas/muro/{p.pk}/copiar/')
        copia = Documento.objects.get(propietario=self.carlos)
        self.assertRedirects(r, f'/materiales/{copia.pk}/', fetch_redirect_response=False)
        self.assertIn('Luis Libre', copia.titulo)
        p.refresh_from_db(); self.assertEqual(p.copias, 1)
        # Un documento ajeno no se puede publicar como propio
        ajeno = Documento.objects.create(propietario=self.bea, colegio=None, titulo='De Bea', contenido={})
        self.cl.post('/chat/colegas/muro/', {'tipo': 'recurso', 'titulo': 'Robado', 'documento': ajeno.pk})
        self.assertFalse(Publicacion.objects.filter(titulo='Robado').exists())
        # Perfil: aportes e insignias
        r = self.cc.get(f'/chat/colegas/u/{self.luis.pk}/')
        self.assertContains(r, 'Aportes recientes'); self.assertContains(r, 'copias de sus recursos')

    def test_reportes_ocultan_y_moderacion(self):
        self.aceptar(self.cl)
        self.cl.post('/chat/colegas/muro/', {'tipo': 'lectura', 'titulo': 'Compre mi curso ya'})
        p = Publicacion.objects.get()
        for c in (self.cb, self.cc, self.cd):
            c.post(f'/chat/colegas/muro/{p.pk}/accion/', {'accion': 'reportar', 'motivo': 'publicidad'})
        p.refresh_from_db(); self.assertTrue(p.oculta)
        self.assertNotContains(self.cc.get('/chat/colegas/muro/'), 'Compre mi curso')
        self.assertContains(self.cl.get('/chat/colegas/muro/'), 'Oculta por reportes')
        staff, cs = self.docente('Admin', 'Plataforma')
        staff.is_staff = True; staff.save()
        self.assertContains(cs.get('/chat/colegas/muro/moderar/'), 'Compre mi curso')
        self.assertEqual(self.cc.get('/chat/colegas/muro/moderar/').status_code, 403)
        cs.post('/chat/colegas/muro/moderar/', {'publicacion': p.pk, 'decision': 'eliminar'})
        self.assertFalse(Publicacion.objects.exists())
        self.assertTrue(Notificacion.objects.filter(destinatario=self.luis, mensaje__contains='normas').exists())

    def test_convocatoria_vencida_sale_del_muro(self):
        from datetime import timedelta
        from django.utils import timezone
        self.aceptar(self.cl)
        Publicacion.objects.create(autor=self.luis, tipo='convocatoria', titulo='Congreso viejo',
                                   fecha_limite=timezone.localdate() - timedelta(days=1))
        Publicacion.objects.create(autor=self.luis, tipo='convocatoria', titulo='Olimpiada 2027',
                                   fecha_limite=timezone.localdate() + timedelta(days=10))
        r = self.cb.get('/chat/colegas/muro/')
        self.assertNotContains(r, 'Congreso viejo'); self.assertContains(r, 'Olimpiada 2027'); self.assertContains(r, 'Convocatorias abiertas')
        self.assertContains(self.cl.get('/chat/colegas/muro/?ver=mias'), 'Congreso viejo')


@override_settings(MEDIA_ROOT=MEDIA)
class ActividadesEnElMuro(TestCase):

    def setUp(self):
        from salon_digital.models import PaginaPublicada
        self.luis, self.cl = Muro.docente(self, 'Luis', 'Libre', 'Matemáticas')
        self.bea, self.cb = Muro.docente(self, 'Beatriz', 'Bonilla', 'Matemáticas')
        for c in (self.cl, self.cb):
            c.post('/chat/colegas/muro/normas/')
        self.pagina = PaginaPublicada(propietario=self.luis.cuenta_salon, titulo='Juego de fracciones', descripcion='Para 6.º',
                                      identificacion='grupo')
        html = b"<html><body><script>const ENDPOINT = 'https://otra.cosa/api';</script>Juego</body></html>"
        self.pagina.archivo.save('juego.html', ContentFile(html), save=False)
        self.pagina.save()

    def test_publicar_jugar_en_practica_y_copiar(self):
        from salon_digital.models import PaginaPublicada
        self.cl.post('/chat/colegas/muro/', {'tipo': 'actividad', 'titulo': '', 'pagina': self.pagina.pk})
        p = Publicacion.objects.get()
        self.assertEqual((p.pagina, p.titulo), (self.pagina, 'Juego de fracciones'))
        r = self.cb.get('/chat/colegas/muro/')
        self.assertContains(r, 'Jugar aquí'); self.assertContains(r, 'Pantalla completa'); self.assertContains(r, 'sandbox=')
        # En modo muro: no pide grupo y los intentos van a la práctica (no a los resultados del autor)
        r = self.cb.get(f'{self.pagina.ruta}?muro=1')
        self.assertEqual(r.status_code, 200)
        self.assertIn(b'/salon_digital/api/practica/', r.content)
        self.assertEqual(r['X-Frame-Options'], 'SAMEORIGIN')
        self.assertEqual(Client(HTTP_HOST='localhost').post('/salon_digital/api/practica/', '{}', content_type='application/json').json()['practica'], True)
        # Sin estar en el muro (o sin ser docente) sigue pidiendo identificarse
        self.assertEqual(Client(HTTP_HOST='localhost').get(f'{self.pagina.ruta}?muro=1').status_code, 302)
        # Copiar a mis actividades: queda sin publicar para que la revise
        r = self.cb.post(f'/chat/colegas/muro/{p.pk}/copiar-actividad/')
        copia = PaginaPublicada.objects.get(propietario=self.bea.cuenta_salon)
        self.assertFalse(copia.visible); self.assertIn('Luis Libre', copia.titulo)
        self.assertRedirects(r, f'/salon_digital/panel/{copia.slug}/editar/', fetch_redirect_response=False)
        p.refresh_from_db(); self.assertEqual(p.copias, 1)
        # Una actividad ajena no se puede publicar como propia
        self.cb.post('/chat/colegas/muro/', {'tipo': 'actividad', 'titulo': 'Robada', 'pagina': self.pagina.pk})
        self.assertFalse(Publicacion.objects.filter(titulo='Robada').exists())
