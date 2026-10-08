# -*- coding: utf-8 -*-
"""PuntoExacto · el cuadernillo del examen escrito en la plataforma.

El docente escribe cada pregunta con sus opciones y marca la correcta: al
guardar, la clave del examen se actualiza sola (la misma que usa el lector de
hojas). Con eso salen el cuadernillo en Word y en PDF, una versión por forma
(A, B, C, D) o uno por estudiante con su nombre impreso.

Las imágenes NO se guardan en el servidor. Viven en la nube del docente
(Google Drive u OneDrive) o en su navegador. Cuando pide el Word o el PDF, el
navegador las manda junto con la petición; el servidor las usa para armar el
archivo y las olvida.

Contenido (JSON):
  {"instrucciones": "...", "nombre": "linea|lista|no", "columnas": 1|2,
   "items": [
     {"id": "...", "tipo": "texto", "texto": "...", "imagenes": [img]},
     {"id": "...", "tipo": "pregunta", "enunciado": "...", "imagenes": [img],
      "opciones": [{"texto": "...", "imagen": img|null}, ...], "correcta": "B"}
   ]}
  img = {"id": "...", "proveedor": "local|google|onedrive", "ref": "...",
         "nombre": "...", "ancho": 10..100}
"""
import base64
import html
import io
import re

from .models import LETRAS

MAX_ITEMS = 200
MAX_TEXTO = 6000
MAX_OPCION = 1500
MAX_IMAGENES = 6
MIN_OPCIONES, MAX_OPCIONES = 2, 6
PROVEEDORES = ('local', 'google', 'onedrive')
MODOS_NOMBRE = ('linea', 'lista', 'no')

INSTRUCCIONES = ('Lea cada pregunta con atención y marque una sola respuesta en la hoja de respuestas, '
                 'rellenando completamente el círculo con lápiz o lapicero negro.')


# ---------------------------------------------------------------------------
# Limpiar lo que llega del navegador
# ---------------------------------------------------------------------------

def _texto(valor, tope):
    return str(valor or '').replace('\r\n', '\n').replace('\r', '\n')[:tope]


def _id(valor):
    v = re.sub(r'[^A-Za-z0-9_-]', '', str(valor or ''))[:64]
    return v


def _imagen(img):
    if not isinstance(img, dict):
        return None
    iid = _id(img.get('id'))
    if not iid:
        return None
    proveedor = img.get('proveedor') if img.get('proveedor') in PROVEEDORES else 'local'
    try:
        ancho = int(img.get('ancho') or 60)
    except (TypeError, ValueError):
        ancho = 60
    return {'id': iid, 'proveedor': proveedor, 'ref': str(img.get('ref') or '')[:200],
            'nombre': _texto(img.get('nombre'), 120), 'ancho': max(10, min(100, ancho))}


def _imagenes(lista):
    salida = [i for i in (_imagen(x) for x in (lista or [])[:MAX_IMAGENES]) if i]
    return salida


def limpiar(contenido, opciones_por_defecto=4):
    """Deja el contenido con la forma esperada y dentro de los topes. Nunca falla."""
    c = contenido if isinstance(contenido, dict) else {}
    salida = {
        'instrucciones': _texto(c.get('instrucciones', INSTRUCCIONES), MAX_TEXTO),
        'nombre': c.get('nombre') if c.get('nombre') in MODOS_NOMBRE else 'linea',
        'columnas': 2 if str(c.get('columnas')) == '2' else 1,
        'items': [],
    }
    vistos = set()
    for it in (c.get('items') or [])[:MAX_ITEMS]:
        if not isinstance(it, dict):
            continue
        iid = _id(it.get('id')) or f'i{len(salida["items"]) + 1}'
        while iid in vistos:
            iid += 'x'
        vistos.add(iid)
        if it.get('tipo') == 'texto':
            salida['items'].append({'id': iid, 'tipo': 'texto', 'texto': _texto(it.get('texto'), MAX_TEXTO),
                                    'imagenes': _imagenes(it.get('imagenes'))})
            continue
        opciones = []
        for op in (it.get('opciones') or [])[:MAX_OPCIONES]:
            op = op if isinstance(op, dict) else {'texto': op}
            opciones.append({'texto': _texto(op.get('texto'), MAX_OPCION), 'imagen': _imagen(op.get('imagen'))})
        while len(opciones) < MIN_OPCIONES:
            opciones.append({'texto': '', 'imagen': None})
        correcta = str(it.get('correcta') or '').strip().upper()[:1]
        if correcta not in LETRAS[:len(opciones)]:
            correcta = ''
        salida['items'].append({'id': iid, 'tipo': 'pregunta', 'enunciado': _texto(it.get('enunciado'), MAX_TEXTO),
                                'imagenes': _imagenes(it.get('imagenes')), 'opciones': opciones,
                                'correcta': correcta})
    return salida


def vacio(examen):
    """Un cuadernillo nuevo con tantas preguntas como tenga el examen, y su clave si ya la tiene."""
    preguntas = list(examen.preguntas.order_by('numero'))
    items = []
    for p in preguntas:
        n = max(MIN_OPCIONES, min(MAX_OPCIONES, p.opciones_efectivas()))
        items.append({'id': f'p{p.numero}', 'tipo': 'pregunta', 'enunciado': '', 'imagenes': [],
                      'opciones': [{'texto': '', 'imagen': None} for _ in range(n)],
                      'correcta': p.correcta if p.correcta in LETRAS[:n] else ''})
    return limpiar({'items': items})


def preguntas_de(contenido):
    return [it for it in contenido['items'] if it['tipo'] == 'pregunta']


def todas_las_imagenes(contenido):
    for it in contenido['items']:
        yield from it.get('imagenes') or []
        for op in it.get('opciones') or []:
            if op.get('imagen'):
                yield op['imagen']


# ---------------------------------------------------------------------------
# La clave: el cuadernillo manda
# ---------------------------------------------------------------------------

def sincronizar_clave(examen, contenido):
    """Pone en el examen el número de preguntas, las opciones y la respuesta correcta de cada una.

    Devuelve (cambio_numero, formas_ajustadas). Lo demás de cada pregunta
    (puntos, componente, bloque, etiquetas) no se toca.
    """
    from . import calificacion as calif
    from . import formas as formas_mod
    from .models import Pregunta

    lista = preguntas_de(contenido)
    cambio_numero = False
    if lista and len(lista) != examen.numero_preguntas:
        examen.numero_preguntas = len(lista)
        examen.save(update_fields=['numero_preguntas'])
        existentes = set(examen.preguntas.values_list('numero', flat=True))
        for n in range(1, examen.numero_preguntas + 1):
            if n not in existentes:
                Pregunta.objects.create(examen=examen, numero=n)
        examen.preguntas.filter(numero__gt=examen.numero_preguntas).delete()
        cambio_numero = True
    por_numero = {p.numero: p for p in examen.preguntas.select_related('bloque', 'examen')}
    for n, it in enumerate(lista, start=1):
        p = por_numero.get(n)
        if p is None:
            continue
        k = len(it['opciones'])
        nuevo_op = None if k == p.opciones_heredadas() else k
        cambios = []
        if p.numero_opciones != nuevo_op:
            p.numero_opciones = nuevo_op
            cambios.append('numero_opciones')
        if p.correcta != it['correcta']:
            p.correcta = it['correcta']
            cambios.append('correcta')
        if cambios:
            p.save(update_fields=cambios)
    if not examen.es_manual:
        examen.preguntas.update(puntos=examen.puntos_automaticos())
    ajustadas = formas_mod.ajustar_formas(examen) if examen.formas.exists() else []
    calif.calificar_examen(examen)
    return cambio_numero, ajustadas


# ---------------------------------------------------------------------------
# Qué va en cada versión impresa
# ---------------------------------------------------------------------------

def _grupos(contenido):
    """A cada pregunta (número de la A) el texto o lectura que la antecede, si hay."""
    grupo, salida, n = None, {}, 0
    for it in contenido['items']:
        if it['tipo'] == 'texto':
            grupo = it
        else:
            n += 1
            salida[n] = grupo
    return salida


def secuencia(contenido, orden=None):
    """Lo que se imprime, en orden, para una forma.

    orden: el de la forma (lista de {'pregunta': n de la A, 'opciones': 'CABD'})
    o None para la A. Con preguntas barajadas, la lectura de una pregunta se
    vuelve a poner antes de ella cuando cambia de lectura respecto a la anterior.
    """
    lista = preguntas_de(contenido)
    if orden is None:
        # La A: tal cual se escribió.
        salida, n = [], 0
        for it in contenido['items']:
            if it['tipo'] == 'texto':
                salida.append({'tipo': 'texto', 'item': it})
            else:
                n += 1
                salida.append({'tipo': 'pregunta', 'numero': n, 'item': it,
                               'opciones': [(LETRAS[j], op) for j, op in enumerate(it['opciones'])]})
        return salida
    grupos = _grupos(contenido)
    salida, anterior = [], object()
    for pos, fila in enumerate(orden, start=1):
        n_a = fila.get('pregunta')
        if not n_a or n_a > len(lista):
            continue
        it = lista[n_a - 1]
        g = grupos.get(n_a)
        if g is not None and g is not anterior:
            salida.append({'tipo': 'texto', 'item': g})
        anterior = g
        letras = fila.get('opciones') or LETRAS[:len(it['opciones'])]
        ops = []
        for j, letra_a in enumerate(letras):
            k = LETRAS.find(letra_a)
            if 0 <= k < len(it['opciones']):
                ops.append((LETRAS[j], it['opciones'][k]))
        salida.append({'tipo': 'pregunta', 'numero': pos, 'item': it, 'opciones': ops})
    return salida


def versiones(examen, contenido, modo=None, por_forma=True):
    """[{'forma', 'estudiante', 'curso', 'secuencia'}] — una por forma o una por estudiante."""
    from . import formas as formas_mod
    modo = modo or contenido['nombre']
    preguntas = list(examen.preguntas.order_by('numero'))
    letras = ['A'] + [f.letra for f in examen.formas.all()]
    ordenes = {'A': None}
    for letra in letras[1:]:
        ordenes[letra] = formas_mod.orden_de(examen, letra, preguntas)

    if modo == 'lista':
        hojas = list(examen.hojas.filter(estudiante__isnull=False)
                     .select_related('estudiante__user', 'estudiante__curso')
                     .order_by('estudiante__curso__nombre', 'estudiante__user__last_name',
                               'estudiante__user__first_name'))
        if hojas:
            filas = [(h.nombre, h.estudiante.curso.nombre if h.estudiante.curso_id else '',
                      h.forma if h.forma in ordenes else 'A') for h in hojas]
        else:
            from notas.models import Estudiante
            ests = (Estudiante.objects.filter(curso__in=examen.cursos.all(), colegio=examen.colegio)
                    .select_related('user', 'curso').order_by('curso__nombre', 'user__last_name', 'user__first_name'))
            filas = [(f'{e.user.last_name} {e.user.first_name}'.strip(), e.curso.nombre if e.curso_id else '', 'A')
                     for e in ests if getattr(e, 'activo', True)]
        return [{'forma': f if len(letras) > 1 else '', 'estudiante': nombre.upper(), 'curso': curso,
                 'secuencia': secuencia(contenido, ordenes[f])} for nombre, curso, f in filas]

    usar = letras if por_forma else ['A']
    return [{'forma': l if len(letras) > 1 else '', 'estudiante': '', 'curso': '',
             'secuencia': secuencia(contenido, ordenes[l])} for l in usar]


# ---------------------------------------------------------------------------
# Texto con exponentes: x^2, x^{n+1}, a_1, a_{ij}
# ---------------------------------------------------------------------------

_MARCAS = re.compile(r'(\^|_)(\{([^{}]{1,40})\}|([A-Za-z0-9áéíóúñ+\-−*°]))')


def trozos(texto):
    """[(texto, 'normal'|'sup'|'sub')] para Word."""
    salida, pos = [], 0
    for m in _MARCAS.finditer(texto or ''):
        if m.start() > pos:
            salida.append((texto[pos:m.start()], 'normal'))
        salida.append((m.group(3) if m.group(3) is not None else m.group(4), 'sup' if m.group(1) == '^' else 'sub'))
        pos = m.end()
    if pos < len(texto or ''):
        salida.append((texto[pos:], 'normal'))
    return salida


def a_html(texto):
    """Escapa y convierte ^ y _ en <sup> y <sub>; respeta los saltos de línea."""
    partes = []
    for t, tipo in trozos(texto):
        t = html.escape(t)
        partes.append(f'<{tipo}>{t}</{tipo}>' if tipo != 'normal' else t)
    return ''.join(partes).replace('\n', '<br>')


# ---------------------------------------------------------------------------
# Imágenes que manda el navegador (solo para esta petición)
# ---------------------------------------------------------------------------

TIPOS_IMAGEN = {'image/png', 'image/jpeg', 'image/gif', 'image/webp'}
MAX_BYTES_IMAGEN = 6 * 1024 * 1024


def leer_imagenes(archivos, contenido):
    """{id: (bytes, tipo)} de las imágenes que el cuadernillo usa. Se normalizan con Pillow:
    lo que no sea imagen se descarta, y las WEBP/GIF pasan a PNG porque Word no las lee."""
    from PIL import Image
    usadas = {img['id'] for img in todas_las_imagenes(contenido)}
    salida = {}
    for nombre, f in archivos.items():
        if not nombre.startswith('img_'):
            continue
        iid = nombre[4:]
        if iid not in usadas or f.size > MAX_BYTES_IMAGEN:
            continue
        try:
            datos = f.read()
            im = Image.open(io.BytesIO(datos))
            im.load()
        except Exception:
            continue
        formato = (im.format or '').upper()
        if formato in ('PNG', 'JPEG'):
            salida[iid] = (datos, 'image/png' if formato == 'PNG' else 'image/jpeg')
        else:
            buf = io.BytesIO()
            (im.convert('RGBA') if im.mode not in ('RGB', 'RGBA') else im).save(buf, 'PNG')
            salida[iid] = (buf.getvalue(), 'image/png')
    return salida


def data_uri(imagenes, img):
    if not img or img['id'] not in imagenes:
        return None
    datos, tipo = imagenes[img['id']]
    return f'data:{tipo};base64,{base64.b64encode(datos).decode()}'


# ---------------------------------------------------------------------------
# PDF
# ---------------------------------------------------------------------------

def generar_pdf(request, examen, contenido, imagenes, lista_versiones):
    from django.template.loader import render_to_string
    from weasyprint import HTML

    def preparar(it):
        return {'texto_html': a_html(it.get('texto') or it.get('enunciado') or ''),
                'imagenes': [(data_uri(imagenes, img), img) for img in it.get('imagenes') or []]}

    hojas = []
    for v in lista_versiones:
        filas = []
        for s in v['secuencia']:
            fila = {'tipo': s['tipo'], **preparar(s['item'])}
            if s['tipo'] == 'pregunta':
                fila['numero'] = s['numero']
                fila['opciones'] = [{'letra': l, 'texto_html': a_html(op['texto']),
                                     'imagen': data_uri(imagenes, op.get('imagen')),
                                     'ancho': (op.get('imagen') or {}).get('ancho', 40)}
                                    for l, op in s['opciones']]
            filas.append(fila)
        hojas.append({**v, 'filas': filas})
    html_doc = render_to_string('puntoexacto/cuadernillo_pdf.html', {
        'examen': examen, 'colegio': examen.colegio, 'contenido': contenido, 'versiones': hojas,
        'instrucciones_html': a_html(contenido['instrucciones']),
    }, request=request)
    return HTML(string=html_doc, base_url=request.build_absolute_uri('/')).write_pdf()


# ---------------------------------------------------------------------------
# Word
# ---------------------------------------------------------------------------

def _leer(archivo):
    if not archivo:
        return None
    try:
        with archivo.open('rb') as f:
            return f.read()
    except Exception:
        return None


def encabezado_docx(doc, colegio, util):
    """El encabezado configurado del colegio (el mismo de boletines y actas): logo izquierdo,
    las cuatro líneas con su fuente, tamaño y estilo, y logo derecho."""
    from docx.enum.table import WD_TABLE_ALIGNMENT
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.shared import Cm, Pt
    from django.utils.html import strip_tags

    izquierdo = _leer(colegio.logo_izquierdo) or _leer(getattr(colegio, 'escudo', None))
    derecho = _leer(colegio.logo_derecho)
    alto = Cm(min(3.0, max(1.2, (colegio.alto_logos_pdf or 65) * 0.0265)))
    tabla = doc.add_table(rows=1, cols=3)
    tabla.alignment = WD_TABLE_ALIGNMENT.CENTER
    izq, centro, der = tabla.rows[0].cells
    lado = Cm(3.0)
    izq.width, centro.width, der.width = lado, util - 2 * lado, lado
    for celda, datos, alineado in ((izq, izquierdo, WD_ALIGN_PARAGRAPH.LEFT), (der, derecho, WD_ALIGN_PARAGRAPH.RIGHT)):
        if datos:
            try:
                p = celda.paragraphs[0]
                p.alignment = alineado
                p.add_run().add_picture(io.BytesIO(datos), height=alto)
            except Exception:
                pass
    lineas = []
    for k in range(1, 5):
        texto = strip_tags(getattr(colegio, f'linea_encabezado_{k}', '') or '').strip()
        if texto:
            lineas.append((texto, k))
    if not lineas:
        lineas = [(colegio.nombre.upper(), 1)]
    for i, (texto, k) in enumerate(lineas):
        p = centro.paragraphs[0] if i == 0 else centro.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_after = Pt(0)
        r = p.add_run(texto)
        r.font.name = getattr(colegio, f'linea_encabezado_{k}_fuente', None) or 'Arial'
        r.font.size = Pt(getattr(colegio, f'linea_encabezado_{k}_tamano', None) or (11 if k == 1 else 8))
        r.bold = bool(getattr(colegio, f'linea_encabezado_{k}_negrilla', k == 1))
        r.italic = bool(getattr(colegio, f'linea_encabezado_{k}_cursiva', False))
        r.underline = bool(getattr(colegio, f'linea_encabezado_{k}_subrayado', False))
    return tabla


def generar_docx(examen, contenido, imagenes, lista_versiones):
    from docx import Document
    from docx.enum.section import WD_SECTION
    from docx.enum.table import WD_TABLE_ALIGNMENT
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn
    from docx.shared import Cm, Pt, RGBColor

    doc = Document()
    estilo = doc.styles['Normal']
    estilo.font.name = 'Arial'
    estilo.font.size = Pt(11)
    estilo.paragraph_format.space_after = Pt(2)
    sec = doc.sections[0]
    sec.page_height, sec.page_width = Cm(27.94), Cm(21.59)       # carta
    for lado in ('left_margin', 'right_margin'):
        setattr(sec, lado, Cm(1.8))
    sec.top_margin, sec.bottom_margin = Cm(1.5), Cm(1.5)
    util = sec.page_width - sec.left_margin - sec.right_margin
    columnas = contenido['columnas']
    ancho_col = (util - Cm(0.8)) / 2 if columnas == 2 else util
    color = (examen.colegio.color_primario or '#193661').lstrip('#')
    try:
        rgb = RGBColor.from_string(color.upper()[:6])
    except Exception:
        rgb = RGBColor(0x19, 0x36, 0x61)

    def columnas_de(seccion, n):
        sectpr = seccion._sectPr
        for viejo in sectpr.findall(qn('w:cols')):
            sectpr.remove(viejo)
        cols = OxmlElement('w:cols')
        cols.set(qn('w:num'), str(n))
        cols.set(qn('w:space'), '454')
        sectpr.append(cols)

    def escribir(parrafo, texto, negrilla=False):
        for t, tipo in trozos(texto):
            for k, linea in enumerate(t.split('\n')):
                if k:
                    parrafo.add_run().add_break()
                r = parrafo.add_run(linea)
                r.bold = negrilla
                if tipo == 'sup':
                    r.font.superscript = True
                elif tipo == 'sub':
                    r.font.subscript = True

    def poner_imagen(img, base):
        if not img:
            return
        if img['id'] not in imagenes:
            p = doc.add_paragraph()
            r = p.add_run(f'[imagen no disponible: {img.get("nombre") or img["id"]}]')
            r.italic = True
            return
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        try:
            p.add_run().add_picture(io.BytesIO(imagenes[img['id']][0]), width=int(base * img['ancho'] / 100))
        except Exception:
            p.add_run('[imagen no válida]').italic = True

    for k, v in enumerate(lista_versiones):
        if k:
            nueva = doc.add_section(WD_SECTION.NEW_PAGE)
            columnas_de(nueva, 1)
        else:
            columnas_de(sec, 1)
        # Encabezado del colegio, el mismo de boletines y actas
        encabezado_docx(doc, examen.colegio, util)
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(6)
        r = p.add_run(examen.titulo)
        r.bold, r.font.size, r.font.color.rgb = True, Pt(13), rgb
        datos = []
        if examen.asignacion_id:
            datos.append(examen.asignacion.materia.nombre)
        if examen.fecha:
            datos.append(examen.fecha.strftime('%d/%m/%Y'))
        if v['forma']:
            datos.append(f'FORMA {v["forma"]}')
        if datos:
            r = p.add_run('   ' + ' · '.join(datos))
            r.font.size = Pt(10)

        if v['estudiante']:
            p = doc.add_paragraph()
            r = p.add_run('Estudiante: ')
            r.bold = True
            p.add_run(v['estudiante'])
            if v['curso']:
                r = p.add_run('     Curso: ')
                r.bold = True
                p.add_run(v['curso'])
        elif contenido['nombre'] == 'linea':
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(8)
            p.add_run('Nombre: ').bold = True
            p.add_run('_' * 52)
            p.add_run('  Curso: ').bold = True
            p.add_run('_' * 10)
        if v['forma']:
            p = doc.add_paragraph()
            r = p.add_run(f'Rellene la burbuja de la FORMA {v["forma"]} en su hoja de respuestas.')
            r.bold, r.font.size = True, Pt(10)
        if contenido['instrucciones'].strip():
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(4)
            r = p.add_run('Instrucciones: ')
            r.bold = True
            escribir(p, contenido['instrucciones'])
            for run in p.runs:
                run.font.size = Pt(10)

        if columnas == 2:
            cuerpo = doc.add_section(WD_SECTION.CONTINUOUS)
            columnas_de(cuerpo, 2)
        base = ancho_col
        for s in v['secuencia']:
            it = s['item']
            if s['tipo'] == 'texto':
                p = doc.add_paragraph()
                p.paragraph_format.space_before = Pt(8)
                escribir(p, it['texto'])
                for img in it['imagenes']:
                    poner_imagen(img, base)
                continue
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(8)
            p.paragraph_format.keep_with_next = True
            r = p.add_run(f'{s["numero"]}. ')
            r.bold = True
            escribir(p, it['enunciado'])
            for img in it['imagenes']:
                poner_imagen(img, base)
            for letra, op in s['opciones']:
                p = doc.add_paragraph()
                p.paragraph_format.left_indent = Cm(0.6)
                p.paragraph_format.keep_with_next = True
                r = p.add_run(f'{letra}. ')
                r.bold = True
                escribir(p, op['texto'])
                if op.get('imagen'):
                    poner_imagen(op['imagen'], base * 0.9)
    salida = io.BytesIO()
    doc.save(salida)
    return salida.getvalue()
