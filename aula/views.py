"""Vistas del aula virtual (las mismas para mcolegio y para Salón Digital)."""
from datetime import timedelta
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.files.base import ContentFile
from django.db.models import Q
from django.http import Http404, HttpResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.views.decorators.clickjacking import xframe_options_sameorigin
from django.views.decorators.http import require_POST

from . import logica
from .models import Actividad, Aula, Comentario, Criterio, Entrega, Instrumento, Material, Nivel, Publicacion, Tarea


# ---------------------------------------------------------------------------
# Ayudas
# ---------------------------------------------------------------------------
def _ctx(request, pk, docente=False):
    aula = get_object_or_404(Aula.objects.select_related(
        'asignacion__materia', 'asignacion__curso', 'asignacion__docente__user', 'grupo__propietario'), pk=pk)
    c = logica.contexto(request, aula)
    if c is None:
        if aula.es_salon:
            raise _Entrar(aula)
        raise _Prohibido('Esta aula es solo para el docente y los estudiantes de la clase.')
    if docente and not c.es_docente:
        raise _Prohibido('Esta acción es solo para el docente.')
    return c


class _Prohibido(Exception):
    pass


class _Entrar(Exception):
    def __init__(self, aula):
        self.aula = aula


def vista_aula(fn):
    """Convierte los «no puede» en la respuesta que corresponde."""
    def envoltura(request, *args, **kwargs):
        try:
            return fn(request, *args, **kwargs)
        except _Entrar as e:
            return redirect('aula:entrar', pk=e.aula.pk)
        except _Prohibido as e:
            if not request.user.is_authenticated and not request.session.get('salon_identidad'):
                from django.contrib.auth.views import redirect_to_login
                return redirect_to_login(request.get_full_path())
            return HttpResponseForbidden(str(e))
    envoltura.__name__ = fn.__name__
    envoltura.__doc__ = fn.__doc__
    return envoltura


def _render(request, c, plantilla, datos, pestana):
    if not c.es_docente:
        persona = c.estudiante or c.integrante
        logica.marcar_visto(c.aula, persona, pestana)
        datos['nuevos'] = logica.novedades(c.aula, persona)
    if c.aula.es_salon:
        datos['pe_activo'] = True
    else:
        from notas.modulos import esta_activo
        datos['pe_activo'] = esta_activo(c.aula.colegio, 'puntoexacto')
    datos.update({'c': c, 'aula': c.aula, 'base': c.base, 'pestana': pestana,
                  'hide_cuenta': c.aula.es_salon and not c.es_docente,
                  'colegio': getattr(request, 'colegio', None)})
    return render(request, plantilla, datos)


def _url(request, nombre, *args):
    return request.build_absolute_uri(reverse(nombre, args=args))


def _guardar_archivo(obj, campo, archivo):
    if archivo:
        getattr(obj, campo).save(archivo.name, archivo, save=False)
        obj.nombre_archivo = archivo.name[:150]


def _persona(aula, clave):
    """'e12' -> Estudiante 12 del curso; 'i7' -> Integrante 7 del grupo."""
    tipo, num = clave[:1], clave[1:]
    if not num.isdigit():
        raise Http404
    if tipo == 'e' and aula.asignacion_id:
        from notas.models import Estudiante
        return get_object_or_404(Estudiante, pk=int(num), curso=aula.asignacion.curso)
    if tipo == 'i' and aula.grupo_id:
        return get_object_or_404(aula.grupo.integrantes, pk=int(num))
    raise Http404


def _clave(persona):
    return logica.clave_de(persona)


def _no_es_para(c, obj):
    """Lo que el docente dejó solo para algunos: los demás no lo ven."""
    if not logica.para_c(obj, c):
        raise Http404


# ---------------------------------------------------------------------------
# Entrada
# ---------------------------------------------------------------------------
@login_required
def inicio(request):
    """Mis aulas: las asignaciones del docente o del estudiante; en Salón Digital, los grupos."""
    colegio = getattr(request, 'colegio', None)
    if colegio is None:
        cuenta = getattr(request.user, 'cuenta_salon', None)
        if cuenta is None:
            return redirect('salon_digital:landing')
        grupos = list(cuenta.grupos.filter(activo=True))
        return render(request, 'aula/inicio_salon.html', {'grupos': grupos, 'cuenta': cuenta,
                                                          'base': 'aula/base_salon.html'})
    from notas.models import AsignacionDocente
    from notas.permisos import es_admin
    asignaciones = AsignacionDocente.objects.filter(colegio=colegio).select_related(
        'materia', 'curso', 'docente__user').order_by('curso__grado', 'curso__nombre', 'materia__nombre')
    est = getattr(request.user, 'estudiante', None)
    if est is not None and est.colegio_id == colegio.id:
        asignaciones = asignaciones.filter(curso=est.curso)
        rol = 'estudiante'
    elif es_admin(request):
        rol = 'admin'
    else:
        asignaciones = asignaciones.filter(docente__user=request.user)
        rol = 'docente'
    asignaciones = list(asignaciones)
    aulas = {a.asignacion_id: a for a in Aula.objects.filter(asignacion__in=asignaciones)}
    pendientes, nuevos = {}, {}
    if rol == 'estudiante':
        from .models import Visto
        clave = logica.clave_de(est)
        vistos = {v.aula_id: v.secciones for v in Visto.objects.filter(aula__in=aulas.values(), estudiante=est)}
        for a in aulas.values():
            hechas = set(Entrega.objects.filter(tarea__aula=a, estudiante=est).values_list('tarea_id', flat=True))
            pendientes[a.asignacion_id] = sum(1 for t in a.tareas.filter(publicada=True)
                                              if t.id not in hechas and logica.es_para(t, clave))
            nuevos[a.asignacion_id] = sum(logica.novedades(a, est, vistos.get(a.id, {})).values())
    for asig in asignaciones:
        asig.aula_virtual = aulas.get(asig.id)
        asig.pendientes = pendientes.get(asig.id, 0)
        asig.nuevos = nuevos.get(asig.id, 0)
    return render(request, 'aula/inicio.html', {'asignaciones': asignaciones, 'rol': rol, 'colegio': colegio,
                                                'base': 'notas/base.html'})


@login_required
@vista_aula
def por_asignacion(request, asignacion_id):
    from notas.models import AsignacionDocente
    asig = get_object_or_404(AsignacionDocente, pk=asignacion_id, colegio=getattr(request, 'colegio', None))
    aula = Aula.objects.filter(asignacion=asig).first() or Aula(asignacion=asig, colegio=asig.colegio)
    if logica.contexto(request, aula) is None:
        raise _Prohibido('Esta aula es solo para el docente y los estudiantes de la clase.')
    aula = logica.aula_de_asignacion(asig)
    return redirect('aula:muro', pk=aula.pk)


@login_required
def por_grupo(request, grupo_id):
    from salon_digital.models import Grupo
    grupo = get_object_or_404(Grupo, pk=grupo_id, propietario__usuario=request.user)
    return redirect('aula:muro', pk=logica.aula_de_grupo(grupo).pk)


def entrar(request, pk):
    """Salón Digital: el estudiante escribe el código del grupo y escoge su nombre."""
    aula = get_object_or_404(Aula, pk=pk, grupo__isnull=False)
    if logica.contexto(request, aula) is not None:
        return redirect('aula:muro', pk=aula.pk)
    grupo = aula.grupo
    codigo = (request.POST.get('codigo') or request.GET.get('codigo') or '').strip().upper()
    valido = codigo == grupo.codigo and grupo.activo
    error = ''
    if codigo and not valido:
        error = 'Ese código no corresponde a esta clase.'
    if request.method == 'POST' and valido and request.POST.get('integrante'):
        integrante = grupo.integrantes.filter(pk=request.POST['integrante'], activo=True).first()
        if integrante:
            from salon_digital import identidad
            identidad.guardar(request, integrante)
            return redirect('aula:muro', pk=aula.pk)
        error = 'No encontramos ese nombre en la clase.'
    return render(request, 'aula/entrar.html', {
        'aula': aula, 'codigo': codigo, 'valido': valido, 'error': error, 'base': 'aula/base_salon.html',
        'hide_cuenta': True,
        'integrantes': grupo.integrantes.filter(activo=True) if valido else [],
    })


def salir(request, pk):
    from salon_digital import identidad
    identidad.olvidar(request)
    return redirect('aula:entrar', pk=pk)


# ---------------------------------------------------------------------------
# Muro
# ---------------------------------------------------------------------------
@vista_aula
def muro(request, pk):
    c = _ctx(request, pk)
    aula = c.aula
    if request.method == 'POST':
        if not c.es_docente:
            raise _Prohibido('Solo el docente publica en el muro.')
        texto = (request.POST.get('texto') or '').strip()
        enlace = (request.POST.get('enlace') or '').strip()
        archivo = request.FILES.get('archivo')
        if not (texto or enlace or archivo):
            messages.warning(request, 'Escriba algo o adjunte un archivo para publicar.')
        elif logica.muy_grande(archivo):
            messages.error(request, f'El archivo pasa de {logica.MAX_ARCHIVO_MB} MB. Súbalo a Drive y pegue el enlace.')
        else:
            pub = Publicacion(aula=aula, autor=request.user, texto=texto[:5000], enlace=enlace[:200])
            _guardar_archivo(pub, 'archivo', archivo)
            pub.save()
            logica.avisar_estudiantes(aula, f'{aula.titulo}: nueva publicación en el muro',
                                      _url(request, 'aula:muro', aula.pk))
            messages.success(request, 'Publicado en el muro.')
        return redirect('aula:muro', pk=aula.pk)

    pubs = list(aula.publicaciones.select_related('autor', 'tarea').prefetch_related('comentarios'))
    if not c.es_docente:
        pubs = [p for p in pubs if p.tarea is None or logica.para_c(p.tarea, c)]
    for p in pubs:
        p.visibles = [k for k in p.comentarios.all() if c.es_docente or not k.oculto]
    proximas = [t for t in aula.tareas.filter(publicada=True, fecha_limite__gte=timezone.now())
                .order_by('fecha_limite') if logica.para_c(t, c)][:4]
    from .models import SesionVivo
    vivos = list(SesionVivo.objects.filter(cuestionario__aula=aula, creada__gte=timezone.now() - timedelta(hours=3))
                 .exclude(estado='fin').select_related('cuestionario'))
    return _render(request, c, 'aula/muro.html', {
        'publicaciones': pubs, 'proximas': proximas, 'horario': logica.horario_de(aula), 'vivos': vivos}, 'muro')


@require_POST
@vista_aula
def comentar(request, pk, pub_id):
    c = _ctx(request, pk)
    pub = get_object_or_404(Publicacion, pk=pub_id, aula=c.aula)
    if not c.es_docente and not c.aula.comentarios_activos:
        messages.warning(request, 'El docente apagó los comentarios.')
        return redirect('aula:muro', pk=pk)
    texto = (request.POST.get('texto') or '').strip()[:1000]
    if texto:
        Comentario.objects.create(publicacion=pub, texto=texto, nombre=c.nombre[:150], usuario=c.usuario,
                                  integrante=c.integrante)
    return redirect(reverse('aula:muro', args=[pk]) + f'#pub-{pub.pk}')


@require_POST
@vista_aula
def moderar(request, pk, pub_id):
    c = _ctx(request, pk, docente=True)
    pub = get_object_or_404(Publicacion, pk=pub_id, aula=c.aula)
    accion = request.POST.get('accion')
    if accion == 'eliminar':
        pub.delete()
        messages.info(request, 'Publicación eliminada.')
    elif accion == 'fijar':
        pub.fijada = not pub.fijada
        pub.save(update_fields=['fijada'])
    elif accion == 'ocultar':
        com = get_object_or_404(Comentario, pk=request.POST.get('comentario'), publicacion=pub)
        com.oculto = not com.oculto
        com.save(update_fields=['oculto'])
    return redirect(reverse('aula:muro', args=[pk]) + f'#pub-{pub.pk}')


# ---------------------------------------------------------------------------
# Clase en vivo y ajustes
# ---------------------------------------------------------------------------
@vista_aula
def clase(request, pk):
    c = _ctx(request, pk)
    aula = c.aula
    if request.method == 'POST':
        if not c.es_docente:
            raise _Prohibido('Solo el docente cambia la clase en vivo.')
        enlace = (request.POST.get('enlace_clase') or '').strip()
        if enlace and not enlace.startswith(('http://', 'https://')):
            enlace = 'https://' + enlace
        aula.enlace_clase = enlace[:200]
        aula.nota_clase = (request.POST.get('nota_clase') or '').strip()[:200]
        aula.bienvenida = (request.POST.get('bienvenida') or '').strip()[:200]
        aula.comentarios_activos = request.POST.get('comentarios_activos') == 'on'
        aula.save()
        if request.POST.get('avisar') == 'on' and aula.enlace_clase:
            logica.avisar_estudiantes(aula, f'{aula.titulo}: la clase en vivo va a empezar',
                                      _url(request, 'aula:clase', aula.pk))
            messages.success(request, 'Guardado. Se avisó a los estudiantes.')
        else:
            messages.success(request, 'Guardado.')
        return redirect('aula:clase', pk=aula.pk)
    return _render(request, c, 'aula/clase.html', {'horario': logica.horario_de(aula)}, 'clase')


# ---------------------------------------------------------------------------
# Material
# ---------------------------------------------------------------------------
@vista_aula
def material(request, pk):
    c = _ctx(request, pk)
    aula = c.aula
    if request.method == 'POST':
        if not c.es_docente:
            raise _Prohibido('Solo el docente agrega material.')
        titulo = (request.POST.get('titulo') or '').strip()[:150]
        enlace = (request.POST.get('enlace') or '').strip()[:200]
        archivo = request.FILES.get('archivo')
        para, error_para = logica.leer_para(request, aula)
        if not titulo or not (enlace or archivo):
            messages.warning(request, 'Escriba el título y adjunte un archivo o pegue un enlace.')
        elif error_para:
            messages.warning(request, error_para)
        elif logica.muy_grande(archivo):
            messages.error(request, f'El archivo pasa de {logica.MAX_ARCHIVO_MB} MB. Súbalo a Drive o YouTube y pegue el enlace.')
        else:
            m = Material(aula=aula, titulo=titulo, unidad=(request.POST.get('unidad') or '').strip()[:80],
                         descripcion=(request.POST.get('descripcion') or '').strip()[:300], enlace=enlace,
                         para=para)
            m.tipo = 'archivo' if archivo else 'enlace'
            _guardar_archivo(m, 'archivo', archivo)
            if not archivo and m.youtube_id:
                m.tipo = 'video'
            m.save()
            if para:
                logica.avisar_estudiantes(aula, f'{aula.titulo}: el docente le dejó material «{m.titulo}»',
                                          _url(request, 'aula:material', aula.pk), para)
            messages.success(request, 'Material agregado.' + (f' Solo lo ven {len(para)} estudiante(s).' if para else ''))
        return redirect('aula:material', pk=aula.pk)
    grupos = {}
    materiales = [m for m in aula.materiales.all() if logica.para_c(m, c)]
    nombres = {p['clave']: p['nombre'] for p in logica.opciones_para(aula)} if c.es_docente else {}
    for m in materiales:
        m.para_nombres = [nombres.get(k, '') for k in m.para] if c.es_docente else []
        grupos.setdefault(m.unidad or 'General', []).append(m)
    unidades = sorted({m.unidad for m in materiales if m.unidad})
    datos = {'grupos': grupos, 'unidades': unidades}
    if c.es_docente:
        datos['opciones_para'] = logica.opciones_para(aula)
    return _render(request, c, 'aula/material.html', datos, 'material')


@require_POST
@vista_aula
def material_eliminar(request, pk, mid):
    c = _ctx(request, pk, docente=True)
    get_object_or_404(Material, pk=mid, aula=c.aula).delete()
    messages.info(request, 'Material eliminado.')
    return redirect('aula:material', pk=pk)


@xframe_options_sameorigin
@vista_aula
def archivo(request, pk, tipo, oid):
    """Abre un archivo del aula (enlace firmado) solo para quien es de la clase."""
    c = _ctx(request, pk)
    modelos = {'pub': Publicacion, 'mat': Material, 'tarea': Tarea, 'act': Actividad}
    if tipo in modelos:
        obj = get_object_or_404(modelos[tipo], pk=oid, aula=c.aula)
        if tipo != 'pub':
            _no_es_para(c, obj)
        elif obj.tarea_id:
            _no_es_para(c, obj.tarea)
    elif tipo == 'entrega':
        obj = get_object_or_404(Entrega, pk=oid, tarea__aula=c.aula)
        if not c.es_docente and not (obj.estudiante_id == getattr(c.estudiante, 'id', -1)
                                     or obj.integrante_id == getattr(c.integrante, 'id', -1)):
            raise _Prohibido('Ese archivo es de otro estudiante.')
    else:
        raise Http404
    if not obj.archivo:
        raise Http404
    return redirect(obj.archivo.url)


# ---------------------------------------------------------------------------
# Tareas
# ---------------------------------------------------------------------------
@vista_aula
def tareas(request, pk):
    c = _ctx(request, pk)
    aula = c.aula
    lista = list(aula.tareas.select_related('instrumento', 'periodo'))
    if not c.es_docente:
        lista = [t for t in lista if t.publicada and logica.para_c(t, c)]
        persona = c.estudiante or c.integrante
        mias = {e.tarea_id: e for e in Entrega.objects.filter(tarea__in=lista, **logica.filtro_persona(persona))}
        for t in lista:
            t.mia = mias.get(t.id)
    else:
        todos = logica.estudiantes(aula)
        for t in lista:
            t.n_entregas = t.entregas.exclude(entregada__isnull=True).count()
            t.n_calificadas = t.entregas.filter(nota__isnull=False).count()
            t.total = len(logica.personas_de(t, aula, todos))
    return _render(request, c, 'aula/tareas.html', {'tareas': lista}, 'tareas')


def _instrumentos_disponibles(request, aula):
    q = Q(propietario=request.user)
    if aula.colegio_id:
        q |= Q(colegio=aula.colegio, compartido=True)
    return Instrumento.objects.filter(q).order_by('nombre')


@vista_aula
def tarea_form(request, pk, tid=None):
    c = _ctx(request, pk, docente=True)
    aula = c.aula
    tarea = get_object_or_404(Tarea, pk=tid, aula=aula) if tid else Tarea(aula=aula)
    instrumentos = _instrumentos_disponibles(request, aula)
    periodos = []
    if aula.colegio_id:
        from notas.models import PeriodoAcademico
        periodos = list(PeriodoAcademico.objects.filter(colegio=aula.colegio).order_by('-ano_lectivo', 'orden')[:8])
    componentes = logica.componentes_de(aula)
    if request.method == 'POST':
        nuevo = tarea.pk is None
        tarea.titulo = (request.POST.get('titulo') or '').strip()[:60]
        tarea.instrucciones = (request.POST.get('instrucciones') or '').strip()
        tarea.enlace = (request.POST.get('enlace') or '').strip()[:200]
        fecha = request.POST.get('fecha_limite') or ''
        dt = parse_datetime(fecha) if fecha else None
        tarea.fecha_limite = timezone.make_aware(dt) if dt and timezone.is_naive(dt) else dt
        tarea.acepta_tardias = request.POST.get('acepta_tardias') == 'on'
        inst_id = request.POST.get('instrumento') or ''
        tarea.instrumento = instrumentos.filter(pk=inst_id).first() if inst_id.isdigit() else None
        per_id = request.POST.get('periodo') or ''
        tarea.periodo = next((p for p in periodos if str(p.id) == per_id), None)
        comp = request.POST.get('componente') or ''
        tarea.componente = comp if comp in {k for k, _ in componentes} else ''
        tarea.publicada = request.POST.get('publicada') == 'on'
        tarea.para, error_para = logica.leer_para(request, aula)
        archivo = request.FILES.get('archivo')
        if not tarea.titulo:
            messages.error(request, 'La tarea necesita un título.')
        elif error_para:
            messages.error(request, error_para)
        elif logica.muy_grande(archivo):
            messages.error(request, f'El archivo pasa de {logica.MAX_ARCHIVO_MB} MB.')
        else:
            _guardar_archivo(tarea, 'archivo', archivo)
            tarea.save()
            if nuevo and tarea.publicada:
                limite = f' · entrega: {timezone.localtime(tarea.fecha_limite):%d/%m %I:%M %p}' if tarea.fecha_limite else ''
                Publicacion.objects.create(aula=aula, autor=request.user, tarea=tarea,
                                           texto=f'Nueva tarea: {tarea.titulo}{limite}')
                logica.avisar_estudiantes(aula, f'{aula.titulo}: nueva tarea «{tarea.titulo}»',
                                          _url(request, 'aula:tarea', aula.pk, tarea.pk), tarea.para)
            messages.success(request, 'Tarea guardada.')
            return redirect('aula:tarea', pk=aula.pk, tid=tarea.pk)
    activo = next((p for p in periodos if p.esta_activo), periodos[0] if periodos else None)
    return _render(request, c, 'aula/tarea_form.html', {
        'tarea': tarea, 'instrumentos': instrumentos, 'periodos': periodos, 'componentes': componentes,
        'periodo_sugerido': tarea.periodo or activo, 'opciones_para': logica.opciones_para(aula),
        'para_actual': tarea.para or request.GET.getlist('para')}, 'tareas')


@require_POST
@vista_aula
def tarea_eliminar(request, pk, tid):
    c = _ctx(request, pk, docente=True)
    get_object_or_404(Tarea, pk=tid, aula=c.aula).delete()
    messages.info(request, 'Tarea eliminada.')
    return redirect('aula:tareas', pk=pk)


@vista_aula
def tarea(request, pk, tid):
    c = _ctx(request, pk)
    aula = c.aula
    t = get_object_or_404(Tarea.objects.select_related('instrumento', 'periodo'), pk=tid, aula=aula)
    _no_es_para(c, t)
    datos = {'t': t, 'para_nombres': logica.nombres_para(t, aula) if c.es_docente else []}
    if c.es_docente:
        entregas = {}
        for e in t.entregas.all():
            entregas[e.integrante_id if aula.es_salon else e.estudiante_id] = e
        filas = []
        for p in logica.personas_de(t, aula):
            e = entregas.get(p.id)
            filas.append({'persona': p, 'nombre': logica.nombre_de(p), 'clave': _clave(p), 'e': e,
                          'desempeno': logica.desempeno(aula, e.nota) if e and e.nota is not None else ''})
        datos.update({'filas': filas, 'n_entregas': sum(1 for f in filas if f['e'] and f['e'].entregada),
                      'n_calificadas': sum(1 for f in filas if f['e'] and f['e'].nota is not None),
                      'puede_planilla': bool(aula.asignacion_id)})
    else:
        persona = c.estudiante or c.integrante
        e = logica.entrega_de(t, persona)
        datos.update({'e': e, 'detalle': _detalle_calificacion(t, e) if e and e.nota is not None else None,
                      'desempeno': logica.desempeno(aula, e.nota) if e and e.nota is not None else ''})
    if t.instrumento_id:
        datos['inst'] = t.instrumento
        datos['niveles'] = list(t.instrumento.niveles.all())
        datos['criterios'] = list(t.instrumento.criterios.all())
        for cr in datos['criterios']:
            cr.celdas = [{'nivel': n, 'texto': cr.descriptor(n)} for n in datos['niveles']]
    return _render(request, c, 'aula/tarea.html', datos, 'tareas')


def _detalle_calificacion(t, e):
    """Lo que el estudiante ve de su calificación: qué nivel le dieron en cada criterio."""
    if not t.instrumento_id:
        return None
    inst = t.instrumento
    niveles = {n.id: n for n in inst.niveles.all()}
    salida = []
    for cr in inst.criterios.all():
        v = (e.seleccion or {}).get(str(cr.id))
        if inst.tipo == 'lista':
            salida.append({'criterio': cr.nombre, 'nivel': 'Sí' if v is True else ('No' if v is False else '—'),
                           'ok': v is True})
        else:
            n = niveles.get(logica._entero(v))
            salida.append({'criterio': cr.nombre, 'nivel': n.nombre if n else '—',
                           'descriptor': cr.descriptor(n) if n else '', 'ok': True})
    return salida


@require_POST
@vista_aula
def entregar(request, pk, tid):
    c = _ctx(request, pk)
    if c.es_docente:
        raise _Prohibido('Las entregas son de los estudiantes.')
    t = get_object_or_404(Tarea, pk=tid, aula=c.aula, publicada=True)
    _no_es_para(c, t)
    persona = c.estudiante or c.integrante
    e = logica.entrega_de(t, persona) or Entrega(tarea=t, **logica.filtro_persona(persona))
    if e.pk and e.estado == 'calificada':
        messages.warning(request, 'Esta tarea ya fue calificada.')
        return redirect('aula:tarea', pk=pk, tid=tid)
    if not t.recibe:
        messages.error(request, 'La fecha de entrega ya pasó y el docente no recibe entregas tardías.')
        return redirect('aula:tarea', pk=pk, tid=tid)
    fotos = [f for f in request.FILES.getlist('fotos') if f]
    archivo = request.FILES.get('archivo')
    texto = (request.POST.get('texto') or '').strip()
    if not (fotos or archivo or texto):
        messages.warning(request, 'Tome las fotos, adjunte un archivo o escriba su respuesta.')
        return redirect('aula:tarea', pk=pk, tid=tid)
    if len(fotos) > logica.MAX_FOTOS:
        messages.error(request, f'Máximo {logica.MAX_FOTOS} fotos por entrega.')
        return redirect('aula:tarea', pk=pk, tid=tid)
    if logica.muy_grande(archivo) or any(f.size > 15 * 1024 * 1024 for f in fotos):
        messages.error(request, 'Algún archivo es demasiado grande.')
        return redirect('aula:tarea', pk=pk, tid=tid)
    if fotos:
        imagenes = [f for f in fotos if logica.es_imagen(f.name)]
        if len(imagenes) != len(fotos):
            messages.error(request, 'En «fotos» solo van imágenes (JPG o PNG).')
            return redirect('aula:tarea', pk=pk, tid=tid)
        try:
            pdf = logica.imagenes_a_pdf(imagenes)
        except Exception:
            messages.error(request, 'No se pudieron leer las fotos. Tómelas de nuevo en JPG.')
            return redirect('aula:tarea', pk=pk, tid=tid)
        nombre = f'{t.titulo[:30]} - {c.nombre[:40]}.pdf'
        e.archivo.save(nombre, ContentFile(pdf), save=False)
        e.nombre_archivo = nombre
    elif archivo:
        _guardar_archivo(e, 'archivo', archivo)
    if texto:
        e.texto = texto[:10000]
    e.entregada = timezone.now()
    e.tardia = t.vencida
    e.estado = 'entregada'
    e.save()
    messages.success(request, '¡Tarea entregada!' + (' (después de la fecha)' if e.tardia else ''))
    return redirect('aula:tarea', pk=pk, tid=tid)


@vista_aula
def calificar(request, pk, tid, clave):
    c = _ctx(request, pk, docente=True)
    aula = c.aula
    t = get_object_or_404(Tarea.objects.select_related('instrumento'), pk=tid, aula=aula)
    persona = _persona(aula, clave)
    e = logica.entrega_de(t, persona) or Entrega(tarea=t, **logica.filtro_persona(persona))
    minima, maxima = logica.rango(aula)
    if request.method == 'POST':
        accion = request.POST.get('accion', 'calificar')
        e.comentario = (request.POST.get('comentario') or '').strip()[:3000]
        if accion == 'devolver':
            e.estado = 'devuelta'
            e.save()
            messages.info(request, f'Devuelta a {logica.nombre_de(persona)} para corregir.')
        else:
            if t.instrumento_id:
                inst = t.instrumento
                sel = {}
                for cr in inst.criterios.all():
                    v = request.POST.get(f'c{cr.id}')
                    if inst.tipo == 'lista':
                        if v in ('si', 'no'):
                            sel[str(cr.id)] = v == 'si'
                    elif v and v.isdigit():
                        sel[str(cr.id)] = int(v)
                nota, completa = logica.calcular_nota(inst, sel, minima, maxima)
                e.seleccion = sel
                if not completa:
                    messages.warning(request, 'Marque un nivel en todos los criterios.')
                    e.save() if e.pk else None
                    return redirect('aula:calificar', pk=pk, tid=tid, clave=clave)
            else:
                from notas.planillas.guardar import a_decimal
                nota = a_decimal(request.POST.get('nota'))
                if nota is None or not (minima <= nota <= maxima):
                    messages.error(request, f'Escriba una nota de {minima} a {maxima}.')
                    return redirect('aula:calificar', pk=pk, tid=tid, clave=clave)
            e.nota = nota
            e.estado = 'calificada'
            e.calificada = timezone.now()
            e.save()
            messages.success(request, f'{logica.nombre_de(persona)}: {nota}')
        siguiente = request.POST.get('siguiente')
        if siguiente:
            return redirect('aula:calificar', pk=pk, tid=tid, clave=siguiente)
        return redirect('aula:tarea', pk=pk, tid=tid)

    personas = logica.estudiantes(aula)
    claves = [_clave(p) for p in personas]
    i = claves.index(clave) if clave in claves else 0
    datos = {'t': t, 'e': e, 'persona': persona, 'nombre': logica.nombre_de(persona), 'clave': clave,
             'anterior': claves[i - 1] if i > 0 else '', 'siguiente': claves[i + 1] if i + 1 < len(claves) else '',
             'posicion': i + 1, 'total': len(claves), 'minima': minima, 'maxima': maxima,
             'n_entregas': t.entregas.exclude(entregada__isnull=True).count()}
    if t.instrumento_id:
        datos['inst'] = t.instrumento
        datos['niveles'] = list(t.instrumento.niveles.all())
        datos['criterios'] = list(t.instrumento.criterios.all())
        for cr in datos['criterios']:
            cr.elegido = (e.seleccion or {}).get(str(cr.id))
            cr.celdas = [{'nivel': n, 'texto': cr.descriptor(n)} for n in datos['niveles']]
        datos['valores'] = {str(n.id): str(n.valor) for n in datos['niveles']}
        datos['pesos'] = {str(cr.id): str(cr.peso) for cr in datos['criterios']}
    return _render(request, c, 'aula/calificar.html', datos, 'tareas')


@vista_aula
def grilla(request, pk, tid):
    """Calificar a todo el curso en una tabla (exposiciones, trabajo en clase)."""
    c = _ctx(request, pk, docente=True)
    aula = c.aula
    t = get_object_or_404(Tarea.objects.select_related('instrumento'), pk=tid, aula=aula)
    if not t.instrumento_id:
        messages.info(request, 'La calificación en grilla necesita una rúbrica o lista de chequeo en la tarea.')
        return redirect('aula:tarea', pk=pk, tid=tid)
    inst = t.instrumento
    criterios = list(inst.criterios.all())
    niveles = list(inst.niveles.all())
    personas = logica.personas_de(t, aula)
    minima, maxima = logica.rango(aula)
    if request.method == 'POST':
        n = 0
        for p in personas:
            k = _clave(p)
            sel = {}
            for cr in criterios:
                v = request.POST.get(f'{k}-{cr.id}')
                if inst.tipo == 'lista':
                    if v in ('si', 'no'):
                        sel[str(cr.id)] = v == 'si'
                elif v and v.isdigit():
                    sel[str(cr.id)] = int(v)
            if not sel:
                continue
            nota, completa = logica.calcular_nota(inst, sel, minima, maxima)
            e = logica.entrega_de(t, p) or Entrega(tarea=t, **logica.filtro_persona(p))
            e.seleccion = sel
            if completa:
                e.nota, e.estado, e.calificada = nota, 'calificada', timezone.now()
                n += 1
            e.save()
        messages.success(request, f'Se calificaron {n} estudiante(s).')
        return redirect('aula:tarea', pk=pk, tid=tid)
    filas = []
    existentes = {(e.integrante_id if aula.es_salon else e.estudiante_id): e for e in t.entregas.all()}
    for p in personas:
        e = existentes.get(p.id)
        sel = (e.seleccion if e else {}) or {}
        filas.append({'clave': _clave(p), 'nombre': logica.nombre_de(p), 'nota': e.nota if e else None,
                      'celdas': [{'criterio': cr, 'valor': sel.get(str(cr.id))} for cr in criterios]})
    return _render(request, c, 'aula/grilla.html', {'t': t, 'inst': inst, 'criterios': criterios,
                                                    'niveles': niveles, 'filas': filas}, 'tareas')


@require_POST
@vista_aula
def pasar_planilla(request, pk, tid):
    c = _ctx(request, pk, docente=True)
    t = get_object_or_404(Tarea, pk=tid, aula=c.aula)
    pasadas, error = logica.pasar_a_planilla(t)
    if error:
        messages.error(request, error)
    else:
        messages.success(request, f'Se pasaron {pasadas} nota(s) a la planilla, en la columna «{t.titulo}» '
                                  f'de {dict(logica.componentes_de(c.aula)).get(t.componente, t.componente)}.')
    return redirect('aula:tarea', pk=pk, tid=tid)


@vista_aula
def calificaciones(request, pk):
    c = _ctx(request, pk, docente=True)
    if request.GET.get('formato') == 'excel':
        r = HttpResponse(logica.excel_calificaciones(c.aula),
                         content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        r['Content-Disposition'] = f'attachment; filename="Calificaciones {c.aula.titulo}.xlsx"'
        return r
    aula = c.aula
    if request.method == 'POST':
        if not aula.es_salon:
            raise _Prohibido('En el colegio las notas se pasan a la planilla oficial desde cada tarea o examen.')
        from .models import ColumnaManual
        accion = request.POST.get('accion', 'guardar')
        if accion == 'agregar':
            titulo = (request.POST.get('titulo') or '').strip()[:60]
            if titulo:
                ColumnaManual.objects.create(aula=aula, titulo=titulo, orden=aula.columnas_manuales.count())
                messages.success(request, f'Columna «{titulo}» agregada: escriba las notas y guarde.')
        elif accion == 'eliminar':
            col = get_object_or_404(ColumnaManual, pk=request.POST.get('columna'), aula=aula)
            col.delete()
            messages.info(request, f'Columna «{col.titulo}» eliminada.')
        elif accion == 'renombrar':
            col = get_object_or_404(ColumnaManual, pk=request.POST.get('columna'), aula=aula)
            titulo = (request.POST.get('titulo') or '').strip()[:60]
            if titulo:
                col.titulo = titulo
                col.save(update_fields=['titulo'])
        else:
            errores = logica.guardar_planilla(aula, request.POST)
            for e in errores[:8]:
                messages.error(request, e)
            if not errores:
                messages.success(request, 'Planilla guardada.')
        return redirect('aula:calificaciones', pk=pk)
    return _render(request, c, 'aula/calificaciones.html', logica.tabla_calificaciones(aula), 'calificaciones')


# ---------------------------------------------------------------------------
# Instrumentos de evaluación
# ---------------------------------------------------------------------------
def _colegio_y_base(request):
    colegio = getattr(request, 'colegio', None)
    return colegio, ('notas/base.html' if colegio else 'aula/base_salon.html')


def _puede_crear(request):
    colegio = getattr(request, 'colegio', None)
    if colegio is not None:
        from notas.models import Docente
        from notas.permisos import es_admin
        return es_admin(request) or Docente.objects.filter(user=request.user, colegio=colegio).exists()
    return hasattr(request.user, 'cuenta_salon')


@login_required
def instrumentos(request):
    if not _puede_crear(request):
        return HttpResponseForbidden('Los instrumentos de evaluación son para los docentes.')
    colegio, base = _colegio_y_base(request)
    if request.method == 'POST':
        accion = request.POST.get('accion')
        if accion == 'plantilla' and request.POST.get('plantilla') in logica.PLANTILLAS:
            inst = logica.desde_plantilla(request.user, colegio, request.POST['plantilla'])
            messages.success(request, 'Listo: ajuste los criterios y los descriptores a su gusto.')
            return redirect('aula:instrumento', iid=inst.pk)
        if accion == 'blanco':
            tipo = 'lista' if request.POST.get('tipo') == 'lista' else 'rubrica'
            inst = logica.crear_instrumento(request.user, colegio, 'Nuevo instrumento', tipo,
                                            [('Criterio 1', 1), ('Criterio 2', 1), ('Criterio 3', 1)])
            return redirect('aula:instrumento', iid=inst.pk)
        if accion == 'importar':
            try:
                archivo = request.FILES.get('archivo')
                filas = logica.leer_tabla(archivo=archivo) if archivo else \
                    logica.leer_tabla(texto=request.POST.get('tabla'))
                criterios, niveles, descriptores, tipo = logica.interpretar_tabla(filas, colegio, request.user)
            except Exception as ex:
                messages.error(request, f'No se pudo leer la tabla: {ex}')
                return redirect('aula:instrumentos')
            nombre = (request.POST.get('nombre') or '').strip() or 'Rúbrica importada'
            inst = logica.crear_instrumento(request.user, colegio, nombre, tipo, criterios, niveles, descriptores)
            messages.success(request, f'Se importaron {len(criterios)} criterio(s). Revise los valores de cada nivel.')
            return redirect('aula:instrumento', iid=inst.pk)
    mios = Instrumento.objects.filter(propietario=request.user).prefetch_related('criterios')
    compartidos = Instrumento.objects.filter(colegio=colegio, compartido=True).exclude(
        propietario=request.user) if colegio else Instrumento.objects.none()
    return render(request, 'aula/instrumentos.html', {
        'mios': mios, 'compartidos': compartidos, 'plantillas': logica.PLANTILLAS, 'base': base,
        'colegio': colegio})


def _instrumento_editable(request, iid):
    inst = get_object_or_404(Instrumento, pk=iid)
    if inst.propietario_id != request.user.id:
        raise Http404
    return inst


@login_required
def instrumento(request, iid):
    inst = get_object_or_404(Instrumento, pk=iid)
    colegio, base = _colegio_y_base(request)
    propio = inst.propietario_id == request.user.id
    if not propio and not (inst.compartido and colegio and inst.colegio_id == colegio.id):
        raise Http404
    usado = Entrega.objects.filter(tarea__instrumento=inst, nota__isnull=False).exists()
    if request.method == 'POST':
        if not propio:
            return HttpResponseForbidden('Solo quien lo creó puede cambiarlo; duplíquelo para tener el suyo.')
        error = _guardar_instrumento(request, inst, usado)
        if error:
            messages.error(request, error)
        else:
            messages.success(request, 'Instrumento guardado.')
        return redirect('aula:instrumento', iid=inst.pk)
    niveles = list(inst.niveles.all())
    criterios = list(inst.criterios.all())
    for cr in criterios:
        cr.textos = [cr.descriptor(n) for n in niveles]
    return render(request, 'aula/instrumento.html', {
        'inst': inst, 'niveles': niveles, 'criterios': criterios, 'propio': propio, 'usado': usado,
        'base': base, 'colegio': colegio, 'imprimir': request.GET.get('imprimir') == '1'})


def _guardar_instrumento(request, inst, usado):
    from notas.planillas.guardar import a_decimal
    P = request.POST
    inst.nombre = (P.get('nombre') or inst.nombre).strip()[:120]
    inst.descripcion = (P.get('descripcion') or '').strip()[:300]
    inst.compartido = P.get('compartido') == 'on'
    nombres_n, valores_n = P.getlist('nivel_nombre'), P.getlist('nivel_valor')
    nombres_c, pesos_c = P.getlist('crit_nombre'), P.getlist('crit_peso')
    filas_n = [(n.strip()[:40], a_decimal(v)) for n, v in zip(nombres_n, valores_n) if n.strip()]
    filas_c = [(i, n.strip()[:200], a_decimal(p) or Decimal('1')) for i, (n, p) in enumerate(zip(nombres_c, pesos_c))
               if n.strip()]
    if inst.tipo == 'rubrica':
        if len(filas_n) < 2 or any(v is None for _, v in filas_n):
            return 'La rúbrica necesita al menos dos niveles, cada uno con su valor.'
    if not filas_c:
        return 'Agregue al menos un criterio.'
    niveles = list(inst.niveles.all())
    criterios = list(inst.criterios.all())
    if usado and (len(filas_c) != len(criterios) or (inst.tipo == 'rubrica' and len(filas_n) != len(niveles))):
        return ('Este instrumento ya se usó para calificar: puede cambiar nombres, valores y descriptores, pero no '
                'agregar ni quitar filas o columnas. Duplíquelo para hacer uno nuevo.')
    inst.save()
    if inst.tipo == 'rubrica':
        for k, (n, v) in enumerate(filas_n):
            if k < len(niveles):
                niveles[k].nombre, niveles[k].valor, niveles[k].orden = n, v, k
                niveles[k].save()
            else:
                niveles.append(Nivel.objects.create(instrumento=inst, nombre=n, valor=v, orden=k))
        for sobra in niveles[len(filas_n):]:
            sobra.delete()
        niveles = niveles[:len(filas_n)]
    for k, (i, n, p) in enumerate(filas_c):
        cr = criterios[k] if k < len(criterios) else Criterio(instrumento=inst)
        cr.nombre, cr.peso, cr.orden = n, p, k
        cr.descriptores = {str(nv.id): (P.get(f'desc_{i}_{j}') or '').strip()[:400] for j, nv in enumerate(niveles)}
        cr.save()
    for sobra in criterios[len(filas_c):]:
        sobra.delete()
    return ''


@login_required
@require_POST
def instrumento_accion(request, iid):
    inst = get_object_or_404(Instrumento, pk=iid)
    colegio, _ = _colegio_y_base(request)
    accion = request.POST.get('accion')
    if accion == 'duplicar':
        if inst.propietario_id != request.user.id and not (inst.compartido and colegio and inst.colegio_id == colegio.id):
            raise Http404
        niveles = [(n.nombre, n.valor) for n in inst.niveles.all()]
        crits = list(inst.criterios.all())
        nuevo = logica.crear_instrumento(
            request.user, colegio, f'{inst.nombre} (copia)', inst.tipo, [(cr.nombre, cr.peso) for cr in crits],
            niveles or None, [[cr.descriptor(n) for n in inst.niveles.all()] for cr in crits])
        messages.success(request, 'Copia creada.')
        return redirect('aula:instrumento', iid=nuevo.pk)
    inst = _instrumento_editable(request, iid)
    if accion == 'eliminar':
        inst.delete()
        messages.info(request, 'Instrumento eliminado.')
    return redirect('aula:instrumentos')


# ---------------------------------------------------------------------------
# Escala de valoración del docente (Salón Digital)
# ---------------------------------------------------------------------------
@login_required
def escala(request):
    """El docente de Salón Digital define su escala; en un colegio rige la del colegio."""
    if getattr(request, 'colegio', None) is not None:
        messages.info(request, 'En el colegio se usa la escala de valoración del colegio.')
        return redirect('aula:inicio')
    if not hasattr(request.user, 'cuenta_salon'):
        return redirect('salon_digital:landing')
    from notas.planillas.guardar import a_decimal
    from .models import EscalaDocente
    obj = EscalaDocente.objects.filter(usuario=request.user).first() or EscalaDocente(usuario=request.user)
    niveles = obj.lista()
    errores = []
    if request.method == 'POST':
        if request.POST.get('accion') == 'nacional':
            from .models import ESCALA_NACIONAL
            obj.niveles = [dict(n) for n in ESCALA_NACIONAL]
            obj.save()
            messages.success(request, 'Volvió a la escala nacional (1,0 a 5,0).')
            return redirect('aula:escala')
        niveles = []
        for n, a, b in zip(request.POST.getlist('nombre'), request.POST.getlist('min'), request.POST.getlist('max')):
            if not (n or '').strip() and not (a or '').strip() and not (b or '').strip():
                continue
            da, db = a_decimal(a), a_decimal(b)
            niveles.append(((n or '').strip().upper()[:40], da.quantize(Decimal('0.1')) if da is not None else None,
                            db.quantize(Decimal('0.1')) if db is not None else None))
        errores = logica.validar_escala(niveles)
        if not errores:
            obj.niveles = [{'nombre': n, 'min': str(a), 'max': str(b)} for n, a, b in sorted(niveles, key=lambda x: x[1])]
            obj.save()
            messages.success(request, 'Escala guardada. Rige en sus aulas, rúbricas y calificaciones.')
            return redirect('aula:escala')
    filas = list(niveles) + [('', None, None)] * max(0, 6 - len(niveles))
    return render(request, 'aula/escala.html', {'filas': filas, 'errores': errores, 'base': 'aula/base_salon.html'})

