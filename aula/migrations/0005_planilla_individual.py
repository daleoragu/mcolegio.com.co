import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("aula", "0004_para_y_vistos"),
        ("notas", "0053_escalas_especiales"),
        ("salon_digital", "0002_paginapublicada_comentarios_and_more"),
    ]

    operations = [
        migrations.AddField(model_name="aula", name="planilla",
                            field=models.JSONField(blank=True, default=dict)),
        migrations.CreateModel(
            name="ColumnaManual",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("titulo", models.CharField(max_length=60)),
                ("orden", models.PositiveSmallIntegerField(default=0)),
                ("creada", models.DateTimeField(auto_now_add=True)),
                ("aula", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,
                                           related_name="columnas_manuales", to="aula.aula")),
            ],
            options={"ordering": ["orden", "id"]},
        ),
        migrations.CreateModel(
            name="NotaManual",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("nota", models.DecimalField(decimal_places=2, max_digits=5)),
                ("columna", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="notas",
                                              to="aula.columnamanual")),
                ("estudiante", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE,
                                                 related_name="+", to="notas.estudiante")),
                ("integrante", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE,
                                                 related_name="+", to="salon_digital.integrante")),
            ],
        ),
    ]
