"""Fase 2: tipos de pregunta, cuadernillo con PuntoExacto y fichas que se resuelven en el aula."""
import io
import json
import shutil
import tempfile
from decimal import Decimal

from django.test import SimpleTestCase, override_settings

from aula.models import Aula, Entrega, Tarea
from materiales import bloques as B
from materiales import calificar as C
from materiales.models import Documento, Imagen
from notas.models import NotaDetallada
from notas.tests.base import ColegioDePrueba

MEDIA = tempfile.mkdtemp(prefix='materiales-f2-')


def png():
    from PIL import Image
    from django.core.files.uploadedfile import SimpleUploadedFile
    salida = io.BytesIO()
    Image.new('RGB', (300, 200), (10, 120, 200)).save(salida, format='PNG')
    return SimpleUploadedFile('g.png', salida.getvalue(), content_type='image/png')


FICHA = {'bloques': [
    {'id': 'u', 'tipo': 'pregunta', 'modo': 'unica', 'enunciado': '¿2+2?', 'opciones': ['3', '4', '5'], 'correcta': 1},
    {'id': 'v', 'tipo': 'pregunta', 'modo': 'varias', 'enunciado': 'Pares', 'opciones': ['2', '3', '4', '5'], 'correctas': [0, 2]},
    {'id': 'f', 'tipo': 'pregunta', 'modo': 'vf', 'enunciado': 'El sol es una estrella', 'valor': True},
    {'id': 'c', 'tipo': 'pregunta', 'modo': 'completar', 'texto': 'La capital es [[Bogotá|Bogota]] y el río [[Magdalena]].', 'puntos': 2},
    {'id': 'n', 'tipo': 'pregunta', 'modo': 'numerica', 'enunciado': '1/2 en decimal', 'respuesta': '0,5', 'tolerancia': '0.01'},
    {'id': 'k', 'tipo': 'pregunta', 'modo': 'corta', 'enunciado': 'Proceso de las plantas', 'aceptadas': ['fotosíntesis']},
    {'id': 'e', 'tipo': 'pregunta', 'modo': 'emparejar', 'enunciado': 'Une', 'pares': [['perro', 'ladra'], ['gato', 'maúlla']]},
    {'id': 'o', 'tipo': 'pregunta', 'modo': 'ordenar', 'enunciado': 'Ordena', 'elementos': ['uno', 'dos', 'tres']},
    {'id': 's', 'tipo': 'pregunta', 'modo': 'clasificar', 'enunciado': 'Clasifica',
     'grupos': [{'nombre': 'Frutas', 'elementos': ['mango']}, {'nombre': 'Verduras', 'elementos': ['zanahoria']}]},
    {'id': 'a', 'tipo': 'pregunta', 'modo': 'abierta', 'enunciado': 'Explica', 'puntos': 3},
]}


class Calificacion(SimpleTestCase):

    def test_cada_tipo(self):
        ficha = B.limpiar(FICHA, set())
        todo_bien = {'u': 1, 'v': [0, 2], 'f': True, 'c': ['bogota', 'Magdalena'], 'n': '0.505', 'k': 'Fotosintesis',
                     'e': {'0': '0', '1': '1'}, 'o': [0, 1, 2], 's': {'0': '0', '1': '1'}, 'a': 'Porque sí'}
        r = C.calificar(ficha, todo_bien)
        self.assertEqual(r['posibles'], Decimal(13))
        self.assertEqual(r['obtenidos'], Decimal(10))           # todo menos la abierta (3 puntos)
        self.assertEqual(r['pendientes'], ['a'])
        mal = {'u': 0, 'v': [0, 1], 'f': False, 'c': ['Medellín', 'magdalena'], 'n': '0.6', 'k': 'respiración',
               'e': {'0': '1', '1': '0'}, 'o': [0, 2, 1], 's': {'0': '1'}, 'a': ''}
        r = C.calificar(ficha, mal)
        d = r['detalle']
        self.assertEqual(d['v']['obtenidos'], Decimal(0))       # una bien y una mal se anulan
        self.assertEqual(d['c']['obtenidos'], Decimal('1.00'))   # la mitad de 2 puntos
        self.assertEqual(d['o']['obtenidos'], Decimal('0.33'))
        self.assertTrue(d['k']['revisar'])
        self.assertFalse(d['a']['revisar'])                      # en blanco: 0, nada que revisar
        # El docente pone puntos a mano
        r = C.calificar(ficha, todo_bien, {'a': '2'})
        self.assertEqual((r['obtenidos'], r['pendientes']), (Decimal(12), []))
        self.assertEqual(C.a_la_escala(Decimal(12), Decimal(13), Decimal(1), Decimal(5)), Decimal('4.7'))
        # Con tildes y mayúsculas exigidas
        estricta = B.limpiar({'bloques': [{'id': 'x', 'tipo': 'pregunta', 'modo': 'completar', 'texto': '[[Bogotá]]', 'mayusculas': True}]}, set())
        self.assertEqual(C.calificar(estricta, {'x': ['bogota']})['obtenidos'], 0)

    def test_respuesta_correcta_en_palabras(self):
        ficha = B.limpiar(FICHA, set())
        textos = {b['id']: C.respuesta_correcta_texto(b) for b in ficha['bloques']}
        self.assertEqual(textos['u'], 'B. 4')
        self.assertEqual(textos['v'], 'A, C')
        self.assertEqual(textos['c'], 'Bogotá · Magdalena')
        self.assertEqual(textos['o'], 'uno → dos → tres')


@override_settings(MEDIA_ROOT=MEDIA)
class Cuadernillo(ColegioDePrueba):

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(MEDIA, ignore_errors=True)

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.a.modulos_activos = list(cls.a.modulos_activos) + ['salon']
        cls.a.save(update_fields=['modulos_activos'])

    def test_cuadernillo_y_puntoexacto(self):
        profe = self.cliente(self.u_docente)
        profe.post('/materiales/nuevo/', {'tipo': 'cuadernillo', 'titulo': 'Simulacro tipo Saber'})
        doc = Documento.objects.get()
        self.assertTrue(doc.contenido['opciones']['portada'])
        contenido = {'bloques': [
            {'id': 's1', 'tipo': 'seccion', 'titulo': 'Lenguaje'},
            {'id': 'x1', 'tipo': 'contexto', 'titulo': 'Jugo de mango', 'html': '<p>Ingredientes…</p>', 'cubre': 0},
            {'id': 'p1', 'tipo': 'pregunta', 'modo': 'unica', 'enunciado': '¿Cuántas?', 'opciones': ['1', '2', '3', '4'], 'correcta': 1},
            {'id': 'p2', 'tipo': 'pregunta', 'modo': 'unica', 'enunciado': 'Indicación', 'opciones': ['A', 'B', 'C', 'D'], 'correcta': 0, 'control': True},
            {'id': 's2', 'tipo': 'seccion', 'titulo': 'Matemáticas'},
            {'id': 'p3', 'tipo': 'pregunta', 'modo': 'vf', 'enunciado': '2 es par', 'valor': True},
            {'id': 'p4', 'tipo': 'pregunta', 'modo': 'unica', 'enunciado': '¿5×2?', 'opciones': ['7', '10', '12'], 'correcta': 1},
        ], 'opciones': dict(doc.contenido['opciones'], sesion='sesión 1', horario='6:30 a. m. a 8:45 a. m.')}
        profe.post(f'/materiales/{doc.pk}/guardar/', json.dumps({'titulo': doc.titulo, 'grado': '4.º', 'contenido': contenido}),
                   content_type='application/json')
        doc.refresh_from_db()
        from materiales import exportar
        ctx = exportar.contexto(doc)
        ctx_x = next(b for b in ctx['bloques'] if b['tipo'] == 'contexto')
        self.assertEqual((ctx_x['desde'], ctx_x['hasta']), (1, 2))
        self.assertEqual(ctx['areas'], ['Lenguaje', 'Matemáticas'])
        r = profe.get(f'/materiales/{doc.pk}/pdf/')
        self.assertTrue(r.content.startswith(b'%PDF'))
        r = profe.get(f'/materiales/{doc.pk}/word/?respuestas=1')
        from docx import Document
        texto = '\n'.join(p.text for p in Document(io.BytesIO(r.content)).paragraphs)
        self.assertIn('Responde las preguntas 1 a 2', texto)
        self.assertIn('Respuesta: B. 2', texto)

        # A PuntoExacto: 4 preguntas, la 2 de control, la 3 verdadero o falso (A/B)
        profe.post(f'/materiales/{doc.pk}/accion/', {'accion': 'puntoexacto', 'asignacion': self.asig.pk, 'periodo': self.p1.pk})
        doc.refresh_from_db()
        ex = doc.examen
        self.assertEqual((ex.numero_preguntas, ex.numero_opciones, ex.asignacion, ex.periodo), (4, 4, self.asig, self.p1))
        claves = [(p.numero, p.correcta, p.es_control, p.numero_opciones) for p in ex.preguntas.order_by('numero')]
        self.assertEqual(claves, [(1, 'B', False, None), (2, 'A', True, None), (3, 'A', False, 2), (4, 'B', False, 3)])
        # Cambia la clave en el cuadernillo y se actualiza
        contenido['bloques'][6]['correcta'] = 2
        profe.post(f'/materiales/{doc.pk}/guardar/', json.dumps({'titulo': doc.titulo, 'contenido': contenido}), content_type='application/json')
        profe.post(f'/materiales/{doc.pk}/accion/', {'accion': 'puntoexacto'})
        self.assertEqual(ex.preguntas.get(numero=4).correcta, 'C')
        # Una pregunta abierta no cabe en la hoja de burbujas
        contenido['bloques'].append({'id': 'p5', 'tipo': 'pregunta', 'modo': 'abierta', 'enunciado': 'Explica'})
        profe.post(f'/materiales/{doc.pk}/guardar/', json.dumps({'titulo': doc.titulo, 'contenido': contenido}), content_type='application/json')
        r = profe.post(f'/materiales/{doc.pk}/accion/', {'accion': 'puntoexacto'}, follow=True)
        self.assertContains(r, 'no va en la hoja de burbujas')
        self.assertEqual(ex.preguntas.count(), 4)


@override_settings(MEDIA_ROOT=MEDIA)
class FichaEnElAula(ColegioDePrueba):

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.a.modulos_activos = list(cls.a.modulos_activos) + ['salon']
        cls.a.save(update_fields=['modulos_activos'])

    def test_asignar_resolver_revisar_y_planilla(self):
        ana, beto = self.estudiantes[0], self.estudiantes[1]
        profe = self.cliente(self.u_docente)
        profe.get(f'/aula/asignacion/{self.asig.id}/')
        aula = Aula.objects.get(asignacion=self.asig)
        profe.post('/materiales/nuevo/', {'tipo': 'taller', 'titulo': 'Taller mixto'})
        doc = Documento.objects.get()
        profe.post('/materiales/imagen/', {'imagen': png()})
        img = Imagen.objects.get()
        contenido = {'bloques': [{'id': 'im', 'tipo': 'imagen', 'imagen': img.pk, 'ancho': 50}] + FICHA['bloques']}
        profe.post(f'/materiales/{doc.pk}/guardar/', json.dumps({'titulo': doc.titulo, 'contenido': contenido}), content_type='application/json')

        r = profe.post(f'/materiales/{doc.pk}/accion/', {'accion': 'ficha', 'aula': aula.pk, 'modo': 'puntos', 'intentos': '2',
                                                         'tiempo': '0', 'mostrar': 'al_terminar'})
        t = Tarea.objects.get(aula=aula)
        self.assertRedirects(r, f'/aula/{aula.pk}/tareas/{t.pk}/editar/', fetch_redirect_response=False)
        self.assertFalse(t.publicada)
        self.assertEqual(t.ficha_config['intentos'], 2)
        # El docente la publica con su periodo y componente (y se avisa)
        profe.post(f'/aula/{aula.pk}/tareas/{t.pk}/editar/', {'titulo': t.titulo, 'publicada': 'on', 'periodo': self.p1.pk,
                                                             'componente': 'SABER'})
        t.refresh_from_db()
        self.assertTrue(t.publicada)
        self.assertEqual(self.cliente(ana.user).get(f'/aula/{aula.pk}/').status_code, 200)

        est = self.cliente(ana.user)
        self.assertContains(est.get(f'/aula/{aula.pk}/tareas/{t.pk}/'), 'Resolver la ficha')
        r = est.get(f'/aula/{aula.pk}/tareas/{t.pk}/ficha/')
        self.assertContains(r, 'Enviar ficha')
        self.assertNotContains(r, 'Respuesta: B. 4')
        self.assertEqual(est.get(f'/aula/{aula.pk}/tareas/{t.pk}/ficha/imagen/{img.pk}/').status_code, 302)
        self.assertEqual(est.get(f'/aula/{aula.pk}/tareas/{t.pk}/ficha/imagen/{img.pk + 99}/').status_code, 404)
        datos = {'r-u': '1', 'r-v': ['0', '2'], 'r-f': 'v', 'r-c-0': 'Bogotá', 'r-c-1': 'magdalena', 'r-n': '0,5',
                 'r-k': 'fotosintesis', 'r-e-0': '0', 'r-e-1': '1', 'r-o': '0,1,2', 'r-s-0': '0', 'r-s-1': '1',
                 'r-a': 'Porque las plantas…'}
        est.post(f'/aula/{aula.pk}/tareas/{t.pk}/ficha/', datos)
        e = Entrega.objects.get(tarea=t, estudiante=ana)
        self.assertEqual((e.intentos, e.estado, e.nota), (1, 'entregada', None))     # falta la abierta
        r = est.get(f'/aula/{aula.pk}/tareas/{t.pk}/ficha/')
        self.assertContains(r, 'está revisando')

        # El docente revisa la abierta: 3 de 3 → todo bien → 5,0
        r = profe.get(f'/aula/{aula.pk}/tareas/{t.pk}/ficha/e{ana.id}/revisar/')
        self.assertContains(r, 'Puntos a mano')
        profe.post(f'/aula/{aula.pk}/tareas/{t.pk}/ficha/e{ana.id}/revisar/', {'p-a': '3', 'comentario': 'Muy bien'})
        e.refresh_from_db()
        self.assertEqual((e.estado, e.nota), ('calificada', Decimal('5.0')))
        self.assertContains(profe.get(f'/aula/{aula.pk}/tareas/{t.pk}/'), 'Revisar ficha')
        profe.post(f'/aula/{aula.pk}/tareas/{t.pk}/planilla/')
        nd = NotaDetallada.objects.get(calificacion_promedio__estudiante=ana, descripcion='Taller mixto')
        self.assertEqual(nd.valor_nota, Decimal('5.0'))

        # Beto: un intento peor no baja; el tercer intento no se acepta
        otro = self.cliente(beto.user)
        otro.post(f'/aula/{aula.pk}/tareas/{t.pk}/ficha/', {'r-u': '1', 'r-a': ''})
        eb = Entrega.objects.get(tarea=t, estudiante=beto)
        self.assertEqual(eb.nota, Decimal('1.3'))       # 1 de 13 puntos
        otro.post(f'/aula/{aula.pk}/tareas/{t.pk}/ficha/', {'r-u': '0'})
        eb.refresh_from_db()
        self.assertEqual((eb.intentos, eb.nota), (2, Decimal('1.3')))
        otro.post(f'/aula/{aula.pk}/tareas/{t.pk}/ficha/', {'r-u': '1', 'r-f': 'v'})
        eb.refresh_from_db()
        self.assertEqual(eb.intentos, 2)
        # El estudiante no revisa fichas
        self.assertEqual(otro.get(f'/aula/{aula.pk}/tareas/{t.pk}/ficha/e{ana.id}/revisar/').status_code, 403)
        # El docente ve la vista previa sin poder enviar
        self.assertContains(profe.get(f'/aula/{aula.pk}/tareas/{t.pk}/ficha/'), 'Vista previa del docente')
