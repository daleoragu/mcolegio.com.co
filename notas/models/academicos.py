# notas/models/academicos.py
from django.db import models
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal
import datetime

from django.contrib.auth.models import User
from .perfiles import Docente, Estudiante, Curso, Colegio

class AreaConocimiento(models.Model):
    colegio = models.ForeignKey(Colegio, on_delete=models.CASCADE, related_name="areas_conocimiento", null=True)
    nombre = models.CharField(max_length=100, verbose_name="Nombre del Área")
    materias = models.ManyToManyField('Materia', through='PonderacionAreaMateria', related_name='areas_ponderadas')
    def __str__(self): return self.nombre
    def save(self, *args, **kwargs):
        self.nombre = self.nombre.upper()
        super().save(*args, **kwargs)
    class Meta:
        unique_together = ('nombre', 'colegio')
        verbose_name = "Área de Conocimiento"; verbose_name_plural = "Áreas de Conocimiento"; ordering = ['nombre']

# Componentes de evaluación: los tres de siempre conservan su código (las notas
# ya guardadas los usan) y los que el colegio agregue son C4, C5… Cómo se llama
# cada uno lo decide el colegio (ComponenteEvaluacion).
CODIGOS_LEGADO = ('SER', 'SABER', 'HACER')
CODIGOS_EXTRA = tuple(f'C{n}' for n in range(4, 13))
CODIGOS_COMPONENTE = CODIGOS_LEGADO + CODIGOS_EXTRA
CHOICES_COMPONENTE = [(c, c) for c in CODIGOS_COMPONENTE]


class Materia(models.Model):
    colegio = models.ForeignKey(Colegio, on_delete=models.CASCADE, related_name="materias", null=True)
    nombre = models.CharField(max_length=100, verbose_name="Nombre de la Materia")
    abreviatura = models.CharField(max_length=10, blank=True, null=True, verbose_name="Abreviatura")
    usar_ponderacion_equitativa = models.BooleanField(default=True, verbose_name="Usar ponderación equitativa por defecto")
    porcentaje_ser = models.PositiveIntegerField(default=30, validators=[MinValueValidator(0), MaxValueValidator(100)], verbose_name="Porcentaje SER por defecto")
    porcentaje_saber = models.PositiveIntegerField(default=40, validators=[MinValueValidator(0), MaxValueValidator(100)], verbose_name="Porcentaje SABER por defecto")
    porcentaje_hacer = models.PositiveIntegerField(default=30, validators=[MinValueValidator(0), MaxValueValidator(100)], verbose_name="Porcentaje HACER por defecto")
    
    # --- NUEVOS CAMPOS PARA FLEXIBILIDAD EN MATERIAS ESPECIALES ---
    promedia_en_boletin = models.BooleanField(default=True, verbose_name="¿Promedia en el Boletín?", help_text="Si se desmarca, no sumará al promedio general.")
    etiqueta_ser = models.CharField(max_length=30, default="SER", verbose_name="Nombre Componente 1 (Ser)")
    etiqueta_saber = models.CharField(max_length=30, default="SABER", verbose_name="Nombre Componente 2 (Saber)")
    etiqueta_hacer = models.CharField(max_length=30, default="HACER", verbose_name="Nombre Componente 3 (Hacer)")
    # {código: porcentaje} de cada componente del colegio. Los tres de siempre
    # también quedan en porcentaje_ser/saber/hacer (ver notas/componentes.py).
    pesos_componentes = models.JSONField(default=dict, blank=True, verbose_name="Porcentajes por componente")

    def __str__(self): return self.nombre
    def clean(self):
        super().clean()
        if not self.usar_ponderacion_equitativa and self.colegio_id:
            from ..componentes import suma_pesos
            total = suma_pesos(self)
            if total != 100:
                raise ValidationError(f"La suma de los porcentajes manuales debe ser 100 (va en {total}).")
    class Meta:
        unique_together = ('nombre', 'colegio')
        verbose_name = "Materia"; verbose_name_plural = "Materias"; ordering = ['nombre']

class PeriodoAcademico(models.Model):
    colegio = models.ForeignKey(Colegio, on_delete=models.CASCADE, related_name="periodos_academicos", null=True)
    nombre = models.CharField(max_length=20, choices=[('PRIMERO', 'Primer Periodo'), ('SEGUNDO', 'Segundo Periodo'), ('TERCERO', 'Tercer Periodo'), ('CUARTO', 'Cuarto Periodo')])
    ano_lectivo = models.PositiveIntegerField(default=datetime.date.today().year)
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()
    peso_porcentual = models.DecimalField(
        max_digits=5, decimal_places=2, default=Decimal('25.00'),
        validators=[MinValueValidator(Decimal('0.00')), MaxValueValidator(Decimal('100.00'))],
        verbose_name="Peso del periodo (%)",
        help_text="Solo se usa si el colegio activó la ponderación por periodos."
    )
    esta_activo = models.BooleanField(default=True, verbose_name="Ingreso de Notas Activo")
    reporte_parcial_activo = models.BooleanField(default=True, verbose_name="Reporte Parcial Activo")
    nivelaciones_activas = models.BooleanField(default=False, verbose_name="Nivelaciones Activas")
    class Meta:
        unique_together = ('nombre', 'ano_lectivo', 'colegio')
        verbose_name = "Periodo Académico"; verbose_name_plural = "Periodos Académicos"; ordering = ['-ano_lectivo', 'fecha_inicio']
    def __str__(self): return f"{self.get_nombre_display()} - {self.ano_lectivo}"
    def clean(self):
        if self.fecha_inicio >= self.fecha_fin: raise ValidationError("La fecha de inicio debe ser anterior a la fecha de fin.")

class AsignacionDocente(models.Model):
    colegio = models.ForeignKey(Colegio, on_delete=models.CASCADE, related_name="asignaciones_docentes", null=True)
    docente = models.ForeignKey(Docente, on_delete=models.CASCADE, verbose_name="Docente")
    materia = models.ForeignKey(Materia, on_delete=models.CASCADE, verbose_name="Materia")
    curso = models.ForeignKey(Curso, on_delete=models.CASCADE, verbose_name="Curso")
    intensidad_horaria_semanal = models.PositiveSmallIntegerField(default=0, verbose_name="Intensidad Horaria (IH)")
    usar_ponderacion_equitativa = models.BooleanField(default=True, verbose_name="Usar ponderación equitativa")
    porcentaje_ser = models.PositiveIntegerField(default=30, validators=[MinValueValidator(0), MaxValueValidator(100)])
    porcentaje_saber = models.PositiveIntegerField(default=40, validators=[MinValueValidator(0), MaxValueValidator(100)])
    porcentaje_hacer = models.PositiveIntegerField(default=30, validators=[MinValueValidator(0), MaxValueValidator(100)])
    pesos_componentes = models.JSONField(default=dict, blank=True, verbose_name="Porcentajes por componente")
    class Meta:
        unique_together = ('docente', 'materia', 'curso', 'colegio')
        verbose_name = "Asignación Académica"; verbose_name_plural = "Asignaciones Académicas"; ordering = ['curso__nombre', 'materia__nombre']
    def __str__(self): return f"{self.docente} - {self.materia} en {self.curso}"
    def clean(self):
        super().clean()
        if not self.usar_ponderacion_equitativa:
            from ..componentes import suma_pesos
            total_porcentaje = suma_pesos(self)
            if total_porcentaje != 100 and total_porcentaje != 0:
                raise ValidationError(f"La suma de porcentajes debe ser 100 (o 0 si no promedia). Actualmente es {total_porcentaje}.")
    
    # Se conservan por compatibilidad: el porcentaje real lo calcula notas/componentes.py
    # para todos los componentes del colegio (pueden ser 1, 3, 5…).
    @property
    def ser_calc(self):
        from ..componentes import pesos
        return pesos(self).get('SER', Decimal('0'))

    @property
    def saber_calc(self):
        from ..componentes import pesos
        return pesos(self).get('SABER', Decimal('0'))

    @property
    def hacer_calc(self):
        from ..componentes import pesos
        return pesos(self).get('HACER', Decimal('0'))

class Calificacion(models.Model):
    colegio = models.ForeignKey(Colegio, on_delete=models.CASCADE, related_name="calificaciones", null=True)
    estudiante = models.ForeignKey(Estudiante, on_delete=models.CASCADE)
    materia = models.ForeignKey(Materia, on_delete=models.CASCADE)
    periodo = models.ForeignKey(PeriodoAcademico, on_delete=models.CASCADE)
    docente = models.ForeignKey(Docente, on_delete=models.SET_NULL, null=True)
    TIPO_NOTA_CHOICES = ([('SER', 'Promedio Ser'), ('SABER', 'Promedio Saber'), ('HACER', 'Promedio Hacer')]
                         + [(c, f'Promedio componente {c[1:]}') for c in CODIGOS_EXTRA]
                         + [('PROM_PERIODO', 'Promedio del Periodo'), ('NIVELACION', 'Nota de Nivelación')])
    tipo_nota = models.CharField(max_length=12, choices=TIPO_NOTA_CHOICES)
    valor_nota = models.DecimalField(max_digits=5, decimal_places=2, validators=[MinValueValidator(Decimal('0')), MaxValueValidator(Decimal('100'))])  # el rango real lo pone la escala del colegio
    es_recuperada = models.BooleanField(default=False, help_text="Indica si esta calificación de periodo fue recuperada con una nivelación.")
    
    # NUEVO CAMPO AÑADIDO PARA INCLUSIÓN
    observacion_inclusion = models.TextField(blank=True, null=True, verbose_name="Indicador de Inclusión", help_text="Indicador personalizado para estudiantes de inclusión")
    # Observación libre del docente sobre el estudiante en la asignatura (opcional).
    # Se guarda en la definitiva del periodo (PROM_PERIODO) y sale en el boletín.
    observacion = models.TextField(blank=True, default='', verbose_name="Observación de la asignatura")
    
    class Meta:
        unique_together = ('estudiante', 'materia', 'periodo', 'tipo_nota', 'colegio')
        verbose_name = "Calificación (Promedio)"; verbose_name_plural = "Calificaciones (Promedios)"
    def __str__(self): return f"{self.estudiante} | {self.materia} | {self.periodo.nombre} - {self.get_tipo_nota_display()}: {self.valor_nota}"

class NotaDetallada(models.Model):
    colegio = models.ForeignKey(Colegio, on_delete=models.CASCADE, related_name="notas_detalladas", null=True)
    calificacion_promedio = models.ForeignKey(Calificacion, on_delete=models.CASCADE, related_name='notas_detalladas')
    descripcion = models.CharField(max_length=100, help_text="Descripción de la nota (ej: 'Examen 1', 'Taller en clase')")
    valor_nota = models.DecimalField(max_digits=5, decimal_places=2, validators=[MinValueValidator(Decimal('0')), MaxValueValidator(Decimal('100'))])  # el rango real lo pone la escala del colegio
    class Meta:
        verbose_name = "Nota Detallada"; verbose_name_plural = "Notas Detalladas"
    def __str__(self): return f"{self.descripcion}: {self.valor_nota}"

class IndicadorLogroPeriodo(models.Model):
    colegio = models.ForeignKey(Colegio, on_delete=models.CASCADE, related_name="indicadores_logro", null=True)
    asignacion = models.ForeignKey(AsignacionDocente, on_delete=models.CASCADE)
    periodo = models.ForeignKey(PeriodoAcademico, on_delete=models.CASCADE)
    descripcion = models.TextField()
    def __str__(self): return f"Indicador para {self.asignacion.materia} en {self.asignacion.curso}"

class ReporteParcial(models.Model):
    colegio = models.ForeignKey(Colegio, on_delete=models.CASCADE, related_name="reportes_parciales", null=True)
    estudiante = models.ForeignKey(Estudiante, on_delete=models.CASCADE)
    asignacion = models.ForeignKey(AsignacionDocente, on_delete=models.CASCADE)
    periodo = models.ForeignKey(PeriodoAcademico, on_delete=models.CASCADE)
    presenta_dificultades = models.BooleanField(default=False)
    class Meta:
        unique_together = ('estudiante', 'asignacion', 'periodo', 'colegio')
        verbose_name = "Reporte Parcial"; verbose_name_plural = "Reportes Parciales"

class Observacion(models.Model):
    colegio = models.ForeignKey(Colegio, on_delete=models.CASCADE, related_name="observaciones", null=True)
    estudiante = models.ForeignKey(Estudiante, on_delete=models.CASCADE)
    docente_reporta = models.ForeignKey(Docente, on_delete=models.SET_NULL, null=True)
    asignacion = models.ForeignKey(AsignacionDocente, on_delete=models.SET_NULL, null=True, blank=True)
    periodo = models.ForeignKey(PeriodoAcademico, on_delete=models.CASCADE, null=True, blank=True)
    TIPO_OBSERVACION_CHOICES = [('ACADEMICA', 'Académica'), ('CONVIVENCIA', 'Convivencia'), ('AUTOMATICA', 'Automática')]
    tipo_observacion = models.CharField(max_length=15, choices=TIPO_OBSERVACION_CHOICES, default='ACADEMICA')
    descripcion = models.TextField()
    fecha_reporte = models.DateTimeField(auto_now_add=True)
    class Meta:
        ordering = ['-fecha_reporte']; verbose_name = "Observación del Estudiante"; verbose_name_plural = "Observaciones del Estudiante"

class PlanDeMejoramiento(models.Model):
    colegio = models.ForeignKey(Colegio, on_delete=models.CASCADE, related_name="planes_mejoramiento", null=True)
    estudiante = models.ForeignKey(Estudiante, on_delete=models.CASCADE)
    asignacion = models.ForeignKey(AsignacionDocente, on_delete=models.CASCADE)
    periodo_recuperado = models.ForeignKey(PeriodoAcademico, on_delete=models.CASCADE)
    descripcion_plan = models.TextField()
    nota_recuperacion = models.DecimalField(max_digits=3, decimal_places=1, null=True, blank=True)
    finalizado_por_admin = models.BooleanField(default=False, help_text="Marcar si la nota ya fue actualizada por el administrador.")
    class Meta:
        unique_together = ('estudiante', 'asignacion', 'periodo_recuperado', 'colegio')
        verbose_name = "Plan de Mejoramiento"; verbose_name_plural = "Planes de Mejoramiento"

class Asistencia(models.Model):
    colegio = models.ForeignKey(Colegio, on_delete=models.CASCADE, related_name="asistencias", null=True)
    ESTADO_CHOICES = [('P', 'Presente'), ('A', 'Ausente'), ('T', 'Tarde')]
    estudiante = models.ForeignKey(Estudiante, on_delete=models.CASCADE)
    asignacion = models.ForeignKey(AsignacionDocente, on_delete=models.CASCADE)
    fecha = models.DateField(default=datetime.date.today)
    estado = models.CharField(max_length=1, choices=ESTADO_CHOICES, default='P')
    justificada = models.BooleanField(default=False)
    class Meta:
        unique_together = ('estudiante', 'asignacion', 'fecha', 'colegio')
        verbose_name = "Registro de Asistencia"; verbose_name_plural = "Registros de Asistencia"; ordering = ['-fecha', 'estudiante__user__last_name']

class InasistenciasManualesPeriodo(models.Model):
    colegio = models.ForeignKey(Colegio, on_delete=models.CASCADE, related_name="inasistencias_manuales", null=True)
    estudiante = models.ForeignKey(Estudiante, on_delete=models.CASCADE)
    asignacion = models.ForeignKey(AsignacionDocente, on_delete=models.CASCADE)
    periodo = models.ForeignKey(PeriodoAcademico, on_delete=models.CASCADE)
    cantidad = models.PositiveIntegerField(default=0)
    class Meta:
        unique_together = ('estudiante', 'asignacion', 'periodo', 'colegio')
        verbose_name = "Inasistencia Manual por Periodo"; verbose_name_plural = "Inasistencias Manuales por Periodo"

class ConfiguracionSistema(models.Model):
    colegio = models.OneToOneField(Colegio, on_delete=models.CASCADE, related_name="configuracion", null=True)
    max_areas_reprobadas = models.PositiveSmallIntegerField(default=2, verbose_name="Máximo de áreas reprobadas para ser promovido")
    
    def __str__(self):
        if self.colegio:
            return f"Configuración de Promoción para {self.colegio.nombre}"
        return "Configuración de Promoción (sin colegio)"
    class Meta:
        verbose_name = "Configuración del Sistema"; verbose_name_plural = "Configuraciones del Sistema"

class PublicacionBoletin(models.Model):
    colegio = models.ForeignKey(Colegio, on_delete=models.CASCADE, related_name="publicaciones_boletines", null=True)
    periodo = models.OneToOneField(PeriodoAcademico, on_delete=models.CASCADE, verbose_name="Periodo Publicado")
    publicado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name="Publicado por")
    fecha_publicacion = models.DateTimeField(auto_now_add=True)
    esta_visible = models.BooleanField(default=False, verbose_name="¿Visible para Estudiantes?")
    def __str__(self): return f"Publicación del {self.periodo} - Visible: {self.esta_visible}"
    class Meta:
        verbose_name = "Publicación de Boletín de Periodo"; verbose_name_plural = "Publicaciones de Boletines de Periodo"; ordering = ['-periodo__ano_lectivo', '-periodo__fecha_inicio']

class PublicacionBoletinFinal(models.Model):
    colegio = models.ForeignKey(Colegio, on_delete=models.CASCADE, related_name="publicaciones_finales", null=True)
    ano_lectivo = models.PositiveIntegerField(unique=True, verbose_name="Año Lectivo Publicado")
    publicado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name="Publicado por")
    fecha_publicacion = models.DateTimeField(auto_now_add=True)
    esta_visible = models.BooleanField(default=False, verbose_name="¿Visible para Estudiantes?")
    def __str__(self): return f"Publicación del Boletín Final {self.ano_lectivo} - Visible: {self.esta_visible}"
    class Meta:
        verbose_name = "Publicación de Boletín Final"; verbose_name_plural = "Publicaciones de Boletines Finales"; ordering = ['-ano_lectivo']

class ConfiguracionCalificaciones(models.Model):
    colegio = models.OneToOneField(Colegio, on_delete=models.CASCADE, related_name="configuracion_calificaciones", null=True)
    docente_puede_modificar = models.BooleanField(default=False, verbose_name="Permitir que los docentes modifiquen los porcentajes de calificación")

    # --- Ponderación de periodos ---
    ponderar_periodos = models.BooleanField(
        default=False,
        verbose_name="Cada periodo vale un porcentaje distinto",
        help_text="Si se deja apagado, todos los periodos pesan igual, como hasta ahora."
    )
    exigir_periodos_completos = models.BooleanField(
        default=False,
        verbose_name="No calcular la definitiva si falta algún periodo",
        help_text="En vez de promediar lo que haya, avisa cuáles periodos faltan. "
                  "Se activa solo cuando se ponderan los periodos."
    )

    # --- Nombres de las tres columnas del boletín ---
    etiqueta_ser = models.CharField(max_length=30, default="SER", verbose_name="Nombre de la columna 1")
    etiqueta_saber = models.CharField(max_length=30, default="SABER", verbose_name="Nombre de la columna 2")
    etiqueta_hacer = models.CharField(max_length=30, default="HACER", verbose_name="Nombre de la columna 3")
    # Para las columnas angostas del boletín (vacío = el nombre completo).
    abreviatura_ser = models.CharField(max_length=10, blank=True, default='', verbose_name="Abreviatura de la columna 1")
    abreviatura_saber = models.CharField(max_length=10, blank=True, default='', verbose_name="Abreviatura de la columna 2")
    abreviatura_hacer = models.CharField(max_length=10, blank=True, default='', verbose_name="Abreviatura de la columna 3")

    # --- Planilla de notas ---
    notas_por_componente = models.PositiveSmallIntegerField(
        default=5, validators=[MinValueValidator(1), MaxValueValidator(15)],
        verbose_name="Notas por componente cuando el docente no elige",
        help_text="Cuántas columnas trae cada componente (SER, SABER, HACER) en la planilla "
                  "en línea y en el Excel, si el docente no configuró las suyas."
    )

    # --- Presentación ---
    colapsar_area_unica = models.BooleanField(
        default=True,
        verbose_name="Unir área y asignatura cuando el área tiene una sola",
        help_text="Evita que la sábana y el boletín repitan la misma nota en dos filas."
    )

    @property
    def pide_todos_los_periodos(self):
        """La ponderación obliga a tener todos los periodos para que el cálculo tenga sentido."""
        return self.exigir_periodos_completos or self.ponderar_periodos

    
    def __str__(self):
        if self.colegio:
            return f"Configuración de Calificaciones para {self.colegio.nombre}"
        return "Configuración de Calificaciones (sin colegio asignado)"
    class Meta:
        verbose_name = "Configuración de Permisos de Calificación"; verbose_name_plural = "Configuración de Permisos de Calificación"

class PlanNotas(models.Model):
    """Las columnas de notas que un docente decidió para un componente.

    Una fila por asignación, periodo y componente: «SABER de Matemáticas 601
    en el primer periodo tiene Taller 1, Quiz y Evaluación». Lo usan la
    planilla en línea y el Excel, así las dos muestran las mismas columnas con
    los mismos nombres. Las notas siguen guardándose en NotaDetallada; su
    descripción es la que las amarra a su columna.
    """
    COMPONENTES = CHOICES_COMPONENTE

    colegio = models.ForeignKey(Colegio, on_delete=models.CASCADE, related_name="planes_notas", null=True)
    asignacion = models.ForeignKey('AsignacionDocente', on_delete=models.CASCADE, related_name='planes_notas')
    periodo = models.ForeignKey('PeriodoAcademico', on_delete=models.CASCADE, related_name='planes_notas')
    componente = models.CharField(max_length=6, choices=COMPONENTES)
    columnas = models.JSONField(default=list, blank=True,
                                help_text="Nombres de las notas, en orden: [\"Taller 1\", \"Quiz\"…]")
    actualizado = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('asignacion', 'periodo', 'componente')
        verbose_name = "Plan de notas"; verbose_name_plural = "Planes de notas"

    def __str__(self):
        return f"{self.asignacion} · {self.periodo} · {self.componente}: {len(self.columnas or [])} nota(s)"


class PonderacionAreaMateria(models.Model):
    colegio = models.ForeignKey(Colegio, on_delete=models.CASCADE, related_name="ponderaciones", null=True)
    area = models.ForeignKey('AreaConocimiento', on_delete=models.CASCADE)
    materia = models.ForeignKey('Materia', on_delete=models.CASCADE)
    peso_porcentual = models.DecimalField(max_digits=5, decimal_places=2, validators=[MinValueValidator(Decimal('0.00')), MaxValueValidator(Decimal('100.00'))], verbose_name="Peso Porcentual (%)")
    class Meta:
        unique_together = ('area', 'materia', 'colegio')
        verbose_name = "Ponderación de Materia en Área"; verbose_name_plural = "Ponderaciones de Materias en Áreas"
    def __str__(self): return f"{self.materia.nombre} en {self.area.nombre} ({self.peso_porcentual}%)"

class EscalaValoracion(models.Model):
    colegio = models.ForeignKey(Colegio, on_delete=models.CASCADE, related_name="escala_valoracion")
    nombre_desempeno = models.CharField(max_length=50, verbose_name="Nombre del Desempeño (e.g., Bajo, Superior)")
    valor_minimo = models.DecimalField(max_digits=4, decimal_places=1, verbose_name="Valor Mínimo")
    valor_maximo = models.DecimalField(max_digits=4, decimal_places=1, verbose_name="Valor Máximo")
    mensaje_boletin = models.TextField(blank=True, help_text="Mensaje opcional para mostrar en el boletín para este rango de notas.")

    def __str__(self):
        return f"{self.nombre_desempeno} ({self.valor_minimo} - {self.valor_maximo}) para {self.colegio.nombre}"

    def clean(self):
        if self.valor_minimo >= self.valor_maximo:
            raise ValidationError("El valor mínimo debe ser menor que el valor máximo.")
        
        superposiciones = EscalaValoracion.objects.filter(
            colegio=self.colegio,
            valor_maximo__gte=self.valor_minimo,
            valor_minimo__lte=self.valor_maximo
        ).exclude(pk=self.pk)
        
        if superposiciones.exists():
            raise ValidationError(f"El rango de notas se superpone con otra escala ya definida: '{superposiciones.first()}'.")

    def save(self, *args, **kwargs):
        self.nombre_desempeno = self.nombre_desempeno.upper()
        super().save(*args, **kwargs)

    class Meta:
        unique_together = ('colegio', 'nombre_desempeno')
        ordering = ['valor_minimo']
        verbose_name = "Escala de Valoración"
        verbose_name_plural = "Escalas de Valoración"


class ComponenteEvaluacion(models.Model):
    """Un componente de evaluación del colegio: «Saber», «Cognitivo», «Nota»…

    El colegio decide cuántos tiene (de 1 en adelante), cómo se llaman, su
    abreviatura para el boletín y en qué orden salen. El código no cambia
    nunca: es con lo que se guardan las notas (Calificacion.tipo_nota).
    """
    colegio = models.ForeignKey(Colegio, on_delete=models.CASCADE, related_name='componentes_evaluacion')
    codigo = models.CharField(max_length=6, choices=CHOICES_COMPONENTE)
    nombre = models.CharField(max_length=30)
    abreviatura = models.CharField(max_length=10, blank=True, default='')
    orden = models.PositiveSmallIntegerField(default=1)

    class Meta:
        unique_together = ('colegio', 'codigo')
        ordering = ['orden', 'id']
        verbose_name = 'Componente de evaluación'
        verbose_name_plural = 'Componentes de evaluación'

    def __str__(self):
        return f'{self.nombre} ({self.codigo})'

    @property
    def encabezado(self):
        return (self.abreviatura or self.nombre).upper()
