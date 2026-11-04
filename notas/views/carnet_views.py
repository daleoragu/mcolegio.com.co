# notas/views/carnet_views.py
"""Carné estudiantil con QR y kiosko de asistencia.

El QR del carné lleva una dirección con un código al azar de cada estudiante
(/c/<código>/), no su número: así nadie arma el QR de otro. El kiosko lee ese
QR con la cámara del equipo o con un lector USB y marca al estudiante presente
en la clase activa; al terminar, un botón marca ausentes a los que no pasaron.
"""
import base64
import re
from datetime import timedelta
from io import BytesIO

import qrcode
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import HttpResponseNotFound, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from ..models.academicos import AsignacionDocente, Asistencia
from ..models.perfiles import Curso, Docente, Estudiante
from ..permisos import es_admin, es_admin_usuario

CLAVE_KIOSKO = 'kiosko_asignacion_id'


def es_admin_del_colegio(user):
    """Superusuario o administrador de ESTE colegio (ver notas/permisos.py)."""
    return es_admin_usuario(user)


def _qr_base64(texto, caja=10, borde=4):
    qr = qrcode.QRCode(version=None, error_correction=qrcode.constants.ERROR_CORRECT_M, box_size=caja, border=borde)
    qr.add_data(texto)
    qr.make(fit=True)
    buffered = BytesIO()
    qr.make_image(fill_color="black", back_color="white").save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode('utf-8')


def url_carnet(request, estudiante):
    return request.build_absolute_uri(reverse('notas:carnet_qr', args=[estudiante.asegurar_codigo_carnet()]))


def _puede_ver_carnet(request, estudiante):
    if es_admin(request):
        return True
    docente = Docente.objects.filter(user=request.user, colegio=request.colegio).first()
    if docente is None:
        return estudiante.user_id == request.user.id
    return (estudiante.curso_id is not None and
            (AsignacionDocente.objects.filter(docente=docente, curso_id=estudiante.curso_id).exists()
             or estudiante.curso.director_grado_id == docente.id))


# ==============================================================================
# CARNÉ INDIVIDUAL E IMPRESIÓN MASIVA
# ==============================================================================

@login_required
def generar_carnet_estudiante(request, estudiante_id):
    if not request.colegio:
        return HttpResponseNotFound("<h1>Colegio no configurado</h1>")
    estudiante = get_object_or_404(Estudiante.objects.select_related('user', 'curso'),
                                   id=estudiante_id, colegio=request.colegio)
    if not _puede_ver_carnet(request, estudiante):
        return HttpResponseNotFound("<h1>Estudiante no encontrado</h1>")
    if request.method == 'POST' and request.POST.get('accion') == 'nuevo_codigo' and es_admin(request):
        estudiante.asegurar_codigo_carnet(nuevo=True)
        messages.success(request, 'Se cambió el código del carné. El carné anterior ya no sirve: imprima este.')
        return redirect('notas:generar_carnet_estudiante', estudiante_id=estudiante.id)
    return render(request, 'notas/docente/carnet_estudiante.html', {
        'colegio': request.colegio,
        'estudiante': estudiante,
        'qr_image': _qr_base64(url_carnet(request, estudiante)),
        'puede_cambiar': es_admin(request),
    })


@login_required
@user_passes_test(es_admin_del_colegio, login_url='/admin/login/')
def impresion_masiva_carnets(request):
    """Carnés de estudiantes (por curso) o de docentes, para imprimir uno o todos."""
    if not request.colegio:
        return HttpResponseNotFound("<h1>Colegio no configurado</h1>")
    from django.templatetags.static import static
    tipo = 'docentes' if request.GET.get('tipo') == 'docentes' else 'estudiantes'
    cursos = Curso.objects.filter(colegio=request.colegio).order_by('nombre')
    curso_seleccionado_id = request.GET.get('curso_id')
    foto_vacia = static('img/default-user.png')
    personas = []
    if tipo == 'estudiantes':
        estudiantes = Estudiante.objects.filter(colegio=request.colegio, is_active=True).select_related('user', 'curso', 'ficha')
        if curso_seleccionado_id:
            estudiantes = estudiantes.filter(curso_id=curso_seleccionado_id)
        for est in estudiantes:
            try:
                ficha = est.ficha
            except Exception:
                ficha = None
            personas.append({
                'id': f'e{est.id}', 'nombre': est.user.get_full_name() or est.user.username,
                'foto': ficha.foto.url if ficha and ficha.foto else foto_vacia,
                'documento': (f"{ficha.get_tipo_documento_display()}: {ficha.numero_documento}"
                              if ficha and ficha.numero_documento else 'Documento: No reg.'),
                'linea': f"Curso: {est.curso.nombre}" if est.curso_id else 'Curso: N/A',
                'pie': 'CARNET ESTUDIANTIL',
                'qr': _qr_base64(url_carnet(request, est), caja=6, borde=2)})
    else:
        directores = {}
        for c in cursos:
            if c.director_grado_id:
                directores.setdefault(c.director_grado_id, []).append(c.nombre)
        for doc in Docente.objects.filter(colegio=request.colegio, user__is_active=True).select_related('user', 'ficha'):
            try:
                ficha = doc.ficha
            except Exception:
                ficha = None
            personas.append({
                'id': f'd{doc.id}', 'nombre': doc.user.get_full_name() or doc.user.username,
                'foto': ficha.foto.url if ficha and ficha.foto else foto_vacia,
                'documento': f"C.C.: {ficha.numero_documento}" if ficha and ficha.numero_documento else 'Documento: No reg.',
                'linea': ('Director(a) de grupo ' + ', '.join(directores[doc.id])) if doc.id in directores else 'Docente',
                'pie': 'CARNET DOCENTE',
                'qr': _qr_base64(request.build_absolute_uri(
                    reverse('notas:carnet_qr', args=[doc.asegurar_codigo_carnet()])), caja=6, borde=2)})

    return render(request, 'notas/admin_tools/impresion_masiva_carnets.html', {
        'colegio': request.colegio,
        'tipo': tipo,
        'personas': personas,
        'cursos': cursos,
        'curso_seleccionado_id': curso_seleccionado_id,
    })


@login_required
def mi_carne(request):
    """El carné digital del estudiante o del docente, para mostrarlo desde el celular."""
    if not request.colegio:
        return HttpResponseNotFound("<h1>Colegio no configurado</h1>")
    from django.templatetags.static import static
    est = Estudiante.objects.filter(user=request.user, colegio=request.colegio).select_related('curso').first()
    doc = None if est else Docente.objects.filter(user=request.user, colegio=request.colegio).first()
    if est is None and doc is None:
        return HttpResponseNotFound("<h1>El carné es para estudiantes y docentes del colegio</h1>")
    persona = est or doc
    try:
        ficha = persona.ficha
    except Exception:
        ficha = None
    if est is not None:
        documento = (f"{ficha.get_tipo_documento_display()}: {ficha.numero_documento}"
                     if ficha and ficha.numero_documento else '')
        linea, pie = (f"Curso {est.curso.nombre}" if est.curso_id else ''), 'CARNÉ ESTUDIANTIL'
    else:
        documento = f"C.C.: {ficha.numero_documento}" if ficha and ficha.numero_documento else ''
        dirige = list(doc.cursos_dirigidos.values_list('nombre', flat=True))
        linea, pie = (('Director(a) de grupo ' + ', '.join(dirige)) if dirige else 'Docente'), 'CARNÉ DOCENTE'
    url = request.build_absolute_uri(reverse('notas:carnet_qr', args=[persona.asegurar_codigo_carnet()]))
    return render(request, 'notas/docente/mi_carne.html', {
        'colegio': request.colegio, 'nombre': request.user.get_full_name() or request.user.username,
        'foto': ficha.foto.url if ficha and ficha.foto else static('img/default-user.png'),
        'documento': documento, 'linea': linea, 'pie': pie, 'es_estudiante': est is not None,
        'activo': est.is_active if est else request.user.is_active,
        'qr': _qr_base64(url, caja=10, borde=2)})


# ==============================================================================
# LO QUE ABRE EL QR
# ==============================================================================

MAX_INTENTOS_PIN = 5
MINUTOS_BLOQUEO_PIN = 15
MINUTOS_SESION_CARNET = 30
CLAVE_CARNET = 'entrada_carnet'      # la sesión se abrió con el carné y el PIN


def _estudiante_del_codigo(request, codigo):
    if not getattr(request, 'colegio', None):
        return None
    return (Estudiante.objects.select_related('user', 'curso', 'colegio')
            .filter(codigo_carnet=codigo, colegio=request.colegio).first())


def carnet_qr(request, codigo):
    """Lo que abre el QR del carné.

    · Con el kiosko activo en ese equipo: marca la asistencia.
    · Si no: muestra que el carné es válido y pide el PIN; con el PIN correcto el
      estudiante entra a su menú (votar, boletín, horario, tareas, certificados).
    """
    from django.contrib.auth import login
    estudiante = _estudiante_del_codigo(request, codigo)
    if estudiante is None:
        docente = (Docente.objects.select_related('user', 'colegio')
                   .filter(codigo_carnet=codigo, colegio=request.colegio).first()
                   if getattr(request, 'colegio', None) else None)
        if docente is not None:
            return render(request, 'notas/docente/carnet_verificado.html', {
                'docente': docente, 'cursos_dirigidos': list(docente.cursos_dirigidos.values_list('nombre', flat=True))})
        return render(request, 'notas/docente/carnet_verificado.html', {'estudiante': None}, status=404)
    if request.user.is_authenticated and request.session.get(CLAVE_KIOSKO):
        resultado = _registrar(request, estudiante)
        getattr(messages, resultado['nivel'])(request, resultado['mensaje'])
        return redirect('notas:vista_kiosko_asistencia')
    if request.user.is_authenticated and request.user.id == estudiante.user_id:
        return redirect('notas:carnet_menu', codigo=codigo)

    error = ''
    ahora = timezone.now()
    bloqueado = estudiante.pin_bloqueado_hasta and estudiante.pin_bloqueado_hasta > ahora
    if request.method == 'POST' and estudiante.is_active:
        if bloqueado:
            error = f'Demasiados intentos. Espere {MINUTOS_BLOQUEO_PIN} minutos o pídale el PIN a su director de grupo.'
        elif estudiante.pin_carnet and (request.POST.get('pin') or '').strip() == estudiante.pin_carnet:
            Estudiante.objects.filter(pk=estudiante.pk).update(pin_fallidos=0, pin_bloqueado_hasta=None)
            login(request, estudiante.user, backend='django.contrib.auth.backends.ModelBackend')
            request.session[CLAVE_CARNET] = codigo
            # En un equipo del colegio la sesión no se queda abierta.
            request.session.set_expiry(MINUTOS_SESION_CARNET * 60)
            return redirect('notas:carnet_menu', codigo=codigo)
        else:
            fallidos = estudiante.pin_fallidos + 1
            cambios = {'pin_fallidos': fallidos}
            if fallidos >= MAX_INTENTOS_PIN:
                cambios = {'pin_fallidos': 0,
                           'pin_bloqueado_hasta': ahora + timedelta(minutes=MINUTOS_BLOQUEO_PIN)}
                error = f'Demasiados intentos. Espere {MINUTOS_BLOQUEO_PIN} minutos o pídale el PIN a su director de grupo.'
            else:
                quedan = MAX_INTENTOS_PIN - fallidos
                error = f'Ese PIN no es. Le quedan {quedan} intento{"s" if quedan != 1 else ""}.'
            Estudiante.objects.filter(pk=estudiante.pk).update(**cambios)
    return render(request, 'notas/docente/carnet_verificado.html', {
        'estudiante': estudiante, 'error': error, 'pedir_pin': estudiante.is_active,
        'otra_sesion': request.user if request.user.is_authenticated else None})


def _menu_carnet(request, estudiante):
    from ..modulos import activos
    mods = activos(request.colegio)
    opciones = []

    def agregar(clave, nombre, icono, ruta, *args):
        try:
            opciones.append({'clave': clave, 'nombre': nombre, 'icono': icono, 'url': reverse(ruta, args=args)})
        except Exception:
            pass

    if 'elecciones' in mods:
        from votaciones.models import Eleccion
        if Eleccion.objects.filter(colegio=request.colegio, estado='abierta').exists():
            agregar('votar', 'Votar', 'fa-check-to-slot', 'votaciones:inicio')
    agregar('boletin', 'Boletín y notas', 'fa-file-invoice', 'notas:mi_boletin')
    if 'horarios' in mods:
        agregar('horario', 'Mi horario', 'fa-calendar-week', 'horarios:mi_horario')
    if 'salon' in mods:
        agregar('tareas', 'Mis tareas', 'fa-list-check', 'aula:inicio')
    if 'certificados' in mods:
        agregar('certificados', 'Certificados', 'fa-award', 'certificados:mis_certificados')
    agregar('panel', 'Todo mi panel', 'fa-house', 'notas:panel_estudiante')
    return opciones


def carnet_menu(request, codigo):
    estudiante = _estudiante_del_codigo(request, codigo)
    if estudiante is None:
        return render(request, 'notas/docente/carnet_verificado.html', {'estudiante': None}, status=404)
    if not request.user.is_authenticated or request.user.id != estudiante.user_id:
        return redirect('notas:carnet_qr', codigo=codigo)
    return render(request, 'notas/docente/carnet_menu.html', {
        'estudiante': estudiante, 'codigo': codigo, 'opciones': _menu_carnet(request, estudiante),
        'minutos': MINUTOS_SESION_CARNET})


@require_POST
def carnet_salir(request, codigo):
    from django.contrib.auth import logout
    logout(request)
    messages.info(request, 'Sesión cerrada. Puede entregar el equipo al siguiente.')
    return redirect('notas:carnet_qr', codigo=codigo)


@login_required
def pines_carnet(request):
    """Lista para imprimir y entregar: estudiante, curso y PIN del carné.

    La ve la administración (todos los cursos) y el director de grupo (los suyos).
    """
    if not request.colegio:
        return HttpResponseNotFound("<h1>Colegio no configurado</h1>")
    if es_admin(request):
        cursos = Curso.objects.filter(colegio=request.colegio)
    else:
        docente = Docente.objects.filter(user=request.user, colegio=request.colegio).first()
        cursos = Curso.objects.filter(colegio=request.colegio, director_grado=docente) if docente else Curso.objects.none()
    cursos = list(cursos.order_by('grado', 'nombre'))
    if not cursos:
        return HttpResponseNotFound("<h1>No tiene cursos a cargo</h1>")
    curso = next((c for c in cursos if str(c.id) == request.GET.get('curso')), cursos[0])
    estudiantes = list(Estudiante.objects.filter(colegio=request.colegio, curso=curso, is_active=True)
                       .select_related('user').order_by('user__last_name', 'user__first_name'))
    if request.method == 'POST':
        est = next((e for e in estudiantes if str(e.id) == request.POST.get('estudiante')), None)
        if est is not None:
            est.asegurar_pin_carnet(nuevo=True)
            messages.success(request, f'Nuevo PIN para {est}: {est.pin_carnet}.')
        return redirect(f"{reverse('notas:pines_carnet')}?curso={curso.id}")
    for est in estudiantes:
        est.asegurar_pin_carnet()
    return render(request, 'notas/admin_tools/pines_carnet.html', {
        'colegio': request.colegio, 'cursos': cursos, 'curso': curso, 'estudiantes': estudiantes})


@login_required
def registrar_asistencia_qr(request, estudiante_id):
    """Dirección de los carnés viejos, que llevaban el número del estudiante. Ya no marca."""
    messages.warning(request, 'Ese es un carné antiguo (con un QR que se podía copiar). '
                              'Imprímale uno nuevo desde «Imprimir carnets».')
    return redirect('notas:vista_kiosko_asistencia')


# ==============================================================================
# KIOSKO
# ==============================================================================

def _asignaciones_kiosko(request):
    qs = AsignacionDocente.objects.filter(colegio=request.colegio).select_related('materia', 'curso')
    if es_admin(request):
        return qs.order_by('curso__nombre', 'materia__nombre')
    docente = Docente.objects.filter(user=request.user, colegio=request.colegio).first()
    if docente is None:
        return qs.none()
    return qs.filter(docente=docente).order_by('curso__nombre', 'materia__nombre')


def _asignacion_activa(request):
    aid = request.session.get(CLAVE_KIOSKO)
    if not aid:
        return None
    asignacion = _asignaciones_kiosko(request).filter(id=aid).first()
    if asignacion is None:
        request.session.pop(CLAVE_KIOSKO, None)
    return asignacion


def _lista_del_dia(asignacion):
    hoy = timezone.localdate()
    estados = dict(Asistencia.objects.filter(asignacion=asignacion, fecha=hoy).values_list('estudiante_id', 'estado'))
    nombres = dict(Asistencia.ESTADO_CHOICES)
    filas = []
    for est in (Estudiante.objects.filter(colegio=asignacion.colegio, curso=asignacion.curso, is_active=True)
                .select_related('user').order_by('user__last_name', 'user__first_name')):
        estado = estados.get(est.id)
        filas.append({'id': est.id, 'nombre': f'{est.user.last_name} {est.user.first_name}'.strip() or est.user.username,
                      'estado': estado or '', 'estado_txt': nombres.get(estado, 'Sin registrar')})
    return {
        'filas': filas,
        'presentes': sum(1 for f in filas if f['estado'] in ('P', 'T')),
        'ausentes': sum(1 for f in filas if f['estado'] == 'A'),
        'pendientes': sum(1 for f in filas if not f['estado']),
        'total': len(filas),
    }


def _registrar(request, estudiante):
    asignacion = _asignacion_activa(request)
    if asignacion is None:
        return {'ok': False, 'nivel': 'error', 'mensaje': 'No hay una clase activa en el kiosko.'}
    nombre = estudiante.user.get_full_name() or estudiante.user.username
    if estudiante.curso_id != asignacion.curso_id or not estudiante.is_active:
        return {'ok': False, 'nivel': 'warning', 'nombre': nombre,
                'mensaje': f'{nombre} no está en {asignacion.curso.nombre}.'}
    asistencia, creada = Asistencia.objects.get_or_create(
        colegio=request.colegio, estudiante=estudiante, asignacion=asignacion, fecha=timezone.localdate(),
        defaults={'estado': 'P'})
    if creada:
        return {'ok': True, 'nivel': 'success', 'nombre': nombre, 'mensaje': f'{nombre}: presente.'}
    if asistencia.excusa_id:
        return {'ok': False, 'nivel': 'info', 'nombre': nombre,
                'mensaje': f'{nombre} tiene excusa aprobada hoy: no se cambia su asistencia.'}
    if asistencia.estado == 'A':
        # Lo habían marcado ausente y llegó: queda como «tarde».
        asistencia.estado = 'T'
        asistencia.save(update_fields=['estado'])
        return {'ok': True, 'nivel': 'success', 'nombre': nombre, 'mensaje': f'{nombre}: llegó tarde.'}
    return {'ok': True, 'nivel': 'info', 'nombre': nombre, 'repetido': True,
            'mensaje': f'{nombre} ya estaba registrado hoy.'}


PATRON_CODIGO = re.compile(r'/c/([A-Za-z0-9_-]{6,16})/?(?:[?#].*)?$')


def codigo_leido(texto):
    """Del texto que entrega la cámara o el lector USB, el código del carné."""
    texto = (texto or '').strip()
    m = PATRON_CODIGO.search(texto)
    if m:
        return m.group(1)
    if re.fullmatch(r'[A-Za-z0-9_-]{6,16}', texto):
        return texto
    return None


@login_required
def vista_kiosko_asistencia(request):
    if not request.colegio:
        return HttpResponseNotFound("<h1>Colegio no configurado</h1>")
    asignaciones = _asignaciones_kiosko(request)

    if request.method == 'POST':
        asignacion_id = request.POST.get('asignacion_id')
        if asignacion_id and asignaciones.filter(id=asignacion_id).exists():
            request.session[CLAVE_KIOSKO] = int(asignacion_id)
        elif 'finalizar' in request.POST:
            request.session.pop(CLAVE_KIOSKO, None)
        return redirect('notas:vista_kiosko_asistencia')

    asignacion = _asignacion_activa(request)
    context = {'colegio': request.colegio, 'asignaciones': asignaciones, 'asignacion_activa': asignacion}
    if asignacion is not None:
        context['dia'] = _lista_del_dia(asignacion)
        context['hoy'] = timezone.localdate()
    return render(request, 'notas/docente/kiosko_asistencia.html', context)


@login_required
@require_POST
def kiosko_registrar(request):
    """El kiosko manda lo que leyó (cámara o lector USB) y recibe a quién marcó."""
    codigo = codigo_leido(request.POST.get('codigo'))
    if codigo is None:
        if re.search(r'/asistencia/registrar-qr/\d+', request.POST.get('codigo') or ''):
            resultado = {'ok': False, 'nivel': 'warning',
                         'mensaje': 'Carné antiguo: imprímale uno nuevo desde «Imprimir carnets».'}
        else:
            resultado = {'ok': False, 'nivel': 'error', 'mensaje': 'Ese código no es de un carné del colegio.'}
    else:
        estudiante = Estudiante.objects.select_related('user').filter(
            codigo_carnet=codigo, colegio=request.colegio).first()
        if estudiante is None:
            resultado = {'ok': False, 'nivel': 'error', 'mensaje': 'Carné no encontrado (o ya fue reemplazado).'}
        else:
            resultado = _registrar(request, estudiante)
    asignacion = _asignacion_activa(request)
    if asignacion is not None:
        resultado['dia'] = _lista_del_dia(asignacion)
    return JsonResponse(resultado)


@login_required
@require_POST
def kiosko_marcar_ausentes(request):
    """Los que no han pasado el carné hoy quedan ausentes en la clase activa."""
    asignacion = _asignacion_activa(request)
    if asignacion is None:
        messages.error(request, 'No hay una clase activa en el kiosko.')
        return redirect('notas:vista_kiosko_asistencia')
    hoy = timezone.localdate()
    ya = set(Asistencia.objects.filter(asignacion=asignacion, fecha=hoy).values_list('estudiante_id', flat=True))
    faltan = [est for est in Estudiante.objects.filter(colegio=request.colegio, curso=asignacion.curso, is_active=True)
              if est.id not in ya]
    Asistencia.objects.bulk_create([
        Asistencia(colegio=request.colegio, estudiante=est, asignacion=asignacion, fecha=hoy, estado='A')
        for est in faltan], ignore_conflicts=True)
    if faltan:
        messages.success(request, f'{len(faltan)} estudiante{"s" if len(faltan) != 1 else ""} '
                                  f'quedaron ausentes. Si alguno llega después, al pasar el carné queda «tarde».')
    else:
        messages.info(request, 'Todos ya tenían registro hoy: no había a quién marcar ausente.')
    return redirect('notas:vista_kiosko_asistencia')
