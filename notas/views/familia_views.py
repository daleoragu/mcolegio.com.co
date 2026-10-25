"""Hermanos: el acudiente une a sus hijos y cambia de uno a otro; la secretaría une a los que sugiere la plataforma."""
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.db.models import Count, Q
from django.http import HttpResponseNotFound
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .. import familia as logica
from ..models import Estudiante, Familia
from ..permisos import admin_requerido

INTENTOS = 5                    # «Agregar otro hijo» con clave equivocada: tantas veces cada 15 minutos


def _mi_estudiante(request):
    return Estudiante.objects.filter(user=request.user, colegio=request.colegio).select_related('curso').first()


@login_required
def mi_familia(request):
    yo = _mi_estudiante(request)
    if yo is None:
        return HttpResponseNotFound('<h1>Esta página es para las cuentas de estudiantes.</h1>')
    if request.method == 'POST' and request.POST.get('accion') == 'agregar':
        clave_intentos = f'familia-intentos:{request.user.id}'
        intentos = cache.get(clave_intentos, 0)
        usuario = (request.POST.get('usuario') or '').strip()
        if intentos >= INTENTOS:
            messages.error(request, 'Ha intentado varias veces. Espere 15 minutos y vuelva a intentarlo.')
        elif not usuario or usuario == request.user.username:
            messages.error(request, 'Escriba el usuario del otro hijo.')
        else:
            otro_user = authenticate(request, username=usuario, password=request.POST.get('clave') or '')
            otro = (Estudiante.objects.filter(user=otro_user, colegio=request.colegio, is_active=True).first()
                    if otro_user else None)
            if otro is None:
                cache.set(clave_intentos, intentos + 1, 15 * 60)
                messages.error(request, 'El usuario o la clave no son correctos, o ese estudiante no es de este colegio.')
            else:
                logica.unir([yo, otro])
                messages.success(request, f'Listo: {otro} quedó en su familia. Ahora le llegan los avisos de los dos.')
        return redirect('notas:mi_familia')
    if request.method == 'POST' and request.POST.get('accion') == 'separar':
        quien = get_object_or_404(Estudiante, pk=request.POST.get('estudiante'), colegio=request.colegio)
        if quien.pk == yo.pk or (yo.familia_id and quien.familia_id == yo.familia_id):
            logica.separar(quien)
            messages.success(request, f'{quien} ya no está en esta familia.')
        return redirect('notas:mi_familia')
    return render(request, 'notas/familia/mi_familia.html', {
        'colegio': request.colegio, 'yo': yo, 'hermanos': logica.hermanos(yo)})


@login_required
@require_POST
def cambiar_de_hijo(request, pk):
    """Entra a la cuenta de un hermano sin clave: ya se probó que es de la misma familia."""
    yo = _mi_estudiante(request)
    otro = get_object_or_404(Estudiante, pk=pk, colegio=request.colegio, is_active=True)
    if yo is None or not yo.familia_id or otro.familia_id != yo.familia_id or otro.pk == yo.pk:
        messages.error(request, 'No se puede cambiar a esa cuenta.')
        return redirect('notas:dashboard')
    # Si un administrador está «viendo como» este estudiante, sigue en modo «ver como» con el hermano:
    # login() limpia la sesión, así que se vuelve a guardar quién era el administrador.
    original = request.session.get('original_user_id')
    login(request, otro.user, backend='django.contrib.auth.backends.ModelBackend')
    if original:
        request.session['original_user_id'] = original
    messages.success(request, f'Ahora está viendo a {otro.user.get_full_name() or otro.user.username}.')
    return redirect('notas:dashboard')


@admin_requerido
def familias(request):
    colegio = request.colegio
    if request.method == 'POST':
        accion = request.POST.get('accion')
        if accion == 'unir':
            ids = request.POST.getlist('estudiantes')
            grupo = list(Estudiante.objects.filter(pk__in=ids, colegio=colegio))
            if len(grupo) >= 2:
                logica.unir(grupo)
                messages.success(request, 'Hermanos unidos: ' + ', '.join(str(e) for e in grupo) + '.')
            else:
                messages.error(request, 'Escoja al menos dos estudiantes.')
        elif accion == 'unir_manual':
            buscados = [(request.POST.get(k) or '').strip() for k in ('uno', 'dos')]
            grupo = []
            for b in buscados:
                e = (Estudiante.objects.filter(colegio=colegio)
                     .filter(Q(user__username__iexact=b) | Q(ficha__numero_documento=b)).first()) if b else None
                if e is None:
                    messages.error(request, f'No se encontró un estudiante con el usuario o documento «{b}».')
                    return redirect('notas:familias')
                grupo.append(e)
            if grupo[0].pk == grupo[1].pk:
                messages.error(request, 'Son el mismo estudiante.')
            else:
                logica.unir(grupo)
                messages.success(request, f'Hermanos unidos: {grupo[0]} y {grupo[1]}.')
        elif accion == 'separar':
            e = get_object_or_404(Estudiante, pk=request.POST.get('estudiante'), colegio=colegio)
            logica.separar(e)
            messages.success(request, f'{e} salió de su familia.')
        return redirect('notas:familias')
    existentes = (Familia.objects.filter(colegio=colegio).annotate(n=Count('miembros')).filter(n__gte=2)
                  .prefetch_related('miembros__user', 'miembros__curso').order_by('-creada'))
    return render(request, 'notas/familia/familias.html', {
        'colegio': colegio, 'sugerencias': logica.sugerencias(colegio), 'familias': existentes})
