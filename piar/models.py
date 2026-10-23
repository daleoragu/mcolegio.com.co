"""PIAR: Plan Individual de Ajustes Razonables (Decreto 1421 de 2017).

Uno por estudiante y por año. Tiene tres partes, como el formato del MEN:
  1. Información del estudiante y valoración pedagógica (la llena quien
     coordina: docente de apoyo, orientación, director de grupo o directivos).
  2. Ajustes razonables por asignatura y por periodo: objetivos, barreras,
     ajustes y evaluación de los ajustes (los llena cada docente de su
     asignatura).
  3. Acta de acuerdo con la familia: compromisos y firmas.
"""
from django.conf import settings
from django.db import models
from django.utils import timezone

from notas.models import Colegio, Docente, Estudiante, Materia, PeriodoAcademico

CATEGORIAS = [
    ('FISICA', 'Discapacidad física'),
    ('AUDITIVA_LSC', 'Discapacidad auditiva – usuario de Lengua de Señas Colombiana'),
    ('AUDITIVA_CAST', 'Discapacidad auditiva – usuario del castellano'),
    ('VISUAL_BAJA', 'Discapacidad visual – baja visión'),
    ('VISUAL_CEGUERA', 'Discapacidad visual – ceguera'),
    ('SORDOCEGUERA', 'Sordoceguera'),
    ('INTELECTUAL', 'Discapacidad intelectual'),
    ('PSICOSOCIAL', 'Discapacidad psicosocial (mental)'),
    ('TEA', 'Trastorno del espectro autista'),
    ('SISTEMICA', 'Discapacidad sistémica'),
    ('MULTIPLE', 'Discapacidad múltiple'),
    ('TALENTO', 'Capacidades o talentos excepcionales'),
    ('APRENDIZAJE', 'Trastorno específico del aprendizaje o del comportamiento'),
    ('PROCESO', 'En proceso de diagnóstico'),
]

TIPOS_AJUSTE = [
    ('CURRICULAR', 'Curriculares'),
    ('DIDACTICO', 'Didácticos'),
    ('METODOLOGICO', 'Metodológicos'),
    ('EVALUATIVO', 'Evaluativos'),
]


class ConfiguracionPiar(models.Model):
    colegio = models.OneToOneField(Colegio, on_delete=models.CASCADE, related_name='config_piar')
    docentes_apoyo = models.ManyToManyField(
        Docente, blank=True, related_name='+', verbose_name='Docentes de apoyo / orientación',
        help_text='Pueden crear y editar todos los PIAR del colegio, como la administración.')
    formato = models.JSONField(default=dict, blank=True, verbose_name='Formato del PIAR',
                               help_text='Qué secciones y columnas salen (lo escoge la orientadora). Ver piar/formato.py.')

    @classmethod
    def de(cls, colegio):
        return cls.objects.get_or_create(colegio=colegio)[0]


class Piar(models.Model):
    ESTADOS = [('BORRADOR', 'En elaboración'), ('VIGENTE', 'Vigente (acta firmada)')]

    colegio = models.ForeignKey(Colegio, on_delete=models.CASCADE, related_name='piars')
    estudiante = models.ForeignKey(Estudiante, on_delete=models.CASCADE, related_name='piars')
    ano_lectivo = models.PositiveIntegerField()
    estado = models.CharField(max_length=10, choices=ESTADOS, default='BORRADOR')
    fecha_elaboracion = models.DateField(default=timezone.localdate, verbose_name='Fecha de elaboración')
    elaborado_por = models.CharField(max_length=200, blank=True, verbose_name='Elaborado por (nombre y cargo)')

    # 1. Información del estudiante
    categoria = models.CharField(max_length=15, choices=CATEGORIAS, blank=True, verbose_name='Categoría')
    diagnostico = models.TextField(blank=True, verbose_name='Diagnóstico',
                                   help_text='Tal como aparece en el soporte médico o de la EPS.')
    fuente_diagnostico = models.CharField(max_length=200, blank=True, verbose_name='Quién lo emitió y cuándo')
    apoyos_salud = models.TextField(blank=True, verbose_name='Terapias, tratamientos o apoyos de salud',
                                    help_text='Terapias que recibe, frecuencia, medicamentos que debe tomar en el colegio.')
    entorno_hogar = models.TextField(blank=True, verbose_name='Entorno del hogar',
                                     help_text='Con quién vive, quién lo acompaña en las tareas, apoyos en casa.')
    trayectoria = models.TextField(blank=True, verbose_name='Trayectoria escolar',
                                   help_text='Colegios anteriores, años repetidos, apoyos que ya ha recibido.')

    # Valoración pedagógica
    descripcion = models.TextField(blank=True, verbose_name='Descripción del estudiante',
                                   help_text='Gustos, intereses, cómo aprende mejor, cómo se relaciona.')
    fortalezas = models.TextField(blank=True, verbose_name='Fortalezas y habilidades')
    barreras = models.TextField(blank=True, verbose_name='Barreras que se evidencian en el colegio',
                                help_text='De aprendizaje, de comunicación, de movilidad, actitudinales, del entorno…')
    apoyos_requeridos = models.TextField(blank=True, verbose_name='Apoyos que requiere',
                                         help_text='Intérprete, material en braille o macrotipo, ubicación en el aula, '
                                                   'tiempos adicionales, acompañamiento…')
    expectativas_familia = models.TextField(blank=True, verbose_name='Expectativas de la familia')
    expectativas_estudiante = models.TextField(blank=True, verbose_name='Expectativas del estudiante')

    # Registro de habilidades {afirmación: valor}, otras dimensiones y recomendaciones por actor
    habilidades = models.JSONField(default=dict, blank=True, verbose_name='Registro de habilidades')
    otras_dimensiones = models.JSONField(default=dict, blank=True,
                                         verbose_name='Convivencia, socialización, participación, autonomía, autocontrol')
    recomendaciones_actores = models.JSONField(default=dict, blank=True,
                                               verbose_name='Recomendaciones para el plan de mejoramiento por actor')

    # 3. Acta de acuerdo
    compromisos_familia = models.TextField(blank=True, verbose_name='Compromisos de la familia')
    compromisos_colegio = models.TextField(blank=True, verbose_name='Compromisos del colegio')
    recomendaciones = models.TextField(blank=True, verbose_name='Recomendaciones',
                                       help_text='Para el plan de mejoramiento institucional, la familia u otros '
                                                 'profesionales.')
    fecha_acta = models.DateField(null=True, blank=True, verbose_name='Fecha de firma del acta de acuerdo')
    compartido_familia = models.BooleanField(default=False, verbose_name='La familia puede descargarlo',
                                             help_text='El PIAR sale en el panel del estudiante para descargarlo.')

    creado_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name='+')
    creado = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('estudiante', 'ano_lectivo')
        ordering = ['-ano_lectivo', 'estudiante__user__last_name', 'estudiante__user__first_name']
        verbose_name = 'PIAR'
        verbose_name_plural = 'PIAR'

    def __str__(self):
        return f'PIAR {self.ano_lectivo} · {self.estudiante}'

    def save(self, *args, **kwargs):
        self.estado = 'VIGENTE' if self.fecha_acta else 'BORRADOR'
        super().save(*args, **kwargs)


class AjustePiar(models.Model):
    """Lo que hace un docente en su asignatura, en un periodo, para este estudiante."""
    piar = models.ForeignKey(Piar, on_delete=models.CASCADE, related_name='ajustes')
    materia = models.ForeignKey(Materia, on_delete=models.CASCADE, related_name='+')
    periodo = models.ForeignKey(PeriodoAcademico, on_delete=models.CASCADE, related_name='+')
    docente = models.ForeignKey(Docente, on_delete=models.SET_NULL, null=True, blank=True, related_name='+')
    objetivos = models.TextField(blank=True, verbose_name='Objetivos / propósitos de aprendizaje')
    barreras = models.TextField(blank=True, verbose_name='Barreras que se evidencian')
    tipos = models.JSONField(default=list, blank=True, verbose_name='Tipo de ajuste')
    ajustes = models.TextField(blank=True, verbose_name='Ajustes razonables')
    apoyos = models.TextField(blank=True, verbose_name='Apoyo requerido')
    no_requiere = models.BooleanField(default=False, verbose_name='No requiere ajustes razonables en esta asignatura')
    evaluacion = models.TextField(blank=True, verbose_name='Evaluación de los ajustes',
                                  help_text='¿Funcionaron? ¿Qué logró el estudiante? ¿Qué hay que cambiar?')
    actualizado = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('piar', 'materia', 'periodo')
        ordering = ['materia__nombre', 'periodo__fecha_inicio']

    def __str__(self):
        return f'{self.piar} · {self.materia} · {self.periodo}'

    @property
    def completo(self):
        return self.no_requiere or bool(self.ajustes.strip())

    def tipos_texto(self):
        nombres = dict(TIPOS_AJUSTE)
        return ', '.join(nombres[t] for t in self.tipos if t in nombres)
