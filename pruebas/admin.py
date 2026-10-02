# pruebas/admin.py
from django.contrib import admin
from django.utils.html import format_html

from .models import Detalle, Opcion, PaginaPublicada, Pregunta, Prueba, Sesion


class OpcionInline(admin.TabularInline):
    model = Opcion
    extra = 0


@admin.register(PaginaPublicada)
class PaginaPublicadaAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'colegio', 'enlace', 'visible', 'endpoint_reescrito', 'visitas', 'actualizada_en')
    list_filter = ('colegio', 'visible', 'area')
    search_fields = ('titulo', 'slug')
    readonly_fields = ('visitas', 'endpoint_reescrito', 'creada_en', 'actualizada_en')

    @admin.display(description='Enlace')
    def enlace(self, obj):
        return format_html('<a href="{}" target="_blank">{}</a>', obj.ruta, obj.ruta)


@admin.register(Prueba)
class PruebaAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'colegio', 'area', 'grado', 'codigo', 'clave_panel', 'total_preguntas', 'activa')
    list_filter = ('colegio', 'area', 'grado', 'activa')
    search_fields = ('titulo', 'codigo')


@admin.register(Pregunta)
class PreguntaAdmin(admin.ModelAdmin):
    list_display = ('prueba', 'orden', 'competencia', 'tema', 'clave', 'pct_referencia')
    list_filter = ('prueba', 'competencia')
    search_fields = ('tema', 'enunciado', 'pregunta')
    inlines = [OpcionInline]


class DetalleInline(admin.TabularInline):
    model = Detalle
    extra = 0
    can_delete = False
    readonly_fields = [f.name for f in Detalle._meta.fields if f.name != 'id']


@admin.register(Sesion)
class SesionAdmin(admin.ModelAdmin):
    list_display = ('completo', 'grupo', 'prueba_nombre', 'aciertos', 'total', 'porcentaje', 'estudiante', 'fecha')
    list_filter = ('colegio', 'pagina', 'prueba', 'grupo')
    search_fields = ('completo', 'apellidos', 'nombres')
    autocomplete_fields = ()
    inlines = [DetalleInline]
    readonly_fields = ('payload', 'recibido_en', 'ip')
