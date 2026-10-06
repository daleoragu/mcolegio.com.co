# /notas/views/indicador_views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.views.decorators.http import require_POST
# Se añade HttpResponseNotFound para manejar el caso de un colegio no identificado
from django.http import HttpResponseNotFound

from ..models import Docente, IndicadorLogroPeriodo, AsignacionDocente, PeriodoAcademico
from ..permisos import es_admin, es_admin_usuario

@login_required
@require_POST
def crear_indicador_vista(request):
    """
    Procesa la petición para crear un nuevo indicador, asegurando que todos
    los objetos pertenezcan al colegio actual.
    """
    if not request.colegio:
        return HttpResponseNotFound("<h1>Colegio no configurado</h1>")

    asignacion_id = request.POST.get('asignacion_id')
    periodo_id = request.POST.get('periodo_id')
    descripcion = request.POST.get('descripcion', '').strip()
    docente_id_param = request.POST.get('docente_id')

    redirect_url = f"{reverse('notas:ingresar_notas_periodo')}?asignacion_id={asignacion_id or ''}&periodo_id={periodo_id or ''}"
    if es_admin(request) and docente_id_param:
        redirect_url += f"&docente_id={docente_id_param}"

    if not all([asignacion_id, periodo_id, descripcion]):
        messages.error(request, "Faltan datos o la descripción está vacía para crear el indicador.")
        return redirect(redirect_url)
    
    try:
        # CORRECCIÓN: Filtrar por colegio al obtener los objetos.
        asignacion = get_object_or_404(AsignacionDocente, id=asignacion_id, colegio=request.colegio)
        periodo = get_object_or_404(PeriodoAcademico, id=periodo_id, colegio=request.colegio)
        
        docente_actual = Docente.objects.filter(user=request.user, colegio=request.colegio).first()
        
        if not (es_admin(request) or (docente_actual and asignacion.docente == docente_actual)):
            messages.error(request, "No tiene permiso para agregar indicadores a esta asignación.")
            return redirect(redirect_url)

        # CORRECCIÓN: Asociar el nuevo indicador al colegio actual.
        # Se asume que el modelo IndicadorLogroPeriodo tiene un campo 'colegio'.
        IndicadorLogroPeriodo.objects.create(
            colegio=request.colegio,
            asignacion=asignacion,
            periodo=periodo,
            descripcion=descripcion
        )
        messages.success(request, "Indicador de logro agregado exitosamente.")
    except Exception as e:
        messages.error(request, f"Error al crear el indicador: {e}")
    
    return redirect(redirect_url)


@login_required
def editar_indicador_vista(request, indicador_id):
    """
    Muestra el formulario para editar un indicador, asegurando que pertenezca
    al colegio actual.
    """
    if not request.colegio:
        return HttpResponseNotFound("<h1>Colegio no configurado</h1>")

    try:
        # CORRECCIÓN: Filtrar por colegio al obtener el indicador.
        indicador = IndicadorLogroPeriodo.objects.select_related('asignacion__docente', 'asignacion__docente__user').get(id=indicador_id, colegio=request.colegio)
        docente_actual = Docente.objects.filter(user=request.user, colegio=request.colegio).first()
        
        if not (es_admin(request) or (docente_actual and indicador.asignacion.docente == docente_actual)):
            messages.error(request, "No tiene permiso para editar este indicador.")
            return redirect('notas:ingresar_notas_periodo')
    except IndicadorLogroPeriodo.DoesNotExist:
        messages.error(request, "El indicador que intenta editar no existe o no pertenece a este colegio.")
        return redirect('notas:ingresar_notas_periodo')

    docente_id_param = indicador.asignacion.docente.id if es_admin(request) else None
    redirect_url = f"{reverse('notas:ingresar_notas_periodo')}?asignacion_id={indicador.asignacion.id}&periodo_id={indicador.periodo.id}"
    if docente_id_param:
        redirect_url += f"&docente_id={docente_id_param}"
    
    if request.method == 'POST':
        nueva_descripcion = request.POST.get('descripcion', '').strip()
        if nueva_descripcion:
            indicador.descripcion = nueva_descripcion
            indicador.save()
            messages.success(request, "Indicador actualizado correctamente.")
        else:
            messages.error(request, "La descripción no puede estar vacía.")
        return redirect(redirect_url)
    
    context = {
        'form': {'descripcion': indicador.descripcion},
        'titulo': f'Editar Indicador para {indicador.asignacion.materia}',
        'url_action': reverse('editar_indicador', args=[indicador.id]),
        'redirect_url_cancel': redirect_url,
        'colegio': request.colegio
    }
    return render(request, 'notas/docente/editar_indicador.html', context)


@login_required
@require_POST
def eliminar_indicador_vista(request, indicador_id):
    """
    Elimina un indicador, asegurando que pertenezca al colegio actual.
    """
    if not request.colegio:
        return HttpResponseNotFound("<h1>Colegio no configurado</h1>")
        
    try:
        # CORRECCIÓN: Filtrar por colegio al obtener el indicador.
        indicador = IndicadorLogroPeriodo.objects.select_related('asignacion__docente').get(id=indicador_id, colegio=request.colegio)
        
        docente_id_param = indicador.asignacion.docente.id if es_admin(request) else None
        redirect_url = f"{reverse('notas:ingresar_notas_periodo')}?asignacion_id={indicador.asignacion.id}&periodo_id={indicador.periodo.id}"
        if docente_id_param:
            redirect_url += f"&docente_id={docente_id_param}"
        
        docente_actual = Docente.objects.filter(user=request.user, colegio=request.colegio).first()
        
        if not (es_admin(request) or (docente_actual and indicador.asignacion.docente == docente_actual)):
            messages.error(request, "No tiene permiso para eliminar este indicador.")
        else:
            indicador.delete()
            messages.success(request, "Indicador eliminado exitosamente.")
        
        return redirect(redirect_url)
    except IndicadorLogroPeriodo.DoesNotExist:
        messages.error(request, "El indicador que intenta eliminar no existe o no pertenece a este colegio.")
        return redirect('notas:ingresar_notas_periodo')
