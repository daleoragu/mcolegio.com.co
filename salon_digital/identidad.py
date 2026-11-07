# salon_digital/identidad.py
"""Quién está presentando la actividad, cuando el docente usa grupos."""

CLAVE_SESION = 'salon_identidad'


def guardar(request, integrante):
    request.session[CLAVE_SESION] = {
        'integrante': integrante.pk,
        'grupo': integrante.grupo_id,
        'nombre': integrante.completo,
        'grupo_nombre': integrante.grupo.nombre,
    }
    request.session.modified = True


def pin_valido(request, integrante, pin):
    """¿Escribió bien su PIN? (solo si el grupo lo pide). Máximo 8 intentos cada 15 minutos por estudiante y equipo."""
    if not integrante.grupo.pedir_pin:
        return True, ''
    from django.core.cache import cache
    ip = request.META.get('HTTP_X_FORWARDED_FOR', '').split(',')[0].strip() or request.META.get('REMOTE_ADDR', '')
    llave = f'salon-pin:{integrante.pk}:{ip}'
    intentos = cache.get(llave) or 0
    if intentos >= 8:
        return False, 'Demasiados intentos. Espere 15 minutos o pídale a su docente un PIN nuevo.'
    if (pin or '').strip() == integrante.pin_chat:
        cache.delete(llave)
        return True, ''
    cache.set(llave, intentos + 1, 15 * 60)
    return False, 'Ese PIN no es el suyo. Revise su tarjeta o pídaselo a su docente.'


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
