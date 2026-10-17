"""Horarios de clase: franjas, reglas, versiones del horario y el generador.

* Jornada y Franja: las horas de clase y los descansos de cada jornada, y qué
  cursos van en ella.
* Las condiciones (bloques dobles, horas en que el docente no puede, clases
  fijadas…) no viven aquí: se ponen en la app de escritorio del generador.
* Horario y Sesion: una versión del horario (borrador o publicado). Una sesión
  es una clase: curso + asignación (materia y docente) + día + franja.
* AplicacionEscritorio: el instalador del generador (plan Premium).
"""
from django.db import models

from notas.models import AsignacionDocente, Colegio, Curso

DIAS = [(1, 'Lunes'), (2, 'Martes'), (3, 'Miércoles'), (4, 'Jueves'), (5, 'Viernes'), (6, 'Sábado')]
DIA_CORTO = {1: 'Lun', 2: 'Mar', 3: 'Mié', 4: 'Jue', 5: 'Vie', 6: 'Sáb'}


def _lunes_a_viernes():
    return [1, 2, 3, 4, 5]


class Jornada(models.Model):
    colegio = models.ForeignKey(Colegio, on_delete=models.CASCADE, related_name='jornadas_horario')
    nombre = models.CharField(max_length=60, default='Mañana')
    dias = models.JSONField(default=_lunes_a_viernes)
    cursos = models.ManyToManyField(Curso, blank=True, related_name='jornadas_horario')
    orden = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ['orden', 'id']

    def __str__(self):
        return self.nombre

    def franjas_de_clase(self):
        return [f for f in self.franjas.all() if not f.descanso]


class Franja(models.Model):
    jornada = models.ForeignKey(Jornada, on_delete=models.CASCADE, related_name='franjas')
    orden = models.PositiveSmallIntegerField(default=0)
    inicio = models.TimeField()
    fin = models.TimeField()
    descanso = models.BooleanField(default=False)
    etiqueta = models.CharField(max_length=30, blank=True)

    class Meta:
        ordering = ['orden', 'inicio']

    def __str__(self):
        return self.etiqueta or f'{self.inicio:%H:%M}–{self.fin:%H:%M}'

    @property
    def texto(self):
        return f'{self.inicio:%H:%M} – {self.fin:%H:%M}'


class Horario(models.Model):
    ESTADOS = [('BORRADOR', 'Borrador'), ('PUBLICADO', 'Publicado'), ('ARCHIVADO', 'Archivado')]
    ORIGENES = [('MANUAL', 'Hecho a mano'), ('GENERADO', 'Generado'), ('IMPORTADO', 'Importado')]

    colegio = models.ForeignKey(Colegio, on_delete=models.CASCADE, related_name='horarios')
    nombre = models.CharField(max_length=80)
    estado = models.CharField(max_length=10, choices=ESTADOS, default='BORRADOR')
    origen = models.CharField(max_length=10, choices=ORIGENES, default='MANUAL')
    puntaje = models.FloatField(null=True, blank=True)
    informe = models.JSONField(default=dict, blank=True)
    creado = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)
    publicado_en = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-actualizado']

    def __str__(self):
        return self.nombre


class Sesion(models.Model):
    horario = models.ForeignKey(Horario, on_delete=models.CASCADE, related_name='sesiones')
    curso = models.ForeignKey(Curso, on_delete=models.CASCADE, related_name='+')
    asignacion = models.ForeignKey(AsignacionDocente, on_delete=models.CASCADE, related_name='+')
    dia = models.PositiveSmallIntegerField(choices=DIAS)
    franja = models.ForeignKey(Franja, on_delete=models.CASCADE, related_name='+')

    class Meta:
        unique_together = ('horario', 'curso', 'dia', 'franja')


class AplicacionEscritorio(models.Model):
    """El instalador de la app de Windows del generador. Lo sube el dueño de la plataforma."""
    archivo = models.FileField(upload_to='app_horarios/')
    version = models.CharField(max_length=20)
    notas = models.CharField(max_length=250, blank=True)
    subido = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-subido']
