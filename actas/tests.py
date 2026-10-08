# -*- coding: utf-8 -*-
"""Actas: informe de la comisión (orden, alcance, observador), cierre congelado, PDF y permisos."""
import datetime
from decimal import Decimal

from notas.models import AsignacionDocente, Calificacion, Materia, RegistroObservador
from notas.tests.base import ColegioDePrueba

from . import logica
from .models import Acta


class Actas(ColegioDePrueba):

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.lengua = Materia.objects.create(colegio=cls.a, nombre='Lenguaje')
        AsignacionDocente.objects.create(colegio=cls.a, docente=cls.docente, materia=cls.lengua, curso=cls.curso)
        ana, beto, caro = cls.estudiantes
        notas = [(ana, cls.materia, cls.p1, '2.0'), (ana, cls.lengua, cls.p1, '2.5'),
                 (beto, cls.materia, cls.p1, '1.5'), (beto, cls.lengua, cls.p1, '4.0'),
                 (caro, cls.materia, cls.p1, '4.0'), (caro, cls.lengua, cls.p1, '4.5'),
                 (beto, cls.materia, cls.p2, '3.5'), (beto, cls.lengua, cls.p2, '4.0')]
        for est, m, p, v in notas:
            Calificacion.objects.create(colegio=cls.a, estudiante=est, materia=m, periodo=p,
                                        tipo_nota='PROM_PERIODO', valor_nota=Decimal(v))

    def _acta(self, **kw):
        datos = dict(colegio=self.a, tipo=Acta.COMISION, numero=1, ano=2026, titulo='Comisión 6.º',
                     fecha=datetime.date(2026, 4, 5), periodo=self.p1)
        datos.update(kw)
        acta = Acta.objects.create(**datos)
        acta.cursos.add(self.curso)
        return acta

    def test_informe_del_periodo_de_mayor_a_menor(self):
        inf = logica.calcular_informe(self._acta())
        self.assertEqual([f['estudiante'] for f in inf['filas']], ['PRUEBA ANA', 'PRUEBA BETO'])
        self.assertEqual([f['n'] for f in inf['filas']], [2, 1])
        self.assertEqual(inf['filas'][0]['asignaturas'][0], {'materia': 'Matemáticas', 'nota': '2.0'})
        self.assertEqual((inf['analizados'], inf['con_pendientes']), (3, 2))
        self.assertNotIn('anotaciones', inf['filas'][0])

    def test_acumulado_del_ano(self):
        # En el 2.º periodo Beto ganó todo, pero en el acumulado sigue debiendo Matemáticas.
        del_periodo = logica.calcular_informe(self._acta(periodo=self.p2))
        self.assertEqual(del_periodo['filas'], [])
        acumulado = logica.calcular_informe(self._acta(numero=2, periodo=self.p2, alcance=Acta.ACUMULADO))
        self.assertIn('PRUEBA BETO', [f['estudiante'] for f in acumulado['filas']])

    def test_anotaciones_solo_si_el_admin_quiere_y_sin_las_positivas(self):
        beto = self.estudiantes[1]
        for sub in ('NEGATIVA', 'NEGATIVA', 'POSITIVA'):
            RegistroObservador.objects.create(colegio=self.a, estudiante=beto, fecha_suceso=datetime.date(2026, 3, 1),
                                              tipo='COMPORTAMENTAL', subtipo=sub, descripcion='x')
        RegistroObservador.objects.create(colegio=self.a, estudiante=beto, fecha_suceso=datetime.date(2026, 5, 1),
                                          tipo='COMPORTAMENTAL', subtipo='NEGATIVA', descripcion='fuera del periodo')
        inf = logica.calcular_informe(self._acta(mostrar_observador=True))
        fila = next(f for f in inf['filas'] if f['estudiante'] == 'PRUEBA BETO')
        self.assertEqual(fila['anotaciones'], 2)

    def test_al_cerrar_el_informe_queda_congelado(self):
        acta = self._acta()
        logica.cerrar(acta)
        Calificacion.objects.filter(estudiante=self.estudiantes[1]).update(valor_nota=Decimal('5.0'))
        acta.refresh_from_db()
        self.assertEqual(len(logica.informe_de(acta)['filas']), 2)
        logica.reabrir(acta)
        self.assertEqual(len(logica.informe_de(acta)['filas']), 1)

    def test_flujo_completo_y_pdf(self):
        c = self.cliente(self.rectora)
        r = c.post('/actas/nueva/COMISION/')
        acta = Acta.objects.get(colegio=self.a)
        self.assertRedirects(r, f'/actas/{acta.id}/', fetch_redirect_response=False)
        self.assertEqual(acta.numero, 1)
        self.assertContains(c.get(f'/actas/{acta.id}/'), 'Qué se revisa')
        datos = {'titulo': 'Comisión grado sexto', 'fecha': '2026-04-05', 'lugar': 'Biblioteca',
                 'periodo': self.p1.id, 'alcance': 'PERIODO', 'cursos': [self.curso.id], 'mostrar_observador': 'on',
                 'orden_del_dia': 'Saludo\nCasos', 'desarrollo': 'Se revisaron los casos.',
                 'decisiones': 'Citar acudientes',
                 'asis_nombre': ['Rosa Rector', 'Pedro Profe', 'Marta Díaz'],
                 'asis_cargo': ['Rectora', 'Director(a) de grado 601', 'Representante de padres — Sexto'],
                 'asis_x': ['0', '2']}
        r = c.post(f'/actas/{acta.id}/', datos)
        self.assertEqual(r.status_code, 302)
        r = c.get(f'/actas/{acta.id}/')
        self.assertContains(r, 'PRUEBA ANA')
        acta.refresh_from_db()
        self.assertEqual([a['asistio'] for a in acta.lista_asistentes()], [True, False, True])
        # La siguiente acta trae el nombre del representante que ya se escribió.
        otra = self._acta(numero=9)
        filas = c.get(f'/actas/{otra.id}/sugerir-asistentes/').json()['filas']
        cargos = {f['cargo']: f['nombre'] for f in filas}
        self.assertEqual(cargos['Representante de padres — Sexto'], 'Marta Díaz')
        self.assertEqual(cargos['Representante de estudiantes — Sexto'], '')
        self.assertEqual(cargos['Director(a) de grado 601'], 'Pedro Profe')
        self.assertIn('Rosa Rector', cargos.values())
        r = c.get(f'/actas/{acta.id}/pdf/')
        self.assertEqual(r['Content-Type'], 'application/pdf')
        c.post(f'/actas/{acta.id}/cerrar/')
        acta.refresh_from_db()
        self.assertTrue(acta.cerrada)
        self.assertContains(c.get(f'/actas/{acta.id}/'), 'PDF para firmar')
        # La siguiente del año toma el número que sigue (ya hay una N.º 9)
        c.post('/actas/nueva/LIBRE/')
        self.assertEqual(Acta.objects.filter(colegio=self.a, tipo=Acta.LIBRE).get().numero, 10)

    def test_comision_exige_cursos(self):
        acta = self._acta()
        acta.cursos.clear()
        r = self.cliente(self.rectora).post(f'/actas/{acta.id}/', {'titulo': 'X', 'fecha': '2026-04-05',
                                                                   'periodo': self.p1.id, 'alcance': 'PERIODO'})
        self.assertContains(r, 'Escoja al menos un curso')

    def test_sugerir_con_cursos_sin_guardar(self):
        acta = self._acta()
        acta.cursos.clear()
        c = self.cliente(self.rectora)
        nombres = [f['nombre'] for f in c.get(f'/actas/{acta.id}/sugerir-asistentes/').json()['filas']]
        self.assertNotIn('Pedro Profe', nombres)
        filas = c.get(f'/actas/{acta.id}/sugerir-asistentes/?cursos={self.curso.id}').json()['filas']
        self.assertIn({'nombre': 'Pedro Profe', 'cargo': 'Director(a) de grado 601', 'asistio': False}, filas)

    def test_asistentes_y_firmas(self):
        acta = self._acta(asistencia=[{'nombre': 'Rosa', 'cargo': 'Rectora', 'asistio': True},
                                      {'nombre': '', 'cargo': '', 'asistio': True}, 'basura',
                                      {'nombre': 'Luis', 'cargo': 'Representante de estudiantes', 'asistio': False}])
        self.assertEqual(len(acta.lista_asistentes()), 2)
        self.assertEqual(acta.cuantos_asistieron, 1)

    def test_solo_administradores_y_de_su_colegio(self):
        acta = self._acta()
        self.assertEqual(self.cliente(self.u_docente).get('/actas/').status_code, 403)
        self.assertEqual(self.cliente(self.u_docente).get(f'/actas/{acta.id}/pdf/').status_code, 403)
        self.assertEqual(self.cliente(self.super, host='b.localhost').get(f'/actas/{acta.id}/').status_code, 404)

    def test_cerrada_no_se_borra(self):
        acta = self._acta()
        logica.cerrar(acta)
        self.cliente(self.rectora).post(f'/actas/{acta.id}/eliminar/')
        self.assertTrue(Acta.objects.filter(id=acta.id).exists())
