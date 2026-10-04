# salon_digital/views_grupos.py
"""Grupos: una forma de organizar, no un requisito."""
import re

from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .decoradores import cuenta_requerida
from .forms import GrupoForm, ListaIntegrantesForm
from .models import Grupo, Integrante


def partir_nombre(linea):
    """Convierte una línea de la lista pegada en (apellidos, nombres).

    Acepta "Ramos Gutiérrez, David Leonardo" y también "Ramos Gutiérrez David".
    Sin coma, se toman las dos primeras palabras como apellidos.
    """
    linea = re.sub(r'^\s*\d+[.\-)\s]+', '', linea.strip())  # numeración de la planilla
    linea = re.sub(r'\s+', ' ', linea)
    if not linea:
        return None

    if ',' in linea:
        apellidos, _, nombres = linea.partition(',')
        return apellidos.strip(), nombres.strip()

    partes = linea.split(' ')
    if len(partes) == 1:
        return partes[0], ''
    if len(partes) == 2:
        return partes[0], partes[1]
    return ' '.join(partes[:2]), ' '.join(partes[2:])


@cuenta_requerida
def grupos(request):
    return render(request, 'salon_digital/grupos.html', {
        'cuenta': request.cuenta,
        'grupos': request.cuenta.grupos.all(),
    })


@cuenta_requerida
def nuevo_grupo(request):
    form = GrupoForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        grupo = form.save(commit=False)
        grupo.propietario = request.cuenta
        grupo.save()
        messages.success(request, f'Grupo {grupo.nombre} creado. Su código es {grupo.codigo}.')
        return redirect('salon_digital:ver_grupo', pk=grupo.pk)
    return render(request, 'salon_digital/form_grupo.html',
                  {'form': form, 'titulo': 'Crear un grupo'})


@cuenta_requerida
def ver_grupo(request, pk):
    grupo = get_object_or_404(Grupo, pk=pk, propietario=request.cuenta)
    form = GrupoForm(instance=grupo)
    lista = ListaIntegrantesForm()

    if request.method == 'POST' and 'pegar' in request.POST:
        lista = ListaIntegrantesForm(request.POST)
        if lista.is_valid():
            nuevos, repetidos = 0, 0
            existentes = {i.completo.lower() for i in grupo.integrantes.all()}
            for linea in lista.cleaned_data['lista'].splitlines():
                partido = partir_nombre(linea)
                if not partido:
                    continue
                apellidos, nombres = partido
                completo = f'{apellidos} {nombres}'.strip().lower()
                if completo in existentes:
                    repetidos += 1
                    continue
                Integrante.objects.create(grupo=grupo, apellidos=apellidos, nombres=nombres)
                existentes.add(completo)
                nuevos += 1
            messages.success(
                request,
                f'{nuevos} estudiantes agregados'
                + (f', {repetidos} ya estaban en la lista.' if repetidos else '.'),
            )
            return redirect('salon_digital:ver_grupo', pk=grupo.pk)

    return render(request, 'salon_digital/ver_grupo.html', {
        'grupo': grupo,
        'form': form,
        'lista': lista,
        'integrantes': grupo.integrantes.all(),
    })


@cuenta_requerida
@require_POST
def editar_grupo(request, pk):
    grupo = get_object_or_404(Grupo, pk=pk, propietario=request.cuenta)
    form = GrupoForm(request.POST, instance=grupo)
    if form.is_valid():
        form.save()
        messages.success(request, 'Grupo actualizado.')
    else:
        messages.error(request, 'Revisa los datos del grupo.')
    return redirect('salon_digital:ver_grupo', pk=pk)


@cuenta_requerida
@require_POST
def eliminar_grupo(request, pk):
    grupo = get_object_or_404(Grupo, pk=pk, propietario=request.cuenta)
    nombre = grupo.nombre
    grupo.delete()
    messages.success(request, f'Grupo {nombre} eliminado. Los resultados recibidos siguen ahí.')
    return redirect('salon_digital:grupos')


@cuenta_requerida
@require_POST
def quitar_integrante(request, pk, integrante_pk):
    grupo = get_object_or_404(Grupo, pk=pk, propietario=request.cuenta)
    integrante = get_object_or_404(Integrante, pk=integrante_pk, grupo=grupo)
    integrante.activo = False
    integrante.save(update_fields=['activo'])
    messages.success(request, f'{integrante.completo} salió del grupo.')
    return redirect('salon_digital:ver_grupo', pk=pk)
