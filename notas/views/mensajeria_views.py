# notas/views/mensajeria_views.py
"""Correo interno del colegio: recibidos, enviados, borradores, destacados y papelera.

Cada persona maneja su copia: si el destinatario borra o destaca un mensaje, al remitente
no le cambia nada (y al revés). Un mensaje se borra de verdad cuando los dos lo sacaron de
la papelera.
"""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import HttpResponseNotFound
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.html import strip_tags
from django.views.decorators.http import require_POST

from ..forms import MensajeForm
from ..models import Mensaje
from ..utils.notificaciones import crear_notificacion

POR_PAGINA = 25

CARPETAS = {
    'recibidos': ('Recibidos', 'fa-inbox', 'notas:bandeja_entrada'),
    'enviados': ('Enviados', 'fa-paper-plane', 'notas:mensajes_enviados'),
    'borradores': ('Borradores', 'fa-pen-to-square', 'notas:borradores'),
    'destacados': ('Destacados', 'fa-star', 'notas:destacados'),
    'papelera': ('Papelera', 'fa-trash-can', 'notas:papelera'),
}


def _consulta(user, colegio, carpeta):
    base = Mensaje.objects.filter(colegio=colegio).select_related('remitente', 'destinatario')
    recibidos = Q(destinatario=user, estado='ENVIADO', eliminado_por_destinatario=False)
    enviados = Q(remitente=user, estado='ENVIADO', eliminado_por_remitente=False)
    if carpeta == 'recibidos':
        qs = base.filter(recibidos)
    elif carpeta == 'enviados':
        qs = base.filter(enviados)
    elif carpeta == 'borradores':
        qs = base.filter(remitente=user, estado='BORRADOR', eliminado_por_remitente=False)
    elif carpeta == 'destacados':
        qs = base.filter((recibidos & Q(destacado_por_destinatario=True)) | (enviados & Q(destacado_por_remitente=True)))
    else:
        qs = base.filter(Q(destinatario=user, estado='ENVIADO', eliminado_por_destinatario=True,
                           purgado_por_destinatario=False)
                         | Q(remitente=user, eliminado_por_remitente=True, purgado_por_remitente=False))
        return qs.distinct().order_by('-fecha_eliminacion', '-fecha_envio')
    return qs.distinct().order_by('-fecha_envio')


def _no_leidos(user, colegio):
    return Mensaje.objects.filter(colegio=colegio, destinatario=user, estado='ENVIADO',
                                  eliminado_por_destinatario=False, leido=False).count()


def _contexto(request, carpeta, **extra):
    ctx = {'colegio': request.colegio, 'carpeta': carpeta, 'carpetas': CARPETAS, 'hoy': timezone.localdate(),
           'no_leidos': _no_leidos(request.user, request.colegio)}
    ctx.update(extra)
    return ctx


def _lado(user, m):
    """'dest' si el usuario recibió el mensaje, 'rem' si lo envió (un mensaje a uno mismo cuenta como recibido)."""
    if m.destinatario_id == user.id and m.estado == 'ENVIADO':
        return 'dest'
    if m.remitente_id == user.id:
        return 'rem'
    return None


def _lista(request, carpeta):
    if not request.colegio:
        return HttpResponseNotFound('<h1>Colegio no configurado</h1>')
    q = (request.GET.get('q') or '').strip()
    qs = _consulta(request.user, request.colegio, carpeta)
    if q:
        filtro = Q(asunto__icontains=q) | Q(cuerpo__icontains=q)
        for campo in ('remitente', 'destinatario'):
            filtro |= Q(**{f'{campo}__first_name__icontains': q}) | Q(**{f'{campo}__last_name__icontains': q})
        qs = qs.filter(filtro)
    pagina = Paginator(qs, POR_PAGINA).get_page(request.GET.get('pagina'))
    filas = []
    for m in pagina:
        lado = _lado(request.user, m)
        otro = m.remitente if lado == 'dest' else m.destinatario
        filas.append({'m': m, 'lado': lado, 'otro': otro, 'no_leido': lado == 'dest' and not m.leido,
                      'destacado': m.destacado_por_destinatario if lado == 'dest' else m.destacado_por_remitente})
    return render(request, 'notas/mensajeria/lista.html', _contexto(
        request, carpeta, filas=filas, pagina=pagina, search_query=q, page_title=CARPETAS[carpeta][0]))


@login_required
def bandeja_entrada_vista(request):
    return _lista(request, 'recibidos')


@login_required
def mensajes_enviados_vista(request):
    return _lista(request, 'enviados')


@login_required
def borradores_vista(request):
    return _lista(request, 'borradores')


@login_required
def destacados_vista(request):
    return _lista(request, 'destacados')


@login_required
def papelera_vista(request):
    return _lista(request, 'papelera')


# ----------------------------------------------------------------------------- redactar

def _cita(m, reenviar=False):
    texto = strip_tags(m.cuerpo or '').strip()
    fecha = timezone.localtime(m.fecha_envio).strftime('%d/%m/%Y a las %I:%M %p')
    autor = m.remitente.get_full_name() or m.remitente.username
    if reenviar:
        cabeza = (f'---------- Mensaje reenviado ----------\nDe: {autor}\nFecha: {fecha}\nAsunto: {m.asunto}\n'
                  f'Para: {m.destinatario.get_full_name() or m.destinatario.username}\n\n')
        return '\n\n' + cabeza + texto
    citado = '\n'.join(f'> {linea}' for linea in texto.splitlines())
    return f'\n\n\nEl {fecha}, {autor} escribió:\n{citado}'


def _prefijo(asunto, prefijo):
    asunto = (asunto or '').strip()
    return asunto if asunto.lower().startswith(prefijo.lower()) else f'{prefijo} {asunto}'.strip()


def _redactar(request, borrador=None):
    if not request.colegio:
        return HttpResponseNotFound('<h1>Colegio no configurado</h1>')
    inicial = {}
    if borrador is None:
        if request.GET.get('responder_a'):
            m = get_object_or_404(Mensaje, id=request.GET['responder_a'], colegio=request.colegio)
            if request.user.id not in (m.destinatario_id, m.remitente_id):
                raise PermissionDenied('No puede responder este mensaje.')
            otro = m.remitente if m.destinatario_id == request.user.id else m.destinatario
            inicial = {'destinatario': otro, 'asunto': _prefijo(m.asunto, 'Re:'), 'cuerpo': _cita(m)}
        elif request.GET.get('reenviar'):
            m = get_object_or_404(Mensaje, id=request.GET['reenviar'], colegio=request.colegio)
            if request.user.id not in (m.destinatario_id, m.remitente_id):
                raise PermissionDenied('No puede reenviar este mensaje.')
            inicial = {'asunto': _prefijo(m.asunto, 'RV:'), 'cuerpo': _cita(m, reenviar=True)}
        elif request.GET.get('para'):
            inicial = {'destinatario': request.GET['para']}

    if request.method == 'POST':
        es_borrador = 'guardar_borrador' in request.POST
        if 'descartar' in request.POST:
            if borrador is not None:
                borrador.delete()
                messages.info(request, 'Borrador descartado.')
            return redirect('notas:borradores' if borrador is not None else 'notas:bandeja_entrada')
        form = MensajeForm(request.POST, instance=borrador, user=request.user, colegio=request.colegio,
                           borrador=es_borrador)
        if form.is_valid():
            m = form.save(commit=False)
            m.remitente = request.user
            m.colegio = request.colegio
            m.asunto = (m.asunto or '').strip() or '(Sin asunto)'
            if es_borrador:
                m.estado = 'BORRADOR'
                m.save()
                messages.success(request, 'Borrador guardado.')
                return redirect('notas:borradores')
            m.estado = 'ENVIADO'
            m.fecha_envio = timezone.now()
            m.leido = False
            m.save()
            crear_notificacion(destinatario=m.destinatario, colegio=request.colegio, tipo='MENSAJE',
                               mensaje=f'Nuevo mensaje de {request.user.get_full_name() or request.user.username}: '
                                       f'{m.asunto}'[:255],
                               url_name='notas:ver_mensaje', kwargs={'mensaje_id': m.id})
            messages.success(request, f'Mensaje enviado a {m.destinatario.get_full_name() or m.destinatario.username}.')
            return redirect('notas:mensajes_enviados')
        messages.error(request, 'Revise lo que falta antes de enviar.')
    else:
        form = MensajeForm(instance=borrador, initial=inicial, user=request.user, colegio=request.colegio)
    return render(request, 'notas/mensajeria/componer_mensaje.html', _contexto(
        request, 'redactar', form=form, borrador=borrador,
        page_title='Editar borrador' if borrador else 'Nuevo mensaje'))


@login_required
def componer_mensaje_vista(request):
    return _redactar(request)


@login_required
def editar_borrador_vista(request, mensaje_id):
    if not request.colegio:
        return HttpResponseNotFound('<h1>Colegio no configurado</h1>')
    borrador = get_object_or_404(Mensaje, id=mensaje_id, colegio=request.colegio, remitente=request.user,
                                 estado='BORRADOR')
    return _redactar(request, borrador)


# ----------------------------------------------------------------------------- ver

@login_required
def ver_mensaje_vista(request, mensaje_id):
    if not request.colegio:
        return HttpResponseNotFound('<h1>Colegio no configurado</h1>')
    m = get_object_or_404(Mensaje.objects.select_related('remitente', 'destinatario'), id=mensaje_id,
                          colegio=request.colegio)
    lado = _lado(request.user, m)
    if lado is None:
        raise PermissionDenied('No tiene permiso para ver este mensaje.')
    if m.estado == 'BORRADOR':
        return redirect('notas:editar_borrador', mensaje_id=m.id)
    if lado == 'dest' and not m.leido:
        m.leido = True
        m.save(update_fields=['leido'])
    en_papelera = m.eliminado_por_destinatario if lado == 'dest' else m.eliminado_por_remitente
    destacado = m.destacado_por_destinatario if lado == 'dest' else m.destacado_por_remitente
    carpeta = 'papelera' if en_papelera else ('recibidos' if lado == 'dest' else 'enviados')
    return render(request, 'notas/mensajeria/detalle_mensaje.html', _contexto(
        request, carpeta, mensaje=m, lado=lado, en_papelera=en_papelera, destacado=destacado,
        page_title=m.asunto))


# ----------------------------------------------------------------------------- acciones

def _aplicar(user, m, accion):
    """Hace la acción sobre la copia de este usuario. Devuelve True si hizo algo."""
    lado = _lado(user, m)
    if lado is None:
        return False
    sufijo = 'destinatario' if lado == 'dest' else 'remitente'
    if accion == 'papelera':
        setattr(m, f'eliminado_por_{sufijo}', True)
        m.fecha_eliminacion = timezone.now()
    elif accion == 'restaurar':
        setattr(m, f'eliminado_por_{sufijo}', False)
        setattr(m, f'purgado_por_{sufijo}', False)
    elif accion == 'eliminar':
        if not getattr(m, f'eliminado_por_{sufijo}'):
            return False                          # solo se elimina para siempre desde la papelera
        setattr(m, f'purgado_por_{sufijo}', True)
        otro = 'remitente' if sufijo == 'destinatario' else 'destinatario'
        # Si el otro también lo sacó (o es un borrador, que solo es de quien lo escribe), se borra de verdad
        if m.estado == 'BORRADOR' or getattr(m, f'purgado_por_{otro}') or m.remitente_id == m.destinatario_id:
            m.delete()
            return True
    elif accion in ('leido', 'no_leido'):
        if lado != 'dest':
            return False
        m.leido = accion == 'leido'
    elif accion in ('destacar', 'quitar_destacado'):
        setattr(m, f'destacado_por_{sufijo}', accion == 'destacar')
    else:
        return False
    m.save()
    return True


TEXTOS = {'papelera': 'movido(s) a la papelera', 'restaurar': 'restaurado(s)', 'eliminar': 'eliminado(s) para siempre',
          'leido': 'marcado(s) como leído(s)', 'no_leido': 'marcado(s) como no leído(s)', 'destacar': 'destacado(s)',
          'quitar_destacado': 'sin destacar'}


def _volver(request, defecto='notas:bandeja_entrada'):
    """A la carpeta de donde vino (solo direcciones de esta misma página)."""
    destino = request.POST.get('volver') or ''
    if destino.startswith('/') and not destino.startswith('//'):
        return redirect(destino)
    return redirect(defecto)


@require_POST
@login_required
def acciones_mensajes_vista(request):
    """Varias a la vez (casillas) o una sola (botón de la fila: accion_uno=accion:id)."""
    if not request.colegio:
        return HttpResponseNotFound('<h1>Colegio no configurado</h1>')
    if request.POST.get('accion_uno'):
        accion, _, uno = request.POST['accion_uno'].partition(':')
        ids = [uno]
    else:
        accion = request.POST.get('accion', '')
        ids = request.POST.getlist('ids')
    ids = [int(x) for x in ids if str(x).isdigit()]
    if request.POST.get('vaciar'):
        ids = list(_consulta(request.user, request.colegio, 'papelera').values_list('id', flat=True))
        accion = 'eliminar'
    if not ids:
        messages.info(request, 'Marque al menos un mensaje.')
        return _volver(request)
    hechos = sum(1 for m in Mensaje.objects.filter(colegio=request.colegio, id__in=ids)
                 .filter(Q(remitente=request.user) | Q(destinatario=request.user)) if _aplicar(request.user, m, accion))
    if hechos:
        messages.success(request, f'{hechos} mensaje(s) {TEXTOS.get(accion, "actualizado(s)")}.')
    return _volver(request)


@require_POST
@login_required
def borrar_mensaje_vista(request, mensaje_id):
    m = get_object_or_404(Mensaje, id=mensaje_id, colegio=request.colegio)
    if not _aplicar(request.user, m, 'papelera'):
        raise PermissionDenied('No tiene permiso para borrar este mensaje.')
    messages.success(request, 'El mensaje se movió a la papelera.')
    return _volver(request)


@require_POST
@login_required
def restaurar_mensaje_vista(request, mensaje_id):
    m = get_object_or_404(Mensaje, id=mensaje_id, colegio=request.colegio)
    if not _aplicar(request.user, m, 'restaurar'):
        raise PermissionDenied('No puede restaurar este mensaje.')
    messages.success(request, 'Mensaje restaurado.')
    return redirect('notas:papelera')


@require_POST
@login_required
def borrar_definitivamente_vista(request, mensaje_id):
    m = get_object_or_404(Mensaje, id=mensaje_id, colegio=request.colegio)
    if not _aplicar(request.user, m, 'eliminar'):
        raise PermissionDenied('Solo se elimina para siempre un mensaje que está en su papelera.')
    messages.success(request, 'Mensaje eliminado para siempre.')
    return redirect('notas:papelera')
