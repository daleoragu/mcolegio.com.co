"""PuntoExacto también funciona en Mi Salón Virtual (plan individual), donde no hay colegio."""


def base_puntoexacto(request):
    if request.path.startswith('/puntoexacto/') and not getattr(request, 'colegio', None):
        return {'pe_base': 'aula/base_salon.html'}
    return {}
