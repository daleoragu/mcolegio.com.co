import datetime

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import Http404, HttpResponse, HttpResponseForbidden, HttpResponseNotFound
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from notas.models import Curso, Docente
from notas.modulos import esta_activo
from notas.permisos import admin_requerido, es_admin

from . import cuadricula, intercambio, logica, nucleo
from .models import DIAS, AplicacionEscritorio, Franja, Horario, Jornada, Sesion


def _premium(request):
    return esta_activo(request.colegio, 'generador_horarios')


# ---------------------------------------------------------------------------
# Panel
# ---------------------------------------------------------------------------
@admin_requerido
def panel(request):
    colegio = request.colegio
    if not colegio:
        return HttpResponseNotFound('<h1>Colegio no configurado</h1>')
    jornadas = list(Jornada.objects.filter(colegio=colegio).prefetch_related('franjas', 'cursos'))
    en_jornada = {c.id for j in jornadas for c in j.cursos.all()}
    sin_jornada = Curso.objects.filter(colegio=colegio).exclude(id__in=en_jornada).order_by('orden')
    horarios = Horario.objects.filter(colegio=colegio).exclude(estado='ARCHIVADO')
    return render(request, 'horarios/panel.html', {
        'colegio': colegio, 'jornadas': jornadas, 'sin_jornada': sin_jornada, 'horarios': horarios,
        'archivados': Horario.objects.filter(colegio=colegio, estado='ARCHIVADO')[:10],
        'premium': _premium(request), 'app': AplicacionEscritorio.objects.first()})


def _hora(txt):
    try:
        return datetime.datetime.strptime((txt or '').strip(), '%H:%M').time()
    except ValueError:
        return None


@admin_requerido
def jornadas(request, pk=None):
    colegio = request.colegio
    jornada = get_object_or_404(Jornada, pk=pk, colegio=colegio) if pk else None
    cursos = Curso.objects.filter(colegio=colegio).order_by('orden')
    otras = {c.id: j.nombre for j in Jornada.objects.filter(colegio=colegio).exclude(pk=pk or 0)
             for c in j.cursos.all()}
    if request.method == 'POST':
        accion = request.POST.get('accion')
        if accion == 'eliminar' and jornada:
            jornada.delete()
            messages.success(request, 'Jornada eliminada.')
            return redirect('horarios:panel')
        nombre = (request.POST.get('nombre') or '').strip() or 'Jornada'
        dias = sorted(int(d) for d in request.POST.getlist('dias') if d.isdigit() and 1 <= int(d) <= 6) or [1, 2, 3, 4, 5]
        if jornada is None:
            jornada = Jornada.objects.create(colegio=colegio, nombre=nombre, dias=dias,
                                             orden=Jornada.objects.filter(colegio=colegio).count())
        else:
            jornada.nombre, jornada.dias = nombre, dias
            jornada.save()
        elegidos = [int(c) for c in request.POST.getlist('cursos') if c.isdigit()]
        jornada.cursos.set(cursos.filter(id__in=elegidos).exclude(id__in=otras.keys()))
        if accion == 'generar_franjas':
            ini = _hora(request.POST.get('g_inicio'))
            try:
                dur = int(request.POST.get('g_duracion') or 55)
                n = int(request.POST.get('g_clases') or 6)
                tras = [int(x) for x in (request.POST.get('g_descanso_tras') or '').replace(' ', '').split(',') if x.isdigit()]
                dur_desc = int(request.POST.get('g_descanso_min') or 30)
            except ValueError:
                ini = None
            if not ini or not (1 <= n <= 14) or not (20 <= dur <= 120):
                messages.error(request, 'Revise la hora de inicio, la duración y el número de clases.')
            else:
                if Sesion.objects.filter(franja__jornada=jornada).exists():
                    messages.error(request, 'Esta jornada ya tiene horarios con clases: cambie las horas una por una.')
                    return redirect('horarios:jornada', jornada.pk)
                jornada.franjas.all().delete()
                t = datetime.datetime.combine(datetime.date.today(), ini)
                orden = 0
                for k in range(1, n + 1):
                    Franja.objects.create(jornada=jornada, orden=orden, inicio=t.time(),
                                          fin=(t + datetime.timedelta(minutes=dur)).time(), etiqueta=f'{k}.ª hora')
                    t += datetime.timedelta(minutes=dur)
                    orden += 1
                    if k in tras and k < n:
                        Franja.objects.create(jornada=jornada, orden=orden, inicio=t.time(),
                                              fin=(t + datetime.timedelta(minutes=dur_desc)).time(), descanso=True,
                                              etiqueta='Descanso')
                        t += datetime.timedelta(minutes=dur_desc)
                        orden += 1
                messages.success(request, 'Horas de clase creadas.')
            return redirect('horarios:jornada', jornada.pk)
        # Editar franjas una por una
        for f in jornada.franjas.all():
            if request.POST.get(f'borrar_{f.id}'):
                if Sesion.objects.filter(franja=f).exists():
                    messages.error(request, f'La hora {f} tiene clases en algún horario: no se puede quitar.')
                    continue
                f.delete()
                continue
            i, fi = _hora(request.POST.get(f'ini_{f.id}')), _hora(request.POST.get(f'fin_{f.id}'))
            if i and fi and i < fi:
                f.inicio, f.fin = i, fi
                f.descanso = bool(request.POST.get(f'desc_{f.id}'))
                f.etiqueta = (request.POST.get(f'etq_{f.id}') or '')[:30]
                f.save()
        i, fi = _hora(request.POST.get('nueva_ini')), _hora(request.POST.get('nueva_fin'))
        if i and fi and i < fi:
            Franja.objects.create(jornada=jornada, inicio=i, fin=fi, descanso=bool(request.POST.get('nueva_desc')),
                                  etiqueta=(request.POST.get('nueva_etq') or '')[:30],
                                  orden=jornada.franjas.count())
        for k, f in enumerate(sorted(jornada.franjas.all(), key=lambda x: x.inicio)):
            if f.orden != k:
                f.orden = k
                f.save(update_fields=['orden'])
        messages.success(request, 'Jornada guardada.')
        return redirect('horarios:jornada', jornada.pk)
    return render(request, 'horarios/jornada.html', {
        'colegio': colegio, 'jornada': jornada, 'cursos': cursos, 'otras': otras, 'dias_todos': DIAS,
        'elegidos': {c.id for c in jornada.cursos.all()} if jornada else set(),
        'dias': jornada.dias if jornada else [1, 2, 3, 4, 5],
        'franjas': sorted(jornada.franjas.all(), key=lambda x: (x.orden, x.inicio)) if jornada else []})


# ---------------------------------------------------------------------------
# Generador (Premium): exportar datos, descargar la app, importar resultado
# ---------------------------------------------------------------------------
@admin_requerido
def exportar_datos(request):
    if not _premium(request):
        return HttpResponseForbidden('El generador de horarios es del plan Premium.')
    if not Jornada.objects.filter(colegio=request.colegio, cursos__isnull=False).exists():
        messages.error(request, 'Primero cree las jornadas, sus horas de clase y asígneles los cursos.')
        return redirect('horarios:panel')
    r = HttpResponse(intercambio.archivo_datos(request.colegio), content_type='application/json')
    r['Content-Disposition'] = f'attachment; filename="datos_horario_{request.colegio.slug}_{timezone.localdate():%Y%m%d}.mch"'
    return r


@admin_requerido
def descargar_app(request):
    if not _premium(request):
        return HttpResponseForbidden('El generador de horarios es del plan Premium.')
    app = AplicacionEscritorio.objects.first()
    if not app:
        messages.info(request, 'La aplicación todavía no está disponible para descargar.')
        return redirect('horarios:panel')
    return redirect(app.archivo.url)


@login_required
def subir_app(request):
    if not request.user.is_superuser:
        return HttpResponseForbidden('Solo el dueño de la plataforma.')
    if request.method == 'POST' and request.FILES.get('archivo'):
        AplicacionEscritorio.objects.create(archivo=request.FILES['archivo'],
                                            version=(request.POST.get('version') or '1.0')[:20],
                                            notas=(request.POST.get('notas') or '')[:250])
        messages.success(request, 'Aplicación subida: los colegios Premium ya la pueden descargar.')
        return redirect('horarios:subir_app')
    return render(request, 'horarios/subir_app.html', {'colegio': request.colegio,
                                                         'apps': AplicacionEscritorio.objects.all()[:10]})


@admin_requerido
@require_POST
def importar(request):
    archivo = request.FILES.get('archivo')
    if not archivo:
        messages.error(request, 'Escoja el archivo.')
        return redirect('horarios:panel')
    nombre = (archivo.name or '').lower()
    try:
        if nombre.endswith('.mchr') or nombre.endswith('.json'):
            if not _premium(request):
                return HttpResponseForbidden('El generador de horarios es del plan Premium.')
            h, avisos = intercambio.importar_resultado(archivo, request.colegio)
        elif nombre.endswith('.xlsx'):
            h, avisos = intercambio.importar_excel(archivo, request.colegio)
        else:
            raise nucleo.ArchivoInvalido('Suba el archivo del generador (.mchr) o un Excel (.xlsx).')
    except nucleo.ArchivoInvalido as e:
        messages.error(request, str(e))
        return redirect('horarios:panel')
    for a in avisos[:10]:
        messages.warning(request, a)
    choques = h.informe.get('choques', [])
    if choques:
        messages.warning(request, f'Se importó con {len(choques)} choque(s): revíselos antes de publicar.')
    else:
        messages.success(request, 'Horario importado sin choques. Revíselo y publíquelo.')
    return redirect('horarios:detalle', h.pk)


# ---------------------------------------------------------------------------
# Un horario
# ---------------------------------------------------------------------------
@admin_requerido
def detalle(request, pk):
    h = get_object_or_404(Horario, pk=pk, colegio=request.colegio)
    todas = list(cuadricula.sesiones(h))
    cursos = sorted({s.curso for s in todas}, key=lambda c: c.orden)
    docentes = sorted({s.asignacion.docente for s in todas if s.asignacion.docente_id},
                      key=lambda d: (d.user.last_name, d.user.first_name))
    ver = request.GET.get('ver') or 'curso'
    elegido = request.GET.get('id')
    tablas = []
    if ver == 'docente' and docentes:
        doc = next((d for d in docentes if str(d.id) == elegido), docentes[0])
        tablas = cuadricula.de_docente(h, doc, todas)
        elegido = doc.id
    elif cursos:
        cur = next((c for c in cursos if str(c.id) == elegido), cursos[0])
        t = cuadricula.de_curso(h, cur, todas)
        tablas = [t] if t else []
        elegido = cur.id
    actual = nucleo.Datos(intercambio.datos_del_colegio(request.colegio, con_firma=False))
    choques = nucleo.revisar(actual, [{'asignacion': s.asignacion_id, 'dia': s.dia, 'franja': s.franja_id} for s in todas])
    faltan = nucleo.horas_faltantes(actual, [{'asignacion': s.asignacion_id} for s in todas])
    return render(request, 'horarios/detalle.html', {
        'colegio': request.colegio, 'h': h, 'tablas': tablas, 'cursos': cursos, 'docentes': docentes, 'ver': ver,
        'elegido': elegido, 'choques': choques, 'n_sesiones': len(todas),
        'faltan': [(actual.nombre_materia(a['materia']), actual.nombre_curso(a['curso']), n) for a, n in faltan][:40],
        'n_faltan': len(faltan)})


@admin_requerido
@require_POST
def accion(request, pk):
    h = get_object_or_404(Horario, pk=pk, colegio=request.colegio)
    que = request.POST.get('que')
    if que == 'publicar':
        todas = list(cuadricula.sesiones(h))
        actual = nucleo.Datos(intercambio.datos_del_colegio(request.colegio, con_firma=False))
        choques = nucleo.revisar(actual, [{'asignacion': s.asignacion_id, 'dia': s.dia, 'franja': s.franja_id} for s in todas])
        if choques:
            messages.error(request, 'No se puede publicar un horario con choques. Corríjalos en el generador y vuelva a importarlo.')
            return redirect('horarios:detalle', h.pk)
        n = logica.publicar(h, request.build_absolute_uri(reverse('horarios:mi_horario')))
        messages.success(request, f'Horario publicado. Se avisó a {n} persona{"s" if n != 1 else ""}.')
    elif que == 'renombrar':
        h.nombre = (request.POST.get('nombre') or h.nombre)[:80]
        h.save(update_fields=['nombre'])
    elif que == 'archivar':
        h.estado = 'ARCHIVADO'
        h.save(update_fields=['estado'])
        messages.success(request, 'Horario archivado.')
        return redirect('horarios:panel')
    elif que == 'eliminar' and h.estado != 'PUBLICADO':
        h.delete()
        messages.success(request, 'Horario eliminado.')
        return redirect('horarios:panel')
    return redirect('horarios:detalle', h.pk)


def _pdf(request, contexto, nombre):
    try:
        from weasyprint import HTML
    except ImportError:
        return HttpResponse('La generación de PDF no está disponible en este servidor.', status=500)
    contexto.update({'colegio': request.colegio, 'hoy': timezone.localdate()})
    html = render_to_string('horarios/pdf.html', contexto, request=request)
    r = HttpResponse(HTML(string=html, base_url=request.build_absolute_uri('/')).write_pdf(), content_type='application/pdf')
    r['Content-Disposition'] = f'inline; filename="{nombre}.pdf"'
    return r


@admin_requerido
def pdf(request, pk):
    h = get_object_or_404(Horario, pk=pk, colegio=request.colegio)
    todas = list(cuadricula.sesiones(h))
    paginas = []
    if request.GET.get('ver') == 'docente':
        docentes = sorted({s.asignacion.docente for s in todas if s.asignacion.docente_id},
                          key=lambda d: (d.user.last_name, d.user.first_name))
        if request.GET.get('id'):
            docentes = [d for d in docentes if str(d.id) == request.GET['id']]
        for d in docentes:
            paginas.append({'titulo': d.user.get_full_name(), 'tablas': cuadricula.de_docente(h, d, todas)})
    else:
        cursos = sorted({s.curso for s in todas}, key=lambda c: c.orden)
        if request.GET.get('id'):
            cursos = [c for c in cursos if str(c.id) == request.GET['id']]
        for c in cursos:
            t = cuadricula.de_curso(h, c, todas)
            paginas.append({'titulo': f'Curso {c.nombre}', 'tablas': [t] if t else []})
    return _pdf(request, {'h': h, 'paginas': paginas}, f'Horario {h.nombre}')


# ---------------------------------------------------------------------------
# Mi horario (docente o estudiante)
# ---------------------------------------------------------------------------
@login_required
def mi_horario(request):
    colegio = request.colegio
    h = cuadricula.publicado(colegio)
    tablas, titulo = [], ''
    docente = Docente.objects.filter(user=request.user, colegio=colegio).first()
    if h and docente:
        tablas = cuadricula.de_docente(h, docente)
        titulo = 'Mi horario de clases'
    elif h:
        curso = cuadricula.curso_del_usuario(request.user, colegio)
        if curso:
            t = cuadricula.de_curso(h, curso)
            tablas = [t] if t else []
            titulo = f'Horario del curso {curso.nombre}'
    if request.GET.get('pdf') and h and tablas:
        return _pdf(request, {'h': h, 'paginas': [{'titulo': titulo, 'tablas': tablas}]}, 'Mi horario')
    return render(request, 'horarios/mi_horario.html', {'colegio': colegio, 'h': h, 'tablas': tablas,
                                                        'titulo': titulo or 'Horario de clases',
                                                        'es_admin': es_admin(request)})
