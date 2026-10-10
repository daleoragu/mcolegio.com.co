import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("actas", "0001_initial"),
        ("notas", "0031_disenos_portal"),
    ]

    operations = [
        migrations.AddField(
            model_name="acta",
            name="estilo_firma",
            field=models.CharField(
                choices=[("CUADRO", "Cuadro: nombre, cargo y firma"),
                         ("LINEAS", "Línea de firma con el nombre debajo")],
                default="CUADRO", max_length=10, verbose_name="Cómo salen las firmas"),
        ),
        migrations.CreateModel(
            name="RedactorActas",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("creado_en", models.DateTimeField(auto_now_add=True)),
                ("colegio", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,
                                              related_name="redactores_actas", to="notas.colegio")),
                ("docente", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE,
                                                 related_name="rol_actas", to="notas.docente")),
            ],
            options={"verbose_name": "Docente que genera actas",
                     "verbose_name_plural": "Docentes que generan actas"},
        ),
    ]
