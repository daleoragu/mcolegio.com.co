"""Catálogo de los Derechos Básicos de Aprendizaje (DBA) oficiales del MEN, copiados tal cual de las cartillas.

Los datos están en materiales/datos/dba/<área>.json (uno por área) y se extraen con materiales/dba/extraer_dba.py.
Cada DBA tiene un código estable «MAT-6-3» (área, grado, número) que se guarda en los materiales y las preguntas.

Áreas SIN DBA (Ética, Religión, Artística, Educación Física, Tecnología, Filosofía, técnicas…): el MEN las orienta
con lineamientos y orientaciones curriculares; ahí la plataforma pide «Competencia o desempeño» en texto libre.
"""
import json
import os
import re
from functools import lru_cache

CARPETA = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'datos', 'dba')

# Cómo escriben el área los docentes → archivo del catálogo
SINONIMOS = {
    'MAT': ('matematica', 'matematicas', 'geometria', 'estadistica', 'aritmetica', 'algebra', 'trigonometria', 'calculo',
            'pensamiento matematico', 'pre calculo', 'precalculo'),
    'LEN': ('lenguaje', 'castellano', 'espanol', 'lengua castellana', 'lectura', 'lectoescritura', 'comunicacion'),
    'NAT': ('naturales', 'ciencias naturales', 'biologia', 'quimica', 'fisica', 'ciencias naturales y educacion ambiental'),
    'SOC': ('sociales', 'ciencias sociales', 'historia', 'geografia', 'democracia', 'catedra de la paz'),
}
ARCHIVOS = {'MAT': 'matematicas.json', 'LEN': 'lenguaje.json', 'NAT': 'naturales.json', 'SOC': 'sociales.json'}
GRADOS_TEXTO = {'primero': 1, 'segundo': 2, 'tercero': 3, 'cuarto': 4, 'quinto': 5, 'sexto': 6, 'septimo': 7, 'octavo': 8,
                'noveno': 9, 'decimo': 10, 'once': 11, 'undecimo': 11, 'onceavo': 11}


def _normal(texto):
    from salon_digital.regiones import normal
    return normal(texto)


@lru_cache(maxsize=8)
def _area(clave):
    ruta = os.path.join(CARPETA, ARCHIVOS.get(clave, ''))
    if clave not in ARCHIVOS or not os.path.exists(ruta):
        return None
    with open(ruta, encoding='utf-8') as f:
        return json.load(f)


def clave_area(texto):
    """'MAT' si el área escrita tiene catálogo de DBA; '' si no (áreas sin DBA o desconocidas)."""
    t = _normal(texto)
    for clave, nombres in SINONIMOS.items():
        if any(t == n or t.startswith(n + ' ') or n in t.split() for n in nombres) and _area(clave):
            return clave
    return ''


def grado_num(texto):
    """'6', '6.º', 'Sexto', '601', 'grado 6' → 6; '' si no se entiende."""
    t = _normal(texto)
    if not t:
        return None
    for palabra, n in GRADOS_TEXTO.items():
        if palabra in t.split():
            return n
    m = re.search(r'\d+', t)
    if not m:
        return None
    n = int(m.group())
    if n > 11 and len(m.group()) == 3:          # «601» = grado 6, grupo 01
        n = int(m.group()[0])
    elif n > 11 and len(m.group()) == 4:        # «1001» = grado 10
        n = int(m.group()[:2])
    return n if 1 <= n <= 11 else None


def dbas(area, grado):
    """[{codigo, n, enunciado, evidencias}] del área (texto o clave) y el grado; [] si no hay catálogo."""
    clave = area if area in ARCHIVOS else clave_area(area)
    datos = _area(clave) if clave else None
    g = grado if isinstance(grado, int) else grado_num(grado)
    if not datos or not g:
        return []
    return [dict(d, codigo=f'{clave}-{g}-{d["n"]}') for d in datos['grados'].get(str(g), [])]


def buscar(codigo):
    """El DBA de un código «MAT-6-3» (con área y grado), o None."""
    m = re.fullmatch(r'([A-Z]{2,4})-(\d{1,2})-(\d{1,2})', str(codigo or ''))
    if not m:
        return None
    for d in dbas(m.group(1), int(m.group(2))):
        if d['n'] == int(m.group(3)):
            datos = _area(m.group(1))
            return dict(d, area=datos['area'], grado=int(m.group(2)), fuente=datos['fuente'])
    return None


def etiqueta(codigo, largo=200):
    """«DBA 3 · Matemáticas 6.º: Reconoce y establece…» para mostrar y guardar como texto."""
    d = buscar(codigo)
    if not d:
        return ''
    return f'DBA {d["n"]} · {d["area"]} {d["grado"]}.º: {d["enunciado"]}'[:largo]


def areas_con_dba():
    return [(c, _area(c)['area']) for c in ARCHIVOS if _area(c)]
