"""Departamentos y municipios de Colombia con su código DANE (DIVIPOLA), para el menú encadenado de la inscripción,
el perfil y los filtros por región del banco y la biblioteca.

Fuente: DANE · DIVIPOLA, «Códigos municipios» (datos.gov.co, conjunto gdxc-w37w): 32 departamentos y Bogotá D.C.,
1 103 municipios, 18 áreas no municipalizadas y 1 isla. El archivo está en salon_digital/datos/divipola.json.
"""
import json
import os
import unicodedata
from functools import lru_cache

PAIS = 'Colombia'


def normal(texto):
    """Sin tildes, minúsculas y sin signos: para comparar lo que la gente escribe («ibague» = «Ibagué»)."""
    t = unicodedata.normalize('NFD', str(texto or '').lower())
    t = ''.join(c for c in t if unicodedata.category(c) != 'Mn')
    return ' '.join(''.join(c if c.isalnum() else ' ' for c in t).split())


@lru_cache(maxsize=1)
def _datos():
    with open(os.path.join(os.path.dirname(__file__), 'datos', 'divipola.json'), encoding='utf-8') as f:
        d = json.load(f)
    deps = sorted(((c, n) for c, n in d['departamentos']), key=lambda x: normal(x[1]))
    muns = {m[0]: {'codigo': m[0], 'nombre': m[1], 'dep': m[2], 'tipo': m[3]} for m in d['municipios']}
    por_dep = {}
    for m in sorted(muns.values(), key=lambda x: normal(x['nombre'])):
        por_dep.setdefault(m['dep'], []).append(m)
    return {'deps': deps, 'dep_nombre': dict(deps), 'muns': muns, 'por_dep': por_dep}


def departamentos():
    return _datos()['deps']


def municipios(dep):
    return _datos()['por_dep'].get(str(dep or ''), [])


def municipio(codigo):
    return _datos()['muns'].get(str(codigo or ''))


def nombre_departamento(codigo):
    return _datos()['dep_nombre'].get(str(codigo or '')[:2], '')


def etiqueta(codigo):
    """«Ibagué, Tolima» (o «Bogotá, D.C.»)."""
    m = municipio(codigo)
    if not m:
        return ''
    dep = nombre_departamento(m['dep'])
    return m['nombre'] if m['codigo'] == '11001' else f"{m['nombre']}, {dep}"


def menu():
    """Lo que necesita el menú encadenado en la página: {departamentos: [[cod, nombre]], municipios: {dep: [[cod, nombre]]}}."""
    d = _datos()
    return {'departamentos': d['deps'], 'municipios': {k: [[m['codigo'], m['nombre']] for m in v] for k, v in d['por_dep'].items()}}


def de_usuario(user, colegio=None):
    """El municipio (código DANE) de un docente: el de su cuenta de Mi Salón o, en un colegio, el del colegio."""
    cuenta = getattr(user, 'cuenta_salon', None) if getattr(user, 'is_authenticated', False) else None
    try:
        if cuenta is not None and cuenta.municipio_dane:
            return cuenta.municipio_dane
    except Exception:
        pass
    if colegio is not None:
        conf = getattr(colegio, 'config_simat', None)
        try:
            if conf is not None and municipio(conf.municipio):
                return conf.municipio
        except Exception:
            return ''
    return ''


def reconocer(municipio_texto, departamento_texto=''):
    """El código DANE de un municipio escrito a mano («ibague», «Ibagué, Tolima», «Bogota»), o '' si hay duda.
    Si el nombre se repite en varios departamentos (p. ej. «Armenia», «La Unión»), usa el departamento escrito."""
    texto = normal(municipio_texto)
    if not texto:
        return ''
    d = _datos()
    dep_txt = normal(departamento_texto)
    # «Ibagué, Tolima» o «Ibagué - Tolima» en el mismo campo
    for dep_cod, dep_nombre in d['deps']:
        nd = normal(dep_nombre)
        if texto.endswith(' ' + nd) and len(texto) > len(nd):
            texto, dep_txt = texto[:-len(nd)].strip(), dep_txt or nd
            break
    if texto in ('bogota', 'bogota d c', 'bogota dc', 'santa fe de bogota'):
        return '11001'
    candidatos = [m for m in d['muns'].values() if normal(m['nombre']) == texto]
    if dep_txt:
        del_dep = [m for m in candidatos if normal(d['dep_nombre'][m['dep']]) == dep_txt]
        if del_dep:
            candidatos = del_dep
    return candidatos[0]['codigo'] if len(candidatos) == 1 else ''
