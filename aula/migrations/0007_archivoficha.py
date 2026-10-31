import django.db.models.deletion
from django.db import migrations, models

import aula.almacen


class Migration(migrations.Migration):

    dependencies = [
        ("aula", "0006_fichas"),
    ]

    operations = [
        migrations.CreateModel(
            name="ArchivoFicha",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("bloque", models.CharField(max_length=20)),
                ("tipo", models.CharField(choices=[("foto", "Foto"), ("audio", "Audio")], default="foto", max_length=5)),
                ("archivo", models.FileField(storage=aula.almacen.privado, upload_to=aula.almacen.ruta_ficha)),
                ("peso", models.PositiveIntegerField(default=0)),
                ("creado", models.DateTimeField(auto_now_add=True)),
                ("entrega", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="archivos_ficha",
                                              to="aula.entrega")),
            ],
            options={"ordering": ["-creado"]},
        ),
    ]
