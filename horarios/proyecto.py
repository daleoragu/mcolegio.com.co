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
ESTADOS_CELDA = ('libre', 'no_puede', 'prefiere_no', 'evitar')
LISTAS_CELDA = ('no_puede', 'prefiere_no', 'evitar')


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
        """Libre → no puede → mejor no → mejor no (fuerte) → libre."""
        actual = self.estado_celda(did, dia, fid)
        nuevo = ESTADOS_CELDA[(ESTADOS_CELDA.index(actual) + 1) % len(ESTADOS_CELDA)]
        self.poner_celda(did, dia, fid, nuevo)
        return nuevo

    # Horas en que un curso no tiene clase (sale temprano, actividad fija…)
    def curso(self, cid):
        r = self.cond['cursos'].setdefault(str(cid), {})
        r.setdefault('no_puede', [])
        return r

    def celda_curso(self, cid, dia, fid):
        return f'{dia}-{fid}' in self.curso(cid)['no_puede']

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
                if self.cond['asignaciones'].get(str(a['id']), {}).get('extra'):
                    extra += n
                else:
                    base += n
                sedes.add(self.datos.sede_de_curso(a['curso']) or 'Principal')
        return base, extra, sorted(sedes)

    # Reuniones, clases simultáneas y espacios
    def reuniones_por_area(self):
        """Una reunión por cada área que todavía no tenga la suya."""
        ya = {r.get('area') for r in self.cond['reuniones']}
        nuevas = 0
        for area in sorted(self.datos.areas):
            docentes = self.datos.docentes_de_area(area)
            if area in ya or len(docentes) < 2:
                continue
            self.cond['reuniones'].append({'nombre': f'Reunión de {area}', 'area': area, 'docentes': docentes,
                                           'jefe': None, 'modo': 'auto', 'dos': True})
            nuevas += 1
        return nuevas

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

    def _correr(self, cond, segundos, semilla, avance=None):
        r = nucleo.generar(self.datos, cond, segundos=segundos, semilla=semilla, avance=avance)
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
        alt['choques'] += self._revisar_excluyente(alt)
        faltan = nucleo.horas_faltantes(self.datos, alt['sesiones'], self.cond)
        alt['sin_ubicar'] = [{'asignacion': a['id'], 'horas': n} for a, n in faltan]
        alt['horas_sin_ubicar'] = sum(n for _, n in faltan)
        self.complementos(alt)
        return alt

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
            if self.docente(did).get('sin_excluyente'):
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

    def generar(self, cuantas=3, segundos=60, avance=None, base=None):
        """Genera alternativas (cada una con otra semilla), respetando las fichas fijadas de `base`."""
        cond = self._cond_con_fijas(base)
        self.alternativas = [a for a in self.alternativas if a.get('manual')]
        nuevas = []
        for k in range(cuantas):
            def av(p, k=k):
                if avance:
                    avance(int((k + p / 100) * 100 / cuantas), f'Alternativa {k + 1} de {cuantas}…')
            nuevas.append(self._correr(cond, segundos, int(time.time()) + k * 7919, av))
        nuevas.sort(key=lambda r: (r['horas_sin_ubicar'], len(r['choques']), r['costo']))
        for i, r in enumerate(nuevas, start=1):
            r['nombre'] = f'Alternativa {i}'
        self.alternativas = nuevas + self.alternativas
        if avance:
            avance(100, 'Listo')
        return nuevas

    def completar(self, alt, segundos=30, avance=None, solo_fijadas=False):
        """Deja quietas las fichas puestas (o solo las fijadas) y ubica lo que falta."""
        cond = self._cond_con_fijas(alt, todas=not solo_fijadas)
        r = self._correr(cond, segundos, int(time.time()),
                         (lambda p: avance(p, 'Completando…')) if avance else None)
        r['nombre'] = f"{alt.get('nombre', 'Horario')} (completado)"
        self.alternativas.insert(0, r)
        if avance:
            avance(100, 'Listo')
        return r

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
                return f'{D.nombre_docente(a["docente"])} ya está en {D.nombre_curso(b["curso"])} a esa hora.'
        did = a.get('docente')
        if did:
            if self.estado_celda(did, dia, fid) == 'no_puede':
                return f'{D.nombre_docente(did)} no puede a esa hora.'
            for r in alt.get('reuniones') or []:
                for reu in (r, r.get('segunda') or {}):
                    if reu.get('dia') == dia and did in reu.get('asisten', []) and reu['inicio'] < fin and ini < reu['fin']:
                        return f'{D.nombre_docente(did)} tiene {r["nombre"]} a esa hora.'
            extra = self.cond['asignaciones'].get(str(aid), {}).get('extra')
            perm = self.docente(did).get('permanencia')
            perm = float(perm) if perm not in (None, '') else float(self.cond.get('permanencia_horas') or 0)
            mias = [(D.intervalo(s['franja']), s) for s in otras
                    if s['dia'] == dia and D.asignaciones.get(s['asignacion'], {}).get('docente') == did]
            reus = nucleo.franjas_de_reuniones(D, alt.get('reuniones')).get((did, dia), [])
            if perm and not extra:
                tramos = [t for t, s in mias if not self.cond['asignaciones'].get(str(s['asignacion']), {}).get('extra')]
                tramos += [D.intervalo(x) for x in reus]       # las reuniones de área van dentro de la permanencia
                tramos.append((ini, fin))
                if max(b for _, b in tramos) - min(x for x, _ in tramos) > perm * 60:
                    return f'Se pasa de las {perm:g} horas de permanencia de {D.nombre_docente(did)} ese día.'
            m = self._motivo_excluyente(did, dia, fid, [(None, {'franja': x}) for x in reus] + mias)
            if m:
                return m
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

    def _numero_hora(self, fid):
        """(número de la hora de clase desde 1, cuántas horas de clase tiene esa jornada)."""
        f = self.datos.franjas[fid]
        clase = [x['id'] for x in self.datos.franjas_de(f['jornada']) if not x['descanso']]
        return (clase.index(fid) + 1 if fid in clase else 0), len(clase)

    def _es_hora(self, fid, n):
        k, total = self._numero_hora(fid)
        return k == min(n, total)

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

    def poner_ficha(self, alt, aid, dia, fid, fijar=True):
        m = self.motivo(alt, aid, dia, fid)
        if m:
            return m
        alt['sesiones'].append({'asignacion': aid, 'curso': self.datos.asignaciones[aid]['curso'], 'dia': dia,
                                'franja': fid, 'fijada': fijar})
        self.revisar(alt)
        return None

    def mover_ficha(self, alt, i, dia, fid, fijar=True):
        s = alt['sesiones'][i]
        m = self.motivo(alt, s['asignacion'], dia, fid, ignorar=i)
        if m:
            return m
        s.update(dia=dia, franja=fid, fijada=fijar or s.get('fijada', False))
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
        del alt['sesiones'][i]
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
                                                        'sub': D.nombre_docente(a.get('docente')),
                                                        'fijada': s.get('fijada', False), 'asig': a['id']})
        return self._tabla(jid, celdas)

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
                                                            'sub': D.nombre_materia(a['materia']),
                                                            'fijada': s.get('fijada', False), 'asig': a['id']})
            for r in alt.get('reuniones') or []:
                for reu in (r, r.get('segunda') or {}):
                    if did in reu.get('asisten', []):
                        for f in j['franjas']:
                            x, y = nucleo.minutos(f['inicio']), nucleo.minutos(f['fin'])
                            if not f['descanso'] and x < reu['fin'] and reu['inicio'] < y:
                                celdas[(reu['dia'], f['id'])].append({'i': None, 'titulo': r['nombre'], 'sub': 'Reunión',
                                                                      'fijada': True, 'reunion': True})
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
                t += ' · no pueden: ' + ', '.join(D.nombre_docente(x) for x in r['faltan'])
            out.append(t)
        return out

    # --- Exportar --------------------------------------------------------------
    def exportar_resultado(self, alt, ruta):
        r = nucleo.resultado(self.datos, alt['sesiones'], alt.get('nombre', 'Horario'),
                             {'huecos': alt.get('huecos'), 'costo': alt.get('costo'),
                              'horas_sin_ubicar': alt.get('horas_sin_ubicar', 0),
                              'reuniones': self.texto_reuniones(alt),
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
        ws.append(['CURSO', 'DIA', 'HORA', 'INICIO', 'MATERIA', 'DOCENTE'])
        orden = {}
        for jid in D.jornadas:
            for i, f in enumerate([f for f in D.franjas_de(jid) if not f['descanso']], start=1):
                orden[f['id']] = i
        for s in sorted(alt['sesiones'], key=lambda s: (D.nombre_curso(D.asignaciones[s['asignacion']]['curso']),
                                                         s['dia'], orden.get(s['franja'], 0))):
            a = D.asignaciones[s['asignacion']]
            ws.append([D.nombre_curso(a['curso']), nucleo.DIAS[s['dia']], orden.get(s['franja']),
                       D.franjas[s['franja']]['inicio'], D.nombre_materia(a['materia']), D.nombre_docente(a.get('docente'))])
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
