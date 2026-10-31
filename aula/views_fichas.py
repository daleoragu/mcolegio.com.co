"""Fichas de Mis materiales que el estudiante resuelve en el aula: se califican solas y el docente revisa lo abierto."""
from datetime import timedelta
from decimal import Decimal

from django.contrib import messages
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone

from materiales import bloques as MB
from materiales import calificar as C
from materiales import exportar as X

from . import logica
from .models import Entrega, Tarea
from .views import _clave, _ctx, _no_es_para, _persona, _render, vista_aula


def _bloques(tarea, semilla):
    """Los bloques listos para pintar: numerados, con los rangos de los contextos y lo mezclado."""
    bloques, total = X._numerar([dict(b) for b in (tarea.ficha or {}).get('bloques', [])])
    for b in bloques:
        if b['tipo'] != 'pregunta':
            continue
        X._preparar_pregunta(b, 'normal')
        if b['modo'] == 'emparejar':
            orden = C.mezclar(b['pares'], f"{b['id']}-{semilla}")
            b['opciones_der'] = [('abcdefghijkl'[k], b['pares'][j][1], j) for k, j in enumerate(orden)]
        elif b['modo'] == 'ordenar':
            orden = C.mezclar(b['elementos'], f"{b['id']}-{semilla}")
            b['inicial'] = [(j, b['elementos'][j]) for j in orden]
        elif b['modo'] == 'clasificar':
            elementos = C.elementos_clasificar(b)
            orden = C.mezclar(elementos, f"{b['id']}-{semilla}")
            b['tarjetas'] = [(j, elementos[j][0], '') for j in orden]
        elif b['modo'] == 'completar':
            partes, respuestas = MB.huecos(b.get('texto'))
            b['huecos'] = [(p, i if i < len(respuestas) else None, '') for i, p in enumerate(partes)]
        if b['modo'] == 'emparejar':
            b['izq_mias'] = [(n, t, '') for n, t in b['izquierda']]
    return bloques, total


def _rellenar(bloques, respuestas, res):
    """Pone en cada pregunta lo que respondió el estudiante, listo para la plantilla."""
    for b in bloques:
        if b['tipo'] != 'pregunta':
            continue
        r = respuestas.get(b['id'])
        b['mia'] = r
        b['res'] = res['detalle'].get(b['id']) if res else None
        if b['modo'] == 'completar':
            valores = list(r or [])
            b['huecos'] = [(p, i, valores[i] if i is not None and i < len(valores) else '') for p, i, _ in b['huecos']]
        elif b['modo'] == 'emparejar':
            r = r or {}
            b['izq_mias'] = [(n, t, str(r.get(str(n - 1), ''))) for n, t in b['izquierda']]
        elif b['modo'] == 'clasificar':
            r = r or {}
            b['tarjetas'] = [(j, t, str(r.get(str(j), ''))) for j, t, _ in b['tarjetas']]
        elif b['modo'] == 'ordenar' and r:
            elementos = b.get('elementos') or []
            b['inicial'] = [(j, elementos[j]) for j in r if 0 <= j < len(elementos)]


def _config(t):
    c = dict(t.ficha_config or {})
    c.setdefault('modo', 'puntos')
    c.setdefault('intentos', 1)
    c.setdefault('tiempo', 0)
    c.setdefault('mostrar', 'al_terminar')
    return c


def _resultado(t, e):
    return C.calificar(t.ficha, e.respuestas, e.manuales)


def _poner_nota(aula, t, e, res):
    """Pone la nota si ya no queda nada por revisar (y si la ficha da nota)."""
    minima, maxima = logica.rango(aula)
    if _config(t)['modo'] == 'formativa' or res['pendientes']:
        e.nota = None
        e.estado = 'entregada'
        e.calificada = None
        return
    e.nota = C.a_la_escala(res['obtenidos'], res['posibles'], minima, maxima)
    e.estado = 'calificada'
    e.calificada = timezone.now()


@vista_aula
def ficha(request, pk, tid):
    c = _ctx(request, pk)
    aula = c.aula
    t = get_object_or_404(Tarea, pk=tid, aula=aula)
    if not t.ficha:
        raise Http404
    _no_es_para(c, t)
    config = _config(t)
    if c.es_docente:
        bloques, total = _bloques(t, 'docente')
        return _render(request, c, 'aula/ficha.html', {'t': t, 'bloques': bloques, 'total': total, 'config': config,
                                                         'previa': True}, 'tareas')
    if not t.publicada:
        raise Http404
    persona = c.estudiante or c.integrante
    e = logica.entrega_de(t, persona)
    semilla = _clave(persona)
    agotados = e is not None and config['intentos'] and e.intentos >= config['intentos']
    cerrada = t.vencida and not t.acepta_tardias
    if request.method == 'POST':
        if agotados or cerrada:
            messages.warning(request, 'Ya no puede enviar esta ficha.')
            return redirect('aula:ficha', pk=pk, tid=tid)
        e = e or Entrega(tarea=t, **logica.filtro_persona(persona))
        respuestas = C.leer_respuestas(t.ficha, request.POST)
        nueva = C.calificar(t.ficha, respuestas)
        anterior = C.calificar(t.ficha, e.respuestas, e.manuales) if e.pk and e.respuestas else None
        # Con varios intentos queda el mejor.
        if anterior is None or nueva['obtenidos'] >= anterior['obtenidos']:
            e.respuestas = respuestas
            e.manuales = {}
            _poner_nota(aula, t, e, nueva)
        e.intentos += 1
        e.entregada = timezone.now()
        e.tardia = bool(t.fecha_limite and timezone.now() > t.fecha_limite)
        e.iniciada = None
        e.save()
        messages.success(request, 'Ficha enviada.')
        return redirect('aula:ficha', pk=pk, tid=tid)
    terminada = e is not None and e.intentos > 0
    if request.GET.get('otra') == '1' and terminada and not agotados and not cerrada:
        terminada = False
    if not terminada and not cerrada:
        e = e or Entrega(tarea=t, **logica.filtro_persona(persona), estado='entregada')
        if e.iniciada is None:
            e.iniciada = timezone.now()
            e.save()
    bloques, total = _bloques(t, semilla)
    datos = {'t': t, 'bloques': bloques, 'total': total, 'config': config, 'e': e, 'terminada': terminada,
             'cerrada': cerrada, 'agotados': agotados}
    if terminada:
        res = _resultado(t, e)
        datos['res'] = res
        datos['mostrar'] = config['mostrar'] == 'al_terminar'
        datos['quedan'] = (config['intentos'] - e.intentos) if config['intentos'] else None
        datos['nota_provisional'] = None
        _rellenar(bloques, e.respuestas, res)
    elif config['tiempo'] and e is not None and e.iniciada:
        fin = e.iniciada + timedelta(minutes=config['tiempo'])
        datos['segundos'] = max(0, int((fin - timezone.now()).total_seconds()))
    return _render(request, c, 'aula/ficha.html', datos, 'tareas')


@vista_aula
def ficha_revisar(request, pk, tid, clave):
    c = _ctx(request, pk, docente=True)
    aula = c.aula
    t = get_object_or_404(Tarea, pk=tid, aula=aula)
    if not t.ficha:
        raise Http404
    persona = _persona(aula, clave)
    e = logica.entrega_de(t, persona)
    if e is None or not e.intentos:
        messages.info(request, 'Este estudiante todavía no ha enviado la ficha.')
        return redirect('aula:tarea', pk=pk, tid=tid)
    preguntas = {b['id']: b for b in C.preguntas(t.ficha)}
    if request.method == 'POST':
        manuales = {}
        for bid in preguntas:
            v = (request.POST.get(f'p-{bid}') or '').strip().replace(',', '.')
            if v:
                try:
                    manuales[bid] = str(Decimal(v))
                except Exception:
                    continue
        e.manuales = manuales
        e.comentario = (request.POST.get('comentario') or '').strip()[:3000]
        _poner_nota(aula, t, e, _resultado(t, e))
        e.save()
        messages.success(request, f'Ficha revisada{": nota " + str(e.nota) if e.nota is not None else ""}.')
        return redirect('aula:tarea', pk=pk, tid=tid)
    res = _resultado(t, e)
    bloques, total = _bloques(t, _clave(persona))
    _rellenar(bloques, e.respuestas, res)
    for b in bloques:
        if b['tipo'] == 'pregunta':
            b['manual'] = e.manuales.get(b['id'], '')
    minima, maxima = logica.rango(aula)
    return _render(request, c, 'aula/ficha.html', {
        't': t, 'bloques': bloques, 'total': total, 'config': _config(t), 'e': e, 'res': res, 'revisar': True,
        'terminada': True, 'mostrar': True, 'nombre': logica.nombre_de(persona), 'clave': clave,
        'nota_provisional': C.a_la_escala(res['obtenidos'], res['posibles'], minima, maxima)}, 'tareas')


@vista_aula
def ficha_imagen(request, pk, tid, iid):
    """Las imágenes de la ficha son del docente: el estudiante las ve solo si están en esa ficha."""
    c = _ctx(request, pk)
    t = get_object_or_404(Tarea, pk=tid, aula=c.aula)
    _no_es_para(c, t)
    usadas = {b.get('imagen') for b in (t.ficha or {}).get('bloques', []) if b.get('imagen')}
    if iid not in usadas:
        raise Http404
    from materiales.models import Imagen
    img = get_object_or_404(Imagen, pk=iid)
    return redirect(img.archivo.url)
