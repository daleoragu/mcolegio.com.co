from django.contrib import admin

from .models import CalificacionHistorica, CertificadoEmitido, ConfiguracionCertificados, SolicitudCertificado


@admin.register(CertificadoEmitido)
class CertificadoEmitidoAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'tipo', 'ano_lectivo', 'estudiante', 'colegio', 'emitido', 'anulado')
    list_filter = ('tipo', 'anulado', 'colegio')
    search_fields = ('codigo', 'estudiante__user__first_name', 'estudiante__user__last_name')


admin.site.register(CalificacionHistorica)
admin.site.register(ConfiguracionCertificados)
admin.site.register(SolicitudCertificado)
