from django.urls import path

from . import views, views_colegas as colegas

app_name = 'chat'

urlpatterns = [
    path('', views.inicio, name='inicio'),
    path('no-leidos/', views.no_leidos, name='no_leidos'),
    path('nueva/', views.nueva, name='nueva'),
    path('grupo/', views.abrir_grupo, name='abrir_grupo'),
    path('grupo/nuevo/', views.grupo_nuevo, name='grupo_nuevo'),
    path('administrar/', views.administrar, name='administrar'),
    path('c/<int:pk>/', views.conversacion, name='conversacion'),
    path('c/<int:pk>/nuevos/', views.nuevos, name='nuevos'),
    path('c/<int:pk>/enviar/', views.enviar, name='enviar'),
    path('c/<int:pk>/accion/', views.accion, name='accion'),
    path('m/<int:mid>/reportar/', views.reportar, name='reportar'),
    path('m/<int:mid>/archivo/', views.archivo, name='archivo'),
    # Mis colegas: docentes de toda la plataforma
    path('colegas/', colegas.inicio, name='colegas'),
    path('colegas/no-leidos/', colegas.no_leidos, name='colegas_no_leidos'),
    path('colegas/solicitud/', colegas.solicitud, name='colegas_solicitud'),
    path('colegas/ajustes/', colegas.ajustes, name='colegas_ajustes'),
    path('colegas/escribir/', colegas.escribir, name='colegas_escribir'),
    path('colegas/grupo/nuevo/', colegas.grupo_nuevo, name='colegas_grupo_nuevo'),
    path('colegas/c/<int:pk>/', colegas.conversacion, name='colegas_conversacion'),
    path('colegas/c/<int:pk>/nuevos/', colegas.nuevos, name='colegas_nuevos'),
    path('colegas/c/<int:pk>/enviar/', colegas.enviar, name='colegas_enviar'),
    path('colegas/c/<int:pk>/accion/', colegas.accion, name='colegas_accion'),
    path('colegas/m/<int:mid>/archivo/', colegas.archivo, name='colegas_archivo'),
]
