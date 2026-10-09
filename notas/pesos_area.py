# notas/pesos_area.py
"""Cuánto pesa cada materia dentro de su área, según el grado.

Hay porcentajes generales (PonderacionAreaMateria, los de siempre) y un grado
puede tener los suyos (PonderacionGrado): Física y Química no pesan lo mismo en
6.° que en 10.°. Boletín, sábana y estadísticas preguntan aquí, con el grado del
curso, y reciben {(area_id, materia_id): peso}.

Qué materias forman cada área lo decide siempre el general: un grado solo
cambia el peso, nunca agrega ni quita materias de un área.
"""
from decimal import Decimal

from .models.academicos import PonderacionAreaMateria, PonderacionGrado


def pesos_areas(colegio, grado=None, materias=None):
    """{(area_id, materia_id): Decimal} para ese grado (None = los generales)."""
    qs = PonderacionAreaMateria.objects.filter(colegio=colegio)
    if materias is not None:
        qs = qs.filter(materia__in=materias)
    pesos = {(p.area_id, p.materia_id): p.peso_porcentual for p in qs}
    if grado is not None and pesos:
        propios = PonderacionGrado.objects.filter(colegio=colegio, grado=grado)
        if materias is not None:
            propios = propios.filter(materia__in=materias)
        for p in propios:
            if (p.area_id, p.materia_id) in pesos:
                pesos[(p.area_id, p.materia_id)] = p.peso_porcentual
    return pesos


def grados_con_pesos_propios(colegio):
    return sorted(set(PonderacionGrado.objects.filter(colegio=colegio).values_list('grado', flat=True)))


def guardar_grado(colegio, grado, valores):
    """valores = {(area_id, materia_id): peso}. Solo pares que existen en el general."""
    validos = set(PonderacionAreaMateria.objects.filter(colegio=colegio).values_list('area_id', 'materia_id'))
    n = 0
    for (area_id, materia_id), peso in valores.items():
        if (area_id, materia_id) not in validos:
            continue
        PonderacionGrado.objects.update_or_create(
            colegio=colegio, area_id=area_id, materia_id=materia_id, grado=grado,
            defaults={'peso_porcentual': Decimal(str(peso))})
        n += 1
    return n


def volver_al_general(colegio, grado):
    return PonderacionGrado.objects.filter(colegio=colegio, grado=grado).delete()[0]
