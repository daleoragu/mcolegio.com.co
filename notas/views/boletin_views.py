# notas/views/boletin_views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, HttpResponseForbidden, HttpResponseNotFound
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.template.loader import render_to_string
from notas.boletin.ponderacion import ajustes as ajustes_colegio
import datetime
from pathlib import Path
import os

try:
    from weasyprint import HTML
    PDF_SUPPORT = True
except ImportError:
    PDF_SUPPORT = False

# Se añade FichaEstudiante para poder obtener el número de documento y la foto
from ..models import (Curso, Sede, PeriodoAcademico, Docente, AsignacionDocente, Estudiante, FichaEstudiante,
                      HistorialMatricula)
from ..boletin.logic import get_datos_boletin_curso, get_datos_boletin_final
from ..permisos import es_admin, es_admin_usuario

@login_required
def selector_boletin_vista(request):
    """
    Muestra los filtros para seleccionar qué boletín generar, filtrando
    por el colegio actual.
    """
    if not request.colegio:
        return HttpResponseNotFound("<h1>Colegio no configurado</h1>")

    context = {'colegio': request.colegio}
    user = request.user
    docente_seleccionado_id = request.GET.get('docente_id')

    if es_admin_usuario(user):
        # Filtra los docentes por el colegio actual
        context['todos_los_docentes'] = Docente.objects.filter(colegio=request.colegio).order_by('user__last_name', 'user__first_name')
        context['docente_seleccionado_id'] = docente_seleccionado_id
        
        cursos = Curso.objects.filter(colegio=request.colegio).order_by('nombre')
        if docente_seleccionado_id:
            cursos_ids = AsignacionDocente.objects.filter(docente_id=docente_seleccionado_id, colegio=request.colegio).values_list('curso_id', flat=True).distinct()
            cursos = cursos.filter(id__in=cursos_ids)
        
        context['cursos'] = cursos
    else:
        try:
            docente_actual = get_object_or_404(Docente, user=user, colegio=request.colegio)
            cursos_ids = AsignacionDocente.objects.filter(docente=docente_actual, colegio=request.colegio).values_list('curso_id', flat=True).distinct()
            context['cursos'] = Curso.objects.filter(id__in=cursos_ids, colegio=request.colegio).order_by('nombre')
        except Docente.DoesNotExist:
            messages.error(request, "Acceso denegado. Su perfil no está asociado a un docente en este colegio.")
            return redirect('notas:dashboard')

    # Filtra periodos y años por el colegio actual
    context['sedes_filtro'] = list(Sede.objects.filter(colegio=request.colegio, activa=True))
    context['periodos'] = PeriodoAcademico.objects.filter(colegio=request.colegio).order_by('-ano_lectivo', 'nombre')
    context['anos_lectivos'] = PeriodoAcademico.objects.filter(colegio=request.colegio).values_list('ano_lectivo', flat=True).distinct().order_by('-ano_lectivo')
    
    return render(request, 'notas/admin_tools/selector_boletin.html', context)

def ano_del_reporte(colegio, reporte_id):
    """El año lectivo de un reporte: 'FINAL_2026' -> 2026; un periodo -> su año."""
    if reporte_id.startswith('FINAL_'):
        try:
            return int(reporte_id.split('_')[1])
        except (ValueError, IndexError):
            return None
    if not str(reporte_id).isdigit():
        return None
    return (PeriodoAcademico.objects.filter(id=reporte_id, colegio=colegio)
            .values_list('ano_lectivo', flat=True).first())


def estudiante_estuvo_en(estudiante, curso, ano):
    """¿El estudiante estuvo en `curso` el año `ano`?

    Si ese año ya se promovió, lo dice el historial: así un estudiante que hoy
    está en SEGUNDO puede abrir su boletín de PRIMERO del año pasado, y no
    puede abrir el de SEGUNDO de un año en que no estuvo ahí. Si el año no se
    ha promovido, vale su curso de hoy, como siempre.
    """
    if ano is not None:
        h = HistorialMatricula.objects.filter(estudiante=estudiante, ano_lectivo=ano).first()
        if h is not None:
            return h.curso_id == curso.id
    return estudiante.curso_id == curso.id


@login_required
def generar_boletin_vista(request):
    """
    Genera un boletín de periodo o final, asegurando que todos los datos
    correspondan al colegio actual y corrigiendo la identificación del estudiante.
    """
    if not request.colegio:
        return HttpResponseNotFound("<h1>Colegio no configurado</h1>")
    if not PDF_SUPPORT:
        return HttpResponse("Error: La librería 'WeasyPrint' no está instalada.", status=500)

    curso_id = request.GET.get('curso_id')
    reporte_id = request.GET.get('reporte_id')

    if not curso_id or not reporte_id:
        return HttpResponse("Error: Debe seleccionar un curso y un tipo de reporte.", status=400)
    
    # Filtra el curso por el colegio actual para seguridad
    curso = get_object_or_404(Curso, id=curso_id, colegio=request.colegio)
    user = request.user

    es_docente_del_curso = False
    es_estudiante_del_curso = False

    if hasattr(user, 'docente') and user.docente.colegio == request.colegio:
        es_docente_del_curso = AsignacionDocente.objects.filter(docente=user.docente, curso=curso).exists()
    
    if hasattr(user, 'estudiante') and user.estudiante.colegio == request.colegio:
        es_estudiante_del_curso = estudiante_estuvo_en(
            user.estudiante, curso, ano_del_reporte(request.colegio, reporte_id))

    if not (es_admin_usuario(user) or es_docente_del_curso or es_estudiante_del_curso):
        return HttpResponseForbidden("No tiene permiso para ver los boletines de este curso.")

    estudiante_especifico = user.estudiante if es_estudiante_del_curso and not es_admin_usuario(user) else None

    # --- NUEVO: SELECCIÓN DE PLANTILLA SEGÚN NIVEL DEL CURSO ---
    if curso.nivel == 'PRE':
        # --- Boletín final ---
        if reporte_id.startswith('FINAL_'):
            try:
                ano_lectivo = int(reporte_id.split('_')[1])
            except (ValueError, IndexError):
                return HttpResponse("Error: Formato de reporte final no válido.", status=400)
            
            boletines_data, nombres_periodos = get_datos_boletin_final(request.colegio, curso, ano_lectivo, estudiante_especifico)
            if not boletines_data:
                return HttpResponse("No se encontraron datos para generar el boletín final de este curso y año.")

            template_path = 'notas/boletin/boletin_prescolar_final_pdf.html'
            pdf_filename = f'boletin_final_pre_{curso.nombre}_{ano_lectivo}.pdf'
            context = { "boletines": boletines_data, "nombres_periodos": nombres_periodos, "curso": curso, "ano_lectivo": ano_lectivo, "colegio": request.colegio, "ajustes": ajustes_colegio(request.colegio) }

        # --- Boletín de periodo ---
        else:
            try:
                periodo = get_object_or_404(PeriodoAcademico, id=reporte_id, colegio=request.colegio)
            except (ValueError, PeriodoAcademico.DoesNotExist):
                return HttpResponse("Error: El periodo seleccionado no es válido.", status=400)

            boletines_data = get_datos_boletin_curso(request.colegio, curso, periodo, estudiante_especifico)
            if not boletines_data:
                return HttpResponse("No se encontraron datos para generar el boletín de este periodo.")

            template_path = 'notas/boletin/boletin_prescolar_pdf.html'
            pdf_filename = f'boletines_pre_{curso.nombre}_{periodo.get_nombre_display()}.pdf'
            context = { "boletines": boletines_data, "curso": curso, "periodo": periodo, "colegio": request.colegio, "ajustes": ajustes_colegio(request.colegio) }

    # --- Cursos normales (primaria, básica, media) ---
    else:
        if reporte_id.startswith('FINAL_'):
            try:
                ano_lectivo = int(reporte_id.split('_')[1])
            except (ValueError, IndexError):
                return HttpResponse("Error: Formato de reporte final no válido.", status=400)
            
            boletines_data, nombres_periodos = get_datos_boletin_final(request.colegio, curso, ano_lectivo, estudiante_especifico)
            if not boletines_data:
                return HttpResponse("No se encontraron datos para generar el boletín final de este curso y año.")

            template_path = 'notas/boletin/boletin_final_pdf.html'
            pdf_filename = f'boletin_final_{curso.nombre}_{ano_lectivo}.pdf'
            context = { "boletines": boletines_data, "nombres_periodos": nombres_periodos, "curso": curso, "ano_lectivo": ano_lectivo, "colegio": request.colegio, "ajustes": ajustes_colegio(request.colegio) }

        else:
            try:
                periodo = get_object_or_404(PeriodoAcademico, id=reporte_id, colegio=request.colegio)
            except (ValueError, PeriodoAcademico.DoesNotExist):
                return HttpResponse("Error: El periodo seleccionado no es válido.", status=400)

            boletines_data = get_datos_boletin_curso(request.colegio, curso, periodo, estudiante_especifico)
            if not boletines_data:
                return HttpResponse("No se encontraron datos para generar el boletín de este periodo.")

            template_path = 'notas/boletin/boletin_pdf.html'
            pdf_filename = f'boletines_{curso.nombre}_{periodo.get_nombre_display()}.pdf'
            context = { "boletines": boletines_data, "curso": curso, "periodo": periodo, "colegio": request.colegio, "ajustes": ajustes_colegio(request.colegio) }

    # --- INICIO: CORRECCIÓN FOTO E IDENTIFICACIÓN SEGURA ---
    for boletin in boletines_data:
        estudiante_obj = boletin.get('estudiante')
        if not estudiante_obj:
            boletin['identificacion'] = "Estudiante no encontrado"
            boletin['foto_estudiante_url'] = None
            boletin['edad'] = "No registrada"
            boletin['acudiente'] = "No registrado"
            continue

        try:
            ficha = FichaEstudiante.objects.get(estudiante=estudiante_obj)
            boletin['identificacion'] = ficha.numero_documento or estudiante_obj.user.username
            
            # Cálculo de Edad
            if ficha.fecha_nacimiento:
                today = datetime.date.today()
                edad = today.year - ficha.fecha_nacimiento.year - ((today.month, today.day) < (ficha.fecha_nacimiento.month, ficha.fecha_nacimiento.day))
                boletin['edad'] = f"{edad} años"
            else:
                boletin['edad'] = "No registrada"
                
            # Nombre de Acudiente
            boletin['acudiente'] = ficha.nombre_acudiente or "No registrado"
            
            # Usamos .url para que WeasyPrint maneje la ruta de forma nativa sin bloqueos (deadlock)
            if ficha.foto and hasattr(ficha.foto, 'url'):
                boletin['foto_estudiante_url'] = ficha.foto.url
            else:
                boletin['foto_estudiante_url'] = None
                
        except FichaEstudiante.DoesNotExist:
            boletin['identificacion'] = estudiante_obj.user.username
            boletin['foto_estudiante_url'] = None
            boletin['edad'] = "No registrada"
            boletin['acudiente'] = "No registrado"
    # --- FIN: CORRECCIÓN ---

    html_string = render_to_string(template_path, context)
    # El base_url se encarga de procesar los ".url" de forma segura
    pdf_file = HTML(string=html_string, base_url=request.build_absolute_uri()).write_pdf()

    response = HttpResponse(pdf_file, content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="{pdf_filename}"'
    
    return response