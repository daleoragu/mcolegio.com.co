"""PuntoExacto · informes por nota, con la escala de valoración del colegio.

Para los exámenes que solo se califican (sin unirlos al estilo ICFES): cada estudiante con su nota y su desempeño
(SUPERIOR, ALTO, BÁSICO, BAJO… o como los llame el colegio), y cada curso con su promedio, cuántos quedaron en cada
desempeño, quién aprobó y qué preguntas costaron más.

La escala es la del área: la escala especial de la materia del examen en ese grado si el colegio tiene una, y si no,
la del colegio (notas/escalas.py). Sin colegio (plan individual) o sin escala configurada, se usa la escala
nacional de referencia (Decreto 1290) llevada al rango de notas del examen.
"""
from collections import defaultdict
from decimal import Decimal
from statistics import mean, pstdev


# Bajo · Básico · Alto · Superior en una escala de 1 a 5: 1,0–2,9 · 3,0–3,9 · 4,0–4,5 · 4,6–5,0 (en fracción del rango)
REFERENCIA = [('BAJO', 0.0), ('BÁSICO', 0.5), ('ALTO', 0.75), ('SUPERIOR', 0.9)]
COLORES = {1: ['#2b8a3e'], 2: ['#c92a2a', '#2b8a3e'], 3: ['#c92a2a', '#e8a317', '#2b8a3e'],
           4: ['#c92a2a', '#e8a317', '#1c7ed6', '#2b8a3e'], 5: ['#c92a2a', '#e8590c', '#e8a317', '#1c7ed6', '#2b8a3e']}
MENSAJES = {
    'BAJO': 'Necesita reforzar los temas evaluados: repase las preguntas que falló y pida apoyo a su docente.',
    'BÁSICO': 'Alcanzó lo básico. Practique los temas de las preguntas que falló para subir de nivel.',
    'ALTO': 'Buen desempeño. Revise las pocas preguntas que falló para llegar a Superior.',
    'SUPERIOR': 'Excelente desempeño: domina los temas evaluados. ¡Siga así!',
}


def _color(i, n):
    tabla = COLORES.get(n) or [COLORES[5][min(4, round(4 * k / max(1, n - 1)))] for k in range(n)]
    return tabla[i]


def _niveles_referencia(examen):
    lo, hi = Decimal(examen.nota_minima), Decimal(examen.nota_maxima)
    rango = hi - lo
    salida = []
    for i, (nombre, f) in enumerate(REFERENCIA):
        minimo = (lo + rango * Decimal(str(f))).quantize(Decimal('0.1'))
        siguiente = REFERENCIA[i + 1][1] if i + 1 < len(REFERENCIA) else None
        maximo = (lo + rango * Decimal(str(siguiente))).quantize(Decimal('0.1')) - Decimal('0.1') if siguiente else hi
        salida.append({'nombre': nombre, 'min': minimo, 'max': maximo, 'mensaje': ''})
    return salida


class Escala:
    """Los niveles que rigen la nota de una hoja (según su grado), leídos una sola vez."""

    def __init__(self, examen):
        self.examen = examen
        self.materia_id = examen.asignacion.materia_id if examen.asignacion_id else None
        self.escalas = None
        if examen.colegio_id:
            from notas import escalas as esc
            self.escalas = esc.de(examen.colegio)
        self._cache = {}
        self.referencia = False

    def niveles(self, grado=None):
        if grado in self._cache:
            return self._cache[grado]
        crudos = self.escalas.niveles(self.materia_id, grado) if self.escalas is not None else []
        lista = [{'nombre': n.nombre_desempeno.upper(), 'min': Decimal(n.valor_minimo), 'max': Decimal(n.valor_maximo),
                  'mensaje': (getattr(n, 'mensaje_boletin', '') or '').strip()} for n in crudos]
        if not lista:
            lista = _niveles_referencia(self.examen)
            self.referencia = True
        for i, n in enumerate(lista):
            n['color'] = _color(i, len(lista))
            n['mensaje'] = n['mensaje'] or MENSAJES.get(n['nombre'].replace('BASICO', 'BÁSICO'), '')
        self._cache[grado] = lista
        return lista

    @staticmethod
    def nivel(niveles, nota):
        if nota is None or not niveles:
            return None
        nota = Decimal(nota)
        for n in niveles:
            if n['min'] <= nota <= n['max']:
                return n
        # Entre dos rangos (p. ej. 2,95 con rangos de un decimal): el más alto cuyo mínimo alcanza
        alcanzados = [n for n in niveles if nota >= n['min']]
        return alcanzados[-1] if alcanzados else niveles[0]

    @staticmethod
    def aprobacion(niveles):
        return niveles[1]['min'] if len(niveles) >= 2 else None


def _grado_num(h):
    from . import hojas as hojas_mod
    try:
        c = hojas_mod.curso_de_hoja(h)
    except Exception:
        c = None
    return getattr(c, 'grado', None) if c is not None else None


def _resumen(filas, niveles):
    """Promedio, extremos, desviación y cuántos en cada desempeño de unas filas de estudiantes."""
    notas = [float(f['nota']) for f in filas]
    n = len(notas)
    dist = []
    for nv in reversed(niveles):
        k = sum(1 for f in filas if f['nivel'] and f['nivel']['nombre'] == nv['nombre'])
        dist.append({'nombre': nv['nombre'], 'color': nv['color'], 'n': k, 'pct': round(100 * k / n) if n else 0,
                     'rango': f"{nv['min']} – {nv['max']}"})
    piso = Escala.aprobacion(niveles)
    aprobados = sum(1 for f in filas if piso is not None and f['nota'] >= piso)
    return {'n': n, 'promedio': round(mean(notas), 2) if notas else None, 'minimo': min(notas) if notas else None,
            'maximo': max(notas) if notas else None, 'desviacion': round(pstdev(notas), 2) if n > 1 else 0.0,
            'distribucion': dist, 'aprobados': aprobados, 'reprobados': n - aprobados,
            'pct_aprobados': round(100 * aprobados / n) if n else 0, 'piso': piso,
            'nivel_promedio': Escala.nivel(niveles, Decimal(str(round(mean(notas), 2)))) if notas else None}


def _preguntas(filas, preguntas):
    """Acierto del grupo por pregunta y por etiqueta («qué evalúa»)."""
    salida, etiquetas = [], defaultdict(lambda: [0, 0])
    n = len(filas)
    for p in preguntas:
        bien = sum(1 for f in filas if p.acierta(f['marcas'].get(p.id, '')))
        pct = round(100 * bien / n) if n else 0
        salida.append({'numero': p.numero, 'pct': pct, 'correcta': p.rotulo_correctas(), 'etiquetas': p.lista_etiquetas()})
        for et in p.lista_etiquetas():
            etiquetas[et][0] += bien
            etiquetas[et][1] += n
    temas = sorted(({'etiqueta': k, 'pct': round(100 * b / t) if t else 0} for k, (b, t) in etiquetas.items()),
                   key=lambda x: x['pct'])
    return salida, temas


def construir(examen, incluir=None, titulo=None):
    """Todo lo que necesitan los informes por nota de un examen.

    incluir: función hoja -> bool para quedarse con una parte (un curso, un grado, los escogidos).
    """
    from . import informes as INF
    escala = Escala(examen)
    preguntas = list(examen.preguntas.filter(anulada=False, es_control=False).order_by('numero'))
    hojas = (examen.hojas.filter(estado__in=('calificada', 'revisar'))
             .select_related('estudiante__user', 'estudiante__curso__sede', 'integrante__grupo').prefetch_related('respuestas'))
    filas = []
    for h in hojas:
        if h.nota is None or (incluir is not None and not incluir(h)):
            continue
        grado = _grado_num(h)
        niveles = escala.niveles(grado)
        marcas = {r.pregunta_id: r.marcada for r in h.respuestas.all()}
        buenas = malas = blancas = 0
        falladas = []
        for p in preguntas:
            m = (marcas.get(p.id) or '').strip()
            if not m:
                blancas += 1
            elif p.acierta(m):
                buenas += 1
                continue
            else:
                malas += 1
            falladas.append({'numero': p.numero, 'marcada': p.rotulo_marcada(m), 'correcta': p.rotulo_correctas(),
                             'etiquetas': ', '.join(p.lista_etiquetas())})
        filas.append({'hoja': h, 'clave': INF._clave_persona(h), 'nombre': h.nombre, 'documento': h.documento,
                      'curso': INF.curso_de(h), 'grado': grado, 'nota': Decimal(h.nota), 'niveles': niveles,
                      'nivel': Escala.nivel(niveles, h.nota), 'buenas': buenas, 'malas': malas, 'blancas': blancas,
                      'falladas': falladas, 'marcas': marcas})
    filas.sort(key=lambda f: (f['curso'], f['nombre'].lower()))

    # Por curso
    cursos = []
    por_curso = defaultdict(list)
    for f in filas:
        por_curso[f['curso']].append(f)
    for nombre in sorted(por_curso, key=lambda t: (int(''.join(ch for ch in t if ch.isdigit()) or 999), t)):
        fs = por_curso[nombre]
        niveles = fs[0]['niveles']
        preg, temas = _preguntas(fs, preguntas)
        cursos.append({'curso': nombre, 'resumen': _resumen(fs, niveles), 'filas': fs, 'niveles': niveles,
                       'dificiles': sorted(preg, key=lambda x: x['pct'])[:10], 'temas': temas})
    # Total
    niveles_total = filas[0]['niveles'] if filas else escala.niveles(None)
    preg, temas = _preguntas(filas, preguntas)
    total = {'resumen': _resumen(filas, niveles_total), 'dificiles': sorted(preg, key=lambda x: x['pct'])[:10],
             'faciles': sorted(preg, key=lambda x: -x['pct'])[:5], 'temas': temas, 'preguntas': preg}

    # Para cada estudiante: cómo le fue frente a su curso
    for c in cursos:
        for f in c['filas']:
            f['promedio_curso'] = c['resumen']['promedio']
            f['aprobo'] = c['resumen']['piso'] is None or f['nota'] >= c['resumen']['piso']
            f['temas'] = _temas_de(f, preguntas)
    return {'examen': examen, 'titulo': titulo or examen.titulo, 'filas': filas, 'cursos': cursos, 'total': total,
            'niveles': niveles_total, 'referencia': escala.referencia, 'n_preguntas': len(preguntas),
            'materia': examen.asignacion.materia.nombre if examen.asignacion_id and examen.asignacion.materia_id else ''}


def _temas_de(f, preguntas):
    """Acierto del estudiante por etiqueta («qué evalúa»), del más bajo al más alto."""
    t = defaultdict(lambda: [0, 0])
    for p in preguntas:
        for et in p.lista_etiquetas():
            t[et][1] += 1
            if p.acierta(f['marcas'].get(p.id, '')):
                t[et][0] += 1
    return sorted(({'etiqueta': k, 'bien': b, 'total': n, 'pct': round(100 * b / n)} for k, (b, n) in t.items()),
                  key=lambda x: x['pct'])


def fila_de(datos, clave):
    return next((f for f in datos['filas'] if f['clave'] == clave), None)

