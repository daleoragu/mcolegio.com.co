# -*- coding: utf-8 -*-
"""Actas: informe de la comisión (orden, alcance, observador), cierre congelado, PDF y permisos."""
import datetime
from decimal import Decimal

from notas.models import AsignacionDocente, Calificacion, Materia, RegistroObservador
from notas.tests.base import ColegioDePrueba

from . import logica
from .models import Acta, RedactorActas


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


class ActasDeDocentes(ColegioDePrueba):
    """El rol de generar actas, el número que pone el administrador, firmas y «todos los docentes»."""

    def setUp(self):
        self.admin = self.cliente(self.rectora)
        self.profe = self.cliente(self.u_docente)

    def dar_rol(self):
        r = self.admin.post('/actas/redactores/', {'docentes': [self.docente.id]})
        self.assertEqual(r.status_code, 302)
        self.assertTrue(RedactorActas.objects.filter(docente=self.docente).exists())

    def test_sin_rol_el_docente_no_entra_y_no_ve_el_menu(self):
        self.assertEqual(self.profe.get('/actas/').status_code, 403)
        self.assertEqual(self.profe.post('/actas/redactores/', {'docentes': [self.docente.id]}).status_code, 403)

    def test_con_rol_redacta_las_suyas_y_le_salen_al_administrador(self):
        self.dar_rol()
        otra = Acta.objects.create(colegio=self.a, tipo=Acta.LIBRE, numero=1, ano=2026, titulo='Consejo directivo',
                                   fecha=datetime.date(2026, 4, 5), creada_por=self.rectora)
        r = self.profe.post('/actas/nueva/LIBRE/')
        mia = Acta.objects.get(creada_por=self.u_docente)
        self.assertRedirects(r, f'/actas/{mia.id}/', fetch_redirect_response=False)
        self.assertEqual(mia.numero, 2)                     # número provisional, el que sigue
        lista = self.profe.get('/actas/')
        self.assertContains(lista, 'Reunión')
        self.assertNotContains(lista, 'Consejo directivo')  # solo ve las suyas
        self.assertEqual(self.profe.get(f'/actas/{otra.id}/').status_code, 404)
        # Edita la suya, pero el número no lo puede tocar.
        r = self.profe.post(f'/actas/{mia.id}/', {'numero': '50', 'titulo': 'Reunión de área', 'fecha': '2026-04-06',
                                                  'estilo_firma': 'LINEAS', 'asis_nombre': ['Pedro Profe'],
                                                  'asis_cargo': ['Docente'], 'asis_x': ['0']})
        self.assertEqual(r.status_code, 302)
        mia.refresh_from_db()
        self.assertEqual((mia.numero, mia.titulo, mia.estilo_firma), (2, 'Reunión de área', 'LINEAS'))
        self.assertEqual(self.profe.post(f'/actas/{mia.id}/numero/', {'numero': '7'}).status_code, 403)
        # Al administrador le sale, marcada como de docente, y le cambia el número.
        lista = self.admin.get('/actas/')
        self.assertContains(lista, 'Reunión de área')
        self.assertContains(lista, 'ac-docente">docente')
        r = self.admin.post(f'/actas/{mia.id}/numero/', {'numero': '1'})   # ya existe la 1
        mia.refresh_from_db()
        self.assertEqual(mia.numero, 2)
        self.admin.post(f'/actas/{mia.id}/numero/', {'numero': '15'})
        mia.refresh_from_db()
        self.assertEqual(mia.numero, 15)
        # El PDF con firmas en líneas.
        r = self.profe.get(f'/actas/{mia.id}/pdf/')
        self.assertEqual(r['Content-Type'], 'application/pdf')
        # Cerrada: el docente no la reabre; el administrador sí, y aun cerrada le cambia el número.
        self.profe.post(f'/actas/{mia.id}/cerrar/')
        mia.refresh_from_db()
        self.assertTrue(mia.cerrada)
        self.assertEqual(self.profe.post(f'/actas/{mia.id}/reabrir/').status_code, 403)
        self.admin.post(f'/actas/{mia.id}/numero/', {'numero': '16'})
        mia.refresh_from_db()
        self.assertEqual((mia.numero, mia.cerrada), (16, True))

    def test_el_administrador_cambia_el_numero_desde_el_formulario(self):
        acta = Acta.objects.create(colegio=self.a, tipo=Acta.LIBRE, numero=3, ano=2026, titulo='X',
                                   fecha=datetime.date(2026, 4, 5))
        Acta.objects.create(colegio=self.a, tipo=Acta.LIBRE, numero=4, ano=2026, titulo='Otra',
                            fecha=datetime.date(2026, 4, 5))
        r = self.admin.post(f'/actas/{acta.id}/', {'numero': '4', 'titulo': 'X', 'fecha': '2026-04-05',
                                                   'estilo_firma': 'CUADRO'})
        self.assertContains(r, 'Ya existe el acta N.º 4')
        self.admin.post(f'/actas/{acta.id}/', {'numero': '9', 'titulo': 'X', 'fecha': '2026-04-05',
                                               'estilo_firma': 'CUADRO'})
        acta.refresh_from_db()
        self.assertEqual(acta.numero, 9)

    def test_agregar_a_todos_los_docentes_solo_administrador(self):
        self.dar_rol()
        acta = Acta.objects.create(colegio=self.a, tipo=Acta.LIBRE, numero=1, ano=2026, titulo='Reunión',
                                   fecha=datetime.date(2026, 4, 5), creada_por=self.u_docente)
        filas = self.admin.get(f'/actas/{acta.id}/sugerir-asistentes/?todos=docentes').json()['filas']
        self.assertIn({'nombre': 'Pedro Profe', 'cargo': 'Docente', 'asistio': False}, filas)
        self.assertContains(self.admin.get(f'/actas/{acta.id}/'), 'Agregar a todos los docentes')
        self.assertEqual(self.profe.get(f'/actas/{acta.id}/sugerir-asistentes/?todos=docentes').status_code, 403)
        self.assertNotContains(self.profe.get(f'/actas/{acta.id}/'), 'Agregar a todos los docentes')

    def test_firmantes_en_lineas(self):
        acta = Acta(asistencia=[{'nombre': 'Rosa', 'cargo': 'Rectora', 'asistio': True},
                                {'nombre': 'Luis', 'cargo': 'Docente', 'asistio': False}])
        self.assertEqual([f['nombre'] for f in logica.firmantes(acta)], ['Rosa'])
        acta.asistencia[0]['asistio'] = False
        self.assertEqual([f['nombre'] for f in logica.firmantes(acta)], ['Rosa', 'Luis'])

    def test_sedes_solo_el_administrador(self):
        from django.contrib.auth.models import Group
        self.u_docente.groups.add(Group.objects.get_or_create(name='Docentes')[0])
        self.assertEqual(self.profe.get('/admin/sedes/').status_code, 403)
        self.assertEqual(self.profe.get('/admin/sedes/crear/').status_code, 403)
        r = self.profe.get('/admin/portal/configuracion/')
        self.assertEqual(r.status_code, 200)
        self.assertNotContains(r, '/admin/sedes/')
        self.assertContains(self.admin.get('/admin/portal/configuracion/'), '/admin/sedes/')
