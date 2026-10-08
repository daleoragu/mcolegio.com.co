# notas/enlaces.py
"""Enlaces que salen por correo.

Detrás del proxy de DigitalOcean la petición llega a Django como http, así que
build_absolute_uri() arma «http://…». Un enlace con un token (recuperar la
contraseña, el descargo del acudiente, la solicitud de prematrícula) no debe
viajar sin cifrar ni en el primer clic: fuera del modo de desarrollo se fuerza https.
"""
from django.conf import settings


def enlace_absoluto(request, ruta='/'):
    url = request.build_absolute_uri(ruta)
    if not settings.DEBUG and url.startswith('http://'):
        host = request.get_host().split(':')[0]
        if host not in ('localhost', '127.0.0.1') and not host.endswith('.localhost'):
            url = 'https://' + url[len('http://'):]
    return url
