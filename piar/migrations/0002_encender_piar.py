"""El PIAR es obligatorio en todos los colegios (Decreto 1421): se enciende en
los que ya existen, salvo los que están en el plan Básico."""
from django.db import migrations

BASICO = {'circulares', 'certificados'}


def encender(apps, schema_editor):
    Colegio = apps.get_model('notas', 'Colegio')
    for c in Colegio.objects.all():
        mods = list(c.modulos_activos or [])
        if 'piar' in mods or set(mods) <= BASICO:
            continue
        mods.append('piar')
        Colegio.objects.filter(pk=c.pk).update(modulos_activos=mods)


class Migration(migrations.Migration):
    dependencies = [('piar', '0001_initial'), ('cartera', '0002_apagada_en_colegios_existentes')]
    operations = [migrations.RunPython(encender, migrations.RunPython.noop)]
