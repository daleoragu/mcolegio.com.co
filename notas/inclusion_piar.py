"""Indicadores de inclusión: la planilla de notas y el PIAR dicen lo mismo.

El docente puede escribir los indicadores del estudiante de inclusión en la planilla (botón de inclusión junto al
nombre) o en el PIAR («Objetivos / propósitos de aprendizaje» de su asignatura en el periodo). Lo que guarde en uno
queda en el otro, y el boletín los toma de la planilla.
"""


def lineas(texto):
    """'- uno\\n• dos\\n\\n' -> ['uno', 'dos']"""
    return [l.strip(' •-*\t') for l in (texto or '').split('\n') if l.strip(' •-*\t')]


def _piar_de(colegio, estudiante, ano):
    try:
        from piar.models import Piar
    except Exception:
        return None
    return Piar.objects.filter(colegio=colegio, estudiante=estudiante, ano_lectivo=ano).order_by('-id').first()


def objetivos_del_piar(colegio, estudiante, materia_id, periodo):
    """Los objetivos del PIAR para esa asignatura y periodo, como texto de la planilla (una línea por indicador)."""
    piar = _piar_de(colegio, estudiante, periodo.ano_lectivo)
    if piar is None:
        return ''
    aj = piar.ajustes.filter(materia_id=materia_id, periodo=periodo, no_requiere=False).first()
    return '\n'.join(lineas(aj.objetivos)) if aj else ''


def planilla_a_piar(colegio, estudiante, materia, periodo, texto, docente=None):
    """Lo que el docente escribió en la planilla pasa al PIAR del estudiante (si tiene PIAR ese año)."""
    nuevos = lineas(texto)
    if not nuevos or not getattr(estudiante, 'es_inclusion', False):
        return
    piar = _piar_de(colegio, estudiante, periodo.ano_lectivo)
    if piar is None:
        return
    from piar.models import AjustePiar
    aj, _ = AjustePiar.objects.get_or_create(piar=piar, materia=materia, periodo=periodo,
                                             defaults={'docente': docente})
    if lineas(aj.objetivos) != nuevos:
        aj.objetivos = '\n'.join(nuevos)
        aj.no_requiere = False
        if docente and not aj.docente_id:
            aj.docente = docente
        aj.save()


def piar_a_planilla(ajuste):
    """Lo que el docente escribió en el PIAR pasa a la planilla (a la definitiva del periodo, si ya existe)."""
    from .models import Calificacion
    piar = ajuste.piar
    texto = '' if ajuste.no_requiere else '\n'.join(lineas(ajuste.objetivos))
    if not texto:
        return
    Calificacion.objects.filter(colegio=piar.colegio, estudiante=piar.estudiante, materia=ajuste.materia,
                                periodo=ajuste.periodo, tipo_nota='PROM_PERIODO').update(observacion_inclusion=texto)
