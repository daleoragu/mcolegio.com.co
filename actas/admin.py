from django.contrib import admin

from .models import Acta


@admin.register(Acta)
class ActaAdmin(admin.ModelAdmin):
    list_display = ('numero', 'ano', 'titulo', 'colegio', 'tipo', 'estado', 'fecha')
    list_filter = ('colegio', 'tipo', 'estado', 'ano')
