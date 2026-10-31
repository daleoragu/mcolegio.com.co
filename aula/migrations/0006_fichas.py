from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("aula", "0005_planilla_individual"),
    ]

    operations = [
        migrations.AddField(model_name="tarea", name="ficha", field=models.JSONField(blank=True, default=dict)),
        migrations.AddField(model_name="tarea", name="ficha_config", field=models.JSONField(blank=True, default=dict)),
        migrations.AddField(model_name="entrega", name="respuestas", field=models.JSONField(blank=True, default=dict)),
        migrations.AddField(model_name="entrega", name="manuales", field=models.JSONField(blank=True, default=dict)),
        migrations.AddField(model_name="entrega", name="intentos", field=models.PositiveSmallIntegerField(default=0)),
        migrations.AddField(model_name="entrega", name="iniciada", field=models.DateTimeField(blank=True, null=True)),
    ]
