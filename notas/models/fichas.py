"""Cambios a la ficha del estudiante: lo que pide el estudiante (o su familia) y el
registro de todo lo que cambia, quién lo hizo y quién lo autorizó."""
from django.contrib.auth.models import User
from django.db import models

from .perfiles import Colegio, Estudiante


class SolicitudFicha(models.Model):
    """El estudiante pide cambiar datos de su ficha; la administración o el director de grupo autoriza."""
    ESTADOS = [('PENDIENTE', 'Pendiente'), ('APROBADA', 'Aprobada'), ('PARCIAL', 'Aprobada en parte'),
               ('RECHAZADA', 'Rechazada')]
    colegio = models.ForeignKey(Colegio, on_delete=models.CASCADE, related_name='solicitudes_ficha')
    estudiante = models.ForeignKey(Estudiante, on_delete=models.CASCADE, related_name='solicitudes_ficha')
    enviada_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='+')
    # {campo: {'etiqueta', 'antes', 'despues' (valor para guardar), 'antes_txt', 'despues_txt'}}
    cambios = models.JSONField(default=dict)
    foto_nueva = models.ImageField(upload_to='fotos_estudiantes/', blank=True, null=True)
    estado = models.CharField(max_length=10, choices=ESTADOS, default='PENDIENTE')
    aprobados = models.JSONField(default=list, blank=True)
    revisada_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='+')
    revisada_en = models.DateTimeField(null=True, blank=True)
    respuesta = models.CharField(max_length=500, blank=True)
    creada = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-creada']
        verbose_name = 'Solicitud de cambio de ficha'
        verbose_name_plural = 'Solicitudes de cambio de ficha'

    def __str__(self):
        return f'{self.estudiante} · {len(self.cambios)} cambio(s) · {self.get_estado_display()}'


class CambioFicha(models.Model):
    """Un dato que cambió en la ficha: qué, de qué a qué, quién lo hizo y quién lo autorizó."""
    ORIGENES = [('ADMIN', 'Administración'), ('DOCENTE', 'Docente'), ('SOLICITUD', 'Solicitud del estudiante')]
    colegio = models.ForeignKey(Colegio, on_delete=models.CASCADE, related_name='+')
    estudiante = models.ForeignKey(Estudiante, on_delete=models.CASCADE, related_name='cambios_ficha')
    campo = models.CharField(max_length=40)
    etiqueta = models.CharField(max_length=80)
    antes = models.TextField(blank=True)
    despues = models.TextField(blank=True)
    hecho_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='+')
    autorizado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='+')
    origen = models.CharField(max_length=10, choices=ORIGENES)
    solicitud = models.ForeignKey(SolicitudFicha, on_delete=models.SET_NULL, null=True, blank=True, related_name='+')
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-creado', '-id']
        verbose_name = 'Cambio en la ficha'
        verbose_name_plural = 'Cambios en la ficha'
