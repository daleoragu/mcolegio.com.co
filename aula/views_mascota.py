"""Mascota académica: adoptar, atenderla respondiendo preguntas y el tablero de la clase."""
from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import redirect
from django.views.decorators.http import require_POST

from . import logica, mascota as MA
from .models import MascotaAula
from .views import _Prohibido, _ctx, _render, vista_aula
from .views_gamificacion import validar_preguntas


def _persona(c):
    return c.estudiante or c.integrante


def _mia(c):
    return MA.de_persona(c.aula, _persona(c))


@vista_aula
def mascota(request, pk):
    c = _ctx(request, pk)
    aula = c.aula
    if c.es_docente:
        if request.method == 'POST':
            texto = (request.POST.get('preguntas') or '').strip()
            if texto:
                preguntas, error = validar_preguntas(texto)
                if error:
                    messages.warning(request, error)
                    return redirect('aula:mascota', pk=pk)
            else:
                preguntas = []
            aula.texto_preguntas_mascota, aula.preguntas_mascota = texto[:60000], preguntas
            aula.save(update_fields=['texto_preguntas_mascota', 'preguntas_mascota'])
            if request.POST.get('todos') and aula.es_salon and aula.grupo_id:
                from .models import Aula
                n = (Aula.objects.filter(grupo__propietario_id=aula.grupo.propietario_id).exclude(pk=aula.pk)
                     .update(texto_preguntas_mascota=texto[:60000], preguntas_mascota=preguntas))
                if n:
                    messages.info(request, f'También quedaron en las mascotas de sus otros {n} grupo(s).')
            messages.success(request, f'Las mascotas de la clase usarán {len(preguntas)} pregunta(s) suyas.' if preguntas
                             else 'Sin preguntas propias: las mascotas usan las de los juegos de la clase (o las de prueba).')
            return redirect('aula:mascota', pk=pk)
        return _render(request, c, 'aula/mascota.html', {
            'tablero': MA.ranking(aula, n=None), 'n_banco': len(MA.banco(aula)), 'propias': len(aula.preguntas_mascota or []),
            'colegio_unica': bool(aula.colegio_id and aula.asignacion_id)},
            'gamificacion')
    if _persona(c) is None:
        raise _Prohibido('La mascota es de cada estudiante.')
    m = _mia(c)
    if request.method == 'POST' and m is None:
        m = MA.nueva(aula, _persona(c), request.POST.get('especie'), request.POST.get('nombre'))
        messages.success(request, f'¡Bienvenido, {m.nombre}! Cuídelo respondiendo preguntas.')
        return redirect('aula:mascota', pk=pk)
    if m is not None:
        MA.actualizar(m)
    from django.middleware.csrf import get_token
    from django.urls import reverse
    config = None
    if m is not None:
        config = {'estado': MA.estado(m), 'csrf': get_token(request),
                  'urlPedir': reverse('aula:mascota_pedir', args=[pk]), 'urlResponder': reverse('aula:mascota_responder', args=[pk]),
                  'urlEstado': reverse('aula:mascota_estado', args=[pk]), 'urlPartida': reverse('aula:mascota_partida', args=[pk]),
                  'urlLogica': reverse('aula:logica', args=[pk])}
    return _render(request, c, 'aula/mascota.html', {
        'm': m, 'ms_config': config, 'especies': MascotaAula.ESPECIES,
        'tablero': MA.ranking(aula, n=10)}, 'gamificacion')


@require_POST
@vista_aula
def mascota_pedir(request, pk):
    c = _ctx(request, pk)
    m = _mia(c)
    if m is None:
        return JsonResponse({'ok': False, 'mensaje': 'Primero adopte una mascota.'})
    pregunta, mensaje = MA.pedir(m, request.POST.get('accion'), logica.clave_de(_persona(c)))
    return JsonResponse({'ok': pregunta is not None, 'pregunta': pregunta, 'mensaje': mensaje, 'estado': MA.estado(m)})


@require_POST
@vista_aula
def mascota_responder(request, pk):
    c = _ctx(request, pk)
    m = _mia(c)
    if m is None:
        return JsonResponse({'ok': False})
    try:
        opcion = int(request.POST.get('opcion'))
    except (TypeError, ValueError):
        opcion = -1
    bien, correcta, mensaje = MA.responder(m, opcion)
    return JsonResponse({'ok': bien is not None, 'bien': bool(bien), 'correcta': correcta, 'mensaje': mensaje,
                         'estado': MA.estado(m)})


@vista_aula
def mascota_estado(request, pk):
    c = _ctx(request, pk)
    m = _mia(c)
    if m is None:
        return JsonResponse({'ok': False})
    MA.actualizar(m)
    return JsonResponse({'ok': True, 'estado': MA.estado(m)})


@require_POST
@vista_aula
def mascota_partida(request, pk):
    """Fin de una partida del minijuego «Atrapa estrellas»."""
    c = _ctx(request, pk)
    m = _mia(c)
    if m is None:
        return JsonResponse({'ok': False})
    subio, mensaje = MA.terminar_partida(m, request.POST.get('estrellas'))
    return JsonResponse({'ok': True, 'subio': subio, 'mensaje': mensaje, 'estado': MA.estado(m)})
