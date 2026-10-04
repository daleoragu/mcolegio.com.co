# -*- coding: utf-8 -*-
"""Banco de pruebas del lector contra fotos sintéticas con verdad conocida."""
import sys, random, itertools, zlib
sys.path.insert(0, '..')
sys.path.insert(0, '.')
from fabrica import hoja_limpia, rellenar, fotografiar
from puntoexacto import hojas, lector

CONDICIONES = [
    ('ideal',            dict(inclinacion=0,    giro=0,    sombra=0,   desenfoque=0,   ruido=0)),
    ('leve',             dict(inclinacion=.03,  giro=1.5,  sombra=.15, desenfoque=.6,  ruido=.006)),
    ('inclinada',        dict(inclinacion=.14,  giro=-4,   sombra=.25, desenfoque=.9,  ruido=.010)),
    ('muy inclinada',    dict(inclinacion=.22,  giro=7,    sombra=.30, desenfoque=1.0, ruido=.012)),
    ('sombra fuerte',    dict(inclinacion=.05,  giro=-2,   sombra=.55, desenfoque=.8,  ruido=.010)),
    ('oscura',           dict(inclinacion=.06,  giro=3,    sombra=.35, desenfoque=1.0, ruido=.015, brillo=.62)),
    ('quemada',          dict(inclinacion=.04,  giro=-1,   sombra=.10, desenfoque=.7,  ruido=.008, brillo=1.35)),
    ('movida',           dict(inclinacion=.08,  giro=2.5,  sombra=.25, desenfoque=2.4, ruido=.012)),
    ('ruidosa',          dict(inclinacion=.07,  giro=-3,   sombra=.30, desenfoque=.8,  ruido=.035)),
    ('girada al revés',  dict(inclinacion=.05,  giro=-8,   sombra=.20, desenfoque=.9,  ruido=.010)),
]
ESTILOS = ['lapicero', 'lapiz', 'flojo']


def una(preguntas, opciones, por_pagina, dpi, cond, estilo, semilla, secciones=None):
    img, info, px = hoja_limpia(preguntas, opciones, por_pagina, dpi=dpi, secciones=secciones)
    geo = hojas.geometria(por_pagina)
    letras = 'ABCDEFGHIJ'[:opciones]
    rnd = random.Random(semilla)
    verdad = {n: rnd.choice(letras) for n in range(1, preguntas + 1)}
    for n in rnd.sample(range(1, preguntas + 1), max(1, preguntas // 10)):
        verdad[n] = ''                       # algunas en blanco
    llena = rellenar(img, info, px, verdad, estilo, semilla=semilla)
    foto = fotografiar(llena, semilla=semilla, **cond)
    try:
        r = lector.leer(foto, geo, info['mapa'], info['radio_mm'], preguntas,
                        lambda n: letras)
    except lector.LecturaFallida as e:
        return None, str(e), verdad, {}
    return r, None, verdad, r['respuestas']


def correr(repeticiones=1):
    total = aciertos = fallos_foto = 0
    errores_detalle = []
    por_condicion = {}
    for (nombre, cond), estilo, dpi, rep in itertools.product(
            CONDICIONES, ESTILOS, (150, 200), range(repeticiones)):
        sem = zlib.crc32(f'{nombre}|{estilo}|{dpi}|{rep}'.encode()) % 9999
        r, error, verdad, resp = una(20, 4, 1, dpi, cond, estilo, semilla=sem)
        n = len(verdad)
        if error:
            fallos_foto += 1
            ok = 0
        else:
            ok = sum(1 for k in verdad if resp.get(k, '') == verdad[k])
            for k in verdad:
                if resp.get(k, '') != verdad[k]:
                    errores_detalle.append((nombre, estilo, dpi, k, verdad[k], resp.get(k, '')))
        total += n; aciertos += ok
        d = por_condicion.setdefault(nombre, [0, 0, 0])
        d[0] += ok; d[1] += n; d[2] += 1 if error else 0
    print(f'{"condición":18} {"aciertos":>12}  {"%":>6}  rechazos')
    for nombre, (ok, n, err) in por_condicion.items():
        print(f'{nombre:18} {ok:>6}/{n:<5} {100*ok/n:>6.1f}  {err}')
    print(f'\nTOTAL {aciertos}/{total} = {100*aciertos/total:.2f}%   fotos rechazadas: {fallos_foto}')
    if errores_detalle:
        print('\nerrores:')
        for e in errores_detalle[:15]:
            print('  ', e)
    return aciertos / total


if __name__ == '__main__':
    import sys as _s; correr(int(_s.argv[1]) if len(_s.argv)>1 else 1)
