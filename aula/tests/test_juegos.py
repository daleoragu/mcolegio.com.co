"""Actividades interactivas y cuestionarios estilo Quizizz / Kahoot."""
import json
import shutil
import tempfile
from datetime import timedelta
from decimal import Decimal

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, override_settings
from django.utils import timezone

from aula import juegos
from aula.models import (Actividad, Aula, Cuestionario, Intento, ResultadoActividad, SesionVivo)
from notas.models import NotaDetallada
from notas.tests.base import CLAVE, ColegioDePrueba

MEDIA = tempfile.mkdtemp(prefix='aula-juegos-')

AIKEN = """¿Cuánto es 2 + 3?
A) 4
B) 5
C) 6
RESPUESTA: B

¿Capital de Colombia?
*A) Bogotá
B) Medellín

¿Cuál es par?
A. 3
B. 7
C. 8
ANSWER: C
"""


@override_settings(MEDIA_ROOT=MEDIA)
class Juegos(ColegioDePrueba):

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
        self.ana, self.beto = self.estudiantes[0], self.estudiantes[1]
        self.profe = self.cliente(self.u_docente)
        self.profe.get(f'/aula/asignacion/{self.asig.id}/')
        self.aula = Aula.objects.get(asignacion=self.asig)
        self.base = f'/aula/{self.aula.pk}'

    # -- Utilidades ---------------------------------------------------------
    def test_aiken_y_puntos(self):
        preguntas = juegos.leer_aiken(AIKEN)
        self.assertEqual(len(preguntas), 3)
        self.assertEqual(preguntas[0][0], '¿Cuánto es 2 + 3?')
        self.assertEqual([c for _, c in preguntas[0][1]], [False, True, False])
        self.assertEqual([c for _, c in preguntas[1][1]], [True, False])
        self.assertEqual(preguntas[1][1][0][0], 'Bogotá')
        self.assertEqual([c for _, c in preguntas[2][1]], [False, False, True])
        self.assertEqual(juegos.puntos(True, 0, 20), 1000)
        self.assertEqual(juegos.puntos(True, 20000, 20), 500)
        self.assertEqual(juegos.puntos(False, 100, 20), 0)
        self.assertEqual(juegos.nota(self.aula, 2, 3), Decimal('3.7'))
        self.assertEqual(juegos.nota_de_puntaje(self.aula, 8, 10), Decimal('4.2'))

    # -- Actividades --------------------------------------------------------
    def test_actividad_html_manda_nota_y_pasa_a_planilla(self):
        html = SimpleUploadedFile('juego.html', b'<html><body>hola</body></html>', content_type='text/html')
        r = self.profe.post(f'{self.base}/actividades/', {
            'titulo': 'Fracciones', 'archivo': html, 'califica': 'on', 'periodo': self.p1.pk, 'componente': 'HACER'})
        a = Actividad.objects.get()
        self.assertRedirects(r, f'{self.base}/actividades/{a.pk}/', fetch_redirect_response=False)
        self.assertTrue(a.califica)
        self.assertEqual(a.componente, 'HACER')
        # Un archivo que no es HTML no se acepta
        self.profe.post(f'{self.base}/actividades/', {
            'titulo': 'Otro', 'archivo': SimpleUploadedFile('x.pdf', b'%PDF')})
        self.assertEqual(Actividad.objects.count(), 1)

        est = self.cliente(self.ana.user)
        self.assertContains(est.get(f'{self.base}/actividades/'), 'Fracciones')
        r = est.get(f'{self.base}/actividades/{a.pk}/')
        self.assertContains(r, 'mcolegio-nota')
        self.assertEqual(est.get(f'{self.base}/archivo/act/{a.pk}/').status_code, 302)

        url = f'{self.base}/actividades/{a.pk}/resultado/'
        r = est.post(url, json.dumps({'puntaje': 8, 'maximo': 10}), content_type='application/json')
        self.assertEqual(r.json()['nota'], '4.2')
        # Un intento peor no baja la nota
        est.post(url, json.dumps({'puntaje': 2, 'maximo': 10}), content_type='application/json')
        res = ResultadoActividad.objects.get()
        self.assertEqual((res.nota, res.ultima, res.intentos), (Decimal('4.2'), Decimal('1.8'), 2))
        # La nota se ajusta a la escala
        est.post(url, json.dumps({'nota': 9}), content_type='application/json')
        res.refresh_from_db()
        self.assertEqual(res.nota, Decimal('5.0'))
        # Basura: error, no se cae
        self.assertEqual(est.post(url, 'nada', content_type='application/json').status_code, 400)
        # El estudiante no pasa notas
        self.assertEqual(est.post(f'{self.base}/actividades/{a.pk}/accion/', {'accion': 'planilla'}).status_code, 403)

        self.assertContains(self.profe.get(f'{self.base}/calificaciones/'), 'Fracciones')
        self.profe.post(f'{self.base}/actividades/{a.pk}/accion/', {'accion': 'planilla'})
        nd = NotaDetallada.objects.get(calificacion_promedio__estudiante=self.ana, descripcion='Fracciones')
        self.assertEqual(nd.valor_nota, Decimal('5.0'))
        self.assertEqual(nd.calificacion_promedio.tipo_nota, 'HACER')

    def test_actividad_por_enlace_y_ejemplo(self):
        self.profe.post(f'{self.base}/actividades/', {'titulo': 'GeoGebra',
                                                     'enlace': 'https://www.geogebra.org/m/abc'})
        a = Actividad.objects.get()
        self.assertFalse(a.califica)
        self.assertContains(self.cliente(self.ana.user).get(f'{self.base}/actividades/{a.pk}/'), 'geogebra.org/m/abc')
        r = self.cliente(self.ana.user).post(f'{self.base}/actividades/{a.pk}/resultado/', '{"nota": 4}',
                                             content_type='application/json')
        self.assertEqual(r.status_code, 404)
        r = self.profe.get('/aula/actividad-ejemplo.html')
        self.assertIn(b"tipo: 'mcolegio-nota'", r.content)

    # -- Cuestionario a su ritmo -------------------------------------------
    def crear_cuestionario(self, **extra):
        self.profe.post(f'{self.base}/cuestionarios/', {'titulo': 'Repaso', 'aiken': AIKEN})
        q = Cuestionario.objects.get()
        for k, v in extra.items():
            setattr(q, k, v)
        q.save()
        return q

    def test_editor_guarda_preguntas(self):
        q = self.crear_cuestionario()
        self.assertEqual(q.preguntas.count(), 3)
        preguntas = [
            {'texto': '¿1 + 1?', 'segundos': '30', 'opciones': [{'texto': '2', 'correcta': True}, {'texto': '3'}]},
            {'texto': 'Sin correcta', 'opciones': [{'texto': 'a'}, {'texto': 'b'}]},
        ]
        r = self.profe.post(f'{self.base}/cuestionarios/{q.pk}/editar/', {
            'titulo': 'Repaso 2', 'segundos': '15', 'a_su_ritmo': 'on', 'periodo': self.p1.pk,
            'componente': 'SABER', 'preguntas_json': json.dumps(preguntas)})
        self.assertEqual(r.status_code, 302)
        q.refresh_from_db()
        self.assertEqual((q.titulo, q.segundos, q.mezclar, q.componente), ('Repaso 2', 15, False, 'SABER'))
        p = q.preguntas.get()
        self.assertEqual(p.tiempo, 30)
        self.assertEqual(self.cliente(self.ana.user).get(f'{self.base}/cuestionarios/{q.pk}/editar/').status_code, 403)

    def test_a_su_ritmo(self):
        q = self.crear_cuestionario(mezclar=False, periodo=self.p1, componente='SABER')
        est = self.cliente(self.ana.user)
        self.assertContains(est.get(f'{self.base}/cuestionarios/'), 'Repaso')
        # GET sin intento: vuelve al detalle
        self.assertEqual(est.get(f'{self.base}/cuestionarios/{q.pk}/jugar/').status_code, 302)
        est.post(f'{self.base}/cuestionarios/{q.pk}/jugar/')
        self.assertEqual(est.get(f'{self.base}/cuestionarios/{q.pk}/jugar/').status_code, 200)
        url = f'{self.base}/cuestionarios/{q.pk}/jugar/estado/'
        correctas = {p.id: p.opciones.get(correcta=True).id for p in q.preguntas.all()}
        incorrecta = {p.id: p.opciones.filter(correcta=False).first().id for p in q.preguntas.all()}
        for i in range(3):
            d = est.get(url).json()
            self.assertEqual(d['numero'], i + 1)
            self.assertNotIn('correcta', d)
            opcion = incorrecta[d['id']] if i == 2 else correctas[d['id']]
            r = est.post(url, json.dumps({'pregunta': d['id'], 'opcion': opcion}), content_type='application/json').json()
            self.assertEqual(r['correcta'], i < 2)
        fin = est.get(url).json()
        self.assertTrue(fin['fin'])
        self.assertEqual((fin['aciertos'], fin['nota']), (2, '3.7'))
        self.assertGreater(fin['puntos'], 1900)
        # Sin reintentos no vuelve a empezar
        est.post(f'{self.base}/cuestionarios/{q.pk}/jugar/')
        self.assertEqual(Intento.objects.count(), 1)
        # Respuesta tardía: no cuenta
        q.reintentos = True
        q.save()
        est.post(f'{self.base}/cuestionarios/{q.pk}/jugar/')
        it = Intento.objects.get(terminado__isnull=True)
        Intento.objects.filter(pk=it.pk).update(inicio_pregunta=timezone.now() - timedelta(seconds=60))
        d = est.get(url).json()
        r = est.post(url, json.dumps({'pregunta': d['id'], 'opcion': correctas[d['id']]}),
                     content_type='application/json').json()
        self.assertFalse(r['correcta'])

        self.profe.post(f'{self.base}/cuestionarios/{q.pk}/accion/', {'accion': 'planilla'})
        nd = NotaDetallada.objects.get(calificacion_promedio__estudiante=self.ana, descripcion='Repaso')
        self.assertEqual(nd.valor_nota, Decimal('3.7'))
        self.assertContains(self.profe.get(f'{self.base}/calificaciones/'), 'Cuestionario')

    # -- En vivo ------------------------------------------------------------
    def test_en_vivo(self):
        q = self.crear_cuestionario(a_su_ritmo=False)
        self.profe.post(f'{self.base}/cuestionarios/{q.pk}/accion/', {'accion': 'vivo'})
        s = SesionVivo.objects.get()
        url = f'{self.base}/vivo/{s.pk}/estado/'
        ana, beto = self.cliente(self.ana.user), self.cliente(self.beto.user)
        self.assertContains(ana.get(f'{self.base}/'), '¡Unirme al juego!')
        self.assertEqual(ana.get(f'{self.base}/vivo/{s.pk}/').status_code, 200)
        beto.get(f'{self.base}/vivo/{s.pk}/')
        d = self.profe.get(url).json()
        self.assertEqual((d['estado'], d['jugadores']), ('espera', 2))
        # Solo el docente avanza: el POST del estudiante es una respuesta
        self.assertEqual(ana.post(url, '{}', content_type='application/json').status_code, 409)

        for _ in range(3):
            d = self.profe.post(url).json()
            self.assertEqual(d['estado'], 'pregunta')
            self.assertNotIn('correcta', d['pregunta'])
            p = q.preguntas.get(pk=d['pregunta']['id'])
            ana.post(url, json.dumps({'opcion': p.opciones.get(correcta=True).id}), content_type='application/json')
            beto.post(url, json.dumps({'opcion': p.opciones.filter(correcta=False).first().id}),
                      content_type='application/json')
            # No se responde dos veces
            r = ana.post(url, json.dumps({'opcion': p.opciones.get(correcta=True).id}), content_type='application/json')
            self.assertEqual(r.status_code, 409)
            d = self.profe.post(url).json()
            self.assertEqual(d['estado'], 'resultado')
            self.assertEqual(sum(d['conteo'].values()), 2)
            self.assertEqual(d['ranking'][0]['nombre'], 'Ana Prueba')
            d = ana.get(url).json()
            self.assertTrue(d['mi_correcta'])
        d = self.profe.post(url).json()
        self.assertEqual(d['estado'], 'fin')
        d = ana.get(url).json()
        self.assertEqual((d['mi_puesto'], d['mi_nota']), (1, '5.0'))
        self.assertEqual(beto.get(url).json()['mi_nota'], '1.0')
        self.assertNotContains(ana.get(f'{self.base}/'), '¡Unirme al juego!')
        self.assertContains(self.profe.get(f'{self.base}/cuestionarios/{q.pk}/'), 'Ana Prueba')


class JuegosSalon(ColegioDePrueba):

    def test_cuestionario_en_salon_digital(self):
        from salon_digital.models import Cuenta, Grupo, Integrante
        u = User.objects.create_user('libre', password=CLAVE)
        cuenta = Cuenta.objects.create(usuario=u, slug='lina', nombre_publico='Lina', estado='verificada')
        grupo = Grupo.objects.create(propietario=cuenta, nombre='7-01')
        luis = Integrante.objects.create(grupo=grupo, apellidos='Pérez', nombres='Luis')
        profe = Client(HTTP_HOST='localhost')
        profe.force_login(u)
        profe.get(f'/aula/grupo/{grupo.pk}/')
        aula = Aula.objects.get(grupo=grupo)
        profe.post(f'/aula/{aula.pk}/cuestionarios/', {'titulo': 'Quiz', 'aiken': AIKEN})
        q = Cuestionario.objects.get()
        est = Client(HTTP_HOST='localhost')
        est.post(f'/aula/{aula.pk}/entrar/', {'codigo': grupo.codigo, 'integrante': luis.pk})
        est.post(f'/aula/{aula.pk}/cuestionarios/{q.pk}/jugar/')
        url = f'/aula/{aula.pk}/cuestionarios/{q.pk}/jugar/estado/'
        for _ in range(3):
            d = est.get(url).json()
            est.post(url, json.dumps({'pregunta': d['id'], 'opcion': None}), content_type='application/json')
        it = Intento.objects.get()
        self.assertEqual((it.integrante, it.nota), (luis, Decimal('1.0')))
        self.assertContains(profe.get(f'/aula/{aula.pk}/calificaciones/'), 'Quiz')
        self.assertContains(profe.get(f'/aula/{aula.pk}/cuestionarios/{q.pk}/'), 'Luis')
