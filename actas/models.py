# -*- coding: utf-8 -*-
"""Actas del colegio: comisión de evaluación y promoción, y actas libres.

Un acta se redacta en borrador y se cierra. Al cerrarla, el informe de la
comisión queda congelado tal como estaba ese día (campo `informe`): si después
cambian las notas, el acta firmada no cambia, como pasa con el papel.
"""
from django.conf import settings
from django.db import models

from notas.models import Colegio, Curso, PeriodoAcademico, Sede


class Acta(models.Model):
    COMISION, LIBRE = 'COMISION', 'LIBRE'
    TIPOS = [(COMISION, 'Comisión de evaluación y promoción'), (LIBRE, 'Acta libre')]
    PERIODO, ACUMULADO = 'PERIODO', 'ACUMULADO'
    ALCANCES = [(PERIODO, 'Pendientes del periodo'), (ACUMULADO, 'Pendientes en el acumulado del año')]
    BORRADOR, CERRADA = 'BORRADOR', 'CERRADA'
    ESTADOS = [(BORRADOR, 'Borrador'), (CERRADA, 'Cerrada')]

    colegio = models.ForeignKey(Colegio, on_delete=models.CASCADE, related_name='actas')
    tipo = models.CharField(max_length=10, choices=TIPOS, default=COMISION)
    numero = models.PositiveIntegerField(verbose_name='Acta N.º')
    ano = models.PositiveIntegerField(verbose_name='Año')
    titulo = models.CharField(max_length=200, verbose_name='Título',
                              help_text='Ej.: Comisión de evaluación y promoción grado sexto')
    fecha = models.DateField(verbose_name='Fecha')
    hora_inicio = models.TimeField(null=True, blank=True, verbose_name='Hora de inicio')
    hora_fin = models.TimeField(null=True, blank=True, verbose_name='Hora de cierre')
    lugar = models.CharField(max_length=200, blank=True, verbose_name='Lugar')

    # Solo comisión
    periodo = models.ForeignKey(PeriodoAcademico, on_delete=models.SET_NULL, null=True, blank=True,
                                verbose_name='Periodo')
    alcance = models.CharField(max_length=10, choices=ALCANCES, default=PERIODO,
                               verbose_name='Asignaturas pendientes')
    cursos = models.ManyToManyField(Curso, blank=True, verbose_name='Cursos')
    sede = models.ForeignKey(Sede, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Sede')
    mostrar_observador = models.BooleanField(
        default=False, verbose_name='Mostrar anotaciones del observador',
        help_text='Al lado de cada estudiante, cuántas anotaciones «a mejorar» tiene en el observador.')

    # Lo que se dijo
    orden_del_dia = models.TextField(blank=True, verbose_name='Orden del día', help_text='Un punto por línea.')
    desarrollo = models.TextField(blank=True, verbose_name='Desarrollo de la reunión')
    decisiones = models.TextField(blank=True, verbose_name='Decisiones y compromisos', help_text='Uno por línea.')
    asistentes = models.TextField(blank=True, verbose_name='Asistentes',
                                  help_text='Uno por línea: Nombre — Cargo')

    informe = models.JSONField(null=True, blank=True, editable=False)  # congelado al cerrar
    estado = models.CharField(max_length=10, choices=ESTADOS, default=BORRADOR)
    cerrada_en = models.DateTimeField(null=True, blank=True)
    creada_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
                                   related_name='+')
    creada_en = models.DateTimeField(auto_now_add=True)
    actualizada_en = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-ano', '-numero']
        constraints = [models.UniqueConstraint(fields=['colegio', 'ano', 'numero'], name='acta_numero_unico')]
        verbose_name = 'Acta'

    def __str__(self):
        return f'Acta {self.numero} de {self.ano} · {self.titulo}'

    @property
    def es_comision(self):
        return self.tipo == self.COMISION

    @property
    def cerrada(self):
        return self.estado == self.CERRADA

    def lista(self, campo):
        return [l.strip(' -•*\t') for l in (getattr(self, campo) or '').splitlines() if l.strip(' -•*\t')]

    @property
    def lista_orden(self):
        return self.lista('orden_del_dia')

    def lista_asistentes(self):
        """[(nombre, cargo)] de las líneas «Nombre — Cargo» (también acepta «-», «|» o «,»)."""
        import re
        salida = []
        for linea in self.lista('asistentes'):
            partes = re.split(r'\s+[—–-]\s+|\s*\|\s*|\s*,\s*', linea, maxsplit=1)
            salida.append((partes[0].strip(), partes[1].strip() if len(partes) > 1 else ''))
        return salida
