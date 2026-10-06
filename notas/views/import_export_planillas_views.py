# notas/views/import_export_planillas_views.py
"""Ruta vieja de «Exportar planillas del docente».

Se conserva porque el botón de «Ingresar notas» y enlaces guardados la usan,
pero ahora genera el Excel nuevo (notas/planillas/excel.py): con el diseño del
colegio, las columnas del plan de notas, las fórmulas de la definitiva y la
posibilidad de subirlo de vuelta.
"""
import re

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseForbidden, HttpResponseNotFound
from django.shortcuts import get_object_or_404

from ..models import AsignacionDocente, Docente, PeriodoAcademico
from ..planillas.excel import generar_libro
from ..permisos import es_admin, es_admin_usuario


@login_required
def exportar_planillas_docente(request, docente_id, periodo_id):
    if not request.colegio:
        return HttpResponseNotFound("<h1>Colegio no configurado</h1>")
    docente = get_object_or_404(Docente, id=docente_id, colegio=request.colegio)
    periodo = get_object_or_404(PeriodoAcademico, id=periodo_id, colegio=request.colegio)
    # Antes no se revisaba: cualquier usuario podía bajar las listas de otro docente.
    if not (es_admin(request) or docente.user_id == request.user.id):
        return HttpResponseForbidden("Solo puede descargar sus propias planillas.")

    asignaciones = list(AsignacionDocente.objects.filter(docente=docente, colegio=request.colegio)
                        .select_related('materia', 'curso', 'docente__user')
                        .order_by('curso__orden', 'curso__nombre', 'materia__nombre'))
    if not asignaciones:
        return HttpResponse("Este docente no tiene asignaturas asignadas en este colegio.", status=404)

    datos = generar_libro(request.colegio, periodo, asignaciones)
    nombre = f"Planillas {docente.user.get_full_name()} {periodo.get_nombre_display()} {periodo.ano_lectivo}"
    nombre = re.sub(r'[^A-Za-z0-9ÁÉÍÓÚÑáéíóúñ _\-]', '', nombre).strip() or 'Planillas'
    respuesta = HttpResponse(datos, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    respuesta['Content-Disposition'] = f'attachment; filename="{nombre}.xlsx"'
    return respuesta
