import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="AjusteCopia",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("destino", models.CharField(choices=[("google", "Google Drive"), ("onedrive", "OneDrive"),
                                                      ("descarga", "Descargar al dispositivo")], default="google",
                                             max_length=8)),
                ("cada_dias", models.PositiveSmallIntegerField(choices=[(1, "Cada día"), (7, "Cada semana"),
                                                                        (30, "Cada mes"), (0, "Solo cuando la pida")],
                                                               default=7)),
                ("incluir_medios", models.BooleanField(default=True, help_text="Fotos, notas de voz y adjuntos.")),
                ("ultima", models.DateTimeField(blank=True, null=True)),
                ("ultimo_peso", models.PositiveBigIntegerField(default=0)),
                ("ultimo_destino", models.CharField(blank=True, max_length=8)),
                ("usuario", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE,
                                                 related_name="ajuste_copia", to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
