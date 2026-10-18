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


class Ciclo(Base):
    """Horario por días de ciclo: si un día no hay clase, el Día N pasa al siguiente."""

    def test_dias_que_se_corren(self):
        import datetime
        from . import ciclo, reemplazos
        from .models import ConfiguracionHorario, DiaSinClase
        c = self.cliente(self.rectora)
        c.post(f'/horarios/jornada/{self.j.pk}/', {'nombre': 'Mañana', 'tipo_dias': 'ciclo', 'n_ciclo': '6',
                                                   'cursos': [self.curso.id], 'accion': 'guardar'})
        self.j.refresh_from_db()
        self.assertEqual(self.j.dias, [101, 102, 103, 104, 105, 106])
        lunes = datetime.date(2026, 10, 19)
        c.post('/horarios/ciclo/', {'accion': 'config', 'inicio': f'{lunes:%Y-%m-%d}', 'semana': ['1', '2', '3', '4', '5']})
        self.assertEqual(ciclo.dia_del_ciclo(self.a, lunes), 1)
        self.assertEqual(ciclo.dia_del_ciclo(self.a, lunes + datetime.timedelta(days=1)), 2)
        self.assertIsNone(ciclo.dia_del_ciclo(self.a, lunes + datetime.timedelta(days=5)))      # sábado
        self.assertEqual(ciclo.dia_del_ciclo(self.a, lunes + datetime.timedelta(days=7)), 6)    # lunes siguiente
        self.assertEqual(ciclo.dia_del_ciclo(self.a, lunes + datetime.timedelta(days=8)), 1)    # vuelve a empezar
        # El martes no hubo clase: el Día 2 pasa al miércoles
        c.post('/horarios/ciclo/', {'accion': 'sin_clase', 'fecha': f'{lunes + datetime.timedelta(days=1):%Y-%m-%d}',
                                    'motivo': 'Paro'})
        self.assertIsNone(ciclo.dia_del_ciclo(self.a, lunes + datetime.timedelta(days=1)))
        self.assertEqual(ciclo.dia_del_ciclo(self.a, lunes + datetime.timedelta(days=2)), 2)
        self.assertContains(c.get('/horarios/ciclo/'), 'Paro')
        # Las clases del «Día 2» salen el miércoles (asistencia y reemplazos)
        h = Horario.objects.create(colegio=self.a, nombre='Ciclo', estado='PUBLICADO')
        Sesion.objects.create(horario=h, curso=self.curso, asignacion=self.asig, materia=self.materia, dia=102,
                              franja=self.f[0])
        miercoles = lunes + datetime.timedelta(days=2)
        self.assertEqual(len(reemplazos.clases_de_hoy(self.a, self.docente, miercoles)), 1)
        self.assertEqual(len(reemplazos.clases_de_hoy(self.a, self.docente, lunes + datetime.timedelta(days=1))), 0)
        r = self.cliente(self.estudiantes[0].user).get('/horarios/mi-horario/')
        self.assertContains(r, 'Día 2')
        # Un festivo del calendario escolar también corre el ciclo
        from calendario.models import Evento
        Evento.objects.create(colegio=self.a, titulo='Festivo', tipo='FESTIVO', fecha=lunes + datetime.timedelta(days=3))
        self.assertIsNone(ciclo.dia_del_ciclo(self.a, lunes + datetime.timedelta(days=3)))
        self.assertEqual(ciclo.dia_del_ciclo(self.a, lunes + datetime.timedelta(days=4)), 3)
        DiaSinClase.objects.all().delete()
        self.assertTrue(ConfiguracionHorario.objects.get(colegio=self.a).ciclo_inicio)

    def test_excel_con_dias_de_ciclo(self):
        self.j.dias = [101, 102, 103, 104, 105, 106, 107, 108, 109, 110]
        self.j.save()
        wb = Workbook()
        ws = wb.active
        ws.append(['CURSO', 'DIA', 'HORA', 'MATERIA'])
        ws.append(['601', 'Día 9', 1, 'Matemáticas'])
        ws.append(['601', 10, 2, 'Inglés'])
        buf = io.BytesIO()
        wb.save(buf)
        self.cliente(self.rectora).post('/horarios/importar/', {'archivo': SimpleUploadedFile('h.xlsx', buf.getvalue())})
        h = Horario.objects.get()
        self.assertEqual(sorted(h.sesiones.values_list('dia', flat=True)), [109, 110])
        self.assertContains(self.cliente(self.rectora).get(f'/horarios/{h.pk}/'), 'Día 10')
        d = intercambio.datos_del_colegio(self.a)
        self.assertEqual(nucleo.DIAS[d['jornadas'][0]['dias'][-1]], 'Día 10')
