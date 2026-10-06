# notas/views/impersonation_views.py
"""«Ver como»: el administrador entra a la plataforma como un docente o estudiante.

Reglas, porque antes no había ninguna sobre A QUIÉN se podía suplantar y
bastaba cambiar el número en la dirección para entrar como cualquiera, incluso
como un superusuario o como alguien de otro colegio:

  * Solo se suplanta a docentes o estudiantes DEL COLEGIO en que se está.
  * Nunca a un superusuario, a un usuario del personal, a otro administrador
    ni a uno mismo.
  * Solo por POST (botón), nunca por un enlace: así otra página no puede
    disparar la suplantación con una imagen o un enlace escondido.
  * Queda registrado en el log quién suplantó a quién.
"""
import logging

from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.shortcuts import redirect
from django.views.decorators.http import require_POST

from ..permisos import es_admin_colegio, es_admin_usuario

logger = logging.getLogger('mcolegio.seguridad')

def es_personal_admin(user):
    """Superusuario o administrador del colegio de la dirección (ver notas/permisos.py)."""
    return es_admin_usuario(user)


def es_administrador_en_alguna_parte(user):
    """¿Administra algún colegio? A esos no se les suplanta nunca."""
    return (user.is_superuser or user.is_staff
            or user.administraciones.filter(activo=True).exists())


def motivo_para_no_suplantar(admin, objetivo, colegio):
    """None si se puede suplantar; si no, el motivo en palabras."""
    if objetivo is None:
        return 'Ese usuario no existe.'
    if objetivo.pk == admin.pk:
        return 'No puede suplantarse a sí mismo.'
    if not objetivo.is_active:
        return 'Ese usuario está desactivado.'
    if es_administrador_en_alguna_parte(objetivo):
        return 'No se puede suplantar a un administrador.'
    if colegio is None:
        return 'No se identificó el colegio.'
    docente = getattr(objetivo, 'docente', None)
    estudiante = getattr(objetivo, 'estudiante', None)
    if not ((docente and docente.colegio_id == colegio.id)
            or (estudiante and estudiante.colegio_id == colegio.id)):
        return 'Ese usuario no pertenece a este colegio.'
    return None


@require_POST
@user_passes_test(es_personal_admin)
def iniciar_suplantacion(request, user_id):
    """Entra como el usuario objetivo y guarda quién era el administrador."""
    if 'original_user_id' in request.session:
        messages.error(request, 'Ya está viendo la plataforma como otro usuario. Vuelva primero a su cuenta.')
        return redirect('notas:dashboard')

    objetivo = User.objects.filter(id=user_id).select_related('docente', 'estudiante').first()
    motivo = motivo_para_no_suplantar(request.user, objetivo, getattr(request, 'colegio', None))
    if motivo:
        logger.warning('Suplantación rechazada: %s (id=%s) intentó entrar como user_id=%s en %s. Motivo: %s',
                       request.user.username, request.user.id, user_id,
                       getattr(getattr(request, 'colegio', None), 'slug', '?'), motivo)
        messages.error(request, motivo)
        return redirect(request.META.get('HTTP_REFERER') or 'notas:dashboard')

    original_user_id = request.user.id
    logger.info('Suplantación: %s (id=%s) entra como %s (id=%s) en %s',
                request.user.username, original_user_id, objetivo.username, objetivo.id,
                request.colegio.slug)
    # El login va PRIMERO porque limpia la sesión; después se guarda el original.
    login(request, objetivo, backend='django.contrib.auth.backends.ModelBackend')
    request.session['original_user_id'] = original_user_id
    messages.success(request, f'Ahora está viendo la plataforma como {objetivo.get_full_name() or objetivo.username}.')
    return redirect('notas:dashboard')


@login_required
def detener_suplantacion(request):
    """Vuelve a la cuenta del administrador original."""
    original_user_id = request.session.get('original_user_id')
    if not original_user_id:
        messages.warning(request, 'No estaba viendo la plataforma como otro usuario.')
        return redirect('notas:dashboard')

    admin_user = User.objects.filter(id=original_user_id).first()
    if admin_user is None or not es_admin_colegio(admin_user, getattr(request, 'colegio', None)):
        # La cuenta original ya no es administradora (o no existe): por
        # seguridad se cierra todo en vez de devolverle un acceso que ya no tiene.
        logger.warning('Fin de suplantación con cuenta original inválida (id=%s). Se cierra la sesión.',
                       original_user_id)
        logout(request)
        messages.error(request, 'Su cuenta de administrador ya no tiene permisos. Inicie sesión de nuevo.')
        return redirect('notas:portal')

    login(request, admin_user, backend='django.contrib.auth.backends.ModelBackend')
    logger.info('Fin de suplantación: %s (id=%s) volvió a su cuenta.', admin_user.username, admin_user.id)
    messages.info(request, 'Volvió a su cuenta de administrador.')
    return redirect('notas:admin_dashboard')
