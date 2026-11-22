# -*- coding: utf-8 -*-
"""Mi banco de materiales también muestra los HTML que sube el docente del plan individual."""
from django.contrib.auth.models import User
from django.test import Client, TestCase

from salon_digital.models import Cuenta, PaginaPublicada


class BancoConHtml(TestCase):

    def setUp(self):
        self.u = User.objects.create_user('profe', password='x', first_name='Ana', last_name='Profe')
        self.cuenta = Cuenta.objects.create(usuario=self.u, slug='ana', nombre_publico='Ana Profe', estado='verificada',
                                            plan='ilimitado')
        self.c = Client(HTTP_HOST='localhost')
        self.c.force_login(self.u)

    def test_sin_html_invita_a_subir(self):
        r = self.c.get('/materiales/?ver=banco')
        self.assertContains(r, 'Mis actividades HTML')
        self.assertContains(r, 'Todavía no ha subido actividades HTML')
        self.assertContains(r, '/salon_digital/panel/nueva/')

    def test_sus_html_salen_en_el_banco(self):
        PaginaPublicada.objects.create(propietario=self.cuenta, titulo='Juego de fracciones', slug='fracciones')
        otro = User.objects.create_user('otro', password='x')
        ajena = Cuenta.objects.create(usuario=otro, slug='otro', nombre_publico='Otro', estado='verificada')
        PaginaPublicada.objects.create(propietario=ajena, titulo='Taller ajeno', slug='ajeno')
        r = self.c.get('/materiales/')                      # con un HTML, abre directo en «Mi banco»
        self.assertContains(r, 'Juego de fracciones')
        self.assertContains(r, '/p/ana/fracciones/')
        self.assertContains(r, 'data-tipo="pagina"')       # se puede compartir
        self.assertNotContains(r, 'Taller ajeno')
        self.assertEqual(r.context['total_banco'], 1)
