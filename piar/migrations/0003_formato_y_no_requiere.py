from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("piar", "0002_encender_piar"),
    ]

    operations = [
        migrations.AddField(
            model_name="configuracionpiar",
            name="formato",
            field=models.JSONField(blank=True, default=dict,
                                   help_text="Qué secciones y columnas salen (lo escoge la orientadora). Ver piar/formato.py.",
                                   verbose_name="Formato del PIAR"),
        ),
        migrations.AddField(
            model_name="piar",
            name="habilidades",
            field=models.JSONField(blank=True, default=dict, verbose_name="Registro de habilidades"),
        ),
        migrations.AddField(
            model_name="piar",
            name="otras_dimensiones",
            field=models.JSONField(blank=True, default=dict,
                                   verbose_name="Convivencia, socialización, participación, autonomía, autocontrol"),
        ),
        migrations.AddField(
            model_name="piar",
            name="recomendaciones_actores",
            field=models.JSONField(blank=True, default=dict,
                                   verbose_name="Recomendaciones para el plan de mejoramiento por actor"),
        ),
        migrations.AddField(
            model_name="ajustepiar",
            name="apoyos",
            field=models.TextField(blank=True, verbose_name="Apoyo requerido"),
        ),
        migrations.AddField(
            model_name="ajustepiar",
            name="no_requiere",
            field=models.BooleanField(default=False, verbose_name="No requiere ajustes razonables en esta asignatura"),
        ),
    ]
