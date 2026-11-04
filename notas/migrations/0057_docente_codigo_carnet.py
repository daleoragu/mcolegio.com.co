import secrets

from django.db import migrations, models


def llenar_codigos(apps, schema_editor):
    Docente = apps.get_model('notas', 'Docente')
    Estudiante = apps.get_model('notas', 'Estudiante')
    usados = set(Estudiante.objects.exclude(codigo_carnet=None).values_list('codigo_carnet', flat=True))
    for doc in Docente.objects.filter(codigo_carnet__isnull=True).only('pk').iterator():
        codigo = secrets.token_urlsafe(9)
        while codigo in usados:
            codigo = secrets.token_urlsafe(9)
        usados.add(codigo)
        Docente.objects.filter(pk=doc.pk).update(codigo_carnet=codigo)


class Migration(migrations.Migration):

    dependencies = [
        ('notas', '0056_estudiante_pin_carnet'),
    ]

    operations = [
        migrations.AddField(
            model_name='docente',
            name='codigo_carnet',
            field=models.CharField(blank=True, editable=False, max_length=16, null=True, unique=True,
                                   verbose_name='Código del carné'),
        ),
        migrations.RunPython(llenar_codigos, migrations.RunPython.noop),
    ]
