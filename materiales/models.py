"""Mis materiales: guías, talleres, evaluaciones y fichas que el docente arma por bloques.

El contenido del documento es un JSON (ver bloques.py). Las imágenes que el docente pega se
guardan en el Space privado, comprimidas, y cuentan en su nube.
"""
import os
import uuid

from django.contrib.auth.models import User
from django.db import models

from aula import almacen


def _ruta_imagen(instancia, nombre):
    ext = os.path.splitext(nombre or '')[1].lower()[:6] or '.jpg'
    return f'materiales/{instancia.propietario_id}/img/{uuid.uuid4().hex[:16]}{ext}'


def _ruta_logo(instancia, nombre):
    ext = os.path.splitext(nombre or '')[1].lower()[:6] or '.png'
    return f'materiales/{instancia.usuario_id}/logo/{uuid.uuid4().hex[:12]}{ext}'


class Documento(models.Model):
    TIPOS = [
        ('guia_momentos', 'Guía por momentos'),
        ('escuela_nueva', 'Guía Escuela Nueva'),
        ('institucional', 'Guía con el formato del colegio'),
        ('taller', 'Taller'),
        ('evaluacion', 'Evaluación'),
        ('ficha', 'Ficha de lectura'),
        ('cuadernillo', 'Cuadernillo tipo Saber'),
        ('ficha_pdf', 'Ficha sobre un PDF'),
        ('libre', 'Documento en blanco'),
    ]
    propietario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='materiales')
    colegio = models.ForeignKey('notas.Colegio', on_delete=models.CASCADE, null=True, blank=True,
                                related_name='materiales')
    titulo = models.CharField(max_length=150)
    tipo = models.CharField(max_length=16, choices=TIPOS, default='libre')
    area = models.CharField(max_length=80, blank=True, verbose_name='Área o asignatura')
    grado = models.CharField(max_length=40, blank=True)
    periodo = models.CharField(max_length=40, blank=True)
    contenido = models.JSONField(default=dict, blank=True)
    # Plantilla del colegio: el rector o coordinador la marca y los docentes la usan como modelo.
    plantilla_colegio = models.BooleanField(default=False)
    # El examen de PuntoExacto que se creó con este cuadernillo (su clave sale de aquí).
    examen = models.ForeignKey('puntoexacto.Examen', on_delete=models.SET_NULL, null=True, blank=True,
                               related_name='materiales')
    creado = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-actualizado']

    def __str__(self):
        return self.titulo


class Imagen(models.Model):
    propietario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='imagenes_materiales')
    archivo = models.FileField(upload_to=_ruta_imagen, storage=almacen.privado)
    ancho = models.PositiveIntegerField(default=0)
    alto = models.PositiveIntegerField(default=0)
    peso = models.PositiveIntegerField(default=0, help_text='Bytes, para la nube del docente.')
    creada = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Imagen {self.pk}'


class PreguntaBanco(models.Model):
    """Una pregunta guardada para volver a usarla. Si el docente la comparte, la ven los demás docentes
    de su colegio (la comunidad abierta llega después)."""
    propietario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='banco_preguntas')
    colegio = models.ForeignKey('notas.Colegio', on_delete=models.CASCADE, null=True, blank=True,
                                related_name='banco_preguntas')
    compartida = models.BooleanField(default=False)
    area = models.CharField(max_length=80, blank=True)
    grado = models.CharField(max_length=40, blank=True)
    tema = models.CharField(max_length=120, blank=True)
    modo = models.CharField(max_length=12, blank=True)
    bloque = models.JSONField(default=dict)
    texto = models.TextField(blank=True, help_text='Lo que se busca: enunciado, opciones y tema.')
    usos = models.PositiveIntegerField(default=0)
    creada = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-creada']

    def __str__(self):
        return self.texto[:60] or f'Pregunta {self.pk}'


class EncabezadoDocente(models.Model):
    """El encabezado del docente del plan individual (en el colegio se usa el del colegio)."""
    usuario = models.OneToOneField(User, on_delete=models.CASCADE, related_name='encabezado_materiales')
    logo = models.FileField(upload_to=_ruta_logo, storage=almacen.privado, blank=True)
    linea1 = models.CharField(max_length=120, blank=True)
    linea2 = models.CharField(max_length=120, blank=True)
    linea3 = models.CharField(max_length=120, blank=True)

    def __str__(self):
        return f'Encabezado de {self.usuario}'

    @property
    def lineas(self):
        return [x for x in (self.linea1, self.linea2, self.linea3) if x]


# ---------------------------------------------------------------------------
# Créditos de IA y saldo prepago
# ---------------------------------------------------------------------------
class CuentaIA(models.Model):
    """Saldo en pesos y ajustes del docente para la IA y la nube. Los créditos se calculan de los movimientos."""
    usuario = models.OneToOneField(User, on_delete=models.CASCADE, related_name='cuenta_ia')
    saldo = models.PositiveIntegerField(default=0, help_text='Pesos. No vence.')
    # Plan individual «con IA» (200 créditos al mes + 8 diarios) activo hasta esta fecha.
    ia_hasta = models.DateField(null=True, blank=True)
    # Usar el saldo sin preguntar cada vez, hasta este tope de pesos al mes.
    saldo_sin_preguntar = models.BooleanField(default=False)
    tope_mes = models.PositiveIntegerField(default=3000)
    # Nube ampliada (GB) hasta esta fecha.
    nube_extra_gb = models.PositiveSmallIntegerField(default=0)
    nube_extra_hasta = models.DateField(null=True, blank=True)

    def __str__(self):
        return f'IA de {self.usuario}'


class MovimientoIA(models.Model):
    TIPOS = [('uso', 'Uso de la IA'), ('paquete', 'Paquete de créditos'), ('regalo', 'Créditos de regalo'),
             ('recarga', 'Recarga de saldo'), ('ajuste', 'Ajuste del administrador'), ('nube', 'Ampliación de la nube'),
             ('plan_ia', 'Plan con IA')]
    BOLSAS = [('dia', 'Recarga diaria'), ('mes', 'Bolsa del mes'), ('extra', 'Paquete o regalo'), ('saldo', 'Saldo')]
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='movimientos_ia')
    colegio = models.ForeignKey('notas.Colegio', on_delete=models.SET_NULL, null=True, blank=True, related_name='+')
    tipo = models.CharField(max_length=8, choices=TIPOS)
    accion = models.CharField(max_length=20, blank=True)
    bolsa = models.CharField(max_length=5, choices=BOLSAS, blank=True)
    creditos = models.IntegerField(default=0, help_text='Gastados en un uso; ganados en un paquete o regalo.')
    pesos = models.IntegerField(default=0, help_text='Cambio del saldo: + recarga, − gasto.')
    devuelto = models.BooleanField(default=False, help_text='La IA falló y se devolvió lo cobrado.')
    tokens_entrada = models.PositiveIntegerField(default=0)
    tokens_salida = models.PositiveIntegerField(default=0)
    costo_usd = models.DecimalField(max_digits=8, decimal_places=5, default=0)
    detalle = models.CharField(max_length=200, blank=True)
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-creado']

    def __str__(self):
        return f'{self.get_tipo_display()} · {self.usuario}'


class Recarga(models.Model):
    """Una recarga de saldo con Wompi (o a mano, si el pago llegó por transferencia)."""
    ESTADOS = [('pendiente', 'Pendiente'), ('aprobada', 'Aprobada'), ('rechazada', 'Rechazada')]
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='recargas_ia')
    referencia = models.CharField(max_length=40, unique=True)
    monto = models.PositiveIntegerField(help_text='Pesos que paga.')
    bono = models.PositiveIntegerField(default=0)
    estado = models.CharField(max_length=10, choices=ESTADOS, default='pendiente')
    transaccion = models.CharField(max_length=60, blank=True)
    metodo = models.CharField(max_length=30, blank=True)
    creada = models.DateTimeField(auto_now_add=True)
    resuelta = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-creada']

    def __str__(self):
        return self.referencia


# ---------------------------------------------------------------------------
# Biblioteca: banco libre, comunidad y mi colegio
# ---------------------------------------------------------------------------
class MaterialCompartido(models.Model):
    ALCANCES = [('libre', 'Banco libre de mcolegio'), ('comunidad', 'Comunidad mcolegio'), ('colegio', 'Mi colegio')]
    ESTADOS = [('revision', 'En revisión'), ('publicado', 'Publicado'), ('rechazado', 'Rechazado'),
               ('oculto', 'Oculto por reportes')]
    documento = models.ForeignKey(Documento, on_delete=models.SET_NULL, null=True, blank=True, related_name='compartidos')
    autor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='materiales_compartidos')
    colegio = models.ForeignKey('notas.Colegio', on_delete=models.CASCADE, null=True, blank=True, related_name='+')
    alcance = models.CharField(max_length=10, choices=ALCANCES, default='comunidad')
    estado = models.CharField(max_length=10, choices=ESTADOS, default='revision')
    motivo = models.CharField(max_length=300, blank=True, help_text='Por qué se rechazó.')
    titulo = models.CharField(max_length=150)
    tipo = models.CharField(max_length=16, choices=Documento.TIPOS, default='libre')
    area = models.CharField(max_length=80, blank=True)
    grado = models.CharField(max_length=40, blank=True)
    tema = models.CharField(max_length=120, blank=True)
    dba = models.CharField(max_length=200, blank=True, verbose_name='DBA o competencia')
    descripcion = models.CharField(max_length=300, blank=True)
    contenido = models.JSONField(default=dict)
    preguntas = models.PositiveSmallIntegerField(default=0)
    usos = models.PositiveIntegerField(default=0)
    estrellas_suma = models.PositiveIntegerField(default=0)
    estrellas_n = models.PositiveIntegerField(default=0)
    regalo_dado = models.BooleanField(default=False)
    creado = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-actualizado']

    def __str__(self):
        return self.titulo

    @property
    def estrellas(self):
        return round(self.estrellas_suma / self.estrellas_n, 1) if self.estrellas_n else None


class Valoracion(models.Model):
    material = models.ForeignKey(MaterialCompartido, on_delete=models.CASCADE, related_name='valoraciones')
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='+')
    estrellas = models.PositiveSmallIntegerField()

    class Meta:
        constraints = [models.UniqueConstraint(fields=['material', 'usuario'], name='materiales_una_valoracion')]


class Reporte(models.Model):
    material = models.ForeignKey(MaterialCompartido, on_delete=models.CASCADE, related_name='reportes')
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='+')
    motivo = models.CharField(max_length=300)
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['material', 'usuario'], name='materiales_un_reporte')]
