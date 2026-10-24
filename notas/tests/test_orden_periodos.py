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
