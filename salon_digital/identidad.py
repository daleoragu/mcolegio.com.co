# salon_digital/identidad.py
"""Quién está presentando la actividad, cuando el docente usa grupos."""

CLAVE_SESION = 'salon_identidad'


def guardar(request, integrante, recordar=False):
    """Deja al estudiante identificado. Con «recordarme», la sesión dura 90 días en ese celular."""
    request.session[CLAVE_SESION] = {
        'integrante': integrante.pk,
        'grupo': integrante.grupo_id,
        'nombre': integrante.completo,
        'grupo_nombre': integrante.grupo.nombre,
    }
    usuario = getattr(request, 'user', None)
    if recordar and not (usuario and usuario.is_authenticated):     # no se alarga la sesión de un docente
        request.session.set_expiry(60 * 60 * 24 * 90)
    request.session.modified = True


def acceso_valido(request, integrante, secreto):
    """¿Puede entrar? Según el grupo: con su contraseña, con su PIN o solo con el nombre.
    Máximo 8 intentos fallidos cada 15 minutos por estudiante y equipo."""
    modo = integrante.grupo.ingreso
    if modo == 'nombre':
        return True, ''
    if modo == 'clave' and not integrante.clave:
        modo = 'pin'               # todavía no tiene contraseña: entra con su PIN de siempre
    from django.core.cache import cache
    ip = request.META.get('HTTP_X_FORWARDED_FOR', '').split(',')[0].strip() or request.META.get('REMOTE_ADDR', '')
    llave = f'salon-pin:{integrante.pk}:{ip}'
    intentos = cache.get(llave) or 0
    if intentos >= 8:
        return False, 'Demasiados intentos. Espere 15 minutos o pídale a su profe que le restablezca la contraseña.'
    secreto = (secreto or '').strip()
    if (integrante.clave_correcta(secreto) if modo == 'clave' else secreto == integrante.pin_chat):
        cache.delete(llave)
        return True, ''
    cache.set(llave, intentos + 1, 15 * 60)
    if modo == 'clave':
        return False, 'Esa contraseña no es. Revise su tarjeta; si la olvidó, pídale a su profe que la restablezca.'
    return False, 'Ese PIN no es el suyo. Revise su tarjeta o pídaselo a su docente.'


def pin_valido(request, integrante, pin):
    """(Nombre antiguo) Igual que acceso_valido."""
    return acceso_valido(request, integrante, pin)


def leer(request):
    return request.session.get(CLAVE_SESION) or None


def olvidar(request):
    request.session.pop(CLAVE_SESION, None)
    request.session.modified = True


def integrante_de(request, pagina):
    """El integrante guardado, solo si pertenece a quien publicó la página."""
    from .models import Integrante

    datos = leer(request)
    if not datos:
        return None
    integrante = Integrante.objects.filter(
        pk=datos.get('integrante'), activo=True,
        grupo__propietario=pagina.propietario,
    ).select_related('grupo').first()

    permitidos = pagina.grupos.all()
    if integrante and permitidos.exists() and integrante.grupo_id not in {g.pk for g in permitidos}:
        return None
    return integrante
