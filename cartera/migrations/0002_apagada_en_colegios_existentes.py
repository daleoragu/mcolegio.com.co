"""Cartera solo para quien la contrate: en los colegios que ya existían al
instalar los módulos queda apagada (los públicos son de matrícula cero). El
dueño de la plataforma la enciende en /plataforma/modulos/."""
from django.db import migrations


def apagar(apps, schema_editor):
    Colegio = apps.get_model('notas', 'Colegio')
    for c in Colegio.objects.all():
        mods = list(c.modulos_activos or [])
        if 'cartera' in mods:
            mods.remove('cartera')
            Colegio.objects.filter(pk=c.pk).update(modulos_activos=mods)


class Migration(migrations.Migration):
    dependencies = [('cartera', '0001_initial'), ('notas', '0042_modulos_activos')]
    operations = [migrations.RunPython(apagar, migrations.RunPython.noop)]
