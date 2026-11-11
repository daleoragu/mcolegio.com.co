# salon_digital/urls.py
from django.urls import path, re_path

from . import views, views_app, views_cuentas, views_espacios, views_grupos, views_pagos

app_name = 'salon_digital'

urlpatterns = [
    # --- Entrada ---
    path('', views.landing, name='landing'),
    # --- La app propia de Mi Salón Virtual (instalable, APK e iPhone) ---
    path('manifest.webmanifest', views_app.manifiesto, name='app_manifiesto'),
    path('app/', views_app.inicio, name='app_inicio'),
    path('app/instalar/', views_app.instalar, name='app_instalar'),
    path('registro/', views_cuentas.registro, name='registro'),
    path('entrar/', views_cuentas.Entrar.as_view(), name='entrar'),
    path('salir/', views_cuentas.salir, name='salir'),
    path('crear-cuenta/', views_cuentas.crear_cuenta, name='crear_cuenta'),
    path('auth/<str:proveedor>/', views_cuentas.social_iniciar, name='social_iniciar'),
    path('auth/<str:proveedor>/vuelta/', views_cuentas.social_vuelta, name='social_vuelta'),
    path('eliminar-datos/', views_cuentas.eliminar_datos, name='eliminar_datos'),
    path('ayuda/', views.ayuda, name='ayuda'),
    path('ayuda/descargar/<slug:cual>/', views.descargar, name='descargar'),

    # --- Los espacios del docente: Inicio y Mi Espacio de Profe ---
    path('inicio/', views_espacios.inicio, name='inicio'),
    path('pizarra/nota/', views_espacios.nota, name='nota_pizarra'),
    path('pizarra/tablero/', views_espacios.tablero, name='tablero'),
    path('pizarra/tablero/<int:pk>/', views_espacios.tablero_abrir, name='tablero_abrir'),
    path('pizarra/tablero/<int:pk>/compartir/', views_espacios.tablero_compartir, name='tablero_compartir'),
    path('pizarra/tablero/<int:pk>/eliminar/', views_espacios.tablero_eliminar, name='tablero_eliminar'),
    path('mi-espacio/', views_espacios.mi_espacio, name='mi_espacio'),
    path('mi-espacio/qr.png', views_espacios.qr_espacio, name='qr_espacio'),
    path('mi-espacio/pagina/<slug:slug>/visibilidad/', views_espacios.visibilidad_pagina, name='visibilidad_pagina'),

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
    path('grupos/<int:pk>/tarjetas/', views_grupos.tarjetas, name='tarjetas_grupo'),
    path('grupos/<int:pk>/estudiante/<int:integrante_pk>/editar/', views_grupos.editar_integrante, name='editar_integrante'),
    path('grupos/<int:pk>/estudiante/<int:integrante_pk>/pin/', views_grupos.nuevo_pin, name='nuevo_pin'),
    path('grupos/<int:pk>/estudiante/<int:integrante_pk>/volver/', views_grupos.reactivar_integrante, name='reactivar_integrante'),
    path('grupos/<int:pk>/quitar/<int:integrante_pk>/', views_grupos.quitar_integrante,
         name='quitar_integrante'),

    # --- Planes y pagos ---
    path('pagos/', views_pagos.planes, name='planes'),
    path('pagos/revisar/', views_pagos.revisar, name='revisar_pagos'),
    path('pagos/comprobante/<int:pk>/', views_pagos.comprobante, name='comprobante'),
    path('pagos/<str:referencia>/', views_pagos.pago, name='pago'),
    path('pagos/<str:referencia>/vuelta/', views_pagos.vuelta, name='pago_vuelta'),

    # --- Revisión de docentes (administradores) ---
    path('revision/', views_cuentas.bandeja_verificaciones, name='bandeja'),
    path('revision/<int:pk>/', views_cuentas.revisar_cuenta, name='revisar_cuenta'),
    path('revision/<int:pk>/plan/', views_cuentas.cambiar_plan, name='cambiar_plan'),

    # --- Resultados (acceso con clave) ---
    path('resultados/<slug:usuario>/<slug:slug>/', views.panel_clave, name='panel_clave'),
    path('resultados/<slug:usuario>/<slug:slug>/ver/', views.panel_resultados, name='panel_resultados'),
    path('resultados/<slug:usuario>/<slug:slug>/excel/', views.exportar_resultados, name='exportar_resultados'),

    # --- Endpoint que reciben las páginas publicadas ---
    path('api/practica/', views.api_practica, name='api_practica'),
    path('api/<slug:usuario>/<slug:slug>/', views.api_resultados, name='api_resultados'),

    # --- Banco de preguntas ---
    path('prueba/<slug:usuario>/<slug:slug>/', views.presentar_prueba, name='presentar_prueba'),
]
