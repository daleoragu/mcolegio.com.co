# notas/views/recuperar_clave_views.py
"""«¿Olvidó su contraseña?» y la contraseña temporal que da el administrador.
La lógica está en notas/recuperar_clave.py."""
from django.contrib import messages
from django.contrib.auth import password_validation
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import SetPasswordForm
from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.http import HttpResponseForbidden, HttpResponseNotFound
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.encoding import force_str
from django.utils.http import url_has_allowed_host_and_scheme, urlsafe_base64_decode
from django.views.decorators.http import require_POST

from .. import recuperar_clave as rc
from ..avisos_familia import correo_configurado
from ..permisos import es_admin, pertenece_al_colegio


class FormNuevaClave(SetPasswordForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['new_password1'].label = 'Nueva contraseña'
        self.fields['new_password2'].label = 'Escríbala otra vez'
        self.fields['new_password1'].help_text = password_validation.password_validators_help_text_html()
        for campo in self.fields.values():
            campo.widget.attrs['class'] = 'form-control'


def _ip(request):
    """La IP del visitante. Detrás de DigitalOcean la pone el proxy en DO-Connecting-IP; si no,
    la ÚLTIMA de X-Forwarded-For (la que agregó el proxy; las primeras las puede inventar cualquiera)."""
    do_ip = request.META.get('HTTP_DO_CONNECTING_IP', '').strip()
    if do_ip:
        return do_ip
    reenviadas = [x.strip() for x in request.META.get('HTTP_X_FORWARDED_FOR', '').split(',') if x.strip()]
    return reenviadas[-1] if reenviadas else request.META.get('REMOTE_ADDR', '')


def pedir_enlace(request):
    colegio = getattr(request, 'colegio', None)
    if colegio is None:
        return HttpResponseNotFound('<h1>Colegio no configurado</h1>')
    enviado = False
    dato = ''
    if request.method == 'POST':
        dato = request.POST.get('dato', '').strip()
        if not dato:
            messages.error(request, 'Escriba su usuario o su correo.')
        elif rc.demasiados_intentos(f'ip:{_ip(request)}', rc.PEDIDOS_POR_IP_HORA):
            messages.error(request, 'Hizo muchos intentos seguidos. Espere una hora y vuelva a probar.')
        else:
            for user in rc.buscar_usuarios(colegio, dato):
                rc.enviar_enlace(request, colegio, user)
            enviado = True     # misma respuesta exista o no el usuario
    return render(request, 'notas/recuperar_clave/pedir.html', {
        'colegio': colegio, 'enviado': enviado, 'dato': dato, 'correo_listo': correo_configurado()})


def nueva_clave(request, uidb64, token):
    colegio = getattr(request, 'colegio', None)
    if colegio is None:
        return HttpResponseNotFound('<h1>Colegio no configurado</h1>')
    try:
        user = User.objects.get(pk=force_str(urlsafe_base64_decode(uidb64)), is_active=True)
    except (User.DoesNotExist, ValueError, TypeError, OverflowError):
        user = None
    valido = (user is not None and not user.is_superuser and pertenece_al_colegio(user, colegio)
              and default_token_generator.check_token(user, token))
    if not valido:
        return render(request, 'notas/recuperar_clave/nueva.html', {'colegio': colegio, 'valido': False})
    if request.method == 'POST':
        form = FormNuevaClave(user, request.POST)
        if form.is_valid():
            form.save()
            return render(request, 'notas/recuperar_clave/nueva.html',
                          {'colegio': colegio, 'valido': True, 'listo': True, 'usuario': user})
    else:
        form = FormNuevaClave(user)
    return render(request, 'notas/recuperar_clave/nueva.html',
                  {'colegio': colegio, 'valido': True, 'form': form, 'usuario': user})


@login_required
@require_POST
def restablecer_por_admin(request, user_id):
    """Le pone una contraseña temporal a un docente o estudiante y se la muestra al administrador."""
    colegio = getattr(request, 'colegio', None)
    if colegio is None or not es_admin(request):
        return HttpResponseForbidden('Solo el administrador del colegio.')
    user = get_object_or_404(User, id=user_id)
    if not rc.puede_restablecer(request.user, colegio, user):
        return HttpResponseForbidden('No puede restablecer la contraseña de este usuario.')
    temporal = rc.clave_temporal()
    user.set_password(temporal)
    user.save(update_fields=['password'])
    volver = request.POST.get('volver', '')
    if not url_has_allowed_host_and_scheme(volver, allowed_hosts={request.get_host()}):
        volver = ''
    correo, de_acudiente = rc.correo_destino(user)
    return render(request, 'notas/recuperar_clave/temporal.html', {
        'usuario': user, 'temporal': temporal, 'volver': volver, 'correo': correo,
        'de_acudiente': de_acudiente, 'page_title': 'Contraseña temporal'})
