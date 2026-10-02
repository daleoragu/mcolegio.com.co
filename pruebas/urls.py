# pruebas/urls.py
from django.urls import path

from . import views

app_name = 'pruebas'

urlpatterns = [
    # --- Administración (requiere iniciar sesión) ---
    path('panel/', views.lista_paginas, name='lista_paginas'),
    path('panel/nueva/', views.nueva_pagina, name='nueva_pagina'),
    path('panel/varias/', views.subir_varias, name='subir_varias'),
    path('panel/<slug:slug>/editar/', views.editar_pagina, name='editar_pagina'),
    path('panel/<slug:slug>/eliminar/', views.eliminar_pagina, name='eliminar_pagina'),
    path('panel/<slug:slug>/qr/', views.qr_hoja, name='qr_hoja'),
    path('panel/<slug:slug>/qr.png', views.qr_imagen, name='qr_imagen'),

    # --- Resultados (acceso con clave, sin iniciar sesión) ---
    path('resultados/<slug:slug>/', views.panel_clave, name='panel_clave'),
    path('resultados/<slug:slug>/ver/', views.panel_resultados, name='panel_resultados'),
    path('resultados/<slug:slug>/excel/', views.exportar_resultados, name='exportar_resultados'),
    path('resultados/vincular/<int:sesion_id>/', views.vincular_sesion, name='vincular_sesion'),

    # --- Endpoint que reciben los HTML publicados ---
    path('api/<slug:slug>/', views.api_resultados, name='api_resultados'),

    # --- Pruebas del banco de preguntas ---
    path('<slug:slug>/', views.presentar_prueba, name='presentar_prueba'),
]
