from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("piar", "0003_formato_y_no_requiere"),
        ("notas", "0048_periodo_orden"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="ajustepiar",
            options={"ordering": ["materia__nombre", "periodo__orden"]},
        ),
    ]
