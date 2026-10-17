from django.urls import path

from . import views

app_name = 'calendario'

urlpatterns = [
    path('', views.calendario, name='inicio'),
    path('evento/<int:pk>/', views.ver_evento, name='evento'),
    path('nuevo/', views.editar, name='nuevo'),
    path('evento/<int:pk>/editar/', views.editar, name='editar'),
    path('evento/<int:pk>/eliminar/', views.eliminar, name='eliminar'),
    path('festivos/', views.agregar_festivos, name='festivos'),
    path('calendario-escolar.ics', views.descargar_ics, name='descargar_ics'),
    path('ical/<str:ficha>/calendario.ics', views.suscripcion_ics, name='ics'),
]
