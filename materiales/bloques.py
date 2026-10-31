"""El contenido de un documento de Mis materiales y cómo se limpia antes de guardarlo.

contenido = {
  "bloques": [
    {"id": "a1", "tipo": "titulo", "texto": "...", "nivel": 1|2},
    {"id": "a2", "tipo": "seccion", "titulo": "Exploración", "indicacion": "..."},
    {"id": "a3", "tipo": "texto", "html": "<p>...</p>"},
    {"id": "a4", "tipo": "imagen", "imagen": 12, "ancho": 60, "pie": "..."},
    {"id": "a5", "tipo": "tabla", "filas": [["", ""], ["", ""]], "encabezado": true},
    {"id": "a6", "tipo": "recuadro", "estilo": "recuerda|reto|vocabulario|nota", "titulo": "...", "html": "..."},
    {"id": "a7", "tipo": "lineas", "n": 4},
    {"id": "a8", "tipo": "pregunta", "enunciado": "...", "imagen": 12|null, "opciones": ["..."],
                 "correcta": 0|null, "lineas": 0},
    {"id": "a9", "tipo": "separador"},
    {"id": "b1", "tipo": "salto"}
  ],
  "opciones": {"columnas": 1|2, "letra": 10..13, "modo": "normal|compacto|maximo",
               "nombre_estudiante": true, "datos": true}
}
"""
import html
import re
from html.parser import HTMLParser

TIPOS = ('titulo', 'seccion', 'texto', 'imagen', 'tabla', 'recuadro', 'lineas', 'pregunta', 'separador', 'salto')
ESTILOS_RECUADRO = {'recuerda': 'Recuerda', 'reto': 'Reto', 'vocabulario': 'Vocabulario', 'nota': 'Nota'}
MODOS = ('normal', 'compacto', 'maximo')
MAX_BLOQUES = 300
MAX_TEXTO = 20000
MAX_CORTO = 600
MAX_OPCIONES = 6
MAX_FILAS, MAX_COLUMNAS = 30, 8

ETIQUETAS = {'b', 'strong', 'i', 'em', 'u', 'br', 'p', 'ul', 'ol', 'li', 'sub', 'sup', 'div', 'span'}
VACIAS = {'br'}


class _Limpiador(HTMLParser):
    """Deja solo negrilla, cursiva, subrayado, listas, párrafos y saltos; sin atributos."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.salida = []
        self.abiertas = []

    def handle_starttag(self, tag, attrs):
        tag = {'strong': 'b', 'em': 'i', 'div': 'p', 'span': None}.get(tag, tag)
        if tag is None or tag not in ETIQUETAS:
            return
        if tag in VACIAS:
            self.salida.append('<br>')
            return
        self.salida.append(f'<{tag}>')
        self.abiertas.append(tag)

    def handle_endtag(self, tag):
        tag = {'strong': 'b', 'em': 'i', 'div': 'p', 'span': None}.get(tag, tag)
        if tag is None or tag in VACIAS or tag not in self.abiertas:
            return
        while self.abiertas:
            t = self.abiertas.pop()
            self.salida.append(f'</{t}>')
            if t == tag:
                break

    def handle_data(self, data):
        self.salida.append(html.escape(data, quote=False))

    def texto(self):
        while self.abiertas:
            self.salida.append(f'</{self.abiertas.pop()}>')
        return ''.join(self.salida)


def limpiar_html(crudo):
    p = _Limpiador()
    try:
        p.feed(str(crudo or '')[:MAX_TEXTO])
        p.close()
    except Exception:
        return html.escape(str(crudo or '')[:MAX_TEXTO])
    salida = p.texto()
    return re.sub(r'(<p></p>)+', '', salida)


def texto_plano(crudo, maximo=MAX_CORTO):
    return ' '.join(str(crudo or '').split())[:maximo]


def _entero(v, defecto, minimo, maximo):
    try:
        return max(minimo, min(maximo, int(v)))
    except (TypeError, ValueError):
        return defecto


def limpiar(contenido, imagenes_validas):
    """Devuelve el contenido limpio: solo tipos conocidos, textos acotados, imágenes del docente."""
    contenido = contenido if isinstance(contenido, dict) else {}
    bloques = []
    for i, b in enumerate((contenido.get('bloques') or [])[:MAX_BLOQUES]):
        if not isinstance(b, dict) or b.get('tipo') not in TIPOS:
            continue
        tipo = b['tipo']
        bid = re.sub(r'[^a-zA-Z0-9_-]', '', str(b.get('id') or ''))[:20] or f'b{i}'
        n = {'id': bid, 'tipo': tipo}
        if tipo == 'titulo':
            n.update(texto=texto_plano(b.get('texto'), 200), nivel=_entero(b.get('nivel'), 1, 1, 2))
        elif tipo == 'seccion':
            n.update(titulo=texto_plano(b.get('titulo'), 120), indicacion=texto_plano(b.get('indicacion'), 400))
        elif tipo == 'texto':
            n.update(html=limpiar_html(b.get('html')))
        elif tipo == 'imagen':
            img = _entero(b.get('imagen'), 0, 0, 2 ** 62)
            if img not in imagenes_validas:
                continue
            n.update(imagen=img, ancho=_entero(b.get('ancho'), 60, 10, 100), pie=texto_plano(b.get('pie'), 200))
        elif tipo == 'tabla':
            filas = [[texto_plano(c, 300) for c in (f or [])[:MAX_COLUMNAS]]
                     for f in (b.get('filas') or [])[:MAX_FILAS] if isinstance(f, list)]
            ancho = max((len(f) for f in filas), default=0)
            if not ancho:
                continue
            n.update(filas=[f + [''] * (ancho - len(f)) for f in filas], encabezado=bool(b.get('encabezado')))
        elif tipo == 'recuadro':
            estilo = b.get('estilo') if b.get('estilo') in ESTILOS_RECUADRO else 'nota'
            n.update(estilo=estilo, titulo=texto_plano(b.get('titulo'), 80) or ESTILOS_RECUADRO[estilo],
                     html=limpiar_html(b.get('html')))
        elif tipo == 'lineas':
            n.update(n=_entero(b.get('n'), 3, 1, 30))
        elif tipo == 'pregunta':
            opciones = [texto_plano(o, 400) for o in (b.get('opciones') or [])[:MAX_OPCIONES]]
            opciones = [o for o in opciones if o]
            correcta = b.get('correcta')
            correcta = correcta if isinstance(correcta, int) and 0 <= correcta < len(opciones) else None
            img = _entero(b.get('imagen'), 0, 0, 2 ** 62)
            n.update(enunciado=texto_plano(b.get('enunciado'), 2000), opciones=opciones, correcta=correcta,
                     imagen=img if img in imagenes_validas else None,
                     lineas=_entero(b.get('lineas'), 0 if opciones else 3, 0, 20))
        bloques.append(n)
    o = contenido.get('opciones') if isinstance(contenido.get('opciones'), dict) else {}
    opciones = {
        'columnas': 2 if str(o.get('columnas')) == '2' else 1,
        'letra': _entero(o.get('letra'), 11, 9, 14),
        'modo': o.get('modo') if o.get('modo') in MODOS else 'normal',
        'nombre_estudiante': o.get('nombre_estudiante', True) is not False,
        'datos': o.get('datos', True) is not False,
    }
    return {'bloques': bloques, 'opciones': opciones}


def imagenes_usadas(contenido):
    salida = set()
    for b in contenido.get('bloques', []):
        if b.get('imagen'):
            salida.add(b['imagen'])
    return salida


def disposicion_opciones(opciones, modo):
    """Cómo van las opciones de una pregunta: 'fila' (todas en una línea), 'dos' (dos por dos) o
    'lista' (una debajo de otra). Es lo que más espacio ahorra en un cuadernillo."""
    if not opciones:
        return 'lista'
    larga = max(len(o) for o in opciones)
    if modo == 'normal':
        return 'fila' if larga <= 8 else 'lista'
    if larga <= (16 if modo == 'compacto' else 22) and len(opciones) <= 5:
        return 'fila'
    if larga <= (40 if modo == 'compacto' else 55):
        return 'dos'
    return 'lista'
