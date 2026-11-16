"""Puntos de la Biblioteca comunitaria: cuánto vale un material y cuánta reputación tiene su autor.

Un material gana puntos cuando otros docentes lo usan, lo califican y lo comentan:
  · cada uso (alguien hizo «Usar una copia») ........ 3 puntos
  · cada calificación ............................... las estrellas que le dieron (1 a 5)
  · cada comentario ................................. 1 punto
La reputación del autor es la suma de los puntos de sus materiales publicados. Con ella sube de nivel y,
al llegar a cada nivel, recibe una sola vez créditos de IA de regalo (los «premios del plan»).
Los puntos sirven también para ordenar la biblioteca («Más puntos»)."""
from django.db.models import Count, Sum

PUNTOS_USO = 3
PUNTOS_COMENTARIO = 1

# (desde cuántos puntos, nombre, color, créditos de IA de regalo al llegar)
NIVELES = [
    (0, 'Docente que comparte', '#64748b', 0),
    (30, 'Bronce', '#b45309', 30),
    (150, 'Plata', '#64748b', 80),
    (400, 'Oro', '#ca8a04', 200),
    (1000, 'Diamante', '#0891b2', 500),
]
PREFIJO_PREMIO = 'Premio Biblioteca · nivel '


def puntos_de(m):
    return m.usos * PUNTOS_USO + m.estrellas_suma + m.comentarios.count() * PUNTOS_COMENTARIO


def actualizar(m):
    """Recalcula los puntos del material y entrega los premios que el autor haya alcanzado."""
    from .models import MaterialCompartido
    m.refresh_from_db(fields=['usos', 'estrellas_suma', 'estrellas_n'])
    m.puntos = puntos_de(m)
    MaterialCompartido.objects.filter(pk=m.pk).update(puntos=m.puntos)
    if m.alcance != 'libre':
        premiar(m.autor)
    return m.puntos


def reputacion(usuario):
    from .models import MaterialCompartido
    return MaterialCompartido.objects.filter(autor=usuario, estado='publicado').aggregate(t=Sum('puntos'))['t'] or 0


def nivel(puntos):
    """{'nombre', 'color', 'puntos', 'siguiente': {...} | None, 'faltan', 'pct'} para mostrar la barra de progreso."""
    actual = NIVELES[0]
    siguiente = None
    for i, n in enumerate(NIVELES):
        if puntos >= n[0]:
            actual = n
            siguiente = NIVELES[i + 1] if i + 1 < len(NIVELES) else None
    datos = {'nombre': actual[1], 'color': actual[2], 'puntos': puntos, 'siguiente': None, 'faltan': 0, 'pct': 100}
    if siguiente:
        tramo = siguiente[0] - actual[0]
        datos.update(siguiente={'nombre': siguiente[1], 'desde': siguiente[0], 'premio': siguiente[3]},
                     faltan=siguiente[0] - puntos, pct=max(3, round(100 * (puntos - actual[0]) / tramo)))
    return datos


def premiar(usuario):
    """Entrega (una sola vez por nivel) los créditos de IA de cada nivel alcanzado. Devuelve los niveles nuevos."""
    from . import creditos as K
    from .models import MovimientoIA
    puntos = reputacion(usuario)
    nuevos = []
    for desde, nombre, _, premio in NIVELES:
        if premio and puntos >= desde:
            detalle = f'{PREFIJO_PREMIO}{nombre}'
            if not MovimientoIA.objects.filter(usuario=usuario, tipo='regalo', detalle=detalle).exists():
                K.regalar(usuario, premio, detalle)
                nuevos.append(nombre)
    return nuevos


def insignias(usuario):
    """Las insignias del autor: por cuánto ha compartido, cuánto se usa y qué tan bien lo califican."""
    from .models import MaterialCompartido
    publicados = MaterialCompartido.objects.filter(autor=usuario, estado='publicado')
    t = publicados.aggregate(n=Count('id'), usos=Sum('usos'), suma=Sum('estrellas_suma'), votos=Sum('estrellas_n'))
    n, usos, suma, votos = t['n'] or 0, t['usos'] or 0, t['suma'] or 0, t['votos'] or 0
    salida = []
    if n >= 1:
        salida.append('Primer material compartido')
    if n >= 10:
        salida.append('10 materiales compartidos')
    if n >= 25:
        salida.append('25 materiales compartidos')
    if usos >= 50:
        salida.append('Sus materiales se usaron 50 veces')
    if votos >= 5 and suma / votos >= 4.5:
        salida.append('Autor destacado (★ 4,5 o más)')
    return salida
