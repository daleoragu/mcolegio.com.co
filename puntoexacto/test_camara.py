# -*- coding: utf-8 -*-
"""Escanear con la cámara en vivo.

    python manage.py test puntoexacto
"""
import io
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
        geo = json.loads(re.search(r'id="pe-datos-geo"[^>]*>(.*?)</script>', html, re.S).group(1))
        esperado = H.geometria(1, 'PE-00001-0001')
        self.assertEqual(geo['ancho_mm'], esperado['ancho_mm'])
        self.assertEqual([list(p) for p in esperado['marcas_mm']], geo['marcas_mm'])

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
