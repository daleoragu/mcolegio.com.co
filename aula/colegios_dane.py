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
