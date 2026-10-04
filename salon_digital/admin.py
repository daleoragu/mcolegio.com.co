# salon_digital/admin.py
from django.contrib import admin
from django.utils.html import format_html

from .models import (
    Comentario, Cuenta, Detalle, Grupo, Integrante, Opcion, PaginaPublicada,
    Pregunta, Prueba, Sesion,
)


@admin.register(Cuenta)
class CuentaAdmin(admin.ModelAdmin):
    list_display = ('nombre_publico', 'slug', 'institucion', 'estado', 'plan', 'vence_en', 'creada_en')
    list_filter = ('estado', 'plan', 'departamento')
    search_fields = ('nombre_publico', 'slug', 'institucion', 'usuario__username', 'usuario__email')
    readonly_fields = ('creada_en', 'revisada_en', 'revisada_por')


class OpcionInline(admin.TabularInline):
    model = Opcion
    extra = 0


@admin.register(PaginaPublicada)
class PaginaPublicadaAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'propietario', 'enlace', 'visible', 'revisada',
                    'endpoint_reescrito', 'visitas', 'actualizada_en')
    list_filter = ('visible', 'revisada', 'tipo', 'area')
    search_fields = ('titulo', 'slug', 'propietario__slug')
    readonly_fields = ('visitas', 'endpoint_reescrito', 'alertas', 'creada_en', 'actualizada_en')

    @admin.display(description='Enlace')
    def enlace(self, obj):
        return format_html('<a href="{}" target="_blank">{}</a>', obj.ruta, obj.ruta)


@admin.register(Prueba)
class PruebaAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'propietario', 'area', 'grado', 'codigo', 'clave_panel',
                    'total_preguntas', 'activa')
    list_filter = ('area', 'grado', 'activa')
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
    list_display = ('completo', 'grupo', 'prueba_nombre', 'aciertos', 'total', 'porcentaje', 'fecha')
    list_filter = ('cuenta', 'grupo')
    search_fields = ('completo', 'apellidos', 'nombres')
    inlines = [DetalleInline]
    readonly_fields = ('payload', 'recibido_en', 'ip')


class IntegranteInline(admin.TabularInline):
    model = Integrante
    extra = 0
    fields = ('apellidos', 'nombres', 'activo')


@admin.register(Grupo)
class GrupoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'propietario', 'codigo', 'total_integrantes', 'activo', 'creado_en')
    list_filter = ('activo',)
    search_fields = ('nombre', 'codigo', 'propietario__slug')
    inlines = [IntegranteInline]


@admin.register(Comentario)
class ComentarioAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'pagina', 'aprobado', 'del_autor', 'creado_en')
    list_filter = ('aprobado', 'del_autor')
    search_fields = ('nombre', 'texto')
    readonly_fields = ('creado_en', 'ip')
