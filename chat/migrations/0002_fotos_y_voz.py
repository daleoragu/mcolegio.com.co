from django.db import migrations, models

import aula.almacen
import chat.models


class Migration(migrations.Migration):

    dependencies = [
        ("chat", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="ajusteschat",
            name="permitir_fotos",
            field=models.BooleanField(default=True, verbose_name="Se pueden enviar fotos"),
        ),
        migrations.AddField(
            model_name="ajusteschat",
            name="permitir_voz",
            field=models.BooleanField(default=True, verbose_name="Se pueden enviar notas de voz"),
        ),
        migrations.AddField(
            model_name="mensaje",
            name="tipo",
            field=models.CharField(choices=[("texto", "Texto"), ("foto", "Foto"), ("voz", "Nota de voz")], default="texto",
                                   max_length=5),
        ),
        migrations.AlterField(
            model_name="mensaje",
            name="texto",
            field=models.TextField(blank=True, max_length=2000),
        ),
        migrations.AddField(
            model_name="mensaje",
            name="archivo",
            field=models.FileField(blank=True, storage=aula.almacen.privado, upload_to=chat.models.ruta_chat),
        ),
        migrations.AddField(
            model_name="mensaje",
            name="peso",
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name="mensaje",
            name="duracion",
            field=models.PositiveSmallIntegerField(default=0, help_text="Segundos de la nota de voz."),
        ),
    ]
