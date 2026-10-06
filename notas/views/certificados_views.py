# notas/views/certificados_views.py

from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import HttpResponse, HttpResponseNotFound

from ..models.perfiles import Estudiante, Curso, Colegio
from ..reportes.certificado_generator import CertificadoPDFGenerator
from ..permisos import es_admin, es_admin_usuario

# Función de permisos para administradores del colegio
def es_admin_del_colegio(user):
    """Superusuario o administrador de ESTE colegio (ver notas/permisos.py)."""
    return es_admin_usuario(user)

@login_required
@user_passes_test(es_admin_del_colegio)
def selector_certificados_vista(request):
    """
    Muestra una lista de estudiantes para que el administrador pueda
    seleccionar a quién generar el certificado.
    """
    if not request.colegio:
        return HttpResponseNotFound("<h1>Colegio no configurado</h1>")

    cursos = Curso.objects.filter(colegio=request.colegio).order_by('nombre')
    curso_seleccionado_id = request.GET.get('curso_id')

    if curso_seleccionado_id:
        estudiantes = Estudiante.objects.filter(colegio=request.colegio, curso_id=curso_seleccionado_id, is_active=True)
    else:
        estudiantes = Estudiante.objects.filter(colegio=request.colegio, is_active=True)

    context = {
        'estudiantes': estudiantes,
        'cursos': cursos,
        'curso_seleccionado_id': curso_seleccionado_id,
    }
    return render(request, 'notas/admin_tools/selector_certificados.html', context)

@login_required
@user_passes_test(es_admin_del_colegio)
def generar_certificado_estudio_pdf(request, estudiante_id):
    """
    Genera el PDF del certificado de estudio para un estudiante específico.
    """
    if not request.colegio:
        return HttpResponseNotFound("<h1>Colegio no configurado</h1>")

    estudiante = get_object_or_404(Estudiante, id=estudiante_id, colegio=request.colegio)
    
    generator = CertificadoPDFGenerator(colegio=request.colegio)
    pdf_file, error_message = generator.generate_report(request, estudiante)

    if error_message:
        return HttpResponse(error_message, status=500)

    nombre_archivo = f"certificado_{estudiante.user.get_full_name().replace(' ', '_')}.pdf"
    response = HttpResponse(pdf_file, content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="{nombre_archivo}"'
    return response
