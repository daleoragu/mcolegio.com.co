# notas/views/carnet_views.py
"""Carné estudiantil con QR y kiosko de asistencia.

El QR del carné lleva una dirección con un código al azar de cada estudiante
(/c/<código>/), no su número: así nadie arma el QR de otro. El kiosko lee ese
QR con la cámara del equipo o con un lector USB y marca al estudiante presente
en la clase activa; al terminar, un botón marca ausentes a los que no pasaron.
"""
import base64
import re
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
    if not request.colegio:
        return HttpResponseNotFound("<h1>Colegio no configurado</h1>")

    cursos = Curso.objects.filter(colegio=request.colegio).order_by('nombre')
    curso_seleccionado_id = request.GET.get('curso_id')
    estudiantes = Estudiante.objects.filter(colegio=request.colegio, is_active=True).select_related('user', 'curso')
    if curso_seleccionado_id:
        estudiantes = estudiantes.filter(curso_id=curso_seleccionado_id)
    estudiantes = list(estudiantes)
    for estudiante in estudiantes:
        estudiante.qr_image_base64 = _qr_base64(url_carnet(request, estudiante), caja=6, borde=2)

    return render(request, 'notas/admin_tools/impresion_masiva_carnets.html', {
        'colegio': request.colegio,
        'estudiantes': estudiantes,
        'cursos': cursos,
        'curso_seleccionado_id': curso_seleccionado_id,
    })


# ==============================================================================
# LO QUE ABRE EL QR
# ==============================================================================

def carnet_qr(request, codigo):
    """Lo que abre el QR del carné.

    Con el kiosko activo en ese equipo, marca la asistencia. Si no, muestra que el
    carné es válido (lo mismo que trae impreso: nombre, curso y colegio).
    """
    estudiante = (Estudiante.objects.select_related('user', 'curso', 'colegio')
                  .filter(codigo_carnet=codigo, colegio=request.colegio).first()
                  if getattr(request, 'colegio', None) else None)
    if estudiante is None:
        return render(request, 'notas/docente/carnet_verificado.html', {'estudiante': None}, status=404)
    if request.user.is_authenticated and request.session.get(CLAVE_KIOSKO):
        resultado = _registrar(request, estudiante)
        getattr(messages, resultado['nivel'])(request, resultado['mensaje'])
        return redirect('notas:vista_kiosko_asistencia')
    return render(request, 'notas/docente/carnet_verificado.html', {'estudiante': estudiante})


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
