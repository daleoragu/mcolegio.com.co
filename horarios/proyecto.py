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
ESTADOS_CELDA = ('libre', 'no_puede', 'prefiere_no')


class Proyecto:
    def __init__(self, crudo, cond=None, alternativas=None, ruta=None):
        self.datos = nucleo.Datos(crudo)
        self.cond = cond or nucleo.condiciones_vacias()
        for k, v in nucleo.condiciones_vacias().items():
            self.cond.setdefault(k, v)
        self.alternativas = alternativas or []
        self.ruta = ruta

    # --- Archivos -----------------------------------------------------------
    @classmethod
    def abrir_datos(cls, ruta):
        with open(ruta, encoding='utf-8-sig') as fh:
            return cls(nucleo.leer_json(fh.read(), nucleo.TIPO_DATOS))

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
        r.setdefault('no_puede', [])
        r.setdefault('prefiere_no', [])
        return r

    def estado_celda(self, did, dia, fid):
        r = self.docente(did)
        clave = f'{dia}-{fid}'
        if clave in r['no_puede']:
            return 'no_puede'
        if clave in r['prefiere_no']:
            return 'prefiere_no'
        return 'libre'

    def poner_celda(self, did, dia, fid, estado):
        r = self.docente(did)
        clave = f'{dia}-{fid}'
        for k in ('no_puede', 'prefiere_no'):
            if clave in r[k]:
                r[k].remove(clave)
        if estado in ('no_puede', 'prefiere_no'):
            r[estado].append(clave)

    def siguiente_estado(self, did, dia, fid):
        """Libre → no puede → prefiere no → libre."""
        actual = self.estado_celda(did, dia, fid)
        nuevo = ESTADOS_CELDA[(ESTADOS_CELDA.index(actual) + 1) % 3]
        self.poner_celda(did, dia, fid, nuevo)
        return nuevo

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
        faltan = nucleo.horas_faltantes(self.datos, alt['sesiones'], self.cond)
        alt['sin_ubicar'] = [{'asignacion': a['id'], 'horas': n} for a, n in faltan]
        alt['horas_sin_ubicar'] = sum(n for _, n in faltan)
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

    def motivo(self, alt, aid, dia, fid, ignorar=None):
        """None si la ficha cabe ahí; si no, por qué."""
        D = self.datos
        a = D.asignaciones[aid]
        jid = D.jornada_de_curso.get(a['curso'])
        if jid is None or fid not in {f['id'] for f in D.jornadas[jid]['franjas'] if not f['descanso']}:
            return 'Esa hora no es de la jornada del curso.'
        if dia not in D.jornadas[jid]['dias']:
            return 'Ese día no hay clases en la jornada del curso.'
        otras = [s for i, s in enumerate(alt['sesiones']) if i != ignorar]
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
            if perm and not extra:
                tramos = [t for t, s in mias if not self.cond['asignaciones'].get(str(s['asignacion']), {}).get('extra')]
                tramos.append((ini, fin))
                if max(b for _, b in tramos) - min(x for x, _ in tramos) > perm * 60:
                    return f'Se pasa de las {perm:g} horas de permanencia de {D.nombre_docente(did)} ese día.'
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
        partes = nucleo.patron(self.asig(aid).get('bloques')) or nucleo.patron(regla.get('bloques')) or [1]
        tope = max(tope, max(partes))
        ese_dia = sum(1 for s in otras if s['dia'] == dia and D.asignaciones.get(s['asignacion'], {}).get('curso') == a['curso']
                      and D.asignaciones.get(s['asignacion'], {}).get('materia') == a['materia'])
        if ese_dia + 1 > tope:
            return f'{D.nombre_materia(a["materia"])} ya tiene {ese_dia} hora(s) ese día (máximo {tope}).'
        return None

    def poner_ficha(self, alt, aid, dia, fid):
        m = self.motivo(alt, aid, dia, fid)
        if m:
            return m
        alt['sesiones'].append({'asignacion': aid, 'curso': self.datos.asignaciones[aid]['curso'], 'dia': dia,
                                'franja': fid, 'fijada': True})
        self.revisar(alt)
        return None

    def mover_ficha(self, alt, i, dia, fid):
        s = alt['sesiones'][i]
        m = self.motivo(alt, s['asignacion'], dia, fid, ignorar=i)
        if m:
            return m
        s.update(dia=dia, franja=fid, fijada=True)
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
            tablas.append(self._tabla(j['id'], celdas))
        return tablas

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
        wb.save(ruta)
