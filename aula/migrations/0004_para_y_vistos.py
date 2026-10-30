import django.db.models.deletion
from django.db import migrations, models

AYUDA = 'Vacío: toda la clase. Si no, solo los estudiantes escogidos.'


class Migration(migrations.Migration):

    dependencies = [
        ("aula", "0003_actividades_cuestionarios"),
        ("notas", "0053_escalas_especiales"),
        ("salon_digital", "0002_paginapublicada_comentarios_and_more"),
    ]

    operations = [
        migrations.AddField(model_name="actividad", name="para",
                            field=models.JSONField(blank=True, default=list, help_text=AYUDA)),
        migrations.AddField(model_name="material", name="para",
                            field=models.JSONField(blank=True, default=list, help_text=AYUDA)),
        migrations.AddField(model_name="tarea", name="para",
                            field=models.JSONField(blank=True, default=list, help_text=AYUDA)),
        migrations.CreateModel(
            name="Visto",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("secciones", models.JSONField(blank=True, default=dict)),
                ("aula", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="vistos",
                                           to="aula.aula")),
                ("estudiante", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE,
                                                 related_name="+", to="notas.estudiante")),
                ("integrante", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE,
                                                 related_name="+", to="salon_digital.integrante")),
            ],
        ),
    ]
