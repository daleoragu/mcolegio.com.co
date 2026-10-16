from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import Http404, HttpResponse, HttpResponseForbidden, HttpResponseNotFound
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from notas.models import AdministradorColegio, Curso, Estudiante, Notificacion
from notas.permisos import admin_requerido, es_admin

from . import logica
from .models import CertificadoEmitido, ConfiguracionCertificados, SolicitudCertificado

MAX_LISTA = 200


def _avisar(colegio, usuarios, mensaje, url):
    for u in {u for u in usuarios if u is not None}:
        Notificacion.objects.create(colegio=colegio, destinatario=u, mensaje=mensaje[:255], tipo='GENERAL', url=url)


# ---------------------------------------------------------------------------
# Secretaría
# ---------------------------------------------------------------------------
@admin_requerido
def panel(request):
    colegio = request.colegio
    if not colegio:
        return HttpResponseNotFound('<h1>Colegio no configurado</h1>')
    q = (request.GET.get('q') or '').strip()
    curso_id = request.GET.get('curso_id') or ''
    incluir = request.GET.get('exalumnos') == '1'
    estudiantes = Estudiante.objects.filter(colegio=colegio).select_related('user', 'curso', 'ficha')
    if not incluir:
        estudiantes = estudiantes.filter(is_active=True)
    if curso_id:
        estudiantes = estudiantes.filter(curso_id=curso_id)
    for palabra in q.split():
        estudiantes = estudiantes.filter(Q(user__first_name__icontains=palabra) | Q(user__last_name__icontains=palabra)
                                         | Q(ficha__numero_documento__icontains=palabra))
    buscando = bool(q or curso_id)
    lista = list(estudiantes.order_by('user__last_name', 'user__first_name')[:MAX_LISTA]) if buscando else []
    pendientes = (SolicitudCertificado.objects.filter(colegio=colegio, estado='PENDIENTE')
                  .select_related('estudiante__user', 'estudiante__curso'))
    return render(request, 'certificados/panel.html', {
        'colegio': colegio, 'cursos': Curso.objects.filter(colegio=colegio).order_by('nombre'),
        'q': q, 'curso_id': curso_id, 'exalumnos': incluir, 'estudiantes': lista, 'buscando': buscando,
        'tope': len(lista) >= MAX_LISTA, 'pendientes': pendientes,
        'emitidos': CertificadoEmitido.objects.filter(colegio=colegio).select_related('estudiante__user')[:15],
        'conf': ConfiguracionCertificados.de(colegio),
    })


@admin_requerido
def estudiante(request, estudiante_id):
    est = get_object_or_404(Estudiante.objects.select_related('user', 'curso'), id=estudiante_id,
                            colegio=request.colegio)
    return render(request, 'certificados/estudiante.html', {
        'colegio': request.colegio, 'est': est, 'anos': logica.anos_disponibles(est),
        'emitidos': est.certificados.all(),
        'solicitudes': est.solicitudes_certificado.all()[:10],
    })


@admin_requerido
@require_POST
def generar(request, estudiante_id):
    est = get_object_or_404(Estudiante, id=estudiante_id, colegio=request.colegio)
    try:
        cert = logica.emitir(est, request.POST.get('tipo'), request.POST.get('ano') or None, request.user)
    except logica.SinDatos as e:
        messages.error(request, str(e))
        return redirect('certificados:estudiante', estudiante_id=est.id)
    return redirect('certificados:pdf', codigo=cert.codigo)


@admin_requerido
@require_POST
def anular(request, codigo):
    cert = get_object_or_404(CertificadoEmitido, codigo=codigo, colegio=request.colegio)
    cert.anulado = True
    cert.motivo_anulacion = (request.POST.get('motivo') or '').strip()[:200]
    cert.save(update_fields=['anulado', 'motivo_anulacion'])
    messages.success(request, f'El certificado {cert.codigo} quedó anulado: al verificarlo, sale como anulado.')
    return redirect('certificados:estudiante', estudiante_id=cert.estudiante_id)


@admin_requerido
@require_POST
def resolver(request, solicitud_id):
    sol = get_object_or_404(SolicitudCertificado, id=solicitud_id, colegio=request.colegio, estado='PENDIENTE')
    url_familia = request.build_absolute_uri(reverse('certificados:mis_certificados'))
    if request.POST.get('accion') == 'aprobar':
        try:
            cert = logica.emitir(sol.estudiante, sol.tipo, sol.ano_lectivo, request.user)
        except logica.SinDatos as e:
            messages.error(request, f'No se pudo aprobar: {e}')
            return redirect('certificados:panel')
        sol.estado, sol.certificado = 'APROBADA', cert
        _avisar(request.colegio, [sol.estudiante.user], f'Su {cert.get_tipo_display().lower()} está listo para descargar.',
                url_familia)
        messages.success(request, f'Aprobado. {sol.estudiante} ya puede descargarlo desde «Mis certificados».')
    else:
        sol.estado = 'RECHAZADA'
        sol.respuesta = (request.POST.get('respuesta') or '').strip()[:200]
        _avisar(request.colegio, [sol.estudiante.user],
                f'Su solicitud de {sol.get_tipo_display().lower()} no fue aprobada'
                + (f': {sol.respuesta}' if sol.respuesta else '. Comuníquese con la secretaría.'), url_familia)
        messages.info(request, 'Solicitud rechazada; se le avisó a la familia.')
    sol.resuelta, sol.resuelta_por = timezone.now(), request.user
    sol.save()
    return redirect('certificados:panel')


@admin_requerido
def configuracion(request):
    conf = ConfiguracionCertificados.de(request.colegio)
    from django import forms

    class Formulario(forms.ModelForm):
        class Meta:
            model = ConfiguracionCertificados
            exclude = ['colegio']
            widgets = {'texto_final': forms.Textarea(attrs={'rows': 3}), 'modo_entrega': forms.RadioSelect}

    form = Formulario(request.POST or None, instance=conf)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Configuración de certificados guardada.')
        return redirect('certificados:panel')
    return render(request, 'certificados/configuracion.html', {'colegio': request.colegio, 'form': form})


@admin_requerido
def importar(request):
    resumen, errores = None, []
    if request.method == 'POST':
        archivo = request.FILES.get('archivo')
        if not archivo:
            errores = ['Escoja el archivo de Excel.']
        else:
            try:
                resumen, errores = logica.importar_excel(archivo, request.colegio, request.user)
            except logica.SinDatos as e:
                errores = [str(e)]
    return render(request, 'certificados/importar.html', {
        'colegio': request.colegio, 'resumen': resumen, 'errores': errores[:60], 'mas_errores': max(0, len(errores) - 60)})


@admin_requerido
def plantilla(request):
    r = HttpResponse(logica.plantilla_excel(),
                     content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    r['Content-Disposition'] = 'attachment; filename="Plantilla notas de años anteriores.xlsx"'
    return r


# ---------------------------------------------------------------------------
# El PDF y la verificación
# ---------------------------------------------------------------------------
def _puede_ver(request, cert):
    if not request.user.is_authenticated:
        return False
    if es_admin(request) and (request.user.is_superuser or cert.colegio_id == getattr(request.colegio, 'id', None)):
        return True
    return cert.estudiante.user_id == request.user.id and not cert.anulado


@login_required
def pdf(request, codigo):
    cert = get_object_or_404(CertificadoEmitido.objects.select_related('colegio', 'estudiante'), codigo=codigo)
    if not _puede_ver(request, cert):
        return HttpResponseForbidden('Este certificado no es suyo.')
    try:
        from weasyprint import HTML
    except ImportError:
        return HttpResponse('La generación de PDF no está disponible en este servidor.', status=500)
    url = request.build_absolute_uri(reverse('certificados:verificar', args=[cert.codigo]))
    plantilla_pdf = 'certificados/pdf_estudio.html' if cert.tipo == 'ESTUDIO' else 'certificados/pdf_calificaciones.html'
    html = render_to_string(plantilla_pdf, {
        'c': cert.contenido, 'cert': cert, 'colegio': cert.colegio, 'url_verificar': url,
        'qr': logica.qr_base64(url)}, request=request)
    datos = HTML(string=html, base_url=request.build_absolute_uri('/')).write_pdf()
    nombre = f'{cert.get_tipo_display()} {cert.ano_lectivo or ""} {cert.contenido.get("nombre", "")}'.strip()
    r = HttpResponse(datos, content_type='application/pdf')
    r['Content-Disposition'] = f'inline; filename="{nombre}.pdf"'
    return r


def verificar(request, codigo=None):
    """Página pública: el QR del certificado abre aquí."""
    codigo = (codigo or request.GET.get('codigo') or '').strip().upper().replace(' ', '').replace('-', '')
    cert = CertificadoEmitido.objects.filter(codigo=codigo).select_related('colegio').first() if codigo else None
    c = cert.contenido if cert else {}
    documento = c.get('documento', '')
    oculto = ('•' * max(0, len(documento) - 4) + documento[-4:]) if documento else ''
    return render(request, 'certificados/verificar.html', {
        'codigo': codigo, 'cert': cert, 'c': c, 'documento_oculto': oculto,
        'colegio': cert.colegio if cert else getattr(request, 'colegio', None)})


# ---------------------------------------------------------------------------
# Estudiante / acudiente
# ---------------------------------------------------------------------------
def _estudiante_de(request):
    if not request.colegio:
        raise Http404
    return Estudiante.objects.filter(user=request.user, colegio=request.colegio).select_related('curso').first()


@login_required
def mis_certificados(request):
    est = _estudiante_de(request)
    if est is None:
        messages.error(request, 'Su usuario no tiene un perfil de estudiante en este colegio.')
        return redirect('notas:dashboard')
    conf = ConfiguracionCertificados.de(request.colegio)
    return render(request, 'certificados/mis_certificados.html', {
        'colegio': request.colegio, 'est': est, 'conf': conf, 'anos': logica.anos_disponibles(est),
        'emitidos': est.certificados.filter(anulado=False),
        'solicitudes': est.solicitudes_certificado.all()[:10],
        'pendientes': set(est.solicitudes_certificado.filter(estado='PENDIENTE')
                          .values_list('tipo', 'ano_lectivo')),
    })


@login_required
@require_POST
def solicitar(request):
    est = _estudiante_de(request)
    if est is None:
        return HttpResponseForbidden('Solo para estudiantes.')
    conf = ConfiguracionCertificados.de(request.colegio)
    tipo = request.POST.get('tipo')
    ano = request.POST.get('ano') or None
    ano = int(ano) if ano and ano.isdigit() else None
    if tipo not in ('ESTUDIO', 'CALIFICACIONES'):
        return HttpResponseForbidden('Tipo desconocido.')
    if tipo == 'CALIFICACIONES' and ano not in logica.anos_disponibles(est):
        messages.error(request, 'No hay notas de ese año.')
        return redirect('certificados:mis_certificados')
    if conf.modo_entrega == 'SECRETARIA':
        messages.info(request, 'En este colegio los certificados se piden directamente en la secretaría.')
        return redirect('certificados:mis_certificados')
    if conf.modo_entrega == 'LIBRE':
        try:
            cert = logica.emitir(est, tipo, ano, request.user)
        except logica.SinDatos as e:
            messages.error(request, str(e))
            return redirect('certificados:mis_certificados')
        return redirect('certificados:pdf', codigo=cert.codigo)
    if est.solicitudes_certificado.filter(estado='PENDIENTE', tipo=tipo, ano_lectivo=ano).exists():
        messages.info(request, 'Ya tiene esa solicitud en trámite.')
        return redirect('certificados:mis_certificados')
    SolicitudCertificado.objects.create(colegio=request.colegio, estudiante=est, tipo=tipo, ano_lectivo=ano,
                                        motivo=(request.POST.get('motivo') or '').strip()[:200])
    admins = [a.user for a in AdministradorColegio.objects.filter(colegio=request.colegio, activo=True)
              .select_related('user')]
    if request.colegio.admin_general_id:
        admins.append(request.colegio.admin_general)
    tipo_txt = dict(CertificadoEmitido.TIPOS)[tipo].lower()
    _avisar(request.colegio, admins, f'{est} pidió un {tipo_txt}{f" de {ano}" if ano else ""}.',
            request.build_absolute_uri(reverse('certificados:panel')))
    messages.success(request, 'Solicitud enviada. Le avisaremos cuando la secretaría la apruebe.')
    return redirect('certificados:mis_certificados')
