# salon_digital/models.py
"""
Salón Digital — herramientas para docentes dentro de mcolegio.com.co.

Tres partes:
  1. Cuentas    -> quién publica, su verificación y su plan.
  2. Contenido  -> páginas HTML publicadas y banco de preguntas.
  3. Resultados -> almacén único para lo que envían las actividades.
"""
import posixpath
import secrets
from datetime import timedelta

from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone
from django.utils.text import slugify

LETRAS = ['A', 'B', 'C', 'D', 'E', 'F']

AREA_CHOICES = [
    ('MAT', 'Matemáticas'),
    ('LEN', 'Lenguaje'),
    ('CIE', 'Ciencias Naturales'),
    ('SOC', 'Ciencias Sociales'),
    ('ING', 'Inglés'),
    ('OTR', 'Otra'),
]

# Qué puede hacer cada plan. 0 significa sin límite.
LIMITES = {
    'prueba':    {'paginas': 3,  'resultados_mes': 300,   'mb': 25,  'dias': 15},
    'mensual':   {'paginas': 30, 'resultados_mes': 5000,  'mb': 60,  'dias': 30},
    'anual':     {'paginas': 60, 'resultados_mes': 15000, 'mb': 60,  'dias': 365},
    'ilimitado': {'paginas': 0,  'resultados_mes': 0,     'mb': 200, 'dias': 0},
}


def clave_aleatoria():
    return secrets.token_hex(3).upper()


def slug_unico(modelo, texto, pk=None, **ambito):
    base = slugify(texto)[:180] or 'pagina'
    slug, n = base, 2
    while modelo.objects.filter(slug=slug, **ambito).exclude(pk=pk).exists():
        slug = f'{base}-{n}'
        n += 1
    return slug


# ---------------------------------------------------------------------------
# 1. Cuentas
# ---------------------------------------------------------------------------

class Cuenta(models.Model):
    """Un docente que publica en Salón Digital."""

    PLAN_CHOICES = [
        ('prueba', 'Prueba gratuita'),
        ('mensual', 'Mensual'),
        ('anual', 'Anual'),
        ('ilimitado', 'Ilimitado'),
    ]
    ESTADO_CHOICES = [
        ('sin_enviar', 'Sin enviar documento'),
        ('pendiente', 'Pendiente de revisión'),
        ('verificada', 'Verificada'),
        ('rechazada', 'Rechazada'),
    ]
    DOCUMENTO_CHOICES = [
        ('constancia', 'Constancia laboral'),
        ('diploma', 'Diploma o acta de grado'),
        ('carne', 'Carné docente'),
        ('estudiante', 'Certificado de estudiante de licenciatura'),
    ]

    usuario = models.OneToOneField(User, on_delete=models.CASCADE, related_name='cuenta_salon')

    slug = models.SlugField(
        max_length=60, unique=True,
        verbose_name='Nombre de usuario',
        help_text='Es lo que aparece en el enlace de tus páginas. Ej: mcolegio.com.co/p/davidramos/',
    )
    nombre_publico = models.CharField(max_length=120, verbose_name='Nombre para mostrar')
    institucion = models.CharField(max_length=200, blank=True, verbose_name='Institución donde trabaja')
    municipio = models.CharField(max_length=100, blank=True)
    departamento = models.CharField(max_length=100, blank=True)
    telefono = models.CharField(max_length=30, blank=True, verbose_name='Celular (opcional)')

    # --- Verificación ---
    estado = models.CharField(max_length=12, choices=ESTADO_CHOICES, default='sin_enviar')
    tipo_documento = models.CharField(max_length=12, choices=DOCUMENTO_CHOICES, blank=True)
    documento = models.FileField(
        upload_to='salon/verificacion/', blank=True, null=True,
        verbose_name='Constancia, diploma o carné',
    )
    revisada_por = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name='cuentas_revisadas',
    )
    revisada_en = models.DateTimeField(null=True, blank=True)
    nota_revision = models.TextField(
        blank=True, verbose_name='Observación de la revisión',
        help_text='Si se rechaza, lo que vea el docente para corregir.',
    )

    # --- Plan ---
    plan = models.CharField(max_length=12, choices=PLAN_CHOICES, default='prueba')
    vence_en = models.DateField(null=True, blank=True)

    creada_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-creada_en']
        verbose_name = 'Cuenta de Salón Digital'
        verbose_name_plural = 'Cuentas de Salón Digital'

    def __str__(self):
        return f'{self.nombre_publico} ({self.slug})'

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slug_unico(Cuenta, self.nombre_publico or self.usuario.username, self.pk)
        if not self.vence_en and self.plan == 'prueba':
            self.vence_en = timezone.localdate() + timedelta(days=LIMITES['prueba']['dias'])
        super().save(*args, **kwargs)

    # --- Estado ---

    @property
    def verificada(self):
        return self.estado == 'verificada'

    @property
    def vencida(self):
        return bool(self.vence_en) and self.vence_en < timezone.localdate()

    @property
    def dias_restantes(self):
        if not self.vence_en:
            return None
        return (self.vence_en - timezone.localdate()).days

    @property
    def activa(self):
        """Puede publicar: verificada y con el plan al día."""
        return self.verificada and not self.vencida

    @property
    def motivo_inactiva(self):
        if not self.verificada:
            return dict(self.ESTADO_CHOICES).get(self.estado, 'Sin verificar')
        if self.vencida:
            return 'Plan vencido'
        return ''

    # --- Límites ---

    def limite(self, cual):
        return LIMITES.get(self.plan, LIMITES['prueba']).get(cual, 0)

    @property
    def paginas_usadas(self):
        return self.paginas.count()

    @property
    def resultados_del_mes(self):
        inicio = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        return self.sesiones.filter(recibido_en__gte=inicio).count()

    def puede_publicar_otra(self):
        tope = self.limite('paginas')
        return tope == 0 or self.paginas_usadas < tope

    def puede_recibir_resultados(self):
        tope = self.limite('resultados_mes')
        return tope == 0 or self.resultados_del_mes < tope

    def extender(self, plan, dias=None):
        """Activa o renueva un plan. Lo usa el administrador al recibir el pago."""
        self.plan = plan
        dias = dias if dias is not None else LIMITES.get(plan, {}).get('dias', 0)
        if dias:
            desde = max(self.vence_en or timezone.localdate(), timezone.localdate())
            self.vence_en = desde + timedelta(days=dias)
        else:
            self.vence_en = None
        self.save(update_fields=['plan', 'vence_en'])
        return self


# ---------------------------------------------------------------------------
# 2. Grupos (opcionales)
# ---------------------------------------------------------------------------

def codigo_grupo():
    """Seis letras fáciles de dictar en voz alta: sin I, O, 0, 1."""
    alfabeto = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789'
    return ''.join(secrets.choice(alfabeto) for _ in range(6))


class Grupo(models.Model):
    """Un curso del docente. Sirve para que los resultados lleguen ordenados.

    No es obligatorio: una actividad puede recibir estudiantes que solo escriben
    su nombre. El grupo organiza, no restringe.
    """

    propietario = models.ForeignKey(Cuenta, on_delete=models.CASCADE, related_name='grupos')
    nombre = models.CharField(max_length=60, verbose_name='Nombre del grupo', help_text='Ej: 7-01')
    descripcion = models.CharField(max_length=200, blank=True, verbose_name='Descripción')
    codigo = models.CharField(
        max_length=8, unique=True, default=codigo_grupo,
        verbose_name='Código para entrar',
        help_text='El que les dictas a los estudiantes la primera vez.',
    )
    activo = models.BooleanField(default=True)
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('propietario', 'nombre')
        ordering = ['nombre']
        verbose_name = 'Grupo'
        verbose_name_plural = 'Grupos'

    def __str__(self):
        return self.nombre

    @property
    def total_integrantes(self):
        return self.integrantes.filter(activo=True).count()


class Integrante(models.Model):
    """Un estudiante dentro de un grupo. Sin cuenta ni contraseña."""

    grupo = models.ForeignKey(Grupo, on_delete=models.CASCADE, related_name='integrantes')
    apellidos = models.CharField(max_length=120)
    nombres = models.CharField(max_length=120)
    completo = models.CharField(max_length=240, blank=True, editable=False)
    activo = models.BooleanField(default=True)
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['apellidos', 'nombres']
        verbose_name = 'Integrante'
        verbose_name_plural = 'Integrantes'

    def __str__(self):
        return self.completo or f'{self.apellidos} {self.nombres}'

    def save(self, *args, **kwargs):
        self.apellidos = self.apellidos.strip()
        self.nombres = self.nombres.strip()
        self.completo = f'{self.apellidos} {self.nombres}'.strip()
        super().save(*args, **kwargs)


# ---------------------------------------------------------------------------
# 3. Páginas publicadas
# ---------------------------------------------------------------------------

class PaginaPublicada(models.Model):
    """Un .html suelto o un sitio .zip publicado por un docente."""

    TIPO_CHOICES = [('html', 'Un solo archivo HTML'), ('sitio', 'Sitio completo (.zip)')]

    propietario = models.ForeignKey(Cuenta, on_delete=models.CASCADE, related_name='paginas')

    titulo = models.CharField(max_length=200, verbose_name='Nombre de la página')
    slug = models.SlugField(
        max_length=200, blank=True, verbose_name='Dirección',
        help_text='Lo que va después de tu nombre en el enlace. Se genera solo si lo dejas vacío.',
    )
    descripcion = models.TextField(blank=True, verbose_name='Descripción breve')

    tipo = models.CharField(max_length=6, choices=TIPO_CHOICES, default='html', editable=False)
    archivo = models.FileField(
        upload_to='salon/paginas/', blank=True, verbose_name='Archivo',
        help_text='Un .html suelto, o un .zip con el sitio completo.',
    )
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
    listar_en_perfil = models.BooleanField(
        default=True, verbose_name='¿Mostrarla en tu página de docente?',
        help_text='Si se desmarca, solo llega quien tenga el enlace.',
    )

    IDENT_CHOICES = [
        ('libre', 'El estudiante escribe su nombre'),
        ('opcional', 'Puede entrar por grupo o escribir su nombre'),
        ('grupo', 'Solo quien esté en un grupo'),
    ]
    identificacion = models.CharField(
        max_length=8, choices=IDENT_CHOICES, default='opcional',
        verbose_name='Cómo se identifica el estudiante',
    )
    grupos = models.ManyToManyField(
        Grupo, blank=True, related_name='paginas',
        verbose_name='Grupos que pueden entrar',
        help_text='Déjalo vacío para aceptar cualquier grupo tuyo.',
    )

    COMENTARIOS_CHOICES = [
        ('no', 'Sin comentarios'),
        ('abiertos', 'Cualquiera comenta y se ve enseguida'),
        ('moderados', 'Los comentarios esperan tu aprobación'),
    ]
    comentarios = models.CharField(
        max_length=10, choices=COMENTARIOS_CHOICES, default='no',
        verbose_name='Comentarios en la página',
    )

    compartir_classroom = models.BooleanField(
        default=True, verbose_name='Mostrar el botón de Google Classroom',
    )

    clave_panel = models.CharField(
        max_length=20, default=clave_aleatoria, verbose_name='Clave para ver resultados',
        help_text='La que le das a otros docentes para que descarguen los informes.',
    )
    captura_resultados = models.BooleanField(
        default=True, verbose_name='¿Guardar los resultados aquí?',
        help_text='Reescribe el ENDPOINT del archivo para que los resultados lleguen a Salón Digital.',
    )
    endpoint_reescrito = models.BooleanField(default=False, editable=False)

    # Moderación
    revisada = models.BooleanField(
        default=False,
        help_text='Una persona revisó el contenido. Las primeras de cada cuenta se revisan.',
    )
    alertas = models.TextField(blank=True, editable=False, help_text='Señales que encontró el escaneo automático.')

    creada_en = models.DateTimeField(auto_now_add=True)
    actualizada_en = models.DateTimeField(auto_now=True)
    visitas = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ('propietario', 'slug')
        ordering = ['-actualizada_en']
        verbose_name = 'Página publicada'
        verbose_name_plural = 'Páginas publicadas'

    def __str__(self):
        return self.titulo

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slug_unico(PaginaPublicada, self.titulo, self.pk, propietario=self.propietario)
        super().save(*args, **kwargs)

    @property
    def ruta(self):
        return f'/p/{self.propietario.slug}/{self.slug}/'

    @property
    def ruta_contenido(self):
        """Ruta del archivo de entrada dentro del almacenamiento."""
        if self.tipo == 'sitio' and self.base_sitio:
            return posixpath.join(self.base_sitio, self.indice or 'index.html')
        return self.archivo.name if self.archivo else ''

    @property
    def total_sesiones(self):
        return self.sesiones.count()

    @property
    def estado(self):
        ahora = timezone.now()
        if not self.propietario.activa:
            return 'suspendida'
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
# 4. Banco de preguntas
# ---------------------------------------------------------------------------

class Prueba(models.Model):
    propietario = models.ForeignKey(Cuenta, on_delete=models.CASCADE, related_name='pruebas')
    titulo = models.CharField(max_length=200, verbose_name='Título de la prueba')
    slug = models.SlugField(max_length=220, blank=True)
    area = models.CharField(max_length=3, choices=AREA_CHOICES, default='MAT')
    grado = models.PositiveSmallIntegerField(verbose_name='Grado')
    descripcion = models.TextField(blank=True, verbose_name='Instrucciones para el estudiante')

    codigo = models.CharField(max_length=20, verbose_name='Código de acceso')
    clave_panel = models.CharField(max_length=20, default=clave_aleatoria, verbose_name='Clave para ver resultados')

    sede = models.CharField(max_length=120, blank=True)
    activa = models.BooleanField(default=True, verbose_name='¿Está abierta?')
    permite_reintentos = models.BooleanField(default=True, verbose_name='¿Puede presentarla varias veces?')
    mostrar_retroalimentacion = models.BooleanField(
        default=True, verbose_name='¿Mostrar las respuestas correctas al terminar?',
    )

    creada_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [('propietario', 'codigo'), ('propietario', 'slug')]
        ordering = ['grado', 'area', 'titulo']
        verbose_name = 'Prueba'
        verbose_name_plural = 'Pruebas'

    def __str__(self):
        return f'{self.titulo} ({self.get_area_display()} · {self.grado}°)'

    def save(self, *args, **kwargs):
        self.codigo = (self.codigo or '').strip().upper()
        if not self.slug:
            self.slug = slug_unico(
                Prueba, f'{self.area}-{self.grado}-{self.titulo}', self.pk, propietario=self.propietario)
        super().save(*args, **kwargs)

    @property
    def total_preguntas(self):
        return self.preguntas.count()

    @property
    def ruta(self):
        return f'/salon_digital/prueba/{self.propietario.slug}/{self.slug}/'

    @property
    def disponible(self):
        return self.activa and self.propietario.activa


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

    imagen = models.ImageField(upload_to='salon/figuras/', blank=True, null=True)
    tabla = models.JSONField(
        blank=True, null=True,
        help_text='Formato {"h": ["encabezado", ...], "r": [["fila", ...], ...]}',
    )

    clave = models.CharField(max_length=1, verbose_name='Respuesta correcta')
    explicacion = models.TextField(blank=True, verbose_name='Explicación de la respuesta')
    analisis_error = models.TextField(blank=True, verbose_name='Análisis del error frecuente')
    pct_referencia = models.FloatField(null=True, blank=True, verbose_name='% de acierto de referencia')

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
    imagen = models.ImageField(upload_to='salon/opciones/', blank=True, null=True)

    class Meta:
        ordering = ['letra']
        unique_together = ('pregunta', 'letra')
        verbose_name = 'Opción'
        verbose_name_plural = 'Opciones'

    def __str__(self):
        return f'{self.letra}. {self.texto[:40]}'


# ---------------------------------------------------------------------------
# 5. Resultados
# ---------------------------------------------------------------------------

class Sesion(models.Model):
    """Una presentación terminada, venga de una página subida o del banco."""

    cuenta = models.ForeignKey(Cuenta, on_delete=models.CASCADE, related_name='sesiones')
    pagina = models.ForeignKey(
        PaginaPublicada, on_delete=models.CASCADE, null=True, blank=True, related_name='sesiones',
    )
    prueba = models.ForeignKey(
        Prueba, on_delete=models.CASCADE, null=True, blank=True, related_name='sesiones',
    )

    grupo = models.ForeignKey(
        Grupo, on_delete=models.SET_NULL, null=True, blank=True, related_name='sesiones')
    integrante = models.ForeignKey(
        Integrante, on_delete=models.SET_NULL, null=True, blank=True, related_name='sesiones')

    clave_prueba = models.CharField(max_length=30, blank=True)
    prueba_nombre = models.CharField(max_length=200, blank=True)

    apellidos = models.CharField(max_length=120, blank=True)
    nombres = models.CharField(max_length=120, blank=True)
    completo = models.CharField(max_length=240, blank=True, db_index=True)
    sede = models.CharField(max_length=120, blank=True)
    grupo_texto = models.CharField(max_length=30, blank=True, verbose_name='Grupo escrito a mano')

    fecha = models.DateTimeField(default=timezone.now)
    aciertos = models.PositiveSmallIntegerField(default=0)
    total = models.PositiveSmallIntegerField(default=0)
    porcentaje = models.FloatField(default=0)
    segundos = models.PositiveIntegerField(default=0)
    cambios = models.PositiveSmallIntegerField(default=0)
    vez = models.PositiveSmallIntegerField(default=1)

    payload = models.JSONField(null=True, blank=True, editable=False)
    recibido_en = models.DateTimeField(auto_now_add=True)
    ip = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        ordering = ['-fecha']
        verbose_name = 'Resultado'
        verbose_name_plural = 'Resultados'
        indexes = [models.Index(fields=['cuenta', '-recibido_en'])]

    def __str__(self):
        return f'{self.completo} · {self.prueba_nombre} · {self.porcentaje}%'

    @property
    def nombre_grupo(self):
        """El del grupo al que pertenece, o el que escribió a mano."""
        return self.grupo.nombre if self.grupo_id else self.grupo_texto

    @property
    def franja(self):
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

    numero = models.CharField(max_length=30, blank=True)
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


# ---------------------------------------------------------------------------
# 6. Comentarios
# ---------------------------------------------------------------------------

class Comentario(models.Model):
    """Lo que escriben los lectores al pie de una página publicada."""

    pagina = models.ForeignKey(PaginaPublicada, on_delete=models.CASCADE, related_name='lista_comentarios')
    responde_a = models.ForeignKey(
        'self', on_delete=models.CASCADE, null=True, blank=True, related_name='respuestas')

    nombre = models.CharField(max_length=120, verbose_name='Quién comenta')
    texto = models.TextField(verbose_name='Comentario')

    aprobado = models.BooleanField(default=True)
    del_autor = models.BooleanField(default=False, help_text='Lo escribió el dueño de la página.')

    creado_en = models.DateTimeField(auto_now_add=True)
    ip = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        ordering = ['creado_en']
        verbose_name = 'Comentario'
        verbose_name_plural = 'Comentarios'
        indexes = [models.Index(fields=['pagina', 'creado_en'])]

    def __str__(self):
        return f'{self.nombre}: {self.texto[:50]}'
