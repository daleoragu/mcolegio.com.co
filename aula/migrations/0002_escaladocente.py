import aula.models
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("aula", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="EscalaDocente",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("niveles", models.JSONField(default=aula.models._escala_nacional)),
                ("actualizada", models.DateTimeField(auto_now=True)),
                ("usuario", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE,
                                                 related_name="escala_aula", to=settings.AUTH_USER_MODEL)),
            ],
            options={"verbose_name": "Escala del docente", "verbose_name_plural": "Escalas de los docentes"},
        ),
    ]
