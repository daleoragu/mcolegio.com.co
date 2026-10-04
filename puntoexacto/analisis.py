# -*- coding: utf-8 -*-
"""PuntoExacto · análisis del examen.

LA DIFERENCIA CON ZIPGRADE
ZipGrade calcula el "porcentaje de acierto" a partir de los PUNTOS. Si el
docente usa un esquema donde acertar vale cero —como el de descuento, donde
acertar solo evita un castigo— entonces reporta que nadie acertó nada, y el
análisis por pregunta queda inservible.

Aquí son dos cosas separadas:
  - si acertó o no  -> se compara con la clave. Sirve para el análisis.
  - cuántos puntos  -> sirve para la nota.

ÍNDICE DE DISCRIMINACIÓN
Mide si una pregunta la aciertan más los estudiantes a quienes mejor les fue
en todo el examen. Se compara el 27% de arriba contra el 27% de abajo (el
reparto clásico de Kelley, que maximiza la sensibilidad de la medida).
Un valor negativo significa que la aciertan MÁS los que peor van: la pregunta
está mal hecha o la clave está equivocada.
"""
from collections import defaultdict
from decimal import Decimal

PROPORCION_GRUPOS = Decimal('0.27')


def _interpretar_dificultad(p):
    if p >= 0.85:
        return 'Muy fácil'
    if p >= 0.60:
        return 'Fácil'
    if p >= 0.35:
        return 'Adecuada'
    if p >= 0.15:
        return 'Difícil'
    return 'Muy difícil'


def _interpretar_discriminacion(d):
    if d is None:
        return 'Pocos datos'
    if d < 0:
        return 'Revisar: la aciertan más los que peor van'
    if d < 0.20:
        return 'Discrimina poco'
    if d < 0.30:
        return 'Aceptable'
    if d < 0.40:
        return 'Buena'
    return 'Muy buena'


def analizar(examen):
    """Devuelve el análisis completo: por pregunta, por etiqueta y general."""
    preguntas = list(examen.preguntas.filter(anulada=False).order_by('numero'))
    hojas = list(examen.hojas.exclude(estado='ausente').prefetch_related('respuestas'))
    if not preguntas or not hojas:
        return {'preguntas': [], 'etiquetas': [], 'resumen': None, 'hojas': len(hojas)}

    # marcadas[hoja_id][pregunta_id] = letra marcada ('' si no marcó)
    marcadas = {h.id: {r.pregunta_id: r.marcada for r in h.respuestas.all()} for h in hojas}

    # Aciertos por hoja: se compara con la CLAVE, no con los puntos.
    aciertos_por_hoja = {}
    for h in hojas:
        m = marcadas[h.id]
        aciertos_por_hoja[h.id] = sum(
            1 for p in preguntas if m.get(p.id) and m[p.id] == p.correcta)

    orden = sorted(hojas, key=lambda h: aciertos_por_hoja[h.id], reverse=True)
    tamano = max(1, int(len(orden) * PROPORCION_GRUPOS))
    grupo_alto = {h.id for h in orden[:tamano]}
    grupo_bajo = {h.id for h in orden[-tamano:]}
    hay_grupos = len(orden) >= 6 and not (grupo_alto & grupo_bajo)

    filas = []
    for p in preguntas:
        reparto = defaultdict(int)
        correctas = altos = bajos = 0
        for h in hojas:
            marca = marcadas[h.id].get(p.id) or '—'
            reparto[marca] += 1
            if marca == p.correcta:
                correctas += 1
                if h.id in grupo_alto:
                    altos += 1
                if h.id in grupo_bajo:
                    bajos += 1

        dificultad = correctas / len(hojas)
        discriminacion = None
        if hay_grupos:
            discriminacion = (altos / tamano) - (bajos / tamano)

        # La opción equivocada que más gente escogió: ahí suele haber un error
        # conceptual concreto, no un despiste.
        distractores = sorted(
            ((op, n) for op, n in reparto.items() if op != p.correcta and op != '—'),
            key=lambda x: -x[1])
        filas.append({
            'numero': p.numero, 'correcta': p.correcta,
            'etiquetas': p.lista_etiquetas(),
            'correctas': correctas, 'total': len(hojas),
            'dificultad': round(dificultad * 100, 1),
            'lectura_dificultad': _interpretar_dificultad(dificultad),
            'discriminacion': round(discriminacion, 3) if discriminacion is not None else None,
            'lectura_discriminacion': _interpretar_discriminacion(discriminacion),
            'reparto': [{'opcion': op, 'n': n, 'pct': round(n * 100 / len(hojas), 1)}
                        for op, n in sorted(reparto.items(), key=lambda x: -x[1])],
            'distractor_fuerte': distractores[0] if distractores else None,
            'en_blanco': reparto.get('—', 0),
        })

    # Por etiqueta: agrupa las preguntas que evalúan lo mismo.
    por_etiqueta = defaultdict(lambda: {'preguntas': [], 'correctas': 0, 'posibles': 0})
    for p, fila in zip(preguntas, filas):
        for et in p.lista_etiquetas():
            d = por_etiqueta[et]
            d['preguntas'].append(p.numero)
            d['correctas'] += fila['correctas']
            d['posibles'] += fila['total']
    etiquetas = [
        {'etiqueta': et, 'preguntas': d['preguntas'],
         'porcentaje': round(d['correctas'] * 100 / d['posibles'], 1) if d['posibles'] else 0}
        for et, d in sorted(por_etiqueta.items())
    ]
    etiquetas.sort(key=lambda e: e['porcentaje'])

    notas = [h.nota for h in hojas if h.nota is not None]
    resumen = None
    if notas:
        ordenadas = sorted(notas)
        mitad = len(ordenadas) // 2
        mediana = (ordenadas[mitad] if len(ordenadas) % 2
                   else (ordenadas[mitad - 1] + ordenadas[mitad]) / 2)
        promedio = sum(notas) / len(notas)
        resumen = {
            'hojas': len(hojas), 'calificadas': len(notas),
            'minima': min(notas), 'maxima': max(notas),
            'promedio': round(promedio, 2), 'mediana': round(mediana, 2),
            'aprobados': sum(1 for n in notas if n >= examen.nota_minima + (
                (examen.nota_maxima - examen.nota_minima) / 2)),
        }

    return {'preguntas': filas, 'etiquetas': etiquetas, 'resumen': resumen,
            'hojas': len(hojas), 'grupos_validos': hay_grupos}
