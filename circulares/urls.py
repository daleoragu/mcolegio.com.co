from django.urls import path

from . import views

app_name = 'circulares'

urlpatterns = [
    path('', views.mis_circulares, name='mis_circulares'),
    path('<int:pk>/', views.ver, name='ver'),
    path('<int:pk>/confirmar/', views.confirmar, name='confirmar'),
    path('gestion/', views.lista, name='lista'),
    path('gestion/nueva/', views.editar, name='nueva'),
    path('gestion/<int:pk>/', views.detalle, name='detalle'),
    path('gestion/<int:pk>/editar/', views.editar, name='editar'),
    path('gestion/<int:pk>/eliminar/', views.eliminar, name='eliminar'),
]
