# notas/alertas.py
"""Alertas tempranas: quién va perdiendo materias, antes de que sea tarde.

Para cada estudiante y cada materia del curso se calcula:
  * la nota del periodo escogido (la nivelación manda si existe), y
  * la nota acumulada del año hasta ese periodo, con la misma cuenta del
    boletín (notas/boletin/ponderacion.py: definitiva_anual).

Riesgo:
  * alto  -> va perdiendo más materias de las que el colegio permite para ser
             promovido (ConfiguracionSistema.max_areas_reprobadas);
  * medio -> va perdiendo al menos una;
  * sin riesgo en lo demás.

Ojo: la promoción se decide por ÁREAS y aquí se cuentan MATERIAS, que es lo
que el docente y el director de grado pueden atender una por una. En un área
de una sola materia es lo mismo.
"""
from collections import defaultdict
from decimal import Decimal

from .boletin.logic import estudiantes_del_curso_en
from .boletin.ponderacion import calculo_en_lote, definitiva_anual, nota_aprobacion
from .models import AsignacionDocente, Calificacion, ConfiguracionSistema, PeriodoAcademico


def maximo_permitido(colegio):
    config = ConfiguracionSistema.objects.filter(colegio=colegio).first()
    return config.max_areas_reprobadas if config else 2


def periodos_hasta(colegio, ano, periodo=None):
    periodos = list(PeriodoAcademico.objects.filter(colegio=colegio, ano_lectivo=ano).order_by('orden'))
    if periodo is None:
        return periodos
    return [p for p in periodos if p.orden <= periodo.orden]


@calculo_en_lote
def alertas_de_curso(colegio, curso, ano, periodo=None, aprobacion=None, maximo=None):
    """[{estudiante, perdidas: [...], perdidas_periodo: n, riesgo, …}] de un curso."""
    aprobacion = Decimal(aprobacion if aprobacion is not None else nota_aprobacion(colegio))
    maximo = maximo if maximo is not None else maximo_permitido(colegio)
    periodos = periodos_hasta(colegio, ano, periodo)
    if not periodos:
        return []
    actual = periodo or periodos[-1]

    asignaciones = list(AsignacionDocente.objects.filter(colegio=colegio, curso=curso)
                        .select_related('materia', 'docente__user'))
    asignaciones = [a for a in asignaciones if getattr(a.materia, 'promedia_en_boletin', True)]
    materias = {a.materia_id: a for a in asignaciones}
    estudiantes = list(estudiantes_del_curso_en(colegio, curso, ano))
    if not estudiantes or not materias:
        return []

    notas = defaultdict(dict)        # (est, materia) -> {periodo: nota efectiva}
    for c in Calificacion.objects.filter(
            colegio=colegio, estudiante__in=estudiantes, materia_id__in=list(materias),
            periodo__in=periodos, tipo_nota__in=['PROM_PERIODO', 'NIVELACION']):
        clave = (c.estudiante_id, c.materia_id)
        previo = notas[clave].get(c.periodo_id)
        if c.tipo_nota == 'NIVELACION':
            notas[clave][c.periodo_id] = ('niv', Decimal(c.valor_nota))
        elif previo is None or previo[0] != 'niv':
            notas[clave][c.periodo_id] = ('prom', Decimal(c.valor_nota))

    # Cada materia se pierde por debajo del piso de su escala (la especial si tiene una en este grado).
    from . import escalas
    esc = escalas.de(colegio)
    piso = {m: (esc.aprobacion(m, curso.grado) if esc.es_especial(m, curso.grado) else aprobacion)
            for m in materias}

    salida = []
    for est in estudiantes:
        perdidas, perdidas_periodo, con_notas = [], 0, False
        lista_periodo = []
        for materia_id, a in materias.items():
            por_periodo = {pid: v for pid, (_, v) in notas.get((est.id, materia_id), {}).items()}
            if not por_periodo:
                continue
            con_notas = True
            acumulada, _ = definitiva_anual(colegio, por_periodo, periodos, exigir=False)
            del_periodo = por_periodo.get(actual.id)
            aprob_m = piso[materia_id]
            pierde_periodo = del_periodo is not None and del_periodo < aprob_m
            perdidas_periodo += 1 if pierde_periodo else 0
            if pierde_periodo:
                lista_periodo.append({'materia': a.materia.nombre, 'nota': del_periodo,
                                      'docente': a.docente.user.get_full_name() if a.docente_id else ''})
            if acumulada is not None and acumulada < aprob_m:
                perdidas.append({'materia': a.materia.nombre,
                                 'docente': a.docente.user.get_full_name() if a.docente_id else '',
                                 'acumulada': acumulada, 'del_periodo': del_periodo,
                                 'falta': (aprob_m - acumulada).quantize(Decimal('0.1'))})
        perdidas.sort(key=lambda x: x['acumulada'])
        n = len(perdidas)
        riesgo = 'alto' if n > maximo else ('medio' if n > 0 else ('sin_notas' if not con_notas else 'ok'))
        salida.append({'estudiante': est, 'curso': curso, 'perdidas': perdidas, 'n': n,
                       'perdidas_periodo': perdidas_periodo, 'riesgo': riesgo,
                       'perdidas_periodo_lista': sorted(lista_periodo, key=lambda x: x['nota'])})
    return salida


def resumen(filas):
    r = {'alto': 0, 'medio': 0, 'ok': 0, 'sin_notas': 0}
    for f in filas:
        r[f['riesgo']] += 1
    r['total'] = len(filas)
    return r


def alertas_finales(colegio, curso, ano):
    """Las alertas del año completo, con la misma cuenta del boletín final (áreas perdidas, promedio mínimo y
    notas de la comisión): lo que la comisión de evaluación necesita tener claro.

    Riesgo: alto -> el boletín final dice NO PROMOVIDO; medio -> pasa, pero pierde alguna área.
    """
    from .boletin.logic import _umbral, get_datos_boletin_final
    try:
        boletines, _ = get_datos_boletin_final(colegio, curso, ano)
    except Exception:
        return []
    salida = []
    for b in boletines:
        areas = []
        for area in b.get('areas', []):
            if area.get('estado_color_css_class') != 'desempeno-reprobado':
                continue
            materias = []
            for m in area['materias']:
                if not m.get('promedia', True):
                    continue
                actual = m['comision'] if m.get('comision') is not None else (
                    m['definitiva_recuperada'] if m['definitiva_recuperada'] is not None else m['definitiva_original'])
                piso = _umbral(colegio, m['materia_id'], curso.grado)
                if actual is None or actual < piso:
                    materias.append({'materia': m['nombre'], 'acumulada': actual,
                                     'docente': m['docente'].user.get_full_name() if m.get('docente') else '',
                                     'falta': (piso - actual).quantize(Decimal('0.1')) if actual is not None else None})
            areas.append({'area': area['nombre'], 'nota': area.get('nota_final_area'), 'materias': materias})
        con_notas = bool(b.get('areas'))
        n = b.get('areas_reprobadas', 0)
        if not con_notas:
            riesgo = 'sin_notas'
        elif b.get('estado_promocion') != 'PROMOVIDO':
            riesgo = 'alto'
        else:
            riesgo = 'medio' if n else 'ok'
        salida.append({'estudiante': b['estudiante'], 'curso': curso, 'n': n, 'riesgo': riesgo,
                       'areas_perdidas': areas, 'promedio': b.get('promedio_general_final'),
                       'motivo': b.get('motivo_promocion', ''), 'por_comision': b.get('por_comision', False),
                       'perdidas': [], 'perdidas_periodo': None})
    return salida
