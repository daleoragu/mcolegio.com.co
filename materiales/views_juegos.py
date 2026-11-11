"""Mis juegos (Planeación): crear, editar y probar los juegos con preguntas sin tener un grupo, y enviarlos a las clases.

Lo que el docente juega aquí es una prueba: no guarda nota. En la clase, el juego queda como juego del aula (JuegoAula),
con sus resultados, su análisis de preguntas y su paso a la planilla."""
import random

from django.contrib import messages
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from .models import JuegoMaterial
from .views import vista


def _aula():
    """Lo del aula que se reutiliza (import diferido: aula también usa materiales)."""
    from aula import animaplano, bancos_juegos, instrucciones
    from aula.models import JuegoAula
    from aula import views_gamificacion as vg
    return animaplano, bancos_juegos, instrucciones, JuegoAula, vg


def _tipos():
    animaplano, bancos_juegos, instrucciones, JuegoAula, vg = _aula()
    return [(k, n, vg.DESCRIPCIONES.get(k, ''), instrucciones.arcade(k)) for k, n in JuegoAula.TIPOS]


def _mio(request, pk):
    return get_object_or_404(JuegoMaterial, pk=pk, propietario=request.user)


def _leer(request, j):
    """Llena el juego con lo que mandó el formulario. Devuelve el error ('' si todo está bien)."""
    animaplano, bancos_juegos, instrucciones, JuegoAula, vg = _aula()
    j.titulo = ' '.join((request.POST.get('titulo') or '').split())[:60]
    tipo = request.POST.get('tipo')
    j.tipo = tipo if tipo in dict(JuegoAula.TIPOS) else 'laberinto'
    for campo, defecto, menor, mayor in (('segundos', 20, 5, 120), ('minutos', 5, 1, 60)):
        try:
            setattr(j, campo, max(menor, min(mayor, int(request.POST.get(campo) or defecto))))
        except ValueError:
            setattr(j, campo, defecto)
    v = request.POST.get('velocidad')
    j.velocidad = v if v in JuegoAula.RITMO else 'normal'
    if not j.titulo:
        return 'Escriba el título del juego.'
    texto = (request.POST.get('preguntas') or '').strip()
    if j.tipo == 'animaplano' and not texto:
        texto = animaplano.generar(request.POST.get('figura'), request.POST.get('operaciones'))
    preguntas, error = vg.validar_preguntas(texto, JuegoAula.MAX_OPCIONES.get(j.tipo, 4), dict(JuegoAula.TIPOS)[j.tipo])
    if error:
        return error
    if j.tipo == 'animaplano':
        malas = animaplano.revisar(preguntas)
        if malas:
            return ('En el animaplano cada respuesta correcta es un punto de la cuadrícula (un número del 1 al 100). Revise las preguntas '
                    + ', '.join(map(str, malas[:15])) + '.')
    j.texto_preguntas, j.preguntas = texto[:60000], preguntas
    return ''


def _contexto_formulario(a, j=None, borrador=None):
    animaplano, bancos_juegos, instrucciones, JuegoAula, vg = _aula()
    if borrador is None and j is not None:
        borrador = {'titulo': j.titulo, 'tipo': j.tipo, 'preguntas': j.texto_preguntas, 'segundos': j.segundos,
                    'minutos': j.minutos, 'velocidad': j.velocidad}
    return {'base': a.base, 'acceso': a, 'tipos': _tipos(), 'borrador': borrador or {},
            'figuras': [(k, n) for k, (n, _) in animaplano.FIGURAS.items()], 'operaciones': animaplano.OPERACIONES,
            'max_opciones': {k: JuegoAula.MAX_OPCIONES.get(k, 4) for k, _ in JuegoAula.TIPOS}}


def _actualizar_copias(j):
    """Lleva los cambios a las clases donde se envió. Las que ya tienen resultados no se tocan (sus notas no cambian).
    Devuelve (actualizadas, bloqueadas)."""
    from aula.models import JuegoAula
    hechas, bloqueadas, vivos = 0, 0, {}
    for aula_id, jid in (j.enviados or {}).items():
        copia = JuegoAula.objects.filter(pk=jid, aula_id=aula_id).first()
        if copia is None:
            continue
        vivos[aula_id] = jid
        if copia.resultados.exists():
            bloqueadas += 1
            continue
        for campo in ('tipo', 'titulo', 'texto_preguntas', 'preguntas', 'segundos', 'minutos', 'velocidad'):
            setattr(copia, campo, getattr(j, campo))
        copia.save()
        hechas += 1
    if vivos != (j.enviados or {}):
        j.enviados = vivos
        j.save(update_fields=['enviados'])
    return hechas, bloqueadas


@vista
def juegos(request, a):
    """Mis juegos: crear uno nuevo, la lista de los míos y la galería para probar cada juego con preguntas de ejemplo."""
    if request.method == 'POST':
        j = JuegoMaterial(propietario=request.user)
        error = _leer(request, j)
        if error:
            messages.warning(request, error)
            ctx = _contexto_formulario(a, borrador={k: request.POST.get(k, '') for k in
                                                   ('titulo', 'preguntas', 'tipo', 'segundos', 'minutos', 'velocidad', 'figura', 'operaciones')})
            return render(request, 'materiales/juegos.html', dict(ctx, mios=_lista(request, a), aulas=a.aulas(), logica=_logica()))
        j.save()
        messages.success(request, f'«{j.titulo}» quedó en Mis juegos con {len(j.preguntas)} pregunta(s). Pruébelo y, cuando esté listo, envíelo a sus clases.')
        return redirect(reverse('materiales:juegos') + f'#j{j.pk}')
    ctx = _contexto_formulario(a)
    return render(request, 'materiales/juegos.html', dict(ctx, mios=_lista(request, a), aulas=a.aulas(), logica=_logica()))


def _lista(request, a):
    nombres = {x.pk: (f'{x.titulo} · {x.subtitulo}' if x.subtitulo else x.titulo) for x in a.aulas()}
    lista = list(JuegoMaterial.objects.filter(propietario=request.user))
    for j in lista:
        j.clases = [nombres[int(k)] for k in (j.enviados or {}) if int(k) in nombres]
    return lista


def _logica():
    from aula.views_logica import JUEGOS, MODO_DE
    return [(i, n, d) for i, n, d, _ in JUEGOS if MODO_DE.get(i, i) == i]


@vista
def juego_editar(request, a, pk):
    j = _mio(request, pk)
    if request.method == 'POST':
        error = _leer(request, j)
        if error:
            messages.warning(request, error)
            j.refresh_from_db()
        else:
            j.save()
            hechas, bloqueadas = _actualizar_copias(j)
            texto = f'Cambios guardados en «{j.titulo}».'
            if hechas:
                texto += f' También se actualizó en {hechas} clase(s).'
            if bloqueadas:
                texto += (f' En {bloqueadas} clase(s) ya hay estudiantes que jugaron: allá sigue la versión anterior '
                          '(envíelo de nuevo para crear otro juego con los cambios).')
            messages.success(request, texto)
            return redirect(reverse('materiales:juegos') + f'#j{j.pk}')
    return render(request, 'materiales/juego_editar.html', dict(_contexto_formulario(a, j), juego=j))


def _jugar(request, a, tipo, titulo, preguntas, segundos=20, minutos=5, velocidad='normal', banco='', elegir=False):
    """La pantalla del juego (la misma de la clase), sin aula: es una prueba y no guarda nota."""
    animaplano, bancos_juegos, instrucciones, JuegoAula, vg = _aula()
    volver = reverse('materiales:juegos')
    jugadores = 2 if tipo in JuegoAula.DOS_JUGADORES and request.GET.get('jugadores') == '2' else 1
    v = request.GET.get('velocidad') if elegir and request.GET.get('velocidad') in JuegoAula.RITMO else velocidad
    if tipo == 'tanques':
        from django.middleware.csrf import get_token
        return render(request, 'aula/juego_tanques.html', {'mcolegio': {
            'preguntas': preguntas, 'guarda': False, 'urlResultado': None, 'csrf': get_token(request),
            'titulo': titulo, 'subtitulo': titulo.upper()[:28], 'eyebrow': 'Prueba del docente',
            'nombre': request.user.get_full_name() or request.user.username, 'curso': '', 'colegio': '', 'docente': '',
            'volver': volver, 'bancoPropio': banco == 'factorizacion'}})
    datos = {'juego': None, 'tipo': tipo, 'nombre_juego': dict(JuegoAula.TIPOS)[tipo], 'segundos': segundos, 'minutos': minutos,
             'preguntas': preguntas, 'guarda': False, 'jugadores': jugadores, 'dos_jugadores': tipo in JuegoAula.DOS_JUGADORES,
             'banco': banco or titulo, 'tema': banco or titulo, 'ritmo': JuegoAula.RITMO.get(v, 1), 'velocidad': v,
             'elegir_velocidad': elegir, 'velocidades': JuegoAula.VELOCIDADES,
             'base': a.base, 'aula': None, 'menu_url': volver, 'prueba_docente': True}
    return render(request, 'aula/juego.html', vg._con_instrucciones(datos))


@vista
def juego_probar(request, a, pk):
    """Probar mi juego tal como lo verán los estudiantes (sin nota)."""
    animaplano, bancos_juegos, instrucciones, JuegoAula, vg = _aula()
    j = _mio(request, pk)
    return _jugar(request, a, j.tipo, j.titulo, vg._para_jugar(j.preguntas, j.tipo), j.segundos, j.minutos, j.velocidad)


@vista
def juego_ejemplo(request, a, tipo, banco='matematicas'):
    """Probar cualquier juego con las preguntas de ejemplo de la plataforma (para conocerlo antes de crear el mío)."""
    animaplano, bancos_juegos, instrucciones, JuegoAula, vg = _aula()
    if tipo not in dict(JuegoAula.TIPOS) or banco not in bancos_juegos.BANCOS:
        raise Http404
    if tipo == 'animaplano':
        from aula.invertida import leer_preguntas
        preguntas = leer_preguntas(animaplano.generar(random.choice(list(animaplano.FIGURAS)), 'mixtas'), vg.MAX_PREGUNTAS)
        return _jugar(request, a, tipo, 'Animaplano', [dict(p, i=i) for i, p in enumerate(preguntas)], 30, 3, banco='operaciones básicas')
    if tipo == 'tanques' and banco == 'factorizacion':
        return _jugar(request, a, tipo, 'Factorización', [], banco='factorizacion')
    cuantas = {'escape': 8, 'penaltis': 30, 'tenis': 40, 'unir': 10, 'dibujo': 16, 'boxeo': 40, 'tanques': 25}.get(tipo, 12)
    preguntas = [dict(p, i=i) for i, p in enumerate(bancos_juegos.preguntas(banco, cuantas))]
    return _jugar(request, a, tipo, bancos_juegos.BANCOS[banco], preguntas, 20 if tipo != 'escape' else 12, 3,
                  banco=bancos_juegos.BANCOS[banco], elegir=True)


@vista
def logica_probar(request, a, juego):
    """Los juegos de lógica (Tangram, Trancón, Escape de la selva…) sin grupo: para conocerlos y probarlos."""
    from aula import instrucciones
    from aula.views_logica import DATOS, MODOS, MODO_DE, niveles
    if juego not in DATOS:
        raise Http404
    _, nombre, desc, archivo = DATOS[juego]
    return render(request, 'aula/logica_juego.html', {
        'juego': juego, 'nombre': nombre, 'desc': desc, 'archivo': archivo, 'niveles': niveles(juego),
        'clave': f'mc-logica-prueba:{request.user.pk}:{juego}', 'servidor': {}, 'guarda': False,
        'modos': MODOS.get(MODO_DE.get(juego), []), 'base': a.base, 'aula': None,
        'menu_url': reverse('materiales:juegos') + '#logica', 'instrucciones_logica': instrucciones.logica(juego, archivo)})


@require_POST
@vista
def juego_enviar(request, a, pk):
    """Enviar el juego a una o varias clases: allá queda como juego del aula (con nota y planilla)."""
    from aula import logica
    from aula.models import JuegoAula
    j = _mio(request, pk)
    mias = {x.pk: x for x in a.aulas()}
    elegidas = [mias[int(x)] for x in request.POST.getlist('aulas') if x.isdigit() and int(x) in mias]
    if not elegidas:
        messages.warning(request, 'Escoja al menos una clase.')
        return redirect(reverse('materiales:juegos') + f'#j{j.pk}')
    enviados = dict(j.enviados or {})
    nuevas, actualizadas = [], 0
    for aula in elegidas:
        previa = JuegoAula.objects.filter(pk=enviados.get(str(aula.pk)), aula=aula).first()
        if previa is not None and not previa.resultados.exists():
            for campo in ('tipo', 'titulo', 'texto_preguntas', 'preguntas', 'segundos', 'minutos', 'velocidad'):
                setattr(previa, campo, getattr(j, campo))
            previa.save()
            actualizadas += 1
            continue
        copia = JuegoAula.objects.create(aula=aula, tipo=j.tipo, titulo=j.titulo, texto_preguntas=j.texto_preguntas,
                                         preguntas=j.preguntas, segundos=j.segundos, minutos=j.minutos, velocidad=j.velocidad)
        enviados[str(aula.pk)] = copia.pk
        nuevas.append(aula.titulo)
        logica.avisar_estudiantes(aula, f'{aula.titulo}: nuevo juego «{j.titulo}» 🎮',
                                  request.build_absolute_uri(reverse('aula:juego', args=[aula.pk, copia.pk])))
    j.enviados = enviados
    j.save(update_fields=['enviados'])
    partes = []
    if nuevas:
        partes.append('Enviado a ' + ', '.join(nuevas) + '. Sus estudiantes ya lo ven en Gamificación.')
    if actualizadas:
        partes.append(f'Actualizado en {actualizadas} clase(s) donde ya estaba.')
    messages.success(request, ' '.join(partes))
    return redirect(reverse('materiales:juegos') + f'#j{j.pk}')


@require_POST
@vista
def juego_vivo(request, a, pk):
    """Jugarlo en vivo con una clase: se vuelve un cuestionario en vivo (el docente proyecta, los estudiantes responden
    desde el celular) y se abre de una vez la partida."""
    from aula import juegos as JQ, logica
    from aula.models import Cuestionario
    j = _mio(request, pk)
    mias = {x.pk: x for x in a.aulas()}
    aula = mias.get(int(request.POST.get('aula') or 0)) if (request.POST.get('aula') or '').isdigit() else None
    if aula is None:
        messages.warning(request, 'Escoja la clase con la que lo va a jugar en vivo.')
        return redirect(reverse('materiales:juegos') + f'#j{j.pk}')
    preguntas = [(p.get('texto', ''), [(o.get('texto', ''), bool(o.get('correcta'))) for o in p.get('opciones', [])][:6])
                 for p in j.preguntas if p.get('opciones')]
    if not preguntas:
        messages.warning(request, 'El juego no tiene preguntas con opciones.')
        return redirect(reverse('materiales:juegos') + f'#j{j.pk}')
    q = Cuestionario.objects.create(aula=aula, titulo=j.titulo[:60], segundos=j.segundos, a_su_ritmo=False,
                                    descripcion='En vivo desde Mis juegos')
    JQ.guardar_preguntas(q, preguntas)
    s = JQ.nueva_sesion(q)
    logica.avisar_estudiantes(aula, f'{aula.titulo}: ¡juego en vivo «{q.titulo}»! Entre ya',
                              request.build_absolute_uri(reverse('aula:vivo', args=[aula.pk, s.pk])))
    return redirect('aula:vivo', pk=aula.pk, sid=s.pk)


def _pub_con_juego(request, pk):
    """La publicación de la Sala de Profesores con un juego que este docente puede ver."""
    from chat.views_muro import visibles
    p = visibles(request.user).filter(pk=pk, juego__isnull=False).select_related('juego', 'autor').first()
    if p is None:
        raise Http404
    return p


@vista
def juego_muro(request, a, pk):
    """Probar el juego que un colega compartió en la Sala de Profesores."""
    animaplano, bancos_juegos, instrucciones, JuegoAula, vg = _aula()
    p = _pub_con_juego(request, pk)
    j = p.juego
    return _jugar(request, a, j.tipo, j.titulo, vg._para_jugar(j.preguntas, j.tipo), j.segundos, j.minutos, j.velocidad)


@require_POST
@vista
def juego_importar(request, a, pk):
    """Copia el juego del colega a «Mis juegos»: queda mío para editarlo, probarlo y enviarlo a mis clases."""
    from chat.models import Publicacion
    from chat.views_colegas import avisar, nombre_de
    p = _pub_con_juego(request, pk)
    j = p.juego
    if j.propietario_id == request.user.pk:
        messages.info(request, 'Ese juego ya es suyo.')
        return redirect('materiales:juegos')
    copia = JuegoMaterial.objects.create(propietario=request.user, tipo=j.tipo, titulo=j.titulo, texto_preguntas=j.texto_preguntas,
                                         preguntas=j.preguntas, segundos=j.segundos, minutos=j.minutos, velocidad=j.velocidad)
    Publicacion.objects.filter(pk=p.pk).update(copias=p.copias + 1)
    avisar(p.autor, f'{nombre_de(request.user)} importó su juego «{j.titulo[:60]}» para usarlo con sus estudiantes. ¡Gracias por compartir!',
           f'/chat/colegas/muro/{p.pk}/')
    messages.success(request, f'«{copia.titulo}» quedó en Mis juegos: pruébelo, ajústelo y envíelo a sus clases.')
    return redirect(reverse('materiales:juegos') + f'#j{copia.pk}')


@require_POST
@vista
def juego_eliminar(request, a, pk):
    j = _mio(request, pk)
    titulo = j.titulo
    j.delete()
    messages.info(request, f'«{titulo}» salió de Mis juegos. Los juegos que ya están en sus clases siguen allá.')
    return redirect('materiales:juegos')
