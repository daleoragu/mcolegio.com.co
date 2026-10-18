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

from .motor import PESOS, Problema, resolver, unidad_simple

TIPO_DATOS = 'mcolegio-horario-datos'
TIPO_RESULTADO = 'mcolegio-horario-resultado'
VERSION = 1
class _Dias(dict):
    """Nombre de cada día: 1-6 son lunes a sábado; 101, 102… son «Día 1», «Día 2»… de un horario
    por días de ciclo (el que se corre si un día no hubo clase)."""
    def __missing__(self, k):
        try:
            k = int(k)
        except (TypeError, ValueError):
            return str(k)
        return f'Día {k - 100}' if k > 100 else f'Día {k}'

    def get(self, k, defecto=None):
        return self[k]


DIAS = _Dias({1: 'Lunes', 2: 'Martes', 3: 'Miércoles', 4: 'Jueves', 5: 'Viernes', 6: 'Sábado'})


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
            'asignaciones': {},          # {aid: {'extra_horas': n, 'bloques': '2+2', 'dividir': bool}}
            'permanencia_horas': 0,      # 0 = sin control; 6 en los oficiales (Decreto 1850/2002)
            'desplazamiento': 30,        # minutos para cambiar de sede
            'max_seguidas': 0,           # máximo de horas seguidas de un docente (0 = sin límite)
            'reuniones': [],
            'simultaneas': [],           # [{'nombre', 'asignaciones': [aid…]}] van a la misma hora
            'espacios': [],              # [{'nombre', 'capacidad'}] sala de sistemas, laboratorio…
            'pesos': {},                 # {criterio: 0..10} prioridades al optimizar (5 = normal)
            'cursos': {},                # {cid: {'no_puede': ['dia-franja']}} horas sin clase del curso
            'actividades': [],           # [{'nombre', 'docentes': [did] (vacío = todos), 'horas', 'max_dia'}]
            'acompanamiento': {'zonas': [], 'max_semana': 2},   # turnos en los descansos
            # Si el docente tiene la hora «b» no tiene la hora «a» el mismo día (ej.: la 7.ª y la 1.ª)
            'excluyente': {'activa': False, 'a': 1, 'b': 7, 'obligatoria': True},
            # Prioridad a los bloques: las materias de N horas o más van en bloques de 2 horas seguidas
            # (2+2+1…) si la materia no tiene sus propios bloques. Si un bloque no cabe, se parte.
            'bloques_general': {'activa': False, 'desde': 2},
            # ¿Un bloque puede quedar partido por el descanso? None = todavía no se ha preguntado
            'bloque_descanso': None,
            # Multigrado (Escuela Nueva): cursos que ven clase juntos, con el mismo docente y en la misma aula
            'multigrado': [],                 # [{'nombre', 'cursos': [cid…]}]
            # Con horas extra, el día puede alargarse hasta estas horas más de la permanencia (0 = sin límite)
            'permanencia_extra': 2}


def horas_extra(cond, aid, ih):
    """Cuántas de las horas de esa clase son horas extra (0 a ih)."""
    r = (cond or {}).get('asignaciones', {}).get(str(aid), {})
    if r.get('extra_horas') not in (None, ''):
        try:
            return max(0, min(ih, int(r['extra_horas'])))
        except (TypeError, ValueError):
            return 0
    return ih if r.get('extra') else 0


def grupos_multigrado(cond=None, juntos=None):
    """{curso: número de grupo} de los cursos que van juntos (de las condiciones o de un informe)."""
    grupos = list(juntos or []) + [g.get('cursos', []) for g in (cond or {}).get('multigrado', [])]
    out = {}
    for k, cursos in enumerate(grupos):
        for c in cursos or []:
            out[int(c)] = k
    return out


# Los criterios que el coordinador puede subir o bajar (de 0 a 10; 5 = normal).
CRITERIOS = [
    ('hueco', 'Que los docentes no tengan horas sueltas entre clases'),
    ('hueco_curso', 'Que los cursos no tengan horas libres en medio de la jornada'),
    ('repetida', 'No repetir la misma materia el mismo día'),
    ('prefiere_no', 'Respetar las horas «mejor no» de los docentes'),
    ('equilibrio', 'Repartir parejo las clases de cada docente en la semana'),
    ('dia_suelto', 'Evitar que un docente vaya un día solo a dar una clase'),
    ('dia_libre', 'Darle el día libre al docente que lo pidió'),
    ('tarde', 'Poner temprano las materias marcadas «primeras horas»'),
    ('ultima', 'Sacar de la última hora las materias marcadas'),
    ('excluyente', 'Evitar que un docente tenga la primera y la última hora el mismo día (si es preferencia)'),
    ('bloque', 'Que las horas de una materia el mismo día queden seguidas (bloques)'),
    ('dia_largo', 'Que las horas extra queden dentro de la jornada normal (pocos días largos)'),
]


def bloques_por_defecto(cond, ih):
    """[2, 2, 1…] si está activa la prioridad a los bloques y la materia tiene suficientes horas."""
    g = cond.get('bloques_general') or {}
    if not g.get('activa'):
        return None
    try:
        desde = max(2, int(g.get('desde') or 2))
    except (TypeError, ValueError):
        desde = 2
    if ih < desde:
        return None
    return [2] * (ih // 2) + [1] * (ih % 2)


def regla_excluyente(cond):
    """(hora_a, hora_b, obligatoria) o None si la regla está apagada."""
    r = cond.get('excluyente') or {}
    if not r.get('activa'):
        return None
    try:
        a, b = int(r.get('a') or 1), int(r.get('b') or 7)
    except (TypeError, ValueError):
        return None
    if a == b or a < 1 or b < 1:
        return None
    return a, b, bool(r.get('obligatoria', True))


def pesos_de(cond):
    """Los pesos del motor según las prioridades (0 a 10) que puso el coordinador."""
    w = {}
    for clave, valor in (cond.get('pesos') or {}).items():
        try:
            f = max(0.0, min(10.0, float(valor))) / 5.0
        except (TypeError, ValueError):
            continue
        if clave in PESOS:
            w[clave] = PESOS[clave] * f
        if clave == 'prefiere_no':
            w['evitar'] = PESOS['evitar'] * f
    return w


def celdas(lista):
    """['1-5', '2-7'] -> {(1, 5), (2, 7)}."""
    out = set()
    for k in lista or []:
        try:
            d, f = str(k).split('-')
            out.add((int(d), int(f)))
        except ValueError:
            pass
    return out


def patron(texto):
    """'2+2+1' -> [2, 2, 1]; None si no se entiende."""
    try:
        partes = [int(x) for x in str(texto or '').replace(' ', '').split('+') if x]
    except ValueError:
        return None
    return partes if partes and all(1 <= x <= 4 for x in partes) else None


def siguientes(datos, cruzar_descanso=False):
    """{franja: la franja de clase que sigue sin descanso en medio}.

    Con cruzar_descanso=True, la hora de antes del descanso y la de después también cuentan
    como seguidas (para los colegios que aceptan bloques partidos por el descanso)."""
    sig = {}
    for jid in datos.jornadas:
        lst = datos.franjas_de(jid)
        if cruzar_descanso:
            clase = [f for f in lst if not f['descanso']]
            for a, b in zip(clase, clase[1:]):
                sig[a['id']] = b['id']
        else:
            for a, b in zip(lst, lst[1:]):
                if not a['descanso'] and not b['descanso']:
                    sig[a['id']] = b['id']
    return sig


def bloque_cruza_descanso(cond):
    return cond.get('bloque_descanso') is True


def corridas(posiciones, sig):
    """[(dia, franja)…] de una misma clase -> largos de los tramos seguidos ([2, 1]…)."""
    por_dia = defaultdict(set)
    for d, f in posiciones:
        por_dia[d].add(f)
    out = []
    ant = {b: a for a, b in sig.items()}
    for fs in por_dia.values():
        for f in fs:
            if ant.get(f) in fs:
                continue
            n, x = 0, f
            while x in fs:
                n += 1
                x = sig.get(x)
            out.append(n)
    return out


def restar_corridas(partes, ya):
    """Quita del patrón de bloques lo que ya está puesto, sin importar el orden.

    Ej.: patrón 2+1 y ya hay una hora suelta -> falta el bloque de 2; ya hay un bloque de 2 ->
    falta la hora suelta. Si lo puesto no coincide con ningún bloque, se descuenta de uno más
    grande (que queda más corto)."""
    quedan = sorted(partes, reverse=True)
    for largo in sorted(ya, reverse=True):
        while largo > 0 and quedan:
            if largo in quedan:
                quedan.remove(largo)
                largo = 0
            else:
                mayores = [p for p in quedan if p > largo]
                if mayores:
                    p = min(mayores)
                    quedan.remove(p)
                    quedan.append(p - largo)
                    largo = 0
                else:
                    p = max(quedan)
                    quedan.remove(p)
                    largo -= p
    return sorted(quedan, reverse=True)


def partes_completas(datos, cond, a):
    """El patrón de bloques de una clase para toda su intensidad (sin contar lo ya puesto)."""
    mat = cond.get('materias', {})
    asg = cond.get('asignaciones', {})
    ih = datos.ih(a['id'], cond)
    regla = mat.get(str(a['materia']), {})
    propia = asg.get(str(a['id']), {})
    partes = patron(propia.get('bloques')) or patron(regla.get('bloques'))
    if partes is None and regla.get('doble'):
        partes = [2] * (ih // 2) + [1] * (ih % 2)
    if partes is None:
        partes = bloques_por_defecto(cond, ih)
    return ajustar(partes or [1] * ih, ih) if ih else []


def bloques_automaticos(ih):
    """'2+2+1' para 5 horas, '2+1' para 3, '2' para 2; '' para 1 hora."""
    if ih < 2:
        return ''
    return '+'.join(str(x) for x in [2] * (ih // 2) + [1] * (ih % 2))


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
    grupo = grupos_multigrado(cond)
    juntas = defaultdict(int)          # multigrado: la clase del grupo cuenta una sola vez al docente
    for a in D.asignaciones.values():
        n = D.ih(a['id'], cond)
        por_curso[a['curso']] += n
        if a.get('docente'):
            if a['curso'] in grupo:
                k = (a['docente'], grupo[a['curso']], a['materia'])
                if n > juntas[k]:
                    por_docente[a['docente']] += n - juntas[k]
                    juntas[k] = n
            else:
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
        cupo -= len(cond.get('cursos', {}).get(str(cid), {}).get('no_puede', []))
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
    salida += _diagnostico_mas(D, cond, por_docente)
    return salida


def _seguidas_max(datos, jid):
    """Cuántas horas de clase seguidas (sin descanso) caben como máximo en la jornada."""
    mejor = n = 0
    for f in datos.franjas_de(jid):
        n = 0 if f['descanso'] else n + 1
        mejor = max(mejor, n)
    return mejor


def _diagnostico_mas(D, cond, por_docente):
    """Revisiones al estilo de GHC: errores que impiden, avisos que dificultan e información."""
    salida = []
    mat, asg = cond.get('materias', {}), cond.get('asignaciones', {})
    # Bloques más largos que las horas seguidas que hay
    for a in D.asignaciones.values():
        jid = D.jornada_de_curso.get(a['curso'])
        if jid is None:
            continue
        partes = patron(asg.get(str(a['id']), {}).get('bloques')) or patron(mat.get(str(a['materia']), {}).get('bloques')) or []
        tope = _seguidas_max(D, jid)
        if partes and max(partes) > tope:
            salida.append(('aviso', f'{D.nombre_materia(a["materia"])} en {D.nombre_curso(a["curso"])}: un bloque de '
                                    f'{max(partes)} horas no cabe (hay máximo {tope} seguidas); se partirá.'))
    # Clases simultáneas con el mismo docente
    for g in cond.get('simultaneas', []):
        docs = [D.asignaciones[int(x)].get('docente') for x in g.get('asignaciones', []) if int(x) in D.asignaciones]
        docs = [d for d in docs if d]
        if len(docs) != len(set(docs)):
            salida.append(('error', f'«{g.get("nombre")}»: un mismo docente no puede estar en dos clases simultáneas.'))
    # Espacios compartidos con más horas de las que caben
    espacios = {e['nombre']: max(1, int(e.get('capacidad') or 1)) for e in cond.get('espacios', []) if e.get('nombre')}
    uso, cupo_esp = defaultdict(int), defaultdict(int)
    for a in D.asignaciones.values():
        e = asg.get(str(a['id']), {}).get('espacio') or mat.get(str(a['materia']), {}).get('espacio')
        jid = D.jornada_de_curso.get(a['curso'])
        if e in espacios and jid is not None:
            uso[e] += D.ih(a['id'], cond)
    for e, cap in espacios.items():
        horas = max((len([f for f in j['franjas'] if not f['descanso']]) * len(j['dias']) for j in D.jornadas.values()),
                    default=0)
        if uso[e] > cap * horas:
            salida.append(('error', f'{e}: se necesitan {uso[e]} horas y solo caben {cap * horas} en la semana.'))
        elif uso[e] > cap * horas * 0.85:
            salida.append(('aviso', f'{e} queda casi lleno ({uso[e]} de {cap * horas} horas): puede costar ubicarlo.'))
    # Demasiadas prohibiciones (GHC: mejor usar «mejor no»)
    nps = {}
    for did, horas in por_docente.items():
        cupo = sum(len([f for f in D.jornadas[j]['franjas'] if not f['descanso']]) * len(D.jornadas[j]['dias'])
                   for j in D.jornadas_de_docente(did))
        np_ = len(cond.get('docentes', {}).get(str(did), {}).get('no_puede', []))
        nps[did] = np_
        libres = cupo - np_
        if cupo and horas <= libres and horas > 0.9 * libres and np_:
            salida.append(('aviso', f'{D.nombre_docente(did)} tiene casi todas sus horas libres ocupadas '
                                    f'({horas} clases en {libres} espacios). Cambie algunos «no puede» por «mejor no».'))
    con = [d for d, n in nps.items() if n]
    if con and len(con) < len(nps):
        salida.append(('info', f'{len(con)} docente(s) tienen horas en «no puede». Para que el horario sea parejo, '
                               'ofrezca a todos la misma posibilidad de pedir horas.'))
    # Regla «si tiene la 7.ª no tiene la 1.ª»: cada día, los docentes de la primera hora y los de
    # la última tienen que ser distintos; si no alcanzan, no hay cómo.
    regla = regla_excluyente(cond)
    if regla and regla[2]:
        for jid, j in D.jornadas.items():
            cursos = len(j.get('cursos') or [])
            docs = {x['docente'] for x in D.asignaciones.values()
                    if x.get('docente') and D.jornada_de_curso.get(x['curso']) == jid}
            if cursos and len(docs) < 2 * cursos:
                salida.append(('aviso', f'{j["nombre"]}: con la regla de la hora {regla[1]} y la hora {regla[0]} '
                                        f'obligatoria hacen falta al menos {2 * cursos} docentes para cubrir la primera y la '
                                        f'última hora de los {cursos} cursos (hay {len(docs)}). Algunos cursos tendrían que '
                                        'salir antes, o póngala como «Si se puede».'))
    # Actividades y acompañamientos
    for act in cond.get('actividades', []):
        if not act.get('horas'):
            salida.append(('info', f'La actividad «{act.get("nombre")}» no tiene horas: no se ubicará.'))
    zonas = cond.get('acompanamiento', {}).get('zonas', [])
    if zonas and not any(f['descanso'] for f in D.franjas.values()):
        salida.append(('aviso', 'Hay zonas de acompañamiento pero las jornadas no tienen descansos.'))
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


def franjas_de_reuniones(datos, reuniones):
    """{(docente, dia): [franja…]}: las horas de clase que ocupa cada reunión a cada asistente."""
    out = defaultdict(list)
    for r in reuniones or []:
        for reu in (r, r.get('segunda') or {}):
            if not reu.get('dia'):
                continue
            for did in reu.get('asisten', []):
                for jid in datos.jornadas_de_docente(did):
                    if reu['dia'] not in datos.jornadas[jid]['dias']:
                        continue
                    for f in datos.franjas_de(jid):
                        if not f['descanso'] and minutos(f['inicio']) < reu['fin'] and reu['inicio'] < minutos(f['fin']):
                            if f['id'] not in out[(did, reu['dia'])]:
                                out[(did, reu['dia'])].append(f['id'])
    return dict(out)


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
        sin = celdas(cond.get('cursos', {}).get(str(cid), {}).get('no_puede'))
        slots[cid] = [(d, f['id']) for d in j['dias'] for f in D.franjas_de(jid) if not f['descanso'] and (d, f['id']) not in sin]
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
        # Sin docente: un número propio (negativo y que no se repite) para que no choque con nadie.
        return a.get('docente') or -(10 ** 9 + abs(a['id']))

    def parte(a):
        return {'curso': a['curso'], 'docente': doc_de(a), 'materia': a['materia'],
                'sede': D.sede_de_curso(a['curso']), 'asig': a['id']}

    sig_bloque = siguientes(D, bloque_cruza_descanso(cond))
    fijas = []
    usadas = defaultdict(int)
    puestas = defaultdict(list)
    for fx in cond.get('fijas', []):
        a = D.asignaciones.get(int(fx['asignacion']))
        if not a:
            continue
        fijas.append(dict(parte(a), asig=a['id'], dia=int(fx['dia']), franja=int(fx['franja']),
                          extra=horas_extra(cond, a['id'], D.ih(a['id'], cond)) >= D.ih(a['id'], cond) > 0,
                          espacio=espacio_de(a)))
        usadas[a['id']] += 1
        puestas[a['id']].append((int(fx['dia']), int(fx['franja'])))

    def partes_de(a, n):
        """Los bloques que faltan por ubicar. El orden no importa: si ya está puesta la hora suelta
        falta el bloque, y si ya está el bloque falta la hora suelta."""
        if not n:
            return []
        completas = partes_completas(D, cond, a)
        faltan = restar_corridas(completas, corridas(puestas.get(a['id'], []), sig_bloque))
        return ajustar(faltan or [1] * n, n)
    unidades = []
    max_materia_dia = {}
    restantes = {}
    for a in D.asignaciones.values():
        if a['curso'] in D.jornada_de_curso:
            restantes[a['id']] = max(0, D.ih(a['id'], cond) - usadas[a['id']])
            regla = mat.get(str(a['materia']), {})
            tope = int(regla.get('max_dia') or defecto)
            partes = partes_completas(D, cond, a)
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
                             'extra': all(horas_extra(cond, a['id'], D.ih(a['id'], cond)) >= D.ih(a['id'], cond) > 0
                                          for a in miembros),
                             'dividir': True, 'espacio': espacio_de(miembros[0]),
                             'partes': [parte(a) for a in miembros]})
        for a in miembros:
            restantes[a['id']] -= n
    # Multigrado (Escuela Nueva): en un grupo de cursos, la misma materia con el mismo docente se da
    # a todos a la vez, en la misma aula. Va como una clase con varias partes (una por curso).
    for g, grupo in enumerate(cond.get('multigrado', [])):
        cursos = {int(c) for c in grupo.get('cursos', [])}
        por = defaultdict(list)
        for a in D.asignaciones.values():
            if a['curso'] in cursos and a.get('docente') and restantes.get(a['id'], 0) > 0:
                por[(a['docente'], a['materia'])].append(a)
        for (_doc, _mat), miembros in por.items():
            if len(miembros) < 2:
                continue
            n = min(restantes[a['id']] for a in miembros)
            for largo in partes_de(miembros[0], n):
                unidades.append({'id': f'M{g}-{len(unidades)}', 'asig': miembros[0]['id'], 'largo': largo,
                                 'extra': all(horas_extra(cond, a['id'], D.ih(a['id'], cond)) >= D.ih(a['id'], cond) > 0
                                              for a in miembros),
                                 'dividir': True, 'espacio': espacio_de(miembros[0]),
                                 'partes': [parte(a) for a in miembros]})
            for a in miembros:
                restantes[a['id']] -= n
    for a in D.asignaciones.values():
        n = restantes.get(a['id'], 0)
        propia = asg.get(str(a['id']), {})
        mias = []
        for largo in partes_de(a, n):
            u = unidad_simple(f'{a["id"]}-{len(unidades)}', a['id'], a['curso'], doc_de(a), a['materia'], largo,
                              D.sede_de_curso(a['curso']), False, propia.get('dividir', True), espacio_de(a))
            unidades.append(u)
            mias.append(u)
        # Las horas extra escogidas: se marcan primero las clases más cortas
        k = horas_extra(cond, a['id'], D.ih(a['id'], cond))
        for u in sorted(mias, key=lambda u: u['largo']):
            if k <= 0:
                break
            u['extra'] = True
            k -= u['largo']
    no_puede = {}
    prefiere_no = {}
    evitar = {}
    dia_libre = set()
    sin_excluyente = set()
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
        evitar[int(did)] = celdas(r.get('evitar'))
        if r.get('dia_libre'):
            dia_libre.add(int(did))
        if r.get('sin_excluyente'):
            sin_excluyente.add(int(did))
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
    # Con horas extra el día puede ser más largo, hasta un tope (las extra no cuentan en la permanencia)
    permanencia_extra = {}
    general_extra = float(cond.get('permanencia_extra') or 0)
    con_extra = {a.get('docente') for a in D.asignaciones.values()
                 if a.get('docente') and horas_extra(cond, a['id'], D.ih(a['id'], cond))}
    dias_largos_max = {}
    for did in con_extra:
        r = cond.get('docentes', {}).get(str(did), {})
        h = r.get('permanencia_extra')
        h = float(h) if h not in (None, '') else general_extra
        if h and did in permanencia:
            permanencia_extra[did] = int(h * 60)
        # Un día largo (pasa de la permanencia o tiene la 1.ª y la última) por cada hora extra
        dias_largos_max[did] = sum(horas_extra(cond, a['id'], D.ih(a['id'], cond))
                                   for a in D.asignaciones.values() if a.get('docente') == did)
    reuniones, no_puede = ubicar_reuniones(D, cond, no_puede)
    reuniones_doc = franjas_de_reuniones(D, reuniones)
    dias_docente = {did: {d for jid in D.jornadas_de_docente(did) for d in D.jornadas[jid]['dias']} for did in dia_libre}
    # Para el día libre se escoge un día por docente (el que ya tiene más horas en «no puede»,
    # o el que tenga menos clases fijadas; se rotan para no dejar a todos libres el mismo día) y
    # sus horas se vuelven «mejor no» fuerte: así el generador lo va vaciando poco a poco.
    for k, did in enumerate(sorted(dia_libre)):
        dias = sorted(dias_docente.get(did) or [])
        if len(dias) < 2:
            continue
        fijadas = defaultdict(int)
        for fx in fijas:
            if fx['docente'] == did:
                fijadas[fx['dia']] += 1
        bloqueadas = defaultdict(int)
        for (d, _) in no_puede.get(did, ()):
            bloqueadas[d] += 1
        rot = {d: (i - k) % len(dias) for i, d in enumerate(dias)}
        dia = min(dias, key=lambda d: (fijadas[d], -bloqueadas[d], rot[d]))
        evitar.setdefault(did, set()).update(
            (dia, f['id']) for jid in D.jornadas_de_docente(did) for f in D.franjas_de(jid) if not f['descanso'])
    p = Problema(franjas_clase, siguiente, slots, unidades, fijas=fijas, no_puede=no_puede, prefiere_no=prefiere_no,
                 max_materia_dia=max_materia_dia, max_docente_dia=max_docente_dia, max_seguidas=max_seguidas,
                 primeras=primeras, dobles=dobles, ultimas=ultimas, permanencia=permanencia,
                 desplazamiento=int(cond.get('desplazamiento') or 0), espacios=espacios, pesos=pesos_de(cond),
                 evitar=evitar, dia_libre=dia_libre, dias_docente=dias_docente,
                 excluyentes=[regla_excluyente(cond)[:2]] if regla_excluyente(cond) else [],
                 excluyente_duro=bool(regla_excluyente(cond) and regla_excluyente(cond)[2]),
                 sin_excluyente=sin_excluyente, reuniones_doc=reuniones_doc, siguiente_bloque=sig_bloque,
                 permanencia_extra=permanencia_extra, dias_largos_max=dias_largos_max)
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
    # Lo que más costó ubicar (como las «sesiones con más rechazos» de GHC): sirve para
    # encontrar la condición que traba el horario.
    rech = defaultdict(int)
    for uid, n in est.rechazos.items():
        u = est.u.get(uid)
        if u and uid not in est.fijas:
            for q in u['partes']:
                rech[q['asig']] += n
    dificiles = [{'asignacion': a, 'rechazos': n} for a, n in sorted(rech.items(), key=lambda x: -x[1])[:10] if n >= 3]
    return {'sesiones': sesiones, 'costo': r['costo'], 'huecos': sum(huecos.values()),
            'sin_ubicar': [{'asignacion': a, 'horas': h} for a, h in sin.items()],
            'divididas': r.get('divididas', []), 'reuniones': getattr(p, 'reuniones', []), 'dificiles': dificiles}


# ---------------------------------------------------------------------------
# Después de ubicar las clases: actividades complementarias y descansos
# ---------------------------------------------------------------------------
def _ocupado(datos, sesiones, reuniones=()):
    """{(docente, dia): [(ini, fin)]} de clases y reuniones."""
    oc = defaultdict(list)
    for s in sesiones:
        a = datos.asignaciones.get(s['asignacion'])
        if a and a.get('docente') and s['franja'] in datos.franjas:
            oc[(a['docente'], s['dia'])].append(datos.intervalo(s['franja']))
    for r in reuniones or []:
        for reu in (r, r.get('segunda') or {}):
            for did in reu.get('asisten', []):
                oc[(did, reu['dia'])].append((reu['inicio'], reu['fin']))
    return oc


def ubicar_actividades(datos, cond, sesiones, reuniones=()):
    """Ubica las horas de actividades complementarias (atención a padres, planeación…).

    Primero en los huecos del docente, luego pegadas a sus clases y dentro de su
    permanencia; nunca en horas que no puede. Devuelve (lista, avisos).
    """
    D = datos
    oc = _ocupado(D, sesiones, reuniones)
    con_clase = {a.get('docente') for a in D.asignaciones.values() if a.get('docente')}
    general = float(cond.get('permanencia_horas') or 0)
    salida, avisos = [], []
    for act in cond.get('actividades', []):
        horas = int(act.get('horas') or 0)
        if horas <= 0:
            continue
        max_dia = int(act.get('max_dia') or 1)
        quienes = [int(x) for x in act.get('docentes') or []] or sorted(con_clase)
        for did in quienes:
            if did not in D.docentes:
                continue
            r = cond.get('docentes', {}).get(str(did), {})
            no = celdas(r.get('no_puede'))
            mejor_no = celdas(r.get('prefiere_no')) | celdas(r.get('evitar'))
            perm = r.get('permanencia')
            perm = float(perm) if perm not in (None, '') else general
            puestas = defaultdict(int)
            for _ in range(horas):
                elegido, puntos = None, None
                for jid in D.jornadas_de_docente(did):
                    j = D.jornadas[jid]
                    for dia in j['dias']:
                        if puestas[dia] >= max_dia:
                            continue
                        tramos = oc.get((did, dia), [])
                        for f in D.franjas_de(jid):
                            if f['descanso'] or (dia, f['id']) in no:
                                continue
                            ini, fin = minutos(f['inicio']), minutos(f['fin'])
                            if any(a < fin and ini < b for a, b in tramos):
                                continue
                            if tramos:
                                lo, hi = min(a for a, _ in tramos), max(b for _, b in tramos)
                                if lo < ini and fin < hi:
                                    pts = 0                      # hueco entre clases
                                elif any(b == ini or a == fin for a, b in tramos) or abs(ini - hi) <= 30 or abs(lo - fin) <= 30:
                                    pts = 1                      # pegada a una clase
                                else:
                                    pts = 3
                                if perm and max(hi, fin) - min(lo, ini) > perm * 60:
                                    continue
                            else:
                                pts = 8                          # un día en que no tiene clases
                            if (dia, f['id']) in mejor_no:
                                pts += 4
                            pts += puestas[dia] * 0.5 + f['orden'] * 0.01
                            if puntos is None or pts < puntos:
                                elegido, puntos = (dia, f, ini, fin), pts
                if elegido is None:
                    avisos.append(f'{act.get("nombre")}: no hubo espacio para una hora de {D.nombre_docente(did)}.')
                    break
                dia, f, ini, fin = elegido
                oc[(did, dia)].append((ini, fin))
                puestas[dia] += 1
                salida.append({'nombre': act.get('nombre') or 'Actividad', 'docente': did, 'dia': dia, 'franja': f['id']})
    return salida, avisos


def asignar_acompanamientos(datos, cond, sesiones):
    """Reparte los turnos de acompañamiento de los descansos (patio, tienda, baños…).

    Toma docentes que ese día tienen clase justo antes o justo después del descanso
    (ya están en el colegio), reparte parejo y respeta el máximo de turnos a la
    semana. Devuelve (turnos, avisos); cada turno: {'dia', 'franja', 'zona', 'docentes'}.
    """
    D = datos
    ac = cond.get('acompanamiento') or {}
    zonas = [z for z in ac.get('zonas', []) if z.get('nombre') and int(z.get('cuantos') or 0) > 0]
    if not zonas:
        return [], []
    tope = int(ac.get('max_semana') or 0) or 99
    oc = _ocupado(D, sesiones)
    carga = defaultdict(int)
    turnos, avisos = [], []
    excluidos = {int(x) for x in ac.get('excluir', [])}
    for jid in sorted(D.jornadas):
        j = D.jornadas[jid]
        if not j.get('cursos'):
            continue
        lst = D.franjas_de(jid)
        for dia in j['dias']:
            for k, f in enumerate(lst):
                if not f['descanso']:
                    continue
                ini, fin = minutos(f['inicio']), minutos(f['fin'])
                antes = {did for (did, d), tr in oc.items() if d == dia and any(b == ini for _, b in tr)}
                despues = {did for (did, d), tr in oc.items() if d == dia and any(a == fin for a, _ in tr)}
                dia_con = {did for (did, d), tr in oc.items() if d == dia and tr and
                           min(a for a, _ in tr) < ini and max(b for _, b in tr) > fin}
                candidatos = (antes | despues | dia_con) - excluidos
                usados = set()
                for z in zonas:
                    n = int(z['cuantos'])
                    orden = sorted(candidatos - usados, key=lambda did: (
                        carga[did], 0 if did in antes and did in despues else (1 if did in antes or did in despues else 2),
                        D.nombre_docente(did)))
                    elegidos = [did for did in orden if carga[did] < tope][:n]
                    for did in elegidos:
                        carga[did] += 1
                        usados.add(did)
                    turnos.append({'dia': dia, 'franja': f['id'], 'zona': z['nombre'], 'docentes': elegidos})
                    if len(elegidos) < n:
                        avisos.append(f'{DIAS[dia]} {f["inicio"]} · {z["nombre"]}: faltan {n - len(elegidos)} docente(s).')
    return turnos, avisos


# ---------------------------------------------------------------------------
# Revisión de choques (la usan la app y la plataforma al importar)
# ---------------------------------------------------------------------------
def revisar(datos, sesiones, cond=None, juntos=None):
    """[texto] con cada choque o incumplimiento.

    juntos: grupos multigrado ([[curso…]…]); en ellos el mismo docente puede estar con varios cursos
    a la misma hora (es la misma clase)."""
    D = datos
    grupo = grupos_multigrado(cond, juntos)
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
                oc = D.asignaciones[otro]['curso']
                if (a['curso'] in grupo and grupo.get(oc) == grupo[a['curso']] and (x, y) == (ini, fin)
                        and D.asignaciones[otro]['materia'] == a['materia']):
                    continue                     # multigrado: es la misma clase con varios cursos
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
