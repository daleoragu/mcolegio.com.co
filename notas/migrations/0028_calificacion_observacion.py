from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('notas', '0027_administrador_colegio'),
    ]

    operations = [
        migrations.AddField(
            model_name='calificacion',
            name='observacion',
            field=models.TextField(blank=True, default='', verbose_name='Observación de la asignatura'),
        ),
    ]
