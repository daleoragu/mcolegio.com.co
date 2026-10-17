"""La plataforma como app del celular (PWA): manifiesto, iconos y service worker.

Cada colegio se instala con su propio nombre, sus colores y su escudo. No hay
que publicar nada en Play Store ni App Store: desde el navegador se toca
«Instalar app» (Android) o «Compartir → Agregar a inicio» (iPhone).
"""
import io
import json

from django.conf import settings
from django.contrib.staticfiles import finders
from django.core.cache import cache
from django.http import Http404, HttpResponse
from django.shortcuts import redirect, render
from django.views.decorators.cache import cache_control

VERSION_SW = '1'
TAMANOS = (192, 512)


def _colores(colegio):
    if colegio is None:
        return '#1f2937', '#ffffff'
    return (colegio.color_topbar or colegio.color_primario or '#343A40'), '#ffffff'


def _nombre_de_app(colegio):
    """El nombre corto que el colegio escogió; si no escogió, las iniciales."""
    propio = (getattr(colegio, 'nombre_app', '') or '').strip()
    return propio[:12] if propio else _nombre_corto(colegio.nombre)


def _nombre_corto(nombre):
    """Lo que sale debajo del icono: corto, para que no lo corte el celular."""
    palabras = [p for p in nombre.split() if p.lower() not in {'de', 'del', 'la', 'el', 'los', 'las', 'y'}]
    if len(nombre) <= 12:
        return nombre
    siglas = ''.join(p[0] for p in palabras if p[0].isalpha()).upper()
    return siglas[:8] if len(siglas) >= 2 else nombre[:12]


@cache_control(max_age=3600)
def manifiesto(request):
    colegio = getattr(request, 'colegio', None)
    nombre = colegio.nombre if colegio else 'mcolegio · Plataforma Académica'
    tema, fondo = _colores(colegio)
    datos = {
        'name': nombre,
        'short_name': _nombre_de_app(colegio) if colegio else 'mcolegio',
        'description': f'Notas, boletines, asistencia y comunicación de {nombre}.',
        'id': '/',
        'start_url': '/app/',
        'scope': '/',
        'display': 'standalone',
        'orientation': 'any',
        'lang': 'es-CO',
        'background_color': fondo,
        'theme_color': tema,
        'icons': [
            {'src': '/app/icono-192.png', 'sizes': '192x192', 'type': 'image/png', 'purpose': 'any'},
            {'src': '/app/icono-512.png', 'sizes': '512x512', 'type': 'image/png', 'purpose': 'any'},
            {'src': '/app/icono-512.png?maskable=1', 'sizes': '512x512', 'type': 'image/png', 'purpose': 'maskable'},
        ],
    }
    return HttpResponse(json.dumps(datos, ensure_ascii=False), content_type='application/manifest+json; charset=utf-8')


def _imagen_del_colegio(colegio):
    for campo in ('escudo', 'logo_izquierdo', 'favicon'):
        f = getattr(colegio, campo, None) if colegio else None
        if f:
            return f
    return None


def _png_icono(colegio, tam, maskable):
    """PNG cuadrado con el escudo centrado sobre blanco. None si no se puede."""
    from PIL import Image
    archivo = _imagen_del_colegio(colegio)
    try:
        if archivo:
            with archivo.open('rb') as fh:       # .open(): en producción está en Spaces, sin ruta en disco
                img = Image.open(io.BytesIO(fh.read()))
                img.load()
        else:
            ruta = finders.find(f'img/mcolegio-{tam}.png') or (settings.BASE_DIR / 'static' / 'img' / f'mcolegio-{tam}.png')
            img = Image.open(ruta)
            img.load()
    except Exception:
        return None
    img = img.convert('RGBA')
    margen = 0.18 if maskable else 0.06       # el icono «maskable» lo recorta el celular en círculo
    caja = int(tam * (1 - 2 * margen))
    img.thumbnail((caja, caja), Image.LANCZOS)
    lienzo = Image.new('RGBA', (tam, tam), (255, 255, 255, 255))
    lienzo.alpha_composite(img, ((tam - img.width) // 2, (tam - img.height) // 2))
    out = io.BytesIO()
    lienzo.convert('RGB').save(out, 'PNG', optimize=True)
    return out.getvalue()


def _icono_de_letras(colegio, tam):
    """Cuadro del color del colegio con sus iniciales, por si no hay ninguna imagen."""
    from PIL import Image, ImageDraw, ImageFont
    color, _ = _colores(colegio)
    try:
        fondo = Image.new('RGB', (tam, tam), color)
    except ValueError:
        fondo = Image.new('RGB', (tam, tam), '#1f2937')
    texto = _nombre_de_app(colegio).replace(' ', '')[:3].upper() if colegio else 'MC'
    d = ImageDraw.Draw(fondo)
    try:
        fuente = ImageFont.load_default(size=int(tam * 0.32))
    except TypeError:
        fuente = ImageFont.load_default()
    caja = d.textbbox((0, 0), texto, font=fuente)
    d.text(((tam - (caja[2] - caja[0])) / 2 - caja[0], (tam - (caja[3] - caja[1])) / 2 - caja[1]), texto,
           fill='white', font=fuente)
    out = io.BytesIO()
    fondo.save(out, 'PNG')
    return out.getvalue()


@cache_control(max_age=86400)
def icono(request, tam):
    if tam not in TAMANOS:
        raise Http404
    colegio = getattr(request, 'colegio', None)
    maskable = request.GET.get('maskable') == '1'
    archivo = _imagen_del_colegio(colegio)
    clave = f'app-icono:{getattr(colegio, "id", 0)}:{getattr(archivo, "name", "")}:{tam}:{int(maskable)}'
    try:
        png = cache.get(clave)
    except Exception:
        png = None
    if png is None:
        png = None
        for origen in (colegio, None):                 # escudo dañado o Spaces caído: el de mcolegio
            try:
                png = _png_icono(origen, tam, maskable)
            except Exception:
                png = None
            if png:
                break
        png = png or _icono_de_letras(colegio, tam)    # nunca falla: sin icono el celular no instala
        try:
            cache.set(clave, png, 6 * 3600)
        except Exception:
            pass
    return HttpResponse(png, content_type='image/png')


SERVICE_WORKER = """// mcolegio · service worker v%(version)s
// Solo guarda la página «sin conexión» y los archivos estáticos (estilos, iconos).
// Las páginas con datos (notas, boletines…) siempre se piden al servidor: nunca
// quedan guardadas en el celular.
const CACHE = 'mcolegio-v%(version)s';
const SIN_CONEXION = '/sin-conexion/';

self.addEventListener('install', (e) => {
  e.waitUntil(caches.open(CACHE).then((c) => c.addAll([SIN_CONEXION, '/app/icono-192.png'])).then(() => self.skipWaiting()));
});

self.addEventListener('activate', (e) => {
  e.waitUntil(caches.keys().then((ks) => Promise.all(ks.filter((k) => k !== CACHE).map((k) => caches.delete(k))))
    .then(() => self.clients.claim()));
});

self.addEventListener('fetch', (e) => {
  const req = e.request;
  if (req.method !== 'GET') return;
  const url = new URL(req.url);
  if (req.mode === 'navigate') {
    e.respondWith(fetch(req).catch(() => caches.match(SIN_CONEXION)));
    return;
  }
  if (url.origin === location.origin && url.pathname.startsWith('/static/')) {
    e.respondWith(caches.open(CACHE).then((c) => c.match(req).then((guardado) => {
      const red = fetch(req).then((r) => { if (r.ok) c.put(req, r.clone()); return r; }).catch(() => guardado);
      return guardado || red;
    })));
  }
});
"""


def service_worker(request):
    r = HttpResponse(SERVICE_WORKER % {'version': VERSION_SW}, content_type='application/javascript; charset=utf-8')
    r['Cache-Control'] = 'no-cache'
    r['Service-Worker-Allowed'] = '/'
    return r


def sin_conexion(request):
    return render(request, 'notas/app/sin_conexion.html', {'colegio': getattr(request, 'colegio', None)})


def diagnostico(request):
    """Página para revisar desde el celular por qué no se deja instalar."""
    return render(request, 'notas/app/diagnostico.html', {'colegio': getattr(request, 'colegio', None)})


def inicio(request):
    """Lo que abre el icono: el panel si ya entró; si no, el portal con el ingreso."""
    if request.user.is_authenticated:
        return redirect('notas:dashboard')
    return redirect('/')
