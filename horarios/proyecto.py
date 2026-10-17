"""Lo que hace la app de escritorio, sin la ventana (así se puede probar).

Un PROYECTO (.mchp) guarda los datos del colegio, las condiciones que el
coordinador fue poniendo y las alternativas generadas.
"""
import json
import time

from . import nucleo

TIPO_PROYECTO = 'mcolegio-horario-proyecto'


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
        nuevo.cond = c
        nuevo.ruta = self.ruta
        return nuevo

    # --- Condiciones ----------------------------------------------------------
    def poner_ih(self, aid, n):
        self.cond['ih'][str(aid)] = max(0, int(n))

    def regla(self, mid):
        return self.cond['materias'].setdefault(str(mid), {})

    def docente(self, did):
        return self.cond['docentes'].setdefault(str(did), {'no_puede': []})

    def alternar_no_puede(self, did, dia, fid):
        r = self.docente(did)
        clave = f'{dia}-{fid}'
        lst = r.setdefault('no_puede', [])
        if clave in lst:
            lst.remove(clave)
            return False
        lst.append(clave)
        return True

    def jornadas_de_docente(self, did):
        ids = {self.datos.jornada_de_curso.get(a['curso']) for a in self.datos.asignaciones.values()
               if a.get('docente') == did}
        return [self.datos.jornadas[j] for j in sorted(ids - {None})]

    def asignaciones_de_curso(self, cid):
        return sorted([a for a in self.datos.asignaciones.values() if a['curso'] == cid],
                      key=lambda a: self.datos.nombre_materia(a['materia']))

    def agregar_fija(self, aid, dia, fid):
        """None si quedó; si no, el motivo."""
        D = self.datos
        a = D.asignaciones[aid]
        jid = D.jornada_de_curso.get(a['curso'])
        if jid is None or fid not in {f['id'] for f in D.jornadas[jid]['franjas'] if not f['descanso']}:
            return 'Esa hora no es de la jornada del curso.'
        if dia not in D.jornadas[jid]['dias']:
            return 'Ese día no hay clases en la jornada del curso.'
        nueva = {'asignacion': aid, 'dia': dia, 'franja': fid}
        ses = [{'asignacion': int(f['asignacion']), 'dia': int(f['dia']), 'franja': int(f['franja'])} for f in self.cond['fijas']]
        problemas = nucleo.revisar(D, ses + [nueva], self.cond)
        if problemas:
            return problemas[-1]
        fijas_de_a = sum(1 for f in self.cond['fijas'] if int(f['asignacion']) == aid)
        if fijas_de_a >= D.ih(aid, self.cond):
            return 'Esa materia ya tiene fijadas todas sus horas.'
        self.cond['fijas'].append(nueva)
        return None

    def quitar_fija(self, i):
        del self.cond['fijas'][i]

    # --- Generar --------------------------------------------------------------
    def generar(self, cuantas=3, segundos=60, avance=None):
        """Genera alternativas (cada una con otra semilla) y las ordena de mejor a peor."""
        self.alternativas = []
        for k in range(cuantas):
            def av(p, k=k):
                if avance:
                    avance(int((k + p / 100) * 100 / cuantas), f'Alternativa {k + 1} de {cuantas}…')
            r = nucleo.generar(self.datos, self.cond, segundos=segundos, semilla=int(time.time()) + k * 7919, avance=av)
            r['choques'] = nucleo.revisar(self.datos, r['sesiones'], self.cond)
            r['horas_sin_ubicar'] = sum(x['horas'] for x in r['sin_ubicar'])
            self.alternativas.append(r)
        self.alternativas.sort(key=lambda r: (r['horas_sin_ubicar'], len(r['choques']), r['costo']))
        for i, r in enumerate(self.alternativas, start=1):
            r['nombre'] = f'Alternativa {i}'
        if avance:
            avance(100, 'Listo')
        return self.alternativas

    # --- Ver -------------------------------------------------------------------
    def _celdas(self, alt, filtro, texto):
        celdas = {}
        for s in alt['sesiones']:
            a = self.datos.asignaciones.get(s['asignacion'])
            if a and filtro(a):
                celdas.setdefault((s['dia'], s['franja']), []).append(texto(a))
        return celdas

    def _tabla(self, jid, celdas):
        j = self.datos.jornadas[jid]
        dias = [(d, nucleo.DIAS[d]) for d in j['dias']]
        filas = [(f, [celdas.get((d, f['id']), []) for d, _ in dias]) for f in self.datos.franjas_de(jid)]
        return {'jornada': j, 'dias': dias, 'filas': filas}

    def tabla_curso(self, alt, cid):
        jid = self.datos.jornada_de_curso.get(cid)
        if jid is None:
            return None
        D = self.datos
        return self._tabla(jid, self._celdas(alt, lambda a: a['curso'] == cid,
                                             lambda a: (D.nombre_materia(a['materia']), D.nombre_docente(a.get('docente')))))

    def tablas_docente(self, alt, did):
        D = self.datos
        celdas = self._celdas(alt, lambda a: a.get('docente') == did,
                              lambda a: (D.nombre_curso(a['curso']), D.nombre_materia(a['materia'])))
        return [self._tabla(j['id'], celdas) for j in self.jornadas_de_docente(did)]

    def sin_ubicar_texto(self, alt):
        D = self.datos
        return [f'{D.nombre_materia(D.asignaciones[x["asignacion"]]["materia"])} en '
                f'{D.nombre_curso(D.asignaciones[x["asignacion"]]["curso"])}: {x["horas"]} h'
                for x in alt['sin_ubicar'] if x['asignacion'] in D.asignaciones]

    # --- Exportar --------------------------------------------------------------
    def exportar_resultado(self, alt, ruta):
        r = nucleo.resultado(self.datos, alt['sesiones'], alt.get('nombre', 'Horario'),
                             {'huecos': alt.get('huecos'), 'costo': alt.get('costo'),
                              'horas_sin_ubicar': alt.get('horas_sin_ubicar', 0)})
        with open(ruta, 'w', encoding='utf-8') as fh:
            json.dump(r, fh, ensure_ascii=False)

    def exportar_excel(self, alt, ruta):
        """Una hoja por curso y otra con todas las clases (para revisar o imprimir)."""
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
                h.append([f'{f["inicio"]}-{f["fin"]}'] + ['\n'.join(f'{m} ({d})' for m, d in x) for x in celdas])
            for col in 'ABCDEFG':
                h.column_dimensions[col].width = 24
            for fila in h.iter_rows(min_row=2):
                for celda in fila:
                    celda.alignment = Alignment(wrap_text=True, vertical='top')
        wb.save(ruta)
