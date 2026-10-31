import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("materiales", "0002_cuadernillo"),
        ("notas", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterField(
            model_name="documento", name="tipo",
            field=models.CharField(choices=[("guia_momentos", "Guía por momentos"), ("escuela_nueva", "Guía Escuela Nueva"), ("institucional", "Guía con el formato del colegio"), ("taller", "Taller"), ("evaluacion", "Evaluación"), ("ficha", "Ficha de lectura"), ("cuadernillo", "Cuadernillo tipo Saber"), ("ficha_pdf", "Ficha sobre un PDF"), ("libre", "Documento en blanco")], default="libre", max_length=16),
        ),
        migrations.CreateModel(
            name="PreguntaBanco",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("compartida", models.BooleanField(default=False)),
                ("area", models.CharField(blank=True, max_length=80)),
                ("grado", models.CharField(blank=True, max_length=40)),
                ("tema", models.CharField(blank=True, max_length=120)),
                ("modo", models.CharField(blank=True, max_length=12)),
                ("bloque", models.JSONField(default=dict)),
                ("texto", models.TextField(blank=True, help_text="Lo que se busca: enunciado, opciones y tema.")),
                ("usos", models.PositiveIntegerField(default=0)),
                ("creada", models.DateTimeField(auto_now_add=True)),
                ("colegio", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE,
                                              related_name="banco_preguntas", to="notas.colegio")),
                ("propietario", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,
                                                  related_name="banco_preguntas", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["-creada"]},
        ),
    ]
