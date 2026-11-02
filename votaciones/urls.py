from django.urls import path

from . import views

app_name = 'votaciones'

urlpatterns = [
    path('', views.inicio, name='inicio'),
    path('<int:pk>/', views.eleccion, name='eleccion'),
    path('<int:pk>/votar/', views.votar, name='votar'),
    path('<int:pk>/mesa/', views.mesa, name='mesa'),
    path('<int:pk>/resultados/', views.resultados, name='resultados'),
    path('<int:pk>/acta/', views.acta, name='acta'),
    path('candidato/<int:cid>/foto/', views.foto, name='foto'),
]
