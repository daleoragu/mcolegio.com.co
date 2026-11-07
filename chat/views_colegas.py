"""Mis colegas (solo plan individual, Mi Salón Virtual): los docentes con cuenta del Salón se agregan como
colegas, se escriben uno a uno y arman grupos de docentes. Nunca estudiantes ni cuentas de los colegios.

  · Para escribirle a alguien uno a uno, los dos deben ser colegas (uno envía la solicitud y el otro la acepta).
  · Los grupos de docentes los arma cualquiera con sus colegas; quien lo crea es moderador y puede agregar o quitar.
  · Cada docente decide si aparece cuando otros buscan colegas, y puede quitar o bloquear a quien quiera.
  · Se reutiliza el chat del colegio (mensajes, fotos, notas de voz, documentos): son conversaciones sin colegio.
"""
from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.cache import cache
from django.db import IntegrityError, transaction
from django.db.models import Count, F, OuterRef, Q, Subquery
from django.http import Http404, HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from notas.models import AdministradorColegio, Docente, Notificacion

from .models import Colega, Conversacion, Mensaje, Participante, PerfilColega
from .views import (MAX_TEXTO, POR_PAGINA, RESPUESTAS_ADULTO, _adjunto, _json, _mensaje_json, fecha_corta,
                    vista_previa)

TIPOS = ('colegas', 'colegas_g')
SOLICITUDES_DIA = 40          # para que nadie llene de solicitudes a los demás
BASE = '/chat/colegas'


# ---------------------------------------------------------------------------
# Quién es docente y cómo se presenta
# ---------------------------------------------------------------------------
def docentes():
    """Los docentes del plan individual (con cuenta de Mi Salón Virtual), activos."""
    return User.objects.filter(is_active=True, cuenta_salon__isnull=False)


def es_docente(user):
    return bool(user and user.is_authenticated and user.is_active and docentes().filter(pk=user.pk).exists())


def nombre_de(u):
    cuenta = getattr(u, 'cuenta_salon', None) if _tiene(u, 'cuenta_salon') else None
    return u.get_full_name() or (cuenta.nombre_publico if cuenta else '') or u.username


def _tiene(u, rel):
    try:
        return getattr(u, rel) is not None
    except Exception:
        return False


def descripcion(u):
    """«Docente · Colegio San José» · «Docente independiente · Líbano, Tolima» + el área si la puso."""
    partes = []
    d = Docente.objects.filter(user=u).select_related('colegio').first()
    if d:
        partes.append(f'Docente · {d.colegio.nombre}')
    else:
        a = AdministradorColegio.objects.filter(user=u, activo=True).select_related('colegio').first()
        if a:
            partes.append(f'{a.get_cargo_display()} · {a.colegio.nombre}')
    if _tiene(u, 'cuenta_salon'):
        c = u.cuenta_salon
        lugar = ', '.join(x for x in (c.municipio, c.departamento) if x)
        if not partes:
            partes.append('Docente' + (f' · {c.institucion}' if c.institucion else ' independiente') + (f' · {lugar}' if lugar else ''))
    perfil = PerfilColega.objects.filter(usuario=u).first()
    if perfil and perfil.municipio and not any(perfil.municipio in x for x in partes):
        partes.append(perfil.municipio)
    if perfil and perfil.area:
        partes.append(perfil.area)
    return ' · '.join(partes) or 'Docente'


def perfil_de(u):
    return PerfilColega.objects.get_or_create(usuario=u)[0]


def foto_de(u):
    """La foto de perfil: la de Mis colegas o, si no subió, la de su ficha de docente del colegio."""
    perfil = PerfilColega.objects.filter(usuario=u).exclude(foto='').first()
    if perfil:
        return perfil.foto.url
    d = Docente.objects.filter(user=u).select_related('ficha').first()
    try:
        return d.ficha.foto.url if d and d.ficha.foto else ''
    except Exception:
        return ''


def tarjeta(u):
    """Lo que se muestra de un colega en listas y búsquedas."""
    return {'u': u, 'nombre': nombre_de(u), 'desc': descripcion(u), 'foto': foto_de(u)}


# ---------------------------------------------------------------------------
# Relaciones
# ---------------------------------------------------------------------------
def relacion(a, b):
    return Colega.objects.filter(Q(de=a, para=b) | Q(de=b, para=a)).first()


def son_colegas(a, b):
    return Colega.objects.filter(Q(de=a, para=b) | Q(de=b, para=a), estado='aceptada').exists()


def bloqueo(a, b):
    return Colega.objects.filter(Q(de=a, para=b) | Q(de=b, para=a), estado='bloqueada').exists()


def mis_colegas(user):
    ids = set(Colega.objects.filter(de=user, estado='aceptada').values_list('para_id', flat=True)) | \
        set(Colega.objects.filter(para=user, estado='aceptada').values_list('de_id', flat=True))
    return User.objects.filter(pk__in=ids, is_active=True)


def avisar(destino, texto, url=f'{BASE}/'):
    d = Docente.objects.filter(user=destino).first()
    Notificacion.objects.bulk_create([Notificacion(colegio=d.colegio if d else None, destinatario=destino, tipo='MENSAJE',
                                                   url=url, mensaje=texto[:255])])


def avisar_mensaje(m):
    """Una notificación por conversación (no una por mensaje), como en el chat del colegio."""
    conv = m.conversacion
    url = f'{BASE}/c/{conv.pk}/'
    destinos = list(Participante.objects.filter(conversacion=conv, activo=True, silenciada=False)
                    .exclude(usuario=m.autor).values_list('usuario_id', flat=True))
    ya = set(Notificacion.objects.filter(destinatario_id__in=destinos, url=url, leido=False).values_list('destinatario_id', flat=True))
    autor = nombre_de(m.autor)
    contenido = vista_previa(m.nombre_archivo if m.tipo == 'doc' else m.texto, m.tipo)
    texto = f'{autor}: {contenido}' if conv.tipo == 'colegas' else f'{conv.nombre} · {autor}: {contenido}'
    colegios = dict(Docente.objects.filter(user_id__in=destinos).values_list('user_id', 'colegio_id'))
    Notificacion.objects.bulk_create([Notificacion(colegio_id=colegios.get(uid), destinatario_id=uid, tipo='MENSAJE', url=url,
                                                   mensaje=texto[:255]) for uid in destinos if uid not in ya])


# ---------------------------------------------------------------------------
# Vistas
# ---------------------------------------------------------------------------
def vista(fn):
    @login_required
    @wraps(fn)
    def envoltura(request, *args, **kwargs):
        if not es_docente(request.user):
            return HttpResponseForbidden('Mis colegas es para los docentes del plan individual (Mi Salón Virtual).')
        return fn(request, *args, **kwargs)
    return envoltura


def _no_leidos(user):
    # todo en un solo filter(): así «ultimo_leido» es el de esta persona y no el de otro participante
    filas = (Mensaje.objects.filter(Q(conversacion__colegio__isnull=True) & Q(conversacion__tipo__in=TIPOS)
                                    & Q(conversacion__participantes__usuario=user) & Q(conversacion__participantes__activo=True)
                                    & (Q(conversacion__participantes__ultimo_leido__isnull=True)
                                       | Q(creado__gt=F('conversacion__participantes__ultimo_leido'))))
             .exclude(autor=user).exclude(eliminado=True).values('conversacion').annotate(n=Count('id')))
    return {f['conversacion']: f['n'] for f in filas}


def _titulo(conv, user):
    if conv.tipo == 'colegas_g':
        return conv.nombre
    otro = next((p.usuario for p in conv.participantes.all() if p.usuario_id != user.pk), None)
    return nombre_de(otro) if otro else 'Colega'


def _volver(user):
    """A dónde regresa la flecha: el panel del colegio o Mis aulas (Salón Digital)."""
    return '/aula/'


def _lista(request, activa=None):
    user = request.user
    pendientes = _no_leidos(user)
    ultimo = Mensaje.objects.filter(conversacion=OuterRef('pk')).order_by('-creado', '-id')
    convs = list(Conversacion.objects.filter(colegio__isnull=True, tipo__in=TIPOS, participantes__usuario=user,
                                             participantes__activo=True)
                 .annotate(u_texto=Subquery(ultimo.values('texto')[:1]), u_tipo=Subquery(ultimo.values('tipo')[:1]),
                           u_borrado=Subquery(ultimo.values('eliminado')[:1]), u_nombre=Subquery(ultimo.values('nombre_archivo')[:1]))
                 .prefetch_related('participantes__usuario').distinct()[:150])
    filas = [{'c': x, 'titulo': _titulo(x, user), 'sin_leer': pendientes.get(x.pk, 0), 'url': f'{BASE}/c/{x.pk}/',
              'foto': '' if x.tipo == 'colegas_g' else foto_de(next((p.usuario for p in x.participantes.all() if p.usuario_id != user.pk), user)),
              'grupo': x.tipo == 'colegas_g', 'cuando': fecha_corta(x.ultimo_mensaje),
              'previa': vista_previa(x.u_nombre if x.u_tipo == 'doc' else x.u_texto, x.u_tipo, x.u_borrado) if x.u_tipo
              else ('Grupo de docentes' if x.tipo == 'colegas_g' else 'Escríbale a su colega')} for x in convs]
    return {'filas': filas, 'activa': activa, 'lista_tpl': 'chat/colegas_lista.html', 'riel_tpl': 'chat/_riel_colegas.html',
            'volver': _volver(user), 'es_del_colegio': False,
            'n_solicitudes': Colega.objects.filter(para=user, estado='pendiente').count(),
            'n_avisos': Notificacion.objects.filter(destinatario=user, leido=False).count(), 'mi_foto': foto_de(user)}


@vista
def inicio(request):
    user = request.user
    q = ' '.join((request.GET.get('q') or '').split())[:60]
    encontrados = []
    if q:
        bloquearon = Colega.objects.filter(para=user, estado='bloqueada').values_list('de_id', flat=True)
        qs = docentes().exclude(pk=user.pk).exclude(pk__in=bloquearon).exclude(perfil_colega__visible=False)
        for palabra in q.split()[:3]:
            qs = qs.filter(Q(first_name__icontains=palabra) | Q(last_name__icontains=palabra) | Q(email__iexact=palabra)
                           | Q(cuenta_salon__nombre_publico__icontains=palabra) | Q(cuenta_salon__institucion__icontains=palabra)
                           | Q(perfil_colega__area__icontains=palabra) | Q(perfil_colega__municipio__icontains=palabra))
        for u in qs.distinct().order_by('first_name', 'last_name')[:40]:
            r = relacion(user, u)
            estado = 'ninguna' if r is None else ('enviada' if r.estado == 'pendiente' and r.de_id == user.pk else
                                                  'recibida' if r.estado == 'pendiente' else
                                                  'bloqueado' if r.estado == 'bloqueada' else 'colegas')
            encontrados.append(dict(tarjeta(u), estado=estado))
    recibidas = [dict(tarjeta(s.de), s=s) for s in Colega.objects.filter(para=user, estado='pendiente').select_related('de')]
    enviadas = [dict(tarjeta(s.para), s=s) for s in Colega.objects.filter(de=user, estado='pendiente').select_related('para')]
    colegas = sorted((tarjeta(u) for u in mis_colegas(user)), key=lambda x: x['nombre'].lower())
    bloqueados = [{'s': s, 'nombre': nombre_de(s.para)} for s in Colega.objects.filter(de=user, estado='bloqueada').select_related('para')]
    # Lo que ya está viendo deja de salir como aviso nuevo
    tab = request.GET.get('tab') or ''
    vistas = [f'{BASE}/?tab=solicitudes'] if (tab == 'solicitudes' or (not tab and not q and recibidas)) else [f'{BASE}/'] if not q and tab in ('', 'colegas') else []
    if vistas:
        Notificacion.objects.filter(destinatario=user, url__in=vistas, leido=False).update(leido=True)
    return render(request, 'chat/colegas_inicio.html', dict(
        _lista(request), q=q, encontrados=encontrados, recibidas=recibidas, enviadas=enviadas, colegas=colegas,
        bloqueados=bloqueados, perfil=perfil_de(user), mi_desc=descripcion(user), tab=request.GET.get('tab') or ''))


@require_POST
@vista
def solicitud(request):
    user = request.user
    otro = get_object_or_404(User, pk=request.POST.get('usuario') or 0)
    que = request.POST.get('accion')
    volver = redirect(request.POST.get('volver') if (request.POST.get('volver') or '').startswith(f'{BASE}/') else f'{BASE}/')
    if otro.pk == user.pk:
        return volver
    with transaction.atomic():
        r = relacion(user, otro)
        if que == 'enviar':
            if not es_docente(otro):
                messages.error(request, 'Solo se pueden agregar docentes.')
            elif r is not None and r.estado == 'bloqueada':
                messages.error(request, 'No se puede enviar la solicitud a esta persona.')
            elif r is not None and r.estado == 'aceptada':
                messages.info(request, f'{nombre_de(otro)} ya es su colega.')
            elif r is not None and r.para_id == user.pk:          # ya le había enviado una: queda aceptada
                r.estado, r.respondida = 'aceptada', timezone.now()
                r.save(update_fields=['estado', 'respondida'])
                avisar(otro, f'{nombre_de(user)} aceptó su solicitud: ya son colegas.')
                messages.success(request, f'Ahora usted y {nombre_de(otro)} son colegas.')
            elif r is not None:
                messages.info(request, 'La solicitud ya está enviada.')
            else:
                clave = f'colegas-solicitudes:{user.pk}:{timezone.localdate()}'
                if (cache.get(clave) or 0) >= SOLICITUDES_DIA:
                    messages.error(request, f'Por hoy ya envió {SOLICITUDES_DIA} solicitudes. Mañana puede enviar más.')
                else:
                    cache.set(clave, (cache.get(clave) or 0) + 1, 86400)
                    try:
                        Colega.objects.create(de=user, para=otro, mensaje=' '.join((request.POST.get('mensaje') or '').split())[:200])
                    except IntegrityError:
                        pass
                    avisar(otro, f'{nombre_de(user)} quiere ser su colega en mcolegio.', f'{BASE}/?tab=solicitudes')
                    messages.success(request, f'Solicitud enviada a {nombre_de(otro)}.')
        elif que == 'aceptar' and r is not None and r.estado == 'pendiente' and r.para_id == user.pk:
            r.estado, r.respondida = 'aceptada', timezone.now()
            r.save(update_fields=['estado', 'respondida'])
            avisar(otro, f'{nombre_de(user)} aceptó su solicitud: ya son colegas.')
            messages.success(request, f'Ahora usted y {nombre_de(otro)} son colegas.')
        elif que == 'rechazar' and r is not None and r.estado == 'pendiente' and r.para_id == user.pk:
            r.delete()
            messages.info(request, 'Solicitud rechazada.')
        elif que == 'cancelar' and r is not None and r.estado == 'pendiente' and r.de_id == user.pk:
            r.delete()
            messages.info(request, 'Solicitud cancelada.')
        elif que == 'quitar' and r is not None and r.estado == 'aceptada':
            r.delete()
            messages.info(request, f'{nombre_de(otro)} ya no está entre sus colegas.')
        elif que == 'bloquear':
            Colega.objects.filter(Q(de=user, para=otro) | Q(de=otro, para=user)).delete()
            Colega.objects.create(de=user, para=otro, estado='bloqueada', respondida=timezone.now())
            messages.info(request, f'Bloqueó a {nombre_de(otro)}: no le podrá escribir ni enviarle solicitudes.')
        elif que == 'desbloquear' and r is not None and r.estado == 'bloqueada' and r.de_id == user.pk:
            r.delete()
            messages.info(request, f'Desbloqueó a {nombre_de(otro)}.')
    return volver


@require_POST
@vista
def ajustes(request):
    p = perfil_de(request.user)
    p.visible = request.POST.get('visible') == 'on'
    p.area = ' '.join((request.POST.get('area') or '').split())[:80]
    p.presentacion = ' '.join((request.POST.get('presentacion') or '').split())[:200]
    p.grados = ' '.join((request.POST.get('grados') or '').split())[:60]
    p.municipio = ' '.join((request.POST.get('municipio') or '').split())[:100]
    if request.POST.get('quitar_foto') == 'on' and p.foto:
        p.foto.delete(save=False)
        p.foto = ''
    f = request.FILES.get('foto')
    if f is not None:
        from django.core.files.base import ContentFile
        from PIL import Image, ImageOps
        import io
        try:
            from materiales.views import preparar_imagen
            datos, ext, _, _ = preparar_imagen(f)
            im = ImageOps.fit(Image.open(io.BytesIO(datos)).convert('RGB'), (400, 400))     # cuadrada, 400 × 400
            salida = io.BytesIO(); im.save(salida, 'JPEG', quality=85, optimize=True)
            if p.foto:
                p.foto.delete(save=False)
            p.foto.save(f'colega-{request.user.pk}.jpg', ContentFile(salida.getvalue()), save=False)
        except ValueError as error:
            messages.error(request, str(error))
            return redirect(f'{BASE}/?tab=perfil')
    p.save()
    messages.success(request, 'Perfil de colega guardado.')
    return redirect(f'{BASE}/?tab=perfil')


def directa(a, b):
    """La conversación uno a uno entre dos colegas (la misma siempre)."""
    x, y = sorted([a.pk, b.pk])
    conv, nueva = Conversacion.objects.get_or_create(colegio=None, clave=f'cd:{x}-{y}', defaults={'tipo': 'colegas', 'creada_por': a})
    if nueva:
        Participante.objects.bulk_create([Participante(conversacion=conv, usuario=a), Participante(conversacion=conv, usuario=b)])
    else:
        Participante.objects.filter(conversacion=conv, usuario__in=[a, b]).update(activo=True)
    return conv


@require_POST
@vista
def escribir(request):
    otro = get_object_or_404(User, pk=request.POST.get('usuario') or 0)
    if not son_colegas(request.user, otro):
        messages.error(request, 'Primero deben ser colegas: envíele una solicitud.')
        return redirect(f'{BASE}/')
    return redirect(f'{BASE}/c/{directa(request.user, otro).pk}/')


@vista
def grupo_nuevo(request):
    """Un grupo de docentes con los colegas que escoja (o todos)."""
    user = request.user
    colegas = mis_colegas(user)
    if request.method == 'POST':
        nombre = ' '.join((request.POST.get('nombre') or '').split())[:80]
        ids = {int(x) for x in request.POST.getlist('miembros') if str(x).isdigit()}
        elegidos = list(colegas if request.POST.get('todos') == 'on' else colegas.filter(pk__in=ids))
        if not nombre or not elegidos:
            messages.error(request, 'Escriba el nombre del grupo y escoja al menos un colega.')
        else:
            conv = Conversacion.objects.create(colegio=None, tipo='colegas_g', nombre=nombre, creada_por=user,
                                               solo_lectura=request.POST.get('solo_lectura') == 'on')
            Participante.objects.bulk_create([Participante(conversacion=conv, usuario=user, moderador=True)] +
                                             [Participante(conversacion=conv, usuario=u) for u in elegidos])
            for u in elegidos:
                avisar(u, f'{nombre_de(user)} lo agregó al grupo de docentes «{nombre}».', f'{BASE}/c/{conv.pk}/')
            return redirect(f'{BASE}/c/{conv.pk}/')
    personas = sorted((tarjeta(u) for u in colegas), key=lambda x: x['nombre'].lower())
    return render(request, 'chat/colegas_grupo_nuevo.html', dict(_lista(request), personas=personas))


def _conversacion(request, pk):
    conv = get_object_or_404(Conversacion, pk=pk, colegio__isnull=True, tipo__in=TIPOS)
    p = Participante.objects.filter(conversacion=conv, usuario=request.user, activo=True).first()
    if p is None:
        raise Http404
    return conv, p


def _otro(conv, user):
    return next((x.usuario for x in conv.participantes.select_related('usuario') if x.usuario_id != user.pk), None)


def puede_escribir(conv, p, user):
    if conv.tipo == 'colegas':
        otro = _otro(conv, user)
        return bool(otro and son_colegas(user, otro))
    return not conv.solo_lectura or p.moderador


def _json_m(m, user, moderador):
    d = _mensaje_json(m, user, moderador)
    d['autor'] = nombre_de(m.autor)
    if d['archivo']:
        d['archivo'] = f'{BASE}/m/{m.pk}/archivo/'
    return d


@vista
def conversacion(request, pk):
    conv, p = _conversacion(request, pk)
    user = request.user
    qs = conv.mensajes.select_related('autor')
    ultimos = list(qs.order_by('-creado', '-id')[:POR_PAGINA])[::-1]
    p.ultimo_leido = timezone.now()
    p.save(update_fields=['ultimo_leido'])
    Notificacion.objects.filter(destinatario=user, url=f'{BASE}/c/{conv.pk}/', leido=False).update(leido=True)
    participantes = [(x.usuario, nombre_de(x.usuario), descripcion(x.usuario), x.moderador, foto_de(x.usuario))
                     for x in conv.participantes.filter(activo=True).select_related('usuario')
                     .order_by('-moderador', 'usuario__first_name', 'usuario__last_name')]
    dentro = {x[0].pk for x in participantes}
    agregables = [{'u': u, 'nombre': nombre_de(u)} for u in mis_colegas(user).exclude(pk__in=dentro)] \
        if conv.tipo == 'colegas_g' and p.moderador else []
    escribir_ok = puede_escribir(conv, p, user)
    return render(request, 'chat/colegas_conversacion.html', dict(
        _lista(request, conv.pk), conv=conv, p=p, titulo=_titulo(conv, user),
        foto_otro='' if conv.tipo == 'colegas_g' else foto_de(_otro(conv, user) or user), otro=_otro(conv, user) if conv.tipo == 'colegas' else None, moderador=p.moderador, participantes=participantes,
        agregables=agregables, puede_escribir=escribir_ok,
        aviso_escribir='' if escribir_ok else ('Ya no son colegas: no se pueden escribir.' if conv.tipo == 'colegas' else 'En este grupo solo escriben los moderadores.'),
        mensajes=[_json_m(m, user, p.moderador) for m in ultimos], hay_mas=qs.count() > POR_PAGINA,
        compartidos=[_json_m(m, user, p.moderador) for m in conv.mensajes.filter(tipo__in=('foto', 'voz', 'doc'), eliminado=False)
                     .exclude(archivo='').select_related('autor').order_by('-creado', '-id')[:12]],
        respuestas=RESPUESTAS_ADULTO,
        cfg={'nuevos': f'{BASE}/c/{conv.pk}/nuevos/', 'enviar': f'{BASE}/c/{conv.pk}/enviar/',
             'accion': f'{BASE}/c/{conv.pk}/accion/', 'autores': conv.tipo == 'colegas_g'}))


@vista
def nuevos(request, pk):
    conv, p = _conversacion(request, pk)
    try:
        despues = int(request.GET.get('despues') or 0)
    except ValueError:
        despues = 0
    lista = list(conv.mensajes.select_related('autor').filter(id__gt=despues)[:100])
    borrados = list(conv.mensajes.filter(id__lte=despues, eliminado=True).values_list('id', flat=True)[:200])
    if lista:
        p.ultimo_leido = timezone.now()
        p.save(update_fields=['ultimo_leido'])
        Notificacion.objects.filter(destinatario=request.user, url=f'{BASE}/c/{conv.pk}/', leido=False).update(leido=True)
    conv.refresh_from_db(fields=['solo_lectura'])
    return JsonResponse({'mensajes': [_json_m(m, request.user, p.moderador) for m in lista], 'borrados': borrados,
                         'puede_escribir': puede_escribir(conv, p, request.user)})


@require_POST
@vista
def enviar(request, pk):
    conv, p = _conversacion(request, pk)
    if not puede_escribir(conv, p, request.user):
        return JsonResponse({'ok': False, 'error': 'Aquí no puede escribir.'}, status=403)
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
    if adjunto is None:
        m = Mensaje.objects.create(conversacion=conv, autor=request.user, texto=texto)
    else:
        from django.core.files.base import ContentFile
        tipo, datos, nombre, segundos, original = adjunto
        m = Mensaje(conversacion=conv, autor=request.user, texto=texto if tipo in ('foto', 'doc') else '', tipo=tipo,
                    peso=len(datos), duracion=segundos, nombre_archivo=original)
        m.archivo.save(nombre, ContentFile(datos), save=False)
        m.save()
    Conversacion.objects.filter(pk=conv.pk).update(ultimo_mensaje=m.creado)
    p.ultimo_leido = m.creado
    p.save(update_fields=['ultimo_leido'])
    avisar_mensaje(m)
    return JsonResponse({'ok': True, 'mensaje': _json_m(m, request.user, p.moderador)})


@require_POST
@vista
def accion(request, pk):
    conv, p = _conversacion(request, pk)
    user = request.user
    que = request.POST.get('accion')
    grupo = conv.tipo == 'colegas_g'
    if que == 'silenciar':
        p.silenciada = not p.silenciada
        p.save(update_fields=['silenciada'])
        messages.info(request, 'No le llegarán avisos de este chat.' if p.silenciada else 'Volverá a recibir avisos de este chat.')
    elif que == 'solo_lectura' and grupo and p.moderador:
        conv.solo_lectura = not conv.solo_lectura
        conv.save(update_fields=['solo_lectura'])
        messages.success(request, 'Ahora solo escriben los moderadores.' if conv.solo_lectura else 'Todos pueden escribir.')
    elif que == 'borrar':
        m = get_object_or_404(Mensaje, pk=request.POST.get('mensaje') or 0, conversacion=conv)
        if m.autor_id == user.pk or p.moderador:
            m.eliminado, m.eliminado_por = True, user
            m.save(update_fields=['eliminado', 'eliminado_por'])
        if request.headers.get('x-requested-with') == 'fetch':
            return JsonResponse({'ok': True})
    elif que == 'renombrar' and grupo and p.moderador:
        nombre = ' '.join((request.POST.get('nombre') or '').split())[:80]
        if nombre:
            conv.nombre = nombre
            conv.save(update_fields=['nombre'])
    elif que == 'agregar' and grupo and p.moderador:
        ids = {int(x) for x in request.POST.getlist('miembros') if str(x).isdigit()}
        nuevos_ = 0
        for u in mis_colegas(user).filter(pk__in=ids):
            Participante.objects.update_or_create(conversacion=conv, usuario=u, defaults={'activo': True})
            avisar(u, f'{nombre_de(user)} lo agregó al grupo de docentes «{conv.nombre}».', f'{BASE}/c/{conv.pk}/')
            nuevos_ += 1
        messages.success(request, f'{nuevos_} colega(s) agregado(s) al grupo.')
    elif que == 'quitar' and grupo and p.moderador:
        Participante.objects.filter(conversacion=conv, usuario_id=request.POST.get('usuario') or 0, moderador=False).update(activo=False)
    elif que == 'moderador' and grupo and p.moderador:
        Participante.objects.filter(conversacion=conv, usuario_id=request.POST.get('usuario') or 0, activo=True).update(moderador=True)
    elif que == 'salir' and grupo:
        p.activo = False
        p.save(update_fields=['activo'])
        # si se va el único moderador, el más antiguo queda de moderador
        if p.moderador and not conv.participantes.filter(activo=True, moderador=True).exists():
            otro = conv.participantes.filter(activo=True).order_by('pk').first()
            if otro:
                otro.moderador = True
                otro.save(update_fields=['moderador'])
        messages.info(request, f'Salió de «{conv.nombre}».')
        return redirect(f'{BASE}/')
    return redirect(f'{BASE}/c/{conv.pk}/')


@vista
def archivo(request, mid):
    m = get_object_or_404(Mensaje.objects.select_related('conversacion'), pk=mid, conversacion__colegio__isnull=True,
                          conversacion__tipo__in=TIPOS)
    _conversacion(request, m.conversacion_id)
    if not m.archivo or m.eliminado:
        raise Http404
    from .views import url_archivo
    return redirect(url_archivo(m))


@vista
def no_leidos(request):
    return JsonResponse({'n': sum(_no_leidos(request.user).values()),
                         'solicitudes': Colega.objects.filter(para=request.user, estado='pendiente').count()})


@vista
def ver(request, uid):
    """El perfil de un docente: foto, colegio o institución, área, grados y presentación."""
    user = request.user
    otro = get_object_or_404(docentes(), pk=uid)
    if Colega.objects.filter(de=otro, para=user, estado='bloqueada').exists():
        raise Http404
    perfil = PerfilColega.objects.filter(usuario=otro).first()
    r = relacion(user, otro)
    if otro.pk != user.pk and perfil and not perfil.visible and not (r and r.estado == 'aceptada'):
        raise Http404
    estado = 'yo' if otro.pk == user.pk else 'ninguna' if r is None else (
        'enviada' if r.estado == 'pendiente' and r.de_id == user.pk else 'recibida' if r.estado == 'pendiente'
        else 'bloqueado' if r.estado == 'bloqueada' else 'colegas')
    mios, suyos = set(mis_colegas(user).values_list('pk', flat=True)), set(mis_colegas(otro).values_list('pk', flat=True))
    grupos = Conversacion.objects.filter(colegio__isnull=True, tipo='colegas_g', participantes__usuario=user, participantes__activo=True) \
        .filter(pk__in=Participante.objects.filter(usuario=otro, activo=True).values('conversacion')).distinct()
    return render(request, 'chat/colegas_perfil.html', dict(
        _lista(request), o=tarjeta(otro), perfil=perfil, estado=estado, en_comun=[tarjeta(u) for u in User.objects.filter(pk__in=(mios & suyos) - {user.pk, otro.pk})[:12]],
        grupos=grupos, desde=r.respondida if r and r.estado == 'aceptada' else None))


def _icono(n):
    u = n.url or ''
    if 'tab=solicitudes' in u:
        return 'fa-user-plus'
    if 'grupo de docentes' in (n.mensaje or ''):
        return 'fa-users'
    if '/c/' in u:
        return 'fa-comment-dots'
    if u.startswith(f'{BASE}/'):
        return 'fa-user-check'
    return 'fa-bell'


@login_required
def avisos(request):
    """La campana: los avisos del docente (solicitudes de colegas, aceptadas, grupos, mensajes…)."""
    from django.utils.timesince import timesince
    qs = Notificacion.objects.filter(destinatario=request.user).order_by('-fecha_creacion')
    lista = list(qs[:15])
    from django.middleware.csrf import get_token
    return JsonResponse({'n': qs.filter(leido=False).count(), 'csrf': get_token(request), 'avisos': [
        {'id': x.pk, 'mensaje': x.mensaje, 'url': f'{BASE}/aviso/{x.pk}/', 'leido': x.leido, 'icono': _icono(x),
         'hace': 'hace ' + timesince(x.fecha_creacion).split(',')[0]} for x in lista]})


@login_required
def aviso(request, nid):
    """Abrir un aviso: queda leído y lleva a donde corresponde."""
    n = get_object_or_404(Notificacion, pk=nid, destinatario=request.user)
    if not n.leido:
        n.leido = True
        n.save(update_fields=['leido'])
    destino = n.url or f'{BASE}/'
    return redirect(destino if destino.startswith('/') else f'{BASE}/')


@require_POST
@login_required
def avisos_leidos(request):
    Notificacion.objects.filter(destinatario=request.user, leido=False).update(leido=True)
    return JsonResponse({'ok': True})


# ---------------------------------------------------------------------------
# Chat flotante (como el de Facebook) en las páginas del Salón Digital, en el computador
# ---------------------------------------------------------------------------
@vista
def mini(request):
    """Lo que muestra el panel del botón de chat: conversaciones y colegas (para abrir un chat nuevo)."""
    datos = _lista(request)
    convs = [{'id': f['c'].pk, 'titulo': f['titulo'], 'foto': f['foto'], 'grupo': f['grupo'], 'sin_leer': f['sin_leer'],
              'previa': f['previa'], 'cuando': f['cuando']} for f in datos['filas']]
    con_chat = {}
    for c in Conversacion.objects.filter(colegio__isnull=True, tipo='colegas', participantes__usuario=request.user,
                                         participantes__activo=True).prefetch_related('participantes'):
        for x in c.participantes.all():
            if x.usuario_id != request.user.pk:
                con_chat[x.usuario_id] = c.pk
    colegas = sorted(({'id': u.pk, 'nombre': nombre_de(u), 'foto': foto_de(u), 'conv': con_chat.get(u.pk)} for u in mis_colegas(request.user)),
                     key=lambda x: x['nombre'].lower())
    from django.middleware.csrf import get_token
    return JsonResponse({'n': sum(c['sin_leer'] for c in convs), 'solicitudes': datos['n_solicitudes'], 'convs': convs, 'colegas': colegas,
                         'csrf': get_token(request)})       # las páginas sin formularios no traen la cookie: aquí va el token


@vista
def mini_conv(request, pk):
    """Los últimos mensajes de una conversación para la ventanita del chat flotante (y quedan leídos)."""
    conv, p = _conversacion(request, pk)
    user = request.user
    ultimos = list(conv.mensajes.select_related('autor').order_by('-creado', '-id')[:40])[::-1]
    p.ultimo_leido = timezone.now()
    p.save(update_fields=['ultimo_leido'])
    Notificacion.objects.filter(destinatario=user, url=f'{BASE}/c/{conv.pk}/', leido=False).update(leido=True)
    otro = _otro(conv, user) if conv.tipo == 'colegas' else None
    return JsonResponse({'id': conv.pk, 'titulo': _titulo(conv, user), 'grupo': conv.tipo == 'colegas_g',
                         'foto': foto_de(otro) if otro else '', 'url': f'{BASE}/c/{conv.pk}/',
                         'puede_escribir': puede_escribir(conv, p, user),
                         'mensajes': [_json_m(m, user, p.moderador) for m in ultimos]})


@require_POST
@vista
def mini_abrir(request):
    """Abrir (o crear) el chat uno a uno con un colega desde el panel flotante."""
    otro = get_object_or_404(User, pk=request.POST.get('usuario') or 0)
    if not son_colegas(request.user, otro):
        return JsonResponse({'ok': False, 'error': 'Primero deben ser colegas.'}, status=403)
    return JsonResponse({'ok': True, 'id': directa(request.user, otro).pk})
