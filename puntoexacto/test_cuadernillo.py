# -*- coding: utf-8 -*-
"""Cuadernillo: escribir el examen, que la clave se actualice sola y que salgan Word y PDF.
Las imágenes llegan con la petición y no se guardan en el servidor."""
import io
import json
import zipfile

from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image

from notas.tests.base import ColegioDePrueba

from . import cuadernillo as C
from .models import Cuadernillo, Examen, Forma


def png(color=(200, 30, 30), tam=(60, 40)):
    buf = io.BytesIO()
    Image.new('RGB', tam, color).save(buf, 'PNG')
    return buf.getvalue()


def pregunta(enunciado, correcta, n=4, img=None):
    return {'id': enunciado[:6].replace(' ', ''), 'tipo': 'pregunta', 'enunciado': enunciado,
            'imagenes': [img] if img else [], 'correcta': correcta,
            'opciones': [{'texto': f'op {l}', 'imagen': None} for l in 'ABCDEF'[:n]]}


IMG = {'id': 'im1', 'proveedor': 'google', 'ref': 'drive-123', 'nombre': 'triangulo.png', 'ancho': 45}


class CuadernilloDelExamen(ColegioDePrueba):

    def setUp(self):
        self.c = self.cliente(self.u_docente)
        r = self.c.post('/puntoexacto/nuevo/', {
            'titulo': 'Parcial de áreas', 'fecha': '2026-10-06', 'componente': 'SABER',
            'numero_preguntas': '3', 'numero_opciones': '4', 'hojas_por_pagina': '1',
            'metodo': 'con_piso', 'nota_todo_mal': '1', 'nota_nada_marcado': '1',
            'opciones_por_pregunta': '{}'})
        self.assertEqual(r.status_code, 302)
        self.ex = Examen.objects.get()

    def url(self, resto=''):
        return f'/puntoexacto/{self.ex.id}/cuadernillo/{resto}'

    def guardar(self, items, **extra):
        contenido = {'instrucciones': 'Marque una sola.', 'nombre': 'linea', 'columnas': 1, 'items': items, **extra}
        return self.c.post(self.url('guardar/'), json.dumps({'contenido': contenido}), content_type='application/json')

    def test_abre_con_las_preguntas_del_examen(self):
        r = self.c.get(self.url())
        self.assertEqual(r.status_code, 200)
        self.assertEqual(len(r.context['contenido']['items']), 3)

    def test_guardar_actualiza_la_clave_y_el_numero_de_preguntas(self):
        items = [{'id': 't1', 'tipo': 'texto', 'texto': 'Lea la tabla.', 'imagenes': []},
                 pregunta('Área del cuadrado de lado 3', 'B'),
                 pregunta('¿Cuánto es 2^3?', 'D'),
                 pregunta('Falso o verdadero', 'A', n=2),
                 pregunta('Sin marcar aún', '')]
        r = self.guardar(items).json()
        self.assertTrue(r['ok'])
        self.assertEqual(r['preguntas'], 4)
        self.assertEqual(r['sin_correcta'], [4])
        self.ex.refresh_from_db()
        self.assertEqual(self.ex.numero_preguntas, 4)
        clave = {p.numero: (p.correcta, p.opciones_efectivas()) for p in self.ex.preguntas.all()}
        self.assertEqual(clave, {1: ('B', 4), 2: ('D', 4), 3: ('A', 2), 4: ('', 4)})
        # Bajar a 2 preguntas quita las sobrantes de la clave.
        self.guardar(items[:3])
        self.assertEqual(self.ex.preguntas.count(), 2)

    def test_el_servidor_solo_guarda_la_referencia_de_la_imagen(self):
        self.guardar([pregunta('Con figura', 'A', img=dict(IMG, datos='data:image/png;base64,AAAA'))])
        img = Cuadernillo.objects.get().contenido['items'][0]['imagenes'][0]
        self.assertEqual(img, {'id': 'im1', 'proveedor': 'google', 'ref': 'drive-123',
                               'nombre': 'triangulo.png', 'ancho': 45})

    def test_limpiar_corrige_lo_raro(self):
        c = C.limpiar({'nombre': 'otro', 'columnas': '7', 'items': [
            {'tipo': 'pregunta', 'enunciado': 'x', 'opciones': ['a'], 'correcta': 'Z'}, 'basura']})
        self.assertEqual(c['nombre'], 'linea')
        self.assertEqual(c['columnas'], 1)
        self.assertEqual(len(c['items']), 1)
        self.assertEqual(len(c['items'][0]['opciones']), 2)
        self.assertEqual(c['items'][0]['correcta'], '')

    def test_exponentes(self):
        self.assertEqual(C.a_html('x^2 + a_{n+1} <b>'), 'x<sup>2</sup> + a<sub>n+1</sub> &lt;b&gt;')

    def test_forma_b_reordena_y_repite_la_lectura(self):
        items = [{'id': 't1', 'tipo': 'texto', 'texto': 'Lectura 1', 'imagenes': []},
                 pregunta('P uno', 'A'), pregunta('P dos', 'B'),
                 {'id': 't2', 'tipo': 'texto', 'texto': 'Lectura 2', 'imagenes': []},
                 pregunta('P tres', 'C')]
        self.guardar(items)
        orden = [{'pregunta': 3, 'opciones': 'ABCD'}, {'pregunta': 1, 'opciones': 'BACD'},
                 {'pregunta': 2, 'opciones': 'ABCD'}]
        contenido = C.limpiar(Cuadernillo.objects.get().contenido)
        seq = C.secuencia(contenido, orden)
        resumen = [s['item'].get('texto') or s['item']['enunciado'] for s in seq]
        self.assertEqual(resumen, ['Lectura 2', 'P tres', 'Lectura 1', 'P uno', 'P dos'])
        # En la B la opción A de la pregunta 1 es la B de la A.
        p1 = seq[3]
        self.assertEqual([(l, op['texto']) for l, op in p1['opciones']][:2], [('A', 'op B'), ('B', 'op A')])

    def test_word_y_pdf_con_imagen_que_no_se_guarda(self):
        self.guardar([pregunta('Área del triángulo', 'A', img=IMG), pregunta('Otra', 'B')])
        archivos_antes = set()
        r = self.c.post(self.url('generar/'), {'formato': 'docx', 'img_im1': SimpleUploadedFile('im1', png(), 'image/png')})
        self.assertEqual(r.status_code, 200)
        self.assertIn('wordprocessingml', r['Content-Type'])
        z = zipfile.ZipFile(io.BytesIO(r.content))
        self.assertTrue(any(n.startswith('word/media/') for n in z.namelist()))
        texto = z.read('word/document.xml').decode()
        self.assertIn('Área del triángulo', texto)
        self.assertIn('Nombre:', texto)
        r = self.c.post(self.url('generar/'), {'formato': 'pdf', 'img_im1': SimpleUploadedFile('im1', png(), 'image/png')})
        self.assertEqual(r['Content-Type'], 'application/pdf')
        self.assertTrue(r.content.startswith(b'%PDF'))
        # Nada de imágenes en la base.
        self.assertNotIn('base64', json.dumps(Cuadernillo.objects.get().contenido))
        self.assertEqual(archivos_antes, set())

    def test_sin_la_imagen_sale_el_aviso(self):
        self.guardar([pregunta('Con figura', 'A', img=IMG)])
        r = self.c.post(self.url('generar/'), {'formato': 'docx'})
        texto = zipfile.ZipFile(io.BytesIO(r.content)).read('word/document.xml').decode()
        self.assertIn('imagen no disponible', texto)

    def test_lo_que_no_es_imagen_se_descarta(self):
        self.guardar([pregunta('Con figura', 'A', img=IMG)])
        malo = SimpleUploadedFile('im1', b'<script>alert(1)</script>', 'image/png')
        r = self.c.post(self.url('generar/'), {'formato': 'docx', 'img_im1': malo})
        self.assertEqual(r.status_code, 200)
        texto = zipfile.ZipFile(io.BytesIO(r.content)).read('word/document.xml').decode()
        self.assertIn('imagen no disponible', texto)

    def test_una_version_por_forma_y_por_estudiante(self):
        self.guardar([pregunta('P uno', 'A'), pregunta('P dos', 'B'), pregunta('P tres', 'C')])
        Forma.objects.create(examen=self.ex, letra='B', orden=[
            {'pregunta': 2, 'opciones': 'ABCD'}, {'pregunta': 1, 'opciones': 'ABCD'}, {'pregunta': 3, 'opciones': 'ABCD'}])
        contenido = C.limpiar(Cuadernillo.objects.get().contenido)
        self.assertEqual([v['forma'] for v in C.versiones(self.ex, contenido)], ['A', 'B'])
        self.ex.cursos.add(self.curso)
        lista = C.versiones(self.ex, contenido, modo='lista')
        self.assertEqual([v['estudiante'] for v in lista], ['PRUEBA ANA', 'PRUEBA BETO', 'PRUEBA CARO'])
        r = self.c.post(self.url('generar/'), {'formato': 'docx', 'nombre': 'lista'})
        texto = zipfile.ZipFile(io.BytesIO(r.content)).read('word/document.xml').decode()
        self.assertIn('PRUEBA BETO', texto)

    def test_otro_docente_no_entra(self):
        from django.contrib.auth.models import User
        from notas.models import Docente
        u = User.objects.create_user('otra', password='x')
        Docente.objects.create(colegio=self.a, user=u)
        otro = self.cliente(u)
        self.assertEqual(otro.get(self.url()).status_code, 404)
        r = otro.post(self.url('guardar/'), '{}', content_type='application/json')
        self.assertEqual(r.status_code, 404)

    def test_ayudante_de_nube(self):
        with self.settings(MICROSOFT_CLIENT_ID='abc123', GOOGLE_CLIENT_ID=''):
            r = self.c.get('/puntoexacto/nube/onedrive/')
            self.assertContains(r, 'abc123')
            self.assertContains(r, 'code_challenge')
            r = self.c.get(self.url())
            self.assertEqual(r.context['nube']['sugerida'], 'onedrive')
            r = self.c.get('/puntoexacto/nube/google/')
            self.assertContains(r, 'todavía no está configurada')
        self.assertEqual(self.c.get('/puntoexacto/nube/dropbox/').status_code, 404)

    def test_gmail_sugiere_drive(self):
        self.u_docente.email = 'profe@gmail.com'
        self.u_docente.save()
        with self.settings(MICROSOFT_CLIENT_ID='abc', GOOGLE_CLIENT_ID='g-1'):
            self.assertEqual(self.c.get(self.url()).context['nube']['sugerida'], 'google')


class HojasYaLeidas(CuadernilloDelExamen):
    def test_no_deja_quitar_ni_mover_preguntas_con_respuestas(self):
        from .models import Hoja, Respuesta
        items = [pregunta('P uno', 'A'), pregunta('P dos', 'B'), pregunta('P tres', 'C')]
        self.guardar(items)
        hoja = Hoja.objects.create(examen=self.ex, estudiante=self.estudiantes[0], identificador='H1')
        for p in self.ex.preguntas.all():
            Respuesta.objects.create(hoja=hoja, pregunta=p, marcada='A')
        r = self.guardar([items[0], items[2]])                       # quitar la del medio
        self.assertEqual(r.status_code, 409)
        self.assertEqual(Respuesta.objects.filter(hoja=hoja).count(), 3)
        self.assertEqual(self.guardar([items[1], items[0], items[2]]).status_code, 409)   # mover
        # Corregir textos y agregar al final sí se puede.
        items[0]['enunciado'] = 'P uno corregida'
        self.assertEqual(self.guardar(items + [pregunta('P cuatro', 'D')]).status_code, 200)
        self.assertEqual(self.ex.preguntas.count(), 4)


class EstudianteNoEntra(CuadernilloDelExamen):
    def test_estudiante_no_ve_ni_cambia_la_clave(self):
        est = self.cliente(self.estudiantes[0].user)
        self.assertEqual(est.get(self.url()).status_code, 404)
        self.assertEqual(est.post(self.url('guardar/'), '{}', content_type='application/json').status_code, 404)
        self.assertEqual(est.get(f'/puntoexacto/{self.ex.id}/clave/').status_code, 404)
        self.assertEqual(est.get('/puntoexacto/').status_code, 403)
        self.assertEqual(est.post('/puntoexacto/nuevo/', {'titulo': 'X'}).status_code, 403)
        self.assertEqual(est.get('/puntoexacto/nube/google/').status_code, 403)


class NubeCentral(CuadernilloDelExamen):
    """Una sola dirección registrada en Google y Azure para todos los colegios."""

    def test_colegio_pasa_por_la_central(self):
        with self.settings(GOOGLE_CLIENT_ID='g1', NUBE_URL='https://mcolegio.com.co'):
            r = self.c.get('/puntoexacto/nube/google/')
        self.assertContains(r, "var CENTRAL = 'https://mcolegio.com.co/puntoexacto/nube\\u002Dcentral/google/'")

    def test_central_sin_sesion_y_solo_dominios_de_la_plataforma(self):
        from django.test import Client
        with self.settings(MICROSOFT_CLIENT_ID='m1', DEBUG=False,
                           ALLOWED_HOSTS=['mcolegio.com.co', '.mcolegio.com.co', 'localhost', 'integradoapr.edu.co']):
            r = Client(HTTP_HOST='mcolegio.com.co').get('/puntoexacto/nube-central/onedrive/')
        self.assertEqual(r.status_code, 200)
        hosts = json.loads(r.content.decode().split('id="hosts" type="application/json">')[1].split('</script>')[0])
        self.assertEqual(hosts, ['mcolegio.com.co', '.mcolegio.com.co', 'integradoapr.edu.co'])   # sin localhost
        self.assertContains(r, 'Pedido no válido')
