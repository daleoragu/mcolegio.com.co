# notas/views/planillas_views.py
"""«Mis planillas»: el punto de entrada del docente a sus notas.

Desde aquí, por cada asignatura:
  * configura cuántas notas tiene cada componente y cómo se llama cada una;
  * abre la planilla en línea;
  * descarga el Excel (una asignatura o todas) para trabajar sin internet;
  * sube el Excel de vuelta, con vista previa antes de guardar.
"""
import re

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseForbidden, HttpResponseNotFound
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from ..models import AsignacionDocente, Docente, PeriodoAcademico
from ..planillas import excel as excel_mod
from ..planillas.columnas import (TOPE_COLUMNAS, columnas_del_plan, componentes_activos, configuracion,
                                  guardar_plan, notas_guardadas)

CLAVE_SESION = 'planilla_subida'


def _docente_actual(request):
    return Docente.objects.filter(user=request.user, colegio=request.colegio).select_related('user').first()


def _docente_y_asignaciones(request):
    """(docente, asignaciones) que puede ver este usuario.

    El docente ve las suyas; el administrador escoge un docente con ?docente=.
    """
    if request.user.is_superuser:
        docente_id = request.GET.get('docente') or request.POST.get('docente')
        docente = Docente.objects.filter(id=docente_id, colegio=request.colegio).select_related('user').first() \
            if docente_id else None
    else:
        docente = _docente_actual(request)
    if docente is None:
        return None, AsignacionDocente.objects.none()
    asignaciones = (AsignacionDocente.objects.filter(docente=docente, colegio=request.colegio)
                    .select_related('materia', 'curso', 'docente__user')
                    .order_by('curso__orden', 'curso__nombre', 'materia__nombre'))
    return docente, asignaciones


def _periodo(request):
    """El periodo escogido, o el abierto más reciente, o el último."""
    periodos = PeriodoAcademico.objects.filter(colegio=request.colegio).order_by('-ano_lectivo', '-fecha_inicio')
    pid = request.GET.get('periodo') or request.POST.get('periodo')
    if pid and str(pid).isdigit():
        p = periodos.filter(id=pid).first()
        if p:
            return p, periodos
    return (periodos.filter(esta_activo=True).first() or periodos.first()), periodos


def _puede_editar(request, asignacion):
    return request.user.is_superuser or (asignacion.docente_id and asignacion.docente.user_id == request.user.id)


@login_required
def mis_planillas(request):
    if not request.colegio:
        return HttpResponseNotFound('<h1>Colegio no configurado</h1>')
    docente, asignaciones = _docente_y_asignaciones(request)
    periodo, periodos = _periodo(request)
    config = configuracion(request.colegio)

    filas = []
    if periodo is not None:
        for a in asignaciones:
            componentes = []
            for codigo, nombre, peso in componentes_activos(a, config):
                por_est = notas_guardadas(a, periodo, codigo)
                columnas = columnas_del_plan(a, periodo, codigo, por_est, config)
                # Columnas que ya tienen notas: no se pueden quitar desde aquí.
                con_notas = set()
                for notas in por_est.values():
                    con_notas.update(d for d, _ in notas)
                componentes.append({'codigo': codigo, 'nombre': nombre,
                                    'peso': format(peso.normalize(), 'f'), 'columnas': columnas,
                                    'con_notas': sorted(con_notas)})
            filas.append({'a': a, 'componentes': componentes})

    return render(request, 'notas/docente/mis_planillas.html', {
        'docente': docente, 'filas': filas, 'periodo': periodo, 'periodos': periodos,
        'docentes': (Docente.objects.filter(colegio=request.colegio).select_related('user')
                     .order_by('user__last_name') if request.user.is_superuser else None),
        'por_defecto': config.notas_por_componente, 'tope': TOPE_COLUMNAS,
        'colegio': request.colegio,
    })


@login_required
@require_POST
def guardar_columnas(request, asignacion_id, periodo_id):
    """Guarda cuántas notas tiene cada componente y cómo se llaman."""
    asignacion = get_object_or_404(AsignacionDocente, id=asignacion_id, colegio=request.colegio)
    periodo = get_object_or_404(PeriodoAcademico, id=periodo_id, colegio=request.colegio)
    if not _puede_editar(request, asignacion):
        return HttpResponseForbidden('Esta asignatura no es suya.')
    for codigo, nombre, _ in componentes_activos(asignacion):
        nombres = [n for n in request.POST.getlist(f'col_{codigo}')]
        if not nombres:
            continue
        # Lo que ya tiene notas no se puede quitar: se conserva al final.
        con_notas = []
        for notas in notas_guardadas(asignacion, periodo, codigo).values():
            con_notas.extend(d for d, _ in notas)
        limpios = [' '.join(n.split()) for n in nombres]
        for d in dict.fromkeys(con_notas):
            if d not in limpios:
                limpios.append(d)
                messages.warning(request, f'«{d}» de {nombre} ya tiene notas, así que se dejó. '
                                          f'Bórrele las notas en la planilla en línea si quiere quitarla.')
        guardar_plan(asignacion, periodo, codigo, limpios[:TOPE_COLUMNAS])
    messages.success(request, f'Columnas de {asignacion.curso.nombre} · {asignacion.materia.nombre} guardadas. '
                              f'Así salen en línea y en el Excel.')
    url = reverse('notas:mis_planillas') + f'?periodo={periodo.id}'
    if request.user.is_superuser and asignacion.docente_id:
        url += f'&docente={asignacion.docente_id}'
    return redirect(url + f'#asig-{asignacion.id}')


def _nombre_archivo(texto):
    limpio = re.sub(r'[^A-Za-z0-9ÁÉÍÓÚÑáéíóúñ _\-]', '', texto).strip()
    return re.sub(r'\s+', ' ', limpio)[:120] or 'Planilla'


@login_required
def descargar_excel(request, periodo_id, asignacion_id=None):
    if not request.colegio:
        return HttpResponseNotFound('<h1>Colegio no configurado</h1>')
    periodo = get_object_or_404(PeriodoAcademico, id=periodo_id, colegio=request.colegio)
    if asignacion_id:
        a = get_object_or_404(AsignacionDocente.objects.select_related('materia', 'curso', 'docente__user'),
                              id=asignacion_id, colegio=request.colegio)
        if not _puede_editar(request, a):
            return HttpResponseForbidden('Esta asignatura no es suya.')
        asignaciones = [a]
        nombre = f'Planilla {a.curso.nombre} {a.materia.nombre} {periodo.get_nombre_display()} {periodo.ano_lectivo}'
    else:
        docente, qs = _docente_y_asignaciones(request)
        if docente is None:
            return HttpResponseForbidden('Escoja un docente.')
        asignaciones = list(qs)
        nombre = f'Planillas {docente.user.get_full_name()} {periodo.get_nombre_display()} {periodo.ano_lectivo}'
    datos = excel_mod.generar_libro(request.colegio, periodo, asignaciones)
    respuesta = HttpResponse(datos, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    respuesta['Content-Disposition'] = f'attachment; filename="{_nombre_archivo(nombre)}.xlsx"'
    return respuesta


@login_required
def subir_excel(request):
    """Paso 1: subir y ver qué cambiaría. Paso 2: confirmar y guardar."""
    if not request.colegio:
        return HttpResponseNotFound('<h1>Colegio no configurado</h1>')
    volver = reverse('notas:mis_planillas')

    if request.method == 'POST' and request.POST.get('accion') == 'confirmar':
        resultado = request.session.pop(CLAVE_SESION, None)
        if not resultado:
            messages.error(request, 'La vista previa venció. Suba el archivo otra vez.')
            return redirect('notas:subir_planilla')
        resumen = excel_mod.aplicar(resultado, request.colegio, request.user)
        total = sum(n for _, n in resumen)
        if resumen:
            detalle = '; '.join(f'{nombre}: {n}' for nombre, n in resumen)
            messages.success(request, f'Se guardaron las notas de {total} estudiante(s). {detalle}.')
        else:
            messages.info(request, 'No había nada que guardar.')
        return redirect(volver)

    if request.method == 'POST' and request.POST.get('accion') == 'cancelar':
        request.session.pop(CLAVE_SESION, None)
        messages.info(request, 'No se guardó nada.')
        return redirect(volver)

    if request.method == 'POST':
        archivo = request.FILES.get('archivo')
        if not archivo:
            messages.error(request, 'Escoja el archivo de Excel.')
            return redirect('notas:subir_planilla')
        if archivo.size > 10 * 1024 * 1024:
            messages.error(request, 'El archivo pesa más de 10 MB. ¿Es la planilla descargada de mColegio?')
            return redirect('notas:subir_planilla')
        try:
            resultado = excel_mod.leer_libro(archivo, request.colegio, request.user)
        except excel_mod.ErrorDeArchivo as e:
            messages.error(request, str(e))
            return redirect('notas:subir_planilla')
        request.session[CLAVE_SESION] = excel_mod.a_sesion(resultado)
        hay_algo = any(h['estado'] == 'ok' and (h['cambian'] or h.get('plan_cambia')) for h in resultado['hojas'])
        return render(request, 'notas/docente/subir_planilla.html', {
            'resultado': resultado, 'hay_algo': hay_algo, 'colegio': request.colegio, 'paso': 'revisar'})

    return render(request, 'notas/docente/subir_planilla.html', {'colegio': request.colegio, 'paso': 'subir'})
