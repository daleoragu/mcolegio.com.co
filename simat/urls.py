from django.urls import path

from . import views

app_name = 'simat'

urlpatterns = [
    path('', views.panel, name='panel'),
    path('configuracion/', views.configuracion, name='configuracion'),
    path('estudiante/<int:pk>/', views.estudiante, name='estudiante'),
    path('exportar/', views.exportar, name='exportar'),
    path('datos/', views.datos_excel, name='datos'),
    path('importar/', views.importar_simat, name='importar'),
]
