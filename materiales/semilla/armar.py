"""Arma los documentos semilla (guía + taller por DBA) y los guarda como borradores de un docente.

Las gráficas se dibujan con el Graficador y quedan como imágenes editables (Imagen.grafica), igual que si el docente
las hubiera hecho en el editor. Las imágenes del banco:
  * «d-…»: dibujos exactos de mcolegio, ya en PNG en materiales/semilla/img/;
  * las de IA («m1-manzana»): se buscan en la carpeta que se indique (--imagenes); si no están, queda un recuadro
    «Imagen pendiente: m1-manzana» que el comando poner_imagenes_semilla cambia por la imagen cuando llega;
  * colecciones («m1-manzana×7/5») y pictogramas («pict:m1-mango.5,m1-banano.3») se arman aquí con la imagen suelta.
"""
import io
import re
from pathlib import Path

from django.core.files.base import ContentFile

from ..dba import catalogo as K
from . import banco, base

AREAS = {'MAT': 'matematicas', 'LEN': 'lenguaje', 'NAT': 'naturales', 'SOC': 'sociales'}
GRADOS = {'MAT': tuple(range(1, 12)), 'LEN': tuple(range(1, 12)), 'NAT': tuple(range(1, 12)), 'SOC': tuple(range(1, 12))}


def _modulos():
    import importlib
    return {(a, g): importlib.import_module(f'{__package__}.{AREAS[a]}_{g}') for a, gs in GRADOS.items() for g in gs}


MODULOS = _modulos()
CARPETA_DIBUJOS = Path(__file__).resolve().parent / 'img'
PENDIENTE = 'Imagen pendiente: '


def unidades(grado, area='MAT'):
    """[(dba del catálogo con «codigo», unidad)] en orden de DBA."""
    grado = int(grado)
    salida = []
    for n, u in sorted(MODULOS[(area, grado)].unidades().items()):
        codigo = f'{area}-{grado}-{n}'
        d = K.buscar(codigo)
        if d is None:
            raise ValueError(f'{codigo} no está en el catálogo')
        salida.append((dict(d, codigo=codigo), u))
    return salida


def documentos(grado, area='MAT'):
    """[{titulo, tipo, dba, bloques}] del grado: primero la guía y luego el taller de cada DBA."""
    grado = int(grado)
    salida = []
    for d, u in unidades(grado, area):
        guia = base.guia(d, u['tema'], u['objetivo'], u['explora'], u['aprende'], u['recuerda'], u['practica'],
                         momentos=u.get('momentos'))
        olimpiada = banco.bloques(grado, d['n']) if area == 'MAT' else []
        preguntas = list(u['taller'])
        if olimpiada:
            preguntas += [base.seccion('Preguntas tipo olimpiada', 'Marca la respuesta correcta.'), *olimpiada]
        taller = base.taller(d, u['tema'], preguntas, **({'indicacion': u['indicacion_taller']} if u.get('indicacion_taller') else {}))
        salida.append({'titulo': u['tema'][:150], 'tipo': 'guia_momentos', 'dba': d, 'tema': u['tema'], 'bloques': guia})
        salida.append({'titulo': f'{u.get("nombre_taller", "Taller")} · {u["tema"]}'[:150], 'tipo': 'taller', 'dba': d,
                       'tema': u['tema'], 'bloques': taller})
    return salida


# ---------------------------------------------------------------------------
# Imágenes
# ---------------------------------------------------------------------------
def _guardar_png(usuario, datos, grafica=None, nombre='imagen.png'):
    from PIL import Image as PILImage
    from ..models import Imagen
    ancho, alto = PILImage.open(io.BytesIO(datos)).size
    img = Imagen(propietario=usuario, ancho=ancho, alto=alto, peso=len(datos), grafica=grafica)
    img.archivo.save(nombre, ContentFile(datos), save=False)
    img.save()
    return img


def _imagen_grafica(usuario, b):
    from .. import graficas as G
    spec = G.limpiar(b['grafica'])
    datos, _, errores = G.dibujar(spec, 'png', dpi=200)
    if errores:
        raise ValueError(f'gráfica con errores: {errores}')
    img = _guardar_png(usuario, datos, grafica=spec, nombre='grafica.png')
    return {'id': b['id'], 'tipo': 'imagen', 'imagen': img.pk, 'ancho': b['ancho'], 'pie': b['pie'],
            'alinear': 'centro', 'ajuste': 'linea'}


def _buscar(id_img, carpetas):
    if id_img.startswith('d-'):
        from .dibujos import archivo
        p = CARPETA_DIBUJOS / archivo(id_img)
        return p if p.exists() else None
    for c in [CARPETA_DIBUJOS, *carpetas]:
        for ext in ('.png', '.jpg', '.jpeg', '.webp'):
            p = Path(c) / f'{id_img}{ext}'
            if p.exists():
                return p
    return None


def _abrir(ruta, lado=None):
    """La imagen sin el borde blanco y, si «lado», reducida para que quepa en ese cuadrado."""
    from PIL import Image as PILImage, ImageChops
    im = PILImage.open(ruta).convert('RGBA')
    fondo = PILImage.new('RGBA', im.size, (255, 255, 255, 255))
    plano = PILImage.alpha_composite(fondo, im).convert('RGB')
    caja = ImageChops.difference(plano, PILImage.new('RGB', plano.size, (255, 255, 255))).getbbox()
    if caja:
        plano = plano.crop(caja)
    if lado:
        plano.thumbnail((lado, lado), PILImage.LANCZOS)
    return plano


def _png(im):
    b = io.BytesIO()
    im.save(b, 'PNG', optimize=True)
    return b.getvalue()


def _coleccion(ruta, cantidad, por_fila, lado=220, hueco=36):
    from PIL import Image as PILImage
    pieza = _abrir(ruta, lado)
    filas = -(-cantidad // por_fila)
    cols = min(cantidad, por_fila)
    lienzo = PILImage.new('RGB', (cols * lado + (cols + 1) * hueco, filas * lado + (filas + 1) * hueco), 'white')
    for k in range(cantidad):
        f, c = divmod(k, por_fila)
        x = hueco + c * (lado + hueco) + (lado - pieza.width) // 2
        y = hueco + f * (lado + hueco) + (lado - pieza.height) // 2
        lienzo.paste(pieza, (x, y))
    return lienzo


def _pictograma(filas, lado=150, hueco=18):
    """Una fila por dato: el dibujo grande a la izquierda (el nombre del dato), una raya y un dibujo por cada uno."""
    from PIL import Image as PILImage, ImageDraw
    n_max = max(n for _, n in filas)
    ancho = hueco + int(lado * 1.3) + 3 * hueco + n_max * (lado + hueco)
    alto = len(filas) * (lado + 2 * hueco) + hueco
    lienzo = PILImage.new('RGB', (ancho, alto), 'white')
    dib = ImageDraw.Draw(lienzo)
    for k, (ruta, n) in enumerate(filas):
        y = hueco + k * (lado + 2 * hueco)
        grande = _abrir(ruta, int(lado * 1.3))
        lienzo.paste(grande, (hueco + (int(lado * 1.3) - grande.width) // 2, y + (lado - grande.height) // 2))
        x0 = hueco + int(lado * 1.3) + 2 * hueco
        dib.line([(x0 - hueco, y - hueco // 2), (x0 - hueco, y + lado + hueco // 2)], fill=(31, 58, 104), width=6)
        chica = _abrir(ruta, int(lado * 0.85))
        for j in range(n):
            x = x0 + j * (lado + hueco)
            dib.rectangle([x, y, x + lado, y + lado], outline=(203, 213, 225), width=3)
            lienzo.paste(chica, (x + (lado - chica.width) // 2, y + (lado - chica.height) // 2))
        if k < len(filas) - 1:
            dib.line([(hueco, y + lado + hueco), (ancho - hueco, y + lado + hueco)], fill=(226, 232, 240), width=3)
    return lienzo


def _datos_imagen(id_img, carpetas):
    """PNG (bytes) de una imagen del banco, o None si falta alguna pieza."""
    if id_img.startswith('pict:'):
        filas = []
        for parte in id_img[5:].split(','):
            nombre, n = parte.rsplit('.', 1)
            ruta = _buscar(nombre, carpetas)
            if ruta is None:
                return None
            filas.append((ruta, int(n)))
        return _png(_pictograma(filas))
    m = re.fullmatch(r'(.+)×(\d+)/(\d+)', id_img)
    if m:
        ruta = _buscar(m.group(1), carpetas)
        return _png(_coleccion(ruta, int(m.group(2)), int(m.group(3)))) if ruta else None
    ruta = _buscar(id_img, carpetas)
    return _png(_abrir(ruta, 1400)) if ruta else None


def _pendiente(b):
    """Recuadro que guarda qué imagen va aquí (se cambia solo cuando llega)."""
    from . import imagenes as I
    base_id = b['img'].split('×')[0]
    info = I.por_id(base_id)
    que = ''
    if b['img'].startswith('pict:'):
        que = 'Pictograma con: ' + ', '.join(f'{p.rsplit(".", 1)[1]} × {p.rsplit(".", 1)[0]}' for p in b['img'][5:].split(','))
    elif '×' in b['img']:
        que = f'{b["img"].split("×")[1].split("/")[0]} veces «{info["nombre"] if info else base_id}»'
    elif info:
        que = info['nombre']
    return base.recuadro(f'{PENDIENTE}{b["img"]}'[:80],
                         f'<p>Aquí va la imagen <b>{b["img"]}</b>{(": " + que) if que else ""}.</p>',
                         f'<p><small>Ancho {b["ancho"]} %{(" · pie: " + b["pie"]) if b["pie"] else ""}. '
                         f'Se pone sola cuando se carga el banco de imágenes.</small></p>', estilo='nota')


def _bloque_imagen(usuario, b, carpetas, cache):
    datos = _datos_imagen(b['img'], carpetas)
    if datos is None:
        return _pendiente(b)
    if b['img'] not in cache:
        cache[b['img']] = _guardar_png(usuario, datos, nombre=re.sub(r'[^\w.-]', '_', b['img'])[:60] + '.png').pk
    return {'id': b['id'], 'tipo': 'imagen', 'imagen': cache[b['img']], 'ancho': b['ancho'], 'pie': b['pie'],
            'alinear': 'centro', 'ajuste': 'linea'}


def resolver(usuario, bloques, carpetas=(), cache=None):
    cache = {} if cache is None else cache
    salida = []
    for b in bloques:
        if b['tipo'] == '_grafica':
            salida.append(_imagen_grafica(usuario, b))
        elif b['tipo'] == '_imagen':
            salida.append(_bloque_imagen(usuario, b, carpetas, cache))
        else:
            salida.append(b)
    return salida


def poner_pendientes(doc, carpetas, cache=None):
    """Cambia los recuadros «Imagen pendiente» del documento por la imagen, si ya está. Devuelve cuántas puso."""
    puestas, nuevos = 0, []
    for b in (doc.contenido or {}).get('bloques', []):
        if b.get('tipo') == 'recuadro' and str(b.get('titulo', '')).startswith(PENDIENTE):
            id_img = b['titulo'][len(PENDIENTE):]
            m = re.search(r'Ancho (\d+) %(?: · pie: ([^.<]*))?', b.get('html', ''))
            r = _bloque_imagen(doc.propietario, {'id': b['id'], 'img': id_img, 'ancho': int(m.group(1)) if m else 40,
                                                 'pie': (m.group(2) or '').strip() if m else ''}, carpetas, {} if cache is None else cache)
            if r['tipo'] == 'imagen':
                puestas += 1
                nuevos.append(r)
                continue
        nuevos.append(b)
    if puestas:
        doc.contenido = dict(doc.contenido, bloques=nuevos)
        doc.save(update_fields=['contenido'])
    return puestas


def guardar(usuario, grado, publicar=False, colegio=None, area='MAT', carpetas=()):
    """Crea los borradores (y, si publicar, los materiales del banco libre). Devuelve los Documentos creados."""
    from .. import bloques as B
    from .. import calificar as C
    from ..models import Documento, MaterialCompartido
    creados, cache = [], {}
    grado = int(grado)
    for item in documentos(grado, area):
        bloques = resolver(usuario, item['bloques'], carpetas, cache)
        imagenes = {b['imagen'] for b in bloques if b['tipo'] == 'imagen'}
        contenido = B.limpiar({'bloques': bloques, 'opciones': {'letra': 14} if grado <= 3 else {}}, imagenes)
        d = item['dba']
        doc = Documento.objects.create(propietario=usuario, colegio=colegio, titulo=item['titulo'], tipo=item['tipo'],
                                       area=d['area'], grado=f'{grado}.º', contenido=contenido)
        creados.append(doc)
        if publicar:
            MaterialCompartido.objects.create(
                documento=doc, autor=usuario, alcance='libre', estado='publicado', titulo=doc.titulo, tipo=doc.tipo,
                area=doc.area, grado=doc.grado, contenido=contenido, tema=item['tema'][:120],
                dba_codigo=d['codigo'], dba=K.etiqueta(d['codigo']),
                descripcion=f'Material semilla de mcolegio alrededor del DBA {d["n"]} de {d["area"]} {grado}.º.',
                preguntas=len([b for b in C.preguntas(contenido) if b.get('modo') != 'hoja']))
    return creados
