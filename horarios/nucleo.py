"""Lo que comparten la plataforma y la app de escritorio (Python puro, sin Django).

* El archivo de DATOS (.mch) que exporta la plataforma: cursos, docentes,
  materias, asignaciones con su intensidad horaria y las jornadas con sus horas.
* Las CONDICIONES que se ponen en la app (bloques dobles, máximo por día,
  primeras horas, horas en que el docente no puede, clases fijadas).
* El archivo RESULTADO (.mchr) que la app guarda y la plataforma importa.
* La revisión de choques, que usan las dos.
"""
import json
from collections import defaultdict

from .motor import Problema, resolver

TIPO_DATOS = 'mcolegio-horario-datos'
TIPO_RESULTADO = 'mcolegio-horario-resultado'
VERSION = 1
DIAS = {1: 'Lunes', 2: 'Martes', 3: 'Miércoles', 4: 'Jueves', 5: 'Viernes', 6: 'Sábado'}


class ArchivoInvalido(Exception):
    pass


def minutos(hhmm):
    h, m = hhmm.split(':')
    return int(h) * 60 + int(m)


def leer_json(texto, tipo):
    try:
        datos = json.loads(texto)
    except (ValueError, TypeError):
        raise ArchivoInvalido('El archivo está dañado o no es de mcolegio.')
    if not isinstance(datos, dict) or datos.get('tipo') != tipo:
        raise ArchivoInvalido('Este archivo no es el que se esperaba. Revise que escogió el archivo correcto.')
    if datos.get('version', 0) > VERSION:
        raise ArchivoInvalido('El archivo es de una versión más nueva: actualice la app.')
    return datos


def condiciones_vacias():
    return {'materias': {}, 'docentes': {}, 'fijas': [], 'ih': {}, 'max_por_dia': 2}


# ---------------------------------------------------------------------------
# Índices sobre los datos
# ---------------------------------------------------------------------------
class Datos:
    def __init__(self, d):
        self.crudo = d
        self.colegio = d['colegio']
        self.cursos = {c['id']: c for c in d['cursos']}
        self.docentes = {x['id']: x for x in d['docentes']}
        self.materias = {m['id']: m for m in d['materias']}
        self.asignaciones = {a['id']: a for a in d['asignaciones']}
        self.jornadas = {j['id']: j for j in d['jornadas']}
        self.franjas = {}
        self.jornada_de_curso = {}
        for j in d['jornadas']:
            for f in j['franjas']:
                self.franjas[f['id']] = dict(f, jornada=j['id'])
            for c in j['cursos']:
                self.jornada_de_curso[c] = j['id']

    def nombre_curso(self, cid):
        return self.cursos.get(cid, {}).get('nombre', f'Curso {cid}')

    def nombre_docente(self, did):
        return self.docentes.get(did, {}).get('nombre', f'Docente {did}') if did else 'Sin docente'

    def nombre_materia(self, mid):
        return self.materias.get(mid, {}).get('nombre', f'Materia {mid}')

    def franjas_de(self, jid):
        return sorted(self.jornadas[jid]['franjas'], key=lambda f: f['orden'])

    def ih(self, aid, cond=None):
        if cond and str(aid) in cond.get('ih', {}):
            return int(cond['ih'][str(aid)])
        return int(self.asignaciones[aid].get('ih') or 0)

    def intervalo(self, fid):
        f = self.franjas[fid]
        return minutos(f['inicio']), minutos(f['fin'])


# ---------------------------------------------------------------------------
# Diagnóstico antes de generar
# ---------------------------------------------------------------------------
def diagnostico(datos, cond):
    """[(nivel, texto)]: 'error' impide generar, 'aviso' es para revisar."""
    D = datos
    salida = []
    por_curso = defaultdict(int)
    por_docente = defaultdict(int)
    for a in D.asignaciones.values():
        n = D.ih(a['id'], cond)
        por_curso[a['curso']] += n
        if a.get('docente'):
            por_docente[a['docente']] += n
    for a in D.asignaciones.values():
        if D.ih(a['id'], cond) == 0:
            salida.append(('aviso', f'{D.nombre_materia(a["materia"])} en {D.nombre_curso(a["curso"])} no tiene intensidad '
                                    'horaria: no se va a ubicar.'))
    for cid, horas in por_curso.items():
        jid = D.jornada_de_curso.get(cid)
        if jid is None:
            salida.append(('error', f'{D.nombre_curso(cid)} no está en ninguna jornada (asígnela en la plataforma).'))
            continue
        cupo = len([f for f in D.jornadas[jid]['franjas'] if not f['descanso']]) * len(D.jornadas[jid]['dias'])
        if horas > cupo:
            salida.append(('error', f'{D.nombre_curso(cid)} tiene {horas} horas de clase y solo hay {cupo} espacios en la semana.'))
    for did, horas in por_docente.items():
        cupo = 0
        jornadas = {D.jornada_de_curso.get(a['curso']) for a in D.asignaciones.values() if a.get('docente') == did}
        for jid in jornadas - {None}:
            cupo += len([f for f in D.jornadas[jid]['franjas'] if not f['descanso']]) * len(D.jornadas[jid]['dias'])
        no_puede = len(cond.get('docentes', {}).get(str(did), {}).get('no_puede', []))
        if horas > cupo - no_puede:
            salida.append(('error', f'{D.nombre_docente(did)} tiene {horas} horas y solo {cupo - no_puede} espacios disponibles.'))
    for a in D.asignaciones.values():
        if not a.get('docente') and D.ih(a['id'], cond):
            salida.append(('aviso', f'{D.nombre_materia(a["materia"])} en {D.nombre_curso(a["curso"])} no tiene docente.'))
    return salida


# ---------------------------------------------------------------------------
# Armar el problema y resolver
# ---------------------------------------------------------------------------
def armar(datos, cond):
    D = datos
    franjas = {}
    siguiente = {}
    for jid, j in D.jornadas.items():
        lst = D.franjas_de(jid)
        for i, f in enumerate(lst):
            franjas[f['id']] = (jid, f['orden'], minutos(f['inicio']), minutos(f['fin']))
        clase = [f for f in lst]
        for a, b in zip(clase, clase[1:]):
            if not a['descanso'] and not b['descanso']:
                siguiente[a['id']] = b['id']
    # Solo las franjas de clase cuentan para el índice de huecos.
    franjas_clase = {fid: v for fid, v in franjas.items() if not D.franjas[fid]['descanso']}
    slots = {}
    for cid, jid in D.jornada_de_curso.items():
        j = D.jornadas[jid]
        slots[cid] = [(d, f['id']) for d in j['dias'] for f in D.franjas_de(jid) if not f['descanso']]
    mat = cond.get('materias', {})
    dobles = {int(m) for m, r in mat.items() if r.get('doble')}
    primeras = {int(m) for m, r in mat.items() if r.get('primeras')}
    defecto = int(cond.get('max_por_dia') or 2)
    fijas = []
    usadas = defaultdict(int)
    for fx in cond.get('fijas', []):
        a = D.asignaciones.get(int(fx['asignacion']))
        if not a:
            continue
        fijas.append({'asig': a['id'], 'curso': a['curso'], 'docente': a.get('docente') or -a['id'],
                      'materia': a['materia'], 'dia': int(fx['dia']), 'franja': int(fx['franja'])})
        usadas[a['id']] += 1
    unidades = []
    max_materia_dia = {}
    for a in D.asignaciones.values():
        if a['curso'] not in D.jornada_de_curso:
            continue
        n = max(0, D.ih(a['id'], cond) - usadas[a['id']])
        regla = mat.get(str(a['materia']), {})
        max_materia_dia[(a['curso'], a['materia'])] = int(regla.get('max_dia') or defecto)
        doc = a.get('docente') or -a['id']          # sin docente: no choca con nadie
        if a['materia'] in dobles:
            for _ in range(n // 2):
                unidades.append({'id': f'{a["id"]}-{len(unidades)}', 'asig': a['id'], 'curso': a['curso'],
                                 'docente': doc, 'materia': a['materia'], 'largo': 2})
            n %= 2
        for _ in range(n):
            unidades.append({'id': f'{a["id"]}-{len(unidades)}', 'asig': a['id'], 'curso': a['curso'],
                             'docente': doc, 'materia': a['materia'], 'largo': 1})
    no_puede = {}
    max_docente_dia = {}
    for did, r in cond.get('docentes', {}).items():
        no_puede[int(did)] = {tuple(int(x) for x in k.split('-')) for k in r.get('no_puede', [])}
        if r.get('max_dia'):
            max_docente_dia[int(did)] = int(r['max_dia'])
    p = Problema(franjas_clase, siguiente, slots, unidades, fijas=fijas, no_puede=no_puede,
                 max_materia_dia=max_materia_dia, max_docente_dia=max_docente_dia, primeras=primeras, dobles=dobles)
    return p


def generar(datos, cond, segundos=30, semilla=0, avance=None):
    """Un horario: {'sesiones': [...], 'sin_ubicar': [...], 'costo', 'huecos'}."""
    from .motor import huecos_por_docente
    p = armar(datos, cond)
    r = resolver(p, segundos=segundos, semilla=semilla, avance=avance)
    est = r['estado']
    sesiones = []
    for fx in cond.get('fijas', []):
        a = datos.asignaciones.get(int(fx['asignacion']))
        if a:
            sesiones.append({'asignacion': a['id'], 'curso': a['curso'], 'dia': int(fx['dia']),
                             'franja': int(fx['franja']), 'fijada': True})
    for uid, (dia, franja) in r['ubicadas'].items():
        u = est.u[uid]
        for f in est.celdas(u, dia, franja):
            sesiones.append({'asignacion': u['asig'], 'curso': u['curso'], 'dia': dia, 'franja': f})
    sin = defaultdict(int)
    for uid in r['sin_ubicar']:
        u = est.u[uid]
        sin[u['asig']] += u['largo']
    huecos = {did: h for did, h in huecos_por_docente(est).items() if did and did > 0}
    return {'sesiones': sesiones, 'costo': r['costo'], 'huecos': sum(huecos.values()),
            'sin_ubicar': [{'asignacion': a, 'horas': h} for a, h in sin.items()]}


# ---------------------------------------------------------------------------
# Revisión de choques (la usan la app y la plataforma al importar)
# ---------------------------------------------------------------------------
def revisar(datos, sesiones, cond=None):
    """[texto] con cada choque o incumplimiento."""
    D = datos
    errores = []
    curso_ocupado = {}
    docente_dia = defaultdict(list)
    horas = defaultdict(int)
    for s in sesiones:
        a = D.asignaciones.get(s['asignacion'])
        if a is None:
            errores.append(f'Hay una clase de una asignación que ya no existe (id {s["asignacion"]}).')
            continue
        if s['franja'] not in D.franjas:
            errores.append(f'{D.nombre_materia(a["materia"])} en {D.nombre_curso(a["curso"])}: hora que no existe.')
            continue
        clave = (a['curso'], s['dia'], s['franja'])
        if clave in curso_ocupado:
            errores.append(f'{D.nombre_curso(a["curso"])} tiene dos clases el {DIAS.get(s["dia"])} a las '
                           f'{D.franjas[s["franja"]]["inicio"]}.')
        curso_ocupado[clave] = a['id']
        horas[a['id']] += 1
        if a.get('docente'):
            ini, fin = D.intervalo(s['franja'])
            for (x, y, otro) in docente_dia[(a['docente'], s['dia'])]:
                if x < fin and ini < y:
                    errores.append(f'{D.nombre_docente(a["docente"])} queda en dos clases el {DIAS.get(s["dia"])} a las '
                                   f'{D.franjas[s["franja"]]["inicio"]} ({D.nombre_curso(a["curso"])} y '
                                   f'{D.nombre_curso(D.asignaciones[otro]["curso"])}).')
            docente_dia[(a['docente'], s['dia'])].append((ini, fin, a['id']))
            if cond:
                no = cond.get('docentes', {}).get(str(a['docente']), {}).get('no_puede', [])
                if f'{s["dia"]}-{s["franja"]}' in no:
                    errores.append(f'{D.nombre_docente(a["docente"])} tiene clase el {DIAS.get(s["dia"])} a las '
                                   f'{D.franjas[s["franja"]]["inicio"]}, hora en que no puede.')
    return errores


def horas_faltantes(datos, sesiones, cond=None):
    horas = defaultdict(int)
    for s in sesiones:
        horas[s['asignacion']] += 1
    salida = []
    for a in datos.asignaciones.values():
        falta = datos.ih(a['id'], cond) - horas[a['id']]
        if falta > 0:
            salida.append((a, falta))
    return salida


def resultado(datos, sesiones, nombre, informe=None):
    return {'tipo': TIPO_RESULTADO, 'version': VERSION, 'nombre': nombre,
            'origen': {'colegio': datos.colegio['id'], 'exportado': datos.crudo.get('exportado'),
                       'firma': datos.crudo.get('firma', '')},
            'sesiones': [{'asignacion': s['asignacion'], 'dia': s['dia'], 'franja': s['franja']} for s in sesiones],
            'informe': informe or {}}
