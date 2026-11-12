"""Las preguntas del banco de la olimpiada (aula/bancos/olimpiada_6_11.json) etiquetadas por DBA de Matemáticas.

La etiqueta sale del tema de cada pregunta; el docente la revisa. Se usan como «Preguntas tipo olimpiada» al final de
cada taller.
"""
import json
from functools import lru_cache
from pathlib import Path

from .base import unica

BANCO = Path(__file__).resolve().parents[2] / 'aula' / 'bancos' / 'olimpiada_6_11.json'

TEMA_A_DBA = {
    6: {'Decimales': 1, 'Fracciones': 1,
        'Operaciones': 2, 'MCD': 2, 'MCM': 2, 'Divisibilidad': 2, 'Números primos': 2, 'Potencias': 2,
        'Ángulos': 5, 'Perímetro': 5, 'Área': 5, 'Volumen': 5,
        'Triángulos': 6, 'Problemas': 9, 'Moda': 11, 'Promedio': 11, 'Probabilidad': 12},
    7: {'Números enteros': 1, 'Porcentajes': 1, 'Fracciones': 2, 'Escalas': 4, 'Volumen': 5,
        'Círculo': 6, 'Área': 6, 'Polígonos': 6,
        'Ecuaciones': 7, 'Proporcionalidad': 7, 'Proporcionalidad inversa': 7,
        'Mediana': 8, 'Promedio': 8, 'Probabilidad': 9},
}


@lru_cache(maxsize=1)
def _banco():
    return json.loads(BANCO.read_text(encoding='utf-8'))


def etiquetadas(grado):
    """[(dba, pregunta del banco)] del grado; las de un tema sin DBA asignado quedan fuera."""
    mapa = TEMA_A_DBA.get(int(grado), {})
    return [(mapa[q['tema']], q) for q in _banco() if q['grado'] == int(grado) and q['tema'] in mapa]


def resumen(grado):
    """{dba: {tema: cuántas}} para mostrar el etiquetado."""
    salida = {}
    for n, q in etiquetadas(grado):
        salida.setdefault(n, {}).setdefault(q['tema'], 0)
        salida[n][q['tema']] += 1
    return dict(sorted(salida.items()))


def bloques(grado, dba):
    """Las preguntas del banco para ese DBA como bloques de selección única."""
    salida = []
    for n, q in etiquetadas(grado):
        if n != dba:
            continue
        correctas = [o['texto'] for o in q['opciones'] if o['correcta']]
        if len(correctas) != 1:
            continue
        salida.append(unica(q['texto'], correctas[0], [o['texto'] for o in q['opciones'] if not o['correcta']]))
    return salida
