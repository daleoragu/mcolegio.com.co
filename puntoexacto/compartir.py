# -*- coding: utf-8 -*-
"""Compartir un examen con otros docentes del colegio.

Cada docente recibe su PROPIA copia: preguntas, clave, puntos, bloques, formas
y cuadernillo. No se copian hojas ni notas. La copia queda sin asignatura ni
cursos, porque cada docente la aplica en los suyos y la lleva a su planilla;
así lo que uno cambie no le mueve el examen ni las notas al otro.
"""
from django.db import transaction

from .models import Bloque, Cuadernillo, Examen, Forma, Pregunta


def _clonar(obj, **cambios):
    obj.pk = None
    obj.id = None
    obj._state.adding = True
    for k, v in cambios.items():
        setattr(obj, k, v)
    obj.save()
    return obj


@transaction.atomic
def copiar(examen, docente, quien=None):
    """Copia `examen` para `docente`. `quien` es el Docente que comparte (puede ser None si es administración)."""
    original_id = examen.id
    origen = Examen.objects.get(id=original_id)
    nombre = ''
    if quien is not None:
        nombre = quien.user.get_full_name() or quien.user.username
    copia = _clonar(origen, docente=docente, asignacion=None, archivado=False,
                    compartido_por=quien, compartido_por_nombre=nombre or 'Administración')

    bloques = {}
    for b in Bloque.objects.filter(examen_id=original_id).order_by('id'):
        viejo = b.id
        bloques[viejo] = _clonar(b, examen=copia).id
    for p in Pregunta.objects.filter(examen_id=original_id).order_by('numero'):
        _clonar(p, examen=copia, bloque_id=bloques.get(p.bloque_id))
    for f in Forma.objects.filter(examen_id=original_id):
        _clonar(f, examen=copia)
    cuad = Cuadernillo.objects.filter(examen_id=original_id).first()
    if cuad:
        _clonar(cuad, examen=copia)
    return copia
