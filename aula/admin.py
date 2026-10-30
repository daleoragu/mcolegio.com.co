from django.contrib import admin

from .models import Aula, Instrumento, Tarea


@admin.register(Aula)
class AulaAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'colegio', 'creada')


@admin.register(Instrumento)
class InstrumentoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'tipo', 'propietario', 'colegio')


@admin.register(Tarea)
class TareaAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'aula', 'fecha_limite', 'publicada')
