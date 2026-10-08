# notas/planillas/columnas.py
"""Qué columnas de notas tiene cada componente y dónde va cada nota.

Las notas se guardan en NotaDetallada con su descripción («Taller 1») y sin
huecos: si un estudiante no tiene la nota 2, su lista es [nota 1, nota 3].
Por eso una nota NO se ubica por su posición en la lista (eso corría la nota
3 a la columna 2) sino por su descripción, contra el plan de notas.
"""
from collections import Counter, OrderedDict
from decimal import Decimal

from ..models.academicos import (Calificacion, ConfiguracionCalificaciones, NotaDetallada,
                                  PlanNotas)

# Los componentes ya no son fijos: cada colegio tiene los suyos (notas/componentes.py).
from .. import componentes as _comp  # noqa: E402
LARGO_MAXIMO = 60   # NotaDetallada.descripcion admite 100; 60 se lee en un encabezado
TOPE_COLUMNAS = 15


def configuracion(colegio):
    config, _ = ConfiguracionCalificaciones.objects.get_or_create(colegio=colegio)
    return config


def nombre_componente(asignacion, codigo, config=None):
    """Cómo se llama el componente: el de la materia (si tiene nombre propio) o el del colegio."""
    return _comp.nombre(asignacion.colegio, codigo, asignacion.materia)


def peso_componente(asignacion, codigo):
    """Porcentaje del componente (Decimal, 0–100), el mismo que usa la plataforma."""
    return Decimal(_comp.pesos(asignacion).get(codigo, 0))


def componentes_activos(asignacion, config=None):
    """[(codigo, nombre, peso%)] de los componentes del colegio que cuentan (peso > 0), en su orden."""
    salida = []
    for codigo, peso in _comp.pesos(asignacion).items():
        if peso > 0:
            salida.append((codigo, nombre_componente(asignacion, codigo), Decimal(peso)))
    return salida


def limpiar_columnas(nombres, cantidad=None):
    """Nombres listos para usar: sin espacios de sobra, cortos y sin vacíos.

    Un nombre vacío se llena con «Nota N». Si se pide una cantidad, se
    completa o se recorta a esa cantidad.
    """
    salida = []
    for i, n in enumerate(nombres or []):
        n = ' '.join(str(n or '').split())[:LARGO_MAXIMO]
        salida.append(n or f'Nota {i + 1}')
    if cantidad is not None:
        cantidad = max(1, min(TOPE_COLUMNAS, int(cantidad)))
        usados = set(salida)
        k = len(salida)
        while len(salida) < cantidad:
            k += 1
            nombre = f'Nota {k}'
            while nombre in usados:
                k += 1
                nombre = f'Nota {k}'
            salida.append(nombre)
            usados.add(nombre)
        salida = salida[:cantidad]
    return salida


def notas_guardadas(asignacion, periodo, codigo, estudiantes=None):
    """{estudiante_id: [(descripcion, valor Decimal), …]} en el orden en que se guardaron."""
    qs = NotaDetallada.objects.filter(
        calificacion_promedio__materia=asignacion.materia,
        calificacion_promedio__periodo=periodo,
        calificacion_promedio__tipo_nota=codigo,
        calificacion_promedio__colegio=asignacion.colegio,
    ).select_related('calificacion_promedio').order_by('id')
    if estudiantes is not None:
        qs = qs.filter(calificacion_promedio__estudiante__in=estudiantes)
    salida = {}
    for n in qs:
        salida.setdefault(n.calificacion_promedio.estudiante_id, []).append((n.descripcion, n.valor_nota))
    return salida


def _columnas_de_las_notas(por_estudiante):
    """Las columnas que se deducen de notas ya guardadas, en su orden natural.

    Cada descripción va en la posición más temprana en que alguien la usó, y
    aparece tantas veces como el estudiante que más veces la repite (hay notas
    viejas con dos «Nota 1»).
    """
    primera_posicion = {}
    veces = Counter()
    for notas in por_estudiante.values():
        cuenta = Counter()
        for i, (desc, _) in enumerate(notas):
            cuenta[desc] += 1
            clave = (desc, cuenta[desc])
            primera_posicion[clave] = min(primera_posicion.get(clave, i), i)
        for desc, n in cuenta.items():
            veces[desc] = max(veces[desc], n)
    claves = [(d, k) for d, n in veces.items() for k in range(1, n + 1)]
    claves.sort(key=lambda c: (primera_posicion.get(c, 999), c[1]))
    return [d for d, _ in claves]


def columnas_del_plan(asignacion, periodo, codigo, por_estudiante=None, config=None):
    """Las columnas de un componente, ya resueltas.

    1. El plan del docente, si lo hizo.
    2. Si no, las que se deducen de las notas ya guardadas.
    3. Si no hay nada, «Nota 1…N» con N = el número por defecto del colegio.
    Siempre se agregan al final las notas guardadas cuyo nombre no está en el
    plan: así reducir el plan nunca esconde una nota que ya existe.
    """
    if por_estudiante is None:
        por_estudiante = notas_guardadas(asignacion, periodo, codigo)
    plan = PlanNotas.objects.filter(asignacion=asignacion, periodo=periodo, componente=codigo).first()
    if plan and plan.columnas:
        columnas = limpiar_columnas(plan.columnas)
    else:
        # Sin plan: las que ya tienen notas, completadas hasta el número que
        # fijó el colegio (si el docente no elige, sale el de por defecto).
        config = config or configuracion(asignacion.colegio)
        deducidas = _columnas_de_las_notas(por_estudiante)
        columnas = limpiar_columnas(deducidas, max(len(deducidas), config.notas_por_componente))
    # Notas cuyo nombre no cabe en el plan: van al final, sin perderse.
    faltan = Counter()
    for notas in por_estudiante.values():
        restantes = Counter(columnas)
        sobra = Counter()
        for desc, _ in notas:
            if restantes[desc] > 0:
                restantes[desc] -= 1
            else:
                sobra[desc] += 1
        for d, n in sobra.items():
            faltan[d] = max(faltan[d], n)
    for d, n in faltan.items():
        columnas.extend([d] * n)
    return columnas


def ubicar(notas, columnas):
    """Pone cada nota en su columna según su descripción. Devuelve [valor|None, …]."""
    valores = [None] * len(columnas)
    libres = OrderedDict()
    for i, c in enumerate(columnas):
        libres.setdefault(c, []).append(i)
    sin_lugar = []
    for desc, valor in notas:
        if libres.get(desc):
            valores[libres[desc].pop(0)] = valor
        else:
            sin_lugar.append(valor)
    # Por si acaso: lo que no encontró su nombre ocupa el primer hueco libre.
    for valor in sin_lugar:
        for i, v in enumerate(valores):
            if v is None:
                valores[i] = valor
                break
    return valores


def guardar_plan(asignacion, periodo, codigo, columnas):
    columnas = limpiar_columnas(columnas)[:TOPE_COLUMNAS] or limpiar_columnas([], 1)
    plan, _ = PlanNotas.objects.update_or_create(
        asignacion=asignacion, periodo=periodo, componente=codigo,
        defaults={'columnas': columnas, 'colegio': asignacion.colegio})
    return plan


def plan_completo(asignacion, periodo, estudiantes=None, config=None):
    """Todo lo que necesita una planilla: por componente, sus columnas y las notas ubicadas.

    {codigo: {'nombre', 'peso', 'columnas': [...], 'valores': {est_id: [v|None,…]}}}
    """
    config = config or configuracion(asignacion.colegio)
    salida = OrderedDict()
    for codigo, nombre, peso in componentes_activos(asignacion, config):
        por_est = notas_guardadas(asignacion, periodo, codigo, estudiantes)
        columnas = columnas_del_plan(asignacion, periodo, codigo, por_est, config)
        salida[codigo] = {
            'nombre': nombre, 'peso': peso, 'columnas': columnas,
            'valores': {eid: ubicar(n, columnas) for eid, n in por_est.items()},
        }
    return salida
