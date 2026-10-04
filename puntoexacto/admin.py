# -*- coding: utf-8 -*-
from django.contrib import admin

from .models import Bloque, Examen, Hoja, Pregunta, Respuesta


class PreguntaEnLinea(admin.TabularInline):
    model = Pregunta
    extra = 0
    fields = ('numero', 'correcta', 'puntos', 'etiquetas', 'anulada')


@admin.register(Examen)
class ExamenAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'colegio', 'fecha', 'numero_preguntas', 'metodo', 'archivado')
    list_filter = ('colegio', 'archivado', 'metodo')
    search_fields = ('titulo',)
    inlines = [PreguntaEnLinea]


@admin.register(Hoja)
class HojaAdmin(admin.ModelAdmin):
    list_display = ('identificador', 'nombre', 'examen', 'estado', 'nota')
    list_filter = ('estado', 'examen__colegio')
    search_fields = ('identificador', 'nombre_libre')


admin.site.register(Respuesta)


@admin.register(Bloque)
class BloqueAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'examen', 'materia', 'orden', 'numero_opciones')
    list_filter = ('examen__colegio',)
    search_fields = ('nombre', 'examen__titulo')
