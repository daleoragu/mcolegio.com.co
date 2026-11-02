"""Quién vota qué, cómo se guarda el voto y cómo se cuentan los resultados."""
import random

from django.db import IntegrityError, transaction
from django.db.models import Count, Q

from notas.models import Docente, Estudiante

from .models import Cargo, Eleccion, Papeleta, VotoEmitido


class YaVoto(Exception):
    pass


def votante(user, colegio):
    """('estudiante', Estudiante) / ('docente', Docente) / (None, None)."""
    if user is None or not user.is_authenticated:
        return None, None
    est = Estudiante.objects.filter(user=user, colegio=colegio, is_active=True).select_related('curso').first()
    if est is not None:
        return 'estudiante', est
    doc = Docente.objects.filter(user=user, colegio=colegio).first()
    if doc is not None:
        return 'docente', doc
    return None, None


def cargos_de(eleccion, tipo, persona):
    """[(cargo, [candidatos])] que esta persona vota. Para el vocero, solo los candidatos de su curso."""
    salida = []
    for cargo in eleccion.cargos.prefetch_related('candidatos'):
        candidatos = list(cargo.candidatos.all())
        if tipo == 'docente':
            if cargo.votan != 'docentes':
                continue
        elif tipo == 'estudiante':
            curso = persona.curso
            if cargo.votan == 'docentes':
                continue
            if cargo.votan == 'grados':
                grado = curso.grado if curso else None
                if grado is None or (cargo.grado_desde is not None and grado < cargo.grado_desde) \
                        or (cargo.grado_hasta is not None and grado > cargo.grado_hasta):
                    continue
            if cargo.votan == 'curso':
                candidatos = [c for c in candidatos if curso and c.curso_id == curso.id]
        else:
            continue
        if candidatos or (cargo.voto_blanco and cargo.votan != 'curso'):
            salida.append((cargo, candidatos))
    return salida


def habilitados(eleccion):
    """Cuántas personas pueden votar en esta elección (para el porcentaje de participación)."""
    colegio = eleccion.colegio
    cargos = list(eleccion.cargos.all())
    n = 0
    if any(c.votan != 'docentes' for c in cargos):
        n += Estudiante.objects.filter(colegio=colegio, is_active=True, curso__isnull=False).count()
    if any(c.votan == 'docentes' for c in cargos):
        n += Docente.objects.filter(colegio=colegio, user__is_active=True).count()
    return n


@transaction.atomic
def emitir(eleccion, user, tipo, persona, elecciones, medio='cuenta', jurado=None):
    """elecciones = {cargo_id: candidato_id o 'blanco'}. Guarda el voto de todos los cargos de una vez.
    ValueError si falta un cargo o la opción no vale; YaVoto si la persona ya votó."""
    if eleccion.estado != 'abierta':
        raise ValueError('La votación no está abierta.')
    papeletas = []
    curso = getattr(persona, 'curso', None) if tipo == 'estudiante' else None
    for cargo, candidatos in cargos_de(eleccion, tipo, persona):
        valor = str(elecciones.get(cargo.pk) or elecciones.get(str(cargo.pk)) or '')
        if valor == 'blanco' and cargo.voto_blanco:
            papeletas.append(Papeleta(cargo=cargo, candidato=None, curso=curso))
            continue
        elegido = next((c for c in candidatos if str(c.pk) == valor), None)
        if elegido is None:
            raise ValueError(f'Escoja una opción para «{cargo.nombre}».')
        papeletas.append(Papeleta(cargo=cargo, candidato=elegido, curso=curso))
    if not papeletas:
        raise ValueError('No hay cargos para usted en esta elección.')
    try:
        with transaction.atomic():
            VotoEmitido.objects.create(eleccion=eleccion, usuario=user, curso=curso, medio=medio, jurado=jurado)
    except IntegrityError:
        raise YaVoto()
    random.shuffle(papeletas)               # el orden tampoco dice nada
    Papeleta.objects.bulk_create(papeletas)
    return len(papeletas)


def resultados(eleccion):
    """[{cargo, filas: [{nombre, numero, votos, pct, ganador}], total, blanco, por_curso}] ordenados por votos."""
    salida = []
    for cargo in eleccion.cargos.prefetch_related('candidatos__curso'):
        conteo = dict(Papeleta.objects.filter(cargo=cargo).values_list('candidato').annotate(n=Count('id')))
        blanco = conteo.pop(None, 0)
        bloques = []
        if cargo.votan == 'curso':
            cursos = {}
            for c in cargo.candidatos.all():
                cursos.setdefault(c.curso, []).append(c)
            for curso, candidatos in sorted(cursos.items(), key=lambda x: (x[0].nombre if x[0] else '')):
                bloques.append((curso.nombre if curso else 'Sin curso', candidatos))
        else:
            bloques.append(('', list(cargo.candidatos.all())))
        partes = []
        for titulo, candidatos in bloques:
            filas = [{'c': c, 'votos': conteo.get(c.pk, 0)} for c in candidatos]
            total = sum(f['votos'] for f in filas)
            maximo = max([f['votos'] for f in filas] or [0])
            for f in filas:
                f['pct'] = round(f['votos'] * 100 / total, 1) if total else 0
                f['ganador'] = maximo > 0 and f['votos'] == maximo
            filas.sort(key=lambda f: -f['votos'])
            empate = sum(1 for f in filas if f['ganador']) > 1
            partes.append({'titulo': titulo, 'filas': filas, 'total': total, 'empate': empate})
        total_cargo = sum(conteo.values()) + blanco
        salida.append({'cargo': cargo, 'partes': partes, 'blanco': blanco, 'total': total_cargo,
                       'pct_blanco': round(blanco * 100 / total_cargo, 1) if total_cargo else 0})
    return salida


def participacion_por_curso(eleccion):
    from notas.models import Curso
    votos = dict(VotoEmitido.objects.filter(eleccion=eleccion, curso__isnull=False)
                 .values_list('curso').annotate(n=Count('id')))
    filas = []
    for curso in Curso.objects.filter(colegio=eleccion.colegio).annotate(
            n_est=Count('estudiante', filter=Q(estudiante__is_active=True))
    ).order_by('orden', 'nombre'):
        if not curso.n_est:
            continue
        v = votos.get(curso.pk, 0)
        filas.append({'curso': curso, 'votaron': v, 'habilitados': curso.n_est, 'pct': round(v * 100 / curso.n_est)})
    return filas


def plantilla_basica(eleccion):
    """Personero, contralor y vocero de cada curso: lo que casi todos los colegios eligen."""
    Cargo.objects.bulk_create([
        Cargo(eleccion=eleccion, nombre='Personero(a) estudiantil', votan='estudiantes', orden=1),
        Cargo(eleccion=eleccion, nombre='Contralor(a) estudiantil', votan='estudiantes', orden=2),
        Cargo(eleccion=eleccion, nombre='Vocero(a) del curso (consejo estudiantil)', votan='curso', voto_blanco=True, orden=3),
    ])
