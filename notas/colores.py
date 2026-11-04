"""Colores que se leen bien sobre el color que escogió el colegio.

Contraste según WCAG 2.1: 4.5:1 para texto, 3:1 para íconos grandes. Para la
campana y los mensajes de la barra superior se pide 4.5, para que se vean bien
incluso de lejos o con el brillo bajo.
"""
import colorsys
import re

MINIMO = 4.5
AMARILLO = '#FFD43B'
OSCURO = '#1F2937'


def a_rgb(color):
    c = (color or '').strip().lstrip('#')
    if len(c) == 3:
        c = ''.join(ch * 2 for ch in c)
    if not re.fullmatch(r'[0-9A-Fa-f]{6}', c):
        return None
    return tuple(int(c[i:i + 2], 16) / 255 for i in (0, 2, 4))


def a_hex(rgb):
    return '#' + ''.join(f'{round(max(0, min(1, v)) * 255):02X}' for v in rgb)


def luminancia(rgb):
    def canal(v):
        return v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4
    r, g, b = (canal(v) for v in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contraste(a, b):
    la, lb = luminancia(a), luminancia(b)
    claro, oscuro = max(la, lb), min(la, lb)
    return (claro + 0.05) / (oscuro + 0.05)


def contrario(fondo, minimo=MINIMO):
    """El color «contrario» al fondo, con contraste suficiente.

    * Fondo con color: el tono opuesto del círculo cromático, claro si el fondo es
      oscuro y oscuro si es claro (azul → naranja, vino → verde agua…).
    * Fondo gris, negro o blanco (sin tono): amarillo sobre oscuro, gris muy oscuro sobre claro.
    * Si aun así no contrasta lo suficiente, blanco o negro.
    """
    rgb = a_rgb(fondo)
    if rgb is None:
        return AMARILLO
    oscuro = luminancia(rgb) < 0.18
    h, l, s = colorsys.rgb_to_hls(*rgb)
    if s < 0.15:
        candidato = a_rgb(AMARILLO if oscuro else OSCURO)
    else:
        h2 = (h + 0.5) % 1.0
        s2 = max(s, 0.75)
        candidato = None
        pasos = [0.72, 0.78, 0.84, 0.9] if oscuro else [0.32, 0.26, 0.2, 0.14]
        for l2 in pasos:
            prueba = colorsys.hls_to_rgb(h2, l2, s2)
            if contraste(prueba, rgb) >= minimo:
                candidato = prueba
                break
    if candidato is None or contraste(candidato, rgb) < minimo:
        blanco, negro = (1, 1, 1), (0, 0, 0)
        candidato = blanco if contraste(blanco, rgb) >= contraste(negro, rgb) else negro
    return a_hex(candidato)


def iconos_topbar(colegio):
    """El color de la campana y los mensajes de la barra superior."""
    if colegio is None:
        return AMARILLO
    fondo = getattr(colegio, 'color_topbar', '') or '#343A40'
    if not getattr(colegio, 'iconos_topbar_auto', True) and a_rgb(getattr(colegio, 'color_iconos_topbar', '')):
        return a_hex(a_rgb(colegio.color_iconos_topbar))
    return contrario(fondo)
