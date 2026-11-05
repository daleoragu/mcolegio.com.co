"""Eventos del colegio en Mi Salón Virtual. El primero: la olimpiada de matemáticas.

- El evento se crea apagado; los estudiantes solo lo ven cuando el organizador lo activa.
- Organizan los administradores del colegio y los docentes que ellos escojan.
- Grupos de participantes con el nombre, los grados y la dificultad que escoja el organizador
  (por defecto: Exploradores 6.º–7.º, Investigadores 8.º–9.º y Expertos 10.º–11.º; se pueden agregar
  grupos de preescolar y primaria). Participan todos los de esos grados, solo ciertos cursos o solo
  ciertos estudiantes.
- Pensamientos: Euclides (geométrico), Newton (numérico y algebraico) y Bernoulli (aleatorio).
- Bloques de N minutos con descanso visual obligatorio entre bloques. Cada reto superado = 1 punto.
  Cada `cada` puntos sale una pregunta de competencia (hasta `por_parada`); bien respondida resta 30 s.
- Gana quien tenga más puntos; si empatan, el menor tiempo efectivo.
El servidor cuenta los puntos y califica las preguntas: el navegador solo manda lo que pasó.
"""
import csv
import json
import os
import random

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import Http404, HttpResponse, HttpResponseForbidden, JsonResponse
from django.contrib.auth.views import redirect_to_login
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from .invertida import leer_preguntas
from .models import Evento, JuegoAula, ParticipacionEvento

import copy

# Grupos por defecto (el organizador los renombra, cambia sus grados o agrega otros). nivel: 0 fácil, 1 media, 2 difícil
GRUPOS_BASE = [{'id': 'exploradores', 'nombre': 'Exploradores', 'grados': [6, 7], 'nivel': 0},
               {'id': 'investigadores', 'nombre': 'Investigadores', 'grados': [8, 9], 'nivel': 1},
               {'id': 'expertos', 'nombre': 'Expertos', 'grados': [10, 11], 'nivel': 2}]
NIVELES = [(0, 'Fácil'), (1, 'Media'), (2, 'Difícil')]
CATEGORIAS = [('euclides', 'Euclides', 'Pensamiento geométrico y espacial'), ('newton', 'Newton', 'Pensamiento numérico y algebraico'),
              ('bernoulli', 'Bernoulli', 'Pensamiento aleatorio, estadístico y combinatorio')]
# Minijuegos de la olimpiada: id, nombre, estilo
JUEGOS = [
    ('tangram', 'Tangram', 'logica'), ('trancon', 'Trancón (tipo Rush Hour)', 'logica'), ('safari', 'Safari', 'logica'),
    ('fila', 'La fila exacta (permutaciones)', 'logica'), ('bango', 'Tablero 36 (tipo Bango)', 'logica'),
    ('kadogemo', 'Cuatro cuadrantes (tipo Kadogemo)', 'logica'), ('nonograma', 'Nonograma', 'logica'), ('hanoi', 'Torres de Hanói', 'logica'),
    ('ranas', 'Ranas saltarinas', 'logica'), ('cerditos', 'Los tres cerditos', 'logica'), ('kiriku', 'Deslizables de colores', 'logica'),
    ('laberinto', 'Laberinto de colores', 'logica'), ('fijas', 'Picas y fijas con figuras', 'logica'),
    ('sokoban', 'Empuja cajas (tipo Sokoban)', 'logica'), ('conejos', 'Conejos saltarines', 'logica'), ('perrito', 'Perrito a su casita', 'logica'),
    ('caperucita', 'Caperucita (piezas de camino)', 'logica'), ('ladron', 'Atrapa al ladrón', 'logica'), ('bloque', 'Bloque rodante (tipo Bloxorz)', 'logica'),
    ('tiro', 'Tiro al vuelo (aves con la respuesta)', 'arcade'), ('pacman', 'Laberinto comelón (galleta con el resultado)', 'arcade'),
    ('speedrun', 'Cálculo veloz (contrarreloj)', 'arcade'),
    ('geoplano', 'Geoplano (bandas elásticas)', 'montessori'), ('regletas', 'Regletas en la balanza (Cuisenaire)', 'montessori'),
    ('cubo', 'Cubo del binomio y del trinomio 3D', 'montessori'),
]
ESTILOS = [('logica', 'Lógica y rompecabezas'), ('arcade', 'Acción arcade (con operaciones según el grupo)'), ('montessori', 'Simuladores Montessori'),
           ('propio', 'Juegos propios del salón virtual (con sus preguntas)')]
# Juegos arcade de la Gamificación que no sirven como reto corto (página propia, partido por minutos, 3 rivales, figura en orden)
NO_EN_EVENTO = {'tanques', 'tenis', 'boxeo', 'animaplano'}


def _arcade():
    """Todos los juegos arcade de la Gamificación como retos del evento (tiro y laberinto ya están arriba)."""
    from .models import JuegoAula as J
    return [('a_' + k, f'{n} (arcade)', 'arcade') for k, n in J.TIPOS if k not in NO_EN_EVENTO and k not in ('tiro', 'laberinto')]


def juegos_del_evento(ev):
    """Los juegos que se pueden poner en el evento: los de lógica, todos los arcade y los juegos propios
    que los docentes armaron en el salón virtual con sus preguntas."""
    lista = list(JUEGOS) + _arcade()
    for j in _juegos_salon(ev).select_related('aula').order_by('-pk')[:80]:
        if len(j.preguntas) >= 2:
            lista.append((f'p_{j.pk}', f'{j.titulo} · {j.get_tipo_display()} ({j.aula.titulo}, {len(j.preguntas)} preg.)', 'propio'))
    return lista


def tipo_motor(juego, propios=None):
    """El juego de la Gamificación con que se juega ese reto (None si es de lógica)."""
    if juego == 'tiro':
        return 'tiro'
    if juego == 'pacman':
        return 'laberinto'
    if juego.startswith('a_'):
        return juego[2:]
    if juego.startswith('p_') and propios is not None:
        t = propios.get(juego, {}).get('tipo')
        return 'impostor' if t in ('tenis', 'boxeo', 'animaplano') else t
    return None
CONFIG = {'juegos': [j[0] for j in JUEGOS] + ['a_' + k for k in ('salto', 'puente', 'escape', 'penaltis', 'carrera', 'baloncesto', 'bandera',
                                                                   'impostor', 'dibujo', 'tesoro', 'carretera', 'unir', 'ovejas')], 'bloques': 2, 'minutos': 15, 'descanso': 3, 'cada': 5, 'por_parada': 1, 'bono': 30,
          'por_juego': {},      # {id: {'grados': [6, 7…], 'dificultad': 'auto'|'facil'|'media'|'dificil'}}
          'grupos': GRUPOS_BASE,
          'participantes': {'modo': 'grados', 'cursos': [], 'estudiantes': []}}   # modo: grados | cursos | estudiantes
DIFICULTADES = [('auto', 'Según el grupo'), ('facil', 'Fácil'), ('media', 'Media'), ('dificil', 'Difícil')]


def todos_los_grados():
    from notas.models.perfiles import GRADOS as G
    return [g for g, _, _ in G]


def etiqueta_grado(g):
    return {-2: 'Prejardín', -1: 'Jardín', 0: 'Transición'}.get(g, f'{g}.º')


def grados_del_colegio(colegio):
    from notas.models import Curso
    g = sorted({x for x in Curso.objects.filter(colegio=colegio).values_list('grado', flat=True) if x is not None})
    return g or list(range(6, 12))


def grupos(c):
    return c.get('grupos') or GRUPOS_BASE


def grupo_por_id(c, gid):
    return next((g for g in grupos(c) if g['id'] == gid), None)


def grupo_de_estudiante(c, est):
    """El grupo del estudiante, si participa (según su grado y la lista de cursos o estudiantes escogidos)."""
    if est is None or not est.curso_id or est.curso.grado is None:
        return None
    part = c.get('participantes') or {}
    modo = part.get('modo', 'grados')
    if modo == 'cursos' and est.curso_id not in part.get('cursos', []):
        return None
    if modo == 'estudiantes' and est.pk not in part.get('estudiantes', []):
        return None
    return next((g for g in grupos(c) if int(est.curso.grado) in g['grados']), None)


def rango_grados(g):
    gs = sorted(g['grados'])
    if not gs:
        return 'sin grados'
    return ', '.join(etiqueta_grado(x) for x in gs) if len(gs) <= 3 or gs != list(range(gs[0], gs[-1] + 1)) \
        else f'{etiqueta_grado(gs[0])} a {etiqueta_grado(gs[-1])}'


def juegos_para(c, grados, lista=None):
    """Los juegos habilitados para alguno de esos grados (si no se dijo nada, para todos)."""
    out = []
    for j in (lista if lista is not None else JUEGOS):
        if j[0] not in c['juegos']:
            continue
        g = (c['por_juego'].get(j[0]) or {}).get('grados')
        if g is None or set(g) & set(grados):
            out.append(j)
    return out


def dificultad(c, juego):
    return (c['por_juego'].get(juego) or {}).get('dificultad', 'auto')
BANCO = os.path.join(os.path.dirname(__file__), 'bancos', 'olimpiada.json')


def config_de(evento):
    c = copy.deepcopy(CONFIG)
    c.update({k: v for k, v in (evento.config or {}).items() if k in CONFIG})
    return c


def _estudiante(request):
    est = getattr(request.user, 'estudiante', None)
    colegio = getattr(request, 'colegio', None)
    return est if est is not None and colegio is not None and est.colegio_id == colegio.id else None


def es_organizador(request, evento=None):
    """Quien creó el evento, los organizadores que escogió y la administración de su colegio."""
    u = request.user
    if not u.is_authenticated:
        return False
    if evento is None:
        return puede_crear(request)
    if u.is_superuser or evento.creador_id == u.pk or evento.organizadores.filter(pk=u.pk).exists():
        return True
    if evento.colegio_id:
        from notas.permisos import es_admin_colegio
        return es_admin_colegio(u, evento.colegio)
    return False


def puede_crear(request):
    """Cualquier docente crea eventos: el del colegio y el de Salón Digital (sin colegio)."""
    u = request.user
    if not u.is_authenticated:
        return False
    colegio = getattr(request, 'colegio', None)
    if colegio is not None:
        from notas.models import Docente
        from notas.permisos import es_admin
        return es_admin(request) or Docente.objects.filter(user=u, colegio=colegio).exists()
    return u.is_superuser or hasattr(u, 'cuenta_salon')


def es_admin_del_evento(request, ev):
    """Puede escoger organizadores y eliminar: quien lo creó o la administración del colegio."""
    from notas.permisos import es_admin_colegio
    u = request.user
    return u.is_authenticated and (u.is_superuser or ev.creador_id == u.pk or (ev.colegio_id and es_admin_colegio(u, ev.colegio)))


def _evento(request, eid):
    """Los eventos del colegio se ven desde su colegio; los abiertos (con código), desde cualquier parte."""
    ev = get_object_or_404(Evento, pk=eid)
    if not ev.codigo:
        ev.save()
    colegio = getattr(request, 'colegio', None)
    if ev.alcance == 'colegio' and (colegio is None or ev.colegio_id != colegio.id) and not es_organizador(request, ev):
        raise Http404
    return ev


def _base(request):
    return 'notas/base.html' if getattr(request, 'colegio', None) is not None and request.user.is_authenticated else 'aula/base_salon.html'


def clave_sesion(ev):
    return f'evento_{ev.pk}'


def participante(request, ev, crear=False):
    """La participación de quien está jugando: estudiante del colegio (con su cuenta) o inscrito con el código."""
    if ev.alcance == 'codigo':
        tok = request.session.get(clave_sesion(ev))
        return ParticipacionEvento.objects.filter(evento=ev, token=tok).first() if tok else None
    est = _estudiante(request)
    if est is None or ev.colegio_id != est.colegio_id:
        return None
    g = grupo_de_estudiante(config_de(ev), est)
    if not g:
        return None
    if crear:
        p, _ = ParticipacionEvento.objects.get_or_create(evento=ev, estudiante=est, defaults={'ciclo': g['id']})
        return p
    return ParticipacionEvento.objects.filter(evento=ev, estudiante=est).first()


def grado_de(p):
    if p.estudiante_id:
        return p.estudiante.curso.grado if p.estudiante.curso_id else None
    return p.grado


def ranking(evento, ciclo=None):
    qs = evento.participaciones.select_related('estudiante__user', 'estudiante__curso')
    if ciclo:
        qs = qs.filter(ciclo=ciclo)
    lista = sorted(qs, key=lambda p: (-p.puntos, p.tiempo_efectivo, p.pk))
    for i, p in enumerate(lista, 1):
        p.puesto = i
    return lista


def hay_eventos_activos(request):
    colegio = getattr(request, 'colegio', None)
    return colegio is not None and Evento.objects.filter(colegio=colegio, activo=True, alcance='colegio').exists()


# ---------------------------------------------------------------------------
# Páginas
# ---------------------------------------------------------------------------
@login_required
def eventos(request):
    from django.db.models import Q
    from notas.permisos import es_admin
    colegio = getattr(request, 'colegio', None)
    organiza = puede_crear(request)
    if colegio is None and not organiza:
        return redirect('aula:evento_entrar')
    if request.method == 'POST':
        if not organiza:
            return HttpResponseForbidden('Solo los docentes crean eventos.')
        titulo = ' '.join((request.POST.get('titulo') or '').split())[:80]
        if not titulo:
            messages.warning(request, 'Escriba el nombre del evento.')
            return redirect('aula:eventos')
        alcance = request.POST.get('alcance') if colegio is not None else 'codigo'
        ev = Evento.objects.create(colegio=colegio, creador=request.user, titulo=titulo, alcance=alcance if alcance in ('colegio', 'codigo') else 'colegio',
                                   config=copy.deepcopy(CONFIG), preguntas=_banco())
        messages.success(request, f'Se creó «{ev.titulo}». Está apagado: configúrelo y actívelo cuando quiera que los participantes lo vean.')
        return redirect('aula:evento_configurar', eid=ev.pk)
    mios = Q(creador=request.user) | Q(organizadores=request.user)
    if colegio is not None and es_admin(request):
        todos = Evento.objects.filter(Q(colegio=colegio) | mios)
    elif organiza:
        todos = Evento.objects.filter(mios | Q(colegio=colegio, activo=True, alcance='colegio') if colegio else mios)
    else:
        todos = Evento.objects.filter(colegio=colegio, activo=True, alcance='colegio')
    todos = todos.distinct()
    est = _estudiante(request)
    mias = {p.evento_id: p for p in ParticipacionEvento.objects.filter(evento__in=todos, estudiante=est)} if est else {}
    lista = []
    for ev in todos:
        ev.mia = mias.get(ev.pk)
        ev.organiza = es_organizador(request, ev)
        ev.n_participantes = ev.participaciones.count()
        lista.append(ev)
    for ev in lista:
        g = grupo_de_estudiante(config_de(ev), est) if est else None
        ev.mi_grupo = g['nombre'] if g else None
    return render(request, 'aula/eventos.html', {'eventos': lista, 'organiza': organiza, 'colegio': colegio, 'base': _base(request)})


def _banco():
    with open(BANCO, encoding='utf-8') as f:
        return json.load(f)


@login_required
def configurar(request, eid):
    ev = _evento(request, eid)
    if not es_organizador(request, ev):
        return HttpResponseForbidden('Solo los organizadores configuran el evento.')
    puede_admin = es_admin_del_evento(request, ev)
    if request.method == 'POST':
        accion = request.POST.get('accion')
        if accion == 'activar':
            ev.activo = not ev.activo
            ev.save(update_fields=['activo'])
            messages.success(request, 'Evento ACTIVO: ya lo ven los estudiantes.' if ev.activo else 'Evento apagado: los estudiantes ya no lo ven.')
        elif accion == 'config':
            c = config_de(ev)
            def entero(k, lo, hi):
                try:
                    c[k] = max(lo, min(hi, int(request.POST.get(k) or c[k])))
                except ValueError:
                    pass
            entero('bloques', 1, 6); entero('minutos', 5, 60); entero('descanso', 1, 15)
            entero('cada', 1, 20); entero('por_parada', 1, 2); entero('bono', 0, 300)
            # Por cada juego: para qué grados va y con qué dificultad
            por_juego, elegidos = {}, []
            for j in juegos_del_evento(ev):
                grados = sorted({int(g) for g in request.POST.getlist('g_' + j[0]) if g.lstrip('-').isdigit() and int(g) in todos_los_grados()})
                dif, vel = request.POST.get('d_' + j[0]), request.POST.get('v_' + j[0])
                por_juego[j[0]] = {'grados': grados, 'dificultad': dif if dif in dict(DIFICULTADES) else 'auto',
                                   'velocidad': vel if vel in JuegoAula.RITMO else 'normal'}
                if grados:
                    elegidos.append(j[0])
            if not elegidos:
                messages.warning(request, 'Escoja al menos un juego para algún grado.')
                return redirect('aula:evento_configurar', eid=ev.pk)
            c['juegos'], c['por_juego'] = elegidos, por_juego
            titulo = ' '.join((request.POST.get('titulo') or '').split())[:80]
            if titulo:
                ev.titulo = titulo
            ev.config = c
            ev.save(update_fields=['config', 'titulo'])
            messages.success(request, 'Configuración guardada.')
        elif accion == 'grupos':
            c = config_de(ev)
            nuevos = []
            for g in grupos(c):
                if request.POST.get('gx_' + g['id']):
                    continue                      # se quitó
                nuevos.append(_leer_grupo(request, g['id'], g, 'g'))
            nombre = ' '.join((request.POST.get('nuevo_nombre') or '').split())[:40]
            if nombre:
                base = ''.join(ch for ch in nombre.lower() if ch.isalnum())[:20] or 'grupo'
                gid, k = base, 2
                while any(x['id'] == gid for x in nuevos):
                    gid, k = f'{base}{k}', k + 1
                nuevos.append(_leer_grupo(request, 'nuevo', {'id': gid, 'nombre': nombre, 'grados': [], 'nivel': 0}, 'n'))
            if not nuevos:
                messages.warning(request, 'Debe quedar al menos un grupo.')
                return redirect('aula:evento_configurar', eid=ev.pk)
            repetidos = [x for g in nuevos for x in g['grados'] if sum(x in h['grados'] for h in nuevos) > 1]
            if repetidos:
                messages.warning(request, f'Un grado solo puede estar en un grupo: revise {", ".join(etiqueta_grado(x) for x in sorted(set(repetidos)))}.')
                return redirect('aula:evento_configurar', eid=ev.pk)
            c['grupos'] = nuevos
            ev.config = c
            ev.save(update_fields=['config'])
            messages.success(request, 'Grupos guardados.')
        elif accion == 'participantes':
            c = config_de(ev)
            modo = request.POST.get('modo')
            c['participantes'] = {'modo': modo if modo in ('grados', 'cursos', 'estudiantes') else 'grados',
                                  'cursos': [int(x) for x in request.POST.getlist('cursos') if x.isdigit()],
                                  'estudiantes': [int(x) for x in request.POST.getlist('estudiantes') if x.isdigit()]}
            ev.config = c
            ev.save(update_fields=['config'])
            messages.success(request, 'Participantes guardados.')
        elif accion in ('pegar', 'importar'):
            ciclo, cat = request.POST.get('ciclo'), request.POST.get('categoria')
            if not grupo_por_id(config_de(ev), ciclo) or cat not in {k for k, _, _ in CATEGORIAS}:
                messages.warning(request, 'Escoja el grupo y el pensamiento.')
                return redirect('aula:evento_configurar', eid=ev.pk)
            if accion == 'pegar':
                preguntas, origen = leer_preguntas(request.POST.get('texto') or '', 300), 'propia'
            else:
                j = _juegos_salon(ev).filter(pk=request.POST.get('juego') or 0).first()
                if j is None:
                    messages.warning(request, 'Escoja un juego del salón virtual.')
                    return redirect('aula:evento_configurar', eid=ev.pk)
                preguntas, origen = j.preguntas, f'Salón virtual: {j.titulo}'
            buenas = [p for p in preguntas if 2 <= len(p.get('opciones', [])) <= 8 and sum(1 for o in p['opciones'] if o.get('correcta')) == 1]
            ev.preguntas = list(ev.preguntas) + [{'ciclo': ciclo, 'categoria': cat, 'texto': p['texto'], 'opciones': p['opciones'], 'origen': origen} for p in buenas]
            ev.save(update_fields=['preguntas'])
            malas = len(preguntas) - len(buenas)
            messages.success(request, f'Se agregaron {len(buenas)} pregunta(s).' + (f' {malas} se saltaron (sin opciones o sin una sola correcta).' if malas else ''))
        elif accion == 'quitar':
            try:
                k = int(request.POST.get('i'))
                ev.preguntas = [p for i, p in enumerate(ev.preguntas) if i != k]
                ev.save(update_fields=['preguntas'])
            except (TypeError, ValueError):
                pass
        elif accion == 'banco':
            ev.preguntas = list(ev.preguntas) + [p for p in _banco() if p not in ev.preguntas]
            ev.save(update_fields=['preguntas'])
            messages.success(request, 'Se agregó el banco inicial de preguntas.')
        elif accion == 'alcance' and ev.colegio_id:
            ev.alcance = 'codigo' if request.POST.get('alcance') == 'codigo' else 'colegio'
            ev.save(update_fields=['alcance'])
            messages.success(request, 'Ahora entra quien tenga el código del evento.' if ev.alcance == 'codigo' else 'Ahora solo participan los estudiantes del colegio.')
        elif accion == 'organizadores' and puede_admin:
            from notas.models import Docente
            ids = request.POST.getlist('organizadores')
            usuarios = [d.user for d in Docente.objects.filter(colegio=ev.colegio, user_id__in=ids)] if ev.colegio_id else []
            ev.organizadores.set(usuarios)
            messages.success(request, f'Organizadores: {len(usuarios)} docente(s), además de la administración.')
        elif accion == 'reiniciar':
            n = ev.participaciones.count()
            ev.participaciones.all().delete()
            messages.success(request, f'Se borraron {n} participación(es): todos empiezan de cero.')
        elif accion == 'eliminar' and puede_admin:
            ev.delete()
            messages.info(request, 'Evento eliminado.')
            return redirect('aula:eventos')
        return redirect('aula:evento_configurar', eid=ev.pk)
    from notas.models import Curso, Docente, Estudiante
    c = config_de(ev)
    conteo = {}
    for p in ev.preguntas:
        conteo[(p.get('ciclo'), p.get('categoria'))] = conteo.get((p.get('ciclo'), p.get('categoria')), 0) + 1
    tabla = [{'ciclo': g['nombre'], 'cifras': [conteo.get((g['id'], ca), 0) for ca, _, _ in CATEGORIAS]} for g in grupos(c)]
    base_grados = grados_del_colegio(ev.colegio) if ev.colegio_id and ev.alcance == 'colegio' else todos_los_grados()
    grados_cols = sorted(set(base_grados) | {x for g in grupos(c) for x in g['grados']})
    cursos = Curso.objects.filter(colegio=ev.colegio).order_by('grado', 'nombre') if ev.colegio_id else Curso.objects.none()
    estudiantes = Estudiante.objects.filter(colegio=ev.colegio, curso__isnull=False).select_related('user', 'curso').order_by('curso__grado', 'curso__nombre', 'user__last_name') if ev.colegio_id else Estudiante.objects.none()
    juegos_salon = _juegos_salon(ev).select_related('aula').order_by('-pk')[:200]
    filas_juegos = []
    for j in juegos_del_evento(ev):
        pj = c['por_juego'].get(j[0]) or {}
        grados = pj.get('grados', grados_cols if j[0] in c['juegos'] else [])
        if j[0] not in c['juegos']:
            grados = []
        filas_juegos.append({'id': j[0], 'nombre': j[1], 'estilo': j[2], 'grados': grados, 'dificultad': pj.get('dificultad', 'auto'),
                             'velocidad': pj.get('velocidad', 'normal'), 'con_velocidad': j[2] in ('arcade', 'propio') or j[0] == 'speedrun'})
    return render(request, 'aula/evento_configurar.html', {
        'ev': ev, 'c': c, 'juegos': JUEGOS, 'filas_juegos': filas_juegos, 'velocidades': JuegoAula.VELOCIDADES, 'grados': [(g, etiqueta_grado(g)) for g in grados_cols],
        'todos_grados': [(g, etiqueta_grado(g)) for g in todos_los_grados()], 'niveles': NIVELES,
        'grupos': [dict(g, rango=rango_grados(g)) for g in grupos(c)], 'cursos': cursos, 'estudiantes': estudiantes,
        'part': c['participantes'], 'dificultades': DIFICULTADES, 'estilos': ESTILOS, 'categorias': CATEGORIAS, 'tabla': tabla,
        'preguntas': list(enumerate(ev.preguntas)), 'juegos_salon': juegos_salon, 'es_admin': puede_admin,
        'docentes': Docente.objects.filter(colegio=ev.colegio).select_related('user').order_by('user__last_name') if ev.colegio_id else [],
        'enlace': request.build_absolute_uri(reverse('aula:evento_inscribirse', args=[ev.codigo])),
        'organizadores': set(ev.organizadores.values_list('pk', flat=True)), 'base': _base(request)})


def _juegos_salon(ev):
    """Los juegos del salón virtual de donde se pueden importar preguntas."""
    if ev.colegio_id:
        return JuegoAula.objects.filter(aula__colegio=ev.colegio)
    return JuegoAula.objects.filter(aula__grupo__propietario__usuario=ev.creador) if ev.creador_id else JuegoAula.objects.none()


def jugar(request, eid):
    ev = _evento(request, eid)
    organiza = es_organizador(request, ev)
    if not ev.activo and not organiza:
        raise Http404
    c = config_de(ev)
    p = participante(request, ev)
    if ev.alcance == 'codigo':
        est = None
        grupo = (grupo_por_id(c, p.ciclo) or next((g for g in grupos(c) if p.grado in g['grados']), None)) if p else None
        if not grupo and not organiza:
            return redirect('aula:evento_inscribirse', codigo=ev.codigo)
    else:
        if not request.user.is_authenticated and not organiza:
            return redirect_to_login(request.get_full_path())
        est = _estudiante(request)
        grupo = grupo_de_estudiante(c, est)
        if not organiza and not grupo:
            messages.info(request, 'Usted no está entre los participantes de este evento.')
            return redirect('aula:eventos')
    grado = (int(est.curso.grado) if est and est.curso_id else p.grado if p else None)
    if not organiza and not juegos_para(c, [grado], juegos_del_evento(ev)):
        messages.info(request, 'Este evento no tiene juegos para su grado.')
        return redirect('aula:eventos' if request.user.is_authenticated else 'aula:evento_entrar')
    if grupo is None:          # prueba del organizador: escoge el grupo
        grupo = grupo_por_id(c, request.GET.get('ciclo')) or grupos(c)[0]
    from .views_logica import niveles
    datos = {
        'evento': ev.pk, 'titulo': ev.titulo, 'prueba': p is None and est is None, 'ciclo': grupo['id'],
        'grupo': {'id': grupo['id'], 'nombre': grupo['nombre'], 'grados': rango_grados(grupo), 'nivel': grupo.get('nivel', 0), 'gmax': max(grupo['grados'] or [11])},
        'config': c, 'juegos': juegos_para(c, [grado] if grado is not None else grupo['grados'], juegos_del_evento(ev)),
        'dificultad': {j[0]: dificultad(c, j[0]) for j in JUEGOS},
        'propios': {}, 'motor': {},
        'ritmo': {j[0]: JuegoAula.RITMO.get((c['por_juego'].get(j[0]) or {}).get('velocidad', 'normal'), 1) for j in juegos_del_evento(ev)},
        'niveles': {j: niveles(j) for j in ('tangram', 'trancon', 'safari', 'bango', 'kadogemo', 'nonograma', 'ranas', 'cerditos', 'kiriku', 'laberinto', 'sokoban', 'bloque', 'conejos', 'perrito')},
        'usuario': request.user.pk or (p.token[:8] if p else 'anon'),
    }
    if p is not None or est is not None:
        datos['servidor'] = _estado(p, c) if p else None
    # Los juegos propios: su tipo y sus preguntas; y con qué juego arcade se juega cada reto
    for jid, _, _ in datos['juegos']:
        if jid.startswith('p_'):
            j = JuegoAula.objects.filter(pk=int(jid[2:])).first()
            if j:
                datos['propios'][jid] = {'tipo': j.tipo, 'titulo': j.titulo, 'preguntas': [dict(q, i=k) for k, q in enumerate(j.preguntas)]}
        t = tipo_motor(jid, datos['propios'])
        if t:
            datos['motor'][jid] = t
    motores = sorted(set(datos['motor'].values()))
    scripts = ['tangram', 'trancon', 'cerditos', 'ranas', 'bango', 'kadogemo', 'kiriku', 'laberinto_colores', 'hanoi', 'fila',
               'nonograma', 'geoplano', 'regletas', 'speedrun', 'fijas', 'sokoban', 'bloque', 'cubo', 'conejos', 'perrito', 'caperucita', 'ladron']
    return render(request, 'aula/evento_jugar.html', {'ev': ev, 'datos': datos, 'grupos': grupos(c), 'organiza': organiza, 'scripts': scripts, 'motores': motores,
                                                      'categorias': CATEGORIAS, 'base': _base(request), 'hide_cuenta': not request.user.is_authenticated})


def entrar_codigo(request):
    """Para los eventos abiertos: se escribe el código del evento."""
    codigo = (request.POST.get('codigo') or request.GET.get('codigo') or '').strip().upper()
    if codigo:
        if Evento.objects.filter(codigo=codigo, alcance='codigo').exists():
            return redirect('aula:evento_inscribirse', codigo=codigo)
        messages.warning(request, 'No hay ningún evento abierto con ese código.')
    return render(request, 'aula/evento_entrar.html', {'base': _base(request), 'hide_cuenta': not request.user.is_authenticated})


def inscribirse(request, codigo):
    """Evento abierto: el participante escribe su nombre, su institución y su grado (no necesita cuenta)."""
    ev = get_object_or_404(Evento, codigo=(codigo or '').upper(), alcance='codigo')
    c = config_de(ev)
    if participante(request, ev):
        return redirect('aula:evento', eid=ev.pk)
    grados = sorted({x for g in grupos(c) for x in g['grados']})
    error = ''
    if request.method == 'POST':
        nombre = ' '.join((request.POST.get('nombre') or '').split())[:120]
        institucion = ' '.join((request.POST.get('institucion') or '').split())[:120]
        try:
            grado = int(request.POST.get('grado'))
        except (TypeError, ValueError):
            grado = None
        g = next((x for x in grupos(c) if grado in x['grados']), None)
        if not ev.activo:
            error = 'El evento todavía no está abierto.'
        elif len(nombre) < 5 or not institucion or g is None:
            error = 'Escriba su nombre completo, su institución y escoja su grado.'
        else:
            import secrets
            p = ParticipacionEvento.objects.create(evento=ev, nombre=nombre, institucion=institucion, grado=grado, ciclo=g['id'],
                                                   token=secrets.token_urlsafe(24))
            request.session[clave_sesion(ev)] = p.token
            return redirect('aula:evento', eid=ev.pk)
    sugerido = {'nombre': '', 'institucion': '', 'grado': None}
    est = _estudiante(request)
    if est is not None:
        sugerido = {'nombre': est.user.get_full_name(), 'institucion': est.colegio.nombre, 'grado': est.curso.grado if est.curso_id else None}
    if request.method == 'POST':
        sugerido.update({k: request.POST.get(k, '') for k in ('nombre', 'institucion')})
    return render(request, 'aula/evento_inscribirse.html', {
        'ev': ev, 'grados': [(x, etiqueta_grado(x)) for x in grados], 'error': error, 'sugerido': sugerido, 'post': request.POST,
        'base': _base(request), 'hide_cuenta': not request.user.is_authenticated})


@login_required
def resultados(request, eid):
    """Los resultados quedan en la base de datos (una participación por estudiante o inscrito).
    Se filtran por grupo (o todos juntos), por grado y por nombre, curso o institución."""
    ev = _evento(request, eid)
    if not es_organizador(request, ev):
        return HttpResponseForbidden('Solo los organizadores ven todos los resultados.')
    c = config_de(ev)
    gsel, gr, q = request.GET.get('grupo', ''), request.GET.get('grado', ''), (request.GET.get('q') or '').strip().lower()

    def filtrar(lista):
        out = []
        for p in lista:
            if gr.lstrip('-').isdigit() and grado_de(p) != int(gr):
                continue
            if q and q not in f'{p.nombre_completo} {p.de_donde}'.lower():
                continue
            out.append(p)
        for k, p in enumerate(out, 1):        # el puesto dentro de lo que se está viendo
            p.puesto = k
        return out
    if gsel == 'todos':
        tablas = [('Todos los grupos juntos', '', filtrar(ranking(ev)))]
    else:
        tablas = [(g['nombre'], rango_grados(g), filtrar(ranking(ev, g['id']))) for g in grupos(c) if not gsel or g['id'] == gsel]
    nombres = {g['id']: g['nombre'] for g in grupos(c)}
    for _, _, filas in tablas:
        for p in filas:
            p.grupo_nombre = nombres.get(p.ciclo, p.ciclo)
            g = grado_de(p)
            p.grado_txt = etiqueta_grado(g) if g is not None else ''
    if request.GET.get('csv'):
        r = HttpResponse(content_type='text/csv; charset=utf-8')
        r['Content-Disposition'] = f'attachment; filename="resultados-evento-{ev.pk}.csv"'
        r.write('\ufeff')
        w = csv.writer(r)
        w.writerow(['Grupo', 'Puesto', 'Participante', 'Grado', 'Curso o institución', 'Puntos', 'Preguntas bien', 'Tiempo efectivo (s)', 'Terminó'])
        for n, _, filas in tablas:
            for p in filas:
                w.writerow([p.grupo_nombre, p.puesto, p.nombre_completo, p.grado_txt, p.de_donde,
                            p.puntos, p.bonos, round(p.tiempo_efectivo, 1), 'sí' if p.terminada else 'no'])
        return r
    grados_hay = sorted({g for g in (grado_de(p) for p in ev.participaciones.select_related('estudiante__curso')) if g is not None})
    return render(request, 'aula/evento_resultados.html', {
        'ev': ev, 'tablas': tablas, 'grupos': grupos(c), 'gsel': gsel, 'gr': gr, 'q': request.GET.get('q', ''),
        'grados': [(g, etiqueta_grado(g)) for g in grados_hay], 'consulta': request.GET.urlencode(), 'base': _base(request)})


# ---------------------------------------------------------------------------
# Lo que manda el juego (el servidor cuenta y califica)
# ---------------------------------------------------------------------------
def _estado(p, c):
    return {'puntos': p.puntos, 'bonos': p.bonos, 'preguntas': p.preguntas_hechas, 'bloque': p.bloque, 'terminada': p.terminada,
            'tiempo': round(p.tiempo_efectivo, 1), 'segundos': round(p.segundos_ultimo_punto, 1), 'secuencia': p.secuencia,
            'debe': max(0, (p.puntos // c['cada']) * c['por_parada'] - p.preguntas_hechas)}


def _participacion(request, ev):
    if not ev.activo:
        return None
    return participante(request, ev, crear=True)


def _leer_grupo(request, clave, g, pref):
    nombre = ' '.join((request.POST.get(f'{pref}n_{clave}') or g['nombre']).split())[:40] or g['nombre']
    grados = sorted({int(x) for x in request.POST.getlist(f'{pref}g_{clave}') if x.lstrip('-').isdigit() and int(x) in todos_los_grados()})
    try:
        nivel = max(0, min(2, int(request.POST.get(f'{pref}l_{clave}', g.get('nivel', 0)))))
    except ValueError:
        nivel = g.get('nivel', 0)
    return {'id': g['id'], 'nombre': nombre, 'grados': grados, 'nivel': nivel}


@require_POST
def registro(request, eid):
    """Llegan, en orden, los retos superados y los cambios de bloque (pueden llegar tarde si no había internet)."""
    ev = _evento(request, eid)
    c = config_de(ev)
    p = _participacion(request, ev)
    if p is None:
        return JsonResponse({'ok': True, 'prueba': True})
    try:
        lista = json.loads(request.body or b'{}').get('eventos') or []
    except (ValueError, AttributeError):
        lista = []
    tope = c['bloques'] * c['minutos'] * 60 + 30
    transcurrido = (timezone.now() - p.empezada).total_seconds() + 60
    for e in lista[:200]:
        try:
            seq, tipo, t = int(e.get('seq')), e.get('tipo'), float(e.get('t') or 0)
        except (TypeError, ValueError, AttributeError):
            continue
        if seq <= p.secuencia or p.terminada:
            continue
        p.secuencia = seq
        t = max(0.0, min(t, tope, transcurrido))
        g = grado_de(p)
        permitidos = {j[0] for j in juegos_para(c, [int(g)] if g is not None else todos_los_grados(), juegos_del_evento(ev))}
        if tipo == 'punto' and e.get('juego') in permitidos:
            ultimo = next((r for r in reversed(p.registro) if r.get('tipo') == 'punto'), None)
            if ultimo and t - ultimo.get('t', 0) < 2:      # demasiado rápido para un reto: no cuenta
                continue
            p.puntos += 1
            p.segundos_ultimo_punto = max(p.segundos_ultimo_punto, t)
            p.registro = (p.registro + [{'tipo': 'punto', 'juego': e.get('juego'), 'nivel': e.get('nivel'), 't': round(t, 1)}])[-500:]
        elif tipo == 'bloque':
            try:
                p.bloque = max(p.bloque, min(c['bloques'], int(e.get('n'))))
            except (TypeError, ValueError):
                pass
        elif tipo == 'fin':
            p.terminada = True
    p.save()
    return JsonResponse({'ok': True, **_estado(p, c)})


def pregunta(request, eid):
    """La siguiente pregunta de competencia (solo si ya le toca). Las opciones van revueltas y sin decir cuál es."""
    ev = _evento(request, eid)
    c = config_de(ev)
    p = _participacion(request, ev)
    prueba = p is None
    if prueba and not es_organizador(request, ev):
        return JsonResponse({'pregunta': None})
    ciclo = p.ciclo if p else request.GET.get('ciclo', 'exploradores')
    if p and not _estado(p, c)['debe']:
        return JsonResponse({'pregunta': None})
    if p and p.pendiente:
        q = p.pendiente
    else:
        hechas = p.preguntas_hechas if p else random.randint(0, 2)
        cat = CATEGORIAS[hechas % 3][0]
        del_ciclo = [(i, x) for i, x in enumerate(ev.preguntas) if x.get('ciclo') == ciclo]
        opciones = [(i, x) for i, x in del_ciclo if x.get('categoria') == cat] or del_ciclo
        if not opciones:
            return JsonResponse({'pregunta': None})
        vistas = set(p.vistas) if p else set()
        nuevas = [(i, x) for i, x in opciones if i not in vistas] or opciones
        i, x = random.choice(nuevas)
        orden = list(range(len(x['opciones'])))
        random.shuffle(orden)
        q = {'i': i, 'orden': orden, 'categoria': x.get('categoria')}
        if p:
            p.pendiente = q
            p.save(update_fields=['pendiente'])
    x = ev.preguntas[q['i']] if q['i'] < len(ev.preguntas) else None
    if x is None:
        if p:
            p.pendiente = {}
            p.save(update_fields=['pendiente'])
        return JsonResponse({'pregunta': None})
    nombres = {k: n for k, n, _ in CATEGORIAS}
    return JsonResponse({'pregunta': {'texto': x['texto'], 'opciones': [x['opciones'][k]['texto'] for k in q['orden']],
                                      'categoria': nombres.get(q.get('categoria'), ''), 'prueba': prueba,
                                      **({'clave': [x['opciones'][k].get('correcta', False) for k in q['orden']]} if prueba else {})}})


@require_POST
def responder(request, eid):
    ev = _evento(request, eid)
    c = config_de(ev)
    p = _participacion(request, ev)
    if p is None or not p.pendiente:
        return JsonResponse({'ok': False})
    try:
        k = int(json.loads(request.body or b'{}').get('k'))
    except (TypeError, ValueError, AttributeError):
        k = -1
    q = p.pendiente
    x = ev.preguntas[q['i']] if q['i'] < len(ev.preguntas) else None
    bien = bool(x and 0 <= k < len(q['orden']) and x['opciones'][q['orden'][k]].get('correcta'))
    correcta = next((j for j, o in enumerate(q['orden']) if x and x['opciones'][o].get('correcta')), None)
    p.preguntas_hechas += 1
    if bien:
        p.bonos += 1
    p.vistas = (p.vistas + [q['i']])[-500:]
    p.pendiente = {}
    p.registro = (p.registro + [{'tipo': 'pregunta', 'bien': bien}])[-500:]
    p.save()
    return JsonResponse({'ok': True, 'bien': bien, 'correcta': correcta, 'bono': c['bono'], **_estado(p, c)})
