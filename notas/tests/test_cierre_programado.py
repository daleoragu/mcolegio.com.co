# -*- coding: utf-8 -*-
"""Plazos de periodo que se cierran solos a una fecha y hora."""
import datetime

from django.core.cache import cache
from django.utils import timezone

from notas import plazos
from notas.models import Notificacion, PeriodoAcademico
from notas.tests.base import ColegioDePrueba


class CierreProgramado(ColegioDePrueba):

    def setUp(self):
        cache.clear()

    def _post(self, **datos):
        datos.setdefault('periodo_id', self.p1.id)
        return self.cliente(self.rectora).post('/admin/panel-control-periodos/', datos)

    def test_programar_y_cerrar_solo_al_vencer(self):
        manana = timezone.localtime() + datetime.timedelta(days=1)
        self._post(action='programar_cierre', item='notas', fecha=manana.strftime('%Y-%m-%dT%H:%M'))
        p = PeriodoAcademico.objects.get(id=self.p1.id)
        self.assertTrue(p.esta_activo)
        self.assertIsNotNone(p.cierre_notas)
        self.assertEqual(plazos.aplicar_cierres(self.a), 0)          # todavía no
        self.assertEqual(plazos.aplicar_cierres(self.a, ahora=p.cierre_notas + datetime.timedelta(minutes=1)), 1)
        p.refresh_from_db()
        self.assertFalse(p.esta_activo)
        self.assertIsNone(p.cierre_notas)
        self.assertTrue(Notificacion.objects.filter(destinatario=self.u_docente, mensaje__contains='como estaba programado').exists())

    def test_programar_un_plazo_cerrado_lo_abre(self):
        PeriodoAcademico.objects.filter(id=self.p1.id).update(nivelaciones_activas=False)
        fecha = (timezone.localtime() + datetime.timedelta(days=2)).strftime('%Y-%m-%dT%H:%M')
        self._post(action='programar_cierre', item='nivelaciones', fecha=fecha)
        self.assertTrue(PeriodoAcademico.objects.get(id=self.p1.id).nivelaciones_activas)

    def test_fecha_pasada_no_se_acepta(self):
        ayer = (timezone.localtime() - datetime.timedelta(days=1)).strftime('%Y-%m-%dT%H:%M')
        self._post(action='programar_cierre', item='reporte', fecha=ayer)
        self.assertIsNone(PeriodoAcademico.objects.get(id=self.p1.id).cierre_reporte_parcial)

    def test_cancelar_y_cerrar_a_mano_quitan_el_programado(self):
        fecha = timezone.now() + datetime.timedelta(days=1)
        PeriodoAcademico.objects.filter(id=self.p1.id).update(cierre_notas=fecha, cierre_reporte_parcial=fecha)
        self._post(action='cancelar_cierre', item='notas')
        self._post(action='toggle_reporte_parcial')
        p = PeriodoAcademico.objects.get(id=self.p1.id)
        self.assertIsNone(p.cierre_notas)
        self.assertTrue(p.esta_activo)
        self.assertFalse(p.reporte_parcial_activo)
        self.assertIsNone(p.cierre_reporte_parcial)

    def test_el_middleware_cierra_lo_vencido(self):
        PeriodoAcademico.objects.filter(id=self.p1.id).update(
            esta_activo=True, cierre_notas=timezone.now() - datetime.timedelta(minutes=5))
        self.cliente(self.u_docente).get('/')
        self.assertFalse(PeriodoAcademico.objects.get(id=self.p1.id).esta_activo)

    def test_el_panel_muestra_el_reloj_y_la_fecha(self):
        fecha = timezone.make_aware(datetime.datetime(2030, 3, 5, 18, 0))
        PeriodoAcademico.objects.filter(id=self.p1.id).update(cierre_notas=fecha)
        r = self.cliente(self.rectora).get('/admin/panel-control-periodos/')
        self.assertContains(r, 'Se cierra el 05/03/2030 06:00 PM')
        self.assertContains(r, 'data-fecha="2030-03-05T18:00"')
        self.assertContains(r, 'cierreModal')
