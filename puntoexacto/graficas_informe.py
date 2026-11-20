"""Gráficas en SVG para los informes en PDF (las dibuja WeasyPrint): sobrias, en grises y un azul de acento."""
from django.utils.html import escape
from django.utils.safestring import mark_safe

AZUL, GRIS, GRIS_T, TXT, TXT2 = '#1f4e9c', '#cbd5e1', '#94a3b8', '#0f172a', '#475569'


def _mezcla(c, frac):
    """El color c aclarado hacia el blanco (frac 0 = c, 1 = blanco)."""
    c = c.lstrip('#')
    try:
        r, g, b = (int(c[i:i + 2], 16) for i in (0, 2, 4))
    except ValueError:
        return GRIS
    return '#%02x%02x%02x' % tuple(round(x + (255 - x) * frac) for x in (r, g, b))


def _tonos(color):
    """Cinco tonos del color de la plataforma, del más claro (nivel 1) al más fuerte."""
    return [_mezcla(color, f) for f in (.78, .6, .4, .15)] + [_mezcla(color, 0)]


def _svg(w, h, cuerpo):
    return mark_safe(f'<svg viewBox="0 0 {w} {h}" width="100%" xmlns="http://www.w3.org/2000/svg" '
                     f'font-family="Helvetica, Arial" font-size="11">{cuerpo}</svg>')


def barras_areas(areas, valores_alumno=None, color=AZUL):
    """Una barra por área (0–100). Con valores_alumno: barra del estudiante (azul) y marca del promedio del grupo."""
    W, izq, ancho, fila = 700, 170, 430, 30
    H = 20 + fila * len(areas) + 26
    s = []
    for i, a in enumerate(areas):
        y = 14 + i * fila
        s.append(f'<text x="{izq - 8}" y="{y + 14}" text-anchor="end" fill="{TXT}">{escape(a["nombre"][:28])}</text>')
        s.append(f'<rect x="{izq}" y="{y}" width="{ancho}" height="18" rx="3" fill="{GRIS}" fill-opacity=".35"/>')
        if valores_alumno is None:
            v = a['promedio']
            s.append(f'<rect x="{izq}" y="{y}" width="{ancho * v / 100:.1f}" height="18" rx="3" fill="{color}"/>')
            d = a.get('desviacion') or 0
            x1, x2 = izq + ancho * max(0, v - d) / 100, izq + ancho * min(100, v + d) / 100
            s.append(f'<line x1="{x1:.1f}" x2="{x2:.1f}" y1="{y + 9}" y2="{y + 9}" stroke="{TXT}" stroke-width="1.2"/>')
            s.append(f'<text x="{izq + ancho + 8}" y="{y + 14}" fill="{TXT2}">{v:.0f} ± {d:.0f}</text>')
        else:
            v, gp = valores_alumno[i], a['grupo']
            s.append(f'<rect x="{izq}" y="{y}" width="{ancho * v / 100:.1f}" height="18" rx="3" fill="{color}"/>')
            xg = izq + ancho * gp / 100
            s.append(f'<line x1="{xg:.1f}" x2="{xg:.1f}" y1="{y - 3}" y2="{y + 21}" stroke="{TXT}" stroke-width="2.5"/>')
            s.append(f'<text x="{izq + ancho + 8}" y="{y + 14}" fill="{TXT2}">{v} · grupo {gp:.0f}</text>')
    yl = H - 8
    if valores_alumno is None:
        s.append(f'<text x="{izq}" y="{yl}" fill="{TXT2}">Barra: promedio del área (0–100) · línea: ± una desviación estándar</text>')
    else:
        s.append(f'<rect x="{izq}" y="{yl - 9}" width="12" height="10" fill="{color}"/><text x="{izq + 16}" y="{yl}" fill="{TXT2}">Su puntaje</text>'
                 f'<line x1="{izq + 100}" x2="{izq + 100}" y1="{yl - 11}" y2="{yl + 1}" stroke="{TXT}" stroke-width="2.5"/>'
                 f'<text x="{izq + 106}" y="{yl}" fill="{TXT2}">Promedio del grupo</text>')
    return _svg(W, H, ''.join(s))


def niveles_areas(areas, color=AZUL):
    """Barra apilada por área: qué porcentaje de estudiantes quedó en cada nivel de desempeño."""
    W, izq, ancho, fila = 700, 170, 470, 30
    H = 20 + fila * len(areas) + 30
    s = []
    for i, a in enumerate(areas):
        y = 14 + i * fila
        s.append(f'<text x="{izq - 8}" y="{y + 14}" text-anchor="end" fill="{TXT}">{escape(a["nombre"][:28])}</text>')
        x = izq
        tonos = _tonos(color) if len(a['niveles']) == 5 else _tonos(color)[:4]
        for k, nv in enumerate(a['niveles']):
            w = ancho * nv['pct'] / 100
            if w <= 0:
                continue
            s.append(f'<rect x="{x:.1f}" y="{y}" width="{w:.1f}" height="18" fill="{tonos[k]}"/>')
            if w > 26:
                s.append(f'<text x="{x + w / 2:.1f}" y="{y + 13}" text-anchor="middle" fill="{"#fff" if k >= 2 else TXT}" font-size="10">{nv["pct"]} %</text>')
            x += w
    yl = H - 8
    for k, nombre in enumerate(['Nivel 1', 'Nivel 2', 'Nivel 3', 'Nivel 4']):
        s.append(f'<rect x="{izq + k * 95}" y="{yl - 9}" width="12" height="10" fill="{_tonos(color)[k]}"/><text x="{izq + k * 95 + 16}" y="{yl}" fill="{TXT2}">{nombre}</text>')
    if any(len(a['niveles']) == 5 for a in areas):
        s.append(f'<text x="{izq + 4 * 95}" y="{yl}" fill="{TXT2}">Inglés: A-, A1, A2, B1, B+</text>')
    return _svg(W, H, ''.join(s))


def histograma(globales, paso=50, color=AZUL):
    """Cuántos estudiantes quedaron en cada rango del puntaje global (0–500)."""
    rangos = list(range(0, 500, paso))
    cuentas = [sum(1 for g in globales if r <= g < r + paso or (r + paso == 500 and g == 500)) for r in rangos]
    W, H, izq, base = 700, 210, 40, 165
    tope = max(cuentas) or 1
    banda = (W - izq - 10) / len(rangos)
    s = []
    for i, (r, n) in enumerate(zip(rangos, cuentas)):
        h = n / tope * 130
        x = izq + i * banda + banda * .12
        s.append(f'<rect x="{x:.1f}" y="{base - h:.1f}" width="{banda * .76:.1f}" height="{h:.1f}" rx="2" fill="{color if n == max(cuentas) else GRIS_T}"/>')
        if n:
            s.append(f'<text x="{x + banda * .38:.1f}" y="{base - h - 4:.1f}" text-anchor="middle" fill="{TXT}" font-weight="bold">{n}</text>')
        s.append(f'<text x="{x + banda * .38:.1f}" y="{base + 14}" text-anchor="middle" fill="{TXT2}" font-size="9.5">{r}–{r + paso - 1 if r + paso < 500 else 500}</text>')
    s.append(f'<line x1="{izq}" x2="{W - 10}" y1="{base}" y2="{base}" stroke="{GRIS_T}"/>')
    s.append(f'<text x="{izq}" y="{base + 34}" fill="{TXT2}">Estudiantes por rango de puntaje global (0 a 500)</text>')
    return _svg(W, H, ''.join(s))


def barra_percentil(p, color=AZUL):
    """Barra de 0 a 100 en cinco tramos, llena hasta el percentil (como la de los reportes de Saber 11)."""
    W, x0, ancho, y = 320, 4, 310, 4
    tramo, sep = ancho / 5, 3
    s = []
    for i in range(5):
        xi = x0 + i * tramo
        w = tramo - sep
        s.append(f'<rect x="{xi:.1f}" y="{y}" width="{w:.1f}" height="9" fill="#e2e8f0"/>')
        lleno = max(0.0, min(w, (p - i * 20) / 20 * tramo))
        if lleno > 0:
            s.append(f'<rect x="{xi:.1f}" y="{y}" width="{min(lleno, w):.1f}" height="9" fill="{color}"/>')
    for i in range(6):
        anc = 'end' if i == 5 else 'start'
        s.append(f'<text x="{x0 + i * tramo - (sep if i == 5 else 0):.1f}" y="{y + 24}" text-anchor="{anc}" fill="{GRIS_T}" font-size="10">{i * 20}</text>')
    return _svg(W, 32, ''.join(s))


def escalera(nombres, escalon, color=AZUL):
    """Escalera de niveles de desempeño: los peldaños alcanzados en el color de la plataforma y una flecha en el suyo."""
    n = len(nombres)
    col_w, alto, x0, base = 46, 8, 4, 32 + 8 * n
    s = []
    for i, nom in enumerate(nombres):
        x = x0 + i * (col_w + 2)
        for k in range(i + 1):
            yk = base - (k + 1) * (alto + 1.5)
            s.append(f'<rect x="{x}" y="{yk:.1f}" width="{col_w}" height="{alto}" fill="{color if i <= escalon else "#cbd5e1"}"/>')
        ytop = base - (i + 1) * (alto + 1.5)
        corto = escape(nom.replace('Nivel ', ''))
        s.append(f'<text x="{x + col_w / 2}" y="{ytop - 3:.1f}" text-anchor="middle" font-size="10" font-weight="bold" fill="{TXT}">{corto}</text>')
        if i == escalon:
            s.append(f'<path d="M{x + col_w / 2 - 4},{ytop - 21:.1f} h8 l-4,5 z" fill="{TXT}"/>')
    return _svg(x0 + n * (col_w + 2), base + 2, ''.join(s))
