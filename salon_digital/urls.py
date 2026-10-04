# salon_digital/urls.py
from django.urls import path, re_path

from . import views, views_cuentas, views_grupos

app_name = 'salon_digital'

urlpatterns = [
    # --- Entrada ---
    path('', views.landing, name='landing'),
    path('registro/', views_cuentas.registro, name='registro'),
    path('entrar/', views_cuentas.Entrar.as_view(), name='entrar'),
    path('salir/', views_cuentas.salir, name='salir'),
    path('crear-cuenta/', views_cuentas.crear_cuenta, name='crear_cuenta'),
    path('ayuda/', views.ayuda, name='ayuda'),
    path('ayuda/descargar/<slug:cual>/', views.descargar, name='descargar'),

    # --- Panel del docente ---
    path('panel/', views.panel, name='panel'),
    path('panel/cuenta/', views_cuentas.mi_cuenta, name='mi_cuenta'),
    path('panel/cuenta/verificar/', views_cuentas.enviar_verificacion, name='enviar_verificacion'),
    path('panel/nueva/', views.nueva_pagina, name='nueva_pagina'),
    path('panel/varias/', views.subir_varias, name='subir_varias'),
    path('panel/<slug:slug>/editar/', views.editar_pagina, name='editar_pagina'),
    path('panel/<slug:slug>/eliminar/', views.eliminar_pagina, name='eliminar_pagina'),
    path('panel/<slug:slug>/qr/', views.qr_hoja, name='qr_hoja'),
    path('panel/<slug:slug>/qr.png', views.qr_imagen, name='qr_imagen'),
    path('panel/<slug:slug>/comentarios/', views.moderar_comentarios, name='moderar_comentarios'),

    # --- Grupos ---
    path('grupos/', views_grupos.grupos, name='grupos'),
    path('grupos/nuevo/', views_grupos.nuevo_grupo, name='nuevo_grupo'),
    path('grupos/<int:pk>/', views_grupos.ver_grupo, name='ver_grupo'),
    path('grupos/<int:pk>/editar/', views_grupos.editar_grupo, name='editar_grupo'),
    path('grupos/<int:pk>/eliminar/', views_grupos.eliminar_grupo, name='eliminar_grupo'),
    path('grupos/<int:pk>/quitar/<int:integrante_pk>/', views_grupos.quitar_integrante,
         name='quitar_integrante'),

    # --- Revisión de docentes (administradores) ---
    path('revision/', views_cuentas.bandeja_verificaciones, name='bandeja'),
    path('revision/<int:pk>/', views_cuentas.revisar_cuenta, name='revisar_cuenta'),
    path('revision/<int:pk>/plan/', views_cuentas.cambiar_plan, name='cambiar_plan'),

    # --- Resultados (acceso con clave) ---
    path('resultados/<slug:usuario>/<slug:slug>/', views.panel_clave, name='panel_clave'),
    path('resultados/<slug:usuario>/<slug:slug>/ver/', views.panel_resultados, name='panel_resultados'),
    path('resultados/<slug:usuario>/<slug:slug>/excel/', views.exportar_resultados, name='exportar_resultados'),

    # --- Endpoint que reciben las páginas publicadas ---
    path('api/<slug:usuario>/<slug:slug>/', views.api_resultados, name='api_resultados'),

    # --- Banco de preguntas ---
    path('prueba/<slug:usuario>/<slug:slug>/', views.presentar_prueba, name='presentar_prueba'),
]
