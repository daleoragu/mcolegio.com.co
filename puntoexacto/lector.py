# -*- coding: utf-8 -*-
"""PuntoExacto · leer una hoja de respuestas desde una foto.

Solo numpy y Pillow, que ya están en requirements.txt. No se agrega OpenCV a
propósito: son ~60 MB en cada despliegue de DigitalOcean para un trabajo que
aquí se hace con álgebra lineal y promedios, porque la hoja no es una escena
cualquiera —sabemos exactamente qué buscar y dónde debería estar.

El camino es:

  1. encontrar las cuatro marcas negras de las esquinas;
  2. con ellas calcular la homografía que lleva milímetros de la hoja a
     píxeles de la foto (NO se endereza la imagen: se mapea cada burbuja a
     donde cayó, que es más rápido y no pierde nitidez);
  3. medir cuán oscura está cada burbuja comparada con el papel que la rodea;
  4. decidir qué se marcó.

Cada paso devuelve además por qué decidió lo que decidió, para que la pantalla
pueda mostrarle al docente una hoja dudosa en vez de inventarse una nota.
"""
import numpy as np
from PIL import Image, ImageOps

# Tamaño al que se reduce la foto antes de buscar las marcas. Más grande no
# mejora la detección y multiplica el tiempo en un celular.
ANCHO_BUSQUEDA = 1100


class LecturaFallida(Exception):
    """La foto no sirve. El mensaje explica qué hacer, no qué pasó por dentro."""


# ---------------------------------------------------------------------------
# Utilidades
# ---------------------------------------------------------------------------

def _a_gris(imagen):
    """Imagen PIL o ruta -> arreglo float32 en escala de grises, 0 negro."""
    if isinstance(imagen, (str, bytes)) or hasattr(imagen, 'read'):
        imagen = Image.open(imagen)
    imagen = ImageOps.exif_transpose(imagen)      # el celular rota por metadato
    return np.asarray(imagen.convert('L'), dtype=np.float32)


def _integral(a):
    """Suma acumulada 2D, para promediar cualquier ventana en tiempo constante."""
    s = np.zeros((a.shape[0] + 1, a.shape[1] + 1), dtype=np.float64)
    s[1:, 1:] = a.cumsum(0).cumsum(1)
    return s


def _media_ventanas(integ, alto, ancho):
    """Promedio de todas las ventanas alto x ancho. Devuelve matriz de medias."""
    s = integ
    total = (s[alto:, ancho:] - s[:-alto, ancho:]
             - s[alto:, :-ancho] + s[:-alto, :-ancho])
    return total / float(alto * ancho)


# ---------------------------------------------------------------------------
# 1. Las marcas de registro
# ---------------------------------------------------------------------------

def encontrar_marcas(gris, marca_mm, ancho_mm):
    """Centro de las cuatro marcas negras, en píxeles de la foto original.

    Se busca una por cuadrante y no todas a la vez: el cuadrante acota el
    problema y, sobre todo, hace que la sombra no importe. Una foto con el
    borde derecho en penumbra tiene un negro distinto al de la izquierda, y un
    umbral único se traga una marca o inventa otra.
    """
    alto0, ancho0 = gris.shape
    escala = ANCHO_BUSQUEDA / ancho0 if ancho0 > ANCHO_BUSQUEDA else 1.0
    chica = np.asarray(Image.fromarray(gris.astype(np.uint8)).resize(
        (max(1, int(ancho0 * escala)), max(1, int(alto0 * escala))), Image.BILINEAR),
        dtype=np.float32)
    alto, ancho = chica.shape

    # La hoja ocupa casi todo el cuadro, así que esto estima bien la escala.
    px_mm = ancho / float(ancho_mm)
    lado = max(6, int(round(marca_mm * px_mm)))
    if lado * 2 >= min(alto, ancho):
        raise LecturaFallida('La foto es demasiado pequeña para leerla. '
                             'Tome la foto más cerca o suba la resolución.')

    integ = _integral(chica)
    medias = _media_ventanas(integ, lado, lado)

    # Un cuadrado negro sólido es oscuro Y está rodeado de papel. Restar el
    # marco de alrededor descarta zonas grandes oscuras, como una sombra fuerte
    # o el código de barras, que son oscuras pero no están rodeadas de blanco.
    ancho_marco = max(2, lado // 2)
    lado2 = lado + 2 * ancho_marco
    if lado2 < min(alto, ancho):
        medias2 = _media_ventanas(integ, lado2, lado2)
        # Media del anillo = (suma del grande - suma del chico) / área del anillo
        area_g, area_c = lado2 * lado2, lado * lado
        rec = (medias2 * area_g)[:medias.shape[0] - 2 * ancho_marco,
                                 :medias.shape[1] - 2 * ancho_marco]
        cen = (medias * area_c)[ancho_marco:medias.shape[0] - ancho_marco,
                                ancho_marco:medias.shape[1] - ancho_marco]
        anillo = (rec - cen) / float(area_g - area_c)
        puntaje = np.full(medias.shape, 1e9, dtype=np.float32)
        puntaje[ancho_marco:medias.shape[0] - ancho_marco,
                ancho_marco:medias.shape[1] - ancho_marco] = cen / area_c - anillo
    else:
        puntaje = medias

    mitad_y, mitad_x = alto // 2, ancho // 2
    cuadrantes = [(0, mitad_y, 0, mitad_x), (0, mitad_y, mitad_x, ancho),
                  (mitad_y, alto, mitad_x, ancho), (mitad_y, alto, 0, mitad_x)]
    centros = []
    for y0, y1, x0, x1 in cuadrantes:
        sub = puntaje[y0:max(y0 + 1, y1 - lado), x0:max(x0 + 1, x1 - lado)]
        if sub.size == 0:
            raise LecturaFallida('No se reconocen las cuatro esquinas de la hoja.')
        iy, ix = np.unravel_index(np.argmin(sub), sub.shape)
        cy, cx = y0 + iy + lado / 2.0, x0 + ix + lado / 2.0
        centros.append(_afinar(chica, cx, cy, lado))

    return [(x / escala, y / escala) for x, y in centros], escala


def _afinar(chica, cx, cy, lado):
    """Centro de masa de lo oscuro alrededor del punto hallado.

    La ventana cae cerca pero no exacta; el centroide da una posición
    sub-píxel, y de ahí sale la precisión de todo lo demás.
    """
    r = int(lado * 0.9)
    y0, y1 = max(0, int(cy - r)), min(chica.shape[0], int(cy + r))
    x0, x1 = max(0, int(cx - r)), min(chica.shape[1], int(cx + r))
    parche = chica[y0:y1, x0:x1]
    if parche.size == 0:
        return cx, cy
    umbral = (parche.min() + parche.max()) / 2.0
    mascara = parche <= umbral
    if mascara.sum() < 4:
        return cx, cy
    ys, xs = np.nonzero(mascara)
    return x0 + xs.mean(), y0 + ys.mean()


# ---------------------------------------------------------------------------
# 2. De milímetros de la hoja a píxeles de la foto
# ---------------------------------------------------------------------------

def homografia(origen, destino):
    """Transformación proyectiva que lleva los 4 puntos de origen a destino."""
    A, b = [], []
    for (x, y), (u, v) in zip(origen, destino):
        A.append([x, y, 1, 0, 0, 0, -u * x, -u * y]); b.append(u)
        A.append([0, 0, 0, x, y, 1, -v * x, -v * y]); b.append(v)
    try:
        h = np.linalg.solve(np.array(A, dtype=np.float64), np.array(b, dtype=np.float64))
    except np.linalg.LinAlgError:
        raise LecturaFallida('Las esquinas detectadas no forman una hoja. '
                             'Repita la foto con la hoja completa y plana.')
    return np.append(h, 1.0).reshape(3, 3)


def _aplicar(H, puntos):
    p = np.hstack([np.asarray(puntos, dtype=np.float64),
                   np.ones((len(puntos), 1))])
    q = p @ H.T
    return q[:, :2] / q[:, 2:3]


def matriz_de_hoja(gris, geo):
    """Homografía milímetros -> píxeles, a partir de las marcas de la foto."""
    centros, _ = encontrar_marcas(gris, geo['marca_mm'], geo['ancho_mm'])
    alto_mm = geo['alto_mm']
    # Los milímetros del generador van de abajo hacia arriba; los píxeles, al
    # revés. Se invierte aquí, una sola vez, y no en cada cuenta posterior.
    destino = [(x, alto_mm - y) for x, y in geo['marcas_mm']]
    H = homografia(destino, centros)
    _validar(H, geo, gris.shape)
    return H, centros


def _validar(H, geo, forma):
    """Rechaza una homografía absurda antes de leer 80 burbujas con ella."""
    esquinas = _aplicar(H, [(0, 0), (geo['ancho_mm'], 0),
                            (geo['ancho_mm'], geo['alto_mm']), (0, geo['alto_mm'])])
    ancho = np.linalg.norm(esquinas[1] - esquinas[0])
    alto = np.linalg.norm(esquinas[3] - esquinas[0])
    if ancho < 50 or alto < 50:
        raise LecturaFallida('La hoja salió demasiado pequeña en la foto. Acérquese.')
    proporcion = (alto / ancho) / (geo['alto_mm'] / geo['ancho_mm'])
    if not 0.72 < proporcion < 1.38:
        raise LecturaFallida('La hoja se ve muy torcida o está incompleta. '
                             'Tome la foto de frente, con las cuatro esquinas negras visibles.')


# ---------------------------------------------------------------------------
# 3. Medir las burbujas
# ---------------------------------------------------------------------------

def nivel_de_negro(gris, centros, marca_mm, H):
    """Qué gris es «negro» en ESTA foto, medido en las marcas de registro.

    Son cuadrados de tinta sólida impresos en la misma hoja, con la misma luz.
    Sirven de patrón: en una foto quemada el papel se va a 255 y el negro sube
    a 120, y sin este patrón una marca de lápiz flojo parece papel sucio.
    """
    ref = _aplicar(H, [(0, 0), (marca_mm * 0.30, 0)])
    r = max(2, int(round(float(np.linalg.norm(ref[1] - ref[0])))))
    muestras = []
    for cx, cy in centros:
        y0, y1 = int(cy - r), int(cy + r + 1)
        x0, x1 = int(cx - r), int(cx + r + 1)
        if y0 < 0 or x0 < 0 or y1 > gris.shape[0] or x1 > gris.shape[1]:
            continue
        muestras.append(np.median(gris[y0:y1, x0:x1]))
    if not muestras:
        return 0.0
    # La mediana entre las cuatro: si una esquina quedó tapada por un dedo o
    # con brillo, no arrastra a las demás.
    return float(np.median(muestras))


def medir_burbujas(gris, H, mapa, radio_mm, alto_mm, negro=0.0):
    """Qué tan llena está cada burbuja, de 0 (vacía) a 1 (rellena).

    No se compara contra un umbral fijo de gris: una foto con sombra tiene el
    papel en 150 y otra con flash en 250. Se compara cada burbuja contra el
    papel que la rodea, en su propio pedazo de hoja.
    """
    claves = list(mapa.keys())
    puntos = [(mapa[k][0], alto_mm - mapa[k][1]) for k in claves]
    centros = _aplicar(H, puntos)

    # Radio en píxeles: se mide transformando un punto a un radio de distancia.
    ref = _aplicar(H, [(mapa[claves[0]][0], alto_mm - mapa[claves[0]][1]),
                       (mapa[claves[0]][0] + radio_mm, alto_mm - mapa[claves[0]][1])])
    radio_px = float(np.linalg.norm(ref[1] - ref[0]))
    if radio_px < 2.0:
        raise LecturaFallida('Las burbujas quedaron demasiado pequeñas en la foto. '
                             'Acérquese o use más resolución.')

    r_dentro = max(1.5, radio_px * 0.62)   # solo el interior, sin tocar el borde
    r_fuera0 = radio_px * 1.35             # anillo de papel, por fuera del círculo
    r_fuera1 = radio_px * 2.10

    alto_px, ancho_px = gris.shape
    radio_caja = int(np.ceil(r_fuera1)) + 1
    dy, dx = np.mgrid[-radio_caja:radio_caja + 1, -radio_caja:radio_caja + 1]
    dist = np.sqrt(dx * dx + dy * dy)
    m_dentro = dist <= r_dentro
    m_fuera = (dist >= r_fuera0) & (dist <= r_fuera1)

    medidas = {}
    posiciones = {}
    for clave, (cx, cy) in zip(claves, centros):
        posiciones[clave] = (round(float(cx), 1), round(float(cy), 1))
        ix, iy = int(round(cx)), int(round(cy))
        y0, y1 = iy - radio_caja, iy + radio_caja + 1
        x0, x1 = ix - radio_caja, ix + radio_caja + 1
        if y0 < 0 or x0 < 0 or y1 > alto_px or x1 > ancho_px:
            medidas[clave] = {'relleno': 0.0, 'fuera': True}
            continue
        parche = gris[y0:y1, x0:x1]
        dentro = parche[m_dentro]
        papel = parche[m_fuera]
        if dentro.size == 0 or papel.size == 0:
            medidas[clave] = {'relleno': 0.0, 'fuera': True}
            continue
        # El papel se toma como el percentil 70 del anillo: así una letra
        # impresa o un pedazo de la banda gris no bajan la referencia.
        nivel_papel = float(np.percentile(papel, 70))
        tinta = float(np.percentile(dentro, 35))   # el 35% más oscuro del interior
        # La escala va de «papel» a «negro de esta foto», no de papel a cero:
        # así una foto quemada y una oscura dan el mismo número para la misma
        # marca de lápiz.
        rango = max(nivel_papel - negro, 12.0)
        relleno = (nivel_papel - tinta) / rango
        medidas[clave] = {'relleno': float(np.clip(relleno, 0.0, 1.0)),
                          'papel': nivel_papel, 'tinta': tinta, 'fuera': False}
    return medidas, radio_px, posiciones


# ---------------------------------------------------------------------------
# 4. Decidir
# ---------------------------------------------------------------------------

# Dos umbrales y no uno. Con uno solo, todo el error del lector era el mismo:
# una marca floja de lápiz leída como casilla en blanco. Una marca tenue pero
# claramente más oscura que sus tres vecinas SÍ es una marca; lo que no se
# puede es aceptar como marca algo tenue cuando las vecinas están igual de
# tenues, porque eso es sombra o papel sucio.
UMBRAL_SOLO = 0.26         # tan oscura que no necesita comparación
UMBRAL_CON_VENTAJA = 0.10  # tenue, pero solo si les saca ventaja a las demás
VENTAJA_MINIMA = 0.09      # cuánto debe ganarle la primera a la segunda
UMBRAL_SOSPECHA = 0.05     # por debajo de esto es ruido de la foto, no lápiz
VENTAJA_SOSPECHA = 0.035   # y aun así tiene que destacarse de sus vecinas

def decidir(medidas, preguntas, letras_por_pregunta):
    """De las medidas a las respuestas, diciendo también de cuáles no está segura.

    Tres resultados por pregunta y no dos: marcada, en blanco, o DUDOSA. Una
    hoja con dudas va a revisión del docente. Adivinar en silencio es lo peor
    que puede hacer un lector: una nota equivocada que nadie supo que lo era.
    """
    respuestas, dudas = {}, []
    for n in range(1, preguntas + 1):
        letras = letras_por_pregunta(n)
        valores = []
        for l in letras:
            m = medidas.get(f'{n}{l}')
            valores.append((m['relleno'] if m else 0.0, l))
        valores.sort(reverse=True)
        if not valores:
            respuestas[n] = ''
            continue
        mejor, segunda = valores[0], (valores[1] if len(valores) > 1 else (0.0, None))

        ventaja = mejor[0] - segunda[0]

        if mejor[0] < UMBRAL_CON_VENTAJA:
            respuestas[n] = ''                      # en blanco
            # Pero si algo asoma por encima del ruido y de sus vecinas, se
            # avisa. Los únicos errores que quedaron en las pruebas fueron
            # marcas de lápiz muy flojas en fotos quemadas, leídas como casilla
            # vacía. Mandarlas a revisión le cuesta al docente un vistazo;
            # tragárselas en silencio le cuesta una nota mal puesta.
            if mejor[0] >= UMBRAL_SOSPECHA and ventaja >= VENTAJA_SOSPECHA:
                dudas.append({'pregunta': n, 'motivo': 'tal vez marcó, muy tenue',
                              'opciones': [mejor[1]],
                              'valores': [round(mejor[0], 3)]})
        elif mejor[0] >= UMBRAL_SOLO and ventaja < VENTAJA_MINIMA:
            # Dos burbujas bien rellenas: es doble marca, no una duda menor.
            respuestas[n] = ''
            dudas.append({'pregunta': n, 'motivo': 'hay dos marcadas',
                          'opciones': [l for _, l in valores[:2]],
                          'valores': [round(v, 3) for v, _ in valores[:2]]})
        elif ventaja < VENTAJA_MINIMA:
            respuestas[n] = ''
            dudas.append({'pregunta': n, 'motivo': 'no se distingue cuál marcó',
                          'opciones': [l for _, l in valores[:2]],
                          'valores': [round(v, 3) for v, _ in valores[:2]]})
        else:
            respuestas[n] = mejor[1]
            if mejor[0] < UMBRAL_SOLO:
                dudas.append({'pregunta': n, 'motivo': 'marca muy tenue',
                              'opciones': [mejor[1]], 'valores': [round(mejor[0], 3)]})
    return respuestas, dudas


# ---------------------------------------------------------------------------
# Todo junto
# ---------------------------------------------------------------------------

def leer(imagen, geo, mapa, radio_mm, preguntas, letras_por_pregunta):
    """Lee una foto y devuelve respuestas, dudas y datos para depurar."""
    gris = _a_gris(imagen)
    H, centros = matriz_de_hoja(gris, geo)
    negro = nivel_de_negro(gris, centros, geo['marca_mm'], H)
    medidas, radio_px, posiciones = medir_burbujas(
        gris, H, mapa, radio_mm, geo['alto_mm'], negro)
    respuestas, dudas = decidir(medidas, preguntas, letras_por_pregunta)
    return {
        'respuestas': respuestas, 'dudas': dudas,
        'marcas': centros, 'radio_px': radio_px, 'negro': negro,
        'medidas': medidas,
        # Dónde cayó cada burbuja EN LA FOTO. Es lo que permite dibujar los
        # círculos encima de la imagen en el celular y que el docente toque la
        # que el estudiante marcó de verdad.
        'posiciones': posiciones,
        'ancho_foto': int(gris.shape[1]), 'alto_foto': int(gris.shape[0]),
    }


# ---------------------------------------------------------------------------
# 5. De qué estudiante es esta hoja
# ---------------------------------------------------------------------------

def _dibujo_de_barras(identificador, geo):
    """(perfil teórico 0/1, ancho en puntos) del código de ese identificador.

    En vez de escribir la tabla de 107 símbolos del Code 128, se le pide el
    dibujo a reportlab, que es la misma biblioteca que lo imprimió. Un
    decodificador propio tendría que ser perfecto; esto solo necesita
    distinguir entre los pocos identificadores que ese examen tiene.

    reportlab describe el código como letras: mayúscula = barra, minúscula =
    espacio, y A/B/C/D = 1/2/3/4 módulos de ancho.
    """
    from reportlab.graphics.barcode import code128

    ancho_barra = geo['barras_ancho_pt']
    alto = geo['barras_grosor_mm'] * 72 / 25.4
    largo_max = geo['barras_largo_max_mm'] * 72 / 25.4
    bc = code128.Code128(identificador, barHeight=alto, barWidth=ancho_barra,
                         humanReadable=False)
    while bc.width > largo_max and bc.barWidth > 0.28:
        bc = code128.Code128(identificador, barHeight=alto,
                             barWidth=bc.barWidth - 0.02, humanReadable=False)
    bc.validate(); bc.encode()
    trozos = bc.decompose()
    anchos = [(c.isupper(), ord(c.upper()) - ord('A') + 1) for c in trozos]
    modulos = sum(w for _, w in anchos)
    # bc.width NO es solo las barras: reportlab le suma una zona de silencio a
    # cada lado (18 pt por omisión). Si se ignoran, el patrón teórico queda
    # estirado sobre toda la franja y no correlaciona con nada. Esto costó un
    # rato de depuración y por eso queda escrito.
    return {'anchos': anchos, 'modulos': modulos, 'ancho_pt': bc.width,
            'lquiet': bc.lquiet, 'rquiet': bc.rquiet, 'barra_pt': bc.barWidth}


def firma_de_barras(gris, H, geo, largo_pt):
    """Perfil de gris a lo largo del código de barras, en coordenadas de hoja.

    Se promedian nueve líneas paralelas: una sola se arruina con un doblez o
    una mota de polvo; la mediana de nueve, no.
    """
    largo_mm = largo_pt * 25.4 / 72
    x0 = geo['barras_x_mm']
    y0 = geo['barras_y0_mm']
    alto_hoja = geo['alto_mm']
    muestras = 1600
    perfiles = []
    for desvio in np.linspace(-geo['barras_grosor_mm'] * 0.30,
                              geo['barras_grosor_mm'] * 0.30, 9):
        puntos = [(x0 + desvio, alto_hoja - y)
                  for y in np.linspace(y0, y0 + largo_mm, muestras)]
        px = _aplicar(H, puntos)
        xs = np.clip(np.round(px[:, 0]).astype(int), 0, gris.shape[1] - 1)
        ys = np.clip(np.round(px[:, 1]).astype(int), 0, gris.shape[0] - 1)
        perfiles.append(gris[ys, xs])
    perfil = np.median(np.vstack(perfiles), axis=0)
    lo, hi = np.percentile(perfil, 4), np.percentile(perfil, 96)
    if hi - lo < 12:
        return None                      # ahí no hay código, hay papel
    return np.clip((hi - perfil) / (hi - lo), 0.0, 1.0)


def _perfil_teorico(dib, muestras):
    """Perfil 0/1 a lo largo de TODO el ancho que ocupa el código, silencios
    incluidos, porque eso es lo que la foto va a recorrer."""
    total_pt = dib['ancho_pt']
    teorico = np.zeros(muestras, dtype=np.float64)
    pos_pt = dib['lquiet']
    for es_barra, w in dib['anchos']:
        ancho_pt = w * dib['barra_pt']
        a = int(muestras * pos_pt / total_pt)
        b = int(muestras * (pos_pt + ancho_pt) / total_pt)
        if es_barra:
            teorico[a:b] = 1.0
        pos_pt += ancho_pt
    return teorico


def _bordes(firma, umbral=0.5):
    """Posiciones (sub-muestra) donde el perfil cruza de claro a oscuro y al revés."""
    s = (firma >= umbral).astype(np.int8)
    cambios = np.nonzero(np.diff(s))[0]
    bordes = []
    for i in cambios:
        a, b = firma[i], firma[i + 1]
        frac = 0.5 if b == a else (umbral - a) / (b - a)
        bordes.append(i + frac)
    return np.array(bordes), s


def _tabla_patrones():
    """Patrones de Code 128 como vectores de anchos, pedidos a reportlab.

    Se le pide a la misma biblioteca que imprimió el código, así que no hay dos
    versiones de la verdad. Mayúscula = barra, minúscula = espacio, A/B/C/D =
    1/2/3/4 módulos.
    """
    from reportlab.graphics.barcode import code128
    tabla = {}
    for valor, patron in code128._patterns.items():
        anchos = [ord(c.upper()) - ord('A') + 1 for c in patron]
        tabla[valor] = anchos
    return tabla


_TABLA = None


def _bordes_a_bordes(anchos):
    """Distancias de borde a borde homólogo: w1+w2, w2+w3, ...

    Es la medida estándar para leer códigos de barras y la razón es física: la
    tinta se corre, y una barra impresa o fotografiada sale más ancha de lo que
    debería exactamente en lo que el espacio vecino sale más angosto. La suma
    de los dos no cambia. Medir cada elemento por separado —que fue mi primer
    intento— se equivocaba hasta en medio módulo y no decodificaba nada.
    """
    a = np.asarray(anchos, dtype=np.float64)
    return a[:-1] + a[1:]


def decodificar_code128(firma):
    """Lee el identificador impreso en el código de barras. None si no se puede.

    Decodifica de verdad, símbolo por símbolo, con dígito verificador. No
    compara la foto contra la lista de estudiantes: dos identificadores que se
    diferencian en el último dígito dan códigos casi idénticos y la
    correlación entre el correcto y el equivocado se separaba por centésimas.
    Con centésimas no se le pone una nota a un estudiante.
    """
    global _TABLA
    if _TABLA is None:
        _TABLA = _tabla_patrones()

    bordes, s = _bordes(firma)
    if len(bordes) < 13:
        return None
    inicio = bordes[0] if s[0] == 0 else 0.0
    anchos = np.diff(np.concatenate([[inicio], bordes[bordes > inicio]]))
    # Code 128: n símbolos de 6 elementos y el de parada con 7.
    if len(anchos) < 25 or (len(anchos) - 1) % 6 != 0:
        return None
    n_simbolos = (len(anchos) - 1) // 6

    referencias = {v: _bordes_a_bordes(a) for v, a in _TABLA.items()}
    valores = []
    pos = 0
    for k in range(n_simbolos):
        largo = 7 if k == n_simbolos - 1 else 6
        grupo = anchos[pos:pos + largo]
        pos += largo
        total = grupo.sum()
        if total <= 0:
            return None
        modulos = (13.0 if largo == 7 else 11.0)
        w = grupo * (modulos / total)
        e = _bordes_a_bordes(w)
        mejor, mejor_d = None, 1e9
        for valor, ref in referencias.items():
            if len(ref) != len(e):
                continue
            d = float(np.sum((ref - e) ** 2))
            if d < mejor_d:
                mejor, mejor_d = valor, d
        # Un símbolo bien leído cae casi encima de su patrón. Si no, la foto no
        # da y es mejor decirlo que entregar un identificador inventado.
        if mejor is None or mejor_d > 1.6:
            return None
        valores.append(mejor)

    if len(valores) < 4 or valores[-1] != 106:
        return None
    arranque, verificador = valores[0], valores[-2]
    cuerpo = valores[1:-2]
    if arranque not in (103, 104, 105):
        return None
    suma = arranque + sum((k + 1) * v for k, v in enumerate(cuerpo))
    if suma % 103 != verificador:
        return None
    return _a_texto(arranque, cuerpo)


def _a_texto(arranque, valores):
    """Valores de Code 128 a la cadena original (juegos A, B y C)."""
    juego = {103: 'A', 104: 'B', 105: 'C'}[arranque]
    salida = []
    for v in valores:
        if v in (99, 100, 101) and juego != 'C' or v == 99:
            if v == 99: juego = 'C'; continue
            if v == 100: juego = 'B'; continue
            if v == 101: juego = 'A'; continue
        if juego == 'C':
            if v > 99:
                if v == 100: juego = 'B'; continue
                if v == 101: juego = 'A'; continue
                return None
            salida.append(f'{v:02d}')
        elif juego == 'B':
            if v == 100: juego = 'B'; continue
            if v == 101: juego = 'A'; continue
            if v > 95: continue
            salida.append(chr(v + 32))
        else:  # juego A
            if v == 100: juego = 'B'; continue
            if v > 95: continue
            salida.append(chr(v + 32) if v < 64 else chr(v - 64))
    return ''.join(salida)


def identificar_hoja(gris, H, geo, candidatos=()):
    """Identificador impreso en la hoja. Devuelve (texto o None, cómo se supo).

    Si lo decodificado coincide con uno de los identificadores del examen, se
    devuelve ese. Si decodifica pero no está en la lista, también se devuelve,
    porque puede ser una hoja de otro examen y el docente debe saberlo en vez
    de que se la asignen a cualquiera.
    """
    candidatos = list(candidatos)
    referencia = candidatos[0] if candidatos else 'PE-00000-0000'
    try:
        dib = _dibujo_de_barras(referencia, geo)
    except Exception:
        return None, 'no se pudo preparar el patrón'
    firma = firma_de_barras(gris, H, geo, dib['ancho_pt'])
    if firma is None:
        return None, 'no se ve el código de barras en la foto'
    texto = decodificar_code128(firma)
    if texto is None:
        return None, 'el código de barras no se pudo leer'
    texto = texto.strip()
    if candidatos and texto not in candidatos:
        return texto, 'el código leído no es de este examen'
    return texto, 'leído del código de barras'
