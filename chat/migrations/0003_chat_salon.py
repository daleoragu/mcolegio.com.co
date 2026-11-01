import django.db.models.deletion
from django.db import migrations, models

import aula.almacen
import chat.models


class Migration(migrations.Migration):

    dependencies = [
        ("chat", "0002_fotos_y_voz"),
        ("salon_digital", "0003_integrante_pin_chat"),
    ]

    operations = [
        migrations.CreateModel(
            name="ConversacionSalon",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("solo_lectura", models.BooleanField(default=False, help_text="Solo escribe el docente.")),
                ("docente_leido", models.DateTimeField(blank=True, null=True)),
                ("ultimo_mensaje", models.DateTimeField(blank=True, null=True)),
                ("creada", models.DateTimeField(auto_now_add=True)),
                ("grupo", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="chats",
                                            to="salon_digital.grupo")),
                ("integrante", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE,
                                                 related_name="chats", to="salon_digital.integrante")),
            ],
            options={"ordering": ["-ultimo_mensaje", "-creada"]},
        ),
        migrations.CreateModel(
            name="MensajeSalon",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("tipo", models.CharField(choices=[("texto", "Texto"), ("foto", "Foto"), ("voz", "Nota de voz")],
                                          default="texto", max_length=5)),
                ("texto", models.TextField(blank=True, max_length=2000)),
                ("archivo", models.FileField(blank=True, storage=aula.almacen.privado, upload_to=chat.models.ruta_salon)),
                ("peso", models.PositiveIntegerField(default=0)),
                ("duracion", models.PositiveSmallIntegerField(default=0)),
                ("creado", models.DateTimeField(auto_now_add=True)),
                ("eliminado", models.BooleanField(default=False)),
                ("conversacion", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="mensajes",
                                                   to="chat.conversacionsalon")),
                ("integrante", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE,
                                                 related_name="mensajes_chat", to="salon_digital.integrante")),
            ],
            options={"ordering": ["creado", "id"]},
        ),
        migrations.CreateModel(
            name="LecturaSalon",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("ultimo_leido", models.DateTimeField()),
                ("conversacion", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="lecturas",
                                                   to="chat.conversacionsalon")),
                ("integrante", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="+",
                                                 to="salon_digital.integrante")),
            ],
        ),
        migrations.AddConstraint(
            model_name="conversacionsalon",
            constraint=models.UniqueConstraint(fields=("grupo", "integrante"), name="chat_salon_una_por_integrante"),
        ),
        migrations.AddConstraint(
            model_name="conversacionsalon",
            constraint=models.UniqueConstraint(condition=models.Q(("integrante__isnull", True)), fields=("grupo",),
                                               name="chat_salon_uno_del_grupo"),
        ),
        migrations.AddConstraint(
            model_name="lecturasalon",
            constraint=models.UniqueConstraint(fields=("conversacion", "integrante"), name="chat_salon_una_lectura"),
        ),
    ]
