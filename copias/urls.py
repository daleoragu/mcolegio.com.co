from django.urls import path

from . import views

app_name = 'copias'

urlpatterns = [
    path('', views.inicio, name='inicio'),
    path('ajustes/', views.ajustes, name='ajustes'),
    path('archivo.zip', views.archivo, name='archivo'),
    path('hecha/', views.hecha, name='hecha'),
    path('pendiente/', views.pendiente, name='pendiente'),
]
