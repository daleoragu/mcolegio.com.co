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
    'sopa': 'Sopa de letras',
    'crucigrama': 'Crucigrama',
}
AUTOMATICAS = ('unica', 'varias', 'vf', 'completar', 'numerica', 'emparejar', 'ordenar', 'clasificar', 'senalar',
               'hoja', 'sopa', 'crucigrama')
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
MAX_FILAS, MAX_COLUMNAS = 40, 8
MAX_CELDA = 1500

# Imagen: dónde va. «linea»: sola en su renglón; «cuadrado»: el texto que sigue la rodea; «detras» / «delante»:
# libre, encima o debajo del texto, en (x, y) = % del ancho de la hoja desde el borde izquierdo y desde donde está el bloque.
ALINEAR = ('izquierda', 'centro', 'derecha')
AJUSTES = ('linea', 'cuadrado', 'detras', 'delante')


def css_imagen(b, ancho_util_mm=None):
    """(clase del contenedor, estilo del contenedor, estilo de la imagen) para la web (ancho_util_mm=None) o el PDF."""
    ajuste, alinear, ancho = b.get('ajuste') or 'linea', b.get('alinear') or 'centro', b.get('ancho') or 60
    if ajuste == 'cuadrado':
        lado = 'right' if alinear == 'derecha' else 'left'
        margen = '0 0 2mm 4mm' if lado == 'right' else '0 4mm 2mm 0'
        return f'img-flota img-{lado}', f'float:{lado};width:{ancho}%;margin:{margen}', 'width:100%'
    if ajuste in ('detras', 'delante'):
        x, y = b.get('x') or 0, b.get('y') or 0
        top = f'{y * ancho_util_mm / 100:.1f}mm' if ancho_util_mm else f'{y}cqw'
        capa = '-1' if ajuste == 'detras' else '5'
        opacidad = (b.get('opacidad') or 100) / 100
        return (f'img-libre img-{ajuste}', 'position:relative;height:0;margin:0;overflow:visible' + ('' if ancho_util_mm else ';container-type:inline-size'),
                f'position:absolute;left:{x}%;top:{top};width:{ancho}%;z-index:{capa};opacity:{opacidad:.2f};max-height:none')
    texto = {'izquierda': 'left', 'derecha': 'right'}.get(alinear, 'center')
    return 'img-linea', f'text-align:{texto}', f'width:{ancho}%'


ETIQUETAS = {'b', 'strong', 'i', 'em', 'u', 's', 'br', 'p', 'ul', 'ol', 'li', 'sub', 'sup', 'div', 'span'}
# Tipos de letra que se pueden escoger: el nombre y lo que se pone en el CSS (con parecidas por si el
# equipo o el servidor del PDF no la tienen)
FUENTES = {
    'Arial': "Arial,'Liberation Sans',Helvetica,sans-serif",
    'Calibri': "Calibri,Carlito,'Liberation Sans',sans-serif",
    'Times New Roman': "'Times New Roman','Liberation Serif',Times,serif",
    'Georgia': "Georgia,'DejaVu Serif',serif",
    'Verdana': "Verdana,'DejaVu Sans',sans-serif",
    'Tahoma': "Tahoma,'DejaVu Sans',sans-serif",
    'Trebuchet MS': "'Trebuchet MS','DejaVu Sans',sans-serif",
    'Century Gothic': "'Century Gothic','URW Gothic',sans-serif",
    'Comic Sans MS': "'Comic Sans MS','Comic Neue',cursive",
    'Courier New': "'Courier New','Liberation Mono',monospace",
}
TAMANOS = (8, 9, 10, 11, 12, 14, 16, 18, 20, 24, 28, 32, 36, 48)
_TAM_PALABRA = {'xx-small': 7, 'x-small': 7.5, 'small': 10, 'medium': 12, 'large': 13.5, 'x-large': 18, 'xx-large': 24, 'xxx-large': 36}
ALINEACIONES = ('left', 'center', 'right', 'justify')
VACIAS = {'br'}


def _a_hex(valor):
    """'#abc', '#aabbcc' o 'rgb(1, 2, 3)' → '#aabbcc'; si no es un color, ''."""
    v = str(valor or '').strip().lower()
    m = re.fullmatch(r'#([0-9a-f]{3})', v)
    if m:
        return '#' + ''.join(c * 2 for c in m.group(1))
    if re.fullmatch(r'#[0-9a-f]{6}', v):
        return v
    m = re.fullmatch(r'rgba?\(\s*(\d{1,3})\s*,\s*(\d{1,3})\s*,\s*(\d{1,3})\s*(?:,\s*([\d.]+)\s*)?\)', v)
    if m and (m.group(4) is None or float(m.group(4)) > 0):
        return '#%02x%02x%02x' % tuple(min(255, int(x)) for x in m.groups()[:3])
    return ''


def _estilo_color(attrs):
    """De un <span style> o <font color>: 'color:#…;background-color:#…' (solo esos dos, validados)."""
    d = dict(attrs)
    color, fondo = _a_hex(d.get('color')), ''
    for parte in str(d.get('style') or '').split(';'):
        if ':' not in parte:
            continue
        k, v = (x.strip().lower() for x in parte.split(':', 1))
        if k == 'color':
            color = _a_hex(v) or color
        elif k in ('background-color', 'background'):
            fondo = _a_hex(v) or fondo
    return ';'.join(x for x in (color and f'color:{color}', fondo and f'background-color:{fondo}') if x)


def fuente(valor):
    """El tipo de letra permitido a partir de lo que mande el navegador ('Georgia, serif', '"Times New Roman"'…)."""
    primera = str(valor or '').split(',')[0].strip().strip('\'"').lower()
    return next((k for k in FUENTES if k.lower() == primera), None)


def tamano_pt(valor):
    """El tamaño de letra en puntos (6 a 72) desde '14pt', '18px', '1.5em' no; 'large'…"""
    v = str(valor or '').strip().lower()
    if v in _TAM_PALABRA:
        return _TAM_PALABRA[v]
    m = re.fullmatch(r'(\d{1,3}(?:\.\d+)?)\s*(pt|px)', v)
    if not m:
        return None
    n = float(m.group(1)) * (0.75 if m.group(2) == 'px' else 1)
    return round(n, 1) if 6 <= n <= 72 else None


def _estilo_span(attrs):
    """Color, relleno, tipo y tamaño de letra de un <span style> o <font>, validados."""
    d = dict(attrs)
    partes = [x for x in _estilo_color(attrs).split(';') if x]
    familia = fuente(d.get('face')) if d.get('face') else None
    tam = None
    for parte in str(d.get('style') or '').split(';'):
        if ':' not in parte:
            continue
        k, v = (x.strip().lower() for x in parte.split(':', 1))
        if k == 'font-family':
            familia = fuente(parte.split(':', 1)[1]) or familia
        elif k == 'font-size':
            tam = tamano_pt(v) or tam
        elif k == 'text-decoration' or k == 'text-decoration-line':
            if 'line-through' in v:
                partes.append('text-decoration:line-through')
    if familia:
        partes.append('font-family:' + FUENTES[familia])
    if tam:
        partes.append(f'font-size:{tam:g}pt')
    return ';'.join(partes)


def _alineacion(attrs):
    d = dict(attrs)
    valor = str(d.get('align') or '').lower()
    for parte in str(d.get('style') or '').split(';'):
        if ':' in parte:
            k, v = (x.strip().lower() for x in parte.split(':', 1))
            if k == 'text-align':
                valor = v
    valor = {'start': 'left', 'end': 'right', 'middle': 'center'}.get(valor, valor)
    return valor if valor in ALINEACIONES else ''


class _Limpiador(HTMLParser):
    """Deja solo negrilla, cursiva, subrayado, tachado, listas, párrafos (con su alineación), saltos, y en los
    <span style> el color de letra, el relleno, el tipo y el tamaño de letra; ningún otro atributo."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.salida = []
        self.abiertas = []

    def handle_starttag(self, tag, attrs):
        if tag in ('span', 'font', 'mark'):
            estilo = _estilo_span(attrs) or ('background-color:#fef08a' if tag == 'mark' else '')
            if estilo:
                self.salida.append(f'<span style="{estilo}">')
                self.abiertas.append('span')
            else:
                self.abiertas.append('-' + tag)      # se cierra sin escribir nada
            return
        tag = {'strong': 'b', 'em': 'i', 'div': 'p', 'strike': 's', 'del': 's'}.get(tag, tag)
        if tag not in ETIQUETAS:
            return
        if tag in VACIAS:
            self.salida.append('<br>')
            return
        alinear = _alineacion(attrs) if tag in ('p', 'li') else ''
        self.salida.append(f'<{tag} style="text-align:{alinear}">' if alinear else f'<{tag}>')
        self.abiertas.append(tag)

    def handle_endtag(self, tag):
        if tag in ('span', 'font', 'mark'):
            # cierra el último span (o el marcador de uno sin color)
            for k in range(len(self.abiertas) - 1, -1, -1):
                if self.abiertas[k] in ('span', '-' + tag, '-span', '-font', '-mark'):
                    while len(self.abiertas) > k:
                        t = self.abiertas.pop()
                        if not t.startswith('-'):
                            self.salida.append(f'</{t}>')
                    return
            return
        tag = {'strong': 'b', 'em': 'i', 'div': 'p', 'strike': 's', 'del': 's'}.get(tag, tag)
        if tag in VACIAS or tag not in self.abiertas:
            return
        while self.abiertas:
            t = self.abiertas.pop()
            if not t.startswith('-'):
                self.salida.append(f'</{t}>')
            if t == tag:
                break

    def handle_data(self, data):
        self.salida.append(html.escape(data, quote=False))

    def texto(self):
        while self.abiertas:
            t = self.abiertas.pop()
            if not t.startswith('-'):
                self.salida.append(f'</{t}>')
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


COLOR_DEFECTO = '#1f3a68'
COLORES = [('#1f3a68', 'Azul institucional'), ('#2563eb', 'Azul claro'), ('#0f766e', 'Verde azulado'), ('#15803d', 'Verde'),
           ('#7c3aed', 'Morado'), ('#be185d', 'Fucsia'), ('#b91c1c', 'Rojo'), ('#c2410c', 'Naranja'), ('#a16207', 'Mostaza'),
           ('#374151', 'Gris oscuro'), ('#000000', 'Negro (ahorra tinta de color)')]


def color_valido(valor, defecto=COLOR_DEFECTO):
    """Un color #rrggbb; si no es válido, el de siempre."""
    v = str(valor or '').strip().lower()
    return v if re.fullmatch(r'#[0-9a-f]{6}', v) else defecto


def comparable(texto):
    """Minúsculas, sin tildes ni espacios de más: para comparar áreas («Matemáticas» = «matematicas»)."""
    import unicodedata
    t = unicodedata.normalize('NFD', str(texto or '').lower())
    return ' '.join(''.join(c for c in t if unicodedata.category(c) != 'Mn').split())


def mezclar(color, blanco):
    """El color aclarado con blanco (blanco = 0..1): para los fondos suaves de los recuadros."""
    c = color_valido(color)
    r, g, b = (int(c[i:i + 2], 16) for i in (1, 3, 5))
    return '#%02x%02x%02x' % tuple(round(x + (255 - x) * blanco) for x in (r, g, b))


def _estilos_celdas(crudo, n_filas, n_cols):
    """Relleno y color de letra de cada celda: {'fila-col': {'f': '#…', 'c': '#…'}} (solo celdas que existen)."""
    salida = {}
    if not isinstance(crudo, dict):
        return salida
    for clave, v in list(crudo.items())[:MAX_FILAS * MAX_COLUMNAS]:
        m = re.fullmatch(r'(\d{1,2})-(\d)', str(clave))
        if not m or not isinstance(v, dict) or int(m.group(1)) >= n_filas or int(m.group(2)) >= n_cols:
            continue
        e = {k: _a_hex(v.get(k)) for k in ('f', 'c') if _a_hex(v.get(k))}
        if e:
            salida[clave] = e
    return salida


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
            n.update(imagen=img, ancho=_entero(b.get('ancho'), 60, 10, 100), pie=texto_plano(b.get('pie'), 200),
                     alinear=b.get('alinear') if b.get('alinear') in ALINEAR else 'centro',
                     ajuste=b.get('ajuste') if b.get('ajuste') in AJUSTES else 'linea',
                     x=_entero(b.get('x'), 0, -50, 100), y=_entero(b.get('y'), 0, -150, 300),
                     opacidad=_entero(b.get('opacidad'), 100, 10, 100))
        elif tipo == 'tabla':
            filas = [[texto_plano(c, MAX_CELDA) for c in (f or [])[:MAX_COLUMNAS]]
                     for f in (b.get('filas') or [])[:MAX_FILAS] if isinstance(f, list)]
            ancho = max((len(f) for f in filas), default=0)
            if not ancho:
                continue
            n.update(filas=[f + [''] * (ancho - len(f)) for f in filas], encabezado=bool(b.get('encabezado')),
                     # privada: datos del estudiante (PIAR) que nunca se envían a la IA
                     privada=bool(b.get('privada')),
                     estilos=_estilos_celdas(b.get('estilos'), len(filas), ancho))
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
        # Color de los títulos, las franjas de sección y los recuadros (antes siempre azul)
        'color': color_valido(o.get('color')),
        # Tamaño de la hoja: carta, oficio o uno personalizado (en la unidad que escoja el docente)
        'papel': papel(o.get('papel')),
        # Marcas a mano alzada sobre la hoja: si salen también al imprimir
        'marcas_pdf': o.get('marcas_pdf', True) is not False,
    }
    return {'bloques': bloques, 'opciones': opciones,
            'anotaciones': limpiar_anotaciones(contenido.get('anotaciones'), {b['id'] for b in bloques})}


# ---------------------------------------------------------------- Marcas a mano alzada sobre la hoja
# Cada marca va pegada a un bloque (si el bloque se mueve, la marca se mueve con él). Las coordenadas van en
# milésimas del ancho útil de la hoja, medidas desde la esquina de arriba a la izquierda del bloque.
HERR_ANOT = ('lapiz', 'resaltar', 'linea', 'flecha', 'rect', 'elipse', 'texto', 'sello')
SELLOS = ('bien', 'mal', 'medio', 'estrella')
MAX_ANOT, MAX_PUNTOS_ANOT, MAX_PUNTOS_TOTAL = 1500, 2000, 60000


def limpiar_anotaciones(crudo, ids):
    salida, total = [], 0
    for a in (crudo if isinstance(crudo, list) else [])[:MAX_ANOT]:
        if not isinstance(a, dict) or a.get('h') not in HERR_ANOT or a.get('b') not in ids:
            continue
        num = lambda v, lo, hi: max(lo, min(hi, float(v))) if isinstance(v, (int, float)) and v == v else None
        puntos = []
        for q in (a.get('p') or [])[:MAX_PUNTOS_ANOT]:
            if not isinstance(q, (list, tuple)) or len(q) < 2:
                continue
            x, y = num(q[0], -200, 1200), num(q[1], -500, 20000)
            if x is None or y is None:
                continue
            punto = [round(x, 1), round(y, 1)]
            if len(q) > 2 and num(q[2], 0, 1) is not None:
                punto.append(round(num(q[2], 0, 1), 2))
            puntos.append(punto)
        if not puntos or total + len(puntos) > MAX_PUNTOS_TOTAL:
            continue
        total += len(puntos)
        n = {'b': a['b'], 'h': a['h'], 'c': color_valido(a.get('c'), '#dc2626'), 'g': round(num(a.get('g'), .5, 40) or 3, 1), 'p': puntos}
        if a['h'] == 'texto':
            n['texto'] = texto_plano(a.get('texto'), 200)
            if not n['texto']:
                continue
        if a['h'] == 'sello':
            n['s'] = a.get('s') if a.get('s') in SELLOS else 'bien'
        if a.get('relleno') and a['h'] in ('rect', 'elipse'):
            n['relleno'] = True
        salida.append(n)
    return salida


def _camino_suave(p):
    if len(p) < 3:
        return 'M' + ' L'.join(f'{x:.1f} {y:.1f}' for x, y, *_ in p) + (f' L{p[0][0] + .1:.1f} {p[0][1]:.1f}' if len(p) == 1 else '')
    d = [f'M{p[0][0]:.1f} {p[0][1]:.1f}']
    for i in range(1, len(p) - 1):
        d.append(f'Q{p[i][0]:.1f} {p[i][1]:.1f} {(p[i][0] + p[i + 1][0]) / 2:.1f} {(p[i][1] + p[i + 1][1]) / 2:.1f}')
    d.append(f'L{p[-1][0]:.1f} {p[-1][1]:.1f}')
    return ' '.join(d)


def _svg_marca(a):
    from html import escape
    c, g, p = a['c'], a['g'], a['p']
    if a['h'] == 'lapiz':
        con = [q[2] for q in p if len(q) > 2]
        ancho = g * (.3 + .85 * (sum(con) / len(con))) if con else g
        return f'<path d="{_camino_suave(p)}" fill="none" stroke="{c}" stroke-width="{ancho:.2f}" stroke-linecap="round" stroke-linejoin="round"/>'
    if a['h'] == 'resaltar':
        return f'<path d="{_camino_suave(p)}" fill="none" stroke="{c}" stroke-opacity=".35" stroke-width="{g * 3:.1f}" stroke-linecap="butt" stroke-linejoin="round"/>'
    if a['h'] in ('linea', 'flecha'):
        (x0, y0), (x1, y1) = p[0][:2], p[-1][:2]
        s = f'<line x1="{x0}" y1="{y0}" x2="{x1}" y2="{y1}" stroke="{c}" stroke-width="{g}" stroke-linecap="round"/>'
        if a['h'] == 'flecha':
            import math
            ang, L = math.atan2(y1 - y0, x1 - x0), 10 + g * 2.5
            pts = [(x1, y1), (x1 - L * math.cos(ang - .45), y1 - L * math.sin(ang - .45)), (x1 - L * math.cos(ang + .45), y1 - L * math.sin(ang + .45))]
            s += f'<polygon points="{" ".join(f"{x:.1f},{y:.1f}" for x, y in pts)}" fill="{c}"/>'
        return s
    if a['h'] in ('rect', 'elipse'):
        (x0, y0), (x1, y1) = p[0][:2], p[-1][:2]
        relleno = f'fill="{c}" fill-opacity=".9"' if a.get('relleno') else 'fill="none"'
        if a['h'] == 'rect':
            return f'<rect x="{min(x0, x1)}" y="{min(y0, y1)}" width="{abs(x1 - x0)}" height="{abs(y1 - y0)}" stroke="{c}" stroke-width="{g}" {relleno}/>'
        return f'<ellipse cx="{(x0 + x1) / 2}" cy="{(y0 + y1) / 2}" rx="{abs(x1 - x0) / 2}" ry="{abs(y1 - y0) / 2}" stroke="{c}" stroke-width="{g}" {relleno}/>'
    if a['h'] == 'texto':
        return (f'<text x="{p[0][0]}" y="{p[0][1]}" fill="{c}" font-family="Arial, sans-serif" font-weight="bold" '
                f'font-size="{14 + g * 3:.0f}">{escape(a["texto"])}</text>')
    if a['h'] == 'sello':
        x, y, t = p[0][0], p[0][1], tam_sello(g)
        return f'<g transform="translate({x} {y}) scale({t / 100:.3f})">{SELLO_SVG[a.get("s", "bien")]}</g>'
    return ''


def tam_sello(g):
    return 22 + g * 4


# Sellos centrados en (0, 0), dibujados en una caja de 100 × 100
SELLO_SVG = {
    'bien': '<path d="M-38 2 L-12 28 L40 -30" fill="none" stroke="#16a34a" stroke-width="14" stroke-linecap="round" stroke-linejoin="round"/>',
    'mal': '<path d="M-30 -30 L30 30 M30 -30 L-30 30" fill="none" stroke="#dc2626" stroke-width="14" stroke-linecap="round"/>',
    'medio': '<path d="M-38 2 L-12 28 L40 -30" fill="none" stroke="#ea580c" stroke-width="14" stroke-linecap="round" stroke-linejoin="round"/>'
             '<path d="M-34 34 L34 -34" stroke="#ea580c" stroke-width="8" stroke-linecap="round"/>',
    'estrella': '<polygon points="0,-46 13,-15 46,-14 20,7 29,40 0,21 -29,40 -20,7 -46,-14 -13,-15" fill="#facc15" stroke="#ca8a04" stroke-width="5" stroke-linejoin="round"/>',
}


def marcas_svg(anotaciones, ancho_px):
    """Las marcas de un bloque como imagen SVG (data URI) y su posición en px dentro del bloque."""
    import base64
    if not anotaciones:
        return None
    xs, ys = [], []
    for a in anotaciones:
        m = tam_sello(a['g']) if a['h'] == 'sello' else (14 + a['g'] * 3) if a['h'] == 'texto' else a['g'] * 3
        for q in a['p']:
            xs += [q[0] - m, q[0] + m * (len(a.get('texto', '')) * .6 + 1 if a['h'] == 'texto' else 1)]
            ys += [q[1] - m, q[1] + m]
    x0, y0, x1, y1 = min(xs), min(ys), max(xs), max(ys)
    k = ancho_px / 1000
    cuerpo = ''.join(_svg_marca(a) for a in anotaciones)
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{x0:.1f} {y0:.1f} {x1 - x0:.1f} {y1 - y0:.1f}" '
           f'width="{(x1 - x0) * k:.1f}" height="{(y1 - y0) * k:.1f}">{cuerpo}</svg>')
    return {'src': 'data:image/svg+xml;base64,' + base64.b64encode(svg.encode()).decode(),
            'css': f'left:{x0 * k:.1f}px;top:{y0 * k:.1f}px;width:{(x1 - x0) * k:.1f}px;height:{(y1 - y0) * k:.1f}px'}


# Tamaños de hoja (ancho × alto en mm). Oficio: el de Colombia (8,5 × 13 pulgadas).
PAPELES = {'carta': ('Carta', 215.9, 279.4), 'oficio': ('Oficio', 215.9, 330.2), 'a4': ('A4', 210.0, 297.0)}
UNIDADES = {'mm': ('milímetros', 1.0), 'cm': ('centímetros', 10.0), 'in': ('pulgadas', 25.4), 'px': ('píxeles', 25.4 / 96)}


def papel(p):
    """{'tipo', 'ancho', 'alto', 'unidad', 'ancho_mm', 'alto_mm', 'nombre'}: carta si no viene nada válido."""
    p = p if isinstance(p, dict) else {}
    tipo = p.get('tipo') if p.get('tipo') in PAPELES or p.get('tipo') == 'personalizado' else 'carta'
    if tipo in PAPELES:
        nombre, ancho_mm, alto_mm = PAPELES[tipo]
        return {'tipo': tipo, 'nombre': nombre, 'unidad': 'cm', 'ancho': round(ancho_mm / 10, 2), 'alto': round(alto_mm / 10, 2),
                'ancho_mm': ancho_mm, 'alto_mm': alto_mm}
    unidad = p.get('unidad') if p.get('unidad') in UNIDADES else 'cm'
    factor = UNIDADES[unidad][1]

    def medida(v, defecto):
        try:
            v = float(str(v).replace(',', '.'))
        except (TypeError, ValueError):
            return defecto
        return v if v > 0 else defecto
    ancho = medida(p.get('ancho'), 215.9 / factor)
    alto = medida(p.get('alto'), 279.4 / factor)
    # entre 7 cm y 60 cm de ancho, y entre 7 cm y 120 cm de alto
    ancho_mm = round(min(600.0, max(70.0, ancho * factor)), 1)
    alto_mm = round(min(1200.0, max(70.0, alto * factor)), 1)
    return {'tipo': 'personalizado', 'nombre': 'Personalizado', 'unidad': unidad,
            'ancho': round(ancho_mm / factor, 2), 'alto': round(alto_mm / factor, 2), 'ancho_mm': ancho_mm, 'alto_mm': alto_mm}


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
         'lineas': _entero(b.get('lineas'), 3 if modo in ('abierta',) else 0, 0, 20),
         'solucion': texto_plano(b.get('solucion'), 2000)}
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
    elif modo == 'sopa':
        from . import juegos
        n['palabras'] = [p for p in (juegos.palabra_limpia(x) for x in (b.get('palabras') or [])[:juegos.MAX_PALABRAS])
                         if len(p) >= juegos.MIN_LARGO]
        n['dificil'] = bool(b.get('dificil'))
        n.update(juegos.generar_sopa(n['palabras'], b.get('id') or 'x', n['dificil']))
    elif modo == 'crucigrama':
        from . import juegos
        pares = []
        for x in (b.get('pares') or [])[:juegos.MAX_PALABRAS]:
            if isinstance(x, (list, tuple)) and len(x) == 2:
                pares.append((texto_plano(x[0], 40), texto_plano(x[1], 200)))
        n['pares'] = [list(x) for x in pares if juegos.palabra_limpia(x[0])]
        n.update(juegos.generar_crucigrama(pares, b.get('id') or 'x'))
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
