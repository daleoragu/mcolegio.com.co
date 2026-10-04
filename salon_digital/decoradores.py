# salon_digital/decoradores.py
from functools import wraps

from django.contrib import messages
from django.shortcuts import redirect


def cuenta_requerida(vista):
    """Exige haber iniciado sesión y tener cuenta de Salón Digital.

    Deja la cuenta en request.cuenta para que la vista no la busque otra vez.
    """
    @wraps(vista)
    def envoltura(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(f"{'/salon_digital/entrar/'}?siguiente={request.path}")
        cuenta = getattr(request.user, 'cuenta_salon', None)
        if cuenta is None:
            return redirect('salon_digital:crear_cuenta')
        request.cuenta = cuenta
        return vista(request, *args, **kwargs)
    return envoltura


def cuenta_activa_requerida(vista):
    """Además de lo anterior, exige cuenta verificada y plan al día."""
    @wraps(vista)
    @cuenta_requerida
    def envoltura(request, *args, **kwargs):
        if not request.cuenta.activa:
            messages.warning(request, _mensaje(request.cuenta))
            return redirect('salon_digital:mi_cuenta')
        return vista(request, *args, **kwargs)
    return envoltura


def _mensaje(cuenta):
    if cuenta.estado == 'sin_enviar':
        return ('Para publicar necesitas verificar que eres docente. '
                'Sube tu constancia laboral, diploma o carné.')
    if cuenta.estado == 'pendiente':
        return 'Tu documento está en revisión. Te avisamos apenas quede aprobado.'
    if cuenta.estado == 'rechazada':
        return f'Tu verificación fue rechazada: {cuenta.nota_revision or "sin observación"}'
    if cuenta.vencida:
        return 'Tu plan venció. Renuévalo para seguir publicando; tus páginas y resultados siguen ahí.'
    return 'Tu cuenta no está activa.'


def staff_requerido(vista):
    @wraps(vista)
    def envoltura(request, *args, **kwargs):
        if not (request.user.is_authenticated and request.user.is_staff):
            return redirect('salon_digital:entrar')
        return vista(request, *args, **kwargs)
    return envoltura
