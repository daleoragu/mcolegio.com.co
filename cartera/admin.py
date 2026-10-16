from django.contrib import admin

from .models import Aplicacion, Beca, Cargo, Concepto, ConfiguracionCartera, Pago, ValorPorGrado

for m in (Aplicacion, Beca, Cargo, Concepto, ConfiguracionCartera, Pago, ValorPorGrado):
    admin.site.register(m)
