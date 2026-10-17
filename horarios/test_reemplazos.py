# -*- coding: utf-8 -*-
"""Reemplazos y asistencia por hora. Sin horario publicado todo sigue como antes."""
import datetime
import json

from django.contrib.auth.models import User

from notas.models import Docente
from notas.models.comunicaciones import Notificacion
from notas.tests.base import CLAVE

from . import reemplazos
from .models import Horario, Reemplazo, Sesion
from .tests import Base

LUNES = datetime.date(2026, 10, 19)


class Reemplazos(Base):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        u = User.objects.create_user('libre', password=CLAVE, first_name='Luis', last_name='Libre')
        cls.doc3 = Docente.objects.create(colegio=cls.a, user=u)

    def _publicar(self):
        h = Horario.objects.create(colegio=self.a, nombre='Oficial', estado='PUBLICADO')
        s1 = Sesion.objects.create(horario=h, curso=self.curso, asignacion=self.asig, dia=1, franja=self.f[0])
        Sesion.objects.create(horario=h, curso=self.curso, asignacion=self.asig2, dia=1, franja=self.f[1])
        return h, s1

    def test_sin_horario_todo_igual(self):
        c = self.cliente(self.rectora)
        self.assertContains(c.get('/horarios/reemplazos/'), 'publicado')
        r = self.cliente(self.u_docente).get(f'/docente/asistencia/?fecha={LUNES:%Y-%m-%d}')
        self.assertEqual(r.status_code, 200)
        self.assertNotContains(r, 'Sus clases de este día')
        self.assertEqual(r.context['clases_hoy'], [])

    def test_sugerir_guardar_y_avisar(self):
        h, s1 = self._publicar()
        c = self.cliente(self.rectora)
        r = c.get(f'/horarios/reemplazos/?fecha={LUNES:%Y-%m-%d}&docente={self.docente.pk}')
        plan = r.context['plan']
        self.assertEqual(len(plan), 1)
        cands = [x['docente'] for x in plan[0]['candidatos']]
        # Inés está en el colegio ese día y conoce el curso: va primero. Luis también está libre.
        self.assertEqual(cands[0], self.doc2)
        self.assertIn(self.doc3, cands)
        self.assertNotIn(self.docente, cands)
        c.post('/horarios/reemplazos/', {'fecha': f'{LUNES:%Y-%m-%d}', 'docente': self.docente.pk,
                                         f'r_{s1.id}': self.doc2.pk, f'n_{s1.id}': 'Guía pág. 40', 'accion': 'guardar'})
        rem = Reemplazo.objects.get()
        self.assertEqual((rem.reemplazante, rem.ausente, rem.nota), (self.doc2, self.docente, 'Guía pág. 40'))
        aviso = Notificacion.objects.get(destinatario=self.doc2.user)
        self.assertIn('601', aviso.mensaje)
        # Guardar otra vez sin cambios no repite el aviso
        c.post('/horarios/reemplazos/', {'fecha': f'{LUNES:%Y-%m-%d}', 'docente': self.docente.pk,
                                         f'r_{s1.id}': self.doc2.pk, f'n_{s1.id}': 'Guía pág. 40', 'accion': 'guardar'})
        self.assertEqual(Notificacion.objects.filter(destinatario=self.doc2.user).count(), 1)
        # Inés ya no aparece libre a esa hora para otra ausencia; el ausente tampoco
        self.assertEqual(reemplazos.ausentes(self.a, LUNES), {self.docente.id})
        # Inés ve el reemplazo y puede tomar la asistencia de esa clase ese día
        ci = self.cliente(self.doc2.user)
        self.assertContains(ci.get('/horarios/mi-horario/'), 'Reemplazos que le tocan')
        r = ci.get(f'/docente/asistencia/?fecha={LUNES:%Y-%m-%d}&asignacion_id={self.asig.id}')
        self.assertTrue(r.context['mostrar_lista'])
        self.assertContains(r, 'reemplazo')
        ok = ci.post('/ajax/guardar-inasistencia/', json.dumps({
            'estudiante_id': self.estudiantes[0].id, 'asignacion_id': self.asig.id,
            'fecha': f'{LUNES:%Y-%m-%d}', 'estado': 'A'}), content_type='application/json')
        self.assertEqual(ok.status_code, 200, ok.content)
        # Otro día no
        otro = LUNES + datetime.timedelta(days=7)
        r = ci.get(f'/docente/asistencia/?fecha={otro:%Y-%m-%d}&asignacion_id={self.asig.id}')
        self.assertFalse(r.context['mostrar_lista'])
        # El docente ausente ya no tiene esa clase en su lista del día
        self.assertEqual(reemplazos.clases_de_hoy(self.a, self.docente, LUNES), [])
        # Quitar la ausencia
        c.post('/horarios/reemplazos/', {'fecha': f'{LUNES:%Y-%m-%d}', 'docente': self.docente.pk, 'accion': 'quitar'})
        self.assertFalse(Reemplazo.objects.exists())

    def test_asistencia_por_hora(self):
        self._publicar()
        r = self.cliente(self.u_docente).get(f'/docente/asistencia/?fecha={LUNES:%Y-%m-%d}')
        self.assertContains(r, 'Sus clases de este día')
        self.assertEqual([c['asignacion'] for c in r.context['clases_hoy']], [self.asig])
        clases = reemplazos.clases_de_hoy(self.a, self.docente, LUNES)
        self.assertEqual(reemplazos.clase_en_curso(clases, datetime.time(6, 55))['asignacion'], self.asig)
        self.assertEqual(reemplazos.clase_en_curso(clases, datetime.time(7, 30))['asignacion'], self.asig)
        self.assertIsNone(reemplazos.clase_en_curso(clases, datetime.time(8, 0)))
        # Si el módulo de horarios está apagado, nada cambia
        self.a.modulos_activos = [m for m in self.a.modulos_activos if m != 'horarios']
        self.a.save()
        r = self.cliente(self.u_docente).get(f'/docente/asistencia/?fecha={LUNES:%Y-%m-%d}')
        self.assertNotContains(r, 'Sus clases de este día')


class Disponibilidad(Base):

    def test_pedir_marcar_y_llega_al_generador(self):
        from . import intercambio
        from .models import Disponibilidad as Disp
        doc = self.cliente(self.u_docente)
        r = doc.get('/horarios/mi-disponibilidad/')
        self.assertContains(r, 'no está recogiendo')
        c = self.cliente(self.rectora)
        c.post('/horarios/disponibilidad/', {'pedir': '1', 'mensaje': 'Horario 2027', 'fecha_limite': '2026-11-20'})
        self.assertTrue(Notificacion.objects.filter(destinatario=self.u_docente, url='/horarios/mi-disponibilidad/').exists())
        self.assertContains(doc.get('/horarios/mi-horario/'), 'Marcar mi disponibilidad')
        clave = f'1-{self.f[0].id}'
        doc.post('/horarios/mi-disponibilidad/', {f'c_{clave}': 'no', f'c_2-{self.f[1].id}': 'pref',
                                                  f'c_3-{self.f[2].id}': 'no',            # descanso: no cuenta
                                                  'dia_libre': '1', 'nota': 'Lunes temprano no'})
        d = Disp.objects.get(docente=self.docente)
        self.assertEqual(d.celdas, {clave: 'no', f'2-{self.f[1].id}': 'pref'})
        self.assertContains(c.get('/horarios/disponibilidad/'), 'Lunes temprano no')
        datos = intercambio.datos_del_colegio(self.a)
        self.assertEqual(datos['disponibilidad'][str(self.docente.id)]['no_puede'], [clave])
        self.assertTrue(datos['disponibilidad'][str(self.docente.id)]['dia_libre'])
        # Solo docentes
        self.assertEqual(self.cliente(self.estudiantes[0].user).get('/horarios/mi-disponibilidad/').status_code, 302)

    def test_otras_tareas_en_mi_horario(self):
        h = Horario.objects.create(colegio=self.a, nombre='Oficial', estado='PUBLICADO', informe={
            'acompanamientos': [{'dia': 1, 'franja': self.f[2].id, 'zona': 'Patio', 'docentes': [self.docente.id]}],
            'actividades': [{'dia': 2, 'franja': self.f[3].id, 'nombre': 'Atención a padres', 'docente': self.docente.id}]})
        Sesion.objects.create(horario=h, curso=self.curso, asignacion=self.asig, dia=1, franja=self.f[0])
        r = self.cliente(self.u_docente).get('/horarios/mi-horario/')
        self.assertContains(r, 'Acompañamiento de descanso · Patio')
        self.assertContains(r, 'Atención a padres')
        self.assertNotContains(self.cliente(self.doc2.user).get('/horarios/mi-horario/'), 'Patio')
