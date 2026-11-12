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
    if nombre == 'dias':                       # d-dias  ·  d-dias-v3-v5 (miércoles y viernes en blanco)
        return tira(DIAS, [int(x[1:]) for x in args if x.startswith('v')])
    if nombre == 'meses':
        return tira(MESES, [int(x[1:]) for x in args if x.startswith('v')], por_fila=6)
    raise ValueError(f'dibujo desconocido: {id_}')
