"""Recargas de saldo con Wompi (Web Checkout).

Variables en DigitalOcean (nunca en el código):
    WOMPI_PUBLIC_KEY        llave pública (pub_prod_… o pub_test_…)
    WOMPI_INTEGRITY_SECRET  secreto de integridad (firma del checkout)
    WOMPI_EVENTS_SECRET     secreto de eventos (firma de los avisos de pago)
    WOMPI_ENTORNO           'sandbox' para pruebas; vacío o 'produccion' para cobrar de verdad
URL de eventos que se registra en el panel de Wompi:
    https://mcolegio.com.co/materiales/pagos/wompi/eventos/
"""
import hashlib
import os
from urllib.parse import urlencode

from django.db import transaction
from django.utils import timezone

from . import creditos
from .models import Recarga

CHECKOUT = 'https://checkout.wompi.co/p/'


def configurado():
    return bool(os.getenv('WOMPI_PUBLIC_KEY') and os.getenv('WOMPI_INTEGRITY_SECRET'))


def api():
    return ('https://sandbox.wompi.co/v1' if os.getenv('WOMPI_ENTORNO', '').lower() == 'sandbox'
            else 'https://production.wompi.co/v1')


def firma_integridad(referencia, centavos, moneda='COP'):
    texto = f'{referencia}{centavos}{moneda}{os.getenv("WOMPI_INTEGRITY_SECRET", "")}'
    return hashlib.sha256(texto.encode()).hexdigest()


def url_checkout(recarga, url_regreso, correo=''):
    centavos = recarga.monto * 100
    datos = {
        'public-key': os.getenv('WOMPI_PUBLIC_KEY', ''),
        'currency': 'COP',
        'amount-in-cents': centavos,
        'reference': recarga.referencia,
        'signature:integrity': firma_integridad(recarga.referencia, centavos),
        'redirect-url': url_regreso,
    }
    if correo:
        datos['customer-data:email'] = correo
    return f'{CHECKOUT}?{urlencode(datos)}'


def _valor(datos, ruta):
    actual = datos
    for parte in ruta.split('.'):
        if not isinstance(actual, dict):
            return ''
        actual = actual.get(parte)
    return '' if actual is None else actual


def evento_valido(cuerpo, cabecera=''):
    """Revisa la firma del aviso: valores de signature.properties + timestamp + secreto de eventos, en SHA-256."""
    secreto = os.getenv('WOMPI_EVENTS_SECRET', '')
    try:
        firma = cuerpo['signature']
        texto = ''.join(str(_valor(cuerpo['data'], p)) for p in firma['properties'])
        texto += str(cuerpo['timestamp']) + secreto
    except (KeyError, TypeError):
        return False
    esperado = hashlib.sha256(texto.encode()).hexdigest()
    recibido = (cabecera or firma.get('checksum') or '').lower()
    return bool(secreto) and esperado == recibido


def consultar(transaccion_id):
    """La transacción vista desde Wompi (por si el aviso tarda). None si no se pudo."""
    import requests
    try:
        r = requests.get(f'{api()}/transactions/{transaccion_id}', timeout=15)
        if r.status_code == 200:
            return (r.json() or {}).get('data')
    except Exception:
        return None
    return None


@transaction.atomic
def aplicar(referencia, estado, transaccion_id='', centavos=None, metodo=''):
    """Aplica el resultado una sola vez: aprobada → saldo + bono; rechazada → se marca. Devuelve la recarga."""
    recarga = Recarga.objects.select_for_update().filter(referencia=referencia).first()
    if recarga is None or recarga.estado != 'pendiente':
        return recarga
    if estado == 'APPROVED':
        if centavos is not None and int(centavos) != recarga.monto * 100:
            return recarga            # el monto no coincide: no se abona
        recarga.estado = 'aprobada'
        creditos.abonar(recarga.usuario, recarga.monto + recarga.bono, 'recarga',
                        f'Recarga {recarga.referencia}' + (f' + bono ${recarga.bono:,}'.replace(',', '.') if recarga.bono else ''))
    elif estado in ('DECLINED', 'VOIDED', 'ERROR'):
        recarga.estado = 'rechazada'
    else:
        return recarga
    recarga.transaccion = str(transaccion_id)[:60]
    recarga.metodo = str(metodo)[:30]
    recarga.resuelta = timezone.now()
    recarga.save()
    return recarga
