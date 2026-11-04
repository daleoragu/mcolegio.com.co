"""Cabinas de votación ligadas al celular del jurado.

1. En la tableta o computador de la cabina se abre /votaciones/cabina/. No hace
   falta iniciar sesión: el equipo muestra un QR y un código de 6 cifras.
2. El jurado, desde su celular (con su cuenta de docente o directivo), abre
   «Cabinas» de la elección y escanea ese QR: la cabina queda vinculada.
3. El jurado verifica al estudiante y escanea su carné: la cabina abre el
   tarjetón de ese estudiante. Al votar, la cabina vuelve a quedar libre.

El voto sigue siendo secreto: se guarda igual que en la mesa (VotoEmitido sin
por quién, Papeleta sin quién), con medio «cabina» y el jurado que lo habilitó.
"""
import base64
import re
from datetime import timedelta
from io import BytesIO

from django.contrib import messages
from django.db import transaction
from django.db.models import Max
from django.http import Http404, HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from notas.models import Estudiante
from notas.views.carnet_views import codigo_leido

from . import logica as L
from .models import Cabina, Eleccion, VotoEmitido
from .views import _eleccion, _puede_jurado, del_colegio

CLAVE_CABINA = 'votaciones_cabina'       # token de la cabina en la sesión del equipo
VIGENCIA_CODIGO = timedelta(hours=12)    # el código de 6 cifras sirve para vincular por un rato
PATRON_VINCULO = re.compile(r'/votaciones/cabina/v/([A-Za-z0-9_-]{6,16})/?')


def _qr(texto):
    import qrcode
    qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_M, box_size=8, border=2)
    qr.add_data(texto)
    qr.make(fit=True)
    salida = BytesIO()
    qr.make_image(fill_color='black', back_color='white').save(salida, format='PNG')
    return base64.b64encode(salida.getvalue()).decode()


# ---------------------------------------------------------------------------
# La cabina (el equipo donde vota el estudiante)
# ---------------------------------------------------------------------------
def _cabina_del_equipo(request, crear=True):
    if getattr(request, 'colegio', None) is None:
        raise Http404
    token = request.session.get(CLAVE_CABINA)
    cabina = Cabina.objects.filter(token=token, colegio=request.colegio).select_related('eleccion', 'jurado', 'votante').first() \
        if token else None
    if cabina is None and crear:
        cabina = Cabina.objects.create(colegio=request.colegio)
        request.session[CLAVE_CABINA] = cabina.token
    return cabina


def _estado(cabina):
    if cabina.eleccion_id is None or cabina.jurado_id is None:
        return 'sin_vincular'
    if cabina.eleccion.estado != 'abierta':
        return 'cerrada'
    return 'votando' if cabina.votante_id else 'libre'


def cabina(request):
    c = _cabina_del_equipo(request)
    Cabina.objects.filter(pk=c.pk).update(visto_en=timezone.now())
    estado = _estado(c)
    if estado == 'votando':
        tipo, persona = L.votante(c.votante, request.colegio)
        cargos = L.cargos_de(c.eleccion, tipo, persona) if tipo == 'estudiante' else []
        ya = VotoEmitido.objects.filter(eleccion=c.eleccion, usuario=c.votante).exists()
        if not cargos or ya:
            Cabina.objects.filter(pk=c.pk).update(votante=None, asignada_en=None)
            return redirect('votaciones:cabina')
        error = ''
        if request.method == 'POST':
            elegidos = {cargo.pk: request.POST.get(f'cargo-{cargo.pk}') for cargo, _ in cargos}
            try:
                with transaction.atomic():
                    # Solo un voto por asignación, aunque toquen dos veces «Confirmar».
                    fila = Cabina.objects.select_for_update().get(pk=c.pk)
                    if fila.votante_id != c.votante_id:
                        return redirect('votaciones:cabina')
                    L.emitir(c.eleccion, c.votante, tipo, persona, elegidos, medio='cabina', jurado=c.jurado)
                    Cabina.objects.filter(pk=c.pk).update(votante=None, asignada_en=None)
            except L.YaVoto:
                Cabina.objects.filter(pk=c.pk).update(votante=None, asignada_en=None)
                return render(request, 'votaciones/listo.html', {'e': c.eleccion, 'ya': True,
                                                                 'siguiente': reverse('votaciones:cabina')})
            except ValueError as ex:
                error = str(ex)
            else:
                return render(request, 'votaciones/listo.html', {'e': c.eleccion, 'siguiente': reverse('votaciones:cabina')})
        return render(request, 'votaciones/tarjeton.html', {
            'e': c.eleccion, 'cargos': cargos, 'error': error, 'mesa': True, 'cabina': c,
            'quien': c.votante.get_full_name() or c.votante.username, 'curso': getattr(persona, 'curso', None)})
    contexto = {'c': c, 'estado': estado, 'e': c.eleccion}
    if estado == 'sin_vincular':
        url = request.build_absolute_uri(reverse('votaciones:cabina_vincular', args=[c.vinculo]))
        contexto.update({'qr': _qr(url), 'codigo': c.codigo})
    return render(request, 'votaciones/cabina.html', contexto)


def cabina_estado(request):
    """La cabina pregunta cada pocos segundos si ya le asignaron un votante."""
    c = _cabina_del_equipo(request, crear=False)
    if c is None:
        return JsonResponse({'estado': 'sin_cabina'})
    Cabina.objects.filter(pk=c.pk).update(visto_en=timezone.now())
    return JsonResponse({'estado': _estado(c), 'votante': c.votante_id or 0, 'jurado': c.jurado_id or 0})


# ---------------------------------------------------------------------------
# El jurado (en su celular)
# ---------------------------------------------------------------------------
def _cabinas_de(e, jurado):
    salida = []
    for c in e.cabinas.filter(jurado=jurado).select_related('votante'):
        salida.append({'id': c.pk, 'numero': c.numero, 'estado': _estado(c),
                       'votante': (c.votante.get_full_name() or c.votante.username) if c.votante_id else '',
                       'desde': timezone.localtime(c.asignada_en).strftime('%I:%M %p') if c.asignada_en else '',
                       'en_linea': bool(c.visto_en and timezone.now() - c.visto_en < timedelta(seconds=30))})
    return salida


def _vincular(request, e, cabina):
    if cabina.colegio_id != request.colegio.id:
        return {'ok': False, 'nivel': 'error', 'mensaje': 'Esa cabina no es de este colegio.'}
    if cabina.jurado_id and cabina.jurado_id != request.user.id and cabina.eleccion_id == e.pk:
        nombre = cabina.jurado.get_full_name() or cabina.jurado.username
        return {'ok': False, 'nivel': 'warning', 'mensaje': f'Esa cabina ya la maneja {nombre}.'}
    if cabina.eleccion_id != e.pk or not cabina.numero:
        cabina.numero = (e.cabinas.aggregate(m=Max('numero'))['m'] or 0) + 1
    cabina.eleccion, cabina.jurado, cabina.votante, cabina.asignada_en = e, request.user, None, None
    cabina.save(update_fields=['eleccion', 'jurado', 'votante', 'asignada_en', 'numero'])
    return {'ok': True, 'nivel': 'success', 'mensaje': f'Cabina {cabina.numero} vinculada. Ya puede escanear carnés.'}


def _asignar(request, e, est, cabina_id=None):
    nombre = est.user.get_full_name() or est.user.username
    if e.estado != 'abierta':
        return {'ok': False, 'nivel': 'error', 'mensaje': 'La votación no está abierta.'}
    if not est.is_active:
        return {'ok': False, 'nivel': 'error', 'mensaje': f'{nombre} no está activo en el colegio.'}
    if VotoEmitido.objects.filter(eleccion=e, usuario=est.user).exists():
        return {'ok': False, 'nivel': 'warning', 'mensaje': f'{nombre} ya votó.'}
    if not L.cargos_de(e, 'estudiante', est):
        return {'ok': False, 'nivel': 'warning', 'mensaje': f'En esta elección no hay cargos para {nombre}.'}
    en_otra = e.cabinas.filter(votante=est.user).first()
    if en_otra is not None:
        return {'ok': False, 'nivel': 'info', 'mensaje': f'{nombre} ya está votando en la cabina {en_otra.numero}.'}
    with transaction.atomic():
        libres = e.cabinas.select_for_update().filter(jurado=request.user, votante__isnull=True)
        if cabina_id:
            libres = libres.filter(pk=cabina_id)
        cabina = libres.order_by('numero').first()
        if cabina is None:
            return {'ok': False, 'nivel': 'warning',
                    'mensaje': 'No hay cabinas libres. Espere a que terminen de votar.' if e.cabinas.filter(jurado=request.user).exists()
                    else 'Primero vincule una cabina: escanee el QR que muestra la pantalla de la cabina.'}
        cabina.votante, cabina.asignada_en = est.user, timezone.now()
        cabina.save(update_fields=['votante', 'asignada_en'])
    curso = f' ({est.curso.nombre})' if est.curso_id else ''
    return {'ok': True, 'nivel': 'success', 'mensaje': f'{nombre}{curso}: pase a la cabina {cabina.numero}.'}


@del_colegio
def jurado(request, pk):
    e = _eleccion(request, pk)
    if not _puede_jurado(request):
        return HttpResponseForbidden('Las cabinas las maneja un docente o un directivo.')
    return render(request, 'votaciones/jurado.html', {
        'e': e, 'cabinas': _cabinas_de(e, request.user), 'votaron': e.votantes.count(),
        'en_cabinas': e.votantes.filter(medio='cabina', jurado=request.user).count()})


@del_colegio
@require_POST
def jurado_accion(request, pk):
    """Lo que leyó el celular del jurado (QR de la cabina o del carné), o liberar/quitar una cabina."""
    e = _eleccion(request, pk)
    if not _puede_jurado(request):
        return HttpResponseForbidden()
    accion = request.POST.get('accion') or 'leer'
    texto = (request.POST.get('texto') or '').strip()
    if accion == 'ver':
        r = {'ok': True}
    elif accion in ('liberar', 'quitar'):
        c = e.cabinas.filter(pk=request.POST.get('cabina') or 0, jurado=request.user).first()
        if c is None:
            r = {'ok': False, 'nivel': 'error', 'mensaje': 'Cabina no encontrada.'}
        elif accion == 'liberar':
            Cabina.objects.filter(pk=c.pk).update(votante=None, asignada_en=None)
            r = {'ok': True, 'nivel': 'info', 'mensaje': f'Cabina {c.numero} libre (no se guardó ningún voto).'}
        else:
            Cabina.objects.filter(pk=c.pk).update(jurado=None, eleccion=None, votante=None, asignada_en=None, numero=0)
            r = {'ok': True, 'nivel': 'info', 'mensaje': f'Cabina {c.numero} desvinculada.'}
    else:
        m = PATRON_VINCULO.search(texto)
        cabina = None
        if m:
            cabina = Cabina.objects.filter(vinculo=m.group(1), colegio=request.colegio).first()
        elif re.fullmatch(r'\d{6}', texto):
            hace = timezone.now() - VIGENCIA_CODIGO
            cabina = Cabina.objects.filter(colegio=request.colegio, creada__gte=hace, jurado__isnull=True,
                                           codigo=texto).order_by('-creada').first()
        if cabina is not None:
            r = _vincular(request, e, cabina)
        elif m or re.fullmatch(r'\d{6}', texto):
            r = {'ok': False, 'nivel': 'error', 'mensaje': 'No se encontró esa cabina. Recargue la pantalla de la cabina.'}
        else:
            codigo = codigo_leido(texto)
            est = Estudiante.objects.select_related('user', 'curso').filter(
                codigo_carnet=codigo, colegio=request.colegio).first() if codigo else None
            if est is None:
                r = {'ok': False, 'nivel': 'error', 'mensaje': 'Ese QR no es de un carné ni de una cabina del colegio.'}
            else:
                r = _asignar(request, e, est, request.POST.get('cabina'))
    r['cabinas'] = _cabinas_de(e, request.user)
    r['votaron'] = e.votantes.count()
    return JsonResponse(r)


@del_colegio
def vincular_desde_enlace(request, vinculo):
    """El jurado escaneó el QR de la cabina con la cámara normal del celular."""
    if not _puede_jurado(request):
        return HttpResponseForbidden('Las cabinas las vincula un docente o un directivo.')
    cabina = get_object_or_404(Cabina, vinculo=vinculo, colegio=request.colegio)
    abiertas = list(Eleccion.objects.filter(colegio=request.colegio, estado='abierta'))
    # Siempre con un botón (POST): abrir un enlace no basta para vincular una cabina.
    if request.method == 'POST':
        e = next((x for x in abiertas if str(x.pk) == request.POST.get('eleccion')), None)
        if e is not None:
            r = _vincular(request, e, cabina)
            getattr(messages, r['nivel'])(request, r['mensaje'])
            return redirect('votaciones:jurado', pk=e.pk)
    if not abiertas:
        messages.info(request, 'No hay ninguna votación abierta para vincular la cabina.')
        return redirect('votaciones:inicio')
    return render(request, 'votaciones/cabina_vincular.html', {'abiertas': abiertas, 'cabina': cabina})
