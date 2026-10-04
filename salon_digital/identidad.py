# salon_digital/identidad.py
"""Quién está presentando la actividad, cuando el docente usa grupos."""

CLAVE_SESION = 'salon_identidad'


def guardar(request, integrante):
    request.session[CLAVE_SESION] = {
        'integrante': integrante.pk,
        'grupo': integrante.grupo_id,
        'nombre': integrante.completo,
        'grupo_nombre': integrante.grupo.nombre,
    }
    request.session.modified = True


def leer(request):
    return request.session.get(CLAVE_SESION) or None


def olvidar(request):
    request.session.pop(CLAVE_SESION, None)
    request.session.modified = True


def integrante_de(request, pagina):
    """El integrante guardado, solo si pertenece a quien publicó la página."""
    from .models import Integrante

    datos = leer(request)
    if not datos:
        return None
    integrante = Integrante.objects.filter(
        pk=datos.get('integrante'), activo=True,
        grupo__propietario=pagina.propietario,
    ).select_related('grupo').first()

    permitidos = pagina.grupos.all()
    if integrante and permitidos.exists() and integrante.grupo_id not in {g.pk for g in permitidos}:
        return None
    return integrante
