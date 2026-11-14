"""Contraseñas fáciles para estudiantes: una palabra y tres cifras («luna-482»). Un niño la escribe sin enredarse
y no es de las contraseñas comunes. Se guardan cifradas; el docente las ve solo al crearlas o restablecerlas."""
import secrets

PALABRAS = ('luna', 'tigre', 'nube', 'rayo', 'pino', 'sapo', 'loro', 'mango', 'rio', 'sol', 'mar', 'osito', 'gato',
            'perro', 'lobo', 'puma', 'oso', 'cielo', 'arena', 'roca', 'cometa', 'faro', 'barco', 'nido', 'fresa', 'kiwi',
            'coco', 'limon', 'pera', 'uva', 'mora', 'buho', 'pato', 'cebra', 'koala', 'panda', 'delfin', 'tortuga',
            'abeja', 'flor', 'hoja', 'trueno', 'volcan', 'isla', 'globo', 'tambor', 'flauta', 'lapiz', 'libro', 'mapa')
COMUNES = {'12345678', '123456789', 'password', 'contraseña', 'contrasena', 'qwerty123', '11111111', '00000000',
           'abcdefgh', 'abc12345', 'colombia', 'mcolegio', 'estudiante', 'colegio1', 'iloveyou'}
MINIMO = 8


def nueva():
    return f'{secrets.choice(PALABRAS)}-{secrets.randbelow(900) + 100}'


def problema(texto, nombre=''):
    """'' si la contraseña sirve; si no, qué le falta (para mostrarlo al lado)."""
    t = (texto or '').strip()
    if len(t) < MINIMO:
        return f'Debe tener al menos {MINIMO} caracteres.'
    if t.lower() in COMUNES or len(set(t)) <= 2:
        return 'Es una contraseña muy común: escoja otra.'
    if nombre and t.lower().replace(' ', '') == nombre.lower().replace(' ', ''):
        return 'No puede ser el mismo nombre del estudiante.'
    return ''
