"""Condiciones del generador, probadas sin base de datos."""
from collections import defaultdict

from django.test import SimpleTestCase

from . import nucleo

HORAS = [('06:30', '07:25'), ('07:25', '08:20'), ('08:20', '09:15'), ('09:15', '09:45', 'D'),
         ('09:45', '10:40'), ('10:40', '11:35'), ('11:35', '12:30')]
TARDE = [('12:30', '13:25'), ('13:25', '14:20'), ('14:20', '15:15'), ('15:15', '15:45', 'D'),
         ('15:45', '16:40'), ('16:40', '17:35'), ('17:35', '18:30')]


def datos(cursos_tarde=(), sedes=None, materias=None, asignaciones=None):
    fid = [100]

    def franjas(lista):
        out = []
        for i, h in enumerate(lista):
            fid[0] += 1
            out.append({'id': fid[0], 'orden': i, 'inicio': h[0], 'fin': h[1], 'descanso': len(h) > 2, 'etiqueta': ''})
        return out
    cursos = [1, 2, 3, 4]
    d = {'tipo': nucleo.TIPO_DATOS, 'colegio': {'id': 1, 'nombre': 'Prueba'},
         'jornadas': [{'id': 1, 'nombre': 'Mañana', 'dias': [1, 2, 3, 4, 5], 'franjas': franjas(HORAS),
                       'cursos': [c for c in cursos if c not in cursos_tarde]},
                      {'id': 2, 'nombre': 'Tarde', 'dias': [1, 2, 3, 4, 5], 'franjas': franjas(TARDE),
                       'cursos': list(cursos_tarde)}],
         'cursos': [{'id': c, 'nombre': f'{c}0{c}', 'sede': (sedes or {}).get(c, 'Principal')} for c in cursos],
         'docentes': [{'id': i, 'nombre': f'Docente {i}'} for i in range(1, 9)],
         'materias': materias or [{'id': m, 'nombre': f'Materia {m}', 'area': 'Ciencias' if m in (1, 2) else 'Humanas'}
                                  for m in range(1, 7)],
         'asignaciones': asignaciones or [
             {'id': c * 10 + m, 'curso': c, 'materia': m, 'docente': m, 'ih': ih}
             for c in cursos for m, ih in ((1, 6), (2, 4), (3, 5), (4, 5), (5, 4), (6, 4))]}
    return nucleo.Datos(d)


def por_docente_dia(D, sesiones, excluir_asig=()):
    m = defaultdict(list)
    for s in sesiones:
        a = D.asignaciones[s['asignacion']]
        if s['asignacion'] in excluir_asig:
            continue
        ini, fin = D.intervalo(s['franja'])
        m[(a['docente'], s['dia'])].append((ini, fin, D.sede_de_curso(a['curso'])))
    return m


def _no_puede(cond):
    return {int(k): {tuple(int(x) for x in v.split('-')) for v in r.get('no_puede', [])}
            for k, r in cond['docentes'].items()}


class Condiciones(SimpleTestCase):

    def _generar(self, D, cond, seg=3):
        r = nucleo.generar(D, cond, segundos=seg, semilla=5)
        self.assertEqual(nucleo.revisar(D, r['sesiones'], cond), [])
        return r

    def test_bloques_por_patron(self):
        D = datos()
        cond = nucleo.condiciones_vacias()
        cond['materias']['1'] = {'bloques': '2+2+1+1'}      # el docente 1 lo da en 4 cursos
        r = self._generar(D, cond)
        self.assertEqual((r['sin_ubicar'], r['divididas']), ([], []))
        for c in (1, 2, 3, 4):
            seguidas = 0
            for dia in range(1, 6):
                fs = sorted(D.franjas[s['franja']]['orden'] for s in r['sesiones']
                            if s['asignacion'] == c * 10 + 1 and s['dia'] == dia)
                if len(fs) == 2 and fs[1] - fs[0] == 1:
                    seguidas += 1
                    self.assertNotEqual(fs[0], 2)               # la 3.ª y la 4.ª tienen el descanso en medio
            self.assertGreaterEqual(seguidas, 2)

    def test_bloque_imposible_se_parte(self):
        D = datos()
        cond = nucleo.condiciones_vacias()
        cond['materias']['1'] = {'bloques': '2+2+2'}        # 12 bloques y el docente solo tiene 10 posibles
        r = nucleo.generar(D, cond, segundos=3, semilla=1)
        self.assertEqual(r['sin_ubicar'], [])
        self.assertTrue(r['divididas'])

    def test_permanencia_y_horas_extra(self):
        # El docente 1 da en la mañana (cursos 1, 2) y en la tarde (cursos 3, 4).
        D = datos(cursos_tarde=(3, 4))
        cond = nucleo.condiciones_vacias()
        cond['permanencia_horas'] = 8
        cond['asignaciones']['31'] = {'extra': True}            # sus horas en el curso 3 son extra
        r = self._generar(D, cond, 4)
        self.assertEqual(r['sin_ubicar'], [])
        for (doc, dia), tramos in por_docente_dia(D, r['sesiones'], excluir_asig={31}).items():
            self.assertLessEqual(max(b for _, b, _ in tramos) - min(a for a, _, _ in tramos), 480, (doc, dia))

    def test_cambio_de_sede(self):
        D = datos(sedes={1: 'Principal', 2: 'Principal', 3: 'Rural', 4: 'Rural'})
        cond = nucleo.condiciones_vacias()
        cond['desplazamiento'] = 40
        r = self._generar(D, cond, 4)
        for (doc, dia), tramos in por_docente_dia(D, r['sesiones']).items():
            tramos.sort()
            for (a1, b1, s1), (a2, b2, s2) in zip(tramos, tramos[1:]):
                if s1 != s2:
                    self.assertGreaterEqual(a2 - b1, 40)

    def test_espacio_compartido_y_simultaneas(self):
        asig = [{'id': c * 10 + m, 'curso': c, 'materia': m, 'docente': c * 10 + m, 'ih': 3}
                for c in (1, 2, 3, 4) for m in (1, 2, 3)]
        D = datos(asignaciones=asig)
        D.docentes.update({x['docente']: {'id': x['docente'], 'nombre': f'D{x["docente"]}'} for x in asig})
        cond = nucleo.condiciones_vacias()
        cond['espacios'] = [{'nombre': 'Sala de sistemas', 'capacidad': 1}]
        cond['materias']['1'] = {'espacio': 'Sala de sistemas'}
        cond['simultaneas'] = [{'nombre': 'Inglés por niveles', 'asignaciones': [12, 22]}]
        r = self._generar(D, cond)
        self.assertEqual(r['sin_ubicar'], [])
        sala = [(s['dia'], s['franja']) for s in r['sesiones'] if s['asignacion'] % 10 == 1]
        self.assertEqual(len(sala), len(set(sala)))             # nunca dos cursos a la vez en la sala
        a = sorted((s['dia'], s['franja']) for s in r['sesiones'] if s['asignacion'] == 12)
        b = sorted((s['dia'], s['franja']) for s in r['sesiones'] if s['asignacion'] == 22)
        self.assertEqual(a, b)

    def test_maximo_seguidas_y_prefiere_no(self):
        D = datos()
        cond = nucleo.condiciones_vacias()
        cond['docentes']['1'] = {'max_seguidas': 2, 'no_puede': []}
        r = self._generar(D, cond)
        orden = {s['franja']: D.franjas[s['franja']]['orden'] for s in r['sesiones']}
        for dia in range(1, 6):
            fs = sorted(orden[s['franja']] for s in r['sesiones'] if D.asignaciones[s['asignacion']]['docente'] == 1
                        and s['dia'] == dia)
            racha = mejor = 0
            for i, f in enumerate(fs):
                racha = racha + 1 if i and f == fs[i - 1] + 1 and fs[i - 1] != 2 else 1
                mejor = max(mejor, racha)
            self.assertLessEqual(mejor, 2)

    def test_reunion_de_area_con_jefe_en_dos(self):
        D = datos()
        cond = nucleo.condiciones_vacias()
        # El docente 2 no puede nunca los lunes y martes; el 1 (jefe) solo puede martes.
        f_clase = [f['id'] for f in D.franjas_de(1) if not f['descanso']]
        cond['docentes']['1'] = {'no_puede': [f'{d}-{f}' for d in (1, 3, 4, 5) for f in f_clase]}
        cond['docentes']['2'] = {'no_puede': [f'{d}-{f}' for d in (2,) for f in f_clase]}
        cond['reuniones'] = [{'nombre': 'Ciencias', 'docentes': [1, 2, 3], 'jefe': 1, 'dos': True}]
        res, bloqueadas = nucleo.ubicar_reuniones(D, cond, _no_puede(cond))
        r = res[0]
        self.assertEqual(r['dia'], 2)
        self.assertEqual(r['asisten'], [1, 3])
        self.assertEqual(r['faltan'], [2])                     # el jefe no tiene otra hora libre
        cond['docentes']['1'] = {'no_puede': [f'{d}-{f}' for d in (3, 4, 5) for f in f_clase]}
        res, bloqueadas = nucleo.ubicar_reuniones(D, cond, _no_puede(cond))
        r = res[0]
        self.assertEqual((r['dia'], r['asisten'], r['faltan']), (1, [1, 2, 3], []))   # el lunes pueden todos
        gen = nucleo.generar(D, cond, segundos=2, semilla=1)
        self.assertEqual(len(gen['reuniones']), 1)
        hora = (gen['reuniones'][0]['dia'], gen['reuniones'][0]['inicio'])
        for s in gen['sesiones']:
            a = D.asignaciones[s['asignacion']]
            if a['docente'] in gen['reuniones'][0]['asisten']:
                self.assertNotEqual((s['dia'], D.intervalo(s['franja'])[0]), hora)


class EditarAMano(SimpleTestCase):
    """Fichas que se arrastran a la cuadrícula, y completar el resto."""

    def setUp(self):
        from .proyecto import Proyecto
        self.p = Proyecto(datos(sedes={1: 'Principal', 2: 'Principal', 3: 'Rural', 4: 'Rural'}).crudo)
        self.D = self.p.datos
        self.f = [f['id'] for f in self.D.franjas_de(1) if not f['descanso']]

    def test_fichas(self):
        p, alt = self.p, self.p.en_blanco()
        self.assertEqual(dict((a['id'], n) for a, n in p.pendientes(alt, 1))[11], 6)
        self.assertIsNone(p.poner_ficha(alt, 11, 1, self.f[0]))
        self.assertIn('ya tiene', p.poner_ficha(alt, 12, 1, self.f[0]))              # el curso ocupado
        self.assertIn('ya está en', p.poner_ficha(alt, 21, 1, self.f[0]))            # el docente 1 en otro curso
        p.cond['desplazamiento'] = 40
        self.assertIn('No le da tiempo', p.poner_ficha(alt, 31, 1, self.f[1]))       # curso 3 está en la sede Rural
        p.poner_celda(2, 1, self.f[1], 'no_puede')
        self.assertIn('no puede', p.poner_ficha(alt, 12, 1, self.f[1]))
        self.assertEqual(p.siguiente_estado(2, 1, self.f[1]), 'prefiere_no')
        self.assertIsNone(p.poner_ficha(alt, 12, 1, self.f[1]))
        self.assertIn('máximo', (p.poner_ficha(alt, 11, 1, self.f[2]) or '') + (p.poner_ficha(alt, 11, 1, self.f[3]) or ''))
        self.assertIsNone(p.mover_ficha(alt, 0, 2, self.f[0]))
        self.assertTrue(alt['sesiones'][0]['fijada'])
        self.assertFalse(p.alternar_fijada(alt, 0))
        nuevo = p.completar(alt, segundos=2)
        self.assertEqual(nuevo['horas_sin_ubicar'], 0)
        self.assertIn({'asignacion': 12, 'curso': 1, 'dia': 1, 'franja': self.f[1], 'fijada': True}, nuevo['sesiones'])

    def test_reuniones_por_area_y_simultaneas(self):
        p = self.p
        self.assertEqual(p.reuniones_por_area(), 2)
        self.assertEqual(p.reuniones_por_area(), 0)
        self.assertIn('distintos', p.agregar_simultanea('x', [11, 12]))
        self.assertIsNone(p.agregar_simultanea('Inglés', [13, 23]))
        alt = p.generar(cuantas=1, segundos=3)[0]
        self.assertEqual(alt['horas_sin_ubicar'], 0)
        self.assertEqual(len(p.texto_reuniones(alt)), 2)
        self.assertTrue(any(x.get('reunion') for t in p.tablas_docente(alt, 1) for _, celdas in t['filas'] for c in celdas for x in c))
