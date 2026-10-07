# -*- coding: utf-8 -*-
"""PuntoExacto · la clave de un examen desde (y hacia) Excel o CSV.

Pensado para los cuadernillos tipo Saber que el colegio ya tiene armados: en
vez de marcar 42 respuestas a mano, se sube la hoja de claves.

Columnas que se reconocen (el orden no importa, mayúsculas y tildes tampoco):

    pregunta | clave | area | competencia | componente | afirmacion | etiquetas
    | control | puntos | clave_b | clave_c | clave_d

Solo «pregunta» y «clave» son obligatorias. Con «area» el examen se parte en
bloques, como la hoja del ICFES. Competencia, componente y afirmación quedan
como temas de la pregunta, que es lo que usa el análisis por tema. «control»
(sí/no) marca las preguntas de control de lectura.
"""
import csv
import io
import unicodedata
from decimal import Decimal, InvalidOperation

from .models import LETRAS

MAX_PREGUNTAS = 150


class ClaveInvalida(Exception):
    """El archivo no se puede usar; el mensaje se le muestra al docente."""


def _llano(texto):
    texto = unicodedata.normalize('NFKD', str(texto or '')).encode('ascii', 'ignore').decode()
    return ' '.join(texto.lower().replace('_', ' ').replace('.', ' ').split())


SINONIMOS = {
    'pregunta': {'pregunta', 'preguntas', 'numero', 'no', 'n', 'n o', 'no o', '#', 'item', 'nro'},
    'clave': {'clave', 'respuesta', 'correcta', 'respuesta correcta', 'clave a', 'forma a'},
    'area': {'area', 'prueba', 'bloque', 'asignatura', 'materia'},
    'competencia': {'competencia', 'competencias'},
    'componente': {'componente', 'componentes', 'eje', 'eje tematico', 'tema'},
    'afirmacion': {'afirmacion', 'aprendizaje', 'evidencia'},
    'etiquetas': {'etiquetas', 'temas'},
    'control': {'control', 'control de lectura', 'es control'},
    'puntos': {'puntos', 'puntaje', 'valor'},
}


def _columna(encabezado):
    llano = _llano(encabezado)
    for nombre, opciones in SINONIMOS.items():
        if llano in opciones:
            return nombre
    # Claves de otras formas: «clave_b», «clave B», «forma b».
    partes = llano.split()
    if len(partes) == 2 and partes[0] in ('clave', 'forma') and partes[1] in ('b', 'c', 'd'):
        return f'forma_{partes[1].upper()}'
    return None


def _filas_de_csv(contenido):
    texto = None
    for codificacion in ('utf-8-sig', 'cp1252', 'latin-1'):
        try:
            texto = contenido.decode(codificacion)
            break
        except UnicodeDecodeError:
            continue
    try:
        dialecto = csv.Sniffer().sniff(texto.splitlines()[0] if texto else ',', delimiters=',;\t')
        separador = dialecto.delimiter
    except csv.Error:
        separador = ','
    filas = [f for f in csv.reader(io.StringIO(texto), delimiter=separador)]
    if not filas:
        return [], []
    encabezado, datos = filas[0], filas[1:]
    # Un texto con coma sin comillas («Ciencia, tecnología y sociedad») parte
    # la fila en una columna de más. Lo que sobra se devuelve a la columna
    # anterior a la última, que es donde suelen ir esos textos largos.
    arregladas = []
    for f in datos:
        if len(f) > len(encabezado) >= 2:
            sobra = len(f) - len(encabezado)
            corte = len(encabezado) - 2
            f = f[:corte] + [','.join(f[corte:corte + sobra + 1])] + f[corte + sobra + 1:]
        arregladas.append(f)
    return encabezado, arregladas


def _filas_de_excel(contenido):
    import openpyxl
    try:
        libro = openpyxl.load_workbook(io.BytesIO(contenido), read_only=True, data_only=True)
    except Exception:
        raise ClaveInvalida('No se pudo abrir el archivo de Excel.')
    hoja = libro.worksheets[0]
    filas = [['' if v is None else str(v).strip() for v in fila]
             for fila in hoja.iter_rows(values_only=True)]
    filas = [f for f in filas if any(f)]
    if not filas:
        return [], []
    return filas[0], filas[1:]


def _filas_de_word(contenido):
    """La primera tabla de un .docx que tenga columnas de pregunta y clave.

    Se lee el XML directamente (un .docx es un zip) para no depender de otra
    librería. Las celdas con varios párrafos se unen con espacio.
    """
    import zipfile
    from xml.etree import ElementTree as ET
    w = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
    try:
        with zipfile.ZipFile(io.BytesIO(contenido)) as z:
            raiz = ET.fromstring(z.read('word/document.xml'))
    except (zipfile.BadZipFile, KeyError, ET.ParseError):
        raise ClaveInvalida('No se pudo abrir el documento de Word.')
    for tabla in raiz.iter(f'{w}tbl'):
        filas = []
        for tr in tabla.iter(f'{w}tr'):
            celdas = []
            for tc in tr.findall(f'{w}tc'):
                parrafos = [''.join(t.text or '' for t in p.iter(f'{w}t')) for p in tc.iter(f'{w}p')]
                celdas.append(' '.join(x.strip() for x in parrafos if x.strip()))
            if any(celdas):
                filas.append(celdas)
        if filas:
            columnas = [_columna(c) for c in filas[0]]
            if 'pregunta' in columnas and 'clave' in columnas:
                return filas[0], filas[1:]
    raise ClaveInvalida('El documento de Word no tiene una tabla con columnas de pregunta y clave.')


def _si(valor):
    return _llano(valor) in ('si', 's', 'x', '1', 'true', 'verdadero', 'yes')


def _limpiar_tema(texto):
    # Los temas de una pregunta se guardan separados por coma: una coma dentro
    # del tema lo partiría en dos.
    return ' '.join(str(texto or '').replace(',', ' ·').split())[:60]


def leer(archivo):
    """Lee el archivo y devuelve la lista de preguntas, o lanza ClaveInvalida.

    [{'numero': 1, 'clave': 'A', 'area': 'Ciencias naturales',
      'temas': ['Uso comprensivo', 'Entorno vivo'], 'control': False,
      'puntos': None, 'formas': {'B': 'C'}}, ...]
    """
    nombre = (getattr(archivo, 'name', '') or '').lower()
    contenido = archivo.read()
    if not contenido:
        raise ClaveInvalida('El archivo está vacío.')
    if nombre.endswith(('.xlsx', '.xlsm')):
        encabezado, filas = _filas_de_excel(contenido)
    elif nombre.endswith(('.csv', '.txt')):
        encabezado, filas = _filas_de_csv(contenido)
    elif nombre.endswith('.docx'):
        encabezado, filas = _filas_de_word(contenido)
    else:
        raise ClaveInvalida('Suba la clave en Excel (.xlsx), CSV (.csv) o Word (.docx) con una tabla.')

    columnas = [_columna(e) for e in encabezado]
    if 'pregunta' not in columnas or 'clave' not in columnas:
        raise ClaveInvalida('El archivo necesita al menos las columnas «pregunta» y «clave» '
                            'en la primera fila.')

    preguntas, errores, vistos = [], [], set()
    for i, fila in enumerate(filas, start=2):
        datos = {}
        for col, valor in zip(columnas, fila):
            if col and col not in datos:
                datos[col] = (valor or '').strip()
        if not any(datos.values()):
            continue
        try:
            numero = int(float(datos.get('pregunta', '').replace(',', '.')))
        except ValueError:
            errores.append(f'Fila {i}: «{datos.get("pregunta")}» no es un número de pregunta.')
            continue
        if numero in vistos:
            errores.append(f'Fila {i}: la pregunta {numero} está repetida.')
            continue
        vistos.add(numero)
        clave = datos.get('clave', '').upper()[:1]
        if clave and clave not in LETRAS:
            errores.append(f'Fila {i}: la clave «{datos.get("clave")}» no es una letra de la A a la J.')
            continue
        # Sin columna «control», se reconoce por la competencia o el componente
        # (así viene en la tabla de especificaciones en Word).
        control = _si(datos.get('control')) or _llano(datos.get('competencia')) == 'control' \
            or _llano(datos.get('componente')).startswith('control de lectura')
        temas = []
        if 'etiquetas' in datos:
            temas += [_limpiar_tema(t) for t in datos['etiquetas'].split(',')]
        for col in ('competencia', 'componente', 'afirmacion'):
            temas.append(_limpiar_tema(datos.get(col)))
        if control:
            # «Control / Control de lectura»: con uno basta.
            temas = [t for t in temas if _llano(t) != 'control'] or ['Control de lectura']
        temas = list(dict.fromkeys(t for t in temas if t))
        puntos = None
        if datos.get('puntos'):
            try:
                puntos = Decimal(datos['puntos'].replace(',', '.'))
            except InvalidOperation:
                errores.append(f'Fila {i}: los puntos «{datos["puntos"]}» no son un número.')
        formas = {}
        for col, valor in datos.items():
            if col.startswith('forma_') and valor:
                letra = valor.upper()[:1]
                if letra not in LETRAS:
                    errores.append(f'Fila {i}: la clave de la forma {col[-1]} «{valor}» no es una letra.')
                else:
                    formas[col[-1]] = letra
        preguntas.append({'numero': numero, 'clave': clave, 'area': datos.get('area', '')[:60],
                          'temas': temas, 'control': control, 'puntos': puntos,
                          'formas': formas})

    if errores:
        raise ClaveInvalida(' '.join(errores[:8]) + (' …' if len(errores) > 8 else ''))
    if not preguntas:
        raise ClaveInvalida('El archivo no trae preguntas.')
    preguntas.sort(key=lambda p: p['numero'])
    numeros = [p['numero'] for p in preguntas]
    if numeros != list(range(1, len(numeros) + 1)):
        faltan = sorted(set(range(1, max(numeros) + 1)) - set(numeros))
        raise ClaveInvalida('Las preguntas deben ir de la 1 en adelante sin saltos'
                            + (f'; faltan: {", ".join(map(str, faltan[:10]))}.' if faltan else '.'))
    if len(preguntas) > MAX_PREGUNTAS:
        raise ClaveInvalida(f'Son {len(preguntas)} preguntas y el máximo es {MAX_PREGUNTAS}.')
    return preguntas


def aplicar(examen, preguntas, control_cuenta=True, crear_bloques=True):
    """Deja el examen como dice el archivo. Devuelve un resumen para mostrar.

    Llamar dentro de una transacción. Las respuestas ya leídas de los
    estudiantes no se tocan: se recalifican con la clave nueva.
    """
    from notas.models.academicos import Materia
    from . import formas as formas_mod
    from .models import Bloque, Forma, Pregunta

    n = len(preguntas)
    tope = max([LETRAS.index(p['clave']) + 1 for p in preguntas if p['clave']]
               + [LETRAS.index(l) + 1 for p in preguntas for l in p['formas'].values()]
               + [examen.numero_opciones])
    examen.numero_preguntas = n
    examen.numero_opciones = max(examen.numero_opciones, tope)
    examen.save(update_fields=['numero_preguntas', 'numero_opciones'])

    existentes = {p.numero: p for p in examen.preguntas.all()}
    examen.preguntas.filter(numero__gt=n).delete()

    # Bloques: uno por área, en el orden en que aparecen. Con una sola área no
    # hace falta partir la hoja.
    areas = list(dict.fromkeys(p['area'] for p in preguntas if p['area']))
    bloque_de = {}
    if crear_bloques and len(areas) > 1:
        examen.bloques.all().delete()
        materias = {_llano(m.nombre): m for m in Materia.objects.filter(colegio=examen.colegio)} \
            if examen.colegio_id else {}
        for orden, area in enumerate(areas, start=1):
            bloque_de[area] = Bloque.objects.create(
                examen=examen, orden=orden, nombre=area, materia=materias.get(_llano(area)))

    for d in preguntas:
        p = existentes.get(d['numero']) or Pregunta(examen=examen, numero=d['numero'])
        p.correcta = d['clave']
        p.etiquetas = ', '.join(d['temas'])[:200]
        # Las de control se leen y se informan, pero no suman (salvo que el
        # docente diga lo contrario al importar).
        p.es_control = d['control'] and not control_cuenta
        if d['puntos'] is not None:
            p.puntos = d['puntos']
        if bloque_de:
            p.bloque = bloque_de.get(d['area'])
        # Si la clave pide más letras de las que tenía la pregunta, se amplía.
        letras_necesarias = max([LETRAS.index(d['clave']) + 1 if d['clave'] else 0]
                                + [LETRAS.index(l) + 1 for l in d['formas'].values()])
        if p.pk and p.opciones_efectivas() < letras_necesarias:
            p.numero_opciones = letras_necesarias
        p.save()

    if not examen.es_manual:
        examen.preguntas.update(puntos=examen.puntos_automaticos())

    # Claves de otras formas (columnas clave_b, clave_c…).
    letras_formas = sorted({l for d in preguntas for l in d['formas']})
    lista = list(examen.preguntas.select_related('bloque').order_by('numero'))
    for letra in letras_formas:
        forma = examen.formas.filter(letra=letra).first()
        if forma is None:
            forma = Forma.objects.create(
                examen=examen, letra=letra,
                orden=[dict(f, pendiente=True) for f in formas_mod.identidad(lista)])
        orden, _ = formas_mod.ajustar(forma.orden, lista)
        for d in preguntas:
            if letra in d['formas']:
                orden[d['numero'] - 1] = formas_mod.marcar_clave(
                    orden, lista, d['numero'], d['formas'][letra])
        forma.orden = orden
        forma.save(update_fields=['orden'])
    formas_mod.ajustar_formas(examen)
    for letra in letras_formas:
        formas_mod.retraducir(letra, examen)

    return {
        'preguntas': n,
        'bloques': [(a, sum(1 for p in preguntas if p['area'] == a)) for a in areas] if bloque_de else [],
        'control': sum(1 for p in preguntas if p['control']),
        'sin_clave': sum(1 for p in preguntas if not p['clave']),
        'formas': letras_formas,
        'temas': len({t for p in preguntas for t in p['temas']}),
    }


# ---------------------------------------------------------------------------
# Exportar
# ---------------------------------------------------------------------------

def filas_para_exportar(examen):
    """Encabezado y filas con la clave del examen, en el formato que se importa."""
    from . import formas as formas_mod
    preguntas = list(examen.preguntas.select_related('bloque').order_by('numero'))
    formas = list(examen.formas.all())
    claves = {f.letra: formas_mod.clave_de(f.orden, preguntas) for f in formas}
    encabezado = ['pregunta', 'clave', 'area', 'etiquetas', 'control', 'puntos', 'anulada']
    encabezado += [f'clave_{f.letra.lower()}' for f in formas]
    filas = []
    for k, p in enumerate(preguntas):
        temas = p.lista_etiquetas()
        filas.append([p.numero, p.correcta, p.bloque.nombre if p.bloque_id else '',
                      ', '.join(temas),
                      'si' if p.es_control else 'no',
                      str(p.puntos).replace('.', ','), 'si' if p.anulada else 'no']
                     + [claves[f.letra][k]['correcta'] for f in formas])
    return encabezado, filas
