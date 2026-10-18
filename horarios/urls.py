from django.urls import path

from . import views

app_name = 'horarios'

urlpatterns = [
    path('', views.panel, name='panel'),
    path('jornada/nueva/', views.jornadas, name='jornada_nueva'),
    path('jornada/<int:pk>/', views.jornadas, name='jornada'),
    path('generador/datos/', views.exportar_datos, name='exportar_datos'),
    path('generador/app/', views.descargar_app, name='descargar_app'),
    path('generador/app/subir/', views.subir_app, name='subir_app'),
    path('importar/', views.importar, name='importar'),
    path('<int:pk>/', views.detalle, name='detalle'),
    path('<int:pk>/accion/', views.accion, name='accion'),
    path('<int:pk>/pdf/', views.pdf, name='pdf'),
    path('mi-horario/', views.mi_horario, name='mi_horario'),
    path('reemplazos/', views.reemplazos_vista, name='reemplazos'),
    path('intensidad/', views.intensidad_vista, name='intensidad'),
    path('ciclo/', views.ciclo_vista, name='ciclo'),
    path('mi-disponibilidad/', views.mi_disponibilidad, name='mi_disponibilidad'),
    path('disponibilidad/', views.disponibilidad_docentes, name='disponibilidad'),
]
