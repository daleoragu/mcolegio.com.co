"""PuntoExacto · informes en PDF al estilo ICFES (por estudiante y general) y pruebas unidas (varios exámenes)."""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.utils import timezone

from . import graficas_informe as GR
from . import informes as INF
from .models import PruebaUnida
from .views import _cuenta_de, _examen_o_404, _examenes_visibles, personal_requerido


# ----------------------------------------------------------------------------- piezas comunes
def _pdf(request, plantilla, ctx, nombre):
    from weasyprint import HTML
    html = render_to_string(plantilla, ctx, request=request)
    r = HttpResponse(HTML(string=html, base_url=request.build_absolute_uri('/')).write_pdf(), content_type='application/pdf')
    r['Content-Disposition'] = f'inline; filename="{nombre}.pdf"'
    return r


def _luz(hexa):
    """Luminancia relativa (0 oscuro · 1 claro) de un color #rrggbb."""
    try:
        r, g, b = (int(hexa.lstrip('#')[i:i + 2], 16) / 255 for i in (0, 2, 4))
    except (ValueError, AttributeError):
        return 0
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def _tema(request):
    """Colores y logo de la plataforma: los del colegio, o los de Mi Salón Virtual en el plan individual."""
    col = getattr(request, 'colegio', None)
    primario, texto, acento, logo = '#1e3a8a', '#ffffff', '#f59e0b', ''
    if col:
        primario = col.color_primario or primario
        texto = col.color_texto_primario or texto
        acento = col.color_iconos_topbar or acento
        if col.logo_izquierdo:
            try:
                import base64
                import mimetypes
                with col.logo_izquierdo.open('rb') as f:
                    tipo = mimetypes.guess_type(col.logo_izquierdo.name)[0] or 'image/png'
                    logo = f'data:{tipo};base64,{base64.b64encode(f.read()).decode()}'
            except Exception:
                logo = ''
    if _luz(primario) > 0.75:             # un primario muy claro no sirve de fondo para títulos: se usa el azul
        primario, texto = '#1e3a8a', '#ffffff'
    return {'primario': primario, 'texto': texto, 'acento': acento,
            'acento_txt': acento if _luz(acento) < 0.55 else primario, 'logo': logo}


def _institucion(request):
    col = getattr(request, 'colegio', None)
    if col:
        return col.nombre
    cuenta = _cuenta_de(request)
    return (request.user.get_full_name() or request.user.username) if cuenta else ''


def _ctx_general(request, datos):
    globales = [p['global'] for p in datos['personas']]
    preguntas = sorted(datos['preguntas'], key=lambda q: q['pct'])
    tema = _tema(request)
    c = tema['primario']
    return {'d': datos, 'r': datos['resumen'], 'institucion': _institucion(request), 'hoy': timezone.localdate(), 'tema': tema,
            'g_areas': GR.barras_areas(datos['areas'], color=c), 'g_niveles': GR.niveles_areas(datos['areas'], color=c),
            'g_hist': GR.histograma(globales, color=c), 'dificiles': preguntas[:10], 'faciles': preguntas[::-1][:5],
            'revisar': [q for q in datos['preguntas'] if q['disc'] is not None and q['disc'] < 0],
            'que_dice': INF.QUE_DICE_NIVEL, 'varias_areas': len(datos['areas']) > 1}


def _ctx_estudiante(datos, clave, tema):
    e = INF.de_estudiante(datos, clave)
    if e is None:
        raise Http404
    c = tema['primario']
    e['g_areas'] = GR.barras_areas(e['areas'], [a['puntaje'] for a in e['areas']], color=c)
    e['g_percentil'] = GR.barra_percentil(e['persona']['percentil'], c)
    for a in e['areas']:
        a['g_percentil'] = GR.barra_percentil(a['percentil'], c)
        a['g_escalera'] = GR.escalera(a['niveles_nombres'], a['escalon'], c)
    e['recomendaciones'] = INF.recomendaciones(e['areas'])
    return e


def _fechas(datos):
    f = sorted(ex.fecha for ex in datos['examenes'] if ex.fecha)
    return {'fecha_desde': f[0] if f else None, 'fecha_hasta': f[-1] if f else None}


def _nombre_archivo(t):
    return ''.join(ch for ch in t if ch.isalnum() or ch in ' -_.')[:80].strip() or 'informe'


# ----------------------------------------------------------------------------- un examen
@login_required
@personal_requerido
def informe_general(request, examen_id):
    examen = _examen_o_404(request, examen_id)
    datos = INF.construir([examen])
    if not datos['personas']:
        messages.info(request, 'Todavía no hay hojas calificadas para hacer el informe.')
        return redirect('puntoexacto:resultados', examen_id=examen.id)
    return _pdf(request, 'puntoexacto/informe_general_pdf.html', _ctx_general(request, datos), f'Informe general - {_nombre_archivo(examen.titulo)}')


@login_required
@personal_requerido
def informe_estudiante(request, examen_id, clave):
    examen = _examen_o_404(request, examen_id)
    datos = INF.construir([examen])
    tema = _tema(request)
    e = _ctx_estudiante(datos, clave, tema)
    return _pdf(request, 'puntoexacto/informe_estudiantes_pdf.html',
                {'d': datos, 'lista': [e], 'institucion': _institucion(request), 'hoy': timezone.localdate(), 'tema': tema, **_fechas(datos)},
                f'Informe - {_nombre_archivo(e["persona"]["nombre"])}')


@login_required
@personal_requerido
def informes_estudiantes(request, examen_id):
    """Los informes de todos los estudiantes en un solo PDF (uno tras otro), para imprimir o repartir."""
    examen = _examen_o_404(request, examen_id)
    datos = INF.construir([examen])
    curso = request.GET.get('curso')
    tema = _tema(request)
    lista = [_ctx_estudiante(datos, p['clave'], tema) for p in sorted(datos['personas'], key=lambda p: (p['curso'], p['nombre']))
             if not curso or p['curso'] == curso]
    if not lista:
        messages.info(request, 'Todavía no hay hojas calificadas para hacer los informes.')
        return redirect('puntoexacto:resultados', examen_id=examen.id)
    return _pdf(request, 'puntoexacto/informe_estudiantes_pdf.html',
                {'d': datos, 'lista': lista, 'institucion': _institucion(request), 'hoy': timezone.localdate(), 'tema': tema, **_fechas(datos)},
                f'Informes por estudiante - {_nombre_archivo(examen.titulo)}')


# ----------------------------------------------------------------------------- pruebas unidas
def _unidas_visibles(request):
    col = getattr(request, 'colegio', None)
    if col:
        return PruebaUnida.objects.filter(colegio=col)
    cuenta = _cuenta_de(request)
    return PruebaUnida.objects.filter(cuenta=cuenta) if cuenta else PruebaUnida.objects.none()


def _unida_o_404(request, pk):
    u = get_object_or_404(_unidas_visibles(request), pk=pk)
    visibles = set(_examenes_visibles(request).values_list('id', flat=True))
    examenes = list(u.examenes.all().order_by('fecha', 'id'))
    if any(e.id not in visibles for e in examenes):
        raise Http404          # tiene un examen que este usuario no puede ver
    return u, examenes


@login_required
@personal_requerido
def unidas(request):
    """Lista de pruebas unidas y formulario para unir exámenes."""
    visibles = _examenes_visibles(request).filter(archivado=False).order_by('-fecha')
    if request.method == 'POST':
        ids = [int(x) for x in request.POST.getlist('examenes') if x.isdigit()]
        escogidos = list(visibles.filter(id__in=ids))
        titulo = ' '.join((request.POST.get('titulo') or '').split())[:160]
        if len(escogidos) < 2:
            messages.warning(request, 'Escoja al menos dos exámenes para unirlos.')
        elif not titulo:
            messages.warning(request, 'Póngale un nombre a la prueba (por ejemplo «Simulacro Saber 11 · noviembre»).')
        else:
            u = PruebaUnida.objects.create(titulo=titulo, colegio=getattr(request, 'colegio', None),
                                           cuenta=None if getattr(request, 'colegio', None) else _cuenta_de(request),
                                           creador=request.user)
            u.examenes.set(escogidos)
            messages.success(request, f'Listo: «{titulo}» une {len(escogidos)} exámenes.')
            return redirect('puntoexacto:unida', pk=u.pk)
    return render(request, 'puntoexacto/unidas.html', {'unidas': _unidas_visibles(request).prefetch_related('examenes'),
                                                       'examenes': visibles})


@login_required
@personal_requerido
def unida(request, pk):
    u, examenes = _unida_o_404(request, pk)
    if request.method == 'POST':
        if request.POST.get('accion') == 'eliminar':
            u.delete()
            messages.info(request, 'Prueba unida eliminada (los exámenes no cambian).')
            return redirect('puntoexacto:unidas')
        areas = {}
        for k, v in request.POST.items():
            if k.startswith('area-') and (v in INF.PRUEBAS or v == 'NO'):
                areas[k[5:]] = v
        u.areas = areas
        u.save(update_fields=['areas'])
        messages.success(request, 'Áreas guardadas.')
        return redirect('puntoexacto:unida', pk=u.pk)
    datos = INF.construir(examenes, u.titulo, u.areas)
    return render(request, 'puntoexacto/unida.html', {'u': u, 'examenes': examenes, 'd': datos, 'pruebas': INF.PRUEBAS})


@login_required
@personal_requerido
def unida_general(request, pk):
    u, examenes = _unida_o_404(request, pk)
    datos = INF.construir(examenes, u.titulo, u.areas)
    if not datos['personas']:
        messages.info(request, 'Todavía no hay hojas calificadas en estos exámenes.')
        return redirect('puntoexacto:unida', pk=u.pk)
    return _pdf(request, 'puntoexacto/informe_general_pdf.html', _ctx_general(request, datos), f'Informe general - {_nombre_archivo(u.titulo)}')


@login_required
@personal_requerido
def unida_estudiantes(request, pk, clave=None):
    u, examenes = _unida_o_404(request, pk)
    datos = INF.construir(examenes, u.titulo, u.areas)
    curso = request.GET.get('curso')
    claves = [clave] if clave else [p['clave'] for p in sorted(datos['personas'], key=lambda p: (p['curso'], p['nombre']))
                                    if not curso or p['curso'] == curso]
    tema = _tema(request)
    lista = [_ctx_estudiante(datos, k, tema) for k in claves]
    if not lista:
        messages.info(request, 'Todavía no hay hojas calificadas en estos exámenes.')
        return redirect('puntoexacto:unida', pk=u.pk)
    nombre = lista[0]['persona']['nombre'] if clave else u.titulo
    return _pdf(request, 'puntoexacto/informe_estudiantes_pdf.html',
                {'d': datos, 'lista': lista, 'institucion': _institucion(request), 'hoy': timezone.localdate(), 'tema': tema, **_fechas(datos)},
                f'Informe - {_nombre_archivo(nombre)}')
