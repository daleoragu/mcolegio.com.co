import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models

import aula.almacen
import materiales.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("notas", "0053_escalas_especiales"),
    ]

    operations = [
        migrations.CreateModel(
            name="Documento",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("titulo", models.CharField(max_length=150)),
                ("tipo", models.CharField(choices=[("guia_momentos", "Guía por momentos"), ("escuela_nueva", "Guía Escuela Nueva"), ("institucional", "Guía con el formato del colegio"), ("taller", "Taller"), ("evaluacion", "Evaluación"), ("ficha", "Ficha de lectura"), ("libre", "Documento en blanco")], default="libre", max_length=16)),
                ("area", models.CharField(blank=True, max_length=80, verbose_name="Área o asignatura")),
                ("grado", models.CharField(blank=True, max_length=40)),
                ("periodo", models.CharField(blank=True, max_length=40)),
                ("contenido", models.JSONField(blank=True, default=dict)),
                ("plantilla_colegio", models.BooleanField(default=False)),
                ("creado", models.DateTimeField(auto_now_add=True)),
                ("actualizado", models.DateTimeField(auto_now=True)),
                ("colegio", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE,
                                              related_name="materiales", to="notas.colegio")),
                ("propietario", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,
                                                  related_name="materiales", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["-actualizado"]},
        ),
        migrations.CreateModel(
            name="Imagen",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("archivo", models.FileField(storage=aula.almacen.privado, upload_to=materiales.models._ruta_imagen)),
                ("ancho", models.PositiveIntegerField(default=0)),
                ("alto", models.PositiveIntegerField(default=0)),
                ("peso", models.PositiveIntegerField(default=0, help_text="Bytes, para la nube del docente.")),
                ("creada", models.DateTimeField(auto_now_add=True)),
                ("propietario", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,
                                                  related_name="imagenes_materiales", to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name="EncabezadoDocente",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("logo", models.FileField(blank=True, storage=aula.almacen.privado, upload_to=materiales.models._ruta_logo)),
                ("linea1", models.CharField(blank=True, max_length=120)),
                ("linea2", models.CharField(blank=True, max_length=120)),
                ("linea3", models.CharField(blank=True, max_length=120)),
                ("usuario", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE,
                                                 related_name="encabezado_materiales", to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
