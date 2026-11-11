"""Con qué bloques arranca cada tipo de documento."""
import uuid


def _id():
    return uuid.uuid4().hex[:8]


def _seccion(titulo, indicacion):
    return {'id': _id(), 'tipo': 'seccion', 'titulo': titulo, 'indicacion': indicacion}


def _texto(html=''):
    return {'id': _id(), 'tipo': 'texto', 'html': html}


def _lineas(n=4):
    return {'id': _id(), 'tipo': 'lineas', 'n': n}


def _pregunta(enunciado='', opciones=None):
    opciones = opciones if opciones is not None else ['', '', '', '']
    return {'id': _id(), 'tipo': 'pregunta', 'modo': 'unica' if opciones else 'abierta', 'enunciado': enunciado,
            'opciones': opciones, 'correcta': None, 'lineas': 0 if opciones else 3, 'puntos': 1}


def _recuadro(estilo, titulo, html=''):
    return {'id': _id(), 'tipo': 'recuadro', 'estilo': estilo, 'titulo': titulo, 'html': html}


def _tabla(filas, encabezado=True):
    return {'id': _id(), 'tipo': 'tabla', 'filas': filas, 'encabezado': encabezado}


RUBRICA = [['Criterio', 'Superior', 'Alto', 'Básico', 'Bajo'],
           ['Contenido y comprensión', '', '', '', ''],
           ['Trabajo en equipo', '', '', '', ''],
           ['Producto o solución', '', '', '', ''],
           ['Presentación y comunicación', '', '', '', '']]


def _objetivo():
    return _recuadro('nota', 'Lo que voy a aprender', '<p>Escriba aquí el objetivo, el DBA o la competencia.</p>')


def _titulo(texto):
    return {'id': _id(), 'tipo': 'titulo', 'texto': texto, 'nivel': 1}


def _datos(campos, privada=False):
    """Tabla de dos columnas: «campo | valor» (el valor queda vacío para llenarlo)."""
    t = _tabla([[c, ''] for c in campos], encabezado=False)
    t['privada'] = privada
    return t


DATOS_CLASE = ['Institución', 'Docente', 'Área / asignatura', 'Grado', 'Periodo', 'Fecha', 'Tema', 'Duración']

# Formatos genéricos: el colegio o el docente les cambia la forma (filas, columnas, nombres) y los llena a mano o con IA.
FORMATOS = {
    'planeacion': lambda: [
        _datos(DATOS_CLASE),
        _seccion('Referentes', 'DBA, estándar o competencia que se trabaja.'),
        _datos(['DBA', 'Estándar / competencia', 'Desempeño esperado', 'Evidencias de aprendizaje']),
        _seccion('Momentos de la clase', ''),
        _tabla([['Momento', 'Actividades', 'Tiempo', 'Recursos'],
                ['Inicio (exploración)', '', '', ''],
                ['Desarrollo (estructuración y práctica)', '', '', ''],
                ['Cierre (transferencia)', '', '', ''],
                ['Evaluación', '', '', '']]),
        _seccion('Diseño Universal para el Aprendizaje (DUA)', 'Cómo llega la clase a todos.'),
        _tabla([['Principio', 'Estrategia en esta clase'],
                ['Representación (varias formas de presentar)', ''],
                ['Acción y expresión (varias formas de mostrar lo aprendido)', ''],
                ['Implicación (motivación y participación)', '']]),
        _datos(['Ajustes para estudiantes con PIAR', 'Observaciones']),
    ],
    'plan_aula': lambda: [
        _datos(['Institución', 'Docente', 'Área / asignatura', 'Grado', 'Periodo', 'Intensidad horaria semanal']),
        _datos(['Pregunta problematizadora', 'Competencias del periodo', 'Criterios de evaluación']),
        _tabla([['Semana', 'Tema', 'DBA / estándar', 'Desempeño', 'Actividades', 'Evaluación']]
               + [[f'Semana {n}', '', '', '', '', ''] for n in range(1, 11)]),
    ],
    'piar': lambda: [
        _texto('<p>Según el Decreto 1421 de 2017. Los datos del estudiante son privados: <b>no se envían a la IA</b>.</p>'),
        _seccion('1. Información del estudiante', 'Datos privados.'),
        _datos(['Nombre del estudiante', 'Documento', 'Grado', 'Edad', 'Fecha de elaboración', 'Docentes que participan'], privada=True),
        _seccion('2. Valoración pedagógica', 'Describa al estudiante sin nombres ni diagnósticos médicos.'),
        _datos(['Fortalezas', 'Gustos e intereses', 'Barreras para el aprendizaje y la participación', 'Apoyos que recibe']),
        _seccion('3. Ajustes razonables por área', ''),
        _tabla([['Área', 'Propósitos / DBA del periodo', 'Barreras identificadas', 'Ajustes razonables (didácticos y evaluativos)', 'Evaluación de los ajustes'],
                ['Matemáticas', '', '', '', ''], ['Lenguaje', '', '', '', ''], ['Ciencias naturales', '', '', '', ''],
                ['Ciencias sociales', '', '', '', ''], ['Inglés', '', '', '', '']]),
        _seccion('4. Compromisos', ''),
        _tabla([['Responsable', 'Compromisos'], ['Docentes', ''], ['Familia', ''], ['Estudiante', ''], ['Institución', '']]),
        _seccion('Firmas', ''),
        _lineas(3),
    ],
    'dua': lambda: [
        _datos(['Docente', 'Área / asignatura', 'Grado', 'Tema']),
        _tabla([['Principio', 'Pauta', 'Estrategia en mi clase'],
                ['Representación (el qué)', 'Percepción: presentar la información de varias formas', ''],
                ['Representación (el qué)', 'Lenguaje y símbolos: aclarar vocabulario y notación', ''],
                ['Representación (el qué)', 'Comprensión: activar saberes previos y destacar ideas clave', ''],
                ['Acción y expresión (el cómo)', 'Acción física: varias formas de responder y moverse', ''],
                ['Acción y expresión (el cómo)', 'Expresión y comunicación: varios medios para mostrar lo aprendido', ''],
                ['Acción y expresión (el cómo)', 'Funciones ejecutivas: metas, planeación y seguimiento', ''],
                ['Implicación (el porqué)', 'Captar el interés: opciones, relevancia y autonomía', ''],
                ['Implicación (el porqué)', 'Mantener el esfuerzo: metas claras, colaboración y retroalimentación', ''],
                ['Implicación (el porqué)', 'Autorregulación: expectativas, estrategias y autoevaluación', '']]),
    ],
}


PLANTILLAS = {
    'guia_momentos': lambda: [
        _objetivo(),
        _seccion('1. Exploración', 'Activemos lo que ya sabemos.'),
        _texto('<p>Una pregunta, una imagen o una situación para despertar el interés.</p>'),
        _lineas(3),
        _seccion('2. Estructuración', 'Aprendamos.'),
        _texto('<p>La explicación del tema, con ejemplos.</p>'),
        _recuadro('recuerda', 'Recuerda', '<p>La idea clave en una o dos frases.</p>'),
        _seccion('3. Práctica', 'Ejercitemos lo aprendido.'),
        _pregunta(),
        _pregunta(opciones=[]),
        _seccion('4. Transferencia', 'Usemos lo aprendido en nuestra vida.'),
        _texto('<p>Una situación del entorno donde se aplica el tema.</p>'),
        _lineas(4),
        _seccion('5. Valoración', '¿Cómo me fue?'),
        _texto('<p>Autoevaluación: ¿qué aprendí?, ¿qué se me dificultó?, ¿qué haré para mejorar?</p>'),
        _lineas(3),
    ],
    'escuela_nueva': lambda: [
        _objetivo(),
        _seccion('A. Actividades básicas · Vivencia', 'Recordemos y compartamos lo que sabemos.'),
        _texto('<p>Trabajo en grupo a partir de una situación cotidiana.</p>'),
        _lineas(3),
        _seccion('B. Fundamentación científica', 'Leamos y comprendamos.'),
        _texto('<p>El concepto explicado con ejemplos.</p>'),
        _recuadro('vocabulario', 'Vocabulario', '<p>Palabras nuevas y su significado.</p>'),
        _seccion('C. Actividades de práctica · Ejercitación', 'Practiquemos solos y en parejas.'),
        _pregunta(),
        _pregunta(opciones=[]),
        _seccion('D. Actividades de aplicación', 'Llevemos lo aprendido a la casa y a la comunidad.'),
        _texto('<p>Una tarea con la familia o la comunidad.</p>'),
        _lineas(4),
    ],
    'taller': lambda: [
        _recuadro('nota', 'Indicaciones', '<p>Lea con atención y responda en el espacio indicado.</p>'),
        _pregunta(),
        _pregunta(),
        _pregunta(opciones=[]),
        _recuadro('reto', 'Reto', '<p>Un problema para quienes terminen primero.</p>'),
    ],
    'evaluacion': lambda: [
        _recuadro('nota', 'Instrucciones', '<p>Cada pregunta tiene cuatro opciones y solo una es correcta.</p>'),
        _pregunta(), _pregunta(), _pregunta(), _pregunta(), _pregunta(),
    ],
    'ficha': lambda: [
        _seccion('Antes de leer', '¿De qué crees que trata el texto?'),
        _lineas(2),
        _seccion('Lectura', ''),
        _texto('<p>Pegue o escriba aquí el texto.</p>'),
        _seccion('Después de leer', 'Responde.'),
        _pregunta(enunciado='Nivel literal: '),
        _pregunta(enunciado='Nivel inferencial: '),
        _pregunta(enunciado='Nivel crítico: ', opciones=[]),
    ],
    'cuadernillo': lambda: [
        _recuadro('nota', 'Instrucciones', '<ol><li>Este cuadernillo tiene preguntas con cuatro opciones de respuesta '
                  '(A, B, C y D) y solo una es correcta.</li><li>Lee el texto o mira el dibujo antes de responder.</li>'
                  '<li>No escribas en el cuadernillo: marca tus respuestas solo en la hoja de respuestas.</li>'
                  '<li>Si necesitas hacer cálculos, usa la hoja de operaciones.</li></ol>'),
        _seccion('Lenguaje', ''),
        {'id': _id(), 'tipo': 'contexto', 'titulo': 'Título del texto', 'html': '<p>Pegue aquí el texto, la '
         'imagen o la gráfica que comparten las preguntas siguientes.</p>', 'imagen': None, 'ancho': 70, 'cubre': 0},
        _pregunta(), _pregunta(),
        _seccion('Matemáticas', ''),
        _pregunta(), _pregunta(),
    ],
    # Estilo Liveworksheets: el docente sube el PDF y pone encima los campos para responder.
    'ficha_pdf': lambda: [
        _recuadro('nota', 'Cómo se arma', '<p>Use el botón <b>Hoja sobre un PDF</b> para subir el PDF o las fotos de la '
                  'guía. Después, encima de cada página, dibuje los espacios para escribir, las casillas y las listas, '
                  'con su respuesta. Este recuadro se puede borrar.</p>'),
    ],
    # --- Modelos pedagógicos -------------------------------------------------------------------
    # Aprendizaje basado en proyectos: una pregunta impulsora, indagación sostenida y un producto que se muestra.
    'abp': lambda: [
        _recuadro('nota', 'Ficha del proyecto', '<p>Complete la tabla. Un proyecto puede integrar varias áreas.</p>'),
        _tabla([['Áreas que integra', ''], ['Grado y duración', ''], ['DBA o competencias', ''], ['Producto final', ''],
                ['Público con quien se socializa', '']], encabezado=False),
        _seccion('1. Pregunta impulsora', 'La pregunta abierta que guía todo el proyecto.'),
        _recuadro('reto', 'Nuestra pregunta', '<p>Ej.: ¿Cómo podemos reducir el consumo de agua en nuestro colegio?</p>'),
        _seccion('2. Lo que sabemos y lo que necesitamos saber', 'Punto de partida de la indagación.'),
        _tabla([['Lo que ya sabemos', 'Lo que necesitamos averiguar'], ['', ''], ['', ''], ['', '']]),
        _seccion('3. Equipos y roles', 'Cada integrante asume un rol y responde por él.'),
        _tabla([['Rol', 'Responsabilidad', 'Integrante'], ['Coordinador', 'Organiza el trabajo y los tiempos', ''],
                ['Investigador', 'Busca y verifica la información', ''], ['Relator', 'Registra avances y decisiones', ''],
                ['Comunicador', 'Prepara la presentación del producto', '']]),
        _seccion('4. Plan de trabajo', 'Hitos con su entregable y su fecha.'),
        _tabla([['Semana', 'Actividad', 'Entregable', 'Fecha'], ['1', '', '', ''], ['2', '', '', ''], ['3', '', '', ''],
                ['4', 'Socialización', 'Producto final', '']]),
        _seccion('5. Investigación', 'Fuentes, entrevistas, experimentos o salidas de campo.'),
        _texto('<p>Indicaciones para investigar y registrar lo encontrado.</p>'),
        _pregunta(enunciado='¿Qué encontramos y de dónde salió la información?', opciones=[]),
        _seccion('6. Producto final y socialización', 'Lo que se construye y a quién se le presenta.'),
        _texto('<p>Describa el producto (maqueta, campaña, video, prototipo, informe) y cómo se presentará.</p>'),
        _seccion('7. Evaluación', 'Rúbrica con la escala de valoración nacional.'),
        _tabla([list(f) for f in RUBRICA]),
        _seccion('8. Reflexión', 'Autoevaluación y coevaluación.'),
        _pregunta(enunciado='¿Qué aprendí y qué aporté a mi equipo?', opciones=[]),
        _pregunta(enunciado='¿Qué mejoraríamos si volviéramos a hacer el proyecto?', opciones=[]),
    ],
    # Aprendizaje basado en retos: involucrarse, investigar y actuar sobre un problema real del entorno.
    'retos': lambda: [
        _objetivo(),
        _seccion('1. Involucrarse', 'De la gran idea al reto.'),
        _tabla([['Gran idea', 'Ej.: el agua, la convivencia, la energía'], ['Pregunta esencial', ''],
                ['El reto', 'Una acción concreta y alcanzable']], encabezado=False),
        _seccion('2. Investigar', 'Preguntas guía, actividades y recursos.'),
        _tabla([['Pregunta guía', 'Actividad o recurso para responderla'], ['', ''], ['', ''], ['', '']]),
        _pregunta(enunciado='Con lo investigado, ¿qué conclusiones sacamos?', opciones=[]),
        _seccion('3. Actuar', 'Proponer, aplicar y evaluar la solución.'),
        _texto('<p>La solución propuesta y cómo se pondrá en práctica.</p>'),
        _tabla([['Paso', 'Responsable', 'Fecha', '¿Se cumplió?'], ['', '', '', ''], ['', '', '', '']]),
        _seccion('4. Evaluación', ''),
        _tabla([list(f) for f in RUBRICA]),
        _recuadro('recuerda', 'Para pensar', '<p>¿Qué cambió en el entorno gracias a nuestra solución?</p>'),
    ],
    # Estudio de caso: una situación real o verosímil que se analiza para decidir.
    'caso': lambda: [
        _objetivo(),
        _seccion('1. El caso', 'Lea la situación con atención.'),
        _texto('<p>Narre aquí el caso: quiénes, dónde, qué pasó y cuál es el dilema.</p>'),
        _seccion('2. Comprensión', ''),
        _pregunta(enunciado='¿Cuál es el problema central del caso?'),
        _pregunta(enunciado='¿Quiénes están involucrados y qué quiere cada uno?', opciones=[]),
        _seccion('3. Análisis', 'Causas, consecuencias y datos importantes.'),
        _tabla([['Causas', 'Consecuencias'], ['', ''], ['', '']]),
        _seccion('4. Alternativas de solución', ''),
        _tabla([['Alternativa', 'Ventajas', 'Desventajas'], ['', '', ''], ['', '', ''], ['', '', '']]),
        _seccion('5. Decisión', ''),
        _pregunta(enunciado='¿Qué decidiría usted y por qué?', opciones=[]),
        _recuadro('recuerda', 'Lección del caso', '<p>¿Qué aprendimos que sirve para otras situaciones?</p>'),
    ],
    # Aula invertida: lo teórico se estudia antes de clase; la clase es para practicar.
    'invertida': lambda: [
        _objetivo(),
        _recuadro('nota', 'Cómo se trabaja esta guía', '<p>Estudie el material <b>antes</b> de la clase. En clase lo '
                  'aplicaremos juntos. Si usa el aula de la plataforma, el video puede llevar preguntas que lo pausan '
                  '(Aula invertida).</p>'),
        _seccion('1. Antes de clase', 'Video, lectura o presentación.'),
        _texto('<p>Enlace o descripción del material: duración, qué mirar con atención.</p>'),
        _pregunta(enunciado='Pregunta de verificación 1: '),
        _pregunta(enunciado='Pregunta de verificación 2: '),
        _pregunta(enunciado='Escriba una duda que le haya quedado.', opciones=[]),
        _seccion('2. En clase', 'Práctica en parejas o grupos, con el docente presente.'),
        _texto('<p>Actividades de aplicación y resolución de problemas.</p>'),
        _pregunta(),
        _pregunta(opciones=[]),
        _seccion('3. Después de clase', 'Refuerzo y aplicación en el entorno.'),
        _texto('<p>Una tarea corta para afianzar.</p>'),
        _lineas(3),
        _seccion('4. Autoevaluación', ''),
        _tabla([['Afirmación', 'Sí', 'A veces', 'No'], ['Estudié el material antes de clase', '', '', ''],
                ['Participé en la práctica', '', '', ''], ['Puedo explicar el tema a un compañero', '', '', '']]),
    ],
    # Aprendizaje cooperativo: interdependencia positiva, roles, responsabilidad individual y grupal.
    'cooperativo': lambda: [
        _objetivo(),
        _recuadro('nota', 'Organización', '<p>Grupos base de 4 integrantes. Cada uno se hace experto en una parte del '
                  'tema (técnica del rompecabezas) y luego la enseña a su grupo.</p>'),
        _seccion('1. Meta del grupo', 'Lo que todos deben lograr: nadie termina hasta que todos entiendan.'),
        _texto('<p>Meta común del grupo.</p>'),
        _seccion('2. Roles', ''),
        _tabla([['Rol', 'Función', 'Integrante'], ['Coordinador', 'Distribuye el trabajo y cuida los tiempos', ''],
                ['Secretario', 'Toma nota de acuerdos y respuestas', ''], ['Portavoz', 'Comparte las conclusiones', ''],
                ['Supervisor', 'Revisa que todos participen y entiendan', '']]),
        _seccion('3. Partes del rompecabezas', 'Cada integrante prepara una parte con los expertos de otros grupos.'),
        _tabla([['Parte', 'Experto', 'Lo más importante para enseñar'], ['A', '', ''], ['B', '', ''], ['C', '', ''],
                ['D', '', '']]),
        _seccion('4. Tarea del grupo', 'Se resuelve entre todos con lo que aportó cada experto.'),
        _pregunta(),
        _pregunta(opciones=[]),
        _seccion('5. Cómo trabajamos', 'Procesamiento grupal.'),
        _pregunta(enunciado='¿Qué hicimos bien como grupo y qué debemos mejorar?', opciones=[]),
        _seccion('6. Evaluación individual y grupal', ''),
        _tabla([['Criterio', 'Valoración'], ['Aporte individual', ''], ['Resultado del grupo', ''], ['Convivencia', '']]),
    ],
    'libre': lambda: [_texto()],
}

OPCIONES_CUADERNILLO = {'columnas': 2, 'letra': 10, 'modo': 'compacto', 'nombre_estudiante': False, 'datos': False,
                        'portada': True, 'sesion': 'sesión 1', 'duracion': '2 horas',
                        'horario': '', 'aviso': 'MATERIAL DE USO INSTITUCIONAL · NO ESCRIBAS EN ESTE CUADERNILLO. '
                        'Marca tus respuestas solo en la hoja de respuestas y devuélvelo completo al terminar.',
                        'fin': 'FIN DE LA SESIÓN. Revisa que hayas marcado todas las respuestas en la hoja de respuestas.'}


def contenido_inicial(tipo, base=None):
    """Bloques de la plantilla; para 'institucional', los del documento modelo del colegio."""
    if tipo == 'institucional' and base is not None:
        bloques = []
        for b in base.contenido.get('bloques', []):
            b = dict(b)
            b['id'] = _id()
            bloques.append(b)
        return {'bloques': bloques, 'opciones': dict(base.contenido.get('opciones') or {})}
    if tipo in FORMATOS:
        return {'bloques': FORMATOS[tipo](), 'opciones': {'columnas': 1, 'letra': 10, 'modo': 'normal',
                                                          'nombre_estudiante': False, 'datos': False}}
    fabrica = PLANTILLAS.get(tipo) or PLANTILLAS['libre']
    if tipo == 'cuadernillo':
        return {'bloques': fabrica(), 'opciones': dict(OPCIONES_CUADERNILLO)}
    if tipo == 'ficha_pdf':
        return {'bloques': fabrica(), 'opciones': {'columnas': 1, 'letra': 11, 'modo': 'compacto',
                                                    'nombre_estudiante': True, 'datos': False}}
    return {'bloques': fabrica(), 'opciones': {'columnas': 1, 'letra': 11, 'modo': 'normal',
                                                'nombre_estudiante': True, 'datos': True}}
