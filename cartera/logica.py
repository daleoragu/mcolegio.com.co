import calendar
import datetime

from django.db import transaction
from django.db.models import Sum
from django.utils import timezone

from notas.models import Estudiante

from .models import MESES, Aplicacion, Beca, Cargo, Concepto, ConfiguracionCartera, Pago


def pesos(valor):
    return '$' + f'{int(valor or 0):,}'.replace(',', '.')


def _vence(ano, mes, dia):
    return datetime.date(ano, mes, min(dia, calendar.monthrange(ano, mes)[1]))


def _descuento(estudiante, concepto, valor):
    pct = 0
    for b in Beca.objects.filter(estudiante=estudiante):
        if b.concepto_id in (None, concepto.id):
            pct = max(pct, b.porcentaje)
    return round(valor * min(pct, 100) / 100)


def generar_cargos(colegio, ano, meses=None, estudiantes=None):
    """Crea lo que falte por cobrar en el año (o en los meses dados). No duplica. Devuelve cuántos creó."""
    conf = ConfiguracionCartera.de(colegio)
    meses = meses or conf.meses_pension
    if estudiantes is None:
        estudiantes = Estudiante.objects.filter(colegio=colegio, is_active=True, curso__isnull=False).select_related('curso')
    conceptos = list(Concepto.objects.filter(colegio=colegio, activo=True).prefetch_related('valores_grado'))
    creados = 0
    for est in estudiantes:
        grado = est.curso.grado if est.curso_id else None
        for c in conceptos:
            valor = c.valor_para(grado)
            if not valor:
                continue
            lista = [m for m in meses if 1 <= int(m) <= 12] if c.tipo == 'MENSUAL' else [c.mes_unico]
            for m in lista:
                m = int(m)
                desc = f'{c.nombre} {MESES[m - 1].lower()} {ano}' if c.tipo == 'MENSUAL' else f'{c.nombre} {ano}'
                _, nuevo = Cargo.objects.get_or_create(
                    estudiante=est, concepto=c, ano=ano, mes=m,
                    defaults={'colegio': colegio, 'descripcion': desc[:120], 'valor': valor,
                              'descuento': _descuento(est, c, valor), 'vence': _vence(ano, m, conf.dia_vencimiento)})
                creados += nuevo
        aplicar_saldo_a_favor(est)
    return creados


def _abiertos(estudiante):
    cargos = [c for c in Cargo.objects.filter(estudiante=estudiante).prefetch_related('aplicaciones__pago')]
    salida = []
    for c in cargos:
        pagado = sum(a.valor for a in c.aplicaciones.all() if not a.pago.anulado)
        saldo = max(0, c.neto - pagado)
        if saldo:
            salida.append((c, saldo))
    salida.sort(key=lambda x: (x[0].vence, x[0].id))
    return salida


def _aplicar(pago, monto):
    """Reparte `monto` del pago entre los cargos abiertos, del más viejo al más nuevo."""
    for cargo, saldo in _abiertos(pago.estudiante):
        if monto <= 0:
            break
        parte = min(saldo, monto)
        Aplicacion.objects.create(pago=pago, cargo=cargo, valor=parte)
        monto -= parte
    return monto


def saldo_a_favor(estudiante):
    pagado = Pago.objects.filter(estudiante=estudiante, anulado=False).aggregate(t=Sum('valor'))['t'] or 0
    aplicado = Aplicacion.objects.filter(pago__estudiante=estudiante, pago__anulado=False).aggregate(t=Sum('valor'))['t'] or 0
    return max(0, pagado - aplicado)


def aplicar_saldo_a_favor(estudiante):
    """Lo pagado de más se usa en los cargos nuevos (por ejemplo, al generar el mes siguiente)."""
    if not saldo_a_favor(estudiante):
        return
    for pago in Pago.objects.filter(estudiante=estudiante, anulado=False).order_by('fecha', 'numero'):
        libre = pago.valor - (pago.aplicaciones.aggregate(t=Sum('valor'))['t'] or 0)
        if libre > 0:
            _aplicar(pago, libre)


@transaction.atomic
def registrar_pago(estudiante, valor, fecha=None, medio='EFECTIVO', referencia='', observacion='', usuario=None):
    conf = ConfiguracionCartera.objects.select_for_update().get(pk=ConfiguracionCartera.de(estudiante.colegio).pk)
    conf.ultimo_recibo += 1
    conf.save(update_fields=['ultimo_recibo'])
    pago = Pago.objects.create(colegio=estudiante.colegio, estudiante=estudiante, numero=conf.ultimo_recibo,
                               fecha=fecha or timezone.localdate(), valor=int(valor), medio=medio,
                               referencia=referencia[:80], observacion=observacion[:200], registrado_por=usuario)
    _aplicar(pago, pago.valor)
    return pago


@transaction.atomic
def anular_pago(pago, motivo=''):
    pago.anulado = True
    pago.motivo_anulacion = motivo[:200]
    pago.save(update_fields=['anulado', 'motivo_anulacion'])
    pago.aplicaciones.all().delete()
    aplicar_saldo_a_favor(pago.estudiante)


def estado(estudiante, hoy=None):
    hoy = hoy or timezone.localdate()
    cargos = list(Cargo.objects.filter(estudiante=estudiante).prefetch_related('aplicaciones__pago').order_by('vence', 'id'))
    filas, total, pagado_total, vencido, primero_vencido = [], 0, 0, 0, None
    for c in cargos:
        pagado = sum(a.valor for a in c.aplicaciones.all() if not a.pago.anulado)
        saldo = max(0, c.neto - pagado)
        en_mora = saldo > 0 and c.vence < hoy
        if en_mora:
            vencido += saldo
            primero_vencido = primero_vencido or c.vence
        total += c.neto
        pagado_total += pagado
        filas.append({'c': c, 'pagado': pagado, 'saldo': saldo, 'en_mora': en_mora})
    saldo = total - pagado_total
    return {'filas': filas, 'total': total, 'pagado': pagado_total, 'saldo': saldo, 'vencido': vencido,
            'a_favor': saldo_a_favor(estudiante), 'dias_mora': (hoy - primero_vencido).days if primero_vencido else 0,
            'pagos': list(estudiante.pagos.all())}


def tiene_paz_y_salvo(estudiante):
    return estado(estudiante)['vencido'] == 0


def resumen(colegio, curso_id=None, solo_mora=False, hoy=None):
    hoy = hoy or timezone.localdate()
    ests = Estudiante.objects.filter(colegio=colegio, is_active=True).select_related('user', 'curso')
    if curso_id:
        ests = ests.filter(curso_id=curso_id)
    filas = []
    tot = {'saldo': 0, 'vencido': 0, 'morosos': 0}
    for e in ests.order_by('curso__nombre', 'user__last_name', 'user__first_name'):
        st = estado(e, hoy)
        if solo_mora and not st['vencido']:
            continue
        filas.append({'e': e, 'saldo': st['saldo'], 'vencido': st['vencido'], 'dias': st['dias_mora']})
        tot['saldo'] += st['saldo']
        tot['vencido'] += st['vencido']
        tot['morosos'] += 1 if st['vencido'] else 0
    inicio_mes = hoy.replace(day=1)
    tot['recaudo_mes'] = (Pago.objects.filter(colegio=colegio, anulado=False, fecha__gte=inicio_mes)
                          .aggregate(t=Sum('valor'))['t'] or 0)
    return filas, tot


def texto_aviso(estudiante, st, url=''):
    nombre = f'{estudiante.user.first_name} {estudiante.user.last_name}'.strip()
    texto = (f'{estudiante.colegio.nombre}: le recordamos que el estado de cuenta de {nombre} tiene un saldo vencido de '
             f'{pesos(st["vencido"])}.')
    conf = ConfiguracionCartera.de(estudiante.colegio)
    if conf.datos_pago.strip():
        texto += f'\nPuede pagar así: {" ".join(conf.datos_pago.split())}'
    texto += '\nSi ya pagó, por favor ignore este mensaje o envíenos el comprobante.'
    if url:
        texto += f'\nConsulte el estado de cuenta en la plataforma: {url}'
    return texto


def bloqueo_certificados(estudiante):
    """El saldo vencido si el colegio exige paz y salvo para los certificados; 0 si no bloquea."""
    from notas.modulos import esta_activo
    colegio = estudiante.colegio
    if not esta_activo(colegio, 'cartera'):
        return 0
    conf = ConfiguracionCartera.objects.filter(colegio=colegio).first()
    if not conf or not conf.exigir_paz_y_salvo:
        return 0
    return estado(estudiante)['vencido']
