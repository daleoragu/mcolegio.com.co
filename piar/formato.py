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
    ('habilidades', 'Registro de habilidades (atención, memoria, razonamiento, lenguaje…)'),
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

ESCALAS = {'1-4': ['1', '2', '3', '4'], 'SINO': ['Sí', 'No', 'N/A']}

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

DEFECTO = {
    'secciones': {k: True for k, _ in SECCIONES},
    'columnas': {k: {'activa': True, 'titulo': t, 'ayuda': a} for k, t, a, _ in COLUMNAS},
    'escala': '1-4',
    'habilidades': HABILIDADES,
    'instrucciones': '',          # lo que la orientadora quiere que lean todos los docentes al llenar
}


def de(colegio):
    """El formato del colegio, completo (lo que falte sale de fábrica)."""
    from .models import ConfiguracionPiar
    guardado = ConfiguracionPiar.de(colegio).formato or {}
    return completar(guardado)


def completar(guardado):
    f = copy.deepcopy(DEFECTO)
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
    if guardado.get('escala') in ESCALAS:
        f['escala'] = guardado['escala']
    if (guardado.get('habilidades') or '').strip():
        f['habilidades'] = guardado['habilidades']
    f['instrucciones'] = (guardado.get('instrucciones') or '').strip()
    return f


def _clave(texto):
    t = re.sub(r'[^a-z0-9]+', '-', texto.lower())[:60].strip('-')
    return t or 'x'


def grupos(formato):
    """[{'nombre', 'filas': [{'tipo': 'sub'|'item', 'texto', 'clave'}]}] del registro de habilidades."""
    salida, actual, vistas = [], None, set()
    for linea in (formato.get('habilidades') or '').splitlines():
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
        t = re.sub(r'^(\d+|[a-z])[.)]\s+', '', t)
        clave = f'{_clave(actual["nombre"])}:{_clave(t)}'
        base, n = clave, 2
        while clave in vistas:
            clave, n = f'{base}-{n}', n + 1
        vistas.add(clave)
        actual['filas'].append({'tipo': 'item', 'texto': t, 'clave': clave})
    return salida


def alertas_habilidades(formato, respuestas):
    """Grupos donde más del 40 % de las afirmaciones quedaron en 1 o 2 (escala 1-4) o en No."""
    bajas = {'1', '2'} if formato['escala'] == '1-4' else {'No'}
    out = []
    for g in grupos(formato):
        items = [f for f in g['filas'] if f['tipo'] == 'item']
        valoradas = [f for f in items if (respuestas or {}).get(f['clave'])]
        if valoradas and sum(1 for f in valoradas if respuestas[f['clave']] in bajas) > 0.4 * len(valoradas):
            out.append(g['nombre'])
    return out
