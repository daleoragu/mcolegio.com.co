# notas/views/importar_views.py
"""Importaciones masivas con vista previa. La lógica está en notas/importar.py."""
from django.contrib import messages
from django.http import Http404, HttpResponse, HttpResponseNotFound
from django.shortcuts import redirect, render
from django.utils.text import slugify
from django.views.decorators.http import require_POST

from .. import importar as imp
from ..models import AsignacionDocente, Curso, Docente, Estudiante, Materia
from ..permisos import admin_requerido

XLSX = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'


def _tipo(tipo):
    if tipo not in imp.TIPOS:
        raise Http404
    return imp.TIPOS[tipo]


@admin_requerido
def importacion(request):
    colegio = getattr(request, 'colegio', None)
    if colegio is None:
        return HttpResponseNotFound('<h1>Colegio no configurado</h1>')
    cuantos = {
        'cursos': Curso.objects.filter(colegio=colegio).count(),
        'docentes': Docente.objects.filter(colegio=colegio).count(),
        'materias': Materia.objects.filter(colegio=colegio).count(),
        'asignacion': AsignacionDocente.objects.filter(colegio=colegio).count(),
        'estudiantes': Estudiante.objects.filter(colegio=colegio, is_active=True).count(),
    }
    tarjetas = [{'clave': t, 'paso': i, 'cuantos': cuantos[t], **imp.TIPOS[t],
                 'obligatorias': [c.titulo for c in imp.columnas(t) if c.obligatoria]}
                for i, t in enumerate(imp.ORDEN, start=1)]
    return render(request, 'notas/importar/inicio.html', {'tarjetas': tarjetas, 'page_title': 'Importar datos'})


@admin_requerido
def plantilla(request, tipo):
    info = _tipo(tipo)
    con_datos = request.GET.get('datos') == '1'
    datos = imp.plantilla(tipo, request.colegio, con_datos=con_datos)
    r = HttpResponse(datos, content_type=XLSX)
    nombre = f'{slugify(info["titulo"])}_{"actual" if con_datos else "plantilla"}_{slugify(request.colegio.nombre)[:30]}.xlsx'
    r['Content-Disposition'] = f'attachment; filename="{nombre}"'
    return r


@admin_requerido
@require_POST
def revisar(request, tipo):
    info = _tipo(tipo)
    archivo = request.FILES.get('archivo')
    if archivo is None:
        messages.error(request, 'Escoja el archivo.')
        return redirect('notas:importacion_datos')
    try:
        filas, reconocidas = imp.leer(archivo, tipo)
    except imp.ArchivoInvalido as e:
        messages.error(request, f'{info["titulo"]}: {e}')
        return redirect('notas:importacion_datos')
    if not filas:
        messages.warning(request, f'{info["titulo"]}: el archivo no tiene filas con datos.')
        return redirect('notas:importacion_datos')
    resultados = imp.revisar(tipo, filas, request.colegio)
    request.session[f'importar:{tipo}'] = {'filas': filas, 'archivo': archivo.name}
    no_reconocidas = [c.titulo for c in imp.columnas(tipo) if c.titulo not in reconocidas]
    return render(request, 'notas/importar/revisar.html', {
        'tipo': tipo, 'info': info, 'resultados': resultados, 'resumen': imp.resumen(resultados),
        'archivo': archivo.name, 'reconocidas': reconocidas, 'no_reconocidas': no_reconocidas,
        'page_title': f'Importar {info["titulo"].lower()}: revisar'})


@admin_requerido
@require_POST
def aplicar(request, tipo):
    info = _tipo(tipo)
    guardado = request.session.pop(f'importar:{tipo}', None)
    if not guardado:
        messages.error(request, 'La revisión venció. Vuelva a subir el archivo.')
        return redirect('notas:importacion_datos')
    filas = [(n, d) for n, d in guardado['filas']]
    resumen, credenciales, resultados = imp.aplicar(tipo, filas, request.colegio)
    if credenciales:
        request.session['importar:credenciales'] = credenciales
    return render(request, 'notas/importar/listo.html', {
        'tipo': tipo, 'info': info, 'resumen': resumen, 'credenciales': credenciales,
        'errores': [r for r in resultados if r['accion'] == 'error'], 'archivo': guardado.get('archivo', ''),
        'siguiente': next((imp.TIPOS[t] | {'clave': t} for t in imp.ORDEN[imp.ORDEN.index(tipo) + 1:]), None),
        'page_title': f'Importar {info["titulo"].lower()}: listo'})


@admin_requerido
def credenciales(request):
    datos = request.session.get('importar:credenciales') or []
    if not datos:
        messages.info(request, 'No hay usuarios nuevos para descargar.')
        return redirect('notas:importacion_datos')
    r = HttpResponse(imp.credenciales_xlsx(datos, request.colegio), content_type=XLSX)
    r['Content-Disposition'] = f'attachment; filename="usuarios_nuevos_{slugify(request.colegio.nombre)[:30]}.xlsx"'
    return r
