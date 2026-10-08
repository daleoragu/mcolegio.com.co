# -*- coding: utf-8 -*-
"""Lo que hace la prematrícula por dentro: radicados, valores por defecto,
buscar a un antiguo, aprobar (crear o actualizar al estudiante) y resumir la
encuesta."""
import datetime
from collections import Counter

from django.contrib.auth.models import Group, User
from django.core import signing
from django.db import transaction
from django.utils import timezone
from django.utils.text import slugify

from notas.models import Estudiante, FichaEstudiante

from .models import Configuracion, PreguntaEncuesta, Requisito, Solicitud

REQUISITOS_BASE = [
    # (nombre, indicación, archivo, obligatorio, para)
    ('Registro civil o tarjeta de identidad del estudiante', 'Foto o PDF legible, por ambas caras si es tarjeta.', True, True, 'TODOS'),
    ('Documento de identidad del acudiente', 'Cédula por ambas caras.', True, True, 'NUEVOS'),
    ('Certificado de estudios o boletín final del año anterior', 'Del último grado aprobado.', True, True, 'NUEVOS'),
    ('Certificado de afiliación a EPS o SISBÉN', '', True, True, 'TODOS'),
    ('Paz y salvo del colegio anterior', 'Si viene de un colegio privado.', True, False, 'NUEVOS'),
    ('Carné de vacunas', 'Para preescolar y primaria.', True, False, 'NUEVOS'),
    ('Foto tipo documento', 'Fondo blanco, reciente.', True, False, 'TODOS'),
]

ENCUESTA_BASE = [
    ('¿Cómo se enteró del colegio?', 'UNA',
     'Recomendación de un familiar o amigo\nRedes sociales\nPortal web del colegio\nVivimos cerca\nYa es estudiante del colegio\nOtro'),
    ('¿Por qué eligió este colegio?', 'VARIAS',
     'Calidad académica\nCercanía a la casa\nModalidad o especialidad\nConvivencia y valores\nHermanos en el colegio\nOtro'),
    ('¿Cómo llegará el estudiante al colegio?', 'UNA',
     'A pie\nBicicleta\nMoto\nTransporte público\nRuta escolar\nVehículo particular'),
    ('¿Tiene computador o tableta con internet en casa?', 'SINO', ''),
    ('¿Cuántas personas viven en el hogar?', 'UNA', '1 o 2\n3 o 4\n5 o 6\n7 o más'),
    ('¿Qué tan satisfecho está con la información recibida en este proceso?', 'ESCALA', ''),
    ('¿Algo más que quiera contarle al colegio?', 'TEXTO', ''),
]

TRATAMIENTO_GENERAL = (
    'Autorizo al colegio a tratar los datos personales del estudiante y de su familia, incluidos '
    'los datos de salud, únicamente para el proceso de matrícula y la atención escolar, conforme '
    'a la Ley 1581 de 2012 y su política de tratamiento de datos. Declaro que la información es verídica.')


def configuracion_de(colegio, crear=True):
    """La configuración del colegio; la primera vez la crea con requisitos y encuesta de ejemplo."""
    conf = Configuracion.objects.filter(colegio=colegio).first()
    if conf is None and crear:
        with transaction.atomic():
            conf = Configuracion.objects.create(colegio=colegio, ano_lectivo=timezone.localdate().year + 1)
            for i, (nombre, desc, archivo, oblig, para) in enumerate(REQUISITOS_BASE):
                Requisito.objects.create(colegio=colegio, nombre=nombre, descripcion=desc,
                                         pide_archivo=archivo, obligatorio=oblig, para=para, orden=i)
            for i, (texto, tipo, opciones) in enumerate(ENCUESTA_BASE):
                PreguntaEncuesta.objects.create(colegio=colegio, texto=texto, tipo=tipo,
                                                opciones=opciones, orden=i)
    return conf


def nuevo_radicado(colegio, ano):
    """PM-2027-0001, consecutivo por colegio y año."""
    n = Solicitud.objects.filter(colegio=colegio, ano_lectivo=ano).count() + 1
    while True:
        radicado = f'PM{colegio.id}-{ano}-{n:04d}'
        if not Solicitud.objects.filter(radicado=radicado).exists():
            return radicado
        n += 1


def buscar_antiguo(colegio, documento, fecha_nacimiento):
    """El estudiante del colegio con ese documento y esa fecha de nacimiento.

    Se piden los dos para que nadie consulte los datos de otro solo con su
    número de documento. Si la ficha no tiene fecha, basta el documento.
    """
    documento = (documento or '').strip()
    if not documento:
        return None
    ficha = (FichaEstudiante.objects.select_related('estudiante__user', 'estudiante__curso')
             .filter(estudiante__colegio=colegio, numero_documento=documento).first())
    if ficha is None:
        return None
    if ficha.fecha_nacimiento and ficha.fecha_nacimiento != fecha_nacimiento:
        return None
    return ficha.estudiante


def datos_iniciales_antiguo(estudiante):
    ficha = getattr(estudiante, 'ficha', None)
    u = estudiante.user
    datos = {'nombres': u.first_name, 'apellidos': u.last_name}
    if ficha:
        datos.update({
            'tipo_documento': ficha.tipo_documento, 'numero_documento': ficha.numero_documento or '',
            'fecha_nacimiento': ficha.fecha_nacimiento, 'lugar_nacimiento': ficha.lugar_nacimiento or '',
            'eps': ficha.eps or '', 'rh': ficha.grupo_sanguineo or '',
            'alergias': ficha.enfermedades_alergias or '',
            'acudiente_nombre': ficha.nombre_acudiente or '', 'acudiente_celular': ficha.celular_acudiente or '',
            'acudiente_correo': ficha.email_acudiente or '',
            'madre_nombre': ficha.nombre_madre or '', 'madre_celular': ficha.celular_madre or '',
            'padre_nombre': ficha.nombre_padre or '', 'padre_celular': ficha.celular_padre or '',
        })
    curso = estudiante.curso
    if curso and curso.grado is not None:
        datos['grado'] = min(curso.grado + 1, 11)
        if curso.sede_id:
            datos['sede'] = curso.sede_id
    return datos


# ---------------------------------------------------------------------------
# Consulta de la familia: enlace firmado con el radicado
# ---------------------------------------------------------------------------

SAL = 'prematricula.consulta'


def token_consulta(solicitud):
    return signing.dumps({'s': solicitud.id, 'r': solicitud.radicado}, salt=SAL, compress=True)


def solicitud_de_token(token, colegio):
    try:
        datos = signing.loads(token, salt=SAL, max_age=400 * 24 * 3600)
    except signing.BadSignature:
        return None
    return Solicitud.objects.filter(id=datos.get('s'), radicado=datos.get('r'), colegio=colegio).first()


# ---------------------------------------------------------------------------
# Aprobar
# ---------------------------------------------------------------------------

class NoSePuedeAprobar(Exception):
    pass


def _usuario_nuevo(nombres, apellidos):
    from unidecode import unidecode
    base = f"{slugify(unidecode(nombres.split()[0].lower()))}.{slugify(unidecode(apellidos.split()[0].lower()))}"
    nombre, i = base, 1
    while User.objects.filter(username=nombre).exists():
        nombre, i = f'{base}{i}', i + 1
    return nombre


def _llenar_ficha(ficha, s):
    ficha.tipo_documento = s.tipo_documento if s.tipo_documento in dict(FichaEstudiante.TIPO_DOCUMENTO_CHOICES) else 'OT'
    ficha.numero_documento = s.numero_documento
    ficha.fecha_nacimiento = s.fecha_nacimiento
    ficha.lugar_nacimiento = s.lugar_nacimiento
    ficha.eps = s.eps
    ficha.grupo_sanguineo = s.rh or None
    alergias = s.alergias
    if s.necesita_apoyo:
        alergias = (alergias + '\n' if alergias else '') + f'Requiere apoyo: {s.apoyo_detalle or "sí"}'
    ficha.enfermedades_alergias = alergias
    ficha.nombre_acudiente = s.acudiente_nombre
    ficha.celular_acudiente = s.acudiente_celular[:20]
    ficha.email_acudiente = s.acudiente_correo or None
    ficha.nombre_madre = s.madre_nombre
    ficha.celular_madre = s.madre_celular[:20]
    ficha.nombre_padre = s.padre_nombre
    ficha.celular_padre = s.padre_celular[:20]
    if s.tipo == 'NUEVO':
        ficha.colegio_anterior = s.colegio_procedencia
        ficha.grado_anterior = s.ultimo_grado[:20]
    ficha.save()


def aprobar(solicitud, usuario):
    """Aprueba: crea al estudiante nuevo en su curso o actualiza la ficha del antiguo.

    Devuelve (estudiante, usuario_creado o None, contraseña o None).

    Si la matrícula es para un año que todavía no empieza, el estudiante nuevo
    queda inactivo: así no aparece en las planillas del año en curso. Se
    activa con «Activar matriculados» cuando empiece el año.
    """
    s = solicitud
    if s.estado == 'APROBADA':
        raise NoSePuedeAprobar('La solicitud ya estaba aprobada.')
    if s.tipo == 'NUEVO' and s.curso_asignado is None:
        raise NoSePuedeAprobar('Asigne el curso antes de aprobar.')
    otra = FichaEstudiante.objects.filter(numero_documento=s.numero_documento)
    if s.tipo == 'ANTIGUO' and s.estudiante_antiguo_id:
        otra = otra.exclude(estudiante=s.estudiante_antiguo)
    if otra.exists():
        quien = otra.select_related('estudiante__user', 'estudiante__colegio').first().estudiante
        raise NoSePuedeAprobar(
            f'Ya hay un estudiante con el documento {s.numero_documento}: {quien} '
            f'({quien.colegio}). Revise si es un estudiante antiguo.')

    usuario_nuevo = clave = None
    with transaction.atomic():
        if s.tipo == 'ANTIGUO' and s.estudiante_antiguo_id:
            est = s.estudiante_antiguo
            u = est.user
            u.first_name, u.last_name = s.nombres[:150], s.apellidos[:150]
            u.save(update_fields=['first_name', 'last_name'])
        else:
            nombre = _usuario_nuevo(s.nombres, s.apellidos)
            clave = nombre        # misma regla que al crear estudiantes a mano
            u = User.objects.create_user(username=nombre, password=clave,
                                         first_name=s.nombres[:150], last_name=s.apellidos[:150])
            grupo, _ = Group.objects.get_or_create(name='Estudiantes')
            u.groups.add(grupo)
            empieza_ya = s.ano_lectivo <= timezone.localdate().year
            est = Estudiante.objects.create(user=u, colegio=s.colegio, curso=s.curso_asignado,
                                            is_active=empieza_ya, es_inclusion=s.necesita_apoyo)
            usuario_nuevo = u
        ficha, _ = FichaEstudiante.objects.get_or_create(estudiante=est)
        _llenar_ficha(ficha, s)
        s.estado = 'APROBADA'
        s.estudiante_creado = est
        s.revisada_por = usuario
        s.decidida = timezone.now()
        s.save()
    return est, usuario_nuevo, clave


# ---------------------------------------------------------------------------
# Encuesta
# ---------------------------------------------------------------------------

def resumen_encuesta(colegio, solicitudes):
    """Por pregunta: conteo de cada opción (o la lista de respuestas abiertas)."""
    salida = []
    solicitudes = list(solicitudes)
    for p in colegio.preguntas_prematricula.filter(activa=True):
        clave = str(p.id)
        respuestas = [s.encuesta.get(clave) for s in solicitudes if s.encuesta.get(clave) not in (None, '', [])]
        if p.tipo == 'TEXTO':
            salida.append({'pregunta': p, 'abiertas': respuestas, 'total': len(respuestas)})
            continue
        conteo = Counter()
        for r in respuestas:
            for v in (r if isinstance(r, list) else [r]):
                conteo[str(v)] += 1
        opciones = p.lista_opciones()
        filas = [(o, conteo.get(o, 0)) for o in opciones] + \
                [(o, n) for o, n in conteo.items() if o not in opciones]
        base = len(respuestas) or 1
        salida.append({'pregunta': p, 'total': len(respuestas),
                       'filas': [(o, n, round(100 * n / base)) for o, n in filas]})
    return salida
