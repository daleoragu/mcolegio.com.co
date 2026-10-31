from django.urls import path

from . import views, views_examenes as vx, views_fichas as vf, views_importar as vi, views_juegos as vj

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

    path('<int:pk>/actividades/', vj.actividades, name='actividades'),
    path('<int:pk>/actividades/<int:aid>/', vj.actividad, name='actividad'),
    path('<int:pk>/actividades/<int:aid>/resultado/', vj.actividad_resultado, name='actividad_resultado'),
    path('<int:pk>/actividades/<int:aid>/accion/', vj.actividad_accion, name='actividad_accion'),
    path('actividad-ejemplo.html', vj.actividad_ejemplo, name='actividad_ejemplo'),

    path('<int:pk>/cuestionarios/', vj.cuestionarios, name='cuestionarios'),
    path('<int:pk>/cuestionarios/<int:cid>/', vj.cuestionario, name='cuestionario'),
    path('<int:pk>/cuestionarios/<int:cid>/editar/', vj.cuestionario_editar, name='cuestionario_editar'),
    path('<int:pk>/cuestionarios/<int:cid>/accion/', vj.cuestionario_accion, name='cuestionario_accion'),
    path('<int:pk>/cuestionarios/<int:cid>/jugar/', vj.jugar, name='jugar'),
    path('<int:pk>/cuestionarios/<int:cid>/jugar/estado/', vj.jugar_estado, name='jugar_estado'),
    path('<int:pk>/vivo/<int:sid>/', vj.vivo, name='vivo'),
    path('<int:pk>/vivo/<int:sid>/estado/', vj.vivo_estado, name='vivo_estado'),

    path('<int:pk>/importar/', vi.importar_notas, name='importar'),
    path('<int:pk>/tareas/<int:tid>/ficha/', vf.ficha, name='ficha'),
    path('<int:pk>/tareas/<int:tid>/ficha/<str:clave>/revisar/', vf.ficha_revisar, name='ficha_revisar'),
    path('<int:pk>/tareas/<int:tid>/ficha/imagen/<int:iid>/', vf.ficha_imagen, name='ficha_imagen'),
    path('<int:pk>/tareas/<int:tid>/rejilla.xlsx', vi.rejilla_plantilla, name='rejilla_plantilla'),
    path('<int:pk>/tareas/<int:tid>/rejilla/importar/', vi.rejilla_importar, name='rejilla_importar'),
    path('<int:pk>/examenes/', vx.examenes, name='examenes'),
    path('<int:pk>/examenes/<int:eid>/', vx.examen, name='examen'),

    path('escala/', views.escala, name='escala'),
    path('instrumentos/', views.instrumentos, name='instrumentos'),
    path('instrumentos/<int:iid>/', views.instrumento, name='instrumento'),
    path('instrumentos/<int:iid>/accion/', views.instrumento_accion, name='instrumento_accion'),
]
