# notas/planillas/pdf.py
"""La planilla de notas en PDF: la misma información del Excel y de la planilla
en línea (columnas con nombre, promedio por componente, final, desempeño y
fallas), lista para imprimir y firmar."""
from decimal import Decimal, ROUND_HALF_UP

from django.template.loader import render_to_string
from django.utils import timezone

from ..models.academicos import InasistenciasManualesPeriodo
from .columnas import configuracion, plan_completo
from .excel import escala_del_colegio, estudiantes_de
from .guardar import CENTESIMA


def _desempeno(nota, escala):
    # Con el valor que se imprime (una décima): 4.54 sale «4,5» y debe decir ALTO,
    # aunque la escala salte de 4.5 a 4.6.
    nota = nota.quantize(Decimal('0.1'), rounding=ROUND_HALF_UP)
    for desde, hasta, nombre in escala:
        if desde <= nota <= hasta:
            return nombre
    return ''


def datos_planilla(colegio, periodo, asignacion, config=None, escala=None):
    """Todo lo de una asignación, listo para dibujar."""
    config = config or configuracion(colegio)
    escala = escala or escala_del_colegio(colegio)
    estudiantes = estudiantes_de(asignacion, periodo)
    plan = plan_completo(asignacion, periodo, estudiantes, config)
    fallas = dict(InasistenciasManualesPeriodo.objects.filter(
        asignacion=asignacion, periodo=periodo, estudiante__in=estudiantes)
        .values_list('estudiante_id', 'cantidad'))

    componentes = [{'codigo': c, 'nombre': d['nombre'], 'peso': format(Decimal(d['peso']).normalize(), 'f'),
                    'columnas': d['columnas']} for c, d in plan.items()]
    filas = []
    for i, est in enumerate(estudiantes, start=1):
        celdas, total, alguna = [], Decimal('0'), False
        for codigo, d in plan.items():
            valores = d['valores'].get(est.id, [None] * len(d['columnas']))
            valores = list(valores) + [None] * (len(d['columnas']) - len(valores))
            validas = [v for v in valores if v is not None]
            prom = (sum(validas) / len(validas)).quantize(CENTESIMA, rounding=ROUND_HALF_UP) if validas else None
            if validas:
                alguna = True
                total += prom * Decimal(d['peso']) / 100
            celdas.append({'notas': valores, 'promedio': prom})
        final = total.quantize(CENTESIMA, rounding=ROUND_HALF_UP) if alguna else None
        filas.append({
            'n': i, 'nombre': f'{est.user.last_name} {est.user.first_name}'.strip().upper() or est.user.username,
            'componentes': celdas, 'final': final,
            'desempeno': _desempeno(final, escala) if final is not None else '',
            'fallas': fallas.get(est.id, ''), 'inclusion': getattr(est, 'es_inclusion', False),
        })
    total_columnas = sum(len(c['columnas']) + 1 for c in componentes)
    return {'asignacion': asignacion, 'componentes': componentes, 'filas': filas,
            'total_columnas': total_columnas,
            'docente': asignacion.docente.user.get_full_name() if asignacion.docente_id else ''}


def generar(request, colegio, periodo, asignaciones):
    """Bytes del PDF con una página (o más) por asignación."""
    from weasyprint import HTML
    config = configuracion(colegio)
    escala = escala_del_colegio(colegio)
    planillas = [datos_planilla(colegio, periodo, a, config, escala) for a in asignaciones]
    html = render_to_string('notas/planillas/planilla_notas_pdf.html', {
        'colegio': colegio, 'periodo': periodo, 'planillas': planillas, 'escala': escala,
        'generado': timezone.localtime(),
    })
    return HTML(string=html, base_url=request.build_absolute_uri('/')).write_pdf()
