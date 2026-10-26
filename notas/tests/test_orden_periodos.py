"""Los periodos salen del primero al último aunque las fechas se hayan escrito mal."""
import datetime

from notas.alertas import periodos_hasta
from notas.models import PeriodoAcademico

from .base import ColegioDePrueba


class OrdenDeLosPeriodos(ColegioDePrueba):

    def test_orden_por_nombre_y_no_por_fecha(self):
        # El primer periodo quedó con una fecha posterior (error de digitación)
        self.p1.fecha_inicio = datetime.date(2026, 9, 1)
        self.p1.fecha_fin = datetime.date(2026, 11, 1)
        self.p1.save()
        tercero = PeriodoAcademico.objects.create(colegio=self.a, nombre='TERCERO', ano_lectivo=2026,
                                                  fecha_inicio=datetime.date(2026, 6, 2),
                                                  fecha_fin=datetime.date(2026, 8, 30))
        nombres = list(PeriodoAcademico.objects.filter(colegio=self.a).values_list('nombre', flat=True))
        self.assertEqual(nombres, ['PRIMERO', 'SEGUNDO', 'TERCERO'])
        self.assertEqual([p.nombre for p in periodos_hasta(self.a, 2026, self.p2)], ['PRIMERO', 'SEGUNDO'])
        self.assertEqual(tercero.orden, 3)
        r = self.cliente(self.rectora).get('/admin/panel-control-periodos/')
        self.assertEqual([p.nombre for p in r.context['periodos']], ['PRIMERO', 'SEGUNDO', 'TERCERO'])
        self.assertContains(r, 'Revise las fechas')

    def test_los_menus_de_periodos_salen_en_orden(self):
        # Con cuatro periodos, el orden alfabético daría Cuarto, Primero, Segundo, Tercero.
        for nombre, mes in (('TERCERO', 7), ('CUARTO', 9)):
            PeriodoAcademico.objects.create(colegio=self.a, nombre=nombre, ano_lectivo=2026,
                                            fecha_inicio=datetime.date(2026, mes, 1),
                                            fecha_fin=datetime.date(2026, mes + 1, 28))
        esperado = ['PRIMERO', 'SEGUNDO', 'TERCERO', 'CUARTO']
        paginas = [
            (self.u_docente, '/docente/ingresar-notas/', 'todos_los_periodos'),
            (self.u_docente, '/docente/reporte-parcial/', 'periodos'),
            (self.u_docente, '/docente/plan-mejoramiento/', 'periodos'),
            (self.u_docente, '/docente/consulta-asistencia/', 'periodos_academicos'),
            (self.rectora, '/reportes/selector-boletin/', 'periodos'),
        ]
        for usuario, url, clave in paginas:
            with self.subTest(url=url):
                r = self.cliente(usuario).get(url)
                self.assertEqual(r.status_code, 200)
                self.assertEqual([p.nombre for p in r.context[clave]], esperado)
