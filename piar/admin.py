from django.contrib import admin

from .models import AjustePiar, Piar


class AjusteInline(admin.TabularInline):
    model = AjustePiar
    extra = 0
    fields = ('materia', 'periodo', 'docente', 'ajustes')


@admin.register(Piar)
class PiarAdmin(admin.ModelAdmin):
    list_display = ('estudiante', 'ano_lectivo', 'colegio', 'estado', 'categoria')
    list_filter = ('colegio', 'ano_lectivo', 'estado')
    search_fields = ('estudiante__user__first_name', 'estudiante__user__last_name')
    inlines = [AjusteInline]
