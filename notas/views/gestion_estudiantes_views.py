# notas/views/gestion_estudiantes_views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import user_passes_test, login_required
from django.contrib.auth.models import User, Group
from django.contrib import messages
from django.db import transaction
from django.db.models import Q
from django.views.decorators.http import require_POST
from django.core.exceptions import PermissionDenied, ObjectDoesNotExist
from django.http import HttpResponseNotFound
from django.utils.text import slugify
from unidecode import unidecode

from ..models import Estudiante, FichaEstudiante, Curso
from ..forms import AdminCrearEstudianteForm, AdminEditarEstudianteForm
from ..permisos import es_admin, es_admin_usuario

def es_personal_admin(user):
    """Verifica si el usuario es superusuario."""
    return es_admin_usuario(user)

# ===============================================================
# VISTAS PARA GESTIÓN DE ESTUDIANTES
# ===============================================================

@user_passes_test(es_personal_admin)
def gestion_estudiantes_vista(request):
    if not request.colegio:
        return HttpResponseNotFound("<h1>Colegio no configurado</h1>")

    # 👇 FILTRADO: Mostrar solo cursos del colegio actual
    cursos = Curso.objects.filter(colegio=request.colegio)
    curso_seleccionado_id = request.GET.get('curso', '')
    query = request.GET.get('q', '')
    
    # 👇 FILTRADO: Mostrar solo estudiantes del colegio actual
    estudiantes_qs = Estudiante.objects.filter(colegio=request.colegio).select_related('user', 'curso').order_by('user__last_name', 'user__first_name')
    
    if curso_seleccionado_id:
        estudiantes_qs = estudiantes_qs.filter(curso_id=curso_seleccionado_id)
    if query:
        estudiantes_qs = estudiantes_qs.filter(
            Q(user__first_name__icontains=query) | Q(user__last_name__icontains=query)
        )
    
    context = {
        'estudiantes': estudiantes_qs,
        'cursos': cursos,
        'curso_seleccionado_id': curso_seleccionado_id,
        'search_query': query,
        'colegio': request.colegio,
    }
    return render(request, 'notas/admin_crud/gestion_estudiantes.html', context)


@user_passes_test(es_personal_admin)
@transaction.atomic
def crear_estudiante_vista(request):
    if not request.colegio:
        return HttpResponseNotFound("<h1>Colegio no configurado</h1>")

    if request.method == 'POST':
        # Pasar el colegio al formulario para filtrar los cursos
        form = AdminCrearEstudianteForm(request.POST, colegio=request.colegio)
        if form.is_valid():
            datos = form.cleaned_data
            nombres = datos['nombres']
            apellidos = datos['apellidos']
            curso = datos['curso']

            primer_nombre = unidecode(nombres.split(' ')[0].lower())
            primer_apellido = unidecode(apellidos.split(' ')[0].lower())
            username_base = f"{slugify(primer_nombre)}.{slugify(primer_apellido)}"
            
            username_final = username_base
            counter = 1
            while User.objects.filter(username=username_final).exists():
                username_final = f"{username_base}{counter}"
                counter += 1

            password_provisional = username_final

            nuevo_usuario = User.objects.create_user(
                username=username_final,
                password=password_provisional,
                first_name=nombres,
                last_name=apellidos
            )
            try:
                grupo_estudiantes, _ = Group.objects.get_or_create(name='Estudiantes')
                nuevo_usuario.groups.add(grupo_estudiantes)
            except ObjectDoesNotExist:
                messages.error(request, "Error crítico: El grupo 'Estudiantes' no fue encontrado.")
                return redirect('notas:crear_estudiante')

            # 👇 ASOCIACIÓN: Crear el estudiante para el colegio actual
            nuevo_estudiante = Estudiante.objects.create(user=nuevo_usuario, curso=curso, colegio=request.colegio)
            FichaEstudiante.objects.create(
                estudiante=nuevo_estudiante,
                tipo_documento=datos.get('tipo_documento'),
                numero_documento=datos.get('numero_documento')
            )

            success_message = (
                f"¡Estudiante '{apellidos}, {nombres}' creado con éxito!<br>"
                f"<strong>Usuario:</strong> {username_final}<br>"
                f"<strong>Contraseña Provisional:</strong> {password_provisional}"
            )
            messages.success(request, success_message, extra_tags='safe')
            return redirect('notas:editar_estudiante', estudiante_id=nuevo_estudiante.id)
    else:
        # Pasar el colegio al formulario para filtrar los cursos
        form = AdminCrearEstudianteForm(colegio=request.colegio)
    
    context = {'form': form, 'titulo': "Crear Nuevo Estudiante", 'colegio': request.colegio}
    return render(request, 'notas/admin_crud/formulario_estudiante.html', context)


@login_required
@transaction.atomic
def editar_estudiante_vista(request, estudiante_id):
    if not request.colegio:
        return HttpResponseNotFound("<h1>Colegio no configurado</h1>")
        
    # 👇 FILTRADO: Obtener el estudiante solo si pertenece al colegio actual
    estudiante = get_object_or_404(Estudiante, id=estudiante_id, colegio=request.colegio)
    
    if not (es_personal_admin(request.user) or request.user.id == estudiante.user.id):
        raise PermissionDenied

    ficha, created = FichaEstudiante.objects.get_or_create(estudiante=estudiante)
    if request.method == 'POST':
        # Pasar el colegio al formulario para filtrar el curso
        form = AdminEditarEstudianteForm(request.POST, request.FILES, instance=ficha, colegio=request.colegio)
        if form.is_valid():
            form.save()
            messages.success(request, f"¡Ficha actualizada con éxito!")
            return redirect('notas:dashboard' if request.user.id == estudiante.user.id else 'notas:gestion_estudiantes')
    else:
        # Pasar el colegio al formulario para filtrar el curso
        form = AdminEditarEstudianteForm(instance=ficha, colegio=request.colegio)
        
    context = { 'form': form, 'titulo': "Editar Estudiante", 'estudiante': estudiante, 'colegio': request.colegio }
    return render(request, 'notas/admin_crud/formulario_estudiante.html', context)


@user_passes_test(es_personal_admin)
@require_POST
def eliminar_estudiante_vista(request, estudiante_id):
    if not request.colegio:
        return HttpResponseNotFound("<h1>Colegio no configurado</h1>")
        
    # 👇 FILTRADO: Asegurarse de que solo se puede eliminar un estudiante del colegio actual
    estudiante = get_object_or_404(Estudiante, id=estudiante_id, colegio=request.colegio)
    estudiante.user.delete()
    messages.success(request, f"Estudiante '{estudiante.user.get_full_name()}' ha sido eliminado permanentemente.")
    return redirect('notas:gestion_estudiantes')
