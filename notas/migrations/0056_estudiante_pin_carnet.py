import secrets

from django.db import migrations, models


def llenar_pines(apps, schema_editor):
    Estudiante = apps.get_model('notas', 'Estudiante')
    for est in Estudiante.objects.filter(pin_carnet='').only('pk').iterator():
        Estudiante.objects.filter(pk=est.pk).update(pin_carnet=f'{secrets.randbelow(10000):04d}')


class Migration(migrations.Migration):

    dependencies = [
        ('notas', '0055_estudiante_codigo_carnet'),
    ]

    operations = [
        migrations.AddField(
            model_name='estudiante',
            name='pin_carnet',
            field=models.CharField(blank=True, default='', max_length=6, verbose_name='PIN del carné'),
        ),
        migrations.AddField(
            model_name='estudiante',
            name='pin_fallidos',
            field=models.PositiveSmallIntegerField(default=0, editable=False),
        ),
        migrations.AddField(
            model_name='estudiante',
            name='pin_bloqueado_hasta',
            field=models.DateTimeField(blank=True, editable=False, null=True),
        ),
        migrations.RunPython(llenar_pines, migrations.RunPython.noop),
    ]
