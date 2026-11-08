"""Botón «Compartir»: con una de mis clases (toda o algunos estudiantes) o con un colega, y «Compartido conmigo»."""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from . import compartir as CP
from . import logica
from .models import CompartidoDocente


def _avisar(destino, texto, url):
    from chat.views_colegas import avisar
    avisar(destino, texto, url)


def _nombre(u):
    from chat.views_colegas import nombre_de
    return nombre_de(u)


def _base(request):
    return 'notas/base.html' if getattr(request, 'colegio', None) is not None else 'aula/base_salon.html'


def _aulas_json(request, excluir=None):
    return [{'id': x.pk, 'nombre': f'{x.titulo} · {x.subtitulo}' if x.subtitulo else x.titulo}
            for x in CP.mis_aulas(request) if x.pk != excluir]


@login_required
def compartir(request, tipo, oid):
    """GET: a dónde se puede compartir (JSON para la ventana). POST: compartir con una clase o con un colega."""
    obj = CP.objeto(request, tipo, oid)
    titulo = CP.titulo_de(tipo, obj)
    origen = getattr(obj, 'aula_id', None)
    if request.method == 'GET':
        return JsonResponse({'titulo': titulo, 'tipo': CP.TIPOS[tipo], 'copiable': CP.se_puede_copiar(tipo, obj),
                             'aulas': _aulas_json(request, origen), 'colegas': CP.colegas(request),
                             'para_todos': CP.para_todos(tipo, obj)})
    if not CP.se_puede_copiar(tipo, obj):
        return JsonResponse({'ok': False, 'error': 'Este taller es un sitio completo (.zip): compártalo con su enlace.'}, status=400)
    if request.POST.get('destino') == 'colega':
        validos = {c['id'] for c in CP.colegas(request)}
        try:
            uid = int(request.POST.get('usuario') or 0)
        except ValueError:
            uid = 0
        if uid not in validos:
            return JsonResponse({'ok': False, 'error': 'Escoja uno de sus colegas.'}, status=400)
        otro = User.objects.get(pk=uid)
        envio = CompartidoDocente.objects.create(de=request.user, para=otro, tipo=tipo, objeto_id=obj.pk, titulo=titulo[:200],
                                                 mensaje=' '.join((request.POST.get('mensaje') or '').split())[:300])
        _avisar(otro, f'{_nombre(request.user)} compartió con usted {CP.TIPOS[tipo].lower()}: «{titulo[:80]}».',
                f'/aula/compartidos/#c{envio.pk}')
        return JsonResponse({'ok': True, 'mensaje': f'Listo: {_nombre(otro)} lo recibe en «Compartido conmigo» y lo agrega a su clase.'})
    aula, para, error = CP.leer_destino(request, con_para=not CP.para_todos(tipo, obj))
    if error:
        return JsonResponse({'ok': False, 'error': error}, status=400)
    nuevo, url = CP.copiar(tipo, obj, aula, para, request.user, request)
    if tipo == 'muro' and obj.autor_id != request.user.pk:
        _avisar(obj.autor, f'{_nombre(request.user)} llevó su publicación «{titulo[:70]}» a una de sus clases. ¡Gracias por compartir!',
                f'/chat/colegas/muro/{obj.pk}/')
    if tipo != 'publicacion':
        logica.avisar_estudiantes(aula, f'{aula.titulo}: nuevo {CP.TIPOS[tipo].lower()} «{titulo[:60]}»',
                                  request.build_absolute_uri(url), para or None)
    quienes = f'{len(para)} estudiante(s)' if para else 'toda la clase'
    return JsonResponse({'ok': True, 'url': url, 'mensaje': f'Compartido con {aula.titulo} ({quienes}).'})


@login_required
def estudiantes(request, pk):
    """Los estudiantes de una de mis clases, para escoger a quién va."""
    aula = next((x for x in CP.mis_aulas(request) if x.pk == pk), None)
    if aula is None:
        raise Http404
    return JsonResponse({'estudiantes': logica.opciones_para(aula)})


@login_required
def compartidos(request):
    """Lo que otros docentes compartieron conmigo: agregarlo a una de mis clases (toda o algunos estudiantes)."""
    if request.method == 'POST':
        envio = get_object_or_404(CompartidoDocente, pk=request.POST.get('compartido') or 0, para=request.user)
        if request.POST.get('accion') == 'quitar':
            envio.delete()
            messages.info(request, 'Quitado de «Compartido conmigo».')
            return redirect('aula:compartidos')
        try:
            obj = CP.objeto(request, envio.tipo, envio.objeto_id, recibido=True)
        except Http404:
            messages.error(request, 'Su autor ya lo borró: no se puede agregar.')
            return redirect('aula:compartidos')
        aula, para, error = CP.leer_destino(request, con_para=not CP.para_todos(envio.tipo, obj))
        if error:
            messages.error(request, error)
            return redirect('aula:compartidos')
        nuevo, url = CP.copiar(envio.tipo, obj, aula, para, request.user, request)
        envio.usado = timezone.now()
        envio.save(update_fields=['usado'])
        _avisar(envio.de, f'{_nombre(request.user)} agregó «{envio.titulo[:80]}» a su clase {aula.titulo}. ¡Gracias por compartir!', '/aula/')
        messages.success(request, f'«{envio.titulo}» quedó en {aula.titulo}.')
        return redirect(url)
    from notas.models import Notificacion
    Notificacion.objects.filter(destinatario=request.user, url__startswith='/aula/compartidos/', leido=False).update(leido=True)
    recibidos = list(CompartidoDocente.objects.filter(para=request.user).select_related('de'))
    for e in recibidos:
        e.de_nombre = _nombre(e.de)
        try:
            e.para_todos = CP.para_todos(e.tipo, CP.objeto(request, e.tipo, e.objeto_id, recibido=True))
        except Http404:
            e.para_todos = True
    return render(request, 'aula/compartidos.html', {'recibidos': recibidos, 'aulas': _aulas_json(request), 'base': _base(request)})
