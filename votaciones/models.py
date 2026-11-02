"""Elecciones del gobierno escolar (Ley 115 art. 94, Decreto 1860): personero, contralor, voceros de curso
y los cargos que el colegio agregue.

El voto es secreto: VotoEmitido guarda QUE la persona votó (para que no vote dos veces) y Papeleta guarda POR
QUIÉN, sin persona, sin hora y con un identificador al azar, de modo que no se pueden cruzar.
"""
import uuid

from django.contrib.auth.models import User
from django.db import models

from aula import almacen


def ruta_foto(instancia, nombre):
    return almacen._ruta(f'votaciones/{instancia.cargo.eleccion_id}', nombre)


class Eleccion(models.Model):
    ESTADOS = [('preparacion', 'En preparación'), ('abierta', 'Votación abierta'), ('cerrada', 'Cerrada')]
    colegio = models.ForeignKey('notas.Colegio', on_delete=models.CASCADE, related_name='elecciones_escolares')
    nombre = models.CharField(max_length=120, default='Elección del gobierno escolar')
    estado = models.CharField(max_length=12, choices=ESTADOS, default='preparacion')
    abierta_en = models.DateTimeField(null=True, blank=True)
    cerrada_en = models.DateTimeField(null=True, blank=True)
    creada = models.DateTimeField(auto_now_add=True)
    creada_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='+')

    class Meta:
        ordering = ['-creada']

    def __str__(self):
        return self.nombre


class Cargo(models.Model):
    VOTAN = [('estudiantes', 'Todos los estudiantes'), ('grados', 'Estudiantes de algunos grados'),
             ('curso', 'Cada curso elige el suyo'), ('docentes', 'Los docentes')]
    eleccion = models.ForeignKey(Eleccion, on_delete=models.CASCADE, related_name='cargos')
    nombre = models.CharField(max_length=80)
    votan = models.CharField(max_length=12, choices=VOTAN, default='estudiantes')
    grado_desde = models.SmallIntegerField(null=True, blank=True)
    grado_hasta = models.SmallIntegerField(null=True, blank=True)
    voto_blanco = models.BooleanField(default=True, verbose_name='Permitir voto en blanco')
    orden = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ['orden', 'id']

    def __str__(self):
        return self.nombre


class Candidato(models.Model):
    cargo = models.ForeignKey(Cargo, on_delete=models.CASCADE, related_name='candidatos')
    nombre = models.CharField(max_length=150)
    usuario = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='+')
    curso = models.ForeignKey('notas.Curso', on_delete=models.SET_NULL, null=True, blank=True, related_name='+',
                              help_text='Para el vocero: el curso que lo elige.')
    numero = models.PositiveSmallIntegerField(default=1)
    foto = models.ImageField(upload_to=ruta_foto, storage=almacen.privado, blank=True)
    propuesta = models.TextField(blank=True, max_length=1500)

    class Meta:
        ordering = ['numero', 'id']

    def __str__(self):
        return f'{self.numero}. {self.nombre}'


class VotoEmitido(models.Model):
    """Quién ya votó en la elección (no por quién)."""
    MEDIOS = [('cuenta', 'Con su cuenta'), ('mesa', 'En la mesa de votación')]
    eleccion = models.ForeignKey(Eleccion, on_delete=models.CASCADE, related_name='votantes')
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='+')
    curso = models.ForeignKey('notas.Curso', on_delete=models.SET_NULL, null=True, blank=True, related_name='+')
    medio = models.CharField(max_length=6, choices=MEDIOS, default='cuenta')
    jurado = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='+')
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['eleccion', 'usuario'], name='votaciones_un_voto_por_persona')]


class Papeleta(models.Model):
    """Un voto por un cargo. Sin persona ni hora: el voto es secreto."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    cargo = models.ForeignKey(Cargo, on_delete=models.CASCADE, related_name='papeletas')
    candidato = models.ForeignKey(Candidato, on_delete=models.CASCADE, null=True, blank=True, related_name='papeletas',
                                  help_text='Vacío: voto en blanco.')
    curso = models.ForeignKey('notas.Curso', on_delete=models.SET_NULL, null=True, blank=True, related_name='+')
