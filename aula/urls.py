from django.urls import path

from . import views

app_name = 'aula'

urlpatterns = [
    path('', views.inicio, name='inicio'),
    path('asignacion/<int:asignacion_id>/', views.por_asignacion, name='por_asignacion'),
    path('grupo/<int:grupo_id>/', views.por_grupo, name='por_grupo'),

    path('<int:pk>/', views.muro, name='muro'),
    path('<int:pk>/entrar/', views.entrar, name='entrar'),
    path('<int:pk>/salir/', views.salir, name='salir'),
    path('<int:pk>/publicacion/<int:pub_id>/comentar/', views.comentar, name='comentar'),
    path('<int:pk>/publicacion/<int:pub_id>/moderar/', views.moderar, name='moderar'),
    path('<int:pk>/clase/', views.clase, name='clase'),
    path('<int:pk>/material/', views.material, name='material'),
    path('<int:pk>/material/<int:mid>/eliminar/', views.material_eliminar, name='material_eliminar'),
    path('<int:pk>/archivo/<str:tipo>/<int:oid>/', views.archivo, name='archivo'),

    path('<int:pk>/tareas/', views.tareas, name='tareas'),
    path('<int:pk>/tareas/nueva/', views.tarea_form, name='tarea_nueva'),
    path('<int:pk>/tareas/<int:tid>/', views.tarea, name='tarea'),
    path('<int:pk>/tareas/<int:tid>/editar/', views.tarea_form, name='tarea_editar'),
    path('<int:pk>/tareas/<int:tid>/eliminar/', views.tarea_eliminar, name='tarea_eliminar'),
    path('<int:pk>/tareas/<int:tid>/entregar/', views.entregar, name='entregar'),
    path('<int:pk>/tareas/<int:tid>/calificar/<str:clave>/', views.calificar, name='calificar'),
    path('<int:pk>/tareas/<int:tid>/grilla/', views.grilla, name='grilla'),
    path('<int:pk>/tareas/<int:tid>/planilla/', views.pasar_planilla, name='pasar_planilla'),
    path('<int:pk>/calificaciones/', views.calificaciones, name='calificaciones'),

    path('instrumentos/', views.instrumentos, name='instrumentos'),
    path('instrumentos/<int:iid>/', views.instrumento, name='instrumento'),
    path('instrumentos/<int:iid>/accion/', views.instrumento_accion, name='instrumento_accion'),
]
