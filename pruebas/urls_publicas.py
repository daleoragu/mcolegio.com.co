# pruebas/urls_publicas.py
"""Rutas cortas del publicador: mcolegio.com.co/p/<nombre>/"""
from django.urls import path

from . import views

app_name = 'paginas'

urlpatterns = [
    path('', views.indice_paginas, name='indice'),
    path('<slug:slug>/', views.ver_pagina, name='ver'),
]
