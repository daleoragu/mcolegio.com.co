from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("notas", "0053_escalas_especiales"),
    ]

    operations = [
        migrations.AddField(
            model_name="colegio",
            name="correo_copias",
            field=models.EmailField(
                blank=True, max_length=255, verbose_name="Correo que recibe copia de los avisos",
                help_text="Le llega una copia oculta de cada correo que la plataforma manda a nombre del colegio "
                          "(observador, inasistencias, reportes, prematrícula) y una sola copia de cada circular. "
                          "Los enlaces para recuperar la contraseña no se copian."),
        ),
    ]
