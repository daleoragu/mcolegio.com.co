"""Qué escala de valoración rige una nota: la del colegio o una escala especial.

Un colegio puede tener escalas especiales para algunas materias (Inglés con el
BAJO hasta 3.4) y, si quiere, solo en algunos grados (Matemáticas de 10.° y
11.°). Todas las pantallas preguntan aquí, con la materia y el grado, en vez de
leer EscalaValoracion directamente.

Precedencia para una materia en un grado:
  1. la escala especial que tiene esa materia y nombra ese grado;
  2. la escala especial que tiene esa materia sin grados (todos los grados);
  3. la escala del colegio.

Las notas de un área usan la escala especial solo si todas sus materias en ese
grado tienen la misma; si no, la del colegio.

Dentro de `ponderacion.en_lote()` las escalas se leen una sola vez.
"""
from decimal import Decimal

APROBACION_POR_DEFECTO = Decimal('3.0')


def _grado(grado):
    try:
        return int(grado) if grado is not None and grado != '' else None
    except (TypeError, ValueError):
        return None


class Escalas:
    def __init__(self, colegio):
        from .models import EscalaEspecial, EscalaValoracion

        self.colegio = colegio
        self.general = list(EscalaValoracion.objects.filter(colegio=colegio).order_by('valor_minimo')) \
            if colegio is not None else []
        self._exacta = {}    # (materia_id, grado) -> niveles
        self._todas = {}     # materia_id -> niveles
        self.especiales = []
        if colegio is None:
            return
        for esp in EscalaEspecial.objects.filter(colegio=colegio).prefetch_related('niveles', 'materias'):
            niveles = sorted(esp.niveles.all(), key=lambda n: n.valor_minimo)
            if not niveles:
                continue
            esp.lista_niveles = niveles
            self.especiales.append(esp)
            grados = [g for g in (_grado(x) for x in (esp.grados or [])) if g is not None]
            for m in esp.materias.all():
                if grados:
                    for g in grados:
                        self._exacta.setdefault((m.id, g), niveles)
                else:
                    self._todas.setdefault(m.id, niveles)

    # -- qué escala --------------------------------------------------------
    def hay_especiales(self):
        return bool(self.especiales)

    def niveles(self, materia_id=None, grado=None):
        """Los niveles (de menor a mayor) que rigen esa materia en ese grado."""
        if materia_id is not None and (self._exacta or self._todas):
            g = _grado(grado)
            if g is not None and (materia_id, g) in self._exacta:
                return self._exacta[(materia_id, g)]
            if materia_id in self._todas:
                return self._todas[materia_id]
        return self.general

    def es_especial(self, materia_id=None, grado=None):
        return self.niveles(materia_id, grado) is not self.general

    def niveles_area(self, materia_ids, grado=None):
        """La escala del área: la especial si todas sus materias comparten la misma."""
        materia_ids = [m for m in materia_ids if m is not None]
        if not materia_ids:
            return self.general
        escalas = [self.niveles(m, grado) for m in materia_ids]
        primera = escalas[0]
        if all(e is primera for e in escalas):
            return primera
        return self.general

    # -- con la nota -------------------------------------------------------
    @staticmethod
    def nivel_de(niveles, nota):
        if nota is None:
            return None
        nota = Decimal(nota)
        cumplen = [n for n in niveles if n.valor_minimo is not None and n.valor_maximo is not None
                   and n.valor_minimo <= nota <= n.valor_maximo]
        # Misma regla de siempre: vale solo si exactamente un rango contiene la nota.
        return cumplen[0] if len(cumplen) == 1 else None

    @staticmethod
    def aprobacion_de(niveles):
        """El piso del segundo nivel (BÁSICO): por debajo se pierde."""
        if len(niveles) >= 2:
            return niveles[1].valor_minimo
        return APROBACION_POR_DEFECTO

    def desempeno(self, nota, materia_id=None, grado=None, niveles=None):
        """Nombre del desempeño en mayúsculas, o '' si no hay nota."""
        if nota is None:
            return ''
        niveles = niveles if niveles is not None else self.niveles(materia_id, grado)
        n = self.nivel_de(niveles, nota)
        if n is not None:
            return n.nombre_desempeno.upper()
        # Sin rango que la contenga: la regla fija de siempre (3.0) para la escala del colegio;
        # en una escala especial, su propio piso de aprobación.
        piso = APROBACION_POR_DEFECTO if niveles is self.general else self.aprobacion_de(niveles)
        return _desempeno_sin_escala(nota, piso)

    def mensaje(self, nota, materia_id=None, grado=None):
        n = self.nivel_de(self.niveles(materia_id, grado), nota)
        return (getattr(n, 'mensaje_boletin', '') or '') if n else ''

    def aprobacion(self, materia_id=None, grado=None, niveles=None):
        return self.aprobacion_de(niveles if niveles is not None else self.niveles(materia_id, grado))

    def pierde(self, nota, materia_id=None, grado=None, niveles=None):
        return nota is not None and Decimal(nota) < self.aprobacion(materia_id, grado, niveles)

    def en_bajo(self, nota, materia_id=None, grado=None, niveles=None):
        """La nota cae en el nivel más bajo de su escala (lo que se pinta en rojo)."""
        if nota is None:
            return False
        niveles = niveles if niveles is not None else self.niveles(materia_id, grado)
        n = self.nivel_de(niveles, nota)
        return n is not None and bool(niveles) and n is niveles[0]

    def nombres(self):
        """Los desempeños de la escala del colegio, de mayor a menor (encabezados de conteos)."""
        return [n.nombre_desempeno.upper() for n in reversed(self.general)]

    def nombre_bajo(self, niveles=None):
        niveles = niveles if niveles is not None else self.general
        return niveles[0].nombre_desempeno.upper() if niveles else 'BAJO'


def _desempeno_sin_escala(nota, aprobacion):
    nota = Decimal(nota)
    if nota >= Decimal('4.6'):
        return 'SUPERIOR'
    if nota >= Decimal('4.0'):
        return 'ALTO'
    if nota >= aprobacion:
        return 'BASICO'
    return 'BAJO'


def de(colegio):
    """Las escalas del colegio; dentro de `en_lote()` se leen una sola vez."""
    from .boletin.ponderacion import recordar
    return recordar(('escalas_v2', getattr(colegio, 'pk', None)), lambda: Escalas(colegio))


# ---------------------------------------------------------------------------
# Validación de una escala especial (la pantalla de configuración la usa)
# ---------------------------------------------------------------------------
def validar_especial(colegio, materias_ids, grados, niveles, excluir_pk=None):
    """Lista de errores en palabras; vacía si todo está bien.

    `niveles` = [(nombre, minimo, maximo)] con Decimal. `grados` = [int], vacía = todos.
    """
    from .models import EscalaEspecial

    errores = []
    if not niveles:
        errores.append('La escala necesita al menos dos desempeños.')
    elif len(niveles) < 2:
        errores.append('La escala necesita al menos dos desempeños (por ejemplo BAJO y BÁSICO).')
    nombres = [n.strip().upper() for n, _, _ in niveles]
    if len(set(nombres)) != len(nombres):
        errores.append('Hay desempeños con el mismo nombre.')
    for nombre, a, b in niveles:
        if a is None or b is None:
            errores.append(f'«{nombre}» necesita nota mínima y máxima.')
        elif a >= b:
            errores.append(f'En «{nombre}» la nota mínima debe ser menor que la máxima.')
    ordenados = sorted([n for n in niveles if n[1] is not None and n[2] is not None], key=lambda n: n[1])
    for (n1, _, b1), (n2, a2, _) in zip(ordenados, ordenados[1:]):
        if a2 <= b1:
            errores.append(f'Los rangos de «{n1}» y «{n2}» se cruzan.')
    if not materias_ids:
        errores.append('Escoja al menos una materia.')

    # Una materia en un grado no puede quedar con dos escalas especiales.
    grados = set(grados or [])
    otras = EscalaEspecial.objects.filter(colegio=colegio, materias__id__in=materias_ids).distinct() \
        .prefetch_related('materias')
    if excluir_pk:
        otras = otras.exclude(pk=excluir_pk)
    for otra in otras:
        g_otra = set(int(g) for g in (otra.grados or []))
        # Las dos para todos los grados, o grados en común. Una para todos y otra para grados
        # puntuales sí se permite: la de grados puntuales manda en esos grados.
        cruce = bool(grados & g_otra) if (grados and g_otra) else (not grados and not g_otra)
        if cruce:
            comunes = [m.nombre for m in otra.materias.all() if m.id in set(materias_ids)]
            errores.append(f'{", ".join(comunes)} ya tiene la escala «{otra.nombre}» en esos grados.')
    return errores
