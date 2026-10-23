"""El boletín final y el libro no deben hacer una consulta por cada nota.

Antes, por cada materia de cada estudiante se leía otra vez la escala y la configuración
del colegio: un libro con todos los cursos hacía decenas de miles de consultas y se demoraba
o se cortaba. Ahora se leen una vez por cálculo.
"""
from decimal import Decimal

from django.db import connection
from django.test.utils import CaptureQueriesContext

from notas.boletin.logic import _get_valoracion, get_datos_boletin_final
from notas.boletin.ponderacion import ajustes, en_lote
from notas.models import AreaConocimiento, AsignacionDocente, Calificacion, Materia, PonderacionAreaMateria

from .base import ColegioDePrueba


class RendimientoDelBoletinFinal(ColegioDePrueba):

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        area = AreaConocimiento.objects.create(colegio=cls.a, nombre='Matemáticas')
        PonderacionAreaMateria.objects.create(colegio=cls.a, area=area, materia=cls.materia, peso_porcentual=100)
        cls.materias = [cls.materia]
        for k in range(4):
            m = Materia.objects.create(colegio=cls.a, nombre=f'Materia {k}')
            ar = AreaConocimiento.objects.create(colegio=cls.a, nombre=f'Área {k}')
            PonderacionAreaMateria.objects.create(colegio=cls.a, area=ar, materia=m, peso_porcentual=100)
            AsignacionDocente.objects.create(colegio=cls.a, docente=cls.docente, materia=m, curso=cls.curso)
            cls.materias.append(m)

    def _notas(self, estudiantes):
        for e in estudiantes:
            for m in self.materias:
                for p, v in ((self.p1, '3.5'), (self.p2, '4.2')):
                    Calificacion.objects.create(colegio=self.a, estudiante=e, materia=m, periodo=p,
                                                tipo_nota='PROM_PERIODO', valor_nota=Decimal(v))

    def _consultas(self):
        with CaptureQueriesContext(connection) as c:
            boletines, _ = get_datos_boletin_final(self.a, self.curso, 2026)
        return len(c.captured_queries), boletines

    def test_las_consultas_no_crecen_con_estudiantes_ni_materias(self):
        self._notas(self.estudiantes)
        pocas, b1 = self._consultas()
        mas = [self.crear_estudiante(f'extra{k}') for k in range(5)]
        self._notas(mas)                            # casi tres veces más estudiantes, mismas materias
        muchas, b2 = self._consultas()
        self.assertEqual(len(b2), len(b1) + 5)
        self.assertLessEqual(muchas, pocas + 3, (pocas, muchas))
        # 8 estudiantes × 5 materias: antes eran cientos de consultas
        self.assertLess(muchas, 40, muchas)
        # Y las notas siguen bien: (3,5 + 4,2) / 2 = 3,9 → BÁSICO
        area = next(a for a in b2[0]['areas'] if a['nombre'] == 'Matemáticas')
        self.assertEqual(area['nota_final_area'], Decimal('3.9'))
        self.assertEqual(area['desempeno_area'], 'BÁSICO')

    def test_fuera_del_calculo_no_queda_nada_guardado(self):
        """Fuera de en_lote cada llamada lee de nuevo (no se queda con datos viejos)."""
        with CaptureQueriesContext(connection) as c:
            ajustes(self.a)
            ajustes(self.a)
        self.assertEqual(len(c.captured_queries), 2)
        with en_lote():
            with CaptureQueriesContext(connection) as c:
                ajustes(self.a)
                ajustes(self.a)
                _get_valoracion(self.a, Decimal('4.7'))
                self.assertEqual(_get_valoracion(self.a, Decimal('2.0')), 'BAJO')
            self.assertEqual(len(c.captured_queries), 2)      # una para ajustes y otra para la escala
        self.assertEqual(_get_valoracion(self.a, Decimal('4.7')), 'SUPERIOR')
