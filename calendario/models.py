"""Calendario escolar: los eventos del año (izadas, entregas, reuniones, festivos…).

Los periodos académicos y sus cierres programados no se guardan aquí: se
muestran solos a partir de los periodos del colegio (ver logica.py).
"""
from django.conf import settings
from django.db import models

from notas.models import Colegio, Curso

TIPOS = [
    ('IZADA', 'Izada de bandera'),
    ('ACTO', 'Acto o celebración'),
    ('REUNION', 'Reunión'),
    ('ENTREGA', 'Entrega de informes'),
    ('EVALUACION', 'Evaluaciones'),
    ('ACADEMICO', 'Actividad académica'),
    ('SALIDA', 'Salida pedagógica'),
    ('FESTIVO', 'Festivo'),
    ('RECESO', 'Vacaciones / receso'),
    ('SIN_CLASE', 'Sin clase para estudiantes'),
    ('OTRO', 'Otro'),
]

COLORES = {
    'IZADA': '#0e7490', 'ACTO': '#7c3aed', 'REUNION': '#2563eb', 'ENTREGA': '#ea580c',
    'EVALUACION': '#dc2626', 'ACADEMICO': '#4338ca', 'SALIDA': '#16a34a', 'FESTIVO': '#be123c',
    'RECESO': '#0891b2', 'SIN_CLASE': '#a16207', 'OTRO': '#475467', 'PERIODO': '#334155', 'CIERRE': '#9333ea',
}

PARA = [
    ('TODOS', 'Toda la comunidad'),
    ('DOCENTES', 'Solo docentes y directivos'),
    ('ESTUDIANTES', 'Estudiantes y familias'),
]


class Evento(models.Model):
    colegio = models.ForeignKey(Colegio, on_delete=models.CASCADE, related_name='eventos_calendario')
    titulo = models.CharField(max_length=120)
    tipo = models.CharField(max_length=12, choices=TIPOS, default='OTRO')
    fecha = models.DateField()
    fecha_fin = models.DateField(null=True, blank=True, help_text='Solo si dura varios días.')
    hora_inicio = models.TimeField(null=True, blank=True)
    hora_fin = models.TimeField(null=True, blank=True)
    lugar = models.CharField(max_length=120, blank=True)
    descripcion = models.TextField(blank=True)
    para = models.CharField(max_length=12, choices=PARA, default='TODOS')
    cursos = models.ManyToManyField(Curso, blank=True, related_name='eventos_calendario',
                                    help_text='Vacío = todos los cursos.')
    creado_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name='+')
    creado = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['fecha', 'hora_inicio', 'titulo']

    def __str__(self):
        return f'{self.fecha:%d/%m/%Y} · {self.titulo}'

    @property
    def ultimo_dia(self):
        return self.fecha_fin if self.fecha_fin and self.fecha_fin > self.fecha else self.fecha

    @property
    def color(self):
        return COLORES.get(self.tipo, '#475467')
