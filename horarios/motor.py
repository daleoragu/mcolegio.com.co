"""Generador de horarios (Python puro, sin dependencias).

Recibe el problema ya armado (ver nucleo.armar) y devuelve dónde va cada clase.

Cómo trabaja:
1. Construcción con «expulsión»: ubica primero lo más difícil (clases
   simultáneas, bloques largos, docentes con poca disponibilidad). Si una clase
   no cabe, se ubica donde menos estorbe y saca a las que chocan, que vuelven a
   la cola (la idea de los generadores conocidos, como FET).
2. Si un bloque no cupo y se permite, se parte en horas sueltas y se intenta
   otra vez (queda en el informe).
3. Mejora: mueve e intercambia clases para quitar horas sueltas de docentes y
   cursos, repartir las materias y respetar las preferencias. Nunca rompe una
   condición obligatoria.

Una «unidad» es una clase (de 1 a 4 horas seguidas). Normalmente tiene una
sola parte (un curso con su docente); las clases simultáneas tienen varias
partes que van a la misma hora (inglés por niveles, media técnica…).

Obligatorias: un curso no tiene dos clases a la vez; un docente no está en dos
lugares a la vez (por hora real); la intensidad horaria; las horas en que el
docente no puede; las clases fijadas; el máximo por día de cada materia y de
cada docente; el máximo de horas seguidas del docente; los bloques van
seguidos, sin descanso en medio; la permanencia diaria (sin contar horas
extra); el tiempo para cambiar de sede; la capacidad de los espacios
compartidos (sala de sistemas, laboratorio, cancha…).
"""
import math
import random
import time
from collections import defaultdict

PESO_HUECO = 3.0          # hora suelta de un docente entre dos clases
PESO_HUECO_CURSO = 4.0    # hora libre de un curso que no está al final del día
PESO_REPETIDA = 2.0       # la misma materia dos veces el mismo día (sin ser bloque)
PESO_TARDE = 0.4          # materias que prefieren las primeras horas
PESO_ULTIMA = 1.5         # materias que mejor no van en la última hora
PESO_PREFIERE_NO = 2.5    # hora en que el docente prefiere no tener clase
PESO_EVITAR = 7.5         # hora que el docente pide evitar con fuerza («mejor no +»)
PESO_DIA_SUELTO = 1.0     # docente que va un día solo a dar una clase
PESO_EQUILIBRIO = 0.3     # repartir parejo las clases del docente en la semana
PESO_DIA_LIBRE = 6.0      # el docente pidió tener un día sin clases
PESO_EXCLUYENTE = 8.0     # el docente tiene el mismo día las dos horas que no deben juntarse (1.ª y 7.ª)
PESO_BLOQUE = 3.0         # horas de la misma materia el mismo día que no quedaron seguidas (bloque roto)

# Los «criterios ponderables» (como en GHC): el coordinador mueve cada uno de 0 a
# 10 y el 5 es lo normal. Aquí quedan los pesos ya multiplicados.
PESOS = {'hueco': PESO_HUECO, 'hueco_curso': PESO_HUECO_CURSO, 'repetida': PESO_REPETIDA, 'tarde': PESO_TARDE,
         'ultima': PESO_ULTIMA, 'prefiere_no': PESO_PREFIERE_NO, 'evitar': PESO_EVITAR, 'dia_suelto': PESO_DIA_SUELTO,
         'equilibrio': PESO_EQUILIBRIO, 'dia_libre': PESO_DIA_LIBRE, 'excluyente': PESO_EXCLUYENTE,
         'bloque': PESO_BLOQUE}


class Problema:
    """Datos del horario (todo con ids y números, sin Django).

    franjas:   {franja_id: (jornada_id, orden, inicio_min, fin_min)}  (solo horas de clase)
    siguiente: {franja_id: franja_id de la clase que sigue sin descanso en medio}
    slots:     {curso_id: [(dia, franja_id), …]}
    unidades:  [{'id', 'asig', 'partes': [{'curso','docente','materia','sede','asig'}], 'largo', 'extra',
                 'dividir', 'espacio'}]
    fijas:     [{'asig', 'curso', 'docente', 'materia', 'dia', 'franja', 'sede', 'extra', 'espacio'}]
    """

    def __init__(self, franjas, siguiente, slots, unidades, fijas=(), no_puede=None, prefiere_no=None,
                 max_materia_dia=None, max_docente_dia=None, max_seguidas=None, primeras=None, dobles=None,
                 ultimas=None, permanencia=None, desplazamiento=0, espacios=None, pesos=None, evitar=None,
                 dia_libre=None, dias_docente=None, excluyentes=None, excluyente_duro=True, sin_excluyente=None,
                 reuniones_doc=None, siguiente_bloque=None):
        self.franjas = franjas
        self.siguiente = siguiente
        self.anterior = {b: a for a, b in siguiente.items()}
        # Para armar bloques: igual a `siguiente`, o saltando el descanso si el colegio lo permite
        self.siguiente_bloque = siguiente_bloque if siguiente_bloque is not None else siguiente
        self.anterior_bloque = {b: a for a, b in self.siguiente_bloque.items()}
        self.slots = slots
        self.unidades = list(unidades)
        self.fijas = list(fijas)
        self.no_puede = no_puede or {}
        self.prefiere_no = prefiere_no or {}
        self.max_materia_dia = max_materia_dia or {}
        self.max_docente_dia = max_docente_dia or {}
        self.max_seguidas = max_seguidas or {}
        self.primeras = primeras or set()
        self.ultimas = ultimas or set()
        self.dobles = dobles or set()
        self.permanencia = permanencia or {}
        self.desplazamiento = desplazamiento or 0
        self.espacios = espacios or {}               # {espacio: capacidad}
        self.w = dict(PESOS, **(pesos or {}))
        self.evitar = evitar or {}                   # {docente: {(dia, franja)}} «mejor no» fuerte
        self.dia_libre = set(dia_libre or ())        # docentes que piden un día sin clases
        self.dias_docente = dias_docente or {}       # {docente: {días en que podría tener clase}}
        # Horas que un docente no puede tener el mismo día: [(hora_a, hora_b)] con números de
        # hora de clase desde 1 (si la jornada tiene menos horas, se toma la última).
        self.excluyentes = list(excluyentes or [])
        self.excluyente_duro = excluyente_duro
        self.sin_excluyente = set(sin_excluyente or ())
        # Reuniones de área ya ubicadas: {(docente, dia): [franja…]}. Cuentan dentro de la
        # permanencia y para la regla de la 1.ª y la 7.ª hora, como si fueran una clase fija.
        self.reuniones_doc = reuniones_doc or {}
        self.por_jornada = defaultdict(list)
        for fid, (jid, orden, ini, fin) in franjas.items():
            self.por_jornada[jid].append((orden, fid))
        self.indice, self.ultimo = {}, {}
        for jid, lst in self.por_jornada.items():
            lst.sort()
            for i, (_, fid) in enumerate(lst):
                self.indice[fid] = i
            self.ultimo[jid] = len(lst) - 1


def unidad_simple(uid, asig, curso, docente, materia, largo=1, sede='', extra=False, dividir=True, espacio=''):
    return {'id': uid, 'asig': asig, 'largo': largo, 'extra': extra, 'dividir': dividir, 'espacio': espacio,
            'partes': [{'curso': curso, 'docente': docente, 'materia': materia, 'sede': sede, 'asig': asig}]}


class Estado:
    def __init__(self, p):
        self.p = p
        self.curso = {}                         # (curso, dia, franja) -> uid
        self.docente = defaultdict(list)        # (docente, dia) -> [(ini, fin, uid, franja)]
        self.espacio = defaultdict(list)        # (espacio, dia) -> [(ini, fin, uid)]
        self.cm = defaultdict(int)              # (curso, materia, dia) -> horas
        self.dd = defaultdict(int)              # (docente, dia) -> horas
        self.cd = defaultdict(set)              # (curso, dia) -> {franjas}
        self.cmf = defaultdict(list)            # (curso, materia, dia) -> [franjas]
        self.pos = {}
        self.u = {}
        self.fijas = set()
        self.w = p.w
        self.rechazos = defaultdict(int)        # uid -> veces que no cupo o la sacaron (dificultad)
        for (doc, dia), fs in p.reuniones_doc.items():
            for k, f in enumerate(fs):
                if f not in p.franjas:
                    continue
                uid = f'R{doc}-{dia}-{k}'
                self.u[uid] = {'id': uid, 'asig': None, 'largo': 1, 'extra': False, 'reunion': True,
                               'partes': [{'curso': None, 'docente': doc, 'materia': None, 'sede': '', 'asig': None}]}
                self.fijas.add(uid)
                _, _, ini, fin = p.franjas[f]
                self.docente[(doc, dia)].append((ini, fin, uid, f))

    def celdas(self, u, dia, franja):
        out = [franja]
        for _ in range(u['largo'] - 1):
            sig = self.p.siguiente_bloque.get(out[-1])
            if not sig:
                return None
            out.append(sig)
        return out

    def choques(self, u, dia, franja, ignorar=()):
        """(cabe, [uids que estorban]). cabe=False si hay algo que no se puede quitar."""
        p = self.p
        celdas = self.celdas(u, dia, franja)
        if not celdas:
            return False, []
        ign = set(ignorar) | {u['id']}
        estorban = set()

        def estorba(uid):
            if uid in self.fijas:
                return False
            estorban.add(uid)
            return True

        tramos = [(p.franjas[f][2], p.franjas[f][3], f) for f in celdas]
        ini_u, fin_u = tramos[0][0], tramos[-1][1]
        for parte in u['partes']:
            doc = parte['docente']
            no_puede = p.no_puede.get(doc, ())
            for (ini, fin, f) in tramos:
                if (dia, f) in no_puede:
                    return False, []
                otro = self.curso.get((parte['curso'], dia, f))
                if otro is not None and otro not in ign and not estorba(otro):
                    return False, []
                for (a, b, uid, _) in self.docente[(doc, dia)]:
                    if uid not in ign and a < fin and ini < b and not estorba(uid):
                        return False, []
            # Cambio de sede
            if p.desplazamiento and parte.get('sede'):
                for (a, b, uid, _) in self.docente[(doc, dia)]:
                    if uid in ign or uid in estorban:
                        continue
                    sede = self._sede(uid, doc)
                    if sede and sede != parte['sede']:
                        hueco = ini_u - b if b <= ini_u else a - fin_u
                        if hueco < p.desplazamiento and not estorba(uid):
                            return False, []
            # Permanencia (las horas extra no cuentan)
            perm = p.permanencia.get(doc)
            if perm and not u.get('extra'):
                lst = [(a, b) for (a, b, uid, _) in self.docente[(doc, dia)]
                       if uid not in ign and uid not in estorban and not self.u[uid].get('extra')] + [(ini_u, fin_u)]
                if max(b for _, b in lst) - min(a for a, _ in lst) > perm:
                    return False, []
            # Horas que no van el mismo día (si tiene la 7.ª no tiene la 1.ª)
            if p.excluyentes and p.excluyente_duro and doc not in p.sin_excluyente:
                for (a, b, uid, f) in self.docente[(doc, dia)]:
                    if uid in ign or uid in estorban:
                        continue
                    if any(_excluye(p, x, f) for x in celdas) and not estorba(uid):
                        return False, []
            # Máximo de horas seguidas
            tope = p.max_seguidas.get(doc)
            if tope:
                mias = {f for (a, b, uid, f) in self.docente[(doc, dia)] if uid not in ign and uid not in estorban
                        and not self.u[uid].get('reunion')}
                mias.update(celdas)
                if _racha(p, mias) > tope:
                    return False, []
            # Máximos por día
            tope = p.max_materia_dia.get((parte['curso'], parte['materia']))
            if tope is not None:
                ya = self.cm[(parte['curso'], parte['materia'], dia)] - sum(
                    self.u[x]['largo'] for x in estorban
                    if any(q['curso'] == parte['curso'] and q['materia'] == parte['materia'] for q in self.u[x]['partes']))
                if ya + u['largo'] > tope:
                    mismos = [x for x, (d, _) in self.pos.items() if d == dia and x not in estorban and x not in ign
                              and x not in self.fijas and any(q['curso'] == parte['curso'] and q['materia'] == parte['materia']
                                                              for q in self.u[x]['partes'])]
                    if not mismos:
                        return False, []
                    estorban.add(mismos[0])
            tope = p.max_docente_dia.get(doc)
            if tope is not None:
                ya = self.dd[(doc, dia)] - sum(self.u[x]['largo'] for x in estorban
                                               if any(q['docente'] == doc for q in self.u[x]['partes']))
                if ya + u['largo'] > tope:
                    mismos = [x for x, (d, _) in self.pos.items() if d == dia and x not in estorban and x not in ign
                              and x not in self.fijas and any(q['docente'] == doc for q in self.u[x]['partes'])]
                    if not mismos:
                        return False, []
                    estorban.add(mismos[0])
        # Espacio compartido
        esp = u.get('espacio')
        if esp and esp in p.espacios:
            cap = p.espacios[esp]
            for (ini, fin, f) in tramos:
                usan = [uid for (a, b, uid) in self.espacio[(esp, dia)] if a < fin and ini < b and uid not in ign
                        and uid not in estorban]
                while len(usan) >= cap:
                    x = usan.pop()
                    if not estorba(x):
                        return False, []
        return True, list(estorban)

    def _sede(self, uid, doc):
        for q in self.u[uid]['partes']:
            if q['docente'] == doc:
                return q.get('sede')
        return None

    def poner(self, u, dia, franja):
        uid = u['id']
        celdas = self.celdas(u, dia, franja)
        for parte in u['partes']:
            for f in celdas:
                self.curso[(parte['curso'], dia, f)] = uid
                _, _, ini, fin = self.p.franjas[f]
                self.docente[(parte['docente'], dia)].append((ini, fin, uid, f))
                self.cd[(parte['curso'], dia)].add(f)
                self.cmf[(parte['curso'], parte['materia'], dia)].append(f)
            self.cm[(parte['curso'], parte['materia'], dia)] += u['largo']
            self.dd[(parte['docente'], dia)] += u['largo']
        if u.get('espacio'):
            for f in celdas:
                _, _, ini, fin = self.p.franjas[f]
                self.espacio[(u['espacio'], dia)].append((ini, fin, uid))
        self.pos[uid] = (dia, franja)

    def quitar(self, uid):
        u = self.u[uid]
        dia, franja = self.pos.pop(uid)
        celdas = self.celdas(u, dia, franja)
        for parte in u['partes']:
            for f in celdas:
                self.curso.pop((parte['curso'], dia, f), None)
                self.cd[(parte['curso'], dia)].discard(f)
                lst = self.cmf[(parte['curso'], parte['materia'], dia)]
                if f in lst:
                    lst.remove(f)
            k = (parte['docente'], dia)
            self.docente[k] = [t for t in self.docente[k] if t[2] != uid]
            self.cm[(parte['curso'], parte['materia'], dia)] -= u['largo']
            self.dd[k] -= u['largo']
        if u.get('espacio'):
            k = (u['espacio'], dia)
            self.espacio[k] = [t for t in self.espacio[k] if t[2] != uid]

    # --- Calidad (menor es mejor) ---------------------------------------
    def costo_docente_dia(self, docente, dia):
        lst = self.docente.get((docente, dia))
        if not lst:
            return 0.0
        por_jornada = defaultdict(set)
        c = 0.0
        w = self.w
        prefiere_no = self.p.prefiere_no.get(docente, ())
        evitar = self.p.evitar.get(docente, ())
        for (ini, fin, uid, f) in lst:
            por_jornada[self.p.franjas[f][0]].add(self.p.indice[f])
            if (dia, f) in prefiere_no:
                c += w['prefiere_no']
            if (dia, f) in evitar:
                c += w['evitar']
        c += w['hueco'] * sum((max(i) - min(i) + 1) - len(i) for i in por_jornada.values())
        if len(lst) == 1:
            c += w['dia_suelto']
        c += w['equilibrio'] * len(lst) ** 2
        p = self.p
        if p.excluyentes and not p.excluyente_duro and docente not in p.sin_excluyente:
            fs = [f for (_, _, _, f) in lst]
            if any(_excluye(p, x, y) for i, x in enumerate(fs) for y in fs[i + 1:]):
                c += w['excluyente']
        return c

    def costo_docente_semana(self, docente):
        """El docente pidió un día libre y tiene clase todos los días."""
        if docente not in self.p.dia_libre:
            return 0.0
        dias = self.p.dias_docente.get(docente) or ()
        if dias and all(self.docente.get((docente, d)) for d in dias):
            return self.w['dia_libre']
        return 0.0

    def costo_curso_dia(self, curso, dia):
        fs = self.cd.get((curso, dia))
        if not fs:
            return 0.0
        idx = [self.p.indice[f] for f in fs]
        return self.w['hueco_curso'] * ((max(idx) + 1) - len(idx))     # libres antes de la última clase

    def costo_unidad(self, uid):
        u = self.u[uid]
        dia, franja = self.pos[uid]
        c = 0.0
        for parte in u['partes']:
            if parte['materia'] in self.p.primeras:
                c += self.w['tarde'] * self.p.indice[franja]
            if parte['materia'] in self.p.ultimas:
                ult = self.celdas(u, dia, franja)[-1]
                if self.p.indice[ult] == self.p.ultimo[self.p.franjas[ult][0]]:
                    c += self.w['ultima']
        return c

    def costo_repeticion(self, curso, materia, dia):
        n = self.cm[(curso, materia, dia)]
        if materia in self.p.dobles:
            c = 0.0 if n <= 3 else self.w['repetida'] * (n - 3)
            # Bloques: las horas del día deben quedar seguidas; una hora sola cuenta un poco
            fs = set(self.cmf.get((curso, materia, dia)) or ())
            if len(fs) >= 2:
                tramos = sum(1 for f in fs if self.p.anterior_bloque.get(f) not in fs)
                c += self.w['bloque'] * (tramos - 1)
            elif len(fs) == 1:
                c += self.w['bloque'] * 0.3
            return c
        return self.w['repetida'] * max(0, n - 1)

    def costo_total(self):
        c = sum(self.costo_docente_dia(d, dia) for (d, dia) in list(self.docente.keys()))
        c += sum(self.costo_curso_dia(cu, dia) for (cu, dia) in list(self.cd.keys()))
        c += sum(self.costo_repeticion(cu, m, dia) for (cu, m, dia) in list(self.cm.keys()))
        c += sum(self.costo_unidad(uid) for uid in self.pos)
        c += sum(self.costo_docente_semana(d) for d in self.p.dia_libre)
        return c


def _numero_hora(p, f, n):
    """¿La franja f es la hora de clase número n (desde 1) de su jornada? Si la jornada tiene
    menos de n horas, cuenta la última."""
    jid = p.franjas[f][0]
    return p.indice[f] == min(n - 1, p.ultimo[jid])


def _excluye(p, f1, f2):
    """¿Esas dos horas no pueden ir el mismo día para un docente? (dentro de la misma jornada)"""
    if p.franjas[f1][0] != p.franjas[f2][0]:
        return False
    for a, b in p.excluyentes:
        if (_numero_hora(p, f1, a) and _numero_hora(p, f2, b)) or (_numero_hora(p, f1, b) and _numero_hora(p, f2, a)):
            return True
    return False


def _racha(p, franjas):
    """La mayor cantidad de horas seguidas (sin descanso en medio) dentro de ese conjunto."""
    mejor = 0
    for f in franjas:
        if p.anterior.get(f) in franjas:
            continue
        n, x = 0, f
        while x in franjas:
            n += 1
            x = p.siguiente.get(x)
        mejor = max(mejor, n)
    return mejor


def _posiciones(p, est, u):
    cursos = [q['curso'] for q in u['partes']]
    comunes = None
    for c in cursos:
        s = set(p.slots.get(c, []))
        comunes = s if comunes is None else comunes & s
    orden = p.slots.get(cursos[0], [])
    comunes = comunes or set()
    out = []
    for (d, f) in orden:
        if (d, f) not in comunes:
            continue
        cs = est.celdas(u, d, f)
        # Todas las horas del bloque (no solo la primera) tienen que ser horas permitidas del curso
        if cs and all((d, x) in comunes for x in cs):
            out.append((d, f))
    return out


def _construir(p, est, cola, posibles, rnd, hasta, avance=None, total=1):
    reciente = {}
    paso = 0
    trabadas = defaultdict(int)
    while cola and time.monotonic() < hasta:
        paso += 1
        uid = cola.pop(0)
        u = est.u[uid]
        mejores, mejor_c = [], None
        for (d, f) in posibles[uid]:
            cabe, estorban = est.choques(u, d, f)
            if not cabe:
                continue
            if estorban:
                c = sum(est.u[x]['largo'] * len(est.u[x]['partes']) * (1 + 4 * (reciente.get(x, -99) > paso - 40))
                        for x in estorban) * 10 + rnd.random() * 5
            else:
                c = rnd.random()
                w = p.w
                for q in u['partes']:
                    if q['materia'] in p.primeras:
                        c += w['tarde'] * p.indice[f]
                    if est.cm[(q['curso'], q['materia'], d)] > 0 and q['materia'] not in p.dobles:
                        c += w['repetida']
                    if (d, f) in p.prefiere_no.get(q['docente'], ()):
                        c += w['prefiere_no']
                    if (d, f) in p.evitar.get(q['docente'], ()):
                        c += w['evitar']
            if mejor_c is None or c < mejor_c - 1e-9:
                mejores, mejor_c = [(d, f, estorban)], c
            elif abs(c - mejor_c) < 1e-9:
                mejores.append((d, f, estorban))
        if not mejores:
            trabadas[uid] += 1
            est.rechazos[uid] += 3
            if trabadas[uid] <= 3:              # si ni sacando a otras cabe, queda sin ubicar
                cola.append(uid)
            continue
        d, f, estorban = rnd.choice(mejores)
        for x in estorban:
            est.quitar(x)
            cola.append(x)
            est.rechazos[x] += 1
        est.poner(u, d, f)
        reciente[uid] = paso
        if avance and paso % 200 == 0:
            avance(min(60, int(60 * (1 - len(cola) / max(1, total)))))


def resolver(p, segundos=20, semilla=0, avance=None):
    """{'ubicadas': {uid: (dia, franja)}, 'sin_ubicar': [uid], 'divididas': [asig], 'costo', 'estado'}."""
    rnd = random.Random(semilla)
    est = Estado(p)
    limite = time.monotonic() + segundos
    t_construir = time.monotonic() + segundos * 0.65

    for i, fx in enumerate(p.fijas):
        u = unidad_simple(f'F{i}', fx['asig'], fx['curso'], fx['docente'], fx['materia'], 1, fx.get('sede', ''),
                          fx.get('extra', False), False, fx.get('espacio', ''))
        est.u[u['id']] = u
        est.fijas.add(u['id'])
        est.poner(u, fx['dia'], fx['franja'])
    for u in p.unidades:
        est.u[u['id']] = u

    posibles = {u['id']: _posiciones(p, est, u) for u in p.unidades}

    def dificultad(u):
        libres = [x for x in posibles[u['id']] if x not in p.no_puede.get(u['partes'][0]['docente'], ())]
        return (-len(u['partes']), -u['largo'], len(libres) + rnd.random())

    cola = [u['id'] for u in sorted(p.unidades, key=dificultad)]
    _construir(p, est, cola, posibles, rnd, t_construir, avance, len(p.unidades))

    divididas = []
    nuevas = []
    for uid in [x for x in est.u if x not in est.pos and x not in est.fijas]:
        u = est.u[uid]
        if u['largo'] > 1 and u.get('dividir'):
            divididas.append(u['asig'])
            del est.u[uid]
            for k in range(u['largo']):
                nu = dict(u, id=f'{uid}.{k}', largo=1)
                est.u[nu['id']] = nu
                posibles[nu['id']] = _posiciones(p, est, nu)
                nuevas.append(nu['id'])
    if nuevas:
        resto = [x for x in est.u if x not in est.pos and x not in est.fijas]
        _construir(p, est, resto, posibles, rnd, max(t_construir, time.monotonic() + segundos * 0.15))

    movibles = [uid for uid in est.pos if uid not in est.fijas]
    t0 = time.monotonic()
    temp = 2.0
    intentos = 0
    actual = est.costo_total()
    mejor, mejor_pos = actual, dict(est.pos)
    while movibles and time.monotonic() < limite:
        intentos += 1
        uid = rnd.choice(movibles)
        u = est.u[uid]
        d0, f0 = est.pos[uid]
        destino = rnd.choice(posibles[uid])
        if destino == (d0, f0):
            continue
        d1, f1 = destino
        est.quitar(uid)
        cabe, estorban = est.choques(u, d1, f1)
        otro = None
        if cabe and len(estorban) == 1 and len(u['partes']) == 1:
            otro = estorban[0]
            ou = est.u[otro]
            if (len(ou['partes']) != 1 or ou['partes'][0]['curso'] != u['partes'][0]['curso']
                    or ou['largo'] != u['largo'] or otro in est.fijas):
                cabe = False
        if not cabe or (estorban and otro is None):
            est.poner(u, d0, f0)
            continue
        est.poner(u, d0, f0)
        implicadas = [uid] + ([otro] if otro else [])
        dias = {d0, d1}
        antes = _costo_local(est, implicadas, dias)
        est.quitar(uid)
        if otro is not None:
            od, of = est.pos[otro]
            est.quitar(otro)
            est.poner(u, d1, f1)
            cabe2, est2 = est.choques(est.u[otro], d0, f0)
            if not cabe2 or est2:
                est.quitar(uid)
                est.poner(est.u[otro], od, of)
                est.poner(u, d0, f0)
                continue
            est.poner(est.u[otro], d0, f0)
        else:
            est.poner(u, d1, f1)
        delta = _costo_local(est, implicadas, dias) - antes
        frac = (time.monotonic() - t0) / max(0.001, limite - t0)
        t = temp * (1 - frac) + 0.01
        if delta > 0 and rnd.random() > math.exp(-delta / t):
            est.quitar(uid)
            if otro is not None:
                est.quitar(otro)
                est.poner(est.u[otro], od, of)
            est.poner(u, d0, f0)
        else:
            actual += delta
            if actual < mejor - 1e-9:
                mejor, mejor_pos = actual, dict(est.pos)
        if avance and intentos % 2000 == 0:
            avance(60 + int(40 * min(1, frac)))

    if mejor_pos != est.pos:
        est = _reconstruir(p, est, mejor_pos)
    return {'ubicadas': {uid: est.pos[uid] for uid in est.pos if uid not in est.fijas},
            'sin_ubicar': [uid for uid in est.u if uid not in est.pos and uid not in est.fijas],
            'divididas': sorted(set(divididas)),
            'costo': round(est.costo_total(), 1), 'estado': est}


def _reconstruir(p, viejo, posiciones):
    est = Estado(p)
    est.u = viejo.u
    est.fijas = viejo.fijas
    est.rechazos = viejo.rechazos
    for uid, (d, f) in posiciones.items():
        est.poner(est.u[uid], d, f)
    return est


def _costo_local(est, uids, dias):
    docentes = {q['docente'] for x in uids for q in est.u[x]['partes']}
    cursos = {q['curso'] for x in uids for q in est.u[x]['partes']}
    cms = {(q['curso'], q['materia']) for x in uids for q in est.u[x]['partes']}
    c = 0.0
    for d in set(dias):
        for doc in docentes:
            c += est.costo_docente_dia(doc, d)
        for cu in cursos:
            c += est.costo_curso_dia(cu, d)
        for (cu, m) in cms:
            c += est.costo_repeticion(cu, m, d)
    for doc in docentes:
        c += est.costo_docente_semana(doc)
    for x in uids:
        if x in est.pos:
            c += est.costo_unidad(x)
    return c


def huecos_por_docente(est):
    salida = defaultdict(int)
    for (doc, dia), lst in list(est.docente.items()):
        por_jornada = defaultdict(set)
        for (ini, fin, uid, f) in lst:
            por_jornada[est.p.franjas[f][0]].add(est.p.indice[f])
        salida[doc] += sum((max(i) - min(i) + 1) - len(i) for i in por_jornada.values() if i)
    return dict(salida)
