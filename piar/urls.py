from django.urls import path

from . import views

app_name = 'piar'

urlpatterns = [
    path('', views.panel, name='panel'),
    path('configuracion/', views.configuracion, name='configuracion'),
    path('mi-piar/', views.mi_piar, name='mi_piar'),
    path('estadisticas/', views.estadisticas, name='estadisticas'),
    path('<int:pk>/', views.detalle, name='detalle'),
    path('<int:pk>/ajuste/<int:materia_id>/<int:periodo_id>/', views.ajuste, name='ajuste'),
    path('<int:pk>/eliminar/', views.eliminar, name='eliminar'),
    path('<int:pk>/piar.pdf', views.pdf, name='pdf'),
    path('<int:pk>/acta.pdf', views.acta_pdf, name='acta'),
]
