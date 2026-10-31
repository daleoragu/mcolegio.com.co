"""Cómo se califica cada tipo de pregunta de una ficha y cómo se mezcla lo que hay que mezclar.

Las respuestas del estudiante se guardan por id de bloque:
  unica: 2 · varias: [0, 2] · vf: true · completar: ["Bogotá", "Magdalena"] · numerica: "3,5"
  corta: "fotosíntesis" · abierta: "texto…" · emparejar: {"0": 2, "1": 0} (izquierda -> derecha original)
  ordenar: [2, 0, 1] (índices originales en el orden que dejó el estudiante)
  clasificar: {"0": 1, "1": 0} (índice del elemento en la lista plana -> grupo)
"""
import random
import unicodedata
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from . import bloques as B

CERO = Decimal('0')


def normal(texto, estricto=False):
    t = ' '.join(str(texto or '').split())
    if estricto:
        return t
    t = unicodedata.normalize('NFD', t.lower())
    return ''.join(c for c in t if unicodedata.category(c) != 'Mn').strip(' .')


def numero(texto):
    t = str(texto or '').strip().replace(' ', '')
    if t.count(',') == 1 and '.' not in t:
        t = t.replace(',', '.')
    try:
        return Decimal(t)
    except InvalidOperation:
        return None


def mezclar(lista, semilla):
    """Mezcla siempre igual para la misma semilla (el estudiante ve lo mismo si vuelve a entrar)."""
    orden = list(range(len(lista)))
    random.Random(str(semilla)).shuffle(orden)
    return orden


def elementos_clasificar(b):
    return [(e, gi) for gi, g in enumerate(b.get('grupos') or []) for e in g['elementos']]


def preguntas(contenido):
    return [b for b in contenido.get('bloques', []) if b.get('tipo') == 'pregunta']


def calificar_una(b, r):
    """(obtenidos, posibles, necesita_revision) de una pregunta."""
    puntos = Decimal(b.get('puntos') or 1)
    modo = b.get('modo')
    frac = CERO
    revisar = False
    try:
        if modo == 'unica':
            frac = Decimal(1) if r is not None and int(r) == b.get('correcta') else CERO
        elif modo == 'varias':
            correctas = set(b.get('correctas') or [])
            marcadas = {int(x) for x in (r or [])}
            if correctas:
                bien = len(marcadas & correctas)
                mal = len(marcadas - correctas)
                frac = max(CERO, Decimal(bien - mal) / Decimal(len(correctas)))
        elif modo == 'vf':
            frac = Decimal(1) if r is not None and bool(r) == bool(b.get('valor')) and r != '' else CERO
        elif modo == 'completar':
            _, respuestas = B.huecos(b.get('texto'))
            dadas = list(r or [])
            estricto = bool(b.get('mayusculas'))
            if respuestas:
                bien = sum(1 for i, acept in enumerate(respuestas)
                           if i < len(dadas) and normal(dadas[i], estricto) in {normal(a, estricto) for a in acept})
                frac = Decimal(bien) / Decimal(len(respuestas))
        elif modo == 'numerica':
            esperado, dado = numero(b.get('respuesta')), numero(r)
            tol = numero(b.get('tolerancia')) or CERO
            frac = Decimal(1) if esperado is not None and dado is not None and abs(dado - esperado) <= abs(tol) else CERO
        elif modo == 'corta':
            if normal(r) and normal(r) in {normal(a) for a in b.get('aceptadas') or []}:
                frac = Decimal(1)
            elif normal(r):
                revisar = True
        elif modo == 'abierta':
            revisar = bool(str(r or '').strip())
        elif modo == 'emparejar':
            pares = b.get('pares') or []
            dadas = r or {}
            if pares:
                bien = sum(1 for i in range(len(pares)) if str(dadas.get(str(i), '')) == str(i))
                frac = Decimal(bien) / Decimal(len(pares))
        elif modo == 'ordenar':
            n = len(b.get('elementos') or [])
            dadas = [int(x) for x in (r or [])]
            if n:
                bien = sum(1 for pos, original in enumerate(dadas[:n]) if pos == original)
                frac = Decimal(bien) / Decimal(n)
        elif modo == 'clasificar':
            elementos = elementos_clasificar(b)
            dadas = r or {}
            if elementos:
                bien = sum(1 for i, (_, g) in enumerate(elementos) if str(dadas.get(str(i), '')) == str(g))
                frac = Decimal(bien) / Decimal(len(elementos))
    except (TypeError, ValueError, AttributeError):
        frac = CERO
    return (puntos * frac).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP), puntos, revisar


def calificar(contenido, respuestas, manuales=None):
    """Califica toda la ficha. manuales = {id_bloque: puntos} que puso el docente (mandan sobre lo automático).

    Devuelve {'obtenidos', 'posibles', 'pendientes': [ids sin revisar], 'detalle': {id: {...}}}.
    """
    respuestas = respuestas or {}
    manuales = manuales or {}
    obtenidos, posibles, pendientes, detalle = CERO, CERO, [], {}
    for b in preguntas(contenido):
        if b.get('control'):
            continue
        o, p, revisar = calificar_una(b, respuestas.get(b['id']))
        if b['id'] in manuales:
            try:
                o = max(CERO, min(p, Decimal(str(manuales[b['id']]))))
                revisar = False
            except (InvalidOperation, ValueError):
                pass
        elif revisar:
            pendientes.append(b['id'])
        obtenidos += o
        posibles += p
        detalle[b['id']] = {'obtenidos': o, 'posibles': p, 'revisar': revisar and b['id'] not in manuales,
                            'automatica': b.get('modo') in B.AUTOMATICAS}
    return {'obtenidos': obtenidos, 'posibles': posibles, 'pendientes': pendientes, 'detalle': detalle}


def a_la_escala(obtenidos, posibles, minima, maxima):
    if not posibles:
        return None
    nota = minima + (maxima - minima) * (Decimal(obtenidos) / Decimal(posibles))
    return nota.quantize(Decimal('0.1'), rounding=ROUND_HALF_UP)


def leer_respuestas(contenido, post):
    """Lee las respuestas del formulario de la ficha (nombres r-<id>, r-<id>-<k>)."""
    salida = {}
    for b in preguntas(contenido):
        bid, modo = b['id'], b.get('modo')
        clave = f'r-{bid}'
        if modo == 'unica':
            v = post.get(clave)
            salida[bid] = int(v) if v not in (None, '') and str(v).isdigit() else None
        elif modo == 'varias':
            salida[bid] = sorted({int(v) for v in post.getlist(clave) if str(v).isdigit()})
        elif modo == 'vf':
            v = post.get(clave)
            salida[bid] = None if v not in ('v', 'f') else v == 'v'
        elif modo == 'completar':
            _, respuestas = B.huecos(b.get('texto'))
            salida[bid] = [B.texto_plano(post.get(f'{clave}-{i}'), 120) for i in range(len(respuestas))]
        elif modo in ('numerica', 'corta'):
            salida[bid] = B.texto_plano(post.get(clave), 200)
        elif modo == 'abierta':
            salida[bid] = str(post.get(clave) or '')[:5000]
        elif modo == 'emparejar':
            salida[bid] = {str(i): post.get(f'{clave}-{i}') for i in range(len(b.get('pares') or []))
                           if str(post.get(f'{clave}-{i}') or '').isdigit()}
        elif modo == 'ordenar':
            orden = [x for x in str(post.get(clave) or '').split(',') if x.isdigit()]
            salida[bid] = [int(x) for x in orden]
        elif modo == 'clasificar':
            salida[bid] = {str(i): post.get(f'{clave}-{i}') for i in range(len(elementos_clasificar(b)))
                           if str(post.get(f'{clave}-{i}') or '').isdigit()}
    return salida


def respuesta_correcta_texto(b):
    """La respuesta correcta en palabras, para la versión del docente y para mostrar al terminar."""
    modo = b.get('modo')
    if modo == 'unica' and b.get('correcta') is not None and b['correcta'] < len(b.get('opciones') or []):
        return f"{'ABCDEF'[b['correcta']]}. {b['opciones'][b['correcta']]}"
    if modo == 'varias':
        return ', '.join(f"{'ABCDEF'[i]}" for i in b.get('correctas') or [])
    if modo == 'vf':
        return 'Verdadero' if b.get('valor') else 'Falso'
    if modo == 'completar':
        return ' · '.join(r[0] for r in B.huecos(b.get('texto'))[1] if r)
    if modo == 'numerica':
        t = b.get('respuesta') or ''
        if b.get('tolerancia'):
            t += f" (± {b['tolerancia']})"
        return f"{t} {b.get('unidad') or ''}".strip()
    if modo == 'corta':
        return ' / '.join(b.get('aceptadas') or [])
    if modo == 'emparejar':
        return ' · '.join(f'{a} → {c}' for a, c in b.get('pares') or [])
    if modo == 'ordenar':
        return ' → '.join(b.get('elementos') or [])
    if modo == 'clasificar':
        return ' · '.join(f"{g['nombre']}: {', '.join(g['elementos'])}" for g in b.get('grupos') or [])
    return ''
