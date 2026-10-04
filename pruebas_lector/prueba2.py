# -*- coding: utf-8 -*-
"""Casos difíciles: lo que de verdad pasa con hojas de salón."""
import sys, random
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, '..')
sys.path.insert(0, '.')
from fabrica import hoja_limpia, rellenar, fotografiar
from puntoexacto import hojas, lector

DURO = dict(inclinacion=.10, giro=-3, sombra=.32, desenfoque=1.0, ruido=.012)


def _base(preguntas=20, opciones=4, por_pagina=1, dpi=200):
    img, info, px = hoja_limpia(preguntas, opciones, por_pagina, dpi=dpi)
    return img, info, px, hojas.geometria(por_pagina)


def _leer(foto, info, geo, preguntas, letras):
    return lector.leer(foto, geo, info['mapa'], info['radio_mm'], preguntas,
                       lambda n: letras)


def caso_doble_marca():
    img, info, px, geo = _base()
    verdad = {n: 'B' for n in range(1, 21)}
    llena = rellenar(img, info, px, verdad, 'lapicero', semilla=1)
    # El estudiante marcó además la C en las preguntas 3, 9 y 15
    llena = rellenar(llena, info, px, {3: 'C', 9: 'C', 15: 'C'}, 'lapicero', semilla=2)
    r = _leer(fotografiar(llena, semilla=1, **DURO), info, geo, 20, 'ABCD')
    dobles = {d['pregunta'] for d in r['dudas'] if d['motivo'] == 'hay dos marcadas'}
    bien_resto = all(r['respuestas'][n] == 'B' for n in range(1, 21) if n not in (3, 9, 15))
    return ('doble marca detectada', dobles == {3, 9, 15} and bien_resto,
            f'marcó dudosas {sorted(dobles)}, esperado [3, 9, 15]')


def caso_borrado():
    """Borró la A y marcó la C: queda un gris tenue donde borró."""
    img, info, px, geo = _base()
    verdad = {n: 'C' for n in range(1, 21)}
    llena = rellenar(img, info, px, verdad, 'lapicero', semilla=1)
    fantasma = {n: 'A' for n in (2, 5, 11, 18)}
    llena = rellenar(llena, info, px, fantasma, 'flojo', semilla=9)
    r = _leer(fotografiar(llena, semilla=2, **DURO), info, geo, 20, 'ABCD')
    ok = all(r['respuestas'][n] == 'C' for n in range(1, 21))
    return ('borrón no confunde', ok,
            f'leyó {[r["respuestas"][n] for n in (2,5,11,18)]} donde esperaba C')


def caso_raya():
    """Una raya de lápiz cruzando la hoja, de las que hace cualquiera."""
    img, info, px, geo = _base()
    verdad = {n: 'D' for n in range(1, 21)}
    llena = rellenar(img, info, px, verdad, 'lapiz', semilla=4)
    d = ImageDraw.Draw(llena)
    d.line([(300, 900), (1400, 1250)], fill=90, width=6)
    r = _leer(fotografiar(llena, semilla=3, **DURO), info, geo, 20, 'ABCD')
    ok = sum(1 for n in range(1, 21) if r['respuestas'][n] == 'D')
    return ('raya atravesada', ok >= 19, f'{ok}/20 correctas')


def caso_chicas(por_pagina, preguntas):
    """Hojas de 4 y 8 por página: burbujas mucho más pequeñas."""
    img, info, px, geo = _base(preguntas, 4, por_pagina, dpi=250)
    rnd = random.Random(por_pagina)
    verdad = {n: rnd.choice('ABCD') for n in range(1, preguntas + 1)}
    llena = rellenar(img, info, px, verdad, 'lapiz', semilla=por_pagina)
    # Solo la primera hoja de la página: se recorta su celda.
    w, h = llena.size
    cols, filas = hojas.REPARTO[por_pagina]
    celda = llena.crop((0, 0, w // cols, h // filas))
    foto = fotografiar(celda, semilla=por_pagina, **DURO)
    try:
        r = _leer(foto, info, geo, preguntas, 'ABCD')
    except lector.LecturaFallida as e:
        return (f'{por_pagina} por página', False, f'rechazada: {e}')
    ok = sum(1 for n in range(1, preguntas + 1) if r['respuestas'][n] == verdad[n])
    return (f'{por_pagina} por página ({preguntas} preg.)', ok == preguntas,
            f'{ok}/{preguntas}')


def caso_ocho_opciones():
    img, info, px, geo = _base(15, 8, 1)
    rnd = random.Random(11)
    verdad = {n: rnd.choice('ABCDEFGH') for n in range(1, 16)}
    llena = rellenar(img, info, px, verdad, 'lapiz', semilla=11)
    r = _leer(fotografiar(llena, semilla=11, **DURO), info, geo, 15, 'ABCDEFGH')
    ok = sum(1 for n in range(1, 16) if r['respuestas'][n] == verdad[n])
    return ('8 opciones', ok == 15, f'{ok}/15')


def caso_baja_resolucion():
    img, info, px, geo = _base(dpi=100)
    rnd = random.Random(5)
    verdad = {n: rnd.choice('ABCD') for n in range(1, 21)}
    llena = rellenar(img, info, px, verdad, 'lapiz', semilla=5)
    try:
        r = _leer(fotografiar(llena, semilla=5, **DURO), info, geo, 20, 'ABCD')
    except lector.LecturaFallida as e:
        return ('foto de baja resolución', True, f'rechazada con aviso: {e}')
    ok = sum(1 for n in range(1, 21) if r['respuestas'][n] == verdad[n])
    return ('foto de baja resolución', ok >= 19, f'{ok}/20')


def caso_esquina_tapada():
    """Un dedo sobre una esquina. Debe RECHAZAR, no inventar."""
    img, info, px, geo = _base()
    verdad = {n: 'A' for n in range(1, 21)}
    llena = rellenar(img, info, px, verdad, 'lapicero', semilla=6)
    foto = fotografiar(llena, semilla=6, **DURO)
    d = ImageDraw.Draw(foto)
    w, h = foto.size
    d.ellipse([w - 330, h - 330, w - 40, h - 40], fill=120)   # dedo
    try:
        r = _leer(foto, info, geo, 20, 'ABCD')
    except lector.LecturaFallida:
        return ('esquina tapada', True, 'rechazada, como debe ser')
    malas = sum(1 for n in range(1, 21) if r['respuestas'][n] != 'A')
    # Si no rechaza, al menos no debe entregar respuestas equivocadas en silencio
    return ('esquina tapada', malas == 0 or len(r['dudas']) > 0,
            f'{malas} errores, {len(r["dudas"])} dudas')


def caso_hoja_en_blanco():
    img, info, px, geo = _base()
    r = _leer(fotografiar(img, semilla=8, **DURO), info, geo, 20, 'ABCD')
    inventadas = sum(1 for n in range(1, 21) if r['respuestas'][n])
    return ('hoja en blanco', inventadas == 0, f'inventó {inventadas} marcas')


if __name__ == '__main__':
    casos = [caso_doble_marca(), caso_borrado(), caso_raya(),
             caso_chicas(4, 20), caso_chicas(8, 10), caso_ocho_opciones(),
             caso_baja_resolucion(), caso_esquina_tapada(), caso_hoja_en_blanco()]
    bien = 0
    for nombre, ok, detalle in casos:
        print(f'{"OK " if ok else "MAL"} {nombre:32} {detalle}')
        bien += ok
    print(f'\n{bien}/{len(casos)} casos difíciles superados')
