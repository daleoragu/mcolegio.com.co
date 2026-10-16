"""Cartera y pensiones de los colegios privados.

* Conceptos de cobro: matrícula, pensión mensual, otros; con un valor general
  y, si se quiere, un valor distinto por grado.
* Becas y descuentos por estudiante (porcentaje).
* Cargos: lo que se le cobra a cada estudiante (un cargo por concepto y mes).
  Se generan con un botón y no se duplican si se vuelve a generar.
* Pagos: cada pago lleva recibo con consecutivo y se aplica a los cargos más
  viejos primero. Un pago anulado deja de contar.

Los valores van en pesos, sin decimales.
"""
from django.conf import settings
from django.db import models
from django.db.models import Sum

from notas.models import Colegio, Estudiante

MESES = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio', 'Agosto', 'Septiembre',
         'Octubre', 'Noviembre', 'Diciembre']


def _meses_por_defecto():
    return list(range(2, 12))          # febrero a noviembre


class ConfiguracionCartera(models.Model):
    colegio = models.OneToOneField(Colegio, on_delete=models.CASCADE, related_name='config_cartera')
    dia_vencimiento = models.PositiveSmallIntegerField(default=5, verbose_name='Día de vencimiento de la pensión',
                                                       help_text='Cada mes la pensión vence ese día.')
    meses_pension = models.JSONField(default=_meses_por_defecto, verbose_name='Meses en que se cobra pensión')
    exigir_paz_y_salvo = models.BooleanField(
        default=False, verbose_name='Exigir paz y salvo para descargar certificados',
        help_text='La familia con saldo vencido no puede descargar ni pedir certificados desde la plataforma.')
    familias_ven_estado = models.BooleanField(default=True, verbose_name='Las familias ven su estado de cuenta')
    datos_pago = models.TextField(blank=True, verbose_name='Cómo pagar',
                                  help_text='Cuenta bancaria, Nequi, horario de tesorería… Sale en el estado de cuenta.')
    ultimo_recibo = models.PositiveIntegerField(default=0, editable=False)

    class Meta:
        verbose_name = 'Configuración de cartera'
        verbose_name_plural = 'Configuración de cartera'

    @classmethod
    def de(cls, colegio):
        return cls.objects.get_or_create(colegio=colegio)[0]


class Concepto(models.Model):
    TIPOS = [('MENSUAL', 'Mensual (pensión)'), ('UNICO', 'Una vez al año (matrícula, otros)')]
    colegio = models.ForeignKey(Colegio, on_delete=models.CASCADE, related_name='conceptos_cobro')
    nombre = models.CharField(max_length=80)
    tipo = models.CharField(max_length=8, choices=TIPOS, default='MENSUAL')
    valor = models.PositiveIntegerField(help_text='Valor general en pesos.')
    mes_unico = models.PositiveSmallIntegerField(default=2, verbose_name='Mes en que se cobra (si es una vez al año)')
    activo = models.BooleanField(default=True)
    orden = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ['orden', 'id']
        verbose_name = 'Concepto de cobro'
        verbose_name_plural = 'Conceptos de cobro'

    def __str__(self):
        return self.nombre

    def valor_para(self, grado):
        v = self.valores_grado.filter(grado=grado).first() if grado is not None else None
        return v.valor if v else self.valor


class ValorPorGrado(models.Model):
    concepto = models.ForeignKey(Concepto, on_delete=models.CASCADE, related_name='valores_grado')
    grado = models.SmallIntegerField()
    valor = models.PositiveIntegerField()

    class Meta:
        unique_together = ('concepto', 'grado')


class Beca(models.Model):
    estudiante = models.ForeignKey(Estudiante, on_delete=models.CASCADE, related_name='becas')
    concepto = models.ForeignKey(Concepto, on_delete=models.CASCADE, null=True, blank=True,
                                 help_text='Vacío = sobre todos los conceptos.')
    porcentaje = models.PositiveSmallIntegerField()
    motivo = models.CharField(max_length=120, blank=True)

    class Meta:
        verbose_name = 'Beca o descuento'
        verbose_name_plural = 'Becas y descuentos'


class Cargo(models.Model):
    colegio = models.ForeignKey(Colegio, on_delete=models.CASCADE, related_name='cargos')
    estudiante = models.ForeignKey(Estudiante, on_delete=models.CASCADE, related_name='cargos')
    concepto = models.ForeignKey(Concepto, on_delete=models.SET_NULL, null=True, blank=True, related_name='cargos')
    ano = models.PositiveIntegerField()
    mes = models.PositiveSmallIntegerField(null=True, blank=True)
    descripcion = models.CharField(max_length=120)
    valor = models.PositiveIntegerField()
    descuento = models.PositiveIntegerField(default=0)
    vence = models.DateField()
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['vence', 'id']
        unique_together = ('estudiante', 'concepto', 'ano', 'mes')

    def __str__(self):
        return f'{self.descripcion} · {self.estudiante}'

    @property
    def neto(self):
        return max(0, self.valor - self.descuento)

    def pagado(self):
        return self.aplicaciones.filter(pago__anulado=False).aggregate(t=Sum('valor'))['t'] or 0

    def saldo(self):
        return max(0, self.neto - self.pagado())


class Pago(models.Model):
    MEDIOS = [('EFECTIVO', 'Efectivo'), ('TRANSFERENCIA', 'Transferencia'), ('NEQUI', 'Nequi / Daviplata'),
              ('CONSIGNACION', 'Consignación'), ('TARJETA', 'Tarjeta'), ('OTRO', 'Otro')]
    colegio = models.ForeignKey(Colegio, on_delete=models.CASCADE, related_name='pagos')
    estudiante = models.ForeignKey(Estudiante, on_delete=models.CASCADE, related_name='pagos')
    numero = models.PositiveIntegerField(help_text='Número de recibo.')
    fecha = models.DateField()
    valor = models.PositiveIntegerField()
    medio = models.CharField(max_length=14, choices=MEDIOS, default='EFECTIVO')
    referencia = models.CharField(max_length=80, blank=True)
    observacion = models.CharField(max_length=200, blank=True)
    registrado_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='+')
    registrado = models.DateTimeField(auto_now_add=True)
    anulado = models.BooleanField(default=False)
    motivo_anulacion = models.CharField(max_length=200, blank=True)

    class Meta:
        ordering = ['-fecha', '-numero']
        unique_together = ('colegio', 'numero')


class Aplicacion(models.Model):
    """Qué parte de un pago cubre qué cargo."""
    pago = models.ForeignKey(Pago, on_delete=models.CASCADE, related_name='aplicaciones')
    cargo = models.ForeignKey(Cargo, on_delete=models.CASCADE, related_name='aplicaciones')
    valor = models.PositiveIntegerField()
