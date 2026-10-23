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

    def test_colores_al_escoger_y_reemplazar(self):
        D = datos()
        p = proyecto(D)
        alt = p.en_blanco()
        f = [x['id'] for x in D.franjas_de(1) if not x['descanso']]
        self.assertIsNone(p.poner_ficha(alt, 11, 1, f[0], fijar=False))      # curso 1, docente 1
        self.assertIsNone(p.poner_ficha(alt, 12, 1, f[1], fijar=True))       # curso 1, docente 2, fijada
        mapa = p.mapa_destinos(alt, 13)                                        # curso 1, docente 3
        self.assertEqual(mapa[(1, f[0])], 'ocupado')                           # amarillo: se puede reemplazar
        self.assertEqual(mapa[(1, f[1])], 'imposible')                         # rojo: está fijada
        self.assertEqual(mapa[(1, f[2])], 'libre')
        estado, texto, _ = p.destino(alt, 13, 1, f[1])
        self.assertIn('fijada', texto)
        # Ocupado por el mismo docente en otro curso también es amarillo
        self.assertEqual(p.mapa_destinos(alt, 21)[(1, f[0])], 'ocupado')    # curso 2, docente 1
        self.assertIsNone(p.reemplazar(alt, 13, 1, f[0], fijar=False))
        self.assertEqual(sorted(s['asignacion'] for s in alt['sesiones']), [12, 13])
        self.assertEqual(dict((a['id'], n) for a, n in p.pendientes(alt, 1))[11], 6)
        self.assertIn('fijada', p.reemplazar(alt, 11, 1, f[1]))

    def test_prioridad_a_los_bloques(self):
        D = datos(cursos_tarde=(3, 4))
        cond = nucleo.condiciones_vacias()
        self.assertIsNone(nucleo.bloques_por_defecto(cond, 4))
        cond['bloques_general'] = {'activa': True, 'desde': 2}
        self.assertEqual(nucleo.bloques_por_defecto(cond, 5), [2, 2, 1])
        self.assertIsNone(nucleo.bloques_por_defecto(cond, 1))
        cond['materias'] = {'6': {'bloques': '1+1+1+1'}}            # esta materia queda por fuera
        r = nucleo.generar(D, cond, segundos=4, semilla=3)
        self.assertEqual(r['sin_ubicar'], [])
        self.assertEqual(nucleo.revisar(D, r['sesiones'], cond), [])
        seguidas = sueltas = 0
        por = defaultdict(set)
        for s in r['sesiones']:
            a = D.asignaciones[s['asignacion']]
            if a['materia'] != 6:
                por[(a['curso'], a['materia'], s['dia'])].add(s['franja'])
        sig = {}
        for j in D.jornadas:
            fs = D.franjas_de(j)
            for x, y in zip(fs, fs[1:]):
                if not x['descanso'] and not y['descanso']:
                    sig[x['id']] = y['id']
        for fs in por.values():
            if len(fs) >= 2:
                if all(sig.get(f) in fs or any(sig.get(g) == f for g in fs) for f in fs):
                    seguidas += 1
                else:
                    sueltas += 1
        self.assertGreater(seguidas, 20)
        self.assertLessEqual(sueltas, 2)

    def test_bloque_no_cae_en_hora_sin_clase_del_curso(self):
        D = datos(cursos_tarde=(3, 4))
        p = proyecto(D)
        f = [x['id'] for x in D.franjas_de(1) if not x['descanso']]
        for dia in range(1, 6):
            p.alternar_celda_curso(1, dia, f[-1])          # el 101 nunca tiene la última hora
        p.cond['bloques_general'] = {'activa': True, 'desde': 2}
        for semilla in range(3):
            r = nucleo.generar(D, p.cond, segundos=2, semilla=semilla)
            self.assertFalse([s for s in r['sesiones'] if s['curso'] == 1 and s['franja'] == f[-1]])

    def test_bloques_en_cualquier_orden(self):
        self.assertEqual(nucleo.restar_corridas([2, 1], [1]), [2])
        self.assertEqual(nucleo.restar_corridas([2, 1], [2]), [1])
        self.assertEqual(nucleo.restar_corridas([1, 2], [1]), [2])         # el orden escrito no importa
        self.assertEqual(nucleo.restar_corridas([2, 2, 1], [1, 1]), [2, 1])  # dos sueltas parten un bloque
        self.assertEqual(nucleo.bloques_automaticos(5), '2+2+1')
        self.assertEqual(nucleo.bloques_automaticos(1), '')
        D = datos(cursos_tarde=(3, 4))
        f = [x['id'] for x in D.franjas_de(1) if not x['descanso']]
        cond = nucleo.condiciones_vacias()
        cond['ih'] = {'15': 3}
        cond['asignaciones'] = {'15': {'bloques': '1+2'}}
        # Fijo primero la hora suelta: lo que falta es el bloque de 2 (no dos sueltas)
        cond['fijas'] = [{'asignacion': 15, 'dia': 1, 'franja': f[0]}]
        p = nucleo.armar(D, cond)
        self.assertEqual(sorted(u['largo'] for u in p.unidades if u['asig'] == 15), [2])
        # Fijo primero el bloque de 2: falta la suelta
        cond['fijas'] = [{'asignacion': 15, 'dia': 2, 'franja': f[0]}, {'asignacion': 15, 'dia': 2, 'franja': f[1]}]
        p = nucleo.armar(D, cond)
        self.assertEqual(sorted(u['largo'] for u in p.unidades if u['asig'] == 15), [1])
        r = nucleo.generar(D, cond, segundos=2, semilla=1)
        self.assertEqual(r['sin_ubicar'], [])

    def test_fichas_de_bloque_a_mano_y_boton(self):
        D = datos(cursos_tarde=(3, 4))
        f = [x['id'] for x in D.franjas_de(1) if not x['descanso']]
        p = proyecto(D)
        self.assertEqual(p.dividir_en_bloques(), len(D.asignaciones))     # todas tienen 4 horas o más
        self.assertEqual(p.asig(13)['bloques'], '2+2+1')                  # 5 horas
        alt = p.en_blanco()
        self.assertEqual(p.piezas_pendientes(alt, 13), [2, 2, 1])
        self.assertIsNone(p.poner_ficha(alt, 13, 1, f[3], fijar=False))   # primero la suelta
        self.assertEqual(p.piezas_pendientes(alt, 13), [2, 2])
        self.assertIn('no cabe', p.destino_bloque(alt, 13, 2, f[2], 2)[1])  # 3.ª hora + descanso
        self.assertEqual(p.mapa_destinos(alt, 13, largo=2)[(2, f[0])], 'libre')
        self.assertIsNone(p.poner_bloque(alt, 13, 2, f[0], 2, fijar=False))
        self.assertEqual(p.piezas_pendientes(alt, 13), [2])
        self.assertEqual(sorted(s['franja'] for s in alt['sesiones'] if s['dia'] == 2), [f[0], f[1]])
        # Un bloque sobre una hora ocupada (que no está fijada) es amarillo y se puede reemplazar
        self.assertIsNone(p.poner_ficha(alt, 23, 3, f[1], fijar=False))
        self.assertEqual(p.destino_bloque(alt, 13, 3, f[0], 2)[0], 'ocupado')
        self.assertEqual(p.quitar_bloques(), len(D.asignaciones))

    def test_bloque_partido_por_el_descanso(self):
        D = datos(cursos_tarde=(3, 4))
        f = [x['id'] for x in D.franjas_de(1) if not x['descanso']]       # el descanso va entre f[2] y f[3]
        p = proyecto(D)
        p.cond['asignaciones'] = {'13': {'bloques': '2+2+1'}}
        alt = p.en_blanco()
        self.assertIsNone(p.celdas_bloque(f[2], 2))                         # sin permiso, no cruza el descanso
        p.cond['bloque_descanso'] = True
        self.assertEqual(p.celdas_bloque(f[2], 2), [f[2], f[3]])
        self.assertIsNone(p.poner_bloque(alt, 13, 1, f[2], 2, fijar=False))
        self.assertEqual(p.piezas_pendientes(alt, 13), [2, 1])               # cuenta como bloque
        nucleo_p = nucleo.armar(D, p.cond)
        self.assertEqual(nucleo_p.siguiente_bloque[f[2]], f[3])
        self.assertNotIn(f[2], nucleo_p.siguiente)                           # las «horas seguidas» del docente no cruzan
        p.cond['bloque_descanso'] = False
        self.assertNotIn(f[2], nucleo.armar(D, p.cond).siguiente_bloque)

    def test_multigrado_escuela_nueva(self):
        # Un docente (1) da Matemáticas a 101 y 202 a la vez, en la misma aula
        materias = [{'id': 1, 'nombre': 'Matemáticas', 'area': 'Matemáticas'}, {'id': 2, 'nombre': 'Lenguaje', 'area': 'Humanas'}]
        asig = [{'id': 11, 'curso': 1, 'materia': 1, 'docente': 1, 'ih': 5},
                {'id': 21, 'curso': 2, 'materia': 1, 'docente': 1, 'ih': 5},
                {'id': 12, 'curso': 1, 'materia': 2, 'docente': 1, 'ih': 5},
                {'id': 22, 'curso': 2, 'materia': 2, 'docente': 1, 'ih': 5}]
        D = datos(materias=materias, asignaciones=asig)
        p = proyecto(D)
        cond = nucleo.condiciones_vacias()
        self.assertIsNone(p.agregar_multigrado('Sede rural', [1, 2]))
        self.assertIn('ya está', p.agregar_multigrado('Otro', [2, 3]))
        cond = p.cond
        # Con el grupo, el docente tiene 10 horas (no 20): cabe
        self.assertFalse([t for n, t in nucleo.diagnostico(D, cond) if n == 'error' and 'Docente 1' in t])
        r = nucleo.generar(D, cond, segundos=2, semilla=1)
        self.assertEqual(r['sin_ubicar'], [])
        self.assertEqual(nucleo.revisar(D, r['sesiones'], cond), [])
        self.assertTrue(nucleo.revisar(D, r['sesiones']))                     # sin el grupo serían choques
        self.assertEqual(nucleo.revisar(D, r['sesiones'], juntos=[[1, 2]]), [])   # como lo revisa la plataforma
        por = defaultdict(set)
        for s in r['sesiones']:
            por[s['asignacion']].add((s['dia'], s['franja']))
        self.assertEqual(por[11], por[21])
        # A mano: poner una ficha pone la del otro curso a la misma hora; quitarla las quita juntas
        alt = p.en_blanco()
        f = [x['id'] for x in D.franjas_de(1) if not x['descanso']]
        self.assertIsNone(p.poner_ficha(alt, 11, 1, f[0], fijar=False))
        self.assertEqual(sorted(s['asignacion'] for s in alt['sesiones']), [11, 21])
        self.assertIsNone(p.mover_ficha(alt, 0, 2, f[1]))
        self.assertEqual({(s['dia'], s['franja']) for s in alt['sesiones']}, {(2, f[1])})
        p.quitar_ficha(alt, 0)
        self.assertEqual(alt['sesiones'], [])

    def test_horas_extra_escogidas_y_permanencia_mayor(self):
        D = datos(cursos_tarde=(3, 4))
        cond = nucleo.condiciones_vacias()
        self.assertEqual(nucleo.horas_extra({'asignaciones': {'13': {'extra': True}}}, 13, 5), 5)   # lo de antes
        cond['asignaciones'] = {'13': {'extra_horas': 2}}
        self.assertEqual(nucleo.horas_extra(cond, 13, 5), 2)
        p = nucleo.armar(D, cond)
        extra = sum(u['largo'] for u in p.unidades if u['asig'] == 13 and u['extra'])
        self.assertEqual(extra, 2)
        # El docente 3 con permanencia de 5 h + hasta 2 h más por sus horas extra
        D = datos()
        cond['docentes'] = {'3': {'permanencia': 5}}
        cond['permanencia_extra'] = 2
        p = nucleo.armar(D, cond)
        self.assertEqual(p.permanencia_extra, {3: 120})
        r = nucleo.generar(D, cond, segundos=4, semilla=2)
        self.assertEqual(r['sin_ubicar'], [])
        por = defaultdict(list)
        for s in r['sesiones']:
            if D.asignaciones[s['asignacion']]['docente'] == 3:
                por[s['dia']].append(D.intervalo(s['franja']))
        for tr in por.values():
            self.assertLessEqual(max(b for _, b in tr) - min(a for a, _ in tr), 7 * 60)
        # En la app: el resumen del docente separa las extra
        pr = proyecto(D)
        pr.cond['asignaciones'] = {'13': {'extra_horas': 2}}
        base, ext, _ = pr.resumen_docente(3)
        self.assertEqual(ext, 2)

    def test_dias_largos_segun_horas_extra(self):
        D = datos(cursos_tarde=(3, 4))
        f = [x['id'] for x in D.franjas_de(1) if not x['descanso']]
        cond = nucleo.condiciones_vacias()
        cond['excluyente'] = {'activa': True, 'a': 1, 'b': 7, 'obligatoria': True}
        cond['asignaciones'] = {'13': {'extra_horas': 2}}           # docente 3: 2 horas extra -> 2 días largos
        p = nucleo.armar(D, cond)
        self.assertEqual(p.dias_largos_max, {3: 2})
        r = nucleo.generar(D, cond, segundos=3, semilla=4)
        self.assertEqual(r['sin_ubicar'], [])
        largos = defaultdict(set)
        for s in r['sesiones']:
            a = D.asignaciones[s['asignacion']]
            if s['franja'] in (f[0], f[-1]):
                largos[(a['docente'], s['dia'])].add(s['franja'])
        dias_con_las_dos = defaultdict(int)
        for (doc, dia), fs in largos.items():
            if len(fs) == 2:
                dias_con_las_dos[doc] += 1
        self.assertLessEqual(dias_con_las_dos.get(3, 0), 2)
        self.assertFalse({d for d in dias_con_las_dos if d != 3})            # los demás, ninguno
        # A mano: con 1 hora extra, el segundo día largo no se deja
        pr = proyecto(D)
        pr.cond['excluyente'] = {'activa': True, 'a': 1, 'b': 7, 'obligatoria': True}
        pr.cond['asignaciones'] = {'13': {'extra_horas': 1}}
        alt = pr.en_blanco()
        self.assertIsNone(pr.poner_ficha(alt, 13, 1, f[0], fijar=False))
        self.assertIsNone(pr.poner_ficha(alt, 23, 1, f[-1], fijar=False))     # primer día largo: sí
        self.assertIsNone(pr.poner_ficha(alt, 13, 2, f[0], fijar=False))
        self.assertIn('día(s) largo', pr.poner_ficha(alt, 23, 2, f[-1], fijar=False))

    def test_asistente_cuando_faltan_horas(self):
        D = datos()
        p = proyecto(D)
        for f in D.franjas_de(1):
            if not f['descanso']:
                for d in (1, 2, 3):
                    p.poner_celda(3, d, f['id'], 'no_puede')     # 20 horas en 2 días: no caben
        p.docente(3)['dia_libre'] = True
        alt = p.generar(cuantas=1, segundos=3)[0]
        self.assertGreater(alt['horas_sin_ubicar'], 0)
        p.cond['permanencia_horas'] = 5
        sug = p.sugerencias(alt)
        p.cond['permanencia_horas'] = 0
        claves = [s['clave'] for s in sug]
        self.assertIn('nopuede-3', claves)
        self.assertIn('dialibre-3', claves)
        self.assertIn('perm-3', claves)
        self.assertEqual(len(claves), len(set(claves)))
        self.assertTrue(p.CONSEJOS)
        for s in sug:
            if s['clave'] in ('nopuede-3', 'dialibre-3', 'perm-3'):
                p.aplicar_sugerencia(s)
        self.assertEqual(p.docente(3)['no_puede'], [])
        self.assertTrue(p.docente(3)['prefiere_no'])
        self.assertFalse(p.docente(3)['dia_libre'])
        self.assertEqual(p.docente(3)['permanencia'], 6)
        alt = p.generar(cuantas=1, segundos=4)[0]
        self.assertEqual(alt['horas_sin_ubicar'], 0)
        self.assertEqual(p.sugerencias(alt), [])

    def test_detener_parar_solo_y_en_vivo(self):
        import time as _t
        D = datos()
        p = proyecto(D)
        vistos = []
        t0 = _t.monotonic()
        alt = p.generar(cuantas=2, segundos=40, vivo=lambda ses, nombre: vistos.append((len(ses), nombre)),
                        parar=lambda: len(vistos) >= 3)
        self.assertLess(_t.monotonic() - t0, 15)
        self.assertEqual(len(alt), 1)                      # al detener no sigue con la segunda alternativa
        self.assertTrue(alt[0]['detenido'])
        self.assertTrue(vistos and vistos[0][1] == 'Alternativa 1')
        prov = p.en_vivo([dict(s) for s in alt[0]['sesiones']], 'Alternativa 1')
        self.assertTrue(prov['vivo'] and prov['nombre'].startswith('⏳'))
        self.assertEqual(prov['horas_sin_ubicar'], alt[0]['horas_sin_ubicar'])
        # Con mucho tiempo, termina solo cuando ya no mejora
        t0 = _t.monotonic()
        r = nucleo.generar(D, nucleo.condiciones_vacias(), segundos=300, semilla=3)
        self.assertLess(_t.monotonic() - t0, 250)                 # de 300 s, para antes
        self.assertEqual(r['sin_ubicar'], [])
        self.assertFalse(r['detenido'])

    def test_dias_largos_compensados_en_la_semana(self):
        D = datos()
        sin, con = [], []
        for activa, lista in ((False, sin), (True, con)):
            p = proyecto(D)
            p.cond['permanencia_horas'] = 5                   # con 5 h no caben todas las clases de la semana
            p.cond['compensar'] = {'activa': activa, 'max': 1}
            alt = p.generar(cuantas=1, segundos=10)[0]
            self.assertEqual(alt['choques'], [])
            lista.append((alt['horas_sin_ubicar'], p, alt))
        self.assertLess(con[0][0], sin[0][0])
        _, p, alt = con[0]
        largos = 0
        for did in range(1, 7):
            total, tope, perfil = p.semana_docente(alt, did)
            self.assertEqual(tope, 5 * 60 * 5)                # 5 h × 5 días = 25 h
            self.assertLessEqual(total, tope, (did, perfil))
            self.assertTrue(all(a <= 6 * 60 for a, _ in perfil.values()))       # máximo 5 + 1 horas por día
            largos += sum(1 for a, _ in perfil.values() if a > 5 * 60)
        self.assertGreater(largos, 0)
        self.assertTrue(p.texto_compensacion(alt))
        # A mano: días largos (1.ª y última) hasta que la semana pase de 25 h
        p.cond['compensar']['activa'] = True
        blanco = p.en_blanco()
        clase = [f for f in D.franjas_de(1) if not f['descanso']]
        pares = [(11, 21), (31, 41), (11, 21), (31, 41), (11, 21)]
        for dia, (x, y) in enumerate(pares, start=1):
            self.assertIsNone(p.poner_ficha(blanco, x, dia, clase[0]['id']))
            self.assertIsNone(p.poner_ficha(blanco, y, dia, clase[-1]['id']))
            se_pasa = [c for c in blanco['choques'] if 'la semana suma' in c]
            self.assertEqual(bool(se_pasa), dia == 5, (dia, blanco['choques']))   # 4 × 6 h = 24 ≤ 25; 5 × 6 = 30
        # Sin compensar, la permanencia es un tope fijo
        p.cond['compensar']['activa'] = False
        otro = p.en_blanco()
        self.assertIsNone(p.poner_ficha(otro, 11, 1, clase[0]['id']))
        self.assertIn('permanencia', p.motivo(otro, 21, 1, clase[-1]['id']))

    def test_docente_que_viaja_compensa_lunes_o_viernes(self):
        D = datos()
        cond = nucleo.condiciones_vacias()
        cond['permanencia_horas'] = 5
        cond['compensar'] = {'activa': True, 'max': 1}
        p = nucleo.armar(D, cond)
        from .motor import Estado
        est = Estado(p)
        self.assertEqual(est.compensacion_faltante(1), 0)       # no viaja → no cuenta
        cond['docentes']['1'] = {'viaja': True}
        p = nucleo.armar(D, cond)
        self.assertIn(1, p.viajan)
        est = Estado(p)
        for u in p.unidades:
            est.u[u['id']] = u
        uni = [u for u in p.unidades if u['partes'][0]['docente'] == 1 and u['largo'] == 1]
        clase = sorted((f for f in p.franjas if p.franjas[f][0] == 1), key=lambda f: p.indice[f])
        # Martes: primera y última (día largo de 6 h, permanencia 5) → 1 hora para compensar
        est.poner(uni[0], 2, clase[0])
        est.poner(uni[1], 2, clase[-1])
        # Lunes desde la primera y viernes hasta la última: no compensa ahí
        est.poner(uni[2], 1, clase[0])
        est.poner(uni[3], 5, clase[-1])
        self.assertEqual(est.compensacion_faltante(1), 1)
        malo = est.costo_docente_semana(1)
        self.assertGreater(malo, 0)
        # El lunes entra a la segunda hora: compensado
        est.quitar(uni[2]['id'])
        est.poner(uni[2], 1, clase[1])
        self.assertEqual(est.compensacion_faltante(1), 0)
        self.assertEqual(est.costo_docente_semana(1), 0)
        # Generando: el docente que viaja queda compensado el lunes o el viernes
        pr = proyecto(D)
        pr.cond.update({'permanencia_horas': 5, 'compensar': {'activa': True, 'max': 1}})
        pr.docente(1)['viaja'] = True
        alt = pr.generar(cuantas=1, segundos=10)[0]
        self.assertEqual(alt['choques'], [])
        txt = pr.texto_viajan(alt)
        if txt:
            self.assertNotIn('sin compensar', txt[0], txt)

    def test_bloquear_horas_por_area(self):
        D = datos()                                    # materias 1 y 2 son de Ciencias
        p = proyecto(D)
        clase = [f for f in D.franjas_de(1) if not f['descanso']]
        for dia in (1, 2, 3, 4, 5):
            self.assertEqual(p.siguiente_estado_area('Ciencias', dia, clase[0]['id']), 'no_puede')
        self.assertEqual(p.siguiente_estado_area('Ciencias', 1, clase[1]['id']), 'no_puede')
        self.assertEqual(p.siguiente_estado_area('Ciencias', 1, clase[1]['id']), 'prefiere_no')
        self.assertEqual(p.estado_celda_area('Ciencias', 1, clase[1]['id']), 'prefiere_no')
        self.assertEqual([j['id'] for j in p.jornadas_de_area('Ciencias')], [1])
        alt = p.generar(cuantas=1, segundos=6)[0]
        self.assertEqual(alt['choques'], [])
        self.assertEqual(alt['horas_sin_ubicar'], 0)
        primeras = [s for s in alt['sesiones'] if s['franja'] == clase[0]['id']]
        self.assertTrue(primeras)
        self.assertFalse([s for s in primeras if D.asignaciones[s['asignacion']]['materia'] in (1, 2)])
        # A mano tampoco deja (y la sugerencia del asistente lo puede quitar)
        blanco = p.en_blanco()
        self.assertIn('Ciencias', p.motivo(blanco, 11, 1, clase[0]['id']))
        self.assertIsNone(p.motivo(blanco, 13, 1, clase[0]['id']))       # materia 3 es de otra área
        p.aplicar_sugerencia({'tipo': 'area_sin', 'datos': {'area': 'Ciencias'}})
        self.assertIsNone(p.motivo(blanco, 11, 1, clase[0]['id']))

    def test_docente_que_viaja_escoge_lunes_o_viernes(self):
        from .motor import Estado
        D = datos()
        cond = nucleo.condiciones_vacias()
        cond['permanencia_horas'] = 5
        cond['compensar'] = {'activa': True, 'max': 1}
        clase = None
        for modo, esperado in (('lunes', 1), ('viernes', 0), ('ambos', 0), (True, 0)):
            cond['docentes']['1'] = {'viaja': modo}
            p = nucleo.armar(D, cond)
            self.assertEqual(p.viajan[1], nucleo.modo_viaja(modo))
            est = Estado(p)
            for u in p.unidades:
                est.u[u['id']] = u
            uni = [u for u in p.unidades if u['partes'][0]['docente'] == 1 and u['largo'] == 1]
            clase = sorted((f for f in p.franjas if p.franjas[f][0] == 1), key=lambda f: p.indice[f])
            est.poner(uni[0], 2, clase[0])
            est.poner(uni[1], 2, clase[-1])            # martes largo: 1 hora por compensar
            est.poner(uni[2], 1, clase[0])             # lunes desde la primera
            est.poner(uni[3], 5, clase[-2])            # viernes sale antes de la última
            self.assertEqual(est.compensacion_faltante(1), esperado, modo)

    def test_reunion_en_el_horario_armado(self):
        D = datos()                                    # Ciencias: docentes 1 y 2
        p = proyecto(D)
        alt = p.generar(cuantas=1, segundos=4)[0]      # sin reuniones: el horario no les dejó hora libre a propósito
        self.assertEqual(p.reuniones_por_area(), 2)
        r = next(x for x in p.cond['reuniones'] if x['area'] == 'Ciencias')
        r['jefe'] = 1
        prop = p.reuniones_en_horario(alt)
        x = next(x for x in prop if x['nombre'] == r['nombre'])
        self.assertIsNotNone(x['dia'])
        self.assertNotIn(1, x['no'])                   # el jefe siempre puede
        self.assertEqual(set(x['libres']) | set(x['mover']) | set(x['no']), {1, 2})
        self.assertTrue(p.texto_reuniones_en_horario(prop, alt))
        antes = len(alt['sesiones'])
        movidas = sum(len(k) for y in prop for k in y['mover'].values())
        n = p.acomodar_reuniones(alt, prop)
        self.assertEqual(n, movidas)
        self.assertEqual(len(alt['sesiones']), antes - n)
        self.assertEqual(r['modo'], 'fija')
        self.assertEqual(int(r['dia']), x['dia'])
        reu = next(y for y in alt['reuniones'] if y['nombre'] == r['nombre'])
        self.assertEqual((reu['dia'], reu['inicio']), (x['dia'], x['inicio']))
        # Completar ubica de nuevo lo que salió, sin pisar la reunión
        nuevo = p.completar(alt, segundos=4)
        self.assertLessEqual(nuevo['horas_sin_ubicar'], n)   # con todo lo demás quieto, casi siempre caben todas
        self.assertEqual(nuevo['choques'], [])
        ocupadas = nucleo.franjas_de_reuniones(D, nuevo['reuniones'])
        for s in nuevo['sesiones']:
            did = D.asignaciones[s['asignacion']]['docente']
            self.assertNotIn(s['franja'], ocupadas.get((did, s['dia']), []))

    def test_reuniones_todas_a_la_misma_hora(self):
        D = datos()
        p = proyecto(D)
        p.reuniones_por_area()
        for r in p.cond['reuniones']:
            r['jefe'] = r['docentes'][0]
        p.cond['reuniones_juntas'] = True
        reus = p.ver_reuniones()
        self.assertTrue(all(r['ubicada'] for r in reus))
        self.assertEqual(len({(r['dia'], r['inicio']) for r in reus}), 1)
        alt = p.generar(cuantas=1, segundos=4)[0]
        self.assertEqual(alt['choques'], [])
        self.assertEqual(len({(r['dia'], r['inicio']) for r in alt['reuniones']}), 1)
        # En un horario ya armado, también buscan una sola hora para todas
        p.cond['reuniones_juntas'] = False
        alt2 = p.generar(cuantas=1, segundos=4)[0]
        p.cond['reuniones_juntas'] = True
        prop = p.reuniones_en_horario(alt2)
        self.assertEqual(len({(x['dia'], x['inicio']) for x in prop}), 1)

    def test_completar_no_deja_todo_fijado_y_soltar_varias(self):
        D = datos()
        p = proyecto(D)
        alt = p.generar(cuantas=1, segundos=3)[0]
        alt['sesiones'][0]['fijada'] = True
        quitada = alt['sesiones'].pop(5)
        nuevo = p.completar(alt, segundos=3)
        self.assertEqual(nuevo['horas_sin_ubicar'], 0)
        self.assertEqual(sum(1 for s in nuevo['sesiones'] if s.get('fijada')), 1)    # solo la que estaba fijada
        self.assertTrue(quitada)
        self.assertEqual(p.fijar_varias(nuevo, {1, 2, 3}, True), 3)
        self.assertEqual(p.fijar_varias(nuevo, None, False), 4)
        self.assertFalse(any(s.get('fijada') for s in nuevo['sesiones']))

    def test_pdf_por_curso_y_por_docente(self):
        import tempfile
        import zipfile
        from . import impresion
        D = datos()
        p = proyecto(D)
        alt = p.generar(cuantas=1, segundos=3)[0]
        tmp = tempfile.mkdtemp()
        n = impresion.zip_individuales(p, alt, os.path.join(tmp, 'h.zip'))
        nombres = zipfile.ZipFile(os.path.join(tmp, 'h.zip')).namelist()
        self.assertEqual(n, 4 + 6)
        self.assertIn('Cursos/Curso 101.pdf', nombres)
        self.assertIn('Docentes/Docente 1.pdf', nombres)
        nc, nd = impresion.todo_junto(p, alt, os.path.join(tmp, 'c.pdf'), os.path.join(tmp, 'd.pdf'))
        self.assertEqual((nc, nd), (4, 6))
        with open(os.path.join(tmp, 'c.pdf'), 'rb') as f:
            self.assertTrue(f.read(5) == b'%PDF-')

    def test_cada_docente_en_una_sola_reunion(self):
        # El docente 1 dicta Ciencias (materia 1, 4 cursos × 6 h) y también una Humanas (materia 3) en un curso
        asign = [{'id': c * 10 + m, 'curso': c, 'materia': m, 'docente': m, 'ih': ih}
                 for c in (1, 2, 3, 4) for m, ih in ((1, 6), (2, 4), (3, 5), (4, 5), (5, 4), (6, 4))]
        asign[2]['docente'] = 1                       # curso 1, materia 3 (Humanas) → docente 1
        D = datos(asignaciones=asign)
        p = proyecto(D)
        self.assertEqual(p.area_principal(1), 'Ciencias')
        self.assertEqual(p.areas_de_docente(1), ['Ciencias', 'Humanas'])
        self.assertEqual(p.reuniones_por_area(), 2)
        todos = [d for r in p.cond['reuniones'] for d in r['docentes']]
        self.assertEqual(len(todos), len(set(todos)))                  # nadie está en dos reuniones
        cien = next(i for i, r in enumerate(p.cond['reuniones']) if r['area'] == 'Ciencias')
        hum = 1 - cien
        self.assertEqual(p.reunion_de(1), cien)
        self.assertFalse(p.cond['reuniones'][cien]['dos'])           # los que no pueden reciben el acta
        # Se puede pasar a otra reunión (y deja de ser jefe de la anterior)
        p.cond['reuniones'][cien]['jefe'] = 1
        p.poner_en_reunion(1, hum)
        self.assertEqual(p.reunion_de(1), hum)
        self.assertIsNone(p.cond['reuniones'][cien]['jefe'])
        self.assertNotIn(1, p.cond['reuniones'][cien]['docentes'])
        p.poner_en_reunion(1, None)
        self.assertIsNone(p.reunion_de(1))
        # Repetidos de versiones anteriores: se quedan en la primera
        p.cond['reuniones'][0]['docentes'].append(5)
        p.cond['reuniones'][1]['docentes'].append(5)
        p.ordenar_reuniones()
        self.assertEqual(sum(5 in r['docentes'] for r in p.cond['reuniones']), 1)
        # En los avisos, los que no pueden «reciben el acta»
        alt = {'reuniones': [{'nombre': 'R', 'ubicada': True, 'dia': 1, 'inicio': 420, 'faltan': [2]}]}
        self.assertIn('reciben el acta', p.texto_reuniones(alt)[0])

    def test_salones_y_agrupaciones(self):
        D = datos()
        p = proyecto(D)
        c = p.cond
        c['modo_salones'] = 'curso'
        c['grupos_salones'] = [{'nombre': 'Bloque A', 'tipo': 'bloque'}, {'nombre': 'Especiales', 'tipo': 'especial'},
                               {'nombre': 'Laboratorios', 'tipo': 'especial'}]
        c['salones'] = [{'id': f'A{k}', 'nombre': f'A-10{k}', 'capacidad': 1, 'grupos': ['Bloque A']} for k in (1, 2, 3, 4)]
        lunes = [f'1-{f["id"]}' for f in D.franjas_de(1) if not f['descanso']]
        c['salones'] += [{'id': 'SIS', 'nombre': 'Sala de sistemas', 'capacidad': 1, 'grupos': ['Especiales'],
                          'no_puede': lunes},
                         {'id': 'L1', 'nombre': 'Lab 1', 'capacidad': 1, 'grupos': ['Laboratorios']},
                         {'id': 'L2', 'nombre': 'Lab 2', 'capacidad': 1, 'grupos': ['Laboratorios']}]
        for cid in (1, 2, 3, 4):
            p.curso(cid)['salon'] = f'S:A{cid}'
        p.regla(2)['salon'] = 'S:SIS'                 # materia 2 (4 cursos × 4 h) en la única sala de sistemas
        p.regla(5)['salon'] = 'G:Laboratorios'        # materia 5: cualquiera de los 2 laboratorios
        self.assertEqual(nucleo.salon_requerido(c, D.asignaciones[12]), 'S:SIS')
        self.assertEqual(nucleo.claves_salon(c, 'S:SIS'), ['S:SIS', 'G:Especiales'])
        alt = p.generar(cuantas=1, segundos=8)[0]
        self.assertEqual(alt['choques'], [])
        self.assertEqual(alt['horas_sin_ubicar'], 0)
        self.assertEqual(alt.get('avisos_salones'), [])
        vistos = defaultdict(list)
        for s in alt['sesiones']:
            a = D.asignaciones[s['asignacion']]
            self.assertIn('salon', s)
            if a['materia'] == 2:
                self.assertEqual(s['salon'], 'SIS')
                self.assertNotEqual(s['dia'], 1)                      # la sala está bloqueada el lunes
            elif a['materia'] == 5:
                self.assertIn(s['salon'], ('L1', 'L2'))
            else:
                self.assertEqual(s['salon'], f'A{a["curso"]}')
            vistos[(s['salon'], s['dia'], s['franja'])].append(a['curso'])
        self.assertTrue(all(len(v) == 1 for v in vistos.values()), [k for k, v in vistos.items() if len(v) > 1])
        self.assertTrue(p.tabla_salon(alt, 'SIS'))
        subs = [x['sub'] for fr, celdas in p.tabla_curso(alt, 1)['filas'] for xs in celdas for x in xs]
        self.assertTrue(any('Sala de sistemas' in t for t in subs), subs)
        # A mano: la sala ya está ocupada a esa hora
        s0 = next(s for s in alt['sesiones'] if D.asignaciones[s['asignacion']]['materia'] == 2)
        otro = next(cid for cid in (1, 2, 3, 4) if cid != D.asignaciones[s0['asignacion']]['curso'])
        blanco = {'sesiones': [dict(s0)], 'reuniones': []}
        self.assertIn('ocupado', p.motivo(blanco, otro * 10 + 2, s0['dia'], s0['franja']))
        self.assertIn('bloqueado', p.motivo(blanco, otro * 10 + 2, 1, D.franjas_de(1)[0]['id']))
        # Sin salones, nada cambia
        c['modo_salones'] = 'apagado'
        self.assertIsNone(nucleo.salon_requerido(c, D.asignaciones[12]))

    def test_bloqueo_general_del_marco(self):
        D = datos()
        p = proyecto(D)
        f0 = [f for f in D.franjas_de(1) if not f['descanso']][0]
        for dia in (1, 3):
            self.assertTrue(p.alternar_celda_marco(dia, f0['id']))
        self.assertTrue(p.celda_marco(1, f0['id']) and p.celda_curso(2, 1, f0['id']))
        alt = p.generar(cuantas=1, segundos=4)[0]
        self.assertEqual(alt['choques'], [])
        self.assertFalse([s for s in alt['sesiones'] if s['franja'] == f0['id'] and s['dia'] in (1, 3)])
        self.assertFalse(p.alternar_celda_marco(3, f0['id']))

    def test_minimo_de_clases_por_dia(self):
        from .motor import Estado
        D = datos()
        cond = nucleo.condiciones_vacias()
        cond['min_dia_docente'] = 3
        cond['docentes']['5'] = {'min_dia': 2}           # el docente 5 tiene su propio mínimo
        p = nucleo.armar(D, cond)
        self.assertEqual(p.min_docente_dia[1], 3)
        self.assertEqual(p.min_docente_dia[5], 2)
        est = Estado(p)
        for u in p.unidades:
            est.u[u['id']] = u
        u1 = next(u for u in p.unidades if u['partes'][0]['docente'] == 1 and u['largo'] == 1)
        f0 = sorted((f for f in p.franjas if p.franjas[f][0] == 1), key=lambda f: p.indice[f])[0]
        est.poner(u1, 2, f0)
        self.assertGreaterEqual(est.costo_docente_dia(1, 2), p.w['minimo'] * 2)   # 1 clase de 3: le faltan 2
        # Generando: nadie queda con menos que su mínimo (hay de sobra para cumplirlo)
        pr = proyecto(D)
        pr.cond['min_dia_docente'] = 2
        alt = pr.generar(cuantas=1, segundos=6)[0]
        self.assertEqual(alt['choques'], [])
        self.assertEqual(alt['avisos_minimo'], [], alt['avisos_minimo'])
        self.assertEqual(pr.minimo_docente(1), 2)

    def test_hora_preferida(self):
        from .motor import Estado
        D = datos()
        p = proyecto(D)
        clase = [f for f in D.franjas_de(1) if not f['descanso']]
        self.assertEqual(p.siguiente_estado(3, 1, clase[0]['id']), 'no_puede')
        for esperado in ('prefiere_no', 'evitar', 'preferida', 'libre'):
            self.assertEqual(p.siguiente_estado(3, 1, clase[0]['id']), esperado)
        for f in clase:
            for d in (1, 2):
                p.poner_celda(3, d, f['id'], 'preferida')
        prob = nucleo.armar(D, p.cond)
        self.assertEqual(len(prob.preferida[3]), 2 * len(clase))
        self.assertGreater(prob.w['preferida'], prob.w['prefiere_no'])        # pesa más que «mejor no»
        est = Estado(prob)
        for u in prob.unidades:
            est.u[u['id']] = u
        u3 = next(u for u in prob.unidades if u['partes'][0]['docente'] == 3 and u['largo'] == 1)
        est.poner(u3, 1, clase[2]['id'])
        en_preferida = est.costo_docente_dia(3, 1)
        est.quitar(u3['id'])
        est.poner(u3, 3, clase[2]['id'])
        self.assertLess(en_preferida, est.costo_docente_dia(3, 3))
        alt = p.generar(cuantas=1, segundos=6)[0]
        self.assertEqual(alt['choques'], [])
        lunes_martes = sum(1 for s in alt['sesiones'] if D.asignaciones[s['asignacion']]['docente'] == 3 and s['dia'] in (1, 2))
        self.assertGreaterEqual(lunes_martes, 10)          # 20 horas: sin preferencia serían unas 8

    def test_maximo_de_dias_largos_al_compensar(self):
        D = datos()
        p = proyecto(D)
        p.cond['permanencia_horas'] = 5
        p.cond['compensar'] = {'activa': True, 'max': 1, 'max_dias': 1}
        self.assertEqual(nucleo.armar(D, p.cond).compensar_max_dias[1], 1)
        alt = p.generar(cuantas=1, segundos=10)[0]
        self.assertEqual(alt['choques'], [])
        for did in range(1, 7):
            _, _, perfil = p.semana_docente(alt, did)
            self.assertLessEqual(sum(1 for a, _ in perfil.values() if a > 5 * 60), 1, (did, perfil))
        # A mano se avisa si se pasa
        blanco = p.en_blanco()
        clase = [f for f in D.franjas_de(1) if not f['descanso']]
        for dia, (x, y) in enumerate([(11, 21), (31, 41)], start=1):
            p.poner_ficha(blanco, x, dia, clase[0]['id'])
            p.poner_ficha(blanco, y, dia, clase[-1]['id'])
        self.assertTrue(any('días largos y el máximo es 1' in c for c in p._revisar_compensacion(blanco)))

    def test_actividad_con_horas_escogidas_a_mano(self):
        D = datos()
        p = proyecto(D)
        ultima = [f for f in D.franjas_de(1) if not f['descanso']][-1]['id']
        p.cond['actividades'] = [{'nombre': 'Reunión de padres', 'docentes': [], 'horas': 2, 'max_dia': 1,
                                  'fijas': [f'4-{ultima}']}]
        alt = p.generar(cuantas=1, segundos=4)[0]
        self.assertFalse([s for s in alt['sesiones'] if s['dia'] == 4 and s['franja'] == ultima])
        for did in range(1, 7):
            mias = [x for x in alt['actividades'] if x['docente'] == did]
            self.assertEqual(len(mias), 2)
            self.assertIn((4, ultima), {(x['dia'], x['franja']) for x in mias})
        # Si a mano le ponen clase a esa hora, se avisa
        s = next(s for s in alt['sesiones'] if D.asignaciones[s['asignacion']]['docente'] == 1)
        s['dia'], s['franja'] = 4, ultima
        _, avisos = nucleo.ubicar_actividades(D, p.cond, alt['sesiones'])
        self.assertTrue(any('Docente 1 tiene clase' in a for a in avisos), avisos)

    def test_niveles(self):
        self.assertEqual([nucleo.nivel_de_grado(g) for g in (0, 3, 7, 11, None)], ['PRE', 'PRI', 'BAS', 'MED', None])
        self.assertTrue(nucleo.grado_en_nivel(10, 'BACH') and nucleo.grado_en_nivel(6, 'BACH'))
        self.assertFalse(nucleo.grado_en_nivel(5, 'BACH'))
        D = datos()
        D.cursos[1]['grado'] = 6
        self.assertEqual(D.docentes_de_nivel('BAS'), [1, 2, 3, 4, 5, 6])
        self.assertEqual(D.docentes_de_nivel('PRI'), [])
