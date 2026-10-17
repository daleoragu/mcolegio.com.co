"""Armar las cuadrículas (día × hora) para mostrar e imprimir."""
from collections import defaultdict

from notas.models import Estudiante

from .models import DIAS, Jornada, Sesion


def _jornadas(colegio):
    return list(Jornada.objects.filter(colegio=colegio).prefetch_related('franjas', 'cursos'))


def _tabla(jornada, celdas):
    """celdas: {(dia, franja_id): [texto…]} -> filas para la plantilla."""
    dias = [(d, n) for d, n in DIAS if d in jornada.dias]
    filas = []
    for f in sorted(jornada.franjas.all(), key=lambda x: (x.orden, x.inicio)):
        filas.append({'franja': f, 'celdas': [celdas.get((d, f.id), []) for d, _ in dias]})
    return {'jornada': jornada, 'dias': dias, 'filas': filas}


def sesiones(horario):
    return (Sesion.objects.filter(horario=horario)
            .select_related('asignacion__materia', 'asignacion__docente__user', 'materia', 'curso', 'franja'))


def de_curso(horario, curso, todas=None):
    todas = todas if todas is not None else list(sesiones(horario).filter(curso=curso))
    j = next((j for j in _jornadas(horario.colegio) if curso in j.cursos.all()), None)
    if j is None:
        return None
    celdas = defaultdict(list)
    for s in todas:
        if s.curso_id == curso.id:
            d = s.docente
            celdas[(s.dia, s.franja_id)].append({'titulo': s.nombre_materia,
                                                 'sub': d.user.get_full_name() if d else 'Sin docente',
                                                 'id': s.asignacion_id, 'sin_docente': d is None})
    return _tabla(j, celdas)


def de_docente(horario, docente, todas=None):
    todas = todas if todas is not None else list(sesiones(horario).filter(asignacion__docente=docente))
    tablas = []
    for j in _jornadas(horario.colegio):
        celdas = defaultdict(list)
        hay = False
        ids = {f.id for f in j.franjas.all()}
        for s in todas:
            if s.asignacion_id and s.asignacion.docente_id == docente.id and s.franja_id in ids:
                celdas[(s.dia, s.franja_id)].append({'titulo': s.curso.nombre, 'sub': s.asignacion.materia.nombre,
                                                     'id': s.asignacion_id})
                hay = True
        if hay:
            tablas.append(_tabla(j, celdas))
    return tablas


def publicado(colegio):
    from .models import Horario
    return Horario.objects.filter(colegio=colegio, estado='PUBLICADO').order_by('-publicado_en').first()


def curso_del_usuario(user, colegio):
    est = Estudiante.objects.filter(user=user, colegio=colegio).select_related('curso').first()
    return est.curso if est else None
