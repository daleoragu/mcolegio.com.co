# notas/middleware.py
import logging

from .models import Colegio

logger = logging.getLogger('mcolegio.colegio')

class ColegioMiddleware:
    """
    Middleware que identifica el colegio activo basándose en el subdominio.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # --- ¡ESTA ES LA CORRECCIÓN CLAVE! ---
        # Ahora solo ignoramos el panel de SUPER-ADMIN, permitiendo que
        # nuestras vistas personalizadas en /admin/ funcionen correctamente.
        if request.path.startswith('/super-admin/'):
            request.colegio = None
            return self.get_response(request)

        host = request.get_host().split(':')[0].lower()
        
        # Define tu dominio principal.
        # Asegúrate de que este dominio coincida con el tuyo en producción.
        main_domain = 'mcolegio.com.co'
        
        request.colegio = None
        
        try:
            # Lógica para producción (ej: colegio-x.mcolegio.com.co)
            if host.endswith(main_domain) and host != main_domain and host != f'www.{main_domain}':
                # Extrae el 'slug' del subdominio.
                slug = host.replace(f'.{main_domain}', '')
                request.colegio = Colegio.objects.get(slug=slug)
            
            # Lógica para desarrollo en localhost (ej: colegio-bilingue-san-sebastian.localhost)
            elif host.endswith('.localhost'):
                slug = host.split('.')[0]
                request.colegio = Colegio.objects.get(slug=slug)

        except Colegio.DoesNotExist:
            # Subdominio sin colegio con ese slug en la base: la página sale
            # como la portada general. Se deja rastro, porque eso es justo lo
            # que se ve cuando «no me deja entrar a un colegio».
            logger.warning('No hay colegio con el subdominio de %s (¿slug mal escrito o base '
                           'distinta?). La página se muestra sin colegio.', host)
        except Exception:
            # Cualquier otro error (base caída, migración pendiente…) tampoco
            # tumba el sitio, pero ya no se pierde: queda en el log con todo
            # el detalle para poder arreglarlo.
            logger.exception('Error identificando el colegio para %s', host)
        
        # ¿Administra el usuario ESTE colegio? Se calcula una vez y queda en
        # request.user, así cualquier vista o plantilla lo consulta sin repetir
        # la búsqueda (ver notas/permisos.py).
        try:
            usuario = getattr(request, 'user', None)
            if usuario is not None and usuario.is_authenticated:
                from .permisos import es_admin_colegio
                usuario.es_admin_colegio = es_admin_colegio(usuario, request.colegio)
        except Exception:
            logger.exception('Error calculando si el usuario administra %s', host)

        response = self.get_response(request)
        return response
