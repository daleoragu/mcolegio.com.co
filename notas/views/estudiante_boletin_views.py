# notas/views/estudiante_boletin_views.py
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib import messages
# Se añade HttpResponseNotFound para manejar el caso de un colegio no identificado
from django.http import HttpResponseNotFound

from ..models import (Estudiante, PublicacionBoletin, PeriodoAcademico, PublicacionBoletinFinal,
                      HistorialMatricula)

@login_required
def mis_boletines_vista(request):
    """
    Muestra al estudiante una lista de los boletines que han sido publicados
    por el colegio actual.
    """
    # CORRECCIÓN: Verificar que se ha identificado un colegio.
    if not request.colegio:
        return HttpResponseNotFound("<h1>Colegio no configurado</h1>")

    try:
        # CORRECCIÓN: Asegurar que se obtiene el estudiante del colegio actual.
        estudiante = Estudiante.objects.get(user=request.user, colegio=request.colegio)
    except Estudiante.DoesNotExist:
        messages.error(request, "Tu usuario no está asociado a un perfil de estudiante en este colegio.")
        return render(request, 'notas/estudiante/mis_boletines.html', {'boletines_disponibles': [], 'colegio': request.colegio})

    # --- CAMBIO ARQUITECTÓNICO IMPORTANTE ---
    # Para que esto funcione, tus modelos de publicación deben estar ligados a un colegio.
    # ACCIÓN REQUERIDA:
    # 1. En `PublicacionBoletin`, añade:
    #    colegio = models.ForeignKey(Colegio, on_delete=models.CASCADE)
    # 2. En `PublicacionBoletinFinal`, añade:
    #    colegio = models.ForeignKey(Colegio, on_delete=models.CASCADE)
    # 3. Haz makemigrations y migrate.

    # CORRECCIÓN: Filtrar publicaciones por el colegio actual.
    periodos_publicados_ids = PublicacionBoletin.objects.filter(
        esta_visible=True,
        colegio=request.colegio
    ).values_list('periodo_id', flat=True)
    
    # La consulta a PeriodoAcademico ya está implícitamente segura porque los IDs vienen de una consulta filtrada.
    periodos_publicados = PeriodoAcademico.objects.filter(id__in=periodos_publicados_ids).order_by('ano_lectivo', 'fecha_inicio')
    
    # En qué curso estuvo cada año. Después de una promoción, los boletines de
    # años pasados se abren con el curso de ese año y no con el de hoy.
    curso_por_ano = dict(HistorialMatricula.objects.filter(estudiante=estudiante)
                         .exclude(curso__isnull=True).values_list('ano_lectivo', 'curso_id'))
    curso_hoy = estudiante.curso_id

    boletines_disponibles = []
    for periodo in periodos_publicados:
        boletines_disponibles.append({
            'id': periodo.id,
            'texto': f"Boletín del {periodo.get_nombre_display()} - {periodo.ano_lectivo}",
            'curso_id': curso_por_ano.get(periodo.ano_lectivo, curso_hoy),
        })
        
    # CORRECCIÓN: Filtrar informes finales por el colegio actual.
    anos_finales_publicados = PublicacionBoletinFinal.objects.filter(
        esta_visible=True,
        colegio=request.colegio
    ).values_list('ano_lectivo', flat=True)

    for ano in anos_finales_publicados:
         boletines_disponibles.append({
            'id': f"FINAL_{ano}",
            'texto': f"Informe Final del Año {ano}",
            'curso_id': curso_por_ano.get(ano, curso_hoy),
        })

    context = {
        'boletines_disponibles': boletines_disponibles,
        # Hay boletines que mostrar si tiene curso hoy o estuvo en alguno antes.
        'curso_id': curso_hoy or (next(iter(curso_por_ano.values()), None)),
        'colegio': request.colegio,
    }
    
    return render(request, 'notas/estudiante/mis_boletines.html', context)
