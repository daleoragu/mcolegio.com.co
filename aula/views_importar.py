"""Importar notas al aula (Excel, CSV o tabla pegada) y rejillas de rúbrica a una tarea."""
from decimal import Decimal

from django.contrib import messages
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from . import importar, logica
from .models import ColumnaManual, Entrega, NotaManual, Tarea
from .views import _ctx, _render, vista_aula

MAX_HOJAS = 6


def _llave(pk):
    return f'aula_importar_{pk}'


def _leer_subida(request):
    """{'hojas': [nombres], 'tablas': [filas por hoja], 'nombre': archivo}"""
    archivo = request.FILES.get('archivo')
    texto = request.POST.get('texto') or ''
    if archivo is None:
        filas, _ = importar.leer_archivo(texto=texto)
        return {'hojas': [], 'tablas': [filas], 'nombre': 'Tabla pegada'}
    if logica.muy_grande(archivo):
        raise ValueError(f'El archivo pasa de {logica.MAX_ARCHIVO_MB} MB.')
    filas, hojas = importar.leer_archivo(archivo=archivo, hoja=0)
    tablas = [filas]
    for k in range(1, min(len(hojas), MAX_HOJAS)):
        archivo.seek(0)
        tablas.append(importar.leer_archivo(archivo=archivo, hoja=k)[0])
    return {'hojas': hojas[:MAX_HOJAS], 'tablas': tablas, 'nombre': archivo.name[:120]}


@vista_aula
def importar_notas(request, pk):
    c = _ctx(request, pk, docente=True)
    aula = c.aula
    llave = _llave(pk)
    minima, maxima = logica.rango(aula)
    if request.method == 'POST' and request.POST.get('accion') == 'leer':
        try:
            subida = _leer_subida(request)
        except ValueError as e:
            messages.error(request, str(e))
            return redirect('aula:importar', pk=pk)
        if not any(subida['tablas']):
            messages.warning(request, 'No se encontró ninguna tabla. Suba el archivo o pegue la tabla con sus encabezados.')
            return redirect('aula:importar', pk=pk)
        request.session[llave] = subida
        return redirect(reverse('aula:importar', args=[pk]) + '?paso=revisar')

    subida = request.session.get(llave)
    if request.GET.get('paso') != 'revisar' and request.method != 'POST' or subida is None:
        request.session.pop(llave, None)
        return _render(request, c, 'aula/importar.html', {'paso': 'subir', 'minima': minima, 'maxima': maxima},
                       'calificaciones')

    try:
        hoja = int(request.POST.get('hoja', request.GET.get('hoja', 0)))
    except ValueError:
        hoja = 0
    hoja = hoja if 0 <= hoja < len(subida['tablas']) else 0
    analisis = importar.analizar(subida['tablas'][hoja], maxima)
    personas = logica.estudiantes(aula)
    por_clave = {logica.clave_de(p): p for p in personas}

    if request.method == 'POST' and request.POST.get('accion') == 'importar' and analisis:
        return _importar(request, c, analisis, por_clave, minima, maxima, llave)

    emparejados = importar.emparejar(analisis['registros'], personas) if analisis else []
    for r, p in zip(analisis['registros'] if analisis else [], emparejados):
        r['clave'] = logica.clave_de(p) if p else ''
    periodos = []
    if aula.colegio_id:
        from notas.models import PeriodoAcademico
        periodos = list(PeriodoAcademico.objects.filter(colegio=aula.colegio).order_by('-ano_lectivo', 'orden')[:8])
    return _render(request, c, 'aula/importar.html', {
        'paso': 'revisar', 'subida': subida, 'hoja': hoja, 'analisis': analisis,
        'opciones': [(logica.clave_de(p), logica.nombre_de(p)) for p in personas],
        'sin_pareja': sum(1 for p in emparejados if p is None),
        'minima': minima, 'maxima': maxima, 'periodos': periodos,
        'periodo_sugerido': next((p for p in periodos if p.esta_activo), None),
        'componentes': logica.componentes_de(aula)}, 'calificaciones')


def _importar(request, c, analisis, por_clave, minima, maxima, llave):
    aula = c.aula
    elegidas = []
    for k, col in enumerate(analisis['columnas']):
        if request.POST.get(f'usar-{k}') != 'on':
            continue
        titulo = (request.POST.get(f'titulo-{k}') or col['titulo']).strip()[:60] or col['titulo']
        maximo = importar.numero(request.POST.get(f'max-{k}'))
        if isinstance(maximo, tuple) or (maximo is not None and maximo <= 0):
            maximo = None
        elegidas.append((k, titulo, maximo))
    if not elegidas:
        messages.warning(request, 'Marque al menos una columna para importar.')
        return redirect(reverse('aula:importar', args=[aula.pk]) + '?paso=revisar')

    quienes = []
    for i, r in enumerate(analisis['registros']):
        p = por_clave.get(request.POST.get(f'quien-{i}', ''))
        if p is not None:
            quienes.append((r, p))
    if not quienes:
        messages.warning(request, 'Ninguna fila quedó emparejada con un estudiante.')
        return redirect(reverse('aula:importar', args=[aula.pk]) + '?paso=revisar')

    periodo = componente = None
    if not aula.es_salon:
        from notas.models import PeriodoAcademico
        periodo = PeriodoAcademico.objects.filter(colegio=aula.colegio, pk=request.POST.get('periodo') or 0).first()
        componente = request.POST.get('componente') or ''

    resumen, errores = [], []
    for k, titulo, maximo in elegidas:
        pares = []
        for r, p in quienes:
            valor = importar.numero(r['valores'][k])
            if valor is None:
                if r['valores'][k].strip():
                    errores.append(f'{logica.nombre_de(p)} · {titulo}: «{r["valores"][k]}» no es un número.')
                continue
            pares.append((p, importar.a_la_escala(valor, maximo, minima, maxima)))
        if aula.es_salon:
            col = aula.columnas_manuales.filter(titulo=titulo).first() or ColumnaManual.objects.create(
                aula=aula, titulo=titulo, orden=aula.columnas_manuales.count())
            for p, nota in pares:
                NotaManual.objects.update_or_create(columna=col, **logica.filtro_persona(p), defaults={'nota': nota})
            resumen.append(f'«{titulo}»: {len(pares)}')
        else:
            n, error = logica.pasar_notas_a_planilla(aula, periodo, componente, titulo, pares)
            if error:
                messages.error(request, error)
                return redirect(reverse('aula:importar', args=[aula.pk]) + '?paso=revisar')
            resumen.append(f'«{titulo}»: {n}')
    request.session.pop(llave, None)
    destino = 'la planilla del grupo' if aula.es_salon else 'la planilla oficial'
    messages.success(request, f'Notas importadas a {destino} — ' + ' · '.join(resumen) + '.')
    for e in errores[:8]:
        messages.warning(request, e)
    return redirect('aula:calificaciones', pk=aula.pk)


# ---------------------------------------------------------------------------
# Rejillas de rúbrica
# ---------------------------------------------------------------------------
@vista_aula
def rejilla_plantilla(request, pk, tid):
    c = _ctx(request, pk, docente=True)
    t = get_object_or_404(Tarea.objects.select_related('instrumento'), pk=tid, aula=c.aula, instrumento__isnull=False)
    r = HttpResponse(importar.plantilla_rejilla(t, logica.personas_de(t, c.aula)),
                     content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    r['Content-Disposition'] = f'attachment; filename="Rejilla {t.titulo}.xlsx"'
    return r


@require_POST
@vista_aula
def rejilla_importar(request, pk, tid):
    c = _ctx(request, pk, docente=True)
    aula = c.aula
    t = get_object_or_404(Tarea.objects.select_related('instrumento'), pk=tid, aula=aula, instrumento__isnull=False)
    try:
        if request.FILES.get('archivo'):
            filas, _ = importar.leer_archivo(archivo=request.FILES['archivo'])
        else:
            filas, _ = importar.leer_archivo(texto=request.POST.get('texto') or '')
    except ValueError as e:
        messages.error(request, str(e))
        return redirect('aula:tarea', pk=pk, tid=tid)
    inst = t.instrumento
    resultado = importar.leer_rejilla(filas, inst, logica.personas_de(t, aula))
    minima, maxima = logica.rango(aula)
    completas = parciales = 0
    for p, sel in resultado['calificados']:
        nota, completa = logica.calcular_nota(inst, sel, minima, maxima)
        e = logica.entrega_de(t, p) or Entrega(tarea=t, **logica.filtro_persona(p))
        e.seleccion = sel
        if completa:
            e.nota, e.estado, e.calificada = nota, 'calificada', timezone.now()
            completas += 1
        else:
            parciales += 1
        e.save()
    if completas or parciales:
        texto = f'Rejilla importada: {completas} estudiante(s) calificados'
        if parciales:
            texto += f'; {parciales} con criterios sin llenar (quedan sin nota hasta completarlos en la grilla)'
        messages.success(request, texto + '.')
    else:
        messages.warning(request, 'No se calificó a nadie: revise que la rejilla tenga la columna de los nombres '
                                  'y una columna por criterio con los mismos nombres de la rúbrica.')
    if resultado['criterios_sin_columna']:
        messages.warning(request, 'No se encontró la columna de: ' + ', '.join(resultado['criterios_sin_columna'][:6]) + '.')
    if resultado['sin_estudiante']:
        messages.warning(request, 'Sin estudiante en la clase: ' + ', '.join(resultado['sin_estudiante'][:10]) + '.')
    for e in resultado['errores'][:6]:
        messages.warning(request, e)
    return redirect('aula:tarea', pk=pk, tid=tid)
