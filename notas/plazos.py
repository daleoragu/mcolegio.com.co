"""Plazos de los periodos que se cierran solos a una fecha y hora.

El administrador abre o cierra con un clic los plazos de cada periodo (ingreso
de notas, reporte parcial, nivelaciones). Con «Programar cierre» deja además
una fecha y hora: al llegar, el plazo se cierra sin que nadie tenga que entrar.

No hace falta una tarea programada en el servidor: en cada visita al colegio
(a lo sumo una vez por minuto) se cierran los plazos vencidos. Como para
escribir notas hay que entrar a la plataforma, el plazo ya está cerrado antes
de que alguien intente usarlo.
"""
from django.core.cache import cache
from django.urls import reverse
from django.utils import timezone

# clave: (campo del interruptor, campo del cierre, nombre, a dónde lleva el aviso)
PLAZOS = {
    'notas': ('esta_activo', 'cierre_notas', 'Ingreso de Notas', 'notas:ingresar_notas_periodo'),
    'reporte': ('reporte_parcial_activo', 'cierre_reporte_parcial', 'Reporte Parcial', 'notas:reporte_parcial'),
    'nivelaciones': ('nivelaciones_activas', 'cierre_nivelaciones', 'Nivelaciones', 'notas:plan_mejoramiento'),
}


def avisar_docentes(colegio, mensaje, url_nombre):
    from django.contrib.auth.models import User
    from .models import Notificacion
    try:
        url = reverse(url_nombre)
    except Exception:
        url = '#'
    Notificacion.objects.bulk_create([
        Notificacion(destinatario=u, mensaje=mensaje[:255], tipo='PERIODO', url=url, colegio=colegio)
        for u in User.objects.filter(docente__colegio=colegio).distinct()])


def aplicar_cierres(colegio, ahora=None):
    """Cierra los plazos vencidos del colegio. Devuelve cuántos cerró."""
    from .models import PeriodoAcademico
    ahora = ahora or timezone.now()
    cerrados = 0
    for interruptor, cierre, nombre, url in PLAZOS.values():
        vencidos = list(PeriodoAcademico.objects.filter(colegio=colegio, **{f'{cierre}__lte': ahora}))
        if not vencidos:
            continue
        PeriodoAcademico.objects.filter(id__in=[p.id for p in vencidos]).update(**{interruptor: False, cierre: None})
        for p in vencidos:
            if getattr(p, interruptor):
                avisar_docentes(colegio, f'Se cerró el plazo de {nombre} del {p}, como estaba programado.', url)
                if interruptor == 'reporte_parcial_activo':
                    from .reporte_aviso import avisar_estudiantes_al_cierre
                    avisar_estudiantes_al_cierre(p)
                cerrados += 1
    return cerrados


def aplicar_si_toca(colegio):
    """Lo llama el middleware: revisa a lo sumo una vez por minuto por colegio."""
    if colegio is None:
        return
    clave = f'plazos-revisados-{colegio.id}'
    if cache.get(clave):
        return
    cache.set(clave, True, 60)
    aplicar_cierres(colegio)
