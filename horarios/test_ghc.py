"""Ideas tomadas de GHC: prioridades, «mejor no» fuerte, día libre, horas sin clase del
curso, actividades complementarias, acompañamiento de descansos, revisión de datos,
lo más difícil de ubicar e intercambiar fichas."""
import json
import os
import tempfile
from collections import defaultdict

from django.test import SimpleTestCase

from . import nucleo
from .motor import PESOS
from .proyecto import Proyecto
from .test_motor import datos


def proyecto(D):
    return Proyecto(D.crudo)


class IdeasDeGHC(SimpleTestCase):

    def test_prioridades(self):
        w = nucleo.pesos_de({'pesos': {'hueco': 10, 'prefiere_no': 0, 'raro': 3}})
        self.assertEqual(w['hueco'], PESOS['hueco'] * 2)
        self.assertEqual((w['prefiere_no'], w['evitar']), (0, 0))
        self.assertNotIn('raro', w)

    def test_curso_sin_clase_y_dia_libre(self):
        D = datos()
        p = proyecto(D)
        j = D.jornadas[1]
        clase = [f for f in D.franjas_de(1) if not f['descanso']]
        for f in clase[-2:]:
            p.alternar_celda_curso(1, 5, f['id'])            # el 101 sale temprano el viernes
        p.docente(2)['dia_libre'] = True                     # 16 horas: cabe en 4 días
        alt = p.generar(cuantas=1, segundos=6)[0]
        self.assertEqual(alt['horas_sin_ubicar'], 0)
        self.assertEqual(alt['choques'], [])
        self.assertFalse([s for s in alt['sesiones'] if D.asignaciones[s['asignacion']]['curso'] == 1
                          and s['dia'] == 5 and s['franja'] in {f['id'] for f in clase[-2:]}])
        dias = {s['dia'] for s in alt['sesiones'] if D.asignaciones[s['asignacion']]['docente'] == 2}
        self.assertLess(len(dias), len(j['dias']))
        # A mano tampoco deja poner clase ahí
        s = next(s for s in alt['sesiones'] if D.asignaciones[s['asignacion']]['curso'] == 1)
        self.assertIn('no tiene clase', p.motivo(alt, s['asignacion'], 5, clase[-1]['id']))

    def test_mejor_no_fuerte(self):
        D = datos()
        p = proyecto(D)
        for f in D.franjas_de(1):
            if not f['descanso']:
                for d in (1, 2):
                    p.poner_celda(3, d, f['id'], 'evitar')
        self.assertEqual(p.estado_celda(3, 1, D.franjas_de(1)[0]['id']), 'evitar')
        alt = p.generar(cuantas=1, segundos=3)[0]
        lunes_martes = sum(1 for s in alt['sesiones'] if D.asignaciones[s['asignacion']]['docente'] == 3 and s['dia'] in (1, 2))
        self.assertLessEqual(lunes_martes, 4)              # 20 horas caben en 3 días: casi nada lunes y martes

    def test_actividades_y_descansos(self):
        D = datos()
        p = proyecto(D)
        p.cond['actividades'] = [{'nombre': 'Atención a padres', 'docentes': [], 'horas': 2, 'max_dia': 1}]
        p.cond['acompanamiento'] = {'zonas': [{'nombre': 'Patio', 'cuantos': 2}, {'nombre': 'Tienda', 'cuantos': 1}],
                                    'max_semana': 3}
        alt = p.generar(cuantas=1, segundos=3)[0]
        por_doc = defaultdict(list)
        for x in alt['actividades']:
            por_doc[x['docente']].append(x)
        self.assertEqual(set(por_doc), {1, 2, 3, 4, 5, 6})
        ocupadas = {(D.asignaciones[s['asignacion']]['docente'], s['dia'], s['franja']) for s in alt['sesiones']}
        for did, xs in por_doc.items():
            self.assertEqual(len(xs), 2)
            self.assertEqual(len({x['dia'] for x in xs}), 2)              # máximo una por día
            for x in xs:
                self.assertNotIn((did, x['dia'], x['franja']), ocupadas)
        self.assertEqual(len(alt['acompanamientos']), 5 * 2)              # 5 días × 2 zonas (un descanso)
        carga = defaultdict(int)
        for t in alt['acompanamientos']:
            descanso = D.franjas[t['franja']]
            self.assertTrue(descanso['descanso'])
            for did in t['docentes']:
                carga[did] += 1
        self.assertLessEqual(max(carga.values()), 3)
        self.assertEqual(sum(carga.values()), 15)
        tablas = p.tablas_docente(alt, alt['acompanamientos'][0]['docentes'][0])
        self.assertTrue(any(x.get('descanso') for t in tablas for _, cs in t['filas'] for xs in cs for x in xs))
        tmp = tempfile.mkdtemp()
        p.exportar_excel(alt, os.path.join(tmp, 'h.xlsx'))
        from openpyxl import load_workbook
        self.assertTrue({'Docentes', 'Libres por hora', 'Descansos', 'Actividades'} <=
                        set(load_workbook(os.path.join(tmp, 'h.xlsx')).sheetnames))
        p.exportar_resultado(alt, os.path.join(tmp, 'h.mchr'))
        with open(os.path.join(tmp, 'h.mchr'), encoding='utf-8') as fh:
            inf = json.load(fh)['informe']
        self.assertEqual(len(inf['acompanamientos']), 10)
        self.assertEqual(len(inf['actividades']), 12)

    def test_revision_de_datos(self):
        D = datos()
        cond = nucleo.condiciones_vacias()
        cond['simultaneas'] = [{'nombre': 'Mal', 'asignaciones': [11, 21]}]       # mismo docente (1)
        cond['espacios'] = [{'nombre': 'Laboratorio', 'capacidad': 1}]
        cond['materias'] = {'1': {'espacio': 'Laboratorio'}, '3': {'espacio': 'Laboratorio', 'bloques': '4+1'}}
        cond['docentes'] = {'2': {'no_puede': [f'1-{f["id"]}' for f in D.franjas_de(1) if not f['descanso']]}}
        diag = nucleo.diagnostico(D, cond)
        textos = ' | '.join(t for _, t in diag)
        self.assertIn('mismo docente', textos)
        self.assertIn('Laboratorio: se necesitan 44 horas', textos)
        self.assertIn('no cabe', textos)                         # bloque de 4 con 3 horas seguidas
        self.assertIn('info', {n for n, _ in diag})

    def test_lo_mas_dificil_e_intercambiar(self):
        D = datos()
        cond = nucleo.condiciones_vacias()
        # Docente 1 con muy poco espacio: es lo que más cuesta ubicar
        cond['docentes'] = {'1': {'no_puede': [f'{d}-{f["id"]}' for d in (1, 2) for f in D.franjas_de(1) if not f['descanso']]}}
        r = nucleo.generar(D, cond, segundos=3, semilla=1)
        self.assertTrue(r['dificiles'])
        self.assertEqual(D.asignaciones[r['dificiles'][0]['asignacion']]['docente'], 1)
        p = proyecto(D)
        alt = p.generar(cuantas=1, segundos=2)[0]
        ses = alt['sesiones']
        cambios = 0
        for i, s in enumerate(ses):
            for t in ses:
                if t is not s and D.asignaciones[t['asignacion']]['curso'] == D.asignaciones[s['asignacion']]['curso'] \
                        and t['asignacion'] != s['asignacion']:
                    a1, a2 = s['asignacion'], t['asignacion']
                    d1, f1, d2, f2 = s['dia'], s['franja'], t['dia'], t['franja']
                    if p.intercambiar(alt, i, d2, f2) is None:
                        self.assertEqual((s['asignacion'], s['dia'], s['franja']), (a1, d2, f2))
                        self.assertEqual((t['asignacion'], t['dia'], t['franja']), (a2, d1, f1))
                        self.assertEqual(alt['choques'], [])
                        cambios += 1
                    break
            if cambios:
                break
        self.assertEqual(cambios, 1)

    def test_disponibilidad_de_la_plataforma(self):
        D = datos()
        crudo = dict(D.crudo)
        f = [x for x in D.franjas_de(1) if not x['descanso']]
        crudo['disponibilidad'] = {'2': {'no_puede': [f'1-{f[0]["id"]}', '9-999'], 'prefiere_no': [f'2-{f[1]["id"]}'],
                                         'dia_libre': True, 'nota': 'Martes estudio'}}
        tmp = tempfile.mkdtemp()
        ruta = os.path.join(tmp, 'd.mch')
        with open(ruta, 'w', encoding='utf-8') as fh:
            json.dump(crudo, fh)
        p = Proyecto.abrir_datos(ruta)
        r = p.docente(2)
        self.assertEqual((r['no_puede'], r['prefiere_no'], r['dia_libre'], r['nota']),
                         ([f'1-{f[0]["id"]}'], [f'2-{f[1]["id"]}'], True, 'Martes estudio'))
        self.assertEqual(p.traer_disponibilidad(solo_sin_marcar=True), 0)

    def test_armar_desde_el_docente(self):
        D = datos()
        p = proyecto(D)
        alt = p.en_blanco()
        pend = p.pendientes_docente(alt, 3)
        self.assertEqual({a['curso'] for a, _ in pend}, {1, 2, 3, 4})
        self.assertEqual(sum(n for _, n in pend), 20)
        f = [x['id'] for x in D.franjas_de(1) if not x['descanso']]
        a1 = next(a for a, _ in pend if a['curso'] == 1)
        a2 = next(a for a, _ in pend if a['curso'] == 2)
        self.assertIsNone(p.poner_ficha(alt, a1['id'], 1, f[0]))
        self.assertIsNone(p.poner_ficha(alt, a2['id'], 1, f[1]))
        self.assertIn('ya está en', p.poner_ficha(alt, a2['id'], 1, f[0]))
        self.assertEqual(sum(n for _, n in p.pendientes_docente(alt, 3)), 18)
        # Intercambio entre cursos distintos del mismo docente
        self.assertIsNone(p.intercambiar(alt, 0, 1, f[1]))
        self.assertEqual([(s['asignacion'], s['franja']) for s in alt['sesiones']], [(a1['id'], f[1]), (a2['id'], f[0])])

    def test_septima_y_primera_no_el_mismo_dia(self):
        D = datos(cursos_tarde=(3, 4))          # con 4 cursos en una jornada y 6 docentes no se podría
        f = [x['id'] for x in D.franjas_de(1) if not x['descanso']]      # 6 horas: la «7.ª» es la última
        p = proyecto(D)
        p.cond['excluyente'] = {'activa': True, 'a': 1, 'b': 7, 'obligatoria': True}
        alt = p.generar(cuantas=1, segundos=4)[0]
        self.assertEqual(alt['horas_sin_ubicar'], 0)
        self.assertEqual(alt['choques'], [])
        por = defaultdict(set)
        for s in alt['sesiones']:
            por[(D.asignaciones[s['asignacion']]['docente'], s['dia'])].add(s['franja'])
        for fs in por.values():
            self.assertFalse(f[0] in fs and f[-1] in fs)
        # A mano tampoco deja
        blanco = p.en_blanco()
        a1, a2 = D.asignaciones[13], D.asignaciones[23]                   # docente 3 en dos cursos de la mañana
        self.assertIsNone(p.poner_ficha(blanco, a1['id'], 2, f[-1]))
        self.assertIn('no puede tener también', p.poner_ficha(blanco, a2['id'], 2, f[0]))
        # Docente al que no se le aplica
        p.docente(3)['sin_excluyente'] = True
        self.assertIsNone(p.poner_ficha(blanco, a2['id'], 2, f[0]))
        # Como preferencia: no prohíbe, solo lo evita
        p.cond['excluyente']['obligatoria'] = False
        p.docente(3)['sin_excluyente'] = False
        self.assertEqual(p.revisar(blanco)['choques'], [])

    def test_aviso_si_no_alcanzan_los_docentes(self):
        D = datos()                                  # 4 cursos y 6 docentes en la mañana
        cond = nucleo.condiciones_vacias()
        cond['excluyente'] = {'activa': True, 'a': 1, 'b': 7, 'obligatoria': True}
        self.assertTrue(any('hacen falta al menos 8 docentes' in t for _, t in nucleo.diagnostico(D, cond)))
        cond['excluyente']['obligatoria'] = False
        self.assertFalse(any('hacen falta' in t for _, t in nucleo.diagnostico(D, cond)))

    def test_reuniones_dentro_de_la_permanencia(self):
        D = datos(cursos_tarde=(3, 4))
        f = [x for x in D.franjas_de(1) if not x['descanso']]
        p = proyecto(D)
        p.cond['permanencia_horas'] = 4
        # Reunión fija el martes a la última hora de la mañana para los docentes 1 y 2
        p.cond['reuniones'] = [{'nombre': 'Ciencias', 'docentes': [1, 2], 'jefe': 1, 'modo': 'fija', 'dia': 2,
                                'hora': f[-1]['inicio'], 'dos': False}]
        p.cond['excluyente'] = {'activa': True, 'a': 1, 'b': 7, 'obligatoria': True}
        alt = p.generar(cuantas=1, segundos=4)[0]
        self.assertEqual(alt['choques'], [])
        ini_reu = nucleo.minutos(f[-1]['inicio'])
        fin_reu = nucleo.minutos(f[-1]['fin'])
        for s in alt['sesiones']:
            a = D.asignaciones[s['asignacion']]
            if a['docente'] in (1, 2) and s['dia'] == 2 and D.franjas[s['franja']]['jornada'] == 1:
                ini, fin = D.intervalo(s['franja'])
                self.assertLessEqual(fin_reu - ini, 4 * 60)          # la reunión cuenta en las 4 horas
                self.assertNotEqual(s['franja'], f[0]['id'])         # y en la regla de la 1.ª y la 7.ª
        # A mano: la primera hora del martes no se deja poner al docente 1
        blanco = p.en_blanco()
        self.assertTrue(p.poner_ficha(blanco, 11, 2, f[0]['id']))
