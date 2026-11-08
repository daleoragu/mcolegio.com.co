"""Planes Gratis, Estándar y Premium: prueba Premium al registrarse, vuelta a Gratis y límites por función."""
from datetime import timedelta

from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.utils import timezone

from aula.models import Evento
from materiales.creditos import plan_de
from materiales.models import Documento

from .limites import marca_pdf
from .models import Cuenta, Grupo


class Planes(TestCase):

    def setUp(self):
        self.u = User.objects.create_user('profe', password='x', first_name='Ana', last_name='Profe')
        self.cuenta = Cuenta.objects.create(usuario=self.u, nombre_publico='Ana Profe', estado='verificada')
        self.c = Client(HTTP_HOST='localhost'); self.c.force_login(self.u)

    def poner(self, plan, dias=30):
        self.cuenta.plan = plan
        self.cuenta.vence_en = timezone.localdate() + timedelta(days=dias) if dias is not None else None
        self.cuenta.save()

    def test_prueba_premium_y_vuelta_a_gratis(self):
        self.assertEqual((self.cuenta.plan, self.cuenta.nivel, self.cuenta.en_prueba), ('prueba', 'premium', True))
        self.assertEqual(self.cuenta.nombre_nivel, 'Prueba Premium')
        self.poner('prueba', -1)
        self.assertEqual((self.cuenta.nivel, self.cuenta.activa), ('gratis', True))     # no se bloquea: pasa a Gratis
        self.poner('estandar', -3)
        self.assertEqual(self.cuenta.nivel, 'gratis')
        self.poner('mensual', 10)                                                         # plan de antes
        self.assertEqual(self.cuenta.nivel, 'estandar')
        self.poner('gratis', None)
        self.assertEqual(self.cuenta.nivel, 'gratis')
        self.assertContains(self.c.get('/salon_digital/pagos/'), 'Gratis para siempre'.split()[0])

    def test_limites_de_gratis(self):
        self.poner('gratis', None)
        # 1 grupo
        Grupo.objects.create(propietario=self.cuenta, nombre='7-01')
        r = self.c.get('/salon_digital/grupos/nuevo/')
        self.assertRedirects(r, '/salon_digital/pagos/?plan=estandar&para=grupos', fetch_redirect_response=False)
        # 10 materiales
        for i in range(10):
            Documento.objects.create(propietario=self.u, colegio=None, titulo=f'Guía {i}', contenido={})
        r = self.c.post('/materiales/nuevo/', {'tipo': 'libre', 'titulo': 'Once'})
        self.assertRedirects(r, '/salon_digital/pagos/?plan=estandar&para=materiales', fetch_redirect_response=False)
        self.assertEqual(Documento.objects.filter(propietario=self.u).count(), 10)
        # Exámenes: de Estándar
        r = self.c.get('/puntoexacto/nuevo/')
        self.assertRedirects(r, '/salon_digital/pagos/?plan=estandar&para=examenes', fetch_redirect_response=False)
        # Eventos: de Premium
        self.assertContains(self.c.get('/aula/eventos/'), 'son del plan Premium')
        self.c.post('/aula/eventos/', {'titulo': 'Olimpiada'})
        self.assertFalse(Evento.objects.exists())
        # PDF con el pie «Hecho con mcolegio» e IA del plan Gratis
        self.assertTrue(marca_pdf(Documento.objects.first()))
        self.assertEqual(plan_de(self.u, None), 'gratis')
        self.assertContains(self.c.get('/salon_digital/pagos/?para=eventos'), 'son del plan <b>Premium</b>')

    def test_estandar_y_premium(self):
        self.poner('estandar')
        Grupo.objects.create(propietario=self.cuenta, nombre='7-01')
        self.assertEqual(self.c.get('/salon_digital/grupos/nuevo/').status_code, 200)
        self.assertEqual(self.c.get('/puntoexacto/nuevo/').status_code, 200)
        self.c.post('/aula/eventos/', {'titulo': 'Olimpiada'})
        self.assertFalse(Evento.objects.exists())                       # Estándar no tiene eventos
        doc = Documento.objects.create(propietario=self.u, colegio=None, titulo='Guía', contenido={})
        self.assertFalse(marca_pdf(doc))
        self.assertEqual(plan_de(self.u, None), 'individual')
        self.poner('premium')
        self.c.post('/aula/eventos/', {'titulo': 'Olimpiada'})
        ev = Evento.objects.get()
        self.assertEqual(plan_de(self.u, None), 'individual_ia')
        # Si Premium vence, ya no puede encender el evento (sí apagarlo)
        self.poner('premium', -1)
        r = self.c.post(f'/aula/eventos/{ev.pk}/configurar/', {'accion': 'activar'})
        ev.refresh_from_db(); self.assertFalse(ev.activo)
        self.assertIn('para=eventos', r['Location'])

    def test_landing_y_admin(self):
        r = Client(HTTP_HOST='localhost').get('/salon_digital/')
        self.assertContains(r, 'Premium'); self.assertContains(r, '$16.000'); self.assertContains(r, 'Probar Premium gratis')
        admin = User.objects.create_user('adm', password='x', is_staff=True)
        a = Client(HTTP_HOST='localhost'); a.force_login(admin)
        a.post(f'/salon_digital/revision/{self.cuenta.pk}/plan/', {'plan': 'premium_anio'})
        self.cuenta.refresh_from_db()
        self.assertEqual(self.cuenta.nivel, 'premium')
        self.assertGreaterEqual(self.cuenta.dias_restantes, 365)
