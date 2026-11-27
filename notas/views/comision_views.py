# notas/views/comision_views.py
"""Comisión de evaluación y promoción: ajustar las notas de un estudiante que la comisión decide promover.

Para cada asignatura perdida en el año se muestra la nota mínima para aprobarla y dos caminos:
  * Nota de la comisión: la definitiva del año que decide la comisión (el boletín final conserva la original
    y muestra «2,8 (3,0 Comisión)»).
  * Nivelación por periodos: se abren los periodos de la asignatura y se escriben nivelaciones; la pantalla
    va contando cuánto falta para que la definitiva del año llegue a la mínima.
Así el boletín final queda de acuerdo con la decisión de promoverlo.

Quién ajusta: el administrador, todo. Un docente, solo la asignatura que dicta y con permiso: lo pide desde las
alertas tempranas («Final del año»), al administrador le llega la notificación y lo aprueba o lo rechaza.
"""
from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db import transaction
from django.http import HttpResponseForbidden, HttpResponseNotFound
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from .. import escalas
from ..boletin.logic import _umbral, get_datos_boletin_final
from ..boletin.ponderacion import ajustes, pesos
from ..models import (AdministradorColegio, AsignacionDocente, Calificacion, Docente, Estudiante, HistorialMatricula,
                      NotaComision, Notificacion, PeriodoAcademico, PermisoComision)
from ..permisos import es_admin, es_admin_usuario
from ..utils.notificaciones import crear_notificaciones_multiples


def _nota(texto):
    texto = (texto or '').strip().replace(',', '.')
    if not texto:
        return None
    try:
        return Decimal(texto)
    except InvalidOperation:
        return 'mal'


def _curso_del_ano(colegio, estudiante, ano):
    h = HistorialMatricula.objects.filter(colegio=colegio, estudiante=estudiante, ano_lectivo=ano,
                                          curso__isnull=False).select_related('curso').first()
    return h.curso if h else estudiante.curso


def _maximo(colegio, materia_id, grado):
    niveles = escalas.de(colegio).niveles(materia_id, grado)
    topes = [n.valor_maximo for n in niveles if n.valor_maximo is not None]
    return max(topes) if topes else Decimal('5.0')


def _asignaturas(colegio, estudiante, curso, ano, periodos, boletin, solo=None):
    """Las asignaturas perdidas (y las que ya tienen nota de comisión), con sus periodos.

    solo: ids de materias a las que se limita (el docente con permiso)."""
    tabla = pesos(colegio, periodos)
    cals = {}
    for c in Calificacion.objects.filter(colegio=colegio, estudiante=estudiante, periodo__in=periodos,
                                         tipo_nota__in=['PROM_PERIODO', 'NIVELACION']):
        cals[(c.materia_id, c.periodo_id, c.tipo_nota)] = c.valor_nota
    salida = []
    for area in boletin['areas']:
        for m in area['materias']:
            if not m.get('promedia', True) or (solo is not None and m['materia_id'] not in solo):
                continue
            umbral = _umbral(colegio, m['materia_id'], curso.grado)
            actual = m['comision'] if m['comision'] is not None else (
                m['definitiva_recuperada'] if m['definitiva_recuperada'] is not None else m['definitiva_original'])
            pierde = actual is None or actual < umbral
            if not pierde and m['comision'] is None and not (m['definitiva_recuperada'] is not None
                                                              and m['definitiva_original'] is not None
                                                              and m['definitiva_original'] < umbral):
                continue
            salida.append({
                'id': m['materia_id'], 'nombre': m['nombre'], 'area': area['nombre'],
                'area_pierde': area.get('estado_color_css_class') == 'desempeno-reprobado',
                'nota_area': area.get('nota_final_area'),
                'original': m['definitiva_original'], 'actual': actual, 'pierde': pierde,
                'comision': m['comision'], 'umbral': umbral, 'maximo': _maximo(colegio, m['materia_id'], curso.grado),
                'periodos': [{
                    'id': p.id, 'nombre': p.get_nombre_display(),
                    'prom': cals.get((m['materia_id'], p.id, 'PROM_PERIODO')),
                    'niv': cals.get((m['materia_id'], p.id, 'NIVELACION')),
                    'peso': float(tabla.get(p.id, 0)),
                } for p in periodos],
            })
    return salida


def _ano(request):
    try:
        return int(request.POST.get('ano') or request.GET.get('ano') or 0)
    except ValueError:
        return 0


def permitidas(request, estudiante, ano):
    """None si es administrador (todo); si no, los ids de materias con permiso aprobado para este docente."""
    if es_admin(request):
        return None
    docente = Docente.objects.filter(user=request.user, colegio=request.colegio).first()
    if docente is None:
        return set()
    return set(PermisoComision.objects.filter(colegio=request.colegio, estudiante=estudiante, ano_lectivo=ano,
                                              docente=docente, estado='APROBADO').values_list('materia_id', flat=True))


def _url_alertas(ano):
    return reverse('notas:alertas_tempranas') + f'?ano={ano}&periodo=final'


@login_required
def comision_estudiante(request, estudiante_id):
    colegio = request.colegio
    if not colegio:
        return HttpResponseNotFound('<h1>Colegio no configurado</h1>')
    estudiante = get_object_or_404(Estudiante.objects.select_related('user', 'curso'), pk=estudiante_id,
                                   colegio=colegio)
    ano = _ano(request)
    solo = permitidas(request, estudiante, ano)
    if solo is not None and not solo:
        return HttpResponseForbidden('Para ajustar notas en la comisión necesita el permiso del administrador. '
                                     'Pídalo desde Alertas tempranas → Final del año.')
    periodos = list(PeriodoAcademico.objects.filter(colegio=colegio, ano_lectivo=ano).order_by('orden'))
    curso = _curso_del_ano(colegio, estudiante, ano)
    if not periodos or not curso:
        messages.error(request, 'No hay periodos de ese año o el estudiante no tiene curso.')
        return redirect('notas:promocion_anual')
    url = reverse('notas:comision_estudiante', args=[estudiante.id]) + f'?ano={ano}'

    if request.method == 'POST':
        _guardar(request, colegio, estudiante, curso, ano, periodos, solo)
        return redirect(url)

    boletin = get_datos_boletin_final(colegio, curso, ano, estudiante)[0][0]
    es_docente = solo is not None
    return render(request, 'notas/admin_crud/comision_estudiante.html', {
        'titulo': 'Comisión de evaluación y promoción',
        'estudiante': estudiante, 'curso': curso, 'ano': ano, 'boletin': boletin,
        'asignaturas': _asignaturas(colegio, estudiante, curso, ano, periodos, boletin, solo),
        'es_docente': es_docente,
        'pide_todos': ajustes(colegio).pide_todos_los_periodos,
        'acta': NotaComision.objects.filter(colegio=colegio, estudiante=estudiante, ano_lectivo=ano)
                .exclude(acta='').values_list('acta', flat=True).first() or '',
        'volver': _url_alertas(ano) if es_docente else reverse('notas:promocion_anual') + f'?ano={ano}',
        'texto_volver': 'Volver a las alertas' if es_docente else 'Volver a la promoción',
    })


def _guardar(request, colegio, estudiante, curso, ano, periodos, solo=None):
    acta = (request.POST.get('acta') or '').strip()[:120]
    asignaciones = {a.materia_id: a for a in AsignacionDocente.objects.filter(colegio=colegio, curso=curso)
                    .select_related('materia', 'docente')}
    errores, cambios = [], 0
    with transaction.atomic():
        for mid_txt in request.POST.getlist('materia'):
            if not mid_txt.isdigit() or int(mid_txt) not in asignaciones:
                continue
            if solo is not None and int(mid_txt) not in solo:
                continue                  # el docente solo ajusta lo que tiene permitido
            asig = asignaciones[int(mid_txt)]
            docente_nota = asig.docente
            if solo is not None:
                docente_nota = Docente.objects.filter(user=request.user, colegio=colegio).first() or asig.docente
            materia = asig.materia
            umbral, maximo = _umbral(colegio, materia.id, curso.grado), _maximo(colegio, materia.id, curso.grado)
            modo = request.POST.get(f'modo_{materia.id}')
            if modo == 'comision':
                valor = _nota(request.POST.get(f'comision_{materia.id}'))
                if valor is None:
                    cambios += NotaComision.objects.filter(colegio=colegio, estudiante=estudiante, materia=materia,
                                                           ano_lectivo=ano).delete()[0]
                elif valor == 'mal' or not (umbral <= valor <= maximo):
                    errores.append(f'{materia.nombre}: la nota de la comisión debe estar entre '
                                   f'{umbral} y {maximo}.')
                else:
                    NotaComision.objects.update_or_create(
                        colegio=colegio, estudiante=estudiante, materia=materia, ano_lectivo=ano,
                        defaults={'valor_nota': valor, 'acta': acta, 'registrado_por': request.user})
                    cambios += 1
            elif modo == 'nivelacion':
                # Por periodos: la nota de comisión (si la había) deja de mandar.
                cambios += NotaComision.objects.filter(colegio=colegio, estudiante=estudiante, materia=materia,
                                                       ano_lectivo=ano).delete()[0]
                for p in periodos:
                    campo = f'niv_{materia.id}_{p.id}'
                    if campo not in request.POST:
                        continue
                    valor = _nota(request.POST.get(campo))
                    base = dict(colegio=colegio, estudiante=estudiante, materia=materia, periodo=p)
                    if valor is None:
                        borradas = Calificacion.objects.filter(tipo_nota='NIVELACION', **base).delete()[0]
                        if borradas:
                            Calificacion.objects.filter(tipo_nota='PROM_PERIODO', **base).update(es_recuperada=False)
                            cambios += borradas
                        continue
                    if valor == 'mal' or not (Decimal('0') < valor <= maximo):
                        errores.append(f'{materia.nombre}, {p.get_nombre_display()}: nivelación fuera de la escala.')
                        continue
                    Calificacion.objects.update_or_create(tipo_nota='NIVELACION', **base,
                                                          defaults={'valor_nota': valor, 'docente': docente_nota})
                    Calificacion.objects.filter(tipo_nota='PROM_PERIODO', **base).update(es_recuperada=valor >= umbral)
                    cambios += 1
    for e in errores:
        messages.error(request, e)
    boletin = get_datos_boletin_final(colegio, curso, ano, estudiante)[0][0]
    estado = boletin['estado_promocion']
    if estado == 'PROMOVIDO':
        messages.success(request, f'Notas guardadas. Con estas notas el boletín final dice: PROMOVIDO'
                                  f'{" POR DECISIÓN DE LA COMISIÓN" if boletin.get("por_comision") else ""}.')
    elif cambios or not errores:
        messages.warning(request, f'Notas guardadas, pero el boletín final aún dice NO PROMOVIDO. '
                                  f'{boletin.get("motivo_promocion", "")}')


# ---------------------------------------------------------------------------------------- permisos del docente
def administradores(colegio):
    usuarios = {a.user for a in AdministradorColegio.objects.filter(colegio=colegio, activo=True).select_related('user')}
    if colegio.admin_general_id:
        usuarios.add(colegio.admin_general)
    return [u for u in usuarios if u.is_active]


@login_required
@require_POST
def pedir_permiso_comision(request):
    """El docente pide permiso para ajustar la nota de su asignatura a un estudiante."""
    colegio = request.colegio
    docente = Docente.objects.filter(user=request.user, colegio=colegio).first() if colegio else None
    ano = _ano(request)
    volver = _url_alertas(ano) + (f"&curso={request.POST.get('curso')}" if (request.POST.get('curso') or '').isdigit() else '')
    if docente is None:
        return HttpResponseForbidden('Solo los docentes piden este permiso.')
    estudiante = get_object_or_404(Estudiante, pk=request.POST.get('estudiante') or 0, colegio=colegio)
    curso = _curso_del_ano(colegio, estudiante, ano)
    asig = AsignacionDocente.objects.filter(colegio=colegio, curso=curso, docente=docente,
                                            materia_id=request.POST.get('materia') or 0).select_related('materia').first()
    if asig is None:
        messages.error(request, 'Solo puede pedir permiso para las asignaturas que usted dicta en ese curso.')
        return redirect(volver)
    vigente = PermisoComision.objects.filter(colegio=colegio, estudiante=estudiante, materia=asig.materia,
                                             ano_lectivo=ano, docente=docente,
                                             estado__in=['PENDIENTE', 'APROBADO']).first()
    if vigente:
        messages.info(request, f'Ese permiso ya está {vigente.get_estado_display().lower()}.')
        return redirect(volver)
    PermisoComision.objects.create(colegio=colegio, estudiante=estudiante, materia=asig.materia, ano_lectivo=ano,
                                   docente=docente, motivo=(request.POST.get('motivo') or '').strip()[:300])
    crear_notificaciones_multiples(
        administradores(colegio),
        f'{request.user.get_full_name() or request.user.username} pide permiso para ajustar la nota de '
        f'{asig.materia.nombre} a {estudiante} (comisión {ano}).',
        'GENERAL', colegio, url_name='notas:permisos_comision')
    messages.success(request, f'Permiso pedido: {asig.materia.nombre} de {estudiante}. Le avisaremos cuando el '
                              f'administrador responda.')
    return redirect(volver)


@user_passes_test(es_admin_usuario)
def permisos_comision(request):
    """Bandeja del administrador: aprobar, rechazar o quitar los permisos que piden los docentes."""
    colegio = request.colegio
    if not colegio:
        return HttpResponseNotFound('<h1>Colegio no configurado</h1>')
    if request.method == 'POST':
        p = get_object_or_404(PermisoComision.objects.select_related('docente__user', 'materia', 'estudiante__user'),
                              pk=request.POST.get('permiso') or 0, colegio=colegio)
        accion = request.POST.get('accion')
        nuevo = {'aprobar': 'APROBADO', 'rechazar': 'RECHAZADO', 'quitar': 'REVOCADO'}.get(accion)
        if nuevo:
            p.estado, p.revisado_por, p.revisado_en = nuevo, request.user, timezone.now()
            p.respuesta = (request.POST.get('respuesta') or '').strip()[:300]
            p.save()
            texto = {'APROBADO': 'aprobó', 'RECHAZADO': 'rechazó', 'REVOCADO': 'quitó'}[nuevo]
            Notificacion.objects.create(
                colegio=colegio, destinatario=p.docente.user, tipo='GENERAL',
                mensaje=(f'El administrador {texto} su permiso para ajustar {p.materia.nombre} de {p.estudiante} '
                         f'(comisión {p.ano_lectivo}).' + (f' {p.respuesta}' if p.respuesta else '')),
                url=(reverse('notas:comision_estudiante', args=[p.estudiante_id]) + f'?ano={p.ano_lectivo}'
                     if nuevo == 'APROBADO' else _url_alertas(p.ano_lectivo)))
            messages.success(request, f'Permiso {p.get_estado_display().lower()}: {p.materia.nombre} de {p.estudiante}.')
        return redirect('notas:permisos_comision')
    qs = (PermisoComision.objects.filter(colegio=colegio)
          .select_related('docente__user', 'materia', 'estudiante__user', 'estudiante__curso', 'revisado_por'))
    return render(request, 'notas/admin_crud/permisos_comision.html', {
        'titulo': 'Permisos para ajustar notas (comisión)',
        'pendientes': list(qs.filter(estado='PENDIENTE')),
        'resueltos': list(qs.exclude(estado='PENDIENTE')[:100]),
    })
