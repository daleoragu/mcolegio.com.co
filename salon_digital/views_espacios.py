"""Inicio y Mi Espacio de Profe: las dos pantallas nuevas del rediseño de Mi Salón Virtual."""
from django.contrib import messages
from django.db.models import Q, Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from .models import NotaPizarra, PaginaPublicada
from .decoradores import cuenta_requerida

COLORES = ['#4f46e5', '#f59e0b', '#10b981', '#ec4899', '#0ea5e9', '#8b5cf6']
DIAS = ['lunes', 'martes', 'miércoles', 'jueves', 'viernes', 'sábado', 'domingo']
MESES = ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre']


def _primer_nombre(user, cuenta):
    nombre = (user.first_name or cuenta.nombre_publico or user.username).strip()
    partes = [p for p in nombre.split() if p.rstrip('.').lower() not in ('prof', 'profe', 'profesor', 'profesora', 'docente', 'lic', 'mg', 'dr', 'dra')]
    return (partes or [nombre])[0]


def _hace(fecha):
    from django.utils.timesince import timesince
    if (timezone.now() - fecha).total_seconds() < 60:
        return 'hace un momento'
    return 'hace ' + timesince(fecha).split(',')[0]


def _comunidad(user, n):
    """Lo último que publicaron otros docentes en la Sala de Profesores."""
    from chat.views_colegas import foto_de, nombre_de
    from chat.views_muro import ICONOS, visibles
    pubs = visibles(user).exclude(autor=user).filter(oculta=False).select_related('autor').order_by('-creada')[:n]
    return [{'p': p, 'nombre': nombre_de(p.autor), 'foto': foto_de(p.autor), 'hace': _hace(p.creada),
             'icono': ICONOS.get(p.tipo, ('fa-note-sticky', '#495057'))[0]} for p in pubs]


def pendientes(cuenta, user, grupos):
    """Lo que el docente tiene por hacer hoy: entregas por calificar, tareas que vencen, invertidas sin ver, colegas."""
    from datetime import timedelta
    from django.db.models import Count
    from django.urls import reverse
    from aula.models import Aula, ClaseInvertida, Entrega, Tarea
    from chat.models import Colega
    aulas = {a.grupo_id: a for a in Aula.objects.filter(grupo__in=grupos)}
    nombre = {g.pk: g.nombre for g in grupos}
    total = {g.pk: g.total_integrantes for g in grupos}
    lista = []
    por_calificar = (Entrega.objects.filter(tarea__aula__in=aulas.values(), entregada__isnull=False, calificada__isnull=True)
                     .values('tarea__aula__grupo_id', 'tarea__aula_id').annotate(n=Count('id')).order_by('-n'))
    for x in por_calificar:
        lista.append({'icono': 'fa-clipboard-check', 'color': '#2563eb', 'url': reverse('aula:tareas', args=[x['tarea__aula_id']]),
                      'texto': f"{x['n']} entrega{'s' if x['n'] != 1 else ''} por calificar", 'grupo': nombre.get(x['tarea__aula__grupo_id'], '')})
    hoy = timezone.localdate()
    for t in Tarea.objects.filter(aula__in=aulas.values(), publicada=True, fecha_limite__date__gte=hoy,
                                  fecha_limite__date__lte=hoy + timedelta(days=1)).select_related('aula').order_by('fecha_limite'):
        cuando = 'hoy' if timezone.localtime(t.fecha_limite).date() == hoy else 'mañana'
        lista.append({'icono': 'fa-hourglass-half', 'color': '#f59e0b', 'url': reverse('aula:tarea', args=[t.aula_id, t.pk]),
                      'texto': f'«{t.titulo}» cierra {cuando}', 'grupo': nombre.get(t.aula.grupo_id, '')})
    hace = timezone.now() - timedelta(days=21)
    for c in (ClaseInvertida.objects.filter(aula__in=aulas.values(), publicada=True, creada__gte=hace)
              .select_related('aula').annotate(n=Count('respuestas')).order_by('-creada')[:6]):
        faltan = total.get(c.aula.grupo_id, 0) - c.n if not c.para else len(c.para) - c.n
        if faltan > 0:
            lista.append({'icono': 'fa-circle-play', 'color': '#e03131', 'url': reverse('aula:invertida', args=[c.aula_id, c.pk]),
                          'texto': f"{faltan} estudiante{'s' if faltan != 1 else ''} no ha{'n' if faltan != 1 else ''} visto «{c.titulo}»",
                          'grupo': nombre.get(c.aula.grupo_id, '')})
    n = Colega.objects.filter(para=user, estado='pendiente').count()
    if n:
        lista.append({'icono': 'fa-user-plus', 'color': '#4f46e5', 'url': '/chat/colegas/?tab=solicitudes',
                      'texto': f"{n} solicitud{'es' if n != 1 else ''} de colegas", 'grupo': 'Sala de Profesores'})
    return lista[:8]


@cuenta_requerida
def inicio(request):
    cuenta, user = request.cuenta, request.user
    hoy = timezone.localdate()
    grupos = list(cuenta.grupos.filter(activo=True).order_by('nombre'))
    for k, g in enumerate(grupos):
        g.color = COLORES[k % len(COLORES)]
    from chat.models import Colega
    from materiales.models import Documento
    return render(request, 'salon_digital/inicio.html', {
        'cuenta': cuenta, 'nombre': _primer_nombre(user, cuenta),
        'falta_region': (cuenta.pais or 'Colombia') == 'Colombia' and not cuenta.municipio_dane,
        'fecha': f'{DIAS[hoy.weekday()].capitalize()}, {hoy.day} de {MESES[hoy.month - 1]}',
        'grupos': grupos, 'comunidad': _comunidad(user, 5), 'pendientes': pendientes(cuenta, user, grupos),
        'notas': [_nota_json(n) for n in NotaPizarra.objects.filter(usuario=user)], 'colores_nota': dict(NotaPizarra.COLORES),
        'n_materiales': Documento.objects.filter(propietario=user).count(),
        'n_paginas': cuenta.paginas.count(),
        'n_solicitudes': Colega.objects.filter(para=user, estado='pendiente').count(),
    })


@cuenta_requerida
def mi_espacio(request):
    """Mi Espacio de Profe: perfil profesional, cifras, enlace público con QR y pestañas con lo mío."""
    from chat.models import Publicacion
    from chat.views_colegas import descripcion, foto_de, mis_colegas, nombre_de, perfil_de
    from chat.views_muro import _con_conteos, _mias, _tarjeta_pub
    cuenta, user = request.cuenta, request.user
    tab = request.GET.get('tab') if request.GET.get('tab') in ('publicaciones', 'paginas', 'vitrina') else 'publicaciones'
    mias = Publicacion.objects.filter(autor=user)
    paginas = list(cuenta.paginas.order_by('-id'))
    ctx = {
        'cuenta': cuenta, 'tab': tab, 'perfil': perfil_de(user),
        'yo': {'nombre': nombre_de(user), 'foto': foto_de(user), 'desc': descripcion(user)},
        'n_publicaciones': mias.count(), 'n_colegas': mis_colegas(user).count(),
        'visitas': cuenta.paginas.aggregate(n=Sum('visitas'))['n'] or 0,
        'copias': mias.aggregate(n=Sum('copias'))['n'] or 0,
        'enlace': request.build_absolute_uri(f'/p/{cuenta.slug}/'),
        'paginas': paginas,
    }
    if tab == 'publicaciones':
        lista = list(_con_conteos(mias).order_by('-creada')[:30])
        marcas = _mias(user, [p.pk for p in lista])
        ctx['pubs'] = [_tarjeta_pub(p, user, marcas) for p in lista]
        ctx['hoy'] = timezone.localdate()
    elif tab == 'vitrina':
        ctx['vitrina'] = [p for p in mias.filter(Q(documento__isnull=False) | Q(pagina__isnull=False))
                          .select_related('documento', 'pagina').order_by('-creada')]
    return render(request, 'salon_digital/mi_espacio.html', ctx)


@cuenta_requerida
def qr_espacio(request):
    from .utils import generar_qr
    return HttpResponse(generar_qr(request.build_absolute_uri(f'/p/{request.cuenta.slug}/')), content_type='image/png')


@require_POST
@cuenta_requerida
def visibilidad_pagina(request, slug):
    """El interruptor de cada página: pública en mi perfil o solo con el enlace."""
    pagina = get_object_or_404(PaginaPublicada, propietario=request.cuenta, slug=slug)
    pagina.listar_en_perfil = request.POST.get('publica') == '1'
    pagina.save(update_fields=['listar_en_perfil'])
    if request.headers.get('x-requested-with') == 'fetch':
        return HttpResponse('ok')
    messages.success(request, f'«{pagina.titulo}»: {"pública en su perfil" if pagina.listar_en_perfil else "solo con el enlace"}.')
    return redirect('/salon_digital/mi-espacio/?tab=paginas')


# ---------------------------------------------------------------------------
# La Pizarra: notas adhesivas del docente y el tablero para la clase
# ---------------------------------------------------------------------------
def _nota_json(n):
    return {'id': n.pk, 'texto': n.texto, 'color': n.color, 'hecha': n.hecha}


@require_POST
@cuenta_requerida
def nota(request):
    """Crear, editar, tachar, borrar u ordenar las notas de la Pizarra (responde JSON)."""
    from django.http import JsonResponse
    accion = request.POST.get('accion')
    mias = NotaPizarra.objects.filter(usuario=request.user)
    if accion == 'crear':
        if mias.count() >= 60:
            return JsonResponse({'ok': False, 'error': 'Tiene 60 notas: borre algunas antes de crear más.'}, status=400)
        n = NotaPizarra.objects.create(usuario=request.user, texto=(request.POST.get('texto') or '')[:400],
                                       color=request.POST.get('color') if request.POST.get('color') in dict(NotaPizarra.COLORES) else 'amarillo',
                                       orden=0)
        mias.exclude(pk=n.pk).update(orden=models_F('orden') + 1)
        return JsonResponse({'ok': True, 'nota': _nota_json(n)})
    if accion == 'ordenar':
        ids = [int(x) for x in request.POST.getlist('ids') if x.isdigit()]
        for i, pk in enumerate(ids):
            mias.filter(pk=pk).update(orden=i)
        return JsonResponse({'ok': True})
    n = mias.filter(pk=request.POST.get('id') or 0).first()
    if n is None:
        return JsonResponse({'ok': False}, status=404)
    if accion == 'borrar':
        n.delete()
        return JsonResponse({'ok': True})
    if 'texto' in request.POST:
        n.texto = request.POST['texto'][:400]
    if request.POST.get('color') in dict(NotaPizarra.COLORES):
        n.color = request.POST['color']
    if 'hecha' in request.POST:
        n.hecha = request.POST['hecha'] == '1'
    n.save()
    return JsonResponse({'ok': True, 'nota': _nota_json(n)})


def models_F(campo):
    from django.db.models import F
    return F(campo)


def _mis_aulas(cuenta):
    from aula.models import Aula
    return list(Aula.objects.filter(grupo__propietario=cuenta, grupo__activo=True).select_related('grupo').order_by('grupo__nombre'))


@cuenta_requerida
def tablero(request):
    """Mis tableros: cada uno es una pantalla infinita para escribir, dibujar y pegar imágenes; se comparte con un grupo."""
    from django.db.models import Count, Sum
    from django.utils.safestring import mark_safe
    from aula import tablero as TB
    from aula.models import TableroClase
    from . import limites
    if request.method == 'POST':
        if not limites.cupo_tableros(request.user):
            return limites.a_planes(request, 'tableros', 'premium')
        t = TableroClase.objects.create(autor=request.user, titulo=' '.join((request.POST.get('titulo') or '').split())[:80]
                                        or f'Tablero del {timezone.localdate():%d/%m/%Y}',
                                        carpeta=' '.join((request.POST.get('carpeta') or '').split())[:60])
        return redirect('salon_digital:tablero_abrir', pk=t.pk)
    todos = TableroClase.objects.filter(autor=request.user)
    carpetas = sorted({c for c in todos.values_list('carpeta', flat=True) if c}, key=str.lower)
    q, carpeta = ' '.join((request.GET.get('q') or '').split()), request.GET.get('carpeta')
    tableros = todos.select_related('aula__grupo').annotate(n_img=Count('imagenes'), mb_img=Sum('imagenes__peso'))
    if q:
        tableros = tableros.filter(titulo__icontains=q)
    if carpeta == '-':
        tableros = tableros.filter(carpeta='')
    elif carpeta:
        tableros = tableros.filter(carpeta=carpeta)
    tableros = list(tableros)
    for t in tableros:
        t.mini = mark_safe(TB.miniatura(t, lambda iid, t=t: reverse('aula:tablero_imagen', args=[t.pk, iid])))
        t.mb = round((t.mb_img or 0) / 1048576, 1)
    cuenta = request.cuenta
    tope = cuenta.limite('tableros') if not request.user.is_superuser else 0
    from materiales.views import cuota_nube, usado_nube
    usado, cuota = usado_nube(request.user), cuota_nube(request.user, cuenta)
    return render(request, 'salon_digital/tableros.html', {
        'tableros': tableros, 'total': todos.count(), 'tope': tope, 'lleno': bool(tope) and todos.count() >= tope,
        'carpetas': carpetas, 'q': q, 'carpeta': carpeta or '',
        'nube': {'usado_mb': round(usado / 1048576, 1), 'cuota_mb': round(cuota / 1048576),
                 'porcentaje': min(100, round(usado * 100 / cuota)) if cuota else 0}})


@require_POST
@cuenta_requerida
def tablero_duplicar(request, pk):
    """Una copia del tablero (con sus imágenes) para reutilizarlo con otro grupo: queda sin compartir."""
    from django.core.files.base import ContentFile
    from aula.models import ImagenTablero, TableroClase
    from materiales.views import cuota_nube, usado_nube
    from . import limites
    t = get_object_or_404(TableroClase, pk=pk, autor=request.user)
    if not limites.cupo_tableros(request.user):
        return limites.a_planes(request, 'tableros', 'premium')
    imagenes = list(t.imagenes.all())
    peso = sum(i.peso for i in imagenes)
    if peso and usado_nube(request.user) + peso > cuota_nube(request.user, request.cuenta):
        messages.warning(request, 'No hay espacio en su nube para copiar las imágenes de este tablero.')
        return redirect('salon_digital:tablero')
    copia = TableroClase.objects.create(autor=request.user, titulo=f'{t.titulo[:72]} (copia)', fondo=t.fondo, carpeta=t.carpeta)
    nuevas = {}
    for i in imagenes:
        try:
            with i.archivo.open('rb') as f:
                datos = f.read()
        except Exception:
            continue
        n = ImagenTablero(tablero=copia, ancho=i.ancho, alto=i.alto, peso=len(datos))
        n.archivo.save('imagen.' + (i.archivo.name.rsplit('.', 1)[-1] if '.' in i.archivo.name else 'jpg'), ContentFile(datos), save=False)
        n.save()
        nuevas[i.pk] = n.pk
    objetos = []
    for o in t.objetos or []:
        if o.get('t') == 'imagen':
            if o.get('img') not in nuevas:
                continue
            o = dict(o, img=nuevas[o['img']])
        objetos.append(o)
    copia.objetos = objetos
    copia.save(update_fields=['objetos'])
    messages.success(request, f'Se creó «{copia.titulo}». Puede compartirlo con otro grupo.')
    return redirect('salon_digital:tablero')


@require_POST
@cuenta_requerida
def tablero_organizar(request, pk):
    """Cambiar el título o la carpeta desde la lista del repositorio."""
    from aula.models import TableroClase
    t = get_object_or_404(TableroClase, pk=pk, autor=request.user)
    if 'titulo' in request.POST:
        t.titulo = ' '.join(request.POST['titulo'].split())[:80] or t.titulo
    if 'carpeta' in request.POST:
        t.carpeta = ' '.join(request.POST['carpeta'].split())[:60]
    t.save(update_fields=['titulo', 'carpeta'])          # sin tocar «actualizado»: el orden es por lo último dibujado
    volver = request.POST.get('volver') or ''
    return redirect(volver if volver.startswith('/salon_digital/pizarra/tablero/') else reverse('salon_digital:tablero'))


@cuenta_requerida
def tablero_abrir(request, pk):
    from aula.models import TableroClase
    from aula.views_tablero import config
    t = get_object_or_404(TableroClase, pk=pk, autor=request.user)
    return render(request, 'salon_digital/tablero.html', {
        'cfg': config(request, t, ('d', True, True), reverse('salon_digital:tablero')), 't': t, 'es_dueno': True,
        'aulas': [{'id': a.pk, 'nombre': a.titulo} for a in _mis_aulas(request.cuenta)]})


@require_POST
@cuenta_requerida
def tablero_compartir(request, pk):
    """Compartir con una clase (o dejar de compartir), permitir que los estudiantes escriban y cambiar el título."""
    from django.http import JsonResponse
    from aula import logica
    from aula.models import TableroClase
    t = get_object_or_404(TableroClase, pk=pk, autor=request.user)
    if 'titulo' in request.POST:
        t.titulo = ' '.join(request.POST['titulo'].split())[:80] or t.titulo
    aulas = {a.pk: a for a in _mis_aulas(request.cuenta)}
    antes = t.aula_id
    if 'aula' in request.POST:
        valor = request.POST.get('aula') or ''
        t.aula = aulas.get(int(valor)) if valor.isdigit() else None
    if 'editan' in request.POST:
        t.editan_estudiantes = request.POST.get('editan') == '1'
    t.save(update_fields=['titulo', 'aula', 'editan_estudiantes', 'actualizado'])
    url = ''
    if t.aula_id:
        url = request.build_absolute_uri(reverse('aula:tablero_ver', args=[t.aula_id, t.pk]))
        if t.aula_id != antes:
            logica.avisar_estudiantes(t.aula, f'{t.aula.titulo}: el docente compartió el tablero «{t.titulo}» 📋', url)
    return JsonResponse({'ok': True, 'compartido': bool(t.aula_id), 'aula': t.aula_id, 'editan': t.editan_estudiantes,
                         'url': url, 'titulo': t.titulo})


@require_POST
@cuenta_requerida
def tablero_eliminar(request, pk):
    from aula.models import TableroClase
    t = get_object_or_404(TableroClase, pk=pk, autor=request.user)
    for img in t.imagenes.all():
        img.archivo.delete(save=False)
    t.delete()
    messages.info(request, 'Tablero eliminado.')
    return redirect('salon_digital:tablero')
