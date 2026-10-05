# -*- coding: utf-8 -*-
import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('puntoexacto', '0003_examen_mostrar_docente_examen_mostrar_fecha'),
    ]

    operations = [
        migrations.AlterField(
            model_name='examen',
            name='metodo',
            field=models.CharField(choices=[('manual', 'Manual: el docente pone los puntos de cada pregunta y la nota es su suma'), ('con_piso', 'Con piso: 0 aciertos saca la nota mínima'), ('proporcional', 'Proporcional: 0 aciertos saca 0 (se ajusta a la mínima)'), ('descuento', 'Por descuento: arranca en la máxima y resta')], default='con_piso', max_length=14, verbose_name='Cómo se calcula la nota'),
        ),
        migrations.AddField(
            model_name='bloque',
            name='peso',
            field=models.DecimalField(blank=True, decimal_places=2, help_text='Vacío = proporcional a sus puntos.', max_digits=5, null=True, validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(100)], verbose_name='Peso en la nota final (%)'),
        ),
    ]
