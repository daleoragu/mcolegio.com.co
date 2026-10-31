"""Exámenes PuntoExacto dentro del aula: la lista, la nota de cada estudiante y sus respuestas."""
from django.shortcuts import get_object_or_404
from django.http import Http404

from . import logica
from .views import _ctx, _render, vista_aula


def _hoja_de(examen, c):
    if c.estudiante is not None:
        return examen.hojas.filter(estudiante=c.estudiante).first()
    if c.integrante is not None:
        return examen.hojas.filter(integrante=c.integrante).first()
    return None


def _url_crear(aula):
    from django.urls import reverse
    base = reverse('puntoexacto:crear')
    if aula.asignacion_id:
        return f'{base}?asignacion={aula.asignacion_id}'
    return f'{base}?grupo={aula.grupo_id}'


def _pe_activo(aula):
    if aula.es_salon:
        return True
    from notas.modulos import esta_activo
    return esta_activo(aula.colegio, 'puntoexacto')


@vista_aula
def examenes(request, pk):
    c = _ctx(request, pk)
    aula = c.aula
    if not _pe_activo(aula):
        raise Http404
    lista = list(logica.examenes_de(aula).select_related('periodo'))
    for ex in lista:
        if c.es_docente:
            ex.n_hojas = ex.hojas.count()
            ex.n_calificadas = ex.hojas.filter(estado='calificada').count()
        else:
            ex.mia = _hoja_de(ex, c)
    if not c.es_docente:
        lista = [ex for ex in lista if ex.mia is not None]
    return _render(request, c, 'aula/examenes.html', {'examenes': lista, 'url_crear': _url_crear(aula)}, 'examenes')


@vista_aula
def examen(request, pk, eid):
    c = _ctx(request, pk)
    aula = c.aula
    if not _pe_activo(aula):
        raise Http404
    ex = get_object_or_404(logica.examenes_de(aula), pk=eid)
    datos = {'ex': ex}
    if c.es_docente:
        datos['hojas'] = list(ex.hojas.select_related('estudiante__user', 'integrante')
                              .order_by('estado', 'nombre_libre'))
        datos['hojas'].sort(key=lambda h: h.nombre)
        datos['desempenos'] = {h.pk: logica.desempeno(aula, h.nota) for h in datos['hojas'] if h.nota is not None}
        for h in datos['hojas']:
            h.desempeno_aula = datos['desempenos'].get(h.pk, '')
    else:
        hoja = _hoja_de(ex, c)
        if hoja is None:
            raise Http404
        datos['hoja'] = hoja
        if hoja.estado == 'calificada':
            marcadas = {r.pregunta_id: r.marcada for r in hoja.respuestas.all()}
            filas = []
            for p in ex.preguntas.filter(anulada=False, es_control=False).select_related('bloque', 'examen'):
                marcada = marcadas.get(p.pk, '')
                fraccion = p.fraccion(marcada)
                filas.append({'numero': p.numero, 'marcada': p.rotulo(marcada) if marcada and marcada != '?' else '',
                              'doble': marcada == '?', 'fraccion': fraccion,
                              'estado': 'bien' if fraccion == 1 else ('parcial' if fraccion > 0 else 'mal'),
                              'tema': p.etiquetas})
            datos['filas'] = filas
            datos['aciertos'] = sum(1 for f in filas if f['estado'] == 'bien')
            datos['desempeno'] = logica.desempeno(aula, hoja.nota) if hoja.nota is not None else ''
    return _render(request, c, 'aula/examen.html', datos, 'examenes')
