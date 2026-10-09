# notas/views/gestion_academica_views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import user_passes_test
from django.contrib import messages
from django.db import transaction, IntegrityError
from django.db.models import Sum, Prefetch, OuterRef, Subquery
from django.views.decorators.http import require_POST
from django.http import HttpResponseNotFound
from django.urls import reverse
from decimal import Decimal

from ..models import (
    Curso, AreaConocimiento, Materia, Docente, AsignacionDocente,
    PonderacionAreaMateria
)
from ..forms import CursoForm, AreaConocimientoForm, MateriaForm
from ..permisos import es_admin, es_admin_usuario

def es_personal_admin(user):
    """Verifica si el usuario es superusuario."""
    return es_admin_usuario(user)

# ===============================================================
# VISTA PRINCIPAL DE ASIGNACIÓN ACADÉMICA
# ===============================================================
@user_passes_test(es_personal_admin)
def gestion_asignacion_academica_vista(request):
    if not request.colegio:
        return HttpResponseNotFound("<h1>Colegio no configurado</h1>")

    docentes_list = Docente.objects.filter(colegio=request.colegio).select_related('user').prefetch_related(
        'asignaciondocente_set__materia',
        'asignaciondocente_set__curso',
        'cursos_dirigidos'
    ).annotate(
        total_ih=Sum('asignaciondocente__intensidad_horaria_semanal', default=0)
    ).order_by('user__last_name')
    
    # Ordena por el nuevo campo 'orden'
    cursos_list = Curso.objects.filter(colegio=request.colegio).annotate(
        total_ih=Sum('asignaciondocente__intensidad_horaria_semanal', default=0)
    ).order_by('orden')
    
    areas_list = AreaConocimiento.objects.filter(colegio=request.colegio).annotate(
        total_ih=Sum('ponderacionareamateria__materia__asignaciondocente__intensidad_horaria_semanal', default=0)
    ).order_by('nombre')

    cursos_para_modal = Curso.objects.filter(colegio=request.colegio).order_by('orden')
    
    cursos_sin_director = Curso.objects.filter(colegio=request.colegio, director_grado__isnull=True).order_by('orden')

    subquery_area_nombre = Subquery(
        PonderacionAreaMateria.objects.filter(materia=OuterRef('pk'), colegio=request.colegio).values('area__nombre')[:1]
    )
    subquery_area_id = Subquery(
        PonderacionAreaMateria.objects.filter(materia=OuterRef('pk'), colegio=request.colegio).values('area__id')[:1]
    )

    materias_para_modal = Materia.objects.filter(colegio=request.colegio).annotate(
        area_nombre_display=subquery_area_nombre,
        area_id_display=subquery_area_id
    ).order_by('nombre')
    
    docentes_para_modal = Docente.objects.filter(colegio=request.colegio).select_related('user').order_by('user__first_name', 'user__last_name')

    context = {
        'docentes_list': docentes_list,
        'cursos_list': cursos_list,
        'areas_list': areas_list,
        'cursos_sin_director': cursos_sin_director,
        'cursos': cursos_para_modal,
        'materias': materias_para_modal,
        'docentes': docentes_para_modal,
        'titulo': "Panel de Asignación Académica",
        'colegio': request.colegio,
    }
    return render(request, 'notas/admin_crud/gestion_asignacion_academica.html', context)

# ===============================================================
# CRUD PARA ASIGNACIONES
# ===============================================================
@user_passes_test(es_personal_admin)
@require_POST
def crear_asignacion_vista(request):
    if not request.colegio:
        return HttpResponseNotFound("<h1>Colegio no configurado</h1>")
    try:
        curso_id = request.POST.get('curso')
        materia_id = request.POST.get('materia')
        docente_id = request.POST.get('docente')
        intensidad_horaria_semanal = request.POST.get('intensidad_horaria_semanal')
        
        asignacion, created = AsignacionDocente.objects.get_or_create(
            colegio=request.colegio,
            curso_id=curso_id,
            materia_id=materia_id,
            docente_id=docente_id,
            defaults={'intensidad_horaria_semanal': intensidad_horaria_semanal}
        )
        if not created:
            asignacion.intensidad_horaria_semanal = intensidad_horaria_semanal
            asignacion.save()
            messages.info(request, 'Asignación actualizada (ya existía).')
        else:
            messages.success(request, 'Asignación creada correctamente.')
    except Exception as e:
        messages.error(request, f'Error al crear la asignación: {e}')
    return redirect(request.META.get('HTTP_REFERER', 'notas:gestion_asignacion_academica'))

@user_passes_test(es_personal_admin)
@require_POST
def editar_asignacion_vista(request, asignacion_id):
    if not request.colegio:
        return HttpResponseNotFound("<h1>Colegio no configurado</h1>")
    
    asignacion = get_object_or_404(AsignacionDocente, pk=asignacion_id, colegio=request.colegio)
    try:
        asignacion.curso_id = request.POST.get('curso')
        asignacion.materia_id = request.POST.get('materia')
        asignacion.docente_id = request.POST.get('docente')
        asignacion.intensidad_horaria_semanal = request.POST.get('intensidad_horaria_semanal')
        asignacion.save()
        messages.success(request, '¡Asignación actualizada!')
    except Exception as e:
        messages.error(request, f'Error al editar la asignación: {e}')
    return redirect(request.META.get('HTTP_REFERER', 'notas:gestion_asignacion_academica'))

@user_passes_test(es_personal_admin)
@require_POST
def eliminar_asignacion_vista(request, asignacion_id):
    if not request.colegio:
        return HttpResponseNotFound("<h1>Colegio no configurado</h1>")
    asignacion = get_object_or_404(AsignacionDocente, id=asignacion_id, colegio=request.colegio)
    asignacion.delete()
    messages.success(request, 'Asignación eliminada.')
    return redirect(request.META.get('HTTP_REFERER', 'notas:gestion_asignacion_academica'))

# ===============================================================
# VISTAS DE DETALLE (POR CURSO, ÁREA Y DOCENTE)
# ===============================================================
@user_passes_test(es_personal_admin)
def detalle_curso(request, curso_id):
    if not request.colegio:
        return HttpResponseNotFound("<h1>Colegio no configurado</h1>")
    curso = get_object_or_404(Curso, pk=curso_id, colegio=request.colegio)
    asignaciones = AsignacionDocente.objects.filter(colegio=request.colegio, curso=curso).select_related('materia', 'docente__user').order_by('materia__nombre')
    total_ih_curso = asignaciones.aggregate(total=Sum('intensidad_horaria_semanal'))['total'] or 0
    cursos_para_modal = Curso.objects.filter(colegio=request.colegio).order_by('orden')
    materias_para_modal = Materia.objects.filter(colegio=request.colegio).order_by('nombre')
    docentes_para_modal = Docente.objects.filter(colegio=request.colegio).select_related('user').order_by('user__first_name')
    context = {
        'titulo': f'Detalle de {curso.nombre}', 'curso': curso, 'asignaciones': asignaciones, 'total_ih_curso': total_ih_curso,
        'cursos': cursos_para_modal, 'materias': materias_para_modal, 'docentes': docentes_para_modal, 'colegio': request.colegio,
    }
    return render(request, 'notas/admin_crud/detalle_curso.html', context)

@user_passes_test(es_personal_admin)
def detalle_area(request, area_id):
    if not request.colegio:
        return HttpResponseNotFound("<h1>Colegio no configurado</h1>")
    area = get_object_or_404(AreaConocimiento, pk=area_id, colegio=request.colegio)
    asignaciones = AsignacionDocente.objects.filter(colegio=request.colegio, materia__ponderacionareamateria__area=area).select_related('materia', 'curso', 'docente__user').order_by('curso__orden', 'materia__nombre')
    total_ih_area = asignaciones.aggregate(total=Sum('intensidad_horaria_semanal'))['total'] or 0
    cursos_para_modal = Curso.objects.filter(colegio=request.colegio).order_by('orden')
    materias_para_modal = Materia.objects.filter(colegio=request.colegio).order_by('nombre')
    docentes_para_modal = Docente.objects.filter(colegio=request.colegio).select_related('user').order_by('user__first_name')
    context = {
        'titulo': f'Detalle del Área: {area.nombre}', 'area': area, 'asignaciones': asignaciones, 'total_ih_area': total_ih_area,
        'cursos': cursos_para_modal, 'materias': materias_para_modal, 'docentes': docentes_para_modal, 'colegio': request.colegio,
    }
    return render(request, 'notas/admin_crud/detalle_area.html', context)

@user_passes_test(es_personal_admin)
def detalle_docente(request, docente_id):
    if not request.colegio:
        return HttpResponseNotFound("<h1>Colegio no configurado</h1>")
    
    docente = get_object_or_404(Docente, pk=docente_id, colegio=request.colegio)
    asignaciones = AsignacionDocente.objects.filter(colegio=request.colegio, docente=docente).select_related('materia', 'curso').order_by('curso__orden', 'materia__nombre')
    total_ih_docente = asignaciones.aggregate(total=Sum('intensidad_horaria_semanal'))['total'] or 0
    cursos_para_modal = Curso.objects.filter(colegio=request.colegio).order_by('orden')
    materias_para_modal = Materia.objects.filter(colegio=request.colegio).order_by('nombre')
    docentes_para_modal = Docente.objects.filter(colegio=request.colegio).select_related('user').order_by('user__first_name')
    context = {
        'titulo': f'Detalle del Docente: {docente.user.get_full_name()}',
        'docente_actual': docente, 'asignaciones': asignaciones, 'total_ih_docente': total_ih_docente,
        'cursos': cursos_para_modal, 'materias': materias_para_modal, 'docentes': docentes_para_modal,
        'colegio': request.colegio,
    }
    return render(request, 'notas/admin_crud/detalle_docente.html', context)

# ===============================================================
# VISTA PARA ASIGNAR DIRECTOR DE GRADO
# ===============================================================
@user_passes_test(es_personal_admin)
@require_POST
def asignar_director_grado_vista(request):
    if not request.colegio:
        return HttpResponseNotFound("<h1>Colegio no configurado</h1>")
    
    try:
        docente_id = request.POST.get('docente_id')
        curso_id = request.POST.get('curso_id')
        
        docente = get_object_or_404(Docente, id=docente_id, colegio=request.colegio)
        curso = get_object_or_404(Curso, id=curso_id, colegio=request.colegio)
        
        curso.director_grado = docente
        curso.save()
        
        messages.success(request, f'Se ha asignado a {docente.user.get_full_name()} como director de {curso.nombre}.')
        
    except Exception as e:
        messages.error(request, f'Error al asignar director de grado: {e}')
        
    return redirect('notas:gestion_asignacion_academica')

# ===============================================================
# VISTAS PARA GESTIÓN DE CURSOS
# ===============================================================
@user_passes_test(es_personal_admin)
def gestion_cursos_vista(request):
    if not request.colegio:
        return HttpResponseNotFound("<h1>Colegio no configurado</h1>")
    
    cursos_qs = Curso.objects.filter(colegio=request.colegio).order_by('orden', 'nombre')

    # --- INICIO: CORRECCIÓN AUTOMÁTICA DEL ORDEN ---
    if cursos_qs.count() > 1 and cursos_qs.last().orden == 0:
        with transaction.atomic():
            cursos_para_inicializar = Curso.objects.filter(colegio=request.colegio).order_by('nombre')
            for i, curso in enumerate(cursos_para_inicializar, 1):
                Curso.objects.filter(pk=curso.pk).update(orden=i)
        
        messages.info(request, "Se ha inicializado el orden de los cursos. Ahora puede usar las flechas.")
        cursos = Curso.objects.filter(colegio=request.colegio).select_related('director_grado__user').order_by('orden')
    else:
        cursos = cursos_qs.select_related('director_grado__user')
    # --- FIN: CORRECCIÓN AUTOMÁTICA DEL ORDEN ---
    cursos = cursos.select_related('sede')

    context = {'cursos': cursos, 'titulo': 'Gestión de Cursos y Grados', 'colegio': request.colegio,
               'hay_sedes': request.colegio.sedes.exists()}
    return render(request, 'notas/admin_crud/gestion_cursos.html', context)

@user_passes_test(es_personal_admin)
@require_POST
@transaction.atomic
def reordenar_curso_vista(request, curso_id, direccion):
    if not request.colegio:
        return HttpResponseNotFound("<h1>Colegio no configurado</h1>")

    curso_a_mover = get_object_or_404(Curso, id=curso_id, colegio=request.colegio)
    
    if direccion == 'subir':
        curso_adyacente = Curso.objects.filter(
            colegio=request.colegio, 
            orden__lt=curso_a_mover.orden
        ).order_by('-orden').first()
    else: # Bajar
        curso_adyacente = Curso.objects.filter(
            colegio=request.colegio, 
            orden__gt=curso_a_mover.orden
        ).order_by('orden').first()

    if curso_adyacente:
        curso_a_mover.orden, curso_adyacente.orden = curso_adyacente.orden, curso_a_mover.orden
        curso_a_mover.save()
        curso_adyacente.save()
        messages.success(request, f"Se ha cambiado el orden de '{curso_a_mover.nombre}'.")
    
    return redirect('notas:gestion_cursos')

@user_passes_test(es_personal_admin)
def crear_curso_vista(request):
    if not request.colegio:
        return HttpResponseNotFound("<h1>Colegio no configurado</h1>")
        
    if request.method == 'POST':
        form = CursoForm(request.POST, colegio=request.colegio)
        if form.is_valid():
            curso = form.save(commit=False)
            curso.colegio = request.colegio
            curso.save()
            messages.success(request, '¡Curso creado exitosamente!')
            return redirect('notas:gestion_cursos')
    else:
        form = CursoForm(colegio=request.colegio)
    context = {'form': form, 'titulo': 'Crear Nuevo Curso / Grado', 'colegio': request.colegio}
    return render(request, 'notas/admin_crud/curso_form.html', context)

@user_passes_test(es_personal_admin)
def editar_curso_vista(request, curso_id):
    if not request.colegio:
        return HttpResponseNotFound("<h1>Colegio no configurado</h1>")
        
    curso = get_object_or_404(Curso, id=curso_id, colegio=request.colegio)
    if request.method == 'POST':
        form = CursoForm(request.POST, instance=curso, colegio=request.colegio)
        if form.is_valid():
            form.save()
            messages.success(request, '¡Curso actualizado exitosamente!')
            return redirect('notas:gestion_cursos')
    else:
        form = CursoForm(instance=curso, colegio=request.colegio)
    context = {'form': form, 'titulo': f'Editar Curso: {curso.nombre}', 'colegio': request.colegio}
    return render(request, 'notas/admin_crud/curso_form.html', context)

@user_passes_test(es_personal_admin)
@require_POST
def eliminar_curso_vista(request, curso_id):
    if not request.colegio:
        return HttpResponseNotFound("<h1>Colegio no configurado</h1>")
        
    curso = get_object_or_404(Curso, id=curso_id, colegio=request.colegio)
    if curso.estudiante_set.exists():
        messages.error(request, f"No se puede eliminar '{curso.nombre}' porque tiene estudiantes asignados.")
    else:
        nombre_curso = curso.nombre
        curso.delete()
        messages.success(request, f"Curso '{nombre_curso}' eliminado con éxito.")
    return redirect('notas:gestion_cursos')

# ===============================================================
# VISTAS PARA GESTIÓN DE ÁREAS Y MATERIAS
# ===============================================================
@user_passes_test(es_personal_admin)
def gestion_materias_vista(request):
    if not request.colegio:
        return HttpResponseNotFound("<h1>Colegio no configurado</h1>")
    materias = Materia.objects.filter(colegio=request.colegio).order_by('nombre')
    context = {'materias': materias, 'titulo': 'Gestión de Materias', 'colegio': request.colegio}
    return render(request, 'notas/admin_crud/gestion_materias.html', context)

@user_passes_test(es_personal_admin)
def gestion_areas_vista(request):
    if not request.colegio:
        return HttpResponseNotFound("<h1>Colegio no configurado</h1>")
    areas = AreaConocimiento.objects.filter(colegio=request.colegio).order_by('nombre')
    context = {'areas': areas, 'titulo': 'Gestión de Áreas', 'colegio': request.colegio}
    return render(request, 'notas/admin_crud/gestion_areas.html', context)

@user_passes_test(es_personal_admin)
def crear_area_vista(request):
    if not request.colegio:
        return HttpResponseNotFound("<h1>Colegio no configurado</h1>")
    if request.method == 'POST':
        form = AreaConocimientoForm(request.POST)
        if form.is_valid():
            area = form.save(commit=False)
            area.colegio = request.colegio
            area.save()
            messages.success(request, f"Área '{form.cleaned_data['nombre']}' creada con éxito.")
            return redirect('notas:gestion_areas')
    else:
        form = AreaConocimientoForm()
    context = {'form': form, 'titulo': 'Crear Nueva Área de Conocimiento', 'colegio': request.colegio}
    return render(request, 'notas/admin_crud/formulario_generico.html', context)

@user_passes_test(es_personal_admin)
def editar_area_vista(request, area_id):
    if not request.colegio:
        return HttpResponseNotFound("<h1>Colegio no configurado</h1>")
    area = get_object_or_404(AreaConocimiento, id=area_id, colegio=request.colegio)
    if request.method == 'POST':
        form = AreaConocimientoForm(request.POST, instance=area)
        if form.is_valid():
            form.save()
            messages.success(request, f"Área '{area.nombre}' actualizada con éxito.")
            return redirect('notas:gestion_areas')
    else:
        form = AreaConocimientoForm(instance=area)
    context = {'form': form, 'titulo': f"Editar Área: {area.nombre}", 'colegio': request.colegio}
    return render(request, 'notas/admin_crud/formulario_generico.html', context)

@user_passes_test(es_personal_admin)
@require_POST
def eliminar_area_vista(request, area_id):
    if not request.colegio:
        return HttpResponseNotFound("<h1>Colegio no configurado</h1>")
    area = get_object_or_404(AreaConocimiento, id=area_id, colegio=request.colegio)
    if area.materias.filter(colegio=request.colegio).exists():
        messages.error(request, f"No se puede eliminar el área '{area.nombre}' porque contiene materias asociadas.")
    else:
        nombre_area = area.nombre
        area.delete()
        messages.success(request, f"Área '{nombre_area}' eliminada con éxito.")
    return redirect('notas:gestion_areas')

@user_passes_test(es_personal_admin)
@transaction.atomic
def crear_materia_vista(request, area_id=None):
    if not request.colegio:
        return HttpResponseNotFound("<h1>Colegio no configurado</h1>")

    if request.method == 'POST':
        form = MateriaForm(request.POST, colegio=request.colegio)
        if form.is_valid():
            materia = form.save(commit=False)
            materia.colegio = request.colegio
            materia.save()

            area_seleccionada = form.cleaned_data.get('area')
            if area_seleccionada:
                PonderacionAreaMateria.objects.get_or_create(
                    colegio=request.colegio,
                    area=area_seleccionada,
                    materia=materia,
                    defaults={'peso_porcentual': 0}
                )

            messages.success(request, f"Materia '{materia.nombre}' creada con éxito.")
            return redirect('notas:gestion_materias')
    else:
        initial_data = {}
        if area_id:
            initial_data['area'] = area_id
        
        form = MateriaForm(colegio=request.colegio, initial=initial_data)

    context = {'form': form, 'titulo': 'Añadir Nueva Materia', 'colegio': request.colegio}
    return render(request, 'notas/admin_crud/formulario_materia.html', context)

@user_passes_test(es_personal_admin)
@transaction.atomic
def editar_materia_vista(request, materia_id):
    if not request.colegio:
        return HttpResponseNotFound("<h1>Colegio no configurado</h1>")
    
    materia = get_object_or_404(Materia, id=materia_id, colegio=request.colegio)

    if request.method == 'POST':
        form = MateriaForm(request.POST, instance=materia, colegio=request.colegio)
        if form.is_valid():
            form.save()
            area_seleccionada = form.cleaned_data.get('area')
            
            PonderacionAreaMateria.objects.filter(colegio=request.colegio, materia=materia).delete()

            if area_seleccionada:
                PonderacionAreaMateria.objects.create(
                    colegio=request.colegio,
                    area=area_seleccionada,
                    materia=materia,
                    peso_porcentual=0
                )

            messages.success(request, f"Materia '{materia.nombre}' actualizada con éxito.")
            return redirect('notas:gestion_materias')
    else:
        ponderacion_actual = PonderacionAreaMateria.objects.filter(colegio=request.colegio, materia=materia).first()
        initial_data = {}
        if ponderacion_actual:
            initial_data['area'] = ponderacion_actual.area
        
        form = MateriaForm(instance=materia, colegio=request.colegio, initial=initial_data)

    context = {'form': form, 'titulo': f"Editar Materia: {materia.nombre}", 'colegio': request.colegio}
    return render(request, 'notas/admin_crud/formulario_materia.html', context)


@user_passes_test(es_personal_admin)
@require_POST
def eliminar_materia_vista(request, materia_id):
    if not request.colegio:
        return HttpResponseNotFound("<h1>Colegio no configurado</h1>")
    materia = get_object_or_404(Materia, id=materia_id, colegio=request.colegio)
    nombre_materia = materia.nombre
    try:
        materia.delete()
        messages.success(request, f"Materia '{nombre_materia}' eliminada con éxito.")
    except IntegrityError:
        messages.error(request, f"No se pudo eliminar la materia. Puede que esté asignada a un docente o tenga notas registradas.")
    return redirect('notas:gestion_materias')

def _grado_pedido(valor, grados):
    try:
        g = int(valor)
    except (TypeError, ValueError):
        return None
    return g if g in grados else None


@user_passes_test(es_personal_admin)
@transaction.atomic
def gestion_ponderacion_areas_vista(request):
    """Peso de cada materia en su área: los generales y, si hace falta, los de cada grado.

    Ej.: en Ciencias Naturales, 6.° puede ser Biología 60 / Química 20 / Física 20 y
    10.° Biología 20 / Química 40 / Física 40. Un grado sin porcentajes propios usa
    los generales.
    """
    from ..models.perfiles import GRADOS
    from ..pesos_area import grados_con_pesos_propios, guardar_grado, pesos_areas, volver_al_general
    colegio = request.colegio
    if not colegio:
        return HttpResponseNotFound("<h1>Colegio no configurado</h1>")
    nombres_grado = {g: n for g, n, _ in GRADOS}
    grados = sorted(set(Curso.objects.filter(colegio=colegio).exclude(grado__isnull=True).values_list('grado', flat=True)))
    grado = _grado_pedido(request.POST.get('grado') if request.method == 'POST' else request.GET.get('grado'), grados)
    url = reverse('notas:gestion_ponderacion_areas') + (f'?grado={grado}' if grado is not None else '')

    if request.method == 'POST':
        if request.POST.get('accion') == 'general' and grado is not None:
            n = volver_al_general(colegio, grado)
            messages.success(request, f'{nombres_grado[grado]} vuelve a usar los porcentajes generales ({n} porcentaje(s) propios borrados).')
            return redirect(url)
        valores = {}
        for clave, valor in request.POST.items():
            if not clave.startswith('peso-'):
                continue
            try:
                _, area_id, materia_id = clave.split('-')
                peso = Decimal(str(valor).replace(',', '.'))
            except (ValueError, ArithmeticError):
                continue
            if Decimal('0') <= peso <= Decimal('100'):
                valores[(int(area_id), int(materia_id))] = peso
        if grado is None:
            for (area_id, materia_id), peso in valores.items():
                PonderacionAreaMateria.objects.filter(colegio=colegio, area_id=area_id, materia_id=materia_id).update(
                    peso_porcentual=peso)
            messages.success(request, 'Porcentajes generales guardados. Los usan todos los grados que no tienen los suyos.')
        else:
            destinos = [grado] + [g for g in (_grado_pedido(x, grados) for x in request.POST.getlist('copiar_a'))
                                  if g is not None and g != grado]
            for g in destinos:
                guardar_grado(colegio, g, valores)
            messages.success(request, 'Porcentajes guardados para ' + ', '.join(nombres_grado[g] for g in destinos) + '.')
        return redirect(url)

    generales = pesos_areas(colegio)
    actuales = pesos_areas(colegio, grado) if grado is not None else generales
    propios = set()
    dictadas = None
    if grado is not None:
        from ..models.academicos import PonderacionGrado
        propios = set(PonderacionGrado.objects.filter(colegio=colegio, grado=grado).values_list('area_id', 'materia_id'))
        dictadas = set(AsignacionDocente.objects.filter(colegio=colegio, curso__grado=grado).values_list('materia_id', flat=True))

    areas = []
    for area in AreaConocimiento.objects.filter(colegio=colegio).order_by('nombre'):
        filas = []
        for p in (PonderacionAreaMateria.objects.filter(colegio=colegio, area=area).select_related('materia')
                  .order_by('materia__nombre')):
            if dictadas and p.materia_id not in dictadas:
                continue
            clave = (area.id, p.materia_id)
            filas.append({'materia': p.materia, 'peso': actuales.get(clave, p.peso_porcentual),
                          'general': generales.get(clave), 'propio': clave in propios,
                          'nombre_campo': f'peso-{area.id}-{p.materia_id}'})
        if filas or grado is None:
            areas.append({'area': area, 'filas': filas, 'propio': any(f['propio'] for f in filas)})

    con_propios = grados_con_pesos_propios(colegio)
    context = {
        'areas': areas,
        'grado': grado,
        'nombre_grado': nombres_grado.get(grado, ''),
        'grados': [{'valor': g, 'nombre': nombres_grado.get(g, g), 'propios': g in con_propios} for g in grados],
        'sin_asignacion': grado is not None and not dictadas,
        'titulo': "Gestión de Ponderación por Áreas",
        'colegio': colegio,
    }
    return render(request, 'notas/admin_crud/ponderacion_areas.html', context)
