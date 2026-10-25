# -*- coding: utf-8 -*-
"""Reporte parcial: «Sí» sugerido por la nota parcial, aviso a la familia e informe en PDF."""
from decimal import Decimal

from notas import reporte_aviso
from notas.models import Calificacion, FichaEstudiante, NotaDetallada, ReporteParcial
from notas.tests.base import ColegioDePrueba


class ReporteAviso(ColegioDePrueba):

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.ana, cls.beto, cls.caro = cls.estudiantes
        # Ana: solo SABER con 2,0 -> parcial 2,0 (HACER sin notas no la baja). Beto: 4,0 y 3,0 -> 3,6.
        for est, comp, valores in ((cls.ana, 'SABER', ['2.0']), (cls.beto, 'SABER', ['4.0']),
                                   (cls.beto, 'HACER', ['3.0'])):
            cal = Calificacion.objects.create(colegio=cls.a, estudiante=est, materia=cls.materia, periodo=cls.p1,
                                              tipo_nota=comp, valor_nota=Decimal(valores[0]))
            for v in valores:
                NotaDetallada.objects.create(colegio=cls.a, calificacion_promedio=cal, descripcion='N', valor_nota=Decimal(v))
        FichaEstudiante.objects.create(estudiante=cls.ana, celular_acudiente='310 555 1234', nombre_acudiente='Marta')

    def test_nota_parcial_solo_con_componentes_que_tienen_notas(self):
        notas = reporte_aviso.notas_parciales(self.asig, self.p1, self.estudiantes)
        self.assertEqual(notas[self.ana.id], Decimal('2.0'))
        self.assertEqual(notas[self.beto.id], Decimal('3.6'))
        self.assertNotIn(self.caro.id, notas)

    def test_en_bajo_sale_marcado_si(self):
        r = self.cliente(self.u_docente).get(f'/docente/reporte-parcial/?asignacion_id={self.asig.id}&periodo_id={self.p1.id}')
        filas = {f['est'].id: f for f in r.context['filas']}
        self.assertTrue(filas[self.ana.id]['si'] and filas[self.ana.id]['sugerido'])
        self.assertFalse(filas[self.beto.id]['si'])
        self.assertFalse(filas[self.caro.id]['si'])
        self.assertContains(r, 'Sugerido por la nota')

    def test_lo_guardado_manda_sobre_la_sugerencia(self):
        ReporteParcial.objects.create(colegio=self.a, estudiante=self.ana, asignacion=self.asig, periodo=self.p1,
                                      presenta_dificultades=False)
        r = self.cliente(self.u_docente).get(f'/docente/reporte-parcial/?asignacion_id={self.asig.id}&periodo_id={self.p1.id}')
        fila = next(f for f in r.context['filas'] if f['est'].id == self.ana.id)
        self.assertFalse(fila['si'])

    def test_aviso_whatsapp_y_enlace_al_informe(self):
        ReporteParcial.objects.create(colegio=self.a, estudiante=self.ana, asignacion=self.asig, periodo=self.p1,
                                      presenta_dificultades=True)
        r = self.cliente(self.u_docente).get(f'/reporte-parcial/aviso/{self.ana.id}/?periodo_id={self.p1.id}')
        self.assertContains(r, 'Matemáticas (2,0)')
        self.assertContains(r, 'https://wa.me/573105551234')
        url = r.context['url_informe']
        self.assertIn('/familia/informe-parcial/', url)
        # La familia descarga el PDF sin iniciar sesión.
        pdf = self.cliente().get(url[url.index('/familia/'):])
        self.assertEqual(pdf.status_code, 200)
        self.assertEqual(pdf['Content-Type'], 'application/pdf')
        self.assertEqual(self.cliente().get('/familia/informe-parcial/token-falso/').status_code, 410)

    def test_el_estudiante_no_puede_avisar_pero_si_descargar_su_informe(self):
        self.assertEqual(self.cliente(self.ana.user).get(
            f'/reporte-parcial/aviso/{self.ana.id}/?periodo_id={self.p1.id}').status_code, 403)
        self.assertEqual(self.cliente(self.ana.user).get(
            f'/reporte-parcial/informe/{self.ana.id}/pdf/?periodo_id={self.p1.id}').status_code, 200)
        self.assertEqual(self.cliente(self.beto.user).get(
            f'/reporte-parcial/informe/{self.ana.id}/pdf/?periodo_id={self.p1.id}').status_code, 403)


    def test_sugerencia_del_docente_en_el_reporte_el_acta_y_el_aviso(self):
        self.p1.reporte_parcial_activo = True
        self.p1.save()
        url = f'/docente/reporte-parcial/?asignacion_id={self.asig.id}&periodo_id={self.p1.id}'
        datos = {'asignacion_id': self.asig.id, 'periodo_id': self.p1.id,
                 f'reporte_{self.ana.id}': 'si', f'sugerencia_{self.ana.id}': '  Entregar el taller de fracciones  ',
                 f'reporte_{self.beto.id}': 'no', f'reporte_{self.caro.id}': 'no'}
        self.cliente(self.u_docente).post(url, datos)
        r = ReporteParcial.objects.get(estudiante=self.ana, periodo=self.p1)
        self.assertTrue(r.presenta_dificultades)
        self.assertEqual(r.sugerencia, 'Entregar el taller de fracciones')
        # Vuelve a salir en el formulario del docente
        self.assertContains(self.cliente(self.u_docente).get(url), 'Entregar el taller de fracciones')
        # En el acta, frente a la asignatura
        acta = self.cliente(self.rectora).get(f'/reporte-parcial/acta/{self.ana.id}/?periodo_id={self.p1.id}')
        self.assertContains(acta, 'Entregar el taller de fracciones')
        # En el aviso a la familia
        aviso = reporte_aviso.texto_aviso(self.ana, self.p1, reporte_aviso.asignaturas_reportadas(self.ana, self.p1))
        self.assertIn('Matemáticas: Entregar el taller de fracciones', aviso)
