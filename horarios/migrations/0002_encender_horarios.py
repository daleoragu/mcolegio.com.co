"""Se enciende «Horarios» en los colegios que ya existen, salvo los del plan Básico.
El generador (Premium) no se enciende solo: lo activa el dueño de la plataforma."""
from django.db import migrations

BASICO = {'circulares', 'certificados'}


def encender(apps, schema_editor):
    Colegio = apps.get_model('notas', 'Colegio')
    for c in Colegio.objects.all():
        mods = list(c.modulos_activos or [])
        if 'horarios' in mods or set(mods) <= BASICO:
            continue
        mods.append('horarios')
        Colegio.objects.filter(pk=c.pk).update(modulos_activos=mods)


class Migration(migrations.Migration):
    dependencies = [('horarios', '0001_initial'), ('simat', '0002_encender_simat')]
    operations = [migrations.RunPython(encender, migrations.RunPython.noop)]
