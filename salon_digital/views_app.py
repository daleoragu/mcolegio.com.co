"""La app propia de Mi Salón Virtual (plan individual), separada de la app de cada colegio.

  · App web instalable (PWA) con su nombre, su ícono y sus accesos directos: /salon_digital/manifest.webmanifest
    Se instala desde Chrome o Edge (Android y computador) o desde Safari con «Agregar a inicio» (iPhone y iPad).
  · APK de Android: es la misma app dentro de una «Trusted Web Activity» (ver apps/misalon/LEEME.md).
    Para que abra sin la barra del navegador, Android revisa /.well-known/assetlinks.json, que se arma con las
    variables de entorno ANDROID_PAQUETE y ANDROID_SHA256 (la huella de la llave con que se firmó la APK).
  · Enlaces de descarga que se muestran en «Instalar la app» (variables de entorno, opcionales):
      SALON_APK_URL   APK para descargar directo (si no, se usa salon_digital/static/salon_digital/app/MiSalon.apk si existe)
      SALON_PLAY_URL  la ficha en Google Play
      SALON_IOS_URL   la ficha en el App Store
"""
import io
import json
import os

from django.contrib.staticfiles import finders
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.templatetags.static import static
from django.urls import reverse
from django.views.decorators.cache import cache_control

APP_ID = '/salon_digital/app/'
NOMBRE = 'Mi Salón Virtual'
PAQUETE = 'co.com.mcolegio.misalon'
AZUL, AZUL_OSCURO = '#2b4f8a', '#1f3a68'


@cache_control(max_age=3600)
def manifiesto(request):
    icono = lambda nombre: static(f'salon_digital/app/{nombre}')
    datos = {
        'id': APP_ID,
        'name': f'{NOMBRE} · mcolegio',
        'short_name': 'Mi Salón',
        'description': 'Tus aulas, grupos, juegos, eventos y colegas docentes en una sola app.',
        'start_url': APP_ID + '?fuente=app',
        'scope': '/',
        'display': 'standalone',
        'display_override': ['window-controls-overlay', 'standalone'],
        'orientation': 'any',
        'lang': 'es-CO',
        'dir': 'ltr',
        'categories': ['education', 'productivity'],
        'background_color': '#ffffff',
        'theme_color': AZUL_OSCURO,
        'icons': [
            {'src': icono('icono-96.png'), 'sizes': '96x96', 'type': 'image/png', 'purpose': 'any'},
            {'src': icono('icono-192.png'), 'sizes': '192x192', 'type': 'image/png', 'purpose': 'any'},
            {'src': icono('icono-512.png'), 'sizes': '512x512', 'type': 'image/png', 'purpose': 'any'},
            {'src': icono('icono-512-maskable.png'), 'sizes': '512x512', 'type': 'image/png', 'purpose': 'maskable'},
        ],
        'shortcuts': [
            {'name': 'Mis aulas', 'url': reverse('aula:inicio'), 'icons': [{'src': icono('icono-96.png'), 'sizes': '96x96'}]},
            {'name': 'Grupos', 'url': reverse('salon_digital:grupos'), 'icons': [{'src': icono('icono-96.png'), 'sizes': '96x96'}]},
            {'name': 'Eventos', 'url': reverse('aula:eventos'), 'icons': [{'src': icono('icono-96.png'), 'sizes': '96x96'}]},
            {'name': 'Colegas', 'url': '/chat/colegas/', 'icons': [{'src': icono('icono-96.png'), 'sizes': '96x96'}]},
        ],
        'prefer_related_applications': False,
    }
    play = os.getenv('SALON_PLAY_URL', '')
    if play:
        datos['related_applications'] = [{'platform': 'play', 'url': play, 'id': os.getenv('ANDROID_PAQUETE', PAQUETE)}]
    return HttpResponse(json.dumps(datos, ensure_ascii=False), content_type='application/manifest+json; charset=utf-8')


def inicio(request):
    """Lo que abre el ícono de la app: Mis aulas si ya entró; si no, el ingreso del Salón."""
    if request.user.is_authenticated and hasattr(request.user, 'cuenta_salon'):
        return redirect('salon_digital:inicio')
    if request.user.is_authenticated:
        return redirect('salon_digital:landing')
    return redirect(reverse('salon_digital:entrar') + '?next=' + reverse('salon_digital:inicio'))


def _qr_svg(texto):
    import qrcode
    import qrcode.image.svg
    img = qrcode.make(texto, image_factory=qrcode.image.svg.SvgPathImage, box_size=8, border=2)
    salida = io.BytesIO()
    img.save(salida)
    return salida.getvalue().decode('utf-8').split('?>', 1)[-1]


def _apk_url():
    if os.getenv('SALON_APK_URL'):
        return os.getenv('SALON_APK_URL')
    return static('salon_digital/app/MiSalon.apk') if finders.find('salon_digital/app/MiSalon.apk') else ''


def instalar(request):
    """Cómo instalar la app en cada equipo (con QR para pasarla del computador al celular)."""
    url = request.build_absolute_uri(reverse('salon_digital:app_instalar'))
    return render(request, 'salon_digital/instalar_app.html', {
        'qr': _qr_svg(url), 'url': url, 'apk_url': _apk_url(), 'play_url': os.getenv('SALON_PLAY_URL', ''),
        'ios_url': os.getenv('SALON_IOS_URL', ''), 'nombre': NOMBRE,
    })


@cache_control(max_age=3600, public=True)
def assetlinks(request):
    """Digital Asset Links: le dice a Android que la APK y mcolegio.com.co son del mismo dueño
    (así la app abre a pantalla completa, sin la barra del navegador)."""
    huellas = [h.strip().upper() for h in os.getenv('ANDROID_SHA256', '').split(',') if h.strip()]
    datos = [{
        'relation': ['delegate_permission/common.handle_all_urls'],
        'target': {'namespace': 'android_app', 'package_name': os.getenv('ANDROID_PAQUETE', PAQUETE),
                   'sha256_cert_fingerprints': huellas},
    }] if huellas else []
    return JsonResponse(datos, safe=False)
