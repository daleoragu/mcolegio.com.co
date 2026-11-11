"""Lo común a los tres chats (colegio, colegas y Mi Salón Virtual): editar un mensaje, buscar lo que se escribió
y vaciar el chat (para mí o, el moderador o el docente, para todos).

Vaciar no borra de la base de datos: solo deja de mostrar lo anterior. Así, en el chat del colegio, los directivos
pueden seguir revisando una conversación con reportes.
"""
from datetime import timedelta

from django.db.models import Q
from django.utils import timezone

HORAS_EDITAR = 24
MAX_TEXTO = 2000


def desde(*fechas):
    """La fecha más reciente de vaciado que aplica (o None)."""
    fechas = [f for f in fechas if f]
    return max(fechas) if fechas else None


def visibles(qs, corte):
    return qs.filter(creado__gt=corte) if corte else qs


def se_puede_editar(m, propio):
    """Solo lo propio, que tenga texto (o pie de foto o documento), no borrado y de las últimas 24 horas."""
    return bool(propio and not m.eliminado and m.tipo in ('texto', 'foto', 'doc')
                and timezone.now() - m.creado < timedelta(hours=HORAS_EDITAR))


def editar(m, texto):
    """Cambia el texto. ValueError si no se puede. Guarda la versión original la primera vez."""
    texto = (texto or '').strip()[:MAX_TEXTO]
    if not texto and m.tipo == 'texto':
        raise ValueError('El mensaje no puede quedar vacío: si quiere quitarlo, bórrelo.')
    if texto == m.texto:
        return m
    if m.editado is None:
        m.texto_original = m.texto
    m.texto, m.editado = texto, timezone.now()
    m.save(update_fields=['texto', 'texto_original', 'editado'])
    return m


def editados(qs, despues):
    """[{id, texto}] de los mensajes ya en pantalla (id ≤ despues) que se editaron: la pantalla los actualiza."""
    return list(qs.filter(id__lte=despues, editado__isnull=False, eliminado=False)
                .order_by('-editado').values('id', 'texto')[:60])


def buscar(qs, q, limite=40):
    """Los mensajes (no borrados) que tienen todas las palabras buscadas, en el texto o en el nombre del documento."""
    palabras = (q or '').split()[:5]
    if not palabras or len(' '.join(palabras)) < 2:
        return []
    qs = qs.filter(eliminado=False)
    for p in palabras:
        qs = qs.filter(Q(texto__icontains=p) | Q(nombre_archivo__icontains=p))
    return list(qs.order_by('-creado', '-id')[:limite])


def resultado(d, q):
    """Lo que necesita la lista de resultados a partir del JSON del mensaje."""
    texto = d.get('texto') or d.get('nombre') or ''
    return {'id': d['id'], 'autor': d['autor'], 'mio': d['mio'], 'dia': d['dia'], 'hora': d['hora'],
            'texto': texto[:300], 'tipo': d['tipo']}


def ultimos(qs, n, ver=None):
    """Los últimos n mensajes; con ver=<id> (desde el buscador), los que rodean ese mensaje."""
    try:
        ver = int(ver) if ver else None
    except (TypeError, ValueError):
        ver = None
    if ver and qs.filter(pk=ver).exists():
        antes = list(qs.filter(id__lte=ver).order_by('-creado', '-id')[:n // 2])[::-1]
        return antes + list(qs.filter(id__gt=ver).order_by('creado', 'id')[:n // 2])
    return list(qs.order_by('-creado', '-id')[:n])[::-1]
