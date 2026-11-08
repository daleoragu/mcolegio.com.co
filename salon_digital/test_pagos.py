"""Planes y pagos: en línea con Wompi y con comprobante (llave Bre-B, Nequi o transferencia)."""
import hashlib
import json
import os
import shutil
import tempfile
from unittest import mock

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings

from materiales.models import CuentaIA
from notas.models import Notificacion

from .models import Cuenta, Pago

MEDIA = tempfile.mkdtemp(prefix='salon-pagos-')
WOMPI = {'WOMPI_PUBLIC_KEY': 'pub_test_x', 'WOMPI_INTEGRITY_SECRET': 'int', 'WOMPI_EVENTS_SECRET': 'ev',
         'SALON_LLAVE_BREB': '@mcolegio', 'SALON_NEQUI': '3006034800', 'SALON_PAGO_TITULAR': 'mcolegio'}


@override_settings(MEDIA_ROOT=MEDIA)
class Pagos(TestCase):

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(MEDIA, ignore_errors=True)

    def setUp(self):
        self.u = User.objects.create_user('profe', password='x', email='profe@correo.co')
        self.cuenta = Cuenta.objects.create(usuario=self.u, nombre_publico='Profe Pérez', estado='verificada')
        self.c = Client(HTTP_HOST='localhost'); self.c.force_login(self.u)
        self.admin = User.objects.create_user('admin', password='x', is_staff=True)
        self.a = Client(HTTP_HOST='localhost'); self.a.force_login(self.admin)

    def test_pagina_y_accesos(self):
        r = self.c.get('/salon_digital/pagos/')
        for t in ('Planes y pagos', 'Plan mensual', 'Plan anual', 'Recarga de saldo', 'PSE', 'Llave Bre-B', 'Tarjeta crédito'):
            self.assertContains(r, t)
        self.assertContains(self.c.get('/salon_digital/panel/cuenta/'), '/salon_digital/pagos/')
        # Aviso cuando la prueba está por terminar
        self.assertContains(self.c.get('/salon_digital/panel/cuenta/'), 'Su prueba gratuita termina')

    @mock.patch.dict(os.environ, WOMPI)
    def test_pago_en_linea_con_wompi(self):
        r = self.c.post('/salon_digital/pagos/', {'concepto': 'anual', 'forma': 'linea'})
        self.assertTrue(r['Location'].startswith('https://checkout.wompi.co/p/'))
        p = Pago.objects.get()
        self.assertEqual((p.monto, p.forma, p.estado), (80000, 'linea', 'pendiente'))
        self.assertIn('amount-in-cents=8000000', r['Location'])
        # El aviso firmado de Wompi lo aprueba y activa el plan anual
        datos = {'transaction': {'id': 'T1', 'reference': p.referencia, 'status': 'APPROVED', 'amount_in_cents': 8000000,
                                 'payment_method_type': 'PSE'}}
        props = ['transaction.id', 'transaction.status', 'transaction.amount_in_cents']
        ts = 1700000000
        firma = hashlib.sha256(('T1APPROVED8000000' + str(ts) + 'ev').encode()).hexdigest()
        cuerpo = {'event': 'transaction.updated', 'data': datos, 'timestamp': ts, 'signature': {'properties': props, 'checksum': firma}}
        self.assertEqual(Client().post('/materiales/pagos/wompi/eventos/', json.dumps(cuerpo), content_type='application/json').status_code, 200)
        p.refresh_from_db(); self.cuenta.refresh_from_db()
        self.assertEqual((p.estado, p.medio, self.cuenta.plan), ('aprobado', 'PSE', 'anual'))
        self.assertTrue(Notificacion.objects.filter(destinatario=self.u, mensaje__contains='Pago aprobado').exists())
        # Repetir el aviso no activa dos veces
        vence = self.cuenta.vence_en
        Client().post('/materiales/pagos/wompi/eventos/', json.dumps(cuerpo), content_type='application/json')
        self.cuenta.refresh_from_db(); self.assertEqual(self.cuenta.vence_en, vence)

    @mock.patch.dict(os.environ, WOMPI)
    def test_monto_alterado_no_activa(self):
        self.c.post('/salon_digital/pagos/', {'concepto': 'mensual', 'forma': 'linea'})
        from salon_digital import pagos as P
        p = P.aplicar_wompi(Pago.objects.get().referencia, 'APPROVED', 'T2', 100, 'CARD')
        self.assertEqual(p.estado, 'pendiente'); self.cuenta.refresh_from_db(); self.assertEqual(self.cuenta.plan, 'prueba')

    @mock.patch.dict(os.environ, WOMPI)
    def test_comprobante_llave_bre_b(self):
        r = self.c.post('/salon_digital/pagos/', {'concepto': 'mensual', 'forma': 'comprobante'})
        p = Pago.objects.get()
        self.assertRedirects(r, f'/salon_digital/pagos/{p.referencia}/', fetch_redirect_response=False)
        pagina = self.c.get(r['Location'])
        self.assertContains(pagina, '@mcolegio'); self.assertContains(pagina, '3006034800'); self.assertContains(pagina, p.referencia)
        foto = SimpleUploadedFile('pago.jpg', b'\xff\xd8\xff' + b'0' * 100, content_type='image/jpeg')
        self.c.post(r['Location'], {'medio': 'Llave Bre-B', 'comprobante': foto})
        p.refresh_from_db(); self.assertEqual((p.estado, p.medio), ('revision', 'Llave Bre-B'))
        self.assertTrue(Notificacion.objects.filter(destinatario=self.admin, mensaje__contains='Pago por revisar').exists())
        # Otro docente no ve el comprobante; el administrador sí
        otro = User.objects.create_user('otro', password='x'); co = Client(HTTP_HOST='localhost'); co.force_login(otro)
        self.assertEqual(co.get(f'/salon_digital/pagos/comprobante/{p.pk}/').status_code, 404)
        self.assertEqual(self.a.get(f'/salon_digital/pagos/comprobante/{p.pk}/').status_code, 200)
        # Solo administradores revisan
        self.assertEqual(self.c.get('/salon_digital/pagos/revisar/').status_code, 302)
        self.assertContains(self.a.get('/salon_digital/pagos/revisar/'), 'Profe Pérez')
        self.a.post('/salon_digital/pagos/revisar/', {'pago': p.pk, 'decision': 'aprobar'})
        p.refresh_from_db(); self.cuenta.refresh_from_db()
        self.assertEqual((p.estado, self.cuenta.plan), ('aprobado', 'mensual'))

    def test_recarga_con_comprobante_y_rechazo(self):
        self.c.post('/salon_digital/pagos/', {'concepto': 'recarga', 'monto': 20000, 'forma': 'comprobante'})
        p = Pago.objects.get(); self.assertEqual((p.monto, p.bono), (20000, 1000))
        self.c.post(f'/salon_digital/pagos/{p.referencia}/', {'comprobante': SimpleUploadedFile('x.pdf', b'%PDF-1.4', content_type='application/pdf')})
        self.a.post('/salon_digital/pagos/revisar/', {'pago': p.pk, 'decision': 'rechazar', 'nota': 'El valor no coincide.'})
        p.refresh_from_db(); self.assertEqual(p.estado, 'rechazado')
        self.assertContains(self.c.get('/salon_digital/pagos/'), 'El valor no coincide')
        # Sube otro y se aprueba: saldo + bono
        self.c.post(f'/salon_digital/pagos/{p.referencia}/', {'comprobante': SimpleUploadedFile('y.pdf', b'%PDF-1.4', content_type='application/pdf')})
        self.a.post('/salon_digital/pagos/revisar/', {'pago': p.pk, 'decision': 'aprobar'})
        self.assertEqual(CuentaIA.objects.get(usuario=self.u).saldo, 21000)
        # Un archivo que no es foto ni PDF no se acepta
        self.c.post('/salon_digital/pagos/', {'concepto': 'mensual', 'forma': 'comprobante'})
        q = Pago.objects.filter(estado='pendiente').get()
        self.c.post(f'/salon_digital/pagos/{q.referencia}/', {'comprobante': SimpleUploadedFile('v.exe', b'MZ', content_type='application/octet-stream')})
        q.refresh_from_db(); self.assertEqual(q.estado, 'pendiente')

    def test_valores_invalidos(self):
        self.c.post('/salon_digital/pagos/', {'concepto': 'recarga', 'monto': 7, 'forma': 'comprobante'})
        self.c.post('/salon_digital/pagos/', {'concepto': 'gratis', 'forma': 'comprobante'})
        self.assertFalse(Pago.objects.exists())
