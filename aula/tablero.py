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
