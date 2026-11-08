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

from . import planilla_preguntas
from .invertida import leer_preguntas
from .models import Evento, GrabacionEvento, JuegoAula, ParticipacionEvento

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
          'participantes': {'modo': 'grados', 'cursos': [], 'estudiantes': []},   # modo: grados | cursos | estudiantes
          # Eventos abiertos: inscripción de los de fuera. aprobacion: el organizador aprueba cada una;
          # cupo_colegio: máximo por institución; cupo_nivel: máximo por institución en cada nivel (grupo); 0 = sin límite
          'inscripcion': {'abierta': False, 'aprobacion': False, 'cupo_colegio': 0, 'cupo_nivel': 0},
          # Supervisión de la prueba (las grabaciones se borran solas a los `dias`):
          #   camara: cámara y micrófono encendidos y grabados · juego: se graba lo que hace en la prueba (celular y
          #   computador) · pantalla: en computador se graba la pantalla completa · salidas: registro de cada vez que
          #   sale de la prueba (otra pestaña, ventana o aplicación), con la hora y el tiempo fuera
          #   guardar: 'video' (trozos de 30 s) o 'pantallazos' (una imagen con cada reto y cada pregunta: gasta muy pocos datos)
          'vigilancia': {'activa': False, 'dias': 30, 'camara': True, 'juego': True, 'pantalla': False, 'salidas': True, 'guardar': 'video'},
          # Retos arcade: 'preguntas' (las cargadas para los juegos y, si faltan, el banco 6.º–11.º del grado),
          # 'propias' (solo las cargadas para los juegos), 'banco' (solo el banco 6.º–11.º) u 'operaciones'
          'arcade': 'preguntas',
          # Fechas (hora de Colombia, 'AAAA-MM-DDTHH:MM'; vacío = sin límite): hasta cuándo se inscriben y cuándo se presenta
          'fechas': {'inscripcion_hasta': '', 'prueba_desde': '', 'prueba_hasta': ''},
          # Inicio programado: el evento apagado se activa solo a esta hora ('AAAA-MM-DDTHH:MM', hora de Colombia)
          'activar_en': '',
          # Veedores: profesores (o grupos de profesores) invitados que ven los resultados en vivo con un enlace de solo lectura
          'veedores': [],
          # Podio de colegios: de cada colegio cuenta su mejor estudiante de cada nivel, con el peso del nivel
          'podio_colegios': {'activo': True, 'pesos': {}}}
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


def graba(v):
    """¿La supervisión de este evento graba video (cámara, juego o pantalla)?"""
    return bool(v.get('activa') and (v.get('camara') or v.get('juego') or v.get('pantalla')))


MOMENTOS = {'reto': 'reto nuevo', 'pregunta': 'pregunta', 'competencia': 'pregunta de competencia', 'volvio': 'volvió a la prueba',
            'salio': 'salió de la prueba', 'cada': 'control', 'inicio': 'inicio'}


def ext_de(tipo):
    """Extensión del archivo según su tipo (los pantallazos guardan el momento después de «;»)."""
    t = (tipo or '').split(';')[0]
    return {'image/jpeg': 'jpg', 'image/png': 'png', 'image/webp': 'webp'}.get(t, 'mp4' if 'mp4' in t else 'webm')


def texto_supervision(v):
    """Las condiciones de supervisión, en palabras, para la inscripción, la planilla y la portada."""
    if not v.get('activa'):
        return ''
    partes = []
    if v.get('camara'):
        partes.append('se toma la imagen de la cámara en cada pantallazo' if v.get('guardar') == 'pantallazos' and (v.get('juego') or v.get('pantalla'))
                      else ('se toman fotos con la cámara en cada reto y en cada pregunta' if v.get('guardar') == 'pantallazos'
                            else 'se graban la cámara y el micrófono (imagen y voz)'))
    foto = v.get('guardar') == 'pantallazos'
    if v.get('pantalla') or v.get('juego'):
        if foto:
            partes.append('se toman pantallazos de la pantalla de la prueba en cada reto y en cada pregunta'
                          + (' (en computador, de la pantalla completa)' if v.get('pantalla') else '')
                          + ' para supervisar que no se salga de ella')
        elif v.get('pantalla'):
            partes.append('se graba la pantalla (en computador, la pantalla completa; en celular o tableta, lo que hace dentro de la prueba)'
                          ' para supervisar que no se salga de la prueba')
        else:
            partes.append('se graba la pantalla de la prueba (lo que hace mientras juega) para supervisar que no se salga de ella')
    if v.get('salidas'):
        partes.append('se lleva un registro de cada vez que el estudiante sale de la prueba (cambia de pestaña, ventana o aplicación),'
                      ' con la hora y el tiempo que estuvo fuera')
    if not partes:
        return ''
    t = 'Para supervisar la prueba ' + (', '.join(partes[:-1]) + ' y ' + partes[-1] if len(partes) > 1 else partes[0]) + '.'
    if graba(v):
        t += f' {"Los pantallazos" if v.get("guardar") == "pantallazos" else "Las grabaciones"} solo los ven los organizadores y se borran a los {v.get("dias", 30)} días.'
    if v.get('salidas'):
        t += ' El registro de salidas lo ven los organizadores y los veedores del evento.'
    return t


def config_de(evento):
    c = copy.deepcopy(CONFIG)
    c.update({k: v for k, v in (evento.config or {}).items() if k in CONFIG})
    c['inscripcion'] = dict(CONFIG['inscripcion'], **(c.get('inscripcion') or {}))
    c['vigilancia'] = dict(CONFIG['vigilancia'], **(c.get('vigilancia') or {}))
    c['fechas'] = dict(CONFIG['fechas'], **(c.get('fechas') or {}))
    c['podio_colegios'] = dict(CONFIG['podio_colegios'], **(c.get('podio_colegios') or {}))
    return c


def _fecha(texto):
    from datetime import datetime
    try:
        return timezone.make_aware(datetime.fromisoformat(texto)) if texto else None
    except (ValueError, TypeError):
        return None


DIAS = ['lunes', 'martes', 'miércoles', 'jueves', 'viernes', 'sábado', 'domingo']
MESES = ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre']


def fecha_bonita(d):
    """sábado 14 de noviembre, 12:00 a. m."""
    d = timezone.localtime(d)
    h = d.hour % 12 or 12
    return f"{DIAS[d.weekday()]} {d.day} de {MESES[d.month - 1]}, {h}:{d.minute:02d} {'a. m.' if d.hour < 12 else 'p. m.'}"


def ventana(c):
    """(inscripción abierta por fecha, prueba abierta por fecha, texto que lo explica) según las fechas del evento."""
    ahora, f = timezone.now(), c['fechas']
    ins_hasta, desde, hasta = _fecha(f['inscripcion_hasta']), _fecha(f['prueba_desde']), _fecha(f['prueba_hasta'])
    bonito = fecha_bonita
    ins = ins_hasta is None or ahora <= ins_hasta
    prueba = (desde is None or ahora >= desde) and (hasta is None or ahora <= hasta)
    if desde and ahora < desde:
        texto = f'La prueba abre el {bonito(desde)}'
    elif hasta and ahora > hasta:
        texto = f'La prueba cerró el {bonito(hasta)}'
    elif hasta:
        texto = f'La prueba está abierta hasta el {bonito(hasta)}'
    else:
        texto = ''
    return {'inscripcion': ins, 'prueba': prueba, 'texto': texto,
            'ins_hasta': bonito(ins_hasta) if ins_hasta else '', 'desde': bonito(desde) if desde else '', 'hasta': bonito(hasta) if hasta else ''}


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
    ev = al_dia(get_object_or_404(Evento, pk=eid))
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
    qs = evento.participaciones.filter(estado='aprobada').select_related('estudiante__user', 'estudiante__curso', 'estudiante__colegio')
    if ciclo:
        qs = qs.filter(ciclo=ciclo)
    lista = sorted(qs, key=lambda p: (-p.puntos, p.tiempo_efectivo, p.pk))
    for i, p in enumerate(lista, 1):
        p.puesto = i
    return lista


def colegio_de(p):
    """El colegio con que compite el participante: su institución (inscritos) o el colegio de su cuenta."""
    if p.estudiante_id:
        return p.estudiante.colegio.nombre if p.estudiante.colegio_id else ''
    return p.institucion


def podio_colegios(ev, c=None):
    """Podio de colegios. De cada colegio cuenta SOLO su mejor estudiante de cada nivel (el mejor puesto del nivel).
    Puntaje = suma de (puntos de ese estudiante × peso del nivel). Desempate: menor suma de tiempos efectivos de sus
    representantes; luego, más niveles con representante."""
    c = c or config_de(ev)
    pesos = c['podio_colegios'].get('pesos') or {}
    colegios = {}
    for g in grupos(c):
        vistos = set()
        for p in ranking(ev, g['id']):          # ya viene ordenado: el primero de cada colegio es su representante
            nombre = colegio_de(p)
            clave = normalizar(nombre)
            if not clave or clave in vistos:
                continue
            vistos.add(clave)
            try:
                peso = float(pesos.get(g['id'], 1) or 1)
            except (TypeError, ValueError):
                peso = 1.0
            x = colegios.setdefault(clave, {'colegio': nombre, 'puntaje': 0.0, 'tiempo': 0.0, 'niveles': {}, 'n': 0})
            x['puntaje'] += p.puntos * peso
            x['tiempo'] += p.tiempo_efectivo
            x['n'] += 1
            x['niveles'][g['id']] = {'nombre': p.nombre_completo, 'puntos': p.puntos, 'puesto': p.puesto, 'tiempo': round(p.tiempo_efectivo)}
    lista = sorted(colegios.values(), key=lambda x: (-x['puntaje'], x['tiempo'], -x['n'], x['colegio'].lower()))
    for i, x in enumerate(lista, 1):
        x['puesto'] = i
        x['puntaje'] = round(x['puntaje'], 2) if x['puntaje'] != int(x['puntaje']) else int(x['puntaje'])
        x['tiempo'] = round(x['tiempo'])
        x['por_nivel'] = [(g['nombre'], x['niveles'].get(g['id'])) for g in grupos(c)]
    return lista


def al_dia(ev):
    """Si el evento está apagado y ya llegó la hora programada, lo activa."""
    cuando = (ev.config or {}).get('activar_en')
    if not ev.activo and cuando and _fecha(cuando) and _fecha(cuando) <= timezone.now():
        ev.activo = True
        ev.config = dict(ev.config, activar_en='', activado_solo=cuando)
        ev.save(update_fields=['activo', 'config'])
    return ev


def activar_programados(throttle=False):
    """Activa los eventos cuya hora de inicio programada ya pasó. Con throttle, revisa a lo sumo cada 30 s."""
    from django.core.cache import cache
    if throttle and not cache.add('eventos-programados', 1, 30):
        return
    for ev in Evento.objects.filter(activo=False, config__has_key='activar_en').exclude(config__activar_en=''):
        al_dia(ev)


def hay_eventos_activos(request):
    colegio = getattr(request, 'colegio', None)
    if colegio is not None:
        activar_programados(throttle=True)
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
    from salon_digital.limites import a_planes, permite
    premium = permite(request.user, 'eventos', colegio)          # en Mi Salón Virtual, los eventos son de Premium
    if request.method == 'POST':
        if not organiza:
            return HttpResponseForbidden('Solo los docentes crean eventos.')
        if not premium:
            return a_planes(request, 'eventos')
        titulo = ' '.join((request.POST.get('titulo') or '').split())[:80]
        if not titulo:
            messages.warning(request, 'Escriba el nombre del evento.')
            return redirect('aula:eventos')
        alcance = request.POST.get('alcance') if colegio is not None else 'codigo'
        ev = Evento.objects.create(colegio=colegio, creador=request.user, titulo=titulo, alcance=alcance if alcance in ('colegio', 'codigo') else 'colegio',
                                   config=copy.deepcopy(CONFIG), preguntas=_banco())
        messages.success(request, f'Se creó «{ev.titulo}». Está apagado: configúrelo y actívelo cuando quiera que los participantes lo vean.')
        return redirect('aula:evento_configurar', eid=ev.pk)
    activar_programados()
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
        f = None if ev.activo else _fecha((ev.config or {}).get('activar_en'))
        ev.programado = fecha_bonita(f) if f else ''
        lista.append(ev)
    for ev in lista:
        g = grupo_de_estudiante(config_de(ev), est) if est else None
        ev.mi_grupo = g['nombre'] if g else None
    return render(request, 'aula/eventos.html', {'eventos': lista, 'organiza': organiza, 'colegio': colegio, 'base': _base(request),
                                                 'premium': premium})


def _banco():
    with open(BANCO, encoding='utf-8') as f:
        return json.load(f)


def grupo_para(c, nivel='', grado=None):
    """El grupo del evento para una pregunta: por el nombre o id del nivel; si no, el que tiene ese grado."""
    if nivel:
        n = normalizar(nivel)
        g = next((g for g in grupos(c) if normalizar(g['nombre']) == n or g['id'] == n), None)
        if g:
            return g
    if grado is not None:
        return next((g for g in grupos(c) if grado in g['grados']), None)
    return None


def es_de_juego(x):
    """Pregunta para los retos de juego (arcade). Las demás son de competencia."""
    return x.get('uso') == 'juegos'


def de_competencia(ev):
    return [x for x in ev.preguntas if not es_de_juego(x)]


def agregar_preguntas(ev, preguntas, origen, ciclo_defecto=None, cat_defecto='newton', uso='competencia'):
    """Agrega preguntas al evento (cada una a su grupo por nivel o grado), para la competencia o para los retos de
    juego. Una pregunta no puede estar en las dos (las de juego se ven en el navegador). Devuelve (agregadas, saltadas)."""
    c = config_de(ev)
    ya = {(x.get('ciclo'), x.get('texto')) for x in ev.preguntas}
    nuevas, saltadas = [], 0
    for p in preguntas:
        g = grupo_para(c, p.get('nivel', ''), p.get('grado')) or grupo_por_id(c, ciclo_defecto)
        cat = p.get('categoria') or cat_defecto
        if g is None or (g['id'], p['texto']) in ya or cat not in {k for k, _, _ in CATEGORIAS}:
            saltadas += 1
            continue
        ya.add((g['id'], p['texto']))
        nuevas.append({'ciclo': g['id'], 'categoria': cat, 'grado': p.get('grado'), 'tema': p.get('tema', ''), 'texto': p['texto'],
                       'opciones': p['opciones'], 'origen': origen, **({'uso': 'juegos'} if uso == 'juegos' else {})})
    if nuevas:
        ev.preguntas = list(ev.preguntas) + nuevas
        ev.save(update_fields=['preguntas'])
    return len(nuevas), saltadas


def _huella(x):
    """Una marca corta de la pregunta, para no tocar otra si la lista cambió mientras el organizador la tenía abierta."""
    import hashlib
    return hashlib.sha1(f"{x.get('ciclo')}|{x.get('texto')}".encode()).hexdigest()[:10]


def _reindexar(ev, nuevo):
    """Las participaciones guardan las preguntas por su posición (la pendiente y las ya vistas): al quitar preguntas
    se corren las posiciones. nuevo: {posición vieja: posición nueva} (las quitadas no están)."""
    for p in ev.participaciones.exclude(pendiente={}, vistas=[]):
        cambios = []
        if p.pendiente and 'i' in p.pendiente:
            if p.pendiente['i'] in nuevo:
                p.pendiente = dict(p.pendiente, i=nuevo[p.pendiente['i']])
            else:
                p.pendiente = {}            # le sale otra
            cambios.append('pendiente')
        if p.vistas:
            p.vistas = [nuevo[i] for i in p.vistas if i in nuevo]
            cambios.append('vistas')
        if cambios:
            p.save(update_fields=cambios)


def quitar_preguntas(ev, indices):
    """Quita preguntas del evento sin dañar lo que llevan los participantes."""
    indices = set(indices)
    quedan, nuevo = [], {}
    for i, x in enumerate(ev.preguntas):
        if i in indices:
            continue
        nuevo[i] = len(quedan)
        quedan.append(x)
    n = len(ev.preguntas) - len(quedan)
    if n:
        ev.preguntas = quedan
        ev.save(update_fields=['preguntas'])
        _reindexar(ev, nuevo)
    return n


def mover_preguntas(ev, indices, uso):
    """Pasa preguntas a la competencia o a los retos arcade. Si una estaba pendiente para alguien y pasa al arcade,
    a esa persona le sale otra (las del arcade se ven en el navegador)."""
    n = 0
    lista = list(ev.preguntas)
    for i in indices:
        if 0 <= i < len(lista):
            x = dict(lista[i])
            if uso == 'juegos' and not es_de_juego(x):
                x['uso'] = 'juegos'; n += 1
            elif uso == 'competencia' and es_de_juego(x):
                x.pop('uso', None); n += 1
            lista[i] = x
    if n:
        ev.preguntas = lista
        ev.save(update_fields=['preguntas'])
        if uso == 'juegos':
            movidas = set(indices)
            for p in ev.participaciones.exclude(pendiente={}):
                if p.pendiente.get('i') in movidas:
                    p.pendiente = {}
                    p.save(update_fields=['pendiente'])
    return n


@login_required
def preguntas_evento(request, eid):
    """Todas las preguntas del evento: filtros, menú por pregunta (eliminar, pasar a la competencia o al arcade)
    y las mismas acciones para varias seleccionadas."""
    ev = _evento(request, eid)
    if not es_organizador(request, ev):
        return HttpResponseForbidden('Solo los organizadores manejan las preguntas.')
    c = config_de(ev)
    if request.method == 'POST':
        accion = request.POST.get('accion')
        elegidas = []
        for v in request.POST.getlist('sel'):
            i, _, huella = v.partition(':')
            if i.isdigit() and int(i) < len(ev.preguntas) and _huella(ev.preguntas[int(i)]) == huella:
                elegidas.append(int(i))
        if not elegidas:
            messages.warning(request, 'Escoja al menos una pregunta (o la lista cambió: vuelva a intentarlo).')
        elif accion == 'eliminar':
            messages.success(request, f'Se eliminaron {quitar_preguntas(ev, elegidas)} pregunta(s).')
        elif accion in ('competencia', 'juegos'):
            n = mover_preguntas(ev, elegidas, accion)
            messages.success(request, f'{n} pregunta(s) pasaron ' + ('a la competencia.' if accion == 'competencia' else 'al arcade (retos de juego).')
                             + (f' {len(elegidas) - n} ya estaban ahí.' if len(elegidas) > n else ''))
        else:
            messages.warning(request, 'Escoja qué hacer con las preguntas seleccionadas.')
        return redirect(f"{reverse('aula:evento_preguntas', args=[ev.pk])}?{request.GET.urlencode()}")
    f_uso, f_grupo, f_cat = request.GET.get('uso', ''), request.GET.get('grupo', ''), request.GET.get('cat', '')
    f_grado, q = request.GET.get('grado', ''), (request.GET.get('q') or '').strip().lower()
    nombres = {g['id']: g['nombre'] for g in grupos(c)}
    cats = {k: n for k, n, _ in CATEGORIAS}
    filas = []
    for i, x in enumerate(ev.preguntas):
        if f_uso == 'juegos' and not es_de_juego(x) or f_uso == 'competencia' and es_de_juego(x):
            continue
        if f_grupo and x.get('ciclo') != f_grupo or f_cat and x.get('categoria') != f_cat:
            continue
        if f_grado.lstrip('-').isdigit() and x.get('grado') != int(f_grado):
            continue
        if q and q not in (x.get('texto', '') + ' ' + x.get('tema', '')).lower():
            continue
        filas.append({'i': i, 'valor': f'{i}:{_huella(x)}', 'x': x, 'juego': es_de_juego(x), 'grupo': nombres.get(x.get('ciclo'), x.get('ciclo')),
                      'cat': cats.get(x.get('categoria'), ''), 'grado': etiqueta_grado(x['grado']) if x.get('grado') is not None else ''})
    total_j = sum(1 for x in ev.preguntas if es_de_juego(x))
    grados_hay = sorted({x['grado'] for x in ev.preguntas if x.get('grado') is not None})
    return render(request, 'aula/evento_preguntas.html', {
        'ev': ev, 'filas': filas, 'total': len(ev.preguntas), 'total_j': total_j, 'total_c': len(ev.preguntas) - total_j,
        'grupos': grupos(c), 'categorias': CATEGORIAS, 'grados': [(g, etiqueta_grado(g)) for g in grados_hay],
        'f': {'uso': f_uso, 'grupo': f_grupo, 'cat': f_cat, 'grado': f_grado, 'q': request.GET.get('q', '')},
        'consulta': request.GET.urlencode(), 'base': _base(request)})


@login_required
def preguntas_planilla(request, eid):
    """Planilla de Excel de las preguntas de competencia: descargar (las del evento, vacía o el banco 6.º–11.º) y subir."""
    ev = _evento(request, eid)
    if not es_organizador(request, ev):
        return HttpResponseForbidden('Solo los organizadores manejan las preguntas.')
    c = config_de(ev)
    if request.method == 'POST':
        archivo = request.FILES.get('archivo')
        if not archivo or archivo.size > 5 * 1024 * 1024:
            messages.warning(request, 'Escoja la planilla (máximo 5 MB).')
            return redirect('aula:evento_configurar', eid=ev.pk)
        preguntas, errores = planilla_preguntas.importar(archivo)
        cat = request.POST.get('categoria') if request.POST.get('categoria') in {k for k, _, _ in CATEGORIAS} else 'newton'
        uso = 'juegos' if request.POST.get('uso') == 'juegos' else 'competencia'
        n, saltadas = agregar_preguntas(ev, preguntas, f'Planilla: {archivo.name[:60]}', request.POST.get('ciclo'), cat, uso)
        messages.success(request, f'Se agregaron {n} pregunta(s) de la planilla ' + ('para los retos de juego.' if uso == 'juegos' else 'para la competencia.') + (f' {saltadas} no se agregaron (sin grupo para su grado o repetidas).' if saltadas else ''))
        if errores:
            messages.warning(request, f'{len(errores)} fila(s) con problemas: ' + ' · '.join((f'fila {f}: ' if f else '') + m for f, m in errores[:12]) + (' …' if len(errores) > 12 else ''))
        return redirect('aula:evento_configurar', eid=ev.pk)
    de = request.GET.get('de', 'evento')
    nombres = {g['id']: g['nombre'] for g in grupos(c)}
    lista = ([] if de == 'vacia' else planilla_preguntas.banco_olimpiada() if de == 'olimpiada'
             else planilla_preguntas.banco_calculo() if de == 'calculo'
             else [x for x in ev.preguntas if es_de_juego(x)] if de == 'juegos' else de_competencia(ev))
    if de in ('olimpiada', 'calculo'):
        lista = [dict(p, ciclo=(grupo_para(c, '', p['grado']) or {}).get('id', p['ciclo'])) for p in lista]
    archivo = planilla_preguntas.descargar(lista, ev.titulo, nombres)
    nombre = {'vacia': 'planilla de preguntas (vacia)', 'olimpiada': 'banco olimpiada 6 a 11', 'calculo': 'banco 10 y 11 - funciones limites y derivadas',
              'juegos': f'preguntas de juego {_nombre_archivo(ev.titulo, 40)}'}.get(de, f'preguntas de competencia {_nombre_archivo(ev.titulo, 40)}')
    return HttpResponse(archivo.getvalue(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                        headers={'Content-Disposition': f'attachment; filename="{nombre}.xlsx"'})


def _veedores_por_grupo(request, c):
    grupos_v = {}
    for v in c['veedores']:
        x = dict(v, enlace=request.build_absolute_uri(reverse('aula:evento_veedor', args=[v['token']])))
        grupos_v.setdefault(v.get('grupo') or 'Sin grupo', []).append(x)
    return sorted(grupos_v.items(), key=lambda kv: (kv[0] == 'Sin grupo', kv[0].lower()))


def limpiar_grabaciones(ev, c=None):
    """Borra las grabaciones que ya cumplieron los días que dice el evento (también lo hace el comando
    `python manage.py limpiar_grabaciones_eventos`, para correrlo cada día)."""
    c = c or config_de(ev)
    limite = timezone.now() - timezone.timedelta(days=c['vigilancia']['dias'])
    viejas = GrabacionEvento.objects.filter(participacion__evento=ev, creada__lt=limite)
    n = viejas.count()
    if n:
        viejas.delete()
    return n


def _resumen_grabaciones(ev):
    from django.db.models import Count, Sum
    qs = GrabacionEvento.objects.filter(participacion__evento=ev)
    r = qs.aggregate(n=Count('id'), b=Sum('bytes'), p=Count('participacion', distinct=True))
    return {'trozos': r['n'] or 0, 'mb': round((r['b'] or 0) / 1048576, 1), 'participantes': r['p'] or 0, 'en_nube': qs.exclude(nube='').count()}


@login_required
def configurar(request, eid):
    ev = _evento(request, eid)
    if not es_organizador(request, ev):
        return HttpResponseForbidden('Solo los organizadores configuran el evento.')
    puede_admin = es_admin_del_evento(request, ev)
    limpiar_grabaciones(ev)
    if request.method == 'POST':
        accion = request.POST.get('accion')
        # En Mi Salón Virtual, encender un evento (activarlo, programarlo o abrir inscripciones) es de Premium.
        # Apagarlo o cerrar inscripciones siempre se puede.
        enciende = ((accion == 'activar' and not ev.activo) or (accion == 'programar' and not request.POST.get('cancelar'))
                    or (accion == 'inscripciones_abrir' and request.POST.get('abrir') == '1'))
        if enciende and ev.colegio_id is None:
            from salon_digital.limites import a_planes, permite
            if not permite(request.user, 'eventos'):
                return a_planes(request, 'eventos')
        if accion == 'activar':
            ev.activo = not ev.activo
            ev.config = dict(ev.config or {}, activar_en='')       # activar o apagar a mano quita lo programado
            ev.save(update_fields=['activo', 'config'])
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
            uso = 'juegos' if request.POST.get('uso') == 'juegos' else 'competencia'
            n, repetidas = agregar_preguntas(ev, [dict(p, nivel='', grado=None) for p in buenas], origen, ciclo, cat, uso)
            malas = len(preguntas) - len(buenas)
            messages.success(request, f'Se agregaron {n} pregunta(s) ' + ('para los retos de juego.' if uso == 'juegos' else 'para la competencia.')
                             + (f' {malas} se saltaron (sin opciones o sin una sola correcta).' if malas else '') + (f' {repetidas} ya estaban.' if repetidas else ''))
        elif accion == 'quitar':
            try:
                quitar_preguntas(ev, [int(request.POST.get('i'))])
            except (TypeError, ValueError):
                pass
        elif accion == 'banco':
            ev.preguntas = list(ev.preguntas) + [p for p in _banco() if p not in ev.preguntas]
            ev.save(update_fields=['preguntas'])
            messages.success(request, 'Se agregó el banco inicial de preguntas.')
        elif accion in ('banco_611', 'banco_calculo'):
            uso = 'juegos' if request.POST.get('uso') == 'juegos' else 'competencia'
            fuente = planilla_preguntas.banco_calculo() if accion == 'banco_calculo' else planilla_preguntas.banco_olimpiada()
            n, sin = agregar_preguntas(ev, [dict(p, nivel='') for p in fuente],
                                       'Banco 10.º y 11.º (cálculo)' if accion == 'banco_calculo' else 'Banco olimpiada 6.º–11.º', uso=uso)
            messages.success(request, f'Se agregaron {n} pregunta(s) del banco ' + ('10.º y 11.º ' if accion == 'banco_calculo' else '6.º–11.º ') + ('para los retos de juego' if uso == 'juegos' else 'para la competencia') + ', cada una al grupo de su grado.'
                             + (f' {sin} no se agregaron (su grado no está en ningún grupo o ya estaban).' if sin else ''))
        elif accion == 'arcade':
            c = config_de(ev)
            elegido = request.POST.get('arcade') if request.POST.get('arcade') in ('preguntas', 'propias', 'banco', 'operaciones') else 'preguntas'
            ev.config = dict(ev.config or {}, arcade=elegido)
            ev.save(update_fields=['config'])
            messages.success(request, 'Los retos arcade ahora usan ' + {'preguntas': 'las preguntas para juegos del grado de cada estudiante (y el banco 6.º–11.º si faltan).',
                                                                         'propias': 'solo las preguntas cargadas para los juegos.',
                                                                         'banco': 'las preguntas del banco 6.º–11.º del grado de cada estudiante.',
                                                                         'operaciones': 'operaciones según el grupo.'}[elegido])
        elif accion == 'alcance' and ev.colegio_id:
            ev.alcance = 'codigo' if request.POST.get('alcance') == 'codigo' else 'colegio'
            ev.save(update_fields=['alcance'])
            messages.success(request, 'Ahora entra quien tenga el código del evento.' if ev.alcance == 'codigo' else 'Ahora solo participan los estudiantes del colegio.')
        elif accion == 'inscripcion':
            c = config_de(ev)
            def cupo(k):
                try:
                    return max(0, min(9999, int(request.POST.get(k) or 0)))
                except ValueError:
                    return 0
            c['inscripcion'] = {'abierta': c['inscripcion']['abierta'], 'aprobacion': bool(request.POST.get('aprobacion')),
                                'cupo_colegio': cupo('cupo_colegio'), 'cupo_nivel': cupo('cupo_nivel')}
            ev.config = dict(ev.config or {}, inscripcion=c['inscripcion'])
            ev.save(update_fields=['config'])
            messages.success(request, 'Inscripción guardada.')
        elif accion in ('veedor', 'veedores', 'veedor_grupo', 'veedor_quitar', 'veedor_activo', 'veedor_reenviar'):
            import secrets
            c = config_de(ev)
            lista = list(c['veedores'])
            limpio = lambda k, n: ' '.join((request.POST.get(k) or '').split())[:n]
            grupo = limpio('grupo', 60)
            nuevo = lambda nombre, correo, tipo='persona': {'token': secrets.token_urlsafe(18), 'nombre': nombre, 'correo': correo, 'grupo': grupo,
                                                            'tipo': tipo, 'activo': True, 'creado': timezone.now().isoformat(timespec='minutes')}
            agregados = []
            if accion == 'veedor':
                nombre, correo = limpio('nombre', 80), limpio('correo', 120)
                if not nombre and not correo:
                    messages.warning(request, 'Escriba el nombre o el correo del profesor.')
                else:
                    agregados.append(nuevo(nombre, correo))
            elif accion == 'veedores':           # varios: «Nombre, correo» por línea
                for linea in (request.POST.get('lista') or '').splitlines()[:300]:
                    partes = [x.strip() for x in linea.replace(';', ',').replace('\t', ',').split(',') if x.strip()]
                    if not partes:
                        continue
                    correo = next((x for x in partes if '@' in x), '')
                    nombre = ' '.join(x for x in partes if x != correo)[:80]
                    agregados.append(nuevo(nombre, correo[:120]))
            elif accion == 'veedor_grupo':
                if not grupo:
                    messages.warning(request, 'Escriba el nombre del grupo de profesores.')
                else:
                    agregados.append(nuevo(f'Enlace del grupo «{grupo}»', '', 'grupo'))
            else:
                v = next((v for v in lista if v['token'] == request.POST.get('token')), None)
                if v and accion == 'veedor_quitar':
                    lista.remove(v); messages.success(request, 'Veedor quitado: su enlace ya no funciona.')
                elif v and accion == 'veedor_activo':
                    v['activo'] = not v.get('activo', True)
                    messages.success(request, 'Enlace ' + ('activado.' if v['activo'] else 'pausado: no funciona hasta que lo vuelva a activar.'))
                elif v and accion == 'veedor_reenviar':
                    messages.success(request, 'Invitación enviada por correo.' if _invitar_veedor(request, ev, v) else 'No se pudo enviar (¿tiene correo?).')
            if agregados:
                lista += agregados
                enviados = sum(_invitar_veedor(request, ev, v) for v in agregados) if request.POST.get('enviar') else 0
                messages.success(request, f'{len(agregados)} veedor(es) invitado(s).' + (f' Se envió el enlace por correo a {enviados}.' if enviados else ' Copie y envíe el enlace de cada uno.'))
            ev.config = dict(ev.config or {}, veedores=lista)
            ev.save(update_fields=['config'])
        elif accion == 'podio_colegios':
            c = config_de(ev)
            pesos = {}
            for g in grupos(c):
                try:
                    pesos[g['id']] = max(0.0, min(10.0, float((request.POST.get('peso_' + g['id']) or '1').replace(',', '.'))))
                except ValueError:
                    pesos[g['id']] = 1.0
            ev.config = dict(ev.config or {}, podio_colegios={'activo': bool(request.POST.get('activo')), 'pesos': pesos})
            ev.save(update_fields=['config'])
            messages.success(request, 'Podio de colegios guardado.')
            return redirect('aula:evento_resultados', eid=ev.pk)
        elif accion == 'inscripciones_abrir':
            c = config_de(ev)
            abrir = request.POST.get('abrir') == '1'
            ev.config = dict(ev.config or {}, inscripcion=dict(c['inscripcion'], abierta=abrir))
            ev.save(update_fields=['config'])
            messages.success(request, 'Inscripciones HABILITADAS: los participantes ya se pueden inscribir con el código o el enlace.'
                             if abrir else 'Inscripciones cerradas: nadie más se puede inscribir. Los inscritos siguen entrando con su documento y su código.')
        elif accion == 'programar':
            cuando = (request.POST.get('activar_en') or '').strip()[:16]
            f = _fecha(cuando)
            if request.POST.get('cancelar'):
                ev.config = dict(ev.config or {}, activar_en='')
                ev.save(update_fields=['config'])
                messages.info(request, 'Se quitó el inicio programado. El evento sigue apagado.')
            elif ev.activo:
                messages.info(request, 'El evento ya está activo.')
            elif f is None:
                messages.warning(request, 'Escoja la fecha y la hora en que debe empezar.')
            elif f <= timezone.now():
                messages.warning(request, 'Esa hora ya pasó. Escoja una hora futura o use «Activar el evento».')
            else:
                ev.config = dict(ev.config or {}, activar_en=cuando)
                ev.save(update_fields=['config'])
                messages.success(request, f'Listo: el evento se activará solo el {fecha_bonita(f)} Hasta entonces los estudiantes no lo ven.')
        elif accion == 'fechas':
            c = config_de(ev)
            nuevas = {}
            for k in ('inscripcion_hasta', 'prueba_desde', 'prueba_hasta'):
                v = (request.POST.get(k) or '').strip()[:16]
                nuevas[k] = v if _fecha(v) else ''
            if nuevas['prueba_desde'] and nuevas['prueba_hasta'] and _fecha(nuevas['prueba_desde']) >= _fecha(nuevas['prueba_hasta']):
                messages.warning(request, 'La prueba debe cerrar después de abrir.')
            else:
                ev.config = dict(ev.config or {}, fechas=nuevas)
                ev.save(update_fields=['config'])
                messages.success(request, 'Fechas guardadas.')
        elif accion == 'vigilancia':
            c = config_de(ev)
            activa = bool(request.POST.get('activa'))
            if activa and not request.POST.get('acepto_legal'):
                messages.warning(request, 'Para supervisar la prueba confirme que tiene la autorización de los acudientes (datos sensibles de menores).')
            else:
                try:
                    dias = max(1, min(365, int(request.POST.get('dias') or c['vigilancia']['dias'])))
                except ValueError:
                    dias = c['vigilancia']['dias']
                op = {k: bool(request.POST.get(k)) for k in ('camara', 'juego', 'pantalla', 'salidas')}
                if activa and not any(op.values()):
                    messages.warning(request, 'Escoja al menos una forma de supervisar (cámara, juego, pantalla o registro de salidas).')
                else:
                    guardar = 'pantallazos' if request.POST.get('guardar') == 'pantallazos' else 'video'
                    c['vigilancia'] = dict({'activa': activa, 'dias': dias, 'guardar': guardar}, **op)
                    ev.config = dict(ev.config or {}, vigilancia=c['vigilancia'])
                    ev.save(update_fields=['config'])
                    if activa:
                        que = [n for k, n in (('camara', 'cámara y micrófono'), ('juego', 'juego'), ('pantalla', 'pantalla completa en computador'),
                                              ('salidas', 'registro de salidas')) if op[k]]
                        messages.success(request, 'Supervisión ACTIVADA: ' + ', '.join(que) + (
                            f'. Se guardan {"pantallazos" if guardar == "pantallazos" else "videos"} y se borran a los {dias} días.' if graba(c['vigilancia']) else '.'))
                    else:
                        messages.success(request, 'Supervisión apagada: no se graba ni se registran salidas.')
        elif accion == 'borrar_grabaciones' and puede_admin:
            n = GrabacionEvento.objects.filter(participacion__evento=ev).count()
            GrabacionEvento.objects.filter(participacion__evento=ev).delete()
            messages.success(request, f'Se borraron {n} trozo(s) de grabación.')
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
    conteo, de_juego = {}, {}
    for p in ev.preguntas:
        if es_de_juego(p):
            de_juego[p.get('ciclo')] = de_juego.get(p.get('ciclo'), 0) + 1
        else:
            conteo[(p.get('ciclo'), p.get('categoria'))] = conteo.get((p.get('ciclo'), p.get('categoria')), 0) + 1
    tabla = [{'ciclo': g['nombre'], 'cifras': [conteo.get((g['id'], ca), 0) for ca, _, _ in CATEGORIAS], 'juegos': de_juego.get(g['id'], 0)} for g in grupos(c)]
    base_grados = grados_del_colegio(ev.colegio) if ev.colegio_id and ev.alcance == 'colegio' else todos_los_grados()
    grados_cols = sorted(set(base_grados) | {x for g in grupos(c) for x in g['grados']})
    cursos = Curso.objects.filter(colegio=ev.colegio).order_by('grado', 'nombre') if ev.colegio_id else Curso.objects.none()
    estudiantes = Estudiante.objects.filter(colegio=ev.colegio, curso__isnull=False).select_related('user', 'curso').order_by('curso__grado', 'curso__nombre', 'user__last_name') if ev.colegio_id else Estudiante.objects.none()
    juegos_salon = _juegos_salon(ev).select_related('aula').order_by('-pk')[:200]
    from . import instrucciones
    tipos_propios = {f'p_{j.pk}': j.tipo for j in juegos_salon}
    filas_juegos = []
    for j in juegos_del_evento(ev):
        pj = c['por_juego'].get(j[0]) or {}
        grados = pj.get('grados', grados_cols if j[0] in c['juegos'] else [])
        if j[0] not in c['juegos']:
            grados = []
        filas_juegos.append({'id': j[0], 'nombre': j[1], 'estilo': j[2], 'grados': grados, 'dificultad': pj.get('dificultad', 'auto'),
                             'instrucciones': instrucciones.de_evento(j[0], tipos_propios),
                             'velocidad': pj.get('velocidad', 'normal'), 'con_velocidad': j[2] in ('arcade', 'propio') or j[0] == 'speedrun'})
    return render(request, 'aula/evento_configurar.html', {
        'ev': ev, 'c': c, 'juegos': JUEGOS, 'filas_juegos': filas_juegos, 'velocidades': JuegoAula.VELOCIDADES, 'grados': [(g, etiqueta_grado(g)) for g in grados_cols],
        'todos_grados': [(g, etiqueta_grado(g)) for g in todos_los_grados()], 'niveles': NIVELES,
        'grupos': [dict(g, rango=rango_grados(g)) for g in grupos(c)], 'cursos': cursos, 'estudiantes': estudiantes,
        'part': c['participantes'], 'dificultades': DIFICULTADES, 'estilos': ESTILOS, 'categorias': CATEGORIAS, 'tabla': tabla,
        'preguntas': list(enumerate(ev.preguntas)), 'juegos_salon': juegos_salon, 'es_admin': puede_admin, 'ins': c['inscripcion'],
        'n_pendientes': ev.participaciones.filter(estado='pendiente').count(),
        'vig': c['vigilancia'], 'vig_texto': texto_supervision(c['vigilancia']),
        'vig_opciones': [(k, t, d, x, r, bool(c['vigilancia'].get(k))) for k, t, d, x, r in (
            ('camara', 'Cámara y micrófono', 'celular y computador', 'Se graban la imagen y la voz. Si los apaga, el juego se detiene hasta encenderlos.', True),
            ('juego', 'Grabar el juego', 'celular y computador', 'Se graba lo que hace en la prueba (retos y preguntas) con la cámara en un recuadro.', True),
            ('pantalla', 'Grabar la pantalla completa', 'solo computador', 'Al empezar debe compartir la pantalla completa; si deja de compartirla, el juego se detiene. En celular se graba el juego.', False),
            ('salidas', 'Registrar salidas de la prueba', 'celular y computador', 'Anota cada vez que cambia de pestaña, ventana o aplicación: la hora y cuánto tiempo estuvo fuera.', True))],
        'grab': _resumen_grabaciones(ev), 'fechas': c['fechas'], 'vent': ventana(c),
        'activar_en': c['activar_en'], 'activar_bonito': fecha_bonita(_fecha(c['activar_en'])) if _fecha(c['activar_en']) else '',
        'minimo_programar': timezone.localtime().strftime('%Y-%m-%dT%H:%M'),
        'veedores': _veedores_por_grupo(request, c),
        'docentes': Docente.objects.filter(colegio=ev.colegio).select_related('user').order_by('user__last_name') if ev.colegio_id else [],
        'enlace': request.build_absolute_uri(reverse('aula:evento_inscribirse', args=[ev.codigo])),
        'organizadores': set(ev.organizadores.values_list('pk', flat=True)), 'base': _base(request)})


def _preguntas_arcade(ev, c, grado, grupo):
    """Las preguntas de selección múltiple de los retos arcade del estudiante: primero las que el organizador cargó
    para los juegos (de su grado; si no hay, de su grupo) y, si faltan, las del banco 6.º–11.º de su grado.
    Nunca las de competencia: las de juego se ven en el navegador."""
    modo = c.get('arcade', 'preguntas')
    competencia = {x.get('texto') for x in de_competencia(ev)}
    gid = (grupo or {}).get('id')
    propias = [x for x in ev.preguntas if es_de_juego(x) and x.get('ciclo') == gid and x.get('texto') not in competencia]
    if grado is not None and any(x.get('grado') == grado for x in propias):
        propias = [x for x in propias if x.get('grado') in (grado, None)]
    random.shuffle(propias)
    lista = list(propias) if modo in ('preguntas', 'propias') else []
    if modo == 'banco' or (modo == 'preguntas' and len(lista) < 30):
        banco = [p for p in planilla_preguntas.banco_olimpiada() if p['texto'] not in competencia and p['texto'] not in {x['texto'] for x in lista}]
        grados = [grado] if grado is not None else (grupo or {}).get('grados', [])
        del_banco = [p for p in banco if p['grado'] in grados] or [p for p in banco if p['grado'] in (grupo or {}).get('grados', [])]
        random.shuffle(del_banco)
        lista += del_banco
    return [{'texto': p['texto'], 'opciones': p['opciones']} for p in lista[:80]]


def _juegos_salon(ev):
    """Los juegos del salón virtual de donde se pueden importar preguntas."""
    if ev.colegio_id:
        return JuegoAula.objects.filter(aula__colegio=ev.colegio)
    return JuegoAula.objects.filter(aula__grupo__propietario__usuario=ev.creador) if ev.creador_id else JuegoAula.objects.none()


def jugar(request, eid):
    ev = _evento(request, eid)
    organiza = es_organizador(request, ev)
    if not ev.activo and not organiza:
        if ev.alcance == 'codigo':          # el inscrito ve su inscripción y cuándo empieza
            return redirect('aula:evento_inscribirse', codigo=ev.codigo)
        raise Http404
    c = config_de(ev)
    p = participante(request, ev)
    if p is not None and p.estado != 'aprobada' and not organiza:
        return estado_inscripcion(request, ev, p)
    vent = ventana(c)
    if not vent['prueba'] and not organiza:
        return render(request, 'aula/evento_cerrado.html', {'ev': ev, 'vent': vent, 'p': p, 'base': _base(request), 'hide_cuenta': not request.user.is_authenticated})
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
        'vigilancia': dict(c['vigilancia'], graba=graba(c['vigilancia']), texto=texto_supervision(c['vigilancia'])) if c['vigilancia']['activa'] else None,
        'arcade_preguntas': _preguntas_arcade(ev, c, grado, grupo) if c.get('arcade', 'preguntas') != 'operaciones' else None,
        'acepto_vigilancia': bool(p and (p.datos or {}).get('vigilancia', {}).get('acepto')),
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


def normalizar(texto):
    """Para contar los cupos: «Colegio  San José» y «colegio san jose» son la misma institución."""
    import unicodedata
    t = unicodedata.normalize('NFKD', texto or '').encode('ascii', 'ignore').decode().lower()
    return ' '.join(t.replace('.', ' ').split())


def cupos(ev, institucion, ciclo, estados=('aprobada', 'pendiente')):
    """(en la institución, en la institución y ese nivel) contando las inscripciones con esos estados."""
    clave = normalizar(institucion)
    misma = [p for p in ev.participaciones.filter(estado__in=estados, estudiante__isnull=True) if normalizar(p.institucion) == clave]
    return len(misma), sum(1 for p in misma if p.ciclo == ciclo)


def sin_cupo(ev, c, institucion, ciclo, estados=('aprobada', 'pendiente')):
    """El motivo si la institución ya llenó su cupo (total o en ese nivel); '' si todavía cabe."""
    ins = c['inscripcion']
    total, nivel = cupos(ev, institucion, ciclo, estados)
    if ins['cupo_colegio'] and total >= ins['cupo_colegio']:
        return f'La institución ya tiene sus {ins["cupo_colegio"]} cupo(s) en este evento.'
    if ins['cupo_nivel'] and nivel >= ins['cupo_nivel']:
        g = grupo_por_id(c, ciclo)
        return f'La institución ya tiene sus {ins["cupo_nivel"]} cupo(s) en el nivel {g["nombre"] if g else ciclo}.'
    return ''


def documento_limpio(texto):
    """«1.023.456.789 » → «1023456789»: así se compara siempre igual."""
    import re
    return re.sub(r'[^0-9A-Za-z]', '', texto or '').upper()[:20]


def inscrito_con(ev, documento, excluir_rechazadas=True):
    qs = ev.participaciones.filter(estudiante__isnull=True)
    if excluir_rechazadas:
        qs = qs.exclude(estado='rechazada')
    return next((x for x in qs if documento and documento_limpio(x.datos.get('documento')) == documento), None)


def estado_inscripcion(request, ev, p, recien=False):
    c = config_de(ev)
    g = grupo_por_id(c, p.ciclo)
    return render(request, 'aula/evento_inscripcion_estado.html', {
        'ev': ev, 'p': p, 'recien': recien, 'vent': ventana(c), 'grupo': g['nombre'] if g else p.ciclo, 'grado': etiqueta_grado(p.grado) if p.grado is not None else '',
        'base': _base(request), 'hide_cuenta': not request.user.is_authenticated})


def inscribirse(request, codigo):
    """Evento abierto: el participante llena el formulario de inscripción (no necesita cuenta).
    Si el organizador pide aprobarlas, queda pendiente hasta que la apruebe; los cupos por institución
    y por nivel se revisan al inscribirse y otra vez al aprobar."""
    ev = al_dia(get_object_or_404(Evento, codigo=(codigo or '').upper(), alcance='codigo'))
    c = config_de(ev)
    ins = c['inscripcion']
    p = participante(request, ev)
    if p:
        recien = request.session.pop(f'evento_{ev.pk}_recien', False)
        if p.estado == 'aprobada' and ev.activo and not recien:
            return redirect('aula:evento', eid=ev.pk)
        return estado_inscripcion(request, ev, p, recien)
    grados = sorted({x for g in grupos(c) for x in g['grados']})
    # Se inscriben cuando el organizador habilita las inscripciones (aunque el evento todavía esté apagado)
    vent = ventana(c)
    recibe = ins['abierta'] and vent['inscripcion']
    error = ''
    from django.core.cache import cache
    from salon_digital.utils import ip_cliente
    ip = ip_cliente(request) or ''
    if request.method == 'POST' and request.POST.get('accion') == 'recuperar':
        # Máximo 10 intentos cada 15 minutos por equipo (la clave no se puede adivinar probando)
        llave = f'evento-recuperar:{ev.pk}:{ip}'
        if (cache.get(llave) or 0) >= 10:
            return render(request, 'aula/evento_inscribirse.html', {
                'ev': ev, 'grados': [(x, etiqueta_grado(x)) for x in grados], 'error': 'Demasiados intentos. Espere 15 minutos.',
                'sugerido': {}, 'ins': ins, 'recibe': recibe, 'niveles': grupos(c), 'base': _base(request), 'hide_cuenta': not request.user.is_authenticated})
        cache.set(llave, (cache.get(llave) or 0) + 1, 15 * 60)
        import secrets
        doc, clave = documento_limpio(request.POST.get('documento')), ''.join((request.POST.get('clave') or '').split()).upper()
        q = inscrito_con(ev, doc, excluir_rechazadas=False)
        if q and clave and secrets.compare_digest(str(q.datos.get('clave', '')), clave):
            # Un solo equipo a la vez: al entrar aquí, la sesión que tuviera abierta en otro equipo se cierra.
            # Su avance (puntos, bloque, tiempo) está en el servidor y sigue igual.
            q.token = secrets.token_urlsafe(24)
            q.save(update_fields=['token'])
            request.session[clave_sesion(ev)] = q.token
            cache.delete(llave)
            if q.estado == 'aprobada' and ev.activo:
                messages.success(request, f'Bienvenido(a) de nuevo, {q.nombre}. Su avance sigue guardado.')
            return redirect('aula:evento_inscribirse', codigo=ev.codigo)
        error = 'No encontramos una inscripción con ese documento y ese código de seguridad.'
    elif request.method == 'POST':
        limpio = lambda k, n: ' '.join((request.POST.get(k) or '').split())[:n]
        nombre, institucion, ciudad = limpio('nombre', 120), limpio('institucion', 120), limpio('ciudad', 80)
        documento, contacto, acompanante = documento_limpio(request.POST.get('documento')), limpio('contacto', 120), limpio('acompanante', 120)
        try:
            grado = int(request.POST.get('grado'))
        except (TypeError, ValueError):
            grado = None
        g = next((x for x in grupos(c) if grado in x['grados']), None)
        llave = f'evento-inscribir:{ev.pk}:{ip}'
        acudiente = limpio('acudiente', 120)
        if request.POST.get('sitio_web'):            # campo escondido: solo lo llenan los robots
            error = 'No se pudo enviar la inscripción.'
        elif (cache.get(llave) or 0) >= 60:           # muchas inscripciones seguidas desde el mismo equipo
            error = 'Se enviaron demasiadas inscripciones desde este equipo. Espere unos minutos.'
        elif not request.POST.get('autoriza'):
            error = 'Para inscribirse debe marcar la autorización del tratamiento de datos personales.'
        elif ins['aprobacion'] and len(acudiente) < 5:
            error = 'Escriba el nombre del acudiente (o del docente responsable) que autoriza los datos.'
        elif not recibe:
            error = 'Las inscripciones de este evento no están abiertas.'
        elif len(nombre) < 5 or not institucion or g is None:
            error = 'Escriba su nombre completo, su institución y escoja su grado.'
        elif len(documento) < 5:
            error = 'Escriba su número de documento (tarjeta de identidad o registro civil).'
        elif ins['aprobacion'] and len(contacto) < 7:
            error = 'Escriba un correo o celular de contacto.'
        elif inscrito_con(ev, documento):
            error = 'Ese documento ya está inscrito: cada documento se inscribe una sola vez. Entre con su documento y su código de seguridad en «Ya me inscribí».'
        else:
            error = sin_cupo(ev, c, institucion, g['id'])
        if not error:
            import secrets
            cache.set(llave, (cache.get(llave) or 0) + 1, 10 * 60)
            clave = ''.join(secrets.choice('ABCDEFGHJKLMNPQRSTUVWXYZ23456789') for _ in range(6))
            p = ParticipacionEvento.objects.create(
                evento=ev, nombre=nombre, institucion=institucion, grado=grado, ciclo=g['id'], token=secrets.token_urlsafe(24),
                estado='pendiente' if ins['aprobacion'] else 'aprobada',
                datos={'documento': documento, 'ciudad': ciudad, 'contacto': contacto, 'acompanante': acompanante, 'clave': clave,
                       # Ley 1581 de 2012: quién autorizó el tratamiento de los datos, cuándo y desde dónde
                       'autorizacion': {'acudiente': acudiente, 'fecha': timezone.now().isoformat(timespec='seconds'), 'ip': ip,
                                        'grabacion': graba(c['vigilancia']),
                                        'supervision': texto_supervision(c['vigilancia'])}})
            request.session[clave_sesion(ev)] = p.token
            request.session[f'evento_{ev.pk}_recien'] = True      # para mostrarle su código de seguridad
            return redirect('aula:evento_inscribirse', codigo=ev.codigo)
    sugerido = {'nombre': '', 'institucion': '', 'grado': None, 'ciudad': '', 'documento': '', 'contacto': '', 'acompanante': '', 'acudiente': ''}
    est = _estudiante(request)
    if est is not None:
        sugerido.update({'nombre': est.user.get_full_name(), 'institucion': est.colegio.nombre, 'grado': est.curso.grado if est.curso_id else None})
    if request.method == 'POST' and request.POST.get('accion') != 'recuperar':
        sugerido.update({k: request.POST.get(k, '') for k in ('nombre', 'institucion', 'ciudad', 'documento', 'contacto', 'acompanante', 'acudiente')})
        try:
            sugerido['grado'] = int(request.POST.get('grado'))
        except (TypeError, ValueError):
            pass
    return render(request, 'aula/evento_inscribirse.html', {
        'ev': ev, 'grados': [(x, etiqueta_grado(x)) for x in grados], 'error': error, 'sugerido': sugerido, 'post': request.POST,
        'ins': ins, 'recibe': recibe, 'niveles': grupos(c), 'vigilancia': c['vigilancia'] if c['vigilancia']['activa'] else None, 'supervision': texto_supervision(c['vigilancia']), 'vent': vent,
        'base': _base(request), 'hide_cuenta': not request.user.is_authenticated})


def avisar_inscripcion(request, ev, p):
    """Le avisa por correo al inscrito (si dejó un correo de contacto) que su inscripción se aprobó o se rechazó."""
    contacto = (p.datos.get('contacto') or '').strip()
    if '@' not in contacto or p.estado == 'pendiente':
        return 0
    from notas.mensajeria import enviar_correo
    enlace = request.build_absolute_uri(reverse('aula:evento_inscribirse', args=[ev.codigo]))
    if p.estado == 'aprobada':
        asunto = f'{ev.titulo}: inscripción aprobada'
        texto = (f'Hola,\n\nLa inscripción de {p.nombre} ({p.institucion}) en «{ev.titulo}» fue APROBADA.\n\n'
                 f'Para participar entre a este enlace{" el día del evento" if not ev.activo else ""}: {enlace}\n'
                 f'Para entrar use «Ya me inscribí» con el documento y el código de seguridad {p.datos.get("clave", "")}.\n\n'
                 '¡Muchos éxitos!')
    else:
        motivo = p.datos.get('motivo') or ''
        asunto = f'{ev.titulo}: inscripción no aprobada'
        texto = (f'Hola,\n\nLa inscripción de {p.nombre} ({p.institucion}) en «{ev.titulo}» no fue aprobada.'
                 + (f'\nMotivo: {motivo}' if motivo else '') + '\n\nSi cree que es un error, comuníquese con el organizador del evento.')
    try:
        return enviar_correo(ev.colegio, asunto, texto, [contacto], fail_silently=True, copia=False) or 0
    except Exception:          # sin correo configurado: no se cae la aprobación
        return 0


@login_required
def planilla(request, eid):
    """Planilla de inscripción en Excel: descargarla (vacía o con los inscritos) y subirla llena."""
    from . import planilla_eventos
    ev = _evento(request, eid)
    if not es_organizador(request, ev):
        return HttpResponseForbidden('Solo los organizadores manejan la planilla.')
    c = config_de(ev)
    if request.method == 'POST':
        archivo = request.FILES.get('archivo')
        if not archivo:
            messages.warning(request, 'Escoja el archivo de la planilla.')
            return redirect('aula:evento_inscripciones', eid=ev.pk)
        if archivo.size > 5 * 1024 * 1024:
            messages.warning(request, 'El archivo es muy grande (máximo 5 MB).')
            return redirect('aula:evento_inscripciones', eid=ev.pk)
        from salon_digital.utils import ip_cliente
        r = planilla_eventos.importar(ev, archivo, c, request.user, ip_cliente(request) or '', aprobar=bool(request.POST.get('aprobar')))
        partes = []
        if r['nuevas']:
            partes.append(f"{r['nuevas']} inscripción(es) nueva(s)")
        if r['actualizadas']:
            partes.append(f"{r['actualizadas']} actualizada(s)")
        if partes:
            messages.success(request, 'Planilla subida: ' + ' y '.join(partes) + '.')
        elif not r['errores']:
            messages.info(request, 'La planilla no tenía estudiantes.')
        request.session[f'evento_planilla_{ev.pk}'] = r['errores'][:300]
        return redirect(f"{reverse('aula:evento_inscripciones', args=[ev.pk])}?estado=todas")
    inscritos = [] if request.GET.get('vacia') else list(ev.participaciones.filter(estudiante__isnull=True).order_by('institucion', 'grado', 'nombre'))
    grados = sorted({x for g in grupos(c) for x in g['grados']})
    archivo = planilla_eventos.descargar(ev, grados, etiqueta_grado, inscritos)
    nombre = f"planilla {_nombre_archivo(ev.titulo, 50)}{' (vacia)' if request.GET.get('vacia') else ''}.xlsx"
    return HttpResponse(archivo.getvalue(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                        headers={'Content-Disposition': f'attachment; filename="{nombre}"'})


@login_required
def inscripciones(request, eid):
    """El organizador revisa las inscripciones de los de fuera: aprueba o rechaza, con los cupos a la vista."""
    ev = _evento(request, eid)
    if not es_organizador(request, ev):
        return HttpResponseForbidden('Solo los organizadores revisan las inscripciones.')
    c = config_de(ev)
    ins = c['inscripcion']
    externas = ev.participaciones.filter(estudiante__isnull=True)
    if request.method == 'POST':
        accion = request.POST.get('accion')
        if accion == 'aprobar_todas':
            n = saltadas = correos = 0
            for p in externas.filter(estado='pendiente').order_by('empezada', 'pk'):
                if sin_cupo(ev, c, p.institucion, p.ciclo, ('aprobada',)):
                    saltadas += 1
                    continue
                p.estado, p.empezada = 'aprobada', timezone.now()
                p.save(update_fields=['estado', 'empezada'])
                n += 1
                correos += avisar_inscripcion(request, ev, p)
            messages.success(request, f'Se aprobaron {n} inscripción(es).' + (f' {saltadas} quedaron pendientes porque su institución ya llenó el cupo.' if saltadas else '')
                             + (f' Se avisó por correo a {correos}.' if correos else ''))
        else:
            p = get_object_or_404(externas, pk=request.POST.get('pid'))
            if accion == 'aprobar':
                motivo = sin_cupo(ev, c, p.institucion, p.ciclo, ('aprobada',))
                if motivo and not request.POST.get('forzar'):
                    messages.warning(request, f'{p.nombre}: {motivo} Puede aprobarla de todos modos con «Aprobar sobre el cupo».')
                else:
                    p.estado, p.empezada = 'aprobada', timezone.now()
                    p.datos.pop('motivo', None)
                    p.save(update_fields=['estado', 'empezada', 'datos'])
                    aviso = ' Se le avisó por correo.' if avisar_inscripcion(request, ev, p) else ''
                    messages.success(request, f'Inscripción de {p.nombre} aprobada.{aviso}')
            elif accion == 'rechazar':
                p.estado = 'rechazada'
                p.datos['motivo'] = ' '.join((request.POST.get('motivo') or '').split())[:200]
                p.save(update_fields=['estado', 'datos'])
                aviso = ' Se le avisó por correo.' if avisar_inscripcion(request, ev, p) else ''
                messages.success(request, f'Inscripción de {p.nombre} rechazada.{aviso}')
            elif accion == 'pendiente':
                p.estado = 'pendiente'
                p.save(update_fields=['estado'])
            elif accion == 'eliminar':
                p.delete()
                messages.success(request, 'Inscripción eliminada.')
        return redirect(f"{reverse('aula:evento_inscripciones', args=[ev.pk])}?{request.GET.urlencode()}")
    filtro = request.GET.get('estado', 'pendiente')
    lista = list(externas.order_by('empezada', 'pk'))
    nombres = {g['id']: g['nombre'] for g in grupos(c)}
    # Cupos usados por institución (y por nivel) con las aprobadas
    resumen = {}
    for p in lista:
        r = resumen.setdefault(normalizar(p.institucion), {'nombre': p.institucion, 'aprobada': 0, 'pendiente': 0, 'rechazada': 0, 'niveles': {}})
        r[p.estado] += 1
        if p.estado == 'aprobada':
            r['niveles'][nombres.get(p.ciclo, p.ciclo)] = r['niveles'].get(nombres.get(p.ciclo, p.ciclo), 0) + 1
    for p in lista:
        p.grupo_nombre = nombres.get(p.ciclo, p.ciclo)
        p.grado_txt = etiqueta_grado(p.grado) if p.grado is not None else ''
        p.sin_cupo = sin_cupo(ev, c, p.institucion, p.ciclo, ('aprobada',)) if p.estado == 'pendiente' else ''
    cuenta = {e: sum(1 for p in lista if p.estado == e) for e, _ in ParticipacionEvento.ESTADOS}
    if filtro in cuenta:
        lista = [p for p in lista if p.estado == filtro]
    if request.GET.get('csv'):
        r = HttpResponse(content_type='text/csv; charset=utf-8')
        r['Content-Disposition'] = f'attachment; filename="inscripciones-evento-{ev.pk}.csv"'
        r.write('\ufeff')
        w = csv.writer(r)
        w.writerow(['Estado', 'Nombre', 'Documento', 'Institución', 'Ciudad', 'Grado', 'Nivel', 'Contacto', 'Docente acompañante', 'Fecha', 'Autorizó los datos', 'Fecha de la autorización'])
        for p in lista:
            w.writerow([p.get_estado_display(), p.nombre, p.datos.get('documento', ''), p.institucion, p.datos.get('ciudad', ''), p.grado_txt,
                        p.grupo_nombre, p.datos.get('contacto', ''), p.datos.get('acompanante', ''), timezone.localtime(p.empezada).strftime('%Y-%m-%d %H:%M'),
                        (p.datos.get('autorizacion') or {}).get('acudiente', ''), (p.datos.get('autorizacion') or {}).get('fecha', '')])
        return r
    return render(request, 'aula/evento_inscripciones.html', {
        'ev': ev, 'lista': lista, 'filtro': filtro, 'cuenta': cuenta, 'ins': ins,
        'errores_planilla': request.session.pop(f'evento_planilla_{ev.pk}', None),
        'resumen': sorted(resumen.values(), key=lambda r: r['nombre'].lower()), 'base': _base(request)})


@login_required
def resultados(request, eid):
    """Los resultados quedan en la base de datos (una participación por estudiante o inscrito).
    Se filtran por grupo (o todos juntos), por grado y por nombre, curso o institución."""
    ev = _evento(request, eid)
    if not es_organizador(request, ev):
        return HttpResponseForbidden('Solo los organizadores ven todos los resultados.')
    return _resultados(request, ev)


def _resultados(request, ev, veedor=None):
    """Los resultados (para los organizadores, o para un veedor con su enlace de solo lectura)."""
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
    from django.db.models import Count
    grabadas = dict(GrabacionEvento.objects.filter(participacion__evento=ev).values_list('participacion').annotate(n=Count('id')))
    for _, _, filas in tablas:
        for p in filas:
            p.n_grab = grabadas.get(p.pk, 0)
            vg = (p.datos or {}).get('vigilancia') or {}
            p.cortes = len(vg.get('cortes') or [])
            p.salidas = len(vg.get('salidas') or [])
            p.fuera = round(sum((x.get('seg') or 0) for x in (vg.get('salidas') or [])))
            p.grupo_nombre = nombres.get(p.ciclo, p.ciclo)
            g = grado_de(p)
            p.grado_txt = etiqueta_grado(g) if g is not None else ''
    salidas_on = bool(c['vigilancia']['activa'] and c['vigilancia'].get('salidas')) or any(p.salidas for _, _, f in tablas for p in f)
    if request.GET.get('csv') == 'colegios':
        r = HttpResponse(content_type='text/csv; charset=utf-8')
        r['Content-Disposition'] = f'attachment; filename="podio-colegios-evento-{ev.pk}.csv"'
        r.write('\ufeff')
        w = csv.writer(r)
        niveles = grupos(c)
        w.writerow(['Puesto', 'Colegio', 'Puntaje', 'Tiempo efectivo sumado (s)'] + [f'{g["nombre"]}: representante (puntos)' for g in niveles])
        for x in podio_colegios(ev, c):
            w.writerow([x['puesto'], x['colegio'], x['puntaje'], x['tiempo']] +
                       [f"{r_['nombre']} ({r_['puntos']})" if r_ else '—' for _, r_ in x['por_nivel']])
        return r
    if request.GET.get('csv'):
        r = HttpResponse(content_type='text/csv; charset=utf-8')
        r['Content-Disposition'] = f'attachment; filename="resultados-evento-{ev.pk}.csv"'
        r.write('\ufeff')
        w = csv.writer(r)
        con_sal = salidas_on
        w.writerow(['Grupo', 'Puesto', 'Participante', 'Grado', 'Curso o institución', 'Puntos', 'Preguntas bien', 'Tiempo efectivo (s)', 'Terminó']
                   + (['Salidas de la prueba', 'Segundos fuera'] if con_sal else []))
        for n, _, filas in tablas:
            for p in filas:
                w.writerow([p.grupo_nombre, p.puesto, p.nombre_completo, p.grado_txt, p.de_donde,
                            p.puntos, p.bonos, round(p.tiempo_efectivo, 1), 'sí' if p.terminada else 'no']
                           + ([p.salidas, p.fuera] if con_sal else []))
        return r
    grados_hay = sorted({g for g in (grado_de(p) for p in ev.participaciones.select_related('estudiante__curso')) if g is not None})
    return render(request, 'aula/evento_resultados.html', {
        'ev': ev, 'tablas': tablas, 'grupos': grupos(c), 'gsel': gsel, 'gr': gr, 'q': request.GET.get('q', ''),
        'grados': [(g, etiqueta_grado(g)) for g in grados_hay], 'consulta': request.GET.urlencode(), 'base': _base(request),
        'vigilancia': not veedor and (graba(c['vigilancia']) or GrabacionEvento.objects.filter(participacion__evento=ev).exists()),
        'salidas_on': salidas_on,
        'grab': None if veedor else _resumen_grabaciones(ev), 'nubes': _nubes(), 'cfg_nube': _config_nube(request, ev),
        'veedor': veedor, 'vent': ventana(c), 'hide_cuenta': bool(veedor) and not request.user.is_authenticated,
        'podio': podio_colegios(ev, c) if c['podio_colegios']['activo'] else None,
        'pesos': [(g['id'], g['nombre'], (c['podio_colegios'].get('pesos') or {}).get(g['id'], 1)) for g in grupos(c)]})


@login_required
def en_vivo(request, eid):
    """Ranking en vivo para proyectar en el auditorio: los primeros de cada grupo, se actualiza solo."""
    ev = _evento(request, eid)
    if not es_organizador(request, ev):
        return HttpResponseForbidden('Solo los organizadores proyectan el ranking.')
    return _en_vivo(request, ev)


def _en_vivo(request, ev, veedor=None):
    c = config_de(ev)
    try:
        cuantos = max(3, min(30, int(request.GET.get('n') or 10)))
    except ValueError:
        cuantos = 10
    tablas = []
    for g in grupos(c):
        filas = ranking(ev, g['id'])
        tablas.append({'nombre': g['nombre'], 'grados': rango_grados(g), 'total': len(filas),
                       'filas': [{'puesto': p.puesto, 'nombre': p.nombre_completo, 'de': p.de_donde, 'puntos': p.puntos,
                                  'bonos': p.bonos, 'tiempo': round(p.tiempo_efectivo), 'terminada': p.terminada} for p in filas[:cuantos]]})
    if request.GET.get('json'):
        return JsonResponse({'tablas': tablas, 'colegios': _podio_vivo(ev, c), 'activo': ev.activo, 'hora': timezone.localtime().strftime('%H:%M:%S')})
    volver = reverse('aula:evento_veedor', args=[veedor['token']]) if veedor else reverse('aula:evento_resultados', args=[ev.pk])
    return render(request, 'aula/evento_en_vivo.html', {'ev': ev, 'tablas': tablas, 'cuantos': cuantos, 'volver': volver, 'veedor': veedor,
                                                        'colegios': _podio_vivo(ev, c)})


def _podio_vivo(ev, c):
    if not c['podio_colegios']['activo']:
        return None
    return [{'puesto': x['puesto'], 'colegio': x['colegio'], 'puntaje': x['puntaje'], 'niveles': x['n']} for x in podio_colegios(ev, c)[:10]]


# ---------------------------------------------------------------------------
# Veedores: profesores o grupos de profesores invitados (solo lectura, con su enlace)
# ---------------------------------------------------------------------------
def _veedor(token):
    """(evento, veedor) del enlace; 404 si no existe o el organizador lo quitó."""
    token = (token or '')[:60]
    if len(token) < 16:
        raise Http404
    for ev in Evento.objects.filter(config__veedores__icontains=token):
        v = next((v for v in config_de(ev)['veedores'] if v.get('token') == token and v.get('activo', True)), None)
        if v:
            return ev, v
    raise Http404


def veedor_resultados(request, token):
    """Lo que ve un veedor: los resultados de todos los grupos (con filtros y CSV), sin poder cambiar nada."""
    ev, v = _veedor(token)
    return _resultados(request, ev, veedor=v)


def veedor_en_vivo(request, token):
    ev, v = _veedor(token)
    return _en_vivo(request, ev, veedor=v)


def _invitar_veedor(request, ev, v):
    """Le manda al veedor su enlace por correo (si tiene)."""
    if '@' not in (v.get('correo') or ''):
        return 0
    from notas.mensajeria import enviar_correo
    enlace = request.build_absolute_uri(reverse('aula:evento_veedor', args=[v['token']]))
    texto = (f"Hola{(' ' + v['nombre']) if v.get('nombre') else ''},\n\nLo invitamos como veedor del evento «{ev.titulo}»"
             + (f" (grupo: {v['grupo']})" if v.get('grupo') else '') + '.\n\n'
             f'Con este enlace puede ver los resultados y el ranking en vivo, con total transparencia (solo lectura):\n{enlace}\n\n'
             'El enlace es personal: no lo publique.')
    try:
        return enviar_correo(ev.colegio, f'{ev.titulo}: invitación como veedor', texto, [v['correo']], fail_silently=True, copia=False) or 0
    except Exception:
        return 0


@login_required
def diplomas(request, eid):
    """Diplomas para imprimir (o guardar en PDF desde el navegador): de los primeros puestos de cada grupo
    o de participación para todos."""
    ev = _evento(request, eid)
    if not es_organizador(request, ev):
        return HttpResponseForbidden('Solo los organizadores sacan los diplomas.')
    c = config_de(ev)
    tipo = request.GET.get('tipo', 'ganadores')
    gsel = request.GET.get('grupo', '')
    try:
        primeros = max(1, min(20, int(request.GET.get('n') or 3)))
    except ValueError:
        primeros = 3
    PUESTOS = ['Primer', 'Segundo', 'Tercer', 'Cuarto', 'Quinto', 'Sexto', 'Séptimo', 'Octavo', 'Noveno', 'Décimo']
    lista = []
    if tipo == 'colegios':           # podio de colegios: diploma para los primeros colegios
        for x in [x for x in podio_colegios(ev, c) if x['puntaje'] > 0][:primeros]:
            lista.append({'nombre': x['colegio'], 'de': '', 'grupo': 'Podio de colegios', 'puntos': x['puntaje'],
                          'puesto': f'{PUESTOS[x["puesto"] - 1]} puesto' if x['puesto'] <= len(PUESTOS) else f'Puesto {x["puesto"]}'})
    for g in ([] if tipo == 'colegios' else grupos(c)):
        if gsel and g['id'] != gsel:
            continue
        filas = ranking(ev, g['id'])
        if tipo == 'ganadores':
            filas = [p for p in filas if p.puntos > 0][:primeros]
        for p in filas:
            lista.append({'nombre': p.nombre_completo, 'de': p.de_donde, 'grupo': g['nombre'], 'puntos': p.puntos,
                          'puesto': (f'{PUESTOS[p.puesto - 1]} puesto' if p.puesto <= len(PUESTOS) else f'Puesto {p.puesto}') if tipo == 'ganadores' else ''})
    firma = {k: ' '.join((request.GET.get(k) or '').split())[:80] for k in ('firmante', 'cargo', 'lugar')}
    if not firma['firmante'] and request.user.is_authenticated:
        firma['firmante'] = request.user.get_full_name()
    return render(request, 'aula/evento_diplomas.html', {
        'ev': ev, 'lista': lista, 'tipo': tipo, 'gsel': gsel, 'primeros': primeros, 'grupos': grupos(c), 'firma': firma,
        'colegio': ev.colegio, 'fecha': timezone.localdate()})


# ---------------------------------------------------------------------------
# Vigilancia con cámara y micrófono
# ---------------------------------------------------------------------------
MAX_TROZO = 12 * 1024 * 1024            # un trozo de ~30 s pesa menos de 1 MB en calidad baja
MAX_PARTICIPANTE = 900 * 1024 * 1024    # tope por participante (unas 10 h): nadie llena el servidor


@require_POST
def grabacion(request, eid):
    """Llegan los trozos de la grabación (y los avisos: aceptó, se apagó la cámara, la volvió a encender)."""
    ev = _evento(request, eid)
    c = config_de(ev)
    if not c['vigilancia']['activa']:
        return JsonResponse({'ok': False, 'error': 'Este evento no tiene supervisión.'}, status=400)
    p = _participacion(request, ev)
    if p is None:
        return JsonResponse({'ok': True, 'prueba': True})
    archivo = request.FILES.get('trozo')
    if archivo is None:
        tipo = request.POST.get('tipo') or ''
        try:
            t = round(float(request.POST.get('t') or 0), 1)
        except ValueError:
            t = 0
        if tipo in ('sale', 'vuelve'):
            # Registro de salidas: «sale» llega al irse (aunque cierre o bloquee el celular); «vuelve» trae cuánto estuvo fuera
            if not c['vigilancia'].get('salidas'):
                return JsonResponse({'ok': True})
            v = (p.datos or {}).get('vigilancia') or {}
            sal = v.get('salidas') or []
            try:
                seg = max(0.0, min(86400.0, float(request.POST.get('seg') or 0)))
            except ValueError:
                seg = 0.0
            if tipo == 'sale':
                sal = sal[-500:] + [{'hora': timezone.localtime().strftime('%H:%M:%S'), 'dia': timezone.localdate().isoformat(), 't': t,
                                     'motivo': (request.POST.get('motivo') or '')[:60], 'seg': None}]
            elif sal and sal[-1].get('seg') is None:
                sal[-1]['seg'] = round(seg, 1)
            else:     # no llegó el aviso de salida (sin internet): se anota igual
                sal = sal[-500:] + [{'hora': timezone.localtime().strftime('%H:%M:%S'), 'dia': timezone.localdate().isoformat(), 't': t,
                                     'motivo': (request.POST.get('motivo') or '')[:60], 'seg': round(seg, 1)}]
            v['salidas'] = sal
            p.datos = dict(p.datos or {}, vigilancia=v)
            p.save(update_fields=['datos'])
            return JsonResponse({'ok': True})
        if tipo in ('acepto', 'corte', 'reanudo'):
            v = (p.datos or {}).get('vigilancia') or {}
            if tipo == 'acepto':
                v.setdefault('acepto', timezone.now().isoformat(timespec='seconds'))
            else:
                v['cortes'] = (v.get('cortes') or [])[-300:] + [{'tipo': tipo, 't': t, 'hora': timezone.localtime().strftime('%H:%M:%S'),
                                                                  'motivo': (request.POST.get('motivo') or '')[:80]}]
            p.datos = dict(p.datos or {}, vigilancia=v)
            p.save(update_fields=['datos'])
        return JsonResponse({'ok': True})
    if not graba(c['vigilancia']):
        return JsonResponse({'ok': False, 'error': 'Este evento no graba.'}, status=400)
    tipo = (archivo.content_type or '').split(';')[0]
    if not tipo.startswith(('video/', 'audio/', 'image/')) or archivo.size > MAX_TROZO:
        return JsonResponse({'ok': False, 'error': 'Trozo no válido.'}, status=400)
    from django.db.models import Sum
    usado = p.grabaciones.aggregate(b=Sum('bytes'))['b'] or 0
    if usado + archivo.size > MAX_PARTICIPANTE:
        return JsonResponse({'ok': False, 'lleno': True})
    try:
        n = int(request.POST.get('n') or 0)
        seg = float(request.POST.get('t') or 0)
    except ValueError:
        n, seg = 0, 0
    momento = request.POST.get('momento') or ''
    if tipo.startswith('image/'):
        if tipo not in ('image/jpeg', 'image/png', 'image/webp'):
            return JsonResponse({'ok': False, 'error': 'Imagen no válida.'}, status=400)
        tipo = f'{tipo};{momento}' if momento in MOMENTOS else tipo
    archivo.name = f"{'pantallazo' if tipo.startswith('image/') else 'trozo'}-{n:05d}.{ext_de(tipo)}"
    GrabacionEvento.objects.create(participacion=p, numero=n, archivo=archivo, tipo=tipo[:60], segundos=seg, bytes=archivo.size)
    return JsonResponse({'ok': True, 'n': n})


@login_required
def grabaciones(request, eid, pid):
    """El organizador ve la grabación de un participante (trozos en orden) y cuándo se apagó la cámara."""
    ev = _evento(request, eid)
    if not es_organizador(request, ev):
        return HttpResponseForbidden('Solo los organizadores ven las grabaciones.')
    limpiar_grabaciones(ev)
    p = get_object_or_404(ParticipacionEvento, pk=pid, evento=ev)
    todos = list(p.grabaciones.all())
    trozos = [t for t in todos if not t.tipo.startswith('image/')]
    fotos = [dict(g=t, momento=MOMENTOS.get(t.tipo.partition(';')[2], 'pantallazo'), min=f'{int(t.segundos // 60)}:{int(t.segundos % 60):02d}')
             for t in todos if t.tipo.startswith('image/')]
    v = dict((p.datos or {}).get('vigilancia') or {})
    v['salidas'] = [dict(x, min=f"{int((x.get('t') or 0) // 60)}:{int((x.get('t') or 0) % 60):02d}") for x in (v.get('salidas') or [])]
    return render(request, 'aula/evento_grabaciones.html', {
        'salidas_on': bool(config_de(ev)['vigilancia'].get('salidas')),
        'ev': ev, 'p': p, 'trozos': trozos, 'fotos': fotos, 'mb': round(sum(t.bytes for t in todos) / 1048576, 1), 'vig': v,
        'dias': config_de(ev)['vigilancia']['dias'], 'base': _base(request),
        'nubes': _nubes(), 'cfg_nube': _config_nube(request, ev), 'en_nube': sum(1 for t in todos if t.nube), 'total': len(todos)})


@login_required
def grabacion_archivo(request, eid, gid):
    """Abre un trozo (enlace firmado que vence) solo para los organizadores. Con ?bytes=1 lo entrega desde
    este mismo sitio: así el navegador del organizador lo puede copiar a su Google Drive u OneDrive."""
    ev = _evento(request, eid)
    if not es_organizador(request, ev):
        return HttpResponseForbidden('Solo los organizadores ven las grabaciones.')
    g = get_object_or_404(GrabacionEvento, pk=gid, participacion__evento=ev)
    if request.GET.get('bytes'):
        from django.http import FileResponse
        r = FileResponse(g.archivo.open('rb'), content_type=(g.tipo or 'video/webm').split(';')[0])
        r['Cache-Control'] = 'no-store'
        return r
    return redirect(g.archivo.url)


def _nubes():
    from django.conf import settings
    return {'google': bool(getattr(settings, 'GOOGLE_CLIENT_ID', '')), 'onedrive': bool(getattr(settings, 'MICROSOFT_CLIENT_ID', ''))}


def _config_nube(request, ev):
    from django.middleware.csrf import get_token
    return {'nube': reverse('aula:evento_grabaciones_nube', args=[ev.pk]), 'ayudante': '/nube/PROV/', 'csrf': get_token(request)}


def _nombre_archivo(texto, largo=60):
    limpio = ''.join(ch if ch.isalnum() or ch in ' -_.' else ' ' for ch in (texto or ''))
    return ' '.join(limpio.split())[:largo] or 'sin nombre'


@login_required
def grabaciones_nube(request, eid):
    """Para copiar las grabaciones a la nube del organizador (lo hace su navegador con su permiso de Drive u
    OneDrive; el permiso no pasa por el servidor).
    GET: la lista de trozos (de un participante con ?pid= o de todo el evento).
    POST accion=marcar: ya quedaron en la nube · accion=borrar: quitarlos del servidor (solo los que ya están en la nube)."""
    ev = _evento(request, eid)
    if not es_organizador(request, ev):
        return HttpResponseForbidden('Solo los organizadores manejan las grabaciones.')
    qs = GrabacionEvento.objects.filter(participacion__evento=ev).select_related('participacion__estudiante__user')
    if request.method == 'POST':
        try:
            d = json.loads(request.body or b'{}')
        except ValueError:
            d = {}
        ids = [int(x) for x in (d.get('ids') or []) if str(x).isdigit()][:2000]
        if d.get('accion') == 'marcar' and d.get('nube') in ('google', 'onedrive'):
            n = qs.filter(pk__in=ids).update(nube=d['nube'])
        elif d.get('accion') == 'borrar':
            viejas = qs.filter(pk__in=ids).exclude(nube='')
            n = viejas.count()
            viejas.delete()          # una por una (con su archivo)
        else:
            n = 0
        return JsonResponse({'ok': True, 'n': n})
    if request.GET.get('pid'):
        qs = qs.filter(participacion_id=request.GET['pid'])
    personas = {}
    for g in qs.order_by('participacion_id', 'numero', 'pk'):
        p = g.participacion
        x = personas.setdefault(p.pk, {'pid': p.pk, 'nombre': _nombre_archivo(p.nombre_completo), 'de': _nombre_archivo(p.de_donde, 40), 'trozos': []})
        x['trozos'].append({'id': g.pk, 'n': g.numero, 'nube': g.nube, 'bytes': g.bytes,
                            'archivo': f"{x['nombre']} - trozo {g.numero:03d} - {timezone.localtime(g.creada):%Hh%Mm%Ss}.{ext_de(g.tipo)}",
                            'url': reverse('aula:evento_grabacion_archivo', args=[ev.pk, g.pk]) + '?bytes=1'})
    return JsonResponse({'evento': _nombre_archivo(ev.titulo), 'personas': list(personas.values())})


@login_required
def grabaciones_zip(request, eid, pid):
    """Descarga en un .zip todos los trozos de un participante."""
    ev = _evento(request, eid)
    if not es_organizador(request, ev):
        return HttpResponseForbidden('Solo los organizadores ven las grabaciones.')
    import tempfile
    import zipfile
    from django.http import FileResponse
    p = get_object_or_404(ParticipacionEvento, pk=pid, evento=ev)
    tmp = tempfile.TemporaryFile()
    with zipfile.ZipFile(tmp, 'w', zipfile.ZIP_STORED) as z:       # el video ya viene comprimido
        for g in p.grabaciones.all():
            with g.archivo.open('rb') as f:
                z.writestr(f"trozo-{g.numero:03d}-{timezone.localtime(g.creada):%H%M%S}.{ext_de(g.tipo)}", f.read())
    tmp.seek(0)
    return FileResponse(tmp, as_attachment=True, filename=f'grabacion - {_nombre_archivo(p.nombre_completo)}.zip', content_type='application/zip')


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
    c = config_de(ev)
    hasta, desde = _fecha(c['fechas']['prueba_hasta']), _fecha(c['fechas']['prueba_desde'])
    if desde and timezone.now() < desde:
        return None
    if hasta and timezone.now() > hasta + timezone.timedelta(minutes=c['bloques'] * (c['minutos'] + c['descanso']) + 10):
        return None
    p = participante(request, ev, crear=True)
    return p if p is not None and p.estado == 'aprobada' else None


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
        del_ciclo = [(i, x) for i, x in enumerate(ev.preguntas) if x.get('ciclo') == ciclo and not es_de_juego(x)]
        grado = grado_de(p) if p else None
        if grado is not None and any(x.get('grado') == grado for _, x in del_ciclo):
            del_ciclo = [(i, x) for i, x in del_ciclo if x.get('grado') in (grado, None)]      # las de su grado (y las generales)
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
