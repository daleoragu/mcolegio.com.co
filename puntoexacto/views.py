# -*- coding: utf-8 -*-
"""PuntoExacto · vistas.

Esta primera versión funciona SIN cámara: el docente crea el examen, imprime
las hojas, digita las respuestas y obtiene las notas y el análisis. El lector
de fotos se conecta después sin cambiar nada de lo que hay aquí.
"""
import datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Q
from django.http import HttpResponse, HttpResponseForbidden, Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.clickjacking import xframe_options_sameorigin

from notas.models.academicos import Materia
from notas.models.perfiles import Curso, Docente, Estudiante

from . import analisis as analisis_mod
from . import calificacion as calif
from . import hojas as hojas_mod
from .forms import ExamenForm
from .hojas import generar_pdf
from .models import COMPONENTES, METODOS, Bloque, Examen, Hoja, Pregunta, Respuesta


# ---------------------------------------------------------------------------
# Quién puede entrar
# ---------------------------------------------------------------------------

def _docente_de(request):
    """El docente de la sesión, o None si es administrador."""
    if not request.colegio:
        return None
    return Docente.objects.filter(user=request.user, colegio=request.colegio).first()


def _cursos_dirigidos(request):
    """Los cursos de los que este usuario es director de grado."""
    docente = _docente_de(request)
    if docente is None:
        return Curso.objects.none()
    return Curso.objects.filter(colegio=request.colegio, director_grado=docente)


def puede_censales(request):
    """Quién puede armar una prueba por bloques (censal).

    Decisión del colegio: el director de grado. Un examen por bloques produce
    una nota por área y puede tocar la planilla de varias asignaturas, así que
    no es cosa de cualquier docente; pero tampoco hay que subirlo hasta rectoría,
    porque el que aplica la prueba en el salón es el director de grupo.
    """
    return (request.user.is_superuser or _docente_de(request) is None
            or _cursos_dirigidos(request).exists())


def _examenes_visibles(request):
    """Un docente ve los suyos; un administrador, los de todo el colegio.

    El director de grado ve además los exámenes por bloques de los cursos que
    dirige, aunque los haya creado otro: es quien responde por esa aplicación.
    """
    base = Examen.objects.filter(colegio=request.colegio)
    docente = _docente_de(request)
    if request.user.is_superuser or docente is None:
        return base
    dirigidos = _cursos_dirigidos(request)
    if dirigidos.exists():
        return base.filter(Q(docente=docente) | Q(cursos__in=dirigidos)).distinct()
    return base.filter(docente=docente)


def _examen_o_404(request, examen_id):
    examen = get_object_or_404(_examenes_visibles(request), id=examen_id)
    return examen


# ---------------------------------------------------------------------------
# Lista y creación
# ---------------------------------------------------------------------------

@login_required
def lista(request):
    if not request.colegio:
        return HttpResponseForbidden('No se identificó el colegio.')
    mostrar_archivados = request.GET.get('archivados') == '1'
    busqueda = (request.GET.get('q') or '').strip()

    examenes = _examenes_visibles(request).filter(archivado=mostrar_archivados)
    if busqueda:
        examenes = examenes.filter(titulo__icontains=busqueda)
    examenes = examenes.select_related('asignacion__materia', 'asignacion__curso', 'periodo')

    return render(request, 'puntoexacto/lista.html', {
        'examenes': examenes, 'archivados': mostrar_archivados, 'busqueda': busqueda,
    })


@login_required
def crear(request):
    if not request.colegio:
        return HttpResponseForbidden('No se identificó el colegio.')
    docente = _docente_de(request)
    inicial = {'fecha': datetime.date.today()}
    form = ExamenForm(request.POST or None, colegio=request.colegio, docente=docente,
                      initial=inicial)
    if request.method == 'POST' and form.is_valid():
        with transaction.atomic():
            examen = form.save(commit=False)
            examen.colegio = request.colegio
            examen.docente = docente
            examen.save()
            form.save_m2m()
            _sincronizar_preguntas(examen)
            _aplicar_opciones(examen, request.POST.get('opciones_por_pregunta'))
        messages.success(request, 'Examen creado. Ahora defina la clave.')
        return redirect('puntoexacto:clave', examen_id=examen.id)
    return render(request, 'puntoexacto/crear.html', {
        'form': form, 'examen': None, 'opciones_actuales': '{}'})


@login_required
def editar(request, examen_id):
    examen = _examen_o_404(request, examen_id)
    docente = _docente_de(request)
    form = ExamenForm(request.POST or None, instance=examen,
                      colegio=request.colegio, docente=docente)
    if request.method == 'POST' and form.is_valid():
        with transaction.atomic():
            examen = form.save()
            _sincronizar_preguntas(examen)
            _aplicar_opciones(examen, request.POST.get('opciones_por_pregunta'))
            calif.calificar_examen(examen)
        messages.success(request, 'Examen actualizado y notas recalculadas.')
        return redirect('puntoexacto:clave', examen_id=examen.id)
    import json
    actuales = {str(p.numero): p.numero_opciones
                for p in examen.preguntas.all() if p.numero_opciones}
    return render(request, 'puntoexacto/crear.html', {
        'form': form, 'examen': examen,
        'opciones_actuales': json.dumps(actuales)})


def _aplicar_opciones(examen, crudo):
    """Guarda las opciones que el docente fijó pregunta por pregunta.

    Llega como JSON {"6": 8, "7": 8} desde la pantalla de creación. Lo que
    venga igual a las opciones del examen se guarda como vacío: así, si después
    el docente cambia el examen de 4 a 5 opciones, las preguntas que nunca tocó
    lo siguen a él en vez de quedarse congeladas en 4.
    """
    import json
    if not crudo:
        return
    try:
        mapa = json.loads(crudo)
    except (ValueError, TypeError):
        return
    if not isinstance(mapa, dict):
        return
    por_numero = {p.numero: p for p in examen.preguntas.all()}
    cambiadas = []
    for clave, valor in mapa.items():
        try:
            numero, opciones = int(clave), int(valor)
        except (ValueError, TypeError):
            continue
        p = por_numero.get(numero)
        if p is None or not (2 <= opciones <= 10):
            continue
        nuevo = None if opciones == examen.numero_opciones else opciones
        if p.numero_opciones != nuevo:
            p.numero_opciones = nuevo
            cambiadas.append(p)
    if cambiadas:
        Pregunta.objects.bulk_update(cambiadas, ['numero_opciones'])


def _sincronizar_preguntas(examen):
    """Crea o quita preguntas para que coincidan con el número configurado.

    Las que ya existen conservan su clave, puntaje y etiquetas: cambiar de 20 a
    25 preguntas no debe borrar el trabajo hecho.
    """
    existentes = {p.numero: p for p in examen.preguntas.all()}
    for n in range(1, examen.numero_preguntas + 1):
        if n not in existentes:
            Pregunta.objects.create(examen=examen, numero=n)
    sobrantes = [n for n in existentes if n > examen.numero_preguntas]
    if sobrantes:
        examen.preguntas.filter(numero__in=sobrantes).delete()


@login_required
def archivar(request, examen_id):
    examen = _examen_o_404(request, examen_id)
    examen.archivado = not examen.archivado
    examen.save(update_fields=['archivado'])
    messages.success(request, 'Examen archivado.' if examen.archivado else 'Examen restaurado.')
    return redirect('puntoexacto:lista')


# ---------------------------------------------------------------------------
# La clave
# ---------------------------------------------------------------------------

@login_required
def clave(request, examen_id):
    examen = _examen_o_404(request, examen_id)
    preguntas = list(examen.preguntas.order_by('numero'))

    if request.method == 'POST':
        with transaction.atomic():
            # Cómo se puntúa: a mano, pregunta por pregunta, o con una fórmula.
            metodo = (request.POST.get('metodo') or '').strip()
            if metodo in {c for c, _ in METODOS} and metodo != examen.metodo:
                examen.metodo = metodo
                examen.save(update_fields=['metodo'])
            for p in preguntas:
                p.correcta = (request.POST.get(f'correcta_{p.numero}') or '').strip().upper()[:1]
                bid = (request.POST.get(f'bloque_{p.numero}') or '').strip()
                p.bloque_id = int(bid) if bid.isdigit() else None
                op = (request.POST.get(f'opciones_{p.numero}') or '').strip()
                p.numero_opciones = int(op) if op.isdigit() and 2 <= int(op) <= 10 else None
                p.etiquetas = (request.POST.get(f'etiquetas_{p.numero}') or '').strip()[:200]
                p.anulada = request.POST.get(f'anulada_{p.numero}') == 'on'
                comp = (request.POST.get(f'componente_{p.numero}') or '').strip().upper()
                p.componente = comp if comp in {c for c, _ in COMPONENTES} else ''
                bruto = (request.POST.get(f'puntos_{p.numero}') or '').replace(',', '.')
                try:
                    p.puntos = Decimal(bruto) if bruto else Decimal('1.00')
                except InvalidOperation:
                    p.puntos = Decimal('1.00')
                p.parciales = _leer_parciales(request, p, examen.letras)
                p.save()
            if not examen.es_manual:
                # Con fórmula, cada pregunta vale lo mismo y el valor lo pone el
                # sistema: lo que se haya escrito en la casilla no cuenta.
                examen.preguntas.update(puntos=examen.puntos_automaticos())
            calif.calificar_examen(examen)
        messages.success(request, 'Clave guardada y notas recalculadas.')
        return redirect('puntoexacto:clave', examen_id=examen.id)

    return render(request, 'puntoexacto/clave.html', {
        'examen': examen, 'preguntas': preguntas, 'letras': list(examen.letras),
        'componentes': [(c, examen.nombre_componente(c)) for c, _ in COMPONENTES],
        'bloques': list(examen.bloques.all()),
        'sin_bloque': examen.preguntas_sin_bloque(),
        'bloques_partidos': [b for b in examen.bloques.all() if not b.es_continuo()],
        'rango_opciones': range(2, 11),
        'avisos': calif.revisar_configuracion(examen),
        'metodos': METODOS,
        'puntos_auto': examen.puntos_automaticos(),
    })


def _leer_parciales(request, pregunta, letras):
    """Lee los créditos parciales: '0.5' por cada opción que no sea la correcta."""
    salida = {}
    for letra in letras:
        if letra == pregunta.correcta:
            continue
        bruto = (request.POST.get(f'parcial_{pregunta.numero}_{letra}') or '').replace(',', '.')
        if not bruto:
            continue
        try:
            valor = Decimal(bruto)
        except InvalidOperation:
            continue
        if Decimal('0') < valor < Decimal('1'):
            salida[letra] = str(valor)
    return salida


# ---------------------------------------------------------------------------
# Hojas: generarlas e imprimirlas
# ---------------------------------------------------------------------------

@login_required
def hojas(request, examen_id):
    examen = _examen_o_404(request, examen_id)
    cursos = Curso.objects.filter(colegio=request.colegio).order_by('orden', 'nombre')

    if request.method == 'POST':
        ids = request.POST.getlist('curso_ids')
        sueltas = int(request.POST.get('sueltas') or 0)
        creadas = _crear_hojas(examen, ids, sueltas)
        messages.success(request, f'Se prepararon {creadas} hoja(s).')
        return redirect('puntoexacto:hojas', examen_id=examen.id)

    from .hojas import sugerir_por_pagina, capacidad, REPARTO
    opciones_tope = examen.opciones_maximas()
    sugerido = sugerir_por_pagina(examen.numero_preguntas, opciones_tope)

    # Qué repartos aguantan este examen. Los que no, salen en la lista pero
    # desactivados y con el motivo: es más útil que esconderlos y que el
    # docente se pregunte por qué no está el de 8.
    repartos = []
    for n in sorted(REPARTO):
        tope = capacidad(n, opciones_tope)
        repartos.append({
            'n': n, 'tope': tope,
            'cabe': examen.numero_preguntas <= tope,
            'actual': n == (examen.hojas_por_pagina or 1),
            'sugerido': n == sugerido,
        })

    return render(request, 'puntoexacto/hojas.html', {
        'examen': examen, 'cursos': cursos,
        'hojas': examen.hojas.select_related('estudiante__user').all(),
        'bloques': examen.secciones(),
        'repartos': repartos,
        'sugerido': sugerido,
        'sugerir': sugerido > (examen.hojas_por_pagina or 1) and not examen.secciones(),
    })


def _crear_hojas(examen, curso_ids, sueltas=0):
    """Una hoja por estudiante, más las sueltas para quien no esté en lista."""
    creadas = 0
    with transaction.atomic():
        if curso_ids:
            examen.cursos.set(Curso.objects.filter(id__in=curso_ids,
                                                   colegio=examen.colegio))
        estudiantes = Estudiante.objects.filter(
            curso__id__in=curso_ids, colegio=examen.colegio, is_active=True
        ).select_related('user')
        ya = set(examen.hojas.filter(estudiante__isnull=False)
                 .values_list('estudiante_id', flat=True))
        siguiente = examen.hojas.count() + 1
        for est in estudiantes:
            if est.id in ya:
                continue
            Hoja.objects.create(examen=examen, estudiante=est,
                                identificador=f'PE-{examen.id:05d}-{siguiente:04d}')
            siguiente += 1
            creadas += 1
        for _ in range(sueltas):
            Hoja.objects.create(examen=examen,
                                identificador=f'PE-{examen.id:05d}-{siguiente:04d}')
            siguiente += 1
            creadas += 1
    return creadas


@login_required
def imprimir(request, examen_id):
    examen = _examen_o_404(request, examen_id)
    lista_hojas = list(examen.hojas.select_related('estudiante__user').all())
    if not lista_hojas:
        messages.error(request, 'Primero prepare las hojas de los estudiantes.')
        return redirect('puntoexacto:hojas', examen_id=examen.id)
    # El reparto se escoge al imprimir y no solo al crear el examen: el docente
    # decide cuánto papel gasta en el momento en que va a la impresora, que es
    # cuando sabe cuántas hojas tiene y si va a recortar.
    try:
        por_pagina = int(request.GET.get('por_pagina') or 0)
    except (TypeError, ValueError):
        por_pagina = 0
    if por_pagina not in hojas_mod.REPARTO:
        por_pagina = examen.hojas_por_pagina or 1

    try:
        pdf = generar_pdf(examen, lista_hojas, por_pagina=por_pagina)
    except ValueError as e:
        messages.error(request, str(e))
        return redirect('puntoexacto:hojas', examen_id=examen.id)

    respuesta = HttpResponse(pdf, content_type='application/pdf')
    respuesta['Content-Disposition'] = (
        f'inline; filename="hojas-{examen.id}-{por_pagina}porpagina.pdf"')
    return respuesta


# ---------------------------------------------------------------------------
# Digitar respuestas
# ---------------------------------------------------------------------------

@login_required
def digitar(request, examen_id, hoja_id):
    examen = _examen_o_404(request, examen_id)
    hoja = get_object_or_404(examen.hojas, id=hoja_id)
    preguntas = list(examen.preguntas.order_by('numero'))

    if request.method == 'POST':
        if request.POST.get('ausente') == 'on':
            hoja.estado = 'ausente'
            hoja.nota = None
            hoja.save(update_fields=['estado', 'nota', 'actualizada'])
            messages.success(request, f'{hoja.nombre} quedó marcado como que no presentó.')
            return redirect('puntoexacto:hojas', examen_id=examen.id)
        with transaction.atomic():
            for p in preguntas:
                marca = (request.POST.get(f'p_{p.numero}') or '').strip().upper()[:1]
                if marca and marca not in examen.letras and marca != Hoja.MARCA_DOBLE:
                    marca = ''
                Respuesta.objects.update_or_create(
                    hoja=hoja, pregunta=p, defaults={'marcada': marca})
            if hoja.estado == 'ausente':
                hoja.estado = 'pendiente'
                hoja.save(update_fields=['estado'])
            calif.calificar_hoja(hoja)
        messages.success(request, f'Respuestas de {hoja.nombre} guardadas.')
        siguiente = examen.hojas.filter(estado='pendiente').exclude(id=hoja.id).first()
        if siguiente and request.POST.get('seguir') == 'on':
            return redirect('puntoexacto:digitar', examen_id=examen.id, hoja_id=siguiente.id)
        return redirect('puntoexacto:hojas', examen_id=examen.id)

    marcadas = {r.pregunta_id: r.marcada for r in hoja.respuestas.all()}
    filas = [{'pregunta': p, 'marcada': marcadas.get(p.id, '')} for p in preguntas]
    return render(request, 'puntoexacto/digitar.html', {
        'examen': examen, 'hoja': hoja, 'filas': filas, 'letras': list(examen.letras),
    })


# ---------------------------------------------------------------------------
# Resultados
# ---------------------------------------------------------------------------

@login_required
def resultados(request, examen_id):
    examen = _examen_o_404(request, examen_id)
    datos = analisis_mod.analizar(examen)
    lista_hojas = examen.hojas.select_related('estudiante__user').all()
    return render(request, 'puntoexacto/resultados.html', {
        'examen': examen, 'analisis': datos, 'hojas': lista_hojas,
        'avisos': calif.revisar_configuracion(examen),
        'recortadas': [h for h in lista_hojas if h.nota_recortada],
        'resumen_bloques': _resumen_bloques(examen),
        'puede_censales': puede_censales(request),
    })


def _resumen_bloques(examen):
    """Promedio del curso en cada bloque, para la pantalla de resultados.

    Es el número que de verdad interesa de una censal: no cuánto sacó cada
    estudiante, sino en qué área está parado el grupo.
    """
    bloques = list(examen.bloques.all())
    if not bloques:
        return []
    from notas.boletin.ponderacion import nota_aprobacion
    minima = nota_aprobacion(examen.colegio)
    hojas_ok = list(examen.hojas.filter(estado='calificada').prefetch_related('respuestas'))
    preguntas = list(examen.preguntas.filter(anulada=False))
    acumulado = {b.id: [] for b in bloques}
    for h in hojas_ok:
        for bid, d in calif.notas_por_bloque(examen, h, preguntas).items():
            if bid in acumulado:
                acumulado[bid].append(d)

    salida = []
    for b in bloques:
        ds = acumulado[b.id]
        n = len(ds)
        promedio = sum((d['nota'] for d in ds), Decimal('0')) / n if n else None
        aciertos = sum(d['correctas'] for d in ds)
        posibles = sum(d['total'] for d in ds)
        salida.append({
            'bloque': b, 'hojas': n,
            'promedio': promedio.quantize(Decimal('0.01')) if promedio is not None else None,
            'acierto': round(100 * aciertos / posibles, 1) if posibles else None,
            'aprobados': sum(1 for d in ds if d['nota'] >= minima) if n else None,
        })
    return salida


@login_required
def exportar(request, examen_id):
    """Una fila por estudiante, con su respuesta en cada pregunta."""
    import openpyxl
    examen = _examen_o_404(request, examen_id)
    preguntas = list(examen.preguntas.order_by('numero'))

    libro = openpyxl.Workbook()
    hoja_x = libro.active
    hoja_x.title = 'Resultados'
    encabezado = ['Estudiante', 'Documento', 'Estado', 'Nota']
    encabezado += [f'P{p.numero}' for p in preguntas]
    encabezado += ['Correctas', 'Incorrectas', 'En blanco']
    hoja_x.append(encabezado)

    for h in examen.hojas.select_related('estudiante__user').prefetch_related('respuestas'):
        marcadas = {r.pregunta_id: r.marcada for r in h.respuestas.all()}
        buenas = sum(1 for p in preguntas
                     if marcadas.get(p.id) and marcadas[p.id] == p.correcta)
        blancas = sum(1 for p in preguntas if not marcadas.get(p.id))
        fila = [h.nombre, h.documento, h.get_estado_display(),
                float(h.nota) if h.nota is not None else '']
        fila += [marcadas.get(p.id, '') for p in preguntas]
        fila += [buenas, len(preguntas) - buenas - blancas, blancas]
        hoja_x.append(fila)

    respuesta = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    respuesta['Content-Disposition'] = f'attachment; filename="examen-{examen.id}.xlsx"'
    libro.save(respuesta)
    return respuesta


@login_required
def llevar_a_planilla(request, examen_id):
    """Agrega el examen como una columna más en la planilla de notas.

    CÓMO FUNCIONA, que es lo que lo hace seguro:
    La planilla carga sus columnas desde NotaDetallada (ingreso_notas_views,
    donde arma data['notas'][key] con las notas detalladas de cada componente).
    Así que escribir una NotaDetallada hace aparecer la columna la próxima vez
    que el docente abra la planilla, y al guardar se reconstruye desde el
    formulario, donde la columna ya está. Se conserva.

    Lo que NO se toca es PROM_PERIODO: esa la calcula la planilla con los pesos
    de SER, SABER y HACER cuando el docente guarda. Hasta que lo haga, la
    definitiva del periodo sigue mostrando el valor anterior, y así se le avisa.
    """
    from notas.models.academicos import Calificacion, NotaDetallada

    examen = _examen_o_404(request, examen_id)
    if not examen.asignacion_id or not examen.periodo_id:
        messages.error(request, 'El examen necesita asignatura y periodo para pasar '
                                'notas a la planilla.')
        return redirect('puntoexacto:resultados', examen_id=examen.id)

    hojas_ok = list(examen.hojas.filter(estado='calificada', estudiante__isnull=False)
                    .select_related('estudiante__user').prefetch_related('respuestas')
                    .order_by('estudiante__user__last_name', 'estudiante__user__first_name'))
    preguntas = list(examen.preguntas.filter(anulada=False))
    componentes = examen.componentes_usados()

    if request.method == 'POST':
        if not examen.periodo.esta_activo:
            messages.error(request, f'El periodo {examen.periodo} tiene el ingreso de notas '
                                    f'cerrado. Pida al administrador que lo abra.')
            return redirect('puntoexacto:planilla', examen_id=examen.id)

        etiqueta = (request.POST.get('etiqueta') or examen.titulo)[:100]
        creadas = 0
        with transaction.atomic():
            for h in hojas_ok:
                reparto = calif.notas_por_componente(examen, h, preguntas)
                for componente, datos in reparto.items():
                    cal, _ = Calificacion.objects.get_or_create(
                        colegio=examen.colegio, estudiante=h.estudiante,
                        materia=examen.asignacion.materia, periodo=examen.periodo,
                        tipo_nota=componente,
                        defaults={'valor_nota': Decimal('0.00'),
                                  'docente': examen.asignacion.docente})
                    # Si ya se había pasado este examen, se reemplaza su columna
                    # en vez de duplicarla.
                    NotaDetallada.objects.filter(
                        calificacion_promedio=cal, descripcion=etiqueta).delete()
                    NotaDetallada.objects.create(
                        colegio=examen.colegio, calificacion_promedio=cal,
                        descripcion=etiqueta, valor_nota=datos['nota'])
                    _recalcular_componente(cal)
                    creadas += 1
                h.enviada_a_planilla = True
                h.save(update_fields=['enviada_a_planilla'])

        messages.success(
            request,
            f'Se agregó la columna «{etiqueta}» con {creadas} nota(s). '
            f'Abra la planilla, revísela y guárdela para que el promedio del '
            f'periodo se actualice.')
        return redirect('puntoexacto:planilla', examen_id=examen.id)

    filas_previas = []
    for h in hojas_ok:
        reparto = calif.notas_por_componente(examen, h, preguntas)
        filas_previas.append({
            'hoja': h,
            'notas': [{'componente': c, 'nombre': examen.nombre_componente(c),
                       'nota': reparto.get(c, {}).get('nota')} for c in componentes],
        })

    return render(request, 'puntoexacto/planilla.html', {
        'examen': examen, 'filas': filas_previas,
        'componentes': [{'codigo': c, 'nombre': examen.nombre_componente(c),
                         'preguntas': sorted(
                             p.numero for p in preguntas
                             if (p.componente or examen.componente) == c)}
                        for c in componentes],
        'ausentes': examen.hojas.filter(estado='ausente'),
        'pendientes': examen.hojas.filter(estado__in=['pendiente', 'revisar']),
        'periodo_cerrado': not examen.periodo.esta_activo,
    })


def _recalcular_componente(calificacion):
    """Deja el promedio del componente como lo dejaría la planilla.

    Misma cuenta que ingreso_notas_views: media simple de sus notas detalladas,
    redondeada a dos decimales. Si no coincidiera, el docente vería un número
    aquí y otro allá.
    """
    from django.db.models import Avg

    promedio = calificacion.notas_detalladas.aggregate(p=Avg('valor_nota'))['p']
    calificacion.valor_nota = (Decimal(promedio).quantize(Decimal('0.01'), ROUND_HALF_UP)
                               if promedio is not None else Decimal('0.00'))
    calificacion.save(update_fields=['valor_nota'])


@login_required
def bloques(request, examen_id):
    """Arma la hoja por áreas: Lenguaje 1-15, Matemáticas 16-35, etc.

    Se piden rangos de preguntas y no se marca pregunta por pregunta, porque un
    censal de 60 son 60 menús desplegables y nadie hace eso dos veces. La
    asignación fina, si hace falta corregir una sola, queda en la pantalla de
    la clave.
    """
    examen = _examen_o_404(request, examen_id)
    if not puede_censales(request):
        return HttpResponseForbidden(
            'Las pruebas por bloques las arma el director de grado o un '
            'administrador del colegio.')

    materias = Materia.objects.filter(colegio=request.colegio).order_by('nombre')

    if request.method == 'POST':
        if request.POST.get('accion') == 'borrar':
            Bloque.objects.filter(examen=examen,
                                  id=request.POST.get('bloque_id')).delete()
            messages.success(request, 'Bloque eliminado. Sus preguntas quedaron sin área.')
            return redirect('puntoexacto:bloques', examen_id=examen.id)

        errores = []
        with transaction.atomic():
            for b in examen.bloques.all():
                b.nombre = (request.POST.get(f'nombre_{b.id}') or b.nombre).strip()[:60]
                mid = (request.POST.get(f'materia_{b.id}') or '').strip()
                b.materia_id = int(mid) if mid.isdigit() else None
                op = (request.POST.get(f'opciones_{b.id}') or '').strip()
                b.numero_opciones = int(op) if op.isdigit() and 2 <= int(op) <= 10 else None
                b.orden = int(request.POST.get(f'orden_{b.id}') or b.orden)
                b.peso = _leer_peso(request.POST.get(f'peso_{b.id}'))
                b.save()
                desde = request.POST.get(f'desde_{b.id}') or ''
                hasta = request.POST.get(f'hasta_{b.id}') or ''
                if desde.isdigit() and hasta.isdigit():
                    d, h = int(desde), int(hasta)
                    if d > h:
                        errores.append(f'{b.nombre}: el rango {d}–{h} está al revés.')
                    else:
                        examen.preguntas.filter(numero__gte=d, numero__lte=h).update(bloque=b)

            nuevo = (request.POST.get('nuevo_nombre') or '').strip()
            if nuevo:
                mid = (request.POST.get('nuevo_materia') or '').strip()
                op = (request.POST.get('nuevo_opciones') or '').strip()
                b = Bloque.objects.create(
                    examen=examen, nombre=nuevo[:60],
                    materia_id=int(mid) if mid.isdigit() else None,
                    numero_opciones=int(op) if op.isdigit() and 2 <= int(op) <= 10 else None,
                    peso=_leer_peso(request.POST.get('nuevo_peso')),
                    orden=(examen.bloques.count() + 1))
                d = request.POST.get('nuevo_desde') or ''
                h = request.POST.get('nuevo_hasta') or ''
                if d.isdigit() and h.isdigit() and int(d) <= int(h):
                    examen.preguntas.filter(numero__gte=int(d),
                                            numero__lte=int(h)).update(bloque=b)

            # Las notas dependen de los bloques y sus pesos: se recalculan.
            calif.calificar_examen(examen)

        for e in errores:
            messages.warning(request, e)
        if not errores:
            messages.success(request, 'Bloques guardados y notas recalculadas.')
        return redirect('puntoexacto:bloques', examen_id=examen.id)

    vigentes = list(examen.preguntas.filter(anulada=False))
    pesos, avisos_pesos = calif.pesos_de_bloques(examen, vigentes)
    filas = []
    for b in examen.bloques.all():
        d, h = b.rango()
        efectivo = pesos.get(b.id)
        filas.append({'b': b, 'desde': d, 'hasta': h,
                      'n': b.preguntas.count(), 'continuo': b.es_continuo(),
                      'peso_efectivo': (efectivo * 100).quantize(Decimal('0.1'))
                      if efectivo is not None else None})
    # Lo que necesita la pantalla para recalcular en vivo, sin guardar: cada
    # pregunta con sus puntos, sus opciones y el bloque en que está hoy.
    preguntas_js = [{'n': p.numero, 'pts': float(p.puntos), 'anulada': p.anulada,
                     'op': p.numero_opciones, 'b': p.bloque_id}
                    for p in examen.preguntas.order_by('numero')]
    return render(request, 'puntoexacto/bloques.html', {
        'examen': examen, 'materias': materias, 'filas': filas,
        'sin_bloque': examen.preguntas_sin_bloque(),
        'rango_opciones': range(2, 11),
        'peso_sin_bloque': ((pesos[None] * 100).quantize(Decimal('0.1'))
                            if None in pesos else None),
        'avisos_pesos': avisos_pesos,
        'preguntas_json': preguntas_js,
    })


def _leer_peso(crudo):
    """Un porcentaje entre 0 y 100, o None si viene vacío o no es número."""
    crudo = (crudo or '').strip().replace(',', '.').rstrip('%')
    if not crudo:
        return None
    try:
        valor = Decimal(crudo)
    except InvalidOperation:
        return None
    if valor < 0 or valor > 100:
        return None
    return valor.quantize(Decimal('0.01'))


@login_required
@xframe_options_sameorigin
def vista_previa_bloques(request, examen_id):
    """La hoja de un examen por bloques, con lo que hay escrito en la pantalla.

    Recibe en ?bloques= la lista de filas tal como están en el formulario, sin
    guardar: [{"clave": "12", "nombre": "Lenguaje", "orden": 1, "desde": 1,
    "hasta": 15, "opciones": 4}, ...]. Reparte las preguntas igual que lo haría
    el botón Guardar y dibuja con el mismo generador que imprime de verdad.
    Sin ?bloques= dibuja lo que ya está guardado. No guarda nada.
    """
    import io
    import json

    examen = _examen_o_404(request, examen_id)
    preguntas = list(examen.preguntas.order_by('numero'))
    asignada = {p.numero: (str(p.bloque_id) if p.bloque_id else None) for p in preguntas}

    filas = []
    crudo = request.GET.get('bloques')
    if crudo:
        try:
            filas = json.loads(crudo)
        except (ValueError, TypeError):
            filas = []
        if not isinstance(filas, list):
            filas = []
    if not filas:
        filas = [{'clave': str(b.id), 'nombre': b.nombre, 'orden': b.orden,
                  'opciones': b.numero_opciones} for b in examen.bloques.all()]

    def entero(valor, defecto=None):
        try:
            return int(valor)
        except (TypeError, ValueError):
            return defecto

    limpias = []
    for i, f in enumerate(filas):
        if not isinstance(f, dict):
            continue
        clave = str(f.get('clave') or f'nuevo{i}')
        nombre = (str(f.get('nombre') or '').strip() or 'Bloque')[:60]
        op = entero(f.get('opciones'))
        limpias.append({'clave': clave, 'nombre': nombre,
                        'orden': entero(f.get('orden'), 99),
                        'opciones': op if op and 2 <= op <= 10 else None,
                        'desde': entero(f.get('desde')), 'hasta': entero(f.get('hasta'))})
        d, h = limpias[-1]['desde'], limpias[-1]['hasta']
        if d and h and d <= h:
            for n in range(d, h + 1):
                if n in asignada:
                    asignada[n] = clave

    secciones = []
    for f in sorted(limpias, key=lambda x: x['orden']):
        suyas = [p for p in preguntas if asignada.get(p.numero) == f['clave']]
        if not suyas:
            continue
        base = f['opciones'] or examen.numero_opciones
        op_preg = [p.numero_opciones or base for p in suyas]
        secciones.append({'nombre': f['nombre'], 'n': len(suyas),
                          'opciones': max([base] + op_preg), 'op_pregunta': op_preg})

    materia = curso = ''
    if examen.asignacion_id:
        materia = examen.asignacion.materia.nombre
        curso = examen.asignacion.curso.nombre
    datos = {
        'colegio': examen.colegio.nombre if examen.colegio_id else '',
        'materia': materia or 'Prueba por áreas', 'curso': curso or 'Curso',
        'periodo': str(examen.periodo) if examen.periodo_id else '',
        'titulo': examen.titulo,
        'estudiante': 'APELLIDOS Y NOMBRES DEL ESTUDIANTE', 'documento': '0000000000',
        'docente': '', 'fecha': '',
    }
    if not secciones:
        return _pdf_de_aviso('Todavía no hay ningún bloque con preguntas. Escriba un '
                             'nombre y el rango «Desde–Hasta» para ver la hoja.')
    try:
        por_pagina = examen.hojas_por_pagina or 1
        if por_pagina not in hojas_mod.REPARTO:
            por_pagina = 1
        buffer = io.BytesIO()
        hojas_mod.generar(buffer, [datos], opciones=examen.numero_opciones,
                          por_pagina=por_pagina, secciones=secciones,
                          identificadores=['PE-MUESTRA'], escudo=None)
    except ValueError as e:
        return _pdf_de_aviso(str(e))
    except Exception as e:
        return _pdf_de_aviso(f'{type(e).__name__}: {e}')

    respuesta = HttpResponse(buffer.getvalue(), content_type='application/pdf')
    respuesta['Content-Disposition'] = 'inline; filename="vista-previa-bloques.pdf"'
    respuesta['Cache-Control'] = 'no-store'
    return respuesta


@login_required
def planilla_bloque(request, examen_id, bloque_id):
    """Lleva la nota de UN bloque a la planilla de su materia.

    Esto es lo que distingue una censal de un examen corriente: la nota de
    Matemáticas va a la planilla de Matemáticas y la de Lenguaje a la de
    Lenguaje, y cada una con el docente que de verdad dicta esa materia en el
    curso del estudiante. Por eso el bloque guarda una materia y no una
    asignación: la asignación se resuelve aquí, estudiante por estudiante.

    Nada de esto ocurre solo. La censal se califica y se analiza sin tocar
    ninguna planilla; este paso hay que pedirlo, bloque por bloque, y queda
    registrado en la columna que se crea.
    """
    from notas.models.academicos import AsignacionDocente, Calificacion, NotaDetallada

    examen = _examen_o_404(request, examen_id)
    bloque = get_object_or_404(Bloque, id=bloque_id, examen=examen)

    if not puede_censales(request):
        return HttpResponseForbidden(
            'Pasar notas de una prueba por bloques a la planilla lo hace el '
            'director de grado o un administrador del colegio.')
    if not bloque.materia_id:
        messages.error(request, f'El bloque «{bloque.nombre}» no tiene materia del '
                                f'colegio, así que no hay planilla a la cual llevarlo. '
                                f'Asígnele una materia en «Bloques».')
        return redirect('puntoexacto:resultados', examen_id=examen.id)
    if not examen.periodo_id:
        messages.error(request, 'El examen necesita un periodo para pasar notas.')
        return redirect('puntoexacto:resultados', examen_id=examen.id)

    hojas_ok = list(examen.hojas.filter(estado='calificada', estudiante__isnull=False)
                    .select_related('estudiante__user', 'estudiante__curso')
                    .prefetch_related('respuestas')
                    .order_by('estudiante__curso__nombre',
                              'estudiante__user__last_name',
                              'estudiante__user__first_name'))
    preguntas = list(examen.preguntas.filter(anulada=False, bloque=bloque))

    # Para cada curso presente, ¿quién dicta esta materia?
    asignaciones = {}
    for a in AsignacionDocente.objects.filter(colegio=examen.colegio,
                                              materia=bloque.materia).select_related('docente__user'):
        asignaciones[a.curso_id] = a

    filas, sin_asignacion = [], set()
    for h in hojas_ok:
        datos = calif.notas_por_bloque(examen, h, preguntas).get(bloque.id)
        if datos is None:
            continue
        curso = h.estudiante.curso
        asig = asignaciones.get(curso.id if curso else None)
        if asig is None and curso:
            sin_asignacion.add(curso.nombre)
        filas.append({'hoja': h, 'curso': curso, 'asignacion': asig,
                      'nota': datos['nota'], 'correctas': datos['correctas'],
                      'total': datos['total']})

    if request.method == 'POST':
        if not examen.periodo.esta_activo:
            messages.error(request, f'El periodo {examen.periodo} tiene el ingreso de '
                                    f'notas cerrado. Pida al administrador que lo abra.')
            return redirect('puntoexacto:planilla_bloque', examen_id=examen.id,
                            bloque_id=bloque.id)

        componente = (request.POST.get('componente') or examen.componente)
        etiqueta = (request.POST.get('etiqueta') or f'{examen.titulo} · {bloque.nombre}')[:100]
        creadas, saltadas = 0, 0
        with transaction.atomic():
            for f in filas:
                if f['asignacion'] is None:
                    saltadas += 1
                    continue
                cal, _ = Calificacion.objects.get_or_create(
                    colegio=examen.colegio, estudiante=f['hoja'].estudiante,
                    materia=bloque.materia, periodo=examen.periodo,
                    tipo_nota=componente,
                    defaults={'valor_nota': Decimal('0.00'),
                              'docente': f['asignacion'].docente})
                NotaDetallada.objects.filter(calificacion_promedio=cal,
                                             descripcion=etiqueta).delete()
                NotaDetallada.objects.create(
                    colegio=examen.colegio, calificacion_promedio=cal,
                    descripcion=etiqueta, valor_nota=f['nota'])
                _recalcular_componente(cal)
                creadas += 1

        messages.success(request, f'Se agregó la columna «{etiqueta}» con {creadas} '
                                  f'nota(s) en {bloque.materia.nombre}.')
        if saltadas:
            messages.warning(request, f'{saltadas} estudiante(s) quedaron por fuera: su '
                                      f'curso no tiene docente asignado en '
                                      f'{bloque.materia.nombre}.')
        return redirect('puntoexacto:resultados', examen_id=examen.id)

    return render(request, 'puntoexacto/planilla_bloque.html', {
        'examen': examen, 'bloque': bloque, 'filas': filas,
        'sin_asignacion': sorted(sin_asignacion),
        'componentes': [(c, examen.nombre_componente(c)) for c, _ in COMPONENTES],
        'etiqueta_sugerida': f'{examen.titulo} · {bloque.nombre}'[:100],
    })


@login_required
@xframe_options_sameorigin
def vista_previa(request):
    """Devuelve el PDF de UNA hoja de muestra con lo que hay en el formulario.

    El decorador xframe_options_sameorigin NO es decorativo. El proyecto tiene
    XFrameOptionsMiddleware activo y no define X_FRAME_OPTIONS, y desde Django
    3.0 ese valor por defecto es DENY: el navegador bloquea la página dentro de
    CUALQUIER marco, incluso uno de la misma página. Por eso la vista previa
    salía en blanco sin error visible. Esto lo permite solo para el mismo
    origen, sin tocar la configuración global del proyecto.

    No dibuja una maqueta en JavaScript: llama al mismo generador que imprime
    las hojas de verdad. Una vista previa hecha aparte se desincroniza del
    generador en la primera semana y entonces miente, que es peor que no tenerla.

    No guarda nada ni toca la base: solo lee parámetros y arma un PDF.
    """
    import json

    def entero(nombre, por_defecto, minimo, maximo):
        try:
            valor = int(request.GET.get(nombre, por_defecto))
        except (TypeError, ValueError):
            return por_defecto
        return max(minimo, min(maximo, valor))

    preguntas = entero('preguntas', 10, 1, 150)
    opciones = entero('opciones', 4, 2, 10)
    por_pagina = entero('por_pagina', 1, 1, 8)
    if por_pagina not in hojas_mod.REPARTO:
        por_pagina = 1

    por_pregunta = {}
    try:
        crudo = json.loads(request.GET.get('ops') or '{}')
        if isinstance(crudo, dict):
            for k, val in crudo.items():
                n, o = int(k), int(val)
                if 1 <= n <= preguntas and 2 <= o <= 10:
                    por_pregunta[n] = o
    except (ValueError, TypeError):
        por_pregunta = {}

    lista_op = [por_pregunta.get(n, opciones) for n in range(1, preguntas + 1)]
    seccion = {'nombre': None, 'n': preguntas,
               'opciones': max(lista_op), 'op_pregunta': lista_op}

    colegio = request.colegio.nombre if request.colegio else 'COLEGIO'
    docente = _docente_de(request)
    nombre_docente = ''
    if request.GET.get('docente') == '1' and docente:
        u = docente.user
        nombre_docente = (u.get_full_name() or u.username).strip()
    texto_fecha = (request.GET.get('fecha') or '') if request.GET.get('ver_fecha') == '1' else ''

    datos = {
        'colegio': colegio,
        'materia': request.GET.get('materia') or 'Asignatura',
        'curso': request.GET.get('curso') or 'Curso',
        'periodo': request.GET.get('periodo') or '',
        'titulo': (request.GET.get('titulo') or 'Examen sin nombre')[:160],
        'estudiante': 'APELLIDOS Y NOMBRES DEL ESTUDIANTE',
        'documento': '0000000000',
        'docente': nombre_docente, 'fecha': texto_fecha,
    }

    # El escudo va solo si lo piden. Leerlo puede significar bajarlo de
    # DigitalOcean Spaces, y una vista previa que se redibuja con cada tecla no
    # puede depender de una descarga remota: si el bucket tarda, el marco se
    # queda cargando y parece que la pantalla está rota.
    escudo = None
    if request.GET.get('escudo') == '1':
        escudo = hojas_mod._escudo_del_colegio(request.colegio)

    import io
    buffer = io.BytesIO()
    try:
        hojas_mod.generar(buffer, [datos], opciones=opciones, por_pagina=por_pagina,
                          secciones=[seccion], identificadores=['PE-MUESTRA'],
                          escudo=escudo)
    except ValueError as e:
        # No caben: se devuelve un PDF que lo dice, en vez de un error 500 que
        # deja el marco en blanco sin explicar nada.
        return _pdf_de_aviso(str(e))
    except Exception as e:
        # Cualquier otra falla al dibujar también se muestra dentro del marco.
        # Un 500 aquí deja la pantalla en blanco y sin pista de qué pasó.
        return _pdf_de_aviso(f'{type(e).__name__}: {e}')

    respuesta = HttpResponse(buffer.getvalue(), content_type='application/pdf')
    respuesta['Content-Disposition'] = 'inline; filename="vista-previa.pdf"'
    respuesta['Cache-Control'] = 'no-store'
    return respuesta


def _pdf_de_aviso(mensaje):
    """Una página con el motivo por el que la hoja no se puede dibujar."""
    import io
    import textwrap
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.units import mm
    from reportlab.pdfgen import canvas as rl_canvas

    buffer = io.BytesIO()
    c = rl_canvas.Canvas(buffer, pagesize=letter)
    ancho, alto = letter
    c.setFillColorRGB(.64, .09, .10)
    c.setFont('Helvetica-Bold', 14)
    c.drawString(20 * mm, alto - 30 * mm, 'Esta hoja no se puede imprimir así')
    c.setFillColorRGB(.2, .2, .2)
    c.setFont('Helvetica', 11)
    y = alto - 40 * mm
    for linea in textwrap.wrap(mensaje, 72):
        c.drawString(20 * mm, y, linea)
        y -= 6 * mm
    c.showPage(); c.save()
    respuesta = HttpResponse(buffer.getvalue(), content_type='application/pdf')
    respuesta['Cache-Control'] = 'no-store'
    return respuesta


# ---------------------------------------------------------------------------
# Calificar con la cámara
# ---------------------------------------------------------------------------

@login_required
def escanear(request, examen_id):
    """Pantalla para tomar fotos de las hojas con el celular."""
    import json

    examen = _examen_o_404(request, examen_id)
    hojas_lista = list(examen.hojas.select_related('estudiante__user')
                       .order_by('identificador'))
    # La lista va al navegador para cuando el código de barras no se deje leer
    # y al docente le toque escoger al estudiante a mano.
    datos = [{'id': h.id, 'nombre': h.nombre,
              'calificada': h.estado == 'calificada'} for h in hojas_lista]
    return render(request, 'puntoexacto/escanear.html', {
        'examen': examen,
        'pendientes': sum(1 for h in hojas_lista if h.estado != 'calificada'),
        'total': len(hojas_lista),
        'hojas_json': json.dumps(datos, ensure_ascii=False),
    })


@login_required
def procesar_foto(request, examen_id):
    """Recibe una foto, la lee y devuelve lo que vio. NO guarda nada.

    La foto no se almacena: entra, se mide y se descarta. Son fotos de hojas de
    estudiantes y no hay ninguna razón para que se acumulen en el bucket del
    colegio; además, el repaso lo hace el navegador con la imagen que ya tiene
    en el teléfono, así que guardarla tampoco serviría de nada.
    """
    from . import lector as lector_mod

    examen = _examen_o_404(request, examen_id)
    if request.method != 'POST' or 'foto' not in request.FILES:
        return JsonResponse({'ok': False, 'error': 'No llegó ninguna foto.'}, status=400)

    archivo = request.FILES['foto']
    if archivo.size > 25 * 1024 * 1024:
        return JsonResponse({'ok': False,
                             'error': 'La foto pesa demasiado. Baje la resolución '
                                      'de la cámara.'}, status=400)

    info = hojas_mod.mapa_de_examen(examen)
    preguntas = list(examen.preguntas.order_by('numero'))
    opciones = {p.numero: p.opciones_efectivas() for p in preguntas}
    letras = lambda n: hojas_mod.LETRAS[:opciones.get(n, examen.numero_opciones)]

    identificadores = list(examen.hojas.values_list('identificador', flat=True))
    geo = hojas_mod.geometria(examen.hojas_por_pagina or 1,
                              identificadores[0] if identificadores else None)

    try:
        gris = lector_mod._a_gris(archivo)
        H, centros = lector_mod.matriz_de_hoja(gris, geo)
        negro = lector_mod.nivel_de_negro(gris, centros, geo['marca_mm'], H)
        medidas, radio_px, posiciones = lector_mod.medir_burbujas(
            gris, H, info['mapa'], info['radio_mm'], geo['alto_mm'], negro)
        respuestas, dudas = lector_mod.decidir(
            medidas, examen.numero_preguntas, letras)
        leido, como = lector_mod.identificar_hoja(gris, H, geo, identificadores)
    except lector_mod.LecturaFallida as e:
        return JsonResponse({'ok': False, 'error': str(e)})
    except Exception as e:
        return JsonResponse({'ok': False,
                             'error': f'No se pudo leer la foto ({type(e).__name__}).'})

    hoja = None
    if leido:
        hoja = examen.hojas.filter(identificador=leido).select_related(
            'estudiante__user').first()

    return JsonResponse({
        'ok': True,
        'hoja_id': hoja.id if hoja else None,
        'hoja_nombre': hoja.nombre if hoja else None,
        'identificador': leido,
        'como_se_supo': como,
        'ya_calificada': bool(hoja and hoja.estado == 'calificada'),
        'respuestas': {str(k): v for k, v in respuestas.items()},
        'dudas': dudas,
        'posiciones': posiciones,
        'radio_px': round(radio_px, 1),
        'ancho_foto': int(gris.shape[1]), 'alto_foto': int(gris.shape[0]),
        'opciones': {str(k): v for k, v in opciones.items()},
        'letras': hojas_mod.LETRAS,
    })


@login_required
def guardar_lectura(request, examen_id):
    """Guarda las respuestas que el docente confirmó en la pantalla."""
    import json

    examen = _examen_o_404(request, examen_id)
    if request.method != 'POST':
        return JsonResponse({'ok': False, 'error': 'Método no permitido.'}, status=405)
    try:
        datos = json.loads(request.body.decode('utf-8'))
    except (ValueError, UnicodeDecodeError):
        return JsonResponse({'ok': False, 'error': 'Datos ilegibles.'}, status=400)

    hoja = examen.hojas.filter(id=datos.get('hoja_id')).first()
    if hoja is None:
        return JsonResponse({'ok': False, 'error': 'No se indicó de quién es la hoja.'},
                            status=400)

    respuestas = datos.get('respuestas') or {}
    preguntas = {p.numero: p for p in examen.preguntas.all()}
    validas = set(hojas_mod.LETRAS)

    with transaction.atomic():
        hoja.respuestas.all().delete()
        nuevas = []
        for clave, letra in respuestas.items():
            try:
                numero = int(clave)
            except (TypeError, ValueError):
                continue
            p = preguntas.get(numero)
            if p is None:
                continue
            letra = (letra or '').strip().upper()[:1]
            if letra and letra not in validas:
                letra = ''
            if letra and hojas_mod.LETRAS.index(letra) >= p.opciones_efectivas():
                letra = ''          # una letra que esa pregunta no tiene
            nuevas.append(Respuesta(hoja=hoja, pregunta=p, marcada=letra))
        Respuesta.objects.bulk_create(nuevas)
        hoja.estado = 'calificada'
        hoja.save(update_fields=['estado'])
        calif.calificar_hoja(hoja)

    hoja.refresh_from_db()
    return JsonResponse({'ok': True, 'nota': str(hoja.nota),
                         'recortada': hoja.nota_recortada,
                         'nombre': hoja.nombre})
