"""Se enciende el módulo SIMAT en los colegios que ya existen, salvo los del plan Básico."""
from django.db import migrations

BASICO = {'circulares', 'certificados'}


def encender(apps, schema_editor):
    Colegio = apps.get_model('notas', 'Colegio')
    for c in Colegio.objects.all():
        mods = list(c.modulos_activos or [])
        if 'simat' in mods or set(mods) <= BASICO:
            continue
        mods.append('simat')
        Colegio.objects.filter(pk=c.pk).update(modulos_activos=mods)


class Migration(migrations.Migration):
    dependencies = [('simat', '0001_initial'), ('piar', '0002_encender_piar')]
    operations = [migrations.RunPython(encender, migrations.RunPython.noop)]
