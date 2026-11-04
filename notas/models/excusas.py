"""Excusas de las fallas: la familia (o el estudiante) la envía desde su panel, el
director de grupo o la coordinación la aprueba y los días aprobados quedan como
«ausente con excusa» en todas las clases, bloqueados para el docente."""
from django.contrib.auth.models import User
from django.db import models

from aula import almacen

from .perfiles import Colegio, Estudiante


def ruta_soporte(instancia, nombre):
    return almacen._ruta(f'excusas/{instancia.colegio_id}', nombre)


class Excusa(models.Model):
    MOTIVOS = [
        ('ENFERMEDAD', 'Enfermedad o incapacidad médica'),
        ('CITA', 'Cita médica u odontológica'),
        ('CALAMIDAD', 'Calamidad doméstica'),
        ('VIAJE', 'Viaje o diligencia familiar'),
        ('REPRESENTACION', 'Representa al colegio (deporte, cultura…)'),
        ('OTRO', 'Otro'),
    ]
    ESTADOS = [('PENDIENTE', 'Pendiente'), ('APROBADA', 'Aprobada'), ('RECHAZADA', 'Rechazada'), ('ANULADA', 'Anulada')]

    colegio = models.ForeignKey(Colegio, on_delete=models.CASCADE, related_name='excusas')
    estudiante = models.ForeignKey(Estudiante, on_delete=models.CASCADE, related_name='excusas')
    enviada_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='+')
    motivo = models.CharField(max_length=15, choices=MOTIVOS, default='ENFERMEDAD')
    desde = models.DateField()
    hasta = models.DateField()
    explicacion = models.TextField(max_length=1500, blank=True)
    soporte = models.FileField(upload_to=ruta_soporte, storage=almacen.privado, blank=True,
                               verbose_name='Soporte (incapacidad, fórmula…)')
    nombre_soporte = models.CharField(max_length=150, blank=True)

    estado = models.CharField(max_length=10, choices=ESTADOS, default='PENDIENTE')
    revisada_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='+')
    revisada_en = models.DateTimeField(null=True, blank=True)
    aprobada_desde = models.DateField(null=True, blank=True)
    aprobada_hasta = models.DateField(null=True, blank=True)
    respuesta = models.CharField(max_length=500, blank=True, verbose_name='Respuesta a la familia')
    fuera_de_plazo = models.BooleanField(default=False)
    # Registros de asistencia que creó la excusa (para borrarlos si se anula).
    asistencias_creadas = models.JSONField(default=list, blank=True)
    creada = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-creada']
        verbose_name = 'Excusa'
        verbose_name_plural = 'Excusas'

    def __str__(self):
        return f'{self.estudiante} · {self.get_motivo_display()} · {self.desde:%d/%m}–{self.hasta:%d/%m}'

    @property
    def dias(self):
        return (self.hasta - self.desde).days + 1
