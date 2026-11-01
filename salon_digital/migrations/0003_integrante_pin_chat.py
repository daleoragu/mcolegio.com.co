from django.db import migrations, models

import salon_digital.models


def pines_distintos(apps, schema_editor):
    """Al agregar el campo todos quedan con el mismo PIN: a cada estudiante se le da el suyo."""
    Integrante = apps.get_model('salon_digital', 'Integrante')
    for i in Integrante.objects.all().only('pk'):
        Integrante.objects.filter(pk=i.pk).update(pin_chat=salon_digital.models.pin_chat())


class Migration(migrations.Migration):

    dependencies = [
        ("salon_digital", "0002_paginapublicada_comentarios_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="integrante",
            name="pin_chat",
            field=models.CharField(default=salon_digital.models.pin_chat, max_length=4, verbose_name="PIN del chat",
                                   help_text="Lo necesita el estudiante para escribir en el chat y ver sus mensajes."),
        ),
        migrations.RunPython(pines_distintos, migrations.RunPython.noop),
    ]
