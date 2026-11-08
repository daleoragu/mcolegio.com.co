"""Planes y pagos: una sola página para pagar el plan o recargar saldo, con todas las formas de pago."""
from django.contrib import messages
from django.contrib.auth.models import User
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from . import pagos as P
from .decoradores import cuenta_requerida, staff_requerido
from .models import Pago

TIPOS_COMPROBANTE = ('image/jpeg', 'image/png', 'image/webp', 'image/heic', 'image/heif', 'application/pdf')
MAX_COMPROBANTE = 6 * 1024 * 1024


def _entero(v):
    try:
        return int(v)
    except (TypeError, ValueError):
        return None


@cuenta_requerida
def planes(request):
    cuenta = request.cuenta
    if request.method == 'POST':
        concepto = request.POST.get('concepto')
        if concepto in ('estandar', 'premium'):
            concepto = f'{concepto}_{"anio" if request.POST.get("periodo") == "anio" else "mes"}'
        forma = request.POST.get('forma')
        v = P.valor(concepto, _entero(request.POST.get('monto')))
        if v is None or forma not in ('linea', 'comprobante'):
            messages.error(request, 'Escoja qué va a pagar y cómo.')
            return redirect('salon_digital:planes')
        if forma == 'linea' and not P.en_linea():
            messages.info(request, 'El pago en línea todavía no está activo. Use la llave Bre-B, Nequi o transferencia.')
            forma = 'comprobante'
        pago = P.nuevo(request.user, concepto, v[0], v[1], forma)
        if forma == 'linea':
            from materiales import wompi
            regreso = request.build_absolute_uri(f'/salon_digital/pagos/{pago.referencia}/vuelta/')
            return redirect(wompi.url_checkout(pago, regreso, request.user.email or ''))
        return redirect('salon_digital:pago', referencia=pago.referencia)
    from materiales.creditos import cuenta as cuenta_ia
    from .planes_tabla import precios, tabla
    escogido = request.GET.get('plan') if request.GET.get('plan') in ('estandar', 'premium', 'recarga') else ''
    if not escogido:
        escogido = 'premium' if cuenta.nivel in ('premium', 'ilimitado') or cuenta.en_prueba else 'estandar'
    return render(request, 'salon_digital/planes.html', {
        'cuenta': cuenta, 'precios': precios(), 'tabla': tabla(), 'recargas': sorted(P.recargas().items()),
        'en_linea': P.en_linea(), 'datos': P.datos_cuenta(), 'saldo': cuenta_ia(request.user).saldo,
        'mis_pagos': Pago.objects.filter(usuario=request.user)[:15], 'escogido': escogido,
        'periodo': 'anio' if request.GET.get('periodo') == 'anio' else 'mes', 'motivo': request.GET.get('para', '')[:40],
    })


@cuenta_requerida
def pago(request, referencia):
    """Pago con llave Bre-B, Nequi o transferencia: los datos para pagar y el formulario del comprobante."""
    p = get_object_or_404(Pago, referencia=referencia, usuario=request.user)
    if request.method == 'POST' and p.estado in ('pendiente', 'revision', 'rechazado') and p.forma == 'comprobante':
        f = request.FILES.get('comprobante')
        if f is None:
            messages.error(request, 'Adjunte la foto o el PDF del comprobante.')
        elif f.size > MAX_COMPROBANTE or (f.content_type or '') not in TIPOS_COMPROBANTE:
            messages.error(request, 'El comprobante debe ser una foto o un PDF de máximo 6 MB.')
        else:
            if p.comprobante:
                p.comprobante.delete(save=False)
            p.comprobante = f
            p.medio = (request.POST.get('medio') or '')[:30]
            p.estado, p.nota = 'revision', ''
            p.save()
            from notas.models import Notificacion
            Notificacion.objects.bulk_create([
                Notificacion(colegio=None, destinatario=u, tipo='GENERAL', url='/salon_digital/pagos/revisar/',
                             mensaje=f'Pago por revisar: {request.cuenta.nombre_publico} · {p.get_concepto_display()} · ${p.monto:,}'.replace(',', '.'))
                for u in User.objects.filter(is_staff=True, is_active=True)])
            messages.success(request, 'Comprobante recibido. Lo revisamos y su plan se activa el mismo día; le llega un aviso.')
            return redirect('salon_digital:pago', referencia=p.referencia)
    return render(request, 'salon_digital/pago.html', {'p': p, 'datos': P.datos_cuenta(), 'cuenta': request.cuenta})


@cuenta_requerida
def vuelta(request, referencia):
    """Wompi devuelve aquí al docente. Si el aviso todavía no llegó, se consulta la transacción."""
    from materiales import wompi
    p = get_object_or_404(Pago, referencia=referencia, usuario=request.user, forma='linea')
    tid = (request.GET.get('id') or '').strip()[:60]
    if p.estado == 'pendiente' and tid:
        datos = wompi.consultar(tid)
        if datos and datos.get('reference') == p.referencia:
            p = P.aplicar_wompi(p.referencia, datos.get('status'), tid, datos.get('amount_in_cents'), datos.get('payment_method_type') or '')
    if p.estado == 'aprobado':
        messages.success(request, f'¡Pago aprobado! {P.describir(p)}')
    elif p.estado == 'rechazado':
        messages.error(request, 'El pago no se aprobó y no se cobró nada. Puede intentarlo otra vez o pagar con llave Bre-B o Nequi.')
    else:
        messages.info(request, 'Su pago está en proceso (PSE puede tardar unos minutos). Apenas se confirme, se activa solo y le llega un aviso.')
    return redirect('salon_digital:planes')


def comprobante(request, pk):
    """El comprobante solo lo ven el docente que pagó y los administradores."""
    p = get_object_or_404(Pago, pk=pk)
    if not request.user.is_authenticated or not (request.user.is_staff or p.usuario_id == request.user.pk) or not p.comprobante:
        raise Http404
    return FileResponse(p.comprobante.open('rb'), filename=p.comprobante.name.rsplit('/', 1)[-1])


@staff_requerido
def revisar(request):
    if request.method == 'POST':
        p = get_object_or_404(Pago, pk=request.POST.get('pago') or 0)
        if request.POST.get('decision') == 'aprobar':
            P.aprobar(p, request.user, request.POST.get('medio') or p.medio)
            messages.success(request, f'Aprobado {p.referencia}: {P.describir(p)}')
        elif request.POST.get('decision') == 'rechazar':
            P.rechazar(p, request.user, (request.POST.get('nota') or '').strip())
            messages.info(request, f'Rechazado {p.referencia}.')
        return redirect('salon_digital:revisar_pagos')
    base = Pago.objects.select_related('usuario__cuenta_salon')
    return render(request, 'salon_digital/pagos_revisar.html', {
        'por_revisar': base.filter(estado='revision'),
        'recientes': base.exclude(estado='revision').exclude(estado='pendiente', forma='comprobante')[:40],
    })


def hay_por_revisar():
    return Pago.objects.filter(estado='revision').count()
