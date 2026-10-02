# config/urls.py
# Este es el archivo de URLs principal de tu proyecto.

from django.contrib import admin
from django.urls import path, include
from django.views.generic.base import RedirectView # <-- 1. IMPORTACIÓN AÑADIDA

# --- Para servir archivos en modo de desarrollo (opcional) ---
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # 1. RUTA PARA EL PANEL DE ADMINISTRACIÓN NATIVO DE DJANGO
    path('super-admin/', admin.site.urls),

    # 2. NUEVA REDIRECCIÓN
    #    Si alguien va a /admin/, lo redirige a la vista correcta del panel de administrador.
    path('admin/', RedirectView.as_view(pattern_name='notas:admin_dashboard', permanent=False)),

    # 3. RUTA DEL NUEVO MÓDULO DE ELECCIONES
    #    Todo lo que empiece por /elecciones2026/ será manejado por tu nueva app.
    path('elecciones2026/', include('elecciones.urls', namespace='elecciones')),

    # 4. MÓDULO DE PRUEBAS
    #    /pruebas/  -> panel, resultados y pruebas del banco de preguntas
    #    /p/        -> páginas HTML publicadas por los docentes
    path('pruebas/', include('pruebas.urls', namespace='pruebas')),
    path('p/', include('pruebas.urls_publicas', namespace='paginas')),

    # 5. RUTAS DE TU APLICACIÓN "NOTAS"
    #    Esta línea incluye todas las URLs de tu archivo 'notas/urls.py'.
    path('', include('notas.urls', namespace='notas')),
]

# --- Personalización del Título y Encabezado del Admin de Django (Opcional) ---
admin.site.site_header = "Administración del Sistema Escolar"
admin.site.site_title = "Portal de Administración"
admin.site.index_title = "Bienvenido al portal de administración"


# --- Configuración para servir archivos de medios (imágenes, etc.) en DESARROLLO ---
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)