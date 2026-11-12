"""Dibujos exactos del material semilla, hechos en código (SVG) con el mismo estilo plano de las imágenes de IA:
contorno grueso marrón oscuro y colores vivos. Lo que debe ser exacto (cantidades, bloques, rectas, relojes, planos)
se dibuja aquí; una IA cuenta mal.

Cada dibujo tiene un id con sus datos («d-bloques-3-4», «d-reloj-3-30») para que una guía lo pida y el PNG se genere
una sola vez (materiales/semilla/img/, con scripts/semilla_png.js). En el servidor solo se usan los PNG.
"""
import math

CONTORNO = '#5a3311'
ROJO, AMARILLO, VERDE, AZUL, NARANJA = '#e63946', '#ffd166', '#52b788', '#4ea8de', '#f4a261'
AZUL_OSC, GRIS = '#1f3a68', '#94a3b8'
LETRA = "font-family:'Nunito','Arial Rounded MT Bold',Arial,sans-serif;font-weight:800"


def _svg(ancho, alto, cuerpo):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {ancho} {alto}" width="{ancho}" height="{alto}">'
            f'<rect width="100%" height="100%" fill="#fff"/>{cuerpo}</svg>')


def _txt(x, y, t, tam=22, color=AZUL_OSC, ancla='middle'):
    return f'<text x="{x}" y="{y}" font-size="{tam}" text-anchor="{ancla}" fill="{color}" style="{LETRA}">{t}</text>'


# --- Base 10 ------------------------------------------------------------------------------------------------------
def bloques(decenas, unidades):
    """Barras de diez (verdes, con sus 10 cuadritos) y cubos sueltos (amarillos)."""
    c, x, partes = 22, 20, []
    for _ in range(decenas):
        for k in range(10):
            partes.append(f'<rect x="{x}" y="{20 + k * c}" width="{c}" height="{c}" fill="{VERDE}" stroke="{CONTORNO}" stroke-width="2.5"/>')
        x += c + 14
    x += 16 if decenas else 0
    for k in range(unidades):
        fila, col = divmod(k, 3)
        partes.append(f'<rect x="{x + col * (c + 6)}" y="{20 + 9 * c - fila * (c + 6)}" width="{c}" height="{c}" fill="{AMARILLO}" '
                      f'stroke="{CONTORNO}" stroke-width="2.5"/>')
    ancho = x + (3 * (c + 6) if unidades else 0) + 14
    return _svg(max(ancho, 120), 20 + 10 * c + 20, ''.join(partes))


def paquetes(decenas, unidades):
    """Lápices amarrados de a 10 (con su cinta) y lápices sueltos."""
    def lapiz(x, y):
        return (f'<rect x="{x}" y="{y + 12}" width="7" height="86" fill="{AMARILLO}" stroke="{CONTORNO}" stroke-width="1.5"/>'
                f'<path d="M{x} {y + 12}l3.5 -12 3.5 12z" fill="#f4e3c1" stroke="{CONTORNO}" stroke-width="1.5"/>'
                f'<rect x="{x}" y="{y + 92}" width="7" height="8" fill="#e5989b" stroke="{CONTORNO}" stroke-width="1.5"/>')
    x, partes = 20, []
    for _ in range(decenas):
        for k in range(10):
            partes.append(lapiz(x + k * 7, 20))
        partes.append(f'<rect x="{x - 3}" y="62" width="76" height="12" rx="3" fill="{ROJO}" stroke="{CONTORNO}" stroke-width="2"/>')
        x += 96
    for k in range(unidades):
        partes.append(lapiz(x + k * 16, 20))
    return _svg(max(x + unidades * 16 + 10, 120), 140, ''.join(partes))


def marco10(rojos, azules=0):
    """Marco de 10 (2 filas de 5) con fichas: rojas y luego azules (para el paso por el diez)."""
    c, partes = 56, []
    for k in range(10):
        f, col = divmod(k, 5)
        x, y = 20 + col * c, 20 + f * c
        partes.append(f'<rect x="{x}" y="{y}" width="{c}" height="{c}" fill="#fff" stroke="{AZUL_OSC}" stroke-width="3"/>')
        if k < rojos + azules:
            color = ROJO if k < rojos else AZUL
            partes.append(f'<circle cx="{x + c / 2}" cy="{y + c / 2}" r="19" fill="{color}" stroke="{CONTORNO}" stroke-width="2.5"/>')
    return _svg(40 + 5 * c, 40 + 2 * c, ''.join(partes))


def tabla100(resaltar=()):
    """Tabla del 1 al 100; las casillas de «resaltar» van en amarillo."""
    c, partes = 40, []
    for n in range(1, 101):
        f, col = divmod(n - 1, 10)
        x, y = 10 + col * c, 10 + f * c
        partes.append(f'<rect x="{x}" y="{y}" width="{c}" height="{c}" fill="{AMARILLO if n in resaltar else "#fff"}" '
                      f'stroke="{GRIS}" stroke-width="1.5"/>' + _txt(x + c / 2, y + 27, n, 17))
    return _svg(20 + 10 * c, 20 + 10 * c, ''.join(partes))


# --- Recta numérica ------------------------------------------------------------------------------------------------
def recta(desde=0, hasta=20, saltos=(), vacios=()):
    """Recta numérica con marcas; «saltos» = [(de, a)] dibuja arcos; «vacios» = números que se dejan en blanco."""
    paso = 44 if hasta - desde <= 20 else 30
    x0, y = 30, 110
    partes = [f'<path d="M{x0 - 15} {y}H{x0 + (hasta - desde) * paso + 15}" stroke="{AZUL_OSC}" stroke-width="4" stroke-linecap="round"/>']
    for n in range(desde, hasta + 1):
        x = x0 + (n - desde) * paso
        partes.append(f'<path d="M{x} {y - 10}V{y + 10}" stroke="{AZUL_OSC}" stroke-width="3"/>')
        if n in vacios:
            partes.append(f'<rect x="{x - 15}" y="{y + 18}" width="30" height="28" rx="5" fill="#fff" stroke="{ROJO}" stroke-width="2.5"/>')
        else:
            partes.append(_txt(x, y + 40, n, 20))
    for a, b in saltos:
        xa, xb = x0 + (a - desde) * paso, x0 + (b - desde) * paso
        alto = 26 + 6 * min(abs(b - a), 6)
        partes.append(f'<path d="M{xa} {y - 12}Q{(xa + xb) / 2} {y - 12 - alto * 2} {xb} {y - 12}" fill="none" stroke="{ROJO}" '
                      f'stroke-width="3.5" stroke-linecap="round"/><path d="M{xb} {y - 12}l-9 -7M{xb} {y - 12}l-2 -11" stroke="{ROJO}" '
                      f'stroke-width="3.5" stroke-linecap="round"/>')
    return _svg(2 * x0 + (hasta - desde) * paso, 170, ''.join(partes))


# --- Medida ----------------------------------------------------------------------------------------------------------
def regla(cm=15, largo=0):
    """Regla en centímetros; si «largo», un lápiz de ese largo encima, empezando en el cero."""
    u, x0 = 36, 30
    partes = [f'<rect x="{x0 - 14}" y="80" width="{cm * u + 28}" height="62" rx="6" fill="{AMARILLO}" stroke="{CONTORNO}" stroke-width="3"/>']
    for k in range(cm * 2 + 1):
        x = x0 + k * u / 2
        partes.append(f'<path d="M{x} 80V{100 if k % 2 else 110}" stroke="{CONTORNO}" stroke-width="2"/>')
        if k % 2 == 0:
            partes.append(_txt(x, 132, k // 2, 17, CONTORNO))
    if largo:
        L = largo * u
        partes.append(f'<rect x="{x0 + 18}" y="38" width="{L - 36}" height="26" fill="{AZUL}" stroke="{CONTORNO}" stroke-width="2.5"/>'
                      f'<path d="M{x0 + L - 18} 38L{x0 + L} 51L{x0 + L - 18} 64z" fill="#f4e3c1" stroke="{CONTORNO}" stroke-width="2.5"/>'
                      f'<rect x="{x0}" y="38" width="18" height="26" fill="#e5989b" stroke="{CONTORNO}" stroke-width="2.5"/>'
                      f'<path d="M{x0} 70V80M{x0 + L} 70V80" stroke="{ROJO}" stroke-width="2" stroke-dasharray="3 2"/>')
    return _svg(cm * u + 60, 160, ''.join(partes))


def lapices(*largos):
    """Lápices de distintos largos (en «cuadros»), uno debajo de otro, para comparar y ordenar."""
    u, partes, colores = 34, [], (ROJO, AZUL, VERDE, NARANJA, AMARILLO)
    for k, L in enumerate(largos):
        y, ancho = 20 + k * 52, L * u
        partes.append(f'<rect x="38" y="{y}" width="{ancho - 40}" height="28" fill="{colores[k % 5]}" stroke="{CONTORNO}" stroke-width="2.5"/>'
                      f'<path d="M{ancho - 2} {y}L{ancho + 18} {y + 14}L{ancho - 2} {y + 28}z" fill="#f4e3c1" stroke="{CONTORNO}" stroke-width="2.5"/>'
                      f'<rect x="20" y="{y}" width="18" height="28" fill="#e5989b" stroke="{CONTORNO}" stroke-width="2.5"/>'
                      + _txt(ancho + 44, y + 22, chr(65 + k), 20))
    return _svg(max(largos) * u + 70, 30 + len(largos) * 52, ''.join(partes))


def reloj(hora, minutos=0):
    """Reloj de manecillas."""
    cx = cy = 130
    partes = [f'<circle cx="{cx}" cy="{cy}" r="110" fill="#fff" stroke="{AZUL_OSC}" stroke-width="8"/>']
    for h in range(1, 13):
        a = math.radians(h * 30 - 90)
        partes.append(_txt(cx + 84 * math.cos(a), cy + 84 * math.sin(a) + 9, h, 26))
        partes.append(f'<circle cx="{cx + 102 * math.cos(a)}" cy="{cy + 102 * math.sin(a)}" r="3" fill="{AZUL_OSC}"/>')
    am = math.radians(minutos * 6 - 90)
    ah = math.radians((hora % 12) * 30 + minutos * 0.5 - 90)
    partes.append(f'<path d="M{cx} {cy}L{cx + 52 * math.cos(ah)} {cy + 52 * math.sin(ah)}" stroke="{ROJO}" stroke-width="10" stroke-linecap="round"/>')
    partes.append(f'<path d="M{cx} {cy}L{cx + 82 * math.cos(am)} {cy + 82 * math.sin(am)}" stroke="{AZUL}" stroke-width="6" stroke-linecap="round"/>')
    partes.append(f'<circle cx="{cx}" cy="{cy}" r="9" fill="{CONTORNO}"/>')
    return _svg(260, 260, ''.join(partes))


def balanza(izquierda, derecha, inclina=0):
    """Balanza de dos platos con una expresión en cada uno («3 + 2» y «5»). inclina: −1 izq. abajo, 0 equilibrio, 1 der. abajo."""
    d = 18 * inclina
    yi, yd = 120 - d, 120 + d
    partes = [f'<path d="M200 70V250M150 250H250" stroke="{CONTORNO}" stroke-width="8" stroke-linecap="round"/>',
              f'<path d="M80 {yi - 50}L320 {yd - 50}" stroke="{CONTORNO}" stroke-width="7" stroke-linecap="round"/>',
              f'<circle cx="200" cy="70" r="10" fill="{AMARILLO}" stroke="{CONTORNO}" stroke-width="3"/>']
    for x, y, t in ((80, yi, izquierda), (320, yd, derecha)):
        partes.append(f'<path d="M{x} {y - 50}L{x - 50} {y}M{x} {y - 50}L{x + 50} {y}" stroke="{GRIS}" stroke-width="2.5"/>'
                      f'<path d="M{x - 62} {y}Q{x} {y + 34} {x + 62} {y}z" fill="{AZUL}" stroke="{CONTORNO}" stroke-width="3"/>'
                      f'<rect x="{x - 52}" y="{y - 46}" width="104" height="40" rx="8" fill="#fff" stroke="{AZUL_OSC}" stroke-width="2.5"/>'
                      + _txt(x, y - 17, t, 24))
    return _svg(400, 270, ''.join(partes))


# --- Geometría -------------------------------------------------------------------------------------------------------
def figuras(nombres=False):
    """Círculo, cuadrado, triángulo y rectángulo (con nombre debajo si «nombres»)."""
    p = [f'<circle cx="80" cy="90" r="55" fill="{ROJO}" stroke="{CONTORNO}" stroke-width="4"/>',
         f'<rect x="175" y="35" width="110" height="110" fill="{AZUL}" stroke="{CONTORNO}" stroke-width="4"/>',
         f'<path d="M380 35L440 145H320z" fill="{AMARILLO}" stroke="{CONTORNO}" stroke-width="4" stroke-linejoin="round"/>',
         f'<rect x="480" y="55" width="170" height="90" fill="{VERDE}" stroke="{CONTORNO}" stroke-width="4"/>']
    if nombres:
        p += [_txt(80, 185, 'círculo'), _txt(230, 185, 'cuadrado'), _txt(380, 185, 'triángulo'), _txt(565, 185, 'rectángulo')]
    return _svg(680, 200 if nombres else 170, ''.join(p))


def solidos(nombres=False):
    """Esfera, cubo, cilindro, cono y prisma rectangular en perspectiva sencilla."""
    k = CONTORNO
    p = [f'<circle cx="75" cy="100" r="55" fill="{ROJO}" stroke="{k}" stroke-width="4"/><ellipse cx="75" cy="100" rx="55" ry="16" fill="none" stroke="{k}" stroke-width="2" stroke-dasharray="5 4"/><ellipse cx="55" cy="78" rx="12" ry="8" fill="#fff" opacity=".45"/>',
         # cubo
         f'<path d="M170 70h80v80h-80z" fill="{AZUL}" stroke="{k}" stroke-width="4"/><path d="M170 70l28-26h80l-28 26z" fill="#90e0ef" stroke="{k}" stroke-width="4" stroke-linejoin="round"/><path d="M250 70l28-26v80l-28 26z" fill="#3a86c8" stroke="{k}" stroke-width="4" stroke-linejoin="round"/>',
         # cilindro
         f'<path d="M320 60v85a45 14 0 0 0 90 0V60" fill="{AMARILLO}" stroke="{k}" stroke-width="4"/><ellipse cx="365" cy="60" rx="45" ry="14" fill="#ffe8a3" stroke="{k}" stroke-width="4"/>',
         # cono
         f'<path d="M500 40L455 145a45 14 0 0 0 90 0z" fill="{VERDE}" stroke="{k}" stroke-width="4" stroke-linejoin="round"/><ellipse cx="500" cy="145" rx="45" ry="14" fill="#95d5b2" stroke="{k}" stroke-width="4"/>',
         # prisma rectangular
         f'<path d="M585 85h120v65h-120z" fill="{NARANJA}" stroke="{k}" stroke-width="4"/><path d="M585 85l26-24h120l-26 24z" fill="#f8c9a0" stroke="{k}" stroke-width="4" stroke-linejoin="round"/><path d="M705 85l26-24v65l-26 24z" fill="#d9822b" stroke="{k}" stroke-width="4" stroke-linejoin="round"/>']
    if nombres:
        p += [_txt(75, 190, 'esfera'), _txt(225, 190, 'cubo'), _txt(365, 190, 'cilindro'), _txt(500, 190, 'cono'), _txt(660, 190, 'prisma')]
    return _svg(760, 205 if nombres else 175, ''.join(p))


def lineas_abiertas():
    """Cuatro líneas: curva cerrada, curva abierta, poligonal cerrada y poligonal abierta (A, B, C, D)."""
    k = AZUL_OSC
    p = [f'<path d="M40 90c0-50 110-60 120-10s-40 70-80 60-40-20-40-50z" fill="none" stroke="{k}" stroke-width="5"/>',
         f'<path d="M210 120c10-70 60-90 90-40s40 40 60-10" fill="none" stroke="{k}" stroke-width="5" stroke-linecap="round"/>',
         f'<path d="M400 140l20-100 70 30 40 70z" fill="none" stroke="{k}" stroke-width="5" stroke-linejoin="round"/>',
         f'<path d="M570 140l30-90 50 70 40-80" fill="none" stroke="{k}" stroke-width="5" stroke-linejoin="round" stroke-linecap="round"/>',
         _txt(100, 185, 'A', 24, ROJO), _txt(285, 185, 'B', 24, ROJO), _txt(465, 185, 'C', 24, ROJO), _txt(630, 185, 'D', 24, ROJO)]
    return _svg(720, 200, ''.join(p))


# --- Ubicación -------------------------------------------------------------------------------------------------------
def plano_salon():
    """Plano del salón visto desde arriba: tablero, puerta, ventana, escritorio del profe y 3 filas de pupitres (A, B, C)."""
    k = CONTORNO
    p = [f'<rect x="20" y="20" width="560" height="420" fill="#fdf6e3" stroke="{k}" stroke-width="6"/>',
         f'<rect x="150" y="26" width="300" height="18" fill="{VERDE}" stroke="{k}" stroke-width="3"/>' + _txt(300, 70, 'tablero', 18),
         f'<rect x="440" y="90" width="110" height="50" fill="{NARANJA}" stroke="{k}" stroke-width="3"/>' + _txt(495, 122, 'profe', 16),
         f'<path d="M20 330v80" stroke="#fff" stroke-width="10"/><path d="M20 330a80 80 0 0 1 80 80" fill="none" stroke="{k}" stroke-width="3" stroke-dasharray="6 4"/>'
         + _txt(60, 312, 'puerta', 16),
         f'<path d="M580 170v120" stroke="{AZUL}" stroke-width="10"/>' + _txt(555, 235, 'ventana', 15, AZUL_OSC, 'end')]
    for fila, y in zip('ABC', (170, 250, 330)):
        for col in range(4):
            x = 120 + col * 95
            p.append(f'<rect x="{x}" y="{y}" width="60" height="40" rx="4" fill="{AMARILLO}" stroke="{k}" stroke-width="3"/>')
        p.append(_txt(95, y + 27, fila, 20, ROJO))
    for col in range(4):
        p.append(_txt(150 + col * 95, 400, col + 1, 18, ROJO))
    return _svg(600, 460, ''.join(p))


def cuadricula(n=6, inicio=(0, 5), meta=(5, 0), camino=()):
    """Cuadrícula de recorridos: estrella en el inicio, casa en la meta y, si «camino», el recorrido con flechas."""
    c, o = 64, 20
    p = []
    for f in range(n):
        for col in range(n):
            p.append(f'<rect x="{o + col * c}" y="{o + f * c}" width="{c}" height="{c}" fill="#fff" stroke="{GRIS}" stroke-width="2"/>')
    cx, cy = o + inicio[0] * c + c / 2, o + inicio[1] * c + c / 2
    estrella = ' '.join(f'{cx + (24 if k % 2 == 0 else 10) * math.cos(math.radians(k * 36 - 90))},'
                        f'{cy + (24 if k % 2 == 0 else 10) * math.sin(math.radians(k * 36 - 90))}' for k in range(10))
    p.append(f'<polygon points="{estrella}" fill="{AMARILLO}" stroke="{CONTORNO}" stroke-width="3"/>')
    mx, my = o + meta[0] * c + c / 2, o + meta[1] * c + c / 2
    p.append(f'<path d="M{mx - 22} {my}L{mx} {my - 22}L{mx + 22} {my}z" fill="{ROJO}" stroke="{CONTORNO}" stroke-width="3" stroke-linejoin="round"/>'
             f'<rect x="{mx - 16}" y="{my}" width="32" height="22" fill="#f4e3c1" stroke="{CONTORNO}" stroke-width="3"/>')
    x, y = inicio
    puntos = [(o + x * c + c / 2, o + y * c + c / 2)]
    flechas = []
    for paso in camino:
        dx, dy = {'→': (1, 0), '←': (-1, 0), '↑': (0, -1), '↓': (0, 1)}[paso]
        mx, my = o + (x + dx / 2) * c + c / 2, o + (y + dy / 2) * c + c / 2
        # punta de flecha en la mitad de cada paso, apuntando hacia donde va
        flechas.append(f'<path d="M{mx - dy * 9 - dx * 7} {my - dx * 9 - dy * 7}L{mx + dx * 9} {my + dy * 9}L{mx + dy * 9 - dx * 7} {my + dx * 9 - dy * 7}" '
                       f'fill="none" stroke="{AZUL}" stroke-width="5" stroke-linecap="round" stroke-linejoin="round"/>')
        x, y = x + dx, y + dy
        puntos.append((o + x * c + c / 2, o + y * c + c / 2))
    if camino:
        p.insert(n * n, f'<polyline points="{" ".join(f"{a},{b}" for a, b in puntos)}" fill="none" stroke="{AZUL}" stroke-width="5" '
                        f'stroke-linecap="round" stroke-linejoin="round" opacity=".55"/>')
        p += flechas
    return _svg(2 * o + n * c, 2 * o + n * c, ''.join(p))


# --- Datos -----------------------------------------------------------------------------------------------------------
def tabla_conteo(datos):
    """Tabla de conteo con palitos agrupados de 5 en 5: datos = [(nombre, cantidad)]."""
    alto, p = 58, []
    p.append(f'<rect x="20" y="20" width="560" height="{alto}" fill="{AZUL_OSC}"/>' + _txt(130, 57, 'Dato', 20, '#fff') + _txt(400, 57, 'Conteo', 20, '#fff'))
    for k, (nombre, n) in enumerate(datos):
        y = 20 + (k + 1) * alto
        p.append(f'<rect x="20" y="{y}" width="560" height="{alto}" fill="{"#f8fafc" if k % 2 else "#fff"}" stroke="{GRIS}" stroke-width="2"/>'
                 f'<path d="M240 {y}v{alto}" stroke="{GRIS}" stroke-width="2"/>' + _txt(130, y + 37, nombre, 20))
        x = 260
        for g in range(0, n, 5):
            m = min(5, n - g)
            for j in range(min(m, 4)):
                p.append(f'<path d="M{x + j * 12} {y + 12}v34" stroke="{CONTORNO}" stroke-width="4" stroke-linecap="round"/>')
            if m == 5:
                p.append(f'<path d="M{x - 6} {y + 42}L{x + 44} {y + 16}" stroke="{ROJO}" stroke-width="4" stroke-linecap="round"/>')
            x += 70
    return _svg(600, 40 + (len(datos) + 1) * alto, ''.join(p))


def monedas(*valores):
    """Monedas genéricas con su valor (no son réplicas): 50, 100, 200, 500 y 1000 pesos."""
    color = {50: '#cbd5e1', 100: AMARILLO, 200: '#cbd5e1', 500: AMARILLO, 1000: NARANJA}
    p, x = [], 20
    for v in valores:
        r = 34 + min(v, 1000) / 1000 * 14
        p.append(f'<circle cx="{x + r}" cy="70" r="{r}" fill="{color.get(v, AMARILLO)}" stroke="{CONTORNO}" stroke-width="4"/>'
                 f'<circle cx="{x + r}" cy="70" r="{r - 8}" fill="none" stroke="{CONTORNO}" stroke-width="1.5" stroke-dasharray="3 3"/>'
                 + _txt(x + r, 79, f'${v}', 22 if v < 1000 else 19, CONTORNO))
        x += 2 * r + 16
    return _svg(x + 4, 140, ''.join(p))


# --- Sociales: orientación y tiempo --------------------------------------------------------------------------------
def rosa_vientos(letras=True):
    """Rosa de los vientos: Norte, Sur, Este (por donde sale el sol) y Oeste."""
    cx = cy = 150
    p = [f'<circle cx="{cx}" cy="{cy}" r="96" fill="#f8fafc" stroke="{GRIS}" stroke-width="3" stroke-dasharray="6 5"/>']
    for ang, color in ((0, ROJO), (90, AZUL_OSC), (180, AZUL_OSC), (270, AZUL_OSC)):
        a = math.radians(ang - 90)
        x, y = cx + 108 * math.cos(a), cy + 108 * math.sin(a)
        l1 = (cx + 18 * math.cos(a + math.pi / 2), cy + 18 * math.sin(a + math.pi / 2))
        l2 = (cx + 18 * math.cos(a - math.pi / 2), cy + 18 * math.sin(a - math.pi / 2))
        p.append(f'<path d="M{x} {y}L{l1[0]} {l1[1]}L{cx} {cy}z" fill="{color}" stroke="{CONTORNO}" stroke-width="2"/>'
                 f'<path d="M{x} {y}L{l2[0]} {l2[1]}L{cx} {cy}z" fill="#fff" stroke="{CONTORNO}" stroke-width="2"/>')
    if letras:
        p += [_txt(cx, 26, 'N', 30, ROJO), _txt(cx, 298, 'S', 30), _txt(287, cy + 10, 'E', 30), _txt(13, cy + 10, 'O', 30)]
    p.append(f'<circle cx="{cx}" cy="{cy}" r="9" fill="{AMARILLO}" stroke="{CONTORNO}" stroke-width="3"/>')
    return _svg(300, 310, ''.join(p))


def _norte(x, y):
    return (f'<path d="M{x} {y + 34}L{x} {y}M{x - 9} {y + 12}L{x} {y}L{x + 9} {y + 12}" stroke="{ROJO}" stroke-width="4" fill="none" '
            f'stroke-linecap="round" stroke-linejoin="round"/>' + _txt(x, y - 6, 'N', 20, ROJO))


def plano_escuela():
    """Plano de la escuela visto desde arriba, con la flecha del norte: rectoría, coordinación, sala de profesores,
    cafetería, patio de recreo, salones y la entrada."""
    k = CONTORNO
    caja = lambda x, y, w, h, color, t, tam=16: (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="6" fill="{color}" stroke="{k}" stroke-width="3"/>'
                                                  + _txt(x + w / 2, y + h / 2 + 6, t, tam))
    p = [f'<rect x="20" y="40" width="640" height="420" rx="10" fill="#fdf6e3" stroke="{k}" stroke-width="5"/>',
         caja(40, 60, 150, 80, '#cde7f0', 'Rectoría'), caja(200, 60, 160, 80, '#cde7f0', 'Coordinación'),
         caja(370, 60, 270, 80, '#e9d8fd', 'Sala de profesores'),
         caja(40, 160, 150, 170, '#ffe8a3', 'Cafetería'),
         f'<rect x="210" y="160" width="270" height="170" rx="6" fill="#b7e4c7" stroke="{k}" stroke-width="3"/>'
         + _txt(345, 250, 'Patio de recreo', 18),
         caja(500, 160, 140, 80, '#fde2e4', 'Salón 1.º'), caja(500, 250, 140, 80, '#fde2e4', 'Salón 2.º'),
         caja(40, 350, 150, 90, '#fde2e4', 'Biblioteca'), caja(210, 350, 270, 90, '#e2e8f0', 'Baños'),
         f'<path d="M520 460h100" stroke="#fff" stroke-width="10"/>' + _txt(570, 488, 'Entrada', 17),
         _norte(695, 70)]
    return _svg(725, 500, ''.join(p))


def mapa_barrio():
    """Mapa sencillo del barrio con calles, la flecha del norte y lugares: casa, escuela, tienda, iglesia, parque y puesto de salud."""
    k = CONTORNO
    p = [f'<rect x="0" y="0" width="700" height="480" fill="#eef6e9"/>',
         f'<path d="M0 230H700M330 0V480" stroke="#cbd5e1" stroke-width="44"/>',
         f'<path d="M0 230H700M330 0V480" stroke="#fff" stroke-width="3" stroke-dasharray="16 12"/>']

    def lugar(x, y, color, t, techo=True):
        r = (f'<path d="M{x - 10} {y + 32}L{x + 45} {y - 8}L{x + 100} {y + 32}z" fill="{ROJO}" stroke="{k}" stroke-width="3" stroke-linejoin="round"/>'
             if techo else '')
        return r + (f'<rect x="{x}" y="{y + 30}" width="90" height="62" rx="4" fill="{color}" stroke="{k}" stroke-width="3"/>'
                    + _txt(x + 45, y + 125, t, 18))
    p += [lugar(60, 40, '#f4e3c1', 'Mi casa'), lugar(470, 40, '#cde7f0', 'Escuela'), lugar(60, 300, '#ffe8a3', 'Tienda'),
          lugar(470, 300, '#e9d8fd', 'Iglesia'),
          f'<circle cx="230" cy="380" r="34" fill="{VERDE}" stroke="{k}" stroke-width="3"/><circle cx="270" cy="355" r="24" fill="{VERDE}" stroke="{k}" stroke-width="3"/>'
          + _txt(245, 445, 'Parque', 18),
          f'<rect x="200" y="70" width="80" height="62" rx="4" fill="#fff" stroke="{k}" stroke-width="3"/><path d="M240 84v34M223 101h34" stroke="{ROJO}" stroke-width="8"/>'
          + _txt(240, 160, 'Puesto de salud', 16),
          _norte(660, 30)]
    return _svg(700, 480, ''.join(p))


DIAS = ('lunes', 'martes', 'miércoles', 'jueves', 'viernes', 'sábado', 'domingo')
MESES = ('enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre')


def tira(nombres, vacios=(), por_fila=7):
    """Tira de días o meses en orden; los de «vacios» (índices desde 1) quedan en blanco para completar."""
    w, h, p = 120, 56, []
    colores = (ROJO, NARANJA, AMARILLO, VERDE, AZUL, '#9d4edd', '#ff70a6')
    for k, n in enumerate(nombres):
        f, c = divmod(k, por_fila)
        x, y = 15 + c * (w + 10), 15 + f * (h + 14)
        color = colores[k % len(colores)]
        p.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="10" fill="#fff" stroke="{color}" stroke-width="4"/>')
        if k + 1 not in vacios:
            p.append(_txt(x + w / 2, y + 36, n, 19))
    filas = -(-len(nombres) // por_fila)
    return _svg(15 + min(len(nombres), por_fila) * (w + 10) + 5, 15 + filas * (h + 14) + 1, ''.join(p))


# --- 2.º: más matemáticas -------------------------------------------------------------------------------------------
def billetes(*valores):
    """Billetes genéricos (no son réplicas) de 1000, 2000, 5000, 10 000…, uno al lado del otro."""
    color = {1000: '#fbd38d', 2000: '#90cdf4', 5000: '#c6f6d5', 10000: '#fed7e2', 20000: '#feebc8', 50000: '#e9d8fd'}
    p, x = [], 15
    for v in valores:
        p.append(f'<rect x="{x}" y="20" width="200" height="100" rx="10" fill="{color.get(v, "#e2e8f0")}" stroke="{CONTORNO}" stroke-width="3"/>'
                 f'<rect x="{x + 10}" y="30" width="180" height="80" rx="6" fill="none" stroke="{CONTORNO}" stroke-width="1.5" stroke-dasharray="4 3"/>'
                 f'<circle cx="{x + 45}" cy="70" r="24" fill="#fff" stroke="{CONTORNO}" stroke-width="2"/>'
                 + _txt(x + 130, 82, f'${v:,}'.replace(',', '.'), 26, CONTORNO))
        x += 215
    return _svg(x, 140, ''.join(p))


def cuadros(ancho, alto, malla=8):
    """Una figura de ancho × alto cuadritos pintada sobre una cuadrícula: su superficie se mide contando cuadritos."""
    c, o = 40, 20
    n = max(malla, ancho + 2)
    filas = max(alto + 2, 4)
    p = []
    for f in range(filas):
        for k in range(n):
            dentro = 1 <= k <= ancho and 1 <= f <= alto
            p.append(f'<rect x="{o + k * c}" y="{o + f * c}" width="{c}" height="{c}" fill="{AMARILLO if dentro else "#fff"}" '
                     f'stroke="{GRIS if not dentro else CONTORNO}" stroke-width="{2.5 if dentro else 1.5}"/>')
    return _svg(2 * o + n * c, 2 * o + filas * c, ''.join(p))


def poligonos():
    """Triángulo, cuadrado, pentágono y hexágono (A, B, C, D) para contar lados."""
    def reg(cx, cy, r, n, color, giro=-90):
        pts = ' '.join(f'{cx + r * math.cos(math.radians(giro + k * 360 / n))},{cy + r * math.sin(math.radians(giro + k * 360 / n))}' for k in range(n))
        return f'<polygon points="{pts}" fill="{color}" stroke="{CONTORNO}" stroke-width="4" stroke-linejoin="round"/>'
    p = [reg(85, 95, 62, 3, AMARILLO), reg(250, 95, 62, 4, AZUL, -45), reg(415, 95, 62, 5, VERDE), reg(580, 95, 62, 6, NARANJA, 0),
         _txt(85, 190, 'A', 24, ROJO), _txt(250, 190, 'B', 24, ROJO), _txt(415, 190, 'C', 24, ROJO), _txt(580, 190, 'D', 24, ROJO)]
    return _svg(665, 205, ''.join(p))


def lineas_posicion():
    """Línea horizontal (A), vertical (B), paralelas (C) y perpendiculares (D)."""
    k = AZUL_OSC
    p = [f'<path d="M30 100H170" stroke="{k}" stroke-width="6" stroke-linecap="round"/>',
         f'<path d="M260 30V170" stroke="{k}" stroke-width="6" stroke-linecap="round"/>',
         f'<path d="M340 60L480 110M340 110L480 160" stroke="{k}" stroke-width="6" stroke-linecap="round"/>',
         f'<path d="M560 160H700M630 160V30" stroke="{k}" stroke-width="6" stroke-linecap="round"/><path d="M630 140h20v20" fill="none" stroke="{ROJO}" stroke-width="3"/>',
         _txt(100, 205, 'A', 24, ROJO), _txt(260, 205, 'B', 24, ROJO), _txt(410, 205, 'C', 24, ROJO), _txt(630, 205, 'D', 24, ROJO)]
    return _svg(730, 220, ''.join(p))


def grafico_puntos(datos, titulo=''):
    """Gráfico de puntos: datos = [(nombre, cantidad)], una columna de puntos sobre cada nombre."""
    w, r, base = 120, 14, 330
    p = [f'<path d="M20 {base}H{40 + len(datos) * w}" stroke="{AZUL_OSC}" stroke-width="4"/>']
    for k, (nombre, n) in enumerate(datos):
        x = 40 + k * w + w / 2
        for j in range(n):
            p.append(f'<circle cx="{x}" cy="{base - 22 - j * (2 * r + 6)}" r="{r}" fill="{(ROJO, AZUL, VERDE, NARANJA, AMARILLO)[k % 5]}" stroke="{CONTORNO}" stroke-width="2.5"/>')
        p.append(_txt(x, base + 30, nombre, 19))
    if titulo:
        p.append(_txt(40 + len(datos) * w / 2, 28, titulo, 20))
    return _svg(60 + len(datos) * w, base + 50, ''.join(p))


# --- 2.º: señales y territorio ------------------------------------------------------------------------------------------
def senales():
    """Seis señales de uso común: PARE, paso peatonal, prohibido el paso, baño, reciclaje y salida de emergencia (A–F)."""
    k = CONTORNO
    oct_ = ' '.join(f'{90 + 62 * math.cos(math.radians(22.5 + i * 45))},{90 + 62 * math.sin(math.radians(22.5 + i * 45))}' for i in range(8))
    p = [f'<polygon points="{oct_}" fill="{ROJO}" stroke="#fff" stroke-width="5"/><polygon points="{oct_}" fill="none" stroke="{k}" stroke-width="2"/>'
         + _txt(90, 101, 'PARE', 30, '#fff'),
         # paso peatonal (azul cuadrado con persona y cebra)
         f'<rect x="200" y="28" width="124" height="124" rx="10" fill="{AZUL}" stroke="{k}" stroke-width="3"/>'
         f'<path d="M222 132h80" stroke="#fff" stroke-width="0"/>' + ''.join(f'<rect x="{214 + i * 20}" y="122" width="12" height="20" fill="#fff"/>' for i in range(5))
         + f'<circle cx="262" cy="56" r="10" fill="#fff"/><path d="M262 68v30M262 76l-14 14M262 76l14 12M262 98l-12 20M262 98l12 20" stroke="#fff" stroke-width="7" stroke-linecap="round"/>',
         # prohibido el paso
         f'<circle cx="420" cy="90" r="62" fill="#fff" stroke="{ROJO}" stroke-width="12"/><path d="M376 46L464 134" stroke="{ROJO}" stroke-width="12"/>'
         f'<circle cx="420" cy="64" r="9" fill="{k}"/><path d="M420 74v28M420 82l-12 12M420 82l12 10M420 102l-10 18M420 102l10 18" stroke="{k}" stroke-width="6" stroke-linecap="round"/>',
         # baño
         f'<rect x="525" y="28" width="124" height="124" rx="10" fill="#fff" stroke="{k}" stroke-width="3"/><path d="M587 40v100" stroke="{k}" stroke-width="2"/>'
         f'<circle cx="557" cy="60" r="9" fill="{AZUL}"/><rect x="547" y="72" width="20" height="38" rx="4" fill="{AZUL}"/><path d="M552 110v22M562 110v22" stroke="{AZUL}" stroke-width="6"/>'
         f'<circle cx="617" cy="60" r="9" fill="{ROJO}"/><path d="M617 70l-16 42h32z" fill="{ROJO}"/><path d="M611 112v20M623 112v20" stroke="{ROJO}" stroke-width="6"/>',
         # reciclaje
         f'<rect x="690" y="28" width="124" height="124" rx="10" fill="{VERDE}" stroke="{k}" stroke-width="3"/>'
         + ''.join(f'<path d="M752 90m{-30 * math.sin(math.radians(a))} {30 * math.cos(math.radians(a))}a30 30 0 0 1 {30 * math.sin(math.radians(a)) - 30 * math.sin(math.radians(a + 100))} '
                   f'{-30 * math.cos(math.radians(a)) + 30 * math.cos(math.radians(a + 100))}" fill="none" stroke="#fff" stroke-width="9" stroke-linecap="round"/>' for a in (0, 120, 240)),
         # salida de emergencia
         f'<rect x="855" y="28" width="124" height="124" rx="10" fill="#2f9e44" stroke="{k}" stroke-width="3"/>'
         f'<rect x="935" y="44" width="30" height="92" fill="#fff"/><circle cx="895" cy="58" r="9" fill="#fff"/>'
         f'<path d="M895 70l-6 28 18 16M889 98l-18 26M893 80l20 4M893 80l-18 10" stroke="#fff" stroke-width="7" stroke-linecap="round" fill="none"/>'
         f'<path d="M870 140h50l-12-10M920 140l-12 10" stroke="#fff" stroke-width="5" fill="none" stroke-linecap="round"/>']
    for i, x in enumerate((90, 262, 420, 587, 752, 917)):
        p.append(_txt(x, 190, 'ABCDEF'[i], 24, ROJO))
    return _svg(1000, 205, ''.join(p))


def arbol_genealogico():
    """Árbol genealógico vacío para llenar: abuelos, padres y yo."""
    k = CONTORNO
    caja = lambda x, y, t, color: (f'<rect x="{x}" y="{y}" width="150" height="74" rx="12" fill="{color}" stroke="{k}" stroke-width="3"/>'
                                   + _txt(x + 75, y + 96, t, 16))
    p = [f'<path d="M95 107V150H265V107M455 107V150H625V107M180 150V190H540V150M360 190V230" stroke="{k}" stroke-width="3" fill="none"/>',
         caja(20, 30, 'abuelo', '#fde2e4'), caja(190, 30, 'abuela', '#fde2e4'), caja(380, 30, 'abuelo', '#cde7f0'), caja(550, 30, 'abuela', '#cde7f0'),
         caja(105, 176, 'papá', '#fde2e4'), caja(465, 176, 'mamá', '#cde7f0'),
         f'<path d="M180 250v-24M540 250v-24" stroke="#fff" stroke-width="0"/>', caja(285, 300, 'yo', AMARILLO)]
    p.insert(0, f'<path d="M180 250V280H540V250M360 280V300" stroke="{k}" stroke-width="3" fill="none"/>')
    return _svg(720, 410, ''.join(p).replace('M180 150V190H540V150M360 190V230', ''))


def municipio():
    """Croquis de un municipio inventado: casco urbano con comunas, corregimiento, veredas, resguardo indígena y río; con el norte."""
    k = CONTORNO
    p = [f'<path d="M60 60L300 30L560 70L640 230L580 420L340 460L110 420L40 250z" fill="#eef6e9" stroke="{k}" stroke-width="5" stroke-linejoin="round"/>',
         f'<path d="M40 250C160 230 250 300 340 280S520 320 640 230" fill="none" stroke="{AZUL}" stroke-width="10" stroke-linecap="round"/>',
         _txt(160, 225, 'río', 16, AZUL_OSC),
         f'<circle cx="340" cy="190" r="62" fill="#fde2e4" stroke="{k}" stroke-width="3"/><path d="M340 128V252M278 190H402" stroke="{k}" stroke-width="2" stroke-dasharray="5 4"/>'
         + _txt(340, 182, 'Casco', 16) + _txt(340, 202, 'urbano', 16),
         f'<rect x="440" y="90" width="120" height="70" rx="10" fill="#ffe8a3" stroke="{k}" stroke-width="3"/>' + _txt(500, 132, 'Corregimiento', 14),
         f'<rect x="100" y="90" width="120" height="70" rx="10" fill="#c6f6d5" stroke="{k}" stroke-width="3"/>' + _txt(160, 132, 'Vereda El Alto', 14),
         f'<rect x="130" y="320" width="130" height="70" rx="10" fill="#c6f6d5" stroke="{k}" stroke-width="3"/>' + _txt(195, 362, 'Vereda La Vega', 14),
         f'<rect x="410" y="320" width="150" height="70" rx="10" fill="#e9d8fd" stroke="{k}" stroke-width="3"/>' + _txt(485, 352, 'Resguardo', 14) + _txt(485, 372, 'indígena', 14),
         _norte(640, 40)]
    return _svg(680, 480, ''.join(p))


# --- 3.º a 5.º: fracciones, multiplicación, ángulos, gráficos --------------------------------------------------------
def fraccion(num, den, forma='barra'):
    """Una fracción pintada: barra partida en «den» partes iguales (o círculo) con «num» partes coloreadas."""
    if forma == 'circulo':
        cx = cy = 110
        r, p = 95, []
        for k in range(den):
            a1, a2 = math.radians(-90 + k * 360 / den), math.radians(-90 + (k + 1) * 360 / den)
            x1, y1, x2, y2 = cx + r * math.cos(a1), cy + r * math.sin(a1), cx + r * math.cos(a2), cy + r * math.sin(a2)
            grande = 1 if 360 / den > 180 else 0
            p.append(f'<path d="M{cx} {cy}L{x1} {y1}A{r} {r} 0 {grande} 1 {x2} {y2}z" fill="{NARANJA if k < num else "#fff"}" stroke="{CONTORNO}" stroke-width="3"/>')
        if den == 1:
            p = [f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{NARANJA if num else "#fff"}" stroke="{CONTORNO}" stroke-width="3"/>']
        return _svg(220, 220, ''.join(p))
    ancho, alto, x0 = 480, 70, 20
    w = ancho / den
    p = [f'<rect x="{x0 + k * w}" y="20" width="{w}" height="{alto}" fill="{AZUL if k < num else "#fff"}" stroke="{CONTORNO}" stroke-width="3"/>'
         for k in range(den)]
    return _svg(ancho + 40, alto + 40, ''.join(p))


def recta_fracciones(den, marcas=()):
    """Recta del 0 al 1 (o al 2) partida en «den» partes; «marcas» = numeradores que se señalan con un punto rojo."""
    hasta = 2 if any(m > den for m in marcas) else 1
    L, x0, y = 560 * hasta / (hasta if hasta == 1 else 1.4), 30, 70
    paso = L / (den * hasta)
    p = [f'<path d="M{x0} {y}H{x0 + L}" stroke="{AZUL_OSC}" stroke-width="4"/>']
    for k in range(den * hasta + 1):
        x = x0 + k * paso
        entero = k % den == 0
        p.append(f'<path d="M{x} {y - (14 if entero else 9)}V{y + (14 if entero else 9)}" stroke="{AZUL_OSC}" stroke-width="{3 if entero else 2}"/>')
        if entero:
            p.append(_txt(x, y + 42, k // den, 22))
    for m in marcas:
        p.append(f'<circle cx="{x0 + m * paso}" cy="{y}" r="9" fill="{ROJO}" stroke="{CONTORNO}" stroke-width="2"/>')
    return _svg(x0 * 2 + L, 125, ''.join(p))


def arreglo(filas, cols):
    """Arreglo rectangular de puntos (filas × columnas) para la multiplicación."""
    c = 44
    p = [f'<circle cx="{30 + j * c}" cy="{30 + i * c}" r="14" fill="{(ROJO, AZUL, VERDE, NARANJA)[i % 4]}" stroke="{CONTORNO}" stroke-width="2.5"/>'
         for i in range(filas) for j in range(cols)]
    return _svg(cols * c + 16, filas * c + 16, ''.join(p))


def angulo(grados):
    """Un ángulo con su arco (sin el número: se mide o se clasifica)."""
    cx, cy, L = 60, 200, 210
    a = math.radians(grados)
    x2, y2 = cx + L * math.cos(a), cy - L * math.sin(a)
    r = 48
    arco_x, arco_y = cx + r * math.cos(a), cy - r * math.sin(a)
    grande = 1 if grados > 180 else 0
    p = [f'<path d="M{cx} {cy}H{cx + L}M{cx} {cy}L{x2} {y2}" stroke="{AZUL_OSC}" stroke-width="6" stroke-linecap="round"/>']
    if grados == 90:
        p.append(f'<path d="M{cx + 30} {cy}V{cy - 30}H{cx}" fill="none" stroke="{ROJO}" stroke-width="4"/>')
    else:
        p.append(f'<path d="M{cx + r} {cy}A{r} {r} 0 {grande} 0 {arco_x} {arco_y}" fill="none" stroke="{ROJO}" stroke-width="4"/>')
    ancho = cx + max(L, x2 - cx if x2 > cx else L) + 20
    izq = min(0, x2 - 20)
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{izq} 0 {ancho - izq} 230" width="{ancho - izq}" height="230"><rect x="{izq}" width="100%" height="100%" fill="#fff"/>{"".join(p)}</svg>'


def desarrollo_cubo():
    """Desarrollo plano del cubo (cruz de 6 cuadrados) con líneas de doblez."""
    c, p = 80, []
    for i, j in ((0, 1), (1, 0), (1, 1), (1, 2), (1, 3), (2, 1)):
        p.append(f'<rect x="{20 + j * c}" y="{20 + i * c}" width="{c}" height="{c}" fill="{(AZUL, VERDE, AMARILLO, NARANJA, ROJO, "#90e0ef")[i * 2 + j % 3]}" '
                 f'stroke="{CONTORNO}" stroke-width="3" stroke-dasharray="{"8 5" if (i, j) != (0, 1) else "0"}"/>')
    return _svg(40 + 4 * c, 40 + 3 * c, ''.join(p))


def circular(datos):
    """Gráfico circular: datos = [(nombre, cantidad)] con su leyenda."""
    total = sum(n for _, n in datos)
    cx, cy, r, a0, p = 140, 140, 115, -90, []
    colores = (ROJO, AZUL, VERDE, NARANJA, AMARILLO, '#9d4edd')
    for k, (nombre, n) in enumerate(datos):
        a1 = a0 + 360 * n / total
        x1, y1 = cx + r * math.cos(math.radians(a0)), cy + r * math.sin(math.radians(a0))
        x2, y2 = cx + r * math.cos(math.radians(a1)), cy + r * math.sin(math.radians(a1))
        p.append(f'<path d="M{cx} {cy}L{x1} {y1}A{r} {r} 0 {1 if a1 - a0 > 180 else 0} 1 {x2} {y2}z" fill="{colores[k % 6]}" stroke="#fff" stroke-width="3"/>')
        p.append(f'<rect x="290" y="{40 + k * 40}" width="26" height="26" rx="4" fill="{colores[k % 6]}"/>' + _txt(326, 60 + k * 40, f'{nombre} ({n})', 19, AZUL_OSC, 'start'))
        a0 = a1
    return _svg(520, 290, ''.join(p))


# --- 3.º a 5.º: ciencias ---------------------------------------------------------------------------------------------------
def sombra(distancia=1):
    """Linterna, objeto y pared: la sombra crece cuando la linterna se acerca al objeto (distancia 1 cerca, 2 media, 3 lejos)."""
    xl = {1: 190, 2: 120, 3: 50}[distancia]
    alto_sombra = {1: 220, 2: 150, 3: 110}[distancia]
    p = [f'<rect x="{xl - 40}" y="135" width="50" height="30" rx="6" fill="{GRIS}" stroke="{CONTORNO}" stroke-width="3"/>',
         f'<path d="M{xl + 10} 150L560 {150 - alto_sombra / 2}M{xl + 10} 150L560 {150 + alto_sombra / 2}" stroke="{AMARILLO}" stroke-width="2" stroke-dasharray="6 4"/>',
         f'<rect x="300" y="120" width="34" height="60" rx="4" fill="{VERDE}" stroke="{CONTORNO}" stroke-width="3"/>',
         f'<rect x="560" y="10" width="20" height="280" fill="#e2e8f0" stroke="{CONTORNO}" stroke-width="2"/>',
         f'<rect x="552" y="{150 - alto_sombra / 2}" width="8" height="{alto_sombra}" fill="#334155"/>',
         _txt(xl - 15, 195, 'linterna', 16), _txt(317, 210, 'objeto', 16), _txt(570, 312, 'pared', 16)]
    return _svg(620, 330, ''.join(p))


def fases_luna():
    """Las cuatro fases principales de la Luna vistas desde la Tierra: nueva, creciente, llena y menguante (A–D)."""
    p = []
    for k, (nombre, x) in enumerate((('nueva', 80), ('creciente', 230), ('llena', 380), ('menguante', 530))):
        p.append(f'<circle cx="{x}" cy="90" r="55" fill="#1e293b" stroke="{CONTORNO}" stroke-width="3"/>')
        if nombre == 'llena':
            p.append(f'<circle cx="{x}" cy="90" r="55" fill="#fef3c7" stroke="{CONTORNO}" stroke-width="3"/>')
        elif nombre == 'creciente':
            p.append(f'<path d="M{x} 35A55 55 0 0 1 {x} 145A25 55 0 0 0 {x} 35z" fill="#fef3c7"/>')
        elif nombre == 'menguante':
            p.append(f'<path d="M{x} 35A55 55 0 0 0 {x} 145A25 55 0 0 1 {x} 35z" fill="#fef3c7"/>')
        p.append(_txt(x, 180, 'ABCD'[k], 24, ROJO))
    return _svg(610, 200, ''.join(p))


def dia_noche():
    """El Sol ilumina la mitad de la Tierra: un lado es de día y el otro de noche; la Tierra gira sobre su eje."""
    p = [f'<circle cx="80" cy="150" r="60" fill="{AMARILLO}" stroke="{NARANJA}" stroke-width="5"/>' + _txt(80, 157, 'Sol', 20),
         ''.join(f'<path d="M150 {150 + d}H330" stroke="{AMARILLO}" stroke-width="3" stroke-dasharray="8 6"/>' for d in (-60, -30, 0, 30, 60)),
         f'<circle cx="430" cy="150" r="90" fill="#1e293b" stroke="{CONTORNO}" stroke-width="3"/>',
         f'<path d="M430 60A90 90 0 0 0 430 240z" fill="{AZUL}"/>',
         f'<path d="M405 70Q380 120 400 150T392 220" fill="none" stroke="{VERDE}" stroke-width="10" stroke-linecap="round"/>',
         f'<path d="M450 40L410 260" stroke="{ROJO}" stroke-width="3" stroke-dasharray="6 4"/>',
         _txt(370, 150, 'día', 20, '#fff'), _txt(480, 150, 'noche', 20, '#fff'),
         f'<path d="M370 40A70 20 0 0 1 500 50" fill="none" stroke="{AZUL_OSC}" stroke-width="3"/><path d="M500 50l-14-2 6-10" fill="none" stroke="{AZUL_OSC}" stroke-width="3"/>']
    return _svg(560, 290, ''.join(p))


def palanca():
    """Palanca: barra, punto de apoyo (triángulo), una piedra pesada y la fuerza que hace la persona."""
    p = [f'<path d="M40 170L520 110" stroke="#8d5524" stroke-width="16" stroke-linecap="round"/>',
         f'<path d="M190 210L230 150L270 210z" fill="{GRIS}" stroke="{CONTORNO}" stroke-width="3"/>' + _txt(230, 238, 'punto de apoyo', 16),
         f'<ellipse cx="80" cy="140" rx="45" ry="32" fill="#94a3b8" stroke="{CONTORNO}" stroke-width="3"/>' + _txt(80, 146, 'carga', 16, '#fff'),
         f'<path d="M500 30V95M488 82l12 14 12-14" stroke="{ROJO}" stroke-width="5" fill="none" stroke-linecap="round"/>' + _txt(500, 22, 'fuerza', 16, ROJO)]
    return _svg(560, 255, ''.join(p))


def circuito(cerrado=True):
    """Circuito sencillo: pila, cables, interruptor y bombillo (encendido si el circuito está cerrado)."""
    k = CONTORNO
    p = [f'<path d="M120 80H420V250H120Z" fill="none" stroke="{ROJO}" stroke-width="6"/>',
         f'<rect x="80" y="135" width="80" height="60" rx="8" fill="{AMARILLO}" stroke="{k}" stroke-width="3"/>' + _txt(120, 172, 'pila', 18),
         _txt(120, 128, '+', 22, ROJO) + _txt(120, 215, '−', 22, AZUL_OSC),
         f'<circle cx="420" cy="165" r="38" fill="{"#fff59d" if cerrado else "#f1f5f9"}" stroke="{k}" stroke-width="3"/>'
         f'<path d="M408 175q12-30 24 0" fill="none" stroke="{k}" stroke-width="3"/>' + _txt(480, 170, 'bombillo', 16, AZUL_OSC, 'start'),
         f'<rect x="230" y="70" width="90" height="20" fill="#fff"/>',
         f'<circle cx="235" cy="80" r="7" fill="{k}"/><circle cx="315" cy="80" r="7" fill="{k}"/>',
         f'<path d="M235 80L{315 if cerrado else 300} {80 if cerrado else 45}" stroke="{k}" stroke-width="6" stroke-linecap="round"/>' + _txt(275, 32, 'interruptor', 16)]
    if cerrado:
        p.append(''.join(f'<path d="M{420 + 52 * math.cos(math.radians(a))} {165 + 52 * math.sin(math.radians(a))}l{10 * math.cos(math.radians(a))} {10 * math.sin(math.radians(a))}" '
                         f'stroke="{NARANJA}" stroke-width="4" stroke-linecap="round"/>' for a in range(-150, 151, 50)))
    return _svg(600, 290, ''.join(p))


# --- 3.º a 5.º: sociales -------------------------------------------------------------------------------------------------
def ramas_poder():
    """Las tres ramas del poder público en Colombia con quién las ejerce."""
    k = CONTORNO
    caja = lambda x, color, t1, t2, t3: (f'<rect x="{x}" y="130" width="220" height="150" rx="14" fill="{color}" stroke="{k}" stroke-width="3"/>'
                                         + _txt(x + 110, 165, t1, 20) + _txt(x + 110, 205, t2, 16) + _txt(x + 110, 232, t3, 16))
    p = [f'<rect x="250" y="20" width="240" height="60" rx="14" fill="{AZUL_OSC}"/>' + _txt(370, 58, 'Poder público', 22, '#fff'),
         f'<path d="M370 80V105M130 105H610M130 105V130M370 105V130M610 105V130" stroke="{k}" stroke-width="3" fill="none"/>',
         caja(20, '#cde7f0', 'Legislativa', 'Congreso', 'hace las leyes'),
         caja(260, '#ffe8a3', 'Ejecutiva', 'Presidente', 'gobierna y ejecuta'),
         caja(500, '#e9d8fd', 'Judicial', 'Jueces y cortes', 'imparte justicia')]
    return _svg(740, 300, ''.join(p))


def linea_tiempo(hitos):
    """Línea de tiempo: hitos = [(año, texto)] ordenados."""
    n = len(hitos)
    ancho = max(700, n * 170)
    p = [f'<path d="M30 120H{ancho - 30}" stroke="{AZUL_OSC}" stroke-width="6" stroke-linecap="round"/>'
         f'<path d="M{ancho - 30} 120l-16-10v20z" fill="{AZUL_OSC}"/>']
    paso = (ancho - 120) / max(1, n - 1)
    for k, (anio, texto) in enumerate(hitos):
        x = 60 + k * paso
        arriba = k % 2 == 0
        p.append(f'<circle cx="{x}" cy="120" r="12" fill="{ROJO}" stroke="{CONTORNO}" stroke-width="3"/>' + _txt(x, 95 if arriba else 160, anio, 20, ROJO))
        for j, linea in enumerate(texto.split('|')):
            p.append(_txt(x, (40 if arriba else 190) + j * 20, linea, 15))
    return _svg(ancho, 240, ''.join(p))


# Los dibujos que usan las guías: id → función y datos. scripts/semilla_png.js los convierte a PNG.
def generar(id_):
    """«d-bloques-3-4» → SVG. Los números del id son los datos."""
    partes = id_.split('-')[1:]
    nombre, args = partes[0], partes[1:]

    def nums(xs):
        return [int(a) for a in xs]
    if nombre == 'bloques':
        return bloques(*nums(args))
    if nombre == 'paquetes':
        return paquetes(*nums(args))
    if nombre == 'marco':
        return marco10(*nums(args))
    if nombre == 'tabla100':
        return tabla100(set(nums(args)))
    if nombre == 'recta':                      # d-recta-0-20  ·  d-recta-0-20-s8a13  ·  d-recta-0-10-v4v7
        a, b = nums(args[:2])
        saltos = [tuple(int(z) for z in x[1:].split('a')) for x in args[2:] if x.startswith('s')]
        vacios = [int(x[1:]) for x in args[2:] if x.startswith('v')]
        return recta(a, b, saltos, vacios)
    if nombre == 'regla':
        return regla(*nums(args))
    if nombre == 'lapices':
        return lapices(*nums(args))
    if nombre == 'reloj':
        return reloj(*nums(args))
    if nombre == 'balanza':                    # d-balanza-3+2-5-0  (el último es la inclinación: i, 0, d)
        izq, der, inc = args
        return balanza(izq.replace('+', ' + ').replace('m', ' − '), der.replace('+', ' + ').replace('m', ' − '),
                       {'i': -1, 'd': 1}.get(inc, 0))
    if nombre == 'figuras':
        return figuras(bool(args and args[0] == 'n'))
    if nombre == 'solidos':
        return solidos(bool(args and args[0] == 'n'))
    if nombre == 'lineas':
        return lineas_abiertas()
    if nombre == 'plano':
        return plano_salon()
    if nombre == 'cuadricula':                 # d-cuadricula  ·  d-cuadricula-RRRUU (R→ L← U↑ D↓)
        camino = [{'R': '→', 'L': '←', 'U': '↑', 'D': '↓'}[ch] for ch in (args[0] if args else '')]
        return cuadricula(camino=camino)
    if nombre == 'conteo':                     # d-conteo-mango.7-banano.4
        return tabla_conteo([(a.split('.')[0].replace('_', ' ').capitalize(), int(a.split('.')[1])) for a in args])
    if nombre == 'monedas':
        return monedas(*nums(args))
    if nombre == 'rosa':
        return rosa_vientos(not (args and args[0] == 'sin'))
    if nombre == 'escuela':
        return plano_escuela()
    if nombre == 'barrio':
        return mapa_barrio()
    if nombre == 'billetes':
        return billetes(*nums(args))
    if nombre == 'cuadros':
        return cuadros(*nums(args))
    if nombre == 'poligonos':
        return poligonos()
    if nombre == 'posiciones':
        return lineas_posicion()
    if nombre == 'puntos':                     # d-puntos-lunes.3-martes.5
        return grafico_puntos([(a.split('.')[0].replace('_', ' '), int(a.split('.')[1])) for a in args])
    if nombre == 'senales':
        return senales()
    if nombre == 'arbol':
        return arbol_genealogico()
    if nombre == 'municipio':
        return municipio()
    if nombre == 'fraccion':                   # d-fraccion-3-4  ·  d-fraccion-3-4-circulo
        return fraccion(int(args[0]), int(args[1]), args[2] if len(args) > 2 else 'barra')
    if nombre == 'rectafr':                    # d-rectafr-4-m3-m6
        return recta_fracciones(int(args[0]), [int(x[1:]) for x in args[1:]])
    if nombre == 'arreglo':
        return arreglo(*nums(args))
    if nombre == 'angulo':
        return angulo(int(args[0]))
    if nombre == 'desarrollo':
        return desarrollo_cubo()
    if nombre == 'circular':                   # d-circular-futbol.8-baloncesto.4
        return circular([(a.split('.')[0].replace('_', ' '), int(a.split('.')[1])) for a in args])
    if nombre == 'sombra':
        return sombra(int(args[0]) if args else 1)
    if nombre == 'lunas':
        return fases_luna()
    if nombre == 'dianoche':
        return dia_noche()
    if nombre == 'palanca':
        return palanca()
    if nombre == 'circuito':
        return circuito(not (args and args[0] == 'abierto'))
    if nombre == 'ramas':
        return ramas_poder()
    if nombre == 'tiempo':                     # d-tiempo-1810.Grito_de|independencia-1819.Batalla_de|Boyacá
        return linea_tiempo([(a.split('.', 1)[0], a.split('.', 1)[1].replace('_', ' ')) for a in args])
    if nombre == 'dias':                       # d-dias  ·  d-dias-v3-v5 (miércoles y viernes en blanco)
        return tira(DIAS, [int(x[1:]) for x in args if x.startswith('v')])
    if nombre == 'meses':
        return tira(MESES, [int(x[1:]) for x in args if x.startswith('v')], por_fila=6)
    raise ValueError(f'dibujo desconocido: {id_}')
