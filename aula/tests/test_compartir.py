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


@override_settings(MEDIA_ROOT=MEDIA)
class CompartirDesdeLaComunidad(ColegioDePrueba):
    """Lo que otro docente publicó en el muro: a una de mis clases (toda o algunos) o a un colega."""

    def test_actividad_recurso_y_experiencia_del_muro(self):
        from chat.models import Colega, Publicacion as PubMuro
        from materiales.models import Documento
        from salon_digital.models import Cuenta, Grupo, Integrante, PaginaPublicada
        autor = User.objects.create_user('bea', password=CLAVE, first_name='Beatriz', last_name='Bonilla')
        cb = Cuenta.objects.create(usuario=autor, slug='bea', nombre_publico='Beatriz Bonilla', estado='verificada')
        yo = User.objects.create_user('luis', password=CLAVE, first_name='Luis', last_name='Libre')
        cy = Cuenta.objects.create(usuario=yo, slug='luis', nombre_publico='Luis Libre', estado='verificada')
        grupo = Grupo.objects.create(propietario=cy, nombre='6-01')
        sara = Integrante.objects.create(grupo=grupo, apellidos='Gómez', nombres='Sara')
        Integrante.objects.create(grupo=grupo, apellidos='Pérez', nombres='Juan')
        amigo = User.objects.create_user('mario', password=CLAVE, first_name='Mario', last_name='Mate')
        Cuenta.objects.create(usuario=amigo, slug='mario', nombre_publico='Mario Mate', estado='verificada')
        Colega.objects.create(de=yo, para=amigo, estado='aceptada')
        pagina = PaginaPublicada(propietario=cb, titulo='Carrera de fracciones')
        pagina.archivo.save('j.html', ContentFile(b'<html>Juego</html>'), save=False)
        pagina.save()
        act = PubMuro.objects.create(autor=autor, tipo='actividad', titulo='Carrera de fracciones', pagina=pagina)
        doc = Documento.objects.create(propietario=autor, colegio=None, titulo='Guía de límites', tipo='taller',
                                       contenido={'bloques': [{'tipo': 'texto', 'html': '<p>Hola</p>'}]})
        rec = PubMuro.objects.create(autor=autor, tipo='recurso', titulo='Guía de límites', documento=doc)
        exp = PubMuro.objects.create(autor=autor, tipo='experiencia', titulo='Mi feria de ciencias', texto='Así la hice')
        c = Client(HTTP_HOST='localhost'); c.force_login(yo)
        self.assertContains(c.get('/chat/colegas/muro/'), 'data-tipo="muro"')
        j = c.get(f'/aula/compartir/muro/{act.pk}/').json()
        self.assertEqual((j['copiable'], j['para_todos']), (True, False))
        aula = j['aulas'][0]['id']
        clave = c.get(f'/aula/compartir/clase/{aula}/estudiantes/').json()['estudiantes']
        clave_sara = next(e['clave'] for e in clave if 'Sara' in e['nombre'])
        # La actividad, solo para Sara
        self.assertTrue(c.post(f'/aula/compartir/muro/{act.pk}/', {'destino': 'clase', 'aula': aula, 'para_modo': 'algunos',
                                                                   'para': [clave_sara]}).json()['ok'])
        a = Actividad.objects.get(aula_id=aula)
        self.assertEqual((a.titulo, a.para), ('Carrera de fracciones', [clave_sara]))
        self.assertTrue(Notificacion.objects.filter(destinatario=autor, mensaje__contains='llevó su publicación').exists())
        # El recurso, como PDF en Material para toda la clase
        self.assertTrue(c.post(f'/aula/compartir/muro/{rec.pk}/', {'destino': 'clase', 'aula': aula, 'para_modo': 'todos'}).json()['ok'])
        from aula.models import Material
        m = Material.objects.get(aula_id=aula)
        self.assertTrue(m.nombre_archivo.endswith('.pdf')); self.assertIn('Beatriz', m.descripcion)
        # La experiencia, al muro del aula (toda la clase)
        self.assertTrue(c.get(f'/aula/compartir/muro/{exp.pk}/').json()['para_todos'])
        c.post(f'/aula/compartir/muro/{exp.pk}/', {'destino': 'clase', 'aula': aula})
        self.assertTrue(Publicacion.objects.filter(aula_id=aula, texto__contains='Mi feria de ciencias').exists())
        # A un colega: le llega a «Compartido conmigo» y lo agrega a su clase
        self.assertTrue(c.post(f'/aula/compartir/muro/{act.pk}/', {'destino': 'colega', 'usuario': amigo.pk}).json()['ok'])
        envio = CompartidoDocente.objects.get(para=amigo)
        self.assertEqual(envio.tipo, 'muro')
        ca = Client(HTTP_HOST='localhost'); ca.force_login(amigo)
        Grupo.objects.create(propietario=amigo.cuenta_salon, nombre='7-02')
        r = ca.get('/aula/compartidos/')
        self.assertContains(r, 'Carrera de fracciones')
        aula_amigo = Aula.objects.get(grupo__propietario=amigo.cuenta_salon)
        ca.post('/aula/compartidos/', {'compartido': envio.pk, 'aula': aula_amigo.pk, 'para_modo': 'todos'})
        self.assertTrue(Actividad.objects.filter(aula=aula_amigo, titulo='Carrera de fracciones').exists())
