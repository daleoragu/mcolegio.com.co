# -*- coding: utf-8 -*-
"""Escanear con la cámara en vivo.

    python manage.py test puntoexacto
"""
import io
import os
import json
import re
import subprocess
import tempfile

from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image, ImageDraw

from notas.tests.base import ColegioDePrueba

from . import hojas as H
from .models import Examen, Hoja


class CamaraEnVivo(ColegioDePrueba):

    def setUp(self):
        self.c = self.cliente(self.rectora)
        self.c.post('/puntoexacto/nuevo/', {
            'titulo': 'Parcial', 'fecha': '2026-10-06', 'componente': 'SABER',
            'numero_preguntas': '8', 'numero_opciones': '4', 'hojas_por_pagina': '1',
            'metodo': 'con_piso', 'nota_todo_mal': '1', 'nota_nada_marcado': '1',
            'opciones_por_pregunta': '{}'})
        self.ex = Examen.objects.get()
        datos = {'metodo': 'con_piso'}
        for n, letra in zip(range(1, 9), 'ABCDABCD'):
            datos.update({f'correcta_{n}': letra, f'opciones_{n}': '4', f'puntos_{n}': '1'})
        self.c.post(f'/puntoexacto/{self.ex.id}/clave/', datos)
        self.hoja = Hoja.objects.create(examen=self.ex, identificador='PE-00001-0001', nombre_libre='Ana')

    def url(self, resto):
        return f'/puntoexacto/{self.ex.id}/{resto}'

    def test_la_pantalla_trae_la_camara_y_donde_van_las_marcas(self):
        r = self.c.get(self.url('escanear/'))
        self.assertEqual(r.status_code, 200)
        html = r.content.decode()
        self.assertIn('id="pe-abrir-camara"', html)
        self.assertIn('id="pe-video"', html)
        self.assertIn('id="pe-rejilla"', html)          # corregir con el dedo
        geos = json.loads(re.search(r'id="pe-datos-geo"[^>]*>(.*?)</script>', html, re.S).group(1))
        # Primero el reparto del examen, después los demás en que pudo imprimirse.
        self.assertEqual(geos[0]['por_pagina'], 1)
        self.assertEqual({g['por_pagina'] for g in geos}, {1, 2, 4, 8})
        esperado = H.geometria(1, 'PE-00001-0001')
        self.assertEqual(geos[0]['ancho_mm'], esperado['ancho_mm'])
        # Con la franja del código de barras la cámara sabe hacia dónde está girada la hoja.
        self.assertEqual(geos[0]['barras_x_mm'], esperado['barras_x_mm'])
        self.assertIn('puntoexacto/escaner.js', html)
        self.assertIn('id="pe-abrir-pdf"', html)          # escanear a PDF
        self.assertIn('accept="application/pdf,image/*"', html)   # calificar un PDF o fotos
        self.assertEqual([list(p) for p in esperado['marcas_mm']], geos[0]['marcas_mm'])

    def test_lee_la_foto_recortada_como_la_manda_la_camara(self):
        """La cámara manda solo el pedazo de la hoja (con un poco de borde) y
        en JPEG; el lector debe leerlo igual que una foto completa."""
        pdf = self.c.get(self.url('hojas/imprimir/')).content
        with tempfile.TemporaryDirectory() as d:
            open(f'{d}/h.pdf', 'wb').write(pdf)
            try:
                subprocess.run(['pdftoppm', '-r', '120', '-png', '-singlefile', f'{d}/h.pdf', f'{d}/h'],
                               check=True)
            except (OSError, subprocess.CalledProcessError):
                self.skipTest('pdftoppm no está instalado')
            hoja = Image.open(f'{d}/h.png').convert('RGB')
        info = H.mapa_de_examen(self.ex)
        esc = hoja.width / info['hoja_w_mm']
        alto_mm = hoja.height / esc
        dib = ImageDraw.Draw(hoja)
        r = info['radio_mm'] * esc * 0.8
        marcadas = {1: 'A', 2: 'B', 3: 'C', 4: 'D', 5: 'A', 6: 'B', 7: 'C'}  # la 8 en blanco
        for p, l in marcadas.items():
            x, y = info['mapa'][f'{p}{l}']
            cx, cy = x * esc, (alto_mm - y) * esc
            dib.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(40, 40, 40))
        # La hoja sobre una mesa, y el recorte que hace el navegador.
        mesa = Image.new('RGB', (hoja.width + 300, hoja.height + 400), (120, 92, 64))
        mesa.paste(hoja, (150, 200))
        recorte = mesa.crop((150 - 20, 200 - 20, 150 + hoja.width + 20, 200 + hoja.height + 20))
        b = io.BytesIO()
        recorte.save(b, 'JPEG', quality=92)
        lect = self.c.post(self.url('escanear/foto/'),
                           {'foto': SimpleUploadedFile('hoja.jpg', b.getvalue(), 'image/jpeg')}).json()
        self.assertTrue(lect['ok'], lect)
        self.assertEqual(lect['hoja_id'], self.hoja.id)
        self.assertEqual({int(k): v for k, v in lect['respuestas'].items() if v}, marcadas)
        self.assertEqual(lect['respuestas']['8'], '')


class UnaSolaIdaAlServidor(CamaraEnVivo):
    """La cámara manda la foto una vez: vuelve lo leído, la nota y, si todo está claro, la hoja guardada."""

    def foto_llena(self, marcadas):
        pdf = self.c.get(self.url('hojas/imprimir/')).content
        with tempfile.TemporaryDirectory() as d:
            open(f'{d}/h.pdf', 'wb').write(pdf)
            try:
                subprocess.run(['pdftoppm', '-r', '100', '-png', '-singlefile', f'{d}/h.pdf', f'{d}/h'], check=True)
            except (OSError, subprocess.CalledProcessError):
                self.skipTest('pdftoppm no está instalado')
            hoja = Image.open(f'{d}/h.png').convert('RGB')
        info = H.mapa_de_examen(self.ex)
        esc = hoja.width / info['hoja_w_mm']
        alto_mm = hoja.height / esc
        dib = ImageDraw.Draw(hoja)
        r = info['radio_mm'] * esc * 0.8
        for p, l in marcadas.items():
            x, y = info['mapa'][f'{p}{l}']
            dib.ellipse([x * esc - r, (alto_mm - y) * esc - r, x * esc + r, (alto_mm - y) * esc + r], fill=(30, 30, 30))
        b = io.BytesIO()
        hoja.save(b, 'JPEG', quality=82)
        return SimpleUploadedFile('hoja.jpg', b.getvalue(), 'image/jpeg')

    def test_calentar_con_get(self):
        self.assertEqual(self.c.get(self.url('escanear/foto/')).json(), {'ok': True})

    def test_sin_auto_no_guarda_pero_trae_la_nota(self):
        marcadas = {n: l for n, l in zip(range(1, 9), 'ABCDABCD')}
        d = self.c.post(self.url('escanear/foto/'), {'foto': self.foto_llena(marcadas)}).json()
        self.assertTrue(d['ok'], d)
        self.assertIsNone(d['guardada'])
        self.assertEqual(d['nota_previa']['buenas'], 8)
        self.assertEqual(d['nota_previa']['nota'], str(self.ex.nota_maxima))
        self.hoja.refresh_from_db()
        self.assertEqual(self.hoja.estado, 'pendiente')

    def test_con_auto_y_todo_claro_queda_guardada(self):
        marcadas = {n: l for n, l in zip(range(1, 9), 'ABCDABCA')}   # la 8 mal
        d = self.c.post(self.url('escanear/foto/'), {'foto': self.foto_llena(marcadas), 'auto': '1'}).json()
        self.assertTrue(d['ok'], d)
        self.assertEqual(d['guardada']['hoja_id'], self.hoja.id)
        self.assertEqual((d['guardada']['buenas'], d['guardada']['malas']), (7, 1))
        self.assertEqual(d['nota_previa']['clave']['8'], 'D')
        self.hoja.refresh_from_db()
        self.assertEqual(self.hoja.estado, 'calificada')
        self.assertEqual(str(self.hoja.nota), d['guardada']['nota'])

    def test_con_auto_pero_con_dudas_no_guarda(self):
        from unittest import mock

        from . import lector
        real = lector.decidir

        def con_duda(medidas, preguntas, letras):
            r, dudas = real(medidas, preguntas, letras)
            if preguntas > 1:      # la lectura de las respuestas (no la de la forma)
                dudas = dudas + [{'pregunta': 1, 'motivo': 'dos marcas'}]
            return r, dudas

        foto = self.foto_llena({n: l for n, l in zip(range(1, 9), 'ABCDABCD')})
        with mock.patch.object(lector, 'decidir', side_effect=con_duda):
            d = self.c.post(self.url('escanear/foto/'), {'foto': foto, 'auto': '1'}).json()
        self.assertTrue(d['ok'], d)
        self.assertIsNone(d['guardada'])
        self.hoja.refresh_from_db()
        self.assertEqual(self.hoja.estado, 'pendiente')


class HojaDeOtroExamen(UnaSolaIdaAlServidor):
    """Una hoja impresa para un examen no se califica con la clave de otro."""

    def test_la_hoja_de_otro_examen_se_rechaza(self):
        foto = self.foto_llena({n: l for n, l in zip(range(1, 9), 'ABCDABCD')})
        # Otro examen del mismo docente, con las mismas preguntas.
        otro = Examen.objects.create(colegio=self.a, docente=self.docente, titulo='Quiz', fecha='2026-10-07',
                                     numero_preguntas=8)
        Hoja.objects.create(examen=otro, identificador=f'PE-{otro.id:05d}-0001', nombre_libre='Beto')
        d = self.c.post(f'/puntoexacto/{otro.id}/escanear/foto/', {'foto': foto, 'auto': '1'}).json()
        self.assertFalse(d['ok'])
        self.assertTrue(d['otro_examen'])
        self.assertIn('«Parcial»', d['error'])
        self.assertEqual(d['url_otro'], f'/puntoexacto/{self.ex.id}/escanear/')
        self.hoja.refresh_from_db()
        self.assertEqual(self.hoja.estado, 'pendiente')
        self.assertFalse(otro.hojas.filter(estado='calificada').exists())

    def test_la_hoja_impresa_dice_el_numero_del_examen(self):
        from .test_formas import texto_del_pdf
        pdf = self.c.get(self.url('hojas/imprimir/')).content
        # reportlab escribe la «º» en octal (\\272).
        self.assertIn(f'Examen N.\\272 {self.ex.id} '.encode(), texto_del_pdf(pdf))

    def test_tambien_si_el_otro_examen_no_tiene_hojas(self):
        foto = self.foto_llena({n: l for n, l in zip(range(1, 9), 'ABCDABCD')})
        vacio = Examen.objects.create(colegio=self.a, docente=self.docente, titulo='Sin hojas',
                                      fecha='2026-10-07', numero_preguntas=8)
        d = self.c.post(f'/puntoexacto/{vacio.id}/escanear/foto/', {'foto': foto}).json()
        self.assertFalse(d['ok'])
        self.assertTrue(d.get('otro_examen'), d)


class TrazosAMedias(CamaraEnVivo):
    """Una burbuja con un par de rayas de lápiz cuenta como marcada; las vacías no."""

    def test_sumar_trazos(self):
        from . import lector
        medidas = {}
        for n in range(1, 11):
            for l in 'ABCD':
                # Vacías: la letra impresa deja el 15 % en ~0.20 y el 35 % en ~0.02.
                medidas[f'{n}{l}'] = {'relleno': 0.02, 'trazo': 0.20, 'fuera': False}
        medidas['3B'] = {'relleno': 0.06, 'trazo': 0.62, 'fuera': False}   # dos rayas de lápiz
        medidas['7C'] = {'relleno': 0.80, 'trazo': 0.95, 'fuera': False}   # bien rellena
        lector._sumar_trazos(medidas)
        respuestas, dudas = lector.decidir(medidas, 10, lambda n: 'ABCD')
        self.assertEqual(respuestas[3], 'B')
        self.assertEqual(respuestas[7], 'C')
        self.assertEqual([n for n in range(1, 11) if respuestas[n] and n not in (3, 7)], [])
        self.assertEqual(medidas['7C']['relleno'], 0.80)   # la bien rellena no cambia


class ImpresaConOtroReparto(CamaraEnVivo):
    """La hoja se imprimió a 4 por página aunque el examen dijera 1: igual se lee bien."""

    def foto_de_reparto(self, por_pagina, marcadas):
        pdf = self.c.get(self.url(f'hojas/imprimir/?por_pagina={por_pagina}')).content
        with tempfile.TemporaryDirectory() as d:
            open(f'{d}/h.pdf', 'wb').write(pdf)
            try:
                subprocess.run(['pdftoppm', '-r', '200', '-png', '-singlefile', f'{d}/h.pdf', f'{d}/h'], check=True)
            except (OSError, subprocess.CalledProcessError):
                self.skipTest('pdftoppm no está instalado')
            pagina = Image.open(f'{d}/h.png').convert('RGB')
        cols, filas = H.REPARTO[por_pagina]
        hoja = pagina.crop((0, 0, pagina.width // cols, pagina.height // filas))
        info = H.mapa_de_examen(self.ex, por_pagina)
        esc = hoja.width / info['hoja_w_mm']
        alto_mm = hoja.height / esc
        dib = ImageDraw.Draw(hoja)
        r = info['radio_mm'] * esc * 0.8
        for p, l in marcadas.items():
            x, y = info['mapa'][f'{p}{l}']
            dib.ellipse([x * esc - r, (alto_mm - y) * esc - r, x * esc + r, (alto_mm - y) * esc + r], fill=(30, 30, 30))
        b = io.BytesIO()
        hoja.save(b, 'JPEG', quality=85)
        return SimpleUploadedFile('hoja.jpg', b.getvalue(), 'image/jpeg')

    def test_imprimir_guarda_el_reparto(self):
        self.c.get(self.url('hojas/imprimir/?por_pagina=4'))
        self.ex.refresh_from_db()
        self.assertEqual(self.ex.hojas_por_pagina, 4)

    def test_lee_la_hoja_de_4_por_pagina_aunque_el_examen_diga_1(self):
        marcadas = {n: l for n, l in zip(range(1, 9), 'DCBADCBA')}
        foto = self.foto_de_reparto(4, marcadas)
        Examen.objects.filter(id=self.ex.id).update(hojas_por_pagina=1)   # como quedó en su colegio
        d = self.c.post(self.url('escanear/foto/'), {'foto': foto}).json()
        self.assertTrue(d['ok'], d)
        self.assertEqual(d['hoja_id'], self.hoja.id)              # el código se leyó
        self.assertEqual({int(k): v for k, v in d['respuestas'].items() if v}, marcadas)
        self.assertEqual(d['dudas'], [])
        self.ex.refresh_from_db()
        self.assertEqual(self.ex.hojas_por_pagina, 4)             # y queda aprendido

    def test_tambien_la_apaisada_de_2_por_pagina(self):
        marcadas = {n: l for n, l in zip(range(1, 9), 'ABCDDCBA')}
        foto = self.foto_de_reparto(2, marcadas)
        Examen.objects.filter(id=self.ex.id).update(hojas_por_pagina=1)
        d = self.c.post(self.url('escanear/foto/'), {'foto': foto, 'por_pagina': '2'}).json()
        self.assertTrue(d['ok'], d)
        self.assertEqual({int(k): v for k, v in d['respuestas'].items() if v}, marcadas)


class RepartoGemelo(ImpresaConOtroReparto, UnaSolaIdaAlServidor):
    """Las hojas de 1 y de 4 por página tienen la misma forma: el lector no debe quedarse con el mapa equivocado."""

    def test_hoja_de_1_por_pagina_con_el_examen_en_4(self):
        marcadas = {1: 'A', 2: 'B', 3: 'C', 4: 'D', 5: 'A', 6: 'B', 7: 'C'}
        foto = self.foto_llena(marcadas)                    # impresa a 1 por página
        Examen.objects.filter(id=self.ex.id).update(hojas_por_pagina=4)
        d = self.c.post(self.url('escanear/foto/'), {'foto': foto, 'por_pagina': '4'}).json()
        self.assertTrue(d['ok'], d)
        self.assertEqual({int(k): v for k, v in d['respuestas'].items() if v}, marcadas)
        self.assertEqual(d['dudas'], [])

    def test_hoja_de_4_por_pagina_con_el_examen_en_1(self):
        marcadas = {n: l for n, l in zip(range(1, 9), 'DCBADCBA')}
        foto = self.foto_de_reparto(4, marcadas)
        Examen.objects.filter(id=self.ex.id).update(hojas_por_pagina=1)
        d = self.c.post(self.url('escanear/foto/'), {'foto': foto, 'por_pagina': '1'}).json()
        self.assertTrue(d['ok'], d)
        self.assertEqual({int(k): v for k, v in d['respuestas'].items() if v}, marcadas)


class PistasDeLaCamara(UnaSolaIdaAlServidor):
    """Una mancha oscura en el fondo (un sofá, una sombra) no debe correr la lectura de la hoja entera."""

    def _foto_con_mancha(self, marcadas):
        hoja = Image.open(self.foto_llena(marcadas)).convert('RGB')
        W, Hh = hoja.size
        m = 150
        fondo = Image.new('RGB', (W + 2 * m, Hh + 2 * m), (70, 70, 78))
        fondo.paste(hoja, (m, m))
        d = ImageDraw.Draw(fondo)
        esc = W / H.geometria(1)['ancho_mm']
        lado = int(H.geometria(1)['marca_mm'] * esc)
        d.rectangle([10, 10, 10 + lado * 2.4, 10 + lado * 2.4], fill=(250, 250, 250))       # papel suelto en el fondo
        d.rectangle([10 + lado * 0.7, 10 + lado * 0.7, 10 + lado * 1.7, 10 + lado * 1.7], fill=(0, 0, 0))
        g = H.geometria(1)
        pistas = [[x * esc + m, (g['alto_mm'] - y) * esc + m] for x, y in g['marcas_mm']]
        b = io.BytesIO()
        fondo.save(b, 'JPEG', quality=90)
        return b.getvalue(), pistas

    def test_con_las_marcas_de_la_camara_lee_bien(self):
        marcadas = {1: 'A', 2: 'B', 3: 'C', 4: 'D', 5: 'A', 6: 'B', 7: 'C'}
        datos, pistas = self._foto_con_mancha(marcadas)
        sin = self.c.post(self.url('escanear/foto/'), {'foto': SimpleUploadedFile('h.jpg', datos, 'image/jpeg')}).json()
        con = self.c.post(self.url('escanear/foto/'), {'foto': SimpleUploadedFile('h.jpg', datos, 'image/jpeg'),
                                                       'marcas': json.dumps(pistas)}).json()
        print('SIN pistas:', sin.get('ok'), {int(k): v for k, v in sin.get('respuestas', {}).items() if v}, len(sin.get('dudas', [])))
        self.assertTrue(con['ok'], con)
        self.assertEqual({int(k): v for k, v in con['respuestas'].items() if v}, marcadas)
        self.assertEqual(con['dudas'], [])

    def test_pistas_malas_no_estorban(self):
        marcadas = {1: 'A', 2: 'B'}
        datos, pistas = self._foto_con_mancha(marcadas)
        malas = [[5, 5], [6, 6], [7, 7], [8, 8]]
        d = self.c.post(self.url('escanear/foto/'), {'foto': SimpleUploadedFile('h.jpg', datos, 'image/jpeg'),
                                                     'marcas': json.dumps(malas)}).json()
        self.assertTrue(d['ok'] or d.get('error'), d)
        d = self.c.post(self.url('escanear/foto/'), {'foto': SimpleUploadedFile('h.jpg', datos, 'image/jpeg'),
                                                     'marcas': 'esto no es json'}).json()
        self.assertIn('ok', d)


class MarcaPegadaAlBorde(UnaSolaIdaAlServidor):
    """La hoja casi toca el borde de la foto: la marca de esa esquina queda sin papel alrededor."""

    def test_marca_al_borde(self):
        marcadas = {1: 'A', 2: 'B', 3: 'C', 4: 'D', 5: 'A', 6: 'B', 7: 'C'}
        hoja = Image.open(self.foto_llena(marcadas)).convert('RGB').rotate(2.5, expand=True, fillcolor=(70, 70, 78))
        g = H.geometria(1)
        W0 = Image.open(self.foto_llena(marcadas)).size[0]
        esc = W0 / g['ancho_mm']
        # Se recorta arriba y a la izquierda justo sobre la marca de esa esquina.
        recorte = int((g['marcas_mm'][0][0] - g['marca_mm'] * 0.55) * esc)
        foto = hoja.crop((recorte, recorte, hoja.width, hoja.height))
        b = io.BytesIO(); foto.save(b, 'JPEG', quality=90)
        datos = b.getvalue()
        # Dónde quedaron las marcas (como las vería la cámara): se buscan en la imagen con el motor del servidor.
        sin = self.c.post(self.url('escanear/foto/'), {'foto': SimpleUploadedFile('h.jpg', datos, 'image/jpeg')}).json()
        print('SIN pistas:', sin.get('ok'), sin.get('error'), {int(k): v for k, v in sin.get('respuestas', {}).items() if v}, len(sin.get('dudas', [])))
        open('/tmp/claude-0/-home-user-mcolegio-com-co/992cef15-1ebd-50c5-a051-1131c8cc80c9/scratchpad/caso/borde.jpg', 'wb').write(datos)


class FotoConFondo(UnaSolaIdaAlServidor):
    """La foto de todo el cuadro, con la hoja más pequeña sobre una tela con textura (como al oprimir el botón)."""

    def test_con_y_sin_pistas(self):
        import random
        marcadas = {1: 'A', 2: 'B', 3: 'C', 4: 'D', 5: 'A', 6: 'B', 7: 'C'}
        hoja = Image.open(self.foto_llena(marcadas)).convert('RGB')
        W, Hh = hoja.size
        random.seed(3)
        fondo = Image.new('RGB', (int(W * 1.45), int(Hh * 1.3)), (95, 95, 100))
        d = ImageDraw.Draw(fondo)
        for _ in range(2500):                                   # tela con textura: motas oscuras y claras
            x, y, t = random.randrange(fondo.width), random.randrange(fondo.height), random.randint(4, 22)
            c = random.choice([25, 40, 60, 140, 170])
            d.rectangle([x, y, x + t, y + t], fill=(c, c, c + 4))
        ox, oy = int(W * 0.12), int(Hh * 0.08)
        fondo.paste(hoja.rotate(-3, expand=False, fillcolor=(95, 95, 100)), (ox, oy))
        b = io.BytesIO(); fondo.save(b, 'JPEG', quality=88)
        datos = b.getvalue()
        g = H.geometria(1)
        esc = W / g['ancho_mm']
        import math
        cx0, cy0, a = W / 2, Hh / 2, math.radians(3)
        def girar(x, y):          # rotate(-3) de PIL gira en el sentido del reloj, alrededor del centro
            dx, dy = x - cx0, y - cy0
            return [cx0 + dx * math.cos(a) - dy * math.sin(a) + ox, cy0 + dx * math.sin(a) + dy * math.cos(a) + oy]
        pistas = [girar(x * esc, (g['alto_mm'] - y) * esc) for x, y in g['marcas_mm']]
        sin = self.c.post(self.url('escanear/foto/'), {'foto': SimpleUploadedFile('h.jpg', datos, 'image/jpeg')}).json()
        con = self.c.post(self.url('escanear/foto/'), {'foto': SimpleUploadedFile('h.jpg', datos, 'image/jpeg'),
                                                       'marcas': json.dumps(pistas)}).json()
        print('SIN pistas:', sin.get('ok'), sin.get('error'), {int(k): v for k, v in sin.get('respuestas', {}).items() if v}, len(sin.get('dudas', [])))
        print('CON pistas:', con.get('ok'), {int(k): v for k, v in con.get('respuestas', {}).items() if v}, len(con.get('dudas', [])))
        open('/tmp/claude-0/-home-user-mcolegio-com-co/992cef15-1ebd-50c5-a051-1131c8cc80c9/scratchpad/caso/fondo.jpg', 'wb').write(datos)
        self.assertEqual({int(k): v for k, v in con['respuestas'].items() if v}, marcadas)


class HojaCurvada(UnaSolaIdaAlServidor):
    """El papel doblado: las esquinas están bien, pero en el centro las burbujas quedan corridas."""

    def _curvada(self, marcadas, fuerza):
        import numpy as np
        hoja = Image.open(self.foto_llena(marcadas)).convert('RGB')
        a = np.asarray(hoja)
        Hh, W = a.shape[:2]
        yy, xx = np.mgrid[0:Hh, 0:W].astype(np.float32)
        # Abombado: el centro se corre hacia arriba y a la izquierda; las esquinas quedan quietas.
        b = np.sin(np.pi * xx / W) * np.sin(np.pi * yy / Hh)
        sx = np.clip(xx + fuerza * b, 0, W - 1).astype(int)
        sy = np.clip(yy + fuerza * b, 0, Hh - 1).astype(int)
        out = Image.fromarray(a[sy, sx])
        buf = io.BytesIO(); out.save(buf, 'JPEG', quality=90)
        return SimpleUploadedFile('h.jpg', buf.getvalue(), 'image/jpeg')

    def test_hoja_curvada(self):
        marcadas = {1: 'A', 2: 'B', 3: 'C', 4: 'D', 5: 'A', 6: 'B', 7: 'C'}
        radio_px = H.mapa_de_examen(self.ex)['radio_mm'] * (Image.open(self.foto_llena(marcadas)).size[0] / H.geometria(1)['ancho_mm'])
        d = self.c.post(self.url('escanear/foto/'), {'foto': self._curvada(marcadas, radio_px * 1.1)}).json()
        print('CURVADA', round(radio_px, 1), d.get('ok'), {int(k): v for k, v in d.get('respuestas', {}).items() if v}, [x['motivo'] for x in d.get('dudas', [])])
        self.assertTrue(d['ok'], d)
        self.assertEqual({int(k): v for k, v in d['respuestas'].items() if v}, marcadas)
        self.assertEqual(d['dudas'], [])


class HojaCurvadaGrande(CamaraEnVivo):
    """60 preguntas, como un simulacro, con el papel abombado."""
    test_la_pantalla_trae_la_camara_y_donde_van_las_marcas = None
    test_lee_la_foto_recortada_como_la_manda_la_camara = None
    test_calentar_con_get = None

    def setUp(self):
        import random
        self.c = self.cliente(self.rectora)
        self.c.post('/puntoexacto/nuevo/', {
            'titulo': 'Simulacro', 'fecha': '2026-10-06', 'componente': 'SABER',
            'numero_preguntas': '60', 'numero_opciones': '4', 'hojas_por_pagina': '1',
            'metodo': 'con_piso', 'nota_todo_mal': '1', 'nota_nada_marcado': '1', 'opciones_por_pregunta': '{}'})
        self.ex = Examen.objects.get()
        random.seed(7)
        datos = {'metodo': 'con_piso'}
        for n in range(1, 61):
            datos.update({f'correcta_{n}': random.choice('ABCD'), f'opciones_{n}': '4', f'puntos_{n}': '1'})
        self.c.post(f'/puntoexacto/{self.ex.id}/clave/', datos)
        self.hoja = Hoja.objects.create(examen=self.ex, identificador=f'PE-{self.ex.id:05d}-0001', nombre_libre='Juan')

    def test_60_preguntas_abombada(self):
        import random
        import time
        import numpy as np
        random.seed(11)
        marcadas = {n: random.choice('ABCD') for n in range(1, 61) if random.random() > 0.1}
        pdf = self.c.get(self.url('hojas/imprimir/')).content
        with tempfile.TemporaryDirectory() as d:
            open(f'{d}/h.pdf', 'wb').write(pdf)
            subprocess.run(['pdftoppm', '-r', '150', '-png', '-singlefile', f'{d}/h.pdf', f'{d}/h'], check=True)
            hoja = Image.open(f'{d}/h.png').convert('RGB')
        info = H.mapa_de_examen(self.ex)
        esc = hoja.width / info['hoja_w_mm']
        alto_mm = hoja.height / esc
        dib = ImageDraw.Draw(hoja)
        r = info['radio_mm'] * esc
        for p, l in marcadas.items():
            x, y = info['mapa'][f'{p}{l}']
            dib.ellipse([x * esc - r * 0.75, (alto_mm - y) * esc - r * 0.75, x * esc + r * 0.75, (alto_mm - y) * esc + r * 0.75],
                        fill=(70, 70, 75))
        a = np.asarray(hoja)
        Hh, W = a.shape[:2]
        yy, xx = np.mgrid[0:Hh, 0:W].astype(np.float32)
        b = np.sin(np.pi * xx / W) * np.sin(np.pi * yy / Hh)
        for fuerza in (0.0, r * 0.6, r * 1.0, r * 1.2, r * 1.4, r * 1.7):
            sx = np.clip(xx + fuerza * b, 0, W - 1).astype(int)
            sy = np.clip(yy - fuerza * 0.6 * b, 0, Hh - 1).astype(int)
            out = Image.fromarray(a[sy, sx]).resize((1600, round(Hh * 1600 / W)))
            buf = io.BytesIO(); out.save(buf, 'JPEG', quality=88)
            if os.environ.get('PE_SAL'):
                out.save(os.path.join(os.environ['PE_SAL'], f'abombada_{round(fuerza / r, 1)}.jpg'), quality=88)
            t = time.perf_counter()
            dd = self.c.post(self.url('escanear/foto/'), {'foto': SimpleUploadedFile('h.jpg', buf.getvalue(), 'image/jpeg')}).json()
            ms = round(1000 * (time.perf_counter() - t))
            leidas = {int(k): v for k, v in dd['respuestas'].items() if v}
            malas = [n for n in range(1, 61) if leidas.get(n, '') != marcadas.get(n, '')]
            print('ABOMBADA', round(fuerza / r, 1), 'radios:', 'malas', malas, 'dudas', len(dd['dudas']), ms, 'ms')
            if fuerza <= r * 1.0:
                self.assertEqual(malas, [], fuerza)
