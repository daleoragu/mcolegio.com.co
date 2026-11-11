"""Tablero de la clase: pantalla infinita, imágenes, compartir con un grupo y permisos de escritura de los estudiantes."""
import io
import json

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase

from aula import tablero as TB
from aula.models import Aula, TableroClase
from salon_digital.models import Cuenta, Grupo, Integrante


def png():
    from PIL import Image
    b = io.BytesIO()
    Image.new('RGB', (40, 30), '#2563eb').save(b, 'PNG')
    return SimpleUploadedFile('foto.png', b.getvalue(), content_type='image/png')


class Tablero(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.u = User.objects.create_user('profe', password='x')
        cls.cuenta = Cuenta.objects.create(usuario=cls.u, slug='profe', nombre_publico='Profe', estado='verificada', plan='ilimitado')
        cls.grupo = Grupo.objects.create(propietario=cls.cuenta, nombre='7-01')
        cls.aula = Aula.objects.create(grupo=cls.grupo)
        cls.ana = Integrante.objects.create(grupo=cls.grupo, nombres='Ana', apellidos='Ruiz')
        cls.beto = Integrante.objects.create(grupo=cls.grupo, nombres='Beto', apellidos='Paz')

    def setUp(self):
        self.d = Client(HTTP_HOST='localhost')
        self.d.force_login(self.u)

    def estudiante(self, integrante):
        c = Client(HTTP_HOST='localhost')
        s = c.session
        s['salon_identidad'] = {'integrante': integrante.pk, 'grupo': self.grupo.pk, 'nombre': 'x', 'grupo_nombre': '7-01'}
        s.save()
        return c

    def op(self, cliente, t, datos):
        return cliente.post(f'/aula/tablero/{t.pk}/op/', json.dumps(datos), content_type='application/json')

    def trazo(self, oid):
        return {'op': 'agregar', 'obj': {'id': oid, 't': 'trazo', 'c': '#dc2626', 'g': 3, 'p': [[0, 0], [50000, 20.25]]}}

    def test_crear_dibujar_imagen_y_estado(self):
        r = self.d.post('/salon_digital/pizarra/tablero/', {'titulo': 'Fracciones'})
        t = TableroClase.objects.get()
        self.assertRedirects(r, f'/salon_digital/pizarra/tablero/{t.pk}/', fetch_redirect_response=False)
        self.assertContains(self.d.get(f'/salon_digital/pizarra/tablero/{t.pk}/'), 'tb-lienzo')
        self.assertEqual(self.op(self.d, t, self.trazo('a1')).json()['v'], 1)
        self.op(self.d, t, self.trazo('a1'))                                   # repetido: no se duplica
        j = self.d.post(f'/aula/tablero/{t.pk}/imagen/', {'imagen': png()}).json()
        self.assertTrue(j['ok'])
        self.assertEqual(self.d.get(j['url']).status_code, 200)
        self.op(self.d, t, {'op': 'agregar', 'obj': {'id': 'im1', 't': 'imagen', 'img': j['id'], 'x': 10, 'y': 10, 'w': 400, 'h': 300}})
        t.refresh_from_db()
        self.assertEqual([o['id'] for o in t.objetos], ['a1', 'im1'])
        self.assertEqual(t.objetos[0]['p'][1], [50000.0, 20.2])               # coordenadas lejanas: pantalla infinita
        e = self.d.get(f'/aula/tablero/{t.pk}/estado/?desde=1').json()
        self.assertEqual([o['op'] for o in e['ops']], ['agregar'])            # solo lo nuevo
        self.assertEqual(self.d.get(f'/aula/tablero/{t.pk}/estado/?desde=2').json().keys() >= {'v'}, True)
        # Validación: tipos, colores e imágenes de otro tablero
        self.assertEqual(self.op(self.d, t, {'op': 'agregar', 'obj': {'id': 'x', 't': 'script'}}).status_code, 400)
        otro = TableroClase.objects.create(autor=self.u)
        img_otro = self.d.post(f'/aula/tablero/{otro.pk}/imagen/', {'imagen': png()}).json()['id']
        self.assertEqual(self.op(self.d, t, {'op': 'agregar', 'obj': {'id': 'im2', 't': 'imagen', 'img': img_otro, 'x': 0, 'y': 0, 'w': 9, 'h': 9}}).status_code, 400)

    def test_compartir_y_permisos_de_los_estudiantes(self):
        t = TableroClase.objects.create(autor=self.u, titulo='Clase')
        ana, beto = self.estudiante(self.ana), self.estudiante(self.beto)
        # Sin compartir, el estudiante no lo ve
        self.assertEqual(ana.get(f'/aula/tablero/{t.pk}/estado/').status_code, 404)
        r = self.d.post(f'/salon_digital/pizarra/tablero/{t.pk}/compartir/', {'aula': self.aula.pk, 'editan': '0'})
        self.assertTrue(r.json()['compartido'])
        self.assertContains(ana.get(f'/aula/{self.aula.pk}/'), 'Tablero en vivo: Clase')
        self.assertContains(ana.get(f'/aula/{self.aula.pk}/tablero/{t.pk}/'), 'tb-lienzo')
        # Solo ver: no puede escribir ni subir imágenes
        self.assertEqual(self.op(ana, t, self.trazo('e1')).status_code, 403)
        self.assertEqual(ana.post(f'/aula/tablero/{t.pk}/imagen/', {'imagen': png()}).status_code, 403)
        self.assertFalse(ana.get(f'/aula/tablero/{t.pk}/estado/').json()['editar'])
        # El docente habilita la escritura: Ana escribe; Beto no puede borrar ni mover lo de Ana; nadie más que el docente limpia
        self.d.post(f'/salon_digital/pizarra/tablero/{t.pk}/compartir/', {'editan': '1'})
        self.assertTrue(ana.get(f'/aula/tablero/{t.pk}/estado/').json()['editar'])
        self.assertEqual(self.op(ana, t, self.trazo('e1')).status_code, 200)
        self.op(beto, t, {'op': 'borrar', 'ids': ['e1']})
        t.refresh_from_db()
        self.assertEqual([o['id'] for o in t.objetos], ['e1'])
        self.assertEqual(self.op(beto, t, {'op': 'reemplazar', 'obj': dict(self.trazo('e1')['obj'], c='#000000')}).status_code, 403)
        self.assertEqual(self.op(ana, t, {'op': 'limpiar'}).status_code, 403)
        self.assertEqual(self.op(ana, t, {'op': 'fondo', 'fondo': 'verde'}).status_code, 403)
        self.op(ana, t, {'op': 'borrar', 'ids': ['e1']})                       # lo suyo sí
        t.refresh_from_db()
        self.assertEqual(t.objetos, [])
        # Dejar de compartir
        self.d.post(f'/salon_digital/pizarra/tablero/{t.pk}/compartir/', {'aula': ''})
        self.assertEqual(ana.get(f'/aula/tablero/{t.pk}/estado/').status_code, 404)
        # Otro docente no abre ni comparte un tablero ajeno
        otro = User.objects.create_user('otro')
        Cuenta.objects.create(usuario=otro, slug='otro', nombre_publico='Otro', estado='verificada')
        c = Client(HTTP_HOST='localhost'); c.force_login(otro)
        self.assertEqual(c.get(f'/salon_digital/pizarra/tablero/{t.pk}/').status_code, 404)
        self.assertEqual(c.get(f'/aula/tablero/{t.pk}/estado/').status_code, 404)

    def test_estado_completo_si_va_muy_atras(self):
        t = TableroClase.objects.create(autor=self.u)
        for k in range(TB.MAX_CAMBIOS + 5):
            TB.aplicar(t.pk, self.trazo(f'z{k}'), 'd', True, True)
        t.refresh_from_db()
        e = TB.estado(t, 1)
        self.assertIn('objetos', e)                                            # demasiado atrás: todo de nuevo
        self.assertIn('ops', TB.estado(t, t.version - 3))
