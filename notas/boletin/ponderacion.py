# notas/boletin/ponderacion.py
"""
El único sitio donde se decide cuánto vale cada periodo.

Lo usan el boletín y la sábana. Si algún día hay que cambiar la fórmula,
se cambia aquí y las dos pantallas quedan de acuerdo. Antes cada una hacía
su propio promedio y podían desincronizarse.
"""
from decimal import Decimal, ROUND_HALF_UP

# Los modelos se importan dentro de cada función, no aquí arriba: este módulo lo
# cargan las vistas, y un import de modelos en el encabezado obliga a que Django
# ya los tenga listos. ConfiguracionCalificaciones además no está exportado en
# notas/models/__init__.py, así que se toma del submódulo donde sí vive.

CERO = Decimal('0.0')
UN_DECIMAL = Decimal('0.1')


class AjustesPorDefecto:
    """Lo que rige cuando un colegio todavía no tiene configuración guardada."""
    ponderar_periodos = False
    exigir_periodos_completos = False
    pide_todos_los_periodos = False
    etiqueta_ser = 'SER'
    etiqueta_saber = 'SABER'
    etiqueta_hacer = 'HACER'
    abreviatura_ser = abreviatura_saber = abreviatura_hacer = ''
    colapsar_area_unica = True


def ajustes(colegio):
    """La configuración del colegio, o unos valores por defecto que no rompen nada."""
    from notas.models.academicos import ConfiguracionCalificaciones

    if colegio is None:
        return AjustesPorDefecto()
    config = ConfiguracionCalificaciones.objects.filter(colegio=colegio).first()
    return config or AjustesPorDefecto()


def pesos(colegio, periodos):
    """Cuánto vale cada periodo, ya normalizado para que la suma sea 1.

    Si el colegio no pondera, todos valen lo mismo. Si pondera pero los
    porcentajes no suman 100, se reparte proporcionalmente igual: así un error
    de digitación no multiplica las notas por un número raro.
    """
    periodos = list(periodos)
    if not periodos:
        return {}

    if not ajustes(colegio).ponderar_periodos:
        igual = Decimal(1) / Decimal(len(periodos))
        return {p.id: igual for p in periodos}

    crudos = {p.id: Decimal(getattr(p, 'peso_porcentual', 0) or 0) for p in periodos}
    total = sum(crudos.values())
    if total <= 0:
        igual = Decimal(1) / Decimal(len(periodos))
        return {p.id: igual for p in periodos}
    return {pid: peso / total for pid, peso in crudos.items()}


def definitiva_anual(colegio, notas_por_periodo, periodos, exigir=None):
    """La nota del año a partir de las notas de cada periodo.

    `notas_por_periodo` es {periodo_id: Decimal o None}.
    `exigir` fuerza o relaja la regla de "todos los periodos": la sábana en curso
    la relaja, porque ahí la columna es un avance y no la nota final.

    Devuelve (nota, faltantes):
      - nota es None cuando el colegio exige todos los periodos y falta alguno,
        o cuando no hay ninguna nota.
      - faltantes es la lista de periodos sin nota, para poder avisar.
    """
    periodos = list(periodos)
    reglas = ajustes(colegio)
    tabla = pesos(colegio, periodos)

    faltantes = [p for p in periodos if notas_por_periodo.get(p.id) is None]

    pide_todos = reglas.pide_todos_los_periodos if exigir is None else exigir
    if pide_todos and faltantes:
        return None, faltantes

    con_nota = [p for p in periodos if notas_por_periodo.get(p.id) is not None]
    if not con_nota:
        return None, faltantes

    # Se reparte el peso de los periodos ausentes entre los que sí tienen nota.
    peso_disponible = sum(tabla[p.id] for p in con_nota)
    if peso_disponible <= 0:
        return None, faltantes

    acumulado = sum(
        Decimal(notas_por_periodo[p.id]) * tabla[p.id] for p in con_nota
    )
    nota = (acumulado / peso_disponible).quantize(UN_DECIMAL, rounding=ROUND_HALF_UP)
    return nota, faltantes


def nota_aprobacion(colegio):
    """La nota mínima para no reprobar, según la escala del colegio.

    Toma el valor más bajo de la escala que no sea la más baja de todas —es
    decir, el piso de BÁSICO. Si el colegio no tiene escalas, usa 3.0.
    """
    from notas.models.academicos import EscalaValoracion

    escalas = list(EscalaValoracion.objects.filter(colegio=colegio).order_by('valor_minimo'))
    if len(escalas) >= 2:
        return escalas[1].valor_minimo
    return Decimal('3.0')


def rango_notas(colegio):
    """(mínima, máxima) de las notas según la escala que declaró el colegio; (1, 5) si no tiene."""
    from notas.models.academicos import EscalaValoracion

    filas = list(EscalaValoracion.objects.filter(colegio=colegio).values_list('valor_minimo', 'valor_maximo'))
    if not filas:
        return Decimal('1'), Decimal('5')
    return Decimal(min(a for a, _ in filas)), Decimal(max(b for _, b in filas))


def nota_maxima(colegio):
    from notas.models.academicos import EscalaValoracion

    escalas = list(EscalaValoracion.objects.filter(colegio=colegio).order_by('-valor_maximo'))
    return escalas[0].valor_maximo if escalas else Decimal('5.0')


def nota_necesaria(colegio, notas_por_periodo, periodos, periodo_objetivo, objetivo=None):
    """Qué nota necesita en `periodo_objetivo` para alcanzar `objetivo` en el año.

    Devuelve un diccionario:
      {'valor': Decimal|None, 'estado': 'ya'|'posible'|'imposible'|'sin_datos'}

    - 'ya'        : con lo que lleva, aunque saque cero, ya alcanza.
    - 'imposible' : ni con la nota máxima de la escala alcanza.
    - 'sin_datos' : faltan notas de periodos anteriores, no se puede proyectar.
    """
    periodos = list(periodos)
    objetivo = Decimal(objetivo) if objetivo is not None else nota_aprobacion(colegio)
    tabla = pesos(colegio, periodos)

    peso_objetivo = tabla.get(periodo_objetivo.id)
    if not peso_objetivo:
        return {'valor': None, 'estado': 'sin_datos'}

    anteriores = [p for p in periodos if p.id != periodo_objetivo.id]
    if any(notas_por_periodo.get(p.id) is None for p in anteriores):
        return {'valor': None, 'estado': 'sin_datos'}

    acumulado = sum(
        Decimal(notas_por_periodo[p.id]) * tabla[p.id] for p in anteriores
    ) if anteriores else CERO

    faltante = (objetivo - acumulado) / peso_objetivo
    faltante = faltante.quantize(UN_DECIMAL, rounding=ROUND_HALF_UP)

    if faltante <= CERO:
        return {'valor': CERO, 'estado': 'ya'}
    if faltante > nota_maxima(colegio):
        return {'valor': faltante, 'estado': 'imposible'}
    return {'valor': faltante, 'estado': 'posible'}
