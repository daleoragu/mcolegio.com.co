"""Mis materiales: guías, talleres, evaluaciones y fichas que el docente arma por bloques.

El contenido del documento es un JSON (ver bloques.py). Las imágenes que el docente pega se
guardan en el Space privado, comprimidas, y cuentan en su nube.
"""
import os
import uuid

from django.contrib.auth.models import User
from django.db import models

from aula import almacen


def _ruta_imagen(instancia, nombre):
    ext = os.path.splitext(nombre or '')[1].lower()[:6] or '.jpg'
    return f'materiales/{instancia.propietario_id}/img/{uuid.uuid4().hex[:16]}{ext}'


def _ruta_logo(instancia, nombre):
    ext = os.path.splitext(nombre or '')[1].lower()[:6] or '.png'
    return f'materiales/{instancia.usuario_id}/logo/{uuid.uuid4().hex[:12]}{ext}'


class Documento(models.Model):
    TIPOS = [
        ('guia_momentos', 'Guía por momentos'),
        ('escuela_nueva', 'Guía Escuela Nueva'),
        ('institucional', 'Guía con el formato del colegio'),
        ('taller', 'Taller'),
        ('evaluacion', 'Evaluación'),
        ('ficha', 'Ficha de lectura'),
        ('cuadernillo', 'Cuadernillo tipo Saber'),
        ('ficha_pdf', 'Ficha sobre un PDF'),
        ('libre', 'Documento en blanco'),
    ]
    propietario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='materiales')
    colegio = models.ForeignKey('notas.Colegio', on_delete=models.CASCADE, null=True, blank=True,
                                related_name='materiales')
    titulo = models.CharField(max_length=150)
    tipo = models.CharField(max_length=16, choices=TIPOS, default='libre')
    area = models.CharField(max_length=80, blank=True, verbose_name='Área o asignatura')
    grado = models.CharField(max_length=40, blank=True)
    periodo = models.CharField(max_length=40, blank=True)
    contenido = models.JSONField(default=dict, blank=True)
    # Plantilla del colegio: el rector o coordinador la marca y los docentes la usan como modelo.
    plantilla_colegio = models.BooleanField(default=False)
    # El examen de PuntoExacto que se creó con este cuadernillo (su clave sale de aquí).
    examen = models.ForeignKey('puntoexacto.Examen', on_delete=models.SET_NULL, null=True, blank=True,
                               related_name='materiales')
    creado = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-actualizado']

    def __str__(self):
        return self.titulo


class Imagen(models.Model):
    propietario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='imagenes_materiales')
    archivo = models.FileField(upload_to=_ruta_imagen, storage=almacen.privado)
    ancho = models.PositiveIntegerField(default=0)
    alto = models.PositiveIntegerField(default=0)
    peso = models.PositiveIntegerField(default=0, help_text='Bytes, para la nube del docente.')
    creada = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Imagen {self.pk}'


class PreguntaBanco(models.Model):
    """Una pregunta guardada para volver a usarla. Si el docente la comparte, la ven los demás docentes
    de su colegio (la comunidad abierta llega después)."""
    propietario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='banco_preguntas')
    colegio = models.ForeignKey('notas.Colegio', on_delete=models.CASCADE, null=True, blank=True,
                                related_name='banco_preguntas')
    compartida = models.BooleanField(default=False)
    area = models.CharField(max_length=80, blank=True)
    grado = models.CharField(max_length=40, blank=True)
    tema = models.CharField(max_length=120, blank=True)
    modo = models.CharField(max_length=12, blank=True)
    bloque = models.JSONField(default=dict)
    texto = models.TextField(blank=True, help_text='Lo que se busca: enunciado, opciones y tema.')
    usos = models.PositiveIntegerField(default=0)
    creada = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-creada']

    def __str__(self):
        return self.texto[:60] or f'Pregunta {self.pk}'


class EncabezadoDocente(models.Model):
    """El encabezado del docente del plan individual (en el colegio se usa el del colegio)."""
    usuario = models.OneToOneField(User, on_delete=models.CASCADE, related_name='encabezado_materiales')
    logo = models.FileField(upload_to=_ruta_logo, storage=almacen.privado, blank=True)
    linea1 = models.CharField(max_length=120, blank=True)
    linea2 = models.CharField(max_length=120, blank=True)
    linea3 = models.CharField(max_length=120, blank=True)

    def __str__(self):
        return f'Encabezado de {self.usuario}'

    @property
    def lineas(self):
        return [x for x in (self.linea1, self.linea2, self.linea3) if x]
