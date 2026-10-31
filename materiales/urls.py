from django.urls import path

from . import views

app_name = 'materiales'

urlpatterns = [
    path('', views.lista, name='lista'),
    path('nuevo/', views.nuevo, name='nuevo'),
    path('encabezado/', views.encabezado, name='encabezado'),
    path('imagen/', views.imagen_subir, name='imagen_subir'),
    path('imagen/<int:pk>/', views.imagen_ver, name='imagen'),
    path('<int:pk>/', views.editor, name='editor'),
    path('<int:pk>/guardar/', views.guardar, name='guardar'),
    path('<int:pk>/accion/', views.accion, name='accion'),
    path('<int:pk>/pdf/', views.pdf, name='pdf'),
    path('<int:pk>/word/', views.word, name='word'),
    path('<int:pk>/paginas/', views.paginas, name='paginas'),
]
