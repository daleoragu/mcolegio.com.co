from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("notas", "0051_inclusion_puesto"),
    ]

    operations = [
        migrations.AddField(
            model_name="reporteparcial",
            name="sugerencia",
            field=models.TextField(blank=True, default="", verbose_name="Qué le falta o qué debe entregar para mejorar"),
        ),
    ]
