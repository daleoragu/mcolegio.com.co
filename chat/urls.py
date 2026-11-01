from django.urls import path

from . import views

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
]
