from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("chat", "0003_chat_salon"),
    ]

    operations = [
        migrations.AddField(
            model_name="ajusteschat",
            name="permitir_documentos",
            field=models.BooleanField(default=True, verbose_name="Se pueden enviar documentos (PDF, Word…)"),
        ),
        migrations.AlterField(
            model_name="mensaje",
            name="tipo",
            field=models.CharField(choices=[("texto", "Texto"), ("foto", "Foto"), ("voz", "Nota de voz"),
                                            ("doc", "Documento")], default="texto", max_length=5),
        ),
        migrations.AddField(
            model_name="mensaje",
            name="nombre_archivo",
            field=models.CharField(blank=True, help_text="Nombre original del documento.", max_length=150),
        ),
        migrations.AlterField(
            model_name="mensajesalon",
            name="tipo",
            field=models.CharField(choices=[("texto", "Texto"), ("foto", "Foto"), ("voz", "Nota de voz"),
                                            ("doc", "Documento")], default="texto", max_length=5),
        ),
        migrations.AddField(
            model_name="mensajesalon",
            name="nombre_archivo",
            field=models.CharField(blank=True, max_length=150),
        ),
    ]
