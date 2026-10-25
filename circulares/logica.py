<<<<<<< HEAD
from django.contrib.auth.models import User
from django.db import transaction
=======
import threading

from django.contrib.auth.models import User
from django.db import close_old_connections, transaction
>>>>>>> origin/mejoras-23-octubre
from django.db.models import Max
from django.utils import timezone

from notas import avisos_familia, mensajeria
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
    if circular.para in ('DOCENTES', 'PERSONAL', 'TODOS'):
        salida += [(u, None) for u in User.objects.filter(docente__colegio=colegio, is_active=True).distinct()]
    if circular.para in ('PERSONAL', 'TODOS'):
        salida += [(u, None) for u in User.objects.filter(administraciones__colegio=colegio,
                                                          administraciones__activo=True, is_active=True).distinct()]
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
                mensajes.append(mensajeria.mensaje(circular.colegio, f'Circular N.º {circular.numero}: {circular.titulo}',
                                                   cuerpo, [destino]))
        correos = mensajeria.enviar_varios(mensajes)
    return len(lista), correos


# ----------------------------------------------------------------------------- WhatsApp

# En las pruebas se pone en False para que el envío ocurra en el mismo hilo.
EN_SEGUNDO_PLANO = True
# Si fallan tantos seguidos, se para: casi siempre es el límite diario de Meta o la línea caída.
MAX_FALLOS_SEGUIDOS = 5


def whatsapp_disponible(colegio):
    """La línea de la plataforma está conectada y el colegio activó los avisos automáticos."""
    return mensajeria.whatsapp_configurado() and bool(getattr(colegio, 'whatsapp_automatico', False))


def texto_whatsapp(circular, url):
    return (f'Se publicó la circular N.º {circular.numero} «{circular.titulo}». '
            f'Véala{" y confirme que la leyó" if circular.pide_confirmacion else ""} en: {url}')


def pendientes_whatsapp(circular):
    """Lecturas de familias a las que todavía no les ha llegado el WhatsApp (y que no la han leído)."""
    ya = {'confirmada__isnull': True} if circular.pide_confirmacion else {'abierta__isnull': True}
    return circular.lecturas.filter(estudiante__isnull=False, whatsapp_enviado__isnull=True, **ya)


def enviar_whatsapp(circular, url):
    """Manda el aviso de la circular por WhatsApp a cada familia que falta. Devuelve (enviados, fallidos).

    A cada familia le llega un solo mensaje, al primer celular de la ficha (acudiente, mamá o papá)."""
    if not whatsapp_disponible(circular.colegio):
        return 0, 0
    texto = texto_whatsapp(circular, url)
    enviados = fallidos = seguidos = 0
    for l in pendientes_whatsapp(circular).select_related('estudiante__ficha'):
        cs = avisos_familia.contactos(l.estudiante)
        if not cs:
            l.whatsapp_detalle = 'La ficha no tiene celular'
            l.save(update_fields=['whatsapp_detalle'])
            continue
        ok, detalle = mensajeria.enviar_whatsapp(circular.colegio, cs[0]['numero'], texto)
        if ok:
            l.whatsapp_enviado = timezone.now()
            l.whatsapp_detalle = f'{cs[0]["rol"]} {cs[0]["visible"]}'[:120]
            enviados, seguidos = enviados + 1, 0
        else:
            l.whatsapp_detalle = f'No salió: {detalle}'[:120]
            fallidos, seguidos = fallidos + 1, seguidos + 1
        l.save(update_fields=['whatsapp_enviado', 'whatsapp_detalle'])
        if seguidos >= MAX_FALLOS_SEGUIDOS:
            break
    return enviados, fallidos


def lanzar_whatsapp(circular, url):
    """Envía en segundo plano para no dejar la página esperando mientras salen cientos de mensajes."""
    if not EN_SEGUNDO_PLANO:
        return enviar_whatsapp(circular, url)

    def trabajo():
        try:
            enviar_whatsapp(circular, url)
        finally:
            close_old_connections()
    threading.Thread(target=trabajo, daemon=True).start()
    return None


def resumen(circular):
    lecturas = circular.lecturas.all()
    total = lecturas.count()
    abiertas = lecturas.filter(abierta__isnull=False).count()
    confirmadas = lecturas.filter(confirmada__isnull=False).count()
    base = confirmadas if circular.pide_confirmacion else abiertas
    return {'total': total, 'abiertas': abiertas, 'confirmadas': confirmadas,
            'pct': round(100 * base / total) if total else 0,
            'whatsapp': lecturas.filter(whatsapp_enviado__isnull=False).count()}
