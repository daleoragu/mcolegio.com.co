# notas/views/administradores_views.py
"""Quiénes administran el colegio: rector, coordinadores, secretaría.

La ve y la usa el superusuario y cualquier administrador del colegio. Un
administrador solo maneja los administradores de SU colegio.
"""
import secrets

from django.contrib import messages
from django.contrib.auth.models import User
from django.db import IntegrityError, transaction
from django.http import HttpResponseNotFound
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from ..models import AdministradorColegio, Docente
from ..permisos import admin_requerido


@admin_requerido
def administradores_colegio(request):
    if not request.colegio:
        return HttpResponseNotFound('<h1>Colegio no configurado</h1>')
    colegio = request.colegio

    if request.method == 'POST':
        origen = request.POST.get('origen')
        cargo = request.POST.get('cargo') or 'ADMINISTRATIVO'
        if cargo not in dict(AdministradorColegio.CARGOS):
            cargo = 'ADMINISTRATIVO'
        usuario, clave_nueva = None, None

        if origen == 'docente':
            docente = Docente.objects.filter(id=request.POST.get('docente'), colegio=colegio).select_related('user').first()
            if docente is None:
                messages.error(request, 'Escoja un docente del colegio.')
                return redirect('notas:administradores_colegio')
            usuario = docente.user
        else:
            nombres = (request.POST.get('nombres') or '').strip()
            apellidos = (request.POST.get('apellidos') or '').strip()
            nombre_usuario = (request.POST.get('usuario') or '').strip()
            if not (nombres and nombre_usuario):
                messages.error(request, 'Escriba al menos el nombre y el usuario.')
                return redirect('notas:administradores_colegio')
            if User.objects.filter(username__iexact=nombre_usuario).exists():
                messages.error(request, f'El usuario «{nombre_usuario}» ya existe. Si es un docente del colegio, '
                                        f'agréguelo desde la lista de docentes.')
                return redirect('notas:administradores_colegio')
            clave_nueva = (request.POST.get('clave') or '').strip() or secrets.token_urlsafe(8)
            usuario = User.objects.create_user(nombre_usuario, email=(request.POST.get('correo') or '').strip(),
                                               password=clave_nueva, first_name=nombres, last_name=apellidos)

        if usuario.is_superuser:
            messages.info(request, f'{usuario.get_full_name() or usuario.username} es superusuario: ya puede todo en todos los colegios.')
            return redirect('notas:administradores_colegio')
        try:
            with transaction.atomic():
                admin, creado = AdministradorColegio.objects.get_or_create(
                    user=usuario, colegio=colegio, defaults={'cargo': cargo})
                if not creado:
                    admin.cargo, admin.activo = cargo, True
                    admin.save(update_fields=['cargo', 'activo'])
        except IntegrityError:
            messages.error(request, 'No se pudo agregar. Intente de nuevo.')
            return redirect('notas:administradores_colegio')

        texto = f'{usuario.get_full_name() or usuario.username} ahora administra {colegio.nombre}.'
        if clave_nueva:
            texto += f' Usuario: {usuario.username} · Clave inicial: {clave_nueva} (cópiela ahora; no se vuelve a mostrar).'
        messages.success(request, texto)
        return redirect('notas:administradores_colegio')

    admins = (AdministradorColegio.objects.filter(colegio=colegio)
              .select_related('user').order_by('-activo', 'user__last_name'))
    ya = set(admins.filter(activo=True).values_list('user_id', flat=True))
    docentes = (Docente.objects.filter(colegio=colegio).exclude(user_id__in=ya)
                .select_related('user').order_by('user__last_name', 'user__first_name'))
    return render(request, 'notas/admin_tools/administradores_colegio.html', {
        'colegio': colegio, 'admins': admins, 'docentes': docentes, 'cargos': AdministradorColegio.CARGOS,
    })


@admin_requerido
@require_POST
def quitar_administrador(request, admin_id):
    admin = get_object_or_404(AdministradorColegio, id=admin_id, colegio=request.colegio)
    if admin.user_id == request.user.id:
        messages.error(request, 'No puede quitarse a sí mismo: pídaselo a otro administrador del colegio.')
        return redirect('notas:administradores_colegio')
    activo = not admin.activo
    admin.activo = activo
    admin.save(update_fields=['activo'])
    nombre = admin.user.get_full_name() or admin.user.username
    messages.success(request, f'{nombre} {"vuelve a administrar" if activo else "ya no administra"} el colegio.')
    return redirect('notas:administradores_colegio')
