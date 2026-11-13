"""Directorio nacional de colegios (MEN, datos.gov.co, año 2025): para que el estudiante escoja su colegio por
Departamento → Municipio → Colegio al inscribirse en un evento, como en «Quiero Ser, Quiero Saber».

Archivo: aula/datos/colegios_dane.json = {fuente, municipios: {«73411»: [[dane, nombre, «O»|«P»], …]}}.
Se actualiza con el directorio del año siguiente (cfw5-qzt5) sin tocar el código.
"""
import json
from functools import lru_cache
from pathlib import Path

ARCHIVO = Path(__file__).resolve().parent / 'datos' / 'colegios_dane.json'


@lru_cache(maxsize=1)
def _datos():
    d = json.loads(ARCHIVO.read_text(encoding='utf-8'))
    por_dane = {c[0]: (c, mun) for mun, lista in d['municipios'].items() for c in lista}
    return d, por_dane


def fuente():
    return _datos()[0]['fuente']


def de_municipio(codigo):
    """[{dane, nombre, oficial}] del municipio (código DANE de 5 cifras), por nombre."""
    return [{'dane': c[0], 'nombre': c[1], 'oficial': c[2] == 'O'} for c in _datos()[0]['municipios'].get(str(codigo or ''), [])]


def buscar(dane):
    """{dane, nombre, oficial, municipio} del colegio, o None."""
    x = _datos()[1].get(''.join(ch for ch in str(dane or '') if ch.isdigit()))
    if not x:
        return None
    c, mun = x
    return {'dane': c[0], 'nombre': c[1], 'oficial': c[2] == 'O', 'municipio': mun}


@lru_cache(maxsize=1)
def _indice():
    """[(texto normalizado, colegio, municipio)] para buscar por palabras sin tildes ni mayúsculas."""
    from salon_digital.regiones import normal
    return [(normal(c[1]), c, mun) for mun, lista in _datos()[0]['municipios'].items() for c in lista]


def buscar_texto(q, mun='', limite=30):
    """Colegios cuyo nombre tiene todas las palabras de q (o su código DANE), en el municipio o en todo el país.
    [{dane, nombre, oficial, municipio, lugar}] con los del municipio primero."""
    from salon_digital.regiones import etiqueta, normal
    q = (q or '').strip()
    digitos = ''.join(ch for ch in q if ch.isdigit())
    palabras = [p for p in normal(q).split() if len(p) >= 2 and not p.isdigit()]
    if not palabras and len(digitos) < 5:
        return []
    salida = []
    for texto, c, m in _indice():
        if mun and m != mun:
            continue
        if (palabras and all(p in texto for p in palabras)) or (len(digitos) >= 5 and c[0].startswith(digitos)):
            salida.append({'dane': c[0], 'nombre': c[1], 'oficial': c[2] == 'O', 'municipio': m, 'lugar': etiqueta(m)})
            if len(salida) >= limite:
                break
    return salida
