# notas/decorators.py
from django.core.exceptions import PermissionDenied
from django.contrib.auth.decorators import user_passes_test
from .permisos import es_admin_usuario

def es_administrador_de_colegio(user):
    """
    Verifica si un usuario es superusuario o pertenece al grupo 'Administrador de colegio'.
    Si el usuario no está autenticado o no cumple la condición, se lanza un error
    de Permiso Denegado, que por defecto resulta en una página de error 403 (Forbidden).
    """
    if not user.is_authenticated:
        raise PermissionDenied

    # Comprueba si es superusuario o si pertenece al grupo requerido.
    if es_admin_usuario(user):
        return True
    
    # Si no cumple ninguna de las condiciones, deniega el acceso.
    raise PermissionDenied

# Este es el decorador que usarás en tus vistas.
# Define la URL a la que se redirigirá si el usuario no está logueado.
admin_colegio_required = user_passes_test(es_administrador_de_colegio, login_url='/admin/login/')
