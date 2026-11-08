from django.urls import path

from . import views, views_colegas as colegas, views_muro as muro

app_name = 'chat'

urlpatterns = [
    path('', views.inicio, name='inicio'),
    path('no-leidos/', views.no_leidos, name='no_leidos'),
    path('nueva/', views.nueva, name='nueva'),
    path('grupo/', views.abrir_grupo, name='abrir_grupo'),
    path('grupo/nuevo/', views.grupo_nuevo, name='grupo_nuevo'),
    path('administrar/', views.administrar, name='administrar'),
    path('c/<int:pk>/', views.conversacion, name='conversacion'),
    path('c/<int:pk>/nuevos/', views.nuevos, name='nuevos'),
    path('c/<int:pk>/enviar/', views.enviar, name='enviar'),
    path('c/<int:pk>/accion/', views.accion, name='accion'),
    path('m/<int:mid>/reportar/', views.reportar, name='reportar'),
    path('m/<int:mid>/archivo/', views.archivo, name='archivo'),
    # Mis colegas: docentes de toda la plataforma
    path('colegas/', colegas.inicio, name='colegas'),
    path('colegas/no-leidos/', colegas.no_leidos, name='colegas_no_leidos'),
    path('colegas/solicitud/', colegas.solicitud, name='colegas_solicitud'),
    path('colegas/ajustes/', colegas.ajustes, name='colegas_ajustes'),
    path('colegas/escribir/', colegas.escribir, name='colegas_escribir'),
    path('colegas/grupo/nuevo/', colegas.grupo_nuevo, name='colegas_grupo_nuevo'),
    path('colegas/c/<int:pk>/', colegas.conversacion, name='colegas_conversacion'),
    path('colegas/c/<int:pk>/nuevos/', colegas.nuevos, name='colegas_nuevos'),
    path('colegas/c/<int:pk>/enviar/', colegas.enviar, name='colegas_enviar'),
    path('colegas/c/<int:pk>/accion/', colegas.accion, name='colegas_accion'),
    path('colegas/m/<int:mid>/archivo/', colegas.archivo, name='colegas_archivo'),
    path('colegas/u/<int:uid>/', colegas.ver, name='colegas_ver'),
    path('colegas/avisos/', colegas.avisos, name='colegas_avisos'),
    path('colegas/avisos/leidos/', colegas.avisos_leidos, name='colegas_avisos_leidos'),
    path('colegas/aviso/<int:nid>/', colegas.aviso, name='colegas_aviso'),
    path('colegas/muro/', muro.muro, name='muro'),
    path('colegas/muro/normas/', muro.normas, name='muro_normas'),
    path('colegas/muro/moderar/', muro.moderar, name='muro_moderar'),
    path('colegas/muro/descartar/', muro.descartar, name='muro_descartar'),
    path('colegas/muro/<int:pk>/', muro.detalle, name='muro_detalle'),
    path('colegas/muro/<int:pk>/reaccion/', muro.reaccion, name='muro_reaccion'),
    path('colegas/muro/<int:pk>/accion/', muro.accion, name='muro_accion'),
    path('colegas/muro/<int:pk>/copiar/', muro.copiar, name='muro_copiar'),
    path('colegas/muro/<int:pk>/copiar-actividad/', muro.copiar_actividad, name='muro_copiar_actividad'),
    path('colegas/muro/<int:pk>/material/', muro.material, name='muro_material'),
    path('colegas/mini/', colegas.mini, name='colegas_mini'),
    path('colegas/mini/abrir/', colegas.mini_abrir, name='colegas_mini_abrir'),
    path('colegas/mini/c/<int:pk>/', colegas.mini_conv, name='colegas_mini_conv'),
]
