"""PuntoExacto · la hoja calificada de cada estudiante, para devolvérsela.

Las fotos no se guardan en la plataforma, así que la hoja se reconstruye: se dibuja la misma hoja que se
imprimió (con su nombre y su código) y encima lo que el lector guardó que marcó, en verde lo bueno y en rojo lo
malo, la respuesta correcta punteada y la nota en una esquina. Cada estudiante sale en su propia página.
"""
import io

from reportlab.lib.colors import Color, HexColor
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas as rl_canvas

from . import formas as formas_mod
from . import hojas as hojas_mod
from .models import Hoja

VERDE, ROJO, GRIS, AZUL = HexColor('#0b8a4a'), HexColor('#c92a2a'), HexColor('#6b7280'), HexColor('#1b5fa8')


def _color_nota(examen, nota):
    try:
        lo, hi = float(examen.nota_minima), float(examen.nota_maxima)
        f = (float(nota) - lo) / ((hi - lo) or 1)
    except (TypeError, ValueError):
        return GRIS
    return HexColor('#0b6b4a') if f >= 0.8 else AZUL if f >= 0.5 else HexColor('#b45309') if f >= 0.35 else ROJO


def _encima(examen, hoja, info, preguntas, ancho_pt, alto_pt):
    """Una página transparente con las marcas de la calificación de esta hoja."""
    buf = io.BytesIO()
    c = rl_canvas.Canvas(buf, pagesize=(ancho_pt, alto_pt))
    mapa, r = info['mapa'], info['radio_mm'] * mm
    orden = formas_mod.orden_de(examen, hoja.forma, preguntas)
    lectura = formas_mod.lectura_de(hoja, preguntas, orden)          # {posición en la hoja: letra marcada}
    por_numero = {p.numero: p for p in preguntas}
    buenas = malas = blancas = 0
    for pos in range(1, examen.numero_preguntas + 1):
        numero, _ = formas_mod.a_forma_a(orden, pos, '')
        p = por_numero.get(numero)
        if p is None:
            continue
        marcada = (lectura.get(str(pos)) or '').strip()
        letras = [l for l in hojas_mod.LETRAS[:p.opciones_efectivas()] if f'{pos}{l}' in mapa]
        # La letra de la hoja que, traducida a la forma A, es la correcta.
        correcta_hoja = next((l for l in letras if formas_mod.a_forma_a(orden, pos, l)[1] == p.correcta), None)
        if p.anulada or p.es_control:
            x, y = mapa[f'{pos}{letras[0]}'] if letras else (None, None)
            if x is not None:
                c.setFillColor(GRIS); c.setFont('Helvetica', 6.5)
                c.drawRightString(x * mm - r * 1.6, y * mm - 2.2, 'anulada' if p.anulada else 'control')
            continue
        if not marcada:
            blancas += 1
        elif marcada == Hoja.MARCA_DOBLE:
            malas += 1
        else:
            fr = p.fraccion(formas_mod.a_forma_a(orden, pos, marcada)[1])
            if fr >= 1:
                buenas += 1
            else:
                malas += 1
        for l in letras:
            x, y = (v * mm for v in mapa[f'{pos}{l}'])
            if marcada == l:
                ok = formas_mod.a_forma_a(orden, pos, l)[1] == p.correcta
                c.setFillColor(Color(0.15, 0.15, 0.18)); c.circle(x, y, r * 0.78, stroke=0, fill=1)
                c.setStrokeColor(VERDE if ok else ROJO); c.setLineWidth(1.8); c.setDash()
                c.circle(x, y, r * 1.28, stroke=1, fill=0)
            elif l == correcta_hoja:
                c.setStrokeColor(VERDE); c.setLineWidth(1.4); c.setDash(2, 1.6)
                c.circle(x, y, r * 1.28, stroke=1, fill=0)
                c.setDash()
        if marcada == Hoja.MARCA_DOBLE and letras:
            x, y = mapa[f'{pos}{letras[-1]}']
            c.setFillColor(ROJO); c.setFont('Helvetica-Bold', 7)
            c.drawString(x * mm + r * 1.7, y * mm - 2.4, 'doble')
    # Sello con la nota
    color = _color_nota(examen, hoja.nota)
    w, h = 62 * mm, 17 * mm
    x0, y0 = ancho_pt - w - 22 * mm, alto_pt - 76 * mm          # debajo del recuadro del nombre, donde no hay nada
    c.setFillColor(Color(1, 1, 1, alpha=0.93)); c.setStrokeColor(color); c.setLineWidth(1.6)
    c.roundRect(x0, y0, w, h, 3 * mm, stroke=1, fill=1)
    c.setFillColor(color); c.setFont('Helvetica-Bold', 22)
    c.drawString(x0 + 4 * mm, y0 + 5 * mm, str(hoja.nota if hoja.nota is not None else '—'))
    c.setFillColor(HexColor('#111827')); c.setFont('Helvetica', 8.5)
    c.drawString(x0 + 27 * mm, y0 + 10 * mm, f'{buenas} bien · {malas} mal')
    c.drawString(x0 + 27 * mm, y0 + 5 * mm, f'{blancas} en blanco')
    # Leyenda al pie
    c.setFont('Helvetica', 6.8); c.setFillColor(GRIS)
    c.drawCentredString(ancho_pt / 2, 6 * mm,
                        'Verde: bien · Rojo: mal · Punteada: la respuesta correcta. Hoja reconstruida con lo que leyó PuntoExacto. '
                        'Informe desarrollado por medio de la plataforma mcolegio · mcolegio.com.co')
    c.showPage(); c.save()
    return buf.getvalue()


def pdf_calificadas(examen, hojas):
    """Bytes de un PDF con la hoja calificada de cada estudiante (una por página, tamaño carta)."""
    from pypdf import PdfReader, PdfWriter

    hojas = [h for h in hojas if h.estado in ('calificada', 'revisar')]
    if not hojas:
        return None
    base = PdfReader(io.BytesIO(hojas_mod.generar_pdf(examen, hojas, por_pagina=1)))
    info = hojas_mod.mapa_de_examen(examen, 1)
    preguntas = list(examen.preguntas.order_by('numero'))
    salida = PdfWriter()
    for pagina, hoja in zip(base.pages, hojas):
        ancho, alto = float(pagina.mediabox.width), float(pagina.mediabox.height)
        capa = PdfReader(io.BytesIO(_encima(examen, hoja, info, preguntas, ancho, alto))).pages[0]
        pagina.merge_page(capa)
        salida.add_page(pagina)
    buf = io.BytesIO()
    salida.write(buf)
    return buf.getvalue()
