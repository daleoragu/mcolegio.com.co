"""Gamificación: juegos con preguntas estilo Saber, calificados en el servidor, y la práctica libre."""
import json
from decimal import Decimal

from aula import bancos_juegos
from aula.models import Aula, JuegoAula, ResultadoJuegoAula
from aula.views_gamificacion import validar_preguntas
from notas.models import Calificacion
from notas.tests.base import ColegioDePrueba

PREGUNTAS = """1. ¿Cuánto es 2 + 2?
A) 3
*B) 4
C) 5
2. Capital de Colombia
*A) Bogotá
B) Cali
3. ¿Cuánto es 3 × 3?
A) 6
B) 8
*C) 9
D) 12
"""


class Gamificacion(ColegioDePrueba):

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.a.modulos_activos = list(cls.a.modulos_activos) + ['salon']
        cls.a.save(update_fields=['modulos_activos'])

    def setUp(self):
        self.ana, self.beto, self.caro = self.estudiantes
        self.profe = self.cliente(self.u_docente)
        self.profe.get(f'/aula/asignacion/{self.asig.id}/')
        self.aula = Aula.objects.get(asignacion=self.asig)
        self.base = f'/aula/{self.aula.pk}/gamificacion'

    def crear(self, **extra):
        datos = {'tipo': 'laberinto', 'titulo': 'Repaso', 'preguntas': PREGUNTAS, 'segundos': '15'}
        datos.update(extra)
        self.profe.post(f'{self.base}/', datos)
        return JuegoAula.objects.order_by('-pk').first()

    def jugar(self, est, respuestas, j):
        c = self.cliente(est.user)
        return c.post(f'{self.base}/{j.pk}/resultado/', json.dumps({'respuestas': respuestas, 'puntaje': 9999999}),
                      content_type='application/json').json()

    def test_validar_preguntas(self):
        p, error = validar_preguntas(PREGUNTAS)
        self.assertEqual((len(p), error), (3, ''))
        _, error = validar_preguntas('1. Abierta sin opciones\n2. Otra\nA) x\nB) y')
        self.assertIn('1, 2', error)                     # la abierta y la que no tiene correcta
        _, error = validar_preguntas('1. Cinco\n*A) a\nB) b\nC) c\nD) d\nE) e')
        self.assertIn('2 a 4 opciones', error)

    def test_muchas_preguntas(self):
        texto = '\n'.join(f'{i}. ¿{i} + 1?\nA) {i}\n*B) {i + 1}' for i in range(1, 121))
        j = self.crear(preguntas=texto)
        self.assertEqual(len(j.preguntas), 120)

    def test_crear_y_ver_en_el_menu(self):
        j = self.crear(tipo='tanques')
        self.assertEqual((j.tipo, j.segundos, len(j.preguntas)), ('tanques', 15, 3))
        r = self.cliente(self.ana.user).get(f'{self.base}/')
        self.assertContains(r, 'AULA ARCADE')
        self.assertContains(r, 'REPASO')
        self.assertContains(r, 'PRÁCTICA LIBRE')
        j = self.crear(tipo='bandera')
        r = self.cliente(self.ana.user).get(f'{self.base}/{j.pk}/')
        self.assertContains(r, 'aula/juegos/motor.js')
        self.assertContains(r, 'aula/juegos/bandera.js')
        self.assertContains(r, 'jg-leyenda')

    def test_el_servidor_califica(self):
        j = self.crear()
        # Dos bien y una mal; el puntaje que manda el juego no cambia la nota
        r = self.jugar(self.ana, [{'i': 0, 'opcion': 1}, {'i': 1, 'opcion': 0}, {'i': 2, 'opcion': 0}], j)
        self.assertEqual((r['aciertos'], r['total']), (2, 3))
        res = ResultadoJuegoAula.objects.get(estudiante=self.ana)
        self.assertEqual(res.nota, Decimal('3.7'))
        # Una pregunta repetida no cuenta dos veces; índices raros se ignoran
        r = self.jugar(self.ana, [{'i': 0, 'opcion': 1}, {'i': 0, 'opcion': 1}, {'i': 99, 'opcion': 0}, {'i': 'x'}], j)
        self.assertEqual(r['aciertos'], 1)
        res.refresh_from_db()
        self.assertEqual((res.nota, res.intentos, res.ultima_nota), (Decimal('3.7'), 2, Decimal('2.3')))   # queda la mejor
        r = self.jugar(self.ana, [{'i': 0, 'opcion': 1}, {'i': 1, 'opcion': 0}, {'i': 2, 'opcion': 2}], j)
        res.refresh_from_db()
        self.assertEqual(res.nota, Decimal('5.0'))

    def test_el_docente_ve_resultados_y_pasa_a_la_planilla(self):
        j = self.crear(periodo=self.p1.id, componente='SABER')
        self.jugar(self.ana, [{'i': 0, 'opcion': 1}, {'i': 1, 'opcion': 0}, {'i': 2, 'opcion': 2}], j)
        r = self.profe.get(f'{self.base}/{j.pk}/')
        self.assertContains(r, 'Resultados (1 jugaron)')
        self.profe.post(f'{self.base}/{j.pk}/accion/', {'accion': 'planilla'})
        j.refresh_from_db()
        self.assertIsNotNone(j.pasado_planilla)
        self.assertTrue(Calificacion.objects.filter(estudiante=self.ana, periodo=self.p1).exists())

    def test_el_docente_prueba_sin_guardar(self):
        j = self.crear()
        r = self.profe.post(f'{self.base}/{j.pk}/resultado/', json.dumps({'respuestas': []}), content_type='application/json')
        self.assertTrue(r.json()['prueba'])
        self.assertFalse(ResultadoJuegoAula.objects.exists())

    def test_practica_libre(self):
        for tipo, _ in JuegoAula.TIPOS:
            for banco in bancos_juegos.BANCOS:
                r = self.cliente(self.ana.user).get(f'{self.base}/practica/{tipo}/{banco}/')
                self.assertEqual(r.status_code, 200, (tipo, banco))
        self.assertEqual(self.cliente(self.ana.user).get(f'{self.base}/practica/otro/matematicas/').status_code, 404)

    def test_bancos_bien_formados(self):
        for banco in bancos_juegos.BANCOS:
            for p in bancos_juegos.preguntas(banco, 10):
                self.assertEqual(sum(1 for o in p['opciones'] if o['correcta']), 1)
                self.assertTrue(2 <= len(p['opciones']) <= 4)
                self.assertEqual(len({o['texto'] for o in p['opciones']}), len(p['opciones']))

    def test_oculto_y_solo_para_algunos(self):
        j = self.crear(para_modo='algunos', para=[f'e{self.beto.id}'])
        self.assertEqual(self.cliente(self.ana.user).get(f'{self.base}/{j.pk}/').status_code, 404)
        self.assertEqual(self.cliente(self.beto.user).get(f'{self.base}/{j.pk}/').status_code, 200)
        self.profe.post(f'{self.base}/{j.pk}/accion/', {'accion': 'publicar'})
        self.assertEqual(self.cliente(self.beto.user).get(f'{self.base}/{j.pk}/').status_code, 404)

    def test_el_estudiante_no_crea_ni_borra(self):
        j = self.crear()
        self.cliente(self.ana.user).post(f'{self.base}/', {'tipo': 'tiro', 'titulo': 'X', 'preguntas': PREGUNTAS})
        self.cliente(self.ana.user).post(f'{self.base}/{j.pk}/accion/', {'accion': 'eliminar'})
        self.assertEqual(JuegoAula.objects.count(), 1)

    def test_juegos_deportivos(self):
        for tipo in ('penaltis', 'tenis', 'carrera', 'baloncesto'):
            r = self.cliente(self.ana.user).get(f'{self.base}/practica/{tipo}/colombia/')
            self.assertEqual(r.status_code, 200, tipo)
            self.assertContains(r, f'aula/juegos/{tipo}.js')
        r = self.cliente(self.ana.user).get(f'{self.base}/practica/tenis/matematicas/?jugadores=2')
        self.assertContains(r, 'jugadores: 2')
        self.assertContains(r, '2 jugadores')

    def test_dos_jugadores_no_guarda_y_penaltis_califica_lo_respondido(self):
        j = self.crear(tipo='penaltis', minutos='3')
        r = self.cliente(self.ana.user).get(f'{self.base}/{j.pk}/?jugadores=2')
        self.assertContains(r, 'const GUARDA = false')
        r = self.cliente(self.ana.user).get(f'{self.base}/{j.pk}/')
        self.assertContains(r, 'const GUARDA = true')
        # Solo respondió 2 de las 3 (la tanda terminó antes): la nota es sobre esas 2
        res = self.jugar(self.ana, [{'i': 0, 'opcion': 1}, {'i': 1, 'opcion': 0}], j)
        self.assertEqual((res['aciertos'], res['total'], res['nota']), (2, 2, '5.0'))

    def test_tenis_guarda_los_minutos(self):
        j = self.crear(tipo='tenis', minutos='10')
        self.assertEqual(j.minutos, 10)
        self.assertContains(self.cliente(self.ana.user).get(f'{self.base}/{j.pk}/'), 'minutos: 10')

    def test_tanques_con_el_diseno_nuevo(self):
        j = self.crear(tipo='tanques')
        r = self.cliente(self.ana.user).get(f'{self.base}/{j.pk}/')
        self.assertTemplateUsed(r, 'aula/juego_tanques.html')
        self.assertContains(r, 'mcolegio-config')
        self.assertContains(r, '"guarda": true')
        # El docente ve los resultados y puede probarlo (sin guardar)
        r = self.profe.get(f'{self.base}/{j.pk}/')
        self.assertContains(r, 'Probar el juego')
        r = self.profe.get(f'{self.base}/{j.pk}/?jugar=1')
        self.assertContains(r, '"guarda": false')

    def test_banco_de_factorizacion(self):
        p = bancos_juegos.preguntas('factorizacion', 10)
        self.assertEqual(len(p), 10)
        self.assertTrue(all(sum(1 for o in x['opciones'] if o['correcta']) == 1 for x in p))
        r = self.cliente(self.ana.user).get(f'{self.base}/practica/tanques/factorizacion/')
        self.assertContains(r, '"bancoPropio": true')
        self.assertEqual(self.cliente(self.ana.user).get(f'{self.base}/practica/laberinto/factorizacion/').status_code, 200)
