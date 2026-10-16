from django.urls import path

from . import views

app_name = 'certificados'

urlpatterns = [
    path('', views.panel, name='panel'),
    path('estudiante/<int:estudiante_id>/', views.estudiante, name='estudiante'),
    path('estudiante/<int:estudiante_id>/generar/', views.generar, name='generar'),
    path('solicitud/<int:solicitud_id>/resolver/', views.resolver, name='resolver'),
    path('configuracion/', views.configuracion, name='configuracion'),
    path('importar/', views.importar, name='importar'),
    path('importar/plantilla/', views.plantilla, name='plantilla'),
    path('mis-certificados/', views.mis_certificados, name='mis_certificados'),
    path('mis-certificados/pedir/', views.solicitar, name='solicitar'),
    path('verificar/', views.verificar, name='verificar_form'),
    path('verificar/<str:codigo>/', views.verificar, name='verificar'),
    path('<str:codigo>/pdf/', views.pdf, name='pdf'),
    path('<str:codigo>/anular/', views.anular, name='anular'),
]
