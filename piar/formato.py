"""Cómo se ve el PIAR en cada colegio: lo escoge la docente orientadora (o de apoyo).

Qué secciones salen, qué columnas llena cada docente en sus ajustes (con el título y la
instrucción que ella quiera), y el registro de habilidades (escala 1 a 4 o Sí/No, con
los grupos y afirmaciones que use el colegio). Se guarda en ConfiguracionPiar.formato;
lo que no esté guardado usa lo de fábrica (el formato del MEN, Anexo 2).
"""
import copy
import re

SECCIONES = [
    ('salud', 'Entorno salud (diagnóstico, quién lo emitió, terapias y apoyos de salud)'),
    ('hogar', 'Entorno hogar'),
    ('educativo', 'Entorno educativo (trayectoria escolar)'),
    ('valoracion', 'Descripción del estudiante, fortalezas, barreras, apoyos y expectativas'),
    ('habilidades', 'Valoración pedagógica por nivel (preescolar, primaria, bachillerato): ámbitos, familia, trayectoria'),
    ('ajustes', 'Ajustes razonables por asignatura (los llena cada docente)'),
    ('otras', 'Otras dimensiones: convivencia, socialización, participación, autonomía, autocontrol'),
    ('actores', 'Recomendaciones para el plan de mejoramiento (familia, docentes, directivos, administrativos, pares)'),
    ('acta', 'Acta de acuerdo con la familia'),
]

COLUMNAS = [
    # (clave, título de fábrica, instrucción de fábrica, se puede apagar)
    ('objetivos', 'Objetivos / propósitos de aprendizaje',
     'Para todo el grado, de acuerdo con los EBC y los DBA del periodo.', True),
    ('barreras', 'Barreras que se evidencian en el contexto',
     'Actitudinales, comunicativas, metodológicas, didácticas, tecnológicas, institucionales…', True),
    ('tipos', 'Tipo de ajuste', '', True),
    ('ajustes', 'Ajustes razonables (apoyos / estrategias)',
     'Qué va a hacer distinto: materiales, tiempos, forma de explicar, forma de evaluar, ubicación.', False),
    ('apoyos', 'Apoyo requerido',
     'Talento humano, técnico, tecnológico, comunicativo, materiales…', True),
    ('evaluacion', 'Evaluación / seguimiento de los ajustes',
     '¿Funcionaron? En clave de temporalidad, responsable y medios. Puede llenarla al cierre del periodo.', True),
]

OTRAS = ['Convivencia', 'Socialización', 'Participación', 'Autonomía', 'Autocontrol']
ACTORES = [('familia', 'Familia, cuidadores o con quienes vive'), ('docentes', 'Docentes'),
           ('directivos', 'Directivos'), ('administrativos', 'Administrativos'), ('pares', 'Pares (sus compañeros)')]

ESCALAS = {'SNAV': ['Sí', 'No', 'A veces'], '1-4': ['1', '2', '3', '4'], 'SINO': ['Sí', 'No', 'N/A']}
NOMBRES_ESCALA = {'SNAV': 'Sí / No / A veces', '1-4': 'Escala de 1 a 4 (1 nunca, 4 siempre)', 'SINO': 'Sí / No / N/A'}

# Un modelo de valoración por nivel: al estudiante le sale el de su grado.
NIVELES_PIAR = [('PRE', 'Preescolar'), ('PRI', 'Primaria'), ('BACH', 'Bachillerato (básica, media y técnica)')]


def nivel_de_grado(grado):
    if grado is None:
        return 'BACH'
    try:
        g = int(grado)
    except (TypeError, ValueError):
        return 'BACH'
    return 'PRE' if g <= 0 else 'PRI' if g <= 5 else 'BACH'

# Los grupos del Anexo 2 del MEN (como vienen en los formatos de los colegios). Una línea
# que empieza con «## » es un grupo; «# » un subtítulo dentro del grupo; lo demás, afirmaciones.
HABILIDADES = """## ATENCIÓN
El estudiante reporta sentirse descansado y haber dormido bien.
# Atención selectiva
Se centra de forma específica en aquellos elementos del ambiente que son relevantes para la tarea que debe desarrollar.
Consigue ignorar aquella información del contexto que no le es útil para lograr el desarrollo de la actividad propuesta.
Cuando se distrae, logra la atención a la meta que debe cumplir y retoma la tarea con facilidad.
# Atención sostenida
Logra mantenerse concentrado en clase, por lapsos de 40 a 45 minutos.
No se distrae fácilmente, a pesar de que en el ambiente haya estímulos que pueden dispersarlo.
Si la tarea o actividad lo demandan, cambia el foco de atención y deja el anterior con facilidad.
# Atención dividida
Es capaz de mantenerse atento a varias fuentes o estímulos sin perder el hilo de la clase o de la actividad.
Puede tomar apuntes o notas de la clase de buena calidad, sin desviarse del tema que se está tratando.
Sigue apropiadamente instrucciones con varios comandos.
## PROCESO DE RAZONAMIENTO
Es hábil para plantear hipótesis o explicaciones frente a fenómenos o situaciones que se exponen en clase.
Para plantear hipótesis o explicaciones, hace un uso adecuado de sus conocimientos previos.
Ante un problema identifica el punto de partida (qué información tiene) y el de llegada (qué debe contestar).
Sabe qué procedimientos de los aprendidos le sirven para solucionar un problema.
Genera un plan o una alternativa de solución adecuada para enfrentar el problema.
Mientras soluciona un problema, reconoce dónde se equivoca y se autocorrige.
Verifica si su solución es correcta.
Puede transferir un conocimiento que domina para explicar un fenómeno o situación poco conocida.
En una discusión o debate, presenta un argumento claro que dé cuenta de su opinión o posición.
Reconoce los argumentos a favor y en contra de los suyos.
Es capaz de organizar y relacionar los conceptos de un tema dado, de modo adecuado.
## COMPETENCIAS LECTORAS Y ESCRITURALES
Evidencia una adecuada lectura «automática» (lee con fluidez, respetando los signos de puntuación y con la entonación adecuada).
En textos poco complejos identifica la idea principal y las secundarias.
En textos complejos identifica la idea principal y las secundarias.
Realiza inferencias que vinculan sus conocimientos con los planteamientos del texto.
Es hábil para hacer esquemas o diagramas con los conceptos fundamentales de un texto y sus relaciones.
Tiene una buena escritura «automática» (no omite letras o sílabas, no pega palabras, no confunde letras).
Escribe con buena redacción.
Escribe con buena ortografía.
En sus escritos presenta un argumento claro que desarrolla a lo largo del texto.
Planifica cómo va a escribir un texto y tiene claridad en lo que va a tratar en cada párrafo.
## MEMORIA
Comenta experiencias de su vida cotidiana en diversos espacios y contextos.
Vincula diversas emociones con sus experiencias y puede narrar con detalle experiencias significativas con sus seres queridos.
Habla de sí mismo y de su proyección en su vida personal, familiar y escolar.
Utiliza una red de conceptos y de vocabulario altamente enriquecida.
Evidencia conocimientos muy especializados sobre un tema particular.
El vocabulario que domina resulta poco frecuente, comparado con el de sus compañeros o personas de su edad.
Recuerda los conocimientos aprendidos previamente sin mayor dificultad.
## FUNCIONES EJECUTIVAS
Organiza su tiempo para poder cumplir con las tareas escolares.
Es flexible ante los cambios y los imprevistos.
Planifica sus actividades día tras día y se ajusta a lo que ha programado.
Considera diversas rutas para resolver una tarea y elige la más adecuada.
Contempla diversas posibilidades para enfrentar una actividad y se acomoda si la que quiere no se puede implementar.
Tiene adecuadas estrategias de monitoreo y seguimiento de sus acciones, y reconoce cuándo debe modificar lo planeado.
## LENGUAJE Y COMUNICACIÓN
Puede comunicarse con otros por vía oral o por otras vías (lengua de señas, tableros de apoyo, etc.).
Es capaz de seguir el hilo de las conversaciones.
Expresa sus ideas con frases gramaticalmente correctas.
Busca hacerse entender en cuanto a lo que requiere o necesita.
Describe acontecimientos familiares o experiencias cotidianas, relacionados con lo que se está hablando.
Actúa de forma interesada cuando otros le hablan.
Interpreta adecuadamente dobles sentidos (refranes, frases hechas, dichos populares, metáforas).
Tiene un sentido del humor apropiado para su edad.
Es recíproco en los intercambios comunicativos con otras personas.
Su estilo de conversación parece extraño (demasiado formal, vocabulario rebuscado, sin expresiones coloquiales).
Emplea un tono de voz ajustado a lo que dice."""

# Quiénes firman. Cada colegio escoge cuáles van en el PIAR y cuáles en el acta, y si las firmas
# salen en líneas (como siempre) o en un cuadro Nombre · Cargo · Firma (como el acta del MEN).
FIRMANTES = [
    ('docentes', 'Docentes de cada asignatura (nombre y área)'),
    ('director', 'Director(a) de grupo'),
    ('orientador', 'Docente orientador(a)'),
    ('apoyo', 'Docente de apoyo pedagógico'),
    ('coordinador', 'Coordinador(a)'),
    ('rector', 'Rector(a)'),
    ('acudiente', 'Acudiente / familia'),
    ('estudiante', 'Estudiante'),
]
ESTILOS_FIRMA = [('lineas', 'Líneas de firma (como hasta ahora)'), ('cuadro', 'Cuadro: nombre, cargo y firma (como el acta)')]

DEFECTO = {
    'secciones': {k: True for k, _ in SECCIONES},
    'columnas': {k: {'activa': True, 'titulo': t, 'ayuda': a} for k, t, a, _ in COLUMNAS},
    'modelos': None,              # se llena abajo con los de cada nivel
    'instrucciones': '',          # lo que la orientadora quiere que lean todos los docentes al llenar
    'firmas': {'estilo': 'lineas',
               'piar': ['docentes', 'director', 'orientador', 'acudiente', 'rector'],
               'acta': ['acudiente', 'estudiante', 'docentes', 'orientador', 'rector'],
               'otros_piar': '', 'otros_acta': ''},
}


def _modelos_de_fabrica():
    from . import plantillas
    return {'PRE': {'escala': 'SNAV', 'habilidades': plantillas.PREESCOLAR},
            'PRI': {'escala': 'SNAV', 'habilidades': plantillas.PRIMARIA},
            'BACH': {'escala': 'SNAV', 'habilidades': plantillas.BACHILLERATO}}


def plantillas_para_cargar():
    """Lo que la orientadora puede cargar en un modelo para partir de ahí."""
    from . import plantillas
    return [('PRE', 'Preescolar (General Santander)', plantillas.PREESCOLAR),
            ('PRI', 'Primaria (General Santander)', plantillas.PRIMARIA),
            ('BACH', 'Bachillerato (General Santander)', plantillas.BACHILLERATO),
            ('MEN', 'Registro de habilidades del MEN (Anexo 2)', HABILIDADES)]


def modelo_de(f, piar):
    """El modelo de valoración que le toca a este PIAR: el que se escogió, o el del grado del estudiante."""
    nivel = (piar.habilidades or {}).get('modelo')
    if nivel not in f['modelos']:
        curso = piar.estudiante.curso if piar.estudiante.curso_id else None
        nivel = nivel_de_grado(curso.grado if curso else None)
    return dict(f['modelos'][nivel], nivel=nivel, nombre=dict(NIVELES_PIAR)[nivel])


def de(colegio):
    """El formato del colegio, completo (lo que falte sale de fábrica)."""
    from .models import ConfiguracionPiar
    guardado = ConfiguracionPiar.de(colegio).formato or {}
    f = completar(guardado)
    if not isinstance(guardado.get('firmas'), dict) and not colegio.firma_director.get('piar', True):
        f['firmas']['piar'] = [k for k in f['firmas']['piar'] if k != 'director']
    return f


def completar(guardado):
    f = copy.deepcopy(DEFECTO)
    f['modelos'] = _modelos_de_fabrica()
    if not isinstance(guardado, dict):
        return f
    for k, v in (guardado.get('secciones') or {}).items():
        if k in f['secciones']:
            f['secciones'][k] = bool(v)
    for k, v in (guardado.get('columnas') or {}).items():
        if k in f['columnas'] and isinstance(v, dict):
            c = f['columnas'][k]
            c['activa'] = bool(v.get('activa', True)) or k == 'ajustes'
            c['titulo'] = (v.get('titulo') or '').strip() or c['titulo']
            if v.get('ayuda') is not None:
                c['ayuda'] = v['ayuda'].strip()
    modelos = guardado.get('modelos')
    if isinstance(modelos, dict):
        for nivel, m in modelos.items():
            if nivel in f['modelos'] and isinstance(m, dict):
                if m.get('escala') in ESCALAS:
                    f['modelos'][nivel]['escala'] = m['escala']
                if (m.get('habilidades') or '').strip():
                    f['modelos'][nivel]['habilidades'] = m['habilidades']
    elif (guardado.get('habilidades') or '').strip():
        # Formato de antes (un solo modelo): vale para los tres niveles
        for m in f['modelos'].values():
            m['habilidades'] = guardado['habilidades']
            m['escala'] = guardado.get('escala') if guardado.get('escala') in ESCALAS else '1-4'
    f['instrucciones'] = (guardado.get('instrucciones') or '').strip()
    fi = guardado.get('firmas')
    if isinstance(fi, dict):
        validos = {k for k, _ in FIRMANTES}
        if fi.get('estilo') in dict(ESTILOS_FIRMA):
            f['firmas']['estilo'] = fi['estilo']
        for doc in ('piar', 'acta'):
            if isinstance(fi.get(doc), list):
                f['firmas'][doc] = [k for k in fi[doc] if k in validos]
            f['firmas'][f'otros_{doc}'] = (fi.get(f'otros_{doc}') or '').strip()
    return f


def firmantes(piar, f, doc='piar', quienes=None, otros=None):
    """[{'nombre', 'cargo'}] de quienes firman ese documento, en el orden de FIRMANTES.

    `quienes` y `otros` cambian lo del formato solo para esa impresión."""
    from notas.models import AsignacionDocente
    est = piar.estudiante
    quienes = f['firmas'][doc] if quienes is None else quienes
    otros = f['firmas'][f'otros_{doc}'] if otros is None else otros
    ficha = getattr(est, 'ficha', None)
    salida = []
    for clave, _ in FIRMANTES:
        if clave not in quienes:
            continue
        if clave == 'docentes':
            vistos = set()
            for a in (AsignacionDocente.objects.filter(curso_id=est.curso_id, docente__isnull=False)
                      .select_related('docente__user', 'materia').order_by('materia__nombre')):
                nombre = a.docente.user.get_full_name() or a.docente.user.username
                if (nombre, a.materia.nombre) not in vistos:
                    vistos.add((nombre, a.materia.nombre))
                    salida.append({'nombre': nombre, 'cargo': f'Docente · {a.materia.nombre}'})
        elif clave == 'director':
            d = est.curso.director_grado if est.curso_id and est.curso.director_grado_id else None
            salida.append({'nombre': d.user.get_full_name() if d else '', 'cargo': 'Director(a) de grupo'})
        elif clave == 'rector':
            salida.append({'nombre': piar.colegio.nombre_rector or '', 'cargo': 'Rector(a)'})
        elif clave == 'acudiente':
            nombre = (getattr(ficha, 'nombre_acudiente', '') or getattr(ficha, 'nombre_madre', '') or '') if ficha else ''
            salida.append({'nombre': nombre, 'cargo': 'Acudiente / familia'})
        elif clave == 'estudiante':
            salida.append({'nombre': est.user.get_full_name(), 'cargo': 'Estudiante'})
        else:
            salida.append({'nombre': '', 'cargo': dict(FIRMANTES)[clave]})
    for linea in (otros or '').splitlines():
        t = linea.strip()
        if not t:
            continue
        nombre, _, cargo = t.partition('—') if '—' in t else t.partition(' - ')
        salida.append({'nombre': nombre.strip(), 'cargo': cargo.strip()} if cargo else {'nombre': '', 'cargo': t})
    return salida


def _clave(texto):
    t = re.sub(r'[^a-z0-9]+', '-', texto.lower())[:60].strip('-')
    return t or 'x'


def grupos(modelo):
    """[{'nombre', 'filas': [...]}] de un modelo de valoración. Cada fila: {'tipo', 'texto', 'clave',
    'opciones'}; tipo 'sub' (subtítulo), 'item' (escala), 'abierta' (texto), 'opcion' (una) o 'varias'."""
    salida, actual, vistas = [], None, set()
    for linea in (modelo.get('habilidades') or '').splitlines():
        t = linea.strip()
        if not t:
            continue
        if t.startswith('## '):
            actual = {'nombre': t[3:].strip(), 'filas': []}
            salida.append(actual)
            continue
        if actual is None:
            actual = {'nombre': 'HABILIDADES', 'filas': []}
            salida.append(actual)
        if t.startswith('# '):
            actual['filas'].append({'tipo': 'sub', 'texto': t[2:].strip()})
            continue
        tipo, opciones = 'item', []
        if t[:2] in ('? ', '* ', '+ '):
            tipo = {'?': 'abierta', '*': 'opcion', '+': 'varias'}[t[0]]
            t = t[2:].strip()
            if tipo != 'abierta':
                t, _, resto = t.partition(':')
                opciones = [o.strip() for o in resto.split('|') if o.strip()]
                if not opciones:
                    tipo = 'abierta'
        else:
            t = re.sub(r'^(\d+|[a-z])[.)]\s+', '', t)
        clave = f'{_clave(actual["nombre"])}:{_clave(t)}'
        base, n = clave, 2
        while clave in vistas:
            clave, n = f'{base}-{n}', n + 1
        vistas.add(clave)
        actual['filas'].append({'tipo': tipo, 'texto': t.strip(), 'clave': clave, 'opciones': opciones})
    return salida


def leer_respuestas(modelo, datos, anteriores=None):
    """Las respuestas del formulario (h_<clave>) que valen para ese modelo."""
    validos = set(ESCALAS[modelo['escala']])
    salida = {k: v for k, v in (anteriores or {}).items() if ':' in k}   # las de otros modelos no se pierden
    for g in grupos(modelo):
        for fila in g['filas']:
            if fila['tipo'] == 'sub':
                continue
            nombre = f'h_{fila["clave"]}'
            if fila['tipo'] == 'varias':
                valor = [o for o in datos.getlist(nombre) if o in fila['opciones']]
            else:
                valor = (datos.get(nombre) or '').strip()
                if fila['tipo'] == 'item' and valor not in validos:
                    valor = ''
                if fila['tipo'] == 'opcion' and valor not in fila['opciones']:
                    valor = ''
                valor = valor[:3000]
            if valor:
                salida[fila['clave']] = valor
            else:
                salida.pop(fila['clave'], None)
    return salida


def alertas_habilidades(modelo, respuestas):
    """Grupos donde más del 40 % de las afirmaciones quedaron en 1 o 2 (escala 1-4) o en No."""
    bajas = {'1', '2'} if modelo['escala'] == '1-4' else {'No'}
    out = []
    for g in grupos(modelo):
        items = [f for f in g['filas'] if f['tipo'] == 'item']
        valoradas = [f for f in items if (respuestas or {}).get(f['clave'])]
        if valoradas and sum(1 for f in valoradas if respuestas[f['clave']] in bajas) > 0.4 * len(valoradas):
            out.append(g['nombre'])
    return out
