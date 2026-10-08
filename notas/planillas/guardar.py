# notas/planillas/guardar.py
"""Guardar las notas de un estudiante y calcular su definitiva del periodo.

Es la regla que usaba la planilla en línea, sacada aquí para que la subida
del Excel la use tal cual. Si mañana cambia la forma de calcular, cambia en
un solo lugar y la planilla en línea y el Excel siguen dando lo mismo.

La regla:
  * Una nota vale si está dentro de la escala de valoración del colegio (de 1 a
    5 si no ha declarado ninguna). Las demás (vacías, fuera de rango, texto) no se
    guardan.
  * El promedio de cada componente es el de sus notas válidas, a 2 decimales;
    sin notas, 0.
  * La definitiva es la suma de cada promedio por su porcentaje, a 2 decimales.
  * Un componente con 0 % no se toca.
"""
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from ..models.academicos import Calificacion, InasistenciasManualesPeriodo, NotaDetallada
from .. import componentes as _comp

# Solo para cuando no hay colegio a mano; lo normal es rango(colegio).
MINIMA = Decimal('1')
MAXIMA = Decimal('5')


def rango(colegio):
    """(mínima, máxima) de la escala que declaró el colegio."""
    if colegio is None:
        return MINIMA, MAXIMA
    from ..boletin.ponderacion import rango_notas
    return rango_notas(colegio)
CENTESIMA = Decimal('0.01')


def a_decimal(valor):
    """'4,5' -> Decimal('4.5'); lo que no sea número -> None."""
    if valor is None:
        return None
    if isinstance(valor, (int, float, Decimal)) and not isinstance(valor, bool):
        try:
            return Decimal(str(valor))
        except InvalidOperation:
            return None
    texto = str(valor).strip().replace(',', '.')
    if not texto:
        return None
    try:
        return Decimal(texto)
    except InvalidOperation:
        return None


LARGO_OBSERVACION = 600


def limpiar_observacion(texto):
    """Sin espacios de sobra y con un tope razonable para el boletín."""
    return ' '.join(str(texto or '').split())[:LARGO_OBSERVACION]


def es_nota_valida(valor, limites=None):
    minima, maxima = limites or (MINIMA, MAXIMA)
    v = a_decimal(valor)
    return v is not None and minima <= v <= maxima


def guardar_componente(colegio, estudiante, asignacion, periodo, codigo, notas, limites=None):
    """Reemplaza las notas de un componente y devuelve su promedio.

    notas: [{'descripcion': 'Taller 1', 'valor': '4,5'}, …] o [(desc, valor), …]
    """
    cal, _ = Calificacion.objects.get_or_create(
        colegio=colegio, estudiante=estudiante, materia=asignacion.materia, periodo=periodo,
        tipo_nota=codigo, defaults={'valor_nota': Decimal('0.0'), 'docente': asignacion.docente})
    cal.notas_detalladas.all().delete()
    minima, maxima = limites or rango(colegio)

    nuevas, total = [], Decimal('0')
    for n in notas:
        desc, valor = (n.get('descripcion'), n.get('valor')) if isinstance(n, dict) else n
        v = a_decimal(valor)
        if v is None or not (minima <= v <= maxima):
            continue
        nuevas.append(NotaDetallada(colegio=colegio, calificacion_promedio=cal,
                                    descripcion=(str(desc or '').strip() or f'Nota {len(nuevas) + 1}')[:100],
                                    valor_nota=v))
        total += v
    if nuevas:
        NotaDetallada.objects.bulk_create(nuevas)
        promedio = total / len(nuevas)
    else:
        promedio = Decimal('0')
    cal.valor_nota = promedio.quantize(CENTESIMA, rounding=ROUND_HALF_UP)
    cal.save()
    return cal.valor_nota


def guardar_estudiante(colegio, asignacion, periodo, estudiante, notas_por_componente,
                       inasistencias=None, observacion_inclusion=None, observacion=None):
    """Guarda todo lo de un estudiante y devuelve su definitiva del periodo.

    notas_por_componente: {código: [...]} con los componentes del colegio (las
    claves también pueden venir en minúscula, como las manda la planilla en línea).
    observacion: texto libre de la asignatura; None = no se toca (el Excel no la trae).
    """
    por_codigo = {k.upper(): v for k, v in (notas_por_componente or {}).items()}
    definitiva = Decimal('0')
    limites = rango(colegio)
    for codigo, porcentaje in _comp.pesos(asignacion).items():
        peso = Decimal(porcentaje) / Decimal(100)
        if peso <= 0:
            continue
        promedio = guardar_componente(colegio, estudiante, asignacion, periodo, codigo,
                                      por_codigo.get(codigo, []), limites)
        definitiva += promedio * peso

    defaults = {'valor_nota': definitiva.quantize(CENTESIMA, rounding=ROUND_HALF_UP),
                'docente': asignacion.docente}
    if observacion_inclusion is not None:
        defaults['observacion_inclusion'] = observacion_inclusion
    if observacion is not None:
        defaults['observacion'] = limpiar_observacion(observacion)
    definitiva_obj, _ = Calificacion.objects.update_or_create(
        colegio=colegio, estudiante=estudiante, materia=asignacion.materia, periodo=periodo,
        tipo_nota='PROM_PERIODO', defaults=defaults)
    if definitiva_obj.observacion_inclusion is None:      # el boletín espera texto, no NULL
        Calificacion.objects.filter(pk=definitiva_obj.pk).update(observacion_inclusion='')

    if inasistencias is not None:
        try:
            cantidad = max(0, int(Decimal(str(inasistencias).strip() or '0')))
        except (InvalidOperation, ValueError):
            cantidad = 0
        InasistenciasManualesPeriodo.objects.update_or_create(
            colegio=colegio, estudiante=estudiante, asignacion=asignacion, periodo=periodo,
            defaults={'cantidad': cantidad})
    return defaults['valor_nota']
