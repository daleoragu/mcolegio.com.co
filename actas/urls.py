# -*- coding: utf-8 -*-
from django.urls import path

from . import views

app_name = 'actas'

urlpatterns = [
    path('', views.lista, name='lista'),
    path('nueva/<str:tipo>/', views.nueva, name='nueva'),
    path('<int:acta_id>/', views.editar, name='editar'),
    path('<int:acta_id>/pdf/', views.pdf, name='pdf'),
    path('<int:acta_id>/cerrar/', views.cerrar, name='cerrar'),
    path('<int:acta_id>/reabrir/', views.reabrir, name='reabrir'),
    path('<int:acta_id>/eliminar/', views.eliminar, name='eliminar'),
    path('<int:acta_id>/sugerir-asistentes/', views.sugerir_asistentes, name='sugerir_asistentes'),
]
