"""Reporte parcial: nota parcial de cada estudiante y aviso a la familia.

* La nota parcial sale de las notas que ya hay en la planilla del periodo: el
  promedio de cada componente que tiene notas, repartiendo el peso solo entre
  esos componentes (un componente sin notas todavía no baja la nota).
* Si la nota parcial está en desempeño bajo, el reporte del docente sale ya
  marcado en «Sí»; el docente decide al guardar.
* El aviso a la familia va por WhatsApp (mensaje listo) o por correo, con un
  enlace personal para descargar el informe parcial en PDF sin usuario ni
  contraseña.
"""
from decimal import Decimal, ROUND_HALF_UP

from django.conf import settings
from django.core import signing
from django.db.models import Count

from . import componentes as _comp
from .avisos_familia import correo_configurado, enlace_whatsapp, contactos  # noqa: F401  (los usa la vista)
from .boletin.ponderacion import nota_aprobacion
from .models import Calificacion, EscalaValoracion, ReporteParcial

SAL = 'notas.reporte-parcial.informe'
DIAS_ENLACE = 30


def notas_parciales(asignacion, periodo, estudiantes):
    """{estudiante_id: nota parcial (Decimal) o None si aún no tiene notas}."""
    pesos = {c: Decimal(p) for c, p in _comp.pesos(asignacion).items() if p and Decimal(p) > 0}
    if not pesos:
        return {}
    filas = (Calificacion.objects.filter(materia=asignacion.materia, periodo=periodo, estudiante__in=estudiantes,
                                         tipo_nota__in=list(pesos))
             .annotate(n=Count('notas_detalladas')).filter(n__gt=0)
             .values_list('estudiante_id', 'tipo_nota', 'valor_nota'))
    por_est = {}
    for est_id, codigo, valor in filas:
        por_est.setdefault(est_id, []).append((pesos[codigo], Decimal(valor)))
    salida = {}
    for est_id, partes in por_est.items():
        total = sum(p for p, _ in partes)
        salida[est_id] = (sum(p * v for p, v in partes) / total).quantize(Decimal('0.1'), rounding=ROUND_HALF_UP)
    return salida


def esta_en_bajo(colegio, nota):
    return nota is not None and nota < nota_aprobacion(colegio)


def desempeno(colegio, nota):
    if nota is None:
        return ''
    e = EscalaValoracion.objects.filter(colegio=colegio, valor_minimo__lte=nota, valor_maximo__gte=nota).first()
    return e.nombre_desempeno.upper() if e else ''


def texto_nota(nota):
    return str(nota).replace('.', ',') if nota is not None else ''


def asignaturas_reportadas(estudiante, periodo):
    """[(materia, docente, nota parcial)] de lo reportado con dificultades en el periodo."""
    reportes = (ReporteParcial.objects.filter(estudiante=estudiante, periodo=periodo, presenta_dificultades=True)
                .select_related('asignacion__materia', 'asignacion__docente__user')
                .order_by('asignacion__materia__nombre'))
    salida = []
    for r in reportes:
        nota = notas_parciales(r.asignacion, periodo, [estudiante]).get(estudiante.id)
        salida.append({'materia': r.asignacion.materia.nombre,
                       'docente': r.asignacion.docente.user.get_full_name() if r.asignacion.docente_id else '',
                       'nota': nota, 'nota_texto': texto_nota(nota),
                       'desempeno': desempeno(estudiante.colegio, nota)})
    return salida


def token_informe(estudiante, periodo):
    return signing.dumps({'e': estudiante.id, 'p': periodo.id}, salt=SAL, compress=True)


def leer_token(token):
    """(estudiante_id, periodo_id) o None si el enlace venció o no es válido."""
    try:
        datos = signing.loads(token, salt=SAL, max_age=DIAS_ENLACE * 24 * 3600)
    except signing.BadSignature:
        return None
    return datos.get('e'), datos.get('p')


def texto_aviso(estudiante, periodo, asignaturas, url_informe=''):
    colegio = estudiante.colegio.nombre
    nombre = f'{estudiante.user.first_name} {estudiante.user.last_name}'.strip() or estudiante.user.username
    lista = ', '.join(a['materia'] + (f' ({a["nota_texto"]})' if a['nota_texto'] else '') for a in asignaturas)
    texto = (f'{colegio}: le informamos que en el informe parcial del {periodo.get_nombre_display().lower()} '
             f'{nombre} presenta dificultades en: {lista}.\n'
             f'Todavía hay tiempo para mejorar antes del cierre del periodo: le pedimos acompañarlo(a) en casa '
             f'y comunicarse con los docentes si lo necesita.')
    if url_informe:
        texto += f'\nDescargue el informe parcial aquí: {url_informe}'
    return texto


def correo_acudiente(estudiante):
    ficha = getattr(estudiante, 'ficha', None)
    return ((getattr(ficha, 'email_acudiente', '') if ficha else '') or '').strip()


def enviar_correo(estudiante, periodo, asignaturas, url_informe):
    """(enviado, detalle)."""
    correo = correo_acudiente(estudiante)
    if not correo:
        return False, 'el estudiante no tiene correo de acudiente en la ficha'
    if not correo_configurado():
        return False, 'el correo de la plataforma no está configurado'
    asunto = f'Informe parcial · {estudiante.user.get_full_name()}'
    try:
        from .mensajeria import enviar_correo as mandar
        mandar(estudiante.colegio, asunto, texto_aviso(estudiante, periodo, asignaturas, url_informe), [correo])
    except Exception as e:
        return False, f'no se pudo enviar ({type(e).__name__})'
    return True, correo
