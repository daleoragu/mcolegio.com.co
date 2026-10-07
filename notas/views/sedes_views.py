# notas/views/sedes_views.py
"""Sedes del colegio: crearlas, editarlas y ver qué cursos tiene cada una."""
from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.db.models import Count
from django.http import HttpResponseNotFound
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from ..forms import SedeForm
from ..models import Curso, Sede
from ..permisos import es_admin_usuario


@user_passes_test(es_admin_usuario)
def gestion_sedes(request):
    if not request.colegio:
        return HttpResponseNotFound("<h1>Colegio no configurado</h1>")
    sedes = (Sede.objects.filter(colegio=request.colegio)
             .annotate(n_cursos=Count('cursos')).order_by('-es_principal', 'orden', 'nombre'))
    sin_sede = Curso.objects.filter(colegio=request.colegio, sede__isnull=True).order_by('orden', 'nombre')
    return render(request, 'notas/admin_crud/gestion_sedes.html', {
        'sedes': sedes, 'sin_sede': sin_sede, 'colegio': request.colegio,
        'titulo': 'Sedes del colegio',
    })


def _formulario(request, sede=None):
    if request.method == 'POST':
        form = SedeForm(request.POST, request.FILES, instance=sede, colegio=request.colegio)
        if form.is_valid():
            nueva = form.save(commit=False)
            nueva.colegio = request.colegio
            if sede is None and not Sede.objects.filter(colegio=request.colegio).exists():
                nueva.es_principal = True     # la primera que se crea es la principal
            nueva.save()
            # Cursos marcados para esta sede
            ids = [int(i) for i in request.POST.getlist('cursos') if i.isdigit()]
            if 'cursos_enviados' in request.POST:
                Curso.objects.filter(colegio=request.colegio, sede=nueva).exclude(id__in=ids).update(sede=None)
                Curso.objects.filter(colegio=request.colegio, id__in=ids).update(sede=nueva)
            messages.success(request, f'Sede «{nueva.nombre}» guardada.')
            return redirect('notas:gestion_sedes')
    else:
        form = SedeForm(instance=sede, colegio=request.colegio)
    cursos = Curso.objects.filter(colegio=request.colegio).select_related('sede').order_by('orden', 'nombre')
    return render(request, 'notas/admin_crud/sede_form.html', {
        'form': form, 'sede': sede, 'cursos': cursos, 'colegio': request.colegio,
        'titulo': f'Editar sede: {sede.nombre}' if sede else 'Nueva sede',
    })


@user_passes_test(es_admin_usuario)
def crear_sede(request):
    if not request.colegio:
        return HttpResponseNotFound("<h1>Colegio no configurado</h1>")
    return _formulario(request)


@user_passes_test(es_admin_usuario)
def editar_sede(request, sede_id):
    if not request.colegio:
        return HttpResponseNotFound("<h1>Colegio no configurado</h1>")
    return _formulario(request, get_object_or_404(Sede, id=sede_id, colegio=request.colegio))


@user_passes_test(es_admin_usuario)
@require_POST
def eliminar_sede(request, sede_id):
    if not request.colegio:
        return HttpResponseNotFound("<h1>Colegio no configurado</h1>")
    sede = get_object_or_404(Sede, id=sede_id, colegio=request.colegio)
    n = sede.cursos.count()
    nombre = sede.nombre
    sede.delete()      # los cursos quedan sin sede, no se borran
    messages.success(request, f'Se eliminó la sede «{nombre}».'
                     + (f' Sus {n} curso(s) quedaron sin sede.' if n else ''))
    return redirect('notas:gestion_sedes')
