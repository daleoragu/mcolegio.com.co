from django.apps import AppConfig


class NotasConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'notas'

    def ready(self):
        # Avisos automáticos (p. ej. estudiante nuevo -> sus docentes).
        from . import senales  # noqa: F401
