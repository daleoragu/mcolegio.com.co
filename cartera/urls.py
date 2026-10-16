from django.urls import path

from . import views

app_name = 'cartera'

urlpatterns = [
    path('', views.panel, name='panel'),
    path('configuracion/', views.configuracion, name='configuracion'),
    path('configuracion/concepto/<int:concepto_id>/', views.configuracion, name='concepto'),
    path('estudiante/<int:pk>/', views.estudiante, name='estudiante'),
    path('estudiante/<int:pk>/estado.pdf', views.estado_pdf, name='estado_pdf'),
    path('estudiante/<int:pk>/paz-y-salvo.pdf', views.paz_y_salvo_pdf, name='paz_y_salvo'),
    path('recibo/<int:pago_id>.pdf', views.recibo_pdf, name='recibo'),
    path('recibo/<int:pago_id>/anular/', views.anular, name='anular'),
    path('mi-cuenta/', views.mi_cuenta, name='mi_cuenta'),
]
