"""Intensidad horaria por grado: cuántas horas tiene cada curso a la semana y si «empata».

Las horas salen de la asignación académica (cuando la materia ya tiene docente) o de
PlanHoras (cuando todavía no lo tiene). «Empatar» es que el total del curso sea igual a
las horas de clase que tiene su jornada, y que los cursos del mismo grado tengan lo mismo.
"""
from collections import OrderedDict, defaultdict

from notas.models import AsignacionDocente, Curso, Materia

from .models import Jornada, PlanHoras


def cupo_por_curso(colegio):
    """{curso_id: horas de clase a la semana de su jornada}."""
    out = {}
    for j in Jornada.objects.filter(colegio=colegio).prefetch_related('franjas', 'cursos'):
        n = sum(1 for f in j.franjas.all() if not f.descanso) * len(j.dias)
        for c in j.cursos.all():
            out[c.id] = n
    return out


def nombre_grado(curso):
    if curso.grado is None:
        return 'Sin grado'
    try:
        return curso.get_grado_display()
    except Exception:
        return f'Grado {curso.grado}'


def tabla(colegio):
    cursos = list(Curso.objects.filter(colegio=colegio).order_by('grado', 'orden', 'nombre'))
    cupo = cupo_por_curso(colegio)
    asig = defaultdict(list)
    for a in AsignacionDocente.objects.filter(colegio=colegio).select_related('materia', 'docente__user'):
        asig[(a.curso_id, a.materia_id)].append(a)
    planes = {(p.curso_id, p.materia_id): p for p in PlanHoras.objects.filter(colegio=colegio)}
    materias = {m.id: m for m in Materia.objects.filter(colegio=colegio)}
    grados = OrderedDict()
    for c in cursos:
        grados.setdefault(c.grado, []).append(c)
    salida = []
    carga = defaultdict(int)
    for lst in asig.values():
        for a in lst:
            carga[a.docente_id] += a.intensidad_horaria_semanal or 0
    for g, cs in grados.items():
        ids = {c.id for c in cs}
        mids = {m for (cid, m) in list(asig) + list(planes) if cid in ids}
        filas = []
        totales = {c.id: 0 for c in cs}
        sin_docente = 0
        for mid in sorted(mids, key=lambda m: materias[m].nombre if m in materias else ''):
            celdas = []
            for c in cs:
                lst = asig.get((c.id, mid), [])
                if lst:
                    horas = sum(a.intensidad_horaria_semanal or 0 for a in lst)
                    celdas.append({'curso': c, 'horas': horas, 'tipo': 'asig', 'editable': len(lst) == 1,
                                   'docente': ', '.join(a.docente.user.get_full_name() or a.docente.user.username
                                                       for a in lst)})
                elif (c.id, mid) in planes:
                    horas = planes[(c.id, mid)].horas
                    celdas.append({'curso': c, 'horas': horas, 'tipo': 'plan', 'editable': True, 'docente': ''})
                    if horas:
                        sin_docente += 1
                else:
                    horas = 0
                    celdas.append({'curso': c, 'horas': 0, 'tipo': 'vacio', 'editable': True, 'docente': ''})
                totales[c.id] += horas
            iguales = len({x['horas'] for x in celdas}) == 1
            filas.append({'materia': materias.get(mid), 'celdas': celdas, 'iguales': iguales})
        resumen = []
        for c in cs:
            n, k = totales[c.id], cupo.get(c.id)
            resumen.append({'curso': c, 'total': n, 'cupo': k, 'dif': (n - k) if k is not None else None})
        salida.append({'grado': g, 'nombre': nombre_grado(cs[0]), 'cursos': cs, 'filas': filas, 'resumen': resumen,
                       'parejos': len({r['total'] for r in resumen}) <= 1,
                       'empata': all(r['dif'] == 0 for r in resumen),
                       'sin_docente': sin_docente})
    return salida, dict(carga)


def guardar(colegio, post):
    """Guarda las horas escritas (h_<curso>_<materia>). Devuelve cuántas cambiaron."""
    asig = defaultdict(list)
    for a in AsignacionDocente.objects.filter(colegio=colegio):
        asig[(a.curso_id, a.materia_id)].append(a)
    cursos = set(Curso.objects.filter(colegio=colegio).values_list('id', flat=True))
    materias = set(Materia.objects.filter(colegio=colegio).values_list('id', flat=True))
    n = 0
    for k, v in post.items():
        if not k.startswith('h_'):
            continue
        try:
            _, cid, mid = k.split('_')
            cid, mid, horas = int(cid), int(mid), max(0, min(40, int(v or 0)))
        except ValueError:
            continue
        if cid not in cursos or mid not in materias:
            continue
        lst = asig.get((cid, mid), [])
        if len(lst) == 1:
            if lst[0].intensidad_horaria_semanal != horas:
                lst[0].intensidad_horaria_semanal = horas
                lst[0].save(update_fields=['intensidad_horaria_semanal'])
                n += 1
        elif not lst:
            plan = PlanHoras.objects.filter(curso_id=cid, materia_id=mid).first()
            if horas == 0:
                if plan:
                    plan.delete()
                    n += 1
            elif plan is None or plan.horas != horas:
                PlanHoras.objects.update_or_create(curso_id=cid, materia_id=mid,
                                                   defaults={'colegio': colegio, 'horas': horas})
                n += 1
    return n


def agregar_materia(colegio, grado, materia_id, horas):
    """Pone la materia en todos los cursos del grado que no la tengan (sin docente)."""
    m = Materia.objects.filter(colegio=colegio, pk=materia_id).first()
    if not m:
        return 0
    n = 0
    for c in Curso.objects.filter(colegio=colegio, grado=grado):
        if AsignacionDocente.objects.filter(curso=c, materia=m).exists():
            continue
        PlanHoras.objects.update_or_create(curso=c, materia=m, defaults={'colegio': colegio, 'horas': max(0, horas)})
        n += 1
    return n
