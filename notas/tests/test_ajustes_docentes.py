# -*- coding: utf-8 -*-
"""Observador por sede, columnas de la planilla para todas las asignaturas y menús nuevos."""
from notas.models import AsignacionDocente, Curso, Materia, PlanNotas, Sede
from notas.planillas.columnas import componentes_activos
from notas.tests.base import ColegioDePrueba


class ObservadorPorSede(ColegioDePrueba):

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.sede1 = Sede.objects.create(colegio=cls.a, nombre='Principal')
        cls.sede2 = Sede.objects.create(colegio=cls.a, nombre='Rural')
        Curso.objects.filter(id=cls.curso.id).update(sede=cls.sede1)
        cls.otro_curso = Curso.objects.create(colegio=cls.a, nombre='602', grado=6, subgrupo='2', sede=cls.sede1)
        cls.rural = Curso.objects.create(colegio=cls.a, nombre='501R', grado=5, sede=cls.sede2)
        cls.dani = cls.crear_estudiante('dani', curso=cls.otro_curso)
        cls.eva = cls.crear_estudiante('eva', curso=cls.rural)

    def test_ve_todos_los_cursos_de_su_sede_y_no_los_de_otra(self):
        r = self.cliente(self.u_docente).get('/observador/seleccionar/')
        self.assertContains(r, 'Mis cursos')
        self.assertContains(r, 'Otros cursos de mi sede')
        self.assertContains(r, '602')
        self.assertNotContains(r, '501R')

    def test_buscar_en_todos_trae_estudiantes_de_otros_cursos_de_la_sede(self):
        r = self.cliente(self.u_docente).get('/observador/seleccionar/?curso_id=todos')
        self.assertContains(r, 'DANI')
        self.assertNotContains(r, 'EVA')

    def test_no_puede_listar_un_curso_de_otra_sede(self):
        r = self.cliente(self.u_docente).get(f'/observador/seleccionar/?curso_id={self.rural.id}')
        self.assertNotContains(r, 'EVA')


class ColumnasParaTodas(ColegioDePrueba):

    def test_aplicar_a_todas_las_asignaturas_del_docente(self):
        fisica = Materia.objects.create(colegio=self.a, nombre='Física', usar_ponderacion_equitativa=False,
                                        porcentaje_ser=0, porcentaje_saber=60, porcentaje_hacer=40)
        otra = AsignacionDocente.objects.create(colegio=self.a, docente=self.docente, materia=fisica, curso=self.curso)
        codigos = [c for c, _, _ in componentes_activos(self.asig)]
        datos = {f'col_{codigos[0]}': ['Taller', 'Quiz', 'Examen'], 'aplicar_todas': '1'}
        r = self.cliente(self.u_docente).post(f'/docente/planillas/{self.asig.id}/{self.p1.id}/columnas/', datos)
        self.assertEqual(r.status_code, 302)
        plan = PlanNotas.objects.get(asignacion=otra, periodo=self.p1, componente=codigos[0])
        self.assertEqual(len(plan.columnas), 3)

    def test_sin_marcar_solo_cambia_esa_asignatura(self):
        fisica = Materia.objects.create(colegio=self.a, nombre='Física')
        otra = AsignacionDocente.objects.create(colegio=self.a, docente=self.docente, materia=fisica, curso=self.curso)
        codigos = [c for c, _, _ in componentes_activos(self.asig)]
        self.cliente(self.u_docente).post(f'/docente/planillas/{self.asig.id}/{self.p1.id}/columnas/',
                                          {f'col_{codigos[0]}': ['Taller']})
        self.assertFalse(PlanNotas.objects.filter(asignacion=otra).exists())


class Menus(ColegioDePrueba):

    def test_subir_planilla_en_el_menu_del_docente(self):
        self.assertContains(self.cliente(self.u_docente).get('/docente/planillas/'), '/docente/planillas/subir/')

    def test_actas_seleccionar_todos(self):
        self.assertContains(self.cliente(self.rectora).get('/actas/'), 'Seleccionar todos')
