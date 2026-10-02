# pruebas/utils.py
import re
from collections import OrderedDict, defaultdict

RE_ENDPOINT = re.compile(r"""(const\s+ENDPOINT\s*=\s*)(['"])(.*?)\2""", re.S)
RE_CLAVE = re.compile(r"""(const\s+CLAVE_PANEL\s*=\s*)(['"])(.*?)\2""", re.S)


def reescribir_endpoint(contenido, url_endpoint, clave_panel=None):
    """Apunta el ENDPOINT del HTML subido hacia la plataforma.

    Devuelve (contenido_nuevo, se_reescribio). Si el archivo no trae la
    constante, se deja intacto: puede ser una página que no recoge resultados.
    """
    if isinstance(contenido, bytes):
        contenido = contenido.decode('utf-8', errors='replace')

    if not RE_ENDPOINT.search(contenido):
        return contenido, False

    contenido = RE_ENDPOINT.sub(lambda m: f"{m.group(1)}'{url_endpoint}'", contenido, count=1)
    if clave_panel and RE_CLAVE.search(contenido):
        contenido = RE_CLAVE.sub(lambda m: f"{m.group(1)}'{clave_panel}'", contenido, count=1)
    return contenido, True


def ip_cliente(request):
    adelante = request.META.get('HTTP_X_FORWARDED_FOR', '')
    if adelante:
        return adelante.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


# ---------------------------------------------------------------------------
# Análisis para el panel del docente
# ---------------------------------------------------------------------------

def analizar(sesiones):
    """Resume un conjunto de sesiones.

    Devuelve un diccionario con el consolidado general, el desempeño por
    competencia y el desempeño pregunta por pregunta, incluyendo qué distractor
    escogió la mayoría cuando la pregunta salió mal.
    """
    sesiones = list(sesiones)
    if not sesiones:
        return {
            'n': 0, 'promedio': 0, 'mejor': 0, 'peor': 0, 'tiempo_promedio': 0,
            'competencias': [], 'preguntas': [], 'franjas': [],
        }

    porcentajes = [s.porcentaje for s in sesiones]
    promedio = round(sum(porcentajes) / len(porcentajes), 1)
    tiempos = [s.segundos for s in sesiones if s.segundos]

    # Franjas
    conteo_franjas = OrderedDict([('Rojo', 0), ('Naranja', 0), ('Amarillo', 0), ('Verde', 0)])
    colores = {'Rojo': '#B3261E', 'Naranja': '#D98324', 'Amarillo': '#9E1982', 'Verde': '#2E7D32'}
    for s in sesiones:
        conteo_franjas[s.franja[0]] += 1

    # Detalles agrupados
    por_competencia = defaultdict(lambda: {'ok': 0, 'n': 0})
    por_pregunta = OrderedDict()

    for s in sesiones:
        for d in s.detalles.all():
            comp = d.competencia or '—'
            por_competencia[comp]['ok'] += 1 if d.acierto else 0
            por_competencia[comp]['n'] += 1

            fila = por_pregunta.setdefault(d.numero or str(d.orden), {
                'numero': d.numero or str(d.orden),
                'orden': d.orden,
                'competencia': comp,
                'aprendizaje': d.aprendizaje,
                'clave': d.clave,
                'explicacion': d.explicacion,
                'ok': 0, 'n': 0,
                'marcas': defaultdict(int),
            })
            fila['n'] += 1
            fila['ok'] += 1 if d.acierto else 0
            fila['marcas'][d.marcada or '—'] += 1

    competencias = [
        {
            'sigla': c,
            'ok': v['ok'],
            'n': v['n'],
            'pct': round(v['ok'] * 100.0 / v['n'], 1) if v['n'] else 0,
        }
        for c, v in sorted(por_competencia.items())
    ]

    preguntas = []
    for fila in por_pregunta.values():
        pct = round(fila['ok'] * 100.0 / fila['n'], 1) if fila['n'] else 0
        errores = {k: v for k, v in fila['marcas'].items() if k != fila['clave']}
        distractor = max(errores.items(), key=lambda x: x[1]) if errores else None
        preguntas.append({
            **fila,
            'marcas': dict(fila['marcas']),
            'pct': pct,
            'distractor': distractor[0] if distractor else '',
            'distractor_n': distractor[1] if distractor else 0,
        })
    preguntas.sort(key=lambda f: f['orden'])

    return {
        'n': len(sesiones),
        'promedio': promedio,
        'mejor': max(porcentajes),
        'peor': min(porcentajes),
        'tiempo_promedio': int(sum(tiempos) / len(tiempos)) if tiempos else 0,
        'competencias': competencias,
        'preguntas': preguntas,
        'franjas': [
            {'nombre': k, 'n': v, 'color': colores[k],
             'pct': round(v * 100.0 / len(sesiones), 1)}
            for k, v in conteo_franjas.items()
        ],
    }


def hhmm(segundos):
    segundos = int(segundos or 0)
    return f'{segundos // 60:02d}:{segundos % 60:02d}'


# ---------------------------------------------------------------------------
# Sitios completos en .zip
# ---------------------------------------------------------------------------

import posixpath
import zipfile
from io import BytesIO

from django.core.files.base import ContentFile
from django.core.files.storage import default_storage

# Lo que se permite publicar. Todo lo demás del .zip se ignora en silencio.
EXTENSIONES_SITIO = {
    '.html', '.htm', '.css', '.js', '.mjs', '.json', '.txt', '.csv', '.xml',
    '.svg', '.png', '.jpg', '.jpeg', '.gif', '.webp', '.avif', '.ico', '.bmp',
    '.woff', '.woff2', '.ttf', '.otf', '.eot',
    '.mp3', '.mp4', '.webm', '.ogg', '.wav', '.pdf', '.map', '.webmanifest',
}

MAX_ARCHIVOS = 600
MAX_DESCOMPRIMIDO = 200 * 1024 * 1024  # 200 MB ya descomprimido


class ZipInvalido(Exception):
    pass


def _ruta_segura(nombre):
    """Descarta rutas peligrosas o inútiles de un .zip.

    Devuelve la ruta limpia, o None si hay que ignorar esa entrada.
    """
    nombre = nombre.replace('\\', '/')
    if nombre.endswith('/'):
        return None
    partes = []
    for parte in nombre.split('/'):
        if parte in ('', '.'):
            continue
        if parte == '..':
            raise ZipInvalido('El archivo .zip contiene rutas que salen de su carpeta.')
        if parte.startswith('__MACOSX') or parte == '.DS_Store':
            return None
        partes.append(parte)
    if not partes:
        return None
    if nombre.startswith('/'):
        raise ZipInvalido('El archivo .zip contiene rutas absolutas.')
    return '/'.join(partes)


def _quitar_carpeta_raiz(rutas):
    """Si todo el .zip cuelga de una sola carpeta, la quita.

    Así un zip que trae "mi-sitio/index.html" se publica como "index.html".
    """
    primeras = {r.split('/')[0] for r in rutas if '/' in r}
    if len(primeras) == 1 and all('/' in r for r in rutas):
        raiz = primeras.pop()
        return {r: r[len(raiz) + 1:] for r in rutas}
    return {r: r for r in rutas}


def extraer_sitio(archivo, base, transformar_html=None):
    """Descomprime un .zip dentro del almacenamiento, bajo `base`.

    `transformar_html` recibe el texto de cada .html y devuelve (texto, cambió).
    Devuelve (cantidad_de_archivos, ruta_del_indice, html_reescritos).
    """
    try:
        comprimido = zipfile.ZipFile(archivo)
    except zipfile.BadZipFile:
        raise ZipInvalido('El archivo no es un .zip válido.')

    entradas = {}
    total = 0
    for info in comprimido.infolist():
        ruta = _ruta_segura(info.filename)
        if not ruta:
            continue
        if posixpath.splitext(ruta)[1].lower() not in EXTENSIONES_SITIO:
            continue
        total += info.file_size
        if total > MAX_DESCOMPRIMIDO:
            raise ZipInvalido('El contenido del .zip supera los 200 MB.')
        entradas[info.filename] = ruta

    if not entradas:
        raise ZipInvalido('El .zip no trae ningún archivo publicable.')
    if len(entradas) > MAX_ARCHIVOS:
        raise ZipInvalido(f'El .zip trae {len(entradas)} archivos y el máximo es {MAX_ARCHIVOS}.')

    limpias = _quitar_carpeta_raiz(set(entradas.values()))

    guardados, reescritos = 0, 0
    indice = None
    for original, ruta in entradas.items():
        destino = limpias[ruta]
        contenido = comprimido.read(original)

        if destino.lower().endswith(('.html', '.htm')) and transformar_html:
            texto, cambio = transformar_html(contenido)
            contenido = texto.encode('utf-8')
            reescritos += 1 if cambio else 0

        default_storage.save(posixpath.join(base, destino), ContentFile(contenido))
        guardados += 1

        if indice is None and destino.lower() in ('index.html', 'index.htm'):
            indice = destino

    if indice is None:
        htmls = sorted(d for d in limpias.values() if d.lower().endswith(('.html', '.htm')))
        if not htmls:
            raise ZipInvalido('El .zip no trae ningún archivo .html.')
        # Se prefiere uno que esté en la raíz del sitio.
        raiz = [h for h in htmls if '/' not in h]
        indice = (raiz or htmls)[0]

    return guardados, indice, reescritos


def borrar_sitio(base):
    """Borra del almacenamiento todos los archivos que cuelgan de `base`."""
    if not base:
        return
    try:
        carpetas, archivos = default_storage.listdir(base)
    except (NotImplementedError, OSError):
        return
    for nombre in archivos:
        try:
            default_storage.delete(posixpath.join(base, nombre))
        except Exception:
            pass
    for carpeta in carpetas:
        borrar_sitio(posixpath.join(base, carpeta))


# ---------------------------------------------------------------------------
# Código QR
# ---------------------------------------------------------------------------

def generar_qr(url, tamano=10):
    """Devuelve el PNG de un código QR como bytes."""
    import qrcode

    codigo = qrcode.QRCode(box_size=tamano, border=2)
    codigo.add_data(url)
    codigo.make(fit=True)
    imagen = codigo.make_image(fill_color='#460F10', back_color='white')

    memoria = BytesIO()
    imagen.save(memoria, format='PNG')
    return memoria.getvalue()
