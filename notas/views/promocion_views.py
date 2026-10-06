# notas/views/promocion_views.py
"""Promoción de fin de año: pasar a cada estudiante al curso que le toca.

Cómo decide, curso por curso:
  * Curso con grado: los promovidos pasan al curso del grado siguiente con el
    mismo subgrupo (601 -> 701), o al único curso de ese grado si hay uno solo.
    Si no se puede saber, se pregunta. Undécimo se gradúa.
  * Curso sin grado (los que se crearon antes, como «PRIMERO» o «SEGUNDO»): se
    pregunta a qué curso pasan. No se adivina por el nombre.
  * Los no promovidos se quedan en el mismo curso.

Quién pasa y quién no lo sugiere el boletín final (la regla de «máximo de
áreas reprobadas» del colegio), pero el administrador decide estudiante por
estudiante: la comisión de evaluación puede haber decidido otra cosa.

Antes de mover a nadie se escribe el historial del año. Con eso el boletín de
ese año sigue saliendo con quienes de verdad estuvieron en cada curso, y la
promoción se puede deshacer.
"""
from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.db import transaction
from django.http import HttpResponseNotFound
from django.shortcuts import redirect, render
from django.urls import reverse

from ..models import Curso, Estudiante, HistorialMatricula, PeriodoAcademico
from ..models.perfiles import NOMBRE_GRADO

GRADUAR = 'GRADUAR'
ELEGIBLES = ('PROMOVIDO', 'NO_PROMOVIDO', 'RETIRADO')


def es_personal_admin(user):
    return user.is_superuser


# ---------------------------------------------------------------------------
# Lógica pura: qué le pasa a un estudiante. Sin base de datos, para probarla.
# ---------------------------------------------------------------------------

def resolver(resultado, curso_origen, destino):
    """(resultado_final, curso_donde_queda, sigue_activo).

    destino: el curso al que pasan los promovidos de su curso, o GRADUAR.
    """
    if resultado == 'RETIRADO':
        return 'RETIRADO', curso_origen, False
    if resultado == 'NO_PROMOVIDO':
        return 'NO_PROMOVIDO', curso_origen, True
    if destino == GRADUAR:
        # El graduado conserva su curso y queda inactivo: no aparece en las
        # listas del año nuevo, pero sus boletines siguen ahí.
        return 'GRADUADO', curso_origen, False
    return 'PROMOVIDO', destino, True


def _orden_curso(c):
    return (c.grado is None, c.grado if c.grado is not None else 0, c.orden, c.nombre)


def _anos(colegio):
    anos = sorted(set(PeriodoAcademico.objects.filter(colegio=colegio)
                      .values_list('ano_lectivo', flat=True)), reverse=True)
    return anos


def _sugerencias(colegio, curso, ano):
    """{estudiante_id: {...}} con lo que dice el boletín final de ese año."""
    from ..boletin.logic import get_datos_boletin_final
    try:
        boletines, _ = get_datos_boletin_final(colegio, curso, ano)
    except Exception:
        # Si el boletín no se puede calcular (curso sin materias, por
        # ejemplo), no se sugiere nada y todos arrancan como promovidos.
        return {}
    salida = {}
    for b in boletines:
        sin_notas = not b.get('areas')
        salida[b['estudiante'].id] = {
            'resultado': 'PROMOVIDO' if (sin_notas or b.get('estado_promocion') == 'PROMOVIDO')
                         else 'NO_PROMOVIDO',
            'areas_reprobadas': b.get('areas_reprobadas', 0),
            'sin_notas': sin_notas,
        }
    return salida


def _destino_desde_post(valor, cursos_por_id):
    if valor == GRADUAR:
        return GRADUAR
    if valor and valor.isdigit():
        return cursos_por_id.get(int(valor))
    return None


@user_passes_test(es_personal_admin)
def promocion_anual(request):
    colegio = request.colegio
    if not colegio:
        return HttpResponseNotFound('<h1>Colegio no configurado</h1>')

    anos = _anos(colegio)
    try:
        ano = int(request.POST.get('ano') or request.GET.get('ano') or (anos[0] if anos else 0))
    except ValueError:
        ano = anos[0] if anos else 0
    if not ano:
        messages.error(request, 'El colegio no tiene periodos académicos: no hay año que promover.')
        return redirect('notas:gestion_cursos')

    url_ano = reverse('notas:promocion_anual') + f'?ano={ano}'
    historial = HistorialMatricula.objects.filter(colegio=colegio, ano_lectivo=ano)
    accion = request.POST.get('accion') if request.method == 'POST' else None

    if accion == 'deshacer':
        return _deshacer(request, colegio, ano, url_ano)
    if historial.exists():
        return _resumen(request, colegio, ano, anos, historial)

    cursos = sorted(Curso.objects.filter(colegio=colegio), key=_orden_curso)
    cursos_por_id = {c.id: c for c in cursos}
    estudiantes = list(Estudiante.objects.filter(colegio=colegio, is_active=True, curso__isnull=False)
                       .select_related('user')
                       .order_by('user__last_name', 'user__first_name'))
    por_curso = {}
    for e in estudiantes:
        por_curso.setdefault(e.curso_id, []).append(e)

    errores = []
    filas = []
    for c in cursos:
        suyos = por_curso.get(c.id, [])
        if not suyos:
            continue
        if accion == 'promover':
            destino = _destino_desde_post(request.POST.get(f'destino_{c.id}'), cursos_por_id)
            sugerencias = {}
        else:
            destino = GRADUAR if c.es_ultimo_grado else c.curso_siguiente_sugerido()
            sugerencias = _sugerencias(colegio, c, ano)
        filas.append({
            'curso': c, 'destino': destino,
            'destino_valor': (GRADUAR if destino == GRADUAR else (destino.id if destino else '')),
            'destino_auto': destino is not None and accion != 'promover',
            'estudiantes': [{
                'e': e,
                'sugerencia': sugerencias.get(e.id),
                'resultado': (request.POST.get(f'resultado_{e.id}') if accion == 'promover'
                              else (sugerencias.get(e.id) or {}).get('resultado', 'PROMOVIDO')),
            } for e in suyos],
        })

    if accion == 'promover':
        for f in filas:
            hay_promovidos = any(x['resultado'] == 'PROMOVIDO' for x in f['estudiantes'])
            if hay_promovidos and f['destino'] is None:
                errores.append(f'Falta decir a qué curso pasan los promovidos de {f["curso"].nombre}.')
            if f['destino'] not in (None, GRADUAR) and f['destino'].id == f['curso'].id and hay_promovidos:
                errores.append(f'Los promovidos de {f["curso"].nombre} no pueden quedarse en el mismo curso: '
                               f'márquelos como «No promovido» o escoja otro curso.')
        if not errores:
            return _aplicar(request, colegio, ano, filas, url_ano)
        for e in errores:
            messages.error(request, e)

    return render(request, 'notas/admin_crud/promocion_anual.html', {
        'titulo': f'Promoción de fin de año {ano}',
        'colegio': colegio, 'ano': ano, 'anos': anos, 'filas': filas,
        'cursos': cursos, 'GRADUAR': GRADUAR,
        'sin_grado': [f['curso'] for f in filas if f['curso'].grado is None],
        'total_estudiantes': sum(len(f['estudiantes']) for f in filas),
        'modo': 'planear',
    })


def _aplicar(request, colegio, ano, filas, url_ano):
    """Escribe el historial y mueve a los estudiantes, todo o nada."""
    conteo = {'PROMOVIDO': 0, 'NO_PROMOVIDO': 0, 'GRADUADO': 0, 'RETIRADO': 0}
    registros, cambiados = [], []
    for f in filas:
        curso = f['curso']
        for x in f['estudiantes']:
            resultado = x['resultado']
            if resultado not in ELEGIBLES:
                # Estudiante que apareció después de abrir la pantalla: no se
                # toca, para no moverlo sin que nadie lo haya visto.
                continue
            e = x['e']
            final, queda_en, activo = resolver(resultado, curso, f['destino'])
            registros.append(HistorialMatricula(
                colegio=colegio, estudiante=e, ano_lectivo=ano,
                curso=curso, curso_nombre=curso.nombre, grado=curso.grado,
                resultado=final,
                curso_destino=queda_en if final == 'PROMOVIDO' else None,
                estaba_activo=e.is_active, registrado_por=request.user))
            e.curso = queda_en
            e.is_active = activo
            cambiados.append(e)
            conteo[final] += 1

    with transaction.atomic():
        # Primero el historial: si algo falla después, no queda nadie movido
        # sin rastro de dónde estaba.
        HistorialMatricula.objects.bulk_create(registros)
        Estudiante.objects.bulk_update(cambiados, ['curso', 'is_active'])

    messages.success(
        request,
        f'Promoción {ano} hecha: {conteo["PROMOVIDO"]} promovido(s), '
        f'{conteo["NO_PROMOVIDO"]} no promovido(s), {conteo["GRADUADO"]} graduado(s), '
        f'{conteo["RETIRADO"]} retirado(s). Los boletines de {ano} siguen saliendo con '
        f'los cursos de ese año.')
    return redirect(url_ano)


def _resumen(request, colegio, ano, anos, historial):
    """Lo que ya se hizo ese año, curso por curso, con la opción de deshacer."""
    filas = {}
    for h in historial.select_related('curso_destino', 'estudiante__user').order_by('curso_nombre'):
        f = filas.setdefault(h.curso_nombre or '(curso borrado)', {
            'curso': h.curso_nombre, 'grado': NOMBRE_GRADO.get(h.grado, '') if h.grado is not None else '',
            'PROMOVIDO': 0, 'NO_PROMOVIDO': 0, 'GRADUADO': 0, 'RETIRADO': 0,
            'destinos': set(), 'no_promovidos': []})
        f[h.resultado] += 1
        if h.curso_destino:
            f['destinos'].add(h.curso_destino.nombre)
        if h.resultado == 'NO_PROMOVIDO':
            f['no_promovidos'].append(str(h.estudiante))
    for f in filas.values():
        f['destinos'] = ', '.join(sorted(f['destinos']))
    posterior = HistorialMatricula.objects.filter(colegio=colegio, ano_lectivo__gt=ano).exists()
    return render(request, 'notas/admin_crud/promocion_anual.html', {
        'titulo': f'Promoción de fin de año {ano}',
        'colegio': colegio, 'ano': ano, 'anos': anos,
        'resumen': list(filas.values()), 'modo': 'hecha',
        'puede_deshacer': not posterior,
        'fecha': historial.order_by('registrado').first().registrado,
    })


def _deshacer(request, colegio, ano, url_ano):
    """Devuelve a cada estudiante al curso y estado que tenía antes."""
    historial = list(HistorialMatricula.objects.filter(colegio=colegio, ano_lectivo=ano)
                     .select_related('estudiante'))
    if not historial:
        messages.info(request, f'La promoción {ano} no se ha hecho; no hay nada que deshacer.')
        return redirect(url_ano)
    if HistorialMatricula.objects.filter(colegio=colegio, ano_lectivo__gt=ano).exists():
        messages.error(request, f'Ya se hizo la promoción de un año posterior a {ano}. '
                                f'Deshaga primero esa.')
        return redirect(url_ano)

    estudiantes = []
    for h in historial:
        e = h.estudiante
        if h.curso_id:
            e.curso_id = h.curso_id
        e.is_active = h.estaba_activo
        estudiantes.append(e)
    with transaction.atomic():
        Estudiante.objects.bulk_update(estudiantes, ['curso', 'is_active'])
        HistorialMatricula.objects.filter(colegio=colegio, ano_lectivo=ano).delete()
    messages.success(request, f'Se deshizo la promoción {ano}: {len(estudiantes)} estudiante(s) '
                              f'volvieron al curso donde estaban.')
    return redirect(url_ano)
