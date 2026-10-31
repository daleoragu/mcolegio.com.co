"""Banco de preguntas de Mis materiales: el docente guarda preguntas para volver a usarlas y, en el
colegio, las puede compartir con los demás docentes."""
import json
import uuid

from django.contrib import messages
from django.core.files.base import ContentFile
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from . import bloques as B
from .models import Imagen, PreguntaBanco
from .views import MB, _doc, vista

POR_PAGINA = 40


def _visibles(a):
    """Las del docente y, en el colegio, las que otros docentes compartieron."""
    q = Q(propietario=a.request.user, colegio=a.colegio)
    if a.colegio is not None:
        q |= Q(colegio=a.colegio, compartida=True)
    return PreguntaBanco.objects.filter(q).select_related('propietario')


def texto_de(bloque, tema=''):
    """Todo lo que sirve para encontrar la pregunta después."""
    partes = [tema, bloque.get('enunciado'), bloque.get('texto')]
    partes += bloque.get('opciones') or []
    partes += bloque.get('aceptadas') or []
    partes += bloque.get('elementos') or []
    partes += [x for par in bloque.get('pares') or [] for x in par]
    partes += [g.get('nombre') for g in bloque.get('grupos') or []]
    return ' '.join(B.texto_plano(p, 2000) for p in partes if p)[:4000]


def resumen(p):
    b = p.bloque
    texto = b.get('enunciado') or b.get('texto') or ''
    if b.get('modo') == 'completar':
        texto = B.HUECO.sub('____', b.get('texto') or '') or texto
    return B.texto_plano(texto, 220) or '(sin enunciado)'


def _filtrar(qs, datos):
    for palabra in B.texto_plano(datos.get('q'), 120).split()[:6]:
        qs = qs.filter(texto__icontains=palabra)
    if datos.get('area'):
        qs = qs.filter(area__icontains=B.texto_plano(datos.get('area'), 80))
    if datos.get('grado'):
        qs = qs.filter(grado__iexact=B.texto_plano(datos.get('grado'), 40))
    if datos.get('modo') in B.MODOS_PREGUNTA:
        qs = qs.filter(modo=datos['modo'])
    if datos.get('alcance') == 'mias':
        qs = qs.filter(propietario=datos['_usuario'])
    return qs


def _validas(usuario):
    return set(Imagen.objects.filter(propietario=usuario).values_list('pk', flat=True))


def guardar_pregunta(a, bloque, area='', grado='', tema='', compartida=False, validas=None):
    """Guarda una pregunta en el banco del docente. Devuelve (pregunta, creada) o (None, error)."""
    if not isinstance(bloque, dict) or bloque.get('tipo') != 'pregunta':
        return None, 'Eso no es una pregunta.'
    validas = _validas(a.request.user) if validas is None else validas
    limpio = dict(B._limpiar_pregunta(bloque, validas), tipo='pregunta')
    if limpio['modo'] == 'hoja':
        return None, 'Las hojas sobre un PDF no van al banco: guarde el documento completo.'
    tema = B.texto_plano(tema, 120)
    texto = texto_de(limpio, tema)
    if not B.texto_plano(texto):
        return None, 'La pregunta está vacía.'
    existente = PreguntaBanco.objects.filter(propietario=a.request.user, colegio=a.colegio, modo=limpio['modo'],
                                             texto=texto).first()
    if existente is not None:
        return existente, False
    p = PreguntaBanco.objects.create(
        propietario=a.request.user, colegio=a.colegio, compartida=bool(compartida) and a.colegio is not None,
        area=B.texto_plano(area, 80), grado=B.texto_plano(grado, 40), tema=tema, modo=limpio['modo'],
        bloque=limpio, texto=texto)
    return p, True


def copiar_imagen(img, usuario):
    with img.archivo.open('rb') as f:
        datos = f.read()
    nueva = Imagen(propietario=usuario, ancho=img.ancho, alto=img.alto, peso=len(datos))
    nombre = img.archivo.name.rsplit('/', 1)[-1]
    nueva.archivo.save(nombre, ContentFile(datos), save=False)
    nueva.save()
    return nueva


def _entero(v):
    try:
        return int(v)
    except (TypeError, ValueError):
        return 0


def _json(request):
    try:
        datos = json.loads(request.body or '{}')
    except ValueError:
        return None
    return datos if isinstance(datos, dict) else None


# ---------------------------------------------------------------------------
# Para el editor (JSON)
# ---------------------------------------------------------------------------
@vista
def banco(request, a):
    datos = dict(request.GET.items(), _usuario=request.user)
    qs = _filtrar(_visibles(a), datos)
    return JsonResponse({'ok': True, 'preguntas': [{
        'id': p.pk, 'resumen': resumen(p), 'modo': B.MODOS_PREGUNTA.get(p.modo, p.modo), 'area': p.area,
        'grado': p.grado, 'tema': p.tema, 'mia': p.propietario_id == request.user.pk, 'compartida': p.compartida,
        'autor': p.propietario.get_full_name() or p.propietario.username, 'imagen': bool(p.bloque.get('imagen')),
    } for p in qs[:POR_PAGINA]]})


@require_POST
@vista
def banco_guardar(request, a):
    datos = _json(request)
    if datos is None:
        return JsonResponse({'ok': False, 'error': 'Datos dañados.'}, status=400)
    validas = _validas(request.user)
    if datos.get('documento'):
        doc = _doc(a, _entero(datos['documento']))
        nuevas = 0
        for b in doc.contenido.get('bloques', []):
            if b.get('tipo') == 'pregunta' and b.get('modo') != 'hoja':
                p, creada = guardar_pregunta(a, b, doc.area, doc.grado, datos.get('tema'), datos.get('compartida'),
                                             validas)
                nuevas += 1 if p is not None and creada is True else 0
        return JsonResponse({'ok': True, 'mensaje': f'{nuevas} pregunta{"s" if nuevas != 1 else ""} nueva'
                                                     f'{"s" if nuevas != 1 else ""} en su banco.'})
    p, resultado = guardar_pregunta(a, datos.get('bloque'), datos.get('area'), datos.get('grado'), datos.get('tema'),
                                    datos.get('compartida'), validas)
    if p is None:
        return JsonResponse({'ok': False, 'error': resultado}, status=400)
    return JsonResponse({'ok': True, 'id': p.pk,
                         'mensaje': 'Guardada en su banco.' if resultado else 'Esa pregunta ya estaba en su banco.'})


@require_POST
@vista
def banco_usar(request, a):
    """Devuelve la pregunta lista para ponerla en el documento. Si la imagen es de otro docente, se copia
    a la nube de quien la usa (así el PDF y la ficha la encuentran)."""
    datos = _json(request) or {}
    p = get_object_or_404(_visibles(a), pk=_entero(datos.get('id')))
    bloque = dict(p.bloque, id=uuid.uuid4().hex[:8], tipo='pregunta')
    imagenes = {}
    if bloque.get('imagen'):
        img = Imagen.objects.filter(pk=bloque['imagen']).first()
        if img is None:
            bloque['imagen'] = None
        elif img.propietario_id != request.user.pk:
            if a.usado() + img.peso > a.cuota():
                return JsonResponse({'ok': False, 'error': f'Su nube está llena ({round(a.cuota() / MB)} MB).'},
                                    status=400)
            try:
                img = copiar_imagen(img, request.user)
                bloque['imagen'] = img.pk
            except Exception:
                bloque['imagen'] = None
        if bloque.get('imagen'):
            imagenes[bloque['imagen']] = request.build_absolute_uri(f'/materiales/imagen/{bloque["imagen"]}/')
    PreguntaBanco.objects.filter(pk=p.pk).update(usos=p.usos + 1)
    return JsonResponse({'ok': True, 'bloque': bloque, 'imagenes': imagenes})


# ---------------------------------------------------------------------------
# Página del banco
# ---------------------------------------------------------------------------
@vista
def banco_pagina(request, a):
    datos = dict(request.GET.items(), _usuario=request.user)
    qs = _filtrar(_visibles(a), datos)
    preguntas = list(qs[:200])
    for p in preguntas:
        p.resumen = resumen(p)
        p.modo_nombre = B.MODOS_PREGUNTA.get(p.modo, p.modo)
        p.mia = p.propietario_id == request.user.pk
    return render(request, 'materiales/banco.html', {
        'base': a.base, 'acceso': a, 'preguntas': preguntas, 'total': qs.count(), 'filtro': request.GET,
        'modos': [(k, v) for k, v in B.MODOS_PREGUNTA.items() if k != 'hoja'],
        'mias': PreguntaBanco.objects.filter(propietario=request.user, colegio=a.colegio).count()})


@require_POST
@vista
def banco_accion(request, a, pk):
    p = get_object_or_404(PreguntaBanco, pk=pk, propietario=request.user, colegio=a.colegio)
    que = request.POST.get('accion')
    if que == 'eliminar':
        p.delete()
        messages.info(request, 'Pregunta quitada del banco.')
    elif que == 'compartir' and a.colegio is not None:
        p.compartida = not p.compartida
        p.save(update_fields=['compartida'])
        messages.success(request, 'Compartida con los docentes del colegio.' if p.compartida else 'Ya no está compartida.')
    elif que == 'tema':
        p.tema = B.texto_plano(request.POST.get('tema'), 120)
        p.area = B.texto_plano(request.POST.get('area'), 80)
        p.grado = B.texto_plano(request.POST.get('grado'), 40)
        p.texto = texto_de(p.bloque, p.tema)
        p.save(update_fields=['tema', 'area', 'grado', 'texto'])
        messages.success(request, 'Datos de la pregunta guardados.')
    volver = request.POST.get('volver') or ''
    if volver.startswith('/materiales/banco/') and '//' not in volver and '\\' not in volver:
        return redirect(volver)
    return redirect('materiales:banco_pagina')
