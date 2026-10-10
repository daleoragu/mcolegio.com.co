# -*- coding: utf-8 -*-
"""Actas del colegio: comisión de evaluación y promoción, y actas libres.

Un acta se redacta en borrador y se cierra. Al cerrarla, el informe de la
comisión queda congelado tal como estaba ese día (campo `informe`): si después
cambian las notas, el acta firmada no cambia, como pasa con el papel.
"""
from django.conf import settings
from django.db import models

from notas.models import Colegio, Curso, Docente, PeriodoAcademico, Sede


class Acta(models.Model):
    COMISION, LIBRE = 'COMISION', 'LIBRE'
    TIPOS = [(COMISION, 'Comisión de evaluación y promoción'), (LIBRE, 'Acta libre')]
    PERIODO, ACUMULADO = 'PERIODO', 'ACUMULADO'
    ALCANCES = [(PERIODO, 'Pendientes del periodo'), (ACUMULADO, 'Pendientes en el acumulado del año')]
    BORRADOR, CERRADA = 'BORRADOR', 'CERRADA'
    ESTADOS = [(BORRADOR, 'Borrador'), (CERRADA, 'Cerrada')]
    CUADRO, LINEAS = 'CUADRO', 'LINEAS'
    ESTILOS_FIRMA = [(CUADRO, 'Cuadro: nombre, cargo y firma'),
                     (LINEAS, 'Línea de firma con el nombre debajo')]

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
    # [{'nombre': ..., 'cargo': ..., 'asistio': bool}] — en el acta sale con una X y su línea de firma.
    asistencia = models.JSONField(default=list, blank=True, verbose_name='Asistentes')
    estilo_firma = models.CharField(max_length=10, choices=ESTILOS_FIRMA, default=CUADRO,
                                    verbose_name='Cómo salen las firmas')

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
        """[{'nombre', 'cargo', 'asistio'}] limpios, sin filas vacías."""
        salida = []
        for a in self.asistencia or []:
            if not isinstance(a, dict):
                continue
            nombre, cargo = str(a.get('nombre') or '').strip(), str(a.get('cargo') or '').strip()
            if nombre or cargo:
                salida.append({'nombre': nombre[:150], 'cargo': cargo[:150], 'asistio': bool(a.get('asistio'))})
        return salida

    @property
    def cuantos_asistieron(self):
        return sum(1 for a in self.lista_asistentes() if a['asistio'])


class RedactorActas(models.Model):
    """Docente al que el administrador le dio el rol de generar actas.

    El docente ve y redacta solo las suyas; al administrador le salen todas y
    es quien puede cambiar el número.
    """
    colegio = models.ForeignKey(Colegio, on_delete=models.CASCADE, related_name='redactores_actas')
    docente = models.OneToOneField(Docente, on_delete=models.CASCADE, related_name='rol_actas')
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Docente que genera actas'
        verbose_name_plural = 'Docentes que generan actas'

    def __str__(self):
        return str(self.docente)
