import django.db.models.deletion
from django.db import migrations, models

TIPOS = [("I", "Tipo I"), ("II", "Tipo II"), ("III", "Tipo III")]


class Migration(migrations.Migration):

    dependencies = [
        ("notas", "0044_colegio_firmas_director"),
    ]

    operations = [
        migrations.CreateModel(
            name="FaltaCatalogo",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("tipo_falta", models.CharField(choices=TIPOS, max_length=3, verbose_name="Tipo")),
                ("numeral", models.CharField(blank=True, default="", help_text="Por ejemplo «Art. 45, num. 3». Opcional.",
                                             max_length=40, verbose_name="Numeral del manual")),
                ("descripcion", models.TextField(verbose_name="Descripción")),
                ("activa", models.BooleanField(default=True)),
                ("colegio", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,
                                              related_name="faltas_catalogo", to="notas.colegio")),
            ],
            options={
                "verbose_name": "Falta del catálogo",
                "verbose_name_plural": "Catálogo de faltas",
                "ordering": ["tipo_falta", "numeral", "id"],
            },
        ),
        migrations.AddField(
            model_name="registroobservador",
            name="falta",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                                    related_name="registros", to="notas.faltacatalogo",
                                    verbose_name="Falta del catálogo"),
        ),
        migrations.AddField(
            model_name="registroobservador",
            name="tipo_falta",
            field=models.CharField(blank=True, choices=TIPOS, default="", max_length=3, verbose_name="Tipo de falta"),
        ),
    ]
