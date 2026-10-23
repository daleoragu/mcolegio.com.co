"""Horarios especiales: día con docentes ausentes, semana A y B, semana de dirección de grado."""
from collections import defaultdict

from django.test import SimpleTestCase

from . import especiales, nucleo
from .proyecto import Proyecto
from .test_motor import datos


def _generado(segundos=6):
    D = datos()
    p = Proyecto(D.crudo)
    alt = p.generar(cuantas=1, segundos=segundos)[0]
    return D, p, alt


class DiaConAusencias(SimpleTestCase):

    def _sin_choques(self, D, alt, dia, plan, ausentes):
        afectados = {c['curso'] for c in plan['cursos']}
        tramos = defaultdict(list)
        for s in alt['sesiones']:
            a = D.asignaciones[s['asignacion']]
            if s['dia'] == dia and a['curso'] not in afectados and a['docente'] not in ausentes:
                tramos[a['docente']].append(D.intervalo(s['franja']))
        for c in plan['cursos']:
            vistas = set()
            for x in c['clases']:
                self.assertNotIn(x['franja'], vistas)            # una clase por hora en el curso
                vistas.add(x['franja'])
                self.assertNotIn(x['docente'], ausentes)
                tramos[x['docente']].append(D.intervalo(x['franja']))
        for did, ts in tramos.items():
            ts.sort()
            for (a1, b1), (a2, b2) in zip(ts, ts[1:]):
                self.assertLessEqual(b1, a2, (did, ts))         # nadie en dos cursos a la vez

    def test_plan_del_dia(self):
        D, p, alt = _generado()
        antes = [dict(s) for s in alt['sesiones']]
        for modo in ('auto', 'temprano', 'tarde'):
            plan = especiales.plan_ausencias(p, alt, 1, [2], modo)
            self.assertEqual({c['curso'] for c in plan['cursos']},
                             {D.asignaciones[s['asignacion']]['curso'] for s in alt['sesiones']
                              if s['dia'] == 1 and D.asignaciones[s['asignacion']]['docente'] == 2})
            self._sin_choques(D, alt, 1, plan, {2})
            for c in plan['cursos']:
                self.assertTrue(c['texto'])
                if c['modo'] == 'temprano':
                    self.assertTrue(c['texto'].startswith('Sale a las'))
                    vacias = [f for f in c['filas'] if f['ahora'].startswith('Sin clase')]
                    self.assertTrue(vacias and c['filas'][-1] in vacias)
                if modo != 'auto':
                    self.assertIn(c['modo'], (modo, 'reemplazos'))
        self.assertEqual(alt['sesiones'], antes)                 # el horario oficial no cambia

    def test_reemplazos_con_umbral(self):
        D, p, alt = _generado()
        carga = especiales.horas_por_docente(p, alt)
        # Con umbral 0 nadie puede reemplazar; con umbral alto, sí
        plan0 = especiales.plan_ausencias(p, alt, 2, [1, 3], 'auto', 0, 0)
        self.assertEqual(plan0['reemplazos'], [])
        plan = especiales.plan_ausencias(p, alt, 2, [1, 3], 'auto', 99, 99)
        self._sin_choques(D, alt, 2, plan, {1, 3})
        for r in plan['reemplazos']:
            self.assertNotIn(r['docente'], (1, 3))
            self.assertIn(r['docente'], carga)
        self.assertEqual(especiales.plan_ausencias(p, alt, 2, [7], 'auto')['cursos'], [])   # sin clases ese día


class SemanaAyB(SimpleTestCase):

    def test_proyecto_de_dos_semanas(self):
        D, p, alt = _generado(4)
        clase = [f for f in D.franjas_de(1) if not f['descanso']]
        p.poner_celda(3, 1, clase[0]['id'], 'no_puede')
        p.cond.setdefault('asignaciones', {})['11'] = {'bloques': '2+2+1+1'}
        q = especiales.dos_semanas(p, alt)
        self.assertEqual(q.datos.jornadas[1]['dias'], list(range(101, 111)))
        self.assertEqual(nucleo.DIAS[101], 'Lunes A')
        self.assertEqual(nucleo.DIAS[110], 'Viernes B')
        self.assertEqual(q.datos.ih(11, q.cond), 12)
        self.assertEqual(q.cond['asignaciones']['11']['bloques'], '2+2+1+1+2+2+1+1')
        self.assertEqual(q.estado_celda(3, 101, clase[0]['id']), 'no_puede')
        self.assertEqual(q.estado_celda(3, 106, clase[0]['id']), 'no_puede')
        self.assertEqual(len(q.alternativas[0]['sesiones']), 2 * len(alt['sesiones']))
        self.assertEqual(q.alternativas[0]['choques'], [])
        prob = nucleo.armar(q.datos, q.cond)
        self.assertEqual(prob.semana_de[101], 0)
        self.assertEqual(prob.semana_de[110], 1)
        nuevo = q.generar(cuantas=1, segundos=8)[0]
        self.assertEqual(nuevo['choques'], [])
        for did, a, b in especiales.balance_semanas(q, nuevo):
            self.assertLessEqual(abs(a - b), 2, (did, a, b))
        # Un proyecto semanal vuelve a los nombres de siempre
        Proyecto(D.crudo)
        self.assertEqual(nucleo.DIAS[101], 'Día 1')


class SemanaDeDireccion(SimpleTestCase):

    def test_hora_de_direccion_y_rotacion(self):
        D, p, alt = _generado()
        for cid in (1, 2, 3, 4):
            p.curso(cid)['director'] = cid                     # el docente 1 dirige el 101, etc.
        n = len(alt['sesiones'])
        nuevo, avisos, resumen = especiales.semana_direccion(p, alt)
        self.assertEqual(avisos, [])
        self.assertEqual(len(nuevo['direccion']), 4)
        self.assertEqual(len(nuevo['sesiones']), n - 4)
        self.assertEqual(len(alt['sesiones']), n)                # el oficial no cambia
        self.assertEqual(nuevo['choques'], [])
        tramos = defaultdict(list)
        for s in nuevo['sesiones']:
            a = D.asignaciones[s['asignacion']]
            tramos[(a['docente'], s['dia'])].append(D.intervalo(s['franja']))
        for x in nuevo['direccion']:
            self.assertNotIn(D.intervalo(x['franja']), tramos[(x['docente'], x['dia'])])
        horas = {did: (a, b) for did, a, b in resumen}
        cedidas = defaultdict(int)
        for x in nuevo['direccion']:
            cedidas[x['docente_cede']] += 1
        for did, (a, b) in horas.items():
            self.assertEqual(b, a - cedidas[did] + (1 if did in (1, 2, 3, 4) else 0))
        primeras = {x['curso']: x['cede'] for x in nuevo['direccion']}
        otro, _, _ = especiales.semana_direccion(p, alt)
        segundas = {x['curso']: x['cede'] for x in otro['direccion']}
        self.assertTrue(all(primeras[c] != segundas[c] for c in primeras), (primeras, segundas))
        # Se ve en las cuadrículas del curso y del director
        t = p.tabla_curso(otro, 1)
        self.assertTrue(any(x.get('titulo') == 'Dirección de grado' for _, cs in t['filas'] for xs in cs for x in xs))

    def test_el_colegio_escoge_la_hora(self):
        D, p, alt = _generado()
        for cid in (1, 2, 3, 4):
            p.curso(cid)['director'] = cid
        f0 = [f for f in D.franjas_de(1) if not f['descanso']][0]['id']
        nuevo, avisos, _ = especiales.semana_direccion(p, alt, 'colegio', 3, f0, guardar_rotacion=False)
        self.assertEqual({(x['dia'], x['franja']) for x in nuevo['direccion']}, {(3, f0)})
        self.assertEqual(nuevo['choques'], [])
        self.assertFalse(p.cond['direccion_grado']['historial'].get('1'))
