from django.conf import settings
from django.contrib.auth.models import User
from django.core.mail import EmailMessage, get_connection
from django.db import transaction
from django.db.models import Max
from django.utils import timezone

from notas import avisos_familia
from notas.models import Estudiante, FichaEstudiante, Notificacion

from .models import Circular, Lectura


def destinatarios(circular):
    """[(usuario, estudiante o None)] a quienes va la circular."""
    colegio = circular.colegio
    salida = []
    if circular.para in ('FAMILIAS', 'CURSOS', 'TODOS'):
        est = Estudiante.objects.filter(colegio=colegio, is_active=True, curso__isnull=False).select_related('user')
        if circular.para == 'CURSOS':
            est = est.filter(curso__in=circular.cursos.all())
        salida += [(e.user, e) for e in est]
    if circular.para in ('DOCENTES', 'TODOS'):
        salida += [(u, None) for u in User.objects.filter(docente__colegio=colegio, is_active=True).distinct()]
    vistos, unicos = set(), []
    for u, e in salida:
        if u.id not in vistos:
            vistos.add(u.id)
            unicos.append((u, e))
    return unicos


def texto_recordatorio(circular, url):
    return (f'{circular.colegio.nombre}: le recordamos leer la circular N.º {circular.numero} '
            f'«{circular.titulo}»{" y confirmar que la leyó" if circular.pide_confirmacion else ""}. '
            f'Está en la plataforma: {url}')


def publicar(circular, url_ver):
    """Numera, crea las lecturas, avisa en la plataforma y por correo. Devuelve (destinatarios, correos)."""
    with transaction.atomic():
        if not circular.numero:
            ultimo = (Circular.objects.filter(colegio=circular.colegio, publicada__year=timezone.now().year)
                      .aggregate(m=Max('numero'))['m'] or 0)
            circular.numero = ultimo + 1
        circular.publicada = timezone.now()
        circular.save(update_fields=['numero', 'publicada'])
        lista = destinatarios(circular)
        Lectura.objects.bulk_create([Lectura(circular=circular, usuario=u, estudiante=e) for u, e in lista],
                                    ignore_conflicts=True)
        Notificacion.objects.bulk_create([
            Notificacion(colegio=circular.colegio, destinatario=u, tipo='GENERAL', url=url_ver,
                         mensaje=f'Nueva circular N.º {circular.numero}: {circular.titulo}'[:255])
            for u, _ in lista])
    correos = 0
    if avisos_familia.correo_configurado():
        fichas = {f.estudiante_id: (f.email_acudiente or '').strip()
                  for f in FichaEstudiante.objects.filter(estudiante__in=[e for _, e in lista if e])}
        mensajes = []
        for u, e in lista:
            destino = fichas.get(e.id) if e else (u.email or '').strip()
            if destino:
                cuerpo = (f'{circular.cuerpo}\n\n—\nCircular N.º {circular.numero} de {circular.colegio.nombre}.\n'
                          f'Véala{" y confirme que la leyó" if circular.pide_confirmacion else ""} en: {url_ver}')
                mensajes.append(EmailMessage(f'Circular N.º {circular.numero}: {circular.titulo}', cuerpo,
                                             settings.DEFAULT_FROM_EMAIL, [destino]))
        if mensajes:
            try:
                correos = get_connection(fail_silently=True).send_messages(mensajes) or 0
            except Exception:
                correos = 0
    return len(lista), correos


def resumen(circular):
    lecturas = circular.lecturas.all()
    total = lecturas.count()
    abiertas = lecturas.filter(abierta__isnull=False).count()
    confirmadas = lecturas.filter(confirmada__isnull=False).count()
    base = confirmadas if circular.pide_confirmacion else abiertas
    return {'total': total, 'abiertas': abiertas, 'confirmadas': confirmadas,
            'pct': round(100 * base / total) if total else 0}
