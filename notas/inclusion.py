"""Estudiantes de inclusión en los puestos y en el promedio del curso.

Cada colegio decide (Configuración de calificaciones → Estudiantes de inclusión):
* Puesto: compiten con todo el curso (GENERAL), tienen su propio puesto entre
  los de inclusión del curso (APARTE, sale «1 (inclusión)») o no llevan puesto
  (SIN, sale «—»).
* Promedio del curso: si cuentan o no en el promedio del curso, el ranking de
  cursos y las estadísticas generales.

Las notas y el boletín del estudiante nunca cambian: esto solo toca cómo se
compara con los demás.
"""
from .boletin.ponderacion import ajustes

SIN_PUESTO = '—'
SUFIJO = ' (inclusión)'


def es_inclusion(estudiante):
    return bool(getattr(estudiante, 'es_inclusion', False))


def modo_puesto(colegio):
    return getattr(ajustes(colegio), 'inclusion_puesto', 'GENERAL') or 'GENERAL'


def cuentan_en_promedio(colegio):
    return bool(getattr(ajustes(colegio), 'inclusion_en_promedio_curso', True))


def _numerar(filas, valor, campo, empates, sufijo=''):
    orden = sorted(filas, key=lambda f: valor(f) or 0, reverse=True)
    anterior, puesto = object(), 0
    for i, f in enumerate(orden):
        v = valor(f) or 0
        if not empates or v != anterior:
            puesto = i + 1
        anterior = v
        f[campo] = f'{puesto}{sufijo}' if sufijo else puesto


def asignar_puestos(filas, colegio, valor, estudiante, campo, empates=False):
    """Pone el puesto en `fila[campo]` según la regla del colegio.

    valor(fila) -> promedio con que se ordena; estudiante(fila) -> el Estudiante.
    Con empates=True, dos promedios iguales comparten puesto (1, 2, 2, 4)."""
    modo = modo_puesto(colegio)
    if modo == 'GENERAL':
        _numerar(filas, valor, campo, empates)
        return
    regulares = [f for f in filas if not es_inclusion(estudiante(f))]
    inclusion = [f for f in filas if es_inclusion(estudiante(f))]
    _numerar(regulares, valor, campo, empates)
    if modo == 'APARTE':
        _numerar(inclusion, valor, campo, empates, SUFIJO)
    else:
        for f in inclusion:
            f[campo] = SIN_PUESTO


def para_podio(filas, colegio, estudiante):
    """Los que pueden salir en el podio o el cuadro de honor del curso."""
    if modo_puesto(colegio) == 'GENERAL':
        return list(filas)
    return [f for f in filas if not es_inclusion(estudiante(f))]
