# notas/views/dashboard_views.py
# CORRECCIÓN: Se ha añadido el namespace 'notas:' a todas las funciones redirect.

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from ..models import Estudiante, Docente
from django.http import HttpResponseNotFound
from ..permisos import es_admin, es_admin_usuario

def es_admin_o_superusuario(user):
    """
    Verifica si el usuario es superusuario o pertenece al grupo de administradores del colegio.
    Asegúrate de tener un grupo llamado 'AdminColegio'.
    """
    if not user.is_authenticated:
        return False
    return es_admin_usuario(user)

@login_required
def dashboard_vista(request):
    """
    Redirige a los usuarios al panel correspondiente según su rol.
    """
    if not request.colegio:
        return HttpResponseNotFound("<h1>Colegio no configurado para este dominio.</h1>")

    if not request.user.is_authenticated:
        # CORREGIDO: Se añade el namespace 'notas:'
        return redirect('notas:logout')
    
    if es_admin_o_superusuario(request.user):
        # CORREGIDO: Se añade el namespace 'notas:'
        return redirect('notas:admin_dashboard')
    
    if Docente.objects.filter(user=request.user, colegio=request.colegio).exists():
        # CORREGIDO: Se añade el namespace 'notas:'
        return redirect('notas:panel_docente')

    if Estudiante.objects.filter(user=request.user, colegio=request.colegio).exists():
        # CORREGIDO: Se añade el namespace 'notas:'
        return redirect('notas:panel_estudiante') 

    return render(request, 'notas/dashboard.html', {'colegio': request.colegio})


@login_required
@user_passes_test(es_admin_o_superusuario)
def admin_dashboard_vista(request):
    """
    Muestra el panel de administración principal.
    """
    if not request.colegio:
        return HttpResponseNotFound("<h1>Colegio no configurado.</h1>")
    
    user_is_also_docente = Docente.objects.filter(user=request.user, colegio=request.colegio).exists()
    
    context = {
        'colegio': request.colegio,
        'user_is_also_docente': user_is_also_docente
    }
    return render(request, 'notas/admin_tools/admin_dashboard.html', context)


@login_required
def docente_dashboard_vista(request):
    """
    Muestra el panel principal para el docente.
    """
    if not request.colegio:
        return HttpResponseNotFound("<h1>Colegio no configurado.</h1>")

    if not (es_admin(request) or Docente.objects.filter(user=request.user, colegio=request.colegio).exists()):
        # CORREGIDO: Se añade el namespace 'notas:'
        return redirect('notas:dashboard')

    context = {
        'colegio': request.colegio
    }
    return render(request, 'notas/docente/dashboard_docente.html', context)


@login_required
def estudiante_dashboard_vista(request):
    """
    Muestra el panel principal para el estudiante.
    """
    if not request.colegio:
        return HttpResponseNotFound("<h1>Colegio no configurado.</h1>")
        
    try:
        estudiante = Estudiante.objects.get(user=request.user, colegio=request.colegio)
        context = {
            'estudiante': estudiante,
            'colegio': request.colegio
        }
    except Estudiante.DoesNotExist:
        context = {
            'estudiante': None,
            'colegio': request.colegio
        }
        
    return render(request, 'notas/estudiante/panel_estudiante.html', context)
