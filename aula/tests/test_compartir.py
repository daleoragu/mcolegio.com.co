"""Botón «Compartir»: con una de mis clases (toda o algunos estudiantes) o con un colega; colegio y plan individual."""
import json
import shutil
import tempfile

from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from django.test import Client, override_settings

from aula.models import Actividad, Aula, ClaseInvertida, CompartidoDocente, Publicacion
from notas.models import AsignacionDocente, Curso, Docente, Notificacion
from notas.tests.base import CLAVE, ColegioDePrueba

MEDIA = tempfile.mkdtemp(prefix='aula-compartir-')


@override_settings(MEDIA_ROOT=MEDIA)
class CompartirEnElColegio(ColegioDePrueba):

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(MEDIA, ignore_errors=True)

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.a.modulos_activos = list(cls.a.modulos_activos) + ['salon']
        cls.a.save(update_fields=['modulos_activos'])

    def setUp(self):
        self.profe = self.cliente(self.u_docente)
        self.profe.get(f'/aula/asignacion/{self.asig.id}/')
        self.aula1 = Aula.objects.get(asignacion=self.asig)
        curso2 = Curso.objects.create(colegio=self.a, nombre='602', grado=6, subgrupo='2')
        asig2 = AsignacionDocente.objects.create(colegio=self.a, docente=self.docente, materia=self.materia, curso=curso2)
        self.profe.get(f'/aula/asignacion/{asig2.id}/')
        self.aula2 = Aula.objects.get(asignacion=asig2)
        self.act = Actividad(aula=self.aula2, titulo='Juego de fracciones', descripcion='Para repasar')
        self.act.archivo.save('juego.html', ContentFile(b'<html><body>Juego</body></html>'), save=False)
        self.act.nombre_archivo = 'juego.html'
        self.act.save()
        self.u_ana = User.objects.create_user('ana_doc', password=CLAVE, first_name='Ana', last_name='Docente')
        self.ana = Docente.objects.create(colegio=self.a, user=self.u_ana)

    def test_con_otra_clase_para_algunos_estudiantes(self):
        url = f'/aula/compartir/actividad/{self.act.pk}/'
        j = self.profe.get(url).json()
        self.assertEqual([x['id'] for x in j['aulas']], [self.aula1.pk])          # no la misma clase de origen
        self.assertIn('Ana Docente', [x['nombre'] for x in j['colegas']])
        est = self.profe.get(f'/aula/compartir/clase/{self.aula1.pk}/estudiantes/').json()['estudiantes']
        r = self.profe.post(url, {'destino': 'clase', 'aula': self.aula1.pk, 'para_modo': 'algunos', 'para': [est[0]['clave']]}).json()
        self.assertTrue(r['ok'])
        copia = Actividad.objects.get(aula=self.aula1)
        self.assertEqual((copia.titulo, copia.para), ('Juego de fracciones', [est[0]['clave']]))
        with copia.archivo.open('rb') as fh:
            self.assertIn(b'Juego', fh.read())
        # «Algunos» sin escoger a nadie: error
        r = self.profe.post(url, {'destino': 'clase', 'aula': self.aula1.pk, 'para_modo': 'algunos'})
        self.assertEqual(r.status_code, 400)

    def test_con_un_colega_y_compartido_conmigo(self):
        inv = ClaseInvertida.objects.create(aula=self.aula1, titulo='Video de fracciones', video='https://www.youtube.com/watch?v=dQw4w9WgXcQ',
                                            preguntas=[{'texto': '¿1/2 + 1/2?', 'opciones': [{'texto': '1', 'correcta': True}, {'texto': '2'}]}])
        r = self.profe.post(f'/aula/compartir/invertida/{inv.pk}/', {'destino': 'colega', 'usuario': self.u_ana.pk,
                                                                     'mensaje': 'Te sirve para 6.º'}).json()
        self.assertTrue(r['ok'])
        envio = CompartidoDocente.objects.get()
        self.assertTrue(Notificacion.objects.filter(destinatario=self.u_ana, mensaje__contains='Video de fracciones').exists())
        # Ana lo ve y lo agrega a su clase
        curso = Curso.objects.create(colegio=self.a, nombre='603', grado=6, subgrupo='3')
        asig = AsignacionDocente.objects.create(colegio=self.a, docente=self.ana, materia=self.materia, curso=curso)
        ana = self.cliente(self.u_ana)
        ana.get(f'/aula/asignacion/{asig.id}/')
        aula_ana = Aula.objects.get(asignacion=asig)
        r = ana.get('/aula/compartidos/')
        self.assertContains(r, 'Video de fracciones'); self.assertContains(r, 'Te sirve para 6.º')
        ana.post('/aula/compartidos/', {'compartido': envio.pk, 'aula': aula_ana.pk, 'para_modo': 'todos'})
        self.assertEqual(ClaseInvertida.objects.get(aula=aula_ana).preguntas, inv.preguntas)
        envio.refresh_from_db(); self.assertIsNotNone(envio.usado)
        self.assertTrue(Notificacion.objects.filter(destinatario=self.u_docente, mensaje__contains='agregó').exists())
        # No puede agregarlo a una clase que no es suya
        ana.post('/aula/compartidos/', {'compartido': envio.pk, 'aula': self.aula2.pk, 'para_modo': 'todos'})
        self.assertFalse(ClaseInvertida.objects.filter(aula=self.aula2).exists())

    def test_solo_lo_propio_y_publicaciones(self):
        # Ana no puede compartir lo de Pedro
        self.assertEqual(self.cliente(self.u_ana).get(f'/aula/compartir/actividad/{self.act.pk}/').status_code, 404)
        # A un docente de otro colegio no se le comparte
        u_otro = User.objects.create_user('lejos', password=CLAVE)
        Docente.objects.create(colegio=self.b, user=u_otro)
        r = self.profe.post(f'/aula/compartir/actividad/{self.act.pk}/', {'destino': 'colega', 'usuario': u_otro.pk})
        self.assertEqual(r.status_code, 400)
        # Publicación del muro a otra clase (la ve toda la clase)
        pub = Publicacion.objects.create(aula=self.aula1, autor=self.u_docente, texto='Guía de la semana')
        self.profe.post(f'/aula/compartir/publicacion/{pub.pk}/', {'destino': 'clase', 'aula': self.aula2.pk,
                                                                     'para_modo': 'algunos', 'para': ['x']})
        self.assertTrue(Publicacion.objects.filter(aula=self.aula2, texto='Guía de la semana').exists())
        self.assertContains(self.profe.get(f'/aula/{self.aula1.pk}/'), 'btn-compartir')


@override_settings(MEDIA_ROOT=MEDIA)
class CompartirEnElPlanIndividual(ColegioDePrueba):

    def test_taller_html_a_un_grupo_y_a_un_colega(self):
        from chat.models import Colega
        from salon_digital.models import Cuenta, Grupo, Integrante, PaginaPublicada
        u = User.objects.create_user('lina', password=CLAVE, first_name='Lina', last_name='Libre')
        cuenta = Cuenta.objects.create(usuario=u, slug='lina', nombre_publico='Lina Libre', estado='verificada')
        grupo = Grupo.objects.create(propietario=cuenta, nombre='7-01')
        Integrante.objects.create(grupo=grupo, apellidos='Pérez', nombres='Luis')
        c = Client(HTTP_HOST='localhost'); c.force_login(u)
        pagina = PaginaPublicada(propietario=cuenta, titulo='Taller de ecuaciones')
        pagina.archivo.save('taller.html', ContentFile(b'<html><body>Taller</body></html>'), save=False)
        pagina.save()
        j = c.get(f'/aula/compartir/pagina/{pagina.pk}/').json()
        self.assertEqual(len(j['aulas']), 1)                                    # su grupo, aunque no hubiera abierto el aula
        r = c.post(f'/aula/compartir/pagina/{pagina.pk}/', {'destino': 'clase', 'aula': j['aulas'][0]['id'], 'para_modo': 'todos'}).json()
        self.assertTrue(r['ok'])
        act = Actividad.objects.get(aula__grupo=grupo)
        self.assertEqual(act.titulo, 'Taller de ecuaciones')
        # Con un colega (de «Mis colegas»)
        u2 = User.objects.create_user('mario', password=CLAVE, first_name='Mario', last_name='Mate')
        Cuenta.objects.create(usuario=u2, slug='mario', nombre_publico='Mario Mate', estado='verificada')
        self.assertEqual(c.get(f'/aula/compartir/pagina/{pagina.pk}/').json()['colegas'], [])
        Colega.objects.create(de=u, para=u2, estado='aceptada')
        r = c.post(f'/aula/compartir/pagina/{pagina.pk}/', {'destino': 'colega', 'usuario': u2.pk}).json()
        self.assertTrue(r['ok'])
        self.assertTrue(CompartidoDocente.objects.filter(para=u2, tipo='pagina').exists())
        self.assertContains(c.get('/salon_digital/panel/'), 'btn-compartir')
