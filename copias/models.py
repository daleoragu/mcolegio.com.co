"""Copia de seguridad de cada persona en su propia nube (Google Drive u OneDrive), como la de WhatsApp.

El archivo se arma en el servidor y el navegador lo sube a la nube de la persona con su permiso; el permiso
nunca se guarda en la plataforma. Aquí solo queda cuándo se hizo la última y cada cuánto la quiere.
"""
from django.contrib.auth.models import User
from django.db import models


class AjusteCopia(models.Model):
    DESTINOS = [('google', 'Google Drive'), ('onedrive', 'OneDrive'), ('descarga', 'Descargar al dispositivo')]
    FRECUENCIAS = [(1, 'Cada día'), (7, 'Cada semana'), (30, 'Cada mes'), (0, 'Solo cuando la pida')]
    usuario = models.OneToOneField(User, on_delete=models.CASCADE, related_name='ajuste_copia')
    destino = models.CharField(max_length=8, choices=DESTINOS, default='google')
    cada_dias = models.PositiveSmallIntegerField(choices=FRECUENCIAS, default=7)
    incluir_medios = models.BooleanField(default=True, help_text='Fotos, notas de voz y adjuntos.')
    ultima = models.DateTimeField(null=True, blank=True)
    ultimo_peso = models.PositiveBigIntegerField(default=0)
    ultimo_destino = models.CharField(max_length=8, blank=True)

    def __str__(self):
        return f'Copia de {self.usuario}'

    @property
    def ultimo_destino_nombre(self):
        return dict(self.DESTINOS).get(self.ultimo_destino, '')
