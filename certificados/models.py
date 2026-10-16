"""Certificados de estudio y de calificaciones, con código de verificación.

Cada certificado que sale queda guardado (``CertificadoEmitido``) con una copia
de lo que decía. Así el código QR del papel abre una página que muestra lo
mismo que se imprimió, aunque después cambien las notas o el estudiante se
retire.
"""
import secrets

from django.conf import settings
from django.db import models

from notas.models import Colegio, Estudiante


class ConfiguracionCertificados(models.Model):
    MODO_ENTREGA = [
        ('SECRETARIA', 'Solo la secretaría los genera'),
        ('APROBACION', 'El estudiante o acudiente los pide y la secretaría los aprueba'),
        ('LIBRE', 'El estudiante o acudiente los descarga sin aprobación'),
    ]
    colegio = models.OneToOneField(Colegio, on_delete=models.CASCADE, related_name='config_certificados')
    modo_entrega = models.CharField(max_length=12, choices=MODO_ENTREGA, default='APROBACION',
                                    verbose_name='Cómo se entregan a las familias')
    firma_nombre = models.CharField(max_length=150, blank=True, verbose_name='Nombre de quien firma',
                                    help_text='Si lo deja vacío, sale el administrador principal del colegio.')
    firma_cargo = models.CharField(max_length=80, default='Rector(a)', verbose_name='Cargo de quien firma')
    firma2_nombre = models.CharField(max_length=150, blank=True, verbose_name='Segunda firma (opcional)',
                                     help_text='Por ejemplo, la secretaria académica.')
    firma2_cargo = models.CharField(max_length=80, blank=True, default='Secretario(a)',
                                    verbose_name='Cargo de la segunda firma')
    mostrar_asignaturas = models.BooleanField(
        default=True, verbose_name='Mostrar las asignaturas de cada área',
        help_text='Si lo quita, el certificado de calificaciones solo lista las áreas.')
    mostrar_intensidad = models.BooleanField(default=True, verbose_name='Mostrar la intensidad horaria')
    texto_final = models.TextField(blank=True, verbose_name='Texto adicional (opcional)',
                                   help_text='Sale antes de las firmas. Por ejemplo, una nota sobre el plan de estudios.')

    class Meta:
        verbose_name = 'Configuración de certificados'
        verbose_name_plural = 'Configuración de certificados'

    def __str__(self):
        return f'Certificados de {self.colegio}'

    @classmethod
    def de(cls, colegio):
        conf, _ = cls.objects.get_or_create(colegio=colegio)
        return conf


class CalificacionHistorica(models.Model):
    """Una nota final de un año que no se llevó en la plataforma.

    Se cargan desde Excel para poder certificar años anteriores a mcolegio
    (y exalumnos que nunca usaron la plataforma).
    """
    colegio = models.ForeignKey(Colegio, on_delete=models.CASCADE, related_name='calificaciones_historicas')
    estudiante = models.ForeignKey(Estudiante, on_delete=models.CASCADE, related_name='calificaciones_historicas')
    ano_lectivo = models.PositiveIntegerField(verbose_name='Año lectivo')
    grado = models.CharField(max_length=40, verbose_name='Grado', help_text='Como debe salir: «Sexto», «601»…')
    area = models.CharField(max_length=120, verbose_name='Área')
    asignatura = models.CharField(max_length=120, blank=True, verbose_name='Asignatura')
    intensidad = models.PositiveSmallIntegerField(null=True, blank=True, verbose_name='Intensidad horaria semanal')
    nota = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    desempeno = models.CharField(max_length=40, blank=True, verbose_name='Desempeño')
    orden = models.PositiveIntegerField(default=0)
    cargado = models.DateTimeField(auto_now_add=True)
    cargado_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name='+')

    class Meta:
        ordering = ['ano_lectivo', 'orden', 'id']
        indexes = [models.Index(fields=['estudiante', 'ano_lectivo'])]
        verbose_name = 'Calificación de años anteriores'
        verbose_name_plural = 'Calificaciones de años anteriores'

    def __str__(self):
        return f'{self.estudiante} · {self.ano_lectivo} · {self.area} {self.asignatura}'.strip()


def _codigo_nuevo():
    # 12 caracteres sin letras que se confunden (0/O, 1/I/L): fácil de dictar.
    alfabeto = 'ABCDEFGHJKMNPQRSTUVWXYZ23456789'
    return ''.join(secrets.choice(alfabeto) for _ in range(12))


class CertificadoEmitido(models.Model):
    TIPOS = [('ESTUDIO', 'Certificado de estudio'), ('CALIFICACIONES', 'Certificado de calificaciones')]

    colegio = models.ForeignKey(Colegio, on_delete=models.CASCADE, related_name='certificados_emitidos')
    estudiante = models.ForeignKey(Estudiante, on_delete=models.CASCADE, related_name='certificados')
    tipo = models.CharField(max_length=15, choices=TIPOS)
    ano_lectivo = models.PositiveIntegerField(null=True, blank=True)
    codigo = models.CharField(max_length=16, unique=True, default=_codigo_nuevo, editable=False)
    contenido = models.JSONField(default=dict, help_text='Lo que dice el certificado, tal como se emitió.')
    emitido = models.DateTimeField(auto_now_add=True)
    emitido_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name='+')
    anulado = models.BooleanField(default=False)
    motivo_anulacion = models.CharField(max_length=200, blank=True)

    class Meta:
        ordering = ['-emitido']
        verbose_name = 'Certificado emitido'
        verbose_name_plural = 'Certificados emitidos'

    def __str__(self):
        ano = f' {self.ano_lectivo}' if self.ano_lectivo else ''
        return f'{self.get_tipo_display()}{ano} · {self.estudiante} · {self.codigo}'


class SolicitudCertificado(models.Model):
    ESTADOS = [('PENDIENTE', 'Pendiente'), ('APROBADA', 'Aprobada'), ('RECHAZADA', 'Rechazada')]

    colegio = models.ForeignKey(Colegio, on_delete=models.CASCADE, related_name='solicitudes_certificado')
    estudiante = models.ForeignKey(Estudiante, on_delete=models.CASCADE, related_name='solicitudes_certificado')
    tipo = models.CharField(max_length=15, choices=CertificadoEmitido.TIPOS)
    ano_lectivo = models.PositiveIntegerField(null=True, blank=True)
    motivo = models.CharField(max_length=200, blank=True, verbose_name='Para qué lo necesita (opcional)')
    estado = models.CharField(max_length=10, choices=ESTADOS, default='PENDIENTE')
    solicitada = models.DateTimeField(auto_now_add=True)
    resuelta = models.DateTimeField(null=True, blank=True)
    resuelta_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
                                     related_name='+')
    respuesta = models.CharField(max_length=200, blank=True)
    certificado = models.ForeignKey(CertificadoEmitido, on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name='solicitudes')

    class Meta:
        ordering = ['-solicitada']
        verbose_name = 'Solicitud de certificado'
        verbose_name_plural = 'Solicitudes de certificado'

    def __str__(self):
        return f'{self.get_tipo_display()} · {self.estudiante} · {self.get_estado_display()}'
