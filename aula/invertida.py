"""Aula invertida: leer las preguntas que pega el docente y calificar las respuestas.

El docente pega las preguntas como texto. Cada pregunta empieza con un número
(«1.», «2)», «Pregunta 3:») o va separada de la anterior por una línea en blanco.

    1. ¿Qué es la fotosíntesis?            ← abierta: el estudiante escribe
    2. ¿Dónde ocurre?
    A) En la raíz
    *B) En las hojas                       ← la correcta, con asterisco
    C) En el tallo
    3. ¿Qué gas libera la planta?
    a. Oxígeno
    b. Nitrógeno
    RESPUESTA: a                           ← o la correcta al final

Las de selección con una correcta se califican solas; las abiertas las lee el docente.

Con el minuto al comienzo («[2:30] ¿Qué es…?») el video de YouTube se pausa ahí,
muestra la pregunta encima y sigue cuando el estudiante responde. Las preguntas
sin minuto quedan para el final.
"""
import re

from .juegos import _OPCION, _RESPUESTA, nota as nota_de

MAX_PREGUNTAS = 50
_NUMERO = re.compile(r'^\s*(?:pregunta\s*)?\d{1,3}\s*[.)\-:]\s*(.*)$', re.I)
_TIEMPO = re.compile(r'^\s*[\[(]\s*(\d{1,2}(?::\d{1,2}){1,2})\s*[\])]\s*(.*)$')


def a_segundos(texto):
    """'2:30' -> 150; '1:02:05' -> 3725."""
    total = 0
    for parte in texto.split(':'):
        total = total * 60 + int(parte)
    return total


def minuto(segundos):
    if segundos is None:
        return ''
    h, resto = divmod(int(segundos), 3600)
    m, s = divmod(resto, 60)
    return f'{h}:{m:02d}:{s:02d}' if h else f'{m}:{s:02d}'


def leer_preguntas(texto, maximo=MAX_PREGUNTAS):
    preguntas = []
    actual = None          # {'texto': [...], 'opciones': [(letra, texto, marcada)], 'respuesta': letra}

    def cerrar():
        nonlocal actual
        texto_p = ' '.join(actual['texto']).strip() if actual else ''
        segundo = None
        m = _TIEMPO.match(texto_p)
        if m:
            segundo, texto_p = a_segundos(m.group(1)), m.group(2).strip()
        if actual and texto_p:
            opciones = [{'texto': t[:300], 'correcta': marcada or (letra == actual['respuesta'])}
                        for letra, t, marcada in actual['opciones']]
            preguntas.append({'texto': texto_p[:1000], 'opciones': opciones, 'segundo': segundo})
        actual = None

    for linea in (texto or '').splitlines():
        limpia = linea.strip()
        if not limpia:
            cerrar()
            continue
        m = _RESPUESTA.match(limpia)
        if m and actual:
            actual['respuesta'] = m.group(2).upper()
            cerrar()
            continue
        m = _OPCION.match(limpia)
        if m and actual and actual['texto']:
            actual['opciones'].append((m.group(2).upper(), m.group(3).strip(), bool(m.group(1))))
            continue
        m = _NUMERO.match(limpia)
        if not m and _TIEMPO.match(limpia):
            m = re.match(r'(.*)', limpia)          # «[2:30] …» también empieza una pregunta
        if m:
            cerrar()
            actual = {'texto': [m.group(1).strip()] if m.group(1).strip() else [], 'opciones': [], 'respuesta': None}
            continue
        if actual is None or actual['opciones']:
            cerrar()
            actual = {'texto': [], 'opciones': [], 'respuesta': None}
        actual['texto'].append(limpia)
    cerrar()
    return preguntas[:maximo]


def es_calificable(pregunta):
    return any(o.get('correcta') for o in pregunta.get('opciones', []))


def calificar(clase, respuestas):
    """(aciertos, nota o None) de unas respuestas {'0': índice | texto}."""
    aciertos = 0
    for i, p in enumerate(clase.preguntas):
        if not es_calificable(p):
            continue
        valor = respuestas.get(str(i))
        if isinstance(valor, int) and 0 <= valor < len(p['opciones']) and p['opciones'][valor].get('correcta'):
            aciertos += 1
    total = clase.calificables
    return aciertos, (nota_de(clase.aula, aciertos, total) if total else None)


def leer_respuestas(clase, post):
    """Del formulario del estudiante: ({'0': …}, faltan[números de pregunta])."""
    respuestas, faltan = {}, []
    for i, p in enumerate(clase.preguntas):
        valor = (post.get(f'p{i}') or '').strip()
        if p.get('opciones'):
            if valor.isdigit() and int(valor) < len(p['opciones']):
                respuestas[str(i)] = int(valor)
            else:
                faltan.append(i + 1)
        elif valor:
            respuestas[str(i)] = valor[:3000]
        else:
            faltan.append(i + 1)
    return respuestas, faltan


def detalle(clase, respuesta):
    """Para mostrar: [{'n', 'texto', 'opciones', 'abierta', 'valor', 'acierto'}]."""
    salida = []
    datos = respuesta.respuestas if respuesta else {}
    for i, p in enumerate(clase.preguntas):
        valor = datos.get(str(i))
        fila = {'n': i + 1, 'i': i, 'texto': p['texto'], 'abierta': not p.get('opciones'),
                'segundo': p.get('segundo'), 'minuto': minuto(p.get('segundo')),
                'opciones': [dict(o, k=k, elegida=(valor == k)) for k, o in enumerate(p.get('opciones', []))],
                'valor': valor, 'calificable': es_calificable(p), 'acierto': None}
        if fila['calificable'] and respuesta is not None:
            fila['acierto'] = isinstance(valor, int) and 0 <= valor < len(p['opciones']) and \
                bool(p['opciones'][valor].get('correcta'))
        salida.append(fila)
    return salida
