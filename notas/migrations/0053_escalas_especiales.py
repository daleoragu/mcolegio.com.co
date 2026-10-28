from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("notas", "0052_reporte_parcial_sugerencia"),
    ]

    operations = [
        migrations.CreateModel(
            name="EscalaEspecial",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("nombre", models.CharField(help_text="Ej.: «Escala de Inglés» o «Media técnica».", max_length=80,
                                            verbose_name="Nombre de la escala")),
                ("grados", models.JSONField(blank=True, default=list, verbose_name="Grados (vacío = todos)")),
                ("colegio", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,
                                              related_name="escalas_especiales", to="notas.colegio")),
                ("materias", models.ManyToManyField(blank=True, related_name="escalas_especiales", to="notas.materia",
                                                    verbose_name="Materias que la usan")),
            ],
            options={"verbose_name": "Escala especial", "verbose_name_plural": "Escalas especiales",
                     "ordering": ["nombre"]},
        ),
        migrations.CreateModel(
            name="NivelEscalaEspecial",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("nombre_desempeno", models.CharField(max_length=50, verbose_name="Desempeño")),
                ("valor_minimo", models.DecimalField(decimal_places=1, max_digits=4, verbose_name="Valor mínimo")),
                ("valor_maximo", models.DecimalField(decimal_places=1, max_digits=4, verbose_name="Valor máximo")),
                ("mensaje_boletin", models.TextField(blank=True)),
                ("escala", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="niveles",
                                             to="notas.escalaespecial")),
            ],
            options={"verbose_name": "Nivel de escala especial", "verbose_name_plural": "Niveles de escala especial",
                     "ordering": ["valor_minimo"], "unique_together": {("escala", "nombre_desempeno")}},
        ),
    ]
