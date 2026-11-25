"""PuntoExacto · informes al estilo ICFES: por estudiante y general, de un examen o de varios unidos.

CÓMO SE ARMAN LAS ÁREAS
  · Un examen con bloques (una censal): cada bloque es un área (Lectura crítica, Matemáticas…).
  · Un examen sin bloques: el examen entero es un área (lleva el nombre del examen).
  · Varios exámenes unidos (un simulacro aplicado por partes): las áreas de todos, y a cada estudiante se le
    juntan sus hojas de los distintos exámenes (por su cuenta del colegio, su integrante del grupo, su documento
    o, si no hay más, su nombre).

PUNTAJES (una aproximación: el ICFES usa teoría de respuesta al ítem, aquí se usa el porcentaje de aciertos)
  · Puntaje de cada área, de 0 a 100: aciertos de las preguntas del área ÷ preguntas del área (sin anuladas ni de control).
  · Puntaje global, de 0 a 500: promedio ponderado de las áreas × 5. Las áreas que se reconocen como pruebas
    Saber 11 pesan como en el ICFES (Lectura crítica, Matemáticas, Sociales y Ciencias 3; Inglés 1); las demás, 1.
  · Nivel de desempeño de cada área con los rangos de Saber 11 (Inglés con los de A-, A1, A2, B1 y B+); un área
    que no es de Saber 11 usa los rangos de Ciencias.
  · Percentil: el porcentaje de estudiantes de la misma prueba con un puntaje global menor.
"""
import math
import unicodedata
from collections import defaultdict

# Pruebas de Saber 11: palabras con que se reconocen, peso en el global y rangos de los niveles (puntaje 0–100)
PRUEBAS = {
    'LC': {'nombre': 'Lectura crítica', 'palabras': ('lectura', 'lenguaje', 'castellano', 'espanol', 'comprension'),
           'peso': 3, 'cortes': (35, 50, 65)},
    'MAT': {'nombre': 'Matemáticas', 'palabras': ('matematic', 'razonamiento cuantitativo', 'aritmetic', 'geometr', 'algebra'),
            'peso': 3, 'cortes': (35, 50, 70)},
    'SOC': {'nombre': 'Sociales y ciudadanas', 'palabras': ('social', 'ciudadan', 'historia', 'geografia', 'filosofia', 'constitucion'),
            'peso': 3, 'cortes': (40, 55, 70)},
    'CN': {'nombre': 'Ciencias naturales', 'palabras': ('ciencia', 'natural', 'biolog', 'quimic', 'fisic'),
           'peso': 3, 'cortes': (40, 55, 70)},
    'ING': {'nombre': 'Inglés', 'palabras': ('ingles', 'english'), 'peso': 1, 'cortes': (36, 57, 70, 87)},
}
NIVELES = ['Nivel 1', 'Nivel 2', 'Nivel 3', 'Nivel 4']
NIVELES_INGLES = ['A-', 'A1', 'A2', 'B1', 'B+']
QUE_DICE_NIVEL = {
    'Nivel 1': 'Responde preguntas de menor complejidad o aún no las supera; necesita acompañamiento en lo básico del área.',
    'Nivel 2': 'Supera las preguntas de menor complejidad; le falta pasar a las que piden relacionar y aplicar.',
    'Nivel 3': 'Relaciona y aplica lo aprendido en situaciones conocidas; está por encima de lo básico.',
    'Nivel 4': 'Resuelve las preguntas de mayor complejidad: interpreta, argumenta y propone en situaciones nuevas.',
}
QUE_DICE_INGLES = {
    'A-': 'Aún no supera las preguntas de menor complejidad de la prueba.',
    'A1': 'Comprende y usa expresiones cotidianas y frases sencillas.',
    'A2': 'Comprende frases y expresiones de uso frecuente sobre temas cercanos.',
    'B1': 'Comprende las ideas principales de textos claros sobre temas conocidos.',
    'B+': 'Supera las preguntas de mayor complejidad de la prueba.',
}


def _plano(t):
    t = unicodedata.normalize('NFKD', str(t or '')).encode('ascii', 'ignore').decode().lower()
    return ' '.join(t.split())


def prueba_de(nombre):
    """La prueba de Saber 11 que corresponde al nombre de un área ('' si ninguna)."""
    n = _plano(nombre)
    for clave, p in PRUEBAS.items():
        if any(w in n for w in p['palabras']):
            return clave
    return ''


def nivel(puntaje, prueba=''):
    cortes = PRUEBAS.get(prueba or 'CN')['cortes']
    nombres = NIVELES_INGLES if prueba == 'ING' else NIVELES
    k = sum(1 for c in cortes if puntaje > c)
    return nombres[k]


def _clave_persona(h):
    if h.estudiante_id:
        return f'e{h.estudiante_id}'
    if h.integrante_id:
        return f'i{h.integrante_id}'
    doc = ''.join(ch for ch in (h.documento_libre or '') if ch.isalnum())
    if doc:
        return f'd{doc}'
    return f'n{_plano(h.nombre_libre)}' if h.nombre_libre else f'h{h.pk}'


_GRADOS_PALABRA = {'transicion': 0, 'primero': 1, 'segundo': 2, 'tercero': 3, 'cuarto': 4, 'quinto': 5, 'sexto': 6,
                   'septimo': 7, 'octavo': 8, 'noveno': 9, 'decimo': 10, 'undecimo': 11, 'once': 11, 'doce': 12}


def numero_de_grado(valor):
    """6 de «6», «6°», «6.º», «Grado 6», «Sexto», «601», «6-1», «Sexto B»; None si no se reconoce.
    (Tres o más cifras: las dos últimas son el grupo: 601 → 6, 1102 → 11.)"""
    import re
    import unicodedata
    t = unicodedata.normalize('NFKD', str(valor or '')).encode('ascii', 'ignore').decode().lower()
    for palabra, n in _GRADOS_PALABRA.items():
        if re.search(rf'\b{palabra}\b', t):
            return n
    m = re.search(r'\d+', t)
    if not m:
        return None
    dig = m.group(0)
    if len(dig) >= 3:
        dig = dig[:-2]
    n = int(dig)
    return n if 0 <= n <= 13 else None


def grado_de(h):
    """«Grado 6» del estudiante de la hoja. Sale del grado del curso y, si el curso no lo tiene (o lo tiene escrito
    distinto: «6°», «Sexto»), del nombre del curso: así 601, 602 y «Sexto B» quedan todos en «Grado 6».
    Si no se puede saber, el nombre del curso o del grupo."""
    from . import hojas as hojas_mod
    try:
        c = hojas_mod.curso_de_hoja(h)
    except Exception:
        c = None
    n = None
    if c is not None:
        n = numero_de_grado(getattr(c, 'grado', None))
        if n is None:
            n = numero_de_grado(c.nombre)
    elif h.integrante_id and getattr(h.integrante, 'grupo', None):
        n = numero_de_grado(h.integrante.grupo.nombre)
    if n is not None:
        return f'Grado {n}'
    return _curso_de(h)


def curso_de(h):
    return _curso_de(h)


def _curso_de(h):
    from . import hojas as hojas_mod
    try:
        c = hojas_mod.curso_de_hoja(h)
    except Exception:
        c = None
    if c is not None:
        return c.nombre
    if h.integrante_id and getattr(h.integrante, 'grupo', None):
        return h.integrante.grupo.nombre
    return 'Sin curso'


def _desv(xs):
    if len(xs) < 2:
        return 0.0
    m = sum(xs) / len(xs)
    return math.sqrt(sum((x - m) ** 2 for x in xs) / (len(xs) - 1))


def _prom(xs):
    return sum(xs) / len(xs) if xs else 0.0


def construir(examenes, titulo=None, areas_fijas=None, incluir=None):
    """Todo lo que necesitan los informes. examenes: lista de Examen (uno o varios unidos).
    areas_fijas: {clave_area: 'MAT'} para forzar a qué prueba de Saber 11 corresponde un área.
    incluir: función hoja -> bool para quedarse con una parte (un grado, un curso, los escogidos)."""
    from .models import Hoja
    areas_fijas = areas_fijas or {}
    areas, por_area_preguntas = [], {}
    for ex in examenes:
        preguntas = list(ex.preguntas.filter(anulada=False, es_control=False).select_related('bloque').order_by('numero'))
        bloques = list(ex.bloques.all())
        grupos = defaultdict(list)
        for p in preguntas:
            grupos[p.bloque_id if bloques else None].append(p)
        orden = [b.id for b in bloques] + ([None] if None in grupos and bloques else []) if bloques else [None]
        for bid in orden:
            ps = grupos.get(bid) or []
            if not ps:
                continue
            nombre = next((b.nombre for b in bloques if b.id == bid), None) or (ex.titulo if len(examenes) > 1 or not bloques else 'Otras preguntas')
            if not bloques and len(examenes) == 1:
                nombre = ex.titulo
            clave = f'{ex.pk}-{bid or 0}'
            fija = areas_fijas.get(clave)
            prueba = '' if fija == 'NO' else (fija if fija in PRUEBAS else prueba_de(nombre))
            areas.append({'clave': clave, 'nombre': nombre, 'examen': ex, 'prueba': prueba, 'n': len(ps),
                          'peso': PRUEBAS[prueba]['peso'] if prueba else 1})
            por_area_preguntas[clave] = ps

    personas = {}
    for ex in examenes:
        hojas = (ex.hojas.filter(estado__in=('calificada', 'revisar'))
                 .select_related('estudiante__user', 'estudiante__curso', 'integrante__grupo').prefetch_related('respuestas'))
        for h in hojas:
            if incluir is not None and not incluir(h):
                continue
            k = _clave_persona(h)
            per = personas.setdefault(k, {'clave': k, 'nombre': h.nombre, 'documento': h.documento, 'curso': _curso_de(h),
                                          'grado': grado_de(h), 'hojas': {}, 'marcas': {}})
            per['hojas'][ex.pk] = h
            per['marcas'].update({r.pregunta_id: r.marcada for r in h.respuestas.all()})

    # Puntajes por área y por persona
    for per in personas.values():
        per['areas'] = {}
        for a in areas:
            if a['examen'].pk not in per['hojas']:
                continue
            ps = por_area_preguntas[a['clave']]
            bien = sum(1 for p in ps if p.acierta(per['marcas'].get(p.id)))
            puntaje = round(100 * bien / len(ps)) if ps else 0
            per['areas'][a['clave']] = {'bien': bien, 'total': len(ps), 'puntaje': puntaje, 'nivel': nivel(puntaje, a['prueba'])}
        pesos = [(per['areas'][a['clave']]['puntaje'], a['peso']) for a in areas if a['clave'] in per['areas']]
        sw = sum(w for _, w in pesos)
        per['global'] = round(5 * sum(p * w for p, w in pesos) / sw) if sw else 0
        per['completo'] = len(per['areas']) == len(areas)
    lista = sorted(personas.values(), key=lambda p: (-p['global'], p['nombre']))
    globales = [p['global'] for p in lista]
    for p in lista:
        p['percentil'] = round(100 * sum(1 for g in globales if g < p['global']) / len(globales)) if globales else 0
    for a in areas:                      # percentil dentro de cada área, entre quienes la presentaron
        pts = [p['areas'][a['clave']]['puntaje'] for p in lista if a['clave'] in p['areas']]
        for p in lista:
            if a['clave'] in p['areas']:
                v = p['areas'][a['clave']]['puntaje']
                p['areas'][a['clave']]['percentil'] = round(100 * sum(1 for x in pts if x < v) / len(pts))

    # Por área: promedio, desviación, niveles, por curso
    cursos = sorted({p['curso'] for p in lista})
    for a in areas:
        pts = [p['areas'][a['clave']]['puntaje'] for p in lista if a['clave'] in p['areas']]
        a['presentaron'] = len(pts)
        a['promedio'] = round(_prom(pts), 1)
        a['desviacion'] = round(_desv(pts), 1)
        nombres = NIVELES_INGLES if a['prueba'] == 'ING' else NIVELES
        a['niveles'] = [{'nivel': nv, 'n': sum(1 for p in lista if a['clave'] in p['areas'] and p['areas'][a['clave']]['nivel'] == nv)}
                        for nv in nombres]
        for x in a['niveles']:
            x['pct'] = round(100 * x['n'] / len(pts)) if pts else 0
        a['por_curso'] = {c: round(_prom([p['areas'][a['clave']]['puntaje'] for p in lista
                                          if p['curso'] == c and a['clave'] in p['areas']]), 1) for c in cursos}
        a['prueba_nombre'] = PRUEBAS[a['prueba']]['nombre'] if a['prueba'] else 'No es de Saber 11'

    # Análisis por pregunta (dificultad, discriminación y distractor) y por competencia (etiquetas)
    preguntas_info, etiquetas = [], defaultdict(lambda: {'bien': 0, 'total': 0, 'area': '', 'preguntas': []})
    orden_global = {p['clave']: i for i, p in enumerate(lista)}
    tam = max(1, int(len(lista) * .27))
    altos, bajos = {p['clave'] for p in lista[:tam]}, {p['clave'] for p in lista[-tam:]}
    hay_grupos = len(lista) >= 6 and not (altos & bajos)
    for a in areas:
        for q in por_area_preguntas[a['clave']]:
            quienes = [p for p in lista if a['examen'].pk in p['hojas']]
            reparto = defaultdict(int)
            bien = ab = bb = 0
            for p in quienes:
                m = p['marcas'].get(q.id) or ''
                reparto[m or '—'] += 1
                if q.acierta(m):
                    bien += 1
                    ab += p['clave'] in altos
                    bb += p['clave'] in bajos
            n = len(quienes) or 1
            dist = sorted(((k, v) for k, v in reparto.items() if k != '—' and not q.acierta(k)), key=lambda x: -x[1])
            info = {'area': a['nombre'], 'numero': q.numero, 'examen': a['examen'].titulo, 'correcta': q.rotulo_correctas(),
                    'etiquetas': q.lista_etiquetas(), 'pct': round(100 * bien / n),
                    'disc': round(ab / tam - bb / tam, 2) if hay_grupos else None,
                    'distractor': (q.rotulo_marcada(dist[0][0]), round(100 * dist[0][1] / n)) if dist else None,
                    'blanco': round(100 * reparto.get('—', 0) / n), 'id': q.id}
            preguntas_info.append(info)
            for et in q.lista_etiquetas():
                e = etiquetas[(a['clave'], et)]
                e['bien'] += bien
                e['total'] += len(quienes)
                e['area'] = a['nombre']
                e['preguntas'].append(q.numero)
    comp = [{'area': v['area'], 'etiqueta': k[1], 'clave': k, 'pct': round(100 * v['bien'] / v['total']) if v['total'] else 0,
             'preguntas': v['preguntas']} for k, v in etiquetas.items()]
    comp.sort(key=lambda c: (c['area'], c['pct']))

    resumen = {
        'presentaron': len(lista), 'completos': sum(1 for p in lista if p['completo']),
        'promedio': round(_prom(globales), 1), 'desviacion': round(_desv(globales), 1),
        'maximo': max(globales) if globales else 0, 'minimo': min(globales) if globales else 0,
        'p25': _cuantil(globales, .25), 'p50': _cuantil(globales, .5), 'p75': _cuantil(globales, .75),
        'cursos': [{'curso': c, 'n': sum(1 for p in lista if p['curso'] == c),
                    'promedio': round(_prom([p['global'] for p in lista if p['curso'] == c]), 1)} for c in cursos],
        'hay_grupos': hay_grupos,
    }
    return {'titulo': titulo or (examenes[0].titulo if len(examenes) == 1 else 'Prueba unida'), 'examenes': examenes,
            'areas': areas, 'personas': lista, 'preguntas': preguntas_info, 'competencias': comp, 'resumen': resumen,
            'por_area_preguntas': por_area_preguntas, '_orden': orden_global}


def _cuantil(xs, q):
    if not xs:
        return 0
    s = sorted(xs)
    i = (len(s) - 1) * q
    lo, hi = int(math.floor(i)), int(math.ceil(i))
    return round(s[lo] + (s[hi] - s[lo]) * (i - lo))


def de_estudiante(datos, clave):
    """El informe de un estudiante: sus áreas frente al grupo, sus competencias, sus fallas y sus conclusiones."""
    per = next((p for p in datos['personas'] if p['clave'] == clave), None)
    if per is None:
        return None
    areas = []
    for a in datos['areas']:
        d = per['areas'].get(a['clave'])
        if d:
            nombres = NIVELES_INGLES if a['prueba'] == 'ING' else NIVELES
            areas.append({**d, 'nombre': a['nombre'], 'grupo': a['promedio'], 'prueba': a['prueba'], 'clave': a['clave'],
                          'diferencia': round(d['puntaje'] - a['promedio']), 'peso': a['peso'],
                          'ponderado': d['puntaje'] * a['peso'], 'niveles_nombres': nombres,
                          'escalon': nombres.index(d['nivel']) if d['nivel'] in nombres else 0,
                          'que_dice': QUE_DICE_NIVEL.get(d['nivel'], '') or QUE_DICE_INGLES.get(d['nivel'], '')})
    # Competencias: su acierto en cada etiqueta frente al del grupo
    comp = []
    grupo = {c['clave']: c['pct'] for c in datos['competencias']}
    for a in datos['areas']:
        if a['clave'] not in per['areas']:
            continue
        por = defaultdict(lambda: [0, 0])
        for q in datos['por_area_preguntas'][a['clave']]:
            for et in q.lista_etiquetas():
                por[et][1] += 1
                por[et][0] += q.acierta(per['marcas'].get(q.id))
        for et, (b, t) in por.items():
            comp.append({'area': a['nombre'], 'etiqueta': et, 'bien': b, 'total': t, 'pct': round(100 * b / t),
                         'grupo': grupo.get((a['clave'], et), 0)})
    # Preguntas que falló
    falladas = []
    for a in datos['areas']:
        if a['clave'] not in per['areas']:
            continue
        for q in datos['por_area_preguntas'][a['clave']]:
            m = per['marcas'].get(q.id) or ''
            if not q.acierta(m):
                info = next((x for x in datos['preguntas'] if x['id'] == q.id), {})
                falladas.append({'area': a['nombre'], 'numero': q.numero, 'marcada': q.rotulo_marcada(m),
                                 'correcta': q.rotulo_correctas(), 'etiquetas': ', '.join(q.lista_etiquetas()),
                                 'grupo_pct': info.get('pct', 0)})
    conclusiones = _conclusiones(per, areas, comp, falladas, datos)
    for x in areas:                      # sus fortalezas y lo que debe reforzar dentro de cada área
        mias = [c for c in comp if c['area'] == x['nombre']]
        x['fuertes'] = [c for c in mias if c['pct'] >= 70]
        x['reforzar'] = [c for c in mias if c['pct'] < 50]
    suma_pesos = sum(x['peso'] for x in areas)
    calculo = {'suma': sum(x['ponderado'] for x in areas), 'pesos': suma_pesos,
               'promedio': round(sum(x['ponderado'] for x in areas) / suma_pesos, 2) if suma_pesos else 0}
    return {'calculo': calculo, 'n_areas_total': len(datos['areas']),'persona': per, 'areas': areas, 'competencias': comp, 'falladas': falladas, 'conclusiones': conclusiones,
            'presentaron': datos['resumen']['presentaron'], 'promedio_global': datos['resumen']['promedio']}


def _conclusiones(per, areas, comp, falladas, datos):
    """Frases cortas y concretas, a partir de los números (sin juicios sobre la persona)."""
    out = []
    g, pg = per['global'], datos['resumen']['promedio']
    if g >= pg + 10:
        out.append(f'Su puntaje global ({g}) está por encima del promedio del grupo ({pg}); queda en el percentil {per["percentil"]}.')
    elif g <= pg - 10:
        out.append(f'Su puntaje global ({g}) está por debajo del promedio del grupo ({pg}); queda en el percentil {per["percentil"]}.')
    else:
        out.append(f'Su puntaje global ({g}) está cerca del promedio del grupo ({pg}); queda en el percentil {per["percentil"]}.')
    if len(areas) > 1:
        mejor = max(areas, key=lambda a: a['puntaje'])
        peor = min(areas, key=lambda a: a['puntaje'])
        out.append(f'Su área más fuerte es {mejor["nombre"]} ({mejor["puntaje"]}/100, {mejor["nivel"]}) y la que más necesita '
                   f'reforzar es {peor["nombre"]} ({peor["puntaje"]}/100, {peor["nivel"]}).')
    fuertes = [c for c in comp if c['total'] >= 2 and c['pct'] >= 70 and c['pct'] >= c['grupo']]
    debiles = [c for c in comp if c['total'] >= 2 and (c['pct'] < 50 or c['pct'] <= c['grupo'] - 15)]
    if fuertes:
        out.append('Domina: ' + '; '.join(f'{c["etiqueta"]} ({c["bien"]} de {c["total"]})' for c in sorted(fuertes, key=lambda c: -c['pct'])[:4]) + '.')
    if debiles:
        out.append('Para reforzar: ' + '; '.join(f'{c["etiqueta"]} ({c["bien"]} de {c["total"]})' for c in sorted(debiles, key=lambda c: c['pct'])[:4]) + '.')
    faciles = [f for f in falladas if f['grupo_pct'] >= 70]
    if faciles:
        out.append(f'Falló {len(faciles)} pregunta{"s" if len(faciles) != 1 else ""} que la mayoría del grupo (70 % o más) acertó: '
                   'vale la pena revisarlas con calma, suelen ser descuidos o temas puntuales.')
    blancas = [f for f in falladas if f['marcada'] == 'sin marcar']
    if len(blancas) >= 3:
        out.append(f'Dejó {len(blancas)} preguntas sin marcar: conviene practicar el manejo del tiempo y responder todas.')
    return out


def recomendaciones(areas):
    """Lo que puede hacer en casa y en clase, según el nivel de cada área."""
    rec = []
    for a in areas:
        if a['nivel'] in ('Nivel 1', 'A-', 'A1'):
            rec.append(f'{a["nombre"]}: repasar lo básico del área con ejercicios cortos todos los días y pedir acompañamiento del docente.')
        elif a['nivel'] in ('Nivel 2', 'A2'):
            rec.append(f'{a["nombre"]}: pasar de recordar a aplicar: resolver problemas con contexto y explicar por escrito cómo se resolvieron.')
    if not rec:
        rec.append('Mantener la práctica con preguntas de mayor complejidad (argumentar, proponer, interpretar gráficas y textos largos).')
    rec.append('Revisar con el docente las preguntas falladas de la tabla: entender por qué la opción escogida no era la correcta.')
    return rec
