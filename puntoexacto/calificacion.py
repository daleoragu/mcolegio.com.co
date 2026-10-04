# -*- coding: utf-8 -*-
"""PuntoExacto · cómo un examen se convierte en nota.

La lógica pura vive en funciones que reciben datos sencillos, para poder
probarlas sin base de datos. Las de abajo solo traducen de los modelos a esos
datos y de vuelta.
"""
from decimal import Decimal, ROUND_HALF_UP

CENTESIMA = Decimal('0.01')


# ---------------------------------------------------------------------------
# Lógica pura
# ---------------------------------------------------------------------------

def acotar(valor, minima, maxima):
    """Ninguna nota se sale de la escala. Devuelve (nota, se_recortó)."""
    if valor < minima:
        return minima, True
    if valor > maxima:
        return maxima, True
    return valor, False


def nota_desde_puntaje(obtenido, posible, maxima, minima, metodo,
                       castigo=Decimal('0')):
    """El puntaje crudo, convertido a nota según el método elegido."""
    if posible <= 0:
        return minima
    if metodo == 'proporcional':
        return (obtenido / posible) * maxima
    if metodo == 'con_piso':
        return (obtenido / posible) * (maxima - minima) + minima
    if metodo == 'descuento':
        return maxima - castigo
    raise ValueError(f'Método de calificación desconocido: {metodo}')


def equilibrio_de_azar(por_error, por_blanco, opciones):
    """Desde qué confianza le conviene al estudiante arriesgar, y si eso está bien.

    Dejar en blanco cuesta `por_blanco` seguro; contestar cuesta `por_error`
    solo si falla. Arriesgar conviene cuando (1 - q) x por_error < por_blanco.
    El punto justo es que ese umbral coincida con el azar puro, 1/opciones:
    así adivinar a lo loco no premia ni castiga.
    """
    azar = Decimal(1) / Decimal(opciones)
    if por_error <= 0:
        return {'umbral': Decimal('0'), 'azar': azar, 'equilibrado': False,
                'veredicto': 'El error no se castiga: siempre conviene contestar.'}
    umbral = Decimal(1) - (por_blanco / por_error)
    neutra = (por_blanco * Decimal(opciones) / Decimal(opciones - 1)
              if opciones > 1 else por_blanco)
    if abs(umbral - azar) < Decimal('0.01'):
        veredicto = 'Adivinar queda neutro. Es el punto justo.'
    elif umbral > azar:
        veredicto = ('Se castiga el intento: al estudiante que duda le conviene dejar en '
                     f'blanco. Para dejarlo neutro, el error debería restar {neutra.quantize(CENTESIMA)}.')
    else:
        veredicto = ('Se premia adivinar al azar. Para dejarlo neutro, el error debería '
                     f'restar {neutra.quantize(CENTESIMA)}.')
    return {'umbral': umbral, 'azar': azar,
            'equilibrado': abs(umbral - azar) < Decimal('0.01'),
            'por_error_neutra': neutra, 'veredicto': veredicto}


# ---------------------------------------------------------------------------
# Puente con los modelos
# ---------------------------------------------------------------------------

def calificar_hoja(hoja, preguntas=None, guardar=True):
    """Califica una hoja y devuelve el detalle de cómo salió."""
    examen = hoja.examen
    if preguntas is None:
        preguntas = list(examen.preguntas.filter(anulada=False))
    marcadas = {r.pregunta_id: r.marcada for r in hoja.respuestas.all()}

    posible = sum(p.puntos for p in preguntas) or Decimal('0')
    obtenido = Decimal('0')
    buenas = parciales = malas = blancas = dobles = 0
    castigo = Decimal('0')
    pen = examen.penalizaciones()

    for p in preguntas:
        marcada = marcadas.get(p.id, '')
        fr = p.fraccion(marcada)
        obtenido += p.puntos * fr
        if not marcada:
            blancas += 1
            castigo += pen['por_blanco']
        else:
            castigo += pen['por_error'] * (Decimal('1') - fr)
            if marcada == hoja.MARCA_DOBLE:
                dobles += 1
            elif fr == 1:
                buenas += 1
            elif fr > 0:
                parciales += 1
            else:
                malas += 1

    bruto = nota_desde_puntaje(obtenido, posible, examen.nota_maxima,
                               examen.nota_minima, examen.metodo, castigo)
    nota, recortada = acotar(bruto, examen.nota_minima, examen.nota_maxima)
    nota = nota.quantize(CENTESIMA, ROUND_HALF_UP)

    if guardar:
        hoja.nota = nota
        hoja.nota_recortada = recortada
        if hoja.estado == 'pendiente':
            hoja.estado = 'revisar' if dobles else 'calificada'
        hoja.save(update_fields=['nota', 'nota_recortada', 'estado', 'actualizada'])

    aviso = None
    if recortada:
        aviso = (f'La nota calculada fue {bruto.quantize(CENTESIMA)} y se ajustó a {nota} '
                 f'para no salirse de la escala.')

    return {
        'nota': nota, 'bruto': bruto.quantize(CENTESIMA), 'recortada': recortada,
        'aviso': aviso, 'obtenido': obtenido.quantize(CENTESIMA), 'posible': posible,
        'buenas': buenas, 'parciales': parciales, 'malas': malas,
        'blancas': blancas, 'dobles': dobles,
    }


def calificar_examen(examen):
    """Recalifica todas las hojas. Se usa al cambiar la clave o anular una pregunta."""
    preguntas = list(examen.preguntas.filter(anulada=False))
    hojas = examen.hojas.exclude(estado='ausente').prefetch_related('respuestas')
    return [calificar_hoja(h, preguntas=preguntas) for h in hojas]


def revisar_configuracion(examen):
    """Avisos que el docente debería ver antes de aplicar el examen."""
    avisos = []
    preguntas = list(examen.preguntas.all())
    vigentes = [p for p in preguntas if not p.anulada]

    sin_clave = [p.numero for p in vigentes if not p.correcta]
    if sin_clave:
        avisos.append('Faltan respuestas en la clave: preguntas '
                      + ', '.join(str(n) for n in sin_clave) + '.')

    total = sum(p.puntos for p in vigentes)
    if total > examen.nota_maxima:
        avisos.append(f'Los puntos suman {total} y la nota máxima es {examen.nota_maxima}. '
                      f'Baje el puntaje de algunas preguntas.')
    elif vigentes and total < examen.nota_maxima and examen.metodo != 'con_piso':
        avisos.append(f'Los puntos suman {total}, menos que la nota máxima '
                      f'{examen.nota_maxima}: un examen perfecto no llegaría a la máxima.')

    letras = examen.letras
    for p in vigentes:
        if p.correcta and p.correcta not in letras:
            avisos.append(f'Pregunta {p.numero}: la respuesta "{p.correcta}" no existe; '
                          f'las opciones son {letras}.')
        for opcion, valor in (p.parciales or {}).items():
            if opcion == p.correcta:
                avisos.append(f'Pregunta {p.numero}: "{opcion}" es la correcta y además '
                              f'aparece como parcial. Sobra.')
            try:
                v = Decimal(str(valor))
            except Exception:
                avisos.append(f'Pregunta {p.numero}: el parcial de "{opcion}" no es un número.')
                continue
            if v <= 0 or v >= 1:
                avisos.append(f'Pregunta {p.numero}: el parcial de "{opcion}" es {v}; '
                              f'debe estar entre 0 y 1.')

    if examen.metodo == 'descuento' and vigentes:
        pen = examen.penalizaciones()
        eq = equilibrio_de_azar(pen['por_error'], pen['por_blanco'], examen.numero_opciones)
        if not eq['equilibrado']:
            avisos.append('Con el método por descuento: ' + eq['veredicto'])
    return avisos


# ---------------------------------------------------------------------------
# Repartir la nota entre los componentes de la planilla
# ---------------------------------------------------------------------------

def notas_por_componente(examen, hoja, preguntas=None):
    """La nota de una hoja, separada por componente (SER, SABER, HACER).

    Un mismo examen puede evaluar SABER en unas preguntas y HACER en otras. Cada
    componente se califica solo con SUS preguntas, con el mismo método y la misma
    escala del examen. Así cada columna de la planilla refleja lo que de verdad
    se evaluó ahí, en vez de repetir la misma nota en las tres.
    """
    if preguntas is None:
        preguntas = list(examen.preguntas.filter(anulada=False))
    marcadas = {r.pregunta_id: r.marcada for r in hoja.respuestas.all()}
    pen = examen.penalizaciones()

    grupos = {}
    for p in preguntas:
        grupos.setdefault(p.componente or examen.componente, []).append(p)

    salida = {}
    for componente, lista in grupos.items():
        posible = sum(p.puntos for p in lista) or Decimal('0')
        obtenido = Decimal('0')
        castigo = Decimal('0')
        for p in lista:
            marcada = marcadas.get(p.id, '')
            fr = p.fraccion(marcada)
            obtenido += p.puntos * fr
            if not marcada:
                castigo += pen['por_blanco']
            else:
                castigo += pen['por_error'] * (Decimal('1') - fr)

        if examen.metodo == 'descuento':
            # El descuento parte de la máxima; al repartirlo por componente hay
            # que repartir también el castigo, si no cada parte arrancaría de
            # cero preguntas y daría siempre la máxima.
            bruto = examen.nota_maxima - castigo
        else:
            bruto = nota_desde_puntaje(obtenido, posible, examen.nota_maxima,
                                       examen.nota_minima, examen.metodo)
        nota, _ = acotar(bruto, examen.nota_minima, examen.nota_maxima)
        salida[componente] = {
            'nota': nota.quantize(CENTESIMA, ROUND_HALF_UP),
            'preguntas': [p.numero for p in lista],
            'obtenido': obtenido.quantize(CENTESIMA), 'posible': posible,
        }
    return salida


def notas_por_bloque(examen, hoja, preguntas=None):
    """La nota de una hoja, separada por bloque (Lenguaje, Matemáticas…).

    Es la misma idea de notas_por_componente, pero agrupando por área en vez de
    por componente. Cada bloque se califica SOLO con sus preguntas y con la
    escala del examen, así que un estudiante que va bien en Matemáticas y mal
    en Lenguaje queda con dos notas distintas y no con un promedio que esconde
    las dos cosas.

    Devuelve {bloque_id: {...}}. Las preguntas sin bloque quedan bajo None.
    """
    if preguntas is None:
        preguntas = list(examen.preguntas.filter(anulada=False))
    marcadas = {r.pregunta_id: r.marcada for r in hoja.respuestas.all()}
    pen = examen.penalizaciones()

    grupos = {}
    for p in preguntas:
        grupos.setdefault(p.bloque_id, []).append(p)

    salida = {}
    for bloque_id, lista in grupos.items():
        posible = sum(p.puntos for p in lista) or Decimal('0')
        obtenido = Decimal('0')
        castigo = Decimal('0')
        correctas = 0
        for p in lista:
            marcada = marcadas.get(p.id, '')
            fr = p.fraccion(marcada)
            obtenido += p.puntos * fr
            if fr == 1:
                correctas += 1
            if not marcada:
                castigo += pen['por_blanco']
            else:
                castigo += pen['por_error'] * (Decimal('1') - fr)

        if examen.metodo == 'descuento':
            bruto = examen.nota_maxima - castigo
        else:
            bruto = nota_desde_puntaje(obtenido, posible, examen.nota_maxima,
                                       examen.nota_minima, examen.metodo)
        nota, recortada = acotar(bruto, examen.nota_minima, examen.nota_maxima)
        salida[bloque_id] = {
            'nota': nota.quantize(CENTESIMA, ROUND_HALF_UP),
            'recortada': recortada,
            'correctas': correctas, 'total': len(lista),
            'obtenido': obtenido.quantize(CENTESIMA), 'posible': posible,
            'preguntas': [p.numero for p in lista],
        }
    return salida
