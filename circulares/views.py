from django import forms
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseNotFound
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from notas import avisos_familia
from notas.models import Curso
from notas.permisos import admin_requerido

from . import logica
from .models import Circular, Lectura


class CircularForm(forms.ModelForm):
    class Meta:
        model = Circular
        fields = ['titulo', 'cuerpo', 'adjunto', 'para', 'cursos', 'pide_confirmacion', 'fecha_limite', 'por_whatsapp']
        widgets = {
            'titulo': forms.TextInput(attrs={'class': 'form-control'}),
            'cuerpo': forms.Textarea(attrs={'class': 'form-control', 'rows': 10}),
            'adjunto': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'para': forms.RadioSelect,
            'cursos': forms.CheckboxSelectMultiple,
            'pide_confirmacion': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'por_whatsapp': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'fecha_limite': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}, format='%Y-%m-%d'),
        }

    def __init__(self, *args, colegio=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['cursos'].queryset = Curso.objects.filter(colegio=colegio).order_by('nombre')
        self.fields['cursos'].required = False
        if not logica.whatsapp_disponible(colegio):      # sin línea conectada no se ofrece
            del self.fields['por_whatsapp']

    def clean(self):
        datos = super().clean()
        if datos.get('para') == 'CURSOS' and not datos.get('cursos'):
            self.add_error('cursos', 'Escoja al menos un curso.')
        return datos


def _url_ver(request, circular):
    return request.build_absolute_uri(reverse('circulares:ver', args=[circular.id]))


# ---------------------------------------------------------------------------
# Administración
# ---------------------------------------------------------------------------
@admin_requerido
def lista(request):
    if not request.colegio:
        return HttpResponseNotFound('<h1>Colegio no configurado</h1>')
    circulares = list(Circular.objects.filter(colegio=request.colegio))
    for c in circulares:
        c.resumen = logica.resumen(c) if not c.es_borrador else None
    return render(request, 'circulares/lista.html', {'colegio': request.colegio, 'circulares': circulares})


@admin_requerido
def editar(request, pk=None):
    circular = get_object_or_404(Circular, pk=pk, colegio=request.colegio) if pk else None
    if circular and not circular.es_borrador:
        messages.info(request, 'Esta circular ya se publicó: no se puede cambiar.')
        return redirect('circulares:detalle', pk=circular.pk)
    form = CircularForm(request.POST or None, request.FILES or None, instance=circular, colegio=request.colegio)
    if request.method == 'POST' and form.is_valid():
        nueva = form.save(commit=False)
        nueva.colegio = request.colegio
        nueva.autor = nueva.autor or request.user
        nueva.save()
        form.save_m2m()
        if request.POST.get('accion') == 'publicar':
            if not logica.destinatarios(nueva):
                messages.error(request, 'No hay a quién enviarla: los cursos escogidos no tienen estudiantes activos. '
                                        'Quedó guardada como borrador.')
                return redirect('circulares:editar', pk=nueva.pk)
            url = _url_ver(request, nueva)
            total, correos = logica.publicar(nueva, url)
            messages.success(request, f'Circular N.º {nueva.numero} publicada para {total} destinatario'
                                      f'{"s" if total != 1 else ""}' + (f'; {correos} correo(s) enviados.' if correos else '.'))
            if nueva.por_whatsapp and logica.whatsapp_disponible(request.colegio):
                logica.lanzar_whatsapp(nueva, url)
                messages.info(request, 'Los WhatsApp a las familias se están enviando. Aquí abajo ve a quién le llegó.')
            return redirect('circulares:detalle', pk=nueva.pk)
        messages.success(request, 'Borrador guardado.')
        return redirect('circulares:editar', pk=nueva.pk)
    return render(request, 'circulares/editar.html', {'colegio': request.colegio, 'form': form, 'circular': circular})


@admin_requerido
@require_POST
def eliminar(request, pk):
    circular = get_object_or_404(Circular, pk=pk, colegio=request.colegio)
    if circular.es_borrador:
        circular.delete()
        messages.success(request, 'Borrador eliminado.')
    else:
        messages.error(request, 'Una circular publicada no se elimina: queda como constancia.')
    return redirect('circulares:lista')


@admin_requerido
def detalle(request, pk):
    circular = get_object_or_404(Circular, pk=pk, colegio=request.colegio)
    filtro = request.GET.get('ver', 'pendientes')
    lecturas = circular.lecturas.select_related('usuario', 'estudiante__curso', 'estudiante__ficha').order_by(
        'estudiante__curso__nombre', 'usuario__last_name', 'usuario__first_name')
    if filtro == 'pendientes':
        lecturas = lecturas.filter(**({'confirmada__isnull': True} if circular.pide_confirmacion else {'abierta__isnull': True}))
    elif filtro == 'listos':
        lecturas = lecturas.filter(**({'confirmada__isnull': False} if circular.pide_confirmacion else {'abierta__isnull': False}))
    url = _url_ver(request, circular)
    texto = logica.texto_recordatorio(circular, url)
    filas = []
    for l in lecturas[:600]:
        contactos = avisos_familia.contactos(l.estudiante) if l.estudiante else []
        for c in contactos:
            c['enlace'] = avisos_familia.enlace_whatsapp(c['numero'], texto)
        filas.append({'l': l, 'contactos': contactos})
    wa = logica.whatsapp_disponible(request.colegio)
    return render(request, 'circulares/detalle.html', {
        'colegio': request.colegio, 'c': circular, 'resumen': logica.resumen(circular), 'filas': filas,
        'filtro': filtro, 'texto': texto, 'whatsapp_disponible': wa,
        'faltan_whatsapp': logica.pendientes_whatsapp(circular).count() if wa else 0})


@admin_requerido
@require_POST
def reenviar_whatsapp(request, pk):
    """Manda el WhatsApp a las familias que faltan (por ejemplo, después del límite diario de Meta)."""
    circular = get_object_or_404(Circular, pk=pk, colegio=request.colegio, publicada__isnull=False)
    if not logica.whatsapp_disponible(request.colegio):
        messages.error(request, 'La línea de WhatsApp no está conectada o el colegio no tiene activados los avisos automáticos.')
    else:
        faltan = logica.pendientes_whatsapp(circular).count()
        if faltan:
            if not circular.por_whatsapp:
                circular.por_whatsapp = True
                circular.save(update_fields=['por_whatsapp'])
            logica.lanzar_whatsapp(circular, _url_ver(request, circular))
            messages.info(request, f'Enviando el WhatsApp a {faltan} familia{"s" if faltan != 1 else ""} que faltaban.')
        else:
            messages.info(request, 'No falta ninguna familia por WhatsApp.')
    return redirect('circulares:detalle', pk=circular.pk)


# ---------------------------------------------------------------------------
# Familias y docentes
# ---------------------------------------------------------------------------
@login_required
def mis_circulares(request):
    lecturas = (Lectura.objects.filter(usuario=request.user, circular__colegio=request.colegio)
                .select_related('circular').order_by('-circular__publicada'))
    return render(request, 'circulares/mis_circulares.html', {'colegio': request.colegio, 'lecturas': lecturas})


@login_required
def ver(request, pk):
    circular = get_object_or_404(Circular, pk=pk, colegio=request.colegio, publicada__isnull=False)
    lectura = Lectura.objects.filter(circular=circular, usuario=request.user).first()
    es_admin = getattr(request.user, 'es_admin_colegio', False) or request.user.is_superuser
    if lectura is None and not es_admin:
        return HttpResponseNotFound('<h1>Esta circular no es para usted.</h1>')
    if lectura and not lectura.abierta:
        lectura.abierta = timezone.now()
        lectura.save(update_fields=['abierta'])
    return render(request, 'circulares/ver.html', {'colegio': request.colegio, 'c': circular, 'lectura': lectura})


@login_required
@require_POST
def confirmar(request, pk):
    lectura = get_object_or_404(Lectura, circular_id=pk, usuario=request.user, circular__colegio=request.colegio)
    if not lectura.confirmada:
        lectura.confirmada = timezone.now()
        lectura.abierta = lectura.abierta or lectura.confirmada
        lectura.quien_confirma = (request.POST.get('nombre') or '').strip()[:120]
        lectura.save()
        messages.success(request, 'Gracias: quedó registrado que leyó la circular.')
    return redirect('circulares:ver', pk=pk)
