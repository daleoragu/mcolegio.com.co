"""Hoja de respuestas de PuntoExacto.

Varias hojas en una sola página de papel: 1, 2, 4 u 8. CADA hoja lleva sus
propias cuatro marcas de registro y su propio código de barras. No se
comparten, porque el docente va a recortar la página y repartir los pedazos,
y cada pedazo tiene que poder leerse solo.

Sobre el espacio en blanco
--------------------------
La versión anterior usaba pasos fijos (9 mm entre burbujas, 8.4 mm entre
filas) sin importar cuántas preguntas tuviera el examen. Resultado: un examen
de 10 preguntas dibujaba una franja apretada arriba y dejaba media hoja
vacía. Ahora el cálculo va al revés: se mide el rectángulo que queda libre
debajo del encabezado y la rejilla se estira para ocuparlo. El número de
columnas se elige probando de 1 a 6 y quedándose con la que permite la
burbuja más grande; el sobrante se reparte centrando, no acumulándolo abajo.
"""
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas as rl_canvas
from reportlab.graphics.barcode import code128

ANCHO, ALTO = letter
LETRAS = 'ABCDEFGHIJ'

# Cómo se parte la página para cada opción: (columnas, filas)
REPARTO = {1: (1, 1), 2: (1, 2), 4: (2, 2), 8: (2, 4)}

# Radio mínimo legible en una foto de celular. Por debajo de esto la burbuja
# se confunde con el grano de la imagen, así que es un piso duro.
RADIO_MIN = 1.55 * mm

# Radio máximo por reparto. Más grande no se lee mejor y empieza a verse mal.
RADIO_MAX = {1: 3.5 * mm, 2: 3.0 * mm, 4: 2.5 * mm, 8: 2.1 * mm}

# Hasta cuánto se puede separar una burbuja de la siguiente, en múltiplos del
# radio. Sin este tope, un examen de 5 preguntas en hoja completa quedaba con
# las burbujas en las esquinas, unidas por nada.
SEP_X_MAX = 3.9
SEP_Y_MAX = 3.6


def _recortar(c, texto, fuente, tam, ancho):
    """Corta por ancho real y no por número de letras.

    Con el escudo y el sello, el espacio del encabezado cambia según la hoja;
    cortar en 46 caracteres dejaba nombres largos encimados en unas hojas y
    cortados de más en otras.
    """
    texto = texto or ''
    if ancho <= 0 or c.stringWidth(texto, fuente, tam) <= ancho:
        return texto
    while texto and c.stringWidth(texto + '…', fuente, tam) > ancho:
        texto = texto[:-1]
    return texto + '…'


def _medidas(por_pagina):
    """Tamaño de la celda y de los elementos que no dependen de la rejilla."""
    cols, filas = REPARTO[por_pagina]
    escala = {1: 1.0, 2: 0.78, 4: 0.60, 8: 0.46}[por_pagina]
    return {
        'por_pagina': por_pagina,
        'cols': cols, 'filas': filas,
        'w': ANCHO / cols, 'h': ALTO / filas,
        'marca': max(5 * mm, 12 * mm * escala),
        'margen': max(3.5 * mm, 9 * mm * escala),
        'barras_alto': max(5.5 * mm, 9 * mm * escala),
        'barras_ancho': max(0.30, 0.52 * escala),
        'franja': max(8 * mm, 13 * mm * escala),
        'fuente': max(6.0, 10 * escala),
        'rmax': RADIO_MAX[por_pagina],
    }


def _area_util(m):
    """Rectángulo libre para las burbujas: (x, y, ancho, alto) relativos."""
    f = m['fuente']
    # Encabezado: colegio + línea de datos + título + recuadro del estudiante.
    alto_cab = f * 1.35 + f * 1.3 + f * 1.2 + 4 * mm + f * 2.4 + 3.5 * mm
    x = m['margen'] + m['franja']
    ancho = m['w'] - m['margen'] - m['franja'] - m['margen']
    arriba = m['h'] - m['margen'] - m['marca'] - 3.5 * mm - alto_cab
    abajo = m['margen'] + m['marca'] + 2 * mm
    return x, abajo, ancho, max(0, arriba - abajo)


def _rejilla_en(util_w, util_h, preguntas, opciones, f, rmax, radio_fijo=None):
    """Mejor rejilla dentro de un rectángulo dado.

    radio_fijo sirve para los exámenes por bloques: todos los bloques deben
    dibujar la burbuja del mismo tamaño aunque tengan distinto número de
    preguntas, o la hoja queda despareja.
    """
    if util_h <= 0 or preguntas <= 0:
        return None
    num_w = f * 2.1          # espacio del número de pregunta a la izquierda
    hueco_col = 3.5 * mm     # separación entre columnas de preguntas

    mejor = None
    for cols in range(1, 9):
        if cols > preguntas:
            break
        por_col = -(-preguntas // cols)
        ancho_col = (util_w - hueco_col * (cols - 1)) / cols
        burbujas_w = ancho_col - num_w
        if burbujas_w <= 0:
            continue
        paso_x = burbujas_w / opciones
        paso_y = util_h / por_col
        radio = min(paso_x * 0.33, paso_y * 0.33, rmax)
        if radio_fijo is not None:
            if paso_x * 0.33 < radio_fijo or paso_y * 0.33 < radio_fijo:
                continue
            radio = radio_fijo
        if radio < RADIO_MIN:
            continue
        # Se prefiere el radio más grande; a igual radio, menos columnas.
        clave = (round(radio, 4), -cols)
        if mejor is None or clave > mejor[0]:
            mejor = (clave, {
                'cols': cols, 'por_col': por_col, 'radio': radio,
                'paso_x': min(paso_x, radio * SEP_X_MAX),
                'paso_y': min(paso_y, radio * SEP_Y_MAX),
                'num_w': num_w, 'hueco_col': hueco_col,
            })
    if mejor is None:
        return None
    r = mejor[1]
    r['ancho_col'] = r['num_w'] + r['paso_x'] * opciones
    r['ancho_total'] = r['ancho_col'] * r['cols'] + r['hueco_col'] * (r['cols'] - 1)
    r['alto_total'] = r['paso_y'] * r['por_col']
    return r


def _rejilla(m, preguntas, opciones):
    _, _, util_w, util_h = _area_util(m)
    return _rejilla_en(util_w, util_h, preguntas, opciones, m['fuente'], m['rmax'])


# Pestaña vertical con el nombre del bloque, al estilo de la hoja del ICFES.
PESTANA_W = 5.2 * mm
HUECO_BLOQUE = 3.0 * mm

# Verdes y azules apagados: imprimen bien en blanco y negro (quedan grises
# distintos) y no compiten con las burbujas.
COLORES_BLOQUE = [
    (0.42, 0.55, 0.31), (0.25, 0.45, 0.55), (0.55, 0.45, 0.25),
    (0.45, 0.35, 0.50), (0.30, 0.52, 0.45), (0.58, 0.38, 0.35),
]


def _bloques(m, secciones, opciones):
    # Cada sección puede fijar sus propias opciones ('opciones') y el número de
    # burbujas de cada pregunta ('op_pregunta'). Si no las trae, hereda las del
    # examen. La rejilla del bloque se dibuja con la pregunta más ancha.
    """Reparte el área útil entre los bloques y les da una burbuja común.

    secciones: [{'nombre': 'Matemáticas', 'n': 20}, ...]. La numeración es
    corrida entre bloques, como en la hoja del ICFES: el bloque 2 empieza
    donde terminó el bloque 1.

    Devuelve None si no caben con el radio mínimo.
    """
    _, ay, aw, ah = _area_util(m)
    f = m['fuente']
    total = sum(s['n'] for s in secciones)
    if total <= 0:
        return None
    k = len(secciones)
    alto_rotulo = f * 1.15 if k > 1 else 0.0
    ancho_bloque = aw - (PESTANA_W if k > 1 else 0.0)
    alto_libre = ah - HUECO_BLOQUE * (k - 1) - alto_rotulo * k
    if alto_libre <= 0 or ancho_bloque <= 0:
        return None

    # Primer reparto proporcional al número de preguntas.
    altos = [alto_libre * s['n'] / total for s in secciones]

    # Radio común: el menor que permita cada bloque en su franja.
    radio = m['rmax']
    for s, alto in zip(secciones, altos):
        r = _rejilla_en(ancho_bloque, alto, s['n'], s.get('opciones') or opciones,
                        f, m['rmax'])
        if r is None:
            return None
        radio = min(radio, r['radio'])
    if radio < RADIO_MIN:
        return None

    rejillas = []
    for s, alto in zip(secciones, altos):
        op = s.get('opciones') or opciones
        r = _rejilla_en(ancho_bloque, alto, s['n'], op, f, m['rmax'], radio_fijo=radio)
        if r is None:
            r = _rejilla_en(ancho_bloque, alto, s['n'], op, f, m['rmax'])
            if r is None:
                return None
        r['opciones'] = op
        r['op_pregunta'] = s.get('op_pregunta') or [op] * s['n']
        r['rot_pregunta'] = s.get('rot_pregunta') or []
        rejillas.append(r)

    # Se apilan de arriba hacia abajo repartiendo el sobrante entre todos.
    usado = sum(r['alto_total'] for r in rejillas) + alto_rotulo * k + HUECO_BLOQUE * (k - 1)
    sobra = max(0.0, ah - usado)
    relleno = sobra / (k + 1)
    bloques, cursor, numero = [], ay + ah - relleno, 1
    for s, r in zip(secciones, rejillas):
        tope = cursor - alto_rotulo
        bloques.append({
            'nombre': s['nombre'], 'desde': numero, 'hasta': numero + s['n'] - 1,
            'bloque_id': s.get('bloque_id'),
            'n': s['n'], 'rej': r, 'tope': tope, 'alto_rotulo': alto_rotulo,
            'ancho': ancho_bloque,
        })
        numero += s['n']
        cursor = tope - r['alto_total'] - HUECO_BLOQUE - relleno
    return {'bloques': bloques, 'radio': radio, 'pestana': k > 1}


def capacidad(por_pagina, opciones=4):
    """Máximo de preguntas que caben sin bajar del radio mínimo."""
    m = _medidas(por_pagina)
    tope = 0
    for n in range(1, 241):
        if _rejilla(m, n, opciones) is None:
            break
        tope = n
    return tope



def ancho_de_barra(por_pagina, identificador):
    """El módulo más ancho que quepa en la franja, hasta un tope.

    Antes era un valor fijo (0.52 pt, menos de 0.2 mm). Sobre papel se ve
    perfecto, pero una cámara de celular tiene que resolver esa barra en uno o
    dos píxeles y el código no se deja leer: el lector decodificaba menos de la
    tercera parte de las fotos. Ahora se engorda hasta llenar el espacio
    disponible, que es gratis —esa franja no la usa nada más— y multiplica por
    dos o tres los píxeles por barra.
    """
    from reportlab.graphics.barcode import code128
    m = _medidas(por_pagina)
    disponible = m['h'] - 2 * m['margen'] - 2 * m['marca'] - 6 * mm
    mejor = 0.30
    paso = 0.02
    ancho = 0.30
    while ancho <= 1.40:
        bc = code128.Code128(identificador, barHeight=m['barras_alto'],
                             barWidth=ancho, humanReadable=False)
        if bc.width > disponible:
            break
        mejor = ancho
        ancho += paso
    return round(mejor, 2)


def _codigo_barras(c, ox, oy, m, identificador):
    """Code 128 vertical en el margen izquierdo, donde no estorba.

    Va rotado 90 grados pegado al borde: esa franja no la usa nada más, así que
    el código no le quita espacio al encabezado ni a las burbujas. Es la razón
    de fondo para preferirlo al QR en hojas pequeñas.

    Debajo va el mismo identificador en letras legibles. Si la foto sale mala y
    el código no se puede leer, el docente lo teclea y sigue adelante en vez de
    quedarse con una hoja huérfana.
    """
    ancho = ancho_de_barra(m['por_pagina'], identificador)
    bc = code128.Code128(identificador, barHeight=m['barras_alto'],
                         barWidth=ancho, humanReadable=False)
    c.saveState()
    c.translate(ox + m['margen'] + m['barras_alto'] + 1.2 * mm,
                oy + m['margen'] + m['marca'] + 3 * mm)
    c.rotate(90)
    bc.drawOn(c, 0, 0)
    c.restoreState()

    c.saveState()
    c.translate(ox + m['margen'] + 1.0 * mm, oy + m['margen'] + m['marca'] + 3 * mm)
    c.rotate(90)
    c.setFont('Helvetica', m['fuente'] * .55)
    c.setFillColorRGB(.4, .4, .4)
    c.drawString(0, 0, identificador)
    c.setFillColorRGB(0, 0, 0)
    c.restoreState()
    return bc.width


def _sello(c, x_der, y_tope, f):
    """Recuadro «PuntoExacto» con un chulito, arriba a la derecha.

    El chulito se dibuja con dos líneas y no con una fuente: así no depende de
    que la impresora tenga ZapfDingbats ni de cómo la tipografía dibuje el
    símbolo, que es justo el tipo de cosa que se descubre con 300 hojas ya
    impresas.

    Devuelve el ancho que ocupó, para que el encabezado no se le encime.
    """
    alto = f * 1.9
    texto = 'PuntoExacto'
    ancho_txt = c.stringWidth(texto, 'Helvetica-Bold', f * .78)
    lado_chulo = alto * .42
    ancho = lado_chulo + 2.2 * mm + ancho_txt + 5 * mm
    x = x_der - ancho
    y = y_tope - alto

    c.setLineWidth(0.7)
    c.setStrokeColorRGB(.22, .36, .52)
    c.setFillColorRGB(.96, .975, .99)
    c.roundRect(x, y, ancho, alto, alto * .28, stroke=1, fill=1)

    # Chulito
    cx = x + 2.5 * mm
    cy = y + alto * .5
    c.setStrokeColorRGB(.13, .50, .33)
    c.setLineWidth(max(0.9, lado_chulo * .26))
    c.setLineCap(1)
    c.line(cx, cy - lado_chulo * .04, cx + lado_chulo * .36, cy - lado_chulo * .42)
    c.line(cx + lado_chulo * .36, cy - lado_chulo * .42, cx + lado_chulo, cy + lado_chulo * .48)
    c.setLineCap(0)

    c.setFillColorRGB(.17, .28, .42)
    c.setFont('Helvetica-Bold', f * .78)
    c.drawString(cx + lado_chulo + 2.2 * mm, cy - f * .27, texto)

    c.setStrokeColorRGB(0, 0, 0)
    c.setFillColorRGB(0, 0, 0)
    c.setLineWidth(1)
    return ancho


def _escudo(c, x, y_tope, lado, imagen):
    """Escudo del colegio, encajado en un cuadrado sin deformarlo."""
    try:
        iw, ih = imagen.getSize()
    except Exception:
        return 0
    if not iw or not ih:
        return 0
    escala = min(lado / iw, lado / ih)
    w, h = iw * escala, ih * escala
    try:
        c.drawImage(imagen, x + (lado - w) / 2, y_tope - lado + (lado - h) / 2,
                    w, h, mask='auto')
    except Exception:
        return 0
    return lado


def _una_hoja(c, ox, oy, m, datos, preguntas, opciones, plan, escudo=None):
    """Dibuja una hoja completa dentro de la celda que empieza en (ox, oy).

    plan es lo que devuelve _bloques(). Devuelve el mapa
    {'1A': (x_mm, y_mm), ...} con el centro de cada burbuja medido desde la
    esquina inferior izquierda de la hoja. Ese mapa es lo que después usa el
    lector de fotos: no tiene que adivinar la geometría.
    """
    mg, mk = m['margen'], m['marca']
    f = m['fuente']
    mapa_forma = {}

    # Marcas de registro propias de esta hoja
    c.setFillColorRGB(0, 0, 0)
    for mx, my in [(ox + mg, oy + m['h'] - mg - mk), (ox + m['w'] - mg - mk, oy + m['h'] - mg - mk),
                   (ox + mg, oy + mg), (ox + m['w'] - mg - mk, oy + mg)]:
        c.rect(mx, my, mk, mk, stroke=0, fill=1)

    # Línea punteada de corte, si comparte página
    if m['cols'] * m['filas'] > 1:
        c.setDash(1, 3); c.setLineWidth(0.4); c.setStrokeColorRGB(.7, .7, .7)
        c.rect(ox + 1 * mm, oy + 1 * mm, m['w'] - 2 * mm, m['h'] - 2 * mm, stroke=1, fill=0)
        c.setDash(); c.setStrokeColorRGB(0, 0, 0)

    izq = ox + mg + m['franja']
    ancho_cab = m['w'] - 2 * mg - m['franja']
    y = oy + m['h'] - mg - mk - 3.5 * mm

    # Sello de PuntoExacto arriba a la derecha, y escudo del colegio a la
    # izquierda. El texto del encabezado se corre para no encimarse con ninguno.
    ancho_sello = _sello(c, izq + ancho_cab, y + f * .75, f)
    texto_izq = izq
    if escudo is not None:
        lado = f * 3.1
        if _escudo(c, izq, y + f * .8, lado, escudo):
            texto_izq = izq + lado + 2.5 * mm

    tope_texto = ancho_cab - ancho_sello - 3 * mm - (texto_izq - izq)
    c.setFont('Helvetica-Bold', f)
    c.drawString(texto_izq, y, _recortar(c, datos['colegio'], 'Helvetica-Bold', f, tope_texto))
    y -= f * 1.35
    c.setFont('Helvetica', f * .82)
    c.drawString(texto_izq, y, _recortar(
        c, f"{datos['materia']} · {datos['curso']} · {datos['periodo']}",
        'Helvetica', f * .82, ancho_cab - (texto_izq - izq)))
    y -= f * 1.3
    c.setFont('Helvetica-Bold', f * .95)
    c.drawString(texto_izq, y, _recortar(c, datos['titulo'], 'Helvetica-Bold', f * .95,
                                         ancho_cab * .62 - (texto_izq - izq)))
    c.setFont('Helvetica', f * .7)
    c.setFillColorRGB(.45, .45, .45)
    tope_op = max([rej['opciones'] for rej in (b['rej'] for b in plan['bloques'])] or [opciones])
    c.drawRightString(izq + ancho_cab, y,
                      f'{preguntas} preguntas · hasta {LETRAS[tope_op - 1]}')
    c.setFillColorRGB(0, 0, 0)
    y -= f * 1.2

    # Recuadro del estudiante
    y -= 4 * mm
    alto_caja = f * 2.4
    base = y - alto_caja
    c.setLineWidth(0.6)
    c.rect(izq, base, ancho_cab, alto_caja, stroke=1, fill=0)

    # Forma del examen, si tiene varias claves: el estudiante rellena la
    # burbuja de la forma que le tocó (se la dicen en el examen impreso), igual
    # que una pregunta más. Las burbujas son del mismo tamaño que las de las
    # preguntas porque el lector mide todas con el mismo radio.
    ancho_forma = 0
    letras_forma = datos.get('formas') or ''
    if len(letras_forma) > 1:
        # Del tamaño de las de las preguntas, salvo en hojas chicas, donde se
        # achican para caber en el recuadro. El lector mide con el radio de las
        # preguntas y solo mira el centro de la burbuja, así que lee igual.
        radio_f = min(plan['radio'], alto_caja / 2 - 1.1 * mm)
        paso_f = min(plan['bloques'][0]['rej']['paso_x'], radio_f * 3.2)
        c.setFont('Helvetica-Bold', f * .62)
        ancho_txt = c.stringWidth('FORMA', 'Helvetica-Bold', f * .62)
        ancho_forma = ancho_txt + 2.2 * mm + paso_f * len(letras_forma) + 1.0 * mm
        fx = izq + ancho_cab - ancho_forma
        yc = base + alto_caja / 2
        c.setLineWidth(0.6)
        c.line(fx - 1.2 * mm, base, fx - 1.2 * mm, base + alto_caja)
        c.drawString(fx, yc - f * .22, 'FORMA')
        for i, letra in enumerate(letras_forma):
            cx = fx + ancho_txt + 2.2 * mm + paso_f * (i + 0.5)
            c.setLineWidth(0.8)
            c.circle(cx, yc, radio_f, stroke=1, fill=0)
            tam = min(f * .6, radio_f * 1.45)
            c.setFont('Helvetica', tam)
            c.setFillColorRGB(.5, .5, .5)
            c.drawCentredString(cx, yc - tam * .3, letra)
            c.setFillColorRGB(0, 0, 0)
            mapa_forma[f'F{letra}'] = (round((cx - ox) / mm, 2), round((yc - oy) / mm, 2))
        c.setLineWidth(0.6)
        ancho_forma += 2.4 * mm

    c.setFont('Helvetica-Bold', f * .95)
    c.drawString(izq + 1.6 * mm, base + alto_caja * .55, _recortar(
        c, datos['estudiante'][:44], 'Helvetica-Bold', f * .95,
        ancho_cab - ancho_forma - 3.2 * mm))
    c.setFont('Helvetica', f * .68)
    c.setFillColorRGB(.35, .35, .35)
    c.drawString(izq + 1.6 * mm, base + alto_caja * .18, f"Doc: {datos['documento']}"[:34])

    # Docente y fecha, si el examen pidió imprimirlos. Van dentro del mismo
    # recuadro, a la derecha: así no le quitan una línea a las burbujas, que es
    # lo único de la hoja que no se puede encoger.
    extra = ' · '.join(x for x in (datos.get('docente'), datos.get('fecha')) if x)
    if extra:
        c.setFont('Helvetica', f * .68)
        c.setFillColorRGB(.35, .35, .35)
        c.drawRightString(izq + ancho_cab - ancho_forma - 1.6 * mm, base + alto_caja * .18,
                          _recortar(c, extra, 'Helvetica', f * .68, ancho_cab * .5 - ancho_forma))
    c.setFillColorRGB(0, 0, 0)

    # --- Bloques de burbujas ---
    ax, _, aw, _ = _area_util(m)
    ax += ox
    mapa = {}
    for idx, b in enumerate(plan['bloques']):
        rej = b['rej']
        radio = rej['radio']
        # Las columnas se reparten a lo ancho del bloque (justificadas), y el
        # bloque arranca pegado al margen izquierdo: así la hoja se lee como
        # una tabla y no como un rectángulo flotando en el centro.
        x0_bloque = ax
        if rej['cols'] > 1:
            hueco = (b['ancho'] - rej['ancho_col'] * rej['cols']) / (rej['cols'] - 1)
            paso_col = rej['ancho_col'] + max(rej['hueco_col'], hueco)
            ancho_banda = b['ancho']
        else:
            paso_col = rej['ancho_col'] + rej['hueco_col']
            ancho_banda = rej['ancho_total']
        tope = oy + b['tope']

        # Rótulo del bloque y pestaña lateral, solo si hay más de uno.
        if plan['pestana']:
            color = COLORES_BLOQUE[idx % len(COLORES_BLOQUE)]
            c.setFillColorRGB(*color)
            c.setFont('Helvetica-Bold', f * .8)
            c.drawString(ax, tope + f * .3, (b['nombre'] or '').upper()[:40])
            c.setFont('Helvetica', f * .66)
            c.setFillColorRGB(.5, .5, .5)
            c.drawString(ax + c.stringWidth((b['nombre'] or '').upper()[:40],
                                            'Helvetica-Bold', f * .8) + 2.5 * mm,
                         tope + f * .3, f"preguntas {b['desde']} a {b['hasta']}")
            # Pestaña vertical pegada al borde derecho del área.
            px = ax + aw - PESTANA_W
            c.setFillColorRGB(*color)
            c.rect(px, tope - rej['alto_total'], PESTANA_W, rej['alto_total'],
                   stroke=0, fill=1)
            c.saveState()
            c.translate(px + PESTANA_W * .72, tope - rej['alto_total'] + 1.5 * mm)
            c.rotate(90)
            c.setFillColorRGB(1, 1, 1)
            c.setFont('Helvetica-Bold', min(f * .7, PESTANA_W * 1.6))
            c.drawString(0, 0, (b['nombre'] or '')[:26])
            c.restoreState()
            c.setFillColorRGB(0, 0, 0)

        for fila in range(rej['por_col']):
            if fila % 2 == 0:
                yy = tope - rej['paso_y'] * (fila + 0.5)
                c.setFillColorRGB(.945, .955, .965)
                c.rect(ax, yy - rej['paso_y'] / 2, ancho_banda, rej['paso_y'],
                       stroke=0, fill=1)
                c.setFillColorRGB(0, 0, 0)

        for j in range(b['n']):
            n = b['desde'] + j
            col, fila = j // rej['por_col'], j % rej['por_col']
            cx0 = x0_bloque + col * paso_col
            yy = tope - rej['paso_y'] * (fila + 0.5)

            c.setFont('Helvetica-Bold', min(f * .8, radio * 2.0))
            c.drawRightString(cx0 + rej['num_w'] - 2.0 * mm, yy - radio * .55, str(n))
            op_n = rej['op_pregunta'][j] if j < len(rej['op_pregunta']) else rej['opciones']
            rot_j = rej['rot_pregunta'][j] if j < len(rej['rot_pregunta']) else []
            for i in range(op_n):
                cx = cx0 + rej['num_w'] + rej['paso_x'] * (i + 0.5)
                c.setLineWidth(0.8)
                c.circle(cx, yy, radio, stroke=1, fill=0)
                # Lo impreso es la etiqueta (V, F, Sí…); el mapa de abajo sigue
                # con la letra interna, que es la que entiende el lector.
                texto = rot_j[i] if i < len(rot_j) and rot_j[i] else LETRAS[i]
                tam = min(f * .6, radio * 1.45)
                if len(texto) > 1:
                    tam = min(tam, radio * 1.05)
                c.setFont('Helvetica', tam)
                c.setFillColorRGB(.5, .5, .5)
                c.drawCentredString(cx, yy - tam * .3, texto)
                c.setFillColorRGB(0, 0, 0)
                mapa[f'{n}{LETRAS[i]}'] = (round((cx - ox) / mm, 2), round((yy - oy) / mm, 2))

        # Separador vertical entre columnas de preguntas
        if rej['cols'] > 1:
            c.setStrokeColorRGB(.82, .82, .82); c.setLineWidth(0.4)
            for col in range(1, rej['cols']):
                sx = x0_bloque + col * paso_col - (paso_col - rej['ancho_col']) / 2
                c.line(sx, tope - rej['alto_total'], sx, tope)
            c.setStrokeColorRGB(0, 0, 0)

    # Las burbujas de forma van al final del mapa: el lector toma el radio de la
    # primera burbuja, y esa debe ser una de pregunta.
    mapa.update(mapa_forma)

    # Pie: a la izquierda la instrucción, a la derecha la firma de la plataforma.
    y_pie = oy + mg + mk * .25
    c.setFont('Helvetica', f * .6)
    c.setFillColorRGB(.5, .5, .5)
    c.drawString(izq, y_pie,
                 'Rellene por completo una sola burbuja por pregunta. Lápiz o tinta oscura.')
    # Firma de la plataforma. Termina antes de la marca de registro de abajo a
    # la derecha: si el texto la pisa, la marca deja de ser un cuadrado negro
    # limpio, y esa es la esquina con la que el lector de fotos endereza la hoja.
    _firma(c, ox + m['w'] - mg - mk - 2.5 * mm, y_pie, f)
    c.setFillColorRGB(0, 0, 0)
    return mapa


def _firma(c, x_der, y, f):
    """«Generado con» + el logo de mcolegio.com.co, abajo a la derecha.

    El logo trae el dominio completo: un docente de otro colegio que recoja una
    hoja del piso tiene que poder leer de dónde salió sin acercarse. Si el
    archivo del logo no estuviera, se escribe el dominio como antes.
    """
    previo = 'Generado con '
    t_prev = f * .62
    logo = _logo_mcolegio()
    if logo is not None:
        alto = f * 1.25
        ancho = alto * logo[1]
        c.drawImage(logo[0], x_der - ancho, y - alto * .28, width=ancho, height=alto, mask='auto')
        ocupado = ancho
    else:
        dominio, t_dom = 'mcolegio.com.co', f * .74
        c.setFont('Helvetica-Bold', t_dom)
        c.setFillColorRGB(.17, .28, .42)
        c.drawRightString(x_der, y, dominio)
        ocupado = c.stringWidth(dominio, 'Helvetica-Bold', t_dom)
    c.setFont('Helvetica', t_prev)
    c.setFillColorRGB(.55, .58, .63)
    c.drawRightString(x_der - ocupado - 1.0 * mm, y, previo)


_LOGO = []


def _logo_mcolegio():
    """(ImageReader, ancho/alto) del logo horizontal, o None si no se encuentra."""
    if not _LOGO:
        try:
            from django.contrib.staticfiles import finders
            from reportlab.lib.utils import ImageReader
            ruta = finders.find('img/mcolegio-logo.png')
            img = ImageReader(ruta) if ruta else None
            _LOGO.append((img, img.getSize()[0] / img.getSize()[1]) if img else None)
        except Exception:
            _LOGO.append(None)
    return _LOGO[0]


def generar(ruta, lista_datos, preguntas=10, opciones=4, por_pagina=1,
            identificadores=None, secciones=None, escudo=None, devolver_mapa=False):
    """secciones: [{'nombre': 'Matemáticas', 'n': 20}, ...] o None.

    Con secciones la hoja sale por bloques rotulados, con numeración corrida,
    como la hoja de respuestas del ICFES. Sin secciones sale un solo bloque,
    sin rótulo ni pestaña.
    """
    m = _medidas(por_pagina)
    if secciones:
        preguntas = sum(s['n'] for s in secciones)
        plan = _bloques(m, secciones, opciones)
    else:
        plan = _bloques(m, [{'nombre': None, 'n': preguntas}], opciones)
    if plan is None:
        tope = capacidad(por_pagina, opciones)
        raise ValueError(
            f'Con {por_pagina} hoja(s) por página y {opciones} opciones caben {tope} '
            f'preguntas en un solo bloque, y se pidieron {preguntas}'
            + (f' en {len(secciones)} bloques' if secciones else '')
            + '. Use menos hojas por página o menos bloques.')

    c = rl_canvas.Canvas(ruta, pagesize=letter)
    mapa = {}
    for i, datos in enumerate(lista_datos):
        pos = i % por_pagina
        if i and pos == 0:
            c.showPage()
        col, fila = pos % m['cols'], pos // m['cols']
        ox = col * m['w']
        oy = ALTO - (fila + 1) * m['h']
        mapa = _una_hoja(c, ox, oy, m, datos, preguntas, opciones, plan, escudo)
        if identificadores:
            _codigo_barras(c, ox, oy, m, identificadores[i])
    c.showPage(); c.save()
    if devolver_mapa:
        return {'mapa': mapa, 'radio_mm': round(plan['radio'] / mm, 2),
                'bloques': [{'nombre': b['nombre'], 'desde': b['desde'],
                             'hasta': b['hasta'], 'cols': b['rej']['cols']}
                            for b in plan['bloques']],
                'hoja_w_mm': round(m['w'] / mm, 2), 'hoja_h_mm': round(m['h'] / mm, 2)}


def geometria(por_pagina, identificador=None):
    """Dónde están las marcas de registro, en mm desde la esquina inferior
    izquierda de la hoja. Es lo que el lector de fotos necesita para enderezar.

    Se calcula de los mismos valores con que se dibujan, en vez de repetirlos:
    si mañana cambia el margen, el lector se entera solo.
    """
    m = _medidas(por_pagina)
    w, h, mg, mk = m['w'] / mm, m['h'] / mm, m['margen'] / mm, m['marca'] / mm
    return {
        'ancho_mm': round(w, 3), 'alto_mm': round(h, 3),
        'marca_mm': round(mk, 3),
        # Franja del código de barras, en los mismos milímetros. Sale de cómo
        # lo dibuja _codigo_barras(): trasladado y girado 90 grados, así que
        # su largo crece hacia arriba y su grosor hacia la izquierda.
        'barras_x_mm': round(mg + 1.0 + (m['barras_alto'] / mm) / 2, 3),
        'barras_grosor_mm': round(m['barras_alto'] / mm, 3),
        'barras_y0_mm': round(mg + mk + 3, 3),
        'barras_ancho_pt': (ancho_de_barra(por_pagina, identificador)
                            if identificador else round(m['barras_ancho'], 4)),
        'barras_largo_max_mm': round(h - 2 * mg - 2 * mk - 6, 3),
        # Orden fijo: superior izquierda, superior derecha, inferior derecha,
        # inferior izquierda. El lector depende de ese orden.
        'marcas_mm': [
            (round(mg + mk / 2, 3), round(h - mg - mk / 2, 3)),
            (round(w - mg - mk / 2, 3), round(h - mg - mk / 2, 3)),
            (round(w - mg - mk / 2, 3), round(mg + mk / 2, 3)),
            (round(mg + mk / 2, 3), round(mg + mk / 2, 3)),
        ],
    }


def sugerir_por_pagina(preguntas, opciones=4):
    """Cuántas hojas por página aprovechan mejor el papel sin apretar.

    Se devuelve el reparto más denso en el que las preguntas siguen entrando
    con holgura (hasta el 80% del tope), porque llenar un reparto al 100%
    deja la hoja al límite del radio mínimo.
    """
    for por_pagina in (8, 4, 2, 1):
        tope = capacidad(por_pagina, opciones)
        if tope and preguntas <= tope * 0.8:
            return por_pagina
    return 1


# ---------------------------------------------------------------------------
# Puente con los modelos
# ---------------------------------------------------------------------------

def _escudo_del_colegio(colegio):
    """El escudo del colegio como imagen lista para dibujar, o None.

    Se intenta primero `escudo` y luego `logo_izquierdo`. Todo va dentro de
    try/except a propósito: el archivo puede estar en DigitalOcean Spaces y no
    responder, o estar registrado en la base pero borrado del bucket. Una hoja
    de respuestas sin escudo sirve igual; una hoja que no se imprime porque la
    imagen falló, no.
    """
    if colegio is None:
        return None
    import io as _io
    from reportlab.lib.utils import ImageReader

    for campo in ('escudo', 'logo_izquierdo'):
        archivo = getattr(colegio, campo, None)
        if not archivo:
            continue
        try:
            with archivo.open('rb') as f:
                datos = f.read()
            if datos:
                return ImageReader(_io.BytesIO(datos))
        except Exception:
            continue
    return None


_CACHE_MAPA = {}


def letras_de_formas(examen):
    """'ABC' si el examen tiene formas B y C; '' si solo tiene la A."""
    otras = ''.join(examen.formas.order_by('letra').values_list('letra', flat=True))
    return ('A' + otras) if otras else ''


def mapa_de_examen(examen):
    """Dónde queda cada burbuja de ESTE examen, en milímetros de la hoja.

    Se genera dibujando una hoja de mentira y quedándose con el mapa, en vez de
    guardar la geometría en la base. Así nunca se desincroniza: si el docente
    cambia el número de preguntas o las opciones, el mapa cambia con él. Se
    guarda en memoria del proceso porque dibujar el PDF cuesta unos milisegundos
    y una tanda de 40 fotos lo pediría 40 veces.
    """
    import io

    por_pagina = examen.hojas_por_pagina or 1
    secciones = examen.secciones_para_hoja()
    firma = (examen.id, examen.numero_preguntas, examen.numero_opciones,
             por_pagina, repr(secciones),
             tuple(sorted((p.numero, p.numero_opciones or 0)
                          for p in examen.preguntas.all())),
             letras_de_formas(examen))
    if firma in _CACHE_MAPA:
        return _CACHE_MAPA[firma]

    datos = {'colegio': '', 'materia': '', 'curso': '', 'periodo': '',
             'titulo': '', 'estudiante': '', 'documento': '',
             'docente': '', 'fecha': '', 'formas': letras_de_formas(examen)}
    info = generar(io.BytesIO(), [datos], preguntas=examen.numero_preguntas,
                   opciones=examen.opciones_maximas(), por_pagina=por_pagina,
                   secciones=secciones, devolver_mapa=True)
    if len(_CACHE_MAPA) > 64:
        _CACHE_MAPA.clear()
    _CACHE_MAPA[firma] = info
    return info


def generar_pdf(examen, hojas_examen, por_pagina=None):
    """Devuelve los bytes del PDF con la hoja de cada estudiante.

    El identificador que va en el código de barras es el de la Hoja, que ya
    quedó guardado en la base. Así la foto se puede amarrar a su estudiante sin
    reconocer el nombre escrito, que es lo que más falla.
    """
    import io

    # por_pagina llega desde la pantalla de impresión; si no, manda lo que
    # quedó guardado en el examen.
    por_pagina = por_pagina or examen.hojas_por_pagina or 1
    if por_pagina not in REPARTO:
        por_pagina = 1
    tope = capacidad(por_pagina, examen.opciones_maximas())
    if examen.numero_preguntas > tope:
        raise ValueError(
            f'Con {por_pagina} hoja(s) por página y {examen.numero_opciones} opciones '
            f'caben {tope} preguntas, y el examen tiene {examen.numero_preguntas}. '
            f'Baje las hojas por página o el número de opciones.')

    colegio = examen.colegio.nombre if examen.colegio_id else ''
    imagen = _escudo_del_colegio(examen.colegio if examen.colegio_id else None)
    materia = curso = ''
    if examen.asignacion_id:
        materia = examen.asignacion.materia.nombre
        curso = examen.asignacion.curso.nombre
    periodo = str(examen.periodo) if examen.periodo_id else ''

    nombre_docente = ''
    if examen.mostrar_docente and examen.docente_id:
        u = examen.docente.user
        nombre_docente = (u.get_full_name() or u.username).strip()
    texto_fecha = ''
    if examen.mostrar_fecha and examen.fecha:
        texto_fecha = examen.fecha.strftime('%d/%m/%Y')

    # Las burbujas de forma solo salen si el examen tiene más de una clave.
    letras_forma = letras_de_formas(examen)

    datos = []
    identificadores = []
    for h in hojas_examen:
        datos.append({
            'colegio': colegio, 'materia': materia, 'curso': curso,
            'periodo': periodo, 'titulo': examen.titulo,
            'estudiante': h.nombre, 'documento': h.documento or '',
            'docente': nombre_docente, 'fecha': texto_fecha,
            'formas': letras_forma,
        })
        identificadores.append(h.identificador)

    buffer = io.BytesIO()
    generar(buffer, datos, preguntas=examen.numero_preguntas,
            opciones=examen.opciones_maximas(), por_pagina=por_pagina,
            identificadores=identificadores, secciones=examen.secciones_para_hoja(),
            escudo=imagen)
    return buffer.getvalue()
