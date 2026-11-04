"""Aula invertida: el docente deja un video y pega las preguntas; el estudiante lo ve y responde."""
from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.db import IntegrityError
from django.http import Http404, JsonResponse
from django.middleware.csrf import get_token
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from . import invertida as INV
from . import logica
from .models import ClaseInvertida, RespuestaInvertida
from .views import _Prohibido, _ctx, _render, _url, vista_aula
from .views_juegos import _datos_planilla, _leer_periodo_componente


def _persona(c):
    return c.estudiante or c.integrante


def _leer_formulario(request, clase, aula):
    """Llena la clase con lo del formulario. Devuelve el error, o ''."""
    clase.titulo = ' '.join((request.POST.get('titulo') or '').split())[:60]
    clase.video = (request.POST.get('video') or '').strip()[:300]
    clase.instrucciones = (request.POST.get('instrucciones') or '').strip()[:3000]
    texto = (request.POST.get('preguntas') or '').strip()
    if not clase.titulo:
        return 'Escriba el título.'
    if not clase.video.startswith(('http://', 'https://')):
        return 'Pegue el enlace del video (por ejemplo https://www.youtube.com/watch?v=…).'
    preguntas = INV.leer_preguntas(texto)
    if not preguntas:
        return 'Pegue al menos una pregunta.'
    if clase.pk and clase.respuestas.exists() and preguntas != clase.preguntas:
        return ('Ya hay estudiantes que respondieron: no se pueden cambiar las preguntas. '
                'Cree otra clase invertida o borre las respuestas primero.')
    clase.texto_preguntas, clase.preguntas = texto[:20000], preguntas
    para, error = logica.leer_para(request, aula)
    if error:
        return error
    clase.para = para
    _leer_periodo_componente(request, clase, aula)
    return ''


@vista_aula
def invertidas(request, pk):
    c = _ctx(request, pk)
    aula = c.aula
    if request.method == 'POST':
        if not c.es_docente:
            raise _Prohibido('Solo el docente crea clases invertidas.')
        clase = ClaseInvertida(aula=aula)
        error = _leer_formulario(request, clase, aula)
        if error:
            messages.warning(request, error)
            request.session['invertida_borrador'] = {k: request.POST.get(k, '') for k in
                                                     ('titulo', 'video', 'instrucciones', 'preguntas')}
            return redirect('aula:invertidas', pk=pk)
        clase.save()
        request.session.pop('invertida_borrador', None)
        logica.avisar_estudiantes(aula, f'{aula.titulo}: nueva clase invertida «{clase.titulo}». Vea el video y responda',
                                  _url(request, 'aula:invertida', aula.pk, clase.pk), clase.para or None)
        messages.success(request, f'Clase invertida publicada con {len(clase.preguntas)} pregunta(s).')
        return redirect('aula:invertida', pk=pk, iid=clase.pk)

    clases = [x for x in aula.invertidas.all() if c.es_docente or (x.publicada and logica.para_c(x, c))]
    if c.es_docente:
        for x in clases:
            x.n_respuestas = x.respuestas.filter(terminada=True).count()
    else:
        mias = {r.clase_id: r for r in RespuestaInvertida.objects.filter(
            clase__in=clases, terminada=True, **logica.filtro_persona(_persona(c)))}
        for x in clases:
            x.mia = mias.get(x.pk)
    datos = {'clases': clases}
    if c.es_docente:
        datos.update(_datos_planilla(aula))
        datos['opciones_para'] = logica.opciones_para(aula)
        datos['borrador'] = request.session.pop('invertida_borrador', None) or {}
    return _render(request, c, 'aula/invertidas.html', datos, 'invertida')


def _clase(c, iid):
    clase = get_object_or_404(ClaseInvertida, pk=iid, aula=c.aula)
    if not c.es_docente and (not clase.publicada or not logica.para_c(clase, c)):
        raise Http404
    return clase


@vista_aula
def invertida(request, pk, iid):
    c = _ctx(request, pk)
    clase = _clase(c, iid)
    if c.es_docente:
        return _vista_docente(request, c, clase)
    persona = _persona(c)
    if persona is None:
        raise _Prohibido('Esta clase la responden los estudiantes.')
    fila_mia = RespuestaInvertida.objects.filter(clase=clase, **logica.filtro_persona(persona)).first()
    mia = fila_mia if fila_mia and fila_mia.terminada else None
    avance = fila_mia if fila_mia and not fila_mia.terminada else None     # lo que lleva viendo el video
    error, faltan = '', []
    if request.method == 'POST' and mia is None:
        respuestas, faltan = INV.leer_respuestas(clase, request.POST)
        if faltan:
            error = 'Le falta responder: ' + ', '.join(str(n) for n in faltan) + '.'
        else:
            aciertos, nota = INV.calificar(clase, respuestas)
            if avance is not None:
                avance.respuestas, avance.aciertos, avance.nota = respuestas, aciertos, nota
                avance.terminada, avance.enviada = True, timezone.now()
                try:
                    duracion = int(float(request.POST.get('duracion') or 0)) or avance.duracion
                    visto = int(float(request.POST.get('visto') or 0))
                except ValueError:
                    duracion, visto = avance.duracion, 0
                avance.duracion = min(duracion, 6 * 3600)
                avance.visto_hasta = max(avance.visto_hasta, min(visto, avance.duracion or visto))
                avance.save(update_fields=['respuestas', 'aciertos', 'nota', 'terminada', 'enviada',
                                           'visto_hasta', 'duracion'])
            else:
                try:
                    RespuestaInvertida.objects.create(clase=clase, respuestas=respuestas, aciertos=aciertos, nota=nota,
                                                      **logica.filtro_persona(persona))
                except IntegrityError:
                    pass
            messages.success(request, '¡Respuestas enviadas!')
            return redirect('aula:invertida', pk=pk, iid=iid)
    detalle = INV.detalle(clase, mia)
    if mia is None:
        # Si le faltó alguna (o ya había respondido mientras veía el video), no pierde lo que llevaba.
        guardadas = avance.respuestas if avance else {}
        for fila in detalle:
            if request.method == 'POST':
                fila['previo'] = request.POST.get(f'p{fila["i"]}', '')
            else:
                valor = guardadas.get(str(fila['i']))
                fila['previo'] = '' if valor is None else str(valor)
            for o in fila['opciones']:
                o['marcada'] = fila['previo'] == str(o['k'])
    return _render(request, c, 'aula/invertida.html', {
        'clase': clase, 'mia': mia, 'detalle': detalle, 'error': error, 'faltan': faltan,
        'avance': avance, 'pausas': clase.con_pausas and mia is None,
        'inv_config': {
            'video': clase.youtube_id,
            'pausas': [{'i': f['i'], 'segundo': f['segundo']} for f in detalle if f['segundo'] is not None],
            'respondidas': sorted(int(k) for k in (avance.respuestas if avance else {})
                                  if clase.preguntas[int(k)].get('segundo') is not None),
            'visto': avance.visto_hasta if avance else 0,
            'urlProgreso': reverse('aula:invertida_progreso', args=[pk, iid]),
            'csrf': get_token(request),
        }}, 'invertida')


@require_POST
@vista_aula
def invertida_progreso(request, pk, iid):
    """Mientras ve el video: guarda las respuestas que va dando y hasta dónde llegó."""
    import json
    c = _ctx(request, pk)
    clase = _clase(c, iid)
    persona = _persona(c)
    if c.es_docente or persona is None:
        raise _Prohibido('Solo para estudiantes.')
    try:
        datos = json.loads(request.body or b'{}')
    except ValueError:
        datos = {}
    r, _ = RespuestaInvertida.objects.get_or_create(clase=clase, **logica.filtro_persona(persona),
                                                    defaults={'terminada': False})
    if r.terminada:
        return JsonResponse({'ok': False, 'terminada': True})
    nuevas = dict(r.respuestas)
    for clave, valor in (datos.get('respuestas') or {}).items():
        if not str(clave).isdigit() or int(clave) >= len(clase.preguntas):
            continue
        p = clase.preguntas[int(clave)]
        if p.get('opciones'):
            if str(valor).isdigit() and int(valor) < len(p['opciones']):
                nuevas[str(clave)] = int(valor)
        elif str(valor).strip():
            nuevas[str(clave)] = str(valor).strip()[:3000]
    r.respuestas = nuevas
    try:
        visto, duracion = int(float(datos.get('visto') or 0)), int(float(datos.get('duracion') or 0))
    except (TypeError, ValueError):
        visto = duracion = 0
    if duracion > 0:
        r.duracion = min(duracion, 6 * 3600)
    r.visto_hasta = max(r.visto_hasta, min(visto, r.duracion or visto))
    r.save(update_fields=['respuestas', 'visto_hasta', 'duracion'])
    return JsonResponse({'ok': True})


def _vista_docente(request, c, clase):
    aula = c.aula
    personas = logica.personas_de(clase, aula)
    respuestas = {}
    for r in clase.respuestas.select_related('estudiante__user', 'integrante'):
        r.en_curso = not r.terminada
        respuestas[logica.clave_de(r.estudiante or r.integrante)] = r
    filas = []
    for p in personas:
        clave = logica.clave_de(p)
        r = respuestas.get(clave)
        filas.append({'clave': clave, 'nombre': logica.nombre_de(p), 'r': r,
                      'detalle': INV.detalle(clase, r) if r else []})
    # Cuántos acertaron cada pregunta de selección, para ver qué no se entendió del video.
    resumen = []
    enviadas = [f['r'] for f in filas if f['r'] and f['r'].terminada]
    for fila in INV.detalle(clase, None):
        if fila['calificable'] and enviadas:
            bien = sum(1 for r in enviadas if INV.detalle(clase, r)[fila['i']]['acierto'])
            fila['pct'] = round(bien * 100 / len(enviadas))
        resumen.append(fila)
    datos = {'clase': clase, 'filas': filas, 'resumen': resumen, 'enviadas': len(enviadas),
             'puede_planilla': bool(aula.asignacion_id), 'opciones_para': logica.opciones_para(aula),
             'rango': logica.rango(aula)}
    datos.update(_datos_planilla(aula))
    return _render(request, c, 'aula/invertida.html', datos, 'invertida')


@require_POST
@vista_aula
def invertida_accion(request, pk, iid):
    c = _ctx(request, pk, docente=True)
    clase = get_object_or_404(ClaseInvertida, pk=iid, aula=c.aula)
    accion = request.POST.get('accion')
    if accion == 'editar':
        error = _leer_formulario(request, clase, c.aula)
        if error:
            messages.warning(request, error)
        else:
            clase.save()
            messages.success(request, 'Cambios guardados.')
    elif accion == 'publicar':
        clase.publicada = not clase.publicada
        clase.save(update_fields=['publicada'])
        messages.info(request, 'Ahora la ven los estudiantes.' if clase.publicada else 'Quedó oculta para los estudiantes.')
    elif accion == 'eliminar':
        clase.delete()
        messages.info(request, 'Clase invertida eliminada.')
        return redirect('aula:invertidas', pk=pk)
    elif accion in ('nota', 'reabrir'):
        clave = request.POST.get('clave') or ''
        r = next((x for x in clase.respuestas.select_related('estudiante', 'integrante')
                  if logica.clave_de(x.estudiante or x.integrante) == clave), None)
        if r is None or (accion == 'nota' and not r.terminada):
            messages.warning(request, 'Ese estudiante no ha enviado sus respuestas.')
        elif accion == 'reabrir':
            r.delete()
            messages.info(request, 'Listo: el estudiante puede responder de nuevo.')
        else:
            minima, maxima = logica.rango(c.aula)
            texto = (request.POST.get('nota') or '').strip().replace(',', '.')
            try:
                valor = Decimal(texto) if texto else None
            except InvalidOperation:
                valor = Decimal('-1')
            if valor is not None and not (minima <= valor <= maxima):
                messages.error(request, f'La nota va de {minima} a {maxima}.')
            else:
                if valor is None:      # vacía: vuelve a la nota automática
                    _, valor = INV.calificar(clase, r.respuestas)
                    r.nota_manual = False
                else:
                    r.nota_manual = True
                r.nota = valor
                r.comentario = (request.POST.get('comentario') or '').strip()[:2000]
                r.save(update_fields=['nota', 'nota_manual', 'comentario'])
                messages.success(request, 'Nota guardada.')
    elif accion == 'planilla':
        pares = [(r.estudiante, r.nota) for r in clase.respuestas.filter(terminada=True).select_related('estudiante')
                 if r.estudiante_id]
        n, error = logica.pasar_notas_a_planilla(c.aula, clase.periodo, clase.componente, clase.titulo, pares)
        if error:
            messages.error(request, error)
        else:
            clase.pasada_planilla = timezone.now()
            clase.save(update_fields=['pasada_planilla'])
            messages.success(request, f'Se pasaron {n} nota(s) a la planilla, columna «{clase.titulo}».')
    return redirect('aula:invertida', pk=pk, iid=iid)
