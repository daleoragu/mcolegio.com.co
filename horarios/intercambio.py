"""Archivos que van y vienen entre la plataforma y la app del generador."""
import hashlib
import hmac
import io
import json
import re
import unicodedata

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from notas.models import AsignacionDocente, Curso, Docente, Materia

from . import nucleo
from .models import Franja, Horario, Jornada, Sesion


def _firma(colegio_id, exportado):
    msg = f'{colegio_id}|{exportado}'.encode()
    return hmac.new(settings.SECRET_KEY.encode(), msg, hashlib.sha256).hexdigest()[:32]


def datos_del_colegio(colegio, con_firma=True):
    """El contenido del archivo de datos (.mch), como diccionario."""
    jornadas = list(Jornada.objects.filter(colegio=colegio).prefetch_related('franjas', 'cursos'))
    cursos_en_jornada = {c.id for j in jornadas for c in j.cursos.all()}
    asignaciones = list(AsignacionDocente.objects.filter(colegio=colegio, curso_id__in=cursos_en_jornada)
                        .select_related('materia', 'docente__user', 'curso'))
    exportado = timezone.now().isoformat(timespec='seconds')
    d = {
        'tipo': nucleo.TIPO_DATOS, 'version': nucleo.VERSION, 'exportado': exportado,
        'colegio': {'id': colegio.id, 'nombre': colegio.nombre},
        'jornadas': [{'id': j.id, 'nombre': j.nombre, 'dias': sorted(j.dias),
                      'cursos': [c.id for c in j.cursos.all()],
                      'franjas': [{'id': f.id, 'orden': f.orden, 'inicio': f.inicio.strftime('%H:%M'),
                                   'fin': f.fin.strftime('%H:%M'), 'descanso': f.descanso, 'etiqueta': f.etiqueta}
                                  for f in sorted(j.franjas.all(), key=lambda x: (x.orden, x.inicio))]}
                     for j in jornadas],
        'cursos': [{'id': c.id, 'nombre': c.nombre, 'grado': c.grado,
                    'sede': c.sede.nombre if c.sede_id else ''}
                   for c in Curso.objects.filter(id__in=cursos_en_jornada).select_related('sede').order_by('orden')],
        'docentes': [{'id': x.id, 'nombre': x.user.get_full_name() or x.user.username}
                     for x in Docente.objects.filter(colegio=colegio).select_related('user')],
        'materias': [{'id': m.id, 'nombre': m.nombre, 'abreviatura': m.abreviatura or ''}
                     for m in Materia.objects.filter(id__in={a.materia_id for a in asignaciones}).order_by('nombre')],
        'asignaciones': [{'id': a.id, 'curso': a.curso_id, 'materia': a.materia_id, 'docente': a.docente_id,
                          'ih': a.intensidad_horaria_semanal} for a in asignaciones],
    }
    if con_firma:
        d['firma'] = _firma(colegio.id, exportado)
    return d


def archivo_datos(colegio):
    return json.dumps(datos_del_colegio(colegio), ensure_ascii=False, indent=1).encode('utf-8')


# ---------------------------------------------------------------------------
# Importar
# ---------------------------------------------------------------------------
def _crear(colegio, nombre, origen, filas, informe):
    """filas: [(asignacion_id, dia, franja_id)] ya validadas."""
    asignaciones = {a.id: a for a in AsignacionDocente.objects.filter(colegio=colegio, id__in={f[0] for f in filas})}
    with transaction.atomic():
        h = Horario.objects.create(colegio=colegio, nombre=nombre[:80], origen=origen, informe=informe)
        Sesion.objects.bulk_create([Sesion(horario=h, curso_id=asignaciones[a].curso_id, asignacion_id=a, dia=d,
                                           franja_id=f) for a, d, f in filas if a in asignaciones],
                                   ignore_conflicts=True)
    return h


def importar_resultado(archivo, colegio):
    """Lee el .mchr de la app. Devuelve (horario, avisos)."""
    texto = archivo.read().decode('utf-8-sig', errors='replace')
    r = nucleo.leer_json(texto, nucleo.TIPO_RESULTADO)
    origen = r.get('origen', {})
    if origen.get('colegio') != colegio.id:
        raise nucleo.ArchivoInvalido('Este horario se hizo con los datos de otro colegio.')
    if origen.get('firma') != _firma(colegio.id, origen.get('exportado')):
        raise nucleo.ArchivoInvalido('El archivo no salió de los datos exportados por esta plataforma.')
    actual = nucleo.Datos(datos_del_colegio(colegio, con_firma=False))
    sesiones, avisos = [], []
    for s in r.get('sesiones', []):
        try:
            a, d, f = int(s['asignacion']), int(s['dia']), int(s['franja'])
        except (KeyError, TypeError, ValueError):
            continue
        if a not in actual.asignaciones or f not in actual.franjas:
            avisos.append('Algunas clases eran de asignaciones u horas que ya no existen y se dejaron por fuera.')
            continue
        sesiones.append({'asignacion': a, 'curso': actual.asignaciones[a]['curso'], 'dia': d, 'franja': f})
    avisos = sorted(set(avisos))
    informe = dict(r.get('informe') or {})
    informe['choques'] = nucleo.revisar(actual, sesiones)
    h = _crear(colegio, r.get('nombre') or 'Horario generado', 'GENERADO',
               [(s['asignacion'], s['dia'], s['franja']) for s in sesiones], informe)
    return h, avisos


def _norm(t):
    t = unicodedata.normalize('NFKD', str(t or '')).encode('ascii', 'ignore').decode().upper()
    return re.sub(r'[^A-Z0-9]', '', t)


DIA_POR_NOMBRE = {'LUNES': 1, 'LU': 1, 'LUN': 1, 'MARTES': 2, 'MA': 2, 'MAR': 2, 'MIERCOLES': 3, 'MI': 3, 'MIE': 3,
                  'JUEVES': 4, 'JU': 4, 'JUE': 4, 'VIERNES': 5, 'VI': 5, 'VIE': 5, 'SABADO': 6, 'SA': 6, 'SAB': 6}


def importar_excel(archivo, colegio):
    """Excel de otra aplicación: columnas CURSO, DIA, HORA, MATERIA (y DOCENTE opcional).

    HORA puede ser el número de la hora de clase (1, 2, 3…) o la hora de inicio (07:00).
    """
    from openpyxl import load_workbook
    try:
        ws = load_workbook(io.BytesIO(archivo.read()), data_only=True, read_only=True).worksheets[0]
    except Exception:
        raise nucleo.ArchivoInvalido('No se pudo abrir el Excel (guárdelo como .xlsx).')
    filas = [list(f) for f in ws.iter_rows(values_only=True)]
    if not filas:
        raise nucleo.ArchivoInvalido('El Excel está vacío.')
    titulos = [_norm(t) for t in filas[0]]
    col = {}
    for clave, nombres in (('curso', ('CURSO', 'GRUPO')), ('dia', ('DIA',)), ('hora', ('HORA', 'BLOQUE', 'FRANJA', 'PERIODO')),
                           ('materia', ('MATERIA', 'ASIGNATURA', 'AREA')), ('docente', ('DOCENTE', 'PROFESOR'))):
        for i, t in enumerate(titulos):
            if t in nombres:
                col[clave] = i
                break
    faltan = [c for c in ('curso', 'dia', 'hora', 'materia') if c not in col]
    if faltan:
        raise nucleo.ArchivoInvalido('Al Excel le faltan las columnas: ' + ', '.join(f.upper() for f in faltan) + '.')
    cursos = {_norm(c.nombre): c for c in Curso.objects.filter(colegio=colegio)}
    jornada_de = {}
    for j in Jornada.objects.filter(colegio=colegio).prefetch_related('franjas', 'cursos'):
        clase = [f for f in sorted(j.franjas.all(), key=lambda x: (x.orden, x.inicio)) if not f.descanso]
        for c in j.cursos.all():
            jornada_de[c.id] = clase
    asig = {}
    for a in AsignacionDocente.objects.filter(colegio=colegio).select_related('materia', 'docente__user'):
        asig.setdefault((a.curso_id, _norm(a.materia.nombre)), []).append(a)
        if a.materia.abreviatura:
            asig.setdefault((a.curso_id, _norm(a.materia.abreviatura)), []).append(a)
    validas, errores = [], []
    for i, f in enumerate(filas[1:], start=2):
        v = lambda k: f[col[k]] if col.get(k) is not None and col[k] < len(f) else None
        if not any(x not in (None, '') for x in f):
            continue
        curso = cursos.get(_norm(v('curso')))
        if not curso:
            errores.append(f'Fila {i}: no hay un curso «{v("curso")}».')
            continue
        dia_txt = str(v('dia') or '').strip()
        dia = int(dia_txt) if dia_txt.isdigit() else DIA_POR_NOMBRE.get(_norm(dia_txt))
        clase = jornada_de.get(curso.id)
        if not clase:
            errores.append(f'Fila {i}: el curso {curso.nombre} no está en ninguna jornada.')
            continue
        hora = v('hora')
        franja = None
        if hasattr(hora, 'strftime'):
            hora = hora.strftime('%H:%M')
        hora = str(hora or '').strip()
        if hora.replace('.0', '').isdigit():
            n = int(float(hora))
            franja = clase[n - 1] if 1 <= n <= len(clase) else None
        elif re.match(r'^\d{1,2}:\d{2}', hora):
            hh = hora[:5].zfill(5)
            franja = next((x for x in clase if x.inicio.strftime('%H:%M') == hh), None)
        if not dia or not franja:
            errores.append(f'Fila {i}: día u hora no válidos ({v("dia")}, {v("hora")}).')
            continue
        candidatas = asig.get((curso.id, _norm(v('materia'))), [])
        if len(candidatas) > 1 and v('docente'):
            candidatas = [a for a in candidatas if _norm(a.docente.user.get_full_name()) == _norm(v('docente'))] or candidatas
        if not candidatas:
            errores.append(f'Fila {i}: {curso.nombre} no tiene la materia «{v("materia")}» en la asignación académica.')
            continue
        validas.append((candidatas[0].id, dia, franja.id))
    if not validas:
        raise nucleo.ArchivoInvalido('No se pudo leer ninguna clase. ' + (errores[0] if errores else ''))
    actual = nucleo.Datos(datos_del_colegio(colegio, con_firma=False))
    sesiones = [{'asignacion': a, 'dia': d, 'franja': f} for a, d, f in validas]
    informe = {'choques': nucleo.revisar(actual, sesiones), 'errores_importacion': errores[:50]}
    h = _crear(colegio, f'Importado {timezone.localdate():%d/%m/%Y}', 'IMPORTADO', validas, informe)
    return h, errores
