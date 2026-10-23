"""Horarios especiales que salen del horario oficial sin cambiarlo.

* Día con docentes ausentes: los cursos afectados salen más temprano o entran más tarde
  (se corren sus clases), y lo que no se pueda correr lo cubre un docente con menos horas.
* Semana A y Semana B: un proyecto aparte con un ciclo de 10 días (Día 1 a 5 = semana A,
  Día 6 a 10 = semana B) y las horas repartidas parejo entre las dos semanas.
* Semana de dirección de grado: cada director tiene una hora con su curso, que le cuenta en
  su asignación; esa hora la cede una materia del curso, rotando cuál cede cada vez.
"""
import copy
import re
from collections import defaultdict

from . import nucleo

UMBRAL_BACHILLERATO = 22
UMBRAL_PRIMARIA = 25


# ----------------------------------------------------------------------------- utilidades

def _hora(D, fid, fin=False):
    f = D.franjas[fid]
    return f['fin'] if fin else f['inicio']


def _choca(tramos, ini, fin):
    return any(a < fin and ini < b for a, b in tramos)


def horas_por_docente(p, alt):
    """{docente: horas de clase a la semana en ese horario}."""
    D = p.datos
    out = defaultdict(int)
    for s in alt['sesiones']:
        a = D.asignaciones.get(s['asignacion'])
        if a and a.get('docente') and s['franja'] in D.franjas:
            out[a['docente']] += 1
    return dict(out)


def _umbral(D, cid, umbral_bach, umbral_prim):
    g = D.cursos.get(cid, {}).get('grado')
    try:
        return umbral_bach if g is not None and int(g) >= 6 else umbral_prim
    except (TypeError, ValueError):
        return umbral_prim


def _ocupacion_del_dia(p, alt, dia):
    """{docente: [(ini, fin)]} de clases, reuniones y actividades ese día."""
    D = p.datos
    oc = defaultdict(list)
    for (did, d), tramos in nucleo._ocupado(D, alt['sesiones'], alt.get('reuniones')).items():
        if d == dia:
            oc[did] += list(tramos)
    for x in alt.get('actividades') or []:
        if x['dia'] == dia and x['franja'] in D.franjas:
            oc[x['docente']].append(D.intervalo(x['franja']))
    return oc


# ----------------------------------------------------------------------------- día con ausencias

def plan_ausencias(p, alt, dia, ausentes, modo='auto', umbral_bach=UMBRAL_BACHILLERATO,
                   umbral_prim=UMBRAL_PRIMARIA):
    """Plan para un día en que faltan docentes, sin tocar el horario oficial.

    modo: 'temprano' (las clases que quedan se corren al comienzo y el curso sale antes),
    'tarde' (se corren al final y el curso entra más tarde) o 'auto' (lo que mueva menos clases).
    Si no se pueden correr, las horas libres en medio de la jornada las cubre un docente que ese
    día está en el colegio, libre a esa hora y con menos horas que el umbral (22 en bachillerato,
    25 en primaria). Devuelve {'cursos': [...], 'reemplazos': [...], 'sin_cubrir': [...],
    'avisos_docentes': {docente: [texto]}}.
    """
    D = p.datos
    ausentes = {int(x) for x in ausentes}
    carga = horas_por_docente(p, alt)
    oc = _ocupacion_del_dia(p, alt, dia)
    for did in ausentes:
        oc.pop(did, None)
    del_dia = [(i, s, D.asignaciones.get(s['asignacion'])) for i, s in enumerate(alt['sesiones'])
               if s['dia'] == dia and s['franja'] in D.franjas and D.asignaciones.get(s['asignacion'])]
    afectados = sorted({a['curso'] for _, _, a in del_dia if a.get('docente') in ausentes},
                       key=D.nombre_curso)
    salida = {'dia': dia, 'ausentes': sorted(ausentes, key=D.nombre_docente), 'cursos': [], 'reemplazos': [],
              'sin_cubrir': [], 'avisos_docentes': defaultdict(list)}
    for cid in afectados:
        jid = D.jornada_de_curso.get(cid)
        if jid is None:
            continue
        franjas = [f['id'] for f in D.franjas_de(jid) if not f['descanso']]
        mias = [(i, s, a) for i, s, a in del_dia if a['curso'] == cid]
        usadas = sorted({s['franja'] for _, s, _ in mias}, key=franjas.index)
        rango = franjas[franjas.index(usadas[0]):franjas.index(usadas[-1]) + 1] if usadas else []
        presentes = [(i, s, a) for i, s, a in mias if a.get('docente') not in ausentes]
        faltan = [(i, s, a) for i, s, a in mias if a.get('docente') in ausentes]
        # La ocupación de los docentes sin las clases de este curso (que se van a reacomodar)
        propias = defaultdict(list)
        for _, s, a in presentes:
            if a.get('docente'):
                propias[a['docente']].append(D.intervalo(s['franja']))

        def libre(did, fid):
            if not did:
                return True
            ini, fin = D.intervalo(fid)
            tramos = list(oc.get(did, []))
            for t in propias.get(did, []):
                if t in tramos:
                    tramos.remove(t)
            return not _choca(tramos, ini, fin)

        opciones = []
        n = len(presentes)
        if n and n < len(rango):
            for nombre, destino in (('temprano', rango[:n]), ('tarde', rango[-n:])):
                if modo not in ('auto', nombre):
                    continue
                asignado = _emparejar(presentes, destino, libre)
                if asignado is not None:
                    movidas = sum(1 for k, fid in asignado.items() if presentes[k][1]['franja'] != fid)
                    opciones.append((movidas, 0 if nombre == 'temprano' else 1, nombre, asignado))
        filas = {fid: {'franja': fid, 'hora': _hora(D, fid), 'antes': '', 'ahora': ''} for fid in rango}
        for i, s, a in mias:
            filas[s['franja']]['antes'] = f'{D.nombre_materia(a["materia"])} · {D.nombre_docente(a.get("docente"))}'
        info = {'curso': cid, 'nombre': D.nombre_curso(cid), 'modo': '', 'texto': '', 'filas': [], 'clases': []}
        if opciones:
            _, _, nombre, asignado = min(opciones)
            for k, fid in asignado.items():
                i, s, a = presentes[k]
                txt = f'{D.nombre_materia(a["materia"])} · {D.nombre_docente(a.get("docente"))}'
                if s['franja'] != fid:
                    txt += f' (corrida de las {_hora(D, s["franja"])})'
                    did = a.get('docente')
                    if did:
                        salida['avisos_docentes'][did].append(
                            f'{D.nombre_curso(cid)}: su clase de las {_hora(D, s["franja"])} pasa a las {_hora(D, fid)}.')
                        tramos = oc[did]
                        viejo = D.intervalo(s['franja'])
                        if viejo in tramos:
                            tramos.remove(viejo)
                        tramos.append(D.intervalo(fid))
                filas[fid]['ahora'] = txt
                info['clases'].append({'franja': fid, 'docente': a.get('docente')})
            for fid in rango:
                if not filas[fid]['ahora']:
                    filas[fid]['ahora'] = 'Sin clase (sale temprano)' if nombre == 'temprano' else 'Sin clase (entra más tarde)'
            ocupadas = [fid for fid in rango if fid in set(asignado.values())]
            info['modo'] = nombre
            info['texto'] = (f'Sale a las {_hora(D, ocupadas[-1], fin=True)}' if nombre == 'temprano'
                             else f'Entra a las {_hora(D, ocupadas[0])}')
        else:
            # No se pudo correr: se quedan donde están y se cubren las horas de en medio
            for i, s, a in presentes:
                filas[s['franja']]['ahora'] = f'{D.nombre_materia(a["materia"])} · {D.nombre_docente(a.get("docente"))}'
                info['clases'].append({'franja': s['franja'], 'docente': a.get('docente')})
            libres_ini = 0
            for fid in rango:
                if filas[fid]['ahora']:
                    break
                libres_ini += 1
            libres_fin = 0
            for fid in reversed(rango):
                if filas[fid]['ahora']:
                    break
                libres_fin += 1
            info['modo'] = 'reemplazos'
            partes = []
            if libres_ini and libres_ini < len(rango):
                partes.append(f'entra a las {_hora(D, rango[libres_ini])}')
            if libres_fin and libres_fin < len(rango):
                partes.append(f'sale a las {_hora(D, rango[-libres_fin - 1], fin=True)}')
            for k, fid in enumerate(rango):
                if filas[fid]['ahora']:
                    continue
                if k < libres_ini:
                    filas[fid]['ahora'] = 'Sin clase (entra más tarde)'
                    continue
                if k >= len(rango) - libres_fin:
                    filas[fid]['ahora'] = 'Sin clase (sale temprano)'
                    continue
                ausente = next((a.get('docente') for _, s, a in faltan if s['franja'] == fid), None)
                quien = _reemplazante(p, alt, cid, fid, oc, carga, ausentes,
                                      _umbral(D, cid, umbral_bach, umbral_prim))
                if quien:
                    oc[quien].append(D.intervalo(fid))
                    carga[quien] = carga.get(quien, 0) + 1
                    filas[fid]['ahora'] = f'Reemplazo: {D.nombre_docente(quien)}'
                    info['clases'].append({'franja': fid, 'docente': quien, 'reemplazo': True})
                    salida['reemplazos'].append({'curso': cid, 'franja': fid, 'docente': quien, 'ausente': ausente})
                    salida['avisos_docentes'][quien].append(
                        f'Reemplazo en {D.nombre_curso(cid)} a las {_hora(D, fid)}'
                        + (f' (por {D.nombre_docente(ausente)})' if ausente else '') + '.')
                else:
                    filas[fid]['ahora'] = 'Sin cubrir'
                    salida['sin_cubrir'].append({'curso': cid, 'franja': fid, 'ausente': ausente})
            info['texto'] = ('Se queda en su horario' + (': ' + ', '.join(partes) if partes else '')
                             + (f' · {sum(1 for f in filas.values() if f["ahora"].startswith("Reemplazo"))} reemplazo(s)'))
        info['filas'] = [filas[fid] for fid in rango]
        salida['cursos'].append(info)
    salida['avisos_docentes'] = dict(salida['avisos_docentes'])
    return salida


def _emparejar(clases, destino, libre):
    """Cada clase a una hora de `destino` donde su docente esté libre. {índice: franja} o None."""
    candidatos = []
    for c in clases:
        _, s, a = c
        ok = [fid for fid in destino if fid == s['franja'] or libre(a.get('docente'), fid)]
        # primero la misma hora (para mover lo menos posible)
        ok.sort(key=lambda fid: fid != s['franja'])
        candidatos.append(ok)
    dueno = {}

    def probar(k, vistos):
        for fid in candidatos[k]:
            if fid in vistos:
                continue
            vistos.add(fid)
            # el mismo docente no puede quedar dos veces a la misma hora
            if fid not in dueno or probar(dueno[fid], vistos):
                dueno[fid] = k
                return True
        return False
    for k in range(len(clases)):
        if not probar(k, set()):
            return None
    return {k: fid for fid, k in dueno.items()}     # {índice de la clase: franja}


def _reemplazante(p, alt, cid, fid, oc, carga, ausentes, umbral):
    D = p.datos
    ini, fin = D.intervalo(fid)
    conocen = {a.get('docente') for a in D.asignaciones.values() if a['curso'] == cid}
    jid = D.jornada_de_curso.get(cid)
    candidatos = []
    for did in D.docentes:
        if did in ausentes or carga.get(did, 0) >= umbral:
            continue
        if jid not in D.jornadas_de_docente(did):
            continue
        tramos = oc.get(did, [])
        if _choca(tramos, ini, fin):
            continue
        en_colegio = bool(tramos)
        candidatos.append((not en_colegio, did not in conocen, carga.get(did, 0), D.nombre_docente(did), did))
    return min(candidatos)[-1] if candidatos else None


# ----------------------------------------------------------------------------- semana A y semana B

NOMBRES_DIA = {1: 'Lunes', 2: 'Martes', 3: 'Miércoles', 4: 'Jueves', 5: 'Viernes', 6: 'Sábado'}
_CELDA = re.compile(r'^(\d+)-(\d+)$')


def _doblar_patron(texto):
    t = str(texto or '').strip()
    return f'{t}+{t}' if t else t


def _doblar_celdas(valor, mapa):
    """Cambia cada 'dia-franja' de la semana por las dos celdas (semana A y semana B)."""
    if isinstance(valor, dict):
        return {k: _doblar_celdas(v, mapa) for k, v in valor.items()}
    if isinstance(valor, list):
        out = []
        for x in valor:
            m = _CELDA.match(x) if isinstance(x, str) else None
            if m and int(m.group(1)) in mapa:
                out += [f'{d}-{m.group(2)}' for d in mapa[int(m.group(1))]]
            else:
                out.append(_doblar_celdas(x, mapa))
        return out
    return valor


def dos_semanas(p, horario=None):
    """Proyecto nuevo con Semana A y Semana B (ciclo de 10 días) a partir de uno semanal.

    Las horas de cada clase se duplican (son para las dos semanas) y el generador las reparte
    parejo. Las horas marcadas (no puede, mejor no, bloqueos…) valen para las dos semanas. Si se
    da un horario, se copia igual en las dos semanas para empezar desde ahí.
    """
    from .proyecto import Proyecto
    D = p.datos
    crudo = copy.deepcopy(D.crudo)
    mapa = {}
    for j in crudo['jornadas']:
        dias = sorted(j['dias'])
        if not dias or any(d > 6 for d in dias):
            continue                      # ya es por ciclo
        n = len(dias)
        for k, d in enumerate(dias):
            mapa.setdefault(d, (100 + k + 1, 100 + n + k + 1))
        j['dias'] = [100 + k for k in range(1, 2 * n + 1)]
    cond = _doblar_celdas(copy.deepcopy(p.cond), mapa)
    cond['ih'] = {str(aid): 2 * D.ih(aid, p.cond) for aid in D.asignaciones}
    for r in cond.get('asignaciones', {}).values():
        if r.get('bloques'):
            r['bloques'] = _doblar_patron(r['bloques'])
        if r.get('extra_horas') not in (None, ''):
            try:
                r['extra_horas'] = 2 * int(r['extra_horas'])
            except (TypeError, ValueError):
                pass
    for r in cond.get('materias', {}).values():
        if r.get('bloques'):
            r['bloques'] = _doblar_patron(r['bloques'])
    cond['fijas'] = [dict(f, dia=d) for f in cond.get('fijas', []) for d in mapa.get(int(f['dia']), (f['dia'],))]
    nombres = {}
    for d, (a, b) in mapa.items():
        nombres[str(a)] = f'{NOMBRES_DIA.get(d, d)} A'
        nombres[str(b)] = f'{NOMBRES_DIA.get(d, d)} B'
    cond['semanas_ab'] = {'activa': True, 'a': sorted(a for a, _ in mapa.values()),
                          'b': sorted(b for _, b in mapa.values()), 'nombres': nombres}
    nuevo = Proyecto(crudo, cond)
    if horario:
        alt = {'nombre': f'{horario.get("nombre") or "Horario"} (A y B)', 'sesiones': [], 'horas_sin_ubicar': 0,
               'choques': [], 'reuniones': nuevo.ver_reuniones(), 'actividades': [], 'acompanamientos': [],
               'costo': None, 'huecos': None, 'divididas': [], 'manual': True}
        for s in horario['sesiones']:
            for d in mapa.get(s['dia'], (s['dia'],)):
                alt['sesiones'].append(dict(s, dia=d, fijada=False))
        nuevo.alternativas.append(alt)
        nuevo.revisar(alt)
    return nuevo


def balance_semanas(p, alt):
    """[(docente, horas semana A, horas semana B)] de un proyecto con semanas A y B."""
    ab = p.cond.get('semanas_ab') or {}
    a, b = set(ab.get('a') or []), set(ab.get('b') or [])
    D = p.datos
    cuenta = defaultdict(lambda: [0, 0])
    for s in alt['sesiones']:
        x = D.asignaciones.get(s['asignacion'])
        if x and x.get('docente'):
            if s['dia'] in a:
                cuenta[x['docente']][0] += 1
            elif s['dia'] in b:
                cuenta[x['docente']][1] += 1
    return sorted(((did, v[0], v[1]) for did, v in cuenta.items()), key=lambda t: D.nombre_docente(t[0]))


# ----------------------------------------------------------------------------- dirección de grado

def director(p, cid):
    r = (p.cond.get('cursos') or {}).get(str(cid)) or {}
    if r.get('director') not in (None, ''):
        return int(r['director'])
    d = p.datos.cursos.get(cid, {}).get('director')
    return int(d) if d else None


def semana_direccion(p, alt, modo='generador', dia=None, franja=None, guardar_rotacion=True):
    """Copia del horario para la semana de dirección de grado.

    Cada director tiene una hora con su curso (le cuenta como clase) y esa hora la cede una
    materia del curso: la que menos veces ha cedido (se rota), mejor de las que tienen más horas
    y en un día en que el director ya está en el colegio. modo='colegio': todos a la misma hora
    (dia, franja). Devuelve (horario nuevo, avisos, [(docente, horas antes, horas esa semana)]).
    """
    D = p.datos
    nuevo = copy.deepcopy(alt)
    nuevo['nombre'] = f'{alt.get("nombre") or "Horario"} · dirección de grado'
    nuevo['direccion'] = []
    for s in nuevo['sesiones']:
        s['fijada'] = False
    reg = p.cond.setdefault('direccion_grado', {})
    historial = reg.setdefault('historial', {})
    avisos = []
    antes = horas_por_docente(p, alt)
    ocupado = defaultdict(list)                  # (docente, dia) -> [(ini, fin)]
    for (did, d), tramos in nucleo._ocupado(D, nuevo['sesiones'], nuevo.get('reuniones')).items():
        ocupado[(did, d)] = list(tramos)
    ceder = set()
    usados_director = {}
    for cid in sorted(D.jornada_de_curso, key=D.nombre_curso):
        dr = director(p, cid)
        if not dr:
            avisos.append(f'{D.nombre_curso(cid)} no tiene director(a) de grado.')
            continue
        if dr in usados_director:
            avisos.append(f'{D.nombre_docente(dr)} es director(a) de {D.nombre_curso(usados_director[dr])} y de '
                          f'{D.nombre_curso(cid)}: se le pone la hora solo en el primero.')
            continue
        hist = historial.setdefault(str(cid), {})
        opciones = []
        for i, s in enumerate(nuevo['sesiones']):
            a = D.asignaciones.get(s['asignacion'])
            if not a or a['curso'] != cid or i in ceder or s['franja'] not in D.franjas:
                continue
            if modo == 'colegio' and (s['dia'] != dia or s['franja'] != franja):
                continue
            ini, fin = D.intervalo(s['franja'])
            tramos = list(ocupado[(dr, s['dia'])])
            if a.get('docente') == dr and (ini, fin) in tramos:
                tramos.remove((ini, fin))               # es su propia clase con el curso
            if modo != 'colegio' and _choca(tramos, ini, fin):
                continue
            presente = bool(ocupado[(dr, s['dia'])])
            veces = int(hist.get(str(a['materia']), 0))
            opciones.append((veces, not presente, -D.ih(a['id'], p.cond), s['dia'], D.franjas[s['franja']]['orden'],
                             i, s, a))
        if not opciones:
            avisos.append(f'{D.nombre_curso(cid)}: no se encontró una hora en que el director(a) esté libre.')
            continue
        *_, i, s, a = min(opciones)
        ceder.add(i)
        usados_director[dr] = cid
        ini, fin = D.intervalo(s['franja'])
        if a.get('docente') and (ini, fin) in ocupado[(a['docente'], s['dia'])]:
            ocupado[(a['docente'], s['dia'])].remove((ini, fin))
        ocupado[(dr, s['dia'])].append((ini, fin))
        nuevo['direccion'].append({'curso': cid, 'docente': dr, 'dia': s['dia'], 'franja': s['franja'],
                                   'cede': a['materia'], 'docente_cede': a.get('docente')})
        if guardar_rotacion:
            hist[str(a['materia'])] = int(hist.get(str(a['materia']), 0)) + 1
    nuevo['sesiones'] = [s for k, s in enumerate(nuevo['sesiones']) if k not in ceder]
    despues = horas_por_docente(p, nuevo)
    for x in nuevo['direccion']:
        despues[x['docente']] = despues.get(x['docente'], 0) + 1
    p.revisar(nuevo)
    resumen = sorted(((did, antes.get(did, 0), despues.get(did, 0)) for did in set(antes) | set(despues)),
                     key=lambda t: D.nombre_docente(t[0]))
    return nuevo, avisos, resumen
