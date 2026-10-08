# -*- coding: utf-8 -*-
"""El informe de la comisión de evaluación y promoción.

Usa la misma cuenta de las alertas tempranas (notas/alertas.py), que a su vez
usa la del boletín: la nivelación reemplaza la nota del periodo y el acumulado
es la definitiva anual ponderada hasta el periodo de la reunión.
"""
from django.db.models import Count, Max, Q
from django.utils import timezone

from notas.alertas import alertas_de_curso, periodos_hasta
from notas.boletin.ponderacion import nota_aprobacion
from notas.models import RegistroObservador

from .models import Acta


def siguiente_numero(colegio, ano):
    ultimo = Acta.objects.filter(colegio=colegio, ano=ano).aggregate(m=Max('numero'))['m']
    return (ultimo or 0) + 1


def _rango_observador(acta):
    """Fechas en que se cuentan las anotaciones: el periodo, o desde el comienzo del año hasta él."""
    p = acta.periodo
    if acta.alcance == Acta.ACUMULADO:
        periodos = periodos_hasta(acta.colegio, p.ano_lectivo, p)
        return (periodos[0].fecha_inicio if periodos else p.fecha_inicio), p.fecha_fin
    return p.fecha_inicio, p.fecha_fin


def _anotaciones(acta, estudiantes):
    desde, hasta = _rango_observador(acta)
    filas = (RegistroObservador.objects
             .filter(estudiante__in=estudiantes, fecha_suceso__gte=desde, fecha_suceso__lte=hasta)
             .filter(Q(subtipo__isnull=True) | ~Q(subtipo='POSITIVA'))
             .values('estudiante_id').annotate(n=Count('id')))
    return {f['estudiante_id']: f['n'] for f in filas}


def _fmt(nota):
    return None if nota is None else f'{nota:.1f}'


def calcular_informe(acta):
    """Diccionario listo para guardar en JSON y para dibujar.

    filas: solo estudiantes con al menos una asignatura pendiente, de más a
    menos pendientes; a igual número, primero el de más anotaciones (si se
    muestran) y luego por curso y apellido.
    """
    colegio, periodo = acta.colegio, acta.periodo
    vacio = {'filas': [], 'cursos': [], 'analizados': 0, 'con_pendientes': 0}
    if periodo is None:
        return vacio
    ano = periodo.ano_lectivo
    cursos = list(acta.cursos.all().order_by('grado', 'nombre'))
    acumulado = acta.alcance == Acta.ACUMULADO
    filas, resumen_cursos, analizados = [], [], 0
    for curso in cursos:
        datos = alertas_de_curso(colegio, curso, ano, periodo)
        analizados += len(datos)
        con = 0
        for d in datos:
            if acumulado:
                pend = [{'materia': p['materia'], 'nota': _fmt(p['acumulada'])} for p in d['perdidas']]
            else:
                pend = [{'materia': p['materia'], 'nota': _fmt(p['nota'])} for p in d['perdidas_periodo_lista']]
            if not pend:
                continue
            con += 1
            u = d['estudiante'].user
            filas.append({'id': d['estudiante'].id, 'estudiante': f'{u.last_name} {u.first_name}'.strip().upper(),
                          'curso': curso.nombre, 'grado': curso.grado if curso.grado is not None else 99, 'n': len(pend), 'asignaturas': pend})
        resumen_cursos.append({'curso': curso.nombre, 'analizados': len(datos), 'con_pendientes': con})

    if acta.mostrar_observador and filas:
        conteo = _anotaciones(acta, [f['id'] for f in filas])
        for f in filas:
            f['anotaciones'] = conteo.get(f['id'], 0)
    filas.sort(key=lambda f: (-f['n'], -f.get('anotaciones', 0), f['grado'], f['curso'], f['estudiante']))
    return {
        'filas': filas, 'cursos': resumen_cursos, 'analizados': analizados, 'con_pendientes': len(filas),
        'periodo': str(periodo), 'alcance': acta.get_alcance_display(), 'acumulado': acumulado,
        'aprobacion': f'{nota_aprobacion(colegio):.1f}', 'observador': acta.mostrar_observador,
        'generado': timezone.localtime().strftime('%d/%m/%Y %I:%M %p'),
    }


def informe_de(acta):
    """El congelado si el acta está cerrada; si no, calculado ahora."""
    if acta.cerrada and acta.informe is not None:
        return acta.informe
    return calcular_informe(acta) if acta.es_comision else None


def cerrar(acta):
    if acta.es_comision:
        acta.informe = calcular_informe(acta)
    acta.estado = Acta.CERRADA
    acta.cerrada_en = timezone.now()
    acta.save()


def reabrir(acta):
    acta.estado = Acta.BORRADOR
    acta.cerrada_en = None
    acta.informe = None
    acta.save()


def asistentes_sugeridos(acta, cursos_ids=None):
    """Directivos del colegio y docentes de los cursos (director de grupo primero), sin repetir."""
    from notas.models import AdministradorColegio, AsignacionDocente
    vistos, salida = set(), []

    def poner(user, cargo):
        if user and user.id not in vistos:
            vistos.add(user.id)
            salida.append(f'{user.get_full_name() or user.username} — {cargo}')

    for adm in (AdministradorColegio.objects.filter(colegio=acta.colegio, activo=True)
                .select_related('user').order_by('id')):
        poner(adm.user, adm.get_cargo_display() if hasattr(adm, 'get_cargo_display') else 'Directivo')
    if acta.es_comision:
        from notas.models import Curso
        cursos = (Curso.objects.filter(colegio=acta.colegio, id__in=cursos_ids) if cursos_ids is not None
                  else acta.cursos.all())
        cursos = list(cursos.select_related('director_grado__user'))
        for c in cursos:
            if c.director_grado_id:
                poner(c.director_grado.user, f'Director(a) de grupo {c.nombre}')
        for a in (AsignacionDocente.objects.filter(colegio=acta.colegio, curso__in=cursos)
                  .select_related('docente__user').order_by('docente__user__last_name')):
            if a.docente_id:
                poner(a.docente.user, 'Docente')
    return '\n'.join(salida)
