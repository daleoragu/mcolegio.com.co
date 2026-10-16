"""Libro final de calificaciones: por curso, las definitivas de cada área del año.

Es el consolidado anual que el colegio imprime, firma y archiva. Sale por curso
o con todos los cursos del año en un solo PDF, con los folios numerados.
"""
from decimal import Decimal, ROUND_HALF_UP

from notas.boletin.logic import get_datos_boletin_final
from notas.models import Curso, FichaEstudiante, HistorialMatricula, PeriodoAcademico

RESULTADO = {'PROMOVIDO': 'Promovido', 'NO_PROMOVIDO': 'No promovido', 'GRADUADO': 'Graduado',
             'RETIRADO': 'Retirado', 'NO PROMOVIDO': 'No promovido'}


def anos(colegio):
    return list(PeriodoAcademico.objects.filter(colegio=colegio).order_by('-ano_lectivo')
                .values_list('ano_lectivo', flat=True).distinct())


def _nota(v):
    if v is None:
        return ''
    return str(Decimal(v).quantize(Decimal('0.1'), rounding=ROUND_HALF_UP)).replace('.', ',')


def datos_curso(colegio, curso, ano):
    boletines, _ = get_datos_boletin_final(colegio, curso, ano)
    areas = []
    for b in boletines:
        for a in b['areas']:
            if not a.get('es_informativa') and a['nombre'] not in areas:
                areas.append(a['nombre'])
    historial = {h.estudiante_id: h.resultado for h in
                 HistorialMatricula.objects.filter(colegio=colegio, curso=curso, ano_lectivo=ano)}
    documentos = dict(FichaEstudiante.objects.filter(estudiante__in=[b['estudiante'] for b in boletines])
                      .values_list('estudiante_id', 'numero_documento'))
    filas = []
    for b in boletines:
        est = b['estudiante']
        notas = {a['nombre']: a for a in b['areas']}
        celdas = []
        for nombre in areas:
            a = notas.get(nombre)
            nota = a['nota_final_area'] if a else None
            celdas.append({'nota': _nota(nota), 'bajo': bool(a and a.get('desempeno_area') == 'BAJO')})
        if not any(c['nota'] for c in celdas):
            continue                      # sin ninguna nota ese año: no va en el libro
        resultado = RESULTADO.get(historial.get(est.id) or b.get('estado_promocion', ''), '')
        filas.append({'nombre': f'{est.user.last_name} {est.user.first_name}'.strip().upper(),
                      'documento': documentos.get(est.id) or '', 'celdas': celdas,
                      'promedio': _nota(b.get('promedio_general_final')), 'resultado': resultado,
                      'en_historial': est.id in historial})
    return {'curso': curso, 'areas': areas, 'filas': filas,
            'director': curso.director_grado.user.get_full_name() if curso.director_grado_id else ''}


def cursos_del_ano(colegio, ano):
    """Cursos que tuvieron estudiantes ese año (por historial o, si es el año en curso, hoy)."""
    con_historial = set(HistorialMatricula.objects.filter(colegio=colegio, ano_lectivo=ano, curso__isnull=False)
                        .values_list('curso_id', flat=True))
    cursos = Curso.objects.filter(colegio=colegio)
    if con_historial:
        cursos = cursos.filter(id__in=con_historial)
    return list(cursos.order_by('orden', 'grado', 'nombre'))
