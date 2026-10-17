# -*- coding: utf-8 -*-
"""Intensidad horaria por grado y horario armado con materias sin docente."""
import io
import json

from django.core.files.uploadedfile import SimpleUploadedFile
from openpyxl import Workbook

from notas.models import AsignacionDocente, Curso, Materia

from . import intercambio, nucleo
from .models import Horario, PlanHoras, Sesion
from .tests import Base


class Intensidad(Base):

    def test_totales_por_grado_y_guardar(self):
        c2 = Curso.objects.create(colegio=self.a, nombre='602', grado=6, subgrupo='2')
        self.j.cursos.add(c2)
        fisica = Materia.objects.create(colegio=self.a, nombre='Física')
        c = self.cliente(self.rectora)
        r = c.get('/horarios/intensidad/')
        self.assertEqual(r.status_code, 200)
        g = r.context['grados'][0]
        res = {x['curso'].nombre: x for x in g['resumen']}
        self.assertEqual((res['601']['total'], res['601']['cupo']), (7, 20))       # 4 + 3; 4 horas × 5 días
        self.assertFalse(g['parejos'])                                               # 602 no tiene nada
        # Guardar: con docente cambia la asignación; sin docente crea el plan
        c.post('/horarios/intensidad/', {f'h_{self.curso.id}_{self.materia.id}': '5',
                                         f'h_{c2.id}_{self.materia.id}': '5', f'h_{c2.id}_{self.ingles.id}': '3'})
        self.asig.refresh_from_db()
        self.assertEqual(self.asig.intensidad_horaria_semanal, 5)
        self.assertEqual(PlanHoras.objects.get(curso=c2, materia=self.materia).horas, 5)
        c.post('/horarios/intensidad/', {'accion': 'agregar', 'grado': '6', 'materia': fisica.id, 'horas': '2'})
        self.assertEqual(PlanHoras.objects.filter(materia=fisica).count(), 2)
        g = self.cliente(self.rectora).get('/horarios/intensidad/').context['grados'][0]
        res = {x['curso'].nombre: x['total'] for x in g['resumen']}
        self.assertEqual(res, {'601': 10, '602': 10})
        self.assertTrue(g['parejos'])
        # Poner 0 a una sin docente la quita
        c.post('/horarios/intensidad/', {f'h_{c2.id}_{fisica.id}': '0'})
        self.assertFalse(PlanHoras.objects.filter(curso=c2, materia=fisica).exists())

    def test_armar_sin_docente_y_amarrar_despues(self):
        fisica = Materia.objects.create(colegio=self.a, nombre='Física')
        plan = PlanHoras.objects.create(colegio=self.a, curso=self.curso, materia=fisica, horas=2)
        d = intercambio.datos_del_colegio(self.a)
        virtual = [x for x in d['asignaciones'] if x['id'] < 0]
        self.assertEqual(virtual, [{'id': -plan.id, 'curso': self.curso.id, 'materia': fisica.id, 'docente': None, 'ih': 2}])
        self.assertFalse([x for x in intercambio.datos_del_colegio(self.a, sin_docente=False)['asignaciones'] if x['id'] < 0])
        D = nucleo.Datos(d)
        res = nucleo.generar(D, nucleo.condiciones_vacias(), segundos=1, semilla=1)
        self.assertEqual(res['sin_ubicar'], [])
        archivo = json.dumps(nucleo.resultado(D, res['sesiones'], 'Con física')).encode()
        self.cliente(self.rectora).post('/horarios/importar/', {'archivo': SimpleUploadedFile('h.mchr', archivo)})
        h = Horario.objects.get()
        sueltas = Sesion.objects.filter(horario=h, asignacion__isnull=True)
        self.assertEqual(sueltas.count(), 2)
        self.assertTrue(all(s.materia_id == fisica.id for s in sueltas))
        r = self.cliente(self.rectora).get(f'/horarios/{h.pk}/')
        self.assertContains(r, 'sin docente')
        self.assertEqual(r.context['choques'], [])
        # Ahora le asignan docente: la clase se amarra sola
        a = AsignacionDocente.objects.create(colegio=self.a, docente=self.doc2, materia=fisica, curso=self.curso,
                                             intensidad_horaria_semanal=2)
        self.cliente(self.rectora).get(f'/horarios/{h.pk}/')
        self.assertEqual(Sesion.objects.filter(horario=h, asignacion=a).count(), 2)
        # Y ya no sale como «sin docente» en los datos
        self.assertFalse([x for x in intercambio.datos_del_colegio(self.a)['asignaciones'] if x['id'] < 0])

    def test_excel_con_materia_sin_docente(self):
        Materia.objects.create(colegio=self.a, nombre='Química')
        wb = Workbook()
        ws = wb.active
        ws.append(['CURSO', 'DIA', 'HORA', 'MATERIA'])
        ws.append(['601', 'Lunes', 1, 'Matemáticas'])
        ws.append(['601', 'Martes', 2, 'Química'])
        ws.append(['601', 'Miércoles', 1, 'Química'])
        buf = io.BytesIO()
        wb.save(buf)
        r = self.cliente(self.rectora).post('/horarios/importar/', {'archivo': SimpleUploadedFile('h.xlsx', buf.getvalue())},
                                            follow=True)
        self.assertContains(r, 'sin docente')
        h = Horario.objects.get()
        self.assertEqual(h.sesiones.count(), 3)
        self.assertEqual(PlanHoras.objects.get(materia__nombre='Química').horas, 2)
        self.assertEqual(h.informe['choques'], [])
        # El estudiante ve la materia aunque no tenga docente
        h.estado = 'PUBLICADO'
        h.save()
        self.assertContains(self.cliente(self.estudiantes[0].user).get('/horarios/mi-horario/'), 'Química')
