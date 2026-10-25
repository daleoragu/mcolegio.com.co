"""Circulares del colegio con confirmación de lectura.

La administración escribe una circular (con adjunto opcional) para todas las
familias, para algunos cursos o para los docentes. A cada destinatario le
llega una notificación (y un correo, si el acudiente tiene); al abrirla queda
registrada como leída y, si se pide, la familia confirma con un botón. La
administración ve quién leyó y a quién falta recordarle.
"""
from django.conf import settings
from django.db import models

from notas.models import Colegio, Curso, Estudiante


class Circular(models.Model):
    PARA = [
        ('FAMILIAS', 'Todas las familias'),
        ('CURSOS', 'Familias de algunos cursos'),
        ('DOCENTES', 'Docentes'),
        ('PERSONAL', 'Docentes y personal administrativo'),
        ('TODOS', 'Familias, docentes y personal administrativo'),
    ]
    colegio = models.ForeignKey(Colegio, on_delete=models.CASCADE, related_name='circulares')
    numero = models.PositiveIntegerField(default=0, help_text='Consecutivo del año.')
    titulo = models.CharField(max_length=200, verbose_name='Asunto')
    cuerpo = models.TextField(verbose_name='Texto de la circular')
    adjunto = models.FileField(upload_to='circulares/', blank=True, null=True,
                               verbose_name='Archivo adjunto (opcional)')
    para = models.CharField(max_length=10, choices=PARA, default='FAMILIAS', verbose_name='Para')
    cursos = models.ManyToManyField(Curso, blank=True, related_name='circulares')
    pide_confirmacion = models.BooleanField(default=True, verbose_name='Pedir que confirmen «Leí la circular»')
    fecha_limite = models.DateField(null=True, blank=True, verbose_name='Confirmar a más tardar (opcional)')
    por_whatsapp = models.BooleanField(default=False, verbose_name='Avisar también por WhatsApp a las familias')
    autor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='+')
    creada = models.DateTimeField(auto_now_add=True)
    publicada = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-creada']
        verbose_name = 'Circular'
        verbose_name_plural = 'Circulares'

    def __str__(self):
        return f'Circular {self.numero} · {self.titulo}'

    @property
    def es_borrador(self):
        return self.publicada is None


class Lectura(models.Model):
    """Un destinatario de una circular: cuándo la abrió y cuándo confirmó."""
    circular = models.ForeignKey(Circular, on_delete=models.CASCADE, related_name='lecturas')
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='lecturas_circulares')
    estudiante = models.ForeignKey(Estudiante, on_delete=models.CASCADE, null=True, blank=True, related_name='+')
    abierta = models.DateTimeField(null=True, blank=True)
    confirmada = models.DateTimeField(null=True, blank=True)
    quien_confirma = models.CharField(max_length=120, blank=True, verbose_name='Nombre de quien confirma')
    whatsapp_enviado = models.DateTimeField(null=True, blank=True, help_text='Cuándo salió el aviso por WhatsApp.')
    whatsapp_detalle = models.CharField(max_length=120, blank=True, help_text='A quién se le mandó o por qué no salió.')

    class Meta:
        unique_together = ('circular', 'usuario')
        verbose_name = 'Lectura de circular'
        verbose_name_plural = 'Lecturas de circulares'
