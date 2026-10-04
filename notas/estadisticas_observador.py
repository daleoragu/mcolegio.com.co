# notas/estadisticas_observador.py
"""
Conteo de anotaciones para el panel de estadísticas.

Dos cosas distintas que NO se mezclan en el mismo total:

  1. RegistroObservador  -> lo que escribe un docente en el observador.
     Tiene dos ejes: tipo (académica / comportamental) y subtipo
     (positiva / negativa).

     Cuando el docente no marcó el subtipo y la anotación es ACADÉMICA,
     el sistema lo deduce del promedio del estudiante en el periodo en
     que ocurrió el hecho: por debajo de la nota de aprobación cuenta
     como negativa, de ahí para arriba como positiva. Si ese estudiante
     no tiene notas en ese periodo no se deduce nada y queda "sin
     clasificar", porque inventarle una categoría sería peor que dejarla
     en blanco.

     Las de convivencia sin marcar NO se deducen: no hay ninguna nota de
     la cual deducirlas. Quedan "sin clasificar" hasta que alguien las
     corrija.

  2. Observacion con tipo AUTOMATICA -> lo que genera el sistema solo,
     a partir del bajo rendimiento. No son anotaciones de convivencia
     y por eso van en su propio bloque.
"""
from collections import OrderedDict

SIN_CLASIFICAR = 'SIN_CLASIFICAR'

ETIQUETAS_TIPO = OrderedDict([
    ('ACADEMICA', 'Académica'),
    ('COMPORTAMENTAL', 'Convivencia'),
])
ETIQUETAS_SUBTIPO = OrderedDict([
    ('POSITIVA', 'Positiva'),
    ('NEGATIVA', 'Negativa'),
    (SIN_CLASIFICAR, 'Sin clasificar'),
])


def _rango_de_fechas(filtros):
    """Las observaciones se guardan con fecha, no con periodo.

    Para poder filtrar por periodo hay que traducir el periodo a un rango
    de fechas. Devuelve (desde, hasta) o (None, None) si no aplica.
    """
    from notas.models.academicos import PeriodoAcademico

    if filtros.get('periodo_id'):
        p = PeriodoAcademico.objects.filter(id=filtros['periodo_id']).first()
        if p:
            return p.fecha_inicio, p.fecha_fin

    if filtros.get('ano_lectivo'):
        periodos = PeriodoAcademico.objects.filter(
            colegio=filtros.get('colegio'), ano_lectivo=filtros['ano_lectivo'],
        ).order_by('fecha_inicio')
        primero, ultimo = periodos.first(), periodos.last()
        if primero and ultimo:
            return primero.fecha_inicio, ultimo.fecha_fin

    return None, None


def _base_observador(filtros):
    from notas.models.comunicaciones import RegistroObservador

    qs = RegistroObservador.objects.all()
    if filtros.get('colegio'):
        qs = qs.filter(estudiante__curso__colegio=filtros['colegio'])
    if filtros.get('curso_ids'):
        qs = qs.filter(estudiante__curso__id__in=filtros['curso_ids'])

    desde, hasta = _rango_de_fechas(filtros)
    if desde and hasta:
        qs = qs.filter(fecha_suceso__gte=desde, fecha_suceso__lte=hasta)
    return qs


def _deducir_subtipos(registros, colegio):
    """Para las académicas sin marcar, deduce el subtipo a partir del promedio.

    Recibe los registros y devuelve {id_registro: 'POSITIVA'|'NEGATIVA'}.
    Lo hace en bloque (3 consultas en total, no una por registro) porque
    un colegio puede tener miles de anotaciones.
    """
    from notas.models.academicos import PeriodoAcademico, Calificacion
    from notas.boletin.ponderacion import nota_aprobacion
    from django.db.models import Avg

    pendientes = [r for r in registros
                  if not r['subtipo'] and r['tipo'] == 'ACADEMICA' and r['fecha_suceso']]
    if not pendientes:
        return {}

    periodos = list(PeriodoAcademico.objects.filter(colegio=colegio)
                    .values('id', 'fecha_inicio', 'fecha_fin'))

    def periodo_de(fecha):
        for p in periodos:
            if p['fecha_inicio'] <= fecha <= p['fecha_fin']:
                return p['id']
        return None

    # Cada anotación cae en el periodo que contiene su fecha.
    por_registro = {}
    pares = set()
    for r in pendientes:
        pid = periodo_de(r['fecha_suceso'])
        if pid:
            por_registro[r['id']] = (r['estudiante_id'], pid)
            pares.add((r['estudiante_id'], pid))
    if not pares:
        return {}

    promedios = {}
    filas = (Calificacion.objects
             .filter(tipo_nota='PROM_PERIODO',
                     estudiante_id__in={e for e, _ in pares},
                     periodo_id__in={p for _, p in pares})
             .values('estudiante_id', 'periodo_id')
             .annotate(prom=Avg('valor_nota')))
    for f in filas:
        promedios[(f['estudiante_id'], f['periodo_id'])] = f['prom']

    minima = nota_aprobacion(colegio)
    deducidos = {}
    for rid, par in por_registro.items():
        prom = promedios.get(par)
        if prom is None:
            continue           # sin notas: no se inventa, queda sin clasificar
        deducidos[rid] = 'NEGATIVA' if prom < minima else 'POSITIVA'
    return deducidos


def contar_observador(filtros=None):
    """Anotaciones del observador, cruzadas por tipo y por subtipo.

    Devuelve la matriz completa, los totales y el desglose por curso:
    "las observaciones de los grados seleccionados, el tipo de anotación".
    """
    filtros = filtros or {}
    qs = _base_observador(filtros)

    # Se traen los registros uno a uno (no agregados) porque a los que les
    # falta el subtipo hay que deducírselo antes de poder contarlos.
    registros = list(qs.values(
        'id', 'estudiante_id', 'tipo', 'subtipo', 'fecha_suceso',
        'estudiante__curso__id', 'estudiante__curso__nombre',
    ))
    deducidos = _deducir_subtipos(registros, filtros.get('colegio'))

    def clasificar(r):
        tipo = r['tipo'] if r['tipo'] in ETIQUETAS_TIPO else 'ACADEMICA'
        sub = r['subtipo'] or deducidos.get(r['id']) or SIN_CLASIFICAR
        if sub not in ETIQUETAS_SUBTIPO:
            sub = SIN_CLASIFICAR
        return tipo, sub

    matriz = {t: {s: 0 for s in ETIQUETAS_SUBTIPO} for t in ETIQUETAS_TIPO}
    por_curso = {}

    for r in registros:
        tipo, sub = clasificar(r)
        matriz[tipo][sub] += 1

        cid = r['estudiante__curso__id']
        if cid not in por_curso:
            por_curso[cid] = {
                'curso_id': cid,
                'curso': r['estudiante__curso__nombre'] or 'Sin curso',
                'detalle': {t: {s: 0 for s in ETIQUETAS_SUBTIPO} for t in ETIQUETAS_TIPO},
                'total': 0,
            }
        por_curso[cid]['detalle'][tipo][sub] += 1
        por_curso[cid]['total'] += 1

    total = sum(sum(subs.values()) for subs in matriz.values())
    return {
        'matriz': matriz,
        'etiquetas_tipo': ETIQUETAS_TIPO,
        'etiquetas_subtipo': ETIQUETAS_SUBTIPO,
        'por_curso': sorted(por_curso.values(), key=lambda c: c['curso']),
        'total': total,
        'positivas': sum(matriz[t]['POSITIVA'] for t in matriz),
        'negativas': sum(matriz[t]['NEGATIVA'] for t in matriz),
        'sin_clasificar': sum(matriz[t][SIN_CLASIFICAR] for t in matriz),
        'deducidas': len(deducidos),
    }


def contar_automaticas(filtros=None):
    """Observaciones generadas por el sistema. Bloque aparte, sin sumar."""
    from django.db.models import Count
    from notas.models.academicos import Observacion

    filtros = filtros or {}
    qs = Observacion.objects.filter(tipo_observacion='AUTOMATICA')
    if filtros.get('colegio'):
        qs = qs.filter(estudiante__curso__colegio=filtros['colegio'])
    if filtros.get('curso_ids'):
        qs = qs.filter(estudiante__curso__id__in=filtros['curso_ids'])
    if filtros.get('periodo_id'):
        qs = qs.filter(periodo_id=filtros['periodo_id'])
    elif filtros.get('ano_lectivo'):
        qs = qs.filter(periodo__ano_lectivo=filtros['ano_lectivo'])

    por_curso = [
        {'curso': f['estudiante__curso__nombre'] or 'Sin curso', 'total': f['n']}
        for f in qs.values('estudiante__curso__nombre').annotate(n=Count('id')).order_by('-n')
    ]
    return {'total': qs.count(), 'por_curso': por_curso}
