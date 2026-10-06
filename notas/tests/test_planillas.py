# notas/tests/test_planillas.py
"""Plan de notas, cálculo de la definitiva y el Excel de ida y vuelta."""
import io
from decimal import Decimal

import openpyxl

from notas.models import Calificacion, PlanNotas
from notas.models.comunicaciones import Notificacion
from notas.planillas.columnas import columnas_del_plan, ubicar
from notas.planillas.excel import generar_libro, leer_libro, aplicar, a_sesion
from notas.planillas.guardar import guardar_estudiante

from .base import ColegioDePrueba


def definitiva(est, periodo):
    return Calificacion.objects.get(estudiante=est, periodo=periodo, tipo_nota='PROM_PERIODO').valor_nota


class Calculo(ColegioDePrueba):

    def test_definitiva_igual_que_la_plataforma(self):
        ana = self.estudiantes[0]
        guardar_estudiante(self.a, self.asig, self.p1, ana,
                           {'SABER': [('Nota 1', '4'), ('Nota 3', '2')], 'HACER': [('Nota 1', '5')]})
        self.assertEqual(definitiva(ana, self.p1), Decimal('3.80'))     # 0,6·3 + 0,4·5

    def test_notas_fuera_de_rango_no_cuentan(self):
        beto = self.estudiantes[1]
        guardar_estudiante(self.a, self.asig, self.p1, beto,
                           {'SABER': [('N1', '7'), ('N2', '4'), ('N3', 'aus')], 'HACER': []})
        self.assertEqual(definitiva(beto, self.p1), Decimal('2.40'))    # solo el 4 cuenta

    def test_cada_nota_va_a_la_columna_de_su_nombre(self):
        self.assertEqual(ubicar([('Nota 1', 4), ('Nota 3', 2)], ['Nota 1', 'Nota 2', 'Nota 3']), [4, None, 2])

    def test_sin_plan_salen_las_del_colegio(self):
        self.assertEqual(len(columnas_del_plan(self.asig, self.p1, 'SABER')), 5)


class ExcelIdaYVuelta(ColegioDePrueba):

    def bajar(self):
        return openpyxl.load_workbook(io.BytesIO(generar_libro(self.a, self.p1, [self.asig])))

    def subir(self, libro, usuario=None):
        salida = io.BytesIO()
        libro.save(salida)
        salida.seek(0)
        return leer_libro(salida, self.a, usuario or self.u_docente)

    def test_lo_que_se_sube_es_lo_que_queda(self):
        import json
        libro = self.bajar()
        ws = libro[libro.sheetnames[1]]
        meta = next(json.loads(c.value) for c in ws[4] if isinstance(c.value, str) and 'mcolegio' in c.value)
        fila_ana = meta['fila']                               # ana es la primera por apellido y nombre
        ws.cell(fila_ana, meta['comp']['SABER'][0], 4.5)      # SABER, nota 1
        ws.cell(fila_ana, meta['comp']['HACER'][0], 3)        # HACER, nota 1
        resultado = self.subir(libro)
        hoja = resultado['hojas'][0]
        self.assertEqual(hoja['estado'], 'ok')
        aplicar(a_sesion(resultado), self.a, self.u_docente)
        ana = self.estudiantes[0]
        esperado = next(e['definitiva'] for e in hoja['estudiantes'] if e['id'] == ana.id)
        self.assertEqual(definitiva(ana, self.p1), esperado)

    def test_otro_docente_no_puede_subir_la_planilla(self):
        from django.contrib.auth.models import User
        from notas.models import Docente
        otra = User.objects.create_user('otra', password='x')
        Docente.objects.create(colegio=self.a, user=otra)
        hoja = self.subir(self.bajar(), usuario=otra)['hojas'][0]
        self.assertEqual(hoja['estado'], 'error')

    def test_avisa_estudiantes_que_llegaron_despues(self):
        libro = self.bajar()
        nuevo = self.crear_estudiante('dani')
        hoja = self.subir(libro)['hojas'][0]
        self.assertIn('PRUEBA DANI', hoja['faltan'])

    def test_estudiante_nuevo_avisa_al_docente(self):
        Notificacion.objects.all().delete()       # los de la preparación ya avisaron
        self.crear_estudiante('eva')
        self.crear_estudiante('fer')
        avisos = Notificacion.objects.filter(destinatario=self.u_docente, tipo='PLANILLA')
        self.assertEqual(avisos.count(), 1)
        self.assertTrue(avisos.first().mensaje.startswith('2 estudiantes nuevos'))
