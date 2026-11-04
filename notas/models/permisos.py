"""Permisos para salir del salón (o del colegio) y lo que pasa al verificarlos con el carné."""
from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone

from .perfiles import Colegio, Estudiante


class PermisoSalida(models.Model):
    # código: (nombre, minutos sugeridos, solo directivos)
    DESTINOS = {
        'BANO': ('Baño', 10, False),
        'ENFERMERIA': ('Enfermería', 20, False),
        'COORDINACION': ('Coordinación', 20, False),
        'ORIENTACION': ('Orientación escolar', 30, False),
        'SECRETARIA': ('Secretaría', 15, False),
        'BIBLIOTECA': ('Biblioteca', 20, False),
        'ENCARGO': ('Encargo del docente', 10, False),
        'SALIDA': ('Salida del colegio', 0, True),        # retiro con el acudiente: hasta el final del día
        'OTRO': ('Otro', 15, False),
    }
    CHOICES = [(k, v[0]) for k, v in DESTINOS.items()]

    colegio = models.ForeignKey(Colegio, on_delete=models.CASCADE, related_name='permisos_salida')
    estudiante = models.ForeignKey(Estudiante, on_delete=models.CASCADE, related_name='permisos_salida')
    otorgado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='+')
    asignacion = models.ForeignKey('notas.AsignacionDocente', on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name='+', help_text='La clase de la que salió.')
    destino = models.CharField(max_length=12, choices=CHOICES, default='BANO')
    nota = models.CharField(max_length=200, blank=True)
    inicio = models.DateTimeField(default=timezone.now)
    vence = models.DateTimeField()
    regreso = models.DateTimeField(null=True, blank=True)
    regreso_marcado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='+')
    anulado = models.BooleanField(default=False)

    class Meta:
        ordering = ['-inicio']
        verbose_name = 'Permiso de salida'
        verbose_name_plural = 'Permisos de salida'
        indexes = [models.Index(fields=['colegio', 'inicio'])]

    def __str__(self):
        return f'{self.estudiante} · {self.get_destino_display()} · {timezone.localtime(self.inicio):%d/%m %H:%M}'

    @property
    def abierto(self):
        return self.regreso is None and not self.anulado

    @property
    def vencido(self):
        return self.abierto and timezone.now() > self.vence

    @property
    def minutos_restantes(self):
        return max(0, int((self.vence - timezone.now()).total_seconds() // 60)) if self.abierto else 0

    @property
    def minutos_fuera(self):
        fin = self.regreso or timezone.now()
        return int((fin - self.inicio).total_seconds() // 60)

    @property
    def minutos_vencido(self):
        return int((timezone.now() - self.vence).total_seconds() // 60) if self.vencido else 0


class VerificacionPermiso(models.Model):
    """Un docente o directivo escaneó el carné de un estudiante fuera del salón."""
    RESULTADOS = [('CON_PERMISO', 'Con permiso'), ('VENCIDO', 'Permiso vencido'), ('SIN_PERMISO', 'Sin permiso')]
    colegio = models.ForeignKey(Colegio, on_delete=models.CASCADE, related_name='+')
    estudiante = models.ForeignKey(Estudiante, on_delete=models.CASCADE, related_name='verificaciones_permiso')
    permiso = models.ForeignKey(PermisoSalida, on_delete=models.SET_NULL, null=True, blank=True, related_name='verificaciones')
    verificado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='+')
    resultado = models.CharField(max_length=12, choices=RESULTADOS)
    reportado = models.BooleanField(default=False, help_text='Se avisó al director de grupo y a coordinación.')
    MEDIOS = [('CARNE', 'Escaneando el carné'), ('NOMBRE', 'Buscando por nombre')]
    medio = models.CharField(max_length=6, choices=MEDIOS, default='CARNE')
    sin_carne = models.BooleanField(default=False, help_text='Ese día el estudiante no traía el carné.')
    momento = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-momento']
