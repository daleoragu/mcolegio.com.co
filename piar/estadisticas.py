"""Estadísticas de los estudiantes de inclusión de un año.

Responde lo que pregunta la orientación y la rectoría:
* ¿Cuántos son, en qué cursos y por qué categoría?
* ¿Cuántos tienen el PIAR vigente, en elaboración o todavía no?
* ¿Los docentes llenaron los ajustes razonables? ¿Qué asignaturas y quiénes faltan?
* ¿Cómo les va? Su promedio por periodo frente al resto de sus cursos, y las
  asignaturas donde más tienen desempeño bajo.
"""
from collections import Counter, defaultdict
from decimal import Decimal

from django.db.models import Q
from django.utils import timezone

from notas.models import AsignacionDocente, Calificacion, EscalaValoracion, Estudiante

from . import logica
from .models import CATEGORIAS, Piar


def _media(valores):
    valores = [v for v in valores if v is not None]
    return round(float(sum(valores) / len(valores)), 2) if valores else None


def _tope_bajo(colegio):
    """Nota máxima del desempeño más bajo de la escala (por defecto 2.9)."""
    e = EscalaValoracion.objects.filter(colegio=colegio).order_by('valor_minimo').first()
    return e.valor_maximo if e else Decimal('2.9')


def calcular(colegio, ano, hoy=None):
    hoy = hoy or timezone.localdate()
    inclusion = list(Estudiante.objects.filter(colegio=colegio, is_active=True)
                     .filter(Q(es_inclusion=True) | Q(piars__ano_lectivo=ano)).distinct()
                     .select_related('user', 'curso').order_by('curso__orden', 'user__last_name'))
    total_colegio = Estudiante.objects.filter(colegio=colegio, is_active=True, curso__isnull=False).count()
    piars = {p.estudiante_id: p for p in Piar.objects.filter(colegio=colegio, ano_lectivo=ano)
             .prefetch_related('ajustes')}

    # --- Quiénes y cómo va su PIAR
    estados = Counter()
    categorias = Counter()
    por_curso = defaultdict(lambda: {'total': 0, 'vigente': 0, 'borrador': 0, 'sin': 0})
    for e in inclusion:
        p = piars.get(e.id)
        clave = 'sin' if p is None else ('vigente' if p.estado == 'VIGENTE' else 'borrador')
        estados[clave] += 1
        categorias[(p.categoria if p and p.categoria else '')] += 1
        fila = por_curso[e.curso.nombre if e.curso_id else 'Sin curso']
        fila['total'] += 1
        fila[clave] += 1
    nombres_cat = dict(CATEGORIAS)
    categorias = sorted(((nombres_cat.get(k, 'Sin categoría registrada'), n) for k, n in categorias.items()),
                        key=lambda x: -x[1])

    # --- Ajustes razonables: lo que debía estar lleno a hoy
    por_materia = defaultdict(lambda: {'listos': 0, 'no_requiere': 0, 'faltan': 0})
    por_docente = defaultdict(int)
    esperado = listos = 0
    pers = logica.periodos(colegio, ano)
    empezados = [p for p in pers if p.fecha_inicio <= hoy]
    asignaciones = defaultdict(list)
    for a in (AsignacionDocente.objects.filter(curso_id__in={e.curso_id for e in inclusion if e.curso_id})
              .select_related('materia', 'docente__user')):
        asignaciones[a.curso_id].append(a)
    for e in inclusion:
        p = piars.get(e.id)
        if p is None:
            continue
        hechos = {(a.materia_id, a.periodo_id): a for a in p.ajustes.all()}
        vistos = set()
        for a in asignaciones.get(e.curso_id, ()):
            if a.materia_id in vistos:
                continue
            vistos.add(a.materia_id)
            for per in empezados:
                esperado += 1
                aj = hechos.get((a.materia_id, per.id))
                m = por_materia[a.materia.nombre]
                if aj and aj.completo:
                    listos += 1
                    m['no_requiere' if aj.no_requiere else 'listos'] += 1
                else:
                    m['faltan'] += 1
                    por_docente[a.docente.user.get_full_name() or a.docente.user.username] += 1
    por_materia = sorted(por_materia.items(), key=lambda x: (-x[1]['faltan'], x[0]))
    por_docente = sorted(por_docente.items(), key=lambda x: (-x[1], x[0]))

    # --- Rendimiento: promedio por periodo frente a los compañeros de sus mismos cursos
    ids_inclusion = {e.id for e in inclusion}
    cursos = {e.curso_id for e in inclusion if e.curso_id}
    notas = (Calificacion.objects.filter(colegio=colegio, tipo_nota='PROM_PERIODO', periodo__in=pers,
                                         estudiante__curso_id__in=cursos, estudiante__is_active=True)
             .values_list('estudiante_id', 'periodo_id', 'materia__nombre', 'valor_nota'))
    por_estudiante = defaultdict(list)              # (estudiante, periodo) -> notas
    bajas = Counter()
    notas_materia_inclusion = Counter()
    tope = _tope_bajo(colegio)
    for est_id, per_id, materia, valor in notas:
        por_estudiante[(est_id, per_id)].append(valor)
        if est_id in ids_inclusion:
            notas_materia_inclusion[materia] += 1
            if valor <= tope:
                bajas[materia] += 1
    rendimiento = []
    for per in pers:
        inc = [_media(v) for (e, p), v in por_estudiante.items() if p == per.id and e in ids_inclusion]
        resto = [_media(v) for (e, p), v in por_estudiante.items() if p == per.id and e not in ids_inclusion]
        if inc or resto:
            rendimiento.append({'periodo': per.get_nombre_display(), 'inclusion': _media(inc), 'resto': _media(resto),
                                'n_inclusion': len(inc)})
    dificultad = [{'materia': m, 'bajas': n, 'total': notas_materia_inclusion[m],
                   'porcentaje': round(100 * n / notas_materia_inclusion[m]) if notas_materia_inclusion[m] else 0}
                  for m, n in bajas.most_common(8)]
    maximo = max([r['inclusion'] or 0 for r in rendimiento] + [r['resto'] or 0 for r in rendimiento] + [0])

    return {
        'total': len(inclusion), 'total_colegio': total_colegio,
        'porcentaje': round(100 * len(inclusion) / total_colegio, 1) if total_colegio else 0,
        'estados': {'vigente': estados['vigente'], 'borrador': estados['borrador'], 'sin': estados['sin']},
        'categorias': categorias, 'por_curso': sorted(por_curso.items()),
        'ajustes': {'esperado': esperado, 'listos': listos,
                    'porcentaje': round(100 * listos / esperado) if esperado else 0},
        'por_materia': por_materia, 'por_docente': por_docente[:15],
        'rendimiento': rendimiento, 'maximo_nota': maximo or 5, 'dificultad': dificultad, 'tope_bajo': tope,
    }
