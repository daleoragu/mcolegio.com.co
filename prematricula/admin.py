from django.contrib import admin

from .models import Configuracion, Documento, PreguntaEncuesta, Requisito, Solicitud


@admin.register(Solicitud)
class SolicitudAdmin(admin.ModelAdmin):
    list_display = ('radicado', 'apellidos', 'nombres', 'grado', 'estado', 'colegio', 'creada')
    list_filter = ('colegio', 'estado', 'tipo', 'ano_lectivo')
    search_fields = ('radicado', 'apellidos', 'nombres', 'numero_documento')


admin.site.register([Configuracion, Requisito, PreguntaEncuesta, Documento])
