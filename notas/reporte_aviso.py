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


def _escala_de(colegio, asignacion):
    """(escalas, materia_id, grado) para la asignación; sin asignación, la escala del colegio."""
    from . import escalas
    esc = escalas.de(colegio)
    if asignacion is None:
        return esc, None, None
    return esc, asignacion.materia_id, asignacion.curso.grado


def esta_en_bajo(colegio, nota, asignacion=None):
    esc, materia_id, grado = _escala_de(colegio, asignacion)
    if esc.es_especial(materia_id, grado):
        return esc.pierde(nota, materia_id, grado)
    return nota is not None and nota < nota_aprobacion(colegio)


def desempeno(colegio, nota, asignacion=None):
    if nota is None:
        return ''
    esc, materia_id, grado = _escala_de(colegio, asignacion)
    nivel = esc.nivel_de(esc.niveles(materia_id, grado), nota)
    if nivel is None and not esc.es_especial(materia_id, grado):
        # Como antes: el primer rango del colegio que la contenga.
        e = EscalaValoracion.objects.filter(colegio=colegio, valor_minimo__lte=nota, valor_maximo__gte=nota).first()
        return e.nombre_desempeno.upper() if e else ''
    return nivel.nombre_desempeno.upper() if nivel else ''


def texto_nota(nota):
    return str(nota).replace('.', ',') if nota is not None else ''


def asignaturas_reportadas(estudiante, periodo):
    """[(materia, docente, nota parcial)] de lo reportado con dificultades en el periodo."""
    reportes = (ReporteParcial.objects.filter(estudiante=estudiante, periodo=periodo, presenta_dificultades=True)
                .select_related('asignacion__materia', 'asignacion__docente__user', 'asignacion__curso')
                .order_by('asignacion__materia__nombre'))
    salida = []
    for r in reportes:
        nota = notas_parciales(r.asignacion, periodo, [estudiante]).get(estudiante.id)
        salida.append({'materia': r.asignacion.materia.nombre,
                       'docente': r.asignacion.docente.user.get_full_name() if r.asignacion.docente_id else '',
                       'nota': nota, 'nota_texto': texto_nota(nota),
                       'desempeno': desempeno(estudiante.colegio, nota, r.asignacion),
                       'sugerencia': (r.sugerencia or '').strip()})
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
    pendientes = [f'- {a["materia"]}: {a["sugerencia"]}' for a in asignaturas if a.get('sugerencia')]
    if pendientes:
        texto += '\nLo que le recomiendan los docentes para mejorar:\n' + '\n'.join(pendientes)
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


def avisar_estudiantes_al_cierre(periodo):
    """Al cerrarse el plazo del reporte parcial, cada estudiante con dificultades recibe el aviso (y al celular).

    Antes del cierre el estudiante no ve nada: los docentes todavía pueden estar llenándolo. Devuelve cuántos avisos."""
    from django.db.models import Count
    from django.urls import reverse
    from .models import Notificacion
    filas = (ReporteParcial.objects.filter(periodo=periodo, presenta_dificultades=True, estudiante__is_active=True)
             .values('estudiante_id', 'estudiante__user_id').annotate(n=Count('id')))
    avisos = []
    for f in filas:
        n = f['n']
        url = reverse('notas:acta_reporte_parcial_estudiante', args=[f['estudiante_id']]) + f'?periodo_id={periodo.id}'
        avisos.append(Notificacion(
            colegio=periodo.colegio, destinatario_id=f['estudiante__user_id'], tipo='RENDIMIENTO', url=url,
            mensaje=(f'Ya puede ver su informe parcial del {periodo.get_nombre_display().lower()}: '
                     f'presenta dificultades en {n} asignatura{"s" if n != 1 else ""}.')[:255]))
    Notificacion.objects.bulk_create(avisos)
    return len(avisos)


def visible_para_estudiante(periodo):
    """El estudiante solo ve el reporte parcial de un periodo cuando su plazo ya se cerró."""
    return not periodo.reporte_parcial_activo
