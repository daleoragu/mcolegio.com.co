import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("puntoexacto", "0009_componentes_dinamicos"),
        ("notas", "0031_disenos_portal"),
    ]

    operations = [
        migrations.AddField(
            model_name="examen",
            name="compartido_por",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                                    related_name="+", to="notas.docente", verbose_name="Compartido por"),
        ),
        migrations.AddField(
            model_name="examen",
            name="compartido_por_nombre",
            field=models.CharField(blank=True, max_length=160),
        ),
    ]
