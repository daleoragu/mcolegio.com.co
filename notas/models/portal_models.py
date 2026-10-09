# notas/models/portal_models.py
from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
# 👇 MODIFICADO: Importamos Colegio
from .perfiles import Colegio

class DocumentoPublico(models.Model):
    # 👇 MODIFICADO: Se añade null=True para permitir la migración
    colegio = models.ForeignKey(Colegio, on_delete=models.CASCADE, related_name="documentos_publicos", null=True)
    titulo = models.CharField(max_length=200, verbose_name="Título del Documento")
    descripcion = models.TextField(blank=True, verbose_name="Descripción Breve")
    # RUTA CORREGIDA: Se elimina 'media/'.
    archivo = models.FileField(upload_to='documentos_publicos/', verbose_name="Archivo (PDF, Word, etc.)")
    fecha_publicacion = models.DateTimeField(default=timezone.now, verbose_name="Fecha de Publicación")
    
    def __str__(self):
        return self.titulo

    class Meta:
        verbose_name = "Documento Público"
        verbose_name_plural = "Documentos Públicos"
        ordering = ['-fecha_publicacion']

class FotoGaleria(models.Model):
    # 👇 MODIFICADO: Se añade null=True para permitir la migración
    colegio = models.ForeignKey(Colegio, on_delete=models.CASCADE, related_name="fotos_galeria", null=True)
    titulo = models.CharField(max_length=150, verbose_name="Título de la Foto", help_text="Un título o descripción corta.")
    # RUTA CORREGIDA:
    imagen = models.ImageField(upload_to='galeria_portal/', verbose_name="Fotografía", blank=True)
    fecha_subida = models.DateTimeField(default=timezone.now)
    # En vez de subir el archivo se puede enlazar (notas/videos.py: analizar_foto). No ocupa espacio.
    FUENTES = [('archivo', 'Archivo subido'), ('drive', 'Google Drive'), ('instagram', 'Instagram'), ('facebook', 'Facebook')]
    fuente = models.CharField(max_length=10, choices=FUENTES, default='archivo')
    enlace = models.CharField(max_length=500, blank=True, verbose_name='Enlace')
    imagen_externa = models.URLField(max_length=500, blank=True)     # Drive: la foto se muestra como cualquier otra
    embed = models.URLField(max_length=600, blank=True)              # Instagram / Facebook: la publicación incrustada

    def __str__(self):
        return self.titulo

    @property
    def url_imagen(self):
        """La dirección de la foto ('' si es una publicación incrustada)."""
        if self.imagen:
            return self.imagen.url
        return self.imagen_externa

    @property
    def es_publicacion(self):
        return self.fuente in ('instagram', 'facebook')
    
    class Meta:
        verbose_name = "Foto de la Galería"
        verbose_name_plural = "Fotos de la Galería"
        ordering = ['-fecha_subida']

class Noticia(models.Model):
    # 👇 MODIFICADO: Se añade null=True para permitir la migración
    colegio = models.ForeignKey(Colegio, on_delete=models.CASCADE, related_name="noticias", null=True)
    ESTADO_CHOICES = [('BORRADOR', 'Borrador'), ('PUBLICADO', 'Publicado')]
    titulo = models.CharField(max_length=255, verbose_name="Titular de la Noticia")
    resumen = models.CharField(max_length=500, verbose_name="Resumen Corto")
    cuerpo = models.TextField(verbose_name="Contenido Completo de la Noticia")
    # RUTA CORREGIDA:
    imagen_portada = models.ImageField(upload_to='noticias_portal/', verbose_name="Imagen de Portada", null=True, blank=True)
    fecha_publicacion = models.DateTimeField(default=timezone.now)
    autor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    estado = models.CharField(max_length=10, choices=ESTADO_CHOICES, default='BORRADOR')

    def __str__(self):
        return self.titulo

    class Meta:
        verbose_name = "Noticia"
        verbose_name_plural = "Noticias"
        ordering = ['-fecha_publicacion']

class ImagenCarrusel(models.Model):
    # 👇 MODIFICADO: Se añade null=True para permitir la migración
    colegio = models.ForeignKey(Colegio, on_delete=models.CASCADE, related_name="imagenes_carrusel", null=True)
    titulo = models.CharField(max_length=100, blank=True)
    subtitulo = models.CharField(max_length=200, blank=True)
    # RUTA CORREGIDA:
    imagen = models.ImageField(upload_to='carrusel_portal/', verbose_name="Imagen de fondo")
    orden = models.PositiveIntegerField(default=0)
    visible = models.BooleanField(default=True)
    
    def __str__(self):
        return self.titulo or f"Imagen {self.id}"

    class Meta:
        verbose_name = "Imagen del Carrusel"
        verbose_name_plural = "Imágenes del Carrusel"
        ordering = ['orden']


EXTENSIONES_RECURSO = ['pdf', 'doc', 'docx', 'ppt', 'pptx', 'xls', 'xlsx', 'odt', 'odp', 'ods',
                       'jpg', 'jpeg', 'png', 'mp3', 'mp4', 'zip', 'ggb']


class RecursoEducativo(models.Model):
    """Un recurso de la sección «Recursos educativos» del portal: un enlace
    (Khan Academy, un video, una plataforma) o un archivo (guía, taller…)."""
    colegio = models.ForeignKey(Colegio, on_delete=models.CASCADE, related_name='recursos_educativos')
    titulo = models.CharField(max_length=150, verbose_name='Título')
    descripcion = models.CharField(max_length=300, blank=True, verbose_name='Descripción breve')
    categoria = models.CharField(max_length=80, blank=True, verbose_name='Categoría',
                                 help_text='Agrupa los recursos en el portal. Ej.: Plataformas gratuitas, Guías de grado 6.°')
    enlace = models.URLField(max_length=500, blank=True, verbose_name='Enlace (opcional)')
    archivo = models.FileField(upload_to='recursos_portal/', blank=True, verbose_name='Archivo (opcional)')
    orden = models.PositiveSmallIntegerField(default=0, verbose_name='Orden')
    visible = models.BooleanField(default=True, verbose_name='Visible en el portal')
    creado = models.DateTimeField(default=timezone.now)

    class Meta:
        verbose_name = 'Recurso educativo'
        verbose_name_plural = 'Recursos educativos'
        ordering = ['categoria', 'orden', 'titulo']

    def __str__(self):
        return self.titulo

    @property
    def url(self):
        if self.archivo:
            return self.archivo.url
        return self.enlace


class VideoPortal(models.Model):
    """Un video del portal (YouTube, Vimeo, Drive o Facebook). Lo publican docentes y administrativos.

    Solo se guarda lo que sale de notas/videos.py (el identificador y la dirección
    armada allí), nunca el código que pegó la persona.
    """
    PROVEEDORES = [('youtube', 'YouTube'), ('vimeo', 'Vimeo'), ('drive', 'Google Drive'), ('facebook', 'Facebook')]

    colegio = models.ForeignKey(Colegio, on_delete=models.CASCADE, related_name='videos_portal')
    titulo = models.CharField(max_length=150, verbose_name='Título')
    descripcion = models.TextField(max_length=600, blank=True, verbose_name='Descripción (opcional)')
    enlace = models.CharField(max_length=500, verbose_name='Enlace del video')
    proveedor = models.CharField(max_length=10, choices=PROVEEDORES)
    video_id = models.CharField(max_length=200)
    embed = models.URLField(max_length=600)
    miniatura = models.URLField(max_length=300, blank=True)
    destacado = models.BooleanField(default=True, verbose_name='Mostrar en la página de inicio')
    visible = models.BooleanField(default=True, verbose_name='Publicado')
    autor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    creado = models.DateTimeField(default=timezone.now)

    class Meta:
        verbose_name = 'Video del portal'
        verbose_name_plural = 'Videos del portal'
        ordering = ['-creado']

    def __str__(self):
        return self.titulo
