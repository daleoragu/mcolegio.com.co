# -*- coding: utf-8 -*-
"""Fábrica de fotos falsas de hojas de respuesta, para probar el lector.

No reemplaza las fotos reales de David: el lápiz tiene textura, el papel se
curva, el flash quema una esquina y nada de eso se simula bien. Lo que sí
permite es construir el lector y medirlo contra una verdad conocida, de modo
que cuando lleguen las fotos reales el trabajo sea ajustar y no empezar.
"""
import io, math, random
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

import sys
sys.path.insert(0, '..')
from puntoexacto import hojas as H

MM = 72 / 25.4  # puntos por mm (unidad de reportlab)


def hoja_limpia(preguntas=20, opciones=4, por_pagina=1, dpi=200, secciones=None):
    """Devuelve (imagen PIL en gris, info del mapa, px_por_mm)."""
    datos = {'colegio': 'I.E.T. GENERAL SANTANDER', 'materia': 'Matemáticas',
             'curso': '901', 'periodo': 'Período 3', 'titulo': 'Prueba de lector',
             'estudiante': 'RAMOS GUTIÉRREZ DAVID LEONARDO',
             'documento': '1.098.765.432', 'docente': '', 'fecha': ''}
    buf = io.BytesIO()
    info = H.generar(buf, [datos], preguntas=preguntas, opciones=opciones,
                     por_pagina=por_pagina, identificadores=['PE-00042-0007'],
                     secciones=secciones, devolver_mapa=True)
    import subprocess, tempfile, os
    with tempfile.TemporaryDirectory() as d:
        pdf = os.path.join(d, 'h.pdf')
        open(pdf, 'wb').write(buf.getvalue())
        subprocess.run(['pdftoppm', '-r', str(dpi), '-gray', '-png', '-f', '1', '-l', '1',
                        pdf, os.path.join(d, 'p')], check=True)
        png = [f for f in os.listdir(d) if f.endswith('.png')][0]
        img = Image.open(os.path.join(d, png)).convert('L').copy()
    return img, info, dpi / 25.4


def rellenar(img, info, px_mm, respuestas, estilo='lapiz', semilla=0):
    """Pinta las burbujas marcadas. respuestas = {1:'A', 2:'C', ...}."""
    rnd = random.Random(semilla)
    alto_mm = info['hoja_h_mm']
    radio_px = info['radio_mm'] * px_mm
    img = img.copy()
    d = ImageDraw.Draw(img)
    for pregunta, letra in respuestas.items():
        if not letra:
            continue
        clave = f'{pregunta}{letra}'
        if clave not in info['mapa']:
            continue
        x_mm, y_mm = info['mapa'][clave]
        cx, cy = x_mm * px_mm, (alto_mm - y_mm) * px_mm
        # El trazo real no es un disco perfecto: se sale un poco y no llena todo.
        r = radio_px * rnd.uniform(0.80, 1.02)
        gris = {'lapiz': rnd.randint(60, 115), 'lapicero': rnd.randint(20, 55),
                'flojo': rnd.randint(140, 180)}[estilo]
        dx, dy = rnd.uniform(-.18, .18) * radio_px, rnd.uniform(-.18, .18) * radio_px
        d.ellipse([cx - r + dx, cy - r + dy, cx + r + dx, cy + r + dy], fill=gris)
    return img


def _homografia(origen, destino):
    """Matriz de la transformación proyectiva que lleva origen -> destino."""
    A, b = [], []
    for (x, y), (u, v) in zip(origen, destino):
        A.append([x, y, 1, 0, 0, 0, -u * x, -u * y]); b.append(u)
        A.append([0, 0, 0, x, y, 1, -v * x, -v * y]); b.append(v)
    h = np.linalg.solve(np.array(A, float), np.array(b, float))
    return np.append(h, 1).reshape(3, 3)


def fotografiar(img, inclinacion=0.0, giro=0.0, sombra=0.0, desenfoque=0.0,
                ruido=0.0, brillo=1.0, semilla=0, margen=0.08):
    """Convierte la hoja perfecta en algo parecido a una foto de celular."""
    rnd = random.Random(semilla)
    w, h = img.size
    lienzo_w, lienzo_h = int(w * (1 + 2 * margen)), int(h * (1 + 2 * margen))
    ox, oy = int(w * margen), int(h * margen)

    esquinas = [(0, 0), (w, 0), (w, h), (0, h)]
    destino = []
    for i, (x, y) in enumerate(esquinas):
        # Perspectiva: se encoge un lado, como cuando el celular no está plano.
        f = 1 - inclinacion * (1 if i in (0, 1) else 0)
        cx, cy = w / 2, h / 2
        nx = cx + (x - cx) * f
        ny = cy + (y - cy) * (1 - inclinacion * 0.35 * (1 if i in (0, 1) else 0))
        a = math.radians(giro)
        rx = cx + (nx - cx) * math.cos(a) - (ny - cy) * math.sin(a)
        ry = cy + (nx - cx) * math.sin(a) + (ny - cy) * math.cos(a)
        destino.append((rx + ox + rnd.uniform(-3, 3), ry + oy + rnd.uniform(-3, 3)))

    M = _homografia(destino, esquinas)          # inversa: destino -> origen
    salida = Image.new('L', (lienzo_w, lienzo_h), 235)
    salida.paste(img.transform((lienzo_w, lienzo_h), Image.PERSPECTIVE,
                               M.flatten()[:8], Image.BICUBIC, fillcolor=255),
                 (0, 0))

    arr = np.asarray(salida, dtype=np.float32)
    if sombra:
        yy, xx = np.mgrid[0:lienzo_h, 0:lienzo_w]
        rampa = (xx / lienzo_w) * 0.6 + (yy / lienzo_h) * 0.4
        arr *= (1 - sombra * rampa)
        # Viñeta: los bordes siempre salen más oscuros que el centro.
        r = np.sqrt(((xx - lienzo_w / 2) / (lienzo_w / 2)) ** 2 +
                    ((yy - lienzo_h / 2) / (lienzo_h / 2)) ** 2)
        arr *= (1 - 0.18 * sombra * np.clip(r, 0, 1.4) ** 2)
    arr *= brillo
    if ruido:
        arr += np.random.default_rng(semilla).normal(0, ruido * 255, arr.shape)
    salida = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
    if desenfoque:
        salida = salida.filter(ImageFilter.GaussianBlur(desenfoque))
    return salida
