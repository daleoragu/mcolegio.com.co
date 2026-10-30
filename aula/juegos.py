"""Cuestionarios estilo Quizizz (a su ritmo) y Kahoot (en vivo), y la nota de las actividades HTML."""
import random
import re
from datetime import timedelta
from decimal import Decimal, ROUND_HALF_UP

from django.db import transaction
from django.utils import timezone

from . import logica
from .models import Intento, OpcionQ, PreguntaQ, RespuestaQ, ResultadoActividad, SesionVivo

UN_DECIMAL = Decimal('0.1')
GRACIA_MS = 1500            # lo que tarda la respuesta en llegar por internet
PUNTOS_MAX = 1000


# ---------------------------------------------------------------------------
# Puntos y nota
# ---------------------------------------------------------------------------
def puntos(correcta, ms, segundos):
    """Como Kahoot: 1000 si responde al instante, 500 si responde en el último segundo, 0 si falla."""
    if not correcta:
        return 0
    fraccion = min(1, max(0, ms / (segundos * 1000)))
    return round(PUNTOS_MAX * (1 - fraccion / 2))


def nota(aula, aciertos, total):
    minima, maxima = logica.rango(aula)
    if not total:
        return None
    return (minima + (maxima - minima) * Decimal(aciertos) / Decimal(total)).quantize(UN_DECIMAL, rounding=ROUND_HALF_UP)


def nota_de_puntaje(aula, puntaje, maximo):
    """La nota de una actividad HTML que manda «puntaje de máximo» (por ejemplo 8 de 10)."""
    minima, maxima = logica.rango(aula)
    puntaje, maximo = Decimal(str(puntaje)), Decimal(str(maximo))
    if maximo <= 0:
        raise ValueError('máximo inválido')
    fraccion = min(Decimal(1), max(Decimal(0), puntaje / maximo))
    return (minima + (maxima - minima) * fraccion).quantize(UN_DECIMAL, rounding=ROUND_HALF_UP)


def guardar_resultado_actividad(actividad, persona, valor):
    filtro = logica.filtro_persona(persona)
    r = ResultadoActividad.objects.filter(actividad=actividad, **filtro).first()
    if r is None:
        return ResultadoActividad.objects.create(actividad=actividad, nota=valor, ultima=valor, **filtro)
    r.ultima = valor
    r.nota = max(r.nota, valor)
    r.intentos += 1
    r.save()
    return r


# ---------------------------------------------------------------------------
# Preguntas: importar en formato Aiken (el que generan las IA y Moodle)
# ---------------------------------------------------------------------------
_OPCION = re.compile(r'^\s*(\*)?\s*([A-Ha-h])[\)\.\-:]\s+(.+)$')
_RESPUESTA = re.compile(r'^\s*(ANSWER|RESPUESTA|CORRECTA)\s*[:=]\s*([A-Ha-h])\s*$', re.I)


def leer_aiken(texto):
    """[(pregunta, [(opción, correcta)])] desde texto como:

        ¿Cuánto es 2 + 3?
        A) 4
        B) 5
        ANSWER: B

    También sirve marcar la correcta con asterisco: «*B) 5». Las preguntas se separan
    con una línea en blanco o con la línea de la respuesta.
    """
    preguntas, actual, opciones, correcta = [], [], [], None

    def cerrar():
        nonlocal actual, opciones, correcta
        if actual and opciones:
            ops = [(t, (correcta == letra) or marcada) for letra, t, marcada in opciones]
            if any(c for _, c in ops):
                preguntas.append((' '.join(actual).strip(), ops))
        actual, opciones, correcta = [], [], None

    for linea in (texto or '').splitlines():
        if not linea.strip():
            if opciones:
                cerrar()
            continue
        m = _RESPUESTA.match(linea)
        if m:
            correcta = m.group(2).upper()
            cerrar()
            continue
        m = _OPCION.match(linea)
        if m and actual:
            opciones.append((m.group(2).upper(), m.group(3).strip()[:300], bool(m.group(1))))
            continue
        if opciones:
            cerrar()
        actual.append(linea.strip())
    cerrar()
    return preguntas


@transaction.atomic
def guardar_preguntas(cuestionario, preguntas):
    """Reemplaza las preguntas. preguntas: [(texto, [(opción, correcta)], segundos|None)]."""
    cuestionario.preguntas.all().delete()
    for i, item in enumerate(preguntas):
        texto, opciones = item[0], item[1]
        segundos = item[2] if len(item) > 2 else None
        p = PreguntaQ.objects.create(cuestionario=cuestionario, orden=i, texto=texto[:2000], segundos=segundos)
        OpcionQ.objects.bulk_create([OpcionQ(pregunta=p, texto=t[:300], correcta=c, orden=k)
                                     for k, (t, c) in enumerate(opciones[:6])])


def _orden(cuestionario):
    ids = list(cuestionario.preguntas.values_list('id', flat=True))
    if cuestionario.mezclar:
        random.shuffle(ids)
    return ids


def _pregunta_json(p, con_correcta=False):
    datos = {'id': p.id, 'texto': p.texto, 'segundos': p.tiempo,
             'opciones': [{'id': o.id, 'texto': o.texto} for o in p.opciones.all()]}
    if con_correcta:
        datos['correcta'] = [o.id for o in p.opciones.all() if o.correcta]
    return datos


# ---------------------------------------------------------------------------
# A su ritmo (Quizizz)
# ---------------------------------------------------------------------------
def intento_abierto(cuestionario, persona):
    return Intento.objects.filter(cuestionario=cuestionario, sesion__isnull=True, terminado__isnull=True,
                                  **logica.filtro_persona(persona)).first()


def puede_iniciar(cuestionario, persona):
    if not cuestionario.a_su_ritmo or not cuestionario.preguntas.exists():
        return False
    if cuestionario.reintentos:
        return True
    return not Intento.objects.filter(cuestionario=cuestionario, sesion__isnull=True, terminado__isnull=False,
                                      **logica.filtro_persona(persona)).exists()


def iniciar(cuestionario, persona):
    abierto = intento_abierto(cuestionario, persona)
    if abierto:
        return abierto
    return Intento.objects.create(cuestionario=cuestionario, orden=_orden(cuestionario), actual=0,
                                  inicio_pregunta=timezone.now(), **logica.filtro_persona(persona))


def estado_intento(intento):
    if intento.terminado or intento.actual >= len(intento.orden):
        return {'fin': True, 'puntos': intento.puntos, 'aciertos': intento.aciertos, 'total': len(intento.orden),
                'nota': str(intento.nota) if intento.nota is not None else None}
    p = PreguntaQ.objects.prefetch_related('opciones').get(pk=intento.orden[intento.actual])
    transcurrido = (timezone.now() - intento.inicio_pregunta).total_seconds() if intento.inicio_pregunta else 0
    datos = _pregunta_json(p)
    datos.update({'fin': False, 'numero': intento.actual + 1, 'total': len(intento.orden), 'puntos': intento.puntos,
                  'restante': max(0, round(p.tiempo - transcurrido, 1))})
    return datos


@transaction.atomic
def responder(intento, pregunta_id, opcion_id):
    intento = Intento.objects.select_for_update().get(pk=intento.pk)
    if intento.terminado or intento.actual >= len(intento.orden) or intento.orden[intento.actual] != pregunta_id:
        return {'error': 'Esa pregunta ya pasó.'}
    p = PreguntaQ.objects.prefetch_related('opciones').get(pk=pregunta_id)
    ms = int((timezone.now() - intento.inicio_pregunta).total_seconds() * 1000)
    opcion = next((o for o in p.opciones.all() if o.id == opcion_id), None)
    a_tiempo = ms <= p.tiempo * 1000 + GRACIA_MS
    correcta = bool(opcion and opcion.correcta and a_tiempo)
    pts = puntos(correcta, ms, p.tiempo)
    RespuestaQ.objects.create(intento=intento, pregunta=p, opcion=opcion if a_tiempo else None, correcta=correcta,
                              milisegundos=ms, puntos=pts)
    intento.puntos += pts
    intento.aciertos += 1 if correcta else 0
    intento.actual += 1
    intento.inicio_pregunta = timezone.now()
    if intento.actual >= len(intento.orden):
        intento.terminado = timezone.now()
        intento.nota = nota(intento.cuestionario.aula, intento.aciertos, len(intento.orden))
    intento.save()
    return {'correcta': correcta, 'correctas': [o.id for o in p.opciones.all() if o.correcta], 'puntos': pts,
            'total_puntos': intento.puntos, 'a_tiempo': a_tiempo}


# ---------------------------------------------------------------------------
# En vivo (Kahoot)
# ---------------------------------------------------------------------------
def sesion_activa(cuestionario):
    return cuestionario.sesiones.exclude(estado='fin').filter(
        creada__gte=timezone.now() - timedelta(hours=3)).first()


def nueva_sesion(cuestionario):
    cuestionario.sesiones.exclude(estado='fin').update(estado='fin')
    return SesionVivo.objects.create(cuestionario=cuestionario, orden=_orden(cuestionario))


def unirse(sesion, persona):
    intento, _ = Intento.objects.get_or_create(
        cuestionario=sesion.cuestionario, sesion=sesion, **logica.filtro_persona(persona),
        defaults={'orden': sesion.orden})
    return intento


@transaction.atomic
def avanzar(sesion):
    """Espera/resultado -> siguiente pregunta (o fin); pregunta -> resultado."""
    sesion = SesionVivo.objects.select_for_update().get(pk=sesion.pk)
    if sesion.estado == 'pregunta':
        sesion.estado = 'resultado'
    elif sesion.estado in ('espera', 'resultado'):
        sesion.indice += 1
        if sesion.indice >= len(sesion.orden):
            sesion.estado = 'fin'
            total = len(sesion.orden)
            for it in sesion.intentos.all():
                it.terminado = timezone.now()
                it.nota = nota(sesion.cuestionario.aula, it.aciertos, total)
                it.save(update_fields=['terminado', 'nota'])
        else:
            sesion.estado = 'pregunta'
            sesion.inicio_pregunta = timezone.now()
    sesion.save()
    return sesion


@transaction.atomic
def responder_vivo(sesion, intento, opcion_id):
    sesion = SesionVivo.objects.get(pk=sesion.pk)
    if sesion.estado != 'pregunta':
        return {'error': 'Ya no se puede responder.'}
    p = PreguntaQ.objects.prefetch_related('opciones').get(pk=sesion.orden[sesion.indice])
    if RespuestaQ.objects.filter(intento=intento, pregunta=p).exists():
        return {'error': 'Ya respondió.'}
    ms = int((timezone.now() - sesion.inicio_pregunta).total_seconds() * 1000)
    if ms > p.tiempo * 1000 + GRACIA_MS:
        return {'error': 'Se acabó el tiempo.'}
    opcion = next((o for o in p.opciones.all() if o.id == opcion_id), None)
    correcta = bool(opcion and opcion.correcta)
    pts = puntos(correcta, ms, p.tiempo)
    RespuestaQ.objects.create(intento=intento, pregunta=p, opcion=opcion, correcta=correcta, milisegundos=ms,
                              puntos=pts)
    from django.db.models import F
    Intento.objects.filter(pk=intento.pk).update(puntos=F('puntos') + pts,
                                                 aciertos=F('aciertos') + (1 if correcta else 0))
    return {'ok': True}


def ranking(sesion, n=5):
    return [{'nombre': i.nombre, 'puntos': i.puntos} for i in
            sesion.intentos.select_related('estudiante__user', 'integrante').order_by('-puntos', 'id')[:n]]


def estado_sesion(sesion, intento=None, docente=False):
    sesion.refresh_from_db()
    datos = {'estado': sesion.estado, 'numero': sesion.indice + 1, 'total': len(sesion.orden),
             'jugadores': sesion.intentos.count()}
    if sesion.estado == 'espera':
        datos['nombres'] = [i.nombre for i in sesion.intentos.select_related('estudiante__user', 'integrante')]
    if sesion.estado in ('pregunta', 'resultado') and 0 <= sesion.indice < len(sesion.orden):
        p = PreguntaQ.objects.prefetch_related('opciones').get(pk=sesion.orden[sesion.indice])
        transcurrido = (timezone.now() - sesion.inicio_pregunta).total_seconds()
        datos['pregunta'] = _pregunta_json(p, con_correcta=sesion.estado == 'resultado')
        datos['restante'] = max(0, round(p.tiempo - transcurrido, 1))
        respuestas = RespuestaQ.objects.filter(intento__sesion=sesion, pregunta=p)
        datos['respondidas'] = respuestas.count()
        if sesion.estado == 'resultado':
            conteo = {o.id: 0 for o in p.opciones.all()}
            for r in respuestas:
                if r.opcion_id in conteo:
                    conteo[r.opcion_id] += 1
            datos['conteo'] = conteo
            datos['ranking'] = ranking(sesion)
        if intento is not None:
            mia = respuestas.filter(intento=intento).first()
            datos['respondio'] = mia is not None
            if sesion.estado == 'resultado':
                datos['mi_correcta'] = bool(mia and mia.correcta)
                datos['mis_puntos'] = mia.puntos if mia else 0
    if sesion.estado == 'fin':
        datos['ranking'] = ranking(sesion, 10)
    if intento is not None:
        intento.refresh_from_db()
        datos['mi_total'] = intento.puntos
        if sesion.estado == 'fin':
            puesto = sum(1 for x in sesion.intentos.all() if x.puntos > intento.puntos) + 1
            datos['mi_puesto'] = puesto
            datos['mi_nota'] = str(intento.nota) if intento.nota is not None else None
    return datos


# ---------------------------------------------------------------------------
# Resultados del cuestionario (la mejor nota de cada uno, a su ritmo o en vivo)
# ---------------------------------------------------------------------------
def mejores_notas(cuestionario):
    """{(estudiante_id|None, integrante_id|None): Intento con la mejor nota}"""
    mejores = {}
    for it in cuestionario.intentos.filter(nota__isnull=False).select_related('estudiante__user', 'integrante'):
        clave = (it.estudiante_id, it.integrante_id)
        if clave not in mejores or it.nota > mejores[clave].nota:
            mejores[clave] = it
    return mejores
