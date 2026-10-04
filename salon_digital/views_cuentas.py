# salon_digital/views_cuentas.py
"""Registro, entrada, perfil, verificación y planes."""
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.decorators.http import require_POST

from .decoradores import cuenta_requerida, staff_requerido
from .forms import CuentaForm, EntrarForm, RegistroForm, VerificacionForm
from .models import LIMITES, Cuenta


class Entrar(LoginView):
    template_name = 'salon_digital/entrar.html'
    authentication_form = EntrarForm
    redirect_authenticated_user = True

    def get_success_url(self):
        siguiente = self.request.GET.get('siguiente')
        if siguiente and siguiente.startswith('/'):
            return siguiente
        return str(reverse_lazy('salon_digital:panel'))


def salir(request):
    logout(request)
    return redirect('salon_digital:landing')


def registro(request):
    if request.user.is_authenticated:
        return redirect('salon_digital:panel')

    form = RegistroForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        usuario = form.save()
        Cuenta.objects.create(
            usuario=usuario,
            nombre_publico=form.cleaned_data['nombre_publico'],
            slug=form.cleaned_data['slug'],
            institucion=form.cleaned_data.get('institucion', ''),
            municipio=form.cleaned_data.get('municipio', ''),
        )
        login(request, usuario)
        messages.success(
            request,
            'Cuenta creada. Tienes 15 días de prueba. Para publicar, sube el documento '
            'que acredita que eres docente.',
        )
        return redirect('salon_digital:mi_cuenta')

    return render(request, 'salon_digital/registro.html', {'form': form})


@login_required
def crear_cuenta(request):
    """Para un usuario de la plataforma que todavía no tiene cuenta de Salón Digital."""
    if getattr(request.user, 'cuenta_salon', None):
        return redirect('salon_digital:panel')

    form = CuentaForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        cuenta = form.save(commit=False)
        cuenta.usuario = request.user
        cuenta.save()
        return redirect('salon_digital:mi_cuenta')

    return render(request, 'salon_digital/crear_cuenta.html', {'form': form})


@cuenta_requerida
def mi_cuenta(request):
    cuenta = request.cuenta
    form = CuentaForm(request.POST or None, instance=cuenta)
    verificacion = VerificacionForm(instance=cuenta)

    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Datos actualizados.')
        return redirect('salon_digital:mi_cuenta')

    return render(request, 'salon_digital/mi_cuenta.html', {
        'cuenta': cuenta,
        'form': form,
        'verificacion': verificacion,
        'limites': LIMITES.get(cuenta.plan, LIMITES['prueba']),
    })


@cuenta_requerida
@require_POST
def enviar_verificacion(request):
    cuenta = request.cuenta
    form = VerificacionForm(request.POST, request.FILES, instance=cuenta)
    if form.is_valid():
        cuenta = form.save(commit=False)
        cuenta.estado = 'pendiente'
        cuenta.nota_revision = ''
        cuenta.save()
        messages.success(
            request,
            'Documento enviado. La revisión la hace una persona, así que puede tardar '
            'un día. Te avisamos por correo.',
        )
    else:
        messages.error(request, 'Revisa el documento: ' + '; '.join(
            f'{c}: {", ".join(e)}' for c, e in form.errors.items()))
    return redirect('salon_digital:mi_cuenta')


# ---------------------------------------------------------------------------
# Revisión (solo administradores)
# ---------------------------------------------------------------------------

@staff_requerido
def bandeja_verificaciones(request):
    return render(request, 'salon_digital/bandeja.html', {
        'pendientes': Cuenta.objects.filter(estado='pendiente').select_related('usuario'),
        'recientes': Cuenta.objects.exclude(estado='pendiente').select_related('usuario')[:25],
    })


@staff_requerido
@require_POST
def revisar_cuenta(request, pk):
    cuenta = get_object_or_404(Cuenta, pk=pk)
    decision = request.POST.get('decision')
    nota = (request.POST.get('nota') or '').strip()

    if decision == 'aprobar':
        cuenta.estado = 'verificada'
        cuenta.nota_revision = nota
        messages.success(request, f'{cuenta.nombre_publico} quedó verificada.')
    elif decision == 'rechazar':
        cuenta.estado = 'rechazada'
        cuenta.nota_revision = nota or 'El documento no permite confirmar que eres docente.'
        messages.info(request, f'{cuenta.nombre_publico} fue rechazada.')
    else:
        return redirect('salon_digital:bandeja')

    cuenta.revisada_por = request.user
    cuenta.revisada_en = timezone.now()
    cuenta.save()
    return redirect('salon_digital:bandeja')


@staff_requerido
@require_POST
def cambiar_plan(request, pk):
    """Activa o renueva un plan cuando llega el pago por Nequi."""
    cuenta = get_object_or_404(Cuenta, pk=pk)
    plan = request.POST.get('plan')
    if plan in dict(Cuenta.PLAN_CHOICES):
        cuenta.extender(plan)
        messages.success(
            request,
            f'{cuenta.nombre_publico}: plan {cuenta.get_plan_display().lower()}'
            + (f', vence el {cuenta.vence_en}.' if cuenta.vence_en else ', sin vencimiento.'),
        )
    return redirect(request.META.get('HTTP_REFERER') or 'salon_digital:bandeja')
