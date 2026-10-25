import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("notas", "0048_periodo_orden"),
    ]

    operations = [
        migrations.CreateModel(
            name="ClavePush",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("privada", models.CharField(max_length=100)),
                ("publica", models.CharField(max_length=200)),
                ("creada", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "verbose_name": "Llave de notificaciones",
                "verbose_name_plural": "Llaves de notificaciones",
            },
        ),
        migrations.CreateModel(
            name="SuscripcionPush",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("endpoint", models.TextField(unique=True)),
                ("p256dh", models.CharField(max_length=200)),
                ("auth", models.CharField(max_length=100)),
                ("dispositivo", models.CharField(blank=True, max_length=200)),
                ("creada", models.DateTimeField(auto_now_add=True)),
                ("ultimo_envio", models.DateTimeField(blank=True, null=True)),
                ("colegio", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE,
                                              related_name="+", to="notas.colegio")),
                ("usuario", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,
                                              related_name="suscripciones_push", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "verbose_name": "Celular con notificaciones",
                "verbose_name_plural": "Celulares con notificaciones",
            },
        ),
    ]
