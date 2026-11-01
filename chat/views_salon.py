"""Chat de Mi Salón Virtual: el docente del plan individual con todo el grupo y con cada estudiante.

  · «Todo el grupo»: lo leen todos los que entran a la clase con el código. Escriben el docente y, si el
    docente no lo deja en «solo yo escribo», los estudiantes que pusieron su PIN.
  · Chat privado de cada estudiante con el docente: solo con el PIN del estudiante.
  · El PIN existe porque los estudiantes no tienen contraseña: sin él cualquiera que tenga el código del
    grupo podría escribir con el nombre de un compañero. Tras 5 intentos fallidos se bloquea 15 minutos.
"""
import json

from django.core.cache import cache
from django.core.files.base import ContentFile
from django.db.models import Count, F, Q
from django.http import Http404, HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from aula import logica
from aula.models import Aula

from .models import ConversacionSalon, LecturaSalon, MensajeSalon
from .views import (MAX_TEXTO, POR_PAGINA, RESPUESTAS_ADULTO, RESPUESTAS_ESTUDIANTE, _adjunto, _json, dia_de,
                    fecha_corta, hora_de, vista_previa)

CLAVE_PIN = 'chat_salon_pin'
MAX_INTENTOS = 5


class Ctx:
    def __init__(self, request, pk):
        self.aula = get_object_or_404(Aula.objects.select_related('grupo__propietario__usuario'), pk=pk,
                                      grupo__isnull=False)
        self.grupo = self.aula.grupo
        c = logica.contexto(request, self.aula)
        self.docente = bool(c and c.es_docente)
        self.integrante = getattr(c, 'integrante', None) if c else None
        self.con_pin = bool(self.integrante and self.integrante.pk in request.session.get(CLAVE_PIN, []))
        self.request = request

    @property
    def nombre_docente(self):
        u = self.grupo.propietario.usuario
        return u.get_full_name() or u.username


def vista(fn):
    def envoltura(request, pk, *args, **kwargs):
        c = Ctx(request, pk)
        if not c.docente and c.integrante is None:
            return redirect('aula:entrar', pk=pk)
        return fn(request, c, *args, **kwargs)
    envoltura.__name__ = fn.__name__
    envoltura.__doc__ = fn.__doc__
    return envoltura


def del_grupo(grupo):
    conv = ConversacionSalon.objects.filter(grupo=grupo, integrante__isnull=True).first()
    return conv or ConversacionSalon.objects.create(grupo=grupo)


def privado(grupo, integrante):
    return ConversacionSalon.objects.get_or_create(grupo=grupo, integrante=integrante)[0]


def _conversacion(c, cid):
    """La conversación si esta persona la puede ver; si no, 404."""
    conv = get_object_or_404(ConversacionSalon.objects.select_related('integrante'), pk=cid, grupo=c.grupo)
    if c.docente:
        return conv
    if conv.integrante_id is None:
        return conv
    if c.con_pin and conv.integrante_id == c.integrante.pk:
        return conv
    raise Http404


def _puede_escribir(c, conv):
    if c.docente:
        return True
    return c.con_pin and (conv.integrante_id is not None or not conv.solo_lectura)


def _leido(c, conv):
    ahora = timezone.now()
    if c.docente:
        ConversacionSalon.objects.filter(pk=conv.pk).update(docente_leido=ahora)
    elif c.integrante is not None:
        LecturaSalon.objects.update_or_create(conversacion=conv, integrante=c.integrante, defaults={'ultimo_leido': ahora})


def no_leidos_docente(grupo):
    """{conversacion_id: mensajes de estudiantes que el docente no ha leído}."""
    filas = (MensajeSalon.objects.filter(conversacion__grupo=grupo, integrante__isnull=False, eliminado=False)
             .filter(Q(conversacion__docente_leido__isnull=True) | Q(creado__gt=F('conversacion__docente_leido')))
             .values('conversacion').annotate(n=Count('id')))
    return {f['conversacion']: f['n'] for f in filas}


def _no_leidos_estudiante(c, convs):
    lecturas = dict(LecturaSalon.objects.filter(integrante=c.integrante, conversacion__in=convs)
                    .values_list('conversacion_id', 'ultimo_leido'))
    salida = {}
    for conv in convs:
        qs = conv.mensajes.filter(eliminado=False).exclude(integrante=c.integrante)
        if lecturas.get(conv.pk):
            qs = qs.filter(creado__gt=lecturas[conv.pk])
        salida[conv.pk] = qs.count()
    return salida


def _json_mensaje(c, m):
    if m.integrante_id is None:
        autor, mio = c.nombre_docente + ' (docente)', c.docente
    else:
        autor, mio = m.integrante.completo, bool(c.integrante and m.integrante_id == c.integrante.pk)
    con_archivo = m.tipo in ('foto', 'voz') and bool(m.archivo) and not m.eliminado
    return {'id': m.pk, 'autor': autor, 'mio': mio, 'tipo': m.tipo, 'texto': '' if m.eliminado else m.texto,
            'eliminado': m.eliminado, 'duracion': m.duracion,
            'archivo': f'/aula/{c.aula.pk}/chat/m/{m.pk}/archivo/' if con_archivo else '',
            'hora': hora_de(m.creado), 'dia': dia_de(m.creado),
            'puede_borrar': not m.eliminado and (c.docente or mio)}


# ---------------------------------------------------------------------------
def _previa(conv):
    m = conv.mensajes.order_by('-creado', '-id').first()
    return vista_previa(m.texto, m.tipo, m.eliminado) if m else ''


def _lista(c):
    grupo_conv = del_grupo(c.grupo)
    base = f'/aula/{c.aula.pk}/chat/'
    if c.docente:
        pendientes = no_leidos_docente(c.grupo)
        privados = {x.integrante_id: x for x in ConversacionSalon.objects.filter(grupo=c.grupo, integrante__isnull=False)}
        filas = [{'url': f'{base}c/{grupo_conv.pk}/', 'titulo': 'Todo el grupo', 'grupo': True, 'id': grupo_conv.pk,
                  'previa': _previa(grupo_conv) or ('Solo usted escribe' if grupo_conv.solo_lectura
                                                     else 'Escriben usted y los estudiantes con PIN'),
                  'sin_leer': pendientes.get(grupo_conv.pk, 0), 'dt': grupo_conv.ultimo_mensaje}]
        estudiantes = []
        for i in c.grupo.integrantes.filter(activo=True):
            conv = privados.get(i.pk)
            estudiantes.append({'url': f'{base}con/{i.pk}/', 'titulo': i.completo, 'grupo': False,
                                'id': conv.pk if conv else None,
                                'previa': (_previa(conv) if conv else '') or 'Chat privado',
                                'sin_leer': pendientes.get(conv.pk, 0) if conv else 0,
                                'dt': conv.ultimo_mensaje if conv else None})
        estudiantes.sort(key=lambda f: (-f['sin_leer'], -(f['dt'].timestamp() if f['dt'] else 0)))
        filas += estudiantes
    else:
        convs = [grupo_conv] + ([privado(c.grupo, c.integrante)] if c.con_pin else [])
        pend = _no_leidos_estudiante(c, convs)
        filas = [{'url': f'{base}c/{x.pk}/', 'grupo': x.integrante_id is None, 'id': x.pk,
                  'titulo': 'Todo el grupo' if x.integrante_id is None else f'{c.nombre_docente} (docente)',
                  'previa': _previa(x) or ('Mensajes para toda la clase' if x.integrante_id is None
                                           else 'Su chat privado con el docente'),
                  'sin_leer': pend.get(x.pk, 0), 'dt': x.ultimo_mensaje} for x in convs]
    for f in filas:
        f['cuando'] = fecha_corta(f['dt'])
    return {'c': c, 'aula': c.aula, 'filas': filas, 'lista_tpl': 'chat/salon_lista.html', 'riel_tpl': 'chat/_riel_salon.html',
            'bloqueado': _bloqueado(c.integrante) if c.integrante else False}


@vista
def inicio(request, c):
    return render(request, 'chat/salon_inicio.html', _lista(c))


def _llave_intentos(integrante):
    return f'chat-salon-pin-{integrante.pk}'


def _bloqueado(integrante):
    return (cache.get(_llave_intentos(integrante)) or 0) >= MAX_INTENTOS


@require_POST
@vista
def pin(request, c):
    if c.integrante is None:
        raise Http404
    from django.contrib import messages
    if _bloqueado(c.integrante):
        messages.error(request, 'Demasiados intentos. Espere 15 minutos o pídale el PIN a su docente.')
    elif (request.POST.get('pin') or '').strip() == c.integrante.pin_chat:
        cache.delete(_llave_intentos(c.integrante))
        lista = [x for x in request.session.get(CLAVE_PIN, []) if x != c.integrante.pk] + [c.integrante.pk]
        request.session[CLAVE_PIN] = lista[-10:]
        messages.success(request, 'Listo. Ya puede escribir en el chat.')
    else:
        llave = _llave_intentos(c.integrante)
        cache.set(llave, (cache.get(llave) or 0) + 1, 15 * 60)
        messages.error(request, 'Ese PIN no es. Pídaselo a su docente.')
    return redirect('aula:chat', pk=c.aula.pk)


@vista
def con(request, c, iid):
    """El docente abre el chat privado con un estudiante."""
    if not c.docente:
        raise Http404
    integrante = get_object_or_404(c.grupo.integrantes, pk=iid)
    return redirect('aula:chat_conversacion', pk=c.aula.pk, cid=privado(c.grupo, integrante).pk)


@vista
def conversacion(request, c, cid):
    conv = _conversacion(c, cid)
    _leido(c, conv)
    qs = conv.mensajes.select_related('integrante')
    ultimos = list(qs.order_by('-creado', '-id')[:POR_PAGINA])[::-1]
    if conv.integrante_id is None:
        titulo, sub = 'Todo el grupo', f'{c.grupo.nombre} · {c.grupo.integrantes.filter(activo=True).count()} estudiantes'
    elif c.docente:
        titulo, sub = conv.integrante.completo, f'Chat privado · {c.grupo.nombre}'
    else:
        titulo, sub = c.nombre_docente, 'Docente · chat privado'
    base = f'/aula/{c.aula.pk}/chat/c/{conv.pk}/'
    if c.docente:
        cerrado = ''
    elif not c.con_pin:
        cerrado = 'Para escribir, ponga su PIN en la lista de chats.'
    else:
        cerrado = 'En este chat solo escribe el docente.'
    return render(request, 'chat/salon_conversacion.html', {
        **_lista(c), 'conv': conv, 'titulo': titulo, 'sub': sub, 'activa': conv.pk,
        'compartidos': [_json_mensaje(c, m) for m in conv.mensajes.filter(tipo__in=('foto', 'voz'), eliminado=False)
                        .exclude(archivo='').select_related('integrante').order_by('-creado', '-id')[:12]],
        'respuestas': RESPUESTAS_ADULTO if c.docente else RESPUESTAS_ESTUDIANTE,
        'mensajes': [_json_mensaje(c, m) for m in ultimos], 'hay_mas': qs.count() > POR_PAGINA,
        'puede_escribir': _puede_escribir(c, conv), 'mensaje_cerrado': cerrado,
        'cfg': {'nuevos': base + 'nuevos/', 'enviar': base + 'enviar/', 'accion': base + 'accion/', 'reportar': '',
                'autores': conv.integrante_id is None}})


@vista
def nuevos(request, c, cid):
    conv = _conversacion(c, cid)
    try:
        despues = int(request.GET.get('despues') or 0)
    except ValueError:
        despues = 0
    lista = list(conv.mensajes.select_related('integrante').filter(id__gt=despues)[:100])
    borrados = list(conv.mensajes.filter(id__lte=despues, eliminado=True).values_list('id', flat=True)[:200])
    if lista:
        _leido(c, conv)
    conv.refresh_from_db(fields=['solo_lectura'])
    return JsonResponse({'mensajes': [_json_mensaje(c, m) for m in lista], 'borrados': borrados,
                         'puede_escribir': _puede_escribir(c, conv)})


@require_POST
@vista
def enviar(request, c, cid):
    conv = _conversacion(c, cid)
    if not _puede_escribir(c, conv):
        return JsonResponse({'ok': False, 'error': 'Para escribir aquí necesita su PIN.' if not c.con_pin
                             else 'En este chat solo escribe el docente.'}, status=403)
    if request.content_type and request.content_type.startswith('multipart/'):
        texto = (request.POST.get('texto') or '').strip()[:MAX_TEXTO]
        try:
            adjunto = _adjunto(request)
        except ValueError as error:
            return JsonResponse({'ok': False, 'error': str(error)}, status=400)
    else:
        texto, adjunto = (_json(request).get('texto') or '').strip()[:MAX_TEXTO], None
    if not texto and adjunto is None:
        return JsonResponse({'ok': False, 'error': 'Escriba un mensaje.'}, status=400)
    autor = None if c.docente else c.integrante
    if adjunto is None:
        m = MensajeSalon.objects.create(conversacion=conv, integrante=autor, texto=texto)
    else:
        tipo, datos, nombre, segundos = adjunto
        m = MensajeSalon(conversacion=conv, integrante=autor, tipo=tipo, texto=texto if tipo == 'foto' else '',
                         peso=len(datos), duracion=segundos)
        m.archivo.save(nombre, ContentFile(datos), save=False)
        m.save()
    ConversacionSalon.objects.filter(pk=conv.pk).update(ultimo_mensaje=m.creado)
    _leido(c, conv)
    return JsonResponse({'ok': True, 'mensaje': _json_mensaje(c, m)})


@require_POST
@vista
def accion(request, c, cid):
    conv = _conversacion(c, cid)
    que = request.POST.get('accion')
    if que == 'borrar':
        m = get_object_or_404(MensajeSalon, pk=request.POST.get('mensaje') or 0, conversacion=conv)
        if c.docente or (c.con_pin and m.integrante_id == c.integrante.pk):
            MensajeSalon.objects.filter(pk=m.pk).update(eliminado=True)
        if request.headers.get('x-requested-with') == 'fetch':
            return JsonResponse({'ok': True})
    elif que == 'solo_lectura' and c.docente and conv.integrante_id is None:
        conv.solo_lectura = not conv.solo_lectura
        conv.save(update_fields=['solo_lectura'])
    return redirect('aula:chat_conversacion', pk=c.aula.pk, cid=conv.pk)


@vista
def archivo(request, c, mid):
    m = get_object_or_404(MensajeSalon, pk=mid, conversacion__grupo=c.grupo)
    _conversacion(c, m.conversacion_id)
    if not m.archivo or m.eliminado:
        raise Http404
    return redirect(m.archivo.url)


@vista
def pines(request, c):
    """Lista para imprimir con el PIN de cada estudiante. El docente puede cambiar uno."""
    if not c.docente:
        return HttpResponseForbidden('Solo el docente ve los PIN.')
    if request.method == 'POST':
        from salon_digital.models import pin_chat
        i = get_object_or_404(c.grupo.integrantes, pk=request.POST.get('integrante') or 0)
        i.pin_chat = pin_chat()
        i.save(update_fields=['pin_chat'])
        cache.delete(_llave_intentos(i))
        from django.contrib import messages
        messages.success(request, f'Nuevo PIN para {i.completo}: {i.pin_chat}')
        return redirect('aula:chat_pines', pk=c.aula.pk)
    return render(request, 'chat/salon_pines.html', {'c': c, 'aula': c.aula,
                                                       'integrantes': c.grupo.integrantes.filter(activo=True)})
