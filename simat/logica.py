"""Lo que se le manda al SIMAT de cada estudiante y qué le falta para estar listo."""
import datetime
import re

from django.utils import timezone

from notas.models import Estudiante, HistorialMatricula
from notas.models.perfiles import normalizar_subgrupo

from . import codigos as C
from .models import ConfiguracionSimat, DatosSimat

PARTICULAS = {'de', 'del', 'la', 'las', 'los', 'san', 'santa', 'da', 'van', 'von', 'y'}


def partir(texto):
    """«de la Cruz Pérez» -> ('DE LA CRUZ', 'PÉREZ'): el primero y el resto."""
    grupos, actual = [], []
    for p in (texto or '').split():
        actual.append(p)
        if p.lower() not in PARTICULAS:
            grupos.append(' '.join(actual))
            actual = []
    if actual:
        grupos.append(' '.join(actual))
    if not grupos:
        return '', ''
    return grupos[0].upper(), ' '.join(grupos[1:]).upper()


def edad(fecha, hoy=None):
    if not fecha:
        return None
    hoy = hoy or timezone.localdate()
    return hoy.year - fecha.year - ((hoy.month, hoy.day) < (fecha.month, fecha.day))


def _sn(v):
    return 'S' if v else 'N'


class Contexto:
    """Lo que se consulta una sola vez para todos los estudiantes."""

    def __init__(self, colegio, ano=None):
        self.colegio = colegio
        self.ano = ano or timezone.localdate().year
        self.conf = ConfiguracionSimat.de(colegio)
        self.historial = {h.estudiante_id: h for h in HistorialMatricula.objects.filter(
            colegio=colegio, ano_lectivo=self.ano - 1)}
        self.hay_historial = bool(self.historial)
        try:
            from piar.models import Piar
            self.piar = {p.estudiante_id: p.categoria for p in Piar.objects.filter(colegio=colegio).order_by('ano_lectivo')}
        except Exception:      # sin el módulo de PIAR instalado
            self.piar = {}


def efectivos(est, ctx):
    """Valor final de cada dato SIMAT del estudiante (lo guardado o lo que se deduce)."""
    conf, col = ctx.conf, ctx.colegio
    d = getattr(est, 'simat', None) or DatosSimat(estudiante=est)
    ficha = getattr(est, 'ficha', None)
    curso = est.curso
    sede = curso.sede if curso else None
    a1, a2 = partir(est.user.last_name)
    n1, n2 = partir(est.user.first_name)
    hist = ctx.historial.get(est.id)

    if d.nuevo is not None:
        nuevo = d.nuevo
    else:
        nuevo = (hist is None) if ctx.hay_historial else False
    situacion = d.situacion_anterior
    if not situacion and hist:
        situacion = {'PROMOVIDO': '1', 'GRADUADO': '1', 'NO_PROMOVIDO': '2', 'RETIRADO': '8'}.get(hist.resultado, '')
    if not situacion and not nuevo:
        situacion = '1'
    repitente = d.repitente or bool(hist and hist.resultado == 'NO_PROMOVIDO')

    if d.discapacidad:
        discapacidad = d.discapacidad
    elif est.es_inclusion and ctx.piar.get(est.id):
        discapacidad = conf.codigo_discapacidad(ctx.piar[est.id])
    else:
        discapacidad = '99'

    jornada = d.jornada
    if not jornada and sede and len(sede.lista_jornadas()) == 1:
        jornada = C.JORNADA_DESDE_SEDE.get(sede.jornadas.split(',')[0], '')
    jornada = jornada or conf.jornada

    sub = normalizar_subgrupo(curso.subgrupo) if curso else ''
    grupo = sub.zfill(2) if sub.isdigit() else (sub or '01')
    if not conf.oficial:
        consecutivo = '00'
    elif sede is None:
        consecutivo = conf.consecutivos.get('', '') or '01'
    else:
        consecutivo = conf.consecutivos.get(str(sede.id)) or ('01' if sede.es_principal else '')
    dane = re.sub(r'\D', '', col.dane or '')
    media = curso is not None and curso.grado in (10, 11)

    return {
        'est': est, 'curso': curso,
        'ano': str(ctx.ano),
        'dpto_institucion': dane[1:3] if len(dane) >= 6 else '',
        'dane_institucion': dane,
        'dane_sede': re.sub(r'\D', '', (sede.codigo_dane if sede else '') or '') or dane,
        'consecutivo_sede': (dane + consecutivo) if consecutivo else '',
        'tipo_documento': C.TIPO_DESDE_FICHA.get(getattr(ficha, 'tipo_documento', '') or '', ''),
        'numero_documento': re.sub(r'[^0-9A-Za-z]', '', (getattr(ficha, 'numero_documento', '') or '')),
        'mpio_expedicion': d.mpio_expedicion,
        'apellido1': d.apellido1 or a1, 'apellido2': d.apellido2 or (a2 if not d.apellido1 else ''),
        'nombre1': d.nombre1 or n1, 'nombre2': d.nombre2 or (n2 if not d.nombre1 else ''),
        'direccion': d.direccion, 'telefono': d.telefono or (getattr(ficha, 'celular_acudiente', '') or ''),
        'mpio_residencia': d.mpio_residencia,
        'estrato': d.estrato,
        'fecha_nacimiento': getattr(ficha, 'fecha_nacimiento', None),
        'mpio_nacimiento': d.mpio_nacimiento,
        'genero': d.genero,
        'vulnerabilidad': d.vulnerabilidad or '9',
        'mpio_desplazamiento': d.mpio_desplazamiento if d.vulnerabilidad == '1' else '',
        'discapacidad': discapacidad,
        'capacidad': d.capacidad or '9',
        'etnia': d.etnia or '00',
        'resguardo': d.resguardo or '000',
        'institucion_bienestar': d.institucion_bienestar,
        'jornada': jornada,
        'caracter': conf.caracter if media else '0',
        'especialidad': conf.especialidad if media else '00',
        'grado': '' if curso is None or curso.grado is None else str(curso.grado),
        'grupo': grupo,
        'metodologia': conf.metodologia,
        'subsidio': _sn(d.subsidio), 'repitente': _sn(repitente), 'nuevo': _sn(nuevo),
        'situacion_anterior': situacion,
        'motivo_retiro': '9',
        'fuente_recursos': conf.fuente_recursos,
        'zona': d.zona,
        'madre_cabeza': _sn(d.madre_cabeza), 'hijo_madre_cabeza': _sn(d.hijo_madre_cabeza),
        'veterano': _sn(d.veterano), 'heroe': _sn(d.heroe),
    }


REQUERIDOS = [
    ('tipo_documento', 'Tipo de documento'), ('numero_documento', 'Número de documento'),
    ('apellido1', 'Primer apellido'), ('nombre1', 'Primer nombre'), ('fecha_nacimiento', 'Fecha de nacimiento'),
    ('genero', 'Género'), ('direccion', 'Dirección'), ('mpio_residencia', 'Municipio de residencia'),
    ('zona', 'Zona'), ('estrato', 'Estrato'), ('mpio_nacimiento', 'Municipio de nacimiento'),
    ('mpio_expedicion', 'Municipio de expedición'), ('grado', 'Grado del curso'),
    ('consecutivo_sede', 'Consecutivo de la sede'), ('situacion_anterior', 'Situación del año anterior'),
]


def faltantes(ef, hoy=None):
    """Lo que le falta o está mal para que el SIMAT lo reciba."""
    salida = [nombre for clave, nombre in REQUERIDOS if not ef.get(clave)]
    tipo, num = ef['tipo_documento'], ef['numero_documento']
    años = edad(ef['fecha_nacimiento'], hoy)
    if num:
        if tipo == '2' and not (num.isdigit() and len(num) in (10, 11)):
            salida.append('La tarjeta de identidad debe tener 10 u 11 números')
        elif tipo in ('5', '7') and not (num.isdigit() and len(num) in (8, 10, 11)):
            salida.append('El registro civil / NUIP debe tener 8, 10 u 11 números')
        elif tipo == '1' and not (num.isdigit() and 3 <= len(num) <= 10):
            salida.append('La cédula debe tener entre 3 y 10 números')
        elif tipo == '3' and len(num) < 7:
            salida.append('La cédula de extranjería debe tener al menos 7 caracteres')
    if tipo == '1' and años is not None and años < 18:
        salida.append(f'Tiene cédula pero {años} años: revise el tipo de documento')
    if tipo == '2' and años is not None and años >= 18:
        salida.append(f'Tiene tarjeta de identidad y {años} años: ¿ya sacó la cédula?')
    if ef['vulnerabilidad'] == '1' and not ef['mpio_desplazamiento']:
        salida.append('Municipio de donde fue desplazado')
    return salida


def estudiantes(colegio, curso_id=None):
    qs = (Estudiante.objects.filter(colegio=colegio, is_active=True, curso__isnull=False)
          .select_related('user', 'curso__sede', 'ficha', 'simat')
          .order_by('curso__orden', 'user__last_name', 'user__first_name'))
    if curso_id:
        qs = qs.filter(curso_id=curso_id)
    return qs


def revision(colegio, curso_id=None, ano=None, hoy=None):
    ctx = Contexto(colegio, ano)
    filas = []
    for est in estudiantes(colegio, curso_id):
        ef = efectivos(est, ctx)
        ef['faltan'] = faltantes(ef, hoy)
        filas.append(ef)
    return ctx, filas


def problemas_del_colegio(colegio):
    conf = ConfiguracionSimat.de(colegio)
    p = []
    dane = re.sub(r'\D', '', colegio.dane or '')
    if len(dane) != 12:
        p.append('El código DANE del colegio debe tener 12 números (Configuración del colegio).')
    if not conf.municipio:
        p.append('Falta el municipio del colegio en la configuración SIMAT.')
    return p


def llenar_vacios(colegio, campo, valor, curso_id=None):
    """Pone el mismo valor a los estudiantes que tienen ese dato vacío. Devuelve cuántos."""
    n = 0
    for est in estudiantes(colegio, curso_id):
        d, _ = DatosSimat.objects.get_or_create(estudiante=est)
        if not getattr(d, campo):
            setattr(d, campo, valor)
            d.save(update_fields=[campo, 'actualizado'])
            n += 1
    return n


CAMPOS_LLENABLES = [
    ('mpio_residencia', 'Municipio de residencia', 'municipio'), ('mpio_nacimiento', 'Municipio de nacimiento', 'municipio'),
    ('mpio_expedicion', 'Municipio de expedición', 'municipio'), ('zona', 'Zona', C.ZONA),
    ('estrato', 'Estrato', C.ESTRATO),
]
