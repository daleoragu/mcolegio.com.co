"""Lo que hace la app de escritorio, sin la ventana (así se puede probar).

Un PROYECTO (.mchp) guarda los datos del colegio, las condiciones que el
coordinador fue poniendo y las alternativas de horario (generadas o armadas a
mano arrastrando fichas).
"""
import copy
import json
import time
from collections import defaultdict

from . import nucleo

TIPO_PROYECTO = 'mcolegio-horario-proyecto'
ESTADOS_CELDA = ('libre', 'no_puede', 'prefiere_no', 'evitar', 'preferida')
LISTAS_CELDA = ('no_puede', 'prefiere_no', 'evitar', 'preferida')
# Áreas y materias: libre → no van → mejor no → preferible (azul) → libre
CICLO_MATERIA = {'libre': 'no_puede', 'no_puede': 'prefiere_no', 'prefiere_no': 'preferida', 'preferida': 'libre'}


class Proyecto:
    def __init__(self, crudo, cond=None, alternativas=None, ruta=None):
        self.datos = nucleo.Datos(crudo)
        self.cond = cond or nucleo.condiciones_vacias()
        for k, v in nucleo.condiciones_vacias().items():
            self.cond.setdefault(k, v)
        self.alternativas = alternativas or []
        self.ruta = ruta
        for alt in self.alternativas:
            alt.setdefault('actividades', [])
            alt.setdefault('acompanamientos', [])
        nucleo.poner_nombres_de_dias(self.cond)

    # --- Archivos -----------------------------------------------------------
    @classmethod
    def abrir_datos(cls, ruta):
        with open(ruta, encoding='utf-8-sig') as fh:
            p = cls(nucleo.leer_json(fh.read(), nucleo.TIPO_DATOS))
        p.traer_disponibilidad()
        return p

    def disponibilidad_plataforma(self):
        """Lo que cada docente marcó en «Mi disponibilidad» de la plataforma."""
        return {int(k): v for k, v in (self.datos.crudo.get('disponibilidad') or {}).items() if int(k) in self.datos.docentes}

    def traer_disponibilidad(self, solo_sin_marcar=False):
        """Pasa a las condiciones las horas que los docentes marcaron en la plataforma.

        Devuelve cuántos docentes se actualizaron. Con solo_sin_marcar no toca a
        quien ya tiene horas marcadas aquí."""
        n = 0
        validas = {f'{d}-{f}' for j in self.datos.jornadas.values() for d in j['dias'] for f in
                   (x['id'] for x in j['franjas'] if not x['descanso'])}
        for did, disp in self.disponibilidad_plataforma().items():
            r = self.docente(did)
            if solo_sin_marcar and any(r.get(k) for k in LISTAS_CELDA):
                continue
            r['no_puede'] = [k for k in disp.get('no_puede', []) if k in validas]
            r['prefiere_no'] = [k for k in disp.get('prefiere_no', []) if k in validas]
            r['evitar'] = []
            if disp.get('dia_libre'):
                r['dia_libre'] = True
            if disp.get('nota'):
                r['nota'] = disp['nota']
            n += 1
        return n

    @classmethod
    def abrir(cls, ruta):
        with open(ruta, encoding='utf-8-sig') as fh:
            p = nucleo.leer_json(fh.read(), TIPO_PROYECTO)
        return cls(p['datos'], p.get('condiciones'), p.get('alternativas'), ruta)

    def guardar(self, ruta=None):
        self.ruta = ruta or self.ruta
        with open(self.ruta, 'w', encoding='utf-8') as fh:
            json.dump({'tipo': TIPO_PROYECTO, 'version': nucleo.VERSION, 'datos': self.datos.crudo,
                       'condiciones': self.cond, 'alternativas': self.alternativas}, fh, ensure_ascii=False)

    def actualizar_datos(self, ruta):
        """Datos nuevos de la plataforma, conservando las condiciones que siguen sirviendo."""
        nuevo = Proyecto.abrir_datos(ruta)
        if nuevo.datos.colegio['id'] != self.datos.colegio['id']:
            raise nucleo.ArchivoInvalido('Esos datos son de otro colegio.')
        d = nuevo.datos
        c = self.cond
        c['fijas'] = [f for f in c['fijas'] if int(f['asignacion']) in d.asignaciones and int(f['franja']) in d.franjas]
        c['ih'] = {k: v for k, v in c['ih'].items() if int(k) in d.asignaciones}
        c['asignaciones'] = {k: v for k, v in c['asignaciones'].items() if int(k) in d.asignaciones}
        for g in c['simultaneas']:
            g['asignaciones'] = [a for a in g['asignaciones'] if int(a) in d.asignaciones]
        for g in c.get('multigrado', []):
            g['cursos'] = [x for x in g.get('cursos', []) if int(x) in d.cursos]
        c['cursos'] = {k: v for k, v in c.get('cursos', {}).items() if int(k) in d.cursos}
        nuevo.cond = c
        nuevo.ruta = self.ruta
        return nuevo

    # --- Condiciones ----------------------------------------------------------
    def poner_ih(self, aid, n):
        self.cond['ih'][str(aid)] = max(0, int(n))

    def regla(self, mid):
        return self.cond['materias'].setdefault(str(mid), {})

    def asig(self, aid):
        return self.cond['asignaciones'].setdefault(str(aid), {})

    def docente(self, did):
        r = self.cond['docentes'].setdefault(str(did), {})
        for k in LISTAS_CELDA:
            r.setdefault(k, [])
        return r

    def estado_celda(self, did, dia, fid):
        r = self.docente(did)
        clave = f'{dia}-{fid}'
        for k in LISTAS_CELDA:
            if clave in r[k]:
                return k
        return 'libre'

    def poner_celda(self, did, dia, fid, estado):
        r = self.docente(did)
        clave = f'{dia}-{fid}'
        for k in LISTAS_CELDA:
            if clave in r[k]:
                r[k].remove(clave)
        if estado in LISTAS_CELDA:
            r[estado].append(clave)

    def siguiente_estado(self, did, dia, fid):
        """Libre → no puede → mejor no → mejor no (fuerte) → preferida → libre."""
        actual = self.estado_celda(did, dia, fid)
        nuevo = ESTADOS_CELDA[(ESTADOS_CELDA.index(actual) + 1) % len(ESTADOS_CELDA)]
        self.poner_celda(did, dia, fid, nuevo)
        return nuevo

    # Horas en que un curso no tiene clase (sale temprano, actividad fija…)
    def curso(self, cid):
        r = self.cond['cursos'].setdefault(str(cid), {})
        r.setdefault('no_puede', [])
        return r

    def _motivo_salon(self, alt, a, dia, fid, ignorar=None):
        """Si la clase necesita un salón (o uno de una agrupación) y a esa hora no queda ninguno."""
        req = nucleo.salon_requerido(self.cond, a)
        llaves = nucleo.claves_salon(self.cond, req)
        if not llaves:
            return None
        D = self.datos
        cap, menos = nucleo.capacidad_salones(self.cond)
        ini, fin = D.intervalo(fid)
        ign = set(ignorar) if isinstance(ignorar, (set, list, tuple)) else {ignorar}
        juntos = nucleo.grupos_multigrado(self.cond)
        for k in llaves:
            libre = cap.get(k, 0) - menos.get(k, {}).get((dia, fid), 0)
            if libre <= 0:
                return f'{nucleo.nombre_salon(self.cond, req)} no está disponible a esa hora (bloqueado en Salones).'
            usan = 0
            for i, s in enumerate(alt['sesiones']):
                if i in ign or s['dia'] != dia or s['franja'] not in D.franjas:
                    continue
                b = D.asignaciones.get(s['asignacion'])
                x, y = D.intervalo(s['franja'])
                if not b or not (x < fin and ini < y):
                    continue
                if juntos.get(b['curso']) is not None and juntos.get(b['curso']) == juntos.get(a['curso']):
                    continue
                if k in nucleo.claves_salon(self.cond, nucleo.salon_requerido(self.cond, b)):
                    usan += 1
            if usan >= libre:
                return f'{nucleo.nombre_salon(self.cond, req)} ya está ocupado a esa hora.'
        return None

    # Horas bloqueadas por área (para todas las materias del área): libre → no van → mejor no → libre
    def area(self, nombre):
        r = self.cond.setdefault('areas', {}).setdefault(nombre, {})
        r.setdefault('no_puede', [])
        r.setdefault('prefiere_no', [])
        return r

    def estado_celda_area(self, nombre, dia, fid):
        r = (self.cond.get('areas') or {}).get(nombre) or {}
        clave = f'{dia}-{fid}'
        if clave in (r.get('no_puede') or []):
            return 'no_puede'
        if clave in (r.get('prefiere_no') or []):
            return 'prefiere_no'
        if clave in (r.get('preferida') or []):
            return 'preferida'
        return 'libre'

    def siguiente_estado_area(self, nombre, dia, fid):
        r = self.area(nombre)
        clave = f'{dia}-{fid}'
        actual = self.estado_celda_area(nombre, dia, fid)
        r.setdefault('preferida', [])
        for k in ('no_puede', 'prefiere_no', 'preferida'):
            if clave in r.get(k, []):
                r[k].remove(clave)
        nuevo = CICLO_MATERIA[actual]
        if nuevo != 'libre':
            r.setdefault(nuevo, []).append(clave)
        return nuevo

    # Horas bloqueadas por materia (libre → no va → mejor no → libre)
    def estado_celda_materia(self, mid, dia, fid):
        r = (self.cond.get('materias') or {}).get(str(mid)) or {}
        clave = f'{dia}-{fid}'
        if clave in (r.get('no_puede') or []):
            return 'no_puede'
        if clave in (r.get('prefiere_no') or []):
            return 'prefiere_no'
        if clave in (r.get('preferida') or []):
            return 'preferida'
        return 'libre'

    def siguiente_estado_materia(self, mid, dia, fid):
        r = self.regla(mid)
        r.setdefault('no_puede', [])
        r.setdefault('prefiere_no', [])
        clave = f'{dia}-{fid}'
        actual = self.estado_celda_materia(mid, dia, fid)
        r.setdefault('preferida', [])
        for k in ('no_puede', 'prefiere_no', 'preferida'):
            if clave in r.get(k, []):
                r[k].remove(clave)
        nuevo = CICLO_MATERIA[actual]
        if nuevo != 'libre':
            r.setdefault(nuevo, []).append(clave)
        return nuevo

    def jornadas_de_materia(self, mid):
        D = self.datos
        jids = {D.jornada_de_curso.get(a['curso']) for a in D.asignaciones.values() if a['materia'] == mid}
        return [D.jornadas[j] for j in sorted(x for x in jids if x in D.jornadas)]

    # --- Salones y agrupaciones ------------------------------------------------------
    def salones(self):
        return self.cond.setdefault('salones', [])

    def salon(self, sid):
        return next((s for s in self.salones() if str(s['id']) == str(sid)), None)

    def nuevo_salon(self, nombre, capacidad=1, grupos=()):
        usados = {str(s['id']) for s in self.salones()}
        k = len(usados) + 1
        while f'S{k}' in usados:
            k += 1
        s = {'id': f'S{k}', 'nombre': nombre.strip() or f'Salón {k}', 'capacidad': max(1, int(capacidad or 1)),
             'grupos': list(grupos), 'no_puede': []}
        self.salones().append(s)
        for g in grupos:
            self.nueva_agrupacion(g)
        return s

    def quitar_salon(self, sid):
        """Quita el salón y lo borra de cursos, profesores, materias y clases que lo pedían."""
        self.cond['salones'] = [s for s in self.salones() if str(s['id']) != str(sid)]
        clave = f'S:{sid}'
        for grupo in ('cursos', 'docentes', 'materias', 'asignaciones'):
            for r in self.cond.get(grupo, {}).values():
                if r.get('salon') == clave:
                    r.pop('salon', None)

    def agrupaciones(self):
        return self.cond.setdefault('grupos_salones', [])

    def nueva_agrupacion(self, nombre, tipo='bloque'):
        nombre = (nombre or '').strip()
        if nombre and not any(g['nombre'] == nombre for g in self.agrupaciones()):
            self.agrupaciones().append({'nombre': nombre, 'tipo': tipo})
        return nombre

    def quitar_agrupacion(self, nombre):
        self.cond['grupos_salones'] = [g for g in self.agrupaciones() if g['nombre'] != nombre]
        for s in self.salones():
            s['grupos'] = [g for g in s.get('grupos') or [] if g != nombre]
        clave = f'G:{nombre}'
        for grupo in ('cursos', 'docentes', 'materias', 'asignaciones'):
            for r in self.cond.get(grupo, {}).values():
                if r.get('salon') == clave:
                    r.pop('salon', None)

    def opciones_salon(self):
        """[(valor, texto)] para escoger dónde va algo: ninguno, un salón o cualquiera de una agrupación."""
        out = [('', '(ninguno)')]
        out += [(f'S:{s["id"]}', s['nombre']) for s in sorted(self.salones(), key=lambda s: s['nombre'])]
        out += [(f'G:{g}', f'Cualquiera de {g}') for g in sorted(nucleo.grupos_de_salones(self.cond))]
        return out

    def usos_salon(self, sid):
        """Quién tiene este salón (o una agrupación suya) como propio: ['Curso 601', 'Prof. …', 'Materia …']."""
        D = self.datos
        s = self.salon(sid) or {}
        claves = {f'S:{sid}'} | {f'G:{g}' for g in s.get('grupos') or []}
        out = []
        for cid, r in self.cond.get('cursos', {}).items():
            if r.get('salon') in claves and int(cid) in D.cursos:
                out.append(f'Curso {D.nombre_curso(int(cid))}')
        for did, r in self.cond.get('docentes', {}).items():
            if r.get('salon') in claves and int(did) in D.docentes:
                out.append(D.nombre_docente(int(did)))
        for mid, r in self.cond.get('materias', {}).items():
            if r.get('salon') in claves and int(mid) in D.materias:
                out.append(f'Materia {D.nombre_materia(int(mid))}')
        return out

    def estado_celda_salon(self, sid, dia, fid):
        s = self.salon(sid) or {}
        return 'no_puede' if f'{dia}-{fid}' in (s.get('no_puede') or []) else 'libre'

    def alternar_celda_salon(self, sid, dia, fid):
        s = self.salon(sid)
        if not s:
            return 'libre'
        lst = s.setdefault('no_puede', [])
        clave = f'{dia}-{fid}'
        if clave in lst:
            lst.remove(clave)
            return 'libre'
        lst.append(clave)
        return 'no_puede'

    def salon_por_curso(self, grupo='Salones de curso'):
        """Crea un salón para cada curso que no tenga (con el nombre del curso) y se lo asigna."""
        D = self.datos
        self.nueva_agrupacion(grupo)
        n = 0
        for c in D.crudo['cursos']:
            if c['id'] not in D.jornada_de_curso or self.curso(c['id']).get('salon'):
                continue
            s = self.nuevo_salon(f'Salón {c["nombre"]}', 1, [grupo])
            self.curso(c['id'])['salon'] = f'S:{s["id"]}'
            n += 1
        return n

    def jornadas_de_area(self, nombre):
        """Las jornadas donde se dictan materias del área."""
        D = self.datos
        mats = set(D.areas.get(nombre, []))
        jids = {D.jornada_de_curso.get(a['curso']) for a in D.asignaciones.values() if a['materia'] in mats}
        return [D.jornadas[j] for j in sorted(x for x in jids if x in D.jornadas)]

    def celda_curso(self, cid, dia, fid):
        clave = f'{dia}-{fid}'
        return clave in self.curso(cid)['no_puede'] or clave in (self.cond.get('marco_bloqueo') or [])

    def celda_marco(self, dia, fid):
        return f'{dia}-{fid}' in (self.cond.get('marco_bloqueo') or [])

    def alternar_celda_marco(self, dia, fid):
        """Hora sin clase para todo el colegio (sí / no)."""
        lst = self.cond.setdefault('marco_bloqueo', [])
        clave = f'{dia}-{fid}'
        if clave in lst:
            lst.remove(clave)
            return False
        lst.append(clave)
        return True

    def alternar_celda_curso(self, cid, dia, fid):
        lst = self.curso(cid)['no_puede']
        clave = f'{dia}-{fid}'
        if clave in lst:
            lst.remove(clave)
            return False
        lst.append(clave)
        return True

    def alternar_no_puede(self, did, dia, fid):
        nuevo = 'libre' if self.estado_celda(did, dia, fid) == 'no_puede' else 'no_puede'
        self.poner_celda(did, dia, fid, nuevo)
        return nuevo == 'no_puede'

    def marcar_dia(self, did, dia, estado):
        for j in self.jornadas_de_docente(did):
            if dia in j['dias']:
                for f in j['franjas']:
                    if not f['descanso']:
                        self.poner_celda(did, dia, f['id'], estado)

    def jornadas_de_docente(self, did):
        return [self.datos.jornadas[j] for j in self.datos.jornadas_de_docente(did)]

    def asignaciones_de_curso(self, cid):
        return sorted([a for a in self.datos.asignaciones.values() if a['curso'] == cid],
                      key=lambda a: self.datos.nombre_materia(a['materia']))

    def resumen_docente(self, did):
        """(horas de clase, horas extra, sedes) del docente."""
        base = extra = 0
        sedes = set()
        for a in self.datos.asignaciones.values():
            if a.get('docente') == did:
                n = self.datos.ih(a['id'], self.cond)
                k = nucleo.horas_extra(self.cond, a['id'], n)
                extra += k
                base += n - k
                sedes.add(self.datos.sede_de_curso(a['curso']) or 'Principal')
        return base, extra, sorted(sedes)

    # Reuniones, clases simultáneas y espacios
    def area_principal(self, did):
        """El área donde el docente dicta más horas (para su reunión de área)."""
        D = self.datos
        horas = defaultdict(int)
        for a in D.asignaciones.values():
            if a.get('docente') == did:
                area = D.materias.get(a['materia'], {}).get('area')
                if area:
                    horas[area] += D.ih(a['id'], self.cond)
        return max(sorted(horas), key=lambda x: horas[x]) if horas else None

    def areas_de_docente(self, did):
        D = self.datos
        return sorted({D.materias.get(a['materia'], {}).get('area') for a in D.asignaciones.values()
                       if a.get('docente') == did and D.materias.get(a['materia'], {}).get('area')})

    def reuniones_por_area(self):
        """Una reunión por cada área que todavía no tenga la suya. Cada docente va a UNA sola reunión:
        la de su área principal (donde dicta más horas), si todavía no está en otra."""
        D = self.datos
        ya = {r.get('area') for r in self.cond['reuniones']}
        ocupados = {int(d) for r in self.cond['reuniones'] for d in r.get('docentes', [])}
        nuevas = 0
        for area in sorted(D.areas):
            if area in ya:
                continue
            docentes = [d for d in D.docentes_de_area(area) if d not in ocupados and self.area_principal(d) == area]
            if len(docentes) < 2:              # un docente solo no hace reunión (se puede pasar a otra a mano)
                continue
            self.cond['reuniones'].append({'nombre': f'Reunión de {area}', 'area': area, 'docentes': docentes,
                                           'jefe': None, 'modo': 'auto', 'dos': False})
            ocupados.update(docentes)
            nuevas += 1
        return nuevas

    def reunion_de(self, did):
        """Índice de la reunión a la que va el docente (o None)."""
        for i, r in enumerate(self.cond.get('reuniones', [])):
            if did in [int(x) for x in r.get('docentes', [])]:
                return i
        return None

    def poner_en_reunion(self, did, i):
        """Pasa al docente a la reunión i (None = a ninguna). Un docente va a una sola reunión."""
        for k, r in enumerate(self.cond.get('reuniones', [])):
            docs = [int(x) for x in r.get('docentes', [])]
            if k == i:
                if did not in docs:
                    docs.append(did)
            else:
                docs = [x for x in docs if x != did]
                if r.get('jefe') and int(r['jefe']) == did:
                    r['jefe'] = None
            r['docentes'] = docs

    def ordenar_reuniones(self):
        """Quita a los docentes repetidos en varias reuniones (se quedan en la primera)."""
        vistos = set()
        for r in self.cond.get('reuniones', []):
            docs = []
            for x in r.get('docentes', []):
                if int(x) not in vistos:
                    vistos.add(int(x))
                    docs.append(int(x))
            r['docentes'] = docs

    def reuniones_en_horario(self, alt):
        """Con el horario ya armado, la mejor hora para cada reunión: donde estén libres la mayoría
        (el jefe siempre) y, si hace falta, qué clases habría que mover para que vengan todos.

        [{'i', 'nombre', 'dia', 'inicio', 'fin', 'libres': [did], 'mover': {did: [índices de sesiones]},
          'no': [did]}] (None en 'dia' si no se encontró hora)."""
        D = self.datos
        no_puede = {int(k): {tuple(int(x) for x in v.split('-')) for v in r.get('no_puede', [])}
                    for k, r in self.cond['docentes'].items()}
        por_doc = defaultdict(list)
        for k, s in enumerate(alt['sesiones']):
            did = D.asignaciones.get(s['asignacion'], {}).get('docente')
            if did and s['franja'] in D.franjas:
                por_doc[(did, s['dia'])].append((D.intervalo(s['franja']), k, bool(s.get('fijada'))))
        tomadas = defaultdict(list)          # reuniones ya escogidas: (did, dia) -> [(ini, fin)]
        horas = nucleo._horas_de_clase(D)

        def miembros_de(r):
            ms = [int(x) for x in r.get('docentes', []) if int(x) in D.docentes]
            jefe = int(r['jefe']) if r.get('jefe') else None
            if jefe and jefe not in ms:
                ms.append(jefe)
            return ms, jefe

        def evaluar(miembros, dia, ini, fin):
            libres, mover, no = [], {}, []
            for did in miembros:
                if nucleo._puede_reunirse(D, did, dia, ini, fin, no_puede) is None or any(
                        a < fin and ini < b for a, b in tomadas[(did, dia)]):
                    no.append(did)
                    continue
                choca = [(k, fija) for (a, b), k, fija in por_doc[(did, dia)] if a < fin and ini < b]
                if not choca:
                    libres.append(did)
                elif any(f for _, f in choca):
                    no.append(did)
                else:
                    mover[did] = [k for k, _ in choca]
            return libres, mover, no

        reus = self.cond.get('reuniones', [])
        comun = None
        if self.cond.get('reuniones_juntas') and reus:
            # Todas juntas: la hora donde vengan más (los jefes siempre), moviendo lo menos posible
            mejor_p = None
            for (dia, ini, fin, _) in horas:
                total, libres_t, ok = 0, 0, True
                for r in reus:
                    ms, jefe = miembros_de(r)
                    libres, mover, no = evaluar(ms, dia, ini, fin)
                    if jefe and jefe in no:
                        ok = False
                        break
                    total += len(libres) + len(mover)
                    libres_t += len(libres)
                if ok and (mejor_p is None or (total, libres_t, ini) > mejor_p):
                    comun, mejor_p = (dia, ini), (total, libres_t, ini)
        salida = []
        for i, r in enumerate(reus):
            miembros, jefe = miembros_de(r)
            mejor, puntos = None, None
            for (dia, ini, fin, _) in horas:
                if comun and (dia, ini) != comun:
                    continue
                libres, mover, no = evaluar(miembros, dia, ini, fin)
                if jefe and jefe in no:
                    continue
                pts = ((len(libres) + len(mover)) * 10000, len(libres) * 100, ini)
                if puntos is None or pts > puntos:
                    mejor, puntos = (dia, ini, fin, libres, mover, no), pts
            res = {'i': i, 'nombre': r.get('nombre') or 'Reunión de área', 'dia': None, 'inicio': None, 'fin': None,
                   'libres': [], 'mover': {}, 'no': miembros}
            if mejor:
                dia, ini, fin, libres, mover, no = mejor
                res.update({'dia': dia, 'inicio': ini, 'fin': fin, 'libres': libres, 'mover': mover, 'no': no})
                for did in libres + list(mover):
                    tomadas[(did, dia)].append((ini, fin))
            salida.append(res)
        return salida

    def texto_reuniones_en_horario(self, propuestas, alt):
        D = self.datos
        out = []
        for x in propuestas:
            if x['dia'] is None:
                out.append(f'{x["nombre"]}: no hay una hora en que pueda el jefe de área.')
                continue
            t = (f'{x["nombre"]}: {nucleo.DIAS[x["dia"]]} {nucleo.texto_hora(x["inicio"])} · '
                 f'{len(x["libres"])} libre(s)')
            if x['mover']:
                clases = []
                for did, ks in x['mover'].items():
                    for k in ks:
                        s = alt['sesiones'][k]
                        a = D.asignaciones[s['asignacion']]
                        clases.append(f'{D.nombre_docente(did)} ({D.nombre_curso(a["curso"])} '
                                      f'{D.nombre_materia(a["materia"])})')
                t += ' · hay que mover: ' + '; '.join(clases)
            if x['no']:
                t += ' · no pueden (reciben el acta): ' + ', '.join(D.nombre_docente(d) for d in x['no'])
            out.append(t)
        return out

    def acomodar_reuniones(self, alt, propuestas):
        """Fija cada reunión en la hora propuesta y saca las clases que estorban (quedan por ubicar,
        para «Completar lo que falta»). Devuelve cuántas horas de clase salieron."""
        quitar = set()
        for x in propuestas:
            if x['dia'] is None:
                continue
            r = self.cond['reuniones'][x['i']]
            r.update({'modo': 'fija', 'dia': x['dia'], 'hora': nucleo.texto_hora(x['inicio'])})
            for ks in x['mover'].values():
                quitar.update(ks)
        alt['sesiones'] = [s for k, s in enumerate(alt['sesiones']) if k not in quitar]
        alt['reuniones'] = self.ver_reuniones()
        self.revisar(alt)
        return len(quitar)

    def ver_reuniones(self):
        no_puede = {int(k): {tuple(int(x) for x in v.split('-')) for v in r.get('no_puede', [])}
                    for k, r in self.cond['docentes'].items()}
        return nucleo.ubicar_reuniones(self.datos, self.cond, no_puede)[0]

    def agregar_simultanea(self, nombre, aids):
        aids = [int(a) for a in aids]
        cursos = [self.datos.asignaciones[a]['curso'] for a in aids]
        if len(aids) < 2:
            return 'Escoja al menos dos clases.'
        if len(set(cursos)) != len(cursos):
            return 'Las clases simultáneas deben ser de cursos distintos.'
        horas = {self.datos.ih(a, self.cond) for a in aids}
        self.cond['simultaneas'].append({'nombre': nombre or 'Clases simultáneas', 'asignaciones': aids})
        return None if len(horas) == 1 else 'Quedó, pero no tienen las mismas horas: solo las comunes van juntas.'

    # --- Generar --------------------------------------------------------------
    def _cond_con_fijas(self, base, todas=False):
        cond = copy.deepcopy(self.cond)
        if base:
            cond['fijas'] = [{'asignacion': s['asignacion'], 'dia': s['dia'], 'franja': s['franja']}
                             for s in base['sesiones'] if todas or s.get('fijada')]
        return cond

    def _correr(self, cond, segundos, semilla, avance=None, vivo=None, parar=None):
        r = nucleo.generar(self.datos, cond, segundos=segundos, semilla=semilla, avance=avance, vivo=vivo, parar=parar)
        fijas = {(f['asignacion'], f['dia'], f['franja']) for f in cond.get('fijas', [])}
        for s in r['sesiones']:
            s['fijada'] = (s['asignacion'], s['dia'], s['franja']) in fijas
        self.revisar(r)
        return r

    def revisar(self, alt):
        alt['choques'] = nucleo.revisar(self.datos, alt['sesiones'], self.cond)
        for s in alt['sesiones']:
            a = self.datos.asignaciones.get(s['asignacion'])
            if a and s['franja'] in self.datos.franjas and self.celda_curso(a['curso'], s['dia'], s['franja']):
                alt['choques'].append(f'{self.datos.nombre_curso(a["curso"])} no tiene clase el '
                                      f'{nucleo.DIAS[s["dia"]]} a las {self.datos.franjas[s["franja"]]["inicio"]}.')
            if a and s['franja'] in self.datos.franjas and self.estado_celda_materia(a['materia'], s['dia'], s['franja']) == 'no_puede':
                alt['choques'].append(f'{self.datos.nombre_materia(a["materia"])} en {self.datos.nombre_curso(a["curso"])} '
                                      f'quedó el {nucleo.DIAS[s["dia"]]} a las {self.datos.franjas[s["franja"]]["inicio"]}, '
                                      'hora bloqueada para la materia.')
            area = a and self.datos.materias.get(a['materia'], {}).get('area')
            if area and s['franja'] in self.datos.franjas and self.estado_celda_area(area, s['dia'], s['franja']) == 'no_puede':
                alt['choques'].append(f'{self.datos.nombre_materia(a["materia"])} ({area}) en '
                                      f'{self.datos.nombre_curso(a["curso"])} quedó el {nucleo.DIAS[s["dia"]]} a las '
                                      f'{self.datos.franjas[s["franja"]]["inicio"]}, hora bloqueada para el área.')
        alt['choques'] += self._revisar_excluyente(alt)
        alt['choques'] += self._revisar_compensacion(alt)
        alt['choques'] += self._revisar_reuniones(alt)
        alt['avisos_salones'] = nucleo.asignar_salones(self.datos, self.cond, alt['sesiones'])
        alt['avisos_minimo'] = self.revisar_minimo(alt)
        faltan = nucleo.horas_faltantes(self.datos, alt['sesiones'], self.cond)
        alt['sin_ubicar'] = [{'asignacion': a['id'], 'horas': n} for a, n in faltan]
        alt['horas_sin_ubicar'] = sum(n for _, n in faltan)
        self.complementos(alt)
        return alt

    def minimo_docente(self, did):
        r = self.cond.get('docentes', {}).get(str(did), {})
        m = int(r.get('min_dia') or self.cond.get('min_dia_docente') or 0)
        return m if m > 1 else 0

    def revisar_minimo(self, alt):
        """Docentes que un día vienen a menos clases que su mínimo (es un aviso, no un choque)."""
        D = self.datos
        por = defaultdict(int)
        for s in alt['sesiones']:
            did = D.asignaciones.get(s['asignacion'], {}).get('docente')
            if did:
                por[(did, s['dia'])] += 1
        out = []
        for (did, dia), n in sorted(por.items(), key=lambda x: (D.nombre_docente(x[0][0]), x[0][1])):
            m = self.minimo_docente(did)
            if m and n < m:
                out.append(f'{D.nombre_docente(did)} tiene {n} clase(s) el {nucleo.DIAS[dia]} (mínimo {m}).')
        return out

    def _revisar_reuniones(self, alt):
        """Docentes con clase a la hora de su reunión de área."""
        D = self.datos
        ocupadas = nucleo.franjas_de_reuniones(D, alt.get('reuniones'))
        if not ocupadas:
            return []
        out = []
        for s in alt['sesiones']:
            did = D.asignaciones.get(s['asignacion'], {}).get('docente')
            if did and s['franja'] in ocupadas.get((did, s['dia']), ()):
                out.append(f'{D.nombre_docente(did)} tiene clase en {D.nombre_curso(s["curso"])} a la hora de su '
                           f'reunión de área ({nucleo.DIAS[s["dia"]]} {D.franjas[s["franja"]]["inicio"]}).')
        return out

    def _revisar_excluyente(self, alt):
        """Docentes que quedaron con las dos horas excluyentes el mismo día (si la regla es obligatoria)."""
        regla = nucleo.regla_excluyente(self.cond)
        if not regla or not regla[2]:
            return []
        a, b, _ = regla
        D = self.datos
        por = defaultdict(list)
        for s in alt['sesiones']:
            x = D.asignaciones.get(s['asignacion'])
            if x and x.get('docente') and s['franja'] in D.franjas:
                por[(x['docente'], s['dia'], D.franjas[s['franja']]['jornada'])].append(s['franja'])
        for (did, dia), fs in nucleo.franjas_de_reuniones(D, alt.get('reuniones')).items():
            for f in fs:
                por[(did, dia, D.franjas[f]['jornada'])].append(f)
        out = []
        for (did, dia, _), fs in por.items():
            if self.docente(did).get('sin_excluyente') or self.extra_docente(did) or self.compensa_docente(did):
                continue
            if any(self._es_hora(f, a) for f in fs) and any(self._es_hora(f, b) for f in fs):
                out.append(f'{D.nombre_docente(did)} tiene la hora {a} y la hora {b} el {nucleo.DIAS[dia]}.')
        return out

    def complementos(self, alt):
        """Actividades complementarias y turnos de descanso (se recalculan con cada cambio)."""
        alt['actividades'], av1 = nucleo.ubicar_actividades(self.datos, self.cond, alt['sesiones'], alt.get('reuniones'))
        alt['acompanamientos'], av2 = nucleo.asignar_acompanamientos(self.datos, self.cond, alt['sesiones'])
        alt['avisos_extra'] = av1 + av2
        return alt

    def generar(self, cuantas=3, segundos=60, avance=None, base=None, vivo=None, parar=None):
        """Genera alternativas (cada una con otra semilla), respetando las fichas fijadas de `base`.

        vivo(sesiones, nombre): lo que va ubicando; parar(): detener y quedarse con lo que lleve."""
        cond = self._cond_con_fijas(base)
        nuevas = []
        for k in range(cuantas):
            if nuevas and parar and parar():
                break
            def av(p, k=k):
                if avance:
                    avance(int((k + p / 100) * 100 / cuantas), f'Alternativa {k + 1} de {cuantas}…')
            vv = (lambda ses, k=k: vivo(ses, f'Alternativa {k + 1}')) if vivo else None
            nuevas.append(self._correr(cond, segundos, int(time.time()) + k * 7919, av, vv, parar))
        self.alternativas = [a for a in self.alternativas if a.get('manual')]
        nuevas.sort(key=lambda r: (r['horas_sin_ubicar'], len(r['choques']), r['costo']))
        for i, r in enumerate(nuevas, start=1):
            r['nombre'] = f'Alternativa {i}'
        self.alternativas = nuevas + self.alternativas
        if avance:
            avance(100, 'Listo')
        return nuevas

    def completar(self, alt, segundos=30, avance=None, solo_fijadas=False, vivo=None, parar=None):
        """Deja quietas las fichas puestas (o solo las fijadas) y ubica lo que falta."""
        cond = self._cond_con_fijas(alt, todas=not solo_fijadas)
        r = self._correr(cond, segundos, int(time.time()),
                         (lambda p: avance(p, 'Completando…')) if avance else None,
                         (lambda ses: vivo(ses, 'Completando')) if vivo else None, parar)
        # Las que ya estaban se respetaron, pero solo quedan fijadas 🔒 las que el usuario había fijado
        candado = {(s['asignacion'], s['dia'], s['franja']) for s in alt['sesiones'] if s.get('fijada')}
        for s in r['sesiones']:
            s['fijada'] = (s['asignacion'], s['dia'], s['franja']) in candado
        r['nombre'] = f"{alt.get('nombre', 'Horario')} (completado)"
        self.alternativas.insert(0, r)
        if avance:
            avance(100, 'Listo')
        return r

    def horas_totales(self):
        return sum(self.datos.ih(aid, self.cond) for aid in self.datos.asignaciones)

    def en_vivo(self, sesiones, nombre='Generando'):
        """Un horario provisional (solo para mirar) con lo que el generador lleva ubicado."""
        alt = {'nombre': f'⏳ {nombre}…', 'vivo': True, 'sesiones': [dict(x, fijada=x.get('fijada', False)) for x in sesiones],
               'costo': None, 'huecos': None, 'reuniones': [], 'divididas': [], 'choques': [],
               'actividades': [], 'acompanamientos': [], 'avisos_extra': []}
        faltan = nucleo.horas_faltantes(self.datos, alt['sesiones'], self.cond)
        alt['sin_ubicar'] = [{'asignacion': a['id'], 'horas': n} for a, n in faltan]
        alt['horas_sin_ubicar'] = sum(n for _, n in faltan)
        return alt

    def fijar_varias(self, alt, indices=None, fijar=False):
        """Suelta (o fija) varias fichas a la vez; indices=None = todas. Devuelve cuántas cambiaron."""
        n = 0
        for k, s in enumerate(alt['sesiones']):
            if indices is not None and k not in indices:
                continue
            if bool(s.get('fijada')) != fijar:
                s['fijada'] = fijar
                n += 1
        return n

    def en_blanco(self):
        alt = {'nombre': f'Horario a mano {sum(1 for a in self.alternativas if a.get("manual")) + 1}', 'manual': True,
               'sesiones': [dict(f, curso=self.datos.asignaciones[int(f['asignacion'])]['curso'], fijada=True,
                                 asignacion=int(f['asignacion']), dia=int(f['dia']), franja=int(f['franja']))
                            for f in self.cond['fijas'] if int(f['asignacion']) in self.datos.asignaciones],
               'costo': None, 'huecos': None, 'reuniones': self.ver_reuniones(), 'divididas': []}
        self.revisar(alt)
        self.alternativas.insert(0, alt)
        return alt

    # --- Editar a mano (fichas) -------------------------------------------------
    def pendientes(self, alt, cid):
        """[(asignación, horas por ubicar)] del curso."""
        hechas = defaultdict(int)
        for s in alt['sesiones']:
            hechas[s['asignacion']] += 1
        return [(a, self.datos.ih(a['id'], self.cond) - hechas[a['id']]) for a in self.asignaciones_de_curso(cid)
                if self.datos.ih(a['id'], self.cond) - hechas[a['id']] > 0]

    def pendientes_docente(self, alt, did):
        """[(asignación, horas por ubicar)] del docente, para armar el horario desde su vista."""
        D = self.datos
        hechas = defaultdict(int)
        for s in alt['sesiones']:
            hechas[s['asignacion']] += 1
        orden = {c['id']: i for i, c in enumerate(D.crudo['cursos'])}
        mias = sorted((a for a in D.asignaciones.values() if a.get('docente') == did and a['curso'] in D.jornada_de_curso),
                      key=lambda a: (orden.get(a['curso'], 0), D.nombre_materia(a['materia'])))
        return [(a, D.ih(a['id'], self.cond) - hechas[a['id']]) for a in mias
                if D.ih(a['id'], self.cond) - hechas[a['id']] > 0]

    def motivo(self, alt, aid, dia, fid, ignorar=None):
        """None si la ficha cabe ahí; si no, por qué."""
        D = self.datos
        a = D.asignaciones[aid]
        jid = D.jornada_de_curso.get(a['curso'])
        if jid is None or fid not in {f['id'] for f in D.jornadas[jid]['franjas'] if not f['descanso']}:
            return 'Esa hora no es de la jornada del curso.'
        if dia not in D.jornadas[jid]['dias']:
            return 'Ese día no hay clases en la jornada del curso.'
        if self.celda_curso(a['curso'], dia, fid):
            return f'{D.nombre_curso(a["curso"])} no tiene clase a esa hora (marcado en Docentes y cursos).'
        m = self._motivo_salon(alt, a, dia, fid, ignorar)
        if m:
            return m
        if self.estado_celda_materia(a['materia'], dia, fid) == 'no_puede':
            return f'{D.nombre_materia(a["materia"])} no va a esa hora (bloqueado en Materias).'
        area = D.materias.get(a['materia'], {}).get('area')
        if area and self.estado_celda_area(area, dia, fid) == 'no_puede':
            return f'Las clases de {area} no van a esa hora (bloqueado por área en Docentes y cursos).'
        ign = set(ignorar) if isinstance(ignorar, (set, list, tuple)) else {ignorar}
        otras = [s for i, s in enumerate(alt['sesiones']) if i not in ign]
        ini, fin = D.intervalo(fid)
        for s in otras:
            if s['dia'] != dia:
                continue
            b = D.asignaciones.get(s['asignacion'])
            if b is None:
                continue
            if b['curso'] == a['curso'] and s['franja'] == fid:
                return f'{D.nombre_curso(a["curso"])} ya tiene {D.nombre_materia(b["materia"])} a esa hora.'
            x, y = D.intervalo(s['franja'])
            if a.get('docente') and b.get('docente') == a['docente'] and x < fin and ini < y:
                if self._juntos(a, b) and s['franja'] == fid:
                    continue                 # multigrado: es la misma clase con otro curso del grupo
                return f'{D.nombre_docente(a["docente"])} ya está en {D.nombre_curso(b["curso"])} a esa hora.'
        did = a.get('docente')
        if did:
            if self.estado_celda(did, dia, fid) == 'no_puede':
                return f'{D.nombre_docente(did)} no puede a esa hora.'
            for r in alt.get('reuniones') or []:
                for reu in (r, r.get('segunda') or {}):
                    if reu.get('dia') == dia and did in reu.get('asisten', []) and reu['inicio'] < fin and ini < reu['fin']:
                        return f'{D.nombre_docente(did)} tiene {r["nombre"]} a esa hora.'
            extra = self._es_extra(alt, aid, otras)
            perm = self.docente(did).get('permanencia')
            perm = float(perm) if perm not in (None, '') else float(self.cond.get('permanencia_horas') or 0)
            mias = [(D.intervalo(s['franja']), s) for s in otras
                    if s['dia'] == dia and D.asignaciones.get(s['asignacion'], {}).get('docente') == did]
            reus = nucleo.franjas_de_reuniones(D, alt.get('reuniones')).get((did, dia), [])
            mas = self.docente(did).get('permanencia_extra')
            mas = float(mas) if mas not in (None, '') else float(self.cond.get('permanencia_extra') or 0)
            if perm and mas and any(nucleo.horas_extra(self.cond, x['id'], D.ih(x['id'], self.cond))
                                    for x in D.asignaciones.values() if x.get('docente') == did):
                todo = [t for t, s in mias] + [D.intervalo(x) for x in reus] + [(ini, fin)]
                if max(b for _, b in todo) - min(x for x, _ in todo) > (perm + mas) * 60:
                    return (f'Ni con las horas extra cabe: se pasa de {perm:g} + {mas:g} horas de '
                            f'{D.nombre_docente(did)} ese día.')
            if perm and not extra:
                tramos = [t for t, s in mias if not (nucleo.horas_extra(self.cond, s['asignacion'], D.ih(s['asignacion'], self.cond))
                                                     >= D.ih(s['asignacion'], self.cond) > 0)]
                tramos += [D.intervalo(x) for x in reus]       # las reuniones de área van dentro de la permanencia
                tramos.append((ini, fin))
                comp = self.compensa_docente(did)
                ancho = max(b for _, b in tramos) - min(x for x, _ in tramos)
                if ancho > perm * 60 + (comp or 0):
                    if comp:
                        return (f'Se pasa de {perm:g} + {comp / 60:g} horas de permanencia de {D.nombre_docente(did)} '
                                'ese día (ni compensando con otro día).')
                    return f'Se pasa de las {perm:g} horas de permanencia de {D.nombre_docente(did)} ese día.'
            k_extra = self.extra_docente(did)
            m = self._motivo_excluyente(did, dia, fid, [(None, {'franja': x}) for x in reus] + mias)
            if m and not k_extra and not self.compensa_docente(did):
                return m
            # Días largos: uno por cada hora extra del docente
            if k_extra:
                franjas_hoy = [s['franja'] for _, s in mias] + list(reus)
                antes = self._dia_largo(did, franjas_hoy)
                despues = self._dia_largo(did, franjas_hoy + [fid])
                if despues and not antes:
                    usados = sum(1 for d in {s['dia'] for s in otras if s['dia'] != dia} if self._dia_largo(
                        did, [s['franja'] for s in otras if s['dia'] == d and
                              D.asignaciones.get(s['asignacion'], {}).get('docente') == did] +
                        nucleo.franjas_de_reuniones(D, alt.get('reuniones')).get((did, d), [])))
                    if usados >= k_extra:
                        return (f'{D.nombre_docente(did)} ya tiene {usados} día(s) largo(s) (uno por cada hora extra): '
                                'no le caben más.')
            despl = int(self.cond.get('desplazamiento') or 0)
            sede = D.sede_de_curso(a['curso'])
            for (x, y), s in mias:
                otra = D.sede_de_curso(D.asignaciones[s['asignacion']]['curso'])
                if despl and sede and otra and otra != sede:
                    hueco = ini - y if y <= ini else x - fin
                    if hueco < despl:
                        return f'No le da tiempo de pasar de {otra} a {sede} ({despl} min).'
        regla = self.regla(a['materia'])
        tope = int(regla.get('max_dia') or self.cond.get('max_por_dia') or 2)
        partes = (nucleo.patron(self.asig(aid).get('bloques')) or nucleo.patron(regla.get('bloques'))
                  or nucleo.bloques_por_defecto(self.cond, D.ih(aid, self.cond)) or [1])
        tope = max(tope, max(partes))
        ese_dia = sum(1 for s in otras if s['dia'] == dia and D.asignaciones.get(s['asignacion'], {}).get('curso') == a['curso']
                      and D.asignaciones.get(s['asignacion'], {}).get('materia') == a['materia'])
        if ese_dia + 1 > tope:
            return f'{D.nombre_materia(a["materia"])} ya tiene {ese_dia} hora(s) ese día (máximo {tope}).'
        return None

    def extra_docente(self, did):
        """Cuántas horas extra tiene el docente (= cuántos días largos puede tener)."""
        D = self.datos
        return sum(nucleo.horas_extra(self.cond, a['id'], D.ih(a['id'], self.cond))
                   for a in D.asignaciones.values() if a.get('docente') == did)

    def _dia_largo(self, did, franjas):
        """¿Con esas horas el día pasa de la permanencia o tiene la 1.ª y la última (si esa regla está)?"""
        D = self.datos
        fs = [f for f in franjas if f in D.franjas]
        if not fs:
            return False
        perm = self.docente(did).get('permanencia')
        perm = float(perm) if perm not in (None, '') else float(self.cond.get('permanencia_horas') or 0)
        tramos = [D.intervalo(f) for f in fs]
        if perm and max(b for _, b in tramos) - min(a for a, _ in tramos) > perm * 60:
            return True
        regla = nucleo.regla_excluyente(self.cond)
        if regla and regla[2] and not self.docente(did).get('sin_excluyente'):
            a, b, _ = regla
            for x in fs:
                for y in fs:
                    if (D.franjas[x]['jornada'] == D.franjas[y]['jornada'] and self._es_hora(x, a)
                            and self._es_hora(y, b)):
                        return True
        return False

    def _numero_hora(self, fid):
        """(número de la hora de clase desde 1, cuántas horas de clase tiene esa jornada)."""
        f = self.datos.franjas[fid]
        clase = [x['id'] for x in self.datos.franjas_de(f['jornada']) if not x['descanso']]
        return (clase.index(fid) + 1 if fid in clase else 0), len(clase)

    def _es_hora(self, fid, n):
        k, total = self._numero_hora(fid)
        return k == min(n, total)

    # --- Compensar días largos (docentes sin horas extra) -----------------------------
    def compensa_docente(self, did):
        """Minutos que un día puede pasar de la permanencia si otro día lo compensa (None si no aplica)."""
        comp = self.cond.get('compensar') or {}
        if not comp.get('activa') or not did or self.extra_docente(did) or not self._permanencia(did):
            return None
        return int(float(comp.get('max') or 1) * 60)

    def _permanencia(self, did):
        perm = self.docente(did).get('permanencia')
        return float(perm) if perm not in (None, '') else float(self.cond.get('permanencia_horas') or 0)

    def perfil_docente(self, alt, did, sesiones=None):
        """{dia: (minutos desde la primera hasta la última, ¿tiene la 1.ª y la última?)}, con reuniones."""
        D = self.datos
        por = defaultdict(list)
        for s in (alt['sesiones'] if sesiones is None else sesiones):
            if s['franja'] in D.franjas and D.asignaciones.get(s['asignacion'], {}).get('docente') == did:
                por[s['dia']].append(s['franja'])
        for (d, dia), fs in nucleo.franjas_de_reuniones(D, alt.get('reuniones')).items():
            if d == did:
                por[dia] += [f for f in fs if f in D.franjas]
        regla = nucleo.regla_excluyente(self.cond)
        duro = bool(regla and regla[2] and not self.docente(did).get('sin_excluyente'))
        salida = {}
        for dia, fs in por.items():
            tramos = [D.intervalo(f) for f in fs]
            ancho = max(b for _, b in tramos) - min(a for a, _ in tramos)
            par = duro and any(D.franjas[x]['jornada'] == D.franjas[y]['jornada'] and self._es_hora(x, regla[0])
                               and self._es_hora(y, regla[1]) for x in fs for y in fs)
            salida[dia] = (ancho, par)
        return salida

    def semana_docente(self, alt, did):
        """(total de la semana, tope = permanencia × días, perfil {dia: (minutos, par)}) en minutos."""
        D = self.datos
        perfil = self.perfil_docente(alt, did)
        dias = {d for jid in D.jornadas_de_docente(did) for d in D.jornadas[jid]['dias']} or set(perfil)
        tope = int(self._permanencia(did) * 60) * max(1, len(dias))
        return sum(a for a, _ in perfil.values()), tope, perfil

    def _revisar_compensacion(self, alt):
        D = self.datos
        out = []
        for did in sorted({a.get('docente') for a in D.asignaciones.values() if a.get('docente')}):
            comp = self.compensa_docente(did)
            if comp is None:
                continue
            total, tope, perfil = self.semana_docente(alt, did)
            perm = self._permanencia(did)
            for d, (a, _) in perfil.items():
                if a > perm * 60 + comp:
                    out.append(f'{D.nombre_docente(did)}: el {nucleo.DIAS[d]} pasa de {perm:g} + '
                               f'{comp / 60:g} horas de permanencia.')
            max_dias = nucleo.max_dias_largos(self.cond, did)
            largos = sum(1 for a, par in perfil.values() if a > perm * 60 or par)
            if max_dias is not None and largos > max_dias:
                out.append(f'{D.nombre_docente(did)}: tiene {largos} días largos y el máximo es {max_dias}.')
            if total > tope:
                out.append(f'{D.nombre_docente(did)}: la semana suma {texto_horas(total)} de permanencia y el máximo '
                           f'es {texto_horas(tope)} ({perm:g} h × {tope // int(perm * 60)} días). Acorte algún día.')
        return out

    def texto_compensacion(self, alt):
        """Para los avisos: docentes con días largos y cómo queda su semana."""
        D = self.datos
        out = []
        for did in sorted({a.get('docente') for a in D.asignaciones.values() if a.get('docente')}, key=D.nombre_docente):
            if self.compensa_docente(did) is None:
                continue
            total, tope, perfil = self.semana_docente(alt, did)
            perm = self._permanencia(did) * 60
            largos = [d for d, (a, par) in sorted(perfil.items()) if a > perm or par]
            if not largos:
                continue
            cortos = [d for d, (a, par) in sorted(perfil.items()) if a < perm and not par]
            t = (f'{D.nombre_docente(did)}: {texto_horas(total)} de {texto_horas(tope)} · largos: '
                 + ', '.join(f'{nucleo.DIAS[d]} {texto_horas(perfil[d][0])}' for d in largos))
            if cortos:
                t += ' · cortos: ' + ', '.join(f'{nucleo.DIAS[d]} {texto_horas(perfil[d][0])}' for d in cortos)
            out.append(t + (' ✖ se pasa' if total > tope else ''))
        return out

    def texto_viajan(self, alt):
        """Docentes que no viven en el municipio y tienen días largos: dónde quedó la compensación."""
        D = self.datos
        out = []
        for did, r in sorted(self.cond.get('docentes', {}).items(), key=lambda x: D.nombre_docente(int(x[0]))):
            did = int(did)
            if not r.get('viaja') or did not in D.docentes:
                continue
            perm = self._permanencia(did) * 60
            perfil = self.perfil_docente(alt, did)
            exceso = sum(max(0, a - perm) for a, _ in perfil.values())
            if not perm or not exceso:
                continue
            dias = sorted({d for jid in D.jornadas_de_docente(did) for d in D.jornadas[jid]['dias']})
            modo = nucleo.modo_viaja(r.get('viaja'))
            partes = []
            for d, primero in ((dias[0], True), (dias[-1], False)):
                if (primero and modo == 'viernes') or (not primero and modo == 'lunes'):
                    continue
                fs = [s['franja'] for s in alt['sesiones'] if s['dia'] == d and s['franja'] in D.franjas
                      and D.asignaciones.get(s['asignacion'], {}).get('docente') == did]
                if not fs:
                    partes.append(f'{nucleo.DIAS[d]} no viene')
                    continue
                orden = [f['id'] for f in D.franjas_de(D.franjas[fs[0]]['jornada']) if not f['descanso']]
                idx = [orden.index(f) for f in fs if f in orden]
                if primero and min(idx):
                    partes.append(f'{nucleo.DIAS[d]} entra a la {min(idx) + 1}.ª hora')
                elif not primero and max(idx) < len(orden) - 1:
                    partes.append(f'{nucleo.DIAS[d]} sale después de la {max(idx) + 1}.ª hora')
            pide = {'lunes': 'prefiere el lunes', 'viernes': 'prefiere el viernes', 'ambos': 'lunes o viernes'}[modo]
            out.append(f'{D.nombre_docente(did)} (viaja, {pide}): días largos suman {texto_horas(exceso)} de más · '
                       + (', '.join(partes) if partes else 'no quedó compensado ahí'))
        return out

    def _motivo_excluyente(self, did, dia, fid, mias):
        regla = nucleo.regla_excluyente(self.cond)
        if not regla or not regla[2] or self.docente(did).get('sin_excluyente'):
            return None
        a, b, _ = regla
        for _, s in mias:
            otra = s['franja']
            if self.datos.franjas[otra]['jornada'] != self.datos.franjas[fid]['jornada']:
                continue
            if (self._es_hora(fid, a) and self._es_hora(otra, b)) or (self._es_hora(fid, b) and self._es_hora(otra, a)):
                return (f'{self.datos.nombre_docente(did)} ya tiene la hora {b if self._es_hora(otra, b) else a} ese día: '
                        f'no puede tener también la {a if self._es_hora(otra, b) else b}.')
        return None

    # --- Multigrado (Escuela Nueva) -----------------------------------------------
    def _juntos(self, a, b):
        """¿Las dos clases son la misma clase multigrado (cursos del mismo grupo, mismo docente y materia)?"""
        g = nucleo.grupos_multigrado(self.cond)
        return (a['curso'] != b['curso'] and a['curso'] in g and g.get(b['curso']) == g[a['curso']]
                and a.get('docente') and a.get('docente') == b.get('docente') and a['materia'] == b['materia'])

    def companeros(self, aid):
        """Las clases de los otros cursos del grupo multigrado que van junto con esta."""
        D = self.datos
        a = D.asignaciones[aid]
        return [b['id'] for b in D.asignaciones.values() if b['id'] != aid and self._juntos(a, b)]

    def agregar_multigrado(self, nombre, cursos):
        cursos = sorted({int(c) for c in cursos})
        if len(cursos) < 2:
            return 'Escoja al menos dos cursos.'
        ya = {c for g in self.cond['multigrado'] for c in g.get('cursos', [])}
        if ya & set(cursos):
            return 'Uno de esos cursos ya está en otro grupo multigrado.'
        self.cond['multigrado'].append({'nombre': nombre or 'Multigrado', 'cursos': cursos})
        return None

    def _es_extra(self, alt, aid, otras=None):
        """¿La próxima hora de esa clase cuenta como extra? Las primeras horas puestas son de clase y
        las últimas (hasta completar las horas extra escogidas) son extra."""
        D = self.datos
        ih = D.ih(aid, self.cond)
        k = nucleo.horas_extra(self.cond, aid, ih)
        if not k:
            return False
        if k >= ih:
            return True
        puestas = sum(1 for s in (otras if otras is not None else alt['sesiones']) if s['asignacion'] == aid)
        return puestas >= ih - k

    def poner_ficha(self, alt, aid, dia, fid, fijar=True):
        m = self.motivo(alt, aid, dia, fid)
        if m:
            return m
        alt['sesiones'].append({'asignacion': aid, 'curso': self.datos.asignaciones[aid]['curso'], 'dia': dia,
                                'franja': fid, 'fijada': fijar})
        # Multigrado: los otros cursos del grupo quedan en la misma hora, con la misma clase
        hechas = defaultdict(int)
        for s in alt['sesiones']:
            hechas[s['asignacion']] += 1
        for b in self.companeros(aid):
            if hechas[b] < self.datos.ih(b, self.cond) and not self.motivo(alt, b, dia, fid):
                alt['sesiones'].append({'asignacion': b, 'curso': self.datos.asignaciones[b]['curso'], 'dia': dia,
                                        'franja': fid, 'fijada': fijar})
        self.revisar(alt)
        return None

    def _juntas_en(self, alt, i):
        """Índices de las fichas multigrado que están en la misma hora que la ficha i."""
        s = alt['sesiones'][i]
        comp = set(self.companeros(s['asignacion']))
        return [k for k, x in enumerate(alt['sesiones']) if k != i and x['asignacion'] in comp
                and x['dia'] == s['dia'] and x['franja'] == s['franja']]

    def mover_ficha(self, alt, i, dia, fid, fijar=True):
        s = alt['sesiones'][i]
        juntas = self._juntas_en(alt, i)
        todas = {i, *juntas}
        m = self.motivo(alt, s['asignacion'], dia, fid, ignorar=todas)
        if m:
            return m
        for k in juntas:
            if self.motivo(alt, alt['sesiones'][k]['asignacion'], dia, fid, ignorar=todas):
                juntas = [x for x in juntas if x != k]
        s.update(dia=dia, franja=fid, fijada=fijar or s.get('fijada', False))
        for k in juntas:                      # multigrado: el grupo se mueve junto
            alt['sesiones'][k].update(dia=dia, franja=fid, fijada=fijar or alt['sesiones'][k].get('fijada', False))
        self.revisar(alt)
        return None

    # --- Colores al escoger una ficha: verde, amarillo, rojo -----------------------
    def estorbos(self, alt, aid, dia, fid, ignorar=()):
        """Índices de las fichas que ocupan ese lugar para esa clase (mismo curso a esa hora, o el
        mismo docente en una hora que se cruza)."""
        D = self.datos
        a = D.asignaciones[aid]
        if fid not in D.franjas:
            return []
        ini, fin = D.intervalo(fid)
        out = []
        for k, x in enumerate(alt['sesiones']):
            if k in ignorar or x['dia'] != dia:
                continue
            b = D.asignaciones.get(x['asignacion'], {})
            if b.get('curso') == a['curso'] and x['franja'] == fid:
                out.append(k)
            elif a.get('docente') and b.get('docente') == a['docente'] and x['franja'] in D.franjas:
                if self._juntos(a, b) and x['franja'] == fid:
                    continue
                y0, y1 = D.intervalo(x['franja'])
                if y0 < fin and ini < y1:
                    out.append(k)
        return out

    def destino(self, alt, aid, dia, fid, i=None, ignorar_tambien=()):
        """Qué pasa si la clase `aid` (o la ficha i) va a (dia, fid):

        ('libre', '', [])           -> verde: cabe.
        ('ocupado', texto, [k…])    -> amarillo: la ocupan fichas que se pueden quitar (reemplazar o intercambiar).
        ('imposible', texto, [k…])  -> rojo: hay una ficha fijada 🔒 o una condición que no se puede romper.
        """
        D = self.datos
        ign = ({i} if i is not None else set()) | set(ignorar_tambien)
        m = self.motivo(alt, aid, dia, fid, ignorar=ign)
        if not m:
            return 'libre', '', []
        est = self.estorbos(alt, aid, dia, fid, ign)
        if not est:
            return 'imposible', m, []
        fijas = [k for k in est if alt['sesiones'][k].get('fijada')]
        if fijas:
            x = D.asignaciones[alt['sesiones'][fijas[0]]['asignacion']]
            return 'imposible', (f'Ahí está {D.nombre_materia(x["materia"])} de {D.nombre_curso(x["curso"])} '
                                 f'({D.nombre_docente(x.get("docente"))}), fijada 🔒.'), est
        m2 = self.motivo(alt, aid, dia, fid, ignorar=ign | set(est))
        if m2:
            return 'imposible', m2, est
        nombres = []
        for k in est:
            x = D.asignaciones[alt['sesiones'][k]['asignacion']]
            nombres.append(f'{D.nombre_materia(x["materia"])} de {D.nombre_curso(x["curso"])} ({D.nombre_docente(x.get("docente"))})')
        return 'ocupado', 'Ocupada por ' + ' y '.join(nombres) + '.', est

    def mapa_destinos(self, alt, aid, i=None, largo=1):
        """{(dia, franja): estado} de todas las horas de clase, para pintar la cuadrícula."""
        out = {}
        for j in self.datos.jornadas.values():
            for f in j['franjas']:
                if f['descanso']:
                    continue
                for dia in j['dias']:
                    if largo > 1:
                        out[(dia, f['id'])] = self.destino_bloque(alt, aid, dia, f['id'], largo)[0]
                    else:
                        out[(dia, f['id'])] = self.destino(alt, aid, dia, f['id'], i)[0]
        return out

    def reemplazar(self, alt, aid, dia, fid, i=None, fijar=True, largo=1):
        """Pone la clase en (dia, fid) y saca las fichas que estorban (vuelven a «por ubicar»)."""
        if largo > 1:
            estado, texto, est = self.destino_bloque(alt, aid, dia, fid, largo)
        else:
            estado, texto, est = self.destino(alt, aid, dia, fid, i)
        if estado == 'imposible':
            return texto
        for k in sorted(est, reverse=True):
            del alt['sesiones'][k]
            if i is not None and k < i:
                i -= 1
        if largo > 1:
            return self.poner_bloque(alt, aid, dia, fid, largo, fijar)
        if i is None:
            return self.poner_ficha(alt, aid, dia, fid, fijar)
        return self.mover_ficha(alt, i, dia, fid, fijar)

    # --- Bloques (2 horas seguidas, etc.) -------------------------------------------
    def _siguientes(self):
        cruzar = nucleo.bloque_cruza_descanso(self.cond)
        if getattr(self, '_sig', None) is None or self._sig_cruza != cruzar:
            self._sig = nucleo.siguientes(self.datos, cruzar)
            self._sig_cruza = cruzar
        return self._sig

    def hay_bloques(self):
        return any(max(self.partes_asig(a) or [1]) > 1 for a in self.datos.asignaciones)

    def celdas_bloque(self, fid, largo):
        """[fid, la siguiente, …] o None si el bloque se cruza con un descanso o el fin de la jornada."""
        out = [fid]
        sig = self._siguientes()
        while len(out) < largo:
            nxt = sig.get(out[-1])
            if not nxt:
                return None
            out.append(nxt)
        return out

    def partes_asig(self, aid):
        return nucleo.partes_completas(self.datos, self.cond, self.datos.asignaciones[aid])

    def piezas_pendientes(self, alt, aid):
        """Los bloques que faltan de esa clase, sin importar en qué orden se pusieron los otros.
        Ej.: 3 horas en 2+1 y ya está la hora suelta -> falta [2]."""
        puestas = [(s['dia'], s['franja']) for s in alt['sesiones'] if s['asignacion'] == aid]
        return nucleo.restar_corridas(self.partes_asig(aid), nucleo.corridas(puestas, self._siguientes()))

    def destino_bloque(self, alt, aid, dia, fid, largo):
        """Como destino(), pero para un bloque de varias horas que empieza en fid."""
        cs = self.celdas_bloque(fid, largo)
        if not cs:
            return 'imposible', f'El bloque de {largo} horas no cabe ahí (se cruza con el descanso o el final de la jornada).', []
        temp = {'sesiones': list(alt['sesiones']), 'reuniones': alt.get('reuniones')}
        cid = self.datos.asignaciones[aid]['curso']
        peor, textos, est_todos = 'libre', [], []
        for c in cs:
            estado, texto, est = self.destino(temp, aid, dia, c, ignorar_tambien=est_todos)
            if estado == 'imposible':
                return 'imposible', texto, est
            if estado == 'ocupado':
                peor = 'ocupado'
                textos.append(texto)
                est_todos += [k for k in est if k not in est_todos]
            temp['sesiones'].append({'asignacion': aid, 'curso': cid, 'dia': dia, 'franja': c, 'fijada': False})
        return peor, ' '.join(textos), est_todos

    def poner_bloque(self, alt, aid, dia, fid, largo, fijar=True):
        if largo <= 1:
            return self.poner_ficha(alt, aid, dia, fid, fijar)
        estado, texto, _ = self.destino_bloque(alt, aid, dia, fid, largo)
        if estado != 'libre':
            return texto
        cid = self.datos.asignaciones[aid]['curso']
        for c in self.celdas_bloque(fid, largo):
            alt['sesiones'].append({'asignacion': aid, 'curso': cid, 'dia': dia, 'franja': c, 'fijada': fijar})
        self.revisar(alt)
        return None

    def dividir_en_bloques(self, sobrescribir=False):
        """Pone bloques de 2 horas (2+2+1…) a las clases que no tienen bloques. Devuelve cuántas."""
        n = 0
        for a in self.datos.asignaciones.values():
            r = self.asig(a['id'])
            regla = self.cond['materias'].get(str(a['materia']), {})
            if not sobrescribir and (r.get('bloques') or regla.get('bloques')):
                continue
            t = nucleo.bloques_automaticos(self.datos.ih(a['id'], self.cond))
            if t and r.get('bloques') != t:
                r['bloques'] = t
                n += 1
        return n

    def quitar_bloques(self):
        n = 0
        for r in self.cond['asignaciones'].values():
            if r.get('bloques'):
                r['bloques'] = ''
                n += 1
        return n

    def intercambiar(self, alt, i, dia, fid):
        """Mueve la ficha i a (dia, fid) y la que estorba ahí (del mismo curso o del mismo docente)
        pasa a donde estaba i."""
        D = self.datos
        s = alt['sesiones'][i]
        a = D.asignaciones[s['asignacion']]
        ini, fin = D.intervalo(fid)

        def estorba(x):
            b = D.asignaciones.get(x['asignacion'], {})
            if x['dia'] != dia:
                return False
            if b.get('curso') == a['curso'] and x['franja'] == fid:
                return True
            if a.get('docente') and b.get('docente') == a['docente'] and x['franja'] in D.franjas:
                y0, y1 = D.intervalo(x['franja'])
                return y0 < fin and ini < y1
            return False
        j = next((k for k, x in enumerate(alt['sesiones']) if k != i and estorba(x)), None)
        if j is None:
            return 'No hay otra ficha en esa hora para intercambiar.'
        t = alt['sesiones'][j]
        d0, f0 = s['dia'], s['franja']
        m = self.motivo(alt, s['asignacion'], dia, fid, ignorar={i, j})
        if m:
            return m
        prueba = {'sesiones': [x for k, x in enumerate(alt['sesiones']) if k not in (i, j)] +
                  [dict(s, dia=dia, franja=fid)], 'reuniones': alt.get('reuniones')}
        m = self.motivo(prueba, t['asignacion'], d0, f0)
        if m:
            return 'La otra ficha no puede pasar: ' + m
        s.update(dia=dia, franja=fid, fijada=True)
        t.update(dia=d0, franja=f0, fijada=True)
        self.revisar(alt)
        return None

    def quitar_ficha(self, alt, i):
        for k in sorted([i] + self._juntas_en(alt, i), reverse=True):
            del alt['sesiones'][k]
        self.revisar(alt)

    def alternar_fijada(self, alt, i):
        alt['sesiones'][i]['fijada'] = not alt['sesiones'][i].get('fijada')
        return alt['sesiones'][i]['fijada']

    # Compatibilidad: fijar una clase antes de generar
    def agregar_fija(self, aid, dia, fid):
        alt = {'sesiones': [{'asignacion': int(f['asignacion']), 'curso': self.datos.asignaciones[int(f['asignacion'])]['curso'],
                             'dia': int(f['dia']), 'franja': int(f['franja'])} for f in self.cond['fijas']]}
        m = self.motivo(alt, aid, dia, fid)
        if m:
            return m
        if sum(1 for f in self.cond['fijas'] if int(f['asignacion']) == aid) >= self.datos.ih(aid, self.cond):
            return 'Esa materia ya tiene fijadas todas sus horas.'
        self.cond['fijas'].append({'asignacion': aid, 'dia': dia, 'franja': fid})
        return None

    def quitar_fija(self, i):
        del self.cond['fijas'][i]

    # --- Ver -------------------------------------------------------------------
    def _tabla(self, jid, celdas):
        j = self.datos.jornadas[jid]
        dias = [(d, nucleo.DIAS[d]) for d in j['dias']]
        filas = [(f, [celdas.get((d, f['id']), []) for d, _ in dias]) for f in self.datos.franjas_de(jid)]
        return {'jornada': j, 'dias': dias, 'filas': filas}

    def tabla_curso(self, alt, cid):
        D = self.datos
        jid = D.jornada_de_curso.get(cid)
        if jid is None:
            return None
        celdas = defaultdict(list)
        for i, s in enumerate(alt['sesiones']):
            a = D.asignaciones.get(s['asignacion'])
            if a and a['curso'] == cid:
                celdas[(s['dia'], s['franja'])].append({'i': i, 'titulo': D.nombre_materia(a['materia']),
                                                        'sub': D.nombre_docente(a.get('docente')) + self._en_salon(s),
                                                        'fijada': s.get('fijada', False), 'asig': a['id']})
        for x in alt.get('direccion') or []:
            if x['curso'] == cid:
                celdas[(x['dia'], x['franja'])].append({'i': None, 'titulo': 'Dirección de grado',
                                                        'sub': D.nombre_docente(x['docente']), 'fijada': True,
                                                        'actividad': True})
        return self._tabla(jid, celdas)

    def _en_salon(self, s):
        if not s.get('salon'):
            return ''
        return ' · ' + ((nucleo.salones_de(self.cond).get(str(s['salon'])) or {}).get('nombre') or str(s['salon']))

    def tabla_salon(self, alt, sid):
        """Cuadrículas (una por jornada) de lo que pasa en un salón."""
        D = self.datos
        tablas = []
        for jid in sorted(D.jornadas):
            ids = {f['id'] for f in D.franjas_de(jid)}
            celdas = defaultdict(list)
            for i, s in enumerate(alt['sesiones']):
                a = D.asignaciones.get(s['asignacion'])
                if a and str(s.get('salon')) == str(sid) and s['franja'] in ids:
                    celdas[(s['dia'], s['franja'])].append({'i': i, 'titulo': D.nombre_curso(a['curso']),
                                                            'sub': f'{D.nombre_materia(a["materia"])} · '
                                                                   f'{D.nombre_docente(a.get("docente"))}',
                                                            'fijada': s.get('fijada', False), 'asig': a['id']})
            if celdas or len(D.jornadas) == 1:
                tablas.append(self._tabla(jid, celdas))
        return tablas

    def tablas_docente(self, alt, did):
        D = self.datos
        tablas = []
        for j in self.jornadas_de_docente(did):
            celdas = defaultdict(list)
            ids = {f['id'] for f in j['franjas']}
            for i, s in enumerate(alt['sesiones']):
                a = D.asignaciones.get(s['asignacion'])
                if a and a.get('docente') == did and s['franja'] in ids:
                    celdas[(s['dia'], s['franja'])].append({'i': i, 'titulo': D.nombre_curso(a['curso']),
                                                            'sub': D.nombre_materia(a['materia']) + self._en_salon(s),
                                                            'fijada': s.get('fijada', False), 'asig': a['id']})
            for r in alt.get('reuniones') or []:
                for reu in (r, r.get('segunda') or {}):
                    if did in reu.get('asisten', []):
                        for f in j['franjas']:
                            x, y = nucleo.minutos(f['inicio']), nucleo.minutos(f['fin'])
                            if not f['descanso'] and x < reu['fin'] and reu['inicio'] < y:
                                celdas[(reu['dia'], f['id'])].append({'i': None, 'titulo': r['nombre'], 'sub': 'Reunión',
                                                                      'fijada': True, 'reunion': True})
            for x in alt.get('direccion') or []:
                if x['docente'] == did and x['franja'] in ids:
                    celdas[(x['dia'], x['franja'])].append({'i': None, 'titulo': D.nombre_curso(x['curso']),
                                                            'sub': 'Dirección de grado', 'fijada': True,
                                                            'actividad': True})
            for x in alt.get('actividades') or []:
                if x['docente'] == did and x['franja'] in ids:
                    celdas[(x['dia'], x['franja'])].append({'i': None, 'titulo': x['nombre'], 'sub': 'Actividad',
                                                            'fijada': True, 'actividad': True})
            for x in alt.get('acompanamientos') or []:
                if did in x['docentes'] and x['franja'] in ids:
                    celdas[(x['dia'], x['franja'])].append({'i': None, 'titulo': x['zona'], 'sub': 'Acompañamiento',
                                                            'fijada': True, 'descanso': True})
            tablas.append(self._tabla(j['id'], celdas))
        return tablas

    # --- Cuando faltan horas: qué aflojar y consejos --------------------------------
    CONSEJOS = [
        'Use «mejor no» en vez de «no puede» cuando no sea indispensable: el generador tiene más espacio.',
        'Dele más segundos: los horarios grandes o con muchas reglas necesitan más tiempo (2 a 5 minutos).',
        'Fije a mano lo más difícil (los docentes con poca disponibilidad o las clases en espacios compartidos) '
        'y deje que el generador complete el resto.',
        'Revise en «7. Asignación académica» que las horas de cada curso no pasen de las horas de su jornada.',
        'Si muchas clases van en bloques de 2 horas, permitir que un bloque se parta cuando no cabe ayuda bastante.',
    ]

    def sugerencias(self, alt):
        """Cambios concretos que pueden ayudar a ubicar lo que falta, de los más suaves a los más fuertes.

        Mira las clases que no se ubicaron y las que más costó ubicar. Cada sugerencia:
        {'clave', 'texto', 'tipo', 'datos'}; se aplica con aplicar_sugerencia()."""
        D, c = self.datos, self.cond
        ids = [x['asignacion'] for x in alt.get('sin_ubicar') or []]
        ids += [x['asignacion'] for x in alt.get('dificiles') or []][:6]
        vistas, out = set(), []
        if not ids:
            return out

        def sug(clave, texto, tipo, **datos):
            if clave not in vistas:
                vistas.add(clave)
                out.append({'clave': clave, 'texto': texto, 'tipo': tipo, 'datos': datos})
        regla_ex = nucleo.regla_excluyente(c)
        for aid in ids:
            a = D.asignaciones.get(aid)
            if not a:
                continue
            did, cid, mid = a.get('docente'), a['curso'], a['materia']
            nom_d, nom_c, nom_m = D.nombre_docente(did), D.nombre_curso(cid), D.nombre_materia(mid)
            r = c['asignaciones'].get(str(aid), {})
            partes = nucleo.partes_completas(D, c, a)
            if max(partes or [1]) > 1 and r.get('dividir') is False:
                sug(f'partir-{aid}', f'Dejar partir los bloques de {nom_m} {nom_c} si no caben', 'partir', aid=aid)
            if max(partes or [1]) > 1 and c.get('bloque_descanso') is False:
                sug('bloque-descanso', 'Permitir que un bloque quede partido por el descanso', 'bloque_descanso')
            if did:
                rd = c['docentes'].get(str(did), {})
                n_no = len(rd.get('no_puede', []))
                if n_no:
                    sug(f'nopuede-{did}', f'Cambiar las {n_no} horas «no puede» de {nom_d} a «mejor no»', 'no_puede', did=did)
                if rd.get('dia_libre'):
                    sug(f'dialibre-{did}', f'Quitarle a {nom_d} el día libre', 'dia_libre', did=did)
                if rd.get('max_dia'):
                    sug(f'maxdia-{did}', f'Quitarle a {nom_d} el máximo de {rd["max_dia"]} clases por día', 'max_dia_doc', did=did)
                if rd.get('max_seguidas') or c.get('max_seguidas'):
                    sug(f'seguidas-{did}', f'Quitarle a {nom_d} el máximo de horas seguidas', 'seguidas', did=did)
                perm = rd.get('permanencia')
                perm = float(perm) if perm not in (None, '') else float(c.get('permanencia_horas') or 0)
                if perm and not (c.get('compensar') or {}).get('activa') and not self.extra_docente(did):
                    sug('compensar', 'Permitir días de hasta 1 hora más de permanencia si la semana no pasa de '
                                     'permanencia × días (ej.: 6 h × 5 = 30 h)', 'compensar')
                if perm:
                    sug(f'perm-{did}', f'Subirle a {nom_d} la permanencia de {perm:g} a {perm + 1:g} horas', 'permanencia',
                        did=did, horas=perm + 1)
                if regla_ex and regla_ex[2] and not rd.get('sin_excluyente'):
                    sug(f'excl-{did}', f'No aplicarle a {nom_d} la regla de la hora {regla_ex[1]} y la {regla_ex[0]}',
                        'excluyente_doc', did=did)
                for g in c.get('reuniones', []):
                    if g.get('modo') == 'fija' and did in [int(x) for x in g.get('docentes', []) if str(x).isdigit()] + [
                            int(g['jefe']) if str(g.get('jefe') or '').isdigit() else None]:
                        sug(f'reu-{g.get("nombre")}', f'Dejar que «{g.get("nombre")}» busque sola su hora (ahora es fija)',
                            'reunion', nombre=g.get('nombre'))
                sedes = {D.sede_de_curso(x['curso']) for x in D.asignaciones.values() if x.get('docente') == did}
                if len(sedes - {''}) > 1 and int(c.get('desplazamiento') or 0) > 15:
                    sug('despl', f'Bajar el tiempo para cambiar de sede de {c.get("desplazamiento")} a 15 minutos', 'desplazamiento')
            regla_m = c['materias'].get(str(mid), {})
            tope = int(regla_m.get('max_dia') or c.get('max_por_dia') or 2)
            jid = D.jornada_de_curso.get(cid)
            n_dias = len(D.jornadas[jid]['dias']) if jid in D.jornadas else 5
            if D.ih(aid, c) > tope * (n_dias - 1):
                sug(f'maxmat-{mid}', f'Permitir {tope + 1} horas de {nom_m} el mismo día', 'max_dia_mat', mid=mid, tope=tope + 1)
            esp = r.get('espacio') or regla_m.get('espacio')
            if esp:
                sug(f'esp-{esp}', f'Ampliar «{esp}» a un curso más a la vez', 'espacio', nombre=esp)
            req = nucleo.salon_requerido(c, a)
            if req and str(req).startswith('S:'):
                nombre_s = nucleo.nombre_salon(c, req)
                sug(f'sal-{req}', f'Dejar que «{nombre_s}» reciba un curso más a la vez (o darle otro salón a '
                                  f'{nom_m} {nom_c})', 'salon_cap', sid=str(req)[2:])
            area = D.materias.get(mid, {}).get('area')
            if area and ((c.get('areas') or {}).get(area) or {}).get('no_puede'):
                sug(f'area-{area}', f'Quitar las horas bloqueadas del área {area}', 'area_sin', area=area)
            if c.get('cursos', {}).get(str(cid), {}).get('no_puede'):
                sug(f'cursosin-{cid}', f'Quitar las horas sin clase marcadas para {nom_c}', 'curso_sin', cid=cid)
        if regla_ex and regla_ex[2]:
            sug('excl-general', f'Volver «si se puede» la regla de la hora {regla_ex[1]} y la {regla_ex[0]}', 'excluyente')
        return out

    def aplicar_sugerencia(self, s):
        c, d = self.cond, s['datos']
        t = s['tipo']
        if t == 'partir':
            self.asig(d['aid'])['dividir'] = True
        elif t == 'bloque_descanso':
            c['bloque_descanso'] = True
        elif t == 'no_puede':
            r = self.docente(d['did'])
            r['prefiere_no'] = sorted(set(r.get('prefiere_no', [])) | set(r.get('no_puede', [])))
            r['no_puede'] = []
        elif t == 'dia_libre':
            self.docente(d['did'])['dia_libre'] = False
        elif t == 'max_dia_doc':
            self.docente(d['did'])['max_dia'] = None
        elif t == 'seguidas':
            self.docente(d['did'])['max_seguidas'] = 99
        elif t == 'permanencia':
            self.docente(d['did'])['permanencia'] = d['horas']
        elif t == 'excluyente_doc':
            self.docente(d['did'])['sin_excluyente'] = True
        elif t == 'compensar':
            c['compensar'] = {'activa': True, 'max': (c.get('compensar') or {}).get('max') or 1}
        elif t == 'excluyente':
            c['excluyente']['obligatoria'] = False
        elif t == 'reunion':
            for g in c.get('reuniones', []):
                if g.get('nombre') == d['nombre']:
                    g['modo'] = 'auto'
        elif t == 'desplazamiento':
            c['desplazamiento'] = 15
        elif t == 'max_dia_mat':
            self.regla(d['mid'])['max_dia'] = d['tope']
        elif t == 'espacio':
            for e in c.get('espacios', []):
                if e.get('nombre') == d['nombre']:
                    e['capacidad'] = int(e.get('capacidad') or 1) + 1
        elif t == 'salon_cap':
            sal = self.salon(d['sid'])
            if sal:
                sal['capacidad'] = int(sal.get('capacidad') or 1) + 1
        elif t == 'area_sin':
            self.area(d['area'])['no_puede'] = []
        elif t == 'curso_sin':
            self.curso(d['cid'])['no_puede'] = []

    def texto_dificiles(self, alt):
        D = self.datos
        return [f'{D.nombre_materia(D.asignaciones[x["asignacion"]]["materia"])} en '
                f'{D.nombre_curso(D.asignaciones[x["asignacion"]]["curso"])} '
                f'({D.nombre_docente(D.asignaciones[x["asignacion"]].get("docente"))})'
                for x in alt.get('dificiles') or [] if x['asignacion'] in D.asignaciones]

    def texto_acompanamientos(self, alt):
        D = self.datos
        return [f'{nucleo.DIAS[x["dia"]]} {D.franjas[x["franja"]]["inicio"]} · {x["zona"]}: '
                + (', '.join(D.nombre_docente(d) for d in x['docentes']) or '—')
                for x in alt.get('acompanamientos') or [] if x['franja'] in D.franjas]

    def libres_por_hora(self, alt):
        """[(jornada, dia, franja, [docentes libres que ese día están en el colegio])] para reemplazos."""
        D = self.datos
        ocupado = nucleo._ocupado(D, alt['sesiones'], alt.get('reuniones'))
        for x in alt.get('actividades') or []:
            ocupado[(x['docente'], x['dia'])].append(D.intervalo(x['franja']))
        salida = []
        for jid in sorted(D.jornadas):
            j = D.jornadas[jid]
            docs = sorted({a['docente'] for a in D.asignaciones.values() if a.get('docente')
                           and D.jornada_de_curso.get(a['curso']) == jid}, key=D.nombre_docente)
            for dia in j['dias']:
                for f in D.franjas_de(jid):
                    if f['descanso']:
                        continue
                    ini, fin = D.intervalo(f['id'])
                    libres = [did for did in docs if ocupado.get((did, dia)) and
                              not any(a < fin and ini < b for a, b in ocupado[(did, dia)])]
                    salida.append((j, dia, f, libres))
        return salida

    def sin_ubicar_texto(self, alt):
        D = self.datos
        return [f'{D.nombre_materia(D.asignaciones[x["asignacion"]]["materia"])} en '
                f'{D.nombre_curso(D.asignaciones[x["asignacion"]]["curso"])}: {x["horas"]} h'
                for x in alt.get('sin_ubicar', []) if x['asignacion'] in D.asignaciones]

    def texto_reuniones(self, alt):
        D = self.datos
        out = []
        for r in alt.get('reuniones') or []:
            if not r.get('ubicada'):
                out.append(f'{r["nombre"]}: no se encontró una hora (revise que el jefe tenga horas libres).')
                continue
            t = f'{r["nombre"]}: {nucleo.DIAS[r["dia"]]} {nucleo.texto_hora(r["inicio"])}'
            if r.get('segunda'):
                s = r['segunda']
                t += f' y {nucleo.DIAS[s["dia"]]} {nucleo.texto_hora(s["inicio"])} (segundo grupo, con el jefe)'
            if r.get('faltan'):
                t += ' · no pueden (reciben el acta): ' + ', '.join(D.nombre_docente(x) for x in r['faltan'])
            out.append(t)
        return out

    # --- Exportar --------------------------------------------------------------
    def exportar_resultado(self, alt, ruta):
        r = nucleo.resultado(self.datos, alt['sesiones'], alt.get('nombre', 'Horario'),
                             {'huecos': alt.get('huecos'), 'costo': alt.get('costo'),
                              'horas_sin_ubicar': alt.get('horas_sin_ubicar', 0),
                              'reuniones': self.texto_reuniones(alt),
                              'multigrado': [g.get('cursos', []) for g in self.cond.get('multigrado', [])],
                              'acompanamientos': [{'dia': x['dia'], 'franja': x['franja'], 'zona': x['zona'],
                                                   'docentes': x['docentes']} for x in alt.get('acompanamientos') or []],
                              'actividades': [{'dia': x['dia'], 'franja': x['franja'], 'nombre': x['nombre'],
                                               'docente': x['docente']} for x in alt.get('actividades') or []],
                              'divididas': [self.datos.nombre_materia(self.datos.asignaciones[a]['materia']) + ' ' +
                                            self.datos.nombre_curso(self.datos.asignaciones[a]['curso'])
                                            for a in alt.get('divididas', []) if a in self.datos.asignaciones]})
        with open(ruta, 'w', encoding='utf-8') as fh:
            json.dump(r, fh, ensure_ascii=False)

    def exportar_excel(self, alt, ruta):
        """Una hoja con todas las clases y una por curso (para revisar o imprimir)."""
        from openpyxl import Workbook
        from openpyxl.styles import Alignment, Font, PatternFill
        D = self.datos
        wb = Workbook()
        ws = wb.active
        ws.title = 'Todas'
        ws.append(['CURSO', 'DIA', 'HORA', 'INICIO', 'MATERIA', 'DOCENTE', 'SALON'])
        orden = {}
        for jid in D.jornadas:
            for i, f in enumerate([f for f in D.franjas_de(jid) if not f['descanso']], start=1):
                orden[f['id']] = i
        for s in sorted(alt['sesiones'], key=lambda s: (D.nombre_curso(D.asignaciones[s['asignacion']]['curso']),
                                                         s['dia'], orden.get(s['franja'], 0))):
            a = D.asignaciones[s['asignacion']]
            ws.append([D.nombre_curso(a['curso']), nucleo.DIAS[s['dia']], orden.get(s['franja']),
                       D.franjas[s['franja']]['inicio'], D.nombre_materia(a['materia']), D.nombre_docente(a.get('docente')),
                       self._en_salon(s)[3:]])
        for c in D.cursos.values():
            t = self.tabla_curso(alt, c['id'])
            if not t:
                continue
            h = wb.create_sheet(c['nombre'][:30].replace('/', '-'))
            h.append(['Hora'] + [n for _, n in t['dias']])
            for celda in h[1]:
                celda.font = Font(bold=True, color='FFFFFF')
                celda.fill = PatternFill('solid', fgColor='3730A3')
            for f, celdas in t['filas']:
                if f['descanso']:
                    h.append([f'{f["inicio"]} {f.get("etiqueta") or "Descanso"}'])
                    continue
                h.append([f'{f["inicio"]}-{f["fin"]}'] + ['\n'.join(f'{x["titulo"]} ({x["sub"]})' for x in xs) for xs in celdas])
            for col in 'ABCDEFG':
                h.column_dimensions[col].width = 24
            for fila in h.iter_rows(min_row=2):
                for celda in fila:
                    celda.alignment = Alignment(wrap_text=True, vertical='top')
        self._hojas_extra(wb, alt)
        wb.save(ruta)

    def _hojas_extra(self, wb, alt):
        from openpyxl.styles import Alignment, Font
        D = self.datos
        # Docentes: el horario de cada uno, uno debajo del otro
        h = wb.create_sheet('Docentes')
        fila = 1
        for d in sorted(D.docentes.values(), key=lambda d: d['nombre']):
            tablas = self.tablas_docente(alt, d['id'])
            if not any(any(xs for _, cs in t['filas'] for xs in cs) for t in tablas):
                continue
            h.cell(fila, 1, d['nombre']).font = Font(bold=True, size=12)
            fila += 1
            for t in tablas:
                h.cell(fila, 1, 'Hora').font = Font(bold=True)
                for c, (_, n) in enumerate(t['dias'], start=2):
                    h.cell(fila, c, n).font = Font(bold=True)
                fila += 1
                for f, cs in t['filas']:
                    h.cell(fila, 1, f'{f["inicio"]}-{f["fin"]}' + (' (descanso)' if f['descanso'] else ''))
                    for c, xs in enumerate(cs, start=2):
                        if xs:
                            h.cell(fila, c, '\n'.join(f'{x["titulo"]} ({x["sub"]})' for x in xs)).alignment = \
                                Alignment(wrap_text=True, vertical='top')
                    fila += 1
            fila += 1
        for col in 'ABCDEFG':
            h.column_dimensions[col].width = 24
        # Docentes libres por hora (para cubrir reemplazos)
        h = wb.create_sheet('Libres por hora')
        h.append(['JORNADA', 'DIA', 'HORA', 'DOCENTES LIBRES (ese día están en el colegio)'])
        for j, dia, f, libres in self.libres_por_hora(alt):
            h.append([j['nombre'], nucleo.DIAS[dia], f'{f["inicio"]}-{f["fin"]}', ', '.join(D.nombre_docente(x) for x in libres)])
        h.column_dimensions['D'].width = 90
        if alt.get('acompanamientos'):
            h = wb.create_sheet('Descansos')
            h.append(['DIA', 'HORA', 'ZONA', 'DOCENTES'])
            for x in alt['acompanamientos']:
                if x['franja'] in D.franjas:
                    h.append([nucleo.DIAS[x['dia']], D.franjas[x['franja']]['inicio'], x['zona'],
                              ', '.join(D.nombre_docente(d) for d in x['docentes'])])
            h.column_dimensions['D'].width = 70
        if alt.get('actividades'):
            h = wb.create_sheet('Actividades')
            h.append(['DOCENTE', 'ACTIVIDAD', 'DIA', 'HORA'])
            for x in sorted(alt['actividades'], key=lambda x: (D.nombre_docente(x['docente']), x['dia'])):
                h.append([D.nombre_docente(x['docente']), x['nombre'], nucleo.DIAS[x['dia']], D.franjas[x['franja']]['inicio']])
            h.column_dimensions['A'].width = 34


def texto_horas(minutos):
    """95 → «1 h 35»; 300 → «5 h»."""
    h, m = divmod(int(round(minutos)), 60)
    return f'{h} h {m:02d}' if m else f'{h} h'
