"""Generador de horarios (Python puro, sin dependencias).

Recibe el problema ya armado (ver datos.py) y devuelve dónde va cada clase.

Cómo trabaja:
1. Construcción con «expulsión»: ubica primero las clases más difíciles (bloques
   dobles, docentes con poca disponibilidad). Si una clase no cabe en ningún
   lado, se ubica donde menos estorbe y saca a las que chocan, que vuelven a la
   cola. Es la misma idea de los generadores conocidos (FET): casi siempre
   encuentra un horario completo si existe.
2. Mejora: con el horario completo, prueba mover y cambiar clases para quitar
   huecos de los docentes, repartir las materias en la semana y llevar las que
   lo piden a las primeras horas. Nunca rompe una condición obligatoria.

Condiciones obligatorias: un curso no tiene dos clases a la vez; un docente no
está en dos lugares a la misma hora (aunque sean de jornadas distintas: se
compara por hora real); cada materia tiene su intensidad horaria; las horas en
que el docente no puede; las clases fijadas a mano no se mueven; máximo de
horas por día de cada materia y de cada docente; los bloques dobles van
seguidos, sin descanso en medio.
"""
import random
import time
from collections import defaultdict

PESO_HUECO = 3.0
PESO_REPETIDA = 2.0
PESO_TARDE = 0.4


class Problema:
    """Datos del horario a generar (todo con ids y números, sin Django).

    franjas:   {franja_id: (jornada_id, orden, inicio_min, fin_min)}
    siguiente: {franja_id: franja_id de la clase que sigue sin descanso en medio}
    slots:     {curso_id: [(dia, franja_id), …]} posiciones de clase del curso
    unidades:  [{'id', 'asig', 'curso', 'docente', 'materia', 'largo'}]  (largo 1 o 2)
    fijas:     [{'asig', 'curso', 'docente', 'materia', 'dia', 'franja'}]
    no_puede:  {docente_id: {(dia, franja_id), …}}
    max_materia_dia: {(curso, materia): n}
    max_docente_dia: {docente_id: n}
    primeras: {materia_id, …}
    """

    def __init__(self, franjas, siguiente, slots, unidades, fijas=(), no_puede=None, max_materia_dia=None,
                 max_docente_dia=None, primeras=None, dobles=None):
        self.franjas = franjas
        self.siguiente = siguiente
        self.slots = slots
        self.unidades = list(unidades)
        self.fijas = list(fijas)
        self.no_puede = no_puede or {}
        self.max_materia_dia = max_materia_dia or {}
        self.max_docente_dia = max_docente_dia or {}
        self.primeras = primeras or set()
        self.dobles = dobles or set()
        # Para convertir horas reales a «franjas del docente» al contar huecos.
        self.por_jornada = defaultdict(list)
        for fid, (jid, orden, ini, fin) in franjas.items():
            self.por_jornada[jid].append((orden, fid))
        self.indice = {}
        for jid, lst in self.por_jornada.items():
            lst.sort()
            for i, (_, fid) in enumerate(lst):
                self.indice[fid] = i


class Estado:
    def __init__(self, p):
        self.p = p
        self.curso = {}                         # (curso, dia, franja) -> uid
        self.docente = defaultdict(list)        # (docente, dia) -> [(ini, fin, uid)]
        self.cm = defaultdict(int)              # (curso, materia, dia) -> horas
        self.dd = defaultdict(int)              # (docente, dia) -> horas
        self.pos = {}                           # uid -> (dia, franja)
        self.u = {}                             # uid -> unidad
        self.fijas = set()

    def celdas(self, u, dia, franja):
        if u['largo'] == 1:
            return [franja]
        sig = self.p.siguiente.get(franja)
        return [franja, sig] if sig else None

    def choques(self, u, dia, franja, ignorar=()):
        """(cabe, [uids que estorban]). cabe=False si hay algo que no se puede quitar."""
        p = self.p
        celdas = self.celdas(u, dia, franja)
        if not celdas:
            return False, []
        estorban = set()
        no_puede = p.no_puede.get(u['docente'], ())
        for f in celdas:
            if (dia, f) in no_puede:
                return False, []
            otro = self.curso.get((u['curso'], dia, f))
            if otro is not None and otro not in ignorar:
                if otro in self.fijas:
                    return False, []
                estorban.add(otro)
            _, _, ini, fin = p.franjas[f]
            for (a, b, uid) in self.docente[(u['docente'], dia)]:
                if uid in ignorar or uid == u['id']:
                    continue
                if a < fin and ini < b:
                    if uid in self.fijas:
                        return False, []
                    estorban.add(uid)
        tope = p.max_materia_dia.get((u['curso'], u['materia']))
        if tope is not None:
            ya = self.cm[(u['curso'], u['materia'], dia)] - sum(
                self.u[x]['largo'] for x in estorban if self.u[x]['curso'] == u['curso'] and self.u[x]['materia'] == u['materia'])
            if ya + u['largo'] > tope:
                mismos = [x for x, (d, _) in self.pos.items() if d == dia and self.u[x]['curso'] == u['curso']
                          and self.u[x]['materia'] == u['materia'] and x not in estorban and x not in ignorar]
                movibles = [x for x in mismos if x not in self.fijas]
                if not movibles:
                    return False, []
                estorban.add(movibles[0])
        tope = p.max_docente_dia.get(u['docente'])
        if tope is not None:
            ya = self.dd[(u['docente'], dia)] - sum(self.u[x]['largo'] for x in estorban if self.u[x]['docente'] == u['docente'])
            if ya + u['largo'] > tope:
                mismos = [x for x, (d, _) in self.pos.items() if d == dia and self.u[x]['docente'] == u['docente']
                          and x not in estorban and x not in self.fijas and x not in ignorar]
                if not mismos:
                    return False, []
                estorban.add(mismos[0])
        return True, list(estorban)

    def poner(self, u, dia, franja):
        uid = u['id']
        for f in self.celdas(u, dia, franja):
            self.curso[(u['curso'], dia, f)] = uid
            _, _, ini, fin = self.p.franjas[f]
            self.docente[(u['docente'], dia)].append((ini, fin, uid))
        self.cm[(u['curso'], u['materia'], dia)] += u['largo']
        self.dd[(u['docente'], dia)] += u['largo']
        self.pos[uid] = (dia, franja)

    def quitar(self, uid):
        u = self.u[uid]
        dia, franja = self.pos.pop(uid)
        for f in self.celdas(u, dia, franja):
            self.curso.pop((u['curso'], dia, f), None)
        lst = self.docente[(u['docente'], dia)]
        self.docente[(u['docente'], dia)] = [t for t in lst if t[2] != uid]
        self.cm[(u['curso'], u['materia'], dia)] -= u['largo']
        self.dd[(u['docente'], dia)] -= u['largo']

    # --- Calidad (menor es mejor) ---------------------------------------
    def costo_docente_dia(self, docente, dia):
        lst = self.docente.get((docente, dia))
        if not lst:
            return 0.0
        por_jornada = defaultdict(list)
        for (ini, fin, uid) in lst:
            u = self.u[uid]
            d, f0 = self.pos[uid]
            for f in self.celdas(u, d, f0):
                por_jornada[self.p.franjas[f][0]].append(self.p.indice[f])
        huecos = 0
        for idx in por_jornada.values():
            idx = sorted(set(idx))
            huecos += (idx[-1] - idx[0] + 1) - len(idx)
        return PESO_HUECO * huecos

    def costo_unidad(self, uid):
        u = self.u[uid]
        dia, franja = self.pos[uid]
        c = 0.0
        if u['materia'] in self.p.primeras:
            c += PESO_TARDE * self.p.indice[franja]
        return c

    def costo_repeticion(self, curso, materia, dia):
        n = self.cm[(curso, materia, dia)]
        if materia in self.p.dobles:
            return 0.0 if n <= 2 else PESO_REPETIDA * (n - 2)
        return PESO_REPETIDA * max(0, n - 1)

    def costo_total(self):
        c = sum(self.costo_docente_dia(d, dia) for (d, dia) in list(self.docente.keys()))
        c += sum(self.costo_repeticion(cu, m, dia) for (cu, m, dia) in list(self.cm.keys()))
        c += sum(self.costo_unidad(uid) for uid in self.pos)
        return c


def _posiciones(p, u):
    return [(d, f) for (d, f) in p.slots.get(u['curso'], []) if u['largo'] == 1 or p.siguiente.get(f)]


def resolver(p, segundos=20, semilla=0, avance=None):
    """Devuelve {'ubicadas': {uid: (dia, franja)}, 'sin_ubicar': [uid], 'costo': float}."""
    rnd = random.Random(semilla)
    est = Estado(p)
    limite = time.monotonic() + segundos
    t_construir = time.monotonic() + segundos * 0.65

    # Fijas primero (las puso el coordinador; no se mueven).
    for i, fx in enumerate(p.fijas):
        uid = f'F{i}'
        u = {'id': uid, 'asig': fx['asig'], 'curso': fx['curso'], 'docente': fx['docente'], 'materia': fx['materia'],
             'largo': 1}
        est.u[uid] = u
        est.fijas.add(uid)
        est.poner(u, fx['dia'], fx['franja'])
    for u in p.unidades:
        est.u[u['id']] = u

    posibles = {u['id']: _posiciones(p, u) for u in p.unidades}

    def dificultad(u):
        libres = [x for x in posibles[u['id']] if x not in p.no_puede.get(u['docente'], ())]
        return (-u['largo'], len(libres) + rnd.random())

    cola = sorted(p.unidades, key=dificultad)
    cola = [u['id'] for u in cola]
    reciente = {}
    paso = 0
    while cola and time.monotonic() < t_construir:
        paso += 1
        uid = cola.pop(0)
        u = est.u[uid]
        mejores, mejor_c = [], None
        for (d, f) in posibles[uid]:
            cabe, estorban = est.choques(u, d, f)
            if not cabe:
                continue
            c = sum(1 + 3 * (reciente.get(x, -99) > paso - 25) for x in estorban) * 10
            if not estorban:
                c = (PESO_TARDE * p.indice[f] if u['materia'] in p.primeras else 0) + rnd.random() \
                    + PESO_REPETIDA * (est.cm[(u['curso'], u['materia'], d)] > 0 and u['materia'] not in p.dobles)
            if mejor_c is None or c < mejor_c - 1e-9:
                mejores, mejor_c = [(d, f, estorban)], c
            elif abs(c - mejor_c) < 1e-9:
                mejores.append((d, f, estorban))
        if not mejores:
            cola.append(uid)                     # no tiene dónde ir ni sacando a otros
            if paso > len(p.unidades) * 50:
                break
            continue
        d, f, estorban = rnd.choice(mejores)
        for x in estorban:
            est.quitar(x)
            cola.append(x)
        est.poner(u, d, f)
        reciente[uid] = paso
        if avance and paso % 200 == 0:
            avance(min(60, int(60 * (1 - len(cola) / max(1, len(p.unidades))))))

    # Mejora: mover o intercambiar sin romper nada.
    movibles = [uid for uid in est.pos if uid not in est.fijas]
    t0 = time.monotonic()
    temp = 2.0
    intentos = 0
    actual = est.costo_total() if not cola else float('inf')
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
        if cabe and len(estorban) == 1:
            otro = estorban[0]
            ou = est.u[otro]
            if ou['curso'] != u['curso'] or ou['largo'] != u['largo'] or otro in est.fijas:
                cabe = False
        if not cabe or len(estorban) > 1:
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
        if delta > 0 and rnd.random() > pow(2.718, -delta / t):
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

    if not cola and mejor_pos != est.pos:
        est = _reconstruir(p, est, mejor_pos)
    return {'ubicadas': {uid: est.pos[uid] for uid in est.pos if uid not in est.fijas},
            'sin_ubicar': [uid for uid in est.u if uid not in est.pos],
            'costo': round(est.costo_total(), 1), 'estado': est}


def _reconstruir(p, viejo, posiciones):
    est = Estado(p)
    est.u = viejo.u
    est.fijas = viejo.fijas
    for uid, (d, f) in posiciones.items():
        est.poner(est.u[uid], d, f)
    return est


def _costo_local(est, uids, dias):
    """Costo de lo que cambia al mover estas clases entre estos días."""
    docentes = {est.u[x]['docente'] for x in uids}
    cms = {(est.u[x]['curso'], est.u[x]['materia']) for x in uids}
    c = 0.0
    for d in set(dias):
        for doc in docentes:
            c += est.costo_docente_dia(doc, d)
        for (cu, m) in cms:
            c += est.costo_repeticion(cu, m, d)
    for x in uids:
        if x in est.pos:
            c += est.costo_unidad(x)
    return c


def huecos_por_docente(est):
    salida = defaultdict(int)
    for (doc, dia) in list(est.docente.keys()):
        salida[doc] += int(est.costo_docente_dia(doc, dia) / PESO_HUECO)
    return dict(salida)
