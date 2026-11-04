from django.urls import path

from . import cabinas, views

app_name = 'votaciones'

urlpatterns = [
    path('', views.inicio, name='inicio'),
    path('<int:pk>/', views.eleccion, name='eleccion'),
    path('<int:pk>/votar/', views.votar, name='votar'),
    path('<int:pk>/mesa/', views.mesa, name='mesa'),
    path('<int:pk>/jurado/', cabinas.jurado, name='jurado'),
    path('<int:pk>/jurado/accion/', cabinas.jurado_accion, name='jurado_accion'),
    path('cabina/', cabinas.cabina, name='cabina'),
    path('cabina/estado/', cabinas.cabina_estado, name='cabina_estado'),
    path('cabina/v/<str:vinculo>/', cabinas.vincular_desde_enlace, name='cabina_vincular'),
    path('<int:pk>/resultados/', views.resultados, name='resultados'),
    path('<int:pk>/acta/', views.acta, name='acta'),
    path('candidato/<int:cid>/foto/', views.foto, name='foto'),
]
