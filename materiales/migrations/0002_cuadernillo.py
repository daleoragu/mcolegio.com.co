import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("materiales", "0001_initial"),
        ("puntoexacto", "0011_grupo_integrante"),
    ]

    operations = [
        migrations.AlterField(
            model_name="documento", name="tipo",
            field=models.CharField(choices=[("guia_momentos", "Guía por momentos"), ("escuela_nueva", "Guía Escuela Nueva"), ("institucional", "Guía con el formato del colegio"), ("taller", "Taller"), ("evaluacion", "Evaluación"), ("ficha", "Ficha de lectura"), ("cuadernillo", "Cuadernillo tipo Saber"), ("libre", "Documento en blanco")], default="libre", max_length=16),
        ),
        migrations.AddField(
            model_name="documento", name="examen",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                                    related_name="materiales", to="puntoexacto.examen"),
        ),
    ]
