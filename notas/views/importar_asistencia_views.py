# notas/views/importar_asistencia_views.py
"""Subir la planilla de asistencia en Excel: revisar primero, guardar después.

Antes esta vista guardaba al instante y terminaba en un redirect con el nombre
de ruta mal escrito: el error deshacía todo y nunca se guardaba nada. Además
solo leía la primera hoja (el primer mes). La lógica vive ahora en
notas/planillas/asistencia.py.
"""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import HttpResponseNotFound
from django.shortcuts import redirect, render

from ..models.perfiles import Docente
from ..permisos import es_admin
from ..planillas import asistencia as planilla

CLAVE_SESION = 'asistencia_por_subir'


def _puede_entrar(request):
    return es_admin(request) or Docente.objects.filter(user=request.user, colegio=request.colegio).exists()


@login_required
def importar_asistencia_excel_vista(request):
    if not getattr(request, 'colegio', None):
        return HttpResponseNotFound('<h1>Colegio no configurado</h1>')
    if not _puede_entrar(request):
        messages.error(request, 'Solo los docentes y directivos del colegio pueden subir asistencia.')
        return redirect('notas:dashboard')
    if request.method != 'POST':
        return redirect('notas:consulta_asistencia')

    accion = request.POST.get('accion', 'revisar')

    if accion == 'cancelar':
        request.session.pop(CLAVE_SESION, None)
        messages.info(request, 'No se guardó nada.')
        return redirect('notas:consulta_asistencia')

    if accion == 'confirmar':
        pendiente = request.session.pop(CLAVE_SESION, None)
        if not pendiente or pendiente.get('colegio') != request.colegio.id:
            messages.error(request, 'La revisión expiró. Suba el archivo otra vez.')
            return redirect('notas:consulta_asistencia')
        with transaction.atomic():
            n = planilla.aplicar(pendiente['cambios'], request.colegio, request.user)
        messages.success(request, f'Asistencia guardada: {n} registro(s) actualizados.')
        return redirect('notas:consulta_asistencia')

    archivo = request.FILES.get('archivo_excel')
    if not archivo:
        messages.error(request, 'Seleccione el archivo de Excel con la asistencia.')
        return redirect('notas:consulta_asistencia')

    resultado = planilla.leer(archivo, request.colegio, request.user)
    if resultado['cambios'] and not resultado['errores']:
        request.session[CLAVE_SESION] = {'colegio': request.colegio.id, 'cambios': resultado['cambios']}
    else:
        request.session.pop(CLAVE_SESION, None)
    return render(request, 'notas/docente/subir_asistencia.html', {'r': resultado, 'archivo': archivo.name})
