"""Muro académico de Mis colegas (plan individual): un espacio para compartir lo que sirve en clase.

  · Cada publicación tiene un tipo (recurso, consulta, experiencia de aula, convocatoria, lectura) y etiquetas de
    área, grados y modelo pedagógico, para que se pueda filtrar y el muro no se llene de cualquier cosa.
  · Se publica para toda la comunidad docente o solo para los colegas. Nunca lo ven estudiantes.
  · Reacciones académicas: «Útil», «Lo usaré en clase» y «Guardar» (en vez de «me gusta»).
  · Un recurso de Mis materiales se puede ver en PDF y copiar a los materiales propios, con crédito al autor.
  · Normas de la comunidad: se aceptan antes de publicar; nada de datos ni fotos de estudiantes. Con 3 reportes de
    docentes distintos la publicación se oculta hasta que un administrador la revisa.
  · Sugerencias de colegas: colegas en común, misma área, mismos grados y mismo municipio.
"""
import io
import re
import unicodedata
from collections import Counter
from datetime import timedelta

from django.contrib import messages
from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from django.db.models import Count, Q
from django.http import Http404, HttpResponse, HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from .models import (Colega, ComentarioMuro, PerfilColega, Publicacion, ReaccionMuro, ReporteMuro,
                     SugerenciaDescartada)
from .views_colegas import BASE, avisar, descripcion, docentes, foto_de, mis_colegas, nombre_de, perfil_de, vista

MURO = f'{BASE}/muro'
REPORTES_PARA_OCULTAR = 3
POR_PAGINA = 15
PUBLICACIONES_DIA = 20
ICONOS = {'recurso': ('fa-file-lines', '#1971c2'), 'actividad': ('fa-gamepad', '#0c8599'), 'consulta': ('fa-circle-question', '#e8590c'),
          'experiencia': ('fa-chalkboard-user', '#2b8a3e'), 'convocatoria': ('fa-bullhorn', '#c2255c'),
          'lectura': ('fa-book-open', '#6741d9')}
MODELOS = ['ABP (proyectos)', 'Aprendizaje basado en retos', 'Estudio de caso', 'Aula invertida', 'Aprendizaje cooperativo',
           'Escuela Nueva', 'Gamificación', 'STEM / STEAM', 'Enseñanza tradicional']
NORMAS = [
    'Comparta lo que le sirve a otros docentes: recursos, preguntas, experiencias, convocatorias y lecturas.',
    'Nunca publique fotos, nombres, notas ni datos de sus estudiantes (Ley 1581 de 2012).',
    'Respete a los colegas: sin insultos, sin política partidista, sin cadenas ni ventas.',
    'Cite la fuente cuando comparta material de otros y respete los derechos de autor.',
    'Si algo no cumple estas normas, repórtelo: con 3 reportes se oculta mientras se revisa.',
]


# ---------------------------------------------------------------------------
# Utilidades
# ---------------------------------------------------------------------------
def _norm(t):
    t = unicodedata.normalize('NFKD', t or '').encode('ascii', 'ignore').decode().lower()
    return ' '.join(re.sub(r'[^a-z0-9 ]', ' ', t).split())


def grados_de(texto):
    """«6.º a 9.º» → {6,7,8,9}; «10, 11» → {10,11}; «Transición» → {0}."""
    t = _norm(texto)
    nums = [int(x) for x in re.findall(r'\d+', t) if 0 <= int(x) <= 11]
    out = set(nums)
    if len(nums) == 2 and re.search(r'\d+\s*(?:o\s*)?(a|al|hasta)\s*\d+', t):     # «6.º a 9.º» queda «6 o a 9 o»
        out |= set(range(min(nums), max(nums) + 1))
    if 'transicion' in t or 'preescolar' in t:
        out.add(0)
    return out


def _bloqueados(user):
    """Los docentes que bloquearon a este o que este bloqueó: no se ven en el muro."""
    pares = Colega.objects.filter(Q(de=user) | Q(para=user), estado='bloqueada').values_list('de_id', 'para_id')
    return {x for par in pares for x in par} - {user.pk}


def visibles(user):
    """Las publicaciones que este docente puede ver."""
    colegas = set(mis_colegas(user).values_list('pk', flat=True))
    qs = Publicacion.objects.filter(Q(visibilidad='todos') | Q(autor__in=colegas | {user.pk}))
    qs = qs.exclude(autor__in=_bloqueados(user))
    if not user.is_staff:
        qs = qs.filter(Q(oculta=False) | Q(autor=user))
    return qs


def _imagen(f):
    """La foto reducida (máx. 1600 px) y sin datos EXIF (ubicación, cámara…)."""
    from PIL import Image, ImageOps
    im = Image.open(f)
    im = ImageOps.exif_transpose(im).convert('RGB')
    im.thumbnail((1600, 1600))
    b = io.BytesIO()
    im.save(b, 'JPEG', quality=84, optimize=True)
    return ContentFile(b.getvalue())


def _tarjeta_pub(p, user, mias):
    ic, color = ICONOS.get(p.tipo, ('fa-note-sticky', '#495057'))
    from django.utils.timesince import timesince
    hace = 'hace un momento' if (timezone.now() - p.creada).total_seconds() < 60 else 'hace ' + timesince(p.creada).split(',')[0]
    from salon_digital.limites import cuenta_de
    c = cuenta_de(p.autor)
    return {'p': p, 'icono': ic, 'color': color, 'hace': hace, 'premium': bool(c and c.nivel in ('premium', 'ilimitado') and not c.en_prueba), 'nombre': nombre_de(p.autor), 'foto': foto_de(p.autor),
            'desc': descripcion(p.autor), 'util': p.n_util, 'usare': p.n_usare, 'n_com': p.n_com,
            'mias': mias.get(p.pk, set()), 'mia': p.autor_id == user.pk,
            'host': re.sub(r'^https?://(www\.)?', '', p.enlace).split('/')[0] if p.enlace else ''}


def _con_conteos(qs):
    return qs.select_related('autor', 'documento', 'pagina__propietario', 'juego').annotate(
        n_util=Count('reacciones', filter=Q(reacciones__tipo='util'), distinct=True),
        n_usare=Count('reacciones', filter=Q(reacciones__tipo='usare'), distinct=True),
        n_com=Count('comentarios', distinct=True))


def _mias(user, ids):
    out = {}
    for pid, tipo in ReaccionMuro.objects.filter(usuario=user, publicacion_id__in=ids).values_list('publicacion_id', 'tipo'):
        out.setdefault(pid, set()).add(tipo)
    return out


# ---------------------------------------------------------------------------
# Sugerencias de colegas
# ---------------------------------------------------------------------------
def sugerencias(user, n=6):
    """[{tarjeta, razones, en_comun}] ordenadas por puntos: colegas en común (3 c/u), misma área (2), mismo municipio (2),
    mismo departamento (1) y grados en común (1)."""
    mios = set(mis_colegas(user).values_list('pk', flat=True))
    con_relacion = {x for par in Colega.objects.filter(Q(de=user) | Q(para=user)).values_list('de_id', 'para_id') for x in par}
    descartados = set(SugerenciaDescartada.objects.filter(usuario=user).values_list('descartado_id', flat=True))
    fuera = mios | con_relacion | descartados | {user.pk}
    comunes = Counter()
    for de, para in Colega.objects.filter(Q(de__in=mios) | Q(para__in=mios), estado='aceptada').values_list('de_id', 'para_id'):
        for a, b in ((de, para), (para, de)):
            if a in mios and b not in fuera:
                comunes[b] += 1
    yo = PerfilColega.objects.filter(usuario=user).first()
    mi_area = _norm(yo.area if yo else '')
    mi_mun = _norm((yo.municipio if yo else '') or getattr(getattr(user, 'cuenta_salon', None), 'municipio', ''))
    mi_dep = _norm(getattr(getattr(user, 'cuenta_salon', None), 'departamento', ''))
    mis_grados = grados_de(yo.grados if yo else '')
    # En la base de datos se busca con el texto tal cual (con tildes); la comparación fina se hace abajo, sin tildes
    crudo = lambda t: (t or '').replace(',', ' ').split()[0] if (t or '').split() else ''
    filtro = Q(pk__in=list(comunes)[:300])
    if mi_area:
        filtro |= Q(perfil_colega__area__icontains=crudo(yo.area)[:6])
    if mi_mun:
        palabra = crudo((yo.municipio if yo else '') or user.cuenta_salon.municipio)
        filtro |= Q(perfil_colega__municipio__icontains=palabra) | Q(cuenta_salon__municipio__icontains=palabra)
    if mi_dep:
        filtro |= Q(cuenta_salon__departamento__icontains=crudo(user.cuenta_salon.departamento))
    candidatos = (docentes().exclude(pk__in=fuera).exclude(perfil_colega__visible=False).filter(filtro)
                  .select_related('perfil_colega', 'cuenta_salon').distinct()[:300])
    filas = []
    for u in candidatos:
        perfil = getattr(u, 'perfil_colega', None) if hasattr(u, 'perfil_colega') else None
        cuenta = getattr(u, 'cuenta_salon', None)
        puntos, razones = 3 * comunes.get(u.pk, 0), []
        if comunes.get(u.pk):
            razones.append(f'{comunes[u.pk]} colega{"s" if comunes[u.pk] > 1 else ""} en común')
        area = _norm(perfil.area if perfil else '')
        if mi_area and area and (mi_area in area or area in mi_area):
            puntos += 2
            razones.append(f'También enseña {perfil.area}')
        mun = _norm((perfil.municipio if perfil else '') or (cuenta.municipio if cuenta else ''))
        if mi_mun and mun and mi_mun.split()[0] == mun.split()[0]:
            puntos += 2
            razones.append(f'De {(perfil.municipio if perfil and perfil.municipio else cuenta.municipio)}')
        elif mi_dep and cuenta and _norm(cuenta.departamento) == mi_dep:
            puntos += 1
            razones.append(f'De {cuenta.departamento}')
        g = mis_grados & grados_de(perfil.grados if perfil else '')
        if g:
            puntos += 1
            razones.append('Enseña ' + ', '.join(f'{x}.º' if x else 'transición' for x in sorted(g)[:3]))
        if puntos:
            filas.append((puntos, u, razones))
    filas.sort(key=lambda x: (-x[0], nombre_de(x[1]).lower()))
    out = [{'t': {'u': u, 'nombre': nombre_de(u), 'foto': foto_de(u), 'desc': descripcion(u)}, 'razones': r[:2]}
           for _, u, r in filas[:n]]
    if len(out) < n:          # comunidad pequeña: los docentes más nuevos
        ya = fuera | {x['t']['u'].pk for x in out}
        for u in docentes().exclude(pk__in=ya).exclude(perfil_colega__visible=False).order_by('-date_joined')[:n - len(out)]:
            out.append({'t': {'u': u, 'nombre': nombre_de(u), 'foto': foto_de(u), 'desc': descripcion(u)}, 'razones': ['Nuevo en la comunidad']})
    return out


@require_POST
@vista
def descartar(request):
    otro = get_object_or_404(User, pk=request.POST.get('usuario') or 0)
    SugerenciaDescartada.objects.get_or_create(usuario=request.user, descartado=otro)
    if request.headers.get('x-requested-with') == 'fetch':
        return JsonResponse({'ok': True})
    return redirect(request.POST.get('volver') if (request.POST.get('volver') or '').startswith(f'{BASE}/') else f'{MURO}/')


# ---------------------------------------------------------------------------
# Insignias del perfil (por aportes, nunca por cantidad de publicaciones a secas)
# ---------------------------------------------------------------------------
def insignias(u):
    recursos = Publicacion.objects.filter(autor=u, tipo='recurso', oculta=False).count()
    utiles = ReaccionMuro.objects.filter(publicacion__autor=u, tipo='util').exclude(usuario=u).count()
    respuestas = ComentarioMuro.objects.filter(autor=u, publicacion__tipo='consulta').exclude(publicacion__autor=u).count()
    mejores = Publicacion.objects.filter(mejor_respuesta__autor=u).exclude(autor=u).count()
    copias = sum(Publicacion.objects.filter(autor=u).values_list('copias', flat=True))
    lista = []
    if recursos >= 3:
        lista.append(('fa-box-open', 'Comparte recursos', f'{recursos} recursos compartidos'))
    if utiles >= 10:
        lista.append(('fa-lightbulb', 'Útil para la comunidad', f'{utiles} colegas marcaron sus aportes como útiles'))
    if respuestas >= 5:
        lista.append(('fa-comments', 'Responde consultas', f'{respuestas} respuestas a consultas'))
    if mejores >= 1:
        lista.append(('fa-medal', 'Mejor respuesta', f'{mejores} vez/veces elegida la mejor respuesta'))
    if copias >= 5:
        lista.append(('fa-copy', 'Material que se usa', f'{copias} docentes copiaron sus recursos'))
    return {'lista': lista, 'recursos': recursos, 'utiles': utiles, 'respuestas': respuestas, 'copias': copias,
            'publicaciones': Publicacion.objects.filter(autor=u, oculta=False).count()}


# ---------------------------------------------------------------------------
# Muro
# ---------------------------------------------------------------------------
def _mis_paginas(user):
    from salon_digital.models import PaginaPublicada
    return PaginaPublicada.objects.filter(propietario__usuario=user, visible=True).order_by('-actualizada_en')[:100]


def _mis_juegos(user):
    from materiales.models import JuegoMaterial
    return JuegoMaterial.objects.filter(propietario=user)[:100]


def _mis_documentos(user):
    from materiales.models import Documento
    return Documento.objects.filter(propietario=user, colegio__isnull=True).order_by('-actualizado')[:100]


def _publicar(request):
    user = request.user
    perfil = perfil_de(user)
    if not perfil.normas_aceptadas:
        messages.warning(request, 'Antes de publicar, lea y acepte las normas de la comunidad.')
        return None
    from django.core.cache import cache
    clave = f'muro-publicar:{user.pk}:{timezone.localdate()}'
    if (cache.get(clave) or 0) >= PUBLICACIONES_DIA:
        messages.error(request, f'Por hoy ya publicó {PUBLICACIONES_DIA} veces. Mañana puede publicar más.')
        return None
    limpio = lambda k, n: ' '.join((request.POST.get(k) or '').split())[:n]
    tipo = request.POST.get('tipo')
    if tipo not in dict(Publicacion.TIPOS):
        tipo = 'experiencia'
    titulo, texto = limpio('titulo', 150), (request.POST.get('texto') or '').strip()[:5000]
    enlace = (request.POST.get('enlace') or '').strip()[:300]
    if enlace and not re.match(r'^https?://[^\s]+\.[^\s]+$', enlace):
        messages.error(request, 'El enlace debe empezar por http:// o https://')
        return None
    documento = None
    if tipo == 'recurso' and request.POST.get('documento'):
        documento = _mis_documentos(user).model.objects.filter(pk=request.POST.get('documento'), propietario=user,
                                                               colegio__isnull=True).first()
    pagina = juego = None
    if tipo == 'actividad':
        valor = request.POST.get('pagina') or ''
        if valor.startswith('j'):          # un juego de «Mis juegos»
            from materiales.models import JuegoMaterial
            juego = JuegoMaterial.objects.filter(pk=valor[1:] if valor[1:].isdigit() else 0, propietario=user).first()
        else:
            pagina = _mis_paginas(user).model.objects.filter(pk=valor if valor.isdigit() else 0, propietario__usuario=user).first()
        if pagina is None and juego is None:
            messages.error(request, 'Escoja una de sus actividades interactivas o uno de Mis juegos.')
            return None
        if juego is not None:
            titulo = titulo or juego.titulo[:150]
            texto = texto or f'{juego.nombre_tipo} con {len(juego.preguntas)} preguntas. Pruébelo aquí e impórtelo a sus juegos.'
        else:
            titulo = titulo or pagina.titulo[:150]
            texto = texto or pagina.descripcion[:5000]
    if len(titulo) < 4:
        messages.error(request, 'Escriba un título (mínimo 4 letras).')
        return None
    if tipo == 'recurso' and not (documento or enlace or request.FILES.get('imagen')):
        messages.error(request, 'Para un recurso, escoja uno de Mis materiales o pegue el enlace.')
        return None
    if tipo == 'consulta' and len(texto) < 10:
        messages.error(request, 'Cuente un poco más su consulta para que los colegas puedan ayudarle.')
        return None
    imagen = request.FILES.get('imagen')
    if imagen:
        if not request.POST.get('sin_estudiantes'):
            messages.error(request, 'Confirme que en la imagen no aparecen estudiantes ni sus datos.')
            return None
        if imagen.size > 8 * 1024 * 1024:
            messages.error(request, 'La imagen pesa más de 8 MB.')
            return None
        try:
            imagen = _imagen(imagen)
        except Exception:
            messages.error(request, 'No se pudo leer la imagen. Pruebe con una foto JPG o PNG.')
            return None
    fecha = None
    if tipo == 'convocatoria' and request.POST.get('fecha_limite'):
        from datetime import date
        try:
            fecha = date.fromisoformat(request.POST.get('fecha_limite'))
        except ValueError:
            fecha = None
    p = Publicacion(autor=user, tipo=tipo, titulo=titulo, texto=texto, enlace=enlace, documento=documento, pagina=pagina, juego=juego,
                    area=limpio('area', 80) or (documento.area if documento else '') or perfil.area,
                    grados=limpio('grados', 40) or (documento.grado if documento else ''),
                    modelo=limpio('modelo', 40), fecha_limite=fecha,
                    visibilidad='colegas' if request.POST.get('visibilidad') == 'colegas' else 'todos')
    if imagen:
        p.imagen.save('muro.jpg', imagen, save=False)
    p.save()
    cache.set(clave, (cache.get(clave) or 0) + 1, 86400)
    messages.success(request, 'Publicado en el muro.')
    return p


@vista
def muro(request):
    user = request.user
    if request.method == 'POST':
        p = _publicar(request)
        return redirect(f'{MURO}/' if p else f'{MURO}/?escribir=1')
    tipo = request.GET.get('tipo') if request.GET.get('tipo') in dict(Publicacion.TIPOS) else ''
    area = ' '.join((request.GET.get('area') or '').split())[:60]
    grado = request.GET.get('grado') or ''
    de = request.GET.get('de') or ''
    q = ' '.join((request.GET.get('q') or '').split())[:60]
    ver = request.GET.get('ver') or ''
    hoy = timezone.localdate()
    qs = visibles(user)
    if ver == 'guardados':
        qs = qs.filter(reacciones__usuario=user, reacciones__tipo='guardar')
    elif ver == 'mias':
        qs = qs.filter(autor=user)
    else:
        qs = qs.filter(Q(fecha_limite__isnull=True) | Q(fecha_limite__gte=hoy))
    if tipo:
        qs = qs.filter(tipo=tipo)
    if area:
        qs = qs.filter(area__icontains=area)
    if de == 'colegas':
        qs = qs.filter(autor__in=mis_colegas(user))
    if q:
        for palabra in q.split()[:4]:
            qs = qs.filter(Q(titulo__icontains=palabra) | Q(texto__icontains=palabra) | Q(area__icontains=palabra)
                           | Q(modelo__icontains=palabra))
    lista = list(_con_conteos(qs.distinct()))
    if grado.isdigit():
        lista = [p for p in lista if not p.grados or int(grado) in grados_de(p.grados)]
    try:
        pagina = max(1, int(request.GET.get('pagina') or 1))
    except ValueError:
        pagina = 1
    total = len(lista)
    lista = lista[(pagina - 1) * POR_PAGINA: pagina * POR_PAGINA]
    mias = _mias(user, [p.pk for p in lista])
    hace7 = timezone.now() - timedelta(days=7)
    destacados = (visibles(user).filter(creada__gte=hace7, oculta=False)
                  .annotate(n=Count('reacciones', filter=Q(reacciones__tipo__in=('util', 'usare')))).filter(n__gt=0)
                  .order_by('-n', '-creada')[:5])
    convocatorias = visibles(user).filter(tipo='convocatoria', fecha_limite__gte=hoy, oculta=False).order_by('fecha_limite')[:4]
    perfil = perfil_de(user)
    from aula.models import Evento
    eventos = list(Evento.objects.filter(Q(creador=user) | Q(organizadores=user), activo=True).distinct().order_by('-creado')[:3])
    filtros = {k: v for k, v in (('tipo', tipo), ('area', area), ('grado', grado), ('de', de), ('q', q), ('ver', ver)) if v}
    from urllib.parse import urlencode
    return render(request, 'chat/muro.html', {
        'pubs': [_tarjeta_pub(p, user, mias) for p in lista], 'tipos': Publicacion.TIPOS, 'iconos': ICONOS,
        'filtros_tipo': [(k, v, ICONOS.get(k, ('fa-note-sticky', ''))[0]) for k, v in Publicacion.TIPOS], 'eventos': eventos,
        'tipo': tipo, 'area': area, 'grado': grado, 'de': de, 'q': q, 'ver': ver,
        'siguiente': f'?{urlencode(dict(filtros, pagina=pagina + 1))}' if pagina * POR_PAGINA < total else '',
        'anterior': f'?{urlencode(dict(filtros, pagina=pagina - 1))}' if pagina > 1 else '',
        'sugerencias': sugerencias(user, 5), 'destacados': destacados, 'convocatorias': convocatorias,
        'perfil': perfil, 'yo': {'nombre': nombre_de(user), 'foto': foto_de(user), 'desc': descripcion(user)},
        'n_colegas': mis_colegas(user).count(), 'n_solicitudes': Colega.objects.filter(para=user, estado='pendiente').count(),
        'documentos': _mis_documentos(user), 'paginas': _mis_paginas(user), 'mis_juegos': _mis_juegos(user), 'modelos': MODELOS, 'normas': NORMAS,
        'escribir': request.GET.get('escribir') == '1', 'compartir': request.GET.get('compartir', ''),
        'compartir_juego': int(request.GET['compartir'][1:]) if request.GET.get('compartir', '')[:1] == 'j' and request.GET['compartir'][1:].isdigit() else None, 'grados_lista': range(0, 12), 'hoy': hoy,
        'pendientes_mod': ReporteMuro.objects.filter(revisado=False, publicacion__oculta=True).values('publicacion').distinct().count() if user.is_staff else 0,
    })


@require_POST
@vista
def normas(request):
    p = perfil_de(request.user)
    if not p.normas_aceptadas:
        p.normas_aceptadas = timezone.now()
        p.save(update_fields=['normas_aceptadas'])
    return redirect(f'{MURO}/?escribir=1')


def _pub(request, pk):
    p = visibles(request.user).filter(pk=pk).first()
    if p is None:
        raise Http404
    return p


@vista
def detalle(request, pk):
    user = request.user
    p = _pub(request, pk)
    if request.method == 'POST':
        if not perfil_de(user).normas_aceptadas:
            messages.warning(request, 'Antes de comentar, acepte las normas de la comunidad en el muro.')
            return redirect(f'{MURO}/{p.pk}/')
        texto = (request.POST.get('texto') or '').strip()[:2000]
        if len(texto) >= 2:
            ComentarioMuro.objects.create(publicacion=p, autor=user, texto=texto)
            if p.autor_id != user.pk:
                avisar(p.autor, f'{nombre_de(user)} comentó su publicación «{p.titulo[:60]}».', f'{MURO}/{p.pk}/')
        return redirect(f'{MURO}/{p.pk}/#comentarios')
    pub = _con_conteos(Publicacion.objects.filter(pk=p.pk)).get()
    comentarios = [{'c': c, 'nombre': nombre_de(c.autor), 'foto': foto_de(c.autor), 'mejor': c.pk == p.mejor_respuesta_id,
                    'mio': c.autor_id == user.pk} for c in p.comentarios.select_related('autor')]
    comentarios.sort(key=lambda x: not x['mejor'])
    return render(request, 'chat/muro_detalle.html', {
        't': _tarjeta_pub(pub, user, _mias(user, [p.pk])), 'comentarios': comentarios, 'detalle': True,
        'yo': {'nombre': nombre_de(user), 'foto': foto_de(user)}, 'normas_ok': bool(perfil_de(user).normas_aceptadas),
        'hoy': timezone.localdate()})


@require_POST
@vista
def reaccion(request, pk):
    p = _pub(request, pk)
    tipo = request.POST.get('tipo')
    if tipo not in dict(ReaccionMuro.TIPOS):
        return JsonResponse({'ok': False}, status=400)
    r = ReaccionMuro.objects.filter(publicacion=p, usuario=request.user, tipo=tipo)
    if r.exists():
        r.delete()
        activa = False
    else:
        ReaccionMuro.objects.create(publicacion=p, usuario=request.user, tipo=tipo)
        activa = True
    n = ReaccionMuro.objects.filter(publicacion=p, tipo=tipo).count()
    if request.headers.get('x-requested-with') == 'fetch':
        return JsonResponse({'ok': True, 'activa': activa, 'n': n})
    return redirect(request.POST.get('volver') if (request.POST.get('volver') or '').startswith(f'{MURO}/') else f'{MURO}/')


@require_POST
@vista
def accion(request, pk):
    user = request.user
    p = _pub(request, pk)
    que = request.POST.get('accion')
    volver = f'{MURO}/{p.pk}/'
    if que == 'eliminar' and (p.autor_id == user.pk or user.is_staff):
        p.delete()
        messages.info(request, 'Publicación eliminada.')
        return redirect(f'{MURO}/')
    if que == 'reportar' and p.autor_id != user.pk:
        ReporteMuro.objects.get_or_create(publicacion=p, usuario=user,
                                          defaults={'motivo': ' '.join((request.POST.get('motivo') or '').split())[:200]})
        if ReporteMuro.objects.filter(publicacion=p, revisado=False).count() >= REPORTES_PARA_OCULTAR and not p.oculta:
            p.oculta = True
            p.save(update_fields=['oculta'])
            for staff in User.objects.filter(is_staff=True, is_active=True):
                avisar(staff, f'Publicación oculta por reportes: «{p.titulo[:60]}». Revísela.', f'{MURO}/moderar/')
        messages.info(request, 'Gracias. La revisaremos.')
        return redirect(f'{MURO}/')
    if que == 'mejor' and p.autor_id == user.pk and p.tipo == 'consulta':
        c = p.comentarios.filter(pk=request.POST.get('comentario') or 0).first()
        p.mejor_respuesta = None if c is None or p.mejor_respuesta_id == c.pk else c
        p.save(update_fields=['mejor_respuesta'])
        if p.mejor_respuesta and c.autor_id != user.pk:
            avisar(c.autor, f'{nombre_de(user)} eligió su respuesta como la mejor en «{p.titulo[:60]}». ¡Gracias por ayudar!',
                   f'{MURO}/{p.pk}/')
        return redirect(volver + '#comentarios')
    if que == 'borrar_comentario':
        c = p.comentarios.filter(pk=request.POST.get('comentario') or 0).first()
        if c and (c.autor_id == user.pk or p.autor_id == user.pk or user.is_staff):
            c.delete()
        return redirect(volver + '#comentarios')
    return redirect(volver)


@require_POST
@vista
def copiar(request, pk):
    """Copia el recurso a Mis materiales del docente, con crédito al autor."""
    from materiales.models import Documento
    from materiales.views import _copiar_imagenes
    p = _pub(request, pk)
    doc = p.documento
    if doc is None:
        messages.error(request, 'Este recurso ya no está disponible para copiar.')
        return redirect(f'{MURO}/{p.pk}/')
    from salon_digital.limites import a_planes, cupo_materiales
    if not cupo_materiales(request.user):
        return a_planes(request, 'materiales', 'estandar')
    contenido = _copiar_imagenes(request.user, doc) if doc.propietario_id != request.user.pk else doc.contenido
    copia = Documento.objects.create(propietario=request.user, colegio=None, titulo=f'{doc.titulo[:120]} (de {nombre_de(p.autor)[:25]})',
                                     tipo=doc.tipo, area=doc.area, grado=doc.grado, periodo=doc.periodo, contenido=contenido)
    if doc.propietario_id != request.user.pk:
        Publicacion.objects.filter(pk=p.pk).update(copias=p.copias + 1)
        avisar(p.autor, f'{nombre_de(request.user)} copió su recurso «{p.titulo[:60]}» a sus materiales.', f'{MURO}/{p.pk}/')
    messages.success(request, 'Copiado a Mis materiales. Ajústelo a su grupo.')
    return redirect('materiales:editor', pk=copia.pk)


@require_POST
@vista
def copiar_actividad(request, pk):
    """Copia la actividad HTML (de un solo archivo) a «Actividades y pruebas» del docente, para usarla con sus grupos."""
    from django.core.files.storage import default_storage
    from salon_digital.models import PaginaPublicada
    p = _pub(request, pk)
    orig = p.pagina
    cuenta = getattr(request.user, 'cuenta_salon', None)
    if orig is None or cuenta is None:
        messages.error(request, 'Esta actividad ya no está disponible para copiar.')
        return redirect(f'{MURO}/{p.pk}/')
    if orig.tipo != 'html':
        messages.info(request, 'Esta actividad es un sitio completo: se puede jugar desde el muro, pero no copiar. '
                               'Pídale el archivo a su autor por mensaje.')
        return redirect(f'{MURO}/{p.pk}/')
    if not cuenta.puede_publicar_otra():
        from salon_digital.limites import a_planes
        return a_planes(request, 'paginas', 'estandar' if cuenta.nivel == 'gratis' else 'premium')
    try:
        with default_storage.open(orig.ruta_contenido, 'rb') as fh:
            datos = fh.read()
    except Exception:
        messages.error(request, 'No se pudo leer el archivo de la actividad.')
        return redirect(f'{MURO}/{p.pk}/')
    copia = PaginaPublicada(propietario=cuenta, titulo=f'{orig.titulo[:170]} (de {nombre_de(p.autor)[:25]})',
                            descripcion=orig.descripcion, area=orig.area, grado=orig.grado, revisada=orig.revisada,
                            alertas=orig.alertas, visible=False)
    copia.archivo.save('actividad.html', ContentFile(datos), save=False)
    copia.save()
    Publicacion.objects.filter(pk=p.pk).update(copias=p.copias + 1)
    avisar(p.autor, f'{nombre_de(request.user)} copió su actividad «{p.titulo[:60]}» para usarla con sus estudiantes.', f'{MURO}/{p.pk}/')
    messages.success(request, 'Copiada a «Actividades y pruebas», sin publicar todavía: revísela, ajuste quién entra y publíquela.')
    return redirect('salon_digital:editar_pagina', slug=copia.slug)


@vista
def material(request, pk):
    """El PDF del recurso compartido (con el encabezado de su autor)."""
    from materiales import exportar
    from materiales.models import EncabezadoDocente
    p = _pub(request, pk)
    if p.documento is None:
        raise Http404
    datos = exportar.pdf(request, p.documento, colegio=None,
                         encabezado=EncabezadoDocente.objects.filter(usuario=p.autor).first(), docente=nombre_de(p.autor))
    r = HttpResponse(datos, content_type='application/pdf')
    r['Content-Disposition'] = f'inline; filename="{exportar.nombre_archivo(p.documento, "pdf")}"'
    return r


@vista
def moderar(request):
    if not request.user.is_staff:
        return HttpResponseForbidden('Solo los administradores moderan el muro.')
    if request.method == 'POST':
        p = get_object_or_404(Publicacion, pk=request.POST.get('publicacion') or 0)
        if request.POST.get('decision') == 'restaurar':
            p.oculta = False
            p.save(update_fields=['oculta'])
            ReporteMuro.objects.filter(publicacion=p).update(revisado=True)
            messages.success(request, 'Publicación restaurada.')
        elif request.POST.get('decision') == 'eliminar':
            avisar(p.autor, f'Su publicación «{p.titulo[:60]}» se retiró por no cumplir las normas de la comunidad.', f'{MURO}/')
            p.delete()
            messages.info(request, 'Publicación eliminada.')
        return redirect(f'{MURO}/moderar/')
    reportadas = (Publicacion.objects.filter(reportes__revisado=False).annotate(n=Count('reportes', distinct=True))
                  .select_related('autor').prefetch_related('reportes').order_by('-n').distinct())
    return render(request, 'chat/muro_moderar.html', {'reportadas': reportadas, 'normas': NORMAS})
