# salon_digital/social.py
"""Entrar o crear la cuenta con Google o con Facebook (OAuth 2.0, sin librerías extra).

Se activa con variables de entorno (en DigitalOcean, nunca en el código):
    GOOGLE_OAUTH_CLIENT_ID, GOOGLE_OAUTH_CLIENT_SECRET
    FACEBOOK_APP_ID, FACEBOOK_APP_SECRET
Sin ellas, el botón de ese proveedor no aparece.

Direcciones de regreso que hay que registrar en cada proveedor:
    https://mcolegio.com.co/salon_digital/auth/google/vuelta/
    https://mcolegio.com.co/salon_digital/auth/facebook/vuelta/
"""
import os
import re
import secrets

import requests
from django.contrib.auth.models import User
from django.urls import reverse
from unidecode import unidecode

TIEMPO = 10
CLAVE_SESION = 'salon_oauth'
VERSION_FACEBOOK = 'v19.0'

PROVEEDORES = {
    'google': {
        'nombre': 'Google',
        'id': 'GOOGLE_OAUTH_CLIENT_ID',
        'secreto': 'GOOGLE_OAUTH_CLIENT_SECRET',
        'autorizar': 'https://accounts.google.com/o/oauth2/v2/auth',
        'token': 'https://oauth2.googleapis.com/token',
        'perfil': 'https://openidconnect.googleapis.com/v1/userinfo',
        'alcance': 'openid email profile',
    },
    'facebook': {
        'nombre': 'Facebook',
        'id': 'FACEBOOK_APP_ID',
        'secreto': 'FACEBOOK_APP_SECRET',
        'autorizar': f'https://www.facebook.com/{VERSION_FACEBOOK}/dialog/oauth',
        'token': f'https://graph.facebook.com/{VERSION_FACEBOOK}/oauth/access_token',
        'perfil': 'https://graph.facebook.com/me',
        'alcance': 'email,public_profile',
    },
}


class ErrorSocial(Exception):
    """Algo salió mal con el proveedor; el mensaje es para mostrárselo al docente."""


def credenciales(proveedor):
    p = PROVEEDORES.get(proveedor)
    if not p:
        return None, None
    return os.getenv(p['id']), os.getenv(p['secreto'])


def disponibles():
    """[(clave, nombre)] de los proveedores configurados."""
    return [(k, p['nombre']) for k, p in PROVEEDORES.items() if all(credenciales(k))]


def url_regreso(request, proveedor):
    dominio = os.getenv('SALON_DOMINIO_PUBLICO')
    ruta = reverse('salon_digital:social_vuelta', args=[proveedor])
    if dominio:
        return f'https://{dominio}{ruta}'
    return request.build_absolute_uri(ruta)


def url_autorizar(request, proveedor, siguiente=''):
    cliente, _ = credenciales(proveedor)
    if not cliente:
        raise ErrorSocial('Esa forma de entrar todavía no está disponible.')
    estado = secrets.token_urlsafe(24)
    request.session[CLAVE_SESION] = {'estado': estado, 'proveedor': proveedor, 'siguiente': siguiente}
    p = PROVEEDORES[proveedor]
    params = {'client_id': cliente, 'redirect_uri': url_regreso(request, proveedor), 'state': estado,
              'response_type': 'code', 'scope': p['alcance']}
    if proveedor == 'google':
        params['prompt'] = 'select_account'
    return requests.Request('GET', p['autorizar'], params=params).prepare().url


def datos_del_regreso(request, proveedor):
    """Valida el regreso y devuelve {'correo', 'nombre', 'nombres', 'apellidos', 'verificado'}."""
    guardado = request.session.pop(CLAVE_SESION, None) or {}
    if not guardado or guardado.get('proveedor') != proveedor or \
            not secrets.compare_digest(str(guardado.get('estado', '')), request.GET.get('state', '')):
        raise ErrorSocial('La sesión venció. Intente otra vez.')
    if request.GET.get('error'):
        raise ErrorSocial('No se completó la entrada: usted canceló o no dio permiso.')
    codigo = request.GET.get('code')
    if not codigo:
        raise ErrorSocial('El proveedor no devolvió el permiso. Intente otra vez.')
    cliente, secreto = credenciales(proveedor)
    p = PROVEEDORES[proveedor]
    regreso = url_regreso(request, proveedor)
    try:
        if proveedor == 'google':
            r = requests.post(p['token'], data={'code': codigo, 'client_id': cliente, 'client_secret': secreto,
                                                'redirect_uri': regreso, 'grant_type': 'authorization_code'},
                              timeout=TIEMPO)
            r.raise_for_status()
            token = r.json()['access_token']
            r = requests.get(p['perfil'], headers={'Authorization': f'Bearer {token}'}, timeout=TIEMPO)
            r.raise_for_status()
            d = r.json()
            datos = {'correo': d.get('email', ''), 'nombre': d.get('name', ''), 'nombres': d.get('given_name', ''),
                     'apellidos': d.get('family_name', ''), 'verificado': bool(d.get('email_verified'))}
        else:
            r = requests.get(p['token'], params={'client_id': cliente, 'client_secret': secreto,
                                                 'redirect_uri': regreso, 'code': codigo}, timeout=TIEMPO)
            r.raise_for_status()
            token = r.json()['access_token']
            r = requests.get(p['perfil'], params={'fields': 'id,name,email,first_name,last_name',
                                                  'access_token': token}, timeout=TIEMPO)
            r.raise_for_status()
            d = r.json()
            # Facebook solo entrega correos confirmados.
            datos = {'correo': d.get('email', ''), 'nombre': d.get('name', ''), 'nombres': d.get('first_name', ''),
                     'apellidos': d.get('last_name', ''), 'verificado': bool(d.get('email'))}
    except (requests.RequestException, KeyError, ValueError):
        raise ErrorSocial(f'No pudimos comunicarnos con {p["nombre"]}. Intente de nuevo en un momento.')
    datos['correo'] = (datos['correo'] or '').strip().lower()
    if not datos['correo']:
        raise ErrorSocial(f'{p["nombre"]} no compartió su correo. Cree la cuenta con su correo electrónico.')
    if not datos['verificado']:
        raise ErrorSocial('Ese correo no está verificado en el proveedor. Cree la cuenta con su correo electrónico.')
    datos['siguiente'] = guardado.get('siguiente', '')
    return datos


def usuario_para(datos):
    """El usuario con ese correo, o uno nuevo. (usuario, nuevo)."""
    existente = User.objects.filter(email__iexact=datos['correo']).order_by('id').first()
    if existente is not None:
        if existente.is_staff or existente.is_superuser:
            raise ErrorSocial('Por seguridad, las cuentas de administración entran con usuario y contraseña.')
        if not existente.is_active:
            raise ErrorSocial('Esa cuenta está desactivada.')
        return existente, False
    base = re.sub(r'[^a-z0-9._-]', '', unidecode(datos['correo'].split('@')[0].lower()))[:24] or 'docente'
    username, n = base, 2
    while User.objects.filter(username=username).exists():
        username, n = f'{base}{n}', n + 1
    u = User(username=username, email=datos['correo'],
             first_name=(datos.get('nombres') or datos.get('nombre') or '')[:150],
             last_name=(datos.get('apellidos') or '')[:150])
    u.set_unusable_password()
    u.save()
    return u, True


def sugerir_usuario(datos_o_usuario):
    """Un nombre de usuario para el enlace público (mcolegio.com.co/p/<este>/)."""
    from .models import Cuenta
    if isinstance(datos_o_usuario, User):
        texto = datos_o_usuario.get_full_name() or datos_o_usuario.username
    else:
        texto = datos_o_usuario.get('nombre') or datos_o_usuario.get('correo', '').split('@')[0]
    base = re.sub(r'[^a-z0-9-]', '', unidecode(texto.lower()).replace(' ', ''))[:30] or 'docente'
    if len(base) < 3:
        base = f'{base}docente'
    slug, n = base, 2
    while Cuenta.objects.filter(slug=slug).exists():
        slug, n = f'{base}{n}', n + 1
    return slug
