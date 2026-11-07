"""Chat interno de cada colegio: conversaciones uno a uno y grupos (curso, asignatura, sala de profesores
y grupos que arma un docente o un directivo).

Reglas (ver reglas.py):
  · Solo personas del mismo colegio.
  · Los estudiantes no se escriben entre ellos en privado. La cuenta del estudiante es también la de su
    acudiente: con ella se escribe a los docentes del curso, al director de grupo y a los directivos.
  · Los mensajes no se borran: quien borra uno lo deja como «mensaje eliminado» y el texto queda guardado
    por si hay un reporte.
  · Texto, fotos, notas de voz y documentos (el colegio puede apagar cada uno). Los archivos son privados.
"""
import datetime

from django.contrib.auth.models import User
from django.db import models

from aula import almacen


def ruta_chat(instancia, nombre):
    return almacen._ruta(f'chat/{instancia.conversacion_id}', nombre)


class AjustesChat(models.Model):
    """Horario de silencio del colegio: los mensajes llegan, pero no avisan al celular ni a la campana."""
    colegio = models.OneToOneField('notas.Colegio', on_delete=models.CASCADE, related_name='ajustes_chat')
    silencio_desde = models.TimeField(default=datetime.time(18, 0), verbose_name='Silencio desde')
    silencio_hasta = models.TimeField(default=datetime.time(6, 0), verbose_name='Silencio hasta')
    silencio_fin_de_semana = models.BooleanField(default=True, verbose_name='Silencio sábados y domingos')
    permitir_fotos = models.BooleanField(default=True, verbose_name='Se pueden enviar fotos')
    permitir_voz = models.BooleanField(default=True, verbose_name='Se pueden enviar notas de voz')
    permitir_documentos = models.BooleanField(default=True, verbose_name='Se pueden enviar documentos (PDF, Word…)')

    def __str__(self):
        return f'Chat de {self.colegio}'


class Conversacion(models.Model):
    TIPOS = [('directa', 'Uno a uno'), ('curso', 'Grupo del curso'), ('asignatura', 'Grupo de la asignatura'),
             ('profesores', 'Sala de profesores'), ('grupo', 'Grupo'),
             ('colegas', 'Colegas: uno a uno'), ('colegas_g', 'Grupo de docentes')]
    # Sin colegio: conversaciones entre colegas docentes de toda la plataforma (ver views_colegas.py)
    colegio = models.ForeignKey('notas.Colegio', on_delete=models.CASCADE, related_name='conversaciones_chat',
                                null=True, blank=True)
    tipo = models.CharField(max_length=10, choices=TIPOS)
    nombre = models.CharField(max_length=80, blank=True)
    # Identifica las conversaciones únicas: «d:3-8» (uno a uno), «c:12» (curso), «a:40» (asignatura), «p» (profesores).
    clave = models.CharField(max_length=40, blank=True)
    curso = models.ForeignKey('notas.Curso', on_delete=models.CASCADE, null=True, blank=True, related_name='+')
    asignacion = models.ForeignKey('notas.AsignacionDocente', on_delete=models.CASCADE, null=True, blank=True,
                                   related_name='+')
    creada_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='+')
    solo_lectura = models.BooleanField(default=False, help_text='Solo los moderadores escriben.')
    creada = models.DateTimeField(auto_now_add=True)
    ultimo_mensaje = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-ultimo_mensaje', '-creada']
        constraints = [models.UniqueConstraint(fields=['colegio', 'clave'], condition=~models.Q(clave=''),
                                               name='chat_una_conversacion_por_clave'),
                       models.UniqueConstraint(fields=['clave'], condition=models.Q(colegio__isnull=True) & ~models.Q(clave=''),
                                               name='chat_colegas_una_por_clave')]

    def __str__(self):
        return self.nombre or f'Conversación {self.pk}'


class PerfilColega(models.Model):
    """Cómo se muestra un docente a los demás docentes de la plataforma (Mis colegas)."""
    usuario = models.OneToOneField(User, on_delete=models.CASCADE, related_name='perfil_colega')
    visible = models.BooleanField(default=True, help_text='Aparece cuando otros docentes buscan colegas.')
    area = models.CharField(max_length=80, blank=True, verbose_name='Área o asignatura')
    presentacion = models.CharField(max_length=200, blank=True, verbose_name='Presentación corta')


class Colega(models.Model):
    """Solicitud de amistad entre dos docentes (solo docentes; nunca estudiantes).
    pendiente: «de» la envió y «para» no ha respondido · aceptada: son colegas · bloqueada: «de» bloqueó a «para»."""
    ESTADOS = [('pendiente', 'Pendiente'), ('aceptada', 'Aceptada'), ('bloqueada', 'Bloqueada')]
    de = models.ForeignKey(User, on_delete=models.CASCADE, related_name='colegas_enviadas')
    para = models.ForeignKey(User, on_delete=models.CASCADE, related_name='colegas_recibidas')
    estado = models.CharField(max_length=10, choices=ESTADOS, default='pendiente')
    mensaje = models.CharField(max_length=200, blank=True)
    creada = models.DateTimeField(auto_now_add=True)
    respondida = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-creada']
        constraints = [models.UniqueConstraint(fields=['de', 'para'], name='chat_una_solicitud_colega')]


class Participante(models.Model):
    conversacion = models.ForeignKey(Conversacion, on_delete=models.CASCADE, related_name='participantes')
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chats')
    moderador = models.BooleanField(default=False)
    silenciada = models.BooleanField(default=False, help_text='No avisa de los mensajes nuevos.')
    ultimo_leido = models.DateTimeField(null=True, blank=True)
    activo = models.BooleanField(default=True, help_text='Falso cuando sale del grupo o deja el curso.')

    class Meta:
        constraints = [models.UniqueConstraint(fields=['conversacion', 'usuario'], name='chat_un_participante')]


class Mensaje(models.Model):
    conversacion = models.ForeignKey(Conversacion, on_delete=models.CASCADE, related_name='mensajes')
    autor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='mensajes_chat')
    TIPOS = [('texto', 'Texto'), ('foto', 'Foto'), ('voz', 'Nota de voz'), ('doc', 'Documento')]
    tipo = models.CharField(max_length=5, choices=TIPOS, default='texto')
    texto = models.TextField(max_length=2000, blank=True)
    archivo = models.FileField(upload_to=ruta_chat, storage=almacen.privado, blank=True)
    peso = models.PositiveIntegerField(default=0)
    duracion = models.PositiveSmallIntegerField(default=0, help_text='Segundos de la nota de voz.')
    nombre_archivo = models.CharField(max_length=150, blank=True, help_text='Nombre original del documento.')
    creado = models.DateTimeField(auto_now_add=True)
    eliminado = models.BooleanField(default=False)
    eliminado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='+')

    class Meta:
        ordering = ['creado', 'id']

    def __str__(self):
        return self.texto[:40] or self.get_tipo_display()


class Reporte(models.Model):
    mensaje = models.ForeignKey(Mensaje, on_delete=models.CASCADE, related_name='reportes')
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='+')
    motivo = models.CharField(max_length=300)
    creado = models.DateTimeField(auto_now_add=True)
    resuelto = models.BooleanField(default=False)
    resuelto_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='+')
    nota = models.CharField(max_length=300, blank=True, help_text='Qué se hizo.')

    class Meta:
        ordering = ['resuelto', '-creado']
        constraints = [models.UniqueConstraint(fields=['mensaje', 'usuario'], name='chat_un_reporte')]


# ---------------------------------------------------------------------------
# Mi Salón Virtual: el docente del plan individual y los estudiantes de sus grupos.
# Los estudiantes no tienen cuenta: entran con el código del grupo y, para escribir o ver
# su chat con el docente, con su PIN (ver salon_digital.Integrante.pin_chat).
# ---------------------------------------------------------------------------
def ruta_salon(instancia, nombre):
    return almacen._ruta(f'chat-salon/{instancia.conversacion_id}', nombre)


class ConversacionSalon(models.Model):
    """Sin integrante: el chat de todo el grupo. Con integrante: el chat de ese estudiante con el docente."""
    grupo = models.ForeignKey('salon_digital.Grupo', on_delete=models.CASCADE, related_name='chats')
    integrante = models.ForeignKey('salon_digital.Integrante', on_delete=models.CASCADE, null=True, blank=True,
                                   related_name='chats')
    solo_lectura = models.BooleanField(default=False, help_text='Solo escribe el docente.')
    docente_leido = models.DateTimeField(null=True, blank=True)
    ultimo_mensaje = models.DateTimeField(null=True, blank=True)
    creada = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-ultimo_mensaje', '-creada']
        constraints = [
            models.UniqueConstraint(fields=['grupo', 'integrante'], name='chat_salon_una_por_integrante'),
            models.UniqueConstraint(fields=['grupo'], condition=models.Q(integrante__isnull=True),
                                    name='chat_salon_uno_del_grupo'),
        ]

    def __str__(self):
        return f'{self.grupo} · {self.integrante or "todo el grupo"}'


class MensajeSalon(models.Model):
    TIPOS = Mensaje.TIPOS
    conversacion = models.ForeignKey(ConversacionSalon, on_delete=models.CASCADE, related_name='mensajes')
    # Sin integrante: lo escribió el docente.
    integrante = models.ForeignKey('salon_digital.Integrante', on_delete=models.CASCADE, null=True, blank=True,
                                   related_name='mensajes_chat')
    tipo = models.CharField(max_length=5, choices=TIPOS, default='texto')
    texto = models.TextField(max_length=2000, blank=True)
    archivo = models.FileField(upload_to=ruta_salon, storage=almacen.privado, blank=True)
    peso = models.PositiveIntegerField(default=0)
    duracion = models.PositiveSmallIntegerField(default=0)
    nombre_archivo = models.CharField(max_length=150, blank=True)
    creado = models.DateTimeField(auto_now_add=True)
    eliminado = models.BooleanField(default=False)

    class Meta:
        ordering = ['creado', 'id']


class LecturaSalon(models.Model):
    """Hasta dónde leyó cada estudiante cada chat (para el número de no leídos)."""
    conversacion = models.ForeignKey(ConversacionSalon, on_delete=models.CASCADE, related_name='lecturas')
    integrante = models.ForeignKey('salon_digital.Integrante', on_delete=models.CASCADE, related_name='+')
    ultimo_leido = models.DateTimeField()

    class Meta:
        constraints = [models.UniqueConstraint(fields=['conversacion', 'integrante'], name='chat_salon_una_lectura')]
