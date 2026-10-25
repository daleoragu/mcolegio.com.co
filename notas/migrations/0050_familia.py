import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("notas", "0049_push"),
    ]

    operations = [
        migrations.CreateModel(
            name="Familia",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("creada", models.DateTimeField(auto_now_add=True)),
                ("colegio", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="familias",
                                              to="notas.colegio")),
            ],
            options={"verbose_name": "Familia", "verbose_name_plural": "Familias"},
        ),
        migrations.AddField(
            model_name="estudiante",
            name="familia",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                                    related_name="miembros", to="notas.familia", verbose_name="Familia (hermanos)"),
        ),
        migrations.AlterField(
            model_name="suscripcionpush",
            name="endpoint",
            field=models.TextField(),
        ),
        migrations.AlterUniqueTogether(
            name="suscripcionpush",
            unique_together={("endpoint", "usuario")},
        ),
    ]
