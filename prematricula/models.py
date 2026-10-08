# -*- coding: utf-8 -*-
"""Prematrícula: las familias piden cupo desde el portal y la secretaría decide.

* Configuracion: si está abierta, para qué año y qué texto de bienvenida.
* Requisito: lo que el colegio pide (documentos y otros), configurable.
* PreguntaEncuesta: la encuesta que llena la familia al final, configurable.
* Solicitud: lo que llena la familia. Al aprobarla, la plataforma crea al
  estudiante en su curso (o actualiza la ficha si ya era del colegio).
* Documento: los archivos que sube la familia, uno por requisito.
"""
from django.conf import settings
from django.db import models

from notas.models.perfiles import Colegio, Curso, Estudiante, GRADO_CHOICES, NOMBRE_GRADO, Sede

TIPOS_DOCUMENTO = [('RC', 'Registro civil'), ('TI', 'Tarjeta de identidad'),
                   ('CC', 'Cédula de ciudadanía'), ('CE', 'Cédula de extranjería'),
                   ('PPT', 'Permiso por protección temporal'), ('OT', 'Otro')]
RH = [('O+', 'O+'), ('O-', 'O-'), ('A+', 'A+'), ('A-', 'A-'), ('B+', 'B+'), ('B-', 'B-'),
      ('AB+', 'AB+'), ('AB-', 'AB-')]


class Configuracion(models.Model):
    colegio = models.OneToOneField(Colegio, on_delete=models.CASCADE, related_name='prematricula')
    abierta = models.BooleanField(default=False, verbose_name='Prematrícula abierta',
                                  help_text='Mientras esté abierta, sale en el portal del colegio.')
    ano_lectivo = models.PositiveSmallIntegerField(verbose_name='Año lectivo al que se matricula')
    fecha_cierre = models.DateField(null=True, blank=True, verbose_name='Fecha de cierre',
                                    help_text='Opcional. Después de esta fecha no se reciben solicitudes.')
    permite_antiguos = models.BooleanField(default=True, verbose_name='Recibir también a estudiantes antiguos',
                                           help_text='Confirman cupo y actualizan sus datos.')
    mensaje = models.TextField(blank=True, verbose_name='Mensaje de bienvenida',
                               help_text='Lo que lee la familia antes de empezar: fechas, costos, horarios…')
    tratamiento_datos = models.TextField(
        blank=True, verbose_name='Autorización de tratamiento de datos',
        help_text='Texto que la familia acepta (Ley 1581 de 2012). Si lo deja vacío se usa uno general.')

    class Meta:
        verbose_name = 'Configuración de prematrícula'

    def __str__(self):
        return f'Prematrícula {self.ano_lectivo} · {self.colegio}'

    def esta_abierta(self):
        from django.utils import timezone
        if not self.abierta:
            return False
        return not (self.fecha_cierre and timezone.localdate() > self.fecha_cierre)


class Requisito(models.Model):
    PARA = [('TODOS', 'Todos'), ('NUEVOS', 'Solo estudiantes nuevos'), ('ANTIGUOS', 'Solo antiguos')]
    colegio = models.ForeignKey(Colegio, on_delete=models.CASCADE, related_name='requisitos_prematricula')
    nombre = models.CharField(max_length=150)
    descripcion = models.CharField(max_length=300, blank=True, verbose_name='Indicación para la familia')
    pide_archivo = models.BooleanField(default=True, verbose_name='La familia sube un archivo')
    obligatorio = models.BooleanField(default=True)
    para = models.CharField(max_length=10, choices=PARA, default='TODOS')
    orden = models.PositiveSmallIntegerField(default=0)
    activo = models.BooleanField(default=True)

    class Meta:
        ordering = ['orden', 'id']

    def __str__(self):
        return self.nombre

    def aplica_a(self, tipo):
        return self.para == 'TODOS' or (self.para == 'NUEVOS') == (tipo == 'NUEVO')


class PreguntaEncuesta(models.Model):
    TIPOS = [('UNA', 'Una opción'), ('VARIAS', 'Varias opciones'), ('SINO', 'Sí / No'),
             ('ESCALA', 'Escala de 1 a 5'), ('TEXTO', 'Respuesta abierta')]
    colegio = models.ForeignKey(Colegio, on_delete=models.CASCADE, related_name='preguntas_prematricula')
    texto = models.CharField(max_length=250, verbose_name='Pregunta')
    tipo = models.CharField(max_length=8, choices=TIPOS, default='UNA')
    opciones = models.TextField(blank=True, help_text='Para «una» o «varias» opciones: una opción por línea.')
    obligatoria = models.BooleanField(default=False)
    orden = models.PositiveSmallIntegerField(default=0)
    activa = models.BooleanField(default=True)

    class Meta:
        ordering = ['orden', 'id']

    def __str__(self):
        return self.texto

    def lista_opciones(self):
        if self.tipo == 'SINO':
            return ['Sí', 'No']
        if self.tipo == 'ESCALA':
            return ['1', '2', '3', '4', '5']
        return [o.strip() for o in self.opciones.splitlines() if o.strip()]


class Solicitud(models.Model):
    ESTADOS = [
        ('RECIBIDA', 'Recibida'),
        ('REVISION', 'En revisión'),
        ('PENDIENTE', 'Falta algo'),
        ('APROBADA', 'Aprobada'),
        ('RECHAZADA', 'No aprobada'),
    ]
    TIPOS = [('NUEVO', 'Estudiante nuevo'), ('ANTIGUO', 'Estudiante antiguo')]

    colegio = models.ForeignKey(Colegio, on_delete=models.CASCADE, related_name='solicitudes_prematricula')
    ano_lectivo = models.PositiveSmallIntegerField()
    radicado = models.CharField(max_length=20, unique=True)
    tipo = models.CharField(max_length=8, choices=TIPOS, default='NUEVO')
    estudiante_antiguo = models.ForeignKey(Estudiante, on_delete=models.SET_NULL, null=True, blank=True,
                                           related_name='prematriculas')
    estado = models.CharField(max_length=10, choices=ESTADOS, default='RECIBIDA')
    creada = models.DateTimeField(auto_now_add=True)
    actualizada = models.DateTimeField(auto_now=True)

    # A qué aspira
    grado = models.SmallIntegerField(choices=GRADO_CHOICES, verbose_name='Grado al que se matricula')
    sede = models.ForeignKey(Sede, on_delete=models.SET_NULL, null=True, blank=True,
                             verbose_name='Sede de preferencia')
    jornada = models.CharField(max_length=20, blank=True, verbose_name='Jornada de preferencia')

    # Estudiante
    nombres = models.CharField(max_length=120)
    apellidos = models.CharField(max_length=120)
    tipo_documento = models.CharField(max_length=3, choices=TIPOS_DOCUMENTO, default='TI')
    numero_documento = models.CharField(max_length=20)
    fecha_nacimiento = models.DateField()
    lugar_nacimiento = models.CharField(max_length=120, blank=True)
    genero = models.CharField(max_length=20, blank=True, choices=[
        ('F', 'Femenino'), ('M', 'Masculino'), ('O', 'Otro'), ('N', 'Prefiere no decir')])
    direccion = models.CharField(max_length=200, blank=True, verbose_name='Dirección de residencia')
    barrio = models.CharField(max_length=120, blank=True, verbose_name='Barrio / vereda')
    telefono = models.CharField(max_length=40, blank=True)
    colegio_procedencia = models.CharField(max_length=200, blank=True)
    ultimo_grado = models.CharField(max_length=40, blank=True, verbose_name='Último grado cursado')

    # Salud y emergencia
    eps = models.CharField(max_length=120, blank=True, verbose_name='EPS')
    rh = models.CharField(max_length=3, choices=RH, blank=True, verbose_name='Grupo sanguíneo y RH')
    alergias = models.TextField(blank=True, verbose_name='Enfermedades, alergias o medicamentos')
    necesita_apoyo = models.BooleanField(default=False, verbose_name='Requiere apoyo pedagógico o de inclusión')
    apoyo_detalle = models.CharField(max_length=300, blank=True, verbose_name='Cuál')
    emergencia_nombre = models.CharField(max_length=160, blank=True, verbose_name='Contacto de emergencia')
    emergencia_telefono = models.CharField(max_length=40, blank=True, verbose_name='Teléfono de emergencia')
    emergencia_parentesco = models.CharField(max_length=60, blank=True, verbose_name='Parentesco')

    # Familia
    acudiente_nombre = models.CharField(max_length=160, verbose_name='Nombre del acudiente')
    acudiente_documento = models.CharField(max_length=20, blank=True, verbose_name='Documento del acudiente')
    acudiente_parentesco = models.CharField(max_length=60, blank=True, verbose_name='Parentesco')
    acudiente_celular = models.CharField(max_length=40, verbose_name='Celular del acudiente')
    acudiente_correo = models.EmailField(blank=True, verbose_name='Correo del acudiente')
    acudiente_ocupacion = models.CharField(max_length=120, blank=True, verbose_name='Ocupación')
    madre_nombre = models.CharField(max_length=160, blank=True, verbose_name='Nombre de la madre')
    madre_celular = models.CharField(max_length=40, blank=True, verbose_name='Celular de la madre')
    padre_nombre = models.CharField(max_length=160, blank=True, verbose_name='Nombre del padre')
    padre_celular = models.CharField(max_length=40, blank=True, verbose_name='Celular del padre')

    acepta_datos = models.BooleanField(default=False)
    encuesta = models.JSONField(default=dict, blank=True)

    # Revisión
    checklist = models.JSONField(default=dict, blank=True,
                                 help_text='{id de requisito: true/false} marcado por la secretaría.')
    curso_asignado = models.ForeignKey(Curso, on_delete=models.SET_NULL, null=True, blank=True,
                                       related_name='prematriculas')
    nota_interna = models.TextField(blank=True, verbose_name='Notas internas de la revisión')
    mensaje_familia = models.TextField(blank=True, verbose_name='Mensaje para la familia',
                                       help_text='Lo ve la familia al consultar su solicitud.')
    revisada_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                                     null=True, blank=True, related_name='+')
    decidida = models.DateTimeField(null=True, blank=True)
    estudiante_creado = models.ForeignKey(Estudiante, on_delete=models.SET_NULL, null=True, blank=True,
                                          related_name='+')

    class Meta:
        ordering = ['-creada']
        verbose_name = 'Solicitud de prematrícula'
        verbose_name_plural = 'Solicitudes de prematrícula'

    def __str__(self):
        return f'{self.radicado} · {self.apellidos} {self.nombres}'

    @property
    def nombre_completo(self):
        return f'{self.apellidos} {self.nombres}'.strip()

    @property
    def nombre_grado(self):
        return NOMBRE_GRADO.get(self.grado, '')

    def requisitos(self):
        return [r for r in self.colegio.requisitos_prematricula.filter(activo=True) if r.aplica_a(self.tipo)]

    def estado_requisitos(self):
        """[(requisito, documento o None, cumple True/False/None)]"""
        docs = {d.requisito_id: d for d in self.documentos.all()}
        return [(r, docs.get(r.id), self.checklist.get(str(r.id))) for r in self.requisitos()]

    def faltantes(self):
        return [r for r, _, cumple in self.estado_requisitos() if r.obligatorio and cumple is not True]


def _ruta_documento(instancia, archivo):
    import os
    import uuid
    s = instancia.solicitud
    ext = os.path.splitext(archivo)[1].lower()[:6]
    return f'prematricula/{s.colegio_id}/{s.ano_lectivo}/{s.radicado}/{uuid.uuid4().hex[:10]}{ext}'


def almacenamiento_privado():
    """Los documentos de las familias no quedan públicos.

    En producción los medios van a DigitalOcean Spaces con lectura pública
    (fotos del portal, escudos). Estos no: se guardan privados y solo los
    entrega la vista de la secretaría, que los lee con las credenciales.
    """
    from django.core.files.storage import default_storage
    opciones = getattr(settings, 'STORAGES', {}).get('default', {})
    if 's3boto3' in opciones.get('BACKEND', ''):
        from storages.backends.s3boto3 import S3Boto3Storage
        privadas = dict(opciones.get('OPTIONS', {}))
        privadas.update({'default_acl': 'private', 'querystring_auth': True, 'custom_domain': None})
        privadas.pop('object_parameters', None)
        return S3Boto3Storage(**privadas)
    return default_storage


class Documento(models.Model):
    solicitud = models.ForeignKey(Solicitud, on_delete=models.CASCADE, related_name='documentos')
    requisito = models.ForeignKey(Requisito, on_delete=models.SET_NULL, null=True, blank=True)
    archivo = models.FileField(upload_to=_ruta_documento, storage=almacenamiento_privado)
    nombre_original = models.CharField(max_length=200, blank=True)
    subido = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['requisito__orden', 'id']

    def __str__(self):
        return self.nombre_original or self.archivo.name
