"""Cómo se califica cada tipo de pregunta de una ficha y cómo se mezcla lo que hay que mezclar.

Las respuestas del estudiante se guardan por id de bloque:
  unica: 2 · varias: [0, 2] · vf: true · completar: ["Bogotá", "Magdalena"] · numerica: "3,5"
  corta: "fotosíntesis" · abierta: "texto…" · emparejar: {"0": 2, "1": 0} (izquierda -> derecha original)
  ordenar: [2, 0, 1] (índices originales en el orden que dejó el estudiante)
  clasificar: {"0": 1, "1": 0} (índice del elemento en la lista plana -> grupo)
  senalar: [[23.5, 40.1], [70, 12]] (los puntos que marcó, en % de la imagen)
  archivo: 15 (id del ArchivoFicha que subió) · hoja: {"c1": "Bogotá", "c2": true, "c3": 1}
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


def dentro(punto, z):
    x, y = punto
    return z['x'] <= x <= z['x'] + z['w'] and z['y'] <= y <= z['y'] + z['h']


def puntos_marcados(r, maximo=30):
    """Los puntos válidos de una respuesta de «señalar»."""
    salida = []
    for p in (r or [])[:maximo]:
        try:
            x, y = float(p[0]), float(p[1])
        except (TypeError, ValueError, IndexError, KeyError):
            continue
        if 0 <= x <= 100 and 0 <= y <= 100:
            salida.append((x, y))
    return salida


def calificar_hoja(b, r):
    """(obtenidos, posibles, revisar, {id_campo: True/False/None}) de una hoja sobre un PDF."""
    r = r if isinstance(r, dict) else {}
    obtenidos, posibles, revisar, estado = CERO, CERO, False, {}
    for c in b.get('campos') or []:
        pts = Decimal(c.get('puntos') or 0)
        dado = r.get(c['id'])
        bien = None
        if c['tipo'] == 'texto':
            aceptadas = [x for x in (c.get('correcta') or '').split('|') if x.strip()]
            if aceptadas:
                bien = normal(dado) in {normal(a) for a in aceptadas}
            elif pts and normal(dado):
                revisar = True
            posibles += pts
        elif c['tipo'] == 'marca':
            marcada = dado is True or dado in ('1', 'on', 'true')
            if c.get('correcta'):
                posibles += pts
                bien = marcada
            else:
                bien = not marcada
                if marcada:
                    obtenidos -= pts      # marcar una que no va resta
        else:
            posibles += pts
            if c.get('correcta') is not None:
                try:
                    bien = dado is not None and dado != '' and int(dado) == c['correcta']
                except (TypeError, ValueError):
                    bien = False
        if bien and (c['tipo'] != 'marca' or c.get('correcta')):
            obtenidos += pts
        estado[c['id']] = bien
    return max(CERO, obtenidos), posibles, revisar, estado


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
        elif modo == 'senalar':
            zonas = b.get('zonas') or []
            marcas = puntos_marcados(r)
            if zonas:
                aciertos = sum(1 for z in zonas if any(dentro(p, z) for p in marcas))
                fuera = sum(1 for p in marcas if not any(dentro(p, z) for z in zonas))
                frac = max(CERO, Decimal(aciertos - fuera) / Decimal(len(zonas)))
        elif modo == 'archivo':
            revisar = r not in (None, '', 0)
        elif modo in ('sopa', 'crucigrama'):
            from . import juegos
            bien, total = (juegos.calificar_sopa if modo == 'sopa' else juegos.calificar_crucigrama)(b, r)
            frac = Decimal(bien) / Decimal(total) if total else CERO
        elif modo == 'hoja':
            o, p, revisar, _ = calificar_hoja(b, r)
            puntos = p if p else puntos
            frac = (o / p) if p else CERO
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
        elif modo == 'senalar':
            marcas = []
            for par in str(post.get(clave) or '').split(';')[:30]:
                xy = par.split(',')
                if len(xy) == 2:
                    marcas.append(list(xy))
            salida[bid] = [[round(x, 1), round(y, 1)] for x, y in puntos_marcados(marcas)]
        elif modo == 'archivo':
            salida[bid] = None          # el archivo lo guarda la vista
        elif modo == 'sopa':
            # Trazos «fila,columna,fila,columna» separados por punto y coma
            trazos = []
            for t in str(post.get(clave) or '').split(';')[:40]:
                partes = t.split(',')
                if len(partes) == 4 and all(x.strip().isdigit() for x in partes):
                    trazos.append([int(x) for x in partes])
            salida[bid] = trazos
        elif modo == 'crucigrama':
            from . import juegos
            salida[bid] = {f'{f}-{c}': juegos.palabra_limpia(post.get(f'{clave}-{f}-{c}'))[:1]
                           for (f, c) in juegos.celdas_crucigrama(b) if post.get(f'{clave}-{f}-{c}')}
        elif modo == 'hoja':
            valores = {}
            for c in b.get('campos') or []:
                v = post.get(f"{clave}-{c['id']}")
                if c['tipo'] == 'marca':
                    valores[c['id']] = v in ('1', 'on')
                elif c['tipo'] == 'lista':
                    valores[c['id']] = int(v) if str(v or '').isdigit() else None
                else:
                    valores[c['id']] = B.texto_plano(v, 120)
            salida[bid] = valores
    return salida


def respuesta_correcta_texto(b):
    """La respuesta correcta en palabras, para la versión del docente y para mostrar al terminar."""
    base = _respuesta_correcta(b)
    if b.get('solucion'):
        return f"{base} — {b['solucion']}" if base else b['solucion']
    return base


def _respuesta_correcta(b):
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
    if modo == 'senalar':
        n = len(b.get('zonas') or [])
        return f'{n} lugar{"es" if n != 1 else ""} marcado{"s" if n != 1 else ""} en verde' if n else ''
    if modo == 'hoja':
        return ' · '.join(texto_campo(c) for c in b.get('campos') or [] if texto_campo(c))
    if modo == 'sopa':
        return ', '.join(u['palabra'] for u in b.get('ubicaciones') or [])
    if modo == 'crucigrama':
        return ' · '.join(f"{p['numero']}{'H' if p['dir'] == 'h' else 'V'}. {p['palabra']}" for p in b.get('palabras') or [])
    return ''


def texto_campo(c):
    """La respuesta de un campo de la hoja en palabras."""
    if c['tipo'] == 'texto':
        return (c.get('correcta') or '').split('|')[0]
    if c['tipo'] == 'marca':
        return '✔' if c.get('correcta') else ''
    if c.get('correcta') is not None and c['correcta'] < len(c.get('opciones') or []):
        return c['opciones'][c['correcta']]
    return ''
