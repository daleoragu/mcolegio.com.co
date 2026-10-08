# notas/urls.py
# Este archivo define todas las URLs específicas de tu aplicación "notas".

from django.urls import path
from .views import (
    auth_views,
    dashboard_views,
    admin_tools_views,
    ingreso_notas_views,
    indicador_views,
    plan_mejoramiento_views,
    observador_views,
    asistencia_views,
    consulta_views,
    boletin_views,
    export_views,
    import_views,
    reporte_parcial_views,
    estadisticas_views,
    mensajeria_views,
    importar_asistencia_views,
    estudiante_observador_views,
    notificaciones_views,
    publicacion_views,
    estudiante_boletin_views,
    portal_views,
    portal_admin_views,
    impersonation_views,
    gestion_academica_views,
    promocion_views,
    sedes_views,
    recuperar_clave_views,
    componentes_views,
    carnet_views,
    certificados_views,
    import_export_planillas_views,
    planillas_views,
    alertas_views,
    administradores_views,
    sabana_views,
    gestion_docentes_views,
    gestion_estudiantes_views,
    reporte_views # <--- === CORRECCIÓN 1: IMPORTAMOS EL ARCHIVO CORRECTO ===
)

# El nombre 'app_name' ayuda a Django a organizar las URLs. Es una buena práctica.
app_name = 'notas'

urlpatterns = [
    # --- Rutas del Portal Público y Autenticación ---
    path('', portal_views.portal_vista, name='portal'),
    path('logout/', auth_views.logout_vista, name='logout'),
    path('logout/confirmacion/', auth_views.logout_confirmacion_vista, name='logout_confirmacion'),
    path('cambiar-password/', auth_views.cambiar_password_vista, name='cambiar_password'),
    path('recuperar-clave/', recuperar_clave_views.pedir_enlace, name='recuperar_clave'),
    path('recuperar-clave/<uidb64>/<token>/', recuperar_clave_views.nueva_clave, name='recuperar_clave_nueva'),
    path('admin/restablecer-clave/<int:user_id>/', recuperar_clave_views.restablecer_por_admin, name='restablecer_clave'),

    # --- Rutas de Paneles de Usuario ---
    path('dashboard/', dashboard_views.dashboard_vista, name='dashboard'),
    path('panel-administrador/', dashboard_views.admin_dashboard_vista, name='admin_dashboard'),
    path('panel-docente/', dashboard_views.docente_dashboard_vista, name='panel_docente'),
    path('panel-estudiante/', dashboard_views.estudiante_dashboard_vista, name='panel_estudiante'),

    # ==========================================================================
    # --- VISTAS PERSONALIZADAS DE ADMINISTRACIÓN ---
    # ==========================================================================
    
    # --- Gestión de Usuarios (Docentes y Estudiantes) ---
    path('admin/gestion-docentes/', gestion_docentes_views.gestion_docentes_vista, name='gestion_docentes'),
    path('admin/gestion-docentes/crear/', gestion_docentes_views.crear_docente_vista, name='crear_docente'),
    path('admin/gestion-docentes/editar/<int:docente_id>/', gestion_docentes_views.editar_docente_vista, name='editar_docente'),
    path('admin/gestion-docentes/eliminar/<int:docente_id>/', gestion_docentes_views.eliminar_docente_vista, name='eliminar_docente'),
    
    path('admin/gestion-estudiantes/', gestion_estudiantes_views.gestion_estudiantes_vista, name='gestion_estudiantes'),
    path('admin/gestion-estudiantes/crear/', gestion_estudiantes_views.crear_estudiante_vista, name='crear_estudiante'),
    path('admin/gestion-estudiantes/editar/<int:estudiante_id>/', gestion_estudiantes_views.editar_estudiante_vista, name='editar_estudiante'),
    path('admin/gestion-estudiantes/eliminar/<int:estudiante_id>/', gestion_estudiantes_views.eliminar_estudiante_vista, name='eliminar_estudiante'),
    
    # --- Herramientas de Administración ---
    path('admin/panel-control-periodos/', admin_tools_views.panel_control_periodos_vista, name='panel_control_periodos'),
    path('admin/panel-control-promocion/', admin_tools_views.panel_control_promocion_vista, name='panel_control_promocion'),
    path('admin/configuracion-calificaciones/', admin_tools_views.configuracion_calificaciones_vista, name='configuracion_calificaciones'),
    path('admin/componentes-evaluacion/', componentes_views.componentes_evaluacion, name='componentes_evaluacion'),
    path('admin/configuracion-escala/', admin_tools_views.configuracion_escala_valoracion_vista, name='configuracion_escala_valoracion'),
    path('panel-administrador/configuracion/escala-valoracion/editar/<int:escala_id>/', admin_tools_views.editar_escala_valoracion_vista, name='editar_escala_valoracion'),
    path('admin/periodo/crear/', admin_tools_views.crear_periodo_vista, name='crear_periodo'),
    path('admin/periodo/editar/<int:periodo_id>/', admin_tools_views.editar_periodo_vista, name='editar_periodo'),
    path('admin/periodo/eliminar/<int:periodo_id>/', admin_tools_views.eliminar_periodo_vista, name='eliminar_periodo'),

    # --- Rutas para Gestión Académica ---
    path('admin/gestion-academica/', gestion_academica_views.gestion_asignacion_academica_vista, name='gestion_asignacion_academica'),
    path('admin/gestion-academica/asignacion/crear/', gestion_academica_views.crear_asignacion_vista, name='crear_asignacion'),
    path('admin/gestion-academica/asignacion/eliminar/<int:asignacion_id>/', gestion_academica_views.eliminar_asignacion_vista, name='eliminar_asignacion'),
    path('admin/gestion-academica/cursos/', gestion_academica_views.gestion_cursos_vista, name='gestion_cursos'),
    path('admin/gestion-academica/cursos/crear/', gestion_academica_views.crear_curso_vista, name='crear_curso'),
    path('admin/gestion-academica/cursos/editar/<int:curso_id>/', gestion_academica_views.editar_curso_vista, name='editar_curso'),
    path('admin/gestion-academica/cursos/eliminar/<int:curso_id>/', gestion_academica_views.eliminar_curso_vista, name='eliminar_curso'),
    path('admin/gestion-academica/cursos/promocion/', promocion_views.promocion_anual, name='promocion_anual'),
    path('admin/sedes/', sedes_views.gestion_sedes, name='gestion_sedes'),
    path('admin/sedes/crear/', sedes_views.crear_sede, name='crear_sede'),
    path('admin/sedes/<int:sede_id>/editar/', sedes_views.editar_sede, name='editar_sede'),
    path('admin/sedes/<int:sede_id>/eliminar/', sedes_views.eliminar_sede, name='eliminar_sede'),
    path('admin/gestion-academica/areas/', gestion_academica_views.gestion_areas_vista, name='gestion_areas'),
    path('admin/gestion-academica/areas/crear/', gestion_academica_views.crear_area_vista, name='crear_area'),
    path('admin/gestion-academica/areas/editar/<int:area_id>/', gestion_academica_views.editar_area_vista, name='editar_area'),
    path('admin/gestion-academica/areas/eliminar/<int:area_id>/', gestion_academica_views.eliminar_area_vista, name='eliminar_area'),
    path('admin/gestion-academica/materias/', gestion_academica_views.gestion_materias_vista, name='gestion_materias'),
    path('admin/gestion-academica/materias/crear/', gestion_academica_views.crear_materia_vista, name='crear_materia'),
    path('admin/gestion-academica/materias/crear/para-area/<int:area_id>/', gestion_academica_views.crear_materia_vista, name='crear_materia_para_area'),
    path('admin/gestion-academica/materias/editar/<int:materia_id>/', gestion_academica_views.editar_materia_vista, name='editar_materia'),
    path('admin/gestion-academica/materias/eliminar/<int:materia_id>/', gestion_academica_views.eliminar_materia_vista, name='eliminar_materia'),
    path('admin/gestion-academica/ponderacion/', gestion_academica_views.gestion_ponderacion_areas_vista, name='gestion_ponderacion_areas'),

    # --- Rutas para el Portal y su Administración ---
    path('admin/portal/configuracion/', portal_admin_views.configuracion_portal_vista, name='configuracion_portal'),
    path('admin/portal/personalizacion/', portal_admin_views.personalizacion_portal_vista, name='personalizacion_portal'),
    path('admin/portal/diseno/', portal_admin_views.elegir_diseno_portal_vista, name='elegir_diseno_portal'),
    path('admin/portal/documentos/', portal_admin_views.gestion_documentos_vista, name='gestion_documentos'),
    path('admin/portal/documentos/eliminar/<int:pk>/', portal_admin_views.eliminar_documento_vista, name='eliminar_documento'),
    path('admin/portal/galeria/', portal_admin_views.gestion_galeria_vista, name='gestion_galeria'),
    path('admin/portal/galeria/eliminar/<int:pk>/', portal_admin_views.eliminar_foto_vista, name='eliminar_foto'),
    path('admin/portal/noticias/', portal_admin_views.gestion_noticias_vista, name='gestion_noticias'),
    path('admin/portal/noticias/crear/', portal_admin_views.crear_noticia_vista, name='crear_noticia'),
    path('admin/portal/noticias/editar/<int:pk>/', portal_admin_views.editar_noticia_vista, name='editar_noticia'),
    path('admin/portal/noticias/eliminar/<int:pk>/', portal_admin_views.eliminar_noticia_vista, name='eliminar_noticia'),
    path('admin/portal/noticias/publicar/<int:pk>/', portal_admin_views.publicar_noticia_vista, name='publicar_noticia'),
    path('admin/portal/carrusel/', portal_admin_views.gestion_carrusel_vista, name='gestion_carrusel'),
    path('admin/portal/carrusel/editar/<int:pk>/', portal_admin_views.editar_imagen_carrusel_vista, name='editar_imagen_carrusel'),
    path('admin/portal/carrusel/eliminar/<int:pk>/', portal_admin_views.eliminar_imagen_carrusel_vista, name='eliminar_imagen_carrusel'),

    # --- Rutas para Importación y Exportación ---
    path('admin/importacion/', import_views.importacion_vista, name='importacion_datos'),
    path('admin/exportar-estudiantes/', export_views.exportar_estudiantes_excel, name='exportar_estudiantes_excel'),
    path('admin/descargar-plantilla-estudiantes/', export_views.descargar_plantilla_estudiantes, name='descargar_plantilla_estudiantes'),
    path('admin/exportar-materias/', export_views.exportar_materias_excel, name='exportar_materias_excel'),
    path('admin/descargar-plantilla-docentes/', export_views.descargar_plantilla_docentes, name='descargar_plantilla_docentes'),
    path('admin/descargar-plantilla-materias/', export_views.descargar_plantilla_materias, name='descargar_plantilla_materias'),   

    # === CORRECCIÓN 2: Se usa el módulo y el nombre de función correctos ===
    path('docente/reportes/asistencia/excel/', reporte_views.generar_reporte_individual_excel, name='generar_reporte_individual_excel'),
    path('docente/reportes/asistencia/pdf/', reporte_views.generar_reporte_individual_pdf, name='generar_reporte_individual_pdf'),

    # --- Rutas para Docentes ---
    path('docente/ingresar-notas/', ingreso_notas_views.IngresoNotasView.as_view(), name='ingresar_notas_periodo'),
    path('docente/exportar-planillas/<int:docente_id>/<int:periodo_id>/', import_export_planillas_views.exportar_planillas_docente, name='exportar_planillas_docente'),
    path('docente/planillas/', planillas_views.mis_planillas, name='mis_planillas'),
    path('alertas-tempranas/', alertas_views.alertas_tempranas, name='alertas_tempranas'),
    path('admin/administradores/', administradores_views.administradores_colegio, name='administradores_colegio'),
    path('admin/administradores/<int:admin_id>/acceso/', administradores_views.quitar_administrador, name='quitar_administrador'),
    path('docente/planillas/subir/', planillas_views.subir_excel, name='subir_planilla'),
    path('docente/planillas/<int:periodo_id>/excel/', planillas_views.descargar_excel, name='descargar_planillas'),
    path('docente/planillas/<int:periodo_id>/excel/<int:asignacion_id>/', planillas_views.descargar_excel, name='descargar_planilla'),
    path('docente/planillas/<int:periodo_id>/pdf/', planillas_views.descargar_pdf, name='descargar_planillas_pdf'),
    path('docente/planillas/<int:periodo_id>/pdf/<int:asignacion_id>/', planillas_views.descargar_pdf, name='descargar_planilla_pdf'),
    path('docente/planillas/<int:asignacion_id>/<int:periodo_id>/columnas/', planillas_views.guardar_columnas, name='guardar_columnas_planilla'),
    path('docente/reporte-parcial/', reporte_parcial_views.reporte_parcial_vista, name='reporte_parcial'),
    path('docente/plan-mejoramiento/', plan_mejoramiento_views.plan_mejoramiento_vista, name='plan_mejoramiento'),
    path('docente/asistencia/', asistencia_views.asistencia_vista, name='asistencia'),
    path('docente/consulta-asistencia/', consulta_views.consulta_asistencia_vista, name='consulta_asistencia'),
    path('docente/importar-asistencia/', importar_asistencia_views.importar_asistencia_excel_vista, name='importar_asistencia_excel'),
    path('indicador/crear/', indicador_views.crear_indicador_vista, name='crear_indicador'),
    path('indicador/editar/<int:indicador_id>/', indicador_views.editar_indicador_vista, name='editar_indicador'),
    path('indicador/eliminar/<int:indicador_id>/', indicador_views.eliminar_indicador_vista, name='eliminar_indicador'),
    
    # --- Rutas para Sábana de Notas ---
    path('docente/selector-sabana/', sabana_views.selector_sabana_vista, name='selector_sabana'),
    path('docente/generar-sabana/', sabana_views.generar_sabana_vista, name='generar_sabana'),
    path('docente/exportar-sabana-excel/', sabana_views.exportar_sabana_excel, name='exportar_sabana_excel'),
    path('docente/generar-sabana-pdf/', sabana_views.generar_sabana_pdf, name='generar_sabana_pdf'),
    
    # --- Rutas para Estudiantes ---
    path('estudiante/mis-boletines/', estudiante_boletin_views.mis_boletines_vista, name='mi_boletin'),
    path('estudiante/mi-observador/', estudiante_observador_views.mi_observador_vista, name='mi_observador'),

    # --- Rutas para Boletines, Reportes y Estadísticas ---
    path('reportes/selector-boletin/', boletin_views.selector_boletin_vista, name='selector_boletin'),
    path('reportes/generar-boletin/', boletin_views.generar_boletin_vista, name='generar_boletin'),
    path('admin/publicacion-boletines/', publicacion_views.panel_publicacion_vista, name='panel_publicacion'),
    path('estadisticas/', estadisticas_views.panel_estadisticas_vista, name='panel_estadisticas'),
    path('estadisticas/generar-pdf/', estadisticas_views.estadisticas_pdf_vista, name='estadisticas_pdf'),
    path('reporte-parcial/acta/<int:estudiante_id>/', reporte_parcial_views.acta_reporte_parcial_estudiante, name='acta_reporte_parcial_estudiante'),
    path('reporte-parcial/estudiantes/', reporte_parcial_views.lista_estudiantes_reporte, name='lista_estudiantes_reporte'),

    # --- Rutas para Mensajería ---
    path('mensajeria/componer/', mensajeria_views.componer_mensaje_vista, name='componer_mensaje'),
    path('mensajeria/bandeja-entrada/', mensajeria_views.bandeja_entrada_vista, name='bandeja_entrada'),
    path('mensajeria/ver/<int:mensaje_id>/', mensajeria_views.ver_mensaje_vista, name='ver_mensaje'),
    path('mensajeria/enviados/', mensajeria_views.mensajes_enviados_vista, name='mensajes_enviados'),
    path('mensajeria/borrar/<int:mensaje_id>/', mensajeria_views.borrar_mensaje_vista, name='borrar_mensaje'),
    path('mensajeria/papelera/', mensajeria_views.papelera_vista, name='papelera'),
    path('mensajeria/restaurar/<int:mensaje_id>/', mensajeria_views.restaurar_mensaje_vista, name='restaurar_mensaje'),
    path('mensajeria/borrar-definitivo/<int:mensaje_id>/', mensajeria_views.borrar_definitivamente_vista, name='borrar_permanentemente_mensaje'),
    path('mensajeria/borradores/', mensajeria_views.borradores_vista, name='borradores'),
    
    # --- Rutas para Observador ---
    path('observador/seleccionar/', observador_views.observador_selector_vista, name='observador_selector'),
    path('observador/detalle/<int:estudiante_id>/', observador_views.vista_detalle_observador, name='vista_detalle_observador'),
    path('observador/crear/<int:estudiante_id>/', observador_views.crear_registro_observador_vista, name='crear_registro_observador'),
    path('observador/ficha/<int:estudiante_id>/editar/', observador_views.editar_ficha_vista, name='editar_ficha'),
    path('observador/pdf/<int:estudiante_id>/', observador_views.generar_observador_pdf_vista, name='generar_observador_pdf'),
    path('familia/observador/<str:token>/', observador_views.respuesta_acudiente_vista, name='respuesta_acudiente'),
    path('observador/registro/<int:registro_id>/avisar/', observador_views.aviso_familia_vista, name='aviso_familia'),
    path('observador/registro/<int:registro_id>/editar/', observador_views.editar_registro_observador_vista, name='editar_registro_observador'),
    path('observador/registro/<int:registro_id>/eliminar/', observador_views.eliminar_registro_observador_vista, name='eliminar_registro_observador'),

    # --- Rutas para Carnets y Certificados ---
    path('carnet/generar/<int:estudiante_id>/', carnet_views.generar_carnet_estudiante, name='generar_carnet_estudiante'),
    path('asistencia/kiosko/', carnet_views.vista_kiosko_asistencia, name='vista_kiosko_asistencia'),
    path('asistencia/registrar-qr/<int:estudiante_id>/', carnet_views.registrar_asistencia_qr, name='registrar_asistencia_qr'),
    path('herramientas/imprimir-carnets/', carnet_views.impresion_masiva_carnets, name='impresion_masiva_carnets'),
    path('herramientas/certificados/', certificados_views.selector_certificados_vista, name='selector_certificados'),
    path('herramientas/certificados/generar/<int:estudiante_id>/', certificados_views.generar_certificado_estudio_pdf, name='generar_certificado_estudio'),

    # --- Rutas AJAX ---
    path('ajax/guardar-inasistencia/', asistencia_views.guardar_inasistencia_ajax, name='guardar_inasistencia_ajax'),
    path('ajax/get-inasistencias-auto/', ingreso_notas_views.ajax_get_inasistencias_auto, name='get_inasistencias_auto'),
    path('ajax/obtener-notificaciones/', notificaciones_views.obtener_notificaciones_dropdown_ajax, name='obtener_notificaciones_dropdown'),
    path('ajax/marcar-leida/', notificaciones_views.marcar_notificacion_leida_ajax, name='marcar_notificacion_leida'),
    path('ajax/datos-graficos/', estadisticas_views.datos_graficos_ajax, name='datos_graficos_ajax'),
    path('ajax/noticia/<int:pk>/', portal_views.ajax_noticia_detalle, name='ajax_noticia_detalle'),
    path('ajax/directorio-docentes/', portal_views.directorio_docentes_json, name='ajax_directorio_docentes'),
    path('ajax/documentos-publicos/', portal_views.documentos_publicos_json, name='ajax_documentos_publicos'),
    path('ajax/noticias/', portal_views.noticias_json, name='ajax_noticias'),
    path('ajax/carrusel/', portal_views.carrusel_imagenes_json, name='ajax_carrusel'),
    path('ajax/historia/', portal_views.ajax_historia, name='ajax_historia'),
    path('ajax/sedes/', portal_views.ajax_sedes_vista, name='ajax_sedes'),
    path('ajax/mision-vision/', portal_views.ajax_mision_vision, name='ajax_mision_vision'),
    path('ajax/modelo-pedagogico/', portal_views.ajax_modelo_pedagogico, name='ajax_modelo_pedagogico'),
    path('ajax/recursos-educativos/', portal_views.ajax_recursos_educativos, name='ajax_recursos_educativos'),
    path('ajax/redes-sociales/', portal_views.ajax_redes_sociales, name='ajax_redes_sociales'),
    path('ajax/galeria-fotos/', portal_views.ajax_galeria_vista, name='ajax_galeria_fotos'),
    path('ajax/obtener-meses/', consulta_views.ajax_obtener_meses_vista, name='ajax_obtener_meses'),

    # --- Rutas de Suplantación ---
    path('suplantar/iniciar/<int:user_id>/', impersonation_views.iniciar_suplantacion, name='iniciar_suplantacion'),
    path('suplantar/detener/', impersonation_views.detener_suplantacion, name='detener_suplantacion'),

    path('admin/gestion-academica/curso/<int:curso_id>/', gestion_academica_views.detalle_curso, name='detalle_curso'),
    path('admin/gestion-academica/asignacion/editar/<int:asignacion_id>/', gestion_academica_views.editar_asignacion_vista, name='editar_asignacion'),
    path('admin/gestion-academica/asignacion/eliminar/<int:asignacion_id>/', gestion_academica_views.eliminar_asignacion_vista, name='eliminar_asignacion'),
    path('admin/gestion-academica/cursos/', gestion_academica_views.gestion_cursos_vista, name='gestion_cursos'),   
    path('admin/gestion-academica/area/<int:area_id>/', gestion_academica_views.detalle_area, name='detalle_area'),
    path('admin/gestion-academica/docente/<int:docente_id>/', gestion_academica_views.detalle_docente, name='detalle_docente'),
    path('admin/gestion-academica/asignar-director-grado/', gestion_academica_views.asignar_director_grado_vista, name='asignar_director_grado'),
    # === INICIO DE LA CORRECCIÓN ===
    # Se corrigió el error de tipeo de 'gestion_acemica_views' a 'gestion_academica_views'.
    path('admin/gestion-academica/cursos/reordenar/<int:curso_id>/<str:direccion>/', gestion_academica_views.reordenar_curso_vista, name='reordenar_curso'),
    # === FIN DE LA CORRECCIÓN ===
]
