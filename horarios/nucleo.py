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

from .motor import Problema, resolver, unidad_simple

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
    return {'materias': {}, 'docentes': {}, 'fijas': [], 'ih': {}, 'max_por_dia': 2,
            'asignaciones': {},          # {aid: {'extra': bool, 'bloques': '2+2', 'dividir': bool}}
            'permanencia_horas': 0,      # 0 = sin control; 6 en los oficiales (Decreto 1850/2002)
            'desplazamiento': 30,        # minutos para cambiar de sede
            'max_seguidas': 0,           # máximo de horas seguidas de un docente (0 = sin límite)
            'reuniones': [],
            'simultaneas': [],           # [{'nombre', 'asignaciones': [aid…]}] van a la misma hora
            'espacios': []}              # [{'nombre', 'capacidad'}] sala de sistemas, laboratorio…


def patron(texto):
    """'2+2+1' -> [2, 2, 1]; None si no se entiende."""
    try:
        partes = [int(x) for x in str(texto or '').replace(' ', '').split('+') if x]
    except ValueError:
        return None
    return partes if partes and all(1 <= x <= 4 for x in partes) else None


def ajustar(partes, total):
    """Recorta o completa un patrón de bloques para que sume `total`."""
    out, resto = [], total
    for x in partes:
        if resto <= 0:
            break
        out.append(min(x, resto))
        resto -= out[-1]
    return out + [1] * resto


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
        self.areas = {}
        for m in d['materias']:
            if m.get('area'):
                self.areas.setdefault(m['area'], []).append(m['id'])
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

    def sede_de_curso(self, cid):
        return self.cursos.get(cid, {}).get('sede') or ''

    def docentes_de_area(self, area):
        mats = set(self.areas.get(area, []))
        return sorted({a['docente'] for a in self.asignaciones.values() if a['materia'] in mats and a.get('docente')},
                      key=self.nombre_docente)

    def jornadas_de_docente(self, did):
        return sorted({self.jornada_de_curso[a['curso']] for a in self.asignaciones.values()
                       if a.get('docente') == did and a['curso'] in self.jornada_de_curso})

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
# Reuniones de área
# ---------------------------------------------------------------------------
def _horas_de_clase(datos):
    """[(dia, inicio, fin, {jornada: franja_id})] de todas las horas de clase, sin repetir."""
    vistas = {}
    for jid, j in datos.jornadas.items():
        for f in datos.franjas_de(jid):
            if f['descanso']:
                continue
            for d in j['dias']:
                clave = (d, minutos(f['inicio']), minutos(f['fin']))
                vistas.setdefault(clave, {})[jid] = f['id']
    return sorted((d, a, b, m) for (d, a, b), m in vistas.items())


def _puede_reunirse(datos, did, dia, ini, fin, no_puede):
    """Franjas del docente que ocupa esa reunión, o None si no puede asistir."""
    ocupa = []
    for jid in datos.jornadas_de_docente(did):
        j = datos.jornadas[jid]
        if dia not in j['dias']:
            continue
        for f in datos.franjas_de(jid):
            if f['descanso']:
                continue
            a, b = minutos(f['inicio']), minutos(f['fin'])
            if a < fin and ini < b:
                if (dia, f['id']) in no_puede.get(did, set()):
                    return None
                ocupa.append(f['id'])
    return ocupa or None


def ubicar_reuniones(datos, cond, no_puede=None):
    """Escoge la hora de cada reunión de área y bloquea esa hora a los que asisten.

    Busca la hora en que puede la mayoría (el jefe de área siempre). Si no pueden
    todos y se permite, busca una segunda reunión para los que faltan, también
    con el jefe. Devuelve (resultados, no_puede actualizado).
    """
    no_puede = {k: set(v) for k, v in (no_puede or {}).items()}
    horas = _horas_de_clase(datos)
    resultados = []
    for r in cond.get('reuniones', []):
        miembros = [int(x) for x in r.get('docentes', []) if int(x) in datos.docentes]
        jefe = int(r['jefe']) if r.get('jefe') else None
        if jefe and jefe not in miembros:
            miembros.append(jefe)
        if not miembros:
            continue

        def evaluar(dia, ini, fin, quienes):
            asisten = {}
            for did in quienes:
                oc = _puede_reunirse(datos, did, dia, ini, fin, no_puede)
                if oc:
                    asisten[did] = oc
            return asisten

        def mejor(quienes, excluir=()):
            elegido, puntos = None, -1
            for (dia, ini, fin, _) in horas:
                if (dia, ini) in excluir:
                    continue
                if r.get('modo') == 'fija' and not excluir:
                    if dia != int(r.get('dia') or 0) or ini != minutos(r.get('hora') or '00:00'):
                        continue
                asisten = evaluar(dia, ini, fin, quienes)
                if jefe and jefe not in asisten:
                    continue
                pts = len(asisten) * 1000 + ini           # a igual asistencia, más tarde en el día
                if pts > puntos:
                    elegido, puntos = (dia, ini, fin, asisten), pts
            return elegido

        primera = mejor(miembros)
        res = {'nombre': r.get('nombre') or 'Reunión de área', 'jefe': jefe, 'miembros': miembros,
               'ubicada': bool(primera), 'segunda': None}
        if primera:
            dia, ini, fin, asisten = primera
            res.update({'dia': dia, 'inicio': ini, 'fin': fin, 'asisten': sorted(asisten),
                        'faltan': sorted(set(miembros) - set(asisten))})
            for did, oc in asisten.items():
                no_puede.setdefault(did, set()).update((dia, f) for f in oc)
            if res['faltan'] and r.get('dos', True):
                quienes = res['faltan'] + ([jefe] if jefe else [])
                otra = mejor(quienes, excluir={(dia, ini)})
                if otra:
                    d2, i2, f2, as2 = otra
                    res['segunda'] = {'dia': d2, 'inicio': i2, 'fin': f2, 'asisten': sorted(as2)}
                    res['faltan'] = sorted(set(res['faltan']) - set(as2))
                    for did, oc in as2.items():
                        no_puede.setdefault(did, set()).update((d2, f) for f in oc)
        resultados.append(res)
    return resultados, no_puede


def texto_hora(m):
    return f'{m // 60:02d}:{m % 60:02d}'


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
    asg = cond.get('asignaciones', {})
    dobles = set()
    primeras = {int(m) for m, r in mat.items() if r.get('primeras')}
    ultimas = {int(m) for m, r in mat.items() if r.get('ultimas')}
    defecto = int(cond.get('max_por_dia') or 2)
    espacios = {e['nombre']: max(1, int(e.get('capacidad') or 1)) for e in cond.get('espacios', []) if e.get('nombre')}

    def espacio_de(a):
        e = asg.get(str(a['id']), {}).get('espacio') or mat.get(str(a['materia']), {}).get('espacio') or ''
        return e if e in espacios else ''

    def doc_de(a):
        return a.get('docente') or -a['id']        # sin docente: no choca con nadie

    def parte(a):
        return {'curso': a['curso'], 'docente': doc_de(a), 'materia': a['materia'],
                'sede': D.sede_de_curso(a['curso']), 'asig': a['id']}

    def partes_de(a, n):
        regla = mat.get(str(a['materia']), {})
        propia = asg.get(str(a['id']), {})
        partes = patron(propia.get('bloques')) or patron(regla.get('bloques'))
        if partes is None and regla.get('doble'):
            ih = D.ih(a['id'], cond)
            partes = [2] * (ih // 2) + [1] * (ih % 2)
        return ajustar(partes or [1] * n, n) if n else []

    fijas = []
    usadas = defaultdict(int)
    for fx in cond.get('fijas', []):
        a = D.asignaciones.get(int(fx['asignacion']))
        if not a:
            continue
        fijas.append(dict(parte(a), asig=a['id'], dia=int(fx['dia']), franja=int(fx['franja']),
                          extra=bool(asg.get(str(a['id']), {}).get('extra')), espacio=espacio_de(a)))
        usadas[a['id']] += 1
    unidades = []
    max_materia_dia = {}
    restantes = {}
    for a in D.asignaciones.values():
        if a['curso'] in D.jornada_de_curso:
            restantes[a['id']] = max(0, D.ih(a['id'], cond) - usadas[a['id']])
            regla = mat.get(str(a['materia']), {})
            tope = int(regla.get('max_dia') or defecto)
            partes = partes_de(a, D.ih(a['id'], cond))
            max_materia_dia[(a['curso'], a['materia'])] = max(tope, max(partes or [1]))
            if any(x > 1 for x in partes):
                dobles.add(a['materia'])
    # Clases simultáneas: varias asignaciones (de cursos distintos) a la misma hora.
    for g, grupo in enumerate(cond.get('simultaneas', [])):
        miembros = []
        for aid in grupo.get('asignaciones', []):
            a = D.asignaciones.get(int(aid))
            if a and a['id'] in restantes and a['curso'] not in {m['curso'] for m in miembros}:
                miembros.append(a)
        if len(miembros) < 2:
            continue
        n = min(restantes[a['id']] for a in miembros)
        for largo in partes_de(miembros[0], n):
            unidades.append({'id': f'S{g}-{len(unidades)}', 'asig': miembros[0]['id'], 'largo': largo,
                             'extra': all(asg.get(str(a['id']), {}).get('extra') for a in miembros),
                             'dividir': True, 'espacio': espacio_de(miembros[0]),
                             'partes': [parte(a) for a in miembros]})
        for a in miembros:
            restantes[a['id']] -= n
    for a in D.asignaciones.values():
        n = restantes.get(a['id'], 0)
        propia = asg.get(str(a['id']), {})
        for largo in partes_de(a, n):
            u = unidad_simple(f'{a["id"]}-{len(unidades)}', a['id'], a['curso'], doc_de(a), a['materia'], largo,
                              D.sede_de_curso(a['curso']), bool(propia.get('extra')), propia.get('dividir', True),
                              espacio_de(a))
            unidades.append(u)
    no_puede = {}
    prefiere_no = {}
    max_seguidas = {}
    max_docente_dia = {}
    permanencia = {}
    general = float(cond.get('permanencia_horas') or 0)
    seguidas = int(cond.get('max_seguidas') or 0)
    for did in D.docentes:
        if general:
            permanencia[did] = int(general * 60)
        if seguidas:
            max_seguidas[did] = seguidas
    for did, r in cond.get('docentes', {}).items():
        no_puede[int(did)] = {tuple(int(x) for x in k.split('-')) for k in r.get('no_puede', [])}
        prefiere_no[int(did)] = {tuple(int(x) for x in k.split('-')) for k in r.get('prefiere_no', [])}
        if r.get('max_seguidas'):
            max_seguidas[int(did)] = int(r['max_seguidas'])
        if r.get('max_dia'):
            max_docente_dia[int(did)] = int(r['max_dia'])
        if r.get('permanencia') is not None and r.get('permanencia') != '':
            h = float(r['permanencia'])
            if h:
                permanencia[int(did)] = int(h * 60)
            else:
                permanencia.pop(int(did), None)
    reuniones, no_puede = ubicar_reuniones(D, cond, no_puede)
    p = Problema(franjas_clase, siguiente, slots, unidades, fijas=fijas, no_puede=no_puede, prefiere_no=prefiere_no,
                 max_materia_dia=max_materia_dia, max_docente_dia=max_docente_dia, max_seguidas=max_seguidas,
                 primeras=primeras, dobles=dobles, ultimas=ultimas, permanencia=permanencia,
                 desplazamiento=int(cond.get('desplazamiento') or 0), espacios=espacios)
    p.reuniones = reuniones
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
            for q in u['partes']:
                sesiones.append({'asignacion': q['asig'], 'curso': q['curso'], 'dia': dia, 'franja': f})
    sin = defaultdict(int)
    for uid in r['sin_ubicar']:
        u = est.u[uid]
        for q in u['partes']:
            sin[q['asig']] += u['largo']
    huecos = {did: h for did, h in huecos_por_docente(est).items() if did and did > 0}
    return {'sesiones': sesiones, 'costo': r['costo'], 'huecos': sum(huecos.values()),
            'sin_ubicar': [{'asignacion': a, 'horas': h} for a, h in sin.items()],
            'divididas': r.get('divididas', []), 'reuniones': getattr(p, 'reuniones', [])}


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
