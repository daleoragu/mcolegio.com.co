# notas/componentes.py
"""Componentes de evaluación del colegio: cuántos son, cómo se llaman y cuánto pesa cada uno.

Antes la plataforma tenía fijos tres (SER, SABER, HACER). Ahora cada colegio
tiene los suyos (de 1 en adelante) en ComponenteEvaluacion. Todo lo que
necesite saberlo (planillas, ingreso de notas, boletín, PuntoExacto) pregunta
aquí y no da por hecho que son tres.

Códigos: los tres de siempre conservan SER, SABER y HACER (las notas guardadas
los usan); los nuevos son C4, C5… El código no cambia aunque cambie el nombre.

Porcentajes: por materia (o por asignación, si el colegio deja que el docente
los cambie) en pesos_componentes = {código: porcentaje}. Los tres de siempre se
copian también en porcentaje_ser/saber/hacer, así nada viejo queda descuadrado.
Con «ponderación equitativa» todos pesan lo mismo (100 / N).
"""
from decimal import ROUND_DOWN, Decimal

from .models.academicos import (CODIGOS_COMPONENTE, CODIGOS_LEGADO, Calificacion, ComponenteEvaluacion,
                                ConfiguracionCalificaciones)

NOMBRES_DEFECTO = {'SER': 'SER', 'SABER': 'SABER', 'HACER': 'HACER'}
PESOS_DEFECTO = {'SER': 30, 'SABER': 40, 'HACER': 30}
CIEN = Decimal('100')


# ---------------------------------------------------------------------------
# Cuáles hay
# ---------------------------------------------------------------------------

def componentes(colegio):
    """Los componentes del colegio, en orden. La primera vez se crean los tres de siempre
    con los nombres que el colegio ya tuviera configurados."""
    if colegio is None:
        return [ComponenteEvaluacion(codigo=c, nombre=c, orden=i) for i, c in enumerate(CODIGOS_LEGADO, 1)]
    lista = list(ComponenteEvaluacion.objects.filter(colegio=colegio).order_by('orden', 'id'))
    if lista:
        return lista
    config = ConfiguracionCalificaciones.objects.filter(colegio=colegio).first()
    for i, codigo in enumerate(CODIGOS_LEGADO, start=1):
        nombre = (getattr(config, f'etiqueta_{codigo.lower()}', '') or codigo).strip() if config else codigo
        abrev = (getattr(config, f'abreviatura_{codigo.lower()}', '') or '').strip() if config else ''
        ComponenteEvaluacion.objects.get_or_create(colegio=colegio, codigo=codigo,
                                                   defaults={'nombre': nombre or codigo, 'abreviatura': abrev,
                                                             'orden': i})
    return list(ComponenteEvaluacion.objects.filter(colegio=colegio).order_by('orden', 'id'))


def codigos(colegio):
    return [c.codigo for c in componentes(colegio)]


def codigos_libres(colegio):
    """Códigos que puede tomar un componente nuevo, en orden.

    No se reusa un código que el colegio ya tenga, ni uno que tenga notas
    guardadas de cualquier año: así un componente nuevo nunca hereda notas
    viejas de otro que se quitó.
    """
    usados = set(ComponenteEvaluacion.objects.filter(colegio=colegio).values_list('codigo', flat=True))
    con_notas = set(Calificacion.objects.filter(colegio=colegio, tipo_nota__in=CODIGOS_COMPONENTE)
                    .values_list('tipo_nota', flat=True).distinct())
    return [c for c in CODIGOS_COMPONENTE if c not in usados and c not in con_notas]


def siguiente_codigo(colegio):
    libres = codigos_libres(colegio)
    return libres[0] if libres else None


def nombre(colegio, codigo, materia=None):
    """El nombre del componente. Una materia puede tener nombre propio para los tres de siempre."""
    if materia is not None and codigo in CODIGOS_LEGADO:
        propio = (getattr(materia, f'etiqueta_{codigo.lower()}', '') or '').strip()
        if propio and propio.upper() != codigo:
            return propio
    for c in componentes(colegio):
        if c.codigo == codigo:
            return c.nombre
    return codigo


# ---------------------------------------------------------------------------
# Cuánto pesa cada uno
# ---------------------------------------------------------------------------

def reparto_igual(n):
    """[33.33, 33.33, 33.34] para 3; [100] para 1. Siempre suma 100."""
    if n <= 0:
        return []
    base = (CIEN / n).quantize(Decimal('0.01'), rounding=ROUND_DOWN)
    return [base] * (n - 1) + [CIEN - base * (n - 1)]


def _guardado(fuente, codigo):
    datos = getattr(fuente, 'pesos_componentes', None) or {}
    if codigo in datos:
        try:
            return Decimal(str(datos[codigo]))
        except Exception:
            return Decimal('0')
    if codigo in CODIGOS_LEGADO:
        return Decimal(getattr(fuente, f'porcentaje_{codigo.lower()}', 0) or 0)
    return Decimal('0')


def pesos_de(fuente, lista_codigos):
    """{código: porcentaje} de una materia o asignación, para esos componentes."""
    if getattr(fuente, 'usar_ponderacion_equitativa', False):
        return dict(zip(lista_codigos, reparto_igual(len(lista_codigos))))
    return {c: _guardado(fuente, c) for c in lista_codigos}


def suma_pesos(fuente):
    colegio = getattr(fuente, 'colegio', None)
    return sum(pesos_de(fuente, codigos(colegio)).values()) if colegio is not None else Decimal('0')


def pesos(asignacion):
    """{código: porcentaje} que rigen para la asignación, en el orden del colegio.

    Si el colegio deja que el docente cambie los porcentajes, mandan los de la
    asignación; si no, los de la materia.
    """
    colegio = asignacion.colegio
    config = ConfiguracionCalificaciones.objects.filter(colegio=colegio).first()
    # Con permiso, la asignación manda solo si el docente ya puso sus porcentajes
    # (al guardarlos queda usar_ponderacion_equitativa=False). Mientras tanto
    # —y así quedan las asignaciones nuevas o importadas— sigue los de la materia.
    propios = config and config.docente_puede_modificar and not asignacion.usar_ponderacion_equitativa
    fuente = asignacion if propios else asignacion.materia
    return pesos_de(fuente, codigos(colegio))


def fijar_pesos(obj, valores, equitativa=None):
    """Guarda {código: porcentaje} en una materia o asignación (sin llamar save)."""
    limpios = {}
    for c, v in (valores or {}).items():
        try:
            limpios[c] = int(Decimal(str(v)))
        except Exception:
            limpios[c] = 0
    obj.pesos_componentes = limpios
    for c in CODIGOS_LEGADO:
        setattr(obj, f'porcentaje_{c.lower()}', limpios.get(c, 0))
    if equitativa is not None:
        obj.usar_ponderacion_equitativa = equitativa


# ---------------------------------------------------------------------------
# Quitar un componente
# ---------------------------------------------------------------------------

def notas_del_componente(colegio, codigo, ano=None):
    """Cuántas calificaciones con notas tiene ese componente en el año, y en qué materias."""
    from .models.academicos import PeriodoAcademico
    from django.db.models import Max
    if ano is None:
        ano = PeriodoAcademico.objects.filter(colegio=colegio).aggregate(m=Max('ano_lectivo'))['m']
    qs = (Calificacion.objects.filter(colegio=colegio, tipo_nota=codigo, notas_detalladas__isnull=False)
          .distinct())
    if ano is not None:
        qs = qs.filter(periodo__ano_lectivo=ano)
    materias = sorted(set(qs.values_list('materia__nombre', flat=True)))
    return qs.count(), materias, ano


# ---------------------------------------------------------------------------
# Cambiar los componentes del colegio
# ---------------------------------------------------------------------------

def _repartir(valores, total):
    """Reparte `total` (entero) entre las claves de `valores` en proporción a ellos."""
    claves = list(valores)
    if not claves:
        return {}
    base = sum(valores.values())
    if base <= 0:
        valores = {c: 1 for c in claves}
        base = len(claves)
    crudos = {c: Decimal(valores[c]) * total / base for c in claves}
    enteros = {c: int(crudos[c]) for c in claves}
    sobra = total - sum(enteros.values())
    for c in sorted(claves, key=lambda c: crudos[c] - enteros[c], reverse=True)[:sobra]:
        enteros[c] += 1
    return enteros


def reajustar_pesos(colegio, antes, despues):
    """Después de quitar o agregar componentes, que los porcentajes sigan sumando 100.

    Lo que pesaban los componentes quitados se reparte entre los que quedan,
    en proporción a lo que ya pesaban. Los nuevos empiezan en 0 % (el colegio
    les pone porcentaje en «Permisos de porcentajes»). Las asignaturas con
    ponderación equitativa no se tocan: se reparten solas.
    """
    from .models.academicos import AsignacionDocente, Materia
    quitados = [c for c in antes if c not in despues]
    cambiados = 0
    for modelo in (Materia, AsignacionDocente):
        for obj in modelo.objects.filter(colegio=colegio, usar_ponderacion_equitativa=False):
            actuales = {c: int(_guardado(obj, c)) for c in antes}
            quedan = {c: actuales.get(c, 0) for c in despues}
            total = sum(actuales.values())
            if quitados and total > 0:
                quedan_viejos = {c: v for c, v in quedan.items() if c in antes}
                # Si no queda ninguno de los de antes, se reparte igual entre los nuevos.
                quedan.update(_repartir(quedan_viejos or quedan, total))
            fijar_pesos(obj, quedan)
            obj.save(update_fields=['pesos_componentes', 'porcentaje_ser', 'porcentaje_saber', 'porcentaje_hacer'])
            cambiados += 1
    return cambiados


def sincronizar_configuracion(colegio):
    """Los nombres de SER, SABER y HACER también quedan en ConfiguracionCalificaciones
    (lo leen partes viejas de la plataforma)."""
    config, _ = ConfiguracionCalificaciones.objects.get_or_create(colegio=colegio)
    por_codigo = {c.codigo: c for c in componentes(colegio)}
    campos = []
    for codigo in CODIGOS_LEGADO:
        comp = por_codigo.get(codigo)
        k = codigo.lower()
        setattr(config, f'etiqueta_{k}', comp.nombre if comp else codigo)
        setattr(config, f'abreviatura_{k}', comp.abreviatura if comp else '')
        campos += [f'etiqueta_{k}', f'abreviatura_{k}']
    config.save(update_fields=campos)
