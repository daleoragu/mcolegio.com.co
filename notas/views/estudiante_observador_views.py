# notas/views/estudiante_observador_views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.utils import timezone
from django.http import HttpResponseNotFound

from ..models import Estudiante, FichaEstudiante, RegistroObservador
# --- INICIO: CORRECCIÓN DE RUTA DE IMPORTACIÓN ---
# Se cambia la importación para que apunte directamente al archivo 'notificaciones.py'
from ..utils.notificaciones import crear_notificacion
# --- FIN: CORRECCIÓN ---
from ..forms import EstudianteCompromisoForm


def es_estudiante(user):
    """¿Es estudiante? Por el grupo «Estudiantes» o por tener perfil de estudiante.

    Un estudiante creado por otro camino puede no tener el grupo: con el perfil
    basta. (Antes, sin el grupo, la página fallaba con un error 500 porque
    intentaba mandarlo a una dirección «login» que no existe.)
    """
    return user.groups.filter(name='Estudiantes').exists() or Estudiante.objects.filter(user=user).exists()

@login_required
@user_passes_test(es_estudiante, login_url='/')
def mi_observador_vista(request):
    """
    Muestra el observador personal del estudiante logueado, asegurando
    que el estudiante pertenezca al colegio actual.
    """
    if not hasattr(request, 'colegio') or not request.colegio:
        return HttpResponseNotFound("<h1>Colegio no configurado</h1>")

    try:
        estudiante = Estudiante.objects.get(user=request.user, colegio=request.colegio)
    except Estudiante.DoesNotExist:
        messages.error(request, "Acceso denegado. Su usuario no está asociado a un perfil de estudiante en este colegio.")
        return redirect('notas:logout')

    ficha, created = FichaEstudiante.objects.get_or_create(estudiante=estudiante)
    
    # CORRECCIÓN CLAVE: Instanciamos el formulario antes del bloque POST
    # para que esté disponible tanto para GET como para re-renderizado si hay errores en el POST.
    compromiso_form = EstudianteCompromisoForm(instance=ficha)

    if request.method == 'POST':
        # Manejar el guardado de un DESCARGO
        if 'guardar_descargo' in request.POST:
            registro_id = request.POST.get('registro_id')
            descargo_texto = request.POST.get('descargo')
            
            if registro_id and descargo_texto:
                registro = get_object_or_404(RegistroObservador, id=registro_id, estudiante=estudiante)
                registro.descargo_estudiante = descargo_texto
                registro.fecha_descargo = timezone.now()
                registro.save()
                
                if registro.docente_reporta:
                    nombre_estudiante = estudiante.user.get_full_name()
                    kwargs_para_url = {'estudiante_id': estudiante.id}

                    crear_notificacion(
                        colegio=request.colegio,
                        destinatario=registro.docente_reporta.user,
                        mensaje=f"El estudiante {nombre_estudiante} ha añadido un descargo a tu observación.",
                        tipo='OBSERVADOR',
                        url_name='vista_detalle_observador',
                        kwargs=kwargs_para_url
                    )
                messages.success(request, "Tu descargo ha sido guardado correctamente.")
                # Solo redirigimos si hubo éxito
                return redirect('notas:mi_observador')
            else:
                messages.error(request, "No se pudo guardar el descargo. Faltaron datos.")
                # Si falla, no redirigimos. Sigue hacia abajo y muestra los errores conservando el estado.

        # Manejar el guardado del COMPROMISO
        elif 'guardar_compromiso' in request.POST:
            compromiso_form = EstudianteCompromisoForm(request.POST, instance=ficha)
            if compromiso_form.is_valid():
                compromiso_form.save()
                messages.success(request, "Tu compromiso ha sido actualizado correctamente.")
                # Solo redirigimos si hubo éxito
                return redirect('notas:mi_observador')
            else:
                messages.error(request, "Hubo un error al guardar tu compromiso. Por favor, inténtalo de nuevo.")
                # Si falla la validación, NO REDIRIGIMOS. Se renderiza la página con los datos que el usuario 
                # había escrito y se muestran los errores, evitando que el form "se quede en blanco de nuevo".
            
    # Obtenemos los registros para pasarlos al contexto
    registros = RegistroObservador.objects.filter(
        estudiante=estudiante, colegio=request.colegio
    ).order_by('-fecha_suceso')

    context = {
        'estudiante': estudiante,
        'ficha': ficha,
        'registros': registros,
        'compromiso_form': compromiso_form,
        'page_title': 'Mi Observador Estudiantil',
        'colegio': request.colegio
    }
    
    return render(request, 'notas/estudiante/mi_observador.html', context)
