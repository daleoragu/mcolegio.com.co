"""Mascota académica: necesidades que bajan con el tiempo y se llenan respondiendo preguntas.

* Comida, sueño y baño bajan con las horas reales (de 100 a 0 en uno o dos días).
* Cada respuesta correcta llena una parte; la equivocada no llena y muestra la correcta.
* Si dos necesidades llegan a cero, la mascota se desmaya: la racha vuelve a cero y se
  reanima con 3 respuestas correctas. Nunca «se muere».
* Las preguntas salen del servidor y aquí se califican: el celular no sabe cuál es la correcta.
* La diversión (el ánimo) también baja con las horas, pero no la desmaya: si se aburre, se pone triste.
  Sube jugando: en el minijuego «Atrapa estrellas» (cada burbuja ? es una pregunta) o cuando el
  estudiante supera niveles de los juegos de lógica («jugó con usted»).
"""
import random

from django.utils import timezone

from . import bancos_juegos

# Puntos que pierde cada necesidad por hora
POR_HORA = {'hambre': 4.0, 'sueno': 3.0, 'higiene': 2.5}
DIVERSION_POR_HORA = 3.5
ACCIONES = {'comer': 'hambre', 'dormir': 'sueno', 'banar': 'higiene', 'jugar': 'diversion'}
# Premio por terminar una partida del minijuego (el puntaje lo cuenta el navegador: por eso es poco y con espera)
PREMIO_PARTIDA_MAX = 15
ESPERA_PARTIDA_MIN = 5
# Premio por cada nivel nuevo de un juego de lógica (máximo 3 niveles por envío)
PREMIO_NIVEL = 20
LLENA = 34
ACIERTOS_PARA_REANIMAR = 3


def actualizar(mascota, ahora=None, guardar=True):
    """Aplica lo que bajaron las necesidades desde la última vez."""
    ahora = ahora or timezone.now()
    horas = max(0.0, (ahora - mascota.actualizada).total_seconds() / 3600)
    if horas and not mascota.debil:
        for campo, tasa in POR_HORA.items():
            setattr(mascota, campo, max(0.0, getattr(mascota, campo) - tasa * horas))
        mascota.diversion = max(0.0, mascota.diversion - DIVERSION_POR_HORA * horas)
        if sum(1 for c in POR_HORA if getattr(mascota, c) <= 0) >= 2:
            mascota.debil, mascota.reanimar = True, 0
    mascota.actualizada = ahora
    mascota.mejor_racha = max(mascota.mejor_racha, dias_vivo(mascota, ahora))
    if guardar:
        mascota.save()
    return mascota


def dias_vivo(mascota, ahora=None):
    if mascota.debil:
        return 0
    return max(0, ((ahora or timezone.now()) - mascota.nacida).days)


def animo(mascota):
    """Cómo se siente, para la cara y el mensaje."""
    if mascota.debil:
        return 'desmayada'
    minimo = min(mascota.hambre, mascota.sueno, mascota.higiene, mascota.diversion + 10)   # aburrirse pesa un poco menos
    if minimo < 15:
        return 'mal'
    if minimo < 40:
        return 'regular'
    return 'feliz'


# Estado de ánimo: qué siente y por qué (lo que más le falta), con una frase para el estudiante
HUMORES = {
    'desmayada': ('Desmayada', '{n} se desmayó. Responda bien para reanimarla.'),
    'hambre': ('Hambrienta', '{n} tiene mucha hambre. ¡Déle de comer!'),
    'sueno': ('Cansada', '{n} se está quedando dormida de pie.'),
    'higiene': ('Sucia', '{n} necesita un buen baño.'),
    'triste': ('Triste', '{n} está triste: hace rato nadie juega con ella.'),
    'aburrida': ('Aburrida', '{n} se aburre. ¿Jugamos un rato?'),
    'contenta': ('Contenta', '{n} está bien, aunque algo le falta.'),
    'feliz': ('Feliz', '¡{n} está feliz!'),
    'euforica': ('Emocionada', '¡{n} está emocionadísima! Todo está al máximo.'),
}


def humor(mascota):
    """El estado de ánimo detallado: (clave, nombre, frase)."""
    n = mascota.nombre
    if mascota.debil:
        clave = 'desmayada'
    else:
        fisicas = {'hambre': mascota.hambre, 'sueno': mascota.sueno, 'higiene': mascota.higiene}
        peor = min(fisicas, key=fisicas.get)
        if fisicas[peor] < 25:
            clave = peor
        elif mascota.diversion < 15:
            clave = 'triste'
        elif mascota.diversion < 40:
            clave = 'aburrida'
        elif min(fisicas[peor], mascota.diversion) >= 85:
            clave = 'euforica'
        elif min(fisicas[peor], mascota.diversion) >= 55:
            clave = 'feliz'
        else:
            clave = 'contenta'
    nombre, frase = HUMORES[clave]
    return clave, nombre, frase.format(n=n)


def estado(mascota):
    return {
        'nombre': mascota.nombre, 'especie': mascota.especie, 'especie_nombre': mascota.get_especie_display(),
        'hambre': round(mascota.hambre), 'sueno': round(mascota.sueno), 'higiene': round(mascota.higiene),
        'diversion': round(mascota.diversion), 'animo': animo(mascota),
        'humor': dict(zip(('clave', 'nombre', 'frase'), humor(mascota))), 'juego_reciente': mascota.juego_reciente, 'debil': mascota.debil, 'reanimar': mascota.reanimar, 'para_reanimar': ACIERTOS_PARA_REANIMAR,
        'dias': dias_vivo(mascota), 'mejor_racha': mascota.mejor_racha,
        'respondidas': mascota.respondidas, 'aciertos': mascota.aciertos,
    }


# ---------------------------------------------------------------------------
# Preguntas
# ---------------------------------------------------------------------------
def aulas_de(aula, persona):
    """Las clases que alimentan la mascota. En el colegio cada estudiante tiene UNA mascota y come preguntas de
    todas las clases de su curso (de cualquier docente); en el plan individual, las de la clase de su profe."""
    from .models import Aula
    curso_id = getattr(persona, 'curso_id', None)
    if aula.colegio_id and aula.asignacion_id and curso_id:
        return list(Aula.objects.filter(colegio_id=aula.colegio_id, asignacion__curso_id=curso_id))
    return [aula]


def de_persona(aula, persona):
    """La mascota del estudiante: en el colegio es una sola aunque la haya adoptado en otra clase."""
    from .models import MascotaAula
    if persona is None:
        return None
    if aula.colegio_id and not hasattr(persona, 'completo'):
        return (MascotaAula.objects.filter(estudiante=persona, aula__colegio_id=aula.colegio_id)
                .order_by('-respondidas', 'creada').first())
    from .logica import filtro_persona
    return MascotaAula.objects.filter(aula=aula, **filtro_persona(persona)).first()


def banco(aula, persona_clave=None, aulas=None):
    """Las preguntas de selección que sirven: las del docente para las mascotas, las de los juegos
    de la clase (o de todas las clases del curso) y, si no hay ninguna, los bancos de prueba."""
    from .logica import es_para
    preguntas = []
    for a in (aulas or [aula]):
        preguntas.extend(a.preguntas_mascota or [])
        for j in a.juegos.filter(publicado=True):
            if persona_clave is None or es_para(j, persona_clave):
                preguntas.extend(j.preguntas)
    buenas = [p for p in preguntas if 2 <= len(p.get('opciones', [])) <= 4
              and sum(1 for o in p['opciones'] if o.get('correcta')) == 1]
    if buenas:
        return buenas
    return (bancos_juegos.preguntas('matematicas', 10) + bancos_juegos.preguntas('colombia', 8)
            + bancos_juegos.preguntas('ingles', 8))


def pedir(mascota, accion, persona_clave=None):
    """Escoge una pregunta para la acción y la deja pendiente. Devuelve (pregunta para mostrar, mensaje)."""
    actualizar(mascota, guardar=False)
    if accion == 'reanimar':
        if not mascota.debil:
            return None, f'{mascota.nombre} está bien despierta.'
    elif accion in ACCIONES:
        if mascota.debil:
            return None, f'{mascota.nombre} está desmayada: primero reanímela.'
        if accion != 'jugar' and getattr(mascota, ACCIONES[accion]) >= 95:
            return None, {'comer': f'{mascota.nombre} no tiene hambre.', 'dormir': f'{mascota.nombre} no tiene sueño.',
                          'banar': f'{mascota.nombre} ya está limpia.'}[accion]
    else:
        return None, 'Acción desconocida.'
    persona = mascota.estudiante or mascota.integrante
    lista = banco(mascota.aula, persona_clave, aulas_de(mascota.aula, persona))
    # Que no salga la misma pregunta dos veces seguidas
    anterior = (mascota.pendiente or {}).get('texto')
    opciones = [p for p in lista if p['texto'] != anterior] or lista
    p = random.choice(opciones)
    orden = list(range(len(p['opciones'])))
    random.shuffle(orden)
    mascota.pendiente = {'accion': accion, 'texto': p['texto'], 'opciones': [p['opciones'][i]['texto'] for i in orden],
                         'correcta': next(n for n, i in enumerate(orden) if p['opciones'][i].get('correcta'))}
    mascota.save()
    return {'texto': mascota.pendiente['texto'], 'opciones': mascota.pendiente['opciones'], 'accion': accion}, ''


def responder(mascota, opcion):
    """Califica la pregunta pendiente. Devuelve (bien, índice de la correcta, mensaje)."""
    p = mascota.pendiente or {}
    if 'correcta' not in p:
        return None, None, 'No hay una pregunta pendiente.'
    actualizar(mascota, guardar=False)
    bien = opcion == p['correcta']
    mascota.respondidas += 1
    accion = p['accion']
    if bien:
        mascota.aciertos += 1
        if accion == 'reanimar':
            mascota.reanimar += 1
            if mascota.reanimar >= ACIERTOS_PARA_REANIMAR:
                mascota.debil, mascota.reanimar = False, 0
                mascota.hambre = mascota.sueno = mascota.higiene = mascota.diversion = 50
                mascota.nacida = timezone.now()
                mensaje = f'¡{mascota.nombre} despertó! Empieza una racha nueva.'
            else:
                mensaje = f'¡Bien! Faltan {ACIERTOS_PARA_REANIMAR - mascota.reanimar} para que despierte.'
        else:
            campo = ACCIONES[accion]
            setattr(mascota, campo, min(100.0, getattr(mascota, campo) + LLENA))
            mensaje = {'comer': '¡Ñam! Qué rico.', 'dormir': '¡Zzz… qué buen descanso!', 'banar': '¡Brilla de limpio!',
                       'jugar': '¡Bien! +5 estrellas y más ánimo.'}[accion]
    else:
        mensaje = 'Esa no era. ' + ('Siga intentando.' if accion == 'reanimar' else f'{mascota.nombre} se quedó esperando.')
    correcta = p['correcta']
    mascota.pendiente = {'texto': p['texto']}
    mascota.save()
    return bien, correcta, mensaje


def nueva(aula, persona, especie, nombre):
    from .logica import filtro_persona
    from .models import MascotaAula
    especie = especie if especie in dict(MascotaAula.ESPECIES) else 'dragon'
    nombre = ' '.join((nombre or '').split())[:20] or dict(MascotaAula.ESPECIES)[especie]
    ahora = timezone.now()
    return MascotaAula.objects.create(aula=aula, especie=especie, nombre=nombre, actualizada=ahora,
                                      nacida=ahora, **filtro_persona(persona))


def ranking(aula, n=10):
    """El tablero de la clase. En el colegio: la mascota única de cada estudiante del curso (la adoptara donde la adoptara)."""
    from .models import MascotaAula
    lista = []
    if aula.colegio_id and aula.asignacion_id:
        vistas, mascotas = set(), []
        for m in (MascotaAula.objects.filter(estudiante__curso_id=aula.asignacion.curso_id, aula__colegio_id=aula.colegio_id)
                  .select_related('estudiante__user', 'integrante').order_by('-respondidas', 'creada')):
            if m.estudiante_id not in vistas:
                vistas.add(m.estudiante_id)
                mascotas.append(m)
    else:
        mascotas = aula.mascotas.select_related('estudiante__user', 'integrante')
    for m in mascotas:
        actualizar(m, guardar=False)
        persona = m.estudiante or m.integrante
        from .logica import nombre_de
        lista.append({'mascota': m, 'dueno': nombre_de(persona), 'dias': dias_vivo(m), 'animo': animo(m), 'humor': humor(m)[1]})
    lista.sort(key=lambda x: (-x['dias'], -x['mascota'].mejor_racha, -x['mascota'].aciertos))
    return lista[:n] if n else lista



def terminar_partida(mascota, estrellas, ahora=None):
    """Fin de una partida de «Atrapa estrellas». El puntaje lo manda el navegador, así que el premio es
    pequeño y solo cuenta una partida cada ESPERA_PARTIDA_MIN minutos. Devuelve (subió, mensaje)."""
    ahora = ahora or timezone.now()
    actualizar(mascota, ahora, guardar=False)
    if mascota.debil:
        return 0, f'{mascota.nombre} está desmayada: primero reanímela.'
    try:
        estrellas = max(0, min(200, int(estrellas)))
    except (TypeError, ValueError):
        estrellas = 0
    if mascota.ultimo_juego and (ahora - mascota.ultimo_juego).total_seconds() < ESPERA_PARTIDA_MIN * 60:
        mascota.save()
        return 0, f'¡{estrellas} estrellas! {mascota.nombre} quedó cansada de correr: la próxima partida le sube el ánimo en unos minutos.'
    sube = min(PREMIO_PARTIDA_MAX, 5 + estrellas // 4) if estrellas else 0
    antes = mascota.diversion
    mascota.diversion = min(100.0, mascota.diversion + sube)
    mascota.ultimo_juego, mascota.juego_reciente = ahora, 'Atrapa estrellas'
    mascota.save()
    return round(mascota.diversion - antes), f'¡{estrellas} estrellas! {mascota.nombre} se divirtió mucho.'


def jugo_logica(aula, persona, nombre_juego, niveles_nuevos):
    """Un nivel nuevo superado en un juego de lógica también anima a la mascota del estudiante."""
    if not niveles_nuevos or persona is None:
        return None
    m = de_persona(aula, persona)
    if m is None:
        return None
    actualizar(m, guardar=False)
    if not m.debil:
        m.diversion = min(100.0, m.diversion + PREMIO_NIVEL * min(3, niveles_nuevos))
    m.juego_reciente = nombre_juego[:80]
    m.save()
    return m
