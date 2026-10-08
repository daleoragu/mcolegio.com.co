# -*- coding: utf-8 -*-
from django.urls import path

from . import views

app_name = 'prematricula'

urlpatterns = [
    # Familia (portal, sin usuario)
    path('', views.inicio, name='inicio'),
    path('antiguo/', views.verificar_antiguo, name='verificar'),
    path('formulario/<str:tipo>/', views.formulario, name='formulario'),
    path('consultar/', views.consultar, name='consultar'),
    path('solicitud/<str:token>/', views.estado, name='estado'),
    # Secretaría
    path('gestion/', views.panel, name='panel'),
    path('gestion/configuracion/', views.configuracion, name='configuracion'),
    path('gestion/encuesta/', views.encuesta, name='encuesta'),
    path('gestion/exportar/', views.exportar, name='exportar'),
    path('gestion/activar/', views.activar, name='activar'),
    path('gestion/habilitar/', views.alternar, name='alternar'),
    path('gestion/<int:solicitud_id>/', views.detalle, name='detalle'),
    path('gestion/<int:solicitud_id>/documentos.zip', views.documentos_zip, name='documentos_zip'),
    path('gestion/documento/<int:documento_id>/', views.documento, name='documento'),
]
