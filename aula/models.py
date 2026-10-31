"""Aula virtual: un mismo motor para dos lugares.

* En mcolegio, un aula por asignación académica (Cálculo 1104): sus estudiantes
  son los del curso y sus notas pasan a la planilla oficial del colegio.
* En Salón Digital, un aula por grupo del docente: sus estudiantes son los
  integrantes del grupo (entran con el código y su nombre) y las notas quedan en
  la planilla propia del aula, que se descarga en Excel.

Partes: muro con comentarios, clase en vivo, material, tareas con entrega e
instrumentos de evaluación (rúbricas y listas de chequeo).
"""
from decimal import Decimal

from django.contrib.auth.models import User
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone

from . import almacen

PLATAFORMAS = [('meet', 'Google Meet'), ('zoom', 'Zoom'), ('teams', 'Microsoft Teams'),
               ('jitsi', 'Jitsi Meet'), ('otra', 'Otra')]


def plataforma_de(url):
    url = (url or '').lower()
    for clave, dominio in (('meet', 'meet.google'), ('zoom', 'zoom.'), ('teams', 'teams.'), ('jitsi', 'jit.si')):
        if dominio in url:
            return clave
    return 'otra' if url else ''


class Aula(models.Model):
    # Uno de los dos: la asignación (colegio) o el grupo (Salón Digital).
    colegio = models.ForeignKey('notas.Colegio', on_delete=models.CASCADE, null=True, blank=True,
                                related_name='aulas')
    asignacion = models.OneToOneField('notas.AsignacionDocente', on_delete=models.CASCADE, null=True, blank=True,
                                      related_name='aula')
    grupo = models.OneToOneField('salon_digital.Grupo', on_delete=models.CASCADE, null=True, blank=True,
                                 related_name='aula')

    bienvenida = models.CharField(max_length=200, blank=True, verbose_name='Mensaje de bienvenida')
    enlace_clase = models.URLField(blank=True, verbose_name='Enlace de la clase en vivo',
                                   help_text='El enlace fijo de Meet, Zoom, Teams o Jitsi.')
    nota_clase = models.CharField(max_length=200, blank=True, verbose_name='Indicaciones para la clase',
                                  help_text='Ej.: «Entrar con la cámara encendida».')
    comentarios_activos = models.BooleanField(default=True, verbose_name='Los estudiantes pueden comentar')
    # Planilla del plan individual: {'pesos': {'tarea:12': 2, 'manual:3': 1}, 'faltantes_minima': false}
    planilla = models.JSONField(default=dict, blank=True)
    creada = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Aula virtual'
        verbose_name_plural = 'Aulas virtuales'

    def __str__(self):
        return self.titulo

    @property
    def es_salon(self):
        return self.grupo_id is not None

    @property
    def titulo(self):
        if self.asignacion_id:
            a = self.asignacion
            return f'{a.materia.nombre} {a.curso.nombre}'
        if self.grupo_id:
            return self.grupo.nombre
        return 'Aula'

    @property
    def subtitulo(self):
        if self.asignacion_id:
            d = self.asignacion.docente
            return f'Prof. {d.user.get_full_name() or d.user.username}' if d else ''
        if self.grupo_id:
            return self.grupo.descripcion or f'Prof. {self.grupo.propietario.nombre_publico}'
        return ''

    @property
    def plataforma(self):
        return plataforma_de(self.enlace_clase)

    @property
    def plataforma_nombre(self):
        return dict(PLATAFORMAS).get(self.plataforma, '')

    @property
    def docente_usuario(self):
        if self.asignacion_id:
            return self.asignacion.docente.user if self.asignacion.docente_id else None
        if self.grupo_id:
            return self.grupo.propietario.usuario
        return None


class Publicacion(models.Model):
    """Lo que el docente pone en el muro."""
    aula = models.ForeignKey(Aula, on_delete=models.CASCADE, related_name='publicaciones')
    autor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='+')
    texto = models.TextField(blank=True)
    enlace = models.URLField(blank=True)
    archivo = models.FileField(upload_to=almacen.ruta_publicacion, storage=almacen.privado, blank=True)
    nombre_archivo = models.CharField(max_length=150, blank=True)
    fijada = models.BooleanField(default=False)
    # Si la publicación anuncia una tarea o un material, enlaza a él.
    tarea = models.ForeignKey('Tarea', on_delete=models.CASCADE, null=True, blank=True, related_name='+')
    creada = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-fijada', '-creada']

    def __str__(self):
        return (self.texto or self.nombre_archivo or 'Publicación')[:60]

    @property
    def es_html(self):
        return self.nombre_archivo.lower().endswith(('.html', '.htm'))

    @property
    def es_imagen(self):
        return self.nombre_archivo.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp'))


class Comentario(models.Model):
    publicacion = models.ForeignKey(Publicacion, on_delete=models.CASCADE, related_name='comentarios')
    # Quién: un usuario (docente o estudiante del colegio) o un integrante de Salón Digital.
    usuario = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='+')
    integrante = models.ForeignKey('salon_digital.Integrante', on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name='+')
    nombre = models.CharField(max_length=150)
    texto = models.CharField(max_length=1000)
    oculto = models.BooleanField(default=False)
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['creado']


class Material(models.Model):
    TIPOS = [('archivo', 'Archivo'), ('enlace', 'Enlace'), ('video', 'Video')]
    aula = models.ForeignKey(Aula, on_delete=models.CASCADE, related_name='materiales')
    periodo = models.ForeignKey('notas.PeriodoAcademico', on_delete=models.SET_NULL, null=True, blank=True,
                                related_name='+')
    unidad = models.CharField(max_length=80, blank=True, verbose_name='Unidad o tema',
                              help_text='Para agrupar: «Unidad 1», «Funciones»…')
    titulo = models.CharField(max_length=150)
    descripcion = models.CharField(max_length=300, blank=True)
    tipo = models.CharField(max_length=8, choices=TIPOS, default='archivo')
    archivo = models.FileField(upload_to=almacen.ruta_material, storage=almacen.privado, blank=True)
    nombre_archivo = models.CharField(max_length=150, blank=True)
    enlace = models.URLField(blank=True)
    para = models.JSONField(default=list, blank=True, help_text='Vacío: toda la clase. Si no, solo los estudiantes escogidos.')
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['unidad', 'creado']

    def __str__(self):
        return self.titulo

    @property
    def es_html(self):
        return self.nombre_archivo.lower().endswith(('.html', '.htm'))

    @property
    def youtube_id(self):
        """El código del video si el enlace es de YouTube (para verlo dentro del aula)."""
        import re
        m = re.search(r'(?:youtu\.be/|youtube\.com/(?:watch\?v=|embed/|shorts/|live/))([\w-]{11})', self.enlace or '')
        return m.group(1) if m else ''


# ---------------------------------------------------------------------------
# Instrumentos de evaluación
# ---------------------------------------------------------------------------
class Instrumento(models.Model):
    """Una rúbrica o una lista de chequeo del docente, reutilizable en varias tareas."""
    TIPOS = [('rubrica', 'Rúbrica'), ('lista', 'Lista de chequeo')]
    propietario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='instrumentos_aula')
    colegio = models.ForeignKey('notas.Colegio', on_delete=models.CASCADE, null=True, blank=True, related_name='+')
    compartido = models.BooleanField(default=False, verbose_name='Compartir con los docentes del colegio')
    tipo = models.CharField(max_length=8, choices=TIPOS, default='rubrica')
    nombre = models.CharField(max_length=120)
    descripcion = models.CharField(max_length=300, blank=True)
    creado = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['nombre']

    def __str__(self):
        return self.nombre

    def criterios_ordenados(self):
        return list(self.criterios.all())

    def niveles_ordenados(self):
        return list(self.niveles.all())


class Nivel(models.Model):
    """Una columna de la rúbrica (Bajo, Básico…) con lo que vale."""
    instrumento = models.ForeignKey(Instrumento, on_delete=models.CASCADE, related_name='niveles')
    nombre = models.CharField(max_length=40)
    valor = models.DecimalField(max_digits=5, decimal_places=2)
    orden = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ['orden', 'valor']


class Criterio(models.Model):
    instrumento = models.ForeignKey(Instrumento, on_delete=models.CASCADE, related_name='criterios')
    nombre = models.CharField(max_length=200)
    peso = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('1'),
                               validators=[MinValueValidator(Decimal('0.01'))])
    orden = models.PositiveSmallIntegerField(default=0)
    # {str(nivel_id): "descriptor"}
    descriptores = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ['orden', 'id']

    def descriptor(self, nivel):
        return (self.descriptores or {}).get(str(nivel.id), '')


# ---------------------------------------------------------------------------
# Tareas y entregas
# ---------------------------------------------------------------------------
class Tarea(models.Model):
    aula = models.ForeignKey(Aula, on_delete=models.CASCADE, related_name='tareas')
    titulo = models.CharField(max_length=60, help_text='Es también el nombre de la columna en la planilla.')
    instrucciones = models.TextField(blank=True)
    archivo = models.FileField(upload_to=almacen.ruta_tarea, storage=almacen.privado, blank=True)
    nombre_archivo = models.CharField(max_length=150, blank=True)
    enlace = models.URLField(blank=True)
    fecha_limite = models.DateTimeField(null=True, blank=True)
    acepta_tardias = models.BooleanField(default=True, verbose_name='Recibir entregas después de la fecha')
    instrumento = models.ForeignKey(Instrumento, on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name='tareas', verbose_name='Cómo se califica')
    # Solo en el colegio: a qué periodo y componente va la nota.
    periodo = models.ForeignKey('notas.PeriodoAcademico', on_delete=models.SET_NULL, null=True, blank=True,
                                related_name='+')
    componente = models.CharField(max_length=6, blank=True)
    publicada = models.BooleanField(default=True)
    para = models.JSONField(default=list, blank=True, help_text='Vacío: toda la clase. Si no, solo los estudiantes escogidos.')
    # Ficha de Mis materiales que se resuelve en línea: copia de sus bloques y cómo se califica
    # ({'modo': 'puntos'|'formativa', 'intentos': 1, 'tiempo': 0, 'mostrar': 'al_terminar'|'nunca'}).
    ficha = models.JSONField(default=dict, blank=True)
    ficha_config = models.JSONField(default=dict, blank=True)
    creada = models.DateTimeField(auto_now_add=True)
    pasada_planilla = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-creada']

    def __str__(self):
        return self.titulo

    @property
    def vencida(self):
        return bool(self.fecha_limite) and timezone.now() > self.fecha_limite

    @property
    def recibe(self):
        return self.publicada and (not self.vencida or self.acepta_tardias)


class Entrega(models.Model):
    ESTADOS = [('entregada', 'Entregada'), ('devuelta', 'Devuelta para corregir'), ('calificada', 'Calificada')]
    tarea = models.ForeignKey(Tarea, on_delete=models.CASCADE, related_name='entregas')
    estudiante = models.ForeignKey('notas.Estudiante', on_delete=models.CASCADE, null=True, blank=True,
                                   related_name='entregas_aula')
    integrante = models.ForeignKey('salon_digital.Integrante', on_delete=models.CASCADE, null=True, blank=True,
                                   related_name='entregas_aula')
    texto = models.TextField(blank=True)
    archivo = models.FileField(upload_to=almacen.ruta_entrega, storage=almacen.privado, blank=True)
    nombre_archivo = models.CharField(max_length=150, blank=True)
    estado = models.CharField(max_length=10, choices=ESTADOS, default='entregada')
    entregada = models.DateTimeField(null=True, blank=True)
    tardia = models.BooleanField(default=False)
    # {str(criterio_id): nivel_id} en rúbricas; {str(criterio_id): true/false} en listas.
    seleccion = models.JSONField(default=dict, blank=True)
    nota = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True,
                               validators=[MinValueValidator(Decimal('0')), MaxValueValidator(Decimal('100'))])
    comentario = models.TextField(blank=True, verbose_name='Comentario para el estudiante')
    calificada = models.DateTimeField(null=True, blank=True)
    # Ficha resuelta en línea: {id_bloque: respuesta}, los puntos que puso el docente a mano y el resumen.
    respuestas = models.JSONField(default=dict, blank=True)
    manuales = models.JSONField(default=dict, blank=True)
    intentos = models.PositiveSmallIntegerField(default=0)
    iniciada = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['tarea', 'estudiante'], condition=models.Q(estudiante__isnull=False),
                                    name='aula_una_entrega_por_estudiante'),
            models.UniqueConstraint(fields=['tarea', 'integrante'], condition=models.Q(integrante__isnull=False),
                                    name='aula_una_entrega_por_integrante'),
        ]

    @property
    def nombre(self):
        if self.estudiante_id:
            u = self.estudiante.user
            return f'{u.last_name} {u.first_name}'.strip() or u.username
        if self.integrante_id:
            return self.integrante.completo
        return ''


# ---------------------------------------------------------------------------
# Escala de valoración del docente (Salón Digital)
# ---------------------------------------------------------------------------
ESCALA_NACIONAL = [
    {'nombre': 'BAJO', 'min': '1.0', 'max': '2.9'},
    {'nombre': 'BÁSICO', 'min': '3.0', 'max': '3.9'},
    {'nombre': 'ALTO', 'min': '4.0', 'max': '4.5'},
    {'nombre': 'SUPERIOR', 'min': '4.6', 'max': '5.0'},
]


def _escala_nacional():
    return [dict(n) for n in ESCALA_NACIONAL]


class EscalaDocente(models.Model):
    """La escala del docente que trabaja por fuera de un colegio (en el colegio rige la del colegio).

    niveles: [{'nombre', 'min', 'max'}] de menor a mayor, con los números como texto.
    """
    usuario = models.OneToOneField(User, on_delete=models.CASCADE, related_name='escala_aula')
    niveles = models.JSONField(default=_escala_nacional)
    actualizada = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Escala del docente'
        verbose_name_plural = 'Escalas de los docentes'

    def lista(self):
        """[(nombre, Decimal min, Decimal max)] de menor a mayor."""
        salida = []
        for n in self.niveles or []:
            try:
                salida.append((str(n['nombre']).upper(), Decimal(str(n['min'])), Decimal(str(n['max']))))
            except Exception:
                continue
        return sorted(salida, key=lambda x: x[1]) or [(n['nombre'], Decimal(n['min']), Decimal(n['max']))
                                                     for n in ESCALA_NACIONAL]



# ---------------------------------------------------------------------------
# Actividades interactivas (apps HTML o enlaces) que pueden devolver la nota
# ---------------------------------------------------------------------------
def _ruta_actividad(instancia, nombre):
    return almacen.ruta_material(instancia, nombre).replace('/material/', '/actividades/')


class Actividad(models.Model):
    aula = models.ForeignKey(Aula, on_delete=models.CASCADE, related_name='actividades')
    titulo = models.CharField(max_length=60)
    descripcion = models.CharField(max_length=300, blank=True)
    archivo = models.FileField(upload_to=_ruta_actividad, storage=almacen.privado, blank=True)
    nombre_archivo = models.CharField(max_length=150, blank=True)
    enlace = models.URLField(blank=True, help_text='GeoGebra, PhET, Wordwall… (se abre dentro del aula si el sitio lo permite).')
    califica = models.BooleanField(default=False, verbose_name='La actividad envía la nota')
    periodo = models.ForeignKey('notas.PeriodoAcademico', on_delete=models.SET_NULL, null=True, blank=True,
                                related_name='+')
    componente = models.CharField(max_length=6, blank=True)
    publicada = models.BooleanField(default=True)
    para = models.JSONField(default=list, blank=True, help_text='Vacío: toda la clase. Si no, solo los estudiantes escogidos.')
    creada = models.DateTimeField(auto_now_add=True)
    pasada_planilla = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-creada']

    def __str__(self):
        return self.titulo


class ResultadoActividad(models.Model):
    actividad = models.ForeignKey(Actividad, on_delete=models.CASCADE, related_name='resultados')
    estudiante = models.ForeignKey('notas.Estudiante', on_delete=models.CASCADE, null=True, blank=True,
                                   related_name='+')
    integrante = models.ForeignKey('salon_digital.Integrante', on_delete=models.CASCADE, null=True, blank=True,
                                   related_name='+')
    nota = models.DecimalField(max_digits=5, decimal_places=2)        # la mejor
    ultima = models.DecimalField(max_digits=5, decimal_places=2)
    intentos = models.PositiveSmallIntegerField(default=1)
    actualizado = models.DateTimeField(auto_now=True)


# ---------------------------------------------------------------------------
# Cuestionarios estilo Quizizz (a su ritmo) y Kahoot (en vivo)
# ---------------------------------------------------------------------------
class Cuestionario(models.Model):
    aula = models.ForeignKey(Aula, on_delete=models.CASCADE, related_name='cuestionarios')
    titulo = models.CharField(max_length=60)
    descripcion = models.CharField(max_length=300, blank=True)
    segundos = models.PositiveSmallIntegerField(default=20, verbose_name='Segundos por pregunta')
    mezclar = models.BooleanField(default=True, verbose_name='Mezclar el orden de las preguntas')
    reintentos = models.BooleanField(default=False, verbose_name='Permitir repetirlo (queda la mejor nota)')
    a_su_ritmo = models.BooleanField(default=True, verbose_name='Abierto para responder a su ritmo')
    periodo = models.ForeignKey('notas.PeriodoAcademico', on_delete=models.SET_NULL, null=True, blank=True,
                                related_name='+')
    componente = models.CharField(max_length=6, blank=True)
    creado = models.DateTimeField(auto_now_add=True)
    pasada_planilla = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-creado']

    def __str__(self):
        return self.titulo


class PreguntaQ(models.Model):
    cuestionario = models.ForeignKey(Cuestionario, on_delete=models.CASCADE, related_name='preguntas')
    orden = models.PositiveSmallIntegerField(default=0)
    texto = models.TextField()
    segundos = models.PositiveSmallIntegerField(null=True, blank=True)

    class Meta:
        ordering = ['orden', 'id']

    @property
    def tiempo(self):
        return self.segundos or self.cuestionario.segundos


class OpcionQ(models.Model):
    pregunta = models.ForeignKey(PreguntaQ, on_delete=models.CASCADE, related_name='opciones')
    texto = models.CharField(max_length=300)
    correcta = models.BooleanField(default=False)
    orden = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ['orden', 'id']


class SesionVivo(models.Model):
    """Una partida en vivo (estilo Kahoot): el docente proyecta y avanza; los estudiantes responden."""
    ESTADOS = [('espera', 'Sala de espera'), ('pregunta', 'Pregunta'), ('resultado', 'Resultado'), ('fin', 'Terminada')]
    cuestionario = models.ForeignKey(Cuestionario, on_delete=models.CASCADE, related_name='sesiones')
    estado = models.CharField(max_length=10, choices=ESTADOS, default='espera')
    indice = models.SmallIntegerField(default=-1)
    orden = models.JSONField(default=list)          # ids de las preguntas en el orden de la partida
    inicio_pregunta = models.DateTimeField(null=True, blank=True)
    creada = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-creada']


class Intento(models.Model):
    cuestionario = models.ForeignKey(Cuestionario, on_delete=models.CASCADE, related_name='intentos')
    sesion = models.ForeignKey(SesionVivo, on_delete=models.CASCADE, null=True, blank=True, related_name='intentos')
    estudiante = models.ForeignKey('notas.Estudiante', on_delete=models.CASCADE, null=True, blank=True,
                                   related_name='+')
    integrante = models.ForeignKey('salon_digital.Integrante', on_delete=models.CASCADE, null=True, blank=True,
                                   related_name='+')
    orden = models.JSONField(default=list)
    actual = models.SmallIntegerField(default=0)
    inicio_pregunta = models.DateTimeField(null=True, blank=True)
    puntos = models.PositiveIntegerField(default=0)
    aciertos = models.PositiveSmallIntegerField(default=0)
    nota = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    iniciado = models.DateTimeField(auto_now_add=True)
    terminado = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-puntos']

    @property
    def nombre(self):
        if self.estudiante_id:
            u = self.estudiante.user
            return f'{u.first_name} {u.last_name}'.strip() or u.username
        return self.integrante.completo if self.integrante_id else ''


class RespuestaQ(models.Model):
    intento = models.ForeignKey(Intento, on_delete=models.CASCADE, related_name='respuestas')
    pregunta = models.ForeignKey(PreguntaQ, on_delete=models.CASCADE, related_name='respuestas')
    opcion = models.ForeignKey(OpcionQ, on_delete=models.SET_NULL, null=True, blank=True, related_name='+')
    correcta = models.BooleanField(default=False)
    milisegundos = models.PositiveIntegerField(default=0)
    puntos = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ('intento', 'pregunta')


class Visto(models.Model):
    """Hasta cuándo vio el estudiante cada sección del aula (para el globo rojo de novedades)."""
    aula = models.ForeignKey(Aula, on_delete=models.CASCADE, related_name='vistos')
    estudiante = models.ForeignKey('notas.Estudiante', on_delete=models.CASCADE, null=True, blank=True,
                                   related_name='+')
    integrante = models.ForeignKey('salon_digital.Integrante', on_delete=models.CASCADE, null=True, blank=True,
                                   related_name='+')
    secciones = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return f'Visto {self.aula_id}'


class ColumnaManual(models.Model):
    """Una columna de notas que el docente del plan individual escribe a mano (quiz en papel, exposición…)."""
    aula = models.ForeignKey(Aula, on_delete=models.CASCADE, related_name='columnas_manuales')
    titulo = models.CharField(max_length=60)
    orden = models.PositiveSmallIntegerField(default=0)
    creada = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['orden', 'id']

    def __str__(self):
        return self.titulo


class NotaManual(models.Model):
    columna = models.ForeignKey(ColumnaManual, on_delete=models.CASCADE, related_name='notas')
    estudiante = models.ForeignKey('notas.Estudiante', on_delete=models.CASCADE, null=True, blank=True,
                                   related_name='+')
    integrante = models.ForeignKey('salon_digital.Integrante', on_delete=models.CASCADE, null=True, blank=True,
                                   related_name='+')
    nota = models.DecimalField(max_digits=5, decimal_places=2)
