"""Quién ve y edita cada PIAR, qué asignaturas lleva y cuánto va lleno."""
from django.db.models import Q
from django.utils import timezone

from notas.models import AsignacionDocente, Estudiante, PeriodoAcademico
from notas.permisos import es_admin

from .models import AjustePiar, ConfiguracionPiar, Piar

# Lo que pasa de un año al siguiente al crear el PIAR nuevo: la información
# del estudiante sigue siendo la misma; los ajustes y el acta son de cada año.
CAMPOS_COPIABLES = ('categoria', 'diagnostico', 'fuente_diagnostico', 'apoyos_salud', 'entorno_hogar',
                    'trayectoria', 'descripcion', 'fortalezas', 'barreras', 'apoyos_requeridos',
                    'expectativas_familia', 'expectativas_estudiante')


# ---------------------------------------------------------------------------
# Permisos
# ---------------------------------------------------------------------------
def docente_de(request):
    d = getattr(request.user, 'docente', None)
    return d if d is not None and d.colegio_id == getattr(request.colegio, 'id', None) else None


def coordina(request):
    """Administración y docentes de apoyo: todos los PIAR del colegio."""
    if es_admin(request):
        return True
    d = docente_de(request)
    return bool(d and ConfiguracionPiar.objects.filter(colegio=request.colegio, docentes_apoyo=d).exists())


def es_director(request, est):
    d = docente_de(request)
    return bool(d and est.curso_id and est.curso.director_grado_id == d.id)


def puede_editar_general(request, piar):
    return coordina(request) or es_director(request, piar.estudiante)


def materias_editables(request, piar):
    """Ids de las asignaturas cuyos ajustes puede llenar este usuario."""
    curso = piar.estudiante.curso_id
    if coordina(request):
        return set(AsignacionDocente.objects.filter(curso_id=curso).values_list('materia_id', flat=True))
    d = docente_de(request)
    if not d:
        return set()
    return set(AsignacionDocente.objects.filter(curso_id=curso, docente=d).values_list('materia_id', flat=True))


def puede_ver(request, piar):
    return puede_editar_general(request, piar) or bool(materias_editables(request, piar))


def cursos_del_docente(docente):
    ids = set(AsignacionDocente.objects.filter(docente=docente).values_list('curso_id', flat=True))
    ids |= set(docente.cursos_dirigidos.values_list('id', flat=True))
    return ids


# ---------------------------------------------------------------------------
# Datos
# ---------------------------------------------------------------------------
def periodos(colegio, ano):
    return list(PeriodoAcademico.objects.filter(colegio=colegio, ano_lectivo=ano).order_by('orden'))


def periodo_en_curso(colegio, ano, hoy=None):
    """El periodo de hoy, o el último que ya empezó."""
    hoy = hoy or timezone.localdate()
    empezados = [p for p in periodos(colegio, ano) if p.fecha_inicio <= hoy]
    return empezados[-1] if empezados else None


def asignaturas(curso_id):
    """[(materia, [nombres de docentes])] del curso, en orden alfabético."""
    por_materia = {}
    for a in (AsignacionDocente.objects.filter(curso_id=curso_id)
              .select_related('materia', 'docente__user').order_by('materia__nombre')):
        m = por_materia.setdefault(a.materia_id, (a.materia, []))
        m[1].append(a.docente.user.get_full_name() or a.docente.user.username)
    return list(por_materia.values())


def matriz(piar, editables, hoy=None, solo=None):
    """Filas por asignatura con una celda por periodo, y el avance del año.

    Con `solo` (ids de materias) salen únicamente esas asignaturas: a cada docente le sale
    solo lo que le toca llenar."""
    hoy = hoy or timezone.localdate()
    pers = periodos(piar.colegio, piar.ano_lectivo)
    hechos = {(a.materia_id, a.periodo_id): a for a in piar.ajustes.all()}
    filas, esperado, listos = [], 0, 0
    for materia, docentes in asignaturas(piar.estudiante.curso_id):
        if solo is not None and materia.id not in solo:
            continue
        celdas = []
        for p in pers:
            aj = hechos.get((materia.id, p.id))
            empezado = p.fecha_inicio <= hoy
            if empezado:
                esperado += 1
                listos += bool(aj and aj.completo)
            celdas.append({'periodo': p, 'ajuste': aj, 'empezado': empezado, 'puede': materia.id in editables})
        filas.append({'materia': materia, 'docentes': docentes, 'celdas': celdas,
                      'puede': materia.id in editables})
    return {'periodos': pers, 'filas': filas, 'esperado': esperado, 'listos': listos,
            'porcentaje': round(100 * listos / esperado) if esperado else 0}


def avance(piar, hoy=None):
    m = matriz(piar, set(), hoy)
    return m['listos'], m['esperado'], m['porcentaje']


def estudiantes_visibles(request, ano):
    """Estudiantes que salen en el panel: los de inclusión y los que ya tienen PIAR ese año."""
    qs = (Estudiante.objects.filter(colegio=request.colegio, is_active=True)
          .filter(Q(es_inclusion=True) | Q(piars__ano_lectivo=ano)).distinct()
          .select_related('user', 'curso'))
    if not coordina(request):
        d = docente_de(request)
        qs = qs.filter(curso_id__in=cursos_del_docente(d)) if d else qs.none()
    return qs.order_by('curso__orden', 'user__last_name', 'user__first_name')


def crear(estudiante, ano, usuario=None):
    """El PIAR del año. Si hay uno del año anterior, arranca con su información."""
    piar = Piar.objects.filter(estudiante=estudiante, ano_lectivo=ano).first()
    if piar:
        return piar, False
    anterior = Piar.objects.filter(estudiante=estudiante, ano_lectivo__lt=ano).order_by('-ano_lectivo').first()
    datos = {c: getattr(anterior, c) for c in CAMPOS_COPIABLES} if anterior else {}
    piar = Piar.objects.create(colegio=estudiante.colegio, estudiante=estudiante, ano_lectivo=ano,
                               creado_por=usuario, **datos)
    if not estudiante.es_inclusion:
        estudiante.es_inclusion = True
        estudiante.save(update_fields=['es_inclusion'])
    return piar, bool(anterior)


def avisar_docentes(piar, url):
    """Al crear el PIAR, a cada docente del curso le llega un aviso con SUS asignaturas."""
    from notas.models import Notificacion
    por_docente = {}
    for a in (AsignacionDocente.objects.filter(curso_id=piar.estudiante.curso_id, docente__isnull=False)
              .select_related('materia', 'docente__user').order_by('materia__nombre')):
        por_docente.setdefault(a.docente, []).append(a.materia.nombre)
    nombre = piar.estudiante.user.get_full_name()
    curso = piar.estudiante.curso.nombre if piar.estudiante.curso_id else ''
    avisos = [Notificacion(colegio=piar.colegio, destinatario=d.user, tipo='GENERAL', url=url,
                           mensaje=(f'PIAR de {nombre} ({curso}): le corresponde llenar los ajustes de '
                                    f'{", ".join(mats)}.')[:255])
              for d, mats in por_docente.items() if d.user_id]
    Notificacion.objects.bulk_create(avisos)
    return len(avisos)


def ajuste_anterior(piar, materia, periodo):
    return (AjustePiar.objects.filter(piar=piar, materia=materia, periodo__orden__lt=periodo.orden)
            .order_by('-periodo__orden').first())


def pendientes_docente(request, ano, hoy=None):
    """[(piar, materia, periodo)] que este docente aún no ha llenado en los periodos ya empezados."""
    hoy = hoy or timezone.localdate()
    d = docente_de(request)
    empezados = [p for p in periodos(request.colegio, ano) if p.fecha_inicio <= hoy]
    if not d or not empezados:
        return []
    piars = list(Piar.objects.filter(colegio=request.colegio, ano_lectivo=ano, estudiante__is_active=True)
                 .select_related('estudiante__user', 'estudiante__curso'))
    if not piars:
        return []
    hechos = {(a.piar_id, a.materia_id, a.periodo_id) for a in AjustePiar.objects.filter(piar__in=piars)
              .filter(Q(no_requiere=True) | ~Q(ajustes=''))}
    salida = []
    for asig in AsignacionDocente.objects.filter(docente=d).select_related('materia').order_by('materia__nombre'):
        for piar in piars:
            if piar.estudiante.curso_id != asig.curso_id:
                continue
            for per in empezados:
                if (piar.id, asig.materia_id, per.id) not in hechos:
                    salida.append((piar, asig.materia, per))
    return salida
