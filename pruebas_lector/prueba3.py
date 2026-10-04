# -*- coding: utf-8 -*-
"""¿Reconoce de quién es la hoja, y nunca se la asigna a otro?"""
import sys, random, io, subprocess, tempfile, os
from PIL import Image
sys.path.insert(0, '..')
sys.path.insert(0, '.')
from fabrica import rellenar, fotografiar
from puntoexacto import hojas, lector

CONDICIONES = {
    'ideal':        dict(inclinacion=0,   giro=0,   sombra=0,   desenfoque=0,  ruido=0),
    'normal':       dict(inclinacion=.06, giro=2,   sombra=.20, desenfoque=.8, ruido=.008),
    'dura':         dict(inclinacion=.10, giro=-3,  sombra=.32, desenfoque=1.0, ruido=.012),
    'muy dura':     dict(inclinacion=.20, giro=6,   sombra=.45, desenfoque=1.6, ruido=.020),
    'oscura':       dict(inclinacion=.07, giro=-2,  sombra=.35, desenfoque=1.0, ruido=.015, brillo=.60),
}

def hoja_de(ident, dpi=200):
    datos = {'colegio':'X','materia':'M','curso':'901','periodo':'P','titulo':'T',
             'estudiante':'E','documento':'1','docente':'','fecha':''}
    buf = io.BytesIO()
    info = hojas.generar(buf, [datos], preguntas=20, opciones=4, por_pagina=1,
                         identificadores=[ident], devolver_mapa=True)
    with tempfile.TemporaryDirectory() as d:
        open(f'{d}/h.pdf','wb').write(buf.getvalue())
        subprocess.run(['pdftoppm','-r',str(dpi),'-gray','-png','-f','1','-l','1',
                        f'{d}/h.pdf',f'{d}/p'], check=True)
        img = Image.open(f'{d}/'+[f for f in os.listdir(d) if f.endswith('.png')][0]).convert('L').copy()
    return img, info

def correr():
    candidatos = [f'PE-00042-{i:04d}' for i in range(1, 41)]
    bien = no_leyo = equivocado = 0
    for nombre, cond in CONDICIONES.items():
        for dpi in (150, 200, 300):
            for idx in (1, 13, 26, 40):
                ident = f'PE-00042-{idx:04d}'
                img, info = hoja_de(ident, dpi)
                rnd = random.Random(idx)
                verdad = {n: rnd.choice('ABCD') for n in range(1,21)}
                foto = fotografiar(rellenar(img, info, dpi/25.4, verdad, 'lapiz', semilla=idx),
                                   semilla=idx, **cond)
                try:
                    gris = lector._a_gris(foto)
                    H, _ = lector.matriz_de_hoja(gris, geo := hojas.geometria(1, ident))
                    leido, como = lector.identificar_hoja(gris, H, geo, candidatos)
                except lector.LecturaFallida as e:
                    leido, como = None, str(e)
                if leido == ident: bien += 1
                elif leido is None: no_leyo += 1
                else:
                    equivocado += 1
                    print(f'  !! {nombre} {dpi}dpi: esperado {ident}, leyó {leido}')
    total = bien + no_leyo + equivocado
    print(f'identificadas {bien}/{total}   no se pudo leer {no_leyo}   '
          f'ASIGNADAS A OTRO {equivocado}')
    return equivocado

if __name__ == '__main__':
    sys.exit(1 if correr() else 0)
