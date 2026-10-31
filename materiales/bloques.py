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

TIPOS = ('titulo', 'seccion', 'texto', 'imagen', 'tabla', 'recuadro', 'lineas', 'pregunta', 'contexto', 'separador',
         'salto')
# Tipos de pregunta. Los de AUTOMATICAS se califican solos; 'corta' se califica sola si coincide con una de
# las respuestas aceptadas; 'abierta' la califica el docente.
MODOS_PREGUNTA = {
    'unica': 'Selección múltiple (una respuesta)',
    'varias': 'Selección múltiple (varias respuestas)',
    'vf': 'Verdadero o falso',
    'completar': 'Completar',
    'numerica': 'Respuesta numérica',
    'corta': 'Respuesta corta',
    'abierta': 'Respuesta abierta',
    'emparejar': 'Unir con línea',
    'ordenar': 'Ordenar',
    'clasificar': 'Clasificar',
    'senalar': 'Señalar en la imagen',
    'archivo': 'Respuesta con foto o audio',
    'hoja': 'Hoja sobre un PDF o una imagen',
}
AUTOMATICAS = ('unica', 'varias', 'vf', 'completar', 'numerica', 'emparejar', 'ordenar', 'clasificar', 'senalar',
               'hoja')
# Lo que el estudiante manda en una respuesta con archivo.
ARCHIVO_TIPOS = {'foto': 'Foto', 'audio': 'Audio', 'cualquiera': 'Foto o audio'}
# Campos que se ponen encima de la página en una hoja sobre un PDF.
CAMPOS_HOJA = {'texto': 'Escribir', 'marca': 'Casilla', 'lista': 'Lista'}
MAX_ZONAS = 12
MAX_CAMPOS = 80
MAX_PARES = 12
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
            n.update(_limpiar_pregunta(b, imagenes_validas))
        elif tipo == 'contexto':
            img = _entero(b.get('imagen'), 0, 0, 2 ** 62)
            n.update(titulo=texto_plano(b.get('titulo'), 150), html=limpiar_html(b.get('html')),
                     imagen=img if img in imagenes_validas else None, ancho=_entero(b.get('ancho'), 70, 10, 100),
                     cubre=_entero(b.get('cubre'), 0, 0, 30))
        bloques.append(n)
    o = contenido.get('opciones') if isinstance(contenido.get('opciones'), dict) else {}
    opciones = {
        'columnas': 2 if str(o.get('columnas')) == '2' else 1,
        'letra': _entero(o.get('letra'), 11, 9, 14),
        'modo': o.get('modo') if o.get('modo') in MODOS else 'normal',
        'nombre_estudiante': o.get('nombre_estudiante', True) is not False,
        'datos': o.get('datos', True) is not False,
        # Cuadernillo: portada y datos de la sesión
        'portada': bool(o.get('portada')),
        'sesion': texto_plano(o.get('sesion'), 60),
        'duracion': texto_plano(o.get('duracion'), 60),
        'horario': texto_plano(o.get('horario'), 80),
        'aviso': texto_plano(o.get('aviso'), 300),
        'fin': texto_plano(o.get('fin'), 200),
    }
    return {'bloques': bloques, 'opciones': opciones}


def _lista(valores, maximo, largo=300):
    return [texto_plano(v, largo) for v in (valores or [])[:maximo] if texto_plano(v, largo)]


def _decimal(v, minimo=0.0, maximo=100.0):
    """Un porcentaje de la imagen, con un decimal."""
    try:
        x = float(v)
    except (TypeError, ValueError):
        return None
    if x != x:       # NaN
        return None
    return round(max(minimo, min(maximo, x)), 1)


def _caja(d):
    """Un rectángulo sobre la imagen en porcentajes {x, y, w, h}, o None si no sirve."""
    if not isinstance(d, dict):
        return None
    x, y, w, h = (_decimal(d.get(k)) for k in ('x', 'y', 'w', 'h'))
    if None in (x, y, w, h) or w < 0.5 or h < 0.5:
        return None
    return {'x': x, 'y': y, 'w': round(min(w, 100 - x), 1), 'h': round(min(h, 100 - y), 1)}


def _limpiar_campo(c, i):
    caja = _caja(c)
    tipo = c.get('tipo') if isinstance(c, dict) else None
    if caja is None or tipo not in CAMPOS_HOJA:
        return None
    cid = re.sub(r'[^a-zA-Z0-9_-]', '', str(c.get('id') or ''))[:12] or f'c{i}'
    n = dict(caja, id=cid, tipo=tipo, puntos=_entero(c.get('puntos'), 1, 0, 20))
    if tipo == 'texto':
        # Respuestas que valen, separadas por |. Vacío = la revisa el docente (o no cuenta si vale 0 puntos).
        n['correcta'] = '|'.join(x.strip() for x in texto_plano(c.get('correcta'), 200).split('|') if x.strip())
    elif tipo == 'marca':
        n['correcta'] = bool(c.get('correcta'))
    else:
        n['opciones'] = _lista(c.get('opciones'), 8, 60)
        k = c.get('correcta')
        n['correcta'] = k if isinstance(k, int) and 0 <= k < len(n['opciones']) else None
    return n


def puntos_hoja(b):
    """Lo que vale una hoja: los campos para escribir o escoger y las casillas que van marcadas."""
    return sum(c['puntos'] for c in b.get('campos') or [] if c['tipo'] != 'marca' or c.get('correcta'))


def _limpiar_pregunta(b, imagenes_validas):
    opciones_crudas = b.get('opciones') or []
    modo = b.get('modo')
    if modo not in MODOS_PREGUNTA:            # documentos de la fase 1
        modo = 'unica' if any(texto_plano(o) for o in opciones_crudas) else 'abierta'
    img = _entero(b.get('imagen'), 0, 0, 2 ** 62)
    n = {'modo': modo, 'enunciado': texto_plano(b.get('enunciado'), 2000),
         'imagen': img if img in imagenes_validas else None,
         'puntos': _entero(b.get('puntos'), 1, 1, 100), 'control': bool(b.get('control')),
         'lineas': _entero(b.get('lineas'), 3 if modo in ('abierta',) else 0, 0, 20)}
    if modo in ('unica', 'varias'):
        opciones = [texto_plano(o, 400) for o in opciones_crudas[:MAX_OPCIONES]]
        # Se quitan las vacías corrigiendo el índice de las correctas.
        indices = [i for i, o in enumerate(opciones) if o]
        nuevo = {viejo: k for k, viejo in enumerate(indices)}
        n['opciones'] = [opciones[i] for i in indices]
        if modo == 'unica':
            c = b.get('correcta')
            n['correcta'] = nuevo.get(c) if isinstance(c, int) else None
        else:
            n['correctas'] = sorted({nuevo[c] for c in (b.get('correctas') or []) if isinstance(c, int) and c in nuevo})
    elif modo == 'vf':
        n['valor'] = bool(b.get('valor'))
    elif modo == 'completar':
        # El texto lleva los huecos así: «La capital es [[Bogotá|Bogota]].»
        n['texto'] = texto_plano(b.get('texto'), 3000)
        n['mayusculas'] = bool(b.get('mayusculas'))
    elif modo == 'numerica':
        n['respuesta'] = texto_plano(b.get('respuesta'), 30)
        n['tolerancia'] = texto_plano(b.get('tolerancia'), 20)
        n['unidad'] = texto_plano(b.get('unidad'), 20)
    elif modo == 'corta':
        n['aceptadas'] = _lista(b.get('aceptadas'), 10, 120)
    elif modo == 'emparejar':
        pares = []
        for p in (b.get('pares') or [])[:MAX_PARES]:
            if isinstance(p, (list, tuple)) and len(p) == 2 and texto_plano(p[0]) and texto_plano(p[1]):
                pares.append([texto_plano(p[0], 200), texto_plano(p[1], 200)])
        n['pares'] = pares
    elif modo == 'ordenar':
        n['elementos'] = _lista(b.get('elementos'), MAX_PARES, 200)
    elif modo == 'clasificar':
        grupos = []
        for g in (b.get('grupos') or [])[:6]:
            if isinstance(g, dict) and texto_plano(g.get('nombre')):
                grupos.append({'nombre': texto_plano(g.get('nombre'), 60),
                               'elementos': _lista(g.get('elementos'), MAX_PARES, 100)})
        n['grupos'] = grupos
    elif modo == 'senalar':
        zonas = [z for z in (_caja(x) for x in (b.get('zonas') or [])[:MAX_ZONAS]) if z]
        n['zonas'] = zonas
        n['ancho'] = _entero(b.get('ancho'), 70, 20, 100)
    elif modo == 'archivo':
        n['archivo'] = b.get('archivo') if b.get('archivo') in ARCHIVO_TIPOS else 'foto'
    elif modo == 'hoja':
        campos, vistos = [], set()
        for i, c in enumerate((b.get('campos') or [])[:MAX_CAMPOS]):
            limpio = _limpiar_campo(c, i)
            if limpio is None:
                continue
            if limpio['id'] in vistos:
                limpio['id'] = f"{limpio['id'][:8]}x{i}"
            vistos.add(limpio['id'])
            campos.append(limpio)
        n['campos'] = campos
        n['puntos'] = max(1, puntos_hoja(n))
        n['lineas'] = 0
    return n


HUECO = re.compile(r'\[\[([^\]]{1,200})\]\]')


def huecos(texto):
    """[[Bogotá|Bogota]] -> partes del texto y, por cada hueco, sus respuestas aceptadas."""
    partes, respuestas, ultimo = [], [], 0
    for m in HUECO.finditer(texto or ''):
        partes.append(texto[ultimo:m.start()])
        respuestas.append([x.strip() for x in m.group(1).split('|') if x.strip()])
        ultimo = m.end()
    partes.append((texto or '')[ultimo:])
    return partes, respuestas


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
