"""Chat interno del colegio."""
import json
from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Count, F, Max, OuterRef, Q, Subquery
from django.http import Http404, HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from notas.models import AsignacionDocente, Curso, Notificacion

from . import reglas as R
from .models import Conversacion, Mensaje, Participante, Reporte

MAX_TEXTO = 2000
POR_PAGINA = 60
MAX_VOZ = 5 * 1024 * 1024          # 5 MB: unos 5 minutos de nota de voz
MAX_DOC = 15 * 1024 * 1024
# Documentos que se pueden adjuntar (lo que usa un colegio): PDF, Word, Excel, PowerPoint y OpenDocument.
EXT_DOC = {'.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.odt', '.ods', '.odp', '.txt'}
MAX_SEGUNDOS_VOZ = 300
RESPUESTAS_ESTUDIANTE = ['¡Gracias profe!', 'Tengo una duda', 'Ya lo envié']
RESPUESTAS_ADULTO = ['Recibido ✅', 'Gracias', 'Lo reviso y le cuento']
EXT_AUDIO = {'audio/mpeg': '.mp3', 'audio/mp4': '.m4a', 'audio/x-m4a': '.m4a', 'audio/aac': '.aac',
             'audio/ogg': '.ogg', 'application/ogg': '.ogg', 'audio/webm': '.webm', 'video/webm': '.webm',
             'audio/wav': '.wav', 'audio/x-wav': '.wav'}


class Ctx:
    def __init__(self, request):
        self.request = request
        self.colegio = getattr(request, 'colegio', None)
        self.user = request.user
        self.rol = R.rol(request.user, self.colegio)

    @property
    def adulto(self):
        return self.rol in ('admin', 'docente')


def vista(fn):
    @login_required
    @wraps(fn)
    def envoltura(request, *args, **kwargs):
        c = Ctx(request)
        if c.colegio is None or c.rol is None:
            return HttpResponseForbidden('El chat es para las personas del colegio.')
        return fn(request, c, *args, **kwargs)
    return envoltura


def _json(request):
    try:
        d = json.loads(request.body or '{}')
    except ValueError:
        return {}
    return d if isinstance(d, dict) else {}


def _no_leidos(user, colegio):
    """{conversacion_id: mensajes sin leer} de esta persona."""
    filas = (Mensaje.objects.filter(Q(conversacion__colegio=colegio) & Q(conversacion__participantes__usuario=user)
                                    & Q(conversacion__participantes__activo=True)
                                    & (Q(conversacion__participantes__ultimo_leido__isnull=True)
                                       | Q(creado__gt=F('conversacion__participantes__ultimo_leido'))))
             .exclude(autor=user).exclude(eliminado=True)
             .values('conversacion').annotate(n=Count('id')))
    return {f['conversacion']: f['n'] for f in filas}


def _titulo(conv, user):
    if conv.tipo != 'directa':
        return conv.nombre
    otro = next((p.usuario for p in conv.participantes.all() if p.usuario_id != user.pk), None)
    return R.nombre_de(otro) if otro else 'Conversación'


def _conversacion(c, pk, auditar=False):
    """(conversación, participante). Un directivo puede abrir para revisar una conversación con reportes."""
    conv = get_object_or_404(Conversacion.objects.select_related('curso', 'asignacion'), pk=pk, colegio=c.colegio)
    R.sincronizar(conv)
    p = R.participante(conv, c.user)
    if p is None:
        if auditar and c.rol == 'admin' and Reporte.objects.filter(mensaje__conversacion=conv).exists():
            return conv, None
        raise Http404
    return conv, p


MESES = ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 'julio', 'agosto', 'septiembre', 'octubre',
         'noviembre', 'diciembre']


def dia_de(dt):
    """«Hoy», «Ayer» o «3 de noviembre», para los separadores del chat."""
    d = timezone.localtime(dt).date()
    hoy = timezone.localdate()
    if d == hoy:
        return 'Hoy'
    if (hoy - d).days == 1:
        return 'Ayer'
    return f'{d.day} de {MESES[d.month - 1]}' + ('' if d.year == hoy.year else f' de {d.year}')


def hora_de(dt):
    return timezone.localtime(dt).strftime('%I:%M %p').lstrip('0').replace('AM', 'a. m.').replace('PM', 'p. m.')


def fecha_corta(dt):
    """Para la lista de chats: la hora si es de hoy; si no, «Ayer» o el día."""
    if dt is None:
        return ''
    d = dia_de(dt)
    return hora_de(dt) if d == 'Hoy' else (d if d == 'Ayer' else timezone.localtime(dt).strftime('%d/%m/%y'))


def _mensaje_json(m, user, moderador):
    con_archivo = m.tipo in ('foto', 'voz', 'doc') and bool(m.archivo) and not m.eliminado
    return {'id': m.pk, 'autor': R.nombre_de(m.autor), 'mio': m.autor_id == user.pk, 'tipo': m.tipo,
            'nombre': m.nombre_archivo, 'peso_txt': peso_txt(m.peso) if m.tipo == 'doc' else '',
            'texto': '' if m.eliminado else m.texto, 'eliminado': m.eliminado,
            'archivo': f'/chat/m/{m.pk}/archivo/' if con_archivo else '', 'duracion': m.duracion,
            'hora': hora_de(m.creado), 'dia': dia_de(m.creado),
            'puede_borrar': not m.eliminado and (m.autor_id == user.pk or moderador)}


def vista_previa(texto, tipo, eliminado=False):
    if eliminado:
        return 'Mensaje eliminado'
    if tipo == 'foto':
        return '📷 ' + (texto or 'Foto')
    if tipo == 'voz':
        return '🎤 Nota de voz'
    if tipo == 'doc':
        return '📄 ' + (texto or 'Documento')
    return texto or ''


def _lista(c, request):
    """Lo que necesita la columna de chats (en el celular es la página de inicio; en el computador va al lado)."""
    pendientes = _no_leidos(c.user, c.colegio)
    ultimo = Mensaje.objects.filter(conversacion=OuterRef('pk')).order_by('-creado', '-id')
    convs = list(Conversacion.objects.filter(colegio=c.colegio, participantes__usuario=c.user,
                                             participantes__activo=True)
                 .annotate(u_texto=Subquery(ultimo.values('texto')[:1]), u_tipo=Subquery(ultimo.values('tipo')[:1]),
                           u_borrado=Subquery(ultimo.values('eliminado')[:1]),
                           u_nombre=Subquery(ultimo.values('nombre_archivo')[:1]))
                 .prefetch_related('participantes__usuario').distinct()[:150])
    filas = [{'c': x, 'titulo': _titulo(x, c.user), 'sin_leer': pendientes.get(x.pk, 0),
              'url': f'/chat/c/{x.pk}/', 'grupo': x.tipo != 'directa', 'cuando': fecha_corta(x.ultimo_mensaje),
              'previa': vista_previa(x.u_nombre if x.u_tipo == 'doc' else x.u_texto, x.u_tipo, x.u_borrado)
              if x.u_tipo else x.get_tipo_display()}
             for x in convs]
    q = (request.GET.get('q') or '').strip()[:60]
    encontrados = []
    if q:
        qs = R.contactos(c.user, c.colegio)
        for palabra in q.split()[:3]:
            qs = qs.filter(Q(first_name__icontains=palabra) | Q(last_name__icontains=palabra)
                           | Q(username__icontains=palabra))
        encontrados = [(u, R.etiqueta(u, c.colegio)) for u in qs.order_by('last_name', 'first_name')[:30]]
    return {'filas': filas, 'q': q, 'encontrados': encontrados, 'rol': c.rol, 'lista_tpl': 'chat/_lista.html', 'riel_tpl': 'chat/_riel.html',
            'grupos': R.grupos_disponibles(c.user, c.colegio) if c.adulto else [],
            'reportes_abiertos': Reporte.objects.filter(mensaje__conversacion__colegio=c.colegio, resuelto=False).count()
            if c.rol == 'admin' else 0}


def url_archivo(m):
    """Enlace al archivo; los documentos se descargan con su nombre original."""
    if m.tipo == 'doc' and m.nombre_archivo:
        from urllib.parse import quote
        disposicion = f"attachment; filename*=UTF-8''{quote(m.nombre_archivo)}"
        try:
            return m.archivo.storage.url(m.archivo.name, parameters={'ResponseContentDisposition': disposicion})
        except TypeError:                     # almacenamiento local (sin parámetros)
            pass
    return m.archivo.url


def peso_txt(n):
    if n >= 1024 * 1024:
        return f'{n / 1024 / 1024:.1f} MB'.replace('.', ',')
    return f'{max(1, round(n / 1024))} KB'


def nombre_limpio(nombre):
    """El nombre original del documento, sin rutas ni caracteres raros (máximo 150)."""
    import os
    nombre = os.path.basename((nombre or '').replace('\\', '/'))
    nombre = ''.join(ch for ch in nombre if ch.isprintable() and ch not in '"<>|:*?')
    return nombre.strip()[-150:] or 'documento'


def _adjunto(request, conv=None, fotos=True, voz=True, documentos=True):
    """(tipo, bytes, nombre para guardar, segundos, nombre original) del archivo que llegó, o ValueError."""
    import os
    f = request.FILES.get('archivo')
    if f is None:
        return None
    if conv is not None:
        aj = R.ajustes(conv.colegio)
        fotos, voz, documentos = aj.permitir_fotos, aj.permitir_voz, aj.permitir_documentos
    mime = (getattr(f, 'content_type', '') or '').lower().split(';')[0]
    ext = os.path.splitext(f.name or '')[1].lower()
    if ext in EXT_DOC or request.POST.get('tipo') == 'doc':
        if not documentos:
            raise ValueError('El colegio no tiene activado el envío de documentos por el chat.')
        if ext not in EXT_DOC:
            raise ValueError('Ese tipo de archivo no se puede enviar. Sirven PDF, Word, Excel, PowerPoint y texto.')
        datos = f.read(MAX_DOC + 1)
        if len(datos) > MAX_DOC:
            raise ValueError('El documento pasa de 15 MB.')
        if not datos:
            raise ValueError('El documento llegó vacío.')
        original = nombre_limpio(f.name)
        return 'doc', datos, f'documento{ext}', 0, original
    if mime.startswith('image/'):
        if not fotos:
            raise ValueError('El colegio no tiene activado el envío de fotos por el chat.')
        from materiales.views import preparar_imagen
        datos, ext, _, _ = preparar_imagen(f)
        return 'foto', datos, f'foto{ext}', 0, ''
    if mime in EXT_AUDIO or mime.startswith('audio/'):
        if not voz:
            raise ValueError('El colegio no tiene activadas las notas de voz.')
        datos = f.read(MAX_VOZ + 1)
        if len(datos) > MAX_VOZ:
            raise ValueError('La nota de voz es muy larga (máximo 5 minutos).')
        if not datos:
            raise ValueError('La nota de voz llegó vacía.')
        try:
            segundos = max(0, min(MAX_SEGUNDOS_VOZ, int(float(request.POST.get('duracion') or 0))))
        except ValueError:
            segundos = 0
        return 'voz', datos, f'voz{EXT_AUDIO.get(mime, ".webm")}', segundos, ''
    raise ValueError('Solo se pueden enviar fotos, notas de voz y documentos (PDF, Word, Excel, PowerPoint).')


# ---------------------------------------------------------------------------
# Lista de conversaciones
# ---------------------------------------------------------------------------
@vista
def inicio(request, c):
    return render(request, 'chat/inicio.html', _lista(c, request))


@vista
def no_leidos(request, c):
    return JsonResponse({'n': sum(_no_leidos(c.user, c.colegio).values())})


@require_POST
@vista
def nueva(request, c):
    otro = get_object_or_404(User, pk=request.POST.get('usuario') or 0)
    if not R.puede_hablar(c.user, otro, c.colegio):
        messages.error(request, 'Con esa persona no se puede abrir un chat.')
        return redirect('chat:inicio')
    conv = R.directa(c.colegio, c.user, otro)
    return redirect('chat:conversacion', pk=conv.pk)


@require_POST
@vista
def abrir_grupo(request, c):
    if not c.adulto:
        raise Http404
    tipo = request.POST.get('tipo')
    disponibles = R.grupos_disponibles(c.user, c.colegio)
    if tipo == 'profesores':
        conv = R.sala_profesores(c.colegio, c.user)
    elif tipo == 'curso':
        curso = get_object_or_404(Curso, pk=request.POST.get('id') or 0, colegio=c.colegio)
        if not any(t == 'curso' and o.pk == curso.pk for t, o, _ in disponibles):
            raise Http404
        conv = R.grupo_curso(c.colegio, curso, c.user)
    elif tipo == 'asignatura':
        a = get_object_or_404(AsignacionDocente, pk=request.POST.get('id') or 0, colegio=c.colegio)
        if not any(t == 'asignatura' and o.pk == a.pk for t, o, _ in disponibles):
            raise Http404
        conv = R.grupo_asignatura(c.colegio, a, c.user)
    else:
        raise Http404
    return redirect('chat:conversacion', pk=conv.pk)


@vista
def grupo_nuevo(request, c):
    """Un grupo que arma el docente o el directivo con las personas que escoja (de sus contactos)."""
    if not c.adulto:
        raise Http404
    contactos = R.contactos(c.user, c.colegio)
    if request.method == 'POST':
        nombre = ' '.join((request.POST.get('nombre') or '').split())[:80]
        ids = {int(x) for x in request.POST.getlist('miembros') if str(x).isdigit()}
        elegidos = list(contactos.filter(pk__in=ids))
        if not nombre or not elegidos:
            messages.error(request, 'Escriba el nombre del grupo y escoja al menos una persona.')
        else:
            conv = Conversacion.objects.create(colegio=c.colegio, tipo='grupo', nombre=nombre, creada_por=c.user,
                                               solo_lectura=request.POST.get('solo_lectura') == 'on')
            Participante.objects.bulk_create([Participante(conversacion=conv, usuario=c.user, moderador=True)] +
                                             [Participante(conversacion=conv, usuario=u) for u in elegidos])
            return redirect('chat:conversacion', pk=conv.pk)
    q = (request.GET.get('q') or '').strip()[:60]
    lista = contactos
    for palabra in q.split()[:3]:
        lista = lista.filter(Q(first_name__icontains=palabra) | Q(last_name__icontains=palabra))
    personas = [(u, R.etiqueta(u, c.colegio)) for u in lista.order_by('last_name', 'first_name')[:200]]
    return render(request, 'chat/grupo_nuevo.html', {'personas': personas, 'q': q})


# ---------------------------------------------------------------------------
# Una conversación
# ---------------------------------------------------------------------------
@vista
def conversacion(request, c, pk):
    conv, p = _conversacion(c, pk, auditar=True)
    auditoria = p is None
    mensajes_qs = conv.mensajes.select_related('autor')
    ultimos = list(mensajes_qs.order_by('-creado', '-id')[:POR_PAGINA])[::-1]
    if p is not None:
        p.ultimo_leido = timezone.now()
        p.save(update_fields=['ultimo_leido'])
        Notificacion.objects.filter(destinatario=c.user, url=f'/chat/c/{conv.pk}/', leido=False).update(leido=True)
    moderador = bool(p and p.moderador)
    participantes = [(x.usuario, R.etiqueta(x.usuario, c.colegio), x.moderador)
                     for x in conv.participantes.filter(activo=True).select_related('usuario')
                     .order_by('-moderador', 'usuario__last_name', 'usuario__first_name')]
    return render(request, 'chat/conversacion.html', {
        'conv': conv, 'p': p, 'titulo': _titulo(conv, c.user), 'auditoria': auditoria, 'moderador': moderador,
        'puede_escribir': R.puede_escribir(conv, p) and not auditoria, 'participantes': participantes,
        'mensajes': [dict(_mensaje_json(m, c.user, moderador), texto_auditoria=m.texto if auditoria else '',
                          archivo_auditoria=f'/chat/m/{m.pk}/archivo/' if auditoria and m.archivo else '')
                     for m in ultimos],
        'hay_mas': mensajes_qs.count() > POR_PAGINA, 'rol': c.rol,
        'reportados': set(Reporte.objects.filter(mensaje__conversacion=conv).values_list('mensaje_id', flat=True))
        if auditoria else set(),
        'silencio': R.en_silencio(c.colegio), 'aj': R.ajustes(c.colegio), 'activa': conv.pk,
        'compartidos': [_mensaje_json(m, c.user, moderador) for m in
                        conv.mensajes.filter(tipo__in=('foto', 'voz', 'doc'), eliminado=False).exclude(archivo='')
                        .select_related('autor').order_by('-creado', '-id')[:12]] if not auditoria else [],
        'respuestas': RESPUESTAS_ESTUDIANTE if c.rol == 'estudiante' else RESPUESTAS_ADULTO,
        **_lista(c, request),
        'cfg': {'nuevos': f'/chat/c/{conv.pk}/nuevos/', 'enviar': f'/chat/c/{conv.pk}/enviar/',
                'accion': f'/chat/c/{conv.pk}/accion/', 'reportar': '/chat/m/ID/reportar/',
                'autores': conv.tipo != 'directa'}})


@vista
def nuevos(request, c, pk):
    """Los mensajes después de ?despues=<id> (la página pregunta cada pocos segundos)."""
    conv, p = _conversacion(c, pk)
    try:
        despues = int(request.GET.get('despues') or 0)
    except ValueError:
        despues = 0
    lista = list(conv.mensajes.select_related('autor').filter(id__gt=despues)[:100])
    # Los borrados que ya estaban en pantalla
    borrados = list(conv.mensajes.filter(id__lte=despues, eliminado=True).values_list('id', flat=True)[:200])
    if lista:
        p.ultimo_leido = timezone.now()
        p.save(update_fields=['ultimo_leido'])
        Notificacion.objects.filter(destinatario=c.user, url=f'/chat/c/{conv.pk}/', leido=False).update(leido=True)
    conv.refresh_from_db(fields=['solo_lectura'])
    return JsonResponse({'mensajes': [_mensaje_json(m, c.user, p.moderador) for m in lista], 'borrados': borrados,
                         'puede_escribir': R.puede_escribir(conv, p)})


@require_POST
@vista
def enviar(request, c, pk):
    conv, p = _conversacion(c, pk)
    if not R.puede_escribir(conv, p):
        return JsonResponse({'ok': False, 'error': 'En este grupo solo escriben los docentes.'}, status=403)
    if request.content_type and request.content_type.startswith('multipart/'):
        texto = (request.POST.get('texto') or '').strip()[:MAX_TEXTO]
        try:
            adjunto = _adjunto(request, conv)
        except ValueError as error:
            return JsonResponse({'ok': False, 'error': str(error)}, status=400)
    else:
        texto, adjunto = (_json(request).get('texto') or '').strip()[:MAX_TEXTO], None
    if not texto and adjunto is None:
        return JsonResponse({'ok': False, 'error': 'Escriba un mensaje.'}, status=400)
    if adjunto is None:
        m = Mensaje.objects.create(conversacion=conv, autor=c.user, texto=texto)
    else:
        from django.core.files.base import ContentFile
        tipo, datos, nombre, segundos, original = adjunto
        m = Mensaje(conversacion=conv, autor=c.user, texto=texto if tipo in ('foto', 'doc') else '', tipo=tipo,
                    peso=len(datos), duracion=segundos, nombre_archivo=original)
        m.archivo.save(nombre, ContentFile(datos), save=False)
        m.save()
    Conversacion.objects.filter(pk=conv.pk).update(ultimo_mensaje=m.creado)
    p.ultimo_leido = m.creado
    p.save(update_fields=['ultimo_leido'])
    R.avisar(m)
    return JsonResponse({'ok': True, 'mensaje': _mensaje_json(m, c.user, p.moderador)})


@require_POST
@vista
def accion(request, c, pk):
    conv, p = _conversacion(c, pk)
    que = request.POST.get('accion')
    if que == 'silenciar':
        p.silenciada = not p.silenciada
        p.save(update_fields=['silenciada'])
        messages.info(request, 'No le llegarán avisos de este chat.' if p.silenciada else 'Volverá a recibir avisos de este chat.')
    elif que == 'solo_lectura' and p.moderador and conv.tipo != 'directa':
        conv.solo_lectura = not conv.solo_lectura
        conv.save(update_fields=['solo_lectura'])
        messages.success(request, 'Ahora solo escriben los moderadores.' if conv.solo_lectura else 'Todos pueden escribir.')
    elif que == 'borrar':
        m = get_object_or_404(Mensaje, pk=request.POST.get('mensaje') or 0, conversacion=conv)
        if m.autor_id == c.user.pk or p.moderador:
            m.eliminado, m.eliminado_por = True, c.user
            m.save(update_fields=['eliminado', 'eliminado_por'])
        if request.headers.get('x-requested-with') == 'fetch':
            return JsonResponse({'ok': True})
    elif que == 'salir' and conv.tipo == 'grupo':
        p.activo = False
        p.save(update_fields=['activo'])
        messages.info(request, f'Salió de «{conv.nombre}».')
        return redirect('chat:inicio')
    elif que == 'agregar' and conv.tipo == 'grupo' and p.moderador:
        ids = {int(x) for x in request.POST.getlist('miembros') if str(x).isdigit()}
        for u in R.contactos(c.user, c.colegio).filter(pk__in=ids):
            Participante.objects.update_or_create(conversacion=conv, usuario=u, defaults={'activo': True})
        messages.success(request, 'Personas agregadas al grupo.')
    elif que == 'quitar' and conv.tipo == 'grupo' and p.moderador:
        Participante.objects.filter(conversacion=conv, usuario_id=request.POST.get('usuario') or 0, moderador=False) \
            .update(activo=False)
    return redirect('chat:conversacion', pk=conv.pk)


@require_POST
@vista
def reportar(request, c, mid):
    m = get_object_or_404(Mensaje.objects.select_related('conversacion'), pk=mid, conversacion__colegio=c.colegio)
    p = R.participante(m.conversacion, c.user)
    if p is None or m.autor_id == c.user.pk:
        raise Http404
    motivo = ' '.join((request.POST.get('motivo') or '').split())[:300] or 'Sin motivo'
    _, nuevo = Reporte.objects.get_or_create(mensaje=m, usuario=c.user, defaults={'motivo': motivo})
    if nuevo:
        from notas.models import AdministradorColegio
        Notificacion.objects.bulk_create([
            Notificacion(colegio=c.colegio, destinatario_id=uid, tipo='GENERAL', url='/chat/administrar/',
                         mensaje=f'Reportaron un mensaje del chat: {motivo}'[:255])
            for uid in AdministradorColegio.objects.filter(colegio=c.colegio, activo=True).values_list('user_id', flat=True)])
    messages.info(request, 'Gracias. Los directivos del colegio van a revisar el mensaje.')
    return redirect('chat:conversacion', pk=m.conversacion_id)


@vista
def archivo(request, c, mid):
    """La foto o la nota de voz de un mensaje: solo para quienes están en la conversación (o un directivo
    que revisa una conversación con reportes). El enlace firmado vence a las pocas horas."""
    m = get_object_or_404(Mensaje.objects.select_related('conversacion'), pk=mid, conversacion__colegio=c.colegio)
    _, p = _conversacion(c, m.conversacion_id, auditar=True)
    if not m.archivo or (m.eliminado and p is not None):
        raise Http404
    return redirect(url_archivo(m))


# ---------------------------------------------------------------------------
# Administración: reportes y horario de silencio
# ---------------------------------------------------------------------------
@vista
def administrar(request, c):
    if c.rol != 'admin':
        return HttpResponseForbidden('Solo los directivos del colegio.')
    aj = R.ajustes(c.colegio)
    if request.method == 'POST':
        if request.POST.get('accion') == 'silencio':
            from datetime import time
            try:
                aj.silencio_desde = time.fromisoformat(request.POST.get('desde') or '18:00')
                aj.silencio_hasta = time.fromisoformat(request.POST.get('hasta') or '06:00')
            except ValueError:
                messages.error(request, 'Revise las horas.')
                return redirect('chat:administrar')
            aj.silencio_fin_de_semana = request.POST.get('fin_de_semana') == 'on'
            aj.permitir_fotos = request.POST.get('fotos') == 'on'
            aj.permitir_voz = request.POST.get('voz') == 'on'
            aj.permitir_documentos = request.POST.get('documentos') == 'on'
            aj.save()
            messages.success(request, 'Ajustes del chat guardados.')
        elif request.POST.get('accion') == 'resolver':
            r = get_object_or_404(Reporte, pk=request.POST.get('reporte') or 0, mensaje__conversacion__colegio=c.colegio)
            r.resuelto, r.resuelto_por = True, c.user
            r.nota = ' '.join((request.POST.get('nota') or '').split())[:300]
            r.save(update_fields=['resuelto', 'resuelto_por', 'nota'])
            if request.POST.get('borrar') == 'on':
                Mensaje.objects.filter(pk=r.mensaje_id).update(eliminado=True, eliminado_por=c.user)
            messages.success(request, 'Reporte cerrado.')
        return redirect('chat:administrar')
    reportes = Reporte.objects.filter(mensaje__conversacion__colegio=c.colegio) \
        .select_related('mensaje__autor', 'mensaje__conversacion', 'usuario', 'resuelto_por')[:100]
    return render(request, 'chat/administrar.html', {'aj': aj, 'reportes': reportes, 'silencio': R.en_silencio(c.colegio)})
