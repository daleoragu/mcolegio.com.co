from django.contrib import admin

from .models import ConfiguracionSimat, DatosSimat

admin.site.register(ConfiguracionSimat)


@admin.register(DatosSimat)
class DatosSimatAdmin(admin.ModelAdmin):
    list_display = ('estudiante', 'genero', 'estrato', 'mpio_residencia', 'actualizado')
    search_fields = ('estudiante__user__first_name', 'estudiante__user__last_name')
