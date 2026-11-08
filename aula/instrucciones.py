"""Las instrucciones de cada juego, para mostrarlas en los menús con el botón «Instrucciones».

Se leen del archivo de cada juego (el campo `instrucciones:` que también usa el juego en pantalla),
así el menú y el juego dicen siempre lo mismo."""
import os
import re
from functools import lru_cache

_ESTATICOS = os.path.join(os.path.dirname(__file__), 'static', 'aula')
_RE = re.compile(r"instrucciones:\s*'((?:[^'\\]|\\.)*)'")
# Lo común a los juegos con preguntas (motor arcade)
COMUN_ARCADE = ('Cada pregunta sale arriba y sus opciones abajo (A, B, C…). Responder bien suma puntos; responder mal '
                'o dejar que se acabe el tiempo quita una vida. Cada 3 preguntas el juego sube de nivel. '
                'Teclado: flechas para moverse y las letras para escoger. Con el botón «Pausa» (o la tecla P) el juego se congela y muestra la pregunta en grande para resolverla en papel; sigue cuando usted toque la pantalla. En el celular se toca la pantalla '
                '(en los juegos que se mueven, se pone el dedo en cualquier parte y se arrastra).')


@lru_cache(maxsize=None)
def _de_archivo(ruta):
    try:
        with open(ruta, encoding='utf-8') as f:
            m = _RE.search(f.read())
    except OSError:
        return ''
    return m.group(1).replace("\\'", "'").replace('\\n', ' ') if m else ''


_CADENA = r"'((?:[^'\\]|\\.)*)'"
_DOBLE = re.compile(r"instrucciones:\s*\w+\s*\?\s*" + _CADENA + r"\s*:\s*\w+\s*\?\s*" + _CADENA + r"\s*:\s*" + _CADENA)


@lru_cache(maxsize=None)
def _doble(ruta):
    """El archivo con tres juegos: instrucciones: selva ? '…' : safari ? '…' : '…' (selva, safari, trancón)."""
    try:
        with open(ruta, encoding='utf-8') as f:
            m = _DOBLE.search(f.read())
    except OSError:
        return '', '', ''
    return tuple(x.replace("\\'", "'") for x in m.groups()) if m else ('', '', '')


def logica(juego, script=None):
    """Instrucciones de un juego de lógica (su id y el nombre de su archivo)."""
    ruta = os.path.join(_ESTATICOS, 'logica', f'{script or juego}.js')
    texto = _de_archivo(ruta)
    if not texto:
        selva, safari, trancon = _doble(ruta)
        texto = {'selva': selva, 'safari': safari}.get(juego, trancon)
    return texto


def arcade(tipo):
    """Instrucciones de un juego con preguntas (por su tipo)."""
    return _de_archivo(os.path.join(_ESTATICOS, 'juegos', f'{tipo}.js'))


def de_evento(juego, propios=None):
    """Instrucciones de un reto del evento: de lógica, arcade (a_tipo, tiro, pacman) o propio (p_id)."""
    from .views_logica import DATOS
    if juego in DATOS:
        return logica(juego, DATOS[juego][3])
    if juego == 'pacman':
        return arcade('laberinto')
    if juego in ('tiro', 'speedrun'):
        return arcade('tiro') if juego == 'tiro' else logica('speedrun')
    if juego.startswith('a_'):
        return arcade(juego[2:])
    if juego.startswith('p_') and propios:
        return arcade(propios.get(juego, ''))
    return ''
