"""Fase 3: señalar en la imagen, respuestas con foto o audio, hojas sobre un PDF y banco de preguntas."""
import io
import json
import shutil
import tempfile
from decimal import Decimal

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.http import QueryDict
from django.test import SimpleTestCase, override_settings

from aula.models import ArchivoFicha, Aula, Entrega, Tarea
from materiales import bloques as B
from materiales import calificar as C
from materiales import exportar as X
from materiales.models import Documento, Imagen, PreguntaBanco
from notas.models import Docente
from notas.tests.base import ColegioDePrueba

MEDIA = tempfile.mkdtemp(prefix='materiales-f3-')


def png(ancho=400, alto=500):
    from PIL import Image
    salida = io.BytesIO()
    Image.new('RGB', (ancho, alto), (240, 240, 240)).save(salida, format='PNG')
    return SimpleUploadedFile('pagina.png', salida.getvalue(), content_type='image/png')


def hoja(img):
    return {'id': 'h1', 'tipo': 'pregunta', 'modo': 'hoja', 'imagen': img, 'campos': [
        {'id': 'c1', 'tipo': 'texto', 'x': 10, 'y': 10, 'w': 30, 'h': 4, 'correcta': 'Bogotá|Bogota', 'puntos': 1},
        {'id': 'c2', 'tipo': 'marca', 'x': 10, 'y': 20, 'w': 3, 'h': 3, 'correcta': True, 'puntos': 1},
        {'id': 'c3', 'tipo': 'marca', 'x': 20, 'y': 20, 'w': 3, 'h': 3, 'correcta': False, 'puntos': 1},
        {'id': 'c4', 'tipo': 'lista', 'x': 10, 'y': 30, 'w': 20, 'h': 4, 'opciones': ['is', 'are', 'am'], 'correcta': 1,
         'puntos': 2},
    ]}


def senalar(img):
    return {'id': 's1', 'tipo': 'pregunta', 'modo': 'senalar', 'enunciado': 'Señala los dos ríos', 'imagen': img,
            'puntos': 2, 'zonas': [{'x': 10, 'y': 10, 'w': 20, 'h': 20}, {'x': 60, 'y': 60, 'w': 20, 'h': 20}]}


class TiposNuevos(SimpleTestCase):

    def test_limpiar(self):
        c = B.limpiar({'bloques': [
            hoja(7), senalar(7),
            {'id': 'f1', 'tipo': 'pregunta', 'modo': 'archivo', 'enunciado': 'Foto', 'archivo': 'raro'},
            {'id': 'z', 'tipo': 'pregunta', 'modo': 'senalar', 'imagen': 7,
             'zonas': [{'x': 95, 'y': 95, 'w': 50, 'h': 50}, {'x': 'nan', 'y': 1, 'w': 1, 'h': 1}, {'x': 1, 'y': 1, 'w': 0.1, 'h': 9}]},
        ]}, {7})
        h, s, f, z = c['bloques']
        self.assertEqual(h['puntos'], 4)                     # 1 + 1 + 2 (la casilla que no va no suma)
        self.assertEqual([x['tipo'] for x in h['campos']], ['texto', 'marca', 'marca', 'lista'])
        self.assertEqual(len(s['zonas']), 2)
        self.assertEqual(f['archivo'], 'foto')
        self.assertEqual(z['zonas'], [{'x': 95.0, 'y': 95.0, 'w': 5.0, 'h': 5.0}])   # recortada al borde

    def test_calificar(self):
        c = B.limpiar({'bloques': [hoja(7), senalar(7),
                                   {'id': 'f1', 'tipo': 'pregunta', 'modo': 'archivo', 'puntos': 2}]}, {7})
        r = C.calificar(c, {'h1': {'c1': 'bogota', 'c2': True, 'c3': False, 'c4': 1},
                            's1': [[15, 15], [70, 70]], 'f1': 12})
        d = r['detalle']
        self.assertEqual((d['h1']['obtenidos'], d['h1']['posibles']), (Decimal(4), Decimal(4)))
        self.assertEqual(d['s1']['obtenidos'], Decimal(2))
        self.assertEqual(r['pendientes'], ['f1'])
        # Marcar la casilla que no va resta; tocar fuera de las zonas también
        r = C.calificar(c, {'h1': {'c1': 'Medellín', 'c2': True, 'c3': True, 'c4': 0}, 's1': [[15, 15], [50, 5]], 'f1': None})
        self.assertEqual(r['detalle']['h1']['obtenidos'], Decimal(0))
        self.assertEqual(r['detalle']['s1']['obtenidos'], Decimal(0))
        self.assertEqual(r['pendientes'], [])

    def test_leer_formulario(self):
        c = B.limpiar({'bloques': [hoja(7), senalar(7)]}, {7})
        post = QueryDict(mutable=True)
        post.update({'r-h1-c1': ' Bogotá ', 'r-h1-c2': '1', 'r-h1-c4': '1', 'r-s1': '15.5,15;70,70;basura;200,5'})
        r = C.leer_respuestas(c, post)
        self.assertEqual(r['h1'], {'c1': 'Bogotá', 'c2': True, 'c3': False, 'c4': 1})
        self.assertEqual(r['s1'], [[15.5, 15.0], [70.0, 70.0]])

    def test_numeracion_sin_hojas(self):
        c = B.limpiar({'bloques': [hoja(7), senalar(7)]}, {7})
        bloques, total = X._numerar(c['bloques'])
        self.assertEqual((total, bloques[0].get('numero'), bloques[1]['numero']), (1, None, 1))


@override_settings(MEDIA_ROOT=MEDIA)
class FichaConArchivosYHoja(ColegioDePrueba):

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(MEDIA, ignore_errors=True)

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.a.modulos_activos = list(cls.a.modulos_activos) + ['salon']
        cls.a.save(update_fields=['modulos_activos'])

    def test_hoja_pdf_senalar_foto_y_audio(self):
        ana, beto = self.estudiantes[0], self.estudiantes[1]
        profe = self.cliente(self.u_docente)
        profe.get(f'/aula/asignacion/{self.asig.id}/')
        aula = Aula.objects.get(asignacion=self.asig)
        profe.post('/materiales/nuevo/', {'tipo': 'ficha_pdf', 'titulo': 'Ficha de inglés'})
        doc = Documento.objects.get()
        self.assertEqual(doc.tipo, 'ficha_pdf')
        profe.post('/materiales/imagen/', {'imagen': png()})
        img = Imagen.objects.get().pk
        contenido = {'bloques': [hoja(img), senalar(img),
                                 {'id': 'f1', 'tipo': 'pregunta', 'modo': 'archivo', 'enunciado': 'Foto del cuaderno', 'archivo': 'foto'},
                                 {'id': 'a1', 'tipo': 'pregunta', 'modo': 'archivo', 'enunciado': 'Lee en voz alta', 'archivo': 'audio'}]}
        profe.post(f'/materiales/{doc.pk}/guardar/', json.dumps({'titulo': doc.titulo, 'contenido': contenido}),
                   content_type='application/json')
        # PDF y Word, también la versión con respuestas
        for url in ('pdf/', 'pdf/?respuestas=1', 'word/', 'word/?respuestas=1'):
            r = profe.get(f'/materiales/{doc.pk}/{url}')
            self.assertEqual(r.status_code, 200, url)
        self.assertTrue(profe.get(f'/materiales/{doc.pk}/pdf/?respuestas=1').content.startswith(b'%PDF'))

        profe.post(f'/materiales/{doc.pk}/accion/', {'accion': 'ficha', 'aula': aula.pk, 'modo': 'puntos', 'intentos': '1',
                                                     'tiempo': '0', 'mostrar': 'al_terminar'})
        t = Tarea.objects.get(aula=aula)
        profe.post(f'/aula/{aula.pk}/tareas/{t.pk}/editar/', {'titulo': t.titulo, 'publicada': 'on', 'periodo': self.p1.pk,
                                                             'componente': 'SABER'})
        est = self.cliente(ana.user)
        r = est.get(f'/aula/{aula.pk}/tareas/{t.pk}/ficha/')
        self.assertContains(r, 'name="r-h1-c1"')
        self.assertContains(r, 'enctype="multipart/form-data"')
        self.assertContains(r, 'fi-senalar')
        self.assertNotContains(r, 'class="fi-zona"')         # las zonas no se ven antes de enviar
        audio = SimpleUploadedFile('voz.webm', b'\x1aE\xdf\xa3audio de prueba', content_type='audio/webm')
        est.post(f'/aula/{aula.pk}/tareas/{t.pk}/ficha/', {
            'r-h1-c1': 'bogota', 'r-h1-c2': '1', 'r-h1-c3': '1', 'r-h1-c4': '1',
            'r-s1': '15,15;70,70', 'r-f1': png(1200, 900), 'r-a1': audio})
        e = Entrega.objects.get(tarea=t, estudiante=ana)
        self.assertEqual((e.nota, e.estado), (None, 'entregada'))       # foto y audio por revisar
        foto, voz = ArchivoFicha.objects.get(tipo='foto'), ArchivoFicha.objects.get(tipo='audio')
        self.assertEqual((e.respuestas['f1'], e.respuestas['a1']), (foto.pk, voz.pk))
        self.assertTrue(voz.archivo.name.endswith('.webm'))
        url_foto = f'/aula/{aula.pk}/tareas/{t.pk}/ficha/archivo/{foto.pk}/'
        self.assertEqual(est.get(url_foto).status_code, 302)
        self.assertEqual(self.cliente(beto.user).get(url_foto).status_code, 403)
        r = est.get(f'/aula/{aula.pk}/tareas/{t.pk}/ficha/')
        self.assertContains(r, 'class="fi-zona"')
        self.assertContains(r, url_foto)

        # El docente oye el audio, ve la foto y pone los puntos: 3 (hoja, una casilla de más) + 2 + 1 + 0,5 = 6,5 de 8
        r = profe.get(f'/aula/{aula.pk}/tareas/{t.pk}/ficha/e{ana.id}/revisar/')
        self.assertContains(r, '<audio')
        profe.post(f'/aula/{aula.pk}/tareas/{t.pk}/ficha/e{ana.id}/revisar/', {'p-f1': '1', 'p-a1': '0,5'})
        e.refresh_from_db()
        self.assertEqual((e.estado, e.nota), ('calificada', Decimal('4.3')))

    def test_archivo_del_tipo_equivocado(self):
        ana = self.estudiantes[0]
        profe = self.cliente(self.u_docente)
        profe.get(f'/aula/asignacion/{self.asig.id}/')
        aula = Aula.objects.get(asignacion=self.asig)
        t = Tarea.objects.create(aula=aula, titulo='Solo foto', publicada=True, ficha={'bloques': [
            {'id': 'f1', 'tipo': 'pregunta', 'modo': 'archivo', 'enunciado': 'Foto', 'archivo': 'foto', 'puntos': 1,
             'control': False, 'lineas': 0, 'imagen': None}]}, ficha_config={'intentos': 1})
        est = self.cliente(ana.user)
        est.post(f'/aula/{aula.pk}/tareas/{t.pk}/ficha/', {
            'r-f1': SimpleUploadedFile('v.webm', b'xx', content_type='audio/webm')})
        e = Entrega.objects.get(tarea=t, estudiante=ana)
        self.assertIsNone(e.respuestas['f1'])
        self.assertFalse(ArchivoFicha.objects.exists())


@override_settings(MEDIA_ROOT=MEDIA)
class BancoDePreguntas(ColegioDePrueba):

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.a.modulos_activos = list(cls.a.modulos_activos) + ['salon']
        cls.a.save(update_fields=['modulos_activos'])
        cls.u_otro = User.objects.create_user('otra', password='x', first_name='Olga', last_name='Otra')
        Docente.objects.create(colegio=cls.a, user=cls.u_otro)

    def _post(self, cliente, url, datos):
        return cliente.post(url, json.dumps(datos), content_type='application/json').json()

    def test_guardar_buscar_compartir_y_usar(self):
        profe = self.cliente(self.u_docente)
        profe.post('/materiales/imagen/', {'imagen': png()})
        img = Imagen.objects.get()
        pregunta = {'id': 'p1', 'tipo': 'pregunta', 'modo': 'unica', 'enunciado': '¿Cuál fracción es mayor?',
                    'opciones': ['1/2', '1/3'], 'correcta': 0, 'imagen': img.pk}
        j = self._post(profe, '/materiales/banco/guardar/', {'bloque': pregunta, 'area': 'Matemáticas', 'grado': '4',
                                                            'tema': 'fracciones', 'compartida': False})
        self.assertTrue(j['ok'])
        j = self._post(profe, '/materiales/banco/guardar/', {'bloque': pregunta, 'tema': 'fracciones'})
        self.assertIn('ya estaba', j['mensaje'])
        self.assertEqual(PreguntaBanco.objects.count(), 1)
        p = PreguntaBanco.objects.get()
        self.assertEqual(profe.get('/materiales/banco/buscar/?q=fraccion').json()['preguntas'][0]['id'], p.pk)
        self.assertEqual(profe.get('/materiales/banco/buscar/?q=célula').json()['preguntas'], [])
        self.assertContains(profe.get('/materiales/banco/'), '¿Cuál fracción es mayor?')

        # La otra docente no la ve hasta que se comparte
        otra = self.cliente(self.u_otro)
        self.assertEqual(otra.get('/materiales/banco/buscar/').json()['preguntas'], [])
        r = otra.post('/materiales/banco/usar/', json.dumps({'id': p.pk}), content_type='application/json')
        self.assertEqual(r.status_code, 404)
        profe.post(f'/materiales/banco/{p.pk}/', {'accion': 'compartir'})
        self.assertEqual(len(otra.get('/materiales/banco/buscar/').json()['preguntas']), 1)
        # Al usarla, la imagen se copia a su nube; no puede borrar la pregunta ajena
        j = self._post(otra, '/materiales/banco/usar/', {'id': p.pk})
        self.assertTrue(j['ok'])
        nueva = Imagen.objects.get(propietario=self.u_otro)
        self.assertEqual(j['bloque']['imagen'], nueva.pk)
        self.assertNotEqual(j['bloque']['id'], 'p1')
        self.assertEqual(otra.post(f'/materiales/banco/{p.pk}/', {'accion': 'eliminar'}).status_code, 404)

        # Guardar todas las preguntas de un documento (las hojas no van)
        profe.post('/materiales/nuevo/', {'tipo': 'taller', 'titulo': 'Taller', 'area': 'Ciencias'})
        doc = Documento.objects.get()
        doc.contenido = {'bloques': [
            {'id': 'a', 'tipo': 'pregunta', 'modo': 'vf', 'enunciado': 'La célula es la unidad de la vida', 'valor': True},
            {'id': 'b', 'tipo': 'pregunta', 'modo': 'abierta', 'enunciado': 'Explica la fotosíntesis'},
            {'id': 'c', 'tipo': 'pregunta', 'modo': 'hoja', 'imagen': img.pk, 'campos': []},
            {'id': 'd', 'tipo': 'texto', 'html': '<p>hola</p>'}]}
        doc.save()
        j = self._post(profe, '/materiales/banco/guardar/', {'documento': doc.pk, 'tema': 'célula'})
        self.assertIn('2 preguntas', j['mensaje'])
        self.assertEqual(PreguntaBanco.objects.filter(area='Ciencias').count(), 2)
        # Un estudiante no entra al banco
        self.assertEqual(self.cliente(self.estudiantes[0].user).get('/materiales/banco/').status_code, 403)
