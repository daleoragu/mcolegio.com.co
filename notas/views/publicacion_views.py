# notas/views/publicacion_views.py

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import user_passes_test
from django.contrib import messages
from django.urls import reverse, NoReverseMatch
from itertools import groupby
# Se añade HttpResponseNotFound para manejar el caso de un colegio no identificado
from django.http import HttpResponseNotFound

from ..models import PeriodoAcademico, PublicacionBoletin, Notificacion, Estudiante, PublicacionBoletinFinal
from ..permisos import es_admin, es_admin_usuario

def es_admin(user):
    return es_admin_usuario(user)

@user_passes_test(es_admin)
def panel_publicacion_vista(request):
    """
    Gestiona la publicación de boletines, asegurando que todas las operaciones
    se realicen dentro del contexto del colegio actual.
    """
    if not request.colegio:
        return HttpResponseNotFound("<h1>Colegio no configurado</h1>")

    if request.method == 'POST':
        tipo_publicacion = request.POST.get('tipo_publicacion')
        accion = request.POST.get('accion')
        
        if tipo_publicacion == 'periodo':
            periodo_id = request.POST.get('periodo_id')
            try:
                # CORRECCIÓN: Filtrar periodo por el colegio actual.
                periodo = PeriodoAcademico.objects.get(id=periodo_id, colegio=request.colegio)
                
                # CORRECCIÓN: Obtener o crear la publicación para el colegio actual.
                publicacion, _ = PublicacionBoletin.objects.get_or_create(
                    periodo=periodo, 
                    colegio=request.colegio,
                    defaults={'publicado_por': request.user}
                )
                
                if accion == 'publicar':
                    publicacion.esta_visible = True
                    publicacion.publicado_por = request.user
                    publicacion.save()
                    messages.success(request, f"Los boletines del '{periodo}' han sido publicados.")
                elif accion == 'ocultar':
                    publicacion.esta_visible = False
                    publicacion.save()
                    messages.warning(request, f"Los boletines del '{periodo}' han sido ocultados.")

            except PeriodoAcademico.DoesNotExist:
                messages.error(request, "El periodo seleccionado no existe o no pertenece a este colegio.")

        elif tipo_publicacion == 'final':
            ano_lectivo = request.POST.get('ano_lectivo')
            try:
                # CORRECCIÓN: Obtener o crear la publicación para el colegio actual.
                publicacion, _ = PublicacionBoletinFinal.objects.get_or_create(
                    ano_lectivo=ano_lectivo, 
                    colegio=request.colegio,
                    defaults={'publicado_por': request.user}
                )

                if accion == 'publicar':
                    publicacion.esta_visible = True
                    publicacion.publicado_por = request.user
                    publicacion.save()
                    messages.success(request, f"El Informe Final del año {ano_lectivo} ha sido publicado y se ha notificado a los estudiantes.")
                    
                    # CORRECCIÓN: Notificar solo a los estudiantes del colegio actual.
                    estudiantes_a_notificar = Estudiante.objects.filter(
                        colegio=request.colegio,
                        calificacion__periodo__ano_lectivo=ano_lectivo
                    ).distinct().select_related('user')
                    
                    try:
                        url_boletin = reverse('mi_boletin')
                    except NoReverseMatch:
                        url_boletin = '#'

                    for est in estudiantes_a_notificar:
                        Notificacion.objects.create(
                            destinatario=est.user,
                            mensaje=f"Ya está disponible tu Informe Final del año {ano_lectivo}.",
                            tipo='GENERAL',
                            url=url_boletin,
                            colegio=request.colegio # Asociar la notificación al colegio
                        )
                elif accion == 'ocultar':
                    publicacion.esta_visible = False
                    publicacion.save()
                    messages.warning(request, f"El Informe Final del año {ano_lectivo} ha sido ocultado.")
            except Exception as e:
                messages.error(request, f"Error al procesar el informe final: {e}")

        return redirect('notas:panel_publicacion')

    # CORRECCIÓN: Filtrar periodos por el colegio actual.
    periodos = PeriodoAcademico.objects.filter(colegio=request.colegio).order_by('-ano_lectivo', 'fecha_inicio')
    periodos_agrupados = {k: list(v) for k, v in groupby(periodos, key=lambda p: p.ano_lectivo)}
    
    # CORRECCIÓN: Filtrar publicaciones por el colegio actual.
    publicaciones_periodos = set(PublicacionBoletin.objects.filter(esta_visible=True, colegio=request.colegio).values_list('periodo_id', flat=True))
    publicaciones_finales = set(PublicacionBoletinFinal.objects.filter(esta_visible=True, colegio=request.colegio).values_list('ano_lectivo', flat=True))
    
    context = {
        'periodos_agrupados': periodos_agrupados,
        'publicaciones_periodos': publicaciones_periodos,
        'publicaciones_finales': publicaciones_finales,
        'colegio': request.colegio
    }
    return render(request, 'notas/admin_tools/publicar_boletines.html', context)
