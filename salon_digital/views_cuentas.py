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

    def get_context_data(self, **kwargs):
        from . import social
        datos = super().get_context_data(**kwargs)
        datos['proveedores'] = social.disponibles()
        return datos

    def get_success_url(self):
        siguiente = self.request.GET.get('siguiente')
        if siguiente and siguiente.startswith('/'):
            return siguiente
        return str(reverse_lazy('aula:inicio'))


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

    from . import social
    return render(request, 'salon_digital/registro.html', {'form': form, 'proveedores': social.disponibles()})


@login_required
def crear_cuenta(request):
    """Para un usuario de la plataforma que todavía no tiene cuenta de Salón Digital."""
    if getattr(request.user, 'cuenta_salon', None):
        return redirect('salon_digital:panel')

    from . import social
    inicial = {'nombre_publico': request.user.get_full_name() or request.user.username,
               'slug': social.sugerir_usuario(request.user)}
    form = CuentaForm(request.POST or None, initial=inicial)
    if request.method == 'POST' and form.is_valid():
        cuenta = form.save(commit=False)
        cuenta.usuario = request.user
        cuenta.save()
        messages.success(request, 'Cuenta creada. Tienes 15 días de prueba. Para publicar, sube el documento '
                                  'que acredita que eres docente.')
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


# ---------------------------------------------------------------------------
# Entrar con Google o Facebook
# ---------------------------------------------------------------------------
def social_iniciar(request, proveedor):
    from . import social
    try:
        url = social.url_autorizar(request, proveedor, request.GET.get('siguiente', ''))
    except social.ErrorSocial as e:
        messages.error(request, str(e))
        return redirect('salon_digital:registro')
    return redirect(url)


def social_vuelta(request, proveedor):
    from . import social
    try:
        datos = social.datos_del_regreso(request, proveedor)
        usuario, nuevo = social.usuario_para(datos)
    except social.ErrorSocial as e:
        messages.error(request, str(e))
        return redirect('salon_digital:registro')
    login(request, usuario, backend='django.contrib.auth.backends.ModelBackend')
    if not getattr(usuario, 'cuenta_salon', None):
        if nuevo:
            messages.info(request, f'¡Bienvenido! Solo falta el nombre con el que te verán tus estudiantes.')
        return redirect('salon_digital:crear_cuenta')
    siguiente = datos.get('siguiente') or ''
    if siguiente.startswith('/') and not siguiente.startswith('//'):
        return redirect(siguiente)
    return redirect('aula:inicio')


def eliminar_datos(request):
    """Instrucciones para borrar los datos (las pide Facebook para aprobar la app)."""
    return render(request, 'salon_digital/eliminar_datos.html')

