from django.contrib import admin

from .models import AplicacionEscritorio, Horario, Jornada

admin.site.register(Jornada)
admin.site.register(Horario)
admin.site.register(AplicacionEscritorio)
