"""Elecciones escolares: preparar (directivos), votar (estudiantes y docentes, o en la mesa) y resultados."""
from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Max
from django.http import Http404, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from notas.models import Curso, Estudiante, Notificacion
from notas.permisos import es_admin

from . import logica as L
from .models import Candidato, Cargo, Eleccion, VotoEmitido

CLAVE_MESA = 'votaciones_mesa'       # {'eleccion': id, 'votante': user_id} mientras un estudiante vota en la mesa


def del_colegio(fn):
    @login_required
    @wraps(fn)
    def envoltura(request, *args, **kwargs):
        if getattr(request, 'colegio', None) is None:
            raise Http404
        return fn(request, *args, **kwargs)
    return envoltura


def solo_admin(fn):
    @del_colegio
    @wraps(fn)
    def envoltura(request, *args, **kwargs):
        if not es_admin(request):
            return HttpResponseForbidden('Esta sección es para los directivos del colegio.')
        return fn(request, *args, **kwargs)
    return envoltura


def _eleccion(request, pk):
    return get_object_or_404(Eleccion, pk=pk, colegio=request.colegio)


def _puede_jurado(request):
    tipo, _ = L.votante(request.user, request.colegio)
    return es_admin(request) or tipo == 'docente'


# ---------------------------------------------------------------------------
# Inicio: el votante ve su tarjetón; el directivo, sus elecciones
# ---------------------------------------------------------------------------
@del_colegio
def inicio(request):
    tipo, persona = L.votante(request.user, request.colegio)
    abiertas = []
    for e in Eleccion.objects.filter(colegio=request.colegio, estado='abierta'):
        cargos = L.cargos_de(e, tipo, persona) if tipo else []
        if cargos:
            abiertas.append({'e': e, 'ya': VotoEmitido.objects.filter(eleccion=e, usuario=request.user).exists(),
                             'cargos': len(cargos)})
    admin = es_admin(request)
    if request.method == 'POST' and admin:
        nombre = ' '.join((request.POST.get('nombre') or '').split())[:120] or f'Elección del gobierno escolar {timezone.localdate().year}'
        e = Eleccion.objects.create(colegio=request.colegio, nombre=nombre, creada_por=request.user)
        if request.POST.get('plantilla') == 'on':
            L.plantilla_basica(e)
        return redirect('votaciones:eleccion', pk=e.pk)
    return render(request, 'votaciones/inicio.html', {
        'abiertas': abiertas, 'admin': admin, 'jurado': _puede_jurado(request),
        'elecciones': Eleccion.objects.filter(colegio=request.colegio) if admin else
        Eleccion.objects.filter(colegio=request.colegio, estado='abierta'),
        'cerradas': Eleccion.objects.filter(colegio=request.colegio, estado='cerrada')[:5],
        'mis_certificados': Eleccion.objects.filter(colegio=request.colegio, votantes__usuario=request.user).exclude(estado='abierta')[:10]})


# ---------------------------------------------------------------------------
# Preparar la elección (directivos)
# ---------------------------------------------------------------------------
GRADOS = [(g, f'{g}°') for g in range(-2, 12)]


@solo_admin
def eleccion(request, pk):
    e = _eleccion(request, pk)
    if request.method == 'POST':
        que = request.POST.get('accion')
        editable = e.estado == 'preparacion'
        if que == 'cargo' and editable:
            nombre = ' '.join((request.POST.get('nombre') or '').split())[:80]
            votan = request.POST.get('votan') if request.POST.get('votan') in dict(Cargo.VOTAN) else 'estudiantes'
            if nombre:
                def grado(campo):
                    try:
                        return int(request.POST.get(campo)) if request.POST.get(campo) not in (None, '') else None
                    except ValueError:
                        return None
                Cargo.objects.create(eleccion=e, nombre=nombre, votan=votan, voto_blanco=request.POST.get('blanco') == 'on',
                                     grado_desde=grado('desde') if votan == 'grados' else None,
                                     grado_hasta=grado('hasta') if votan == 'grados' else None,
                                     orden=(e.cargos.aggregate(m=Max('orden'))['m'] or 0) + 1)
        elif que == 'quitar_cargo' and editable:
            Cargo.objects.filter(eleccion=e, pk=request.POST.get('cargo') or 0).delete()
        elif que == 'candidato' and editable:
            cargo = get_object_or_404(Cargo, pk=request.POST.get('cargo') or 0, eleccion=e)
            usuario = None
            curso = None
            nombre = ' '.join((request.POST.get('nombre') or '').split())[:150]
            est = Estudiante.objects.filter(pk=request.POST.get('estudiante') or 0, colegio=request.colegio).select_related('user', 'curso').first()
            if est is not None:
                usuario, curso = est.user, est.curso
                nombre = nombre or (est.user.get_full_name() or est.user.username)
            if cargo.votan == 'curso' and curso is None:
                messages.error(request, f'Para «{cargo.nombre}» escoja un estudiante: cada curso vota por los de su curso.')
            elif not nombre:
                messages.error(request, 'Escoja el estudiante o escriba el nombre del candidato.')
            else:
                hermanos = cargo.candidatos.filter(curso=curso) if cargo.votan == 'curso' else cargo.candidatos.all()
                c = Candidato(cargo=cargo, nombre=nombre, usuario=usuario, curso=curso,
                              numero=(hermanos.aggregate(m=Max('numero'))['m'] or 0) + 1,
                              propuesta=(request.POST.get('propuesta') or '').strip()[:1500])
                foto = request.FILES.get('foto')
                if foto is not None:
                    try:
                        from django.core.files.base import ContentFile
                        from materiales.views import preparar_imagen
                        datos, ext, _, _ = preparar_imagen(foto)
                        c.foto.save(f'candidato{ext}', ContentFile(datos), save=False)
                    except ValueError as error:
                        messages.warning(request, f'La foto no se guardó: {error}')
                c.save()
                messages.success(request, f'Candidato agregado: {c.numero}. {c.nombre}.')
        elif que == 'quitar_candidato' and editable:
            Candidato.objects.filter(cargo__eleccion=e, pk=request.POST.get('candidato') or 0).delete()
        elif que == 'abrir' and e.estado == 'preparacion':
            vacios = [c.nombre for c in e.cargos.all() if not c.candidatos.exists()]
            if not e.cargos.exists():
                messages.error(request, 'Agregue al menos un cargo con sus candidatos.')
            elif vacios:
                messages.error(request, 'Estos cargos no tienen candidatos: ' + ', '.join(vacios) + '.')
            else:
                e.estado, e.abierta_en = 'abierta', timezone.now()
                e.save(update_fields=['estado', 'abierta_en'])
                _avisar(e)
                messages.success(request, 'Votación abierta. Se avisó a quienes pueden votar.')
        elif que == 'cerrar' and e.estado == 'abierta':
            e.estado, e.cerrada_en = 'cerrada', timezone.now()
            e.save(update_fields=['estado', 'cerrada_en'])
            messages.success(request, 'Votación cerrada. Ya puede ver los resultados y el acta.')
        elif que == 'renombrar':
            nombre = ' '.join((request.POST.get('nombre') or '').split())[:120]
            if nombre:
                e.nombre = nombre
                e.save(update_fields=['nombre'])
        elif que == 'eliminar':
            # En preparación basta con confirmar. Abierta o cerrada ya tiene votos:
            # solo se borra si fue un error y escribiendo ELIMINAR, porque se pierden
            # los votos, los resultados y el acta.
            if e.estado != 'preparacion' and (request.POST.get('confirmacion') or '').strip().upper() != 'ELIMINAR':
                messages.error(request, 'Para eliminar una elección que ya tiene votos, escriba ELIMINAR en la casilla.')
                return redirect('votaciones:eleccion', pk=e.pk)
            nombre, votos = e.nombre, e.votantes.count()
            for c in Candidato.objects.filter(cargo__eleccion=e).exclude(foto=''):
                try:
                    c.foto.delete(save=False)
                except Exception:
                    pass
            e.delete()
            messages.info(request, f'Elección «{nombre}» eliminada' + (f' con sus {votos} votos.' if votos else '.'))
            return redirect('votaciones:inicio')
        return redirect('votaciones:eleccion', pk=e.pk)
    estudiantes = Estudiante.objects.filter(colegio=request.colegio, is_active=True, curso__isnull=False) \
        .select_related('user', 'curso').order_by('curso__orden', 'curso__nombre', 'user__last_name', 'user__first_name')
    return render(request, 'votaciones/eleccion.html', {
        'e': e, 'cargos': e.cargos.prefetch_related('candidatos__curso'), 'estudiantes': estudiantes,
        'votan': Cargo.VOTAN, 'grados': GRADOS,
        'votaron': e.votantes.count(), 'habilitados': L.habilitados(e)})


def _avisar(e):
    from notas.models import Docente
    destinos = set()
    cargos = list(e.cargos.all())
    if any(c.votan != 'docentes' for c in cargos):
        destinos |= set(Estudiante.objects.filter(colegio=e.colegio, is_active=True, curso__isnull=False)
                        .values_list('user_id', flat=True))
    if any(c.votan == 'docentes' for c in cargos):
        destinos |= set(Docente.objects.filter(colegio=e.colegio).values_list('user_id', flat=True))
    Notificacion.objects.bulk_create([
        Notificacion(colegio=e.colegio, destinatario_id=uid, tipo='GENERAL', url='/votaciones/',
                     mensaje=f'🗳️ Ya puede votar: {e.nombre}'[:255]) for uid in destinos])


@del_colegio
def foto(request, cid):
    c = get_object_or_404(Candidato, pk=cid, cargo__eleccion__colegio=request.colegio)
    if not c.foto:
        raise Http404
    return redirect(c.foto.url)


# ---------------------------------------------------------------------------
# Votar
# ---------------------------------------------------------------------------
@del_colegio
def votar(request, pk):
    e = _eleccion(request, pk)
    tipo, persona = L.votante(request.user, request.colegio)
    return _tarjeton(request, e, request.user, tipo, persona, 'cuenta')


def _tarjeton(request, e, user, tipo, persona, medio):
    if e.estado != 'abierta':
        messages.info(request, 'Esta votación no está abierta.')
        return redirect('votaciones:inicio')
    cargos = L.cargos_de(e, tipo, persona) if tipo else []
    if not cargos:
        messages.info(request, 'En esta elección no hay cargos para usted.')
        return redirect('votaciones:inicio' if medio == 'cuenta' else 'votaciones:mesa', **({} if medio == 'cuenta' else {'pk': e.pk}))
    if VotoEmitido.objects.filter(eleccion=e, usuario=user).exists():
        if medio == 'mesa':
            request.session.pop(CLAVE_MESA, None)
            messages.warning(request, f'{user.get_full_name() or user.username} ya votó.')
            return redirect('votaciones:mesa', pk=e.pk)
        return render(request, 'votaciones/listo.html', {'e': e, 'ya': True})
    error = ''
    if request.method == 'POST':
        elegidos = {c.pk: request.POST.get(f'cargo-{c.pk}') for c, _ in cargos}
        try:
            L.emitir(e, user, tipo, persona, elegidos, medio=medio, jurado=request.user if medio == 'mesa' else None)
        except L.YaVoto:
            error = 'Ya había votado: su voto anterior es el que cuenta.'
        except ValueError as ex:
            error = str(ex)
        else:
            if medio == 'mesa':
                request.session.pop(CLAVE_MESA, None)
                return render(request, 'votaciones/listo.html', {'e': e, 'mesa': True})
            return render(request, 'votaciones/listo.html', {'e': e})
    return render(request, 'votaciones/tarjeton.html', {
        'e': e, 'cargos': cargos, 'error': error, 'mesa': medio == 'mesa',
        'quien': user.get_full_name() or user.username,
        'curso': getattr(persona, 'curso', None)})


# ---------------------------------------------------------------------------
# Mesa de votación: un computador o tableta del colegio con un jurado al lado
# ---------------------------------------------------------------------------
@del_colegio
def mesa(request, pk):
    e = _eleccion(request, pk)
    if not _puede_jurado(request):
        return HttpResponseForbidden('La mesa de votación la abre un docente o un directivo.')
    sesion = request.session.get(CLAVE_MESA) or {}
    if sesion.get('eleccion') == e.pk and sesion.get('votante'):
        user = User.objects.filter(pk=sesion['votante']).first()
        tipo, persona = L.votante(user, request.colegio)
        if request.method == 'POST' and request.POST.get('accion') == 'cancelar':
            request.session.pop(CLAVE_MESA, None)
            return redirect('votaciones:mesa', pk=e.pk)
        if tipo == 'estudiante':
            return _tarjeton(request, e, user, tipo, persona, 'mesa')
        request.session.pop(CLAVE_MESA, None)
    error = ''
    if request.method == 'POST' and request.POST.get('accion') == 'buscar':
        q = (request.POST.get('usuario') or '').strip()
        est = Estudiante.objects.filter(colegio=request.colegio, is_active=True, user__username__iexact=q) \
            .select_related('user', 'curso').first()
        if est is None:
            # También sirve el QR del carné (con un lector USB queda escrito aquí).
            from notas.views.carnet_views import codigo_leido
            codigo = codigo_leido(q)
            if codigo:
                est = Estudiante.objects.filter(colegio=request.colegio, is_active=True, codigo_carnet=codigo) \
                    .select_related('user', 'curso').first()
        if est is None:
            error = 'No hay un estudiante activo con ese usuario en el colegio.'
        elif VotoEmitido.objects.filter(eleccion=e, usuario=est.user).exists():
            error = f'{est.user.get_full_name() or est.user.username} ({est.curso.nombre if est.curso_id else "sin curso"}) ya votó.'
        elif e.estado != 'abierta':
            error = 'La votación no está abierta.'
        else:
            request.session[CLAVE_MESA] = {'eleccion': e.pk, 'votante': est.user_id}
            return redirect('votaciones:mesa', pk=e.pk)
    return render(request, 'votaciones/mesa.html', {
        'e': e, 'error': error, 'votaron': e.votantes.count(),
        'en_mesa': e.votantes.filter(jurado=request.user).count()})


# ---------------------------------------------------------------------------
# Resultados y acta
# ---------------------------------------------------------------------------
@solo_admin
def resultados(request, pk):
    e = _eleccion(request, pk)
    return render(request, 'votaciones/resultados.html', {
        'e': e, 'resultados': L.resultados(e), 'votaron': e.votantes.count(), 'habilitados': L.habilitados(e),
        'por_curso': L.participacion_por_curso(e),
        'por_mesa': e.votantes.filter(medio='mesa').count()})


@solo_admin
def acta(request, pk):
    e = _eleccion(request, pk)
    if e.estado != 'cerrada':
        messages.info(request, 'El acta sale cuando se cierra la votación.')
        return redirect('votaciones:resultados', pk=e.pk)
    votaron, habilitados = e.votantes.count(), L.habilitados(e)
    return render(request, 'votaciones/acta.html', {
        'e': e, 'resultados': L.resultados(e), 'votaron': votaron, 'habilitados': habilitados,
        'pct': round(votaron * 100 / habilitados, 1) if habilitados else 0, 'hoy': timezone.localtime()})


# ---------------------------------------------------------------------------
# Quién votó y quién no, y el certificado electoral
# ---------------------------------------------------------------------------
@solo_admin
def votantes(request, pk):
    """Lista de las personas habilitadas: quién ya votó (cuándo y cómo) y quién falta. Nunca dice por quién votó."""
    e = _eleccion(request, pk)
    curso_id = request.GET.get('curso') if (request.GET.get('curso') or '').isdigit() else None
    estado = request.GET.get('estado') if request.GET.get('estado') in ('votaron', 'faltan') else ''
    filas = L.lista_votantes(e, curso_id)
    total, votaron = len(filas), sum(1 for f in filas if f['voto'])
    if estado == 'votaron':
        filas = [f for f in filas if f['voto']]
    elif estado == 'faltan':
        filas = [f for f in filas if not f['voto']]
    if request.GET.get('excel'):
        return _votantes_excel(e, filas)
    return render(request, 'votaciones/votantes.html', {
        'e': e, 'filas': filas, 'total': total, 'votaron': votaron, 'faltan': total - votaron,
        'pct': round(votaron * 100 / total) if total else 0, 'curso_id': int(curso_id) if curso_id else None, 'estado': estado,
        'cursos': Curso.objects.filter(colegio=request.colegio).order_by('orden', 'nombre')})


def _votantes_excel(e, filas):
    from django.http import HttpResponse
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill
    wb = Workbook()
    ws = wb.active
    ws.title = 'Votantes'
    ws.append([e.nombre])
    ws['A1'].font = Font(bold=True, size=13)
    ws.append(['Nombre', 'Curso', 'Votó', 'Fecha y hora', 'Cómo votó'])
    for c in ws[2]:
        c.font = Font(bold=True, color='FFFFFF')
        c.fill = PatternFill('solid', fgColor='1F3A68')
    for f in filas:
        v = f['voto']
        ws.append([f['nombre'], f['curso'].nombre if f['curso'] else 'Docente', 'Sí' if v else 'No',
                   timezone.localtime(v.creado).strftime('%d/%m/%Y %I:%M %p') if v else '', v.get_medio_display() if v else ''])
    for col, ancho in zip('ABCDE', (38, 12, 8, 22, 22)):
        ws.column_dimensions[col].width = ancho
    r = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    r['Content-Disposition'] = f'attachment; filename="votantes-{e.pk}.xlsx"'
    wb.save(r)
    return r


@del_colegio
def certificado(request, pk):
    """El certificado electoral de quien votó. El estudiante descarga el suyo; un directivo puede imprimir el de cualquier
    votante (?u=<id>), por ejemplo para quien votó en la mesa o en una cabina."""
    e = _eleccion(request, pk)
    usuario = request.user
    if request.GET.get('u') and es_admin(request):
        usuario = get_object_or_404(User, pk=request.GET.get('u'))
    voto = VotoEmitido.objects.filter(eleccion=e, usuario=usuario).select_related('curso').first()
    if voto is None:
        messages.info(request, 'El certificado electoral es para quien ya votó en esta elección.')
        return redirect('votaciones:inicio')
    tipo, persona = L.votante(usuario, request.colegio)
    documento = ''
    if tipo == 'estudiante':
        ficha = getattr(persona, 'ficha', None) if hasattr(persona, 'ficha') else None
        documento = f'{ficha.get_tipo_documento_display()} {ficha.numero_documento}' if ficha and ficha.numero_documento else ''
    codigo = L.codigo_certificado(e.pk, usuario.pk)
    return render(request, 'votaciones/certificado.html', {
        'e': e, 'colegio': request.colegio, 'voto': voto, 'nombre': usuario.get_full_name() or usuario.username,
        'tipo': tipo, 'documento': documento, 'curso': voto.curso or getattr(persona, 'curso', None), 'codigo': codigo,
        'verificar': request.build_absolute_uri(f'/votaciones/certificado/verificar/?codigo={codigo}')})


def verificar_certificado(request):
    """Cualquiera puede comprobar si un certificado electoral es auténtico con su código."""
    colegio = getattr(request, 'colegio', None)
    if colegio is None:
        raise Http404
    codigo = (request.GET.get('codigo') or '').strip()
    voto = L.buscar_certificado(colegio, codigo) if codigo else None
    return render(request, 'votaciones/verificar.html', {'colegio': colegio, 'codigo': codigo, 'voto': voto,
                                                         'nombre': (voto.usuario.get_full_name() or voto.usuario.username) if voto else ''})
