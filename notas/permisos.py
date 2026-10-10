# notas/permisos.py
"""Quién manda en cada colegio. La única regla, en un solo lugar.

Tres roles:
  * Superusuario (el dueño de la plataforma): entra a todos los colegios y
    puede todo en todos.
  * Administrador del colegio (rector, coordinador, secretaría): puede todo lo
    que puede el superusuario, pero SOLO en el colegio que tiene a cargo
    (modelo AdministradorColegio). En otro colegio no es nadie.
  * Docente: como siempre.

Cómo se usa:
  * En una vista:            if es_admin(request): …
  * Como decorador:          @admin_requerido
  * En user_passes_test(f):  def f(user): return es_admin_usuario(user)
  * En una plantilla:        {% if user.es_admin_colegio %} …

El middleware del colegio (notas/middleware.py) calcula una vez por petición
si el usuario es administrador del colegio de la dirección y lo deja en
request.user.es_admin_colegio. Por eso user_passes_test, que solo recibe el
usuario, también respeta el colegio.
"""
from functools import wraps

from django.contrib.auth.views import redirect_to_login
from django.http import HttpResponseForbidden


def es_admin_colegio(user, colegio):
    """¿Este usuario administra este colegio? (el superusuario, siempre)."""
    if user is None or not getattr(user, 'is_authenticated', False) or not user.is_active:
        return False
    if user.is_superuser:
        return True
    if colegio is None:
        return False
    from .models.perfiles import AdministradorColegio
    return AdministradorColegio.objects.filter(user=user, colegio=colegio, activo=True).exists()


def es_admin_usuario(user):
    """Para user_passes_test: lo que dejó calculado el middleware."""
    if user is None or not getattr(user, 'is_authenticated', False):
        return False
    return bool(user.is_superuser or getattr(user, 'es_admin_colegio', False))


def es_admin(request):
    return es_admin_usuario(getattr(request, 'user', None))


def admin_requerido(vista):
    """La vista es solo para el administrador del colegio (o el superusuario)."""
    @wraps(vista)
    def envoltura(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect_to_login(request.get_full_path())
        if not es_admin(request):
            return HttpResponseForbidden('Esta sección es para la administración del colegio.')
        return vista(request, *args, **kwargs)
    return envoltura


def pertenece_al_colegio(user, colegio):
    """¿Puede iniciar sesión en este colegio? Docente, estudiante o administrador de él."""
    if colegio is None or not user.is_active:
        return False
    if user.is_superuser:
        return True
    docente = getattr(user, 'docente', None)
    estudiante = getattr(user, 'estudiante', None)
    from .models.perfiles import AdministradorColegio
    return bool((docente and docente.colegio_id == colegio.id)
                or (estudiante and estudiante.colegio_id == colegio.id)
                or AdministradorColegio.objects.filter(user=user, colegio=colegio, activo=True).exists())


def es_docente_usuario(user):
    """¿Es docente? Por el grupo «Docentes» o por tener perfil de Docente.

    El grupo se pone al importar o crear docentes desde la plataforma, pero un
    docente creado por otro camino (p. ej. el admin de Django) puede no tenerlo;
    con el perfil basta para que le salgan sus menús y sus herramientas.
    """
    if user is None or not getattr(user, 'is_authenticated', False):
        return False
    if user.groups.filter(name='Docentes').exists():
        return True
    from .models.perfiles import Docente
    return Docente.objects.filter(user=user).exists()
