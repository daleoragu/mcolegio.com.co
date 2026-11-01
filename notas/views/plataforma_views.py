"""Pantallas del dueño de la plataforma (superusuario), por encima de los colegios."""
from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import get_object_or_404, redirect, render

from ..models import Colegio
from ..modulos import MODULOS, PLANES, activos


def _es_dueno(user):
    return user.is_authenticated and user.is_superuser


@user_passes_test(_es_dueno, login_url='/super-admin/login/')
def modulos_colegios(request):
    """Qué módulos tiene activos cada colegio (lo que contrató)."""
    if request.method == 'POST':
        colegio = get_object_or_404(Colegio, pk=request.POST.get('colegio'))
        plan = request.POST.get('plan')
        if plan in PLANES:
            elegidos = list(PLANES[plan][1])
            texto = f'plan {PLANES[plan][0]}'
        else:
            elegidos = [m for m in MODULOS if request.POST.get(f'mod_{m}')]
            texto = 'módulos guardados'
        colegio.modulos_activos = elegidos
        colegio.save(update_fields=['modulos_activos'])
        messages.success(request, f'{colegio.nombre}: {texto} ({len(elegidos)} de {len(MODULOS)} módulos activos).')
        return redirect(request.path + f'#colegio-{colegio.pk}')
    filas = [{'c': c, 'activos': activos(c)} for c in Colegio.objects.order_by('nombre')]
    return render(request, 'notas/plataforma/modulos.html', {
        'filas': filas, 'modulos': MODULOS, 'planes': PLANES})


@user_passes_test(_es_dueno, login_url='/super-admin/login/')
def probar_correo(request):
    """Manda un correo de prueba en el momento y muestra el error exacto si no sale.

    Muestra cómo quedó la configuración sin enseñar la contraseña (solo cuántas letras tiene y si
    trae espacios, que es el error más común al pegar la contraseña de aplicación de Gmail)."""
    import socket
    import time
    from django.conf import settings
    from django.core.mail import get_connection
    from .. import mensajeria

    clave = getattr(settings, 'EMAIL_HOST_PASSWORD', '') or ''
    config = {
        'host': getattr(settings, 'EMAIL_HOST', ''), 'puerto': getattr(settings, 'EMAIL_PORT', ''),
        'tls': getattr(settings, 'EMAIL_USE_TLS', False), 'usuario': getattr(settings, 'EMAIL_HOST_USER', ''),
        'remitente': getattr(settings, 'DEFAULT_FROM_EMAIL', ''), 'clave_letras': len(clave),
        'clave_espacios': ' ' in clave, 'activo': mensajeria.correo_configurado(),
        'backend': getattr(settings, 'EMAIL_BACKEND', ''),
    }
    pasos, error, destino = [], '', ''
    colegios = Colegio.objects.order_by('nombre')
    if request.method == 'POST':
        destino = (request.POST.get('destino') or '').strip()[:200]
        colegio = colegios.filter(pk=request.POST.get('colegio') or 0).first()
        if '@' not in destino:
            error = 'Escriba un correo de destino.'
        elif not config['activo']:
            error = 'El correo no está configurado: falta EMAIL_HOST en DigitalOcean (o la app no se ha vuelto a publicar).'
        else:
            inicio = time.monotonic()
            try:
                socket.create_connection((config['host'], int(config['puerto'])), timeout=10).close()
                pasos.append(f'Conexión con {config["host"]}:{config["puerto"]}: bien '
                             f'({round((time.monotonic() - inicio) * 1000)} ms).')
                conexion = get_connection(fail_silently=False, timeout=20)
                conexion.open()
                pasos.append('Usuario y contraseña: aceptados.')
                m = mensajeria.mensaje(colegio, 'Prueba de correo de mcolegio',
                                       'Este es un correo de prueba de la plataforma mcolegio. Si le llegó, '
                                       'el envío de correos está funcionando.', [destino])
                conexion.send_messages([m])
                conexion.close()
                pasos.append(f'Correo entregado al servidor, de «{m.from_email}» para {destino}. Si no aparece en '
                             'unos minutos, revise spam o los filtros del correo institucional.')
            except Exception as e:
                error = mensajeria.explicar_error(e)
    return render(request, 'notas/plataforma/probar_correo.html', {
        'config': config, 'pasos': pasos, 'error': error, 'destino': destino or request.user.email,
        'colegios': colegios})
