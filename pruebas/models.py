# pruebas/models.py
"""
Módulo de pruebas de la plataforma. Cubre tres cosas:

1. Páginas publicadas  -> subir un .html y que quede en línea (estilo Netlify).
2. Banco de preguntas  -> pruebas importadas a la base de datos, editables.
3. Resultados          -> un único almacén (Sesion + Detalle) para las dos vías.
"""
import posixpath
import secrets

from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone
from django.utils.text import slugify

from notas.models import Colegio, Curso, Estudiante

LETRAS = ['A', 'B', 'C', 'D', 'E', 'F']

AREA_CHOICES = [
    ('MAT', 'Matemáticas'),
    ('LEN', 'Lenguaje'),
    ('CIE', 'Ciencias Naturales'),
    ('SOC', 'Ciencias Sociales'),
    ('ING', 'Inglés'),
    ('OTR', 'Otra'),
]


def clave_aleatoria():
    return secrets.token_hex(3).upper()


def slug_unico(modelo, colegio, texto, pk=None):
    base = slugify(texto)[:180] or 'pagina'
    slug, n = base, 2
    while modelo.objects.filter(colegio=colegio, slug=slug).exclude(pk=pk).exists():
        slug = f'{base}-{n}'
        n += 1
    return slug


# ---------------------------------------------------------------------------
# 1. Páginas publicadas
# ---------------------------------------------------------------------------

class PaginaPublicada(models.Model):
    """Un archivo HTML subido por un docente y servido desde el dominio."""

    colegio = models.ForeignKey(Colegio, on_delete=models.CASCADE, related_name='paginas_publicadas')

    titulo = models.CharField(max_length=200, verbose_name='Nombre de la página')
    slug = models.SlugField(
        max_length=200, blank=True,
        verbose_name='Dirección',
        help_text='Lo que va después de /p/ en el enlace. Se genera solo si lo dejas vacío.',
    )
    descripcion = models.TextField(blank=True, verbose_name='Descripción breve')

    TIPO_CHOICES = [
        ('html', 'Un solo archivo HTML'),
        ('sitio', 'Sitio completo (.zip)'),
    ]
    tipo = models.CharField(max_length=6, choices=TIPO_CHOICES, default='html', editable=False)

    archivo = models.FileField(
        upload_to='paginas/', blank=True,
        verbose_name='Archivo',
        help_text='Un .html suelto, o un .zip con el sitio completo.',
    )

    # Para sitios: carpeta del bucket donde quedaron los archivos extraídos.
    base_sitio = models.CharField(max_length=300, blank=True, editable=False)
    indice = models.CharField(
        max_length=200, default='index.html', blank=True,
        verbose_name='Archivo de entrada',
        help_text='Cuál archivo abre primero. Normalmente index.html.',
    )
    archivos_sitio = models.PositiveIntegerField(default=0, editable=False)

    area = models.CharField(max_length=3, choices=AREA_CHOICES, blank=True)
    grado = models.PositiveSmallIntegerField(null=True, blank=True)

    visible = models.BooleanField(default=True, verbose_name='¿Está publicada?')
    abre_en = models.DateTimeField(
        null=True, blank=True, verbose_name='Se abre el',
        help_text='Déjalo vacío para que esté disponible desde ya.',
    )
    cierra_en = models.DateTimeField(
        null=True, blank=True, verbose_name='Se cierra el',
        help_text='Déjalo vacío para que no se cierre nunca.',
    )
    listar_en_portal = models.BooleanField(
        default=False,
        verbose_name='¿Mostrarla en la lista pública?',
        help_text='Si se desmarca, solo llega quien tenga el enlace.',
    )

    clave_panel = models.CharField(
        max_length=20, default=clave_aleatoria,
        verbose_name='Clave para ver resultados',
        help_text='La que le das a los docentes para descargar los informes.',
    )
    captura_resultados = models.BooleanField(
        default=True,
        verbose_name='¿Guardar los resultados en la plataforma?',
        help_text='Reescribe el ENDPOINT del archivo para que los resultados lleguen aquí.',
    )
    endpoint_reescrito = models.BooleanField(default=False, editable=False)

    creada_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    creada_en = models.DateTimeField(auto_now_add=True)
    actualizada_en = models.DateTimeField(auto_now=True)
    visitas = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ('colegio', 'slug')
        ordering = ['-actualizada_en']
        verbose_name = 'Página publicada'
        verbose_name_plural = 'Páginas publicadas'

    def __str__(self):
        return self.titulo

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slug_unico(PaginaPublicada, self.colegio, self.titulo, self.pk)
        super().save(*args, **kwargs)

    @property
    def ruta(self):
        return f'/p/{self.slug}/'

    @property
    def total_sesiones(self):
        return self.sesiones.count()

    @property
    def url_contenido(self):
        """La dirección real del archivo que se muestra dentro del marco."""
        from django.core.files.storage import default_storage
        if self.tipo == 'sitio' and self.base_sitio:
            return default_storage.url(posixpath.join(self.base_sitio, self.indice or 'index.html'))
        return self.archivo.url if self.archivo else ''

    @property
    def estado(self):
        """'abierta', 'oculta', 'programada' o 'cerrada'."""
        ahora = timezone.now()
        if not self.visible:
            return 'oculta'
        if self.abre_en and ahora < self.abre_en:
            return 'programada'
        if self.cierra_en and ahora > self.cierra_en:
            return 'cerrada'
        return 'abierta'

    @property
    def disponible(self):
        return self.estado == 'abierta'


# ---------------------------------------------------------------------------
# 2. Banco de preguntas
# ---------------------------------------------------------------------------

class Prueba(models.Model):
    colegio = models.ForeignKey(Colegio, on_delete=models.CASCADE, related_name='pruebas')
    titulo = models.CharField(max_length=200, verbose_name='Título de la prueba')
    slug = models.SlugField(max_length=220, blank=True)
    area = models.CharField(max_length=3, choices=AREA_CHOICES, default='MAT')
    grado = models.PositiveSmallIntegerField(verbose_name='Grado')
    descripcion = models.TextField(blank=True, verbose_name='Instrucciones para el estudiante')

    codigo = models.CharField(
        max_length=20, verbose_name='Código de acceso',
        help_text='El que escribe el estudiante para entrar. Ej: MAT7-2026',
    )
    clave_panel = models.CharField(
        max_length=20, default=clave_aleatoria, verbose_name='Clave para ver resultados',
    )

    sede = models.CharField(max_length=120, default='Sede Principal')
    activa = models.BooleanField(default=True, verbose_name='¿Está abierta?')
    permite_reintentos = models.BooleanField(default=True, verbose_name='¿Puede presentarla varias veces?')
    mostrar_retroalimentacion = models.BooleanField(
        default=True, verbose_name='¿Mostrar las respuestas correctas al terminar?',
    )

    creada_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    creada_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [('colegio', 'codigo'), ('colegio', 'slug')]
        ordering = ['grado', 'area', 'titulo']
        verbose_name = 'Prueba'
        verbose_name_plural = 'Pruebas'

    def __str__(self):
        return f'{self.titulo} ({self.get_area_display()} · {self.grado}°)'

    def save(self, *args, **kwargs):
        self.codigo = (self.codigo or '').strip().upper()
        if not self.slug:
            self.slug = slug_unico(Prueba, self.colegio, f'{self.area}-{self.grado}-{self.titulo}', self.pk)
        super().save(*args, **kwargs)

    @property
    def total_preguntas(self):
        return self.preguntas.count()

    @property
    def ruta(self):
        return f'/pruebas/{self.slug}/'


class Pregunta(models.Model):
    prueba = models.ForeignKey(Prueba, on_delete=models.CASCADE, related_name='preguntas')
    orden = models.PositiveSmallIntegerField(default=0)

    codigo_origen = models.CharField(max_length=30, blank=True)
    competencia = models.CharField(max_length=10, blank=True, help_text='Sigla: NV, GM, AL, SEM, SIN, PRA...')
    competencia_nombre = models.CharField(max_length=120, blank=True)
    tema = models.CharField(max_length=200, blank=True)
    aprendizaje = models.TextField(blank=True, verbose_name='Aprendizaje evaluado')

    enunciado = models.TextField(verbose_name='Contexto o enunciado')
    pregunta = models.TextField(blank=True, verbose_name='Pregunta concreta')

    imagen = models.ImageField(upload_to='pruebas/figuras/', blank=True, null=True)
    tabla = models.JSONField(
        blank=True, null=True,
        help_text='Formato {"h": ["encabezado", ...], "r": [["fila", ...], ...]}',
    )

    clave = models.CharField(max_length=1, verbose_name='Respuesta correcta')
    explicacion = models.TextField(blank=True, verbose_name='Explicación de la respuesta')
    analisis_error = models.TextField(blank=True, verbose_name='Análisis del error frecuente')
    pct_referencia = models.FloatField(
        null=True, blank=True, verbose_name='% de acierto de referencia',
        help_text='Resultado de una aplicación anterior. Solo sirve de comparación.',
    )

    class Meta:
        ordering = ['orden', 'id']
        verbose_name = 'Pregunta'
        verbose_name_plural = 'Preguntas'

    def __str__(self):
        return f'{self.prueba.codigo} · P{self.orden}'


class Opcion(models.Model):
    pregunta = models.ForeignKey(Pregunta, on_delete=models.CASCADE, related_name='opciones')
    letra = models.CharField(max_length=1)
    texto = models.TextField(blank=True)
    imagen = models.ImageField(upload_to='pruebas/opciones/', blank=True, null=True)

    class Meta:
        ordering = ['letra']
        unique_together = ('pregunta', 'letra')
        verbose_name = 'Opción'
        verbose_name_plural = 'Opciones'

    def __str__(self):
        return f'{self.letra}. {self.texto[:40]}'


# ---------------------------------------------------------------------------
# 3. Resultados (almacén único)
# ---------------------------------------------------------------------------

class Sesion(models.Model):
    """Una presentación terminada, venga de una página subida o del banco.

    Guarda los mismos campos que enviaba el HTML original, para que los archivos
    ya generados funcionen sin modificarles la estructura del envío.
    """

    colegio = models.ForeignKey(Colegio, on_delete=models.CASCADE, related_name='sesiones_prueba')
    pagina = models.ForeignKey(
        PaginaPublicada, on_delete=models.CASCADE, null=True, blank=True, related_name='sesiones',
    )
    prueba = models.ForeignKey(
        Prueba, on_delete=models.CASCADE, null=True, blank=True, related_name='sesiones',
    )

    clave_prueba = models.CharField(max_length=30, blank=True, help_text='El campo "prueba" del envío (ej: p1).')
    prueba_nombre = models.CharField(max_length=200, blank=True)

    apellidos = models.CharField(max_length=120, blank=True)
    nombres = models.CharField(max_length=120, blank=True)
    completo = models.CharField(max_length=240, blank=True, db_index=True)
    sede = models.CharField(max_length=120, blank=True)
    grupo = models.CharField(max_length=30, blank=True)

    fecha = models.DateTimeField(default=timezone.now)
    aciertos = models.PositiveSmallIntegerField(default=0)
    total = models.PositiveSmallIntegerField(default=0)
    porcentaje = models.FloatField(default=0)
    segundos = models.PositiveIntegerField(default=0)
    cambios = models.PositiveSmallIntegerField(default=0)
    vez = models.PositiveSmallIntegerField(default=1)

    estudiante = models.ForeignKey(
        Estudiante, on_delete=models.SET_NULL, null=True, blank=True, related_name='sesiones_prueba',
    )
    curso = models.ForeignKey(Curso, on_delete=models.SET_NULL, null=True, blank=True)

    payload = models.JSONField(null=True, blank=True, editable=False)
    recibido_en = models.DateTimeField(auto_now_add=True)
    ip = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        ordering = ['-fecha']
        verbose_name = 'Resultado'
        verbose_name_plural = 'Resultados'
        indexes = [models.Index(fields=['colegio', '-fecha'])]

    def __str__(self):
        return f'{self.completo} · {self.prueba_nombre} · {self.porcentaje}%'

    @property
    def franja(self):
        """Las mismas cuatro franjas de color del HTML original."""
        p = self.porcentaje
        if p <= 20:
            return ('Rojo', '#B3261E')
        if p < 40:
            return ('Naranja', '#D98324')
        if p < 70:
            return ('Amarillo', '#9E1982')
        return ('Verde', '#2E7D32')

    @property
    def origen(self):
        return self.pagina or self.prueba


class Detalle(models.Model):
    sesion = models.ForeignKey(Sesion, on_delete=models.CASCADE, related_name='detalles')
    orden = models.PositiveSmallIntegerField(default=0)

    numero = models.CharField(max_length=30, blank=True, help_text='Id de la pregunta en el banco original.')
    aprendizaje = models.TextField(blank=True)
    competencia = models.CharField(max_length=10, blank=True)
    acierto = models.BooleanField(default=False)
    marcada = models.CharField(max_length=2, blank=True)
    clave = models.CharField(max_length=2, blank=True)
    explicacion = models.TextField(blank=True)
    intentos = models.PositiveSmallIntegerField(default=0)
    segundos = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['orden', 'id']
        verbose_name = 'Detalle de respuesta'
        verbose_name_plural = 'Detalles de respuesta'
