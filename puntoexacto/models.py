# -*- coding: utf-8 -*-
"""PuntoExacto · modelos.

Un examen de selección múltiple que se imprime, se responde en papel y se
califica. Vive al lado de la plataforma de notas pero no depende de ella para
existir: el campo `cuenta` deja la puerta abierta a Salón Digital, donde el
docente trabaja por su cuenta y no hay colegio.

Lo que NO está aquí a propósito: cursos, estudiantes y etiquetas de contenido.
Eso ya existe en la plataforma y se reusa en vez de duplicarse.
"""
from decimal import Decimal

from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models

from notas.models.academicos import AsignacionDocente, PeriodoAcademico
from notas.models.academicos import Materia
from notas.models.perfiles import Colegio, Curso, Docente, Estudiante


METODOS = [
    ('manual', 'Manual: el docente pone los puntos de cada pregunta y la nota es su suma'),
    ('con_piso', 'Con piso: 0 aciertos saca la nota mínima'),
    ('proporcional', 'Proporcional: 0 aciertos saca 0 (se ajusta a la mínima)'),
    ('descuento', 'Por descuento: arranca en la máxima y resta'),
]

LETRAS = 'ABCDEFGHIJ'

# A qué columna de la planilla va la nota. Son los tres componentes que maneja
# el ingreso de notas; cada colegio puede llamarlos distinto, pero por dentro
# se guardan así.
COMPONENTES = [
    ('SER', 'SER'),
    ('SABER', 'SABER'),
    ('HACER', 'HACER'),
]


class Examen(models.Model):
    """Un examen aplicado a uno o varios cursos.

    A diferencia de ZipGrade, donde un examen pertenece a un solo curso y hay
    que crearlo de nuevo para cada uno, aquí el mismo examen se aplica a varios
    y los resultados quedan separados por curso. Eso permite comparar cómo le
    fue a 801 frente a 802 en la misma prueba.
    """
    colegio = models.ForeignKey(Colegio, on_delete=models.CASCADE,
                                related_name='examenes_puntoexacto', null=True, blank=True)
    docente = models.ForeignKey(Docente, on_delete=models.CASCADE,
                                related_name='examenes_puntoexacto', null=True, blank=True)
    # Reservado para Salón Digital, donde no hay colegio ni docente institucional.
    cuenta = models.ForeignKey('salon_digital.Cuenta', on_delete=models.CASCADE,
                               related_name='examenes_puntoexacto', null=True, blank=True)

    titulo = models.CharField(max_length=160, verbose_name='Nombre del examen')
    asignacion = models.ForeignKey(AsignacionDocente, on_delete=models.SET_NULL,
                                   null=True, blank=True, verbose_name='Asignatura y curso')
    cursos = models.ManyToManyField(Curso, blank=True, related_name='examenes_puntoexacto',
                                    verbose_name='Cursos donde se aplica')
    periodo = models.ForeignKey(PeriodoAcademico, on_delete=models.SET_NULL,
                                null=True, blank=True)
    fecha = models.DateField(verbose_name='Fecha de aplicación')

    numero_preguntas = models.PositiveSmallIntegerField(
        default=20, validators=[MinValueValidator(1), MaxValueValidator(150)])
    numero_opciones = models.PositiveSmallIntegerField(
        default=4, validators=[MinValueValidator(2), MaxValueValidator(8)],
        verbose_name='Opciones por pregunta')
    hojas_por_pagina = models.PositiveSmallIntegerField(
        default=1, choices=[(1, '1 por página'), (2, '2 por página'),
                            (4, '4 por página'), (8, '8 por página')])

    metodo = models.CharField(max_length=14, choices=METODOS, default='con_piso',
                              verbose_name='Cómo se calcula la nota')
    nota_maxima = models.DecimalField(max_digits=4, decimal_places=2, default=Decimal('5.00'))
    nota_minima = models.DecimalField(max_digits=4, decimal_places=2, default=Decimal('1.00'))
    # Solo para el método por descuento. El docente escribe los dos resultados
    # que quiere y el sistema deduce cuánto resta cada error y cada blanco.
    nota_todo_mal = models.DecimalField(
        max_digits=4, decimal_places=2, default=Decimal('1.00'),
        verbose_name='Nota de quien marca todo mal')
    nota_nada_marcado = models.DecimalField(
        max_digits=4, decimal_places=2, default=Decimal('2.00'),
        verbose_name='Nota de quien no marca nada')

    componente = models.CharField(
        max_length=6, choices=COMPONENTES, default='SABER',
        verbose_name='A qué columna de la planilla va',
        help_text='Si alguna pregunta tiene su propio componente, el examen se '
                  'parte en varias columnas, una por componente.')

    mostrar_docente = models.BooleanField(
        default=False, verbose_name='Imprimir el nombre del docente en la hoja')
    mostrar_fecha = models.BooleanField(
        default=False, verbose_name='Imprimir la fecha de presentación en la hoja')
    archivado = models.BooleanField(default=False)
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-fecha', '-creado']
        verbose_name = 'Examen'
        verbose_name_plural = 'Exámenes'

    def __str__(self):
        return f'{self.titulo} ({self.fecha})'

    @property
    def letras(self):
        return LETRAS[:self.numero_opciones]

    @property
    def preguntas_vigentes(self):
        return self.preguntas.filter(anulada=False)

    @property
    def es_manual(self):
        return self.metodo == 'manual'

    def puntos_automaticos(self):
        """Lo que vale cada pregunta cuando la nota sale de una fórmula.

        Con fórmula todas valen lo mismo: lo que aporta un acierto a la nota.
        Con piso, cada acierto sube (máxima - mínima) / n desde la mínima; en
        los demás, máxima / n. A la fórmula solo le importa la proporción, así
        que el redondeo a centésimas no cambia ninguna nota.
        """
        from decimal import ROUND_HALF_UP
        n = self.preguntas_vigentes.count()
        if not n:
            return Decimal('1.00')
        rango = self.nota_maxima - (self.nota_minima if self.metodo == 'con_piso' else 0)
        valor = (rango / n).quantize(Decimal('0.01'), ROUND_HALF_UP)
        return valor if valor > 0 else Decimal('0.01')

    @property
    def puntos_posibles(self):
        total = self.preguntas_vigentes.aggregate(s=models.Sum('puntos'))['s']
        return total or Decimal('0')

    def nombre_componente(self, codigo):
        """Cómo llama este colegio a SER, SABER o HACER.

        Hay colegios que les dicen distinto, y eso ya está configurado en
        ConfiguracionCalificaciones. Se respeta para que el docente vea el
        mismo nombre en PuntoExacto y en el boletín.
        """
        if not self.colegio_id:
            return codigo
        from notas.models.academicos import ConfiguracionCalificaciones
        config = ConfiguracionCalificaciones.objects.filter(colegio=self.colegio).first()
        if not config:
            return codigo
        return getattr(config, f'etiqueta_{codigo.lower()}', codigo) or codigo

    def componentes_usados(self):
        """Los componentes a los que este examen va a mandar notas."""
        propios = set(
            self.preguntas_vigentes.exclude(componente='')
            .values_list('componente', flat=True))
        hay_sin_componente = self.preguntas_vigentes.filter(componente='').exists()
        if hay_sin_componente or not propios:
            propios.add(self.componente)
        return sorted(propios)

    def penalizaciones(self):
        """Cuánto resta cada error y cada blanco, deducido de los dos topes."""
        vigentes = self.preguntas_vigentes.count()
        if not vigentes:
            return {'por_error': Decimal('0'), 'por_blanco': Decimal('0')}
        return {
            'por_error': (self.nota_maxima - self.nota_todo_mal) / vigentes,
            'por_blanco': (self.nota_maxima - self.nota_nada_marcado) / vigentes,
        }


    def secciones(self):
        """Bloques de la hoja, en orden, con sus opciones por pregunta.

        Devuelve [] si el examen no tiene bloques: entonces la hoja sale de una
        sola rejilla, como un examen corriente.
        """
        salida = []
        for b in self.bloques.all():
            preguntas = list(b.preguntas.order_by('numero'))
            if not preguntas:
                continue
            salida.append({
                'nombre': b.nombre,
                'n': len(preguntas),
                'opciones': b.opciones_efectivas(),
                'op_pregunta': [p.opciones_efectivas() for p in preguntas],
                'bloque_id': b.id,
            })
        return salida

    @property
    def es_censal(self):
        return self.bloques.exists()

    def preguntas_sin_bloque(self):
        """Preguntas huérfanas cuando el examen ya tiene bloques.

        No se reparten solas: se le avisa al docente, porque adivinar a qué
        área pertenece una pregunta es justo lo que no debe hacer el programa.
        """
        if not self.bloques.exists():
            return []
        return list(self.preguntas.filter(bloque__isnull=True).order_by('numero'))

    def opciones_maximas(self):
        """La letra más alta que aparece en todo el examen."""
        tope = self.numero_opciones
        for p in self.preguntas.all():
            tope = max(tope, p.opciones_efectivas())
        return tope


class Bloque(models.Model):
    """Un área de la hoja: Lenguaje, Matemáticas, Competencias ciudadanas…

    Dos formas de usarlo, y el colegio escoge:

    * Con materia: el bloque apunta a una Materia del colegio. Entonces su nota
      puede llevarse a la planilla de esa asignatura, resolviendo el docente
      según el curso de cada estudiante. Es el caso de una censal por áreas.
    * Sin materia, solo nombre: el bloque organiza la hoja y las estadísticas y
      nada más. Sirve para lo que no es una materia del plan de estudios
      (lectura crítica, competencias ciudadanas, un simulacro por competencias).

    La numeración de la hoja es corrida entre bloques, como en la hoja del
    ICFES, así que el campo `orden` manda sobre el papel.
    """

    examen = models.ForeignKey(Examen, on_delete=models.CASCADE, related_name='bloques')
    orden = models.PositiveSmallIntegerField(default=1)
    nombre = models.CharField(max_length=60, verbose_name='Nombre del bloque')
    materia = models.ForeignKey(Materia, on_delete=models.SET_NULL, null=True, blank=True,
                                related_name='bloques_puntoexacto',
                                verbose_name='Materia del colegio',
                                help_text='Opcional. Solo si quiere que la nota de este '
                                          'bloque pueda ir a la planilla de esa asignatura.')
    numero_opciones = models.PositiveSmallIntegerField(
        null=True, blank=True, verbose_name='Opciones del bloque',
        help_text='Vacío = las del examen.')
    # Cuánto pesa la nota de este bloque en la nota final de la prueba.
    # Vacío = lo que le toque según sus puntos (con todos vacíos, la nota
    # final sale igual que si el examen no tuviera bloques).
    peso = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name='Peso en la nota final (%)',
        help_text='Vacío = proporcional a sus puntos.')

    class Meta:
        ordering = ['orden', 'id']
        verbose_name = 'Bloque de examen'
        verbose_name_plural = 'Bloques de examen'

    def __str__(self):
        return f'{self.nombre} ({self.examen.titulo})'

    def opciones_efectivas(self):
        """La rejilla del bloque se dibuja con la pregunta más ancha que tenga."""
        tope = self.numero_opciones or self.examen.numero_opciones
        for p in self.preguntas.all():
            if p.numero_opciones:
                tope = max(tope, p.numero_opciones)
        return tope

    def rango(self):
        nums = list(self.preguntas.order_by('numero').values_list('numero', flat=True))
        return (nums[0], nums[-1]) if nums else (None, None)

    def es_continuo(self):
        """¿Sus preguntas van seguidas? Si no, la hoja queda rara y se avisa."""
        nums = sorted(self.preguntas.values_list('numero', flat=True))
        return not nums or nums == list(range(nums[0], nums[0] + len(nums)))


class Pregunta(models.Model):
    """Una pregunta, su respuesta correcta y cuánto vale cada opción."""
    examen = models.ForeignKey(Examen, on_delete=models.CASCADE, related_name='preguntas')
    numero = models.PositiveSmallIntegerField()
    correcta = models.CharField(max_length=1, blank=True, verbose_name='Respuesta correcta')
    puntos = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('1.00'))
    # {'B': 0.5} -> marcar B da la mitad del puntaje de la pregunta.
    parciales = models.JSONField(default=dict, blank=True,
                                 verbose_name='Opciones con crédito parcial')
    bloque = models.ForeignKey('Bloque', on_delete=models.SET_NULL, null=True,
                               blank=True, related_name='preguntas',
                               verbose_name='Bloque o área')
    numero_opciones = models.PositiveSmallIntegerField(
        null=True, blank=True, verbose_name='Opciones de esta pregunta',
        help_text='Vacío = las del bloque, o las del examen. Sirve para hojas '
                  'tipo ICFES, donde unas preguntas son A–D y otras A–H.')
    etiquetas = models.CharField(max_length=200, blank=True,
                                 verbose_name='Qué evalúa',
                                 help_text='Separadas por coma. Se repiten entre preguntas '
                                           'a propósito: así se agrupan en el análisis.')
    componente = models.CharField(
        max_length=6, choices=COMPONENTES, blank=True,
        verbose_name='Componente',
        help_text='Vacío = el del examen. Permite que un mismo examen evalúe '
                  'SABER en unas preguntas y HACER en otras.')
    anulada = models.BooleanField(default=False)

    class Meta:
        ordering = ['numero']
        unique_together = ('examen', 'numero')

    def __str__(self):
        return f'{self.examen.titulo} · pregunta {self.numero}'

    def opciones_efectivas(self):
        """Cuántas burbujas lleva esta pregunta.

        Pregunta -> bloque -> examen, el primero que diga algo manda.
        """
        if self.numero_opciones:
            return self.numero_opciones
        if self.bloque_id and self.bloque.numero_opciones:
            return self.bloque.numero_opciones
        return self.examen.numero_opciones

    def letras(self):
        return LETRAS[:self.opciones_efectivas()]

    def lista_etiquetas(self):
        return [e.strip() for e in self.etiquetas.split(',') if e.strip()]

    def fraccion(self, marcada):
        """Qué fracción del puntaje gana esta respuesta: de 0 a 1."""
        if not marcada or marcada == Hoja.MARCA_DOBLE:
            return Decimal('0')
        if marcada == self.correcta:
            return Decimal('1')
        try:
            return Decimal(str(self.parciales.get(marcada, 0)))
        except Exception:
            return Decimal('0')


class Hoja(models.Model):
    """La hoja de un estudiante: su identificador y sus respuestas."""
    MARCA_DOBLE = '?'

    ESTADOS = [
        ('pendiente', 'Sin calificar'),
        ('calificada', 'Calificada'),
        ('revisar', 'Necesita revisión'),
        ('ausente', 'No presentó'),
    ]

    examen = models.ForeignKey(Examen, on_delete=models.CASCADE, related_name='hojas')
    estudiante = models.ForeignKey(Estudiante, on_delete=models.CASCADE,
                                   null=True, blank=True, related_name='hojas_puntoexacto')
    # Cuando el estudiante no está en ninguna lista (Salón Digital, o alguien
    # que llegó al colegio y todavía no se ha matriculado).
    nombre_libre = models.CharField(max_length=160, blank=True)
    documento_libre = models.CharField(max_length=40, blank=True)

    identificador = models.CharField(max_length=40, unique=True,
                                     help_text='Lo que va en el código de barras.')
    estado = models.CharField(max_length=12, choices=ESTADOS, default='pendiente')
    nota = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    nota_recortada = models.BooleanField(
        default=False, help_text='La nota calculada se salía de la escala y se ajustó.')
    enviada_a_planilla = models.BooleanField(default=False)
    actualizada = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['estudiante__user__last_name', 'nombre_libre']
        verbose_name = 'Hoja'
        verbose_name_plural = 'Hojas'

    def __str__(self):
        return f'{self.nombre} · {self.examen.titulo}'

    @property
    def nombre(self):
        if self.estudiante_id and self.estudiante.user:
            completo = f'{self.estudiante.user.last_name} {self.estudiante.user.first_name}'.strip()
            return completo or self.estudiante.user.username
        return self.nombre_libre or 'Sin identificar'

    @property
    def documento(self):
        if self.estudiante_id and hasattr(self.estudiante, 'ficha'):
            return self.estudiante.ficha.numero_documento or ''
        return self.documento_libre


class Respuesta(models.Model):
    """Lo que marcó el estudiante en una pregunta. Vacío = no marcó."""
    hoja = models.ForeignKey(Hoja, on_delete=models.CASCADE, related_name='respuestas')
    pregunta = models.ForeignKey(Pregunta, on_delete=models.CASCADE, related_name='respuestas')
    marcada = models.CharField(max_length=1, blank=True)

    class Meta:
        unique_together = ('hoja', 'pregunta')
        ordering = ['pregunta__numero']

    def __str__(self):
        return f'{self.hoja_id} · P{self.pregunta.numero} = {self.marcada or "en blanco"}'
