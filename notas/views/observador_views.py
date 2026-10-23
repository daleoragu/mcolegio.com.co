# notas/views/observador_views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import HttpResponse, HttpResponseNotFound
from django.template.loader import render_to_string
from django.urls import reverse

try:
    from weasyprint import HTML
    PDF_SUPPORT = True
except ImportError:
    PDF_SUPPORT = False

from ..forms import RegistroObservadorForm, FichaEstudianteForm
from ..models import (
    Docente, Estudiante, Curso, FichaEstudiante, 
    AsignacionDocente, RegistroObservador, Notificacion
)
from ..permisos import es_admin, es_admin_usuario, es_docente_usuario
from .. import avisos_familia, observador_catalogo

def es_docente_o_superuser(user):
    return es_admin_usuario(user) or es_docente_usuario(user)


def _cursos_de_la_sede_del_docente(docente, colegio):
    """Todos los cursos de las sedes donde el docente tiene clase.

    Un docente puede anotar en el observador a cualquier estudiante de su
    sede, no solo a los de sus cursos (el que lo vio en el patio, en el
    descanso, en una salida). Si el colegio no usa sedes, son todos los cursos.
    """
    from django.db.models import Q
    asignados = Curso.objects.filter(
        colegio=colegio,
        id__in=AsignacionDocente.objects.filter(docente=docente, colegio=colegio).values_list('curso_id', flat=True))
    sedes = set(asignados.values_list('sede_id', flat=True))
    filtro = Q(sede_id__in=[s for s in sedes if s is not None])
    if None in sedes:
        filtro |= Q(sede__isnull=True)
    if not sedes:
        return Curso.objects.none()
    return Curso.objects.filter(colegio=colegio).filter(filtro).order_by('nombre')

@login_required
@user_passes_test(es_docente_o_superuser)
def observador_selector_vista(request):
    if not request.colegio:
        return HttpResponseNotFound("<h1>Colegio no configurado</h1>")

    user = request.user
    cursos = Curso.objects.none()
    mis_cursos_ids = set()
    estudiantes = Estudiante.objects.none()

    if es_admin_usuario(user):
        cursos = Curso.objects.filter(colegio=request.colegio).order_by('nombre')
    else:
        docente = Docente.objects.filter(user=user, colegio=request.colegio).first()
        if docente is None:
            messages.error(request, "Su perfil no está asociado a un docente en este colegio.")
            return redirect('notas:dashboard')
        cursos = _cursos_de_la_sede_del_docente(docente, request.colegio)
        mis_cursos_ids = set(AsignacionDocente.objects.filter(docente=docente, colegio=request.colegio)
                             .values_list('curso_id', flat=True))

    curso_seleccionado_id = request.GET.get('curso_id')
    if curso_seleccionado_id:
        estudiantes = Estudiante.objects.filter(colegio=request.colegio, is_active=True)
        if curso_seleccionado_id == 'todos':
            # Todos los estudiantes de la(s) sede(s) del docente, para buscar por nombre.
            estudiantes = estudiantes.filter(curso__in=cursos)
        else:
            estudiantes = estudiantes.filter(curso_id=curso_seleccionado_id, curso__in=cursos)
        estudiantes = estudiantes.select_related('user', 'curso').order_by('user__last_name', 'user__first_name')

    if request.method == 'POST':
        estudiante_id = request.POST.get('estudiante_id')
        if estudiante_id:
            return redirect('notas:vista_detalle_observador', estudiante_id=estudiante_id)

    mis = [c for c in cursos if c.id in mis_cursos_ids] if not es_admin_usuario(user) else []
    otros = [c for c in cursos if c.id not in mis_cursos_ids] if not es_admin_usuario(user) else list(cursos)
    context = {
        'colegio': request.colegio,
        'cursos': cursos,
        'mis_cursos': mis,
        'otros_cursos': otros,
        'estudiantes': estudiantes,
        'curso_seleccionado_id': curso_seleccionado_id,
        'page_title': 'Seleccionar Estudiante para Observador'
    }
    return render(request, 'notas/observador/selector.html', context)

@login_required
@user_passes_test(es_docente_o_superuser)
def vista_detalle_observador(request, estudiante_id):
    if not request.colegio:
        return HttpResponseNotFound("<h1>Colegio no configurado</h1>")
        
    estudiante = get_object_or_404(Estudiante, id=estudiante_id, colegio=request.colegio)
    ficha, created = FichaEstudiante.objects.get_or_create(estudiante=estudiante)
    registros = RegistroObservador.objects.filter(estudiante=estudiante, colegio=request.colegio)
    
    context = {
        'colegio': request.colegio,
        'estudiante': estudiante,
        'ficha': ficha,
        'registros': registros,
        'page_title': f"Observador de {estudiante.user.get_full_name()}"
    }
    return render(request, 'notas/observador/detalle_observador.html', context)

@login_required
@user_passes_test(es_docente_o_superuser)
def crear_registro_observador_vista(request, estudiante_id):
    if not request.colegio:
        return HttpResponseNotFound("<h1>Colegio no configurado</h1>")
        
    estudiante = get_object_or_404(Estudiante, id=estudiante_id, colegio=request.colegio)
    docente = Docente.objects.filter(user=request.user, colegio=request.colegio).first()

    if request.method == 'POST':
        form = RegistroObservadorForm(request.POST, colegio=request.colegio)
        if form.is_valid():
            nuevo_registro = form.save(commit=False)
            nuevo_registro.colegio = request.colegio
            nuevo_registro.estudiante = estudiante
            nuevo_registro.docente_reporta = docente
            
            if nuevo_registro.tipo != 'COMPORTAMENTAL':
                nuevo_registro.subtipo = None
                nuevo_registro.tipo_falta, nuevo_registro.falta = '', None
                
            nuevo_registro.save()
            
            try:
                url_destino = reverse('notas:mi_observador')
            except:
                url_destino = '#'

            Notificacion.objects.create(
                colegio=request.colegio,
                destinatario=estudiante.user,
                mensaje=f"Se ha registrado una nueva anotación {nuevo_registro.get_tipo_display()} en tu observador.",
                tipo='OBSERVADOR',
                url=url_destino
            )

            messages.success(request, f"Observación para {estudiante.user.get_full_name()} guardada correctamente.")
            # Aviso a la familia: el correo sale solo; el WhatsApp se envía
            # desde la pantalla siguiente con un toque.
            enviado, detalle = avisos_familia.enviar_correo(
                nuevo_registro, request.build_absolute_uri('/'), _url_respuesta(request, nuevo_registro))
            if enviado:
                messages.info(request, f"Se envió un aviso al correo del acudiente ({detalle}).")
            enviado_wa, detalle_wa = avisos_familia.enviar_whatsapp(nuevo_registro, request.build_absolute_uri('/'))
            if enviado_wa:
                messages.info(request, f"Se envió el aviso por WhatsApp ({detalle_wa}).")
            return redirect('notas:aviso_familia', registro_id=nuevo_registro.id)
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"Error en '{field.capitalize()}': {error}")
    else:
        form = RegistroObservadorForm(colegio=request.colegio)

    context = {
        'colegio': request.colegio,
        'form': form,
        'estudiante': estudiante,
        'catalogo_faltas': observador_catalogo.catalogo_para_buscar(request.colegio),
        'page_title': f"Nueva Observación para {estudiante.user.get_full_name()}"
    }
    return render(request, 'notas/observador/crear_registro.html', context)


@login_required
@user_passes_test(es_docente_o_superuser)
def editar_registro_observador_vista(request, registro_id):
    if not request.colegio:
        return HttpResponseNotFound("<h1>Colegio no configurado</h1>")
        
    registro = get_object_or_404(RegistroObservador, id=registro_id, colegio=request.colegio)
    estudiante = registro.estudiante
    
    # Validar que sea el creador de la nota o un administrador
    es_autor = registro.docente_reporta and registro.docente_reporta.user == request.user
    if not (es_autor or es_admin(request)):
        messages.error(request, "No tienes permiso para editar esta observación. Solo el autor puede hacerlo.")
        return redirect('notas:vista_detalle_observador', estudiante_id=estudiante.id)

    if request.method == 'POST':
        form = RegistroObservadorForm(request.POST, instance=registro, colegio=request.colegio)
        if form.is_valid():
            registro_actualizado = form.save(commit=False)
            if registro_actualizado.tipo != 'COMPORTAMENTAL':
                registro_actualizado.subtipo = None
                registro_actualizado.tipo_falta, registro_actualizado.falta = '', None
            registro_actualizado.save()
            
            messages.success(request, "Observación actualizada correctamente.")
            return redirect('notas:vista_detalle_observador', estudiante_id=estudiante.id)
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"Error en '{field.capitalize()}': {error}")
    else:
        form = RegistroObservadorForm(instance=registro, colegio=request.colegio)

    context = {
        'colegio': request.colegio,
        'form': form,
        'estudiante': estudiante,
        'registro': registro,
        'catalogo_faltas': observador_catalogo.catalogo_para_buscar(request.colegio),
        'page_title': f"Editar Observación de {estudiante.user.get_full_name()}"
    }
    return render(request, 'notas/observador/editar_registro.html', context)

@login_required
@user_passes_test(es_docente_o_superuser)
def eliminar_registro_observador_vista(request, registro_id):
    if not request.colegio:
        return HttpResponseNotFound("<h1>Colegio no configurado</h1>")
        
    registro = get_object_or_404(RegistroObservador, id=registro_id, colegio=request.colegio)
    estudiante = registro.estudiante
    
    es_autor = registro.docente_reporta and registro.docente_reporta.user == request.user
    if not (es_autor or es_admin(request)):
        messages.error(request, "No tienes permiso para eliminar esta observación.")
        return redirect('notas:vista_detalle_observador', estudiante_id=estudiante.id)

    if request.method == 'POST':
        registro.delete()
        messages.success(request, "La observación ha sido eliminada del historial.")
        
    return redirect('notas:vista_detalle_observador', estudiante_id=estudiante.id)


@login_required
@user_passes_test(es_docente_o_superuser)
def editar_ficha_vista(request, estudiante_id):
    if not request.colegio:
        return HttpResponseNotFound("<h1>Colegio no configurado</h1>")
        
    estudiante = get_object_or_404(Estudiante, id=estudiante_id, colegio=request.colegio)
    ficha, created = FichaEstudiante.objects.get_or_create(estudiante=estudiante)

    if request.method == 'POST':
        form = FichaEstudianteForm(request.POST, request.FILES, instance=ficha)
        if form.is_valid():
            form.save()
            messages.success(request, f"Ficha de {estudiante.user.get_full_name()} actualizada correctamente.")
            return redirect('notas:vista_detalle_observador', estudiante_id=estudiante.id)
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"Error en '{field.capitalize()}': {error}")
    else:
        form = FichaEstudianteForm(instance=ficha)
    
    context = {
        'colegio': request.colegio,
        'form': form,
        'estudiante': estudiante,
        'page_title': f"Editando Ficha de {estudiante.user.get_full_name()}"
    }
    return render(request, 'notas/observador/editar_ficha.html', context)

@login_required
@user_passes_test(es_docente_o_superuser)
def generar_observador_pdf_vista(request, estudiante_id):
    if not request.colegio:
        return HttpResponseNotFound("<h1>Colegio no configurado</h1>")
    if not PDF_SUPPORT:
        return HttpResponse("Error: El servidor no tiene instalada la librería WeasyPrint para generar PDFs.", status=500)
            
    estudiante = get_object_or_404(Estudiante, id=estudiante_id, colegio=request.colegio)
    ficha, _ = FichaEstudiante.objects.get_or_create(estudiante=estudiante)
    registros = RegistroObservador.objects.filter(estudiante=estudiante, colegio=request.colegio)

    # Creamos la URL absoluta para que WeasyPrint pueda ver y exportar la foto en el PDF
    foto_url = request.build_absolute_uri(ficha.foto.url) if ficha.foto and ficha.foto.name else None

    context = {
        'colegio': request.colegio,
        'estudiante': estudiante,
        'ficha': ficha,
        'foto_url': foto_url,
        'registros': registros,
    }
    
    html_string = render_to_string('notas/observador/observador_pdf.html', context)
    base_url = request.build_absolute_uri()
    
    try:
        pdf_file = HTML(string=html_string, base_url=base_url).write_pdf()
        response = HttpResponse(pdf_file, content_type='application/pdf')
        response['Content-Disposition'] = f'inline; filename="observador_{estudiante.user.username}.pdf"'
        return response
    except Exception as e:
        return HttpResponse(f"Error técnico al generar el PDF: {str(e)}", status=500)

@login_required
@user_passes_test(es_docente_o_superuser)
def aviso_familia_vista(request, registro_id):
    """Avisar a la familia de una anotación: botones de WhatsApp y correo."""
    if not request.colegio:
        return HttpResponseNotFound("<h1>Colegio no configurado</h1>")
    registro = get_object_or_404(RegistroObservador.objects.select_related('estudiante__user', 'colegio'),
                                 id=registro_id, colegio=request.colegio)
    url_portal = request.build_absolute_uri('/')
    if request.method == 'POST' and request.POST.get('accion') == 'correo':
        enviado, detalle = avisos_familia.enviar_correo(registro, url_portal,
                                                        _url_respuesta(request, registro))
        if enviado:
            messages.success(request, f"Aviso enviado al correo {detalle}.")
        else:
            messages.warning(request, f"No se envió el correo: {detalle}.")
        return redirect('notas:aviso_familia', registro_id=registro.id)

    texto = avisos_familia.texto_aviso(registro, url_portal)
    contactos = avisos_familia.contactos(registro.estudiante)
    for c in contactos:
        c['enlace'] = avisos_familia.enlace_whatsapp(c['numero'], texto)
    ficha = getattr(registro.estudiante, 'ficha', None)
    return render(request, 'notas/observador/aviso_familia.html', {
        'colegio': request.colegio, 'registro': registro, 'estudiante': registro.estudiante,
        'texto': texto, 'contactos': contactos,
        'correo_acudiente': getattr(ficha, 'email_acudiente', '') if ficha else '',
        'correo_configurado': avisos_familia.correo_configurado(),
        'page_title': 'Avisar a la familia',
    })


def _url_respuesta(request, registro):
    from ..enlaces import enlace_absoluto
    return enlace_absoluto(
        request, reverse('notas:respuesta_acudiente', args=[avisos_familia.token_respuesta(registro)]))


def respuesta_acudiente_vista(request, token):
    """Página del enlace del correo: el acudiente ve la anotación, se da por
    enterado y escribe su descargo. Sin usuario: el enlace firmado es la llave.
    """
    from django.db import transaction
    from django.utils import timezone

    registro, problema = avisos_familia.registro_de_token(token)
    if registro is not None and getattr(request, 'colegio', None) and registro.colegio_id != request.colegio.id:
        registro, problema = None, 'invalido'      # el enlace es de otro colegio
    contexto = {'registro': registro, 'problema': problema,
                'colegio': registro.colegio if registro else getattr(request, 'colegio', None)}
    if registro is None:
        return render(request, 'notas/observador/respuesta_acudiente.html', contexto, status=404)

    if request.method == 'POST' and not registro.acudiente_enterado:
        firma = ' '.join((request.POST.get('firma') or '').split())[:160]
        descargo = (request.POST.get('descargo') or '').strip()[:2000]
        if len(firma) < 5:
            contexto.update(error='Escriba su nombre completo.', firma=firma, descargo=descargo)
            return render(request, 'notas/observador/respuesta_acudiente.html', contexto)
        with transaction.atomic():
            registro.acudiente_enterado = timezone.now()
            registro.firma_acudiente = firma
            registro.descargo_acudiente = descargo
            registro.save(update_fields=['acudiente_enterado', 'firma_acudiente', 'descargo_acudiente'])
            # Le avisa a quien registró la anotación.
            if registro.docente_reporta_id:
                Notificacion.objects.create(
                    colegio=registro.colegio, destinatario=registro.docente_reporta.user, tipo='OBSERVADOR',
                    mensaje=(f"El acudiente de {registro.estudiante.user.get_full_name()} "
                             f"{'respondió' if descargo else 'se dio por enterado de'} la anotación "
                             f"del {registro.fecha_suceso:%d/%m/%Y}.")[:255],
                    url=reverse('notas:vista_detalle_observador', args=[registro.estudiante_id]))
        return redirect('notas:respuesta_acudiente', token=token)
    return render(request, 'notas/observador/respuesta_acudiente.html', contexto)


# ----------------------------------------------------------------------------- catálogo de faltas

def _xlsx(datos, nombre):
    r = HttpResponse(datos, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    r['Content-Disposition'] = f'attachment; filename="{nombre}.xlsx"'
    return r


@login_required
@user_passes_test(es_admin_usuario)
def catalogo_faltas_vista(request):
    """El colegio arma su lista de faltas Tipo I, II y III (a mano, desde Excel o con ejemplos)."""
    from ..models import FaltaCatalogo, TIPOS_FALTA
    colegio = request.colegio
    if not colegio:
        return HttpResponseNotFound("<h1>Colegio no configurado</h1>")
    if request.GET.get('descargar'):
        return _xlsx(observador_catalogo.plantilla_catalogo(colegio), 'Catálogo de faltas')

    if request.method == 'POST':
        accion = request.POST.get('accion')
        if accion == 'ejemplos':
            n = observador_catalogo.cargar_ejemplos(colegio)
            messages.success(request, f'Se agregaron {n} ejemplos. Ajústelos a su manual de convivencia.' if n
                             else 'Los ejemplos ya estaban en su catálogo.')
        elif accion == 'importar':
            archivo = request.FILES.get('archivo')
            if not archivo:
                messages.error(request, 'Escoja el archivo de Excel.')
            else:
                n, errores = observador_catalogo.importar_catalogo(colegio, archivo)
                if n:
                    messages.success(request, f'Se agregaron {n} faltas al catálogo.')
                for e in errores[:15]:
                    messages.warning(request, e)
                if not n and not errores:
                    messages.info(request, 'No había faltas nuevas en el archivo.')
        elif accion in ('crear', 'editar'):
            tipo = observador_catalogo.tipo_de(request.POST.get('tipo_falta'))
            desc = (request.POST.get('descripcion') or '').strip()
            numeral = (request.POST.get('numeral') or '').strip()[:40]
            if not tipo or not desc:
                messages.error(request, 'Escoja el tipo y escriba la descripción.')
            elif accion == 'crear':
                FaltaCatalogo.objects.create(colegio=colegio, tipo_falta=tipo, numeral=numeral, descripcion=desc)
                messages.success(request, 'Falta agregada al catálogo.')
            else:
                FaltaCatalogo.objects.filter(colegio=colegio, id=request.POST.get('id')).update(
                    tipo_falta=tipo, numeral=numeral, descripcion=desc)
                messages.success(request, 'Falta actualizada.')
        elif accion == 'alternar':
            f = get_object_or_404(FaltaCatalogo, colegio=colegio, id=request.POST.get('id'))
            f.activa = not f.activa
            f.save(update_fields=['activa'])
        elif accion == 'eliminar':
            f = get_object_or_404(FaltaCatalogo, colegio=colegio, id=request.POST.get('id'))
            usada = f.registros.exists()
            f.delete()
            messages.success(request, 'Falta eliminada.' + (' Las observaciones que la usaban conservan su texto y su tipo.' if usada else ''))
        return redirect(request.get_full_path())

    faltas = FaltaCatalogo.objects.filter(colegio=colegio)
    tipo = request.GET.get('tipo', '')
    q = (request.GET.get('q') or '').strip()
    if tipo:
        faltas = faltas.filter(tipo_falta=tipo)
    if q:
        from django.db.models import Q
        for p in q.split():
            faltas = faltas.filter(Q(descripcion__icontains=p) | Q(numeral__icontains=p))
    from django.db.models import Count
    conteo = dict(FaltaCatalogo.objects.filter(colegio=colegio).values_list('tipo_falta')
                  .annotate(n=Count('id')).values_list('tipo_falta', 'n'))
    return render(request, 'notas/observador/catalogo_faltas.html', {
        'colegio': colegio, 'faltas': faltas.annotate(usos=Count('registros')), 'tipos': TIPOS_FALTA,
        'tipo': tipo, 'q': q, 'conteo': conteo, 'page_title': 'Catálogo de faltas'})


# ----------------------------------------------------------------------------- observaciones desde Excel

def _cursos_permitidos(request):
    if es_admin_usuario(request.user):
        return Curso.objects.filter(colegio=request.colegio).order_by('nombre'), None
    docente = Docente.objects.filter(user=request.user, colegio=request.colegio).first()
    if docente is None:
        return Curso.objects.none(), None
    return _cursos_de_la_sede_del_docente(docente, request.colegio), docente


@login_required
@user_passes_test(es_docente_o_superuser)
def observador_excel_vista(request):
    """Sin internet: el docente baja el Excel del curso, lo llena y lo sube después."""
    if not request.colegio:
        return HttpResponseNotFound("<h1>Colegio no configurado</h1>")
    cursos, docente = _cursos_permitidos(request)
    curso_id = request.POST.get('curso_id') or request.GET.get('curso_id')
    curso = cursos.filter(id=curso_id).first() if curso_id and str(curso_id).isdigit() else None

    def estudiantes_de(c):
        return (Estudiante.objects.filter(colegio=request.colegio, is_active=True, curso=c)
                .select_related('user', 'ficha').order_by('user__last_name', 'user__first_name'))

    if request.GET.get('descargar') and curso:
        return _xlsx(observador_catalogo.plantilla_observaciones(request.colegio, estudiantes_de(curso)),
                     f'Observador {curso.nombre}')

    resultado = None
    if request.method == 'POST':
        archivo = request.FILES.get('archivo')
        if not curso or not archivo:
            messages.error(request, 'Escoja el curso y el archivo de Excel.')
        else:
            registros, errores = observador_catalogo.importar_observaciones(
                request.colegio, docente, archivo, estudiantes_de(curso))
            resultado = {'registros': registros, 'errores': errores}
            if registros:
                avisar = request.POST.get('avisar') == 'on'
                correos = 0
                url_destino = reverse('notas:mi_observador')
                for r in registros:
                    Notificacion.objects.create(
                        colegio=request.colegio, destinatario=r.estudiante.user, tipo='OBSERVADOR', url=url_destino,
                        mensaje=f"Se ha registrado una nueva anotación {r.get_tipo_display()} en tu observador.")
                    if avisar:
                        enviado, _ = avisos_familia.enviar_correo(
                            r, request.build_absolute_uri('/'), _url_respuesta(request, r))
                        correos += int(enviado)
                messages.success(request, f'Se guardaron {len(registros)} observaciones de {curso.nombre}.'
                                 + (f' Se avisó por correo a {correos} familias.' if avisar else ''))
            elif not errores:
                messages.info(request, 'El archivo no tenía observaciones (todas las filas sin descripción).')
            else:
                messages.error(request, 'No se guardó nada: corrija estas filas y vuelva a subir el archivo.')

    return render(request, 'notas/observador/observador_excel.html', {
        'colegio': request.colegio, 'cursos': cursos, 'curso': curso, 'resultado': resultado,
        'page_title': 'Observador sin internet (Excel)'})
