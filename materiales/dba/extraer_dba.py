"""Extrae los DBA de una cartilla oficial del MEN (PDF) a JSON, copiando el texto tal cual.

Se guía por la tipografía de la cartilla: número grande (Medium, ≥30), enunciado (Medium, verde), títulos de sección
«Evidencias de aprendizaje» / «Ejemplo» (Book, verde), viñetas (Wingdings) y texto (Book, oscuro). Los ejemplos no
se copian. Uso: python extraer_dba.py cartilla.pdf salida.json
"""
import json
import re
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET


MARCAS = re.compile(r'\.indd|\d{1,2}/\d{1,2}/\d{2}\s+\d{1,2}:\d{2}|^\s*\d{1,3}\s*$')   # marcas de imprenta y números de página


def lineas(pdf):
    with tempfile.TemporaryDirectory() as d:
        subprocess.run(['pdftohtml', '-xml', '-i', '-q', pdf, d + '/x'], check=True, capture_output=True)
        raiz = ET.parse(d + '/x.xml').getroot()
    fuentes = {f.get('id'): f.attrib for f in raiz.iter('fontspec')}
    for pagina in raiz.iter('page'):
        ancho = int(pagina.get('width'))
        filas = []
        for t in pagina.iter('text'):
            texto = ''.join(t.itertext())
            f = fuentes[t.get('font')]
            filas.append({'top': int(t.get('top')), 'left': int(t.get('left')), 'width': int(t.get('width')), 'texto': texto, 'size': int(f['size']),
                          'family': f['family'], 'color': f['color'], 'pag': int(pagina.get('number'))})
        # columna izquierda y luego la derecha, cada una de arriba abajo
        filas = [r for r in filas if not MARCAS.search(r['texto']) and r['color'].lower() != '#ffffff']
        for r in filas:
            r['col'] = r['left'] >= ancho * 0.47
        filas = _unir_renglones(filas)
        # Una línea de texto abre una evidencia nueva si tiene una viñeta a su misma altura (±4 px) en su columna
        vinetas = [r for r in filas if 'Wingdings' in r['family']]
        for r in filas:
            r['abre'] = any(v['col'] == r['col'] and abs(v['top'] - r['top']) <= 4 and v['left'] < r['left'] for v in vinetas)
        filas = [r for r in filas if 'Wingdings' not in r['family']]
        filas.sort(key=lambda r: (r['col'], r['top'], r['left']))
        yield int(pagina.get('number')), filas


def _unir_renglones(filas):
    """Algunas cartillas traen cada letra por separado: los pedazos del mismo renglón (misma columna, ±2 px de alto,
    misma letra) se unen; con espacio solo si entre ellos queda un hueco."""
    filas = sorted(filas, key=lambda r: (r['col'], r['top'], r['left']))
    salida = []
    for r in filas:
        prev = salida[-1] if salida else None
        if (prev and prev['col'] == r['col'] and abs(prev['top'] - r['top']) <= 2 and prev['family'] == r['family']
                and prev['color'] == r['color'] and prev['size'] == r['size'] and 0 <= r['left'] - (prev['left'] + prev['width']) < 25):
            hueco = r['left'] - (prev['left'] + prev['width'])
            junto = prev['texto'].endswith(' ') or r['texto'].startswith(' ')
            prev['texto'] += r['texto'] if (junto or hueco <= r['size'] * 0.12) else ' ' + r['texto']
            prev['width'] = r['left'] + r['width'] - prev['left']
        else:
            salida.append(dict(r))
    return salida


def tipo(r):
    fam, color = r['family'], r['color'].lower()
    if 'Wingdings' in fam:
        return 'vineta'
    color_area = color not in ('#241f1f', '#000000', '#231f20', '#ffffff', '#1d1d1b', '#222221')
    if not color_area:
        return 'texto'
    if r['size'] < 16:
        return 'nada'                      # textos de dibujos y tablas de los ejemplos (el enunciado va en 17)
    if r['size'] >= 30:
        return 'numero'
    if r['size'] >= 18 and r['top'] < 140:
        return 'grado'
    t = limpio(r['texto']).lower()
    if t.startswith('evidencias de') or t in ('evidencias', 'aprendizaje') or t.rstrip(':') in ('ejemplo', 'ejemplos'):
        return 'seccion'
    return 'enunciado'


# «fi» y «fl» que la capa de texto de algunas cartillas pierde (queda un espacio): solo palabras conocidas
_LIGADURAS = re.compile(r'\b(geográ|grá|signi|cientí|identi|clasi|especí|bene|modi|justi|cali|veri|plani|demográ|bibliográ|topográ|'
                        r'cartográ|pací|super|su|de|o|a|di|in|con|re|con)\s(cos|cas|co|ca|ca[cn]i[oó]n|caciones|cado|cados|cada|cadas|'
                        r'ciente|cientes|cial|ciales|cie|cies|nición|niciones|nir|nen|ne|cultad|cultades|cio|cios|exión|exiones|uye|uyen|'
                        r'ujo|ujos|ctos?|car|cativo|cativa|cativos|cativas)\b')
_RAICES_FL = ('re', 'in', 'con', 'super', 'a', 'di')


def _ligaduras(t):
    def cambio(m):
        raiz, cola = m.group(1), m.group(2)
        lig = 'fl' if raiz in _RAICES_FL and cola[:2] in ('ex', 'uy', 'uj', 'ct') else 'fi'
        if raiz in ('de', 'o', 'a', 'di', 'in', 'con', 're', 'su') and lig == 'fi' and cola not in ('ne', 'nen', 'nir', 'nición', 'niciones', 'ciente', 'cientes', 'cio', 'cios', 'cultad', 'cultades', 'cial', 'ciales', 'cie', 'cies'):
            return m.group(0)                      # «de cada», «o como»: palabras normales, no se tocan
        return raiz + lig + cola
    return _LIGADURAS.sub(cambio, t)


# Errores de la capa de texto de las cartillas (la palabra está bien en el PDF impreso, pero sin espacios en el texto)
CORRECCIONES = {
    'Comprendelaimportanciadelasasociaciones,': 'Comprende la importancia de las asociaciones,',   # Sociales 8.º, DBA 8
}


def limpio(t):
    t = re.sub(r'\s+', ' ', t).strip()
    for mal, bien in CORRECCIONES.items():
        t = t.replace(mal, bien)
    return _ligaduras(re.sub(r'^[´`¨^~]+\s*', '', t))


# Lo que se cuela de la página en la última evidencia: créditos de fotos, notas al pie y la contraportada
_COLADO = re.compile(r'\s+(Fotos?\s+tomadas?\b|Fotografía\s+tomada\b|Machu Picchu \(|Centro Administrativo Nacional\b|'
                     r'No se espera en este nivel escolar\b|Las reglas de juego serán…).*$')
# Renglones que el PDF trae con las letras en desorden (se dejan tal cual dicen las cartillas impresas)
_REVUELTOS = {'C om para l a e st r uc t ura soc ial , po íl it c a y económica': 'Compara la estructura social, política y económica',
              'ap licación ,': 'aplicación,', 'que é stas traen': 'que éstas traen', 'instrume n tos': 'instrumentos'}


def pulir_evidencias(evidencias):
    """Une los renglones que quedaron partidos (el siguiente empieza en minúscula) y quita lo que se coló de la página."""
    salida = []
    for e in evidencias:
        if salida and (e[:1].islower() or (len(salida[-1]) < 12 and not salida[-1].endswith('.'))):
            salida[-1] += ' ' + e
        else:
            salida.append(e)
    limpias = []
    for e in salida:
        for mal, bien in _REVUELTOS.items():
            e = e.replace(mal, bien)
        e = _COLADO.sub('', e).strip()
        if e:
            limpias.append(e)
    return limpias


def extraer(pdf):
    dbas, actual, modo, grado = [], None, None, None
    for pag, filas in lineas(pdf):
        # el grado de la página: su título «… • Grado 6º» (en la primera página del grado se lee después del DBA 1)
        titulo = ' '.join(r['texto'] for r in sorted(filas, key=lambda r: (r['top'], r['left']))
                          if r['size'] >= 18 and 'Medium' in r['family'] and r['color'].lower() not in ('#241f1f', '#ffffff') and r['top'] < 140)
        m = re.search(r'Grado\s*(\d+)', titulo)
        if m:
            grado = m.group(1)
        elif re.search(r'Transici', titulo):
            grado = '0'
        if not m and grado is None:
            continue                       # páginas de presentación, antes del primer grado
        if actual is not None and actual['numero'] is None:
            modo = None                    # lo que quedó sin número en la página anterior no se mezcla
        for r in filas:
            k, texto = tipo(r), r['texto']
            if k == 'grado':
                m = re.search(r'Grado\s*(\d+|Transici)', texto)
                if m:
                    grado = m.group(1)
                continue
            if k == 'numero':
                n = re.match(r'\s*(\d+)\.?', texto)
                if not n:
                    continue
                if actual is not None and actual['numero'] is None and modo == 'enunciado':
                    actual['numero'] = int(n.group(1))
                else:
                    actual = {'grado': grado, 'numero': int(n.group(1)), 'enunciado': '', 'evidencias': [], 'pagina': pag}
                    dbas.append(actual)
                modo = 'enunciado'
            elif k == 'enunciado':
                if modo != 'enunciado' or actual is None:
                    actual = {'grado': grado, 'numero': None, 'enunciado': '', 'evidencias': [], 'pagina': pag}
                    dbas.append(actual)
                    modo = 'enunciado'
                actual['enunciado'] += ' ' + texto
            elif k == 'seccion':
                t = limpio(texto).lower()
                modo = 'evidencias' if t.startswith('evidencias') else ('ejemplo' if t.startswith('ejemplo') else modo)
            elif k == 'texto' and modo == 'evidencias' and actual is not None:
                if r['abre'] or not actual['evidencias']:
                    actual['evidencias'].append('')
                actual['evidencias'][-1] += ' ' + texto
    salida = []
    for d in dbas:
        d['enunciado'] = limpio(d['enunciado'])
        d['evidencias'] = pulir_evidencias([limpio(e) for e in d['evidencias'] if limpio(e)])
        if d['enunciado'] and d['grado'] and d['numero']:
            salida.append(d)
    return salida


if __name__ == '__main__':
    datos = extraer(sys.argv[1])
    json.dump(datos, open(sys.argv[2], 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    from collections import Counter
    print(len(datos), 'DBA ·', dict(Counter(d['grado'] for d in datos)))
