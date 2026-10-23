from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("circulares", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="circular",
            name="para",
            field=models.CharField(
                choices=[
                    ("FAMILIAS", "Todas las familias"),
                    ("CURSOS", "Familias de algunos cursos"),
                    ("DOCENTES", "Docentes"),
                    ("PERSONAL", "Docentes y personal administrativo"),
                    ("TODOS", "Familias, docentes y personal administrativo"),
                ],
                default="FAMILIAS",
                max_length=10,
                verbose_name="Para",
            ),
        ),
    ]
