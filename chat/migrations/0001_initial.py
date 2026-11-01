import datetime

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("notas", "0054_colegio_correo_copias"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="AjustesChat",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("silencio_desde", models.TimeField(default=datetime.time(18, 0), verbose_name="Silencio desde")),
                ("silencio_hasta", models.TimeField(default=datetime.time(6, 0), verbose_name="Silencio hasta")),
                ("silencio_fin_de_semana", models.BooleanField(default=True, verbose_name="Silencio sábados y domingos")),
                ("colegio", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="ajustes_chat",
                                                 to="notas.colegio")),
            ],
        ),
        migrations.CreateModel(
            name="Conversacion",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("tipo", models.CharField(choices=[("directa", "Uno a uno"), ("curso", "Grupo del curso"),
                                                   ("asignatura", "Grupo de la asignatura"),
                                                   ("profesores", "Sala de profesores"), ("grupo", "Grupo")],
                                          max_length=10)),
                ("nombre", models.CharField(blank=True, max_length=80)),
                ("clave", models.CharField(blank=True, max_length=40)),
                ("solo_lectura", models.BooleanField(default=False, help_text="Solo los moderadores escriben.")),
                ("creada", models.DateTimeField(auto_now_add=True)),
                ("ultimo_mensaje", models.DateTimeField(blank=True, null=True)),
                ("asignacion", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE,
                                                 related_name="+", to="notas.asignaciondocente")),
                ("colegio", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,
                                              related_name="conversaciones_chat", to="notas.colegio")),
                ("creada_por", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                                                 related_name="+", to=settings.AUTH_USER_MODEL)),
                ("curso", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE,
                                            related_name="+", to="notas.curso")),
            ],
            options={
                "ordering": ["-ultimo_mensaje", "-creada"],
                "constraints": [models.UniqueConstraint(condition=models.Q(("clave", ""), _negated=True),
                                                        fields=("colegio", "clave"),
                                                        name="chat_una_conversacion_por_clave")],
            },
        ),
        migrations.CreateModel(
            name="Mensaje",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("texto", models.TextField(max_length=2000)),
                ("creado", models.DateTimeField(auto_now_add=True)),
                ("eliminado", models.BooleanField(default=False)),
                ("autor", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="mensajes_chat",
                                            to=settings.AUTH_USER_MODEL)),
                ("conversacion", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="mensajes",
                                                   to="chat.conversacion")),
                ("eliminado_por", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                                                    related_name="+", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["creado", "id"]},
        ),
        migrations.CreateModel(
            name="Participante",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("moderador", models.BooleanField(default=False)),
                ("silenciada", models.BooleanField(default=False, help_text="No avisa de los mensajes nuevos.")),
                ("ultimo_leido", models.DateTimeField(blank=True, null=True)),
                ("activo", models.BooleanField(default=True, help_text="Falso cuando sale del grupo o deja el curso.")),
                ("conversacion", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,
                                                   related_name="participantes", to="chat.conversacion")),
                ("usuario", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="chats",
                                              to=settings.AUTH_USER_MODEL)),
            ],
            options={"constraints": [models.UniqueConstraint(fields=("conversacion", "usuario"), name="chat_un_participante")]},
        ),
        migrations.CreateModel(
            name="Reporte",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("motivo", models.CharField(max_length=300)),
                ("creado", models.DateTimeField(auto_now_add=True)),
                ("resuelto", models.BooleanField(default=False)),
                ("nota", models.CharField(blank=True, help_text="Qué se hizo.", max_length=300)),
                ("mensaje", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="reportes",
                                              to="chat.mensaje")),
                ("resuelto_por", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                                                   related_name="+", to=settings.AUTH_USER_MODEL)),
                ("usuario", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="+",
                                              to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "ordering": ["resuelto", "-creado"],
                "constraints": [models.UniqueConstraint(fields=("mensaje", "usuario"), name="chat_un_reporte")],
            },
        ),
    ]
