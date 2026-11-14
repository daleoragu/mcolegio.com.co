"""Imprimir guías ahorrando papel: varias guías por hoja (como las hojas de respuestas de PuntoExacto) y folleto.

* ``copias(pdf, 2)``: cada hoja lleva 2 copias de la misma página (hoja horizontal, cada copia a media carta).
  Con 4, cuatro copias en cuadrícula. Si la guía tiene varias páginas, la hoja 1 lleva la página 1 repetida, la
  hoja 2 la página 2, etc.: se imprime por las dos caras, se corta por la línea punteada y salen guías completas.
* ``folleto(pdf)``: las páginas se reordenan para doblar la hoja por la mitad como una cartilla (8, 1 | 2, 7 …).
  Se imprime a doble cara volteando por el borde corto, se dobla y se grapa en el centro.

Se trabaja sobre el PDF ya armado, así que todo (fórmulas, imágenes, encabezado) sale igual, solo más pequeño.
"""
import io

from pypdf import PageObject, PdfReader, PdfWriter, Transformation

MARGEN = 10          # puntos alrededor de cada copia (≈ 3,5 mm)


def _lineas_corte(ancho, alto, verticales=(), horizontales=()):
    """Una página transparente con líneas punteadas de corte (o de doblez)."""
    from reportlab.lib.colors import Color
    from reportlab.pdfgen import canvas
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=(ancho, alto))
    c.setStrokeColor(Color(0.55, 0.55, 0.55))
    c.setLineWidth(0.6)
    c.setDash(4, 4)
    for x in verticales:
        c.line(x, 6, x, alto - 6)
    for y in horizontales:
        c.line(6, y, ancho - 6, y)
    c.showPage()
    c.save()
    return PdfReader(io.BytesIO(buf.getvalue())).pages[0]


def _poner(hoja, pagina, x, y, ancho_caja, alto_caja):
    """Pone la página escalada y centrada dentro de la caja (x, y, ancho, alto) de la hoja."""
    w, h = float(pagina.mediabox.width), float(pagina.mediabox.height)
    escala = min((ancho_caja - 2 * MARGEN) / w, (alto_caja - 2 * MARGEN) / h)
    dx = x + (ancho_caja - w * escala) / 2
    dy = y + (alto_caja - h * escala) / 2
    hoja.merge_transformed_page(pagina, Transformation().scale(escala, escala).translate(dx, dy))


def _medidas(lector):
    p = lector.pages[0]
    return float(p.mediabox.width), float(p.mediabox.height)


def _salida(escritor):
    buf = io.BytesIO()
    escritor.write(buf)
    return buf.getvalue()


def copias(pdf, n):
    """n = 2 o 4 copias de cada página por hoja."""
    lector = PdfReader(io.BytesIO(pdf))
    if n not in (2, 4) or not lector.pages:
        return pdf
    W, H = _medidas(lector)                    # carta vertical: 612 × 792
    escritor = PdfWriter()
    for pagina in lector.pages:
        if n == 2:                             # hoja horizontal, dos mitades
            hoja = PageObject.create_blank_page(width=H, height=W)
            for k in range(2):
                _poner(hoja, pagina, k * H / 2, 0, H / 2, W)
            hoja.merge_page(_lineas_corte(H, W, verticales=[H / 2]))
        else:                                  # hoja vertical, cuatro cuartos
            hoja = PageObject.create_blank_page(width=W, height=H)
            for fila in range(2):
                for col in range(2):
                    _poner(hoja, pagina, col * W / 2, fila * H / 2, W / 2, H / 2)
            hoja.merge_page(_lineas_corte(W, H, verticales=[W / 2], horizontales=[H / 2]))
        escritor.add_page(hoja)
    return _salida(escritor)


def orden_folleto(n_paginas):
    """El orden de las páginas en las caras de las hojas de un folleto (None = página en blanco).
    Con 8 páginas: [(8, 1), (2, 7), (6, 3), (4, 5)] (izquierda, derecha de cada cara)."""
    total = -(-n_paginas // 4) * 4 or 4
    numero = lambda k: k if k <= n_paginas else None
    caras = []
    for i in range(total // 2):
        izq, der = (total - i, i + 1) if i % 2 == 0 else (i + 1, total - i)
        caras.append((numero(izq), numero(der)))
    return caras


def folleto(pdf):
    """Folleto: dos páginas por cara en hoja horizontal, en el orden para doblar y grapar."""
    lector = PdfReader(io.BytesIO(pdf))
    if not lector.pages:
        return pdf
    W, H = _medidas(lector)
    escritor = PdfWriter()
    doblez = _lineas_corte(H, W, verticales=[H / 2])
    for izq, der in orden_folleto(len(lector.pages)):
        hoja = PageObject.create_blank_page(width=H, height=W)
        for k, num in enumerate((izq, der)):
            if num is not None:
                _poner(hoja, lector.pages[num - 1], k * H / 2, 0, H / 2, W)
        hoja.merge_page(doblez)
        escritor.add_page(hoja)
    return _salida(escritor)


def aplicar(pdf, impresion):
    """impresion: '', '2', '4' o 'folleto'."""
    if impresion in ('2', '4'):
        return copias(pdf, int(impresion))
    if impresion == 'folleto':
        return folleto(pdf)
    return pdf


def contar(pdf):
    """Cuántas páginas tiene un PDF."""
    try:
        return len(PdfReader(io.BytesIO(pdf)).pages)
    except Exception:
        return 0
