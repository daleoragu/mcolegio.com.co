# notas/models/comunicaciones.py
from django.db import models
from django.contrib.auth.models import User
# 👇 MODIFICADO: Importamos Colegio
from .perfiles import Estudiante, Docente, Colegio

class Mensaje(models.Model):
    # 👇 MODIFICADO: Se añade null=True para permitir la migración
    colegio = models.ForeignKey(Colegio, on_delete=models.CASCADE, related_name="mensajes", null=True)
    # --- INICIO: Se añaden las opciones para el estado ---
    ESTADO_CHOICES = [
        ('ENVIADO', 'Enviado'),
        ('BORRADOR', 'Borrador'),
    ]
    # --- FIN ---

    remitente = models.ForeignKey(User, on_delete=models.CASCADE, related_name="mensajes_enviados", verbose_name="Remitente")
    destinatario = models.ForeignKey(User, on_delete=models.CASCADE, related_name="mensajes_recibidos", verbose_name="Destinatario")
    asunto = models.CharField(max_length=200, verbose_name="Asunto")
    cuerpo = models.TextField(verbose_name="Cuerpo del Mensaje")
    fecha_envio = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Envío")
    leido = models.BooleanField(default=False, verbose_name="¿Leído?")
    
    # --- INICIO: Se añade el nuevo campo 'estado' ---
    estado = models.CharField(
        max_length=10,
        choices=ESTADO_CHOICES,
        default='ENVIADO',
        verbose_name="Estado del Mensaje"
    )
    # --- FIN ---

    eliminado_por_remitente = models.BooleanField(default=False)
    eliminado_por_destinatario = models.BooleanField(default=False)
    fecha_eliminacion = models.DateTimeField(null=True, blank=True, verbose_name="Fecha de Eliminación")
    # Cada lado decide por su cuenta: destacar, y sacar de la papelera para siempre sin borrárselo al otro.
    destacado_por_remitente = models.BooleanField(default=False)
    destacado_por_destinatario = models.BooleanField(default=False)
    purgado_por_remitente = models.BooleanField(default=False)
    purgado_por_destinatario = models.BooleanField(default=False)

    def __str__(self):
        return f"De: {self.remitente.username} | Para: {self.destinatario.username} | Asunto: {self.asunto}"

    class Meta:
        verbose_name = "Mensaje"
        verbose_name_plural = "Mensajes"
        ordering = ['-fecha_envio']

# --- Los siguientes modelos no se modifican ---
TIPOS_FALTA = [('I', 'Tipo I'), ('II', 'Tipo II'), ('III', 'Tipo III')]


class FaltaCatalogo(models.Model):
    """Una situación del manual de convivencia que el docente escoge al anotar en el observador.

    Ley 1620 de 2013 y Decreto 1965 de 2013: situaciones Tipo I, II y III. El colegio
    arma su lista (a mano, desde Excel o partiendo de los ejemplos) y el docente la
    busca al escribir la observación en vez de redactarla cada vez.
    """
    colegio = models.ForeignKey(Colegio, on_delete=models.CASCADE, related_name='faltas_catalogo')
    tipo_falta = models.CharField(max_length=3, choices=TIPOS_FALTA, verbose_name='Tipo')
    numeral = models.CharField(max_length=40, blank=True, default='', verbose_name='Numeral del manual',
                               help_text='Por ejemplo «Art. 45, num. 3». Opcional.')
    descripcion = models.TextField(verbose_name='Descripción')
    activa = models.BooleanField(default=True)

    class Meta:
        ordering = ['tipo_falta', 'numeral', 'id']
        verbose_name = 'Falta del catálogo'
        verbose_name_plural = 'Catálogo de faltas'

    def __str__(self):
        return f'{self.get_tipo_falta_display()} · {self.numeral + " · " if self.numeral else ""}{self.descripcion[:60]}'


class RegistroObservador(models.Model):
    # 👇 MODIFICADO: Se añade null=True para permitir la migración
    colegio = models.ForeignKey(Colegio, on_delete=models.CASCADE, related_name="registros_observador", null=True)
    TIPO_CHOICES = [('ACADEMICA', 'Académica'), ('COMPORTAMENTAL', 'Comportamental')]
    SUBTIPO_CHOICES = [('POSITIVA', 'Positiva'), ('NEGATIVA', 'A Mejorar')]

    estudiante = models.ForeignKey(Estudiante, on_delete=models.CASCADE, related_name="registros_observador")
    docente_reporta = models.ForeignKey(Docente, on_delete=models.SET_NULL, null=True, related_name="observaciones_hechas")
    fecha_suceso = models.DateField(verbose_name="Fecha del Suceso")
    tipo = models.CharField(max_length=15, choices=TIPO_CHOICES)
    subtipo = models.CharField(max_length=10, choices=SUBTIPO_CHOICES, blank=True, null=True, help_text="Positiva o a mejorar. Aplica tanto a convivencia como a académicas.")
    descripcion = models.TextField(verbose_name="Descripción del Suceso (Docente)")
    fecha_registro = models.DateTimeField(auto_now_add=True)
    descargo_estudiante = models.TextField(verbose_name="Descargo del Estudiante", blank=True, null=True)
    fecha_descargo = models.DateTimeField(null=True, blank=True)
    notificado_a_estudiante = models.BooleanField(default=False)
    # Respuesta del acudiente desde el enlace del correo (sin usuario).
    acudiente_enterado = models.DateTimeField(null=True, blank=True, verbose_name="Acudiente enterado el")
    firma_acudiente = models.CharField(max_length=160, blank=True, default='', verbose_name="Quién firmó como enterado")
    descargo_acudiente = models.TextField(blank=True, default='', verbose_name="Descargo o comentario del acudiente")
    falta = models.ForeignKey(FaltaCatalogo, on_delete=models.SET_NULL, null=True, blank=True,
                              related_name='registros', verbose_name='Falta del catálogo')
    tipo_falta = models.CharField(max_length=3, choices=TIPOS_FALTA, blank=True, default='',
                                  verbose_name='Tipo de falta')

    def __str__(self):
        return f"Observación para {self.estudiante} del {self.fecha_suceso}"
    
    class Meta:
        ordering = ['-fecha_suceso']
        verbose_name = "Registro del Observador"
        verbose_name_plural = "Registros del Observador"

class NotificacionManager(models.Manager):
    def bulk_create(self, objs, *args, **kwargs):
        """Las que se crean de a muchas (circulares, plazos…) también salen al celular."""
        creadas = super().bulk_create(objs, *args, **kwargs)
        from notas import push
        push.programar(creadas)
        return creadas


class Notificacion(models.Model):
    objects = NotificacionManager()
    # 👇 MODIFICADO: Se añade null=True para permitir la migración
    colegio = models.ForeignKey(Colegio, on_delete=models.CASCADE, related_name="notificaciones", null=True)
    destinatario = models.ForeignKey(User, on_delete=models.CASCADE, related_name="notificaciones")
    mensaje = models.CharField(max_length=255)
    leido = models.BooleanField(default=False)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    url = models.URLField(max_length=200, null=True, blank=True)
    TIPO_CHOICES = [
        ('MENSAJE', 'Nuevo Mensaje'),
        ('OBSERVADOR', 'Observación Registrada'),
        ('PERIODO', 'Cambio en Periodo'),
        ('RENDIMIENTO', 'Alerta de Rendimiento'),
        ('GENERAL', 'Aviso General'),
        ('PLANILLA', 'Cambio en la planilla'),
    ]
    tipo = models.CharField(max_length=15, choices=TIPO_CHOICES, default='GENERAL')

    def __str__(self):
        return f"Notificación para {self.destinatario.username}: {self.mensaje[:30]}"

    class Meta:
        ordering = ['-fecha_creacion']
        verbose_name = "Notificación"
        verbose_name_plural = "Notificaciones"


class SuscripcionPush(models.Model):
    """Un celular o computador que aceptó recibir las notificaciones de la plataforma.

    Las guarda el navegador al tocar «Activar avisos»; el endpoint es la dirección
    del servicio de notificaciones del navegador (Google, Apple, Mozilla)."""
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='suscripciones_push')
    colegio = models.ForeignKey(Colegio, on_delete=models.CASCADE, null=True, blank=True, related_name='+')
    endpoint = models.TextField()
    p256dh = models.CharField(max_length=200)
    auth = models.CharField(max_length=100)
    dispositivo = models.CharField(max_length=200, blank=True)
    creada = models.DateTimeField(auto_now_add=True)
    ultimo_envio = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('endpoint', 'usuario')     # un celular puede tener abiertas las cuentas de varios hijos
        verbose_name = 'Celular con notificaciones'
        verbose_name_plural = 'Celulares con notificaciones'

    def __str__(self):
        return f'{self.usuario} · {self.dispositivo[:40]}'


class ClavePush(models.Model):
    """Las llaves VAPID de la plataforma (una sola fila). Se crean solas la primera vez.

    Si se cambian, todos los celulares tienen que volver a activar los avisos."""
    privada = models.CharField(max_length=100)
    publica = models.CharField(max_length=200)
    creada = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Llave de notificaciones'
        verbose_name_plural = 'Llaves de notificaciones'
