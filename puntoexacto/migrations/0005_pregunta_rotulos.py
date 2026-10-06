# -*- coding: utf-8 -*-
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('puntoexacto', '0004_metodo_manual_bloque_peso'),
    ]

    operations = [
        migrations.AddField(
            model_name='pregunta',
            name='rotulos',
            field=models.CharField(blank=True, help_text='Separadas por coma, máximo 2 caracteres cada una. Ej.: V,F', max_length=40, verbose_name='Etiquetas de las opciones'),
        ),
    ]
