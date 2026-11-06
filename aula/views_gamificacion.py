"""Gamificación: juegos con preguntas estilo Saber (las del docente o los bancos de prueba)."""
import json
import random

from django.contrib import messages
from django.db import IntegrityError
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from django.views.decorators.http import require_POST

from . import animaplano, bancos_juegos, instrucciones, logica
from .invertida import leer_preguntas
from .juegos import nota as nota_de
from .models import JuegoAula, ResultadoJuegoAula
from .views import _Prohibido, _ctx, _render, _url, vista_aula
from .views_juegos import _datos_planilla, _leer_periodo_componente

MAX_PREGUNTAS = 300
DESCRIPCIONES = {
    'laberinto': 'Cómase la galleta con la respuesta correcta y esquive los virus.',
    'tanques': 'Dispárele al tanque que lleva la respuesta correcta.',
    'tiro': 'Toque el ave con la respuesta correcta antes de que se acabe el tiempo.',
    'salto': 'Salte a la plataforma correcta; las demás se derrumban.',
    'puente': 'Párese en la baldosa correcta antes de que el tiempo llegue a cero.',
    'escape': 'Cada respuesta abre un candado. ¡Salga antes de que se acabe el tiempo!',
    'penaltis': 'Patee a la sección del arco con la respuesta correcta. 1 o 2 jugadores.',
    'tenis': 'Responda bien para pasar la pelota por encima de la malla. Partido con reloj. 1 o 2 jugadores.',
    'carrera': 'Cámbiese al carril de la respuesta correcta antes de que llegue la barrera.',
    'baloncesto': 'Lance al aro de la respuesta correcta. ¡Encestar seguido hace racha!',
    'bandera': 'Robe la bandera correcta y tráigala a su base sin que lo atrapen.',
    'impostor': 'En la nave, saque por la compuerta a los impostores (las respuestas equivocadas).',
    'dibujo': 'Cada respuesta correcta pinta una parte del dibujo. El dibujo depende de la materia.',
    'tesoro': 'Cave en la marca correcta de la isla y arme el mapa del cofre.',
    'carretera': 'De ciudad en ciudad: choque el carro de la respuesta correcta, esquive los otros y no se quede sin gasolina.',
    'unir': 'Una cada pregunta con su respuesta trazando líneas.',
    'animaplano': 'Resuelva cada operación, toque el punto del resultado y descubra la figura (1 a 100).',
    'ovejas': 'La oveja arquera: jale el arco y suelte para reventar el globo del lobo con la respuesta correcta.',
    'boxeo': 'Cada guante es una respuesta: acierte para golpear, falle y lo golpean. Tres rivales. 1 o 2 jugadores.',
}


def _persona(c):
    return c.estudiante or c.integrante


def validar_preguntas(texto, maximo=8, juego=''):
    """(preguntas, error). Cada pregunta: de 2 a `maximo` opciones (hasta 8, A–H, como en PuntoExacto) y una correcta
    marcada. Cada juego dice cuántas caben (JuegoAula.MAX_OPCIONES): el boxeo, por ejemplo, solo 2 (los dos guantes)."""
    preguntas = leer_preguntas(texto, MAX_PREGUNTAS)
    if not preguntas:
        return [], 'Pegue al menos una pregunta con sus opciones.'
    malas = []
    for n, p in enumerate(preguntas, 1):
        ops = p.get('opciones', [])
        if not (2 <= len(ops) <= maximo) or sum(1 for o in ops if o.get('correcta')) != 1:
            malas.append(n)
    if malas:
        letras = 'ABCDEFGH'[maximo - 1]
        return preguntas, ('Revise las preguntas ' + ', '.join(map(str, malas[:15])) + ('…' if len(malas) > 15 else '') +
                           f': {"en «" + juego + "» " if juego else "en los juegos "}cada pregunta lleva de 2 a {maximo} opciones '
                           f'(A a {letras}) y una sola correcta marcada con *.')
    return preguntas, ''


def _para_jugar(preguntas, tipo=None):
    """Las preguntas en otro orden cada vez (cada una con su número para calificar).
    En el animaplano van en su orden: así se dibuja la figura."""
    lista = [dict(p, i=i) for i, p in enumerate(preguntas)]
    if tipo != 'animaplano':
        random.shuffle(lista)
    return lista


def _con_instrucciones(datos):
    """Las instrucciones del juego para el botón «Instrucciones» de la pantalla del juego."""
    datos['instrucciones_juego'] = instrucciones.arcade(datos.get('tipo') or '')
    datos['instrucciones_comun'] = instrucciones.COMUN_ARCADE
    return datos


@vista_aula
def gamificacion(request, pk):
    c = _ctx(request, pk)
    aula = c.aula
    if request.method == 'POST':
        if not c.es_docente:
            raise _Prohibido('Solo el docente crea juegos.')
        j = JuegoAula(aula=aula)
        error = _leer(request, j, aula)
        if error:
            messages.warning(request, error)
            request.session['juego_borrador'] = {k: request.POST.get(k, '') for k in ('titulo', 'preguntas', 'tipo', 'segundos', 'minutos', 'figura', 'operaciones', 'velocidad')}
            return redirect('aula:gamificacion', pk=pk)
        j.save()
        request.session.pop('juego_borrador', None)
        logica.avisar_estudiantes(aula, f'{aula.titulo}: nuevo juego «{j.titulo}» 🎮', _url(request, 'aula:juego', aula.pk, j.pk),
                                  j.para or None)
        messages.success(request, f'Juego publicado con {len(j.preguntas)} pregunta(s).')
        return redirect('aula:gamificacion', pk=pk)
    juegos = [j for j in aula.juegos.all() if c.es_docente or (j.publicado and logica.para_c(j, c))]
    for j in juegos:
        j.instrucciones = instrucciones.arcade(j.tipo)
    if not c.es_docente:
        mios = {r.juego_id: r for r in ResultadoJuegoAula.objects.filter(juego__in=juegos, **logica.filtro_persona(_persona(c)))}
        for j in juegos:
            j.mio = mios.get(j.pk)
    else:
        for j in juegos:
            j.n_resultados = j.resultados.count()
    datos = {'juegos': juegos, 'tipos': [(k, n, DESCRIPCIONES[k], instrucciones.arcade(k)) for k, n in JuegoAula.TIPOS], 'bancos': bancos_juegos.BANCOS,
             'figuras': [(k, n) for k, (n, _) in animaplano.FIGURAS.items()], 'operaciones': animaplano.OPERACIONES,
             'max_opciones': {k: JuegoAula.MAX_OPCIONES.get(k, 4) for k, _ in JuegoAula.TIPOS}}
    if c.es_docente:
        datos.update(_datos_planilla(aula))
        datos['opciones_para'] = logica.opciones_para(aula)
        datos['borrador'] = request.session.pop('juego_borrador', None) or {}
    return _render(request, c, 'aula/gamificacion.html', datos, 'gamificacion')


def _leer(request, j, aula):
    j.titulo = ' '.join((request.POST.get('titulo') or '').split())[:60]
    tipo = request.POST.get('tipo')
    j.tipo = tipo if tipo in dict(JuegoAula.TIPOS) else 'laberinto'
    try:
        j.segundos = max(5, min(120, int(request.POST.get('segundos') or 20)))
    except ValueError:
        j.segundos = 20
    try:
        j.minutos = max(1, min(60, int(request.POST.get('minutos') or 5)))
    except ValueError:
        j.minutos = 5
    v = request.POST.get('velocidad')
    j.velocidad = v if v in JuegoAula.RITMO else 'normal'
    if not j.titulo:
        return 'Escriba el título del juego.'
    texto = (request.POST.get('preguntas') or '').strip()
    if j.tipo == 'animaplano' and not texto:
        # Sin preguntas: la plataforma arma las operaciones de la figura escogida
        texto = animaplano.generar(request.POST.get('figura'), request.POST.get('operaciones'))
    preguntas, error = validar_preguntas(texto, JuegoAula.MAX_OPCIONES.get(j.tipo, 4), j.get_tipo_display())
    if error:
        return error
    if j.tipo == 'animaplano':
        malas = animaplano.revisar(preguntas)
        if malas:
            return ('En el animaplano cada respuesta correcta es un punto de la cuadrícula (un número del 1 al 100). Revise las preguntas '
                    + ', '.join(map(str, malas[:15])) + '.')
    if j.pk and j.resultados.exists() and preguntas != j.preguntas:
        return 'Ya hay estudiantes que jugaron: no se pueden cambiar las preguntas. Cree otro juego.'
    j.texto_preguntas, j.preguntas = texto[:60000], preguntas
    para, error = logica.leer_para(request, aula)
    if error:
        return error
    j.para = para
    _leer_periodo_componente(request, j, aula)
    return ''


def _tema(aula):
    """La materia del aula: el juego «Arma el dibujo» escoge el dibujo con ella."""
    try:
        return aula.asignacion.materia.nombre if aula.asignacion_id else aula.titulo
    except AttributeError:
        return aula.titulo


def _jugadores(request, tipo):
    return 2 if tipo in JuegoAula.DOS_JUGADORES and request.GET.get('jugadores') == '2' else 1


def _juego(c, jid):
    j = get_object_or_404(JuegoAula, pk=jid, aula=c.aula)
    if not c.es_docente and (not j.publicado or not logica.para_c(j, c)):
        raise Http404
    return j


def _tanques(request, c, preguntas, guarda, titulo, url_resultado, banco_propio=False):
    """El juego de tanques con el diseño «Tanques del Álgebra», a pantalla completa."""
    from django.middleware.csrf import get_token
    from django.shortcuts import render
    from django.urls import reverse
    aula = c.aula
    persona = _persona(c)
    docente = aula.asignacion.docente.user.get_full_name() if aula.asignacion_id and aula.asignacion.docente_id else ''
    return render(request, 'aula/juego_tanques.html', {'mcolegio': {
        'preguntas': preguntas, 'guarda': guarda, 'urlResultado': url_resultado, 'csrf': get_token(request),
        'titulo': titulo, 'subtitulo': titulo.upper()[:28], 'eyebrow': aula.titulo,
        'nombre': logica.nombre_de(persona) if persona else (request.user.get_full_name() or request.user.username),
        'curso': aula.asignacion.curso.nombre if aula.asignacion_id else '',
        'colegio': aula.colegio.nombre if aula.colegio_id else '', 'docente': docente,
        'volver': reverse('aula:gamificacion', args=[aula.pk]), 'bancoPropio': banco_propio}})


@vista_aula
def juego(request, pk, jid):
    """Jugar el juego del docente (el docente también lo puede probar; su resultado no se guarda)."""
    c = _ctx(request, pk)
    j = _juego(c, jid)
    if j.tipo == 'tanques' and (not c.es_docente or request.GET.get('jugar')):
        from django.urls import reverse
        return _tanques(request, c, _para_jugar(j.preguntas), not c.es_docente, j.titulo,
                        reverse('aula:juego_resultado', args=[pk, jid]))
    jugadores = _jugadores(request, j.tipo)
    datos = {'juego': j, 'tipo': j.tipo, 'nombre_juego': j.get_tipo_display(), 'segundos': j.segundos, 'minutos': j.minutos,
             'preguntas': _para_jugar(j.preguntas, j.tipo), 'guarda': not c.es_docente and jugadores == 1, 'jugadores': jugadores,
             'dos_jugadores': j.tipo in JuegoAula.DOS_JUGADORES, 'tema': _tema(c.aula),
             'ritmo': JuegoAula.RITMO.get(j.velocidad, 1), 'velocidad': j.velocidad}
    if c.es_docente:
        filas = []
        resultados = {logica.clave_de(r.estudiante or r.integrante): r
                      for r in j.resultados.select_related('estudiante__user', 'integrante')}
        for p in logica.personas_de(j, c.aula):
            filas.append({'nombre': logica.nombre_de(p), 'r': resultados.get(logica.clave_de(p))})
        datos.update({'filas': filas, 'puede_planilla': bool(c.aula.asignacion_id)})
        datos.update(_datos_planilla(c.aula))
    else:
        datos['mio'] = ResultadoJuegoAula.objects.filter(juego=j, **logica.filtro_persona(_persona(c))).first()
    return _render(request, c, 'aula/juego.html', _con_instrucciones(datos), 'gamificacion')


@require_POST
@vista_aula
def juego_resultado(request, pk, jid):
    """El juego terminó: el servidor califica con las respuestas (no confía en el puntaje que manda el juego)."""
    c = _ctx(request, pk)
    j = _juego(c, jid)
    persona = _persona(c)
    if c.es_docente or persona is None:
        return JsonResponse({'ok': True, 'prueba': True})
    try:
        datos = json.loads(request.body or b'{}')
    except ValueError:
        datos = {}
    elegidas = {}
    for r in datos.get('respuestas') or []:
        try:
            i, k = int(r.get('i')), r.get('opcion')
        except (TypeError, ValueError, AttributeError):
            continue
        if 0 <= i < len(j.preguntas) and i not in elegidas:
            elegidas[i] = k if isinstance(k, int) else None
    aciertos = sum(1 for i, k in elegidas.items()
                   if k is not None and 0 <= k < len(j.preguntas[i]['opciones']) and j.preguntas[i]['opciones'][k].get('correcta'))
    # Penaltis y tenis terminan solos (la tanda o el reloj): la nota es sobre lo que respondió.
    total = max(1, len(elegidas)) if j.tipo in JuegoAula.TERMINAN_SOLOS else len(j.preguntas)
    nota = nota_de(c.aula, aciertos, total)
    try:
        puntaje = max(0, min(10 ** 7, int(datos.get('puntaje') or 0)))
    except (TypeError, ValueError):
        puntaje = 0
    r, _ = ResultadoJuegoAula.objects.get_or_create(juego=j, **logica.filtro_persona(persona))
    r.intentos += 1
    r.ultima_nota = nota
    if r.nota is None or (nota is not None and nota >= r.nota):
        r.nota, r.aciertos, r.total = nota, aciertos, total
    r.puntaje = max(r.puntaje, puntaje)
    r.save()
    return JsonResponse({'ok': True, 'aciertos': aciertos, 'total': total, 'nota': str(nota) if nota is not None else '',
                         'mejor': str(r.nota) if r.nota is not None else '', 'intentos': r.intentos})


@vista_aula
def practica(request, pk, tipo, banco):
    """Práctica libre con los bancos de prueba: para todos, sin nota."""
    c = _ctx(request, pk)
    if tipo not in dict(JuegoAula.TIPOS) or banco not in bancos_juegos.BANCOS:
        raise Http404
    if tipo == 'animaplano':          # una figura al azar con operaciones de las cuatro
        preguntas = leer_preguntas(animaplano.generar(random.choice(list(animaplano.FIGURAS)), 'mixtas'), MAX_PREGUNTAS)
        return _render(request, c, 'aula/juego.html', _con_instrucciones({
            'juego': None, 'tipo': tipo, 'nombre_juego': 'Animaplano', 'segundos': 30, 'minutos': 3,
            'preguntas': [dict(p, i=i) for i, p in enumerate(preguntas)], 'guarda': False, 'jugadores': 1,
            'banco': 'operaciones básicas', 'tema': ''}), 'gamificacion')
    if tipo == 'tanques':
        if banco == 'factorizacion':        # los 6 temas del juego original, cada uno su nivel
            return _tanques(request, c, [], False, 'Factorización', None, banco_propio=True)
        preguntas = [dict(p, i=i) for i, p in enumerate(bancos_juegos.preguntas(banco, 25))]
        return _tanques(request, c, preguntas, False, bancos_juegos.BANCOS[banco], None)
    cuantas = {'escape': 8, 'penaltis': 30, 'tenis': 40, 'unir': 10, 'dibujo': 16, 'boxeo': 40}.get(tipo, 12)
    preguntas = bancos_juegos.preguntas(banco, cuantas)
    return _render(request, c, 'aula/juego.html', _con_instrucciones({
        'juego': None, 'tipo': tipo, 'nombre_juego': dict(JuegoAula.TIPOS)[tipo], 'segundos': 20 if tipo != 'escape' else 12,
        'minutos': 3, 'preguntas': [dict(p, i=i) for i, p in enumerate(preguntas)], 'guarda': False,
        'jugadores': _jugadores(request, tipo), 'dos_jugadores': tipo in JuegoAula.DOS_JUGADORES,
        'banco': bancos_juegos.BANCOS[banco], 'tema': f'{banco} {_tema(c.aula)}',
        'ritmo': JuegoAula.RITMO.get(request.GET.get('velocidad'), 1), 'velocidad': request.GET.get('velocidad') if request.GET.get('velocidad') in JuegoAula.RITMO else 'normal',
        'elegir_velocidad': True, 'velocidades': JuegoAula.VELOCIDADES}), 'gamificacion')


@require_POST
@vista_aula
def juego_accion(request, pk, jid):
    c = _ctx(request, pk, docente=True)
    j = get_object_or_404(JuegoAula, pk=jid, aula=c.aula)
    accion = request.POST.get('accion')
    if accion == 'publicar':
        j.publicado = not j.publicado
        j.save(update_fields=['publicado'])
        messages.info(request, 'Ahora lo ven los estudiantes.' if j.publicado else 'Quedó oculto para los estudiantes.')
    elif accion == 'eliminar':
        j.delete()
        messages.info(request, 'Juego eliminado.')
        return redirect('aula:gamificacion', pk=pk)
    elif accion == 'planilla':
        pares = [(r.estudiante, r.nota) for r in j.resultados.select_related('estudiante') if r.estudiante_id]
        n, error = logica.pasar_notas_a_planilla(c.aula, j.periodo, j.componente, j.titulo, pares)
        if error:
            messages.error(request, error)
        else:
            j.pasado_planilla = timezone.now()
            j.save(update_fields=['pasado_planilla'])
            messages.success(request, f'Se pasaron {n} nota(s) a la planilla, columna «{j.titulo}».')
    elif accion == 'periodo':
        _leer_periodo_componente(request, j, c.aula)
        j.save(update_fields=['periodo', 'componente'])
        messages.success(request, 'Periodo y componente guardados.')
    return redirect('aula:juego', pk=pk, jid=jid)
