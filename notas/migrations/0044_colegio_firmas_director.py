from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("notas", "0043_colegio_nombre_app"),
    ]

    operations = [
        migrations.AddField(
            model_name="colegio",
            name="firmas_director",
            field=models.JSONField(
                blank=True,
                default=dict,
                help_text="En qué documentos sale la firma del director(a) de grado. Lo que no esté aquí usa el valor de fábrica.",
                verbose_name="Firma del director(a) de grado",
            ),
        ),
    ]
