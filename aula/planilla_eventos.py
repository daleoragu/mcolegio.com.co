"""Planilla de inscripción de los eventos abiertos (Excel), para repartirla entre los colegios.

El organizador la descarga (vacía o con los inscritos), la comparte (por ejemplo en su nube), cada colegio
la llena con sus estudiantes y el organizador la vuelve a subir: se crean las inscripciones nuevas y se
actualizan las que ya existían (se reconocen por el número de documento). Se revisan los datos, el grado,
la autorización de datos y los cupos por institución y por nivel. Se aceptan .xlsx y .csv."""
import csv
import io
import secrets
import unicodedata

from django.utils import timezone
from openpyxl import Workbook, load_workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation

AZUL, ORO, GRIS = 'FF1F3A68', 'FFF2B632', 'FFE9ECEF'
# (clave, título en la planilla, ancho, obligatoria)
COLUMNAS = [
    ('nombre', 'Nombre completo', 32, True),
    ('documento', 'Número de documento', 18, True),
    ('institucion', 'Colegio o institución', 30, True),
    ('ciudad', 'Municipio o ciudad', 18, False),
    ('grado', 'Grado', 12, True),
    ('contacto', 'Correo o celular de contacto', 28, False),
    ('acudiente', 'Acudiente (o docente) que autoriza los datos', 30, True),
    ('acompanante', 'Docente acompañante', 24, False),
    ('autoriza', 'Autoriza datos (SÍ)', 14, True),
    ('estado', 'Estado (no llenar)', 16, False),
    ('clave', 'Clave para entrar (no llenar)', 16, False),
]
PALABRAS_GRADO = {'prejardin': -2, 'jardin': -1, 'transicion': 0, 'primero': 1, 'segundo': 2, 'tercero': 3, 'cuarto': 4, 'quinto': 5,
                  'sexto': 6, 'septimo': 7, 'octavo': 8, 'noveno': 9, 'decimo': 10, 'once': 11, 'undecimo': 11}


def _plano(texto):
    t = unicodedata.normalize('NFKD', str(texto or '')).encode('ascii', 'ignore').decode().lower()
    return ' '.join(t.replace('.', ' ').replace('°', ' ').replace('º', ' ').split())


def leer_grado(valor):
    """7, '7', '7.º', '7°', 'Séptimo', 'Transición' → número de grado (None si no se entiende)."""
    if valor is None or valor == '':
        return None
    if isinstance(valor, (int, float)):
        return int(valor)
    t = _plano(valor)
    for palabra in t.split():
        if palabra.lstrip('-').isdigit():
            return int(palabra)
        if palabra in PALABRAS_GRADO:
            return PALABRAS_GRADO[palabra]
    return None


def descargar(ev, grados, etiqueta, inscritos=()):
    """El libro de Excel: hoja «Inscripción» (con los inscritos, si se piden) e «Instrucciones»."""
    libro = Workbook()
    hoja = libro.active
    hoja.title = 'Inscripción'
    hoja.append([f'{ev.titulo} · planilla de inscripción · código del evento {ev.codigo}'])
    hoja['A1'].font = Font(bold=True, size=13, color=AZUL)
    hoja.append(['Llene una fila por estudiante. No cambie los títulos de las columnas. Las columnas grises las llena la plataforma.'])
    hoja['A2'].font = Font(italic=True, size=9, color='FF5B6474')
    hoja.append([t for _, t, _, _ in COLUMNAS])
    for i, (clave, _, ancho, oblig) in enumerate(COLUMNAS, start=1):
        c = hoja.cell(row=3, column=i)
        c.font = Font(bold=True, color='FFFFFFFF' if clave not in ('estado', 'clave') else 'FF495057', size=10)
        c.fill = PatternFill('solid', fgColor=(AZUL if oblig else 'FF3B5BDB') if clave not in ('estado', 'clave') else GRIS)
        c.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
        hoja.column_dimensions[get_column_letter(i)].width = ancho
    hoja.row_dimensions[3].height = 32
    hoja.freeze_panes = 'A4'
    for p in inscritos:
        d = p.datos or {}
        hoja.append([p.nombre, d.get('documento', ''), p.institucion, d.get('ciudad', ''), etiqueta(p.grado) if p.grado is not None else '',
                     d.get('contacto', ''), (d.get('autorizacion') or {}).get('acudiente', ''), d.get('acompanante', ''),
                     'SÍ' if d.get('autorizacion') else '', p.get_estado_display(), d.get('clave', '')])
    # Listas para escoger el grado y la autorización
    ultima = max(hoja.max_row, 3) + 500
    lista_grados = DataValidation(type='list', formula1='"' + ','.join(etiqueta(g) for g in grados) + '"', allow_blank=True,
                                  error='Escoja un grado de la lista.', errorTitle='Grado')
    lista_si = DataValidation(type='list', formula1='"SÍ,NO"', allow_blank=True)
    hoja.add_data_validation(lista_grados); hoja.add_data_validation(lista_si)
    lista_grados.add(f'E4:E{ultima}'); lista_si.add(f'I4:I{ultima}')
    gris = PatternFill('solid', fgColor='FFF8F9FA')
    for fila in range(4, ultima + 1):
        for col in (10, 11):
            hoja.cell(row=fila, column=col).fill = gris

    from .views_eventos import config_de, texto_supervision
    ins = libro.create_sheet('Instrucciones')
    filas = [
        ['Cómo llenar la planilla'],
        [''],
        ['1. Una fila por estudiante. Las columnas en azul oscuro son obligatorias.'],
        ['2. Número de documento: el del estudiante (tarjeta de identidad o registro civil). Con él se reconoce la inscripción si la planilla se sube otra vez.'],
        ['3. Grado: escójalo de la lista. Grados de este evento: ' + ', '.join(etiqueta(g) for g in grados) + '.'],
        ['4. Autoriza datos: escriba SÍ solo si el acudiente autorizó el tratamiento de los datos (Ley 1581 de 2012)'
         + (' y la supervisión de la prueba. ' + texto_supervision(config_de(ev)['vigilancia']) if config_de(ev)['vigilancia']['activa'] else '.')],
        ['5. No llene «Estado» ni «Clave»: los pone la plataforma. Con el documento y la clave cada estudiante entra al evento'
         ' (en el enlace del evento, «Ya me inscribí»).'],
        ['6. Devuelva la planilla al organizador del evento sin cambiar los títulos de las columnas.'],
    ]
    for f in filas:
        ins.append(f)
    ins['A1'].font = Font(bold=True, size=13, color=AZUL)
    ins.column_dimensions['A'].width = 130
    for fila in ins.iter_rows(min_row=3):
        fila[0].alignment = Alignment(wrap_text=True, vertical='top')
    salida = io.BytesIO()
    libro.save(salida)
    salida.seek(0)
    return salida


def _filas(archivo):
    """Las filas del archivo subido (xlsx o csv) como listas de valores."""
    nombre = (archivo.name or '').lower()
    if nombre.endswith('.csv'):
        texto = archivo.read().decode('utf-8-sig', errors='replace')
        try:
            dialecto = csv.Sniffer().sniff(texto[:4000], delimiters=',;\t')
        except csv.Error:
            dialecto = csv.excel
        return [fila for fila in csv.reader(io.StringIO(texto), dialecto)]
    libro = load_workbook(archivo, read_only=True, data_only=True)
    hoja = libro['Inscripción'] if 'Inscripción' in libro.sheetnames else libro.worksheets[0]
    return [list(f) for f in hoja.iter_rows(values_only=True)]


def _encabezados(filas):
    """(número de la fila de títulos, {clave: columna}) buscando los títulos de la planilla."""
    buscar = {k: _plano(t).split(' (')[0] for k, t, _, _ in COLUMNAS}
    for n, fila in enumerate(filas[:15]):
        planos = [_plano(v) for v in fila]
        cols = {}
        for k, b in buscar.items():
            for i, v in enumerate(planos):
                if v and (v.startswith(b) or b.startswith(v)) and i not in cols.values():
                    cols[k] = i
                    break
        if {'nombre', 'documento', 'institucion', 'grado'} <= set(cols):
            return n, cols
    return None, {}


def importar(ev, archivo, c, usuario, ip, aprobar=False):
    """Crea o actualiza las inscripciones de la planilla. Devuelve {'nuevas', 'actualizadas', 'errores': [(fila, motivo)]}."""
    from .models import ParticipacionEvento
    from .views_eventos import grupos, normalizar, sin_cupo
    try:
        filas = _filas(archivo)
    except Exception:
        return {'nuevas': 0, 'actualizadas': 0, 'errores': [(0, 'No se pudo leer el archivo. Súbalo en Excel (.xlsx) o .csv.')]}
    n_tit, cols = _encabezados(filas)
    if n_tit is None:
        return {'nuevas': 0, 'actualizadas': 0, 'errores': [(0, 'No se encontraron los títulos de la planilla (Nombre completo, Número de documento, Colegio o institución, Grado). Use la planilla descargada.')]}
    externas = {(p.datos or {}).get('documento'): p for p in ev.participaciones.filter(estudiante__isnull=True) if (p.datos or {}).get('documento')}
    vig = c['vigilancia']['activa']
    res = {'nuevas': 0, 'actualizadas': 0, 'errores': []}
    vistos = set()
    for k, fila in enumerate(filas[n_tit + 1:], start=n_tit + 2):
        val = lambda clave: ('' if cols.get(clave) is None or cols[clave] >= len(fila) or fila[cols[clave]] is None else str(fila[cols[clave]]).strip())
        if not any(val(x) for x in ('nombre', 'documento', 'institucion')):
            continue
        nombre, institucion = ' '.join(val('nombre').split())[:120], ' '.join(val('institucion').split())[:120]
        documento = ''.join(val('documento').split()).replace('.', '')[:20]
        if documento.endswith('.0'):
            documento = documento[:-2]
        g_val = fila[cols['grado']] if cols.get('grado') is not None and cols['grado'] < len(fila) else None
        grado = leer_grado(g_val)
        g = next((x for x in grupos(c) if grado in x['grados']), None)
        acudiente = ' '.join(val('acudiente').split())[:120]
        autoriza = _plano(val('autoriza')) in ('si', 's', 'x', '1', 'yes', 'true', 'verdadero')
        if len(nombre) < 5:
            res['errores'].append((k, 'Falta el nombre completo.')); continue
        if len(documento) < 5:
            res['errores'].append((k, f'{nombre}: falta el número de documento.')); continue
        if documento in vistos:
            res['errores'].append((k, f'{nombre}: el documento {documento} está repetido en la planilla.')); continue
        vistos.add(documento)
        if not institucion:
            res['errores'].append((k, f'{nombre}: falta el colegio o institución.')); continue
        if g is None:
            res['errores'].append((k, f'{nombre}: el grado «{g_val or ""}» no está en este evento.')); continue
        if not autoriza or len(acudiente) < 5:
            res['errores'].append((k, f'{nombre}: falta la autorización de datos (SÍ) y el nombre del acudiente que la da.')); continue
        datos_nuevos = {'documento': documento, 'ciudad': ' '.join(val('ciudad').split())[:80], 'contacto': ' '.join(val('contacto').split())[:120],
                        'acompanante': ' '.join(val('acompanante').split())[:120]}
        autorizacion = {'acudiente': acudiente, 'fecha': timezone.now().isoformat(timespec='seconds'), 'ip': ip, 'grabacion': vig,
                        'origen': 'planilla', 'subida_por': usuario.get_username()}
        p = externas.get(documento)
        if p is not None:          # ya estaba: se actualiza (sin cambiar su estado)
            if p.ciclo != g['id'] and p.estado == 'aprobada':
                motivo = sin_cupo(ev, c, institucion, g['id'], ('aprobada',))
                if motivo and normalizar(p.institucion) == normalizar(institucion):
                    res['errores'].append((k, f'{nombre}: no se cambió de nivel. {motivo}')); continue
            p.nombre, p.institucion, p.grado, p.ciclo = nombre, institucion, grado, g['id']
            p.datos = dict(p.datos or {}, **datos_nuevos, autorizacion=autorizacion)
            p.save()
            res['actualizadas'] += 1
            continue
        estado = 'aprobada' if (aprobar or not c['inscripcion']['aprobacion']) else 'pendiente'
        motivo = sin_cupo(ev, c, institucion, g['id'], ('aprobada',) if estado == 'aprobada' else ('aprobada', 'pendiente'))
        if motivo:
            res['errores'].append((k, f'{nombre}: {motivo}')); continue
        clave = ''.join(secrets.choice('ABCDEFGHJKLMNPQRSTUVWXYZ23456789') for _ in range(6))
        externas[documento] = ParticipacionEvento.objects.create(
            evento=ev, nombre=nombre, institucion=institucion, grado=grado, ciclo=g['id'], token=secrets.token_urlsafe(24), estado=estado,
            datos=dict(datos_nuevos, clave=clave, autorizacion=autorizacion))
        res['nuevas'] += 1
    return res
