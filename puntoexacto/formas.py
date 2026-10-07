# -*- coding: utf-8 -*-
"""PuntoExacto · formas del examen (A, B, C, D).

Una forma es el mismo examen con las preguntas y/o las opciones en otro orden.
Todo se califica sobre la forma A: lo que el estudiante marcó en su hoja se
traduce a «qué pregunta de la A y qué letra de la A» antes de guardarse.

Para que el lector de fotos no tenga que saber nada de formas, la hoja de
respuestas impresa es idéntica en todas: una pregunta solo puede cambiar de
lugar con otra que tenga el mismo número de opciones, las mismas etiquetas
(V/F…) y esté en el mismo bloque. Las opciones de una pregunta con etiquetas
propias (V/F, Sí/No) no se mezclan: «Falso, Verdadero» no tiene sentido.
"""
import random

from .models import LETRAS, Forma, Hoja, Respuesta, limpiar_rotulos

MAX_FORMAS = 4          # A + B, C, D


# ---------------------------------------------------------------------------
# Lo que puede cambiar de lugar con qué
# ---------------------------------------------------------------------------

def grupo(p):
    """Dos preguntas pueden intercambiar su lugar si tienen el mismo grupo."""
    return (p.bloque_id, p.opciones_efectivas(), tuple(limpiar_rotulos(p.rotulos)))


def se_mezclan_opciones(p):
    return not limpiar_rotulos(p.rotulos)


def identidad(preguntas):
    return [{'pregunta': p.numero, 'opciones': LETRAS[:p.opciones_efectivas()]}
            for p in preguntas]


def generar_orden(preguntas, mezclar_preguntas=True, mezclar_opciones=True, azar=None):
    """Un orden al azar que respeta los grupos. preguntas: en orden de número."""
    azar = azar or random.Random()
    orden = identidad(preguntas)
    if mezclar_preguntas:
        por_grupo = {}
        for i, p in enumerate(preguntas):
            por_grupo.setdefault(grupo(p), []).append(i)
        for posiciones in por_grupo.values():
            numeros = [preguntas[i].numero for i in posiciones]
            if len(numeros) > 1:
                barajados = numeros[:]
                # Que no salga igual a la A por casualidad.
                for _ in range(10):
                    azar.shuffle(barajados)
                    if barajados != numeros:
                        break
                numeros = barajados
            for i, n in zip(posiciones, numeros):
                orden[i]['pregunta'] = n
    if mezclar_opciones:
        por_numero = {p.numero: p for p in preguntas}
        for fila in orden:
            p = por_numero[fila['pregunta']]
            if se_mezclan_opciones(p):
                letras = list(LETRAS[:p.opciones_efectivas()])
                azar.shuffle(letras)
                fila['opciones'] = ''.join(letras)
    return orden


def problemas(orden, preguntas):
    """Qué está mal en un orden (lista de textos). Vacía = se puede usar."""
    salida = []
    if len(orden) != len(preguntas):
        salida.append(f'Tiene {len(orden)} preguntas y el examen tiene {len(preguntas)}.')
    por_numero = {p.numero: p for p in preguntas}
    usadas = {}
    for k, (fila, en_hoja) in enumerate(zip(orden, preguntas), start=1):
        n = fila.get('pregunta')
        p = por_numero.get(n)
        if p is None:
            salida.append(f'Pregunta {k}: la pregunta {n} no existe en la forma A.')
            continue
        if n in usadas:
            salida.append(f'La pregunta {n} de la A está repetida (en la {usadas[n]} y en la {k}).')
        usadas.setdefault(n, k)
        if grupo(p) != grupo(en_hoja):
            salida.append(f'Pregunta {k}: la {n} de la A no puede ir ahí '
                          f'(otro bloque, otro número de opciones u otras etiquetas).')
            continue
        letras = LETRAS[:p.opciones_efectivas()]
        ops = fila.get('opciones') or ''
        if sorted(ops) != sorted(letras):
            salida.append(f'Pregunta {k}: las opciones «{ops}» no son un orden de {letras}.')
        elif ops != letras and not se_mezclan_opciones(p):
            salida.append(f'Pregunta {k}: tiene etiquetas propias ({p.rotulos}); '
                          f'sus opciones no se mezclan.')
    return salida


def ajustar(orden, preguntas):
    """Arregla un orden que quedó desactualizado al cambiar la clave.

    Pasa al agregar o quitar preguntas, o al cambiar opciones o bloques. Lo que
    sigue sirviendo se respeta; lo que no, se llena con preguntas libres del
    mismo grupo (de preferencia la misma de la A). Devuelve (orden, cambió).
    """
    por_numero = {p.numero: p for p in preguntas}
    nuevo = [dict(f) for f in orden[:len(preguntas)]]
    nuevo += [dict(f) for f in identidad(preguntas[len(nuevo):])]

    usadas, malas = set(), []
    for k, (fila, en_hoja) in enumerate(zip(nuevo, preguntas)):
        p = por_numero.get(fila.get('pregunta'))
        if p is None or p.numero in usadas or grupo(p) != grupo(en_hoja):
            malas.append(k)
        else:
            usadas.add(p.numero)
    libres = [p for p in preguntas if p.numero not in usadas]
    for k in malas:
        en_hoja = preguntas[k]
        candidatas = [p for p in libres if grupo(p) == grupo(en_hoja)]
        p = en_hoja if en_hoja in candidatas else candidatas[0]
        libres.remove(p)
        nuevo[k] = {'pregunta': p.numero, 'opciones': ''}
    for fila in nuevo:
        p = por_numero[fila['pregunta']]
        letras = LETRAS[:p.opciones_efectivas()]
        ops = fila.get('opciones') or ''
        if sorted(ops) != sorted(letras) or not se_mezclan_opciones(p):
            fila['opciones'] = letras
    return nuevo, nuevo != orden


def ajustar_formas(examen):
    """Ajusta todas las formas tras cambiar la clave. Devuelve las letras que cambiaron."""
    preguntas = list(examen.preguntas.select_related('bloque', 'examen').order_by('numero'))
    cambiadas = []
    for f in examen.formas.all():
        nuevo, cambio = ajustar(f.orden, preguntas)
        if cambio:
            f.orden = nuevo
            f.save(update_fields=['orden'])
            cambiadas.append(f.letra)
    for letra in cambiadas:
        retraducir(letra, examen)
    return cambiadas


def orden_de(examen, letra, preguntas=None):
    """El orden de una forma, o la identidad para la A (o si la forma no existe)."""
    if preguntas is None:
        preguntas = list(examen.preguntas.order_by('numero'))
    if letra and letra != 'A':
        f = examen.formas.filter(letra=letra).first()
        if f is not None:
            return f.orden
    return identidad(preguntas)


# ---------------------------------------------------------------------------
# Traducir: hoja impresa <-> forma A
# ---------------------------------------------------------------------------

def a_forma_a(orden, posicion, marcada):
    """(posición en la hoja, letra marcada en la hoja) -> (número en la A, letra en la A).

    Si la fila no sirve (la forma quedó desactualizada) se deja tal cual.
    """
    fila = orden[posicion - 1] if 0 < posicion <= len(orden) else None
    if not fila:
        return posicion, marcada
    numero = fila.get('pregunta') or posicion
    if not marcada or marcada == Hoja.MARCA_DOBLE or marcada not in LETRAS:
        return numero, marcada
    i = LETRAS.index(marcada)
    ops = fila.get('opciones') or ''
    return numero, (ops[i] if i < len(ops) else marcada)


def letra_en_hoja(fila, letra_a):
    """La letra de la A -> la letra con que aparece en esta forma."""
    ops = fila.get('opciones') or ''
    if not letra_a or letra_a not in ops:
        return letra_a
    return LETRAS[ops.index(letra_a)]


def guardar_lectura(hoja, lectura, preguntas=None, orden=None):
    """Guarda lo marcado en la hoja y lo deja traducido a la forma A en Respuesta.

    lectura: {posición en la hoja (int o str): letra}. No califica.
    """
    examen = hoja.examen
    if preguntas is None:
        preguntas = list(examen.preguntas.order_by('numero'))
    if orden is None:
        orden = orden_de(examen, hoja.forma, preguntas)
    por_numero = {p.numero: p for p in preguntas}

    limpia = {}
    for clave, letra in (lectura or {}).items():
        try:
            pos = int(clave)
        except (TypeError, ValueError):
            continue
        en_hoja = por_numero.get(pos)
        if en_hoja is None:
            continue
        letra = (letra or '').strip().upper()[:1]
        if letra and letra != Hoja.MARCA_DOBLE and letra not in en_hoja.letras():
            letra = ''          # una letra que esa pregunta no tiene
        limpia[str(pos)] = letra

    hoja.respuestas.all().delete()
    nuevas, vistas = [], set()
    for clave, letra in limpia.items():
        numero, letra_a = a_forma_a(orden, int(clave), letra)
        p = por_numero.get(numero)
        if p is None or p.id in vistas:
            continue
        vistas.add(p.id)
        nuevas.append(Respuesta(hoja=hoja, pregunta=p, marcada=letra_a))
    Respuesta.objects.bulk_create(nuevas)
    hoja.lectura = limpia
    hoja.save(update_fields=['lectura', 'actualizada'])


def lectura_de(hoja, preguntas=None, orden=None):
    """Lo marcado en la hoja por posición. Si no se guardó, se reconstruye."""
    if hoja.lectura:
        return {str(k): v for k, v in hoja.lectura.items()}
    examen = hoja.examen
    if preguntas is None:
        preguntas = list(examen.preguntas.order_by('numero'))
    if orden is None:
        orden = orden_de(examen, hoja.forma, preguntas)
    marcadas = {r.pregunta.numero: r.marcada for r in hoja.respuestas.select_related('pregunta')}
    salida = {}
    for k, fila in enumerate(orden, start=1):
        letra_a = marcadas.get(fila.get('pregunta'), '')
        salida[str(k)] = letra_a if letra_a == Hoja.MARCA_DOBLE else letra_en_hoja(fila, letra_a)
    return salida


def clave_de(orden, preguntas):
    """La clave de una forma: [(posición, pregunta de la A, letra correcta en esta forma)]."""
    por_numero = {p.numero: p for p in preguntas}
    salida = []
    for k, fila in enumerate(orden, start=1):
        p = por_numero.get(fila.get('pregunta'))
        # «pendiente»: clave nueva en la que el docente aún no marcó esta respuesta.
        correcta = (letra_en_hoja(fila, p.correcta) if p and p.correcta
                    and not fila.get('pendiente') else '')
        ops = fila.get('opciones') or ''
        salida.append({'posicion': k, 'pregunta': p, 'correcta': correcta,
                       'pendiente': bool(fila.get('pendiente')),
                       'correcta_ver': p.rotulo(correcta) if p and correcta else '',
                       'anulada': bool(p and p.anulada),
                       'opciones': ops,
                       'mezcladas': ops != LETRAS[:len(ops)],
                       'opciones_ver': ' '.join(p.rotulo(o) for o in ops) if p else ops})
    return salida


def retraducir(forma_o_letra, examen):
    """Vuelve a traducir las hojas ya leídas de una forma (tras corregirla)."""
    from . import calificacion as calif
    letra = getattr(forma_o_letra, 'letra', forma_o_letra)
    preguntas = list(examen.preguntas.order_by('numero'))
    orden = orden_de(examen, letra, preguntas)
    n = 0
    for h in examen.hojas.filter(forma=letra):
        if not h.lectura:
            continue
        guardar_lectura(h, h.lectura, preguntas, orden)
        calif.calificar_hoja(h)
        n += 1
    return n


# ---------------------------------------------------------------------------
# Repartir formas entre las hojas
# ---------------------------------------------------------------------------

def letras_del_examen(examen):
    return ['A'] + list(examen.formas.values_list('letra', flat=True))


def siguiente_letra(examen):
    usadas = set(examen.formas.values_list('letra', flat=True))
    for letra in Forma.LETRAS_FORMA:
        if letra not in usadas:
            return letra
    return None


def nueva_clave(examen):
    """Crea la siguiente forma (B, C o D) en blanco, para marcarle su clave.

    Arranca con cada pregunta apuntando a la del mismo número en la A y sin
    respuesta marcada: el docente llena la clave de su examen B como llenó la
    de la A. Devuelve la Forma, o None si ya están las cuatro.
    """
    letra = siguiente_letra(examen)
    if letra is None:
        return None
    preguntas = list(examen.preguntas.order_by('numero'))
    orden = [dict(fila, pendiente=True) for fila in identidad(preguntas)]
    return Forma.objects.create(examen=examen, letra=letra, orden=orden)


def faltantes(orden):
    """Cuántas respuestas de la clave de una forma faltan por marcar."""
    return sum(1 for fila in orden if fila.get('pendiente'))


def marcar_clave(orden, preguntas, posicion, letra_correcta, numero_a=None):
    """Pone la respuesta correcta de una posición de la forma.

    Si la pregunta de la A no cambia y la letra ya era la correcta, se respeta
    el orden de opciones que tenía (por ejemplo, el que sorteó la plataforma).
    Si no, se arma un orden que la cumpla cambiando dos opciones de lugar.
    """
    por_numero = {p.numero: p for p in preguntas}
    fila = dict(orden[posicion - 1])
    numero = numero_a or fila.get('pregunta')
    p = por_numero.get(numero)
    if p is None:
        return fila
    letras_p = LETRAS[:p.opciones_efectivas()]
    if numero != fila.get('pregunta'):
        fila = {'pregunta': numero, 'opciones': letras_p}
    if not letra_correcta:
        fila['pendiente'] = True
        return fila
    fila.pop('pendiente', None)
    ops = fila.get('opciones') or letras_p
    if sorted(ops) != sorted(letras_p):
        ops = letras_p
    if not p.correcta or p.correcta not in ops or letra_correcta not in letras_p:
        fila['opciones'] = ops
        return fila
    if letra_en_hoja({'opciones': ops}, p.correcta) == letra_correcta:
        fila['opciones'] = ops
        return fila
    lista = list(letras_p)
    i, j = lista.index(letra_correcta), lista.index(p.correcta)
    lista[i], lista[j] = lista[j], lista[i]
    fila['opciones'] = ''.join(lista)
    return fila
