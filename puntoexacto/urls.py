# -*- coding: utf-8 -*-
from django.urls import path

from . import views

app_name = 'puntoexacto'

urlpatterns = [
    path('', views.lista, name='lista'),
    path('nuevo/', views.crear, name='crear'),
    path('vista-previa/', views.vista_previa, name='vista_previa'),
    path('<int:examen_id>/editar/', views.editar, name='editar'),
    path('<int:examen_id>/archivar/', views.archivar, name='archivar'),
    path('<int:examen_id>/compartir/', views.compartir, name='compartir'),
    path('<int:examen_id>/clave/', views.clave, name='clave'),
    path('<int:examen_id>/clave/importar/', views.importar_clave, name='importar_clave'),
    path('<int:examen_id>/clave/exportar/', views.exportar_clave, name='exportar_clave'),
    path('<int:examen_id>/clave/<str:letra>/', views.clave_forma, name='clave_forma'),
    path('<int:examen_id>/bloques/', views.bloques, name='bloques'),
    path('<int:examen_id>/bloques/vista-previa/', views.vista_previa_bloques,
         name='vista_previa_bloques'),
    path('<int:examen_id>/cuadernillo/', views.cuadernillo, name='cuadernillo'),
    path('<int:examen_id>/cuadernillo/guardar/', views.cuadernillo_guardar, name='cuadernillo_guardar'),
    path('<int:examen_id>/cuadernillo/generar/', views.cuadernillo_generar, name='cuadernillo_generar'),
    path('nube/<str:proveedor>/', views.nube_ayudante, name='nube_ayudante'),
    path('nube-central/<str:proveedor>/', views.nube_central, name='nube_central'),
    path('<int:examen_id>/formas/', views.formas, name='formas'),
    path('<int:examen_id>/formas/<str:letra>/', views.forma_editar, name='forma_editar'),
    path('<int:examen_id>/formas-excel/', views.formas_exportar, name='formas_exportar'),
    path('<int:examen_id>/formas-imprimir/', views.formas_imprimir, name='formas_imprimir'),
    path('<int:examen_id>/hojas/', views.hojas, name='hojas'),
    path('<int:examen_id>/hojas/imprimir/', views.imprimir, name='imprimir'),
    path('<int:examen_id>/hoja/<int:hoja_id>/digitar/', views.digitar, name='digitar'),
    path('<int:examen_id>/escanear/', views.escanear, name='escanear'),
    path('<int:examen_id>/escanear/foto/', views.procesar_foto, name='procesar_foto'),
    path('<int:examen_id>/escanear/guardar/', views.guardar_lectura, name='guardar_lectura'),
    path('<int:examen_id>/escanear/nota/', views.nota_previa, name='nota_previa'),
    path('<int:examen_id>/resultados/', views.resultados, name='resultados'),
    path('<int:examen_id>/exportar/', views.exportar, name='exportar'),
    path('<int:examen_id>/planilla/', views.llevar_a_planilla, name='planilla'),
    path('<int:examen_id>/planilla/bloque/<int:bloque_id>/', views.planilla_bloque,
         name='planilla_bloque'),
]
