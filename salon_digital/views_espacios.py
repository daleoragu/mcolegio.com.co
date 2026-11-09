"""Inicio y Mi Espacio de Profe: las dos pantallas nuevas del rediseño de Mi Salón Virtual."""
from django.contrib import messages
from django.db.models import Q, Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from .models import PaginaPublicada
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
        'fecha': f'{DIAS[hoy.weekday()].capitalize()}, {hoy.day} de {MESES[hoy.month - 1]}',
        'grupos': grupos, 'comunidad': _comunidad(user, 5),
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
