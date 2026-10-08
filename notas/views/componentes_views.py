# notas/views/componentes_views.py
"""Componentes de evaluación: cuántas columnas de nota tiene el colegio y cómo se llaman.

No todos los colegios califican con SER, SABER y HACER: uno puede tener un solo
componente y otro cinco. Aquí el administrador los agrega, los quita, les pone
nombre y abreviatura y los ordena. Es lo que sale en el encabezado del boletín y
en las planillas (en línea, Excel y PDF), el ingreso de notas y PuntoExacto.

Un componente que ya tiene notas en el año no se puede quitar.
"""
from django.contrib import messages
from django.db import transaction
from django.http import HttpResponseNotFound
from django.shortcuts import redirect, render

from .. import componentes as comp
from ..models import Materia
from ..models.academicos import CODIGOS_COMPONENTE, CODIGOS_LEGADO, ComponenteEvaluacion
from ..permisos import admin_requerido

LARGO_NOMBRE = 30
LARGO_ABREVIATURA = 10
MAXIMO = len(CODIGOS_COMPONENTE)


def _materias_con_nombres_propios(colegio, actuales):
    """Asignaturas que le cambiaron el nombre a SER/SABER/HACER solo para ellas."""
    legado = [c for c in actuales if c.codigo in CODIGOS_LEGADO]
    salida = []
    for m in Materia.objects.filter(colegio=colegio).order_by('nombre'):
        propios = [(getattr(m, f'etiqueta_{c.codigo.lower()}', '') or '').strip() for c in legado]
        if any(p and p.upper() != c.codigo for p, c in zip(propios, legado)):
            salida.append({'materia': m, 'nombres': propios})
    return legado, salida


def _leer_filas(post):
    """Las filas tal como vienen del formulario, en el orden de la pantalla."""
    codigos = post.getlist('codigo')
    nombres = post.getlist('nombre')
    abrevs = post.getlist('abreviatura')
    filas = []
    for i, codigo in enumerate(codigos):
        filas.append({
            'codigo': (codigo or '').strip().upper(),
            'nombre': ' '.join((nombres[i] if i < len(nombres) else '').split()),
            'abreviatura': ' '.join((abrevs[i] if i < len(abrevs) else '').split()),
        })
    return filas


def _validar(colegio, filas, actuales):
    errores = []
    if not filas:
        errores.append('Debe quedar al menos un componente.')
    if len(filas) > MAXIMO:
        errores.append(f'Máximo {MAXIMO} componentes.')
    por_codigo = {c.codigo: c for c in actuales}
    vistos = set()
    for i, f in enumerate(filas, 1):
        if f['codigo'] and f['codigo'] not in por_codigo:
            errores.append(f'La fila {i} no corresponde a un componente de este colegio. Recargue la página.')
        if not f['nombre']:
            errores.append(f'Escriba el nombre del componente {i}.')
        elif len(f['nombre']) > LARGO_NOMBRE:
            errores.append(f'El nombre «{f["nombre"]}» es muy largo (máximo {LARGO_NOMBRE} letras).')
        if len(f['abreviatura']) > LARGO_ABREVIATURA:
            errores.append(f'La abreviatura «{f["abreviatura"]}» es muy larga (máximo {LARGO_ABREVIATURA}).')
        clave = f['nombre'].upper()
        if clave and clave in vistos:
            errores.append('Cada componente debe tener un nombre distinto.')
        vistos.add(clave)
    codigos_enviados = [f['codigo'] for f in filas if f['codigo']]
    if len(codigos_enviados) != len(set(codigos_enviados)):
        errores.append('Hay un componente repetido. Recargue la página.')
    # Los que se quitan no pueden tener notas este año.
    for c in actuales:
        if c.codigo not in codigos_enviados:
            cuantas, materias, ano = comp.notas_del_componente(colegio, c.codigo)
            if cuantas:
                lista = ', '.join(materias[:5]) + ('…' if len(materias) > 5 else '')
                errores.append(f'«{c.nombre}» no se puede quitar: ya tiene notas en {ano} ({lista}).')
    nuevos = sum(1 for f in filas if not f['codigo'])
    if nuevos > len(comp.codigos_libres(colegio)):
        errores.append('No quedan más componentes disponibles.')
    return list(dict.fromkeys(errores))


@transaction.atomic
def _guardar(colegio, filas, actuales):
    antes = [c.codigo for c in actuales]
    por_codigo = {c.codigo: c for c in actuales}
    libres = comp.codigos_libres(colegio)
    enviados = {f['codigo'] for f in filas if f['codigo']}
    ComponenteEvaluacion.objects.filter(colegio=colegio).exclude(codigo__in=enviados).delete()
    despues = []
    for orden, f in enumerate(filas, 1):
        if f['codigo']:
            c = por_codigo[f['codigo']]
        else:
            c = ComponenteEvaluacion(colegio=colegio, codigo=libres.pop(0))
        c.nombre, c.abreviatura, c.orden = f['nombre'], f['abreviatura'], orden
        c.save()
        despues.append(c.codigo)
    if antes != despues:
        comp.reajustar_pesos(colegio, antes, despues)
    comp.sincronizar_configuracion(colegio)
    return [c for c in despues if c not in antes], [c for c in antes if c not in despues]


@admin_requerido
def componentes_evaluacion(request):
    colegio = getattr(request, 'colegio', None)
    if colegio is None:
        return HttpResponseNotFound('<h1>Colegio no configurado</h1>')
    actuales = comp.componentes(colegio)
    errores = []

    if request.method == 'POST' and request.POST.get('accion') == 'unificar':
        # Las asignaturas vuelven a los nombres del colegio.
        n = Materia.objects.filter(colegio=colegio).update(etiqueta_ser='SER', etiqueta_saber='SABER',
                                                           etiqueta_hacer='HACER')
        messages.success(request, f'Listo: {n} asignatura(s) usan ahora los nombres del colegio.')
        return redirect('notas:componentes_evaluacion')

    if request.method == 'POST':
        filas = _leer_filas(request.POST)
        errores = _validar(colegio, filas, actuales)
        if not errores:
            agregados, quitados = _guardar(colegio, filas, actuales)
            texto = 'Componentes guardados. Ya salen en el boletín, las planillas y el ingreso de notas.'
            if agregados:
                texto += (' Los nuevos empiezan en 0 %: póngales su porcentaje en «Permisos de porcentajes»'
                          ' (o use ponderación equitativa) para que aparezcan en las planillas.')
            if quitados:
                texto += ' Lo que pesaban los que quitó se repartió entre los que quedan.'
            messages.success(request, texto)
            return redirect('notas:componentes_evaluacion')
    else:
        filas = [{'codigo': c.codigo, 'nombre': c.nombre, 'abreviatura': c.abreviatura} for c in actuales]

    # Cuáles tienen notas este año (esos no se pueden quitar).
    for f in filas:
        f['notas'], f['materias'] = 0, []
        if f['codigo']:
            f['notas'], f['materias'], _ = comp.notas_del_componente(colegio, f['codigo'])

    legado, propias = _materias_con_nombres_propios(colegio, actuales)
    return render(request, 'notas/admin_tools/componentes_evaluacion.html', {
        'filas': filas, 'errores': errores, 'maximo': MAXIMO,
        'largo_nombre': LARGO_NOMBRE, 'largo_abreviatura': LARGO_ABREVIATURA,
        'legado': legado, 'propias': propias,
        'page_title': 'Componentes de evaluación'})
