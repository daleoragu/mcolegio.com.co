# notas/videos.py
"""Reconoce un video pegado por el docente: el enlace de YouTube, Vimeo, Google Drive
o Facebook, o el código de inserción (<iframe …>) que dan esas páginas.

Nunca se guarda ni se muestra el HTML que pega la persona: se saca el
identificador del video y la dirección para incrustarlo se arma aquí, siempre
contra sitios conocidos. Así nadie puede colar un script en el portal.
"""
import re
from html import unescape
from urllib.parse import parse_qs, quote, urlparse

PROVEEDORES = [('youtube', 'YouTube'), ('vimeo', 'Vimeo'), ('drive', 'Google Drive'), ('facebook', 'Facebook')]

_ID_YT = re.compile(r'^[A-Za-z0-9_-]{11}$')


class VideoNoReconocido(ValueError):
    pass


def _segundos(valor):
    """'90', '90s', '1m30s', '1h2m3s' -> 90… ; lo demás -> 0."""
    if not valor:
        return 0
    valor = str(valor).strip().lower()
    if valor.isdigit():
        return int(valor)
    m = re.fullmatch(r'(?:(\d+)h)?(?:(\d+)m)?(?:(\d+)s)?', valor)
    if not m or not any(m.groups()):
        return 0
    h, mi, s = (int(x or 0) for x in m.groups())
    return h * 3600 + mi * 60 + s


def _del_iframe(texto):
    """Del código <iframe src="…"> saca la dirección del video."""
    m = re.search(r'<iframe[^>]*\ssrc\s*=\s*["\']([^"\']+)["\']', texto, re.I)
    if not m:
        raise VideoNoReconocido('El código no trae la dirección del video (src). Pegue mejor el enlace.')
    return unescape(m.group(1)).strip()


def analizar(texto):
    """Devuelve {'proveedor', 'video_id', 'embed', 'miniatura'} o lanza VideoNoReconocido."""
    texto = (texto or '').strip()
    if not texto:
        raise VideoNoReconocido('Pegue el enlace del video.')
    if '<' in texto:
        texto = _del_iframe(texto)
    if texto.startswith('//'):
        texto = 'https:' + texto
    if not re.match(r'^https?://', texto, re.I):
        texto = 'https://' + texto
    u = urlparse(texto)
    host = (u.hostname or '').lower()
    if host.startswith('www.'):
        host = host[4:]
    if host.startswith('m.'):
        host = host[2:]
    q = parse_qs(u.query)
    partes = [p for p in u.path.split('/') if p]

    # --- YouTube ---------------------------------------------------------
    if host in ('youtube.com', 'youtube-nocookie.com', 'youtu.be', 'music.youtube.com'):
        vid = None
        if host == 'youtu.be' and partes:
            vid = partes[0]
        elif partes[:1] == ['watch']:
            vid = (q.get('v') or [None])[0]
        elif len(partes) >= 2 and partes[0] in ('embed', 'shorts', 'live', 'v'):
            vid = partes[1]
        if not vid or not _ID_YT.match(vid):
            raise VideoNoReconocido('No encontré el video en ese enlace de YouTube. Use «Compartir → Copiar enlace».')
        inicio = _segundos((q.get('t') or q.get('start') or [''])[0])
        embed = f'https://www.youtube-nocookie.com/embed/{vid}?rel=0' + (f'&start={inicio}' if inicio else '')
        return {'proveedor': 'youtube', 'video_id': vid, 'embed': embed,
                'miniatura': f'https://i.ytimg.com/vi/{vid}/hqdefault.jpg'}

    # --- Vimeo -----------------------------------------------------------
    if host in ('vimeo.com', 'player.vimeo.com'):
        numeros = [p for p in partes if p.isdigit()]
        if not numeros:
            raise VideoNoReconocido('No encontré el número del video de Vimeo.')
        vid = numeros[0]
        return {'proveedor': 'vimeo', 'video_id': vid, 'embed': f'https://player.vimeo.com/video/{vid}',
                'miniatura': ''}

    # --- Google Drive ----------------------------------------------------
    if host == 'drive.google.com':
        vid = None
        if len(partes) >= 3 and partes[0] == 'file' and partes[1] == 'd':
            vid = partes[2]
        elif (q.get('id') or [None])[0]:
            vid = q['id'][0]
        if not vid or not re.fullmatch(r'[A-Za-z0-9_-]{10,}', vid):
            raise VideoNoReconocido('No encontré el archivo en ese enlace de Drive.')
        return {'proveedor': 'drive', 'video_id': vid, 'embed': f'https://drive.google.com/file/d/{vid}/preview',
                'miniatura': ''}

    # --- Facebook --------------------------------------------------------
    if host in ('facebook.com', 'fb.watch', 'web.facebook.com'):
        if host == 'facebook.com' and partes[:2] == ['plugins', 'video.php']:
            href = (q.get('href') or [''])[0]
            if not href:
                raise VideoNoReconocido('No encontré el video de Facebook en ese código.')
            return analizar(href)
        if host != 'fb.watch' and not ('videos' in partes or partes[:1] in (['watch'], ['reel'])):
            raise VideoNoReconocido('Ese enlace de Facebook no es de un video.')
        limpio = f'https://{u.hostname}{u.path}' + (f'?v={q["v"][0]}' if q.get('v') else '')
        return {'proveedor': 'facebook', 'video_id': limpio[:200],
                'embed': 'https://www.facebook.com/plugins/video.php?show_text=false&href=' + quote(limpio, safe=''),
                'miniatura': ''}

    raise VideoNoReconocido('Por ahora se aceptan videos de YouTube, Vimeo, Google Drive y Facebook.')


# ---------------------------------------------------------------------------
# Fotos por enlace (galería)
# ---------------------------------------------------------------------------

def analizar_foto(texto):
    """Foto o publicación enlazada. Devuelve {'fuente', 'imagen_externa', 'embed', 'enlace'}.

    - Google Drive: se muestra como foto normal (el archivo debe estar compartido
      con «Cualquier persona con el enlace»).
    - Instagram y Facebook: sus fotos sueltas tienen direcciones que caducan, así
      que se muestra la publicación incrustada, que sí dura.
    """
    texto = (texto or '').strip()
    if not texto:
        raise VideoNoReconocido('Pegue el enlace de la foto.')
    if '<' in texto:
        m = re.search(r'data-instgrm-permalink\s*=\s*["\']([^"\']+)["\']', texto, re.I)
        texto = unescape(m.group(1)) if m else _del_iframe(texto)
    if not re.match(r'^https?://', texto, re.I):
        texto = 'https://' + texto.lstrip('/')
    u = urlparse(texto)
    host = (u.hostname or '').lower()
    for prefijo in ('www.', 'm.', 'web.'):
        if host.startswith(prefijo):
            host = host[len(prefijo):]
    q = parse_qs(u.query)
    partes = [p for p in u.path.split('/') if p]

    if host == 'drive.google.com':
        vid = None
        if len(partes) >= 3 and partes[0] == 'file' and partes[1] == 'd':
            vid = partes[2]
        elif (q.get('id') or [None])[0]:
            vid = q['id'][0]
        if not vid or not re.fullmatch(r'[A-Za-z0-9_-]{10,}', vid):
            raise VideoNoReconocido('No encontré la foto en ese enlace de Drive.')
        return {'fuente': 'drive', 'imagen_externa': f'https://drive.google.com/thumbnail?id={vid}&sz=w1600',
                'embed': '', 'enlace': f'https://drive.google.com/file/d/{vid}/view'}

    if host == 'instagram.com':
        for i, p in enumerate(partes[:-1]):
            if p in ('p', 'reel', 'tv') and re.fullmatch(r'[A-Za-z0-9_-]{5,40}', partes[i + 1]):
                codigo = partes[i + 1]
                return {'fuente': 'instagram', 'imagen_externa': '',
                        'embed': f'https://www.instagram.com/p/{codigo}/embed/captioned/',
                        'enlace': f'https://www.instagram.com/p/{codigo}/'}
        raise VideoNoReconocido('Ese enlace de Instagram no es de una publicación (debe tener /p/ o /reel/).')

    if host in ('facebook.com', 'fb.com'):
        if partes[:2] == ['plugins', 'post.php'] or partes[:2] == ['plugins', 'video.php']:
            href = (q.get('href') or [''])[0]
            if not href:
                raise VideoNoReconocido('No encontré la publicación de Facebook en ese código.')
            return analizar_foto(href)
        limpio = f'https://www.facebook.com{u.path}'
        claves = [k for k in ('fbid', 'story_fbid', 'id', 'set') if q.get(k)]
        if claves:
            limpio += '?' + '&'.join(f'{k}={quote(q[k][0], safe="")}' for k in claves)
        if not (claves or any(p in ('posts', 'photos', 'photo', 'share', 'permalink.php', 'photo.php') for p in partes)):
            raise VideoNoReconocido('Ese enlace de Facebook no es de una publicación o foto.')
        return {'fuente': 'facebook', 'imagen_externa': '',
                'embed': 'https://www.facebook.com/plugins/post.php?show_text=true&width=500&href=' + quote(limpio, safe=''),
                'enlace': limpio}

    if host == 'photos.google.com' or host == 'photos.app.goo.gl':
        raise VideoNoReconocido('Google Fotos no deja mostrar sus fotos en otras páginas. Súbala a Google Drive, '
                                'compártala con «Cualquier persona con el enlace» y pegue ese enlace.')
    raise VideoNoReconocido('Se aceptan enlaces de Google Drive, Instagram y Facebook.')


# ---------------------------------------------------------------------------
# Una imagen o un documento por enlace (noticias, carrusel, sedes, documentos)
# ---------------------------------------------------------------------------

_URL_SEGURA = re.compile(r"^https://[A-Za-z0-9._~:/?#\[\]@!$&*+,;=%-]+$")


def imagen_desde_enlace(texto):
    """La dirección de una imagen que se pueda mostrar sola (portada, foto de sede…).

    Google Drive se convierte en su miniatura grande; también vale el enlace
    directo a una imagen (https://…/foto.jpg). Instagram y Facebook no sirven aquí:
    sus fotos caducan a los pocos días.
    """
    texto = (texto or '').strip()
    if not texto:
        raise VideoNoReconocido('Pegue el enlace de la imagen.')
    if '<' in texto:
        texto = _del_iframe(texto)
    if not re.match(r'^https?://', texto, re.I):
        texto = 'https://' + texto.lstrip('/')
    host = (urlparse(texto).hostname or '').lower()
    if host.endswith('drive.google.com'):
        return analizar_foto(texto)['imagen_externa']
    if any(host.endswith(h) for h in ('instagram.com', 'facebook.com', 'fbcdn.net', 'cdninstagram.com', 'fb.com')):
        raise VideoNoReconocido('Las fotos de Instagram y Facebook dejan de verse a los pocos días. Súbala aquí o '
                                'póngala en Google Drive y pegue ese enlace. (En la Galería sí se puede pegar la publicación.)')
    if host in ('photos.google.com', 'photos.app.goo.gl'):
        raise VideoNoReconocido('Google Fotos no deja mostrar sus fotos en otras páginas. Súbala a Google Drive, '
                                'compártala con «Cualquier persona con el enlace» y pegue ese enlace.')
    texto = re.sub(r'^http://', 'https://', texto, flags=re.I)
    if not _URL_SEGURA.match(texto) or not re.search(r'\.(jpe?g|png|webp|gif)(\?|$)', texto, re.I):
        raise VideoNoReconocido('Pegue un enlace de Google Drive o el enlace directo de una imagen (que termine en .jpg, .png o .webp).')
    return texto


def documento_desde_enlace(texto):
    """Enlace a un documento guardado en otra parte (Drive, OneDrive, Dropbox, la página de la Secretaría…)."""
    texto = (texto or '').strip()
    if not re.match(r'^https?://', texto, re.I):
        texto = 'https://' + texto.lstrip('/')
    texto = re.sub(r'^http://', 'https://', texto, flags=re.I)
    if not _URL_SEGURA.match(texto) or not urlparse(texto).hostname or '.' not in urlparse(texto).hostname:
        raise VideoNoReconocido('Ese enlace no es válido. Cópielo completo desde el navegador (empieza por https://).')
    return texto
