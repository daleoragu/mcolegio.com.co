# -*- coding: utf-8 -*-
# Grado y subgrupo en el curso, y el historial de matrícula por año.
#
# No toca ningún dato existente: los cursos que ya hay quedan con grado vacío
# y subgrupo vacío, y siguen funcionando igual que antes.
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models

GRADO_CHOICES = [
    ('Preescolar', [(-2, 'Prejardín'), (-1, 'Jardín'), (0, 'Transición')]),
    ('Primaria', [(1, 'Primero'), (2, 'Segundo'), (3, 'Tercero'), (4, 'Cuarto'), (5, 'Quinto')]),
    ('Básica Secundaria', [(6, 'Sexto'), (7, 'Séptimo'), (8, 'Octavo'), (9, 'Noveno')]),
    ('Media', [(10, 'Décimo'), (11, 'Undécimo')]),
]


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('notas', '0024_alter_registroobservador_subtipo'),
    ]

    operations = [
        migrations.AddField(
            model_name='curso',
            name='grado',
            field=models.SmallIntegerField(blank=True, choices=GRADO_CHOICES, help_text='Con el grado, el sistema sabe a qué curso pasan sus estudiantes al año siguiente.', null=True, verbose_name='Grado'),
        ),
        migrations.AddField(
            model_name='curso',
            name='subgrupo',
            field=models.CharField(blank=True, default='', help_text='Solo si el grado tiene varios grupos: 01, 02… o A, B… Déjelo vacío si hay un solo curso de ese grado.', max_length=10, verbose_name='Subgrupo (opcional)'),
        ),
        migrations.CreateModel(
            name='HistorialMatricula',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('ano_lectivo', models.PositiveIntegerField(verbose_name='Año lectivo')),
                ('curso_nombre', models.CharField(blank=True, max_length=100)),
                ('grado', models.SmallIntegerField(blank=True, null=True)),
                ('resultado', models.CharField(choices=[('PROMOVIDO', 'Promovido'), ('NO_PROMOVIDO', 'No promovido'), ('GRADUADO', 'Graduado'), ('RETIRADO', 'Retirado')], max_length=14)),
                ('estaba_activo', models.BooleanField(default=True)),
                ('registrado', models.DateTimeField(auto_now_add=True)),
                ('colegio', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='historial_matriculas', to='notas.colegio')),
                ('curso', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='historial_matriculas', to='notas.curso')),
                ('curso_destino', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to='notas.curso')),
                ('estudiante', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='historial_matriculas', to='notas.estudiante')),
                ('registrado_por', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Historial de matrícula',
                'verbose_name_plural': 'Historial de matrículas',
                'ordering': ['-ano_lectivo', 'curso_nombre'],
                'unique_together': {('estudiante', 'ano_lectivo')},
            },
        ),
    ]
