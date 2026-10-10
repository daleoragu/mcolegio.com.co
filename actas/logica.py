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


def _nombres_anteriores(acta):
    """{cargo: nombre} de las actas anteriores del colegio: los representantes se escriben una vez."""
    nombres = {}
    for previa in (Acta.objects.filter(colegio=acta.colegio).exclude(id=acta.id)
                   .order_by('-ano', '-numero').only('asistencia')[:30]):
        for a in previa.lista_asistentes():
            if a['cargo'] and a['nombre'] and a['cargo'] not in nombres:
                nombres[a['cargo']] = a['nombre']
    return nombres


def asistentes_sugeridos(acta, cursos_ids=None):
    """[{'nombre', 'cargo', 'asistio': False}] para marcar con X.

    Comisión: por cada grado, el director de grado de cada curso, un
    representante de los padres y uno de los estudiantes. Antes, los directivos.
    Acta libre: los directivos. El nombre de un representante se toma de la
    última acta en que se escribió para ese mismo cargo.
    """
    from notas.models import AdministradorColegio, Curso
    previos = _nombres_anteriores(acta)
    vistos, salida = set(), []

    def poner(nombre, cargo):
        clave = (nombre.lower(), cargo.lower())
        if clave in vistos:
            return
        vistos.add(clave)
        salida.append({'nombre': nombre or previos.get(cargo, ''), 'cargo': cargo, 'asistio': False})

    for adm in (AdministradorColegio.objects.filter(colegio=acta.colegio, activo=True)
                .select_related('user').order_by('id')):
        poner(adm.user.get_full_name() or adm.user.username, adm.get_cargo_display())
    if acta.es_comision:
        cursos = (Curso.objects.filter(colegio=acta.colegio, id__in=cursos_ids) if cursos_ids is not None
                  else acta.cursos.all())
        cursos = list(cursos.select_related('director_grado__user').order_by('grado', 'nombre'))
        por_grado = {}
        for c in cursos:
            por_grado.setdefault((c.grado if c.grado is not None else 99,
                                  c.get_grado_display() if c.grado is not None else ''), []).append(c)
        for (_, nombre_grado), lista in sorted(por_grado.items()):
            for c in lista:
                if c.director_grado_id:
                    poner(c.director_grado.user.get_full_name() or c.director_grado.user.username,
                          f'Director(a) de grado {c.nombre}')
                else:
                    poner('', f'Director(a) de grado {c.nombre}')
            sufijo = f' — {nombre_grado}' if nombre_grado else ''
            poner('', f'Representante de padres{sufijo}')
            poner('', f'Representante de estudiantes{sufijo}')
    return salida


def todos_los_docentes(colegio):
    """[{'nombre', 'cargo': 'Docente', 'asistio': False}] de todos los docentes activos, por apellido.

    Para las reuniones de profesores: el administrador los trae de una vez y
    después marca quién asistió.
    """
    from notas.models import Docente
    salida = []
    for d in (Docente.objects.filter(colegio=colegio, user__is_active=True).select_related('user')
              .order_by('user__last_name', 'user__first_name')):
        u = d.user
        nombre = f'{u.first_name} {u.last_name}'.strip() or u.username
        salida.append({'nombre': nombre, 'cargo': 'Docente', 'asistio': False})
    return salida


def firmantes(acta):
    """Quiénes firman en el estilo de líneas: los que asistieron; si no se marcó a nadie, todos."""
    lista = acta.lista_asistentes()
    marcados = [a for a in lista if a['asistio']]
    return marcados or lista
