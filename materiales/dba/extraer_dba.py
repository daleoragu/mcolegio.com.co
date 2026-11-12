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
            filas.append({'top': int(t.get('top')), 'left': int(t.get('left')), 'texto': texto, 'size': int(f['size']),
                          'family': f['family'], 'color': f['color'], 'pag': int(pagina.get('number'))})
        # columna izquierda y luego la derecha, cada una de arriba abajo
        filas = [r for r in filas if not MARCAS.search(r['texto'])]
        for r in filas:
            r['col'] = r['left'] >= ancho * 0.47
        # Una línea de texto abre una evidencia nueva si tiene una viñeta a su misma altura (±4 px) en su columna
        vinetas = [r for r in filas if 'Wingdings' in r['family']]
        for r in filas:
            r['abre'] = any(v['col'] == r['col'] and abs(v['top'] - r['top']) <= 4 and v['left'] < r['left'] for v in vinetas)
        filas = [r for r in filas if 'Wingdings' not in r['family']]
        filas.sort(key=lambda r: (r['col'], r['top'], r['left']))
        yield int(pagina.get('number')), filas


def tipo(r):
    fam, color = r['family'], r['color'].lower()
    if 'Wingdings' in fam:
        return 'vineta'
    verde = color not in ('#241f1f', '#000000', '#231f20', '#ffffff')
    if verde and 'Medium' in fam and r['size'] >= 30:
        return 'numero'
    if verde and 'Medium' in fam and r['size'] >= 18 and r['top'] < 140:
        return 'grado'
    if verde and 'Medium' in fam:
        return 'enunciado'
    if verde:
        return 'seccion'
    if color == '#ffffff':
        return 'nada'
    return 'texto'


def limpio(t):
    return re.sub(r'\s+', ' ', t).strip()


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
        d['evidencias'] = [limpio(e) for e in d['evidencias'] if limpio(e)]
        if d['enunciado'] and d['grado'] and d['numero']:
            salida.append(d)
    return salida


if __name__ == '__main__':
    datos = extraer(sys.argv[1])
    json.dump(datos, open(sys.argv[2], 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    from collections import Counter
    print(len(datos), 'DBA ·', dict(Counter(d['grado'] for d in datos)))
