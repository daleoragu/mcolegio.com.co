"""Pantallas del dueño de la plataforma (superusuario), por encima de los colegios."""
from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import get_object_or_404, redirect, render

from ..models import Colegio
from ..modulos import MODULOS, PLANES, activos


def _es_dueno(user):
    return user.is_authenticated and user.is_superuser


@user_passes_test(_es_dueno, login_url='/super-admin/login/')
def modulos_colegios(request):
    """Qué módulos tiene activos cada colegio (lo que contrató)."""
    if request.method == 'POST':
        colegio = get_object_or_404(Colegio, pk=request.POST.get('colegio'))
        plan = request.POST.get('plan')
        if plan in PLANES:
            elegidos = list(PLANES[plan][1])
            texto = f'plan {PLANES[plan][0]}'
        else:
            elegidos = [m for m in MODULOS if request.POST.get(f'mod_{m}')]
            texto = 'módulos guardados'
        colegio.modulos_activos = elegidos
        colegio.save(update_fields=['modulos_activos'])
        messages.success(request, f'{colegio.nombre}: {texto} ({len(elegidos)} de {len(MODULOS)} módulos activos).')
        return redirect(request.path + f'#colegio-{colegio.pk}')
    filas = [{'c': c, 'activos': activos(c)} for c in Colegio.objects.order_by('nombre')]
    return render(request, 'notas/plataforma/modulos.html', {
        'filas': filas, 'modulos': MODULOS, 'planes': PLANES})
