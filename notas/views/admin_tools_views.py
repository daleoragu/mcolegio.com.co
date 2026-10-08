# notas/views/admin_tools_views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.urls import reverse, reverse_lazy
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.contrib.auth.models import User, Group
from django.http import HttpResponse, HttpResponseNotFound
from django.contrib.auth import get_user_model
from django import forms
from django.forms import modelformset_factory
from django.db.models import Max
from django.views.generic.edit import UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.exceptions import ImproperlyConfigured, ValidationError
from django.views.decorators.http import require_POST
from django.db import IntegrityError, transaction

# --- INICIO: CORRECCIÓN DE IMPORTACIONES ---
from ..models.perfiles import Colegio, Docente, Curso, Estudiante
from ..models.academicos import (
    Materia, AsignacionDocente, PeriodoAcademico, ReporteParcial, 
    Observacion, ConfiguracionSistema, ConfiguracionCalificaciones,
    EscalaValoracion
)
from ..models.comunicaciones import Notificacion
from ..forms import ColegioPersonalizacionForm, EscalaValoracionForm
from ..permisos import es_admin, es_admin_usuario
# --- FIN: CORRECCIÓN DE IMPORTACIONES ---


# --- FUNCIÓN DE TEST PARA SUPERUSUARIO ---
def es_superusuario(user):
    return es_admin_usuario(user)


# --- VISTAS EXISTENTES (CÓDIGO ORIGINAL) ---
def enviar_notificacion_consolidada(request, estudiante, periodo, forzar_envio=False):
    colegio = request.colegio
    if not colegio:
        return False

    if Observacion.objects.filter(estudiante=estudiante, tipo_observacion='AUTOMATICA', periodo=periodo).exists():
        print(f"DEBUG: Notificación para {estudiante} en {periodo} ya fue procesada previamente.")
        return False

    reportes_realizados = ReporteParcial.objects.filter(estudiante=estudiante, periodo=periodo)
    total_asignaciones_curso = AsignacionDocente.objects.filter(
        curso=estudiante.curso, colegio=colegio
    ).count()

    if not forzar_envio and (reportes_realizados.count() < total_asignaciones_curso or total_asignaciones_curso == 0):
        return False
        
    if not reportes_realizados.exists():
        return False

    acudiente_email = getattr(estudiante, 'correo_electronico_contacto', None)
    if not acudiente_email:
        print(f"DEBUG: No se envió correo para {estudiante} (no hay email de contacto).")
        return False

    materias_con_dificultades = reportes_realizados.filter(presenta_dificultades=True)
    
    if materias_con_dificultades.exists():
        texto_materias = ", ".join([r.asignacion.materia.nombre for r in materias_con_dificultades])
        descripcion_observacion = f"Informe parcial consolidado del {periodo}: Se identificaron dificultades académicas en: {texto_materias}."
    else:
        descripcion_observacion = f"Informe parcial consolidado del {periodo}: ¡Felicitaciones! Desempeño adecuado en todas las materias reportadas."
    
    Observacion.objects.update_or_create(
        estudiante=estudiante, 
        tipo_observacion='AUTOMATICA',
        periodo=periodo,
        colegio=colegio,
        defaults={
            'descripcion': descripcion_observacion, 
            'docente_reporta': estudiante.curso.director_grado if estudiante.curso and estudiante.curso.director_grado else None
        }
    )
    
    context_email = {'estudiante': estudiante, 'periodo': periodo, 'materias_con_dificultades': materias_con_dificultades, 'colegio': colegio}
    html_message = render_to_string('notas/emails/email_reporte_parcial.html', context_email)
    plain_message = render_to_string('notas/emails/email_reporte_parcial.txt', context_email)
    asunto = f"Informe Parcial Consolidado - {estudiante.user.get_full_name()} - {periodo}"
    
    try:
        send_mail(asunto, plain_message, settings.DEFAULT_FROM_EMAIL, [acudiente_email], html_message=html_message)
        return True
    except Exception as e:
        print(f"ERROR al enviar correo para {estudiante}: {e}")
        return False

@login_required
@user_passes_test(es_superusuario)
def panel_control_periodos_vista(request):
    if not request.colegio:
        return HttpResponseNotFound("<h1>Colegio no configurado</h1>")

    if request.method == 'POST':
        try:
            action = request.POST.get('action')
            periodo_id = request.POST.get('periodo_id')
            
            periodo = get_object_or_404(PeriodoAcademico, id=periodo_id, colegio=request.colegio)
            
            mensaje_notificacion = ""
            url_notificacion = "#"

            if action == 'toggle_ingreso_notas':
                periodo.esta_activo = not periodo.esta_activo
                estado = "abierto" if periodo.esta_activo else "cerrado"
                messages.success(request, f"El Ingreso de Notas para '{periodo}' ha sido {estado}.")
                mensaje_notificacion = f"El plazo para Ingresar Notas del {periodo} ha sido {estado}."
                url_notificacion = reverse('notas:ingresar_notas_periodo')
            
            elif action == 'toggle_reporte_parcial':
                periodo.reporte_parcial_activo = not periodo.reporte_parcial_activo
                estado = "abierto" if periodo.reporte_parcial_activo else "cerrado"
                messages.success(request, f"El plazo para el Reporte Parcial de '{periodo}' ha sido {estado}.")
                mensaje_notificacion = f"El plazo para generar Reportes Parciales del {periodo} ha sido {estado}."
                url_notificacion = reverse('notas:reporte_parcial')

            elif action == 'toggle_nivelaciones':
                periodo.nivelaciones_activas = not periodo.nivelaciones_activas
                estado = "abierto" if periodo.nivelaciones_activas else "cerrado"
                messages.success(request, f"El plazo para las Nivelaciones de '{periodo}' ha sido {estado}.")
                mensaje_notificacion = f"El plazo para registrar Nivelaciones del {periodo} ha sido {estado}."
                url_notificacion = reverse('notas:plan_mejoramiento')
            
            else:
                messages.error(request, "Acción no reconocida.")

            periodo.save()
            
            if mensaje_notificacion:
                docentes_user = User.objects.filter(docente__colegio=request.colegio)
                for docente_user in docentes_user:
                    Notificacion.objects.create(
                        destinatario=docente_user,
                        mensaje=mensaje_notificacion,
                        tipo='PERIODO',
                        url=url_notificacion,
                        colegio=request.colegio
                    )

        except PeriodoAcademico.DoesNotExist:
            messages.error(request, "El periodo que intentó modificar no existe o no pertenece a este colegio.")
        except Exception as e:
            messages.error(request, f"Ocurrió un error inesperado: {e}")
        
        return redirect('notas:panel_control_periodos')

    periodos = PeriodoAcademico.objects.filter(colegio=request.colegio).order_by('-ano_lectivo', '-fecha_inicio')
    context = {
        'periodos': periodos,
        'colegio': request.colegio,
    }
    
    return render(request, 'notas/admin_tools/panel_control_periodos.html', context)


@login_required
@user_passes_test(es_superusuario)
def panel_control_promocion_vista(request):
    if not request.colegio:
        return HttpResponseNotFound("<h1>Colegio no configurado</h1>")

    config, created = ConfiguracionSistema.objects.get_or_create(colegio=request.colegio)

    if request.method == 'POST':
        max_reprobadas_str = request.POST.get('max_areas_reprobadas')
        
        if max_reprobadas_str is not None and max_reprobadas_str.isdigit():
            config.max_areas_reprobadas = int(max_reprobadas_str)
            config.save()
            messages.success(request, "La regla de promoción ha sido actualizada correctamente.")
            return redirect('notas:panel_control_promocion')
        else:
            messages.error(request, "Por favor, ingrese un número válido.")

    context = {
        'config': config,
        'colegio': request.colegio,
    }
    return render(request, 'notas/admin_tools/panel_control_promocion.html', context)


class MateriaPorcentajeForm(forms.ModelForm):
    class Meta:
        model = Materia
        fields = ['porcentaje_ser', 'porcentaje_saber', 'porcentaje_hacer', 'usar_ponderacion_equitativa']
        widgets = {
            'porcentaje_ser': forms.NumberInput(attrs={'class': 'form-control form-control-sm'}),
            'porcentaje_saber': forms.NumberInput(attrs={'class': 'form-control form-control-sm'}),
            'porcentaje_hacer': forms.NumberInput(attrs={'class': 'form-control form-control-sm'}),
            'usar_ponderacion_equitativa': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class ConfiguracionGlobalForm(forms.ModelForm):
    class Meta:
        model = ConfiguracionCalificaciones
        fields = [
            'docente_puede_modificar',
            'ponderar_periodos', 'exigir_periodos_completos',
            'colapsar_area_unica',
        ]
        widgets = {
            'ponderar_periodos': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'exigir_periodos_completos': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'colapsar_area_unica': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'docente_puede_modificar': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class PesoPeriodoForm(forms.ModelForm):
    """Solo el porcentaje; el resto del periodo se edita en su propia pantalla."""
    class Meta:
        model = PeriodoAcademico
        fields = ['peso_porcentual']
        widgets = {
            'peso_porcentual': forms.NumberInput(
                attrs={'class': 'form-control form-control-sm', 'step': '0.01', 'min': 0, 'max': 100}),
        }

@user_passes_test(es_admin_usuario)
def configuracion_calificaciones_vista(request):
    if not request.colegio:
        return HttpResponseNotFound("<h1>Colegio no configurado</h1>")

    materias_colegio = Materia.objects.filter(colegio=request.colegio)
    MateriaFormSet = modelformset_factory(Materia, form=MateriaPorcentajeForm, extra=0)
    PesosFormSet = modelformset_factory(PeriodoAcademico, form=PesoPeriodoForm, extra=0)

    config_global, _ = ConfiguracionCalificaciones.objects.get_or_create(colegio=request.colegio)

    ano_actual = PeriodoAcademico.objects.filter(colegio=request.colegio).aggregate(
        maximo=Max('ano_lectivo'))['maximo']
    periodos_colegio = PeriodoAcademico.objects.filter(
        colegio=request.colegio, ano_lectivo=ano_actual).order_by('fecha_inicio')

    if request.method == 'POST':
        formset = MateriaFormSet(request.POST, queryset=materias_colegio)
        form_global = ConfiguracionGlobalForm(request.POST, instance=config_global)
        formset_pesos = PesosFormSet(request.POST, queryset=periodos_colegio, prefix='pesos')
        
        # Se añade la variable para forzar la sincronización
        forzar_sincronizacion = request.POST.get('forzar_sincronizacion') == 'on'

        if formset.is_valid() and form_global.is_valid() and formset_pesos.is_valid():
            materias_guardadas = formset.save()
            form_global.save()
            formset_pesos.save()

            if form_global.cleaned_data.get('ponderar_periodos'):
                suma = sum(
                    (f.cleaned_data.get('peso_porcentual') or 0) for f in formset_pesos.forms)
                if abs(float(suma) - 100) > 0.01:
                    messages.warning(
                        request,
                        f'Los porcentajes de los periodos suman {suma}% en vez de 100%. '
                        f'Las notas se calculan repartiendo proporcionalmente, pero conviene '
                        f'corregirlos para que los boletines digan lo que esperas.'
                    )

            # ==================================================================
            # INICIO DE LA CORRECCIÓN
            # ==================================================================
            # Si el administrador marcó la casilla, se forzará la actualización
            # de TODAS las asignaciones, eliminando personalizaciones de docentes.
            if forzar_sincronizacion:
                with transaction.atomic():
                    for materia in materias_guardadas:
                        AsignacionDocente.objects.filter(materia=materia).update(
                            # Se resetea el 'usar_ponderacion_equitativa' de la asignación
                            # para que dependa de la configuración de la materia.
                            usar_ponderacion_equitativa=True, 
                            porcentaje_ser=materia.porcentaje_ser,
                            porcentaje_saber=materia.porcentaje_saber,
                            porcentaje_hacer=materia.porcentaje_hacer
                        )
                messages.success(request, 'Configuración guardada y sincronizada forzosamente con todas las asignaciones.')
            else:
                messages.success(request, 'La configuración de calificaciones por defecto ha sido actualizada.')
            # ==================================================================
            # FIN DE LA CORRECCIÓN
            # ==================================================================
            return redirect('notas:configuracion_calificaciones')
        else:
            messages.error(request, 'Por favor, corrija los errores en el formulario.')

    else:
        formset = MateriaFormSet(queryset=materias_colegio.order_by('nombre'))
        form_global = ConfiguracionGlobalForm(instance=config_global)
        formset_pesos = PesosFormSet(queryset=periodos_colegio, prefix='pesos')

    context = {
        'formset': formset,
        'form_global': form_global,
        'formset_pesos': formset_pesos,
        'periodos_colegio': periodos_colegio,
        'page_title': 'Configuración de Calificaciones por Materia',
        'colegio': request.colegio,
    }
    return render(request, 'notas/admin_tools/configuracion_calificaciones.html', context)


@login_required
@user_passes_test(es_superusuario)
def configuracion_escala_valoracion_vista(request):
    if not request.colegio:
        return HttpResponseNotFound("<h1>Colegio no configurado</h1>")

    colegio = request.colegio
    
    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'create':
            form = EscalaValoracionForm(request.POST)
            form.instance.colegio = colegio
            if form.is_valid():
                try:
                    form.save()
                    messages.success(request, f"Nivel '{form.cleaned_data['nombre_desempeno']}' creado exitosamente.")
                except Exception as e:
                    messages.error(request, f"Ocurrió un error inesperado al guardar el nivel: {e}")
            else:
                for field, errors in form.errors.items():
                    for error in errors:
                        messages.error(request, f"Error en el campo '{field}': {error}")

        elif action == 'delete':
            escala_id = request.POST.get('escala_id')
            escala_a_eliminar = get_object_or_404(EscalaValoracion, id=escala_id, colegio=colegio)
            try:
                nombre_escala = escala_a_eliminar.nombre_desempeno
                escala_a_eliminar.delete()
                messages.warning(request, f"El nivel '{nombre_escala}' ha sido eliminado.")
            except Exception as e:
                messages.error(request, f"No se pudo eliminar el nivel: {e}")
        
        return redirect('notas:configuracion_escala_valoracion')

    escalas = EscalaValoracion.objects.filter(colegio=colegio).order_by('valor_minimo')
    form = EscalaValoracionForm()

    context = {
        'titulo': 'Configurar Escala de Valoración',
        'escalas': escalas,
        'form': form,
        'colegio': colegio,
    }
    return render(request, 'notas/admin_tools/configuracion_escala.html', context)

@login_required
@user_passes_test(es_superusuario)
@require_POST
def editar_escala_valoracion_vista(request, escala_id):
    if not request.colegio:
        return HttpResponseNotFound("<h1>Colegio no configurado</h1>")
    
    escala_a_editar = get_object_or_404(EscalaValoracion, id=escala_id, colegio=request.colegio)
    form = EscalaValoracionForm(request.POST, instance=escala_a_editar)
    
    form.instance.colegio = request.colegio

    if form.is_valid():
        try:
            form.save()
            messages.success(request, f"Nivel '{escala_a_editar.nombre_desempeno}' actualizado correctamente.")
        except Exception as e:
            messages.error(request, f"Ocurrió un error al actualizar el nivel: {e}")
    else:
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(request, f"Error al editar '{escala_a_editar.nombre_desempeno}': {error}")
    
    return redirect('notas:configuracion_escala_valoracion')


class ColegioPersonalizacionUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Colegio
    form_class = ColegioPersonalizacionForm
    template_name = 'notas/admin_tools/configuracion_colegio.html'
    success_url = reverse_lazy('configuracion_colegio')

    def get_object(self, queryset=None):
        if hasattr(self.request, 'colegio') and self.request.colegio:
            return self.request.colegio
        try:
            if hasattr(self.request.user, 'docente'):
                return self.request.user.docente.colegio
        except Docente.DoesNotExist:
            pass
        if self.request.user.is_superuser:
            return Colegio.objects.first()
        raise ImproperlyConfigured("El usuario no está asociado a ningún colegio para poder editarlo.")

    def test_func(self):
        return es_admin(self.request)

    def form_valid(self, form):
        messages.success(self.request, '¡La configuración de tu colegio ha sido actualizada!')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo_pagina'] = f"Personalizar la Apariencia de {self.object.nombre}"
        context['colegio'] = self.object
        return context


@user_passes_test(es_superusuario)
@require_POST
def crear_periodo_vista(request):
    if not request.colegio:
        return HttpResponseNotFound("<h1>Colegio no configurado</h1>")
    try:
        PeriodoAcademico.objects.create(
            colegio=request.colegio,
            nombre=request.POST.get('nombre'),
            ano_lectivo=int(request.POST.get('ano_lectivo')),
            fecha_inicio=request.POST.get('fecha_inicio'),
            fecha_fin=request.POST.get('fecha_fin'),
            esta_activo=request.POST.get('esta_activo') == 'on',
            reporte_parcial_activo=request.POST.get('reporte_parcial_activo') == 'on',
            nivelaciones_activas=request.POST.get('nivelaciones_activas') == 'on'
        )
        messages.success(request, 'Período académico creado exitosamente.')
    except (ValueError, IntegrityError) as e:
        messages.error(request, f"Error al crear el período: {e}")
    except Exception as e:
        messages.error(request, f"Ocurrió un error inesperado: {e}")
    return redirect('notas:panel_control_periodos')


@user_passes_test(es_superusuario)
@require_POST
def editar_periodo_vista(request, periodo_id):
    if not request.colegio:
        return HttpResponseNotFound("<h1>Colegio no configurado</h1>")
    periodo = get_object_or_404(PeriodoAcademico, id=periodo_id, colegio=request.colegio)
    try:
        periodo.nombre = request.POST.get('nombre')
        periodo.ano_lectivo = int(request.POST.get('ano_lectivo'))
        periodo.fecha_inicio = request.POST.get('fecha_inicio')
        periodo.fecha_fin = request.POST.get('fecha_fin')
        periodo.esta_activo = request.POST.get('esta_activo') == 'on'
        periodo.reporte_parcial_activo = request.POST.get('reporte_parcial_activo') == 'on'
        periodo.nivelaciones_activas = request.POST.get('nivelaciones_activas') == 'on'
        periodo.save()
        messages.success(request, 'Período académico actualizado exitosamente.')
    except (ValueError, IntegrityError) as e:
        messages.error(request, f"Error al actualizar el período: {e}")
    except Exception as e:
        messages.error(request, f"Ocurrió un error inesperado: {e}")
    return redirect('notas:panel_control_periodos')


@user_passes_test(es_superusuario)
@require_POST
def eliminar_periodo_vista(request, periodo_id):
    if not request.colegio:
        return HttpResponseNotFound("<h1>Colegio no configurado</h1>")
    periodo = get_object_or_404(PeriodoAcademico, id=periodo_id, colegio=request.colegio)
    try:
        periodo.delete()
        messages.success(request, 'Período eliminado exitosamente.')
    except Exception as e:
        messages.error(request, f'Error al eliminar el período: {e}')
    return redirect('notas:panel_control_periodos')
