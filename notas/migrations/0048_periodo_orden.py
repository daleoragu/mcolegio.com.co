from django.db import migrations, models

ORDEN = {'PRIMERO': 1, 'SEGUNDO': 2, 'TERCERO': 3, 'CUARTO': 4}


def llenar(apps, schema_editor):
    Periodo = apps.get_model('notas', 'PeriodoAcademico')
    for nombre, n in ORDEN.items():
        Periodo.objects.filter(nombre=nombre).update(orden=n)


class Migration(migrations.Migration):

    dependencies = [
        ("notas", "0047_mensaje_destacado_y_purgado"),
    ]

    operations = [
        migrations.AddField(
            model_name="periodoacademico",
            name="orden",
            field=models.PositiveSmallIntegerField(db_index=True, default=0, editable=False),
        ),
        migrations.RunPython(llenar, migrations.RunPython.noop),
        migrations.AlterModelOptions(
            name="periodoacademico",
            options={"ordering": ["-ano_lectivo", "orden", "fecha_inicio"], "verbose_name": "Periodo Académico",
                     "verbose_name_plural": "Periodos Académicos"},
        ),
        migrations.AlterModelOptions(
            name="publicacionboletin",
            options={"ordering": ["-periodo__ano_lectivo", "-periodo__orden"],
                     "verbose_name": "Publicación de Boletín de Periodo",
                     "verbose_name_plural": "Publicaciones de Boletines de Periodo"},
        ),
    ]
