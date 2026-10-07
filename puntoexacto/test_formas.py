# -*- coding: utf-8 -*-
"""Formas del examen (A, B, C, D).

    python manage.py test puntoexacto
"""
import random
from collections import Counter
from decimal import Decimal

from notas.tests.base import ColegioDePrueba

from . import formas as F
from .models import Bloque, Examen, Forma, Hoja, Pregunta


def texto_del_pdf(pdf):
    """Las órdenes de dibujo del PDF de reportlab, ya descomprimidas."""
    import base64, re, zlib
    salida = b''
    for crudo in re.findall(rb'stream\r?\n(.*?)~>endstream', pdf, re.S):
        salida += zlib.decompress(base64.a85decode(crudo, adobe=False, ignorechars=b' \t\n\r\v'))
    return salida


class FormasDelExamen(ColegioDePrueba):

    def setUp(self):
        self.c = self.cliente(self.rectora)
        r = self.c.post('/puntoexacto/nuevo/', {
            'titulo': 'Parcial', 'fecha': '2026-10-06', 'componente': 'SABER',
            'numero_preguntas': '6', 'numero_opciones': '4', 'hojas_por_pagina': '1',
            'metodo': 'con_piso', 'nota_todo_mal': '1', 'nota_nada_marcado': '1',
            'opciones_por_pregunta': '{}'})
        self.assertEqual(r.status_code, 302)
        self.ex = Examen.objects.get()
        # Clave: 1 A, 2 B, 3 C, 4 D, 5 A y la 6 es Verdadero/Falso con F correcta.
        datos = {'metodo': 'con_piso'}
        for n, letra in zip(range(1, 7), 'ABCDAB'):
            datos.update({f'correcta_{n}': letra, f'opciones_{n}': '4', f'puntos_{n}': '1'})
        datos.update({'opciones_6': '2', 'rotulos_6': 'V,F'})
        self.c.post(f'/puntoexacto/{self.ex.id}/clave/', datos)
        self.preguntas = list(self.ex.preguntas.order_by('numero'))

    def url(self, resto):
        return f'/puntoexacto/{self.ex.id}/{resto}'

    def crear_forma_b(self, orden=None):
        orden = orden or F.generar_orden(self.preguntas, azar=random.Random(3))
        return Forma.objects.create(examen=self.ex, letra='B', orden=orden)

    def respuestas_perfectas(self, orden):
        return {str(c['posicion']): c['correcta'] for c in F.clave_de(orden, self.preguntas)}

    # --------------------------------------------------------------- generar
    def test_la_forma_al_azar_es_valida_y_respeta_lo_que_no_se_mezcla(self):
        for semilla in range(20):
            orden = F.generar_orden(self.preguntas, azar=random.Random(semilla))
            self.assertEqual(F.problemas(orden, self.preguntas), [])
            # La V/F tiene 2 opciones y es la única: no se mueve ni se mezcla.
            self.assertEqual(orden[5], {'pregunta': 6, 'opciones': 'AB'})
        self.assertNotEqual(F.generar_orden(self.preguntas, azar=random.Random(1)),
                            F.identidad(self.preguntas))

    def test_con_bloques_solo_se_mezcla_dentro_del_bloque(self):
        b1 = Bloque.objects.create(examen=self.ex, nombre='Uno', orden=1)
        b2 = Bloque.objects.create(examen=self.ex, nombre='Dos', orden=2)
        self.ex.preguntas.filter(numero__lte=3).update(bloque=b1)
        self.ex.preguntas.filter(numero__gt=3).update(bloque=b2)
        preguntas = list(self.ex.preguntas.select_related('bloque').order_by('numero'))
        for semilla in range(20):
            orden = F.generar_orden(preguntas, azar=random.Random(semilla))
            self.assertEqual({f['pregunta'] for f in orden[:3]}, {1, 2, 3})
            self.assertEqual(F.problemas(orden, preguntas), [])

    def test_problemas_detecta_repetidas_y_opciones_que_no_son_permutacion(self):
        orden = F.identidad(self.preguntas)
        orden[1] = {'pregunta': 1, 'opciones': 'ABCC'}
        textos = ' '.join(F.problemas(orden, self.preguntas))
        self.assertIn('repetida', textos)
        self.assertIn('no son un orden', textos)

    # --------------------------------------------------------------- calificar
    def test_digitar_la_forma_b_con_su_clave_saca_la_maxima(self):
        forma = self.crear_forma_b()
        hoja = Hoja.objects.create(examen=self.ex, identificador='PE-1', forma='B')
        perfectas = self.respuestas_perfectas(forma.orden)
        r = self.c.post(self.url(f'hoja/{hoja.id}/digitar/'),
                        {f'p_{k}': v for k, v in perfectas.items()})
        self.assertEqual(r.status_code, 302)
        hoja.refresh_from_db()
        self.assertEqual(hoja.nota, self.ex.nota_maxima)
        self.assertEqual(hoja.lectura, perfectas)
        # Las respuestas quedan guardadas en la forma A: la correcta de cada pregunta.
        for resp in hoja.respuestas.select_related('pregunta'):
            self.assertEqual(resp.marcada, resp.pregunta.correcta)
        # Al volver a abrir, se ve lo que hay en SU hoja, no lo de la A.
        h = self.c.get(self.url(f'hoja/{hoja.id}/digitar/')).content.decode()
        self.assertIn('forma B', h)

    def test_la_clave_de_la_a_en_una_hoja_b_no_saca_la_maxima(self):
        forma = self.crear_forma_b()
        self.assertNotEqual(self.respuestas_perfectas(forma.orden),
                            self.respuestas_perfectas(F.identidad(self.preguntas)))
        hoja = Hoja.objects.create(examen=self.ex, identificador='PE-1', forma='B')
        self.c.post(self.url(f'hoja/{hoja.id}/digitar/'),
                    {f'p_{k}': v for k, v in
                     self.respuestas_perfectas(F.identidad(self.preguntas)).items()})
        hoja.refresh_from_db()
        self.assertLess(hoja.nota, self.ex.nota_maxima)

    def test_la_camara_traduce_la_forma_de_la_hoja(self):
        import json
        forma = self.crear_forma_b()
        hoja = Hoja.objects.create(examen=self.ex, identificador='PE-1', forma='B')
        r = self.c.post(self.url('escanear/guardar/'), json.dumps(
            {'hoja_id': hoja.id, 'respuestas': self.respuestas_perfectas(forma.orden)}),
            content_type='application/json')
        self.assertTrue(r.json()['ok'])
        hoja.refresh_from_db()
        self.assertEqual(hoja.nota, self.ex.nota_maxima)

    def test_corregir_la_equivalencia_recalifica_las_hojas_ya_leidas(self):
        forma = self.crear_forma_b()
        hoja = Hoja.objects.create(examen=self.ex, identificador='PE-1', forma='B')
        # El estudiante marcó la clave de la A, pero la forma estaba mal escrita:
        # en realidad la B era igual a la A.
        self.c.post(self.url(f'hoja/{hoja.id}/digitar/'),
                    {f'p_{k}': v for k, v in
                     self.respuestas_perfectas(F.identidad(self.preguntas)).items()})
        hoja.refresh_from_db()
        self.assertLess(hoja.nota, self.ex.nota_maxima)
        datos = {'accion': 'guardar'}
        for k, p in enumerate(self.preguntas, start=1):
            datos[f'p_{k}'] = str(p.numero)
            datos[f'o_{k}'] = p.letras()
        r = self.c.post(self.url('formas/B/'), datos)
        self.assertEqual(r.status_code, 302)
        forma.refresh_from_db()
        self.assertEqual(forma.orden, F.identidad(self.preguntas))
        hoja.refresh_from_db()
        self.assertEqual(hoja.nota, self.ex.nota_maxima)

    def test_equivalencia_escrita_solo_con_la_respuesta_correcta(self):
        """El docente tiene su forma B en Word: solo sabe su orden y su clave."""
        Forma.objects.create(examen=self.ex, letra='B', orden=F.identidad(self.preguntas))
        # La B es la A al revés en las 5 primeras, y su clave es D C B A D.
        datos = {'accion': 'guardar'}
        for k, (n, clave_b) in enumerate(zip([5, 4, 3, 2, 1], 'DCBAD'), start=1):
            datos.update({f'p_{k}': str(n), f'o_{k}': '', f'c_{k}': clave_b})
        datos.update({'p_6': '6', 'o_6': 'AB'})
        r = self.c.post(self.url('formas/B/'), datos)
        self.assertEqual(r.status_code, 302, r.content.decode()[:3000])
        orden = Forma.objects.get().orden
        self.assertEqual(F.problemas(orden, self.preguntas), [])
        clave = [c['correcta'] for c in F.clave_de(orden, self.preguntas)]
        self.assertEqual(clave, list('DCBADB'))

    def test_equivalencia_invalida_no_se_guarda(self):
        Forma.objects.create(examen=self.ex, letra='B', orden=F.identidad(self.preguntas))
        datos = {'accion': 'guardar'}
        for k in range(1, 7):
            datos.update({f'p_{k}': '1' if k <= 5 else '6', f'o_{k}': ''})
        r = self.c.post(self.url('formas/B/'), datos)
        self.assertEqual(r.status_code, 200)
        self.assertIn('repetida', r.content.decode())
        self.assertEqual(Forma.objects.get().orden, F.identidad(self.preguntas))

    # --------------------------------------------------------------- nueva clave
    def clave_a(self, **extra):
        datos = {'metodo': 'con_piso', **extra}
        for p in self.preguntas:
            datos.update({f'correcta_{p.numero}': p.correcta,
                          f'opciones_{p.numero}': str(p.opciones_efectivas()),
                          f'puntos_{p.numero}': '1', f'rotulos_{p.numero}': p.rotulos})
        return datos

    def test_nueva_clave_desde_la_pantalla_de_la_clave(self):
        r = self.c.post(self.url('clave/'), self.clave_a(accion='nueva_clave'))
        self.assertRedirects(r, self.url('clave/B/'), fetch_redirect_response=False)
        forma = Forma.objects.get()
        self.assertEqual(F.faltantes(forma.orden), 6)
        h = self.c.get(self.url('clave/B/')).content.decode()
        self.assertIn('Faltan 6 por marcar', h)
        self.assertIn('Clave A', h)
        # El docente marca la clave de su forma B: D C B A D y F.
        datos = {'accion': 'guardar'}
        for k, letra in enumerate('DCBADB', start=1):
            datos[f'correcta_{k}'] = letra
        self.c.post(self.url('clave/B/'), datos)
        forma.refresh_from_db()
        self.assertEqual(F.faltantes(forma.orden), 0)
        self.assertEqual([c['correcta'] for c in F.clave_de(forma.orden, self.preguntas)],
                         list('DCBADB'))
        # Un estudiante de la B que marca esa clave saca la máxima.
        hoja = Hoja.objects.create(examen=self.ex, identificador='PE-1')
        r = self.c.post(self.url(f'hoja/{hoja.id}/digitar/'),
                        {'forma': 'B', **{f'p_{k}': l for k, l in enumerate('DCBADB', start=1)}})
        hoja.refresh_from_db()
        self.assertEqual((hoja.forma, hoja.nota), ('B', self.ex.nota_maxima))
        # Y uno que marcó la clave de la A, diciendo que es de la B, no.
        hoja2 = Hoja.objects.create(examen=self.ex, identificador='PE-2')
        self.c.post(self.url(f'hoja/{hoja2.id}/digitar/'),
                    {'forma': 'B', **{f'p_{k}': l for k, l in enumerate('ABCDAB', start=1)}})
        hoja2.refresh_from_db()
        self.assertLess(hoja2.nota, self.ex.nota_maxima)

    def test_clave_b_con_preguntas_en_otro_orden(self):
        self.c.post(self.url('clave/'), self.clave_a(accion='nueva_clave'))
        # En la B la 1 es la 3 de la A y la 3 es la 1; la clave de la B es C B A D A F.
        datos = {'accion': 'guardar', 'a_1': '3', 'a_3': '1'}
        for k, letra in enumerate('CBADAB', start=1):
            datos[f'correcta_{k}'] = letra
        self.c.post(self.url('clave/B/'), datos)
        orden = Forma.objects.get().orden
        self.assertEqual([f['pregunta'] for f in orden], [3, 2, 1, 4, 5, 6])
        # Como la 3 de la A tenía C y la 1 tenía A, no hizo falta mover opciones.
        self.assertEqual(orden[0]['opciones'], 'ABCD')

    def test_las_hojas_no_traen_forma_hasta_que_se_leen(self):
        self.crear_forma_b()
        self.c.post(self.url('hojas/'), {'curso_ids': [self.curso.id], 'sueltas': '0'})
        self.assertEqual(set(self.ex.hojas.values_list('forma', flat=True)), {'A'})

    def test_la_camara_lee_la_burbuja_de_forma(self):
        """Hoja impresa -> imagen con las burbujas rellenas -> lector."""
        import io, json, subprocess, tempfile
        from PIL import Image, ImageDraw
        from django.core.files.uploadedfile import SimpleUploadedFile
        from . import hojas as H
        forma = self.crear_forma_b()
        hoja = Hoja.objects.create(examen=self.ex, identificador='PE-00001-0001', nombre_libre='Ana')
        pdf = self.c.get(self.url('hojas/imprimir/')).content
        with tempfile.TemporaryDirectory() as d:
            open(f'{d}/h.pdf', 'wb').write(pdf)
            try:
                subprocess.run(['pdftoppm', '-r', '110', '-png', '-singlefile', f'{d}/h.pdf', f'{d}/h'],
                               check=True)
            except (OSError, subprocess.CalledProcessError):
                self.skipTest('pdftoppm no está instalado')
            img = Image.open(f'{d}/h.png').convert('L')
        info = H.mapa_de_examen(self.ex)
        esc = img.width / info['hoja_w_mm']
        alto_mm = img.height / esc
        r = info['radio_mm'] * esc * 0.8
        dib = ImageDraw.Draw(img)
        clave_b = self.respuestas_perfectas(forma.orden)
        for clave in [f'{k}{l}' for k, l in clave_b.items()] + ['FB']:
            x, y = info['mapa'][clave]
            cx, cy = x * esc, (alto_mm - y) * esc
            dib.ellipse([cx - r, cy - r, cx + r, cy + r], fill=20)
        b = io.BytesIO(); img.save(b, 'PNG')
        lect = self.c.post(self.url('escanear/foto/'),
                           {'foto': SimpleUploadedFile('f.png', b.getvalue(), 'image/png')}).json()
        self.assertTrue(lect['ok'], lect)
        self.assertEqual((lect['formas'], lect['forma'], lect['forma_duda']), ('AB', 'B', None))
        g = self.c.post(self.url('escanear/guardar/'), json.dumps(
            {'hoja_id': lect['hoja_id'], 'respuestas': lect['respuestas'], 'forma': lect['forma']}),
            content_type='application/json').json()
        self.assertEqual(g['forma'], 'B')
        hoja.refresh_from_db()
        self.assertEqual(hoja.nota, self.ex.nota_maxima)

    def test_no_se_borra_una_forma_con_hojas_calificadas(self):
        forma = self.crear_forma_b()
        hoja = Hoja.objects.create(examen=self.ex, identificador='PE-1', forma='B')
        self.c.post(self.url(f'hoja/{hoja.id}/digitar/'),
                    {f'p_{k}': v for k, v in self.respuestas_perfectas(forma.orden).items()})
        self.c.post(self.url('formas/'), {'accion': 'borrar', 'letra': 'B'})
        self.assertTrue(self.ex.formas.exists())

    # --------------------------------------------------------------- clave cambia
    def test_agregar_y_quitar_preguntas_deja_las_formas_validas(self):
        self.crear_forma_b()
        datos = {'metodo': 'con_piso', 'accion': 'agregar'}
        for p in self.preguntas:
            datos.update({f'correcta_{p.numero}': p.correcta,
                          f'opciones_{p.numero}': str(p.opciones_efectivas()),
                          f'puntos_{p.numero}': '1', f'rotulos_{p.numero}': p.rotulos})
        self.c.post(self.url('clave/'), datos)
        preguntas = list(self.ex.preguntas.order_by('numero'))
        self.assertEqual(len(preguntas), 7)
        self.assertEqual(F.problemas(Forma.objects.get().orden, preguntas), [])
        datos['accion'] = 'quitar'
        self.c.post(self.url('clave/'), datos)
        self.c.post(self.url('clave/'), datos)        # quita también la 6 (V/F)
        preguntas = list(self.ex.preguntas.order_by('numero'))
        self.assertEqual(len(preguntas), 5)
        self.assertEqual(F.problemas(Forma.objects.get().orden, preguntas), [])

    # --------------------------------------------------------------- impresión
    def test_la_hoja_impresa_dice_su_forma_solo_si_hay_formas(self):
        Hoja.objects.create(examen=self.ex, identificador='PE-1', nombre_libre='Ana')
        sin = self.c.get(self.url('hojas/imprimir/'))
        self.assertEqual(sin.status_code, 200)
        self.assertNotIn(b'FORMA', texto_del_pdf(sin.content))
        self.crear_forma_b()
        con = texto_del_pdf(self.c.get(self.url('hojas/imprimir/')).content)
        self.assertIn(b'(FORMA)', con)
        from . import hojas as H
        self.assertIn('FB', H.mapa_de_examen(self.ex)['mapa'])

    def test_pantallas_de_formas(self):
        self.crear_forma_b()
        for resto in ('formas/', 'formas/B/', 'formas-imprimir/'):
            r = self.c.get(self.url(resto))
            self.assertEqual(r.status_code, 200, resto)
        self.assertContains(self.c.get(self.url('formas/')), 'Tabla de equivalencias')
        r = self.c.get(self.url('formas-excel/'))
        self.assertEqual(r.status_code, 200)
        import io, openpyxl
        libro = openpyxl.load_workbook(io.BytesIO(r.content))
        self.assertEqual(libro.sheetnames, ['Claves', 'Forma B'])
        # La V/F sale con su etiqueta, no con la letra interna.
        claves = libro['Claves']
        self.assertEqual(claves.cell(row=claves.max_row, column=2).value, 'F')
