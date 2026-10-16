"""Datos que pide el SIMAT y que la ficha del estudiante no tenía."""
from django.core.validators import RegexValidator
from django.db import models

from notas.models import Colegio, Estudiante

from . import codigos as C

DANE_MPIO = RegexValidator(r'^\d{5}$', 'Escriba el código DANE de 5 cifras (departamento + municipio). Ej.: 73443.')


def _mpio(verbose, ayuda=''):
    return models.CharField(max_length=5, blank=True, validators=[DANE_MPIO], verbose_name=verbose, help_text=ayuda)


class ConfiguracionSimat(models.Model):
    SEPARADORES = [(';', 'Punto y coma ( ; )'), (',', 'Coma ( , )')]
    CODIFICACIONES = [('cp1252', 'Windows (ANSI)'), ('utf-8', 'UTF-8')]

    colegio = models.OneToOneField(Colegio, on_delete=models.CASCADE, related_name='config_simat')
    municipio = _mpio('Municipio del colegio', 'Código DANE de 5 cifras. Se usa para llenar los vacíos de un clic.')
    oficial = models.BooleanField(default=True, verbose_name='Colegio oficial (público)',
                                  help_text='Los privados usan «00» como consecutivo de sede.')
    jornada = models.CharField(max_length=2, choices=C.JORNADA, default='2', verbose_name='Jornada por defecto')
    caracter = models.CharField(max_length=2, choices=C.CARACTER, default='1', verbose_name='Carácter (media)')
    especialidad = models.CharField(max_length=2, choices=C.ESPECIALIDAD, default='05', verbose_name='Especialidad (media)')
    metodologia = models.CharField(max_length=2, choices=C.METODOLOGIA, default='1', verbose_name='Metodología')
    fuente_recursos = models.CharField(max_length=2, choices=C.FUENTE_RECURSOS, default='1',
                                       verbose_name='Fuente de recursos')
    # {sede_id: "01"}: consecutivo de cada sede en el DUE.
    consecutivos = models.JSONField(default=dict, blank=True)
    # {categoría PIAR: código}: cuando el SIMAT de la secretaría usa otros códigos.
    discapacidad_piar = models.JSONField(default=dict, blank=True)
    columnas = models.TextField(blank=True, verbose_name='Fila de títulos de la plantilla del SIMAT',
                                help_text='Pegue aquí la fila de títulos de la plantilla de cargue que le da el SIMAT. '
                                          'El archivo sale con esas columnas y en ese orden. Vacío: orden del manual.')
    separador = models.CharField(max_length=1, choices=SEPARADORES, default=';')
    codificacion = models.CharField(max_length=10, choices=CODIFICACIONES, default='cp1252')

    @classmethod
    def de(cls, colegio):
        return cls.objects.get_or_create(colegio=colegio)[0]

    def codigo_discapacidad(self, categoria):
        return (self.discapacidad_piar or {}).get(categoria) or C.DISCAPACIDAD_DESDE_PIAR.get(categoria, '99')


class DatosSimat(models.Model):
    estudiante = models.OneToOneField(Estudiante, on_delete=models.CASCADE, primary_key=True, related_name='simat')
    apellido1 = models.CharField(max_length=60, blank=True, verbose_name='Primer apellido')
    apellido2 = models.CharField(max_length=60, blank=True, verbose_name='Segundo apellido')
    nombre1 = models.CharField(max_length=60, blank=True, verbose_name='Primer nombre')
    nombre2 = models.CharField(max_length=60, blank=True, verbose_name='Segundo nombre')
    genero = models.CharField(max_length=1, choices=C.GENERO, blank=True, verbose_name='Género')
    estrato = models.CharField(max_length=1, choices=C.ESTRATO, blank=True, verbose_name='Estrato')
    direccion = models.CharField(max_length=120, blank=True, verbose_name='Dirección de residencia')
    telefono = models.CharField(max_length=30, blank=True, verbose_name='Teléfono')
    mpio_residencia = _mpio('Municipio de residencia')
    zona = models.CharField(max_length=1, choices=C.ZONA, blank=True, verbose_name='Zona')
    mpio_nacimiento = _mpio('Municipio de nacimiento')
    mpio_expedicion = _mpio('Municipio de expedición del documento')
    vulnerabilidad = models.CharField(max_length=1, choices=C.VULNERABILIDAD, default='9',
                                      verbose_name='Situación de vulnerabilidad')
    mpio_desplazamiento = _mpio('Municipio de donde fue desplazado')
    discapacidad = models.CharField(max_length=2, choices=[('', 'Según el PIAR')] + C.DISCAPACIDAD, blank=True,
                                    verbose_name='Discapacidad',
                                    help_text='Vacío: sale de la categoría del PIAR (o «No aplica»).')
    capacidad = models.CharField(max_length=1, choices=C.CAPACIDAD, default='9', verbose_name='Capacidades excepcionales')
    etnia = models.CharField(max_length=3, blank=True, default='00', verbose_name='Etnia (código)',
                             help_text='00 = No aplica, 200 = Negritudes, 400 = Rom. Los demás, según la tabla del SIMAT.')
    resguardo = models.CharField(max_length=4, blank=True, default='000', verbose_name='Resguardo (código)')
    jornada = models.CharField(max_length=2, choices=[('', 'La del colegio')] + C.JORNADA, blank=True,
                               verbose_name='Jornada')
    repitente = models.BooleanField(default=False, verbose_name='Repitente')
    nuevo = models.BooleanField(null=True, blank=True, verbose_name='Nuevo en la institución',
                                help_text='Vacío: se calcula con el historial de matrícula.')
    situacion_anterior = models.CharField(max_length=1, choices=C.SITUACION_ANTERIOR, blank=True,
                                          verbose_name='Situación del año anterior')
    subsidio = models.BooleanField(default=False, verbose_name='Matrícula contratada (subsidio)')
    madre_cabeza = models.BooleanField(default=False, verbose_name='Madre cabeza de familia')
    hijo_madre_cabeza = models.BooleanField(default=False, verbose_name='Hijo de madre cabeza de familia')
    veterano = models.BooleanField(default=False, verbose_name='Beneficiario veterano de la Fuerza Pública')
    heroe = models.BooleanField(default=False, verbose_name='Beneficiario héroe de la Nación')
    institucion_bienestar = models.CharField(max_length=120, blank=True, verbose_name='Institución de bienestar de origen',
                                             help_text='Solo para preescolar, si viene de un hogar o CDI.')
    actualizado = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Datos SIMAT'
        verbose_name_plural = 'Datos SIMAT'

    def __str__(self):
        return f'SIMAT · {self.estudiante}'
