"""Planes y pagos de Mi Salón Virtual en un solo lugar.

Dos formas de pagar:
  · En línea con Wompi (tarjeta crédito o débito, PSE, Nequi, botón Bancolombia…): se activa solo.
  · Llave Bre-B, Nequi o transferencia: el docente paga, sube la foto del comprobante y un administrador
    lo aprueba con un clic; al aprobarlo el plan o el saldo se activan solos.

Variables en DigitalOcean (además de las de Wompi, ver materiales/wompi.py):
    SALON_PAGO_TITULAR   a nombre de quién sale la cuenta (ej.: «mcolegio · David …»)
    SALON_LLAVE_BREB     la llave Bre-B (celular, correo, documento o alfanumérica)
    SALON_NEQUI          número de Nequi
    SALON_CUENTA_BANCO   texto de la cuenta para transferencia (ej.: «Bancolombia ahorros 123-456789-00»)
"""
import os
import secrets

from django.db import transaction
from django.utils import timezone

from .models import PLANES, PRECIOS, Cuenta, Pago


def plan_de_concepto(concepto):
    """'premium_anio' → ('premium', 'anio', precio, días); None si no es un plan."""
    plan, _, periodo = (concepto or '').partition('_')
    if (plan, periodo) in PRECIOS:
        return (plan, periodo) + PRECIOS[(plan, periodo)]
    return None


def recargas():
    from materiales.creditos import RECARGAS
    return RECARGAS


def datos_cuenta():
    """Lo que se muestra para pagar con comprobante (solo lo que esté configurado)."""
    return {k: v for k, v in (('titular', os.getenv('SALON_PAGO_TITULAR', '')), ('llave', os.getenv('SALON_LLAVE_BREB', '')),
                              ('nequi', os.getenv('SALON_NEQUI', '')), ('banco', os.getenv('SALON_CUENTA_BANCO', ''))) if v}


def en_linea():
    from materiales import wompi
    return wompi.configurado()


def valor(concepto, monto=None):
    """(monto, bono) del concepto, o None si no es válido."""
    p = plan_de_concepto(concepto)
    if p:
        return p[2], 0
    if concepto == 'recarga' and monto in recargas():
        return monto, recargas()[monto]
    return None


def nuevo(usuario, concepto, monto, bono, forma):
    return Pago.objects.create(usuario=usuario, concepto=concepto, monto=monto, bono=bono, forma=forma,
                               referencia=f'SD{usuario.pk}-{secrets.token_hex(5).upper()}')


def _activar(pago):
    p = plan_de_concepto(pago.concepto)
    if p:
        cuenta = Cuenta.objects.filter(usuario=pago.usuario).first()
        if cuenta is not None:
            cuenta.extender(p[0], p[3])
    else:
        from materiales import creditos
        creditos.abonar(pago.usuario, pago.monto + pago.bono, 'recarga',
                        f'Recarga {pago.referencia}' + (f' + bono ${pago.bono:,}'.replace(',', '.') if pago.bono else ''))


def _avisar(usuario, texto, url='/salon_digital/pagos/'):
    from notas.models import Notificacion
    Notificacion.objects.bulk_create([Notificacion(colegio=None, destinatario=usuario, tipo='GENERAL', url=url, mensaje=texto[:255])])


def describir(pago):
    p = plan_de_concepto(pago.concepto)
    if p:
        c = Cuenta.objects.filter(usuario=pago.usuario).first()
        hasta = f' hasta el {c.vence_en:%d/%m/%Y}' if c and c.vence_en else ''
        return f'Plan {PLANES[p[0]]["nombre"]} activo{hasta}.'
    return f'Recarga aprobada: ${pago.monto + pago.bono:,} en su saldo.'.replace(',', '.')


@transaction.atomic
def aprobar(pago, por=None, medio=''):
    """Aprueba una sola vez y activa el plan o el saldo."""
    pago = Pago.objects.select_for_update().get(pk=pago.pk)
    if pago.estado == 'aprobado':
        return pago
    pago.estado = 'aprobado'
    pago.resuelto = timezone.now()
    pago.revisado_por = por
    if medio:
        pago.medio = medio[:30]
    pago.save()
    _activar(pago)
    _avisar(pago.usuario, f'Pago aprobado ({pago.referencia}). {describir(pago)}')
    return pago


@transaction.atomic
def rechazar(pago, por=None, nota=''):
    pago = Pago.objects.select_for_update().get(pk=pago.pk)
    if pago.estado == 'aprobado':
        return pago
    pago.estado, pago.resuelto, pago.revisado_por = 'rechazado', timezone.now(), por
    pago.nota = (nota or 'No pudimos confirmar el pago con ese comprobante.')[:255]
    pago.save()
    if pago.forma == 'comprobante':
        _avisar(pago.usuario, f'No pudimos confirmar el pago {pago.referencia}: {pago.nota}')
    return pago


def aplicar_wompi(referencia, estado, transaccion_id='', centavos=None, metodo=''):
    """Resultado de Wompi para un pago de aquí (referencias SD…). Devuelve el pago o None."""
    pago = Pago.objects.filter(referencia=referencia, forma='linea').first()
    if pago is None or pago.estado in ('aprobado', 'rechazado'):
        return pago
    pago.transaccion = str(transaccion_id)[:60]
    pago.save(update_fields=['transaccion'])
    if estado == 'APPROVED':
        if centavos is not None and int(centavos) != pago.monto * 100:
            return pago                      # el monto no coincide: no se activa
        return aprobar(pago, medio=str(metodo))
    if estado in ('DECLINED', 'VOIDED', 'ERROR'):
        Pago.objects.filter(pk=pago.pk).update(estado='rechazado', resuelto=timezone.now(), medio=str(metodo)[:30])
        pago.refresh_from_db()
    return pago
