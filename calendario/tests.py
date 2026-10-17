# -*- coding: utf-8 -*-
"""Calendario escolar: crear, quién ve qué, avisos, festivos, Google Calendar / iCal."""
import datetime

from django.utils import timezone

from notas.models import Curso
from notas.models.comunicaciones import Notificacion
from notas.modulos import PLANES
from notas.tests.base import ColegioDePrueba

from . import festivos, logica
from .models import Evento


class Calendario(ColegioDePrueba):

    def test_festivos_de_colombia(self):
        f = dict(festivos.festivos(2026))
        for dia in [(1, 12), (3, 23), (4, 2), (4, 3), (5, 18), (6, 8), (6, 15), (6, 29), (8, 17), (10, 12),
                    (11, 2), (11, 16), (12, 8)]:
            self.assertIn(datetime.date(2026, *dia), f)
        self.assertEqual(len(f), 18)
        self.assertEqual(festivos.pascua(2027), datetime.date(2027, 3, 28))

    def test_crear_con_aviso_y_ver(self):
        c = self.cliente(self.rectora)
        r = c.post('/calendario/nuevo/', {'titulo': 'Izada de bandera', 'tipo': 'IZADA', 'fecha': '2026-10-20',
                                          'hora_inicio': '07:00', 'para': 'TODOS', 'lugar': 'Patio', 'avisar': '1'})
        self.assertEqual(r.status_code, 302)
        e = Evento.objects.get()
        avisados = set(Notificacion.objects.values_list('destinatario_id', flat=True))
        self.assertEqual(avisados, {self.u_docente.id} | {x.user_id for x in self.estudiantes})
        r = self.cliente(self.estudiantes[0].user).get('/calendario/?ano=2026&mes=10')
        self.assertContains(r, 'Izada de bandera')
        r = self.cliente(self.estudiantes[0].user).get(f'/calendario/evento/{e.pk}/')
        self.assertContains(r, 'calendar.google.com')
        self.assertNotContains(r, 'Eliminar')
        # Solo administración edita
        self.assertEqual(self.cliente(self.u_docente).post('/calendario/nuevo/', {'titulo': 'x', 'fecha': '2026-10-20'}).status_code, 403)

    def test_quien_ve_que(self):
        otro = Curso.objects.create(colegio=self.a, nombre='1101', grado=11, subgrupo='1')
        Evento.objects.create(colegio=self.a, titulo='Consejo académico', fecha=datetime.date(2026, 10, 21), para='DOCENTES')
        e = Evento.objects.create(colegio=self.a, titulo='Prueba Saber 11', fecha=datetime.date(2026, 10, 22), para='ESTUDIANTES')
        e.cursos.add(otro)
        est = self.cliente(self.estudiantes[0].user).get('/calendario/?ano=2026&mes=10')
        self.assertNotContains(est, 'Consejo académico')
        self.assertNotContains(est, 'Prueba Saber 11')
        doc = self.cliente(self.u_docente).get('/calendario/?ano=2026&mes=10')
        self.assertContains(doc, 'Consejo académico')
        self.assertContains(doc, 'Prueba Saber 11')
        self.assertEqual(logica.destinatarios(e), set())   # nadie en 1101
        self.assertEqual(self.cliente(self.estudiantes[0].user).get(f'/calendario/evento/{e.pk}/').status_code, 404)

    def test_periodos_salen_solos(self):
        r = self.cliente(self.u_docente).get('/calendario/?ano=2026&mes=4')
        self.assertContains(r, 'Termina el primer periodo')
        self.assertContains(r, 'Inicia el segundo periodo')

    def test_agregar_festivos_una_vez(self):
        c = self.cliente(self.rectora)
        c.post('/calendario/festivos/', {'ano': 2026})
        c.post('/calendario/festivos/', {'ano': 2026})
        self.assertEqual(Evento.objects.filter(tipo='FESTIVO').count(), 18)

    def test_ical_y_suscripcion(self):
        Evento.objects.create(colegio=self.a, titulo='Entrega de boletines, periodo 3', tipo='ENTREGA',
                              fecha=timezone.localdate() + datetime.timedelta(days=3), para='TODOS')
        r = self.cliente(self.u_docente).get('/calendario/calendario-escolar.ics')
        texto = r.content.decode()
        self.assertTrue(texto.startswith('BEGIN:VCALENDAR'))
        self.assertIn('Entrega de boletines\\, periodo 3', texto)
        ficha = logica.ficha_ics(self.estudiantes[0].user, self.a)
        sin_sesion = self.cliente().get(f'/calendario/ical/{ficha}/calendario.ics')
        self.assertEqual(sin_sesion.status_code, 200)
        self.assertIn('VEVENT', sin_sesion.content.decode())
        self.assertEqual(self.cliente().get(f'/calendario/ical/{ficha}x/calendario.ics').status_code, 404)
        # La ficha de un colegio no sirve en otro
        self.assertEqual(self.cliente(host='b.localhost').get(f'/calendario/ical/{ficha}/calendario.ics').status_code, 404)

    def test_modulo(self):
        self.assertNotIn('calendario', PLANES['basico'][1])
        self.assertIn('calendario', PLANES['publico'][1])
        self.a.modulos_activos = ['circulares']
        self.a.save()
        self.assertEqual(self.cliente(self.rectora).get('/calendario/').status_code, 403)
