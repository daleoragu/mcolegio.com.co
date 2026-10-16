# -*- coding: utf-8 -*-
"""Cartera: cobros por grado y con beca, pagos a lo más viejo, mora, paz y salvo y certificados."""
import datetime

from notas.modulos import TODOS
from notas.tests.base import ColegioDePrueba

from . import logica
from .models import Beca, Cargo, Concepto, ConfiguracionCartera, ValorPorGrado


class Cartera(ColegioDePrueba):

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.a.modulos_activos = list(TODOS)
        cls.a.save()
        cls.pension = Concepto.objects.create(colegio=cls.a, nombre='Pensión', tipo='MENSUAL', valor=300000)
        ValorPorGrado.objects.create(concepto=cls.pension, grado=6, valor=350000)
        cls.matricula = Concepto.objects.create(colegio=cls.a, nombre='Matrícula', tipo='UNICO', valor=500000, mes_unico=1)
        conf = ConfiguracionCartera.de(cls.a)
        conf.meses_pension = [2, 3]
        conf.dia_vencimiento = 5
        conf.save()
        cls.ana, cls.beto, _ = cls.estudiantes

    def test_generar_por_grado_sin_duplicar(self):
        n = logica.generar_cargos(self.a, 2026)
        self.assertEqual(n, 9)                         # 3 estudiantes × (2 pensiones + matrícula)
        self.assertEqual(logica.generar_cargos(self.a, 2026), 0)
        c = Cargo.objects.get(estudiante=self.ana, concepto=self.pension, mes=2)
        self.assertEqual((c.valor, c.vence), (350000, datetime.date(2026, 2, 5)))   # valor del grado sexto

    def test_beca(self):
        Beca.objects.create(estudiante=self.beto, concepto=self.pension, porcentaje=50)
        logica.generar_cargos(self.a, 2026)
        self.assertEqual(Cargo.objects.get(estudiante=self.beto, concepto=self.pension, mes=3).neto, 175000)
        self.assertEqual(Cargo.objects.get(estudiante=self.beto, concepto=self.matricula).neto, 500000)

    def test_pago_va_a_lo_mas_viejo_y_sobra_a_favor(self):
        logica.generar_cargos(self.a, 2026)
        p1 = logica.registrar_pago(self.ana, 600000, datetime.date(2026, 2, 10))
        self.assertEqual(p1.numero, 1)
        st = logica.estado(self.ana, hoy=datetime.date(2026, 3, 20))
        self.assertEqual(st['saldo'], 1200000 - 600000)
        # Matrícula (ene) pagada y 100.000 de febrero; queda en mora el resto de febrero y marzo.
        self.assertEqual(st['vencido'], 600000)
        p2 = logica.registrar_pago(self.ana, 700000)
        self.assertEqual(p2.numero, 2)
        self.assertEqual(logica.saldo_a_favor(self.ana), 100000)
        logica.anular_pago(p2)
        self.assertEqual(logica.saldo_a_favor(self.ana), 0)
        self.assertEqual(logica.estado(self.ana)['saldo'], 600000)

    def test_paz_y_salvo_y_certificados(self):
        logica.generar_cargos(self.a, 2026)
        conf = ConfiguracionCartera.de(self.a)
        conf.exigir_paz_y_salvo = True
        conf.save()
        fam = self.cliente(self.ana.user)
        r = fam.post('/certificados/mis-certificados/pedir/', {'tipo': 'ESTUDIO'}, follow=True)
        self.assertContains(r, 'paz y salvo')
        self.assertEqual(fam.get(f'/cartera/estudiante/{self.ana.id}/paz-y-salvo.pdf').status_code, 302)
        logica.registrar_pago(self.ana, 1200000)
        self.assertEqual(logica.bloqueo_certificados(self.ana), 0)
        r = fam.get(f'/cartera/estudiante/{self.ana.id}/paz-y-salvo.pdf')
        self.assertEqual(r['Content-Type'], 'application/pdf')

    def test_pantallas(self):
        c = self.cliente(self.rectora)
        r = c.post('/cartera/', {'accion': 'generar', 'ano': 2026})
        self.assertEqual(Cargo.objects.count(), 9)
        self.assertContains(c.get('/cartera/'), 'Cartera total')
        r = c.post(f'/cartera/estudiante/{self.ana.id}/', {'accion': 'pago', 'valor': 500000, 'fecha': '2026-02-01',
                                                            'medio': 'NEQUI', 'referencia': 'M123'})
        self.assertEqual(r.status_code, 302)
        pago = self.ana.pagos.get()
        self.assertEqual(c.get(f'/cartera/recibo/{pago.id}.pdf')['Content-Type'], 'application/pdf')
        self.assertEqual(self.cliente(self.ana.user).get(f'/cartera/recibo/{pago.id}.pdf').status_code, 200)
        self.assertEqual(self.cliente(self.beto.user).get(f'/cartera/recibo/{pago.id}.pdf').status_code, 403)
        self.assertContains(self.cliente(self.ana.user).get('/cartera/mi-cuenta/'), 'Mi estado de cuenta')
        self.assertEqual(self.cliente(self.u_docente).get('/cartera/').status_code, 403)

    def test_modulo_apagado(self):
        self.a.modulos_activos = [m for m in TODOS if m != 'cartera']
        self.a.save()
        self.assertEqual(self.cliente(self.rectora).get('/cartera/').status_code, 403)
        self.assertNotContains(self.cliente(self.rectora).get('/panel-administrador/'), 'Cartera y pensiones')
