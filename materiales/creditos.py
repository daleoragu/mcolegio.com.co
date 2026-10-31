"""Créditos de IA, saldo prepago y nube ampliada de cada docente.

Cada docente tiene bolsas que no se acumulan:
  · Recarga diaria: se llena cada día; lo que no se usa se pierde. Se gasta primero.
  · Bolsa del mes: se llena el día 1; lo que sobra no pasa al otro mes.
  · Extra (paquetes comprados y regalos por compartir): dura hasta fin de mes.
  · Saldo en pesos: no vence; cada crédito cuesta PESOS_POR_CREDITO y solo se usa si el docente lo acepta.
Un uso sale entero de una sola bolsa. Si la IA falla, el uso se devuelve.
"""
from datetime import timedelta
from decimal import Decimal

from django.db import transaction
from django.db.models import Sum
from django.utils import timezone

from .models import CuentaIA, MovimientoIA

PESOS_POR_CREDITO = 20
# (créditos diarios, créditos del mes)
CUPOS = {
    'prueba': (0, 30),           # 30 en total durante la prueba
    'individual': (3, 0),        # planes de hoy: 3 diarios para probarla
    'individual_ia': (8, 200),
    'premium': (5, 150),         # colegio Premium, por docente
    'colegio': (3, 0),
}
PAQUETE = {'creditos': 300, 'pesos': 5000}
PLAN_IA = {'pesos': 6000, 'dias': 30}            # $16.000 − $10.000 del plan de hoy
NUBE = {10: 3000, 50: 10000}                     # GB extra por 30 días → pesos
RECARGAS = {10000: 0, 20000: 1000, 50000: 5000}  # monto → bono
REGALO_COMPARTIR = 20
# Precio de la IA por millón de tokens (Claude Haiku 4.5), para el panel de costos.
USD_ENTRADA, USD_SALIDA = Decimal('1'), Decimal('5')


class SinCreditos(Exception):
    def __init__(self, estado, costo):
        super().__init__('Sin créditos')
        self.estado = estado
        self.costo = costo


def cuenta(usuario):
    c, _ = CuentaIA.objects.get_or_create(usuario=usuario)
    return c


def plan_de(usuario, colegio):
    hoy = timezone.localdate()
    if colegio is not None:
        from notas.modulos import esta_activo
        return 'premium' if esta_activo(colegio, 'salon') else 'colegio'
    c = CuentaIA.objects.filter(usuario=usuario).first()
    if c and c.ia_hasta and c.ia_hasta >= hoy:
        return 'individual_ia'
    cuenta_salon = getattr(usuario, 'cuenta_salon', None)
    if cuenta_salon is not None and cuenta_salon.plan == 'prueba':
        return 'prueba'
    return 'individual'


def _inicio_dia():
    ahora = timezone.localtime()
    return ahora.replace(hour=0, minute=0, second=0, microsecond=0)


def _inicio_mes():
    return _inicio_dia().replace(day=1)


def _usados(usuario, bolsa, desde):
    return MovimientoIA.objects.filter(usuario=usuario, tipo='uso', bolsa=bolsa, devuelto=False,
                                       creado__gte=desde).aggregate(t=Sum('creditos'))['t'] or 0


def estado(usuario, colegio):
    """Lo que muestra el medidor."""
    plan = plan_de(usuario, colegio)
    diario, mensual = CUPOS[plan]
    mes = _inicio_mes()
    ganados = MovimientoIA.objects.filter(usuario=usuario, tipo__in=('paquete', 'regalo'), creado__gte=mes) \
        .aggregate(t=Sum('creditos'))['t'] or 0
    c = cuenta(usuario)
    gastado_saldo = -(MovimientoIA.objects.filter(usuario=usuario, tipo='uso', bolsa='saldo', devuelto=False,
                                                  creado__gte=mes).aggregate(t=Sum('pesos'))['t'] or 0)
    hoy = timezone.localdate()
    manana = hoy + timedelta(days=1)
    proximo_mes = (hoy.replace(day=1) + timedelta(days=32)).replace(day=1)
    return {
        'plan': plan,
        'dia': max(0, diario - _usados(usuario, 'dia', _inicio_dia())), 'dia_total': diario,
        'mes': max(0, mensual - _usados(usuario, 'mes', mes)), 'mes_total': mensual,
        'extra': max(0, ganados - _usados(usuario, 'extra', mes)),
        'saldo': c.saldo, 'saldo_creditos': c.saldo // PESOS_POR_CREDITO,
        'sin_preguntar': c.saldo_sin_preguntar, 'tope_mes': c.tope_mes, 'gastado_saldo_mes': gastado_saldo,
        'renueva_dia': manana, 'renueva_mes': proximo_mes,
        'ia_hasta': c.ia_hasta, 'nube_extra_gb': c.nube_extra_gb if c.nube_extra_hasta and c.nube_extra_hasta >= hoy else 0,
        'nube_extra_hasta': c.nube_extra_hasta,
    }


def resumen(est):
    """Créditos disponibles sin tocar el saldo."""
    return est['dia'] + est['mes'] + est['extra']


@transaction.atomic
def cobrar(usuario, colegio, accion, creditos, usar_saldo=False, detalle=''):
    """Saca los créditos de una sola bolsa (diaria, mes, extra) o, si el docente acepta, del saldo.
    Devuelve el movimiento; si no alcanza, SinCreditos con el estado del medidor."""
    c = CuentaIA.objects.select_for_update().get_or_create(usuario=usuario)[0]
    est = estado(usuario, colegio)
    for bolsa in ('dia', 'mes', 'extra'):
        if est[bolsa] >= creditos:
            return MovimientoIA.objects.create(usuario=usuario, colegio=colegio, tipo='uso', accion=accion, bolsa=bolsa,
                                               creditos=creditos, detalle=detalle[:200])
    pesos = creditos * PESOS_POR_CREDITO
    dentro_del_tope = c.saldo_sin_preguntar and est['gastado_saldo_mes'] + pesos <= c.tope_mes
    if c.saldo >= pesos and (usar_saldo or dentro_del_tope):
        c.saldo -= pesos
        c.save(update_fields=['saldo'])
        return MovimientoIA.objects.create(usuario=usuario, colegio=colegio, tipo='uso', accion=accion, bolsa='saldo',
                                           creditos=creditos, pesos=-pesos, detalle=detalle[:200])
    raise SinCreditos(est, creditos)


@transaction.atomic
def devolver(mov, motivo=''):
    """La IA falló: el uso no cuenta y, si salió del saldo, vuelve la plata."""
    mov = MovimientoIA.objects.select_for_update().get(pk=mov.pk)
    if mov.devuelto:
        return
    mov.devuelto = True
    mov.detalle = (f'{mov.detalle} · devuelto: {motivo}' if motivo else mov.detalle)[:200]
    mov.save(update_fields=['devuelto', 'detalle'])
    if mov.bolsa == 'saldo' and mov.pesos:
        c = CuentaIA.objects.select_for_update().get(usuario=mov.usuario)
        c.saldo += -mov.pesos
        c.save(update_fields=['saldo'])


def anotar_consumo(mov, tokens_entrada, tokens_salida):
    mov.tokens_entrada = tokens_entrada
    mov.tokens_salida = tokens_salida
    mov.costo_usd = (Decimal(tokens_entrada) * USD_ENTRADA + Decimal(tokens_salida) * USD_SALIDA) / Decimal(1_000_000)
    mov.save(update_fields=['tokens_entrada', 'tokens_salida', 'costo_usd'])


@transaction.atomic
def gastar_saldo(usuario, pesos, tipo, detalle, colegio=None, creditos=0):
    """Paga con el saldo un paquete, el plan con IA o la nube. Devuelve False si no alcanza."""
    c = CuentaIA.objects.select_for_update().get_or_create(usuario=usuario)[0]
    if c.saldo < pesos:
        return False
    c.saldo -= pesos
    hoy = timezone.localdate()
    if tipo == 'plan_ia':
        c.ia_hasta = max(c.ia_hasta or hoy, hoy) + timedelta(days=PLAN_IA['dias'])
    c.save()
    MovimientoIA.objects.create(usuario=usuario, colegio=colegio, tipo=tipo, creditos=creditos, pesos=-pesos,
                                detalle=detalle[:200])
    return True


@transaction.atomic
def ampliar_nube(usuario, gb):
    pesos = NUBE.get(gb)
    if pesos is None:
        return False
    c = CuentaIA.objects.select_for_update().get_or_create(usuario=usuario)[0]
    if c.saldo < pesos:
        return False
    hoy = timezone.localdate()
    vigente = c.nube_extra_hasta and c.nube_extra_hasta >= hoy
    c.saldo -= pesos
    # Si ya tiene una ampliación vigente del mismo tamaño se alarga; si cambia de tamaño, empieza hoy.
    desde = c.nube_extra_hasta if vigente and c.nube_extra_gb == gb else hoy
    c.nube_extra_gb = gb
    c.nube_extra_hasta = desde + timedelta(days=30)
    c.save()
    MovimientoIA.objects.create(usuario=usuario, tipo='nube', pesos=-pesos, detalle=f'Nube +{gb} GB por 30 días')
    return True


@transaction.atomic
def abonar(usuario, pesos, tipo='recarga', detalle=''):
    c = CuentaIA.objects.select_for_update().get_or_create(usuario=usuario)[0]
    c.saldo = max(0, c.saldo + pesos)
    c.save(update_fields=['saldo'])
    MovimientoIA.objects.create(usuario=usuario, tipo=tipo, pesos=pesos, detalle=detalle[:200])


def regalar(usuario, creditos, detalle):
    MovimientoIA.objects.create(usuario=usuario, tipo='regalo', bolsa='extra', creditos=creditos, detalle=detalle[:200])


def nube_extra_bytes(usuario):
    c = CuentaIA.objects.filter(usuario=usuario).first()
    if c and c.nube_extra_gb and c.nube_extra_hasta and c.nube_extra_hasta >= timezone.localdate():
        return c.nube_extra_gb * 1024 * 1024 * 1024
    return 0
