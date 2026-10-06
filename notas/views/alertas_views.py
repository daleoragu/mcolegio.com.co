# notas/views/alertas_views.py
"""Tablero de alertas tempranas.

Lo ve el administrador (todos los cursos) y el director de grado (solo los
cursos que dirige). Un docente sin dirección de grupo no entra: estas son
notas de todas las materias, no solo de las suyas.
"""
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden, HttpResponseNotFound
from django.shortcuts import render

from ..alertas import alertas_de_curso, maximo_permitido, resumen
from ..boletin.ponderacion import nota_aprobacion
from ..models import Curso, Docente, PeriodoAcademico
from ..permisos import es_admin, es_admin_usuario

ORDEN_RIESGO = {'alto': 0, 'medio': 1, 'ok': 2, 'sin_notas': 3}


def _cursos_visibles(request):
    if es_admin(request):
        return Curso.objects.filter(colegio=request.colegio)
    docente = Docente.objects.filter(user=request.user, colegio=request.colegio).first()
    if docente is None:
        return Curso.objects.none()
    return Curso.objects.filter(colegio=request.colegio, director_grado=docente)


@login_required
def alertas_tempranas(request):
    if not request.colegio:
        return HttpResponseNotFound('<h1>Colegio no configurado</h1>')
    cursos = list(_cursos_visibles(request).order_by('grado', 'orden', 'nombre'))
    if not cursos and not es_admin(request):
        return HttpResponseForbidden('Las alertas tempranas las ven el administrador y el director de grado.')

    anos = sorted(set(PeriodoAcademico.objects.filter(colegio=request.colegio)
                      .values_list('ano_lectivo', flat=True)), reverse=True)
    try:
        ano = int(request.GET.get('ano') or (anos[0] if anos else 0))
    except ValueError:
        ano = anos[0] if anos else 0
    periodos = list(PeriodoAcademico.objects.filter(colegio=request.colegio, ano_lectivo=ano).order_by('fecha_inicio'))
    periodo = next((p for p in periodos if str(p.id) == request.GET.get('periodo')), None)
    if periodo is None and periodos:
        # Por defecto: el último periodo abierto, o el último del año.
        abiertos = [p for p in periodos if p.esta_activo]
        periodo = abiertos[-1] if abiertos else periodos[-1]

    curso_sel = next((c for c in cursos if str(c.id) == request.GET.get('curso')), None)
    aprobacion = nota_aprobacion(request.colegio)
    maximo = maximo_permitido(request.colegio)

    filas, por_curso = [], []
    if periodo is not None:
        for c in ([curso_sel] if curso_sel else cursos):
            del_curso = alertas_de_curso(request.colegio, c, ano, periodo, aprobacion, maximo)
            filas.extend(del_curso)
            r = resumen(del_curso)
            if r['total']:
                por_curso.append({'curso': c, **r})
    filas.sort(key=lambda f: (ORDEN_RIESGO[f['riesgo']], -f['n'], f['curso'].orden,
                              f['estudiante'].user.last_name))
    ver = request.GET.get('ver', 'riesgo')
    visibles = [f for f in filas if f['riesgo'] in ('alto', 'medio')] if ver == 'riesgo' else filas

    return render(request, 'notas/alertas_tempranas.html', {
        'colegio': request.colegio, 'cursos': cursos, 'curso_sel': curso_sel,
        'anos': anos, 'ano': ano, 'periodos': periodos, 'periodo': periodo,
        'filas': visibles, 'total_filas': len(filas), 'resumen': resumen(filas), 'por_curso': por_curso,
        'aprobacion': aprobacion, 'maximo': maximo, 'ver': ver,
    })
