# notas/recuperar_clave.py
"""Recuperar la contraseña sin depender de nadie.

1. En el portal, «¿Olvidó su contraseña?» pide el usuario (o el correo).
2. Si la persona es de ESTE colegio y tiene un correo, le llega un enlace que
   sirve una sola vez y vence (PASSWORD_RESET_TIMEOUT, una hora). El enlace
   deja de servir apenas se cambia la contraseña, porque el token de Django
   incluye el hash de la contraseña actual.
3. Los estudiantes casi nunca tienen correo propio: el enlace va entonces al
   correo del acudiente que está en la ficha.
4. Si no hay correo, el administrador del colegio le da una contraseña
   temporal desde la gestión de docentes o estudiantes.

La respuesta del formulario es siempre la misma, exista o no el usuario, para
que nadie pueda averiguar qué usuarios hay probando nombres.
"""
import secrets

from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.core.cache import cache
from django.core.mail import send_mail
from django.db.models import Q
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from .avisos_familia import correo_configurado
from .permisos import pertenece_al_colegio

INTENTOS_POR_HORA = 5


def demasiados_intentos(clave):
    """Freno sencillo contra quien manda el formulario cien veces."""
    llave = f'recuperar-clave:{clave}'
    n = cache.get(llave, 0)
    if n >= INTENTOS_POR_HORA:
        return True
    cache.set(llave, n + 1, 3600)
    return False


def correo_destino(user):
    """(correo, es_del_acudiente). El del usuario y, si es estudiante sin correo, el del acudiente."""
    propio = (user.email or '').strip()
    if propio:
        return propio, False
    estudiante = getattr(user, 'estudiante', None)
    ficha = getattr(estudiante, 'ficha', None) if estudiante else None
    acudiente = ((getattr(ficha, 'email_acudiente', '') if ficha else '') or '').strip()
    if acudiente:
        return acudiente, True
    return '', False


def buscar_usuarios(colegio, dato):
    """Usuarios activos de este colegio que coinciden con el usuario o el correo escrito."""
    dato = (dato or '').strip()
    if not dato:
        return []
    filtro = Q(username__iexact=dato)
    if '@' in dato:
        filtro |= Q(email__iexact=dato) | Q(estudiante__ficha__email_acudiente__iexact=dato)
    candidatos = User.objects.filter(filtro, is_active=True).distinct()[:10]
    # El superusuario no se recupera por aquí: él tiene su propio camino.
    return [u for u in candidatos if not u.is_superuser and pertenece_al_colegio(u, colegio)]


def enlace(request, user):
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    return request.build_absolute_uri(reverse('notas:recuperar_clave_nueva', args=[uid, token]))


def enviar_enlace(request, colegio, user):
    """Manda el correo. Devuelve True si salió."""
    correo, de_acudiente = correo_destino(user)
    if not correo or not correo_configurado():
        return False
    contexto = {
        'colegio': colegio, 'usuario': user, 'nombre': user.get_full_name() or user.username,
        'enlace': enlace(request, user), 'de_acudiente': de_acudiente,
        'minutos': getattr(settings, 'PASSWORD_RESET_TIMEOUT', 3600) // 60,
    }
    texto = render_to_string('notas/recuperar_clave/correo.txt', contexto)
    html = render_to_string('notas/recuperar_clave/correo.html', contexto)
    try:
        send_mail(f'{colegio.nombre}: recuperar contraseña', texto, settings.DEFAULT_FROM_EMAIL,
                  [correo], html_message=html, fail_silently=False)
    except Exception:
        return False
    return True


# Sin letras que se confunden (0/O, 1/l/I) para dictarla por teléfono.
_LETRAS = 'abcdefghjkmnpqrstuvwxyzABCDEFGHJKMNPQRSTUVWXYZ23456789'


def clave_temporal(largo=8):
    return ''.join(secrets.choice(_LETRAS) for _ in range(largo))


def puede_restablecer(admin, colegio, user):
    """El administrador restablece docentes y estudiantes de SU colegio; nunca a otro administrador
    ni al superusuario (salvo que quien lo haga sea el superusuario)."""
    from .models.perfiles import AdministradorColegio
    if user.is_superuser:
        return False
    if admin.is_superuser:
        return pertenece_al_colegio(user, colegio)
    if AdministradorColegio.objects.filter(user=user, activo=True).exists():
        return False
    docente = getattr(user, 'docente', None)
    estudiante = getattr(user, 'estudiante', None)
    return bool((docente and docente.colegio_id == colegio.id)
                or (estudiante and estudiante.colegio_id == colegio.id))
