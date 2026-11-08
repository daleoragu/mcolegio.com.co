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
        p, error = validar_preguntas('1. Ocho\n*A) a\nB) b\nC) c\nD) d\nE) e\nF) f\nG) g\nH) h')
        self.assertEqual((len(p[0]['opciones']), error), (8, ''))
        _, error = validar_preguntas('1. Una sola\n*A) a')
        self.assertIn('2 a 8 opciones', error)

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

    def test_expulsa_al_impostor(self):
        j = self.crear(tipo='impostor')
        r = self.cliente(self.ana.user).get(f'{self.base}/{j.pk}/')
        self.assertContains(r, 'aula/juegos/impostor.js')
        self.assertContains(self.cliente(self.ana.user).get(f'{self.base}/'), 'EXPULSA AL IMPOSTOR')

    def test_ocho_opciones_y_juegos_nuevos(self):
        texto = '1. ¿Capital del Tolima?\nA) Neiva\nB) Cali\nC) Tunja\nD) Pasto\nE) Armenia\nF) Pereira\n*G) Ibagué\nH) Bogotá\n'
        for tipo in ('dibujo', 'tesoro', 'unir'):
            j = self.crear(tipo=tipo, preguntas=texto)
            self.assertEqual((j.tipo, len(j.preguntas[0]['opciones'])), (tipo, 8))
            r = self.cliente(self.ana.user).get(f'{self.base}/{j.pk}/')
            self.assertContains(r, f'aula/juegos/{tipo}.js')
            self.assertContains(r, 'jg-completa')          # botón de pantalla completa
        # El juego manda el número original de la opción (G = 6): el servidor la califica bien
        r = self.jugar(self.ana, [{'i': 0, 'opcion': 6}], j)
        self.assertEqual((r['aciertos'], r['total']), (1, 1))
        # Cada juego admite las opciones que le caben: la carretera 6 y el boxeo 2 (los dos guantes)
        antes = JuegoAula.objects.count()
        for tipo in ('carretera', 'boxeo'):
            r = self.profe.post(f'{self.base}/', {'tipo': tipo, 'titulo': 'X', 'preguntas': texto, 'segundos': '15'}, follow=True)
            self.assertContains(r, 'opciones')
        self.assertEqual(JuegoAula.objects.count(), antes)
        j = self.crear(tipo='boxeo', preguntas='1. ¿Capital del Tolima?\nA) Neiva\n*B) Ibagué\n')
        self.assertEqual((j.tipo, len(j.preguntas[0]['opciones'])), ('boxeo', 2))
        r = self.jugar(self.ana, [{'i': 0, 'opcion': 1}], j)
        self.assertEqual((r['aciertos'], r['total']), (1, 1))
        # La página trae el editor con lo que cabe en cada juego
        r = self.profe.get(f'{self.base}/')
        self.assertContains(r, 'aula/juegos/editor.js')
        self.assertContains(r, '"boxeo": 2')
        # El boxeo termina por KO: la nota es sobre lo respondido, y se puede jugar entre dos
        self.assertIn('boxeo', JuegoAula.TERMINAN_SOLOS)
        self.assertContains(self.cliente(self.ana.user).get(f'{self.base}/{j.pk}/?jugadores=2'), 'jugadores: 2')

    def test_animaplano(self):
        # Sin preguntas: la plataforma arma las operaciones de la figura, en orden
        j = self.crear(tipo='animaplano', preguntas='', figura='estrella', operaciones='multi')
        from aula import animaplano
        puntos = [int(next(o['texto'] for o in p['opciones'] if o['correcta'])) for p in j.preguntas]
        self.assertEqual(puntos, animaplano.FIGURAS['estrella'][1][0])
        self.assertIn('×', j.texto_preguntas)
        r = self.cliente(self.ana.user).get(f'{self.base}/{j.pk}/')
        self.assertEqual([p['i'] for p in r.context['preguntas']], list(range(len(puntos))))   # no se revuelven
        # Con preguntas propias: cada respuesta tiene que ser un punto del 1 al 100
        antes = JuegoAula.objects.count()
        self.crear(tipo='animaplano', preguntas='1. 50 + 70 =\n*A) 120\nB) 110\n')
        self.assertEqual(JuegoAula.objects.count(), antes)
        j = self.crear(tipo='animaplano', preguntas='1. 8 × 5 − 8 =\n*A) 32\nB) 33\n2. (nuevo trazo) 7 × 3 =\n*A) 21\nB) 12\n')
        self.assertEqual(len(j.preguntas), 2)
        self.assertEqual(self.cliente(self.ana.user).get(f'{self.base}/practica/animaplano/matematicas/').status_code, 200)
        self.assertContains(self.cliente(self.ana.user).get(f'{self.base}/practica/ovejas/colombia/'), 'aula/juegos/ovejas.js')

    def test_juegos_de_logica(self):
        from aula.views_logica import JUEGOS, niveles
        r = self.cliente(self.ana.user).get(f'/aula/{self.aula.pk}/logica/')
        self.assertContains(r, 'Juegos de lógica')
        for id_, nombre, _, archivo in JUEGOS:
            r = self.cliente(self.ana.user).get(f'/aula/{self.aula.pk}/logica/{id_}/')
            self.assertContains(r, f'aula/logica/{archivo}.js')
            self.assertContains(r, 'lg-datos')
            self.assertTrue(niveles(id_) is not None)
        self.assertEqual(self.cliente(self.ana.user).get(f'/aula/{self.aula.pk}/logica/otro/').status_code, 404)
        # Tablero 36: cada reto tiene su solución y cubre las 35 casillas
        d = niveles('bango')
        for n in d['retos']:
            celdas = [tuple(c) for p in d['soluciones'][str(n)].values() for c in p]
            self.assertEqual(len(set(celdas)), 35)
            self.assertNotIn(((n - 1) // 6, (n - 1) % 6), celdas)

    def test_escape_de_la_selva(self):
        """Escape de la selva: niveles propios 7×7 (no los del Safari), del fácil al difícil, cada uno con solución."""
        import random
        from aula import instrucciones
        from aula.logica_generadores import trancon as T
        from aula.views_logica import niveles
        selva, safari = niveles('selva'), niveles('safari')
        self.assertGreaterEqual(len(selva), 30)
        self.assertFalse({'/'.join(f) for _, f in selva} & {'/'.join(f) for _, f in safari})
        self.assertEqual([m for m, _ in selva], sorted(m for m, _ in selva))
        self.assertGreaterEqual(selva[-1][0], 25)
        for m, filas in random.Random(1).sample(selva, 4):
            self.assertEqual(len(filas), 7)
            self.assertTrue(all(len(f) == 7 for f in filas))
            self.assertEqual(T.resolver(7, T.piezas_de(filas), 3, limite=2000000), m)
        self.assertIn('jaguares', instrucciones.logica('selva', 'trancon'))
        r = self.cliente(self.ana.user).get(f'/aula/{self.aula.pk}/logica/selva/')
        self.assertContains(r, 'Escape de la selva')
        self.assertContains(r, 'Jeep grande · lodo fijo')               # el selector de modo

    def test_selva_jeep_grande(self):
        """Modos con el jeep grande (2×2): hasta 11 animales de 1×2, 5 de 1×3 y 2 charcos de lodo, fijos o móviles."""
        import random
        from collections import Counter
        from aula import instrucciones
        from aula.logica_generadores import trancon as T
        from aula.views_logica import niveles
        for modo, lodo, tipo_lodo in (('selva_fijo', 'PQ', 'fija'), ('selva_movil', 'LM', '4')):
            retos = niveles(modo)
            self.assertGreaterEqual(len(retos), 25)
            self.assertEqual([m for m, _ in retos], sorted(m for m, _ in retos))
            for m, filas in retos:
                letras = Counter(ch for f in filas for ch in f if ch != '.')
                self.assertEqual(letras['x'], 4)                                  # jeep 2×2
                piezas = T.piezas_de(filas)
                self.assertEqual(piezas[0][2:4], (2, 2))
                tam = Counter(max(a, w) for f, c, a, w, t in piezas[1:] if (a, w) != (2, 2))
                self.assertLessEqual(tam[2], 11)
                self.assertLessEqual(tam[3], 5)
                charcos = [p for p in piezas[1:] if p[2:4] == (2, 2)]
                self.assertLessEqual(len(charcos), 2)
                self.assertTrue(all(p[4] == tipo_lodo for p in charcos))
                self.assertFalse(set(letras) - set('x' + lodo + 'abcdefghijknopqr'))
            for m, filas in random.Random(3).sample(retos, 3):
                self.assertEqual(T.resolver(7, T.piezas_de(filas), T.SALIDA_JEEP, limite=3000000), m)
            self.assertIn('2×2', instrucciones.logica(modo, 'trancon'))
        c = self.cliente(self.ana.user)
        menu = c.get(f'/aula/{self.aula.pk}/logica/')
        self.assertContains(menu, 'Modos:')
        self.assertNotContains(menu, 'Modo jeep grande (2×2): 16 especies')   # una sola tarjeta para los tres modos
        self.assertContains(c.get(f'/aula/{self.aula.pk}/logica/selva_movil/'), 'btn-success">Jeep grande · lodo móvil')

    def test_velocidad_de_los_juegos(self):
        j = self.crear(tipo='ovejas', velocidad='lenta')
        self.assertEqual(j.velocidad, 'lenta')
        self.assertContains(self.cliente(self.ana.user).get(f'{self.base}/{j.pk}/'), 'ritmo: 0.6')
        r = self.cliente(self.ana.user).get(f'{self.base}/practica/tiro/matematicas/?velocidad=rapida')
        self.assertContains(r, 'ritmo: 1.3')
        self.assertContains(r, 'Velocidad:')

    def test_boton_instrucciones(self):
        """Cada juego tiene su botón «Instrucciones» y en los menús la explicación va al lado de cada juego."""
        from aula import instrucciones
        from aula.views_logica import JUEGOS as LOGICA
        self.assertTrue(all(len(instrucciones.logica(i, a)) > 40 for i, _, _, a in LOGICA))
        self.assertTrue(all(len(instrucciones.arcade(k)) > 40 for k, _ in JuegoAula.TIPOS))
        c = self.cliente(self.ana.user)
        r = c.get(f'{self.base}/')
        self.assertContains(r, 'gm-ins')
        self.assertContains(r, instrucciones.arcade('boxeo')[:30])
        r = c.get(f'/aula/{self.aula.pk}/logica/')
        self.assertContains(r, 'Saque el jeep')                 # Safari, distinto del Trancón
        self.assertContains(c.get(f'/aula/{self.aula.pk}/logica/kadogemo/'), 'id="lg-instr"')
        r = c.get(f'{self.base}/practica/bandera/matematicas/')
        self.assertContains(r, 'id="jg-instr"')
        self.assertContains(r, 'ponga el dedo en cualquier parte')

    def test_avance_de_logica_en_el_servidor(self):
        """El avance de los juegos de lógica queda en la plataforma y el docente lo ve."""
        from aula.models import ProgresoLogica
        ana = self.cliente(self.ana.user)
        url = f'/aula/{self.aula.pk}/logica/tangram/avance/'
        r = ana.post(url, json.dumps({'total': 16, 'niveles': {'0': {'estrellas': 2, 'movs': 30, 'segundos': 95, 'ayudas': 1},
                                                               '1': {'estrellas': 3, 'movs': 12, 'segundos': 40}}}), content_type='application/json').json()
        self.assertEqual(set(r['niveles']), {'0', '1'})
        # Lo mejor de cada nivel: más estrellas reemplaza; menos estrellas no
        ana.post(url, json.dumps({'niveles': {'0': {'estrellas': 3, 'movs': 20, 'segundos': 60}, '1': {'estrellas': 1, 'segundos': 5}}}), content_type='application/json')
        p = ProgresoLogica.objects.get(aula=self.aula, estudiante=self.ana, juego='tangram')
        self.assertEqual((p.niveles['0']['estrellas'], p.niveles['1']['segundos'], p.total, p.superados), (3, 40, 16, 2))
        # Al volver (en otro equipo) la página trae lo guardado
        r = ana.get(f'/aula/{self.aula.pk}/logica/tangram/')
        self.assertEqual(set(r.context['servidor']), {'0', '1'})
        self.assertContains(r, '/logica/tangram/avance/')
        # El docente no guarda avance; ve el informe
        self.assertTrue(self.profe.post(url, json.dumps({'niveles': {'0': {'estrellas': 3}}}), content_type='application/json').json()['prueba'])
        r = self.profe.get(f'/aula/{self.aula.pk}/logica/informe/')
        fila = next(f for f in r.context['filas'] if f['superados'])
        self.assertEqual((fila['superados'], fila['estrellas']), (2, 6))
        self.assertContains(self.profe.get(f'/aula/{self.aula.pk}/logica/informe/?juego=tangram'), '2 de 16')
        self.assertContains(self.profe.get(f'/aula/{self.aula.pk}/logica/'), 'Avance de los estudiantes')
        self.assertEqual(ana.get(f'/aula/{self.aula.pk}/logica/informe/').status_code, 403)

    def test_analisis_de_preguntas(self):
        """El docente ve qué preguntas se fallan más, la opción equivocada que más escogen y quién necesita refuerzo."""
        j = self.crear(tipo='laberinto')
        # Ana: la primera bien y la segunda mal; Beto: las dos mal con la misma opción equivocada
        bien0 = next(k for k, o in enumerate(j.preguntas[0]['opciones']) if o['correcta'])
        mal0 = next(k for k, o in enumerate(j.preguntas[0]['opciones']) if not o['correcta'])
        mal1 = next(k for k, o in enumerate(j.preguntas[1]['opciones']) if not o['correcta'])
        self.jugar(self.ana, [{'i': 0, 'opcion': bien0}, {'i': 1, 'opcion': mal1}], j)
        self.jugar(self.beto, [{'i': 0, 'opcion': mal0}, {'i': 1, 'opcion': mal1}], j)
        # El segundo intento de Beto no cambia el primero
        self.jugar(self.beto, [{'i': 0, 'opcion': bien0}, {'i': 1, 'opcion': None}], j)
        r = self.profe.get(f'{self.base}/{j.pk}/analisis/')
        ps = {p['n']: p for p in r.context['preguntas']}
        self.assertEqual((ps[1]['bien'], ps[1]['respondieron'], ps[2]['pct']), (1, 2, 0))
        self.assertEqual(ps[2]['errada'][1], 2)
        self.assertEqual([e['nombre'] for e in r.context['refuerzo']][0].split()[0], 'Prueba')
        self.assertEqual(len(r.context['refuerzo']), 2)
        r = self.profe.get(f'{self.base}/{j.pk}/analisis/?intento=ultimo')
        ps = {p['n']: p for p in r.context['preguntas']}
        self.assertEqual((ps[1]['bien'], ps[2]['tiempo']), (2, 1))
        self.assertContains(self.profe.get(f'{self.base}/{j.pk}/'), 'Análisis de preguntas')
        self.assertEqual(self.cliente(self.ana.user).get(f'{self.base}/{j.pk}/analisis/').status_code, 403)

    def test_banco_de_preguntas(self):
        from aula.models import PreguntaBanco
        r = self.profe.post('/aula/banco/', {'accion': 'agregar', 'tema': 'Fracciones', 'grado': '6', 'compartida': 'on',
                                              'preguntas': PREGUNTAS + '\n\n9. Abierta sin opciones'}, follow=True)
        n = PreguntaBanco.objects.filter(propietario=self.u_docente, tema='Fracciones').count()
        self.assertGreaterEqual(n, 2)
        self.assertContains(r, 'no se guardaron')
        # No se repiten
        self.profe.post('/aula/banco/', {'accion': 'agregar', 'tema': 'Fracciones', 'preguntas': PREGUNTAS})
        self.assertEqual(PreguntaBanco.objects.filter(tema='Fracciones').count(), n)
        # El editor las trae por JSON (filtradas por tema)
        j = self.profe.get('/aula/banco/json/?tema=Fracciones').json()
        self.assertEqual((len(j['preguntas']), j['temas']), (n, ['Fracciones']))
        self.profe.post('/aula/banco/json/', {'ids': [j['preguntas'][0]['id']]})
        self.assertEqual(PreguntaBanco.objects.get(pk=j['preguntas'][0]['id']).usos, 1)
        # Al publicar un juego se pueden guardar sus preguntas en el banco
        self.crear(titulo='Repaso de potencias', preguntas='1. ¿2³?\nA) 6\n*B) 8\n', al_banco='on')
        self.assertTrue(PreguntaBanco.objects.filter(tema='Repaso de potencias', texto='¿2³?').exists())
        # Los estudiantes no entran
        self.assertEqual(self.cliente(self.ana.user).get('/aula/banco/').status_code, 403)
        self.assertContains(self.profe.get(f'{self.base}/'), '/aula/banco/json/')

    def test_planilla_de_preguntas_banco_y_editor(self):
        import io
        from django.core.files.uploadedfile import SimpleUploadedFile
        from openpyxl import load_workbook
        from aula.models import PreguntaBanco
        # El banco 6.º–11.º a mi banco (con grado y tema)
        self.profe.post('/aula/banco/', {'accion': 'olimpiada'})
        self.assertEqual(PreguntaBanco.objects.filter(propietario=self.u_docente).count(), 240)
        self.assertTrue(PreguntaBanco.objects.filter(grado=9, tema__startswith='Olimpiada 9.º').exists())
        # Descargar mi banco y subir una planilla
        libro = load_workbook(io.BytesIO(self.profe.get('/aula/banco/planilla/?de=mias').content))
        self.assertGreaterEqual(libro['Preguntas'].max_row, 241)
        libro = load_workbook(io.BytesIO(self.profe.get('/aula/banco/planilla/?de=vacia').content))
        h = libro['Preguntas']
        h.append(['6', '', 'Newton', 'Fracciones', '¿Cuánto es 1/2 + 1/4?', '3/4', '2/6', '1/8', '1', '', '', '', '', 'A'])
        out = io.BytesIO(); libro.save(out)
        self.profe.post('/aula/banco/planilla/', {'archivo': SimpleUploadedFile('p.xlsx', out.getvalue())})
        q = PreguntaBanco.objects.get(texto='¿Cuánto es 1/2 + 1/4?')
        self.assertEqual((q.grado, q.tema, q.competencia), (6, 'Fracciones', 'Pensamiento numérico'))
        # El editor de juegos la lee (sin guardar) y respeta las opciones que caben (boxeo: 2)
        j = self.profe.post('/aula/banco/planilla/?leer=1&max=8', {'archivo': SimpleUploadedFile('p.xlsx', out.getvalue())}).json()
        self.assertIn('*A) 3/4', j['texto'])
        j = self.profe.post('/aula/banco/planilla/?leer=1&max=2', {'archivo': SimpleUploadedFile('p.xlsx', out.getvalue())}).json()
        self.assertEqual((j['texto'], len(j['errores'])), ('', 1))
        self.assertContains(self.profe.get(f'{self.base}/'), '/aula/banco/planilla/')
        # Práctica libre con las preguntas de la olimpiada de cada grado
        r = self.cliente(self.ana.user).get(f'{self.base}/practica/laberinto/olimpiada9/')
        self.assertEqual(r.status_code, 200)
        from aula.planilla_preguntas import banco_olimpiada
        de9 = {p['texto'] for p in banco_olimpiada() if p['grado'] == 9}
        self.assertTrue(all(p['texto'] in de9 for p in r.context['preguntas']))
        self.assertContains(self.cliente(self.ana.user).get(f'{self.base}/'), 'OLIMPIADA DE MATEMÁTICAS 11.º')
