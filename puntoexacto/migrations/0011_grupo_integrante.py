import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("puntoexacto", "0010_examen_compartido"),
        ("salon_digital", "0002_paginapublicada_comentarios_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="examen", name="grupo",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                                    related_name="examenes_puntoexacto", to="salon_digital.grupo",
                                    verbose_name="Grupo"),
        ),
        migrations.AddField(
            model_name="hoja", name="integrante",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE,
                                    related_name="hojas_puntoexacto", to="salon_digital.integrante"),
        ),
    ]
