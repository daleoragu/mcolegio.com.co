from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("notas", "0050_familia"),
    ]

    operations = [
        migrations.AlterField(
            model_name="estudiante",
            name="es_inclusion",
            field=models.BooleanField(
                default=False,
                help_text="Marcar si el estudiante pertenece al programa de inclusión. Cómo entra al puesto y al "
                          "promedio del curso se define en la configuración de calificaciones.",
                verbose_name="Estudiante de Inclusión"),
        ),
        migrations.AddField(
            model_name="configuracioncalificaciones",
            name="inclusion_en_promedio_curso",
            field=models.BooleanField(
                default=True,
                help_text="Si se apaga, el promedio del curso, el ranking de cursos y las estadísticas generales se "
                          "calculan sin ellos. Sus notas y su boletín no cambian.",
                verbose_name="Los estudiantes de inclusión cuentan en el promedio del curso"),
        ),
        migrations.AddField(
            model_name="configuracioncalificaciones",
            name="inclusion_puesto",
            field=models.CharField(
                choices=[("GENERAL", "Compiten por el puesto con todo el curso"),
                         ("APARTE", "Tienen su propio puesto, entre los estudiantes de inclusión del curso"),
                         ("SIN", "No se les asigna puesto")],
                default="GENERAL", help_text="En el boletín, el boletín final y la sábana.", max_length=10,
                verbose_name="Puesto de los estudiantes de inclusión"),
        ),
    ]
