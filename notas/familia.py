"""Hermanos en el mismo colegio: una familia, varios estudiantes.

Para qué sirve:
* El acudiente abre la cuenta de un hijo en el celular y pasa a la de otro con
  un toque, sin volver a escribir la clave.
* Las notificaciones de todos los hijos le llegan a ese celular, con el nombre
  del hijo adelante («Ana: Nueva circular…»).

Cómo se arma la familia (nunca sola, para no mezclar datos de niños ajenos):
* La familia, desde la app: «Agregar otro hijo» con el usuario y la clave de
  ese hijo (así demuestra que es su acudiente).
* La secretaría: la plataforma le sugiere los estudiantes que comparten el
  celular del acudiente, la mamá o el papá, y ella los une con un clic.
"""
from django.db import transaction

from .avisos_familia import normalizar_celular
from .models import Estudiante, Familia, FichaEstudiante


def hermanos(estudiante):
    """Los otros hijos activos de la misma familia (sin el propio)."""
    if estudiante is None or not estudiante.familia_id:
        return Estudiante.objects.none()
    return (Estudiante.objects.filter(familia_id=estudiante.familia_id, colegio_id=estudiante.colegio_id, is_active=True)
            .exclude(pk=estudiante.pk).select_related('user', 'curso'))


@transaction.atomic
def unir(estudiantes):
    """Pone a todos en una misma familia; si alguno ya tenía familia, se juntan. Devuelve la familia."""
    estudiantes = [e for e in estudiantes if e is not None]
    colegios = {e.colegio_id for e in estudiantes}
    if len(estudiantes) < 2 or len(colegios) != 1:
        raise ValueError('Los hermanos deben ser al menos dos y del mismo colegio.')
    existentes = sorted({e.familia_id for e in estudiantes if e.familia_id})
    if existentes:
        familia = Familia.objects.get(pk=existentes[0])
        if len(existentes) > 1:
            Estudiante.objects.filter(familia_id__in=existentes[1:]).update(familia=familia)
            Familia.objects.filter(pk__in=existentes[1:]).delete()
    else:
        familia = Familia.objects.create(colegio_id=colegios.pop())
    Estudiante.objects.filter(pk__in=[e.pk for e in estudiantes]).update(familia=familia)
    for e in estudiantes:
        e.familia = familia
    return familia


@transaction.atomic
def separar(estudiante):
    """Saca al estudiante de su familia. Si queda uno solo, la familia se deshace."""
    familia_id = estudiante.familia_id
    if not familia_id:
        return
    Estudiante.objects.filter(pk=estudiante.pk).update(familia=None)
    estudiante.familia = None
    if Estudiante.objects.filter(familia_id=familia_id).count() < 2:
        Estudiante.objects.filter(familia_id=familia_id).update(familia=None)
        Familia.objects.filter(pk=familia_id).delete()


def sugerencias(colegio):
    """[[estudiante, …]] que comparten un celular de acudiente, mamá o papá y todavía no están unidos."""
    fichas = (FichaEstudiante.objects.filter(estudiante__colegio=colegio, estudiante__is_active=True)
              .select_related('estudiante__user', 'estudiante__curso'))
    por_numero, estudiantes = {}, {}
    for f in fichas:
        estudiantes[f.estudiante_id] = f.estudiante
        for cel in (f.celular_acudiente, f.celular_madre, f.celular_padre):
            numero = normalizar_celular(cel)
            if numero:
                por_numero.setdefault(numero, set()).add(f.estudiante_id)
    # Grupos conectados: si Ana comparte el de la mamá con Beto y Beto el del papá con Caro, son los tres.
    padre = {}

    def raiz(x):
        while padre.setdefault(x, x) != x:
            padre[x] = padre[padre[x]]
            x = padre[x]
        return x
    for ids in por_numero.values():
        ids = sorted(ids)
        for otro in ids[1:]:
            padre[raiz(otro)] = raiz(ids[0])
    grupos = {}
    for eid in padre:
        grupos.setdefault(raiz(eid), []).append(estudiantes[eid])
    salida = []
    for grupo in grupos.values():
        if len(grupo) < 2:
            continue
        familias = {e.familia_id for e in grupo}
        if len(familias) == 1 and None not in familias:
            continue                                        # ya están todos juntos
        salida.append(sorted(grupo, key=lambda e: (e.user.last_name, e.user.first_name)))
    return sorted(salida, key=lambda g: (g[0].user.last_name, g[0].user.first_name))


def destinos_por_usuario(user_ids):
    """{usuario: (usuarios que deben recibir sus avisos, nombre del hijo o '')}.

    Un estudiante en familia: los avisos van a todos los hermanos (el celular puede tener abierta
    la cuenta de cualquiera) y llevan su nombre. Los demás: solo a sí mismos, sin nombre."""
    user_ids = set(user_ids)
    salida = {u: ({u}, '') for u in user_ids}
    filas = list(Estudiante.objects.filter(user_id__in=user_ids, familia__isnull=False)
                 .values_list('user_id', 'familia_id', 'user__first_name'))
    if not filas:
        return salida
    miembros = {}
    for fam, uid in Estudiante.objects.filter(familia_id__in={f for _, f, _ in filas}, is_active=True) \
            .values_list('familia_id', 'user_id'):
        miembros.setdefault(fam, set()).add(uid)
    for uid, fam, nombre in filas:
        salida[uid] = (miembros.get(fam, set()) | {uid}, (nombre or '').split(' ')[0])
    return salida
