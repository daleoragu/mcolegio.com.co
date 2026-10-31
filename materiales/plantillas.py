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
    return {'id': _id(), 'tipo': 'pregunta', 'enunciado': enunciado,
            'opciones': opciones if opciones is not None else ['', '', '', ''], 'correcta': None, 'lineas': 0}


def _recuadro(estilo, titulo, html=''):
    return {'id': _id(), 'tipo': 'recuadro', 'estilo': estilo, 'titulo': titulo, 'html': html}


def _objetivo():
    return _recuadro('nota', 'Lo que voy a aprender', '<p>Escriba aquí el objetivo, el DBA o la competencia.</p>')


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
    'libre': lambda: [_texto()],
}


def contenido_inicial(tipo, base=None):
    """Bloques de la plantilla; para 'institucional', los del documento modelo del colegio."""
    if tipo == 'institucional' and base is not None:
        bloques = []
        for b in base.contenido.get('bloques', []):
            b = dict(b)
            b['id'] = _id()
            bloques.append(b)
        return {'bloques': bloques, 'opciones': dict(base.contenido.get('opciones') or {})}
    fabrica = PLANTILLAS.get(tipo) or PLANTILLAS['libre']
    return {'bloques': fabrica(), 'opciones': {'columnas': 1, 'letra': 11, 'modo': 'normal',
                                                'nombre_estudiante': True, 'datos': True}}
