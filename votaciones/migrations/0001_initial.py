import uuid

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models

import aula.almacen
import votaciones.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("notas", "0054_colegio_correo_copias"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Eleccion",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("nombre", models.CharField(default="Elección del gobierno escolar", max_length=120)),
                ("estado", models.CharField(choices=[("preparacion", "En preparación"), ("abierta", "Votación abierta"),
                                                     ("cerrada", "Cerrada")], default="preparacion", max_length=12)),
                ("abierta_en", models.DateTimeField(blank=True, null=True)),
                ("cerrada_en", models.DateTimeField(blank=True, null=True)),
                ("creada", models.DateTimeField(auto_now_add=True)),
                ("colegio", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,
                                              related_name="elecciones_escolares", to="notas.colegio")),
                ("creada_por", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                                                 related_name="+", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["-creada"]},
        ),
        migrations.CreateModel(
            name="Cargo",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("nombre", models.CharField(max_length=80)),
                ("votan", models.CharField(choices=[("estudiantes", "Todos los estudiantes"),
                                                    ("grados", "Estudiantes de algunos grados"),
                                                    ("curso", "Cada curso elige el suyo"), ("docentes", "Los docentes")],
                                           default="estudiantes", max_length=12)),
                ("grado_desde", models.SmallIntegerField(blank=True, null=True)),
                ("grado_hasta", models.SmallIntegerField(blank=True, null=True)),
                ("voto_blanco", models.BooleanField(default=True, verbose_name="Permitir voto en blanco")),
                ("orden", models.PositiveSmallIntegerField(default=0)),
                ("eleccion", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="cargos",
                                               to="votaciones.eleccion")),
            ],
            options={"ordering": ["orden", "id"]},
        ),
        migrations.CreateModel(
            name="Candidato",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("nombre", models.CharField(max_length=150)),
                ("numero", models.PositiveSmallIntegerField(default=1)),
                ("foto", models.ImageField(blank=True, storage=aula.almacen.privado, upload_to=votaciones.models.ruta_foto)),
                ("propuesta", models.TextField(blank=True, max_length=1500)),
                ("cargo", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="candidatos",
                                            to="votaciones.cargo")),
                ("curso", models.ForeignKey(blank=True, help_text="Para el vocero: el curso que lo elige.", null=True,
                                            on_delete=django.db.models.deletion.SET_NULL, related_name="+",
                                            to="notas.curso")),
                ("usuario", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                                              related_name="+", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["numero", "id"]},
        ),
        migrations.CreateModel(
            name="VotoEmitido",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("medio", models.CharField(choices=[("cuenta", "Con su cuenta"), ("mesa", "En la mesa de votación")],
                                           default="cuenta", max_length=6)),
                ("creado", models.DateTimeField(auto_now_add=True)),
                ("curso", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                                            related_name="+", to="notas.curso")),
                ("eleccion", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="votantes",
                                               to="votaciones.eleccion")),
                ("jurado", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                                             related_name="+", to=settings.AUTH_USER_MODEL)),
                ("usuario", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="+",
                                              to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name="Papeleta",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("candidato", models.ForeignKey(blank=True, help_text="Vacío: voto en blanco.", null=True,
                                                on_delete=django.db.models.deletion.CASCADE, related_name="papeletas",
                                                to="votaciones.candidato")),
                ("cargo", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="papeletas",
                                            to="votaciones.cargo")),
                ("curso", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                                            related_name="+", to="notas.curso")),
            ],
        ),
        migrations.AddConstraint(
            model_name="votoemitido",
            constraint=models.UniqueConstraint(fields=("eleccion", "usuario"), name="votaciones_un_voto_por_persona"),
        ),
    ]
