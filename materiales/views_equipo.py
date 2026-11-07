"""Trabajo colaborativo en Mis materiales: invitar docentes a construir una guía juntos.

  · En el colegio se invita a los compañeros del mismo colegio (docentes y directivos).
  · En el plan individual (Mi Salón Virtual) se invita a los colegas de «Mis colegas».
  · El dueño decide si cada invitado puede editar o solo ver, y lo puede quitar. El invitado acepta o rechaza,
    y puede salirse cuando quiera. Solo el dueño borra el material o lo marca como formato.
  · Si dos docentes guardan a la vez sobre la misma versión, el segundo recibe un aviso en vez de borrar lo del
    primero (Documento.version), y el editor muestra quién más lo tiene abierto.
"""
import time

from django.contrib import messages
from django.contrib.auth.models import User
from django.core.cache import cache
from django.db.models import Q
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.views.decorators.http import require_POST

from .models import Colaborador, Documento
from .views import vista

PRESENCIA_SEG = 45


def nombre(u):
    return (u.get_full_name() or u.username) if u else ''


def accesibles(a):
    """Los materiales del docente y los que construye con otros (en el mismo colegio o en el plan individual)."""
    return Documento.objects.filter(colegio=a.colegio).filter(
        Q(propietario=a.request.user) | Q(colaboradores__usuario=a.request.user, colaboradores__estado='aceptada')).distinct()


def doc_equipo(a, pk):
    """(documento, rol): 'dueno', 'editar' o 'ver'. 404 si no es del docente ni lo invitaron."""
    doc = get_object_or_404(Documento, pk=pk, colegio=a.colegio)
    if doc.propietario_id == a.request.user.pk:
        return doc, 'dueno'
    c = Colaborador.objects.filter(documento=doc, usuario=a.request.user, estado='aceptada').first()
    if c is None:
        raise Http404
    return doc, c.permiso


def _avisar(a, destino, texto, url='/materiales/'):
    from notas.models import Notificacion
    Notificacion.objects.bulk_create([Notificacion(colegio=a.colegio, destinatario=destino, tipo='GENERAL', url=url,
                                                   mensaje=texto[:255])])


# ---------------------------------------------------------------------------
# A quién se puede invitar
# ---------------------------------------------------------------------------
def candidatos(a):
    """Usuarios que este docente puede invitar: compañeros del colegio o colegas del plan individual."""
    yo = a.request.user
    if a.colegio is not None:
        return (User.objects.filter(is_active=True).filter(
            Q(docente__colegio=a.colegio) | Q(administraciones__colegio=a.colegio, administraciones__activo=True))
            .exclude(pk=yo.pk).distinct())
    from chat.views_colegas import mis_colegas
    return mis_colegas(yo).exclude(pk=yo.pk)


def _areas_de(a, ids):
    """{usuario_id: 'Matemáticas, Física'} para mostrar al lado del nombre."""
    if a.colegio is not None:
        from notas.models import AsignacionDocente
        filas = (AsignacionDocente.objects.filter(colegio=a.colegio, docente__user_id__in=ids)
                 .values_list('docente__user_id', 'materia__nombre').distinct())
    else:
        from chat.models import PerfilColega
        filas = PerfilColega.objects.filter(usuario_id__in=ids).exclude(area='').values_list('usuario_id', 'area')
    out = {}
    for uid, area in filas:
        if area and area not in out.setdefault(uid, []):
            out[uid].append(area)
    return {k: ', '.join(v[:3]) for k, v in out.items()}


def areas_disponibles(a):
    if a.colegio is not None:
        from notas.models import AsignacionDocente
        return sorted({n for n in AsignacionDocente.objects.filter(colegio=a.colegio).values_list('materia__nombre', flat=True) if n})
    from chat.models import PerfilColega
    return sorted({x for x in PerfilColega.objects.filter(usuario__in=candidatos(a)).values_list('area', flat=True) if x})


def _filtrar(a, qs, q, area):
    for palabra in q.split()[:3]:
        qs = qs.filter(Q(first_name__icontains=palabra) | Q(last_name__icontains=palabra) | Q(email__iexact=palabra))
    if area:
        if a.colegio is not None:
            from notas.models import AsignacionDocente
            ids = AsignacionDocente.objects.filter(colegio=a.colegio, materia__nombre__icontains=area).values('docente__user_id')
        else:
            from chat.models import PerfilColega
            ids = PerfilColega.objects.filter(area__icontains=area).values('usuario_id')
        qs = qs.filter(pk__in=ids)
    return qs


def _equipo_json(doc):
    return [{'id': c.pk, 'usuario': c.usuario_id, 'nombre': nombre(c.usuario), 'permiso': c.permiso, 'estado': c.estado}
            for c in doc.colaboradores.select_related('usuario')]


@vista
def equipo(request, a, pk):
    """GET: el equipo y la búsqueda de docentes (q, area). POST (solo el dueño): invitar, permiso, quitar."""
    doc, rol = doc_equipo(a, pk)
    if request.method == 'POST':
        if rol != 'dueno':
            return JsonResponse({'ok': False, 'error': 'Solo el dueño del material invita o quita docentes.'}, status=403)
        que = request.POST.get('accion')
        if que == 'invitar':
            otro = candidatos(a).filter(pk=request.POST.get('usuario') or 0).first()
            if otro is None:
                return JsonResponse({'ok': False, 'error': 'Ese docente no se puede invitar.' + (
                    '' if a.colegio is not None else ' En el plan individual primero deben ser colegas.')}, status=400)
            permiso = 'ver' if request.POST.get('permiso') == 'ver' else 'editar'
            c, nuevo = Colaborador.objects.get_or_create(documento=doc, usuario=otro,
                                                         defaults={'permiso': permiso, 'invitado_por': request.user})
            if nuevo:
                _avisar(a, otro, f'{nombre(request.user)} lo invitó a construir «{doc.titulo}» en Mis materiales.')
        elif que == 'permiso':
            Colaborador.objects.filter(documento=doc, pk=request.POST.get('colaborador') or 0).update(
                permiso='ver' if request.POST.get('permiso') == 'ver' else 'editar')
        elif que == 'quitar':
            Colaborador.objects.filter(documento=doc, pk=request.POST.get('colaborador') or 0).delete()
        return JsonResponse({'ok': True, 'equipo': _equipo_json(doc)})
    q = ' '.join((request.GET.get('q') or '').split())[:60]
    area = (request.GET.get('area') or '').strip()[:80]
    encontrados = []
    if rol == 'dueno' and (q or area or request.GET.get('todos')):
        ya = set(doc.colaboradores.values_list('usuario_id', flat=True))
        lista = list(_filtrar(a, candidatos(a), q, area).exclude(pk__in=ya).order_by('first_name', 'last_name')[:40])
        areas = _areas_de(a, [u.pk for u in lista])
        encontrados = [{'id': u.pk, 'nombre': nombre(u), 'area': areas.get(u.pk, '')} for u in lista]
    return JsonResponse({'ok': True, 'rol': rol, 'equipo': _equipo_json(doc), 'encontrados': encontrados,
                         'areas': areas_disponibles(a) if rol == 'dueno' else []})


@require_POST
@vista
def invitacion(request, a, cid):
    """El invitado acepta o rechaza; un colaborador se sale."""
    c = get_object_or_404(Colaborador, pk=cid, usuario=request.user, documento__colegio=a.colegio)
    que = request.POST.get('accion')
    if que == 'aceptar' and c.estado == 'pendiente':
        c.estado = 'aceptada'
        c.save(update_fields=['estado'])
        _avisar(a, c.documento.propietario, f'{nombre(request.user)} aceptó construir «{c.documento.titulo}» con usted.',
                f'/materiales/{c.documento_id}/')
        messages.success(request, f'Ya puede trabajar en «{c.documento.titulo}».')
        return redirect('materiales:editor', pk=c.documento_id)
    if que in ('rechazar', 'salir'):
        titulo = c.documento.titulo
        c.delete()
        messages.info(request, f'Ya no está en «{titulo}».')
    return redirect('materiales:lista')


@vista
def estado(request, a, pk):
    """Para el editor: la versión guardada y quién más tiene el material abierto ahora."""
    doc, rol = doc_equipo(a, pk)
    clave = f'mm-presencia:{doc.pk}'
    ahora = time.time()
    presentes = {k: v for k, v in (cache.get(clave) or {}).items() if ahora - v[1] < PRESENCIA_SEG}
    presentes[str(request.user.pk)] = (nombre(request.user), ahora)
    cache.set(clave, presentes, 300)
    return JsonResponse({'version': doc.version, 'editado_por': nombre(doc.editado_por),
                         'editado_por_otro': bool(doc.editado_por_id and doc.editado_por_id != request.user.pk),
                         'presentes': [v[0] for k, v in presentes.items() if k != str(request.user.pk)]})
