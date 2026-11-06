"""Banco de preguntas del docente (por tema, competencia y grado).

- Se llena pegando preguntas (el mismo formato de los juegos y cuestionarios) o guardando las de un juego.
- Las compartidas las ven los demás docentes del mismo colegio.
- El editor de juegos las trae con «Traer del banco» (banco_json)."""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render

from . import planilla_preguntas
from .invertida import leer_preguntas
from .models import PreguntaBanco
from .views import _colegio_y_base, _puede_crear

MAX = 300


def visibles(request):
    """Las mías y las compartidas por los docentes de mi colegio."""
    colegio = getattr(request, 'colegio', None)
    q = Q(propietario=request.user)
    if colegio is not None:
        q |= Q(colegio=colegio, compartida=True)
    return PreguntaBanco.objects.filter(q).select_related('propietario')


def filtrar(request, qs):
    tema, buscar, de = request.GET.get('tema', ''), (request.GET.get('q') or '').strip(), request.GET.get('de', '')
    if tema:
        qs = qs.filter(tema=tema)
    if buscar:
        qs = qs.filter(Q(texto__icontains=buscar) | Q(tema__icontains=buscar) | Q(competencia__icontains=buscar))
    if de == 'mias':
        qs = qs.filter(propietario=request.user)
    elif de == 'compartidas':
        qs = qs.exclude(propietario=request.user)
    try:
        g = int(request.GET.get('grado'))
        qs = qs.filter(Q(grado=g) | Q(grado__isnull=True))
    except (TypeError, ValueError):
        pass
    return qs


def guardar_en_banco(user, colegio, preguntas, tema, competencia='', grado=None, compartida=False):
    """Guarda preguntas de selección (las que ya estaban con el mismo texto y tema no se repiten). Devuelve cuántas."""
    ya = set(PreguntaBanco.objects.filter(propietario=user, tema=tema).values_list('texto', flat=True))
    nuevas = []
    for p in preguntas:
        ops = p.get('opciones') or []
        if len(ops) < 2 or sum(1 for o in ops if o.get('correcta')) != 1 or p['texto'] in ya:
            continue
        ya.add(p['texto'])
        nuevas.append(PreguntaBanco(propietario=user, colegio=colegio, tema=tema[:80], competencia=competencia[:80], grado=grado,
                                    texto=p['texto'][:1000], opciones=[{'texto': o['texto'][:300], 'correcta': bool(o.get('correcta'))} for o in ops[:8]],
                                    compartida=compartida))
    PreguntaBanco.objects.bulk_create(nuevas)
    return len(nuevas)


@login_required
def banco(request):
    if not _puede_crear(request):
        return HttpResponseForbidden('El banco de preguntas es para los docentes.')
    colegio, base = _colegio_y_base(request)
    if request.method == 'POST':
        accion = request.POST.get('accion')
        if accion == 'agregar':
            tema = ' '.join((request.POST.get('tema') or '').split())[:80]
            preguntas = leer_preguntas(request.POST.get('preguntas') or '', MAX)
            try:
                grado = int(request.POST.get('grado'))
            except (TypeError, ValueError):
                grado = None
            if not tema:
                messages.warning(request, 'Escriba el tema de las preguntas.')
            else:
                n = guardar_en_banco(request.user, colegio, preguntas, tema, ' '.join((request.POST.get('competencia') or '').split()),
                                     grado, bool(request.POST.get('compartida')) and colegio is not None)
                malas = len(preguntas) - n
                messages.success(request, f'Se guardaron {n} pregunta(s) en «{tema}».' +
                                 (f' {malas} no se guardaron (repetidas, sin opciones o sin una correcta marcada con *).' if malas else ''))
        elif accion in ('borrar', 'compartir'):
            p = get_object_or_404(PreguntaBanco, pk=request.POST.get('pid'), propietario=request.user)
            if accion == 'borrar':
                p.delete()
            else:
                p.compartida = not p.compartida and colegio is not None
                p.save(update_fields=['compartida'])
        elif accion == 'olimpiada':
            n = _guardar_con_grado(request.user, colegio, [dict(p, tema=f"Olimpiada {p['grado']}.º · {p['tema']}") for p in planilla_preguntas.banco_olimpiada()], 'Olimpiada')
            messages.success(request, f'Se agregaron {n} pregunta(s) del banco olimpiada 6.º–11.º (tema «Olimpiada 6.º · …»).')
        elif accion == 'borrar_tema':
            n, _ = PreguntaBanco.objects.filter(propietario=request.user, tema=request.POST.get('tema', '')).delete()
            messages.success(request, f'Se borraron {n} pregunta(s).')
        return redirect(f"{request.path}?{request.GET.urlencode()}")
    todas = visibles(request)
    temas = sorted({t for t in todas.values_list('tema', flat=True)}, key=str.lower)
    lista = list(filtrar(request, todas)[:MAX])
    return render(request, 'aula/banco.html', {
        'base': base, 'colegio': colegio, 'lista': lista, 'temas': temas, 'total': todas.count(),
        'tema': request.GET.get('tema', ''), 'q': request.GET.get('q', ''), 'de': request.GET.get('de', ''),
        'grados': [(g, f'{g}.º' if g > 0 else ('Transición' if g == 0 else 'Preescolar')) for g in range(-2, 12)]})


def _guardar_con_grado(user, colegio, preguntas, tema_defecto, compartida=False):
    """Como guardar_en_banco, pero cada pregunta trae su tema y su grado (planilla o banco 6.º–11.º)."""
    ya = set(PreguntaBanco.objects.filter(propietario=user).values_list('tema', 'texto'))
    nuevas = []
    for p in preguntas:
        tema = (p.get('tema') or tema_defecto or 'Sin tema')[:80]
        if (tema, p['texto']) in ya:
            continue
        ya.add((tema, p['texto']))
        comp = {'euclides': 'Pensamiento geométrico', 'newton': 'Pensamiento numérico', 'bernoulli': 'Pensamiento aleatorio'}.get(p.get('categoria'), '')
        nuevas.append(PreguntaBanco(propietario=user, colegio=colegio, tema=tema, competencia=comp, grado=p.get('grado'),
                                    texto=p['texto'][:1000], opciones=p['opciones'][:8], compartida=compartida))
    PreguntaBanco.objects.bulk_create(nuevas)
    return len(nuevas)


@login_required
def banco_planilla(request):
    """Planilla de Excel del banco: descargar (mis preguntas, vacía o el banco 6.º–11.º) y subir.
    Con ?leer=1 (POST) solo la lee y devuelve las preguntas en el formato de pegar, para el editor de juegos."""
    from django.http import HttpResponse
    if not _puede_crear(request):
        return HttpResponseForbidden('El banco de preguntas es para los docentes.')
    colegio, _ = _colegio_y_base(request)
    if request.method == 'POST':
        archivo = request.FILES.get('archivo')
        if not archivo or archivo.size > 5 * 1024 * 1024:
            if request.GET.get('leer'):
                return JsonResponse({'texto': '', 'errores': [[0, 'Escoja la planilla (máximo 5 MB).']]})
            messages.warning(request, 'Escoja la planilla (máximo 5 MB).')
            return redirect('aula:banco')
        try:
            maximo = max(2, min(8, int(request.GET.get('max') or 8)))
        except ValueError:
            maximo = 8
        preguntas, errores = planilla_preguntas.importar(archivo, maximo)
        if request.GET.get('leer'):
            return JsonResponse({'texto': planilla_preguntas.como_texto(preguntas), 'n': len(preguntas), 'errores': errores[:50]})
        n = _guardar_con_grado(request.user, colegio, preguntas, ' '.join((request.POST.get('tema') or '').split()),
                               bool(request.POST.get('compartida')) and colegio is not None)
        messages.success(request, f'Se guardaron {n} pregunta(s) de la planilla.' + (f' {len(preguntas) - n} ya estaban.' if len(preguntas) > n else ''))
        if errores:
            messages.warning(request, f'{len(errores)} fila(s) con problemas: ' + ' · '.join((f'fila {f}: ' if f else '') + m for f, m in errores[:12]))
        return redirect('aula:banco')
    de = request.GET.get('de', 'mias')
    if de == 'olimpiada':
        lista, nombre = planilla_preguntas.banco_olimpiada(), 'banco olimpiada 6 a 11'
    elif de == 'vacia':
        lista, nombre = [], 'planilla de preguntas (vacia)'
    else:
        lista = [{'grado': p.grado, 'tema': p.tema, 'texto': p.texto, 'opciones': p.opciones,
                  'categoria': {'Pensamiento geométrico': 'euclides', 'Pensamiento numérico': 'newton', 'Pensamiento aleatorio': 'bernoulli'}.get(p.competencia, '')}
                 for p in filtrar(request, visibles(request))]
        nombre = 'mi banco de preguntas'
    archivo = planilla_preguntas.descargar(lista, 'Banco de preguntas')
    return HttpResponse(archivo.getvalue(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                        headers={'Content-Disposition': f'attachment; filename="{nombre}.xlsx"'})


@login_required
def banco_json(request):
    """Para el editor de juegos: las preguntas que se pueden traer (filtradas por tema o búsqueda)."""
    if not _puede_crear(request):
        return JsonResponse({'preguntas': [], 'temas': []}, status=403)
    if request.method == 'POST':          # se llevaron a un juego: cuenta los usos
        ids = [int(x) for x in request.POST.getlist('ids') if x.isdigit()][:MAX]
        for p in visibles(request).filter(pk__in=ids):
            p.usos += 1
            p.save(update_fields=['usos'])
        return JsonResponse({'ok': True})
    todas = visibles(request)
    lista = filtrar(request, todas)[:MAX]
    return JsonResponse({
        'temas': sorted({t for t in todas.values_list('tema', flat=True)}, key=str.lower),
        'preguntas': [{'id': p.pk, 'tema': p.tema, 'competencia': p.competencia, 'grado': p.grado, 'texto': p.texto, 'opciones': p.opciones,
                       'de': '' if p.propietario_id == request.user.pk else (p.propietario.get_full_name() or p.propietario.username)} for p in lista]})
