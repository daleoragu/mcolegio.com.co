"""Copia de seguridad: la persona escoge Drive, OneDrive o descargarla, y cada cuánto se la recuerda."""
import json

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import FileResponse, JsonResponse
from django.shortcuts import redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from .armar import armar
from .models import AjusteCopia


def _ajuste(user, crear=False):
    a = AjusteCopia.objects.filter(usuario=user).first()
    if a is None:
        a = AjusteCopia(usuario=user)
        if crear:
            a.save()
    return a


def pendiente_para(user):
    """Días de atraso si la persona activó copias periódicas y ya le toca; None si no."""
    a = AjusteCopia.objects.filter(usuario=user).first()
    if a is None or not a.cada_dias:
        return None
    if a.ultima is None:
        return 0
    dias = (timezone.now() - a.ultima).days
    return dias if dias >= a.cada_dias else None


def _nubes():
    google = bool(getattr(settings, 'GOOGLE_CLIENT_ID', ''))
    onedrive = bool(getattr(settings, 'MICROSOFT_CLIENT_ID', ''))
    return {'google': google, 'onedrive': onedrive}


@login_required
def inicio(request):
    a = _ajuste(request.user)
    nubes = _nubes()
    if not nubes.get(a.destino, a.destino == 'descarga'):
        a.destino = 'google' if nubes['google'] else ('onedrive' if nubes['onedrive'] else 'descarga')
    volver = request.GET.get('volver') or ''
    if not volver.startswith('/') or volver.startswith('//'):
        volver = '/salon_digital/panel/' if getattr(request, 'colegio', None) is None else '/'
    return render(request, 'copias/inicio.html', {
        'a': a, 'nubes': nubes, 'ahora': request.GET.get('ahora') == '1', 'volver': volver,
        'cfg': {'generar': '/copias/archivo.zip', 'hecha': '/copias/hecha/', 'ayudante': '/nube/PROV/',
                'destino': a.destino, 'medios': a.incluir_medios,
                'nombre': f'mcolegio-copia-{timezone.localdate():%Y-%m-%d}.zip'}})


@require_POST
@login_required
def ajustes(request):
    a = _ajuste(request.user, crear=True)
    destino = request.POST.get('destino')
    if destino in dict(AjusteCopia.DESTINOS):
        a.destino = destino
    try:
        cada = int(request.POST.get('cada_dias', a.cada_dias))
    except ValueError:
        cada = a.cada_dias
    if cada in dict(AjusteCopia.FRECUENCIAS):
        a.cada_dias = cada
    a.incluir_medios = request.POST.get('medios') == 'on'
    a.save()
    messages.success(request, 'Ajustes de la copia guardados.')
    return redirect(f'/copias/?volver={request.POST.get("volver") or ""}')


@login_required
def archivo(request):
    medios = request.GET.get('medios', '1') == '1'
    archivo_zip, tam = armar(request.user, medios=medios)
    r = FileResponse(archivo_zip, content_type='application/zip', as_attachment=True,
                     filename=f'mcolegio-copia-{timezone.localdate():%Y-%m-%d}.zip')
    r['Content-Length'] = str(tam)
    r['Cache-Control'] = 'no-store'
    return r


@require_POST
@login_required
def hecha(request):
    try:
        d = json.loads(request.body or '{}')
    except ValueError:
        d = {}
    a = _ajuste(request.user, crear=True)
    a.ultima = timezone.now()
    a.ultimo_destino = d.get('destino') if d.get('destino') in dict(AjusteCopia.DESTINOS) else 'descarga'
    try:
        a.ultimo_peso = max(0, int(d.get('peso') or 0))
    except (TypeError, ValueError):
        a.ultimo_peso = 0
    a.save(update_fields=['ultima', 'ultimo_destino', 'ultimo_peso'])
    return JsonResponse({'ok': True, 'ultima': timezone.localtime(a.ultima).strftime('%d/%m/%Y %I:%M %p').lower()})


@login_required
def pendiente(request):
    dias = pendiente_para(request.user)
    return JsonResponse({'pendiente': dias is not None, 'dias': dias or 0})
