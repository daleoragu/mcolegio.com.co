"""El tablero de la clase: operaciones (agregar, reemplazar, borrar, limpiar, fondo), quién puede hacer qué y
lo que cambió desde la versión que tiene cada pantalla.

Todo llega validado: coordenadas acotadas, colores #rrggbb, textos cortos y solo imágenes de este tablero.
El docente puede todo; un estudiante, si el docente lo habilitó, agrega y modifica/borra solo lo suyo."""
import re

from django.db import transaction

from .models import TableroClase

MAX_OBJETOS = 4000
MAX_PUNTOS = 3000
MAX_CAMBIOS = 400
LIMITE = 1_000_000          # el mundo es «infinito», pero no tanto
TIPOS = ('trazo', 'linea', 'texto', 'imagen')
HERRAMIENTAS = ('lapiz', 'resaltar', 'linea', 'poli')     # poli: segmentos rectos (formas, regla, compás)
FONDOS = ('blanco', 'cuadros', 'rayas', 'verde')


def _num(v, minimo=-LIMITE, maximo=LIMITE):
    try:
        x = float(v)
    except (TypeError, ValueError):
        raise ValueError('número inválido')
    if x != x:
        raise ValueError('número inválido')
    return round(max(minimo, min(maximo, x)), 1)


def _punto(p):
    x, y = _num(p[0]), _num(p[1])
    if len(p) < 3 or p[2] is None:
        return [x, y]
    try:
        pr = float(p[2])
    except (TypeError, ValueError):
        return [x, y]
    if pr != pr:
        return [x, y]
    return [x, y, -1 if pr < 0 else round(min(1.0, pr), 2)]


def _color(v):
    from materiales.bloques import _a_hex
    return _a_hex(v) or '#111827'


def limpiar_objeto(o, tablero, autor):
    """El objeto validado (con su autor puesto por el servidor) o ValueError."""
    if not isinstance(o, dict):
        raise ValueError('objeto inválido')
    oid = str(o.get('id') or '')
    if not re.fullmatch(r'[a-zA-Z0-9_-]{1,24}', oid):
        raise ValueError('id inválido')
    t = o.get('t')
    if t not in TIPOS:
        raise ValueError('tipo inválido')
    n = {'id': oid, 't': t, 'a': autor, 'c': _color(o.get('c')), 'g': int(_num(o.get('g', 3), 1, 400))}
    if t in ('trazo', 'linea'):
        puntos = o.get('p')
        if not isinstance(puntos, list) or not puntos or len(puntos) > MAX_PUNTOS:
            raise ValueError('trazo inválido')
        # Cada punto: [x, y] o [x, y, presión 0..1] (lápiz); en «poli», presión -1 = levantar el lápiz (otra parte de la forma)
        n['p'] = [_punto(p) for p in puntos if isinstance(p, (list, tuple)) and len(p) >= 2]
        if not n['p']:
            raise ValueError('trazo vacío')
        n['h'] = o.get('h') if o.get('h') in HERRAMIENTAS else 'lapiz'
    elif t == 'texto':
        n.update(x=_num(o.get('x')), y=_num(o.get('y')), texto=str(o.get('texto') or '')[:2000])
        if not n['texto'].strip():
            raise ValueError('texto vacío')
    else:
        try:
            img = int(o.get('img'))
        except (TypeError, ValueError):
            raise ValueError('imagen inválida')
        if not tablero.imagenes.filter(pk=img).exists():
            raise ValueError('imagen de otro tablero')
        n.update(img=img, x=_num(o.get('x')), y=_num(o.get('y')), w=_num(o.get('w'), 4, 50000), h=_num(o.get('h'), 4, 50000))
    return n


def aplicar(tablero_id, op, autor, es_docente, puede_editar):
    """Aplica una operación y devuelve la versión nueva. ValueError / PermissionError si no se puede."""
    if not puede_editar:
        raise PermissionError('El docente no ha habilitado la escritura en este tablero.')
    if not isinstance(op, dict):
        raise ValueError('operación inválida')
    tipo = op.get('op')
    with transaction.atomic():
        t = TableroClase.objects.select_for_update().get(pk=tablero_id)
        objetos = list(t.objetos or [])
        por_id = {o['id']: k for k, o in enumerate(objetos)}

        def mio(oid):
            k = por_id.get(oid)
            return k is not None and (es_docente or objetos[k].get('a') == autor)

        if tipo == 'agregar':
            o = limpiar_objeto(op.get('obj'), t, autor)
            if o['id'] in por_id:
                return t.version                       # ya estaba (el mismo envío repetido)
            if len(objetos) >= MAX_OBJETOS:
                raise ValueError('El tablero está lleno: borre algo o abra otro tablero.')
            objetos.append(o)
            registro = {'op': 'agregar', 'obj': o}
        elif tipo == 'reemplazar':
            o = op.get('obj') or {}
            if not mio(str(o.get('id'))):
                raise PermissionError('Solo puede mover o cambiar lo que usted hizo.')
            k = por_id[o['id']]
            nuevo = limpiar_objeto(o, t, objetos[k].get('a', autor))
            objetos[k] = nuevo
            registro = {'op': 'reemplazar', 'obj': nuevo}
        elif tipo == 'borrar':
            ids = [str(x) for x in (op.get('ids') or [op.get('id')]) if x][:500]
            quitar = {i for i in ids if mio(i)}
            if not quitar:
                return t.version
            objetos = [o for o in objetos if o['id'] not in quitar]
            registro = {'op': 'borrar', 'ids': sorted(quitar)}
        elif tipo == 'limpiar':
            if not es_docente:
                raise PermissionError('Solo el docente borra todo el tablero.')
            objetos = []
            registro = {'op': 'limpiar'}
        elif tipo == 'fondo':
            if not es_docente or op.get('fondo') not in FONDOS:
                raise PermissionError('Solo el docente cambia el fondo.')
            t.fondo = op['fondo']
            registro = {'op': 'fondo', 'fondo': t.fondo}
        else:
            raise ValueError('operación desconocida')
        t.version += 1
        t.objetos = objetos
        t.cambios = (list(t.cambios or []) + [[t.version, registro]])[-MAX_CAMBIOS:]
        t.save(update_fields=['objetos', 'cambios', 'version', 'fondo', 'actualizado'])
        return t.version


def estado(t, desde):
    """Lo que necesita una pantalla que va en la versión «desde»: nada, las operaciones nuevas o todo."""
    base = {'v': t.version, 'editan': t.editan_estudiantes, 'compartido': t.aula_id is not None, 'fondo': t.fondo,
            'titulo': t.titulo}
    if desde == t.version:
        return base
    cambios = t.cambios or []
    if desde is not None and 0 <= desde < t.version and cambios and cambios[0][0] <= desde + 1:
        return dict(base, ops=[op for v, op in cambios if v > desde])
    return dict(base, objetos=t.objetos or [])


def miniatura(t, url_imagen=None, ancho=320, alto=180, max_objetos=600, max_imagenes=4):
    """Un SVG pequeño con lo que tiene el tablero, para la lista del repositorio (se arma al vuelo: no ocupa nube).
    Encuadra todo lo dibujado; los trazos se simplifican. url_imagen(id) da la dirección de cada imagen pegada."""
    from django.utils.html import escape
    objetos = [o for o in (t.objetos or []) if isinstance(o, dict)][-max_objetos:]
    fondo = '#1f3d2f' if t.fondo == 'verde' else '#ffffff'
    cajas = []
    for o in objetos:
        if o.get('t') in ('trazo', 'linea') and o.get('p'):
            xs, ys = [p[0] for p in o['p']], [p[1] for p in o['p']]
            cajas.append((min(xs), min(ys), max(xs), max(ys)))
        elif o.get('t') == 'texto':
            lineas = str(o.get('texto', '')).split('\n')
            g = o.get('g', 16)
            cajas.append((o['x'], o['y'], o['x'] + max(len(x) for x in lineas) * g * .55, o['y'] + len(lineas) * g * 1.25))
        elif o.get('t') == 'imagen':
            cajas.append((o['x'], o['y'], o['x'] + o['w'], o['y'] + o['h']))
    if not cajas:
        return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {ancho} {alto}" class="tb-mini" role="img" aria-label="Tablero vacío">'
                f'<rect width="{ancho}" height="{alto}" fill="{fondo}"/></svg>')
    x0, y0 = min(c[0] for c in cajas), min(c[1] for c in cajas)
    x1, y1 = max(c[2] for c in cajas), max(c[3] for c in cajas)
    w, h = max(x1 - x0, 1), max(y1 - y0, 1)
    # Margen y la misma proporción de la tarjeta
    m = max(w, h) * .06 + 10
    x0, y0, w, h = x0 - m, y0 - m, w + 2 * m, h + 2 * m
    if w / h < ancho / alto:
        x0, w = x0 - (h * ancho / alto - w) / 2, h * ancho / alto
    else:
        y0, h = y0 - (w * alto / ancho - h) / 2, w * alto / ancho
    minimo = w / 220            # que las líneas delgadas se alcancen a ver en pequeño
    r = lambda v: f'{v:.1f}'
    partes, imagenes = [], 0
    for o in objetos:
        tipo, color = o.get('t'), escape(o.get('c', '#111827'))
        if tipo in ('trazo', 'linea') and o.get('p'):
            pts = o['p']
            paso = max(1, len(pts) // 40)
            elegidos = pts[::paso] + ([pts[-1]] if (len(pts) - 1) % paso else [])
            d, nuevo = [], True
            for p in elegidos:
                if len(p) > 2 and p[2] == -1:
                    nuevo = True
                d.append(('M' if nuevo else 'L') + r(p[0]) + ' ' + r(p[1]))
                nuevo = False
            if len(d) == 1:
                d.append('l0.1 0')
            opacidad = ' stroke-opacity=".35"' if o.get('h') == 'resaltar' else ''
            grosor = max(o.get('g', 3) * (3 if o.get('h') == 'resaltar' else 1), minimo)
            partes.append(f'<path d="{"".join(d)}" fill="none" stroke="{color}" stroke-width="{r(grosor)}" '
                          f'stroke-linecap="round" stroke-linejoin="round"{opacidad}/>')
        elif tipo == 'texto':
            g = o.get('g', 16)
            for k, linea in enumerate(str(o.get('texto', '')).split('\n')[:12]):
                if linea.strip():
                    partes.append(f'<text x="{r(o["x"])}" y="{r(o["y"] + g * (k + .9))}" font-size="{r(g)}" fill="{color}" '
                                  f'font-family="system-ui,sans-serif">{escape(linea[:80])}</text>')
        elif tipo == 'imagen':
            caja = f'x="{r(o["x"])}" y="{r(o["y"])}" width="{r(o["w"])}" height="{r(o["h"])}"'
            if url_imagen and imagenes < max_imagenes:
                imagenes += 1
                partes.append(f'<image {caja} href="{escape(url_imagen(o["img"]))}" preserveAspectRatio="none"/>')
            else:
                partes.append(f'<rect {caja} fill="#e2e8f0" stroke="#94a3b8" stroke-width="{r(minimo)}"/>')
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{r(x0)} {r(y0)} {r(w)} {r(h)}" class="tb-mini" role="img" '
            f'aria-label="Vista previa del tablero" preserveAspectRatio="xMidYMid meet">'
            f'<rect x="{r(x0)}" y="{r(y0)}" width="{r(w)}" height="{r(h)}" fill="{fondo}"/>{"".join(partes)}</svg>')
