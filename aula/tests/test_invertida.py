"""Aula invertida: video + preguntas pegadas, respuestas del estudiante, nota y planilla."""
from decimal import Decimal

from aula.invertida import leer_preguntas
from aula.models import Aula, ClaseInvertida, RespuestaInvertida
from notas.models import Calificacion, Notificacion
from notas.tests.base import ColegioDePrueba

PREGUNTAS = """1. ¿Qué es la fotosíntesis?
2. ¿Dónde ocurre?
A) En la raíz
*B) En las hojas
C) En el tallo
3. ¿Qué gas libera?
a. Oxígeno
b. Nitrógeno
RESPUESTA: a
"""


class LeerPreguntas(ColegioDePrueba):

    def test_abiertas_y_de_seleccion(self):
        p = leer_preguntas(PREGUNTAS)
        self.assertEqual([x['texto'] for x in p], ['¿Qué es la fotosíntesis?', '¿Dónde ocurre?', '¿Qué gas libera?'])
        self.assertEqual(p[0]['opciones'], [])
        self.assertEqual([o['correcta'] for o in p[1]['opciones']], [False, True, False])
        self.assertEqual([o['correcta'] for o in p[2]['opciones']], [True, False])

    def test_separadas_por_linea_en_blanco_y_varias_lineas(self):
        p = leer_preguntas('Explique con sus palabras\npor qué el cielo es azul.\n\n¿Le gustó el video?\nA) Sí\nB) No')
        self.assertEqual(p[0]['texto'], 'Explique con sus palabras por qué el cielo es azul.')
        self.assertEqual(len(p[1]['opciones']), 2)
        self.assertFalse(any(o['correcta'] for o in p[1]['opciones']))

    def test_vacio(self):
        self.assertEqual(leer_preguntas('   \n\n'), [])


class _BaseInvertida(ColegioDePrueba):

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
        self.base = f'/aula/{self.aula.pk}/invertida'

    def crear(self, **extra):
        datos = {'titulo': 'Fotosíntesis', 'video': 'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
                 'instrucciones': 'Véalo antes de clase', 'preguntas': PREGUNTAS}
        datos.update(extra)
        r = self.profe.post(f'{self.base}/', datos)
        return r, ClaseInvertida.objects.order_by('-pk').first()

    def responder(self, est, datos):
        c = self.cliente(est.user)
        return c, c.post(f'{self.base}/{self.clase.pk}/', datos)


class AulaInvertida(_BaseInvertida):

    def test_el_docente_publica_y_avisa(self):
        r, self.clase = self.crear()
        self.assertRedirects(r, f'{self.base}/{self.clase.pk}/', fetch_redirect_response=False)
        self.assertEqual(len(self.clase.preguntas), 3)
        self.assertEqual(self.clase.calificables, 2)
        self.assertEqual(self.clase.youtube_id, 'dQw4w9WgXcQ')
        self.assertTrue(Notificacion.objects.filter(destinatario=self.ana.user, mensaje__contains='clase invertida').exists())
        r = self.cliente(self.ana.user).get(f'{self.base}/{self.clase.pk}/')
        self.assertContains(r, 'youtube-nocookie.com/embed/dQw4w9WgXcQ')
        self.assertContains(r, 'Enviar respuestas')
        self.assertNotContains(r, 'inv-op correcta')     # no ve cuál es la correcta antes de responder

    def test_sin_preguntas_o_sin_video_no_se_guarda(self):
        self.crear(preguntas='')
        self.crear(video='no es un enlace')
        self.assertFalse(ClaseInvertida.objects.exists())

    def test_responder_calificar_y_ver_resultado(self):
        _, self.clase = self.crear()
        # Le falta una: no guarda y conserva lo escrito
        c, r = self.responder(self.ana, {'p0': 'Es cuando la planta hace su alimento', 'p1': '1'})
        self.assertContains(r, 'Le falta responder: 3')
        self.assertContains(r, 'Es cuando la planta hace su alimento')
        self.assertFalse(RespuestaInvertida.objects.exists())
        # Completa: 2 de 2 correctas
        c, r = self.responder(self.ana, {'p0': 'Es cuando la planta hace su alimento', 'p1': '1', 'p2': '0'})
        resp = RespuestaInvertida.objects.get(estudiante=self.ana)
        self.assertEqual(resp.aciertos, 2)
        self.assertEqual(resp.nota, Decimal('5.0'))
        r = c.get(f'{self.base}/{self.clase.pk}/')
        self.assertContains(r, 'Respuestas enviadas')
        # No puede responder dos veces
        c.post(f'{self.base}/{self.clase.pk}/', {'p0': 'otra', 'p1': '0', 'p2': '1'})
        self.assertEqual(RespuestaInvertida.objects.get(estudiante=self.ana).aciertos, 2)
        # Beto: 0 de 2
        self.responder(self.beto, {'p0': 'no sé', 'p1': '0', 'p2': '1'})
        self.assertEqual(RespuestaInvertida.objects.get(estudiante=self.beto).nota, Decimal('1.0'))

    def test_el_docente_ve_resumen_pone_nota_y_reabre(self):
        _, self.clase = self.crear()
        self.responder(self.ana, {'p0': 'Mi respuesta abierta', 'p1': '1', 'p2': '1'})
        r = self.profe.get(f'{self.base}/{self.clase.pk}/')
        self.assertContains(r, '1 de 3 respondieron')
        self.assertContains(r, 'Mi respuesta abierta')
        self.assertContains(r, '100 % acertó')
        self.assertContains(r, '0 % acertó')
        accion = f'{self.base}/{self.clase.pk}/accion/'
        self.profe.post(accion, {'accion': 'nota', 'clave': f'e{self.ana.id}', 'nota': '4,5', 'comentario': 'Bien'})
        resp = RespuestaInvertida.objects.get(estudiante=self.ana)
        self.assertEqual((resp.nota, resp.nota_manual, resp.comentario), (Decimal('4.5'), True, 'Bien'))
        self.profe.post(accion, {'accion': 'nota', 'clave': f'e{self.ana.id}', 'nota': '9'})
        self.assertEqual(RespuestaInvertida.objects.get(estudiante=self.ana).nota, Decimal('4.5'))
        self.profe.post(accion, {'accion': 'reabrir', 'clave': f'e{self.ana.id}'})
        self.assertFalse(RespuestaInvertida.objects.exists())

    def test_pasar_a_la_planilla(self):
        _, self.clase = self.crear(periodo=self.p1.id, componente='SABER')
        self.responder(self.ana, {'p0': 'x', 'p1': '1', 'p2': '0'})
        self.profe.post(f'{self.base}/{self.clase.pk}/accion/', {'accion': 'planilla'})
        self.clase.refresh_from_db()
        self.assertIsNotNone(self.clase.pasada_planilla)
        self.assertTrue(Calificacion.objects.filter(estudiante=self.ana, periodo=self.p1).exists())

    def test_no_cambia_preguntas_si_ya_respondieron(self):
        _, self.clase = self.crear()
        self.responder(self.ana, {'p0': 'x', 'p1': '1', 'p2': '0'})
        self.profe.post(f'{self.base}/{self.clase.pk}/accion/', {
            'accion': 'editar', 'titulo': 'Nuevo título', 'video': self.clase.video, 'preguntas': '1. Otra cosa'})
        self.clase.refresh_from_db()
        self.assertEqual(self.clase.titulo, 'Fotosíntesis')
        self.profe.post(f'{self.base}/{self.clase.pk}/accion/', {
            'accion': 'editar', 'titulo': 'Nuevo título', 'video': self.clase.video, 'preguntas': PREGUNTAS})
        self.clase.refresh_from_db()
        self.assertEqual(self.clase.titulo, 'Nuevo título')

    def test_oculta_y_solo_para_algunos(self):
        _, self.clase = self.crear(para_modo='algunos', para=[f'e{self.beto.id}'])
        self.assertEqual(self.cliente(self.ana.user).get(f'{self.base}/{self.clase.pk}/').status_code, 404)
        self.assertEqual(self.cliente(self.beto.user).get(f'{self.base}/{self.clase.pk}/').status_code, 200)
        self.profe.post(f'{self.base}/{self.clase.pk}/accion/', {'accion': 'publicar'})
        self.assertEqual(self.cliente(self.beto.user).get(f'{self.base}/{self.clase.pk}/').status_code, 404)

    def test_el_estudiante_no_edita(self):
        _, self.clase = self.crear()
        r = self.cliente(self.ana.user).post(f'{self.base}/{self.clase.pk}/accion/', {'accion': 'eliminar'})
        self.assertEqual(r.status_code, 403)
        self.assertTrue(ClaseInvertida.objects.exists())

    def test_pestana_en_el_aula(self):
        r = self.cliente(self.ana.user).get(f'/aula/{self.aula.pk}/')
        self.assertContains(r, 'Aula invertida')


PAUSADAS = """[0:05] ¿Qué es la fotosíntesis?
[0:12] ¿Dónde ocurre?
A) En la raíz
*B) En las hojas
¿Qué aprendió del video?
"""


class VideoConPausas(_BaseInvertida):
    """El video se detiene en las preguntas con minuto y se guarda el avance."""

    def test_lee_el_minuto(self):
        p = leer_preguntas('[2:30] Uno\n1. [1:02:05] Dos\nA) x\n*B) y\nTres sin minuto')
        self.assertEqual([x['segundo'] for x in p], [150, 3725, None])
        self.assertEqual(p[0]['texto'], 'Uno')

    def test_pagina_con_pausas(self):
        _, self.clase = self.crear(preguntas=PAUSADAS)
        self.assertTrue(self.clase.con_pausas)
        r = self.cliente(self.ana.user).get(f'{self.base}/{self.clase.pk}/')
        self.assertContains(r, 'invertida_pausas.js')
        self.assertContains(r, 'id="inv-config"')
        self.assertContains(r, 'aparece en el video en el minuto 0:05')
        self.assertContains(r, 'id="inv-enviar" disabled')

    def test_sin_youtube_no_hay_pausas(self):
        _, self.clase = self.crear(preguntas=PAUSADAS, video='https://drive.google.com/file/d/abc/view')
        self.assertFalse(self.clase.con_pausas)
        self.assertNotContains(self.cliente(self.ana.user).get(f'{self.base}/{self.clase.pk}/'), 'invertida_pausas.js')

    def test_guarda_el_avance_y_luego_envia(self):
        import json
        _, self.clase = self.crear(preguntas=PAUSADAS)
        c = self.cliente(self.ana.user)
        url = f'{self.base}/{self.clase.pk}/progreso/'
        r = c.post(url, json.dumps({'respuestas': {'0': 'Hacer alimento', '1': '1', '9': 'x'}, 'visto': 14, 'duracion': 60}),
                   content_type='application/json')
        self.assertTrue(r.json()['ok'])
        av = RespuestaInvertida.objects.get(estudiante=self.ana)
        self.assertEqual((av.terminada, av.respuestas, av.visto_hasta, av.pct_visto),
                         (False, {'0': 'Hacer alimento', '1': 1}, 14, 23))
        # Al volver, la página trae lo que ya respondió en el video
        r = c.get(f'{self.base}/{self.clase.pk}/')
        self.assertContains(r, 'Hacer alimento')
        self.assertContains(r, '"respondidas": [0, 1]')
        # El docente lo ve «viendo el video» y no cuenta como respuesta enviada
        r = self.profe.get(f'{self.base}/{self.clase.pk}/')
        self.assertContains(r, 'Viendo el video')
        self.assertContains(r, 'Vio el 23 % del video')
        self.assertContains(r, '0 de 3 respondieron')
        # Envía todo
        c.post(f'{self.base}/{self.clase.pk}/', {'p0': 'Hacer alimento', 'p1': '1', 'p2': 'Mucho'})
        av.refresh_from_db()
        self.assertTrue(av.terminada)
        self.assertEqual((av.aciertos, av.nota), (1, Decimal('5.0')))
        self.assertEqual(RespuestaInvertida.objects.count(), 1)
        # Ya enviada, el avance no la cambia
        r = c.post(url, json.dumps({'respuestas': {'2': 'otra'}}), content_type='application/json')
        self.assertFalse(r.json()['ok'])
        self.assertContains(self.profe.get(f'{self.base}/{self.clase.pk}/'), '1 de 3 respondieron')

    def test_el_visto_no_pasa_de_la_duracion(self):
        import json
        _, self.clase = self.crear(preguntas=PAUSADAS)
        c = self.cliente(self.ana.user)
        c.post(f'{self.base}/{self.clase.pk}/progreso/', json.dumps({'visto': 500, 'duracion': 60}),
               content_type='application/json')
        self.assertEqual(RespuestaInvertida.objects.get(estudiante=self.ana).visto_hasta, 60)

    def test_el_docente_no_usa_el_avance(self):
        _, self.clase = self.crear(preguntas=PAUSADAS)
        r = self.profe.post(f'{self.base}/{self.clase.pk}/progreso/', '{}', content_type='application/json')
        self.assertEqual(r.status_code, 403)
