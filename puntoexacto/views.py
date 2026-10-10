# -*- coding: utf-8 -*-
"""PuntoExacto · vistas.

Esta primera versión funciona SIN cámara: el docente crea el examen, imprime
las hojas, digita las respuestas y obtiene las notas y el análisis. El lector
de fotos se conecta después sin cambiar nada de lo que hay aquí.
"""
import datetime
import re
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
from . import formas as formas_mod
from . import hojas as hojas_mod
from .forms import ExamenForm
from .hojas import generar_pdf
from .models import (LETRAS, METODOS, Bloque, Examen, Forma, Hoja, Pregunta,
                     Respuesta, limpiar_rotulos)
from notas.permisos import es_admin


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
    return es_admin(request) or _cursos_dirigidos(request).exists()


def _examenes_visibles(request):
    """Un docente ve los suyos; un administrador, los de todo el colegio.

    El director de grado ve además los exámenes por bloques de los cursos que
    dirige, aunque los haya creado otro: es quien responde por esa aplicación.
    """
    base = Examen.objects.filter(colegio=request.colegio)
    if es_admin(request):
        return base
    docente = _docente_de(request)
    if docente is None:
        # Ni administrador ni docente de este colegio (p. ej. un estudiante): nada.
        return base.none()
    dirigidos = _cursos_dirigidos(request)
    if dirigidos.exists():
        return base.filter(Q(docente=docente) | Q(cursos__in=dirigidos)).distinct()
    return base.filter(docente=docente)


def es_personal(request):
    """PuntoExacto es para docentes y administradores del colegio, no para estudiantes."""
    return bool(getattr(request, 'colegio', None)) and (es_admin(request) or _docente_de(request) is not None)


def personal_requerido(vista):
    from functools import wraps

    @wraps(vista)
    def envoltura(request, *args, **kwargs):
        if not es_personal(request):
            return HttpResponseForbidden('PuntoExacto es para docentes y administradores del colegio.')
        return vista(request, *args, **kwargs)
    return envoltura


def _examen_o_404(request, examen_id):
    examen = get_object_or_404(_examenes_visibles(request), id=examen_id)
    return examen


# ---------------------------------------------------------------------------
# Lista y creación
# ---------------------------------------------------------------------------

@login_required
@personal_requerido
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
@personal_requerido
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
def compartir(request, examen_id):
    """Le manda a otros docentes una copia del examen (clave, puntos, formas y cuadernillo)."""
    from notas.utils.notificaciones import crear_notificacion

    from . import compartir as compartir_mod

    examen = _examen_o_404(request, examen_id)
    yo = _docente_de(request)
    excluir = {d for d in (yo and yo.id, examen.docente_id) if d}
    docentes = (Docente.objects.filter(colegio=request.colegio, user__is_active=True)
                .exclude(id__in=excluir).select_related('user')
                .order_by('user__last_name', 'user__first_name'))
    if request.method == 'POST':
        elegidos = list(docentes.filter(id__in=[x for x in request.POST.getlist('docentes') if x.isdigit()]))
        if not elegidos:
            messages.error(request, 'Escoja al menos un docente.')
        else:
            nombre = (yo.user.get_full_name() if yo else '') or 'La administración'
            for d in elegidos:
                copia = compartir_mod.copiar(examen, d, quien=yo)
                try:
                    crear_notificacion(d.user, f'{nombre} le compartió el examen «{examen.titulo}» en PuntoExacto.',
                                       'GENERAL', request.colegio, 'puntoexacto:editar', {'examen_id': copia.id})
                except Exception:
                    pass   # la copia ya quedó; el aviso es lo de menos
            messages.success(request, f'Se le envió una copia a {len(elegidos)} docente(s). '
                                      'Cada uno la ve en su PuntoExacto y la aplica en sus cursos.')
            return redirect('puntoexacto:lista')
    return render(request, 'puntoexacto/compartir.html', {'examen': examen, 'docentes': docentes})


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
            _avisar_formas_ajustadas(request, examen)
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


def _avisar_formas_ajustadas(request, examen):
    """Tras cambiar la clave o los bloques, deja las formas B, C, D coherentes."""
    cambiadas = formas_mod.ajustar_formas(examen)
    if cambiadas:
        lista = ', '.join(cambiadas)
        messages.warning(
            request, f'Cambió la estructura del examen y se ajustó la forma {lista}. '
                     f'Revise sus equivalencias en «Formas» y, si ya las imprimió, '
                     f'vuelva a imprimir esas hojas.')


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
    preguntas = list(examen.preguntas.select_related('bloque').order_by('numero'))
    bloques_del_examen = {b.id: b for b in examen.bloques.all()}

    if request.method == 'POST':
        accion = request.POST.get('accion') or ''
        ancla = ''
        validos = {c for c, _ in _componentes_del_examen(examen)}
        with transaction.atomic():
            # Cómo se puntúa: a mano, pregunta por pregunta, o con una fórmula.
            metodo = (request.POST.get('metodo') or '').strip()
            if metodo in {c for c, _ in METODOS} and metodo != examen.metodo:
                examen.metodo = metodo
                examen.save(update_fields=['metodo'])

            # Primero se guarda todo lo escrito, también cuando el botón fue
            # «agregar» o «eliminar»: así no se pierde lo que se iba llenando.
            for p in preguntas:
                bid = (request.POST.get(f'bloque_{p.numero}') or '').strip()
                p.bloque = bloques_del_examen.get(int(bid)) if bid.isdigit() else None

                # Opciones: el número que dejó el botón de más/menos. Si es el
                # mismo que heredaría del bloque o del examen se guarda vacío,
                # para que siga a esos si después cambian.
                op = (request.POST.get(f'opciones_{p.numero}') or '').strip()
                op = int(op) if op.isdigit() and 2 <= int(op) <= 10 else None
                p.numero_opciones = None if op in (None, p.opciones_heredadas()) else op

                p.rotulos = ','.join(limpiar_rotulos(request.POST.get(f'rotulos_{p.numero}')))[:40]
                letras_p = p.letras()
                correcta = (request.POST.get(f'correcta_{p.numero}') or '').strip().upper()[:1]
                # Si le bajaron opciones y la correcta quedó por fuera, se borra
                # en vez de calificar contra una burbuja que ya no existe.
                p.correcta = correcta if correcta in letras_p else ''

                p.etiquetas = (request.POST.get(f'etiquetas_{p.numero}') or '').strip()[:200]
                p.anulada = request.POST.get(f'anulada_{p.numero}') == 'on'
                p.es_control = request.POST.get(f'control_{p.numero}') == 'on'
                comp = (request.POST.get(f'componente_{p.numero}') or '').strip().upper()
                p.componente = comp if comp in validos else ''
                bruto = (request.POST.get(f'puntos_{p.numero}') or '').replace(',', '.')
                try:
                    p.puntos = Decimal(bruto) if bruto else Decimal('1.00')
                except InvalidOperation:
                    p.puntos = Decimal('1.00')
                p.parciales = _leer_parciales(request, p, letras_p)
                p.save()

            nueva = None
            if accion == 'nueva_clave':
                nueva = formas_mod.nueva_clave(examen)
                if nueva is None:
                    messages.warning(request, 'El examen ya tiene cuatro claves (A, B, C y D).')
            if accion == 'agregar':
                ancla = _agregar_pregunta(request, examen, preguntas)
            elif accion == 'quitar':
                ancla = _quitar_pregunta(request, examen, preguntas)

            if not examen.es_manual:
                # Con fórmula, cada pregunta vale lo mismo y el valor lo pone el
                # sistema: lo que se haya escrito en la casilla no cuenta.
                examen.preguntas.update(puntos=examen.puntos_automaticos())
            _avisar_formas_ajustadas(request, examen)
            calif.calificar_examen(examen)

        if nueva is not None:
            messages.success(request, f'Clave A guardada. Ahora marque la clave de la forma '
                                      f'{nueva.letra}.')
            return redirect('puntoexacto:clave_forma', examen_id=examen.id, letra=nueva.letra)
        if not accion:
            messages.success(request, 'Clave guardada y notas recalculadas.')
        destino = redirect('puntoexacto:clave', examen_id=examen.id)
        if ancla:
            destino['Location'] += f'#{ancla}'
        return destino

    return render(request, 'puntoexacto/clave.html', {
        'examen': examen, 'preguntas': preguntas,
        'letras_todas': list(LETRAS),
        'componentes': _componentes_del_examen(examen),
        'bloques': list(bloques_del_examen.values()),
        'sin_bloque': examen.preguntas_sin_bloque(),
        'bloques_partidos': [b for b in bloques_del_examen.values() if not b.es_continuo()],
        'avisos': calif.revisar_configuracion(examen),
        'metodos': METODOS,
        'puntos_auto': examen.puntos_automaticos(),
        'max_preguntas': 150,
        'formas': _pestanas_de_claves(examen),
    })


def _pestanas_de_claves(examen):
    """[(letra, faltan por marcar)] de las formas B, C, D para las pestañas."""
    return [(f.letra, formas_mod.faltantes(f.orden)) for f in examen.formas.all()]


@login_required
def clave_forma(request, examen_id, letra):
    """La clave de la forma B (o C, D): solo la respuesta correcta de cada pregunta.

    Puntos, temas, componente y bloque son los de la pregunta de la A a la que
    corresponde; por defecto, la del mismo número. Si en la B las preguntas
    van en otro orden, se puede decir cuál es en la columna de la derecha.
    """
    examen = _examen_o_404(request, examen_id)
    forma = get_object_or_404(examen.formas, letra=(letra or '').upper())
    preguntas = list(examen.preguntas.select_related('bloque').order_by('numero'))
    por_numero = {p.numero: p for p in preguntas}

    if request.method == 'POST':
        accion = request.POST.get('accion') or ''
        if accion == 'borrar':
            leidas = examen.hojas.filter(forma=forma.letra).exclude(lectura={}).count()
            if leidas:
                messages.error(request, f'La forma {forma.letra} ya tiene {leidas} hoja(s) '
                                        f'calificada(s); no se puede borrar.')
                return redirect('puntoexacto:clave_forma', examen_id=examen.id, letra=forma.letra)
            with transaction.atomic():
                forma.delete()
                examen.hojas.filter(forma=forma.letra).update(forma='A')
            messages.success(request, f'Se borró la clave {forma.letra}.')
            return redirect('puntoexacto:clave', examen_id=examen.id)

        orden = [dict(f) for f in forma.orden]
        for k, en_hoja in enumerate(preguntas, start=1):
            if k > len(orden):
                break
            crudo = (request.POST.get(f'a_{k}') or '').strip()
            numero = int(crudo) if crudo.isdigit() and int(crudo) in por_numero else None
            correcta = (request.POST.get(f'correcta_{k}') or '').strip().upper()[:1]
            orden[k - 1] = formas_mod.marcar_clave(orden, preguntas, k, correcta, numero)
        errores = formas_mod.problemas(orden, preguntas)
        if errores:
            for e in errores:
                messages.error(request, e)
        else:
            with transaction.atomic():
                forma.orden = orden
                forma.save(update_fields=['orden'])
                n = formas_mod.retraducir(forma, examen)
            faltan = formas_mod.faltantes(orden)
            texto = f'Clave {forma.letra} guardada.'
            if n:
                texto += f' Se recalificaron {n} hoja(s) de esa forma.'
            if faltan:
                messages.warning(request, texto + f' Faltan {faltan} respuesta(s) por marcar.')
            else:
                messages.success(request, texto)
            if accion == 'nueva_clave':
                nueva = formas_mod.nueva_clave(examen)
                if nueva is not None:
                    return redirect('puntoexacto:clave_forma', examen_id=examen.id,
                                    letra=nueva.letra)
        return redirect('puntoexacto:clave_forma', examen_id=examen.id, letra=forma.letra)

    filas = []
    for c in formas_mod.clave_de(forma.orden, preguntas):
        k = c['posicion']
        en_hoja = preguntas[k - 1]
        g = formas_mod.grupo(en_hoja)
        filas.append({
            'k': k, 'c': c,
            'opciones': list(zip(en_hoja.letras(), en_hoja.lista_rotulos())),
            'candidatas': [q.numero for q in preguntas if formas_mod.grupo(q) == g],
            'cambiada': c['pregunta'] is not None and c['pregunta'].numero != k,
        })
    return render(request, 'puntoexacto/clave_forma.html', {
        'examen': examen, 'forma': forma, 'filas': filas,
        'formas': _pestanas_de_claves(examen),
        'faltan': formas_mod.faltantes(forma.orden),
        'alguna_cambiada': any(f['cambiada'] for f in filas),
        'puede_nueva': formas_mod.siguiente_letra(examen) is not None,
    })


def _agregar_pregunta(request, examen, preguntas):
    """Agrega al final las preguntas que pida el docente (casilla «cuántas»), copiando la forma
    de la última.

    Copia opciones, etiquetas, bloque y componente porque casi siempre las que
    siguen son del mismo tipo: si la 20 era Verdadero/Falso, la 21 también.
    No copia la respuesta correcta ni lo que evalúa.
    """
    disponibles = 150 - examen.numero_preguntas
    if disponibles <= 0:
        messages.warning(request, 'El examen ya tiene 150 preguntas, que es el máximo.')
        return ''
    try:
        cantidad = int(request.POST.get('cantidad_agregar') or 1)
    except ValueError:
        cantidad = 1
    cantidad = max(1, min(cantidad, disponibles))
    ultima = preguntas[-1] if preguntas else None
    primera = examen.numero_preguntas + 1
    Pregunta.objects.bulk_create([Pregunta(
        examen=examen, numero=n,
        numero_opciones=ultima.numero_opciones if ultima else None,
        rotulos=ultima.rotulos if ultima else '',
        bloque=ultima.bloque if ultima else None,
        componente=ultima.componente if ultima else '',
        puntos=ultima.puntos if ultima else Decimal('1.00')) for n in range(primera, primera + cantidad)])
    examen.numero_preguntas += cantidad
    examen.save(update_fields=['numero_preguntas'])
    if cantidad == 1:
        messages.success(request, f'Se agregó la pregunta {primera}. Márquele la respuesta correcta.')
    else:
        messages.success(request, f'Se agregaron {cantidad} preguntas (de la {primera} a la '
                                  f'{examen.numero_preguntas}). Márqueles la respuesta correcta.')
    tope = hojas_mod.capacidad(examen.hojas_por_pagina or 1, examen.opciones_maximas())
    if examen.numero_preguntas > tope:
        messages.warning(
            request, f'Con {examen.hojas_por_pagina or 1} hoja(s) por página caben {tope} '
                     f'preguntas y ya van {examen.numero_preguntas}. Al imprimir escoja '
                     f'menos hojas por página.')
    if examen.hojas.filter(respuestas__isnull=False).exists():
        messages.warning(request, 'Este examen ya tiene hojas impresas o calificadas: la '
                                  'pregunta nueva no está en esas hojas. Vuelva a imprimirlas.')
    return f'p{primera}'


def _quitar_pregunta(request, examen, preguntas):
    """Elimina la última pregunta, con sus respuestas.

    Solo la última, para no renumerar: si se borrara la 7, la 8 pasaría a ser
    la 7 y todas las hojas ya impresas quedarían corridas.
    """
    if len(preguntas) <= 1:
        messages.warning(request, 'El examen tiene que tener al menos una pregunta.')
        return ''
    ultima = preguntas[-1]
    ultima.delete()
    examen.numero_preguntas = len(preguntas) - 1
    examen.save(update_fields=['numero_preguntas'])
    messages.success(request, f'Se eliminó la pregunta {ultima.numero}.')
    return f'p{examen.numero_preguntas}'


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
        'con_formas': examen.formas.exists(),
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
        nuevos = [est for est in estudiantes if est.id not in ya] + [None] * sueltas
        siguiente = examen.hojas.count() + 1
        # La forma no se decide aquí: si el examen tiene varias claves, el
        # estudiante la marca en su hoja y se sabe al leerla.
        for est in nuevos:
            Hoja.objects.create(examen=examen, estudiante=est,
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
        forma = (request.POST.get('forma') or hoja.forma).strip().upper()[:1]
        if forma in formas_mod.letras_del_examen(examen) and forma != hoja.forma:
            hoja.forma = forma
            hoja.save(update_fields=['forma'])
        with transaction.atomic():
            # Se guarda lo que dice la hoja impresa; formas_mod lo traduce a la
            # forma A, que es contra la que se califica.
            lectura = {str(p.numero): request.POST.get(f'p_{p.numero}') or ''
                       for p in preguntas}
            formas_mod.guardar_lectura(hoja, lectura, preguntas)
            if hoja.estado == 'ausente':
                hoja.estado = 'pendiente'
                hoja.save(update_fields=['estado'])
            calif.calificar_hoja(hoja)
        messages.success(request, f'Respuestas de {hoja.nombre} guardadas.')
        siguiente = examen.hojas.filter(estado='pendiente').exclude(id=hoja.id).first()
        if siguiente and request.POST.get('seguir') == 'on':
            return redirect('puntoexacto:digitar', examen_id=examen.id, hoja_id=siguiente.id)
        return redirect('puntoexacto:hojas', examen_id=examen.id)

    # Las preguntas se muestran como están en la hoja del estudiante: si le
    # tocó la forma B, la 1 es la 1 de su hoja aunque sea la 7 de la A.
    marcadas = formas_mod.lectura_de(hoja, preguntas)
    filas = [{'pregunta': p, 'marcada': marcadas.get(str(p.numero), ''),
              # (letra interna, lo que se ve): se guarda la letra, se muestra V/F.
              'opciones': list(zip(p.letras(), p.lista_rotulos()))}
             for p in preguntas]
    return render(request, 'puntoexacto/digitar.html', {
        'examen': examen, 'hoja': hoja, 'filas': filas,
        'con_formas': examen.formas.exists(),
        'letras_forma': formas_mod.letras_del_examen(examen),
    })


# ---------------------------------------------------------------------------
# Resultados
# ---------------------------------------------------------------------------

@login_required
def resultados(request, examen_id):
    examen = _examen_o_404(request, examen_id)
    datos = analisis_mod.analizar(examen)
    lista_hojas = list(examen.hojas.select_related('estudiante__user').prefetch_related('respuestas'))
    controles = list(examen.preguntas.filter(es_control=True).order_by('numero'))
    for h in lista_hojas:
        h.control = calif.control_de_hoja(h, controles) if h.estado in ('calificada', 'revisar') else None
    return render(request, 'puntoexacto/resultados.html', {
        'examen': examen, 'analisis': datos, 'hojas': lista_hojas,
        'controles': controles,
        'marcados_r': [h for h in lista_hojas if h.control and h.control['r']],
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
    preguntas = list(examen.preguntas.filter(anulada=False, es_control=False))
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
    con_formas = examen.formas.exists()
    encabezado = ['Estudiante', 'Documento', 'Estado', 'Nota'] + (['Forma'] if con_formas else [])
    # Las respuestas van siempre en la numeración de la forma A.
    encabezado += [f'P{p.numero}' for p in preguntas]
    controles = [p for p in preguntas if p.es_control]
    encabezado += ['Correctas', 'Incorrectas', 'En blanco']
    if controles:
        encabezado += ['Control de lectura', 'Marca R']
    hoja_x.append(encabezado)

    for h in examen.hojas.select_related('estudiante__user').prefetch_related('respuestas'):
        marcadas = {r.pregunta_id: r.marcada for r in h.respuestas.all()}
        buenas = sum(1 for p in preguntas
                     if marcadas.get(p.id) and marcadas[p.id] == p.correcta)
        blancas = sum(1 for p in preguntas if not marcadas.get(p.id))
        fila = [h.nombre, h.documento, h.get_estado_display(),
                float(h.nota) if h.nota is not None else '']
        if con_formas:
            fila.append(h.forma)
        fila += [marcadas.get(p.id, '') for p in preguntas]
        fila += [buenas, len(preguntas) - buenas - blancas, blancas]
        if controles:
            ctl = calif.control_de_hoja(h, controles) if h.estado in ('calificada', 'revisar') else None
            fila += [f"{ctl['aciertos']}/{ctl['total']}" if ctl else '', 'R' if ctl and ctl['r'] else '']
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
    preguntas = list(examen.preguntas.filter(anulada=False, es_control=False))
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


def _componentes_del_examen(examen):
    """[(código, nombre)] que el docente puede elegir: los del colegio (y el del
    examen, si es uno que el colegio ya quitó)."""
    from notas.componentes import codigos as codigos_colegio
    lista = codigos_colegio(examen.colegio) if examen.colegio_id else ['SER', 'SABER', 'HACER']
    if examen.componente and examen.componente not in lista:
        lista = lista + [examen.componente]
    return [(c, examen.nombre_componente(c)) for c in lista]


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
            _avisar_formas_ajustadas(request, examen)
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
            _avisar_formas_ajustadas(request, examen)
            calif.calificar_examen(examen)

        for e in errores:
            messages.warning(request, e)
        if not errores:
            messages.success(request, 'Bloques guardados y notas recalculadas.')
        return redirect('puntoexacto:bloques', examen_id=examen.id)

    vigentes = list(examen.preguntas.filter(anulada=False, es_control=False))
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
    preguntas_js = [{'n': p.numero, 'pts': float(p.puntos), 'anulada': p.anulada or p.es_control,
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
        rot_preg = []
        for p, o in zip(suyas, op_preg):
            propias = limpiar_rotulos(p.rotulos)
            rot_preg.append([propias[i] if i < len(propias) and propias[i] else LETRAS[i]
                             for i in range(o)])
        secciones.append({'nombre': f['nombre'], 'n': len(suyas),
                          'opciones': max([base] + op_preg), 'op_pregunta': op_preg,
                          'rot_pregunta': rot_preg})

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
        hojas_mod.generar(buffer, [datos], opciones=max(x['opciones'] for x in secciones),
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
    preguntas = list(examen.preguntas.filter(anulada=False, es_control=False, bloque=bloque))

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

        componente = (request.POST.get('componente') or examen.componente).strip().upper()
        if componente not in {c for c, _ in _componentes_del_examen(examen)}:
            componente = examen.componente
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
        'componentes': _componentes_del_examen(examen),
        'etiqueta_sugerida': f'{examen.titulo} · {bloque.nombre}'[:100],
    })


@login_required
@personal_requerido
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
    # La cámara del navegador busca las cuatro marcas en vivo y necesita saber
    # dónde quedan en la hoja (y su tamaño) para dibujar los recuadros guía.
    geo = _geometria_de_examen(examen, [h.identificador for h in hojas_lista])
    guia = {k: geo[k] for k in ('ancho_mm', 'alto_mm', 'marca_mm', 'marcas_mm')}
    return render(request, 'puntoexacto/escanear.html', {
        'examen': examen,
        'pendientes': sum(1 for h in hojas_lista if h.estado != 'calificada'),
        'total': len(hojas_lista),
        'hojas_json': json.dumps(datos, ensure_ascii=False),
        'geo_json': json.dumps(guia),
    })


def _geometria_de_examen(examen, identificadores):
    return hojas_mod.geometria(examen.hojas_por_pagina or 1,
                               identificadores[0] if identificadores else None)


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
    geo = _geometria_de_examen(examen, identificadores)

    try:
        gris = lector_mod._a_gris(archivo)
        H, centros = lector_mod.matriz_de_hoja(gris, geo)
        negro = lector_mod.nivel_de_negro(gris, centros, geo['marca_mm'], H)
        medidas, radio_px, posiciones = lector_mod.medir_burbujas(
            gris, H, info['mapa'], info['radio_mm'], geo['alto_mm'], negro)
        respuestas, dudas = lector_mod.decidir(
            medidas, examen.numero_preguntas, letras)
        leido, como = lector_mod.identificar_hoja(gris, H, geo, identificadores)
        # La forma se lee como una pregunta más, con las burbujas «FA», «FB»…
        letras_forma = hojas_mod.letras_de_formas(examen)
        forma, forma_duda = '', None
        if letras_forma:
            de_forma = {f'1{l}': medidas[f'F{l}'] for l in letras_forma if f'F{l}' in medidas}
            r_forma, d_forma = lector_mod.decidir(de_forma, 1, lambda n: letras_forma)
            forma = r_forma.get(1, '')
            if d_forma:
                forma_duda = d_forma[0]['motivo']
            elif not forma:
                forma_duda = 'no marcó la forma'
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
        'formas': letras_forma,
        'forma': forma,
        'forma_duda': forma_duda,
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
def nota_previa(request, examen_id):
    """La nota que sacaría una hoja con estas respuestas, SIN guardar nada.

    La cámara la muestra encima de la foto apenas lee la hoja, y la recalcula
    cada vez que el docente corrige una burbuja. Se califica de verdad (con los
    mismos bloques, formas y penalizaciones) en una hoja de paso que se deshace
    al terminar.
    """
    import json
    import uuid

    examen = _examen_o_404(request, examen_id)
    if request.method != 'POST':
        return JsonResponse({'ok': False, 'error': 'Método no permitido.'}, status=405)
    try:
        datos = json.loads(request.body.decode('utf-8'))
    except (ValueError, UnicodeDecodeError):
        return JsonResponse({'ok': False, 'error': 'Datos ilegibles.'}, status=400)
    respuestas = datos.get('respuestas') if isinstance(datos.get('respuestas'), dict) else {}
    forma = (datos.get('forma') or 'A').strip().upper()[:1]
    if forma not in formas_mod.letras_del_examen(examen):
        forma = 'A'
    preguntas = list(examen.preguntas.order_by('numero'))
    orden = formas_mod.orden_de(examen, forma, preguntas)
    clave = {str(c['posicion']): c['correcta'] for c in formas_mod.clave_de(orden, preguntas)
             if not c['anulada'] and not (c['pregunta'] and c['pregunta'].es_control)}
    with transaction.atomic():
        de_paso = Hoja.objects.create(examen=examen, identificador=f'PREVIA-{uuid.uuid4().hex[:20]}', forma=forma)
        formas_mod.guardar_lectura(de_paso, respuestas, preguntas, orden)
        r = calif.calificar_hoja(de_paso, guardar=False)
        transaction.set_rollback(True)
    return JsonResponse({
        'ok': True, 'nota': str(r['nota']), 'buenas': r['buenas'], 'malas': r['malas'],
        'blancas': r['blancas'], 'parciales': r['parciales'], 'dobles': r['dobles'],
        'total': len(clave), 'nota_maxima': str(examen.nota_maxima), 'clave': clave,
        'forma': forma, 'recortada': r['recortada'],
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
    if not isinstance(respuestas, dict):
        respuestas = {}

    forma = (datos.get('forma') or '').strip().upper()[:1]
    if forma and forma in formas_mod.letras_del_examen(examen):
        hoja.forma = forma
    elif not examen.formas.filter(letra=hoja.forma).exists():
        hoja.forma = 'A'

    with transaction.atomic():
        hoja.save(update_fields=['forma'])
        # Las respuestas vienen por posición en la hoja impresa; si la hoja es
        # de la forma B se traducen a la A antes de guardarse.
        formas_mod.guardar_lectura(hoja, respuestas)
        hoja.estado = 'calificada'
        hoja.save(update_fields=['estado'])
        calif.calificar_hoja(hoja)

    hoja.refresh_from_db()
    return JsonResponse({'ok': True, 'nota': str(hoja.nota), 'forma': hoja.forma,
                         'recortada': hoja.nota_recortada,
                         'nombre': hoja.nombre})


# ---------------------------------------------------------------------------
# Formas del examen (A, B, C, D)
# ---------------------------------------------------------------------------

def _tabla_formas(examen, preguntas, lista_formas):
    """Filas de la tabla de equivalencias: una por posición de la hoja."""
    claves = {'A': formas_mod.clave_de(formas_mod.identidad(preguntas), preguntas)}
    for f in lista_formas:
        claves[f.letra] = formas_mod.clave_de(f.orden, preguntas)
    filas = []
    for k in range(len(preguntas)):
        filas.append({'posicion': k + 1,
                      'celdas': [claves[letra][k] if k < len(claves[letra]) else None
                                 for letra in ['A'] + [f.letra for f in lista_formas]]})
    return filas


@login_required
def formas(request, examen_id):
    examen = _examen_o_404(request, examen_id)
    preguntas = list(examen.preguntas.select_related('bloque').order_by('numero'))

    if request.method == 'POST':
        accion = request.POST.get('accion') or ''
        letra = (request.POST.get('letra') or '').strip().upper()[:1]
        with transaction.atomic():
            if accion in ('generar', 'manual'):
                nueva = formas_mod.siguiente_letra(examen)
                if nueva is None:
                    messages.warning(request, 'El examen ya tiene las formas A, B, C y D.')
                    return redirect('puntoexacto:formas', examen_id=examen.id)
                if accion == 'generar':
                    mezclar_p = request.POST.get('mezclar_preguntas') == 'on'
                    mezclar_o = request.POST.get('mezclar_opciones') == 'on'
                    if not (mezclar_p or mezclar_o):
                        messages.warning(request, 'Escoja si se mezclan las preguntas, '
                                                  'las opciones o ambas.')
                        return redirect('puntoexacto:formas', examen_id=examen.id)
                    orden = formas_mod.generar_orden(preguntas, mezclar_p, mezclar_o)
                else:
                    orden = formas_mod.identidad(preguntas)
                Forma.objects.create(examen=examen, letra=nueva, orden=orden)
                if accion == 'manual':
                    messages.info(request, f'Escriba la equivalencia de la forma {nueva}.')
                    return redirect('puntoexacto:forma_editar', examen_id=examen.id, letra=nueva)
                messages.success(request, f'Se creó la forma {nueva}. Las hojas ahora traen '
                                          f'burbujas para marcar la forma: imprímalas de nuevo '
                                          f'si ya lo había hecho.')
            elif accion == 'borrar':
                forma = examen.formas.filter(letra=letra).first()
                if forma is not None:
                    leidas = examen.hojas.filter(forma=letra).exclude(lectura={}).count()
                    if leidas:
                        messages.error(request, f'La forma {letra} ya tiene {leidas} hoja(s) '
                                                f'calificada(s); no se puede borrar.')
                        return redirect('puntoexacto:formas', examen_id=examen.id)
                    forma.delete()
                    examen.hojas.filter(forma=letra).update(forma='A')
                    messages.success(request, f'Se borró la forma {letra}. Si ya imprimió las '
                                              f'hojas, vuelva a imprimirlas: cambian las '
                                              f'burbujas de forma.')
        return redirect('puntoexacto:formas', examen_id=examen.id)

    lista_formas = list(examen.formas.all())
    for f in lista_formas:
        f.problemas = formas_mod.problemas(f.orden, preguntas)
    conteo = {}
    for letra in examen.hojas.exclude(lectura={}).values_list('forma', flat=True):
        conteo[letra] = conteo.get(letra, 0) + 1
    letras = ['A'] + [f.letra for f in lista_formas]
    return render(request, 'puntoexacto/formas.html', {
        'examen': examen, 'formas': lista_formas,
        'letras': letras,
        'conteo': [(letra, conteo.get(letra, 0)) for letra in letras],
        'filas': _tabla_formas(examen, preguntas, lista_formas),
        'total_hojas': examen.hojas.count(),
        'puede_crear': len(lista_formas) < formas_mod.MAX_FORMAS - 1,
        'hay_bloques': examen.bloques.exists(),
        'hay_rotulos': any(not formas_mod.se_mezclan_opciones(p) for p in preguntas),
    })


@login_required
def forma_editar(request, examen_id, letra):
    """La equivalencia de una forma, pregunta por pregunta.

    Sirve para dos cosas: revisar la que se sorteó, o escribir la de un examen
    B que el docente ya tenía hecho en Word.
    """
    examen = _examen_o_404(request, examen_id)
    forma = get_object_or_404(examen.formas, letra=(letra or '').upper())
    preguntas = list(examen.preguntas.select_related('bloque').order_by('numero'))
    por_numero = {p.numero: p for p in preguntas}
    errores = []
    orden = forma.orden

    if request.method == 'POST':
        if request.POST.get('accion') == 'sortear':
            orden = formas_mod.generar_orden(
                preguntas, request.POST.get('mezclar_preguntas') == 'on',
                request.POST.get('mezclar_opciones') == 'on')
        else:
            orden = []
            for k, en_hoja in enumerate(preguntas, start=1):
                crudo = (request.POST.get(f'p_{k}') or '').strip()
                numero = int(crudo) if crudo.isdigit() else en_hoja.numero
                p = por_numero.get(numero, en_hoja)
                letras_p = LETRAS[:p.opciones_efectivas()]
                ops = ''.join(ch for ch in (request.POST.get(f'o_{k}') or '').upper()
                              if ch.isalpha())
                correcta_aqui = (request.POST.get(f'c_{k}') or '').strip().upper()[:1]
                if not ops:
                    # El docente solo sabe la respuesta de su forma B: se arma un
                    # orden que la respete cambiando dos opciones de lugar.
                    lista = list(letras_p)
                    if correcta_aqui in lista and p.correcta in lista:
                        i, j = lista.index(correcta_aqui), lista.index(p.correcta)
                        lista[i], lista[j] = lista[j], lista[i]
                    ops = ''.join(lista)
                orden.append({'pregunta': numero, 'opciones': ops})
        errores = formas_mod.problemas(orden, preguntas)
        if not errores:
            with transaction.atomic():
                forma.orden = orden
                forma.save(update_fields=['orden'])
                n = formas_mod.retraducir(forma, examen)
            messages.success(request, f'Forma {forma.letra} guardada.'
                             + (f' Se recalificaron {n} hoja(s) de esa forma.' if n else ''))
            return redirect('puntoexacto:formas', examen_id=examen.id)

    # Qué preguntas de la A pueden ir en cada posición (mismo bloque, mismas opciones).
    filas = []
    for k, en_hoja in enumerate(preguntas, start=1):
        fila = orden[k - 1] if k - 1 < len(orden) else {'pregunta': en_hoja.numero, 'opciones': ''}
        p = por_numero.get(fila.get('pregunta'), en_hoja)
        g = formas_mod.grupo(en_hoja)
        filas.append({
            'k': k, 'fila': fila, 'pregunta': p,
            'candidatas': [q.numero for q in preguntas if formas_mod.grupo(q) == g],
            'letras': list(LETRAS[:en_hoja.opciones_efectivas()]),
            'correcta': formas_mod.letra_en_hoja(fila, p.correcta) if p.correcta else '',
            'fija': not formas_mod.se_mezclan_opciones(en_hoja),
            'bloque': en_hoja.bloque.nombre if en_hoja.bloque_id else '',
        })
    return render(request, 'puntoexacto/forma_editar.html', {
        'examen': examen, 'forma': forma, 'filas': filas, 'errores': errores,
        'hay_bloques': examen.bloques.exists(),
        'leidas': examen.hojas.filter(forma=forma.letra).exclude(lectura={}).count(),
    })


@login_required
def formas_exportar(request, examen_id):
    """Tabla de equivalencias y claves en Excel, para armar el examen en Word."""
    import openpyxl
    from openpyxl.styles import Alignment, Font, PatternFill

    examen = _examen_o_404(request, examen_id)
    preguntas = list(examen.preguntas.select_related('bloque').order_by('numero'))
    lista_formas = list(examen.formas.all())
    letras = ['A'] + [f.letra for f in lista_formas]
    claves = {'A': formas_mod.clave_de(formas_mod.identidad(preguntas), preguntas)}
    for f in lista_formas:
        claves[f.letra] = formas_mod.clave_de(f.orden, preguntas)

    negrita = Font(bold=True, color='FFFFFF')
    fondo = PatternFill('solid', fgColor='193661')
    centro = Alignment(horizontal='center', vertical='center', wrap_text=True)

    def encabezar(hoja_x, titulos, anchos):
        hoja_x.append(titulos)
        for i, celda in enumerate(hoja_x[hoja_x.max_row], start=1):
            celda.font, celda.fill, celda.alignment = negrita, fondo, centro
            hoja_x.column_dimensions[openpyxl.utils.get_column_letter(i)].width = anchos[i - 1] if i <= len(anchos) else 12
        hoja_x.freeze_panes = hoja_x.cell(row=hoja_x.max_row + 1, column=1)

    libro = openpyxl.Workbook()
    resumen = libro.active
    resumen.title = 'Claves'
    resumen.append([f'{examen.titulo} · respuestas correctas por forma'])
    resumen['A1'].font = Font(bold=True, size=13)
    encabezar(resumen, ['Pregunta'] + [f'Forma {letra}' for letra in letras], [11] + [11] * len(letras))
    for k in range(len(preguntas)):
        fila = [k + 1]
        for letra in letras:
            c = claves[letra][k]
            fila.append('ANULADA' if c['anulada'] else (c['pregunta'].rotulo(c['correcta']) if c['pregunta'] else ''))
        resumen.append(fila)
        for celda in resumen[resumen.max_row]:
            celda.alignment = centro

    max_op = max((p.opciones_efectivas() for p in preguntas), default=4)
    for letra in letras[1:]:
        hx = libro.create_sheet(f'Forma {letra}')
        hx.append([f'Cómo armar la forma {letra} a partir de la forma A'])
        hx['A1'].font = Font(bold=True, size=13)
        hx.append(['En cada pregunta de la forma ' + letra + ': copie la pregunta indicada de la A '
                   'y ponga sus opciones en el orden que dice la tabla.'])
        encabezar(hx, [f'Pregunta en la {letra}', 'Es la pregunta de la A']
                  + [f'Opción {LETRAS[i]} = opción de la A' for i in range(max_op)]
                  + [f'Correcta en la {letra}'], [13, 13] + [12] * max_op + [13])
        for c in claves[letra]:
            p = c['pregunta']
            ops = list(c['opciones'])
            hx.append([c['posicion'], p.numero if p else '']
                      + [p.rotulo(o) if p else o for o in ops] + [''] * (max_op - len(ops))
                      + ['ANULADA' if c['anulada'] else (p.rotulo(c['correcta']) if p else '')])
            for celda in hx[hx.max_row]:
                celda.alignment = centro

    respuesta = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    respuesta['Content-Disposition'] = f'attachment; filename="formas-examen-{examen.id}.xlsx"'
    libro.save(respuesta)
    return respuesta


@login_required
def formas_imprimir(request, examen_id):
    """La misma tabla de equivalencias, en una página lista para imprimir."""
    examen = _examen_o_404(request, examen_id)
    preguntas = list(examen.preguntas.select_related('bloque').order_by('numero'))
    lista_formas = list(examen.formas.all())
    detalle = [{'letra': f.letra, 'claves': formas_mod.clave_de(f.orden, preguntas)}
               for f in lista_formas]
    return render(request, 'puntoexacto/formas_imprimir.html', {
        'examen': examen, 'letras': ['A'] + [f.letra for f in lista_formas],
        'filas': _tabla_formas(examen, preguntas, lista_formas),
        'detalle': detalle,
    })


# ---------------------------------------------------------------------------
# Clave desde / hacia Excel o CSV
# ---------------------------------------------------------------------------

@login_required
def importar_clave(request, examen_id):
    """Sube la hoja de claves de un cuadernillo y arma el examen con ella."""
    from . import importar_clave as imp

    examen = _examen_o_404(request, examen_id)
    if request.method != 'POST':
        return redirect('puntoexacto:clave', examen_id=examen.id)
    archivo = request.FILES.get('archivo')
    if archivo is None:
        messages.error(request, 'Escoja el archivo con la clave.')
        return redirect('puntoexacto:clave', examen_id=examen.id)
    if archivo.size > 2 * 1024 * 1024:
        messages.error(request, 'El archivo pesa demasiado para ser una clave (máximo 2 MB).')
        return redirect('puntoexacto:clave', examen_id=examen.id)
    try:
        preguntas = imp.leer(archivo)
        with transaction.atomic():
            r = imp.aplicar(examen, preguntas,
                            control_cuenta=request.POST.get('control_cuenta') == 'on',
                            crear_bloques=request.POST.get('crear_bloques') == 'on')
            calif.calificar_examen(examen)
    except imp.ClaveInvalida as e:
        messages.error(request, f'No se cargó la clave: {e}')
        return redirect('puntoexacto:clave', examen_id=examen.id)

    partes = [f'Clave cargada: {r["preguntas"]} preguntas']
    if r['bloques']:
        partes.append('bloques ' + ', '.join(f'{a} ({n})' for a, n in r['bloques']))
    if r['temas']:
        partes.append(f'{r["temas"]} temas para el análisis')
    if r['control']:
        partes.append(f'{r["control"]} de control de lectura')
    if r['formas']:
        partes.append('claves de las formas ' + ', '.join(r['formas']))
    messages.success(request, '; '.join(partes) + '.')
    if r['sin_clave']:
        messages.warning(request, f'{r["sin_clave"]} pregunta(s) venían sin clave: márquelas abajo.')
    if examen.hojas.exclude(lectura={}).exists():
        messages.info(request, 'Las hojas ya calificadas se recalificaron con esta clave.')
    tope = hojas_mod.capacidad(examen.hojas_por_pagina or 1, examen.opciones_maximas())
    if examen.numero_preguntas > tope:
        messages.warning(request, f'Con {examen.hojas_por_pagina or 1} hoja(s) por página caben '
                                  f'{tope} preguntas: al imprimir escoja menos hojas por página.')
    return redirect('puntoexacto:clave', examen_id=examen.id)


@login_required
def exportar_clave(request, examen_id):
    """La clave del examen en Excel o CSV, en el mismo formato que se importa."""
    import csv
    from . import importar_clave as imp

    examen = _examen_o_404(request, examen_id)
    encabezado, filas = imp.filas_para_exportar(examen)
    nombre = f'clave-{examen.id}'
    if request.GET.get('formato') == 'csv':
        respuesta = HttpResponse(content_type='text/csv; charset=utf-8')
        respuesta['Content-Disposition'] = f'attachment; filename="{nombre}.csv"'
        respuesta.write('﻿')      # para que Excel abra bien las tildes
        escritor = csv.writer(respuesta)
        escritor.writerow(encabezado)
        escritor.writerows(filas)
        return respuesta

    import openpyxl
    from openpyxl.styles import Font, PatternFill, Alignment
    libro = openpyxl.Workbook()
    hoja_x = libro.active
    hoja_x.title = 'Clave'
    hoja_x.append(encabezado)
    for celda in hoja_x[1]:
        celda.font = Font(bold=True, color='FFFFFF')
        celda.fill = PatternFill('solid', fgColor='193661')
        celda.alignment = Alignment(horizontal='center')
    for fila in filas:
        hoja_x.append(fila)
    for letra, ancho in zip('ABCDEFGHIJ', [10, 8, 24, 48, 9, 8, 9, 9, 9, 9]):
        hoja_x.column_dimensions[letra].width = ancho
    hoja_x.freeze_panes = 'A2'
    respuesta = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    respuesta['Content-Disposition'] = f'attachment; filename="{nombre}.xlsx"'
    libro.save(respuesta)
    return respuesta


# ---------------------------------------------------------------------------
# Cuadernillo: escribir el examen en la plataforma (ver cuadernillo.py)
# ---------------------------------------------------------------------------

def _nube_config(request):
    """Qué nubes hay configuradas y cuál se le sugiere a este docente según su correo."""
    from django.conf import settings
    google = getattr(settings, 'GOOGLE_CLIENT_ID', '') or ''
    microsoft = getattr(settings, 'MICROSOFT_CLIENT_ID', '') or ''
    correo = (request.user.email or '').lower()
    dominio = correo.split('@')[-1] if '@' in correo else ''
    if dominio in ('gmail.com', 'googlemail.com') and google:
        sugerida = 'google'
    elif microsoft:
        sugerida = 'onedrive'        # Office 365 institucional, Outlook, Hotmail…
    elif google:
        sugerida = 'google'
    else:
        sugerida = 'local'
    return {'google': bool(google), 'onedrive': bool(microsoft), 'sugerida': sugerida, 'correo': correo}


@login_required
def cuadernillo(request, examen_id):
    from . import cuadernillo as cmod
    from .models import Cuadernillo
    examen = _examen_o_404(request, examen_id)
    obj = Cuadernillo.objects.filter(examen=examen).first()
    contenido = cmod.limpiar(obj.contenido) if obj else cmod.vacio(examen)
    return render(request, 'puntoexacto/cuadernillo.html', {
        'examen': examen, 'contenido': contenido, 'nube': _nube_config(request),
        'con_formas': examen.formas.exists(), 'letras_formas': ['A'] + [f.letra for f in examen.formas.all()],
        'con_hojas': examen.hojas.filter(estudiante__isnull=False).exists(),
        'tiene_bloques': examen.bloques.exists(), 'guardado': obj.actualizado if obj else None,
    })


@login_required
def cuadernillo_guardar(request, examen_id):
    import json
    from . import cuadernillo as cmod
    from .models import Cuadernillo
    if request.method != 'POST':
        return JsonResponse({'ok': False, 'error': 'Use POST.'}, status=405)
    examen = _examen_o_404(request, examen_id)
    try:
        datos = json.loads(request.body.decode('utf-8') or '{}')
    except (ValueError, UnicodeDecodeError):
        return JsonResponse({'ok': False, 'error': 'No se entendió lo enviado.'}, status=400)
    contenido = cmod.limpiar(datos.get('contenido'))
    # Con hojas ya leídas, quitar o mover preguntas cambiaría la clave de respuestas que
    # ya existen y borraría las de las preguntas que sobran. Solo se puede agregar al final.
    previo = Cuadernillo.objects.filter(examen=examen).first()
    antes = [it['id'] for it in cmod.preguntas_de(cmod.limpiar(previo.contenido) if previo else cmod.vacio(examen))]
    ahora = [it['id'] for it in cmod.preguntas_de(contenido)]
    if ahora[:len(antes)] != antes and Respuesta.objects.filter(hoja__examen=examen).exists():
        return JsonResponse({'ok': False, 'error': (
            'Este examen ya tiene hojas leídas: no se pueden quitar ni cambiar de lugar preguntas, '
            'porque se dañarían las respuestas ya guardadas. Puede corregir textos, agregar preguntas al '
            'final o anular una pregunta en «Clave».')}, status=409)
    with transaction.atomic():
        obj, _ = Cuadernillo.objects.get_or_create(examen=examen)
        obj.contenido = contenido
        obj.save()
        cambio, ajustadas = cmod.sincronizar_clave(examen, contenido)
    from django.utils import timezone
    return JsonResponse({
        'ok': True, 'hora': timezone.localtime(obj.actualizado).strftime('%I:%M %p').lower(),
        'preguntas': len(cmod.preguntas_de(contenido)), 'cambio_numero': cambio, 'formas_ajustadas': ajustadas,
        'sin_correcta': [n for n, it in enumerate(cmod.preguntas_de(contenido), start=1) if not it['correcta']],
    })


@login_required
def cuadernillo_generar(request, examen_id):
    """Word o PDF. Las imágenes llegan en la misma petición y no se guardan."""
    from . import cuadernillo as cmod
    from .models import Cuadernillo
    if request.method != 'POST':
        return HttpResponse(status=405)
    examen = _examen_o_404(request, examen_id)
    obj = Cuadernillo.objects.filter(examen=examen).first()
    if obj is None:
        return HttpResponse('Primero guarde el cuadernillo.', status=400)
    contenido = cmod.limpiar(obj.contenido)
    modo = request.POST.get('nombre') if request.POST.get('nombre') in cmod.MODOS_NOMBRE else contenido['nombre']
    por_forma = request.POST.get('por_forma', '1') == '1'
    imagenes = cmod.leer_imagenes(request.FILES, contenido)
    versiones = cmod.versiones(examen, contenido, modo=modo, por_forma=por_forma)
    if not versiones:
        return HttpResponse('No hay estudiantes para poner los nombres: el examen no tiene cursos con estudiantes '
                            'activos. Escoja «línea para el nombre» o prepare las hojas del examen.', status=400)
    from unidecode import unidecode
    base = re.sub(r'[^A-Za-z0-9_-]+', '_', unidecode(examen.titulo)).strip('_')[:50] or 'examen'
    if request.POST.get('formato') == 'pdf':
        try:
            datos = cmod.generar_pdf(request, examen, contenido, imagenes, versiones)
        except ImportError:
            return HttpResponse('Falta WeasyPrint en el servidor.', status=500)
        r = HttpResponse(datos, content_type='application/pdf')
        r['Content-Disposition'] = f'attachment; filename="{base}.pdf"'
        return r
    datos = cmod.generar_docx(examen, contenido, imagenes, versiones)
    r = HttpResponse(datos, content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document')
    r['Content-Disposition'] = f'attachment; filename="{base}.docx"'
    return r


@login_required
@personal_requerido
def nube_ayudante(request, proveedor):
    """Ventanita que conecta la nube del docente (Google Drive u OneDrive) y le pasa el permiso
    a la pestaña del editor por un canal del navegador (BroadcastChannel), en el mismo
    subdominio del colegio. El permiso nunca pasa por el servidor.

    Con NUBE_URL, el ida y vuelta con Google o Microsoft se hace por la página central
    (nube_central), que es la única dirección registrada allá: así un colegio nuevo no
    obliga a registrar nada."""
    from django.conf import settings
    if proveedor not in ('google', 'onedrive'):
        raise Http404
    return render(request, 'puntoexacto/nube_ayudante.html', {
        'proveedor': proveedor,
        'client_id': getattr(settings, 'GOOGLE_CLIENT_ID' if proveedor == 'google' else 'MICROSOFT_CLIENT_ID', ''),
        'correo': request.user.email or '',
        'central': (getattr(settings, 'NUBE_URL', '') or '') + f'/puntoexacto/nube-central/{proveedor}/'
                   if getattr(settings, 'NUBE_URL', '') else '',
    })


def _hosts_de_colegios():
    """Los dominios a los que la página central puede devolver el permiso: los de ALLOWED_HOSTS
    («.mcolegio.com.co» = cualquier subdominio). localhost solo en desarrollo."""
    from django.conf import settings
    salida = []
    for h in settings.ALLOWED_HOSTS:
        h = h.strip().lower()
        if h == '*':
            # Comodín: solo se acepta en desarrollo y solo para localhost.
            if settings.DEBUG:
                salida += ['localhost', '.localhost']
            continue
        if not h:
            continue
        if not settings.DEBUG and ('localhost' in h or h.startswith('127.')):
            continue
        salida.append(h)
    return salida


def nube_central(request, proveedor):
    """La única dirección registrada en Google y Azure. Recibe la respuesta de Google o
    Microsoft y la devuelve, por el fragmento de la dirección (que no llega a ningún
    servidor), a la ventanita del colegio que la pidió. Solo devuelve a dominios de la
    plataforma. No usa sesión ni guarda nada."""
    from django.conf import settings
    if proveedor not in ('google', 'onedrive'):
        raise Http404
    return render(request, 'puntoexacto/nube_central.html', {
        'proveedor': proveedor,
        'client_id': getattr(settings, 'GOOGLE_CLIENT_ID' if proveedor == 'google' else 'MICROSOFT_CLIENT_ID', ''),
        'hosts': _hosts_de_colegios(), 'debug': settings.DEBUG,
    })
