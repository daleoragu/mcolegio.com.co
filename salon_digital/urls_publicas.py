# salon_digital/urls_publicas.py
"""Rutas cortas: mcolegio.com.co/p/<usuario>/<pagina>/"""
from django.urls import path, re_path

from . import views

app_name = 'paginas'

urlpatterns = [
    path('<slug:usuario>/', views.perfil_publico, name='perfil'),
    path('<slug:usuario>/<slug:slug>/', views.ver_pagina, name='ver'),
    path('<slug:usuario>/<slug:slug>/entrar/', views.identificarse, name='identificarse'),
    path('<slug:usuario>/<slug:slug>/sin-grupo/', views.entrar_sin_grupo, name='entrar_sin_grupo'),
    path('<slug:usuario>/<slug:slug>/comentar/', views.comentar, name='comentar'),
    re_path(r'^(?P<usuario>[-\w]+)/(?P<slug>[-\w]+)/(?P<ruta>.+)$',
            views.archivo_pagina, name='archivo'),
]
