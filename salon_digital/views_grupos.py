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
    from .limites import a_planes, cupo_grupos
    if not cupo_grupos(request.cuenta):
        return a_planes(request, 'grupos', 'estandar')
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

    if request.method == 'POST' and 'uno' in request.POST:
        apellidos = ' '.join((request.POST.get('apellidos') or '').split())[:120]
        nombres = ' '.join((request.POST.get('nombres') or '').split())[:120]
        if not apellidos and not nombres:
            messages.warning(request, 'Escriba los apellidos y los nombres del estudiante.')
        else:
            completo = f'{apellidos} {nombres}'.strip().lower()
            ya = grupo.integrantes.filter(completo__iexact=completo).first()
            if ya and ya.activo:
                messages.info(request, f'{ya.completo} ya está en el grupo.')
            elif ya:
                ya.activo = True
                ya.save(update_fields=['activo'])
                messages.success(request, f'{ya.completo} volvió al grupo.')
            else:
                nuevo = Integrante.objects.create(grupo=grupo, apellidos=apellidos, nombres=nombres)
                messages.success(request, f'{nuevo.completo} agregado. Su PIN es {nuevo.pin_chat}.')
        return redirect('salon_digital:ver_grupo', pk=grupo.pk)

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

    aula = getattr(grupo, 'aula', None)
    return render(request, 'salon_digital/ver_grupo.html', {
        'grupo': grupo,
        'form': form,
        'lista': lista,
        'integrantes': grupo.integrantes.filter(activo=True),
        'retirados': grupo.integrantes.filter(activo=False, solicitud=False),
        'solicitudes': grupo.integrantes.filter(solicitud=True),
        'sin_clave': grupo.integrantes.filter(activo=True, clave='').count(),
        'aula': aula,
        'enlace': _enlace_entrada(request, grupo),
    })


def _enlace_entrada(request, grupo):
    """El enlace con que entran los estudiantes a la clase (con el código ya escrito), si el grupo tiene aula."""
    from django.urls import reverse
    aula = getattr(grupo, 'aula', None)
    if aula is None:
        return ''
    return request.build_absolute_uri(reverse('aula:entrar', args=[aula.pk])) + f'?codigo={grupo.codigo}'


@cuenta_requerida
@require_POST
def editar_integrante(request, pk, integrante_pk):
    """Corregir el nombre de un estudiante (lo que ya entregó sigue siendo suyo)."""
    grupo = get_object_or_404(Grupo, pk=pk, propietario=request.cuenta)
    integrante = get_object_or_404(Integrante, pk=integrante_pk, grupo=grupo)
    apellidos = ' '.join((request.POST.get('apellidos') or '').split())[:120]
    nombres = ' '.join((request.POST.get('nombres') or '').split())[:120]
    if not apellidos and not nombres:
        messages.warning(request, 'El nombre no puede quedar vacío.')
    else:
        integrante.apellidos, integrante.nombres = apellidos, nombres
        integrante.save()
        messages.success(request, f'Nombre actualizado: {integrante.completo}.')
    return redirect('salon_digital:ver_grupo', pk=pk)


@cuenta_requerida
@require_POST
def nuevo_pin(request, pk, integrante_pk):
    """Un PIN nuevo para el estudiante (si lo olvidó o alguien más lo conoce)."""
    from .models import pin_chat
    grupo = get_object_or_404(Grupo, pk=pk, propietario=request.cuenta)
    integrante = get_object_or_404(Integrante, pk=integrante_pk, grupo=grupo)
    integrante.pin_chat = pin_chat()
    integrante.save(update_fields=['pin_chat'])
    messages.success(request, f'Nuevo PIN de {integrante.completo}: {integrante.pin_chat}')
    return redirect('salon_digital:ver_grupo', pk=pk)


@cuenta_requerida
@require_POST
def reactivar_integrante(request, pk, integrante_pk):
    grupo = get_object_or_404(Grupo, pk=pk, propietario=request.cuenta)
    integrante = get_object_or_404(Integrante, pk=integrante_pk, grupo=grupo)
    integrante.activo = True
    integrante.save(update_fields=['activo'])
    messages.success(request, f'{integrante.completo} volvió al grupo.')
    return redirect('salon_digital:ver_grupo', pk=pk)


@cuenta_requerida
def tarjetas(request, pk):
    """Tarjetas de acceso para imprimir y recortar: enlace (con QR), código del grupo, nombre y PIN de cada estudiante."""
    import base64
    from .utils import generar_qr
    grupo = get_object_or_404(Grupo, pk=pk, propietario=request.cuenta)
    enlace = _enlace_entrada(request, grupo)
    qr = base64.b64encode(generar_qr(enlace, 6)).decode() if enlace else ''
    recientes = claves_recientes(request, grupo)
    integrantes = list(grupo.integrantes.filter(activo=True))
    if request.GET.get('recientes'):
        integrantes = [i for i in integrantes if i.pk in recientes]
    for i in integrantes:
        i.clave_tarjeta = recientes.get(i.pk, '')
    return render(request, 'salon_digital/tarjetas_grupo.html', {
        'grupo': grupo, 'enlace': enlace, 'qr': qr, 'integrantes': integrantes, 'cuenta': request.cuenta})


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


# ---------------------------------------------------------------------------
# Cuentas de estudiantes (como Khan Academy): nombre + contraseña que crea el docente
# ---------------------------------------------------------------------------
HORAS_CLAVES = 3          # las contraseñas recién creadas se pueden ver e imprimir durante 3 horas


def _llave_claves(grupo):
    return f'claves_grupo_{grupo.pk}'


def _recordar_claves(request, grupo, nuevas):
    """Las contraseñas en claro quedan solo en la sesión del docente, un rato, para mostrarlas e imprimir las tarjetas."""
    import time
    datos = request.session.get(_llave_claves(grupo)) or {}
    if time.time() - datos.get('t', 0) > HORAS_CLAVES * 3600:
        datos = {}
    datos.setdefault('claves', {}).update({str(k): v for k, v in nuevas.items()})
    datos['t'] = time.time()
    request.session[_llave_claves(grupo)] = datos


def claves_recientes(request, grupo):
    """{integrante_pk: contraseña} de las creadas o restablecidas hace poco en esta sesión."""
    import time
    datos = request.session.get(_llave_claves(grupo)) or {}
    if time.time() - datos.get('t', 0) > HORAS_CLAVES * 3600:
        return {}
    return {int(k): v for k, v in (datos.get('claves') or {}).items()}


def _nombres_de(request):
    """Los nombres escritos en la tabla (uno por fila) y los pegados en el cuadro, sin vacíos ni repetidos."""
    nombres, vistos = [], set()
    filas = list(request.POST.getlist('nombre')) + (request.POST.get('lista') or '').splitlines()
    for fila in filas:
        partido = partir_nombre(fila)
        if not partido:
            continue
        completo = ' '.join(f'{partido[0]} {partido[1]}'.split())[:240]
        if completo.lower() not in vistos:
            vistos.add(completo.lower())
            nombres.append(completo)
    return nombres


@cuenta_requerida
def agregar_estudiantes(request, pk):
    """Paso 1: escribir (o pegar) los nombres. Paso 2: revisar las contraseñas propuestas y crear las cuentas."""
    from . import claves
    grupo = get_object_or_404(Grupo, pk=pk, propietario=request.cuenta)
    existentes = {i.completo.lower(): i for i in grupo.integrantes.all()}
    paso = request.POST.get('paso') if request.method == 'POST' else ''
    if paso == 'revisar':
        nombres = _nombres_de(request)
        ya = [n for n in nombres if n.lower() in existentes and existentes[n.lower()].activo]
        filas = [{'nombre': n, 'clave': claves.nueva(), 'error': ''} for n in nombres if n not in ya]
        if not filas:
            messages.warning(request, 'Escriba al menos un nombre nuevo.' + (f' {len(ya)} ya estaban en el grupo.' if ya else ''))
            return redirect('salon_digital:agregar_estudiantes', pk=grupo.pk)
        return render(request, 'salon_digital/agregar_estudiantes.html', {'grupo': grupo, 'paso': 2, 'filas': filas, 'ya': ya})
    if paso == 'crear':
        nombres, contrasenas = request.POST.getlist('nombre'), request.POST.getlist('clave')
        filas = []
        for nombre, clave in zip(nombres, contrasenas):
            nombre = ' '.join(nombre.split())[:240]
            if nombre:
                filas.append({'nombre': nombre, 'clave': clave.strip(), 'error': claves.problema(clave, nombre)})
        falta_permiso = not request.POST.get('permiso')
        if falta_permiso or any(f['error'] for f in filas):
            if falta_permiso:
                messages.warning(request, 'Confirme que tiene el permiso de los padres o acudientes para crear las cuentas.')
            return render(request, 'salon_digital/agregar_estudiantes.html', {'grupo': grupo, 'paso': 2, 'filas': filas})
        creadas = {}
        for f in filas:
            apellidos, nombres_ = partir_nombre(f['nombre'])
            previo = existentes.get(' '.join(f'{apellidos} {nombres_}'.split()).lower())
            i = previo or Integrante(grupo=grupo, apellidos=apellidos, nombres=nombres_)
            i.activo = True
            i.poner_clave(f['clave'])
            i.save()
            creadas[i.pk] = f['clave']
        _recordar_claves(request, grupo, creadas)
        messages.success(request, f'Se crearon {len(creadas)} cuenta(s). Imprima las tarjetas ahora: las contraseñas no se vuelven a mostrar.')
        return redirect('salon_digital:cuentas_grupo', pk=grupo.pk)
    return render(request, 'salon_digital/agregar_estudiantes.html', {'grupo': grupo, 'paso': 1})


@cuenta_requerida
def cuentas_grupo(request, pk):
    """Las contraseñas recién creadas o restablecidas (solo en esta sesión, por unas horas) para copiarlas o imprimirlas."""
    grupo = get_object_or_404(Grupo, pk=pk, propietario=request.cuenta)
    recientes = claves_recientes(request, grupo)
    filas = [(i, recientes[i.pk]) for i in grupo.integrantes.filter(pk__in=recientes.keys())]
    return render(request, 'salon_digital/cuentas_grupo.html', {'grupo': grupo, 'filas': filas, 'horas': HORAS_CLAVES})


@cuenta_requerida
@require_POST
def restablecer_clave(request, pk, integrante_pk):
    """El docente le da una contraseña nueva al estudiante (la escribe él o se propone una fácil)."""
    from . import claves
    grupo = get_object_or_404(Grupo, pk=pk, propietario=request.cuenta)
    integrante = get_object_or_404(Integrante, pk=integrante_pk, grupo=grupo)
    nueva = (request.POST.get('clave') or '').strip() or claves.nueva()
    error = claves.problema(nueva, integrante.completo)
    if error:
        messages.warning(request, f'{integrante.completo}: {error}')
        return redirect('salon_digital:ver_grupo', pk=pk)
    integrante.poner_clave(nueva)
    integrante.save(update_fields=['clave', 'clave_propia'])
    _recordar_claves(request, grupo, {integrante.pk: nueva})
    messages.success(request, f'Nueva contraseña de {integrante.completo}: {nueva}')
    return redirect('salon_digital:ver_grupo', pk=pk)


@cuenta_requerida
@require_POST
def claves_para_todos(request, pk):
    """Contraseñas nuevas para los que no tienen (o para todos), por ejemplo al pasar un grupo de PIN a contraseña."""
    from . import claves
    grupo = get_object_or_404(Grupo, pk=pk, propietario=request.cuenta)
    lista = grupo.integrantes.filter(activo=True)
    if request.POST.get('cuales') != 'todos':
        lista = lista.filter(clave='')
    nuevas = {}
    for i in lista:
        nuevas[i.pk] = claves.nueva()
        i.poner_clave(nuevas[i.pk])
        i.save(update_fields=['clave', 'clave_propia'])
    _recordar_claves(request, grupo, nuevas)
    messages.success(request, f'{len(nuevas)} contraseña(s) nuevas. Imprima las tarjetas ahora.')
    return redirect('salon_digital:cuentas_grupo', pk=grupo.pk)


@cuenta_requerida
def carta_padres(request, pk):
    """Carta modelo para las familias: qué es la plataforma, qué datos se usan y cómo entra su hijo."""
    grupo = get_object_or_404(Grupo, pk=pk, propietario=request.cuenta)
    return render(request, 'salon_digital/carta_padres.html', {'grupo': grupo, 'cuenta': request.cuenta,
                                                                'enlace': _enlace_entrada(request, grupo)})


@cuenta_requerida
@require_POST
def responder_solicitud(request, pk, integrante_pk):
    """Un estudiante de otra clase pidió unirse con el código: el docente lo aprueba (queda en la lista con su misma
    cuenta y contraseña) o lo rechaza (la solicitud se borra)."""
    grupo = get_object_or_404(Grupo, pk=pk, propietario=request.cuenta)
    pedido = get_object_or_404(Integrante, pk=integrante_pk, grupo=grupo, solicitud=True)
    if request.POST.get('accion') == 'aprobar':
        pedido.activo, pedido.solicitud = True, False
        pedido.save(update_fields=['activo', 'solicitud'])
        messages.success(request, f'{pedido.completo} ya está en {grupo.nombre}. Entra con su misma contraseña de siempre.')
    else:
        nombre = pedido.completo
        pedido.delete()
        messages.info(request, f'Se rechazó la solicitud de {nombre}.')
    return redirect('salon_digital:ver_grupo', pk=pk)
