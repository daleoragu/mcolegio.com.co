import secrets

from django.db import migrations, models


def llenar_codigos(apps, schema_editor):
    Estudiante = apps.get_model('notas', 'Estudiante')
    usados = set()
    for est in Estudiante.objects.filter(codigo_carnet__isnull=True).only('pk').iterator():
        codigo = secrets.token_urlsafe(9)
        while codigo in usados:
            codigo = secrets.token_urlsafe(9)
        usados.add(codigo)
        Estudiante.objects.filter(pk=est.pk).update(codigo_carnet=codigo)


class Migration(migrations.Migration):

    dependencies = [
        ('notas', '0054_colegio_correo_copias'),
    ]

    operations = [
        migrations.AddField(
            model_name='estudiante',
            name='codigo_carnet',
            field=models.CharField(blank=True, editable=False, max_length=16, null=True, unique=True,
                                   verbose_name='Código del carné'),
        ),
        migrations.RunPython(llenar_codigos, migrations.RunPython.noop),
    ]
