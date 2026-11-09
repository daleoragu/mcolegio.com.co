"""Rediseño de Mi Salón Virtual: Inicio, Sala de Profesores, Mi Espacio, Mis Estudiantes y Planeación."""
from django.contrib.auth.models import User
from django.test import TestCase

from .models import Cuenta, Grupo, PaginaPublicada


class Espacios(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.u = User.objects.create_user('profe', password='x', first_name='David')
        cls.cuenta = Cuenta.objects.create(usuario=cls.u, slug='davidramos', nombre_publico='Prof. David Leonardo',
                                           estado='verificada', plan='ilimitado')
        cls.grupo = Grupo.objects.create(propietario=cls.cuenta, nombre='7-01 Matemáticas')
        cls.pagina = PaginaPublicada.objects.create(propietario=cls.cuenta, titulo='Funciones cuadráticas', slug='funciones',
                                                    identificacion='libre', listar_en_perfil=False)

    def setUp(self):
        self.client.force_login(self.u)

    def test_inicio_con_los_cuatro_espacios(self):
        r = self.client.get('/salon_digital/inicio/')
        self.assertContains(r, 'Hola, Profe David')
        for nombre in ('Sala de Profesores', 'Mi Espacio de Profe', 'Mis Estudiantes', 'Planeación', 'Mis clases activas',
                       'Actividad de la comunidad', '7-01 Matemáticas'):
            self.assertContains(r, nombre)
        self.assertContains(r, 'class="esp-abajo"')                 # barra de abajo en el celular
        self.assertContains(r, 'aria-current="page">Inicio</a>')

    def test_el_menu_marca_el_espacio_de_cada_pagina(self):
        casos = [('/chat/colegas/muro/', 'Sala de Profesores'), ('/salon_digital/mi-espacio/', 'Mi Espacio'),
                 ('/salon_digital/panel/', 'Mi Espacio'), ('/chat/colegas/muro/?ver=guardados', 'Mi Espacio'),
                 ('/aula/', 'Mis Estudiantes'), ('/salon_digital/grupos/', 'Mis Estudiantes'),
                 ('/materiales/', 'Planeación'), ('/aula/instrumentos/', 'Planeación'), ('/aula/banco/', 'Planeación'),
                 ('/puntoexacto/', 'Planeación')]
        for url, espacio in casos:
            r = self.client.get(url)
            self.assertEqual(r.status_code, 200, url)
            self.assertContains(r, f'aria-current="page">{espacio}</a>', msg_prefix=url)

    def test_sala_de_profesores_reacomodada(self):
        from django.utils import timezone
        from chat.views_colegas import perfil_de
        p = perfil_de(self.u)
        p.normas_aceptadas = timezone.now()
        p.save()
        r = self.client.get('/chat/colegas/muro/')
        for texto in ('Navegación', 'Filtros', 'Eventos activos', 'Guía pedagógica', 'Juego interactivo (HTML)'):
            self.assertContains(r, texto)

    def test_mi_espacio_perfil_qr_y_paginas(self):
        r = self.client.get('/salon_digital/mi-espacio/')
        self.assertContains(r, 'Prof. David Leonardo')
        self.assertContains(r, '/p/davidramos')
        self.assertContains(r, 'Visitas a /p/davidramos')
        self.assertEqual(self.client.get('/salon_digital/mi-espacio/qr.png')['Content-Type'], 'image/png')
        r = self.client.get('/salon_digital/mi-espacio/?tab=paginas')
        self.assertContains(r, 'Funciones cuadráticas')
        self.assertContains(r, 'Solo con enlace')
        # el interruptor: pública en mi perfil / solo con enlace
        self.client.post('/salon_digital/mi-espacio/pagina/funciones/visibilidad/', {'publica': '1'}, HTTP_X_REQUESTED_WITH='fetch')
        self.pagina.refresh_from_db()
        self.assertTrue(self.pagina.listar_en_perfil)
        self.client.post('/salon_digital/mi-espacio/pagina/funciones/visibilidad/', {})
        self.pagina.refresh_from_db()
        self.assertFalse(self.pagina.listar_en_perfil)
        # la página de otro docente no se toca
        otro = Cuenta.objects.create(usuario=User.objects.create_user('otro'), slug='otro', nombre_publico='Otro', estado='verificada')
        ajena = PaginaPublicada.objects.create(propietario=otro, titulo='Ajena', slug='ajena', identificacion='libre')
        self.assertEqual(self.client.post('/salon_digital/mi-espacio/pagina/ajena/visibilidad/', {'publica': '1'}).status_code, 404)

    def test_para_hoy_en_el_inicio(self):
        from datetime import timedelta
        from django.utils import timezone
        from aula.models import Aula, ClaseInvertida, Entrega, Tarea
        from salon_digital.models import Integrante
        aula = Aula.objects.create(grupo=self.grupo)
        ana = Integrante.objects.create(grupo=self.grupo, nombres='Ana', apellidos='Ruiz')
        t = Tarea.objects.create(aula=aula, titulo='Taller 1', fecha_limite=timezone.now() + timedelta(hours=2))
        Entrega.objects.create(tarea=t, integrante=ana, entregada=timezone.now())
        ClaseInvertida.objects.create(aula=aula, titulo='Regla de tres', video='https://youtu.be/abcdefghijk')
        r = self.client.get('/salon_digital/inicio/')
        self.assertContains(r, 'Para hoy')
        self.assertContains(r, '1 entrega por calificar')
        self.assertContains(r, '«Taller 1» cierra')
        self.assertContains(r, '1 estudiante no ha visto «Regla de tres»')

    def test_mis_estudiantes_y_planeacion(self):
        from aula.models import Aula
        aula = Aula.objects.create(grupo=self.grupo)
        r = self.client.get(f'/aula/{aula.pk}/')
        self.assertContains(r, 'class="me-grupos"')                   # barra lateral con los grupos
        self.assertContains(r, 'Código ' + self.grupo.codigo)
        self.assertContains(r, 'Panel del Aula')
        r = self.client.get('/materiales/')
        self.assertContains(r, 'Estudio de Planeación')
        self.assertContains(r, 'Importar material')

    def test_editar_perfil_desde_mi_espacio(self):
        r = self.client.get('/salon_digital/mi-espacio/')
        self.assertContains(r, '/chat/colegas/?tab=perfil&volver=/salon_digital/mi-espacio/')
        r = self.client.get('/chat/colegas/?tab=perfil&volver=/salon_digital/mi-espacio/')
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'name="volver" value="/salon_digital/mi-espacio/"')
        self.assertRedirects(self.client.get('/chat/colegas/ajustes/'), '/chat/colegas/?tab=perfil', fetch_redirect_response=False)
        r = self.client.post('/chat/colegas/ajustes/', {'presentacion': 'Apasionado por la geometría', 'visible': 'on',
                                                        'volver': '/salon_digital/mi-espacio/'})
        self.assertRedirects(r, '/salon_digital/mi-espacio/', fetch_redirect_response=False)
        self.assertContains(self.client.get('/salon_digital/mi-espacio/'), 'Apasionado por la geometría')
        r = self.client.post('/chat/colegas/ajustes/', {'volver': '//otro-sitio.com/'})
        self.assertRedirects(r, '/chat/colegas/?tab=perfil', fetch_redirect_response=False)

    def test_al_entrar_llega_al_inicio(self):
        self.client.logout()
        r = self.client.post('/salon_digital/entrar/', {'username': 'profe', 'password': 'x'})
        self.assertRedirects(r, '/salon_digital/inicio/', fetch_redirect_response=False)
