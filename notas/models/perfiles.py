# notas/models/perfiles.py
from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify
from django.conf import settings 
from django.urls import reverse 
from django.db.models import Max # <--- IMPORTADO PARA EL ORDEN

# ==============================================================================
# MODELO CENTRAL PARA MULTI-COLEGIO (VERSIÓN COMPLETA Y CORREGIDA)
# ==============================================================================

class Colegio(models.Model):
    """
    Modelo central que representa a cada institución educativa en la plataforma.
    """
    FONT_CHOICES = [
        ('Helvetica', 'Helvetica (Estándar)'),
        ('Arial', 'Arial'),
        ('Times New Roman', 'Times New Roman'),
        ('Courier', 'Courier (Máquina de escribir)'),
        ('Verdana', 'Verdana'),
        ('Georgia', 'Georgia'),
        ('Garamond', 'Garamond'),
        ('Tahoma', 'Tahoma'),
        ('Game On_PersonalUseOnly', 'Game On (Personalizada)'),
    ]

    LAYOUT_CHOICES = [
        ('topbar', 'Clásico: barra de navegación superior'),
        ('sidebar', 'Lateral: menú a la izquierda'),
        ('franja', 'Institucional: franja de contacto y menú centrado'),
        ('portada', 'Portada: imagen grande de bienvenida'),
        ('mosaico', 'Mosaico: bloques de colores en la página de inicio'),
        ('minimal', 'Minimalista: limpio y con mucho espacio'),
        ('revista', 'Revista: noticias destacadas como un periódico'),
    ]
    # Los diseños con página de inicio armada en el servidor (los nuevos).
    DISENOS_CON_INICIO = ('franja', 'portada', 'mosaico', 'minimal', 'revista')

    # --- Campos de Identificación ---
    nombre = models.CharField(max_length=255, unique=True, verbose_name="Nombre del Colegio")
    slug = models.SlugField(max_length=255, unique=True, blank=True, help_text="Identificador para la URL (se genera automáticamente)")
    domain = models.CharField(max_length=255, unique=True, null=True, blank=True, verbose_name="Dominio Personalizado", help_text="Ej: integradoapr.edu.co")
    admin_general = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="colegios_administrados", verbose_name="Administrador Principal")
    
    # --- Datos Oficiales ---
    nit = models.CharField(max_length=50, blank=True, verbose_name="NIT del Colegio")
    resolucion_aprobacion = models.CharField(max_length=255, blank=True, verbose_name="Resolución de Aprobación")
    nombre_rector = models.CharField(max_length=255, blank=True, null=True, verbose_name="Nombre Completo del Rector(a)")
    direccion = models.CharField(max_length=255, blank=True, verbose_name="Dirección Física")
    ciudad = models.CharField(max_length=100, blank=True, null=True, verbose_name="Ciudad")
    departamento = models.CharField(max_length=100, blank=True, null=True, verbose_name="Departamento")
    dane = models.CharField(max_length=20, blank=True, null=True, verbose_name="Código DANE")

    # --- Campos para Encabezado Personalizado en PDF ---
    linea_encabezado_1 = models.CharField(max_length=255, blank=True, null=True, verbose_name="Línea 1 del Encabezado")
    linea_encabezado_1_fuente = models.CharField(max_length=100, choices=FONT_CHOICES, default='Helvetica', verbose_name="Fuente L1")
    linea_encabezado_1_tamano = models.PositiveSmallIntegerField(default=11, verbose_name="Tamaño L1 (pt)")
    linea_encabezado_1_negrilla = models.BooleanField(default=True, verbose_name="Negrilla L1")
    linea_encabezado_1_cursiva = models.BooleanField(default=False, verbose_name="Cursiva L1")
    linea_encabezado_1_subrayado = models.BooleanField(default=False, verbose_name="Subrayado L1")

    linea_encabezado_2 = models.CharField(max_length=255, blank=True, null=True, verbose_name="Línea 2 del Encabezado")
    linea_encabezado_2_fuente = models.CharField(max_length=100, choices=FONT_CHOICES, default='Helvetica', verbose_name="Fuente L2")
    linea_encabezado_2_tamano = models.PositiveSmallIntegerField(default=8, verbose_name="Tamaño L2 (pt)")
    linea_encabezado_2_negrilla = models.BooleanField(default=False, verbose_name="Negrilla L2")
    linea_encabezado_2_cursiva = models.BooleanField(default=False, verbose_name="Cursiva L2")
    linea_encabezado_2_subrayado = models.BooleanField(default=False, verbose_name="Subrayado L2")

    linea_encabezado_3 = models.CharField(max_length=255, blank=True, null=True, verbose_name="Línea 3 del Encabezado")
    linea_encabezado_3_fuente = models.CharField(max_length=100, choices=FONT_CHOICES, default='Helvetica', verbose_name="Fuente L3")
    linea_encabezado_3_tamano = models.PositiveSmallIntegerField(default=8, verbose_name="Tamaño L3 (pt)")
    linea_encabezado_3_negrilla = models.BooleanField(default=False, verbose_name="Negrilla L3")
    linea_encabezado_3_cursiva = models.BooleanField(default=False, verbose_name="Cursiva L3")
    linea_encabezado_3_subrayado = models.BooleanField(default=False, verbose_name="Subrayado L3")

    linea_encabezado_4 = models.CharField(max_length=255, blank=True, null=True, verbose_name="Línea 4 del Encabezado")
    linea_encabezado_4_fuente = models.CharField(max_length=100, choices=FONT_CHOICES, default='Helvetica', verbose_name="Fuente L4")
    linea_encabezado_4_tamano = models.PositiveSmallIntegerField(default=8, verbose_name="Tamaño L4 (pt)")
    linea_encabezado_4_negrilla = models.BooleanField(default=False, verbose_name="Negrilla L4")
    linea_encabezado_4_cursiva = models.BooleanField(default=False, verbose_name="Cursiva L4")
    linea_encabezado_4_subrayado = models.BooleanField(default=False, verbose_name="Subrayado L4")

    linea_encabezado_5 = models.CharField(max_length=255, blank=True, null=True, verbose_name="Línea 5 del Encabezado")
    linea_encabezado_5_fuente = models.CharField(max_length=100, choices=FONT_CHOICES, default='Helvetica', verbose_name="Fuente L5")
    linea_encabezado_5_tamano = models.PositiveSmallIntegerField(default=8, verbose_name="Tamaño L5 (pt)")
    linea_encabezado_5_negrilla = models.BooleanField(default=False, verbose_name="Negrilla L5")
    linea_encabezado_5_cursiva = models.BooleanField(default=False, verbose_name="Cursiva L5")
    linea_encabezado_5_subrayado = models.BooleanField(default=False, verbose_name="Subrayado L5")
    
    encabezado_pdf_sin_bordes = models.BooleanField(default=False, verbose_name="Quitar bordes del encabezado en PDF", help_text="Marcar si el encabezado debe ocupar todo el ancho sin bordes (diseño especial).")

    # --- Identidad Visual ---
    logo_izquierdo = models.ImageField(upload_to='logos_colegios/', blank=True, null=True, verbose_name="Logo Izquierdo (Reportes)", help_text="Ej: Logo del Colegio")
    logo_derecho = models.ImageField(upload_to='logos_colegios/', blank=True, null=True, verbose_name="Logo Derecho (Reportes)", help_text="Ej: Logo de la Gobernación")
    favicon = models.ImageField(upload_to='logos_colegios/', blank=True, null=True, help_text="Icono para la pestaña del navegador (32x32px)")
    escudo = models.ImageField(upload_to='logos_colegios/', blank=True, null=True, verbose_name="Logo/Escudo Principal del Portal", help_text="Escudo para el portal y marca de agua en PDFs")
    firma_rector = models.ImageField(upload_to='firmas_rectores/', blank=True, null=True, verbose_name="Firma del Rector(a)", help_text="Imagen de la firma para los reportes") 
    alto_logos_pdf = models.PositiveSmallIntegerField(default=65, verbose_name="Altura Máxima de Logos en PDF (px)", help_text="Ajusta la altura de los logos para que se alineen con el texto del encabezado.")

    # --- Configuración de Boletines en PDF ---
    mostrar_foto_estudiante_boletin = models.BooleanField(default=False, verbose_name="Mostrar Foto del Estudiante en Boletines")
    mostrar_firma_rector_boletin = models.BooleanField(default=False, verbose_name="Mostrar Firma del Rector en Boletines")
    fuente_firma_rector = models.CharField(max_length=100, choices=FONT_CHOICES, default='Helvetica', verbose_name="Fuente de la Firma del Rector")
    tamano_firma_rector = models.PositiveSmallIntegerField(default=10, verbose_name="Tamaño de Letra del Rector (pt)")
    
    tamano_letra_boletin = models.PositiveSmallIntegerField(default=9, verbose_name="Tamaño de Letra General (px)", help_text="Ajusta el tamaño del texto general de los boletines (Recomendado: 8 o 9).")
    
    formatear_logros_automatico = models.BooleanField(
        default=True, 
        verbose_name="Formatear logros automáticamente",
        help_text="Si se desactiva, el logro se mostrará exactamente como lo escribió el docente. Si se activa, se convertirá a minúsculas y se le añadirá un prefijo de coherencia."
    )

    # --- Campos de Contenido del Portal ---
    lema = models.CharField(max_length=255, blank=True, null=True, verbose_name="Lema o Slogan")
    historia = models.TextField(blank=True, null=True, verbose_name="Historia / Quiénes Somos")
    mision = models.TextField(blank=True, null=True, verbose_name="Misión")
    vision = models.TextField(blank=True, null=True, verbose_name="Visión")
    modelo_pedagogico = models.TextField(blank=True, null=True, verbose_name="Modelo Pedagógico")

    # --- Paleta de Colores del Portal ---
    color_primario = models.CharField(max_length=7, default='#0D6EFD', verbose_name="Color Primario (Botones, Acentos)")
    color_secundario = models.CharField(max_length=7, default='#6C757D', verbose_name="Color Secundario (Textos sutiles)")
    color_texto_primario = models.CharField(max_length=7, default='#FFFFFF', help_text="Color del texto sobre el color primario (ej. en botones)")
    color_fondo = models.CharField(max_length=7, default='#F8F9FA', help_text="Color de fondo general de las páginas")
    color_topbar = models.CharField(max_length=7, default='#343A40', verbose_name="Color de Fondo Barra Superior/Lateral")
    color_topbar_texto = models.CharField(max_length=7, default='#FFFFFF', verbose_name="Color de Texto Barra Superior/Lateral")
    color_footer = models.CharField(max_length=7, default='#212529', verbose_name="Color de Fondo Pie de Página")
    color_footer_texto = models.CharField(max_length=7, default='#FFFFFF', verbose_name="Color de Texto Pie de Página")

    # --- Datos de Contacto ---
    telefono = models.CharField(max_length=50, blank=True, verbose_name="Teléfono Principal")
    email_contacto = models.EmailField(max_length=255, blank=True, verbose_name="Email de Contacto")
    whatsapp_numero = models.CharField(max_length=20, blank=True, verbose_name="Número de WhatsApp", help_text="Incluir código de país, ej: 573001234567")
    
    # --- Redes Sociales ---
    url_facebook = models.URLField(max_length=255, blank=True, verbose_name="URL de Facebook")
    url_instagram = models.URLField(max_length=255, blank=True, verbose_name="URL de Instagram")
    url_tiktok = models.URLField(max_length=255, blank=True, verbose_name="URL de TikTok")
    url_youtube = models.URLField(max_length=255, blank=True, verbose_name="URL de YouTube")

    # --- Configuración del Portal ---
    portal_publico_activo = models.BooleanField(default=True, verbose_name="¿Portal Público Activo?")
    layout_portal = models.CharField(max_length=10, choices=LAYOUT_CHOICES, default='topbar', verbose_name="Diseño del Portal")

    def __str__(self):
        return self.nombre

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.nombre)
        super().save(*args, **kwargs)
        
    def get_absolute_url(self):
        if not settings.DEBUG:
            main_domain = "mcolegio.com.co"
            return f"https://{self.slug}.{main_domain}"
        else:
            return f"http://{self.slug}.localhost:8000"

    class Meta:
        verbose_name = "Colegio"
        verbose_name_plural = "Colegios"
        ordering = ['nombre']

NIVEL_CHOICES = [
    ('PRE', 'Preescolar'),
    ('PRI', 'Primaria'),
    ('BAS', 'Básica Secundaria'),
    ('MED', 'Media')
]

# ------------------------------------------------------------------------------
# GRADOS
# El grado es lo que el sistema necesita para saber a dónde pasa un estudiante
# al año siguiente. El NOMBRE del curso sigue siendo libre («PRIMERO», «601»,
# «SEXTO A»): es la etiqueta que el colegio usa. El grado es la otra etiqueta,
# la que entiende la promoción. Los cursos viejos pueden no tener grado; a esos
# se les pregunta a dónde pasan cuando llega la promoción.
# ------------------------------------------------------------------------------
GRADOS = [
    # (número, nombre, nivel)
    (-2, 'Prejardín', 'PRE'),
    (-1, 'Jardín', 'PRE'),
    (0, 'Transición', 'PRE'),
    (1, 'Primero', 'PRI'),
    (2, 'Segundo', 'PRI'),
    (3, 'Tercero', 'PRI'),
    (4, 'Cuarto', 'PRI'),
    (5, 'Quinto', 'PRI'),
    (6, 'Sexto', 'BAS'),
    (7, 'Séptimo', 'BAS'),
    (8, 'Octavo', 'BAS'),
    (9, 'Noveno', 'BAS'),
    (10, 'Décimo', 'MED'),
    (11, 'Undécimo', 'MED'),
]
GRADO_MAXIMO = 11
NOMBRE_GRADO = {n: nombre for n, nombre, _ in GRADOS}
NIVEL_DE_GRADO = {n: nivel for n, _, nivel in GRADOS}
# Agrupados por nivel, para que el desplegable salga ordenado.
GRADO_CHOICES = [
    (etiqueta, [(n, nombre) for n, nombre, nivel in GRADOS if nivel == codigo])
    for codigo, etiqueta in NIVEL_CHOICES
]


def normalizar_subgrupo(subgrupo):
    """Cómo se guarda el subgrupo: tal cual lo escribió el colegio.

    Solo se limpian espacios y guiones de los bordes y se pasa a mayúscula
    («a» -> «A», « -1 » -> «1»). NO se le agregan ceros: el «1» de un colegio
    que nombra sus cursos 71 se queda «1».
    """
    return (subgrupo or '').strip().strip('-').strip().upper()


def clave_subgrupo(subgrupo):
    """Lo que se compara para saber si dos subgrupos son el mismo.

    «1», «01» y «001» son el mismo grupo; «A» y «a» también. Así 601 (subgrupo
    «01») encuentra a 71 (subgrupo «1») en la promoción, sin que el sistema le
    cambie el nombre a ninguno de los dos.
    """
    s = normalizar_subgrupo(subgrupo)
    return str(int(s)) if s.isdigit() else s


# Cómo arma cada colegio el nombre de un curso con grupos. Con letras no hay
# ceros que poner: 701 y 71 dan «7A»; 7-1 da «7-A».
FORMATOS_NOMBRE = [
    ('701', '701 · el grupo con dos cifras'),
    ('71', '71 · el grupo como se escribe'),
    ('7-1', '7-1 · con guion'),
]
FORMATO_POR_DEFECTO = '701'


def nombre_curso_sugerido(grado, subgrupo='', formato=FORMATO_POR_DEFECTO):
    """El nombre que se le pone al curso si el colegio lo deja vacío.

    Sin subgrupo es grado único y el nombre es el del grado: «SÉPTIMO».
    Con subgrupo depende del formato del colegio:
        701 -> «701», «7A»     71 -> «71», «7A»     7-1 -> «7-1», «7-A»
    En preescolar no hay número de grado: «TRANSICIÓN 01», «JARDÍN A».
    """
    sub = normalizar_subgrupo(subgrupo)
    if grado is None:
        return ''
    if not sub:
        return NOMBRE_GRADO.get(grado, str(grado)).upper()
    if sub.isdigit():
        sub = sub.zfill(2) if formato == '701' else str(int(sub))
    if grado <= 0:
        return f'{NOMBRE_GRADO.get(grado, "")} {sub}'.upper()
    separador = '-' if formato == '7-1' else ''
    return f'{grado}{separador}{sub}'


def formato_del_colegio(colegio):
    """El formato que ya usa el colegio, deducido de sus propios cursos.

    Se busca un curso con grado y subgrupo numérico y se mira con cuál formato
    coincide su nombre. Si no hay ninguno que lo diga, 701.
    """
    if colegio is None:
        return FORMATO_POR_DEFECTO
    cursos = (Curso.objects.filter(colegio=colegio, grado__gt=0)
              .exclude(subgrupo='').order_by('-id')[:30])
    for c in cursos:
        if not normalizar_subgrupo(c.subgrupo).isdigit():
            continue
        for formato, _ in FORMATOS_NOMBRE:
            if nombre_curso_sugerido(c.grado, c.subgrupo, formato) == c.nombre:
                return formato
    for c in cursos:          # solo hay grupos con letra: 7-A delata el guion
        if '-' in c.nombre:
            return '7-1'
    return FORMATO_POR_DEFECTO


class Sede(models.Model):
    """Una sede del colegio: la principal, la de primaria, la rural…

    Un colegio sin sedes registradas funciona como siempre. Cuando tiene, cada
    curso puede pertenecer a una, y eso deja filtrar boletines, sábana, alertas
    y estadísticas por sede. Las sedes activas salen en el portal.
    """
    JORNADAS = [
        ('MANANA', 'Mañana'),
        ('TARDE', 'Tarde'),
        ('NOCHE', 'Noche'),
        ('UNICA', 'Única'),
        ('FIN_SEMANA', 'Fin de semana'),
    ]
    NIVELES = [
        ('PRE', 'Preescolar'),
        ('PRI', 'Básica primaria'),
        ('SEC', 'Básica secundaria'),
        ('MED', 'Media'),
        ('ADU', 'Adultos'),
    ]

    colegio = models.ForeignKey(Colegio, on_delete=models.CASCADE, related_name='sedes')
    nombre = models.CharField(max_length=120, verbose_name='Nombre de la sede',
                              help_text='Ej.: Sede Principal, Sede Simón Bolívar.')
    es_principal = models.BooleanField(default=False, verbose_name='Es la sede principal')
    codigo_dane = models.CharField(max_length=20, blank=True, verbose_name='Código DANE de la sede')
    direccion = models.CharField(max_length=255, blank=True, verbose_name='Dirección')
    barrio = models.CharField(max_length=120, blank=True, verbose_name='Barrio / vereda')
    telefono = models.CharField(max_length=60, blank=True, verbose_name='Teléfono')
    correo = models.EmailField(blank=True, verbose_name='Correo')
    encargado = models.CharField(max_length=160, blank=True, verbose_name='Coordinador o encargado')
    # Varias opciones guardadas como texto «MANANA,TARDE»: son pocas, no se
    # consultan por separado y así no hace falta otra tabla.
    jornadas = models.CharField(max_length=80, blank=True, verbose_name='Jornadas')
    niveles = models.CharField(max_length=80, blank=True, verbose_name='Niveles que ofrece')
    descripcion = models.TextField(blank=True, verbose_name='Descripción para el portal')
    foto = models.ImageField(upload_to='sedes/', null=True, blank=True, verbose_name='Foto de la sede')
    enlace_mapa = models.URLField(max_length=500, blank=True, verbose_name='Enlace de Google Maps',
                                  help_text='Abra la sede en Google Maps, toque «Compartir» y pegue el enlace.')
    activa = models.BooleanField(default=True, verbose_name='Activa',
                                 help_text='Las inactivas no salen en el portal ni en los filtros.')
    orden = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ['-es_principal', 'orden', 'nombre']
        unique_together = ('colegio', 'nombre')
        verbose_name = 'Sede'
        verbose_name_plural = 'Sedes'

    def __str__(self):
        return self.nombre

    def lista_jornadas(self):
        nombres = dict(self.JORNADAS)
        return [nombres[c] for c in self.jornadas.split(',') if c in nombres]

    def lista_niveles(self):
        nombres = dict(self.NIVELES)
        return [nombres[c] for c in self.niveles.split(',') if c in nombres]

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Solo una principal por colegio.
        if self.es_principal:
            Sede.objects.filter(colegio=self.colegio, es_principal=True).exclude(pk=self.pk).update(es_principal=False)


class Curso(models.Model):
    colegio = models.ForeignKey(Colegio, on_delete=models.CASCADE, related_name="cursos")
    nombre = models.CharField(max_length=100, verbose_name="Nombre del Curso")
    nivel = models.CharField(max_length=4, choices=NIVEL_CHOICES, default='BAS', verbose_name="Nivel Escolar")
    # Vacío en los cursos que se crearon antes de que existiera: no se les
    # inventa un grado a partir del nombre. Los nuevos sí lo llevan siempre.
    grado = models.SmallIntegerField(
        choices=GRADO_CHOICES, null=True, blank=True, verbose_name="Grado",
        help_text="Con el grado, el sistema sabe a qué curso pasan sus estudiantes "
                  "al año siguiente.")
    subgrupo = models.CharField(
        max_length=10, blank=True, default='', verbose_name="Subgrupo (opcional)",
        help_text="Solo si el grado tiene varios grupos: 01, 02… o A, B… "
                  "Déjelo vacío si hay un solo curso de ese grado.")
    director_grado = models.ForeignKey('Docente', on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Director de Grado", related_name="cursos_dirigidos")
    sede = models.ForeignKey(Sede, on_delete=models.SET_NULL, null=True, blank=True,
                             related_name='cursos', verbose_name='Sede')
    
    orden = models.PositiveIntegerField(default=0, db_index=True)

    def __str__(self): 
        return self.nombre
        
    def save(self, *args, **kwargs):
        self.subgrupo = normalizar_subgrupo(self.subgrupo)
        if self.grado is not None:
            # El nivel sale del grado: así nunca queda un Sexto marcado como
            # Preescolar, que cambiaría la plantilla del boletín.
            self.nivel = NIVEL_DE_GRADO.get(self.grado, self.nivel)
            if not (self.nombre or '').strip():
                self.nombre = nombre_curso_sugerido(self.grado, self.subgrupo,
                                                    formato_del_colegio(self.colegio))
        self.nombre = self.nombre.upper()
        if self.pk is None: 
            max_orden = Curso.objects.filter(colegio=self.colegio).aggregate(Max('orden'))['orden__max']
            self.orden = (max_orden or 0) + 1
        super().save(*args, **kwargs)

    @property
    def tiene_grado(self):
        return self.grado is not None

    @property
    def nombre_grado(self):
        return NOMBRE_GRADO.get(self.grado, '') if self.grado is not None else ''

    @property
    def es_ultimo_grado(self):
        return self.grado == GRADO_MAXIMO

    def grado_siguiente(self):
        if self.grado is None or self.grado >= GRADO_MAXIMO:
            return None
        return self.grado + 1

    def curso_siguiente_sugerido(self):
        """A qué curso pasan sus estudiantes promovidos, si se puede saber solo.

        Con el mismo subgrupo si existe (601 -> 701), o el único curso del
        grado siguiente. Si hay varios y ninguno coincide, devuelve None y la
        pantalla de promoción lo pregunta: adivinar ahí repartiría mal a los
        estudiantes.
        """
        siguiente = self.grado_siguiente()
        if siguiente is None:
            return None
        candidatos = list(Curso.objects.filter(colegio=self.colegio, grado=siguiente))
        if not candidatos:
            return None
        # Con sedes, se queda en su sede si allá hay grado siguiente.
        if self.sede_id:
            de_su_sede = [c for c in candidatos if c.sede_id == self.sede_id]
            if de_su_sede:
                candidatos = de_su_sede
        if self.subgrupo:
            mio = clave_subgrupo(self.subgrupo)
            for c in candidatos:
                if clave_subgrupo(c.subgrupo) == mio:
                    return c
        if len(candidatos) == 1:
            return candidatos[0]
        return None
        
    class Meta:
        unique_together = ('nombre', 'colegio')
        verbose_name = "Curso"
        verbose_name_plural = "Cursos"
        ordering = ['orden'] 

class Docente(models.Model):
    colegio = models.ForeignKey(Colegio, on_delete=models.CASCADE, related_name="docentes")
    user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name="Usuario de Login")
    
    def __str__(self): 
        return self.user.get_full_name() or self.user.username
        
    def es_director_de_grupo(self, curso):
        return self.cursos_dirigidos.filter(pk=curso.pk).exists()

    class Meta:
        unique_together = ('user', 'colegio')
        verbose_name = "Docente"
        verbose_name_plural = "Docentes"
        ordering = ['user__last_name', 'user__first_name']

class Estudiante(models.Model):
    colegio = models.ForeignKey(Colegio, on_delete=models.CASCADE, related_name="estudiantes")
    user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name="Usuario de Login")
    curso = models.ForeignKey(Curso, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Curso Asignado")
    is_active = models.BooleanField(default=True, verbose_name="¿Estudiante Activo?")
    
    # NUEVO CAMPO AÑADIDO PARA INCLUSIÓN
    es_inclusion = models.BooleanField(default=False, verbose_name="Estudiante de Inclusión", help_text="Marcar si el estudiante pertenece al programa de inclusión. Se ignorará para rankings.")
    
    def __str__(self): 
        return self.user.get_full_name() or self.user.username
        
    class Meta:
        unique_together = ('user', 'colegio')
        verbose_name = "Estudiante"
        verbose_name_plural = "Estudiantes"
        ordering = ['user__last_name', 'user__first_name']

class FichaEstudiante(models.Model):
    TIPO_DOCUMENTO_CHOICES = [('CC', 'Cédula de Ciudadanía'), ('TI', 'Tarjeta de Identidad'), ('RC', 'Registro Civil'), ('CE', 'Cédula de Extranjería'), ('OT', 'Otro')]
    GRUPO_SANGUINEO_CHOICES = [('O+', 'O+'), ('O-', 'O-'), ('A+', 'A+'), ('A-', 'A-'), ('B+', 'B+'), ('B-', 'B-'), ('AB+', 'AB+'), ('AB-', 'AB-')]
    
    estudiante = models.OneToOneField(Estudiante, on_delete=models.CASCADE, primary_key=True, related_name="ficha")
    tipo_documento = models.CharField(max_length=2, choices=TIPO_DOCUMENTO_CHOICES, default='TI', verbose_name="Tipo de Documento")
    numero_documento = models.CharField(max_length=20, unique=True, null=True, blank=True, verbose_name="Número de Documento")
    lugar_nacimiento = models.CharField(max_length=100, blank=True, null=True)
    fecha_nacimiento = models.DateField(null=True, blank=True)
    eps = models.CharField(max_length=100, blank=True, null=True, verbose_name="EPS")
    grupo_sanguineo = models.CharField(max_length=3, choices=GRUPO_SANGUINEO_CHOICES, blank=True, null=True, verbose_name="Grupo Sanguíneo y RH")
    enfermedades_alergias = models.TextField(blank=True, null=True, verbose_name="Enfermedades o Alergias")
    foto = models.ImageField(upload_to='fotos_estudiantes/', null=True, blank=True, verbose_name="Foto del Estudiante")
    nombre_padre = models.CharField(max_length=200, blank=True, null=True)
    celular_padre = models.CharField(max_length=20, blank=True, null=True)
    nombre_madre = models.CharField(max_length=200, blank=True, null=True)
    celular_madre = models.CharField(max_length=20, blank=True, null=True)
    nombre_acudiente = models.CharField(max_length=200, blank=True, null=True)
    celular_acudiente = models.CharField(max_length=20, blank=True, null=True)
    email_acudiente = models.EmailField(blank=True, null=True)
    espera_en_porteria = models.BooleanField(default=False)
    colegio_anterior = models.CharField(max_length=200, blank=True, null=True)
    grado_anterior = models.CharField(max_length=20, blank=True, null=True)
    compromiso_padre = models.TextField(blank=True, null=True, verbose_name="Compromiso del Padre/Acudiente")
    compromiso_estudiante = models.TextField(blank=True, null=True, verbose_name="Compromiso del Estudiante")
    
    # CORRECCIÓN DE UNICIDAD EN EL MODELO: Forzamos la conversión de valores vacíos a NULL en base de datos
    def save(self, *args, **kwargs):
        if not self.numero_documento or str(self.numero_documento).strip() == '':
            self.numero_documento = None
        super().save(*args, **kwargs)

    def __str__(self): 
        return f"Ficha de {self.estudiante.user.get_full_name()}"

class FichaDocente(models.Model):
    docente = models.OneToOneField(Docente, on_delete=models.CASCADE, primary_key=True, related_name="ficha")
    numero_documento = models.CharField(max_length=20, unique=True, null=True, blank=True, verbose_name="Número de Documento")
    telefono = models.CharField(max_length=20, blank=True, null=True, verbose_name="Teléfono de Contacto")
    direccion = models.CharField(max_length=255, blank=True, null=True, verbose_name="Dirección de Residencia")
    titulo_profesional = models.CharField(max_length=200, blank=True, null=True, verbose_name="Título Profesional")
    foto = models.ImageField(upload_to='fotos_docentes/', null=True, blank=True, verbose_name="Foto del Docente")
    
    def save(self, *args, **kwargs):
        if not self.numero_documento or str(self.numero_documento).strip() == '':
            self.numero_documento = None
        super().save(*args, **kwargs)

    def __str__(self): 
        return f"Ficha de {self.docente.user.get_full_name()}"
        
    class Meta:
        verbose_name = "Ficha del Docente"
        verbose_name_plural = "Fichas de Docentes"


class AdministradorColegio(models.Model):
    """Rector, coordinador o secretaría: administra UN colegio.

    Puede todo lo que puede el superusuario, pero solo en este colegio (ver
    notas/permisos.py). Se puede ser además docente del mismo colegio.
    """
    CARGOS = [
        ('RECTOR', 'Rector(a)'),
        ('COORDINADOR', 'Coordinador(a)'),
        ('SECRETARIA', 'Secretaría académica'),
        ('ADMINISTRATIVO', 'Administrativo'),
        ('OTRO', 'Otro'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='administraciones')
    colegio = models.ForeignKey(Colegio, on_delete=models.CASCADE, related_name='administradores')
    cargo = models.CharField(max_length=15, choices=CARGOS, default='ADMINISTRATIVO')
    activo = models.BooleanField(default=True, help_text='Desmárquelo para quitarle el acceso sin borrar el registro.')
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'colegio')
        verbose_name = 'Administrador del colegio'
        verbose_name_plural = 'Administradores del colegio'
        ordering = ['colegio__nombre', 'user__last_name']

    def __str__(self):
        return f'{self.user.get_full_name() or self.user.username} · {self.get_cargo_display()} · {self.colegio}'


class HistorialMatricula(models.Model):
    """En qué curso estuvo un estudiante un año, y cómo terminó ese año.

    Se escribe al hacer la promoción de fin de año, ANTES de mover a nadie.
    Sirve para tres cosas:
      * que el boletín final de un año pasado siga saliendo con los
        estudiantes que de verdad estuvieron en ese curso, aunque hoy estén en
        otro;
      * saber de dónde viene cada estudiante;
      * poder deshacer la promoción si algo salió mal.
    """
    RESULTADOS = [
        ('PROMOVIDO', 'Promovido'),
        ('NO_PROMOVIDO', 'No promovido'),
        ('GRADUADO', 'Graduado'),
        ('RETIRADO', 'Retirado'),
    ]

    colegio = models.ForeignKey(Colegio, on_delete=models.CASCADE, related_name='historial_matriculas')
    estudiante = models.ForeignKey(Estudiante, on_delete=models.CASCADE, related_name='historial_matriculas')
    ano_lectivo = models.PositiveIntegerField(verbose_name='Año lectivo')
    curso = models.ForeignKey(Curso, on_delete=models.SET_NULL, null=True, blank=True,
                              related_name='historial_matriculas')
    # Copia del nombre y del grado: si el curso se renombra o se borra, el
    # historial sigue diciendo dónde estuvo.
    curso_nombre = models.CharField(max_length=100, blank=True)
    grado = models.SmallIntegerField(null=True, blank=True)
    resultado = models.CharField(max_length=14, choices=RESULTADOS)
    curso_destino = models.ForeignKey(Curso, on_delete=models.SET_NULL, null=True, blank=True,
                                      related_name='+')
    # Cómo estaba antes de la promoción, para poder deshacerla tal cual.
    estaba_activo = models.BooleanField(default=True)
    registrado = models.DateTimeField(auto_now_add=True)
    registrado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                       related_name='+')

    class Meta:
        unique_together = ('estudiante', 'ano_lectivo')
        ordering = ['-ano_lectivo', 'curso_nombre']
        verbose_name = 'Historial de matrícula'
        verbose_name_plural = 'Historial de matrículas'

    def __str__(self):
        return f'{self.estudiante} · {self.ano_lectivo} · {self.curso_nombre} · {self.get_resultado_display()}'
