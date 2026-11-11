"""Qué deja hacer el plan de Mi Salón Virtual (Gratis, Estándar o Premium) en cada función.

Solo aplica a los docentes del plan individual (cuando no se está dentro de un colegio). En los colegios
manda lo que el colegio contrató. Lo que un docente ya tiene nunca se borra: solo no puede crear más.
"""
from django.contrib import messages
from django.shortcuts import redirect

TEXTOS = {
    'eventos': 'Los eventos y olimpiadas son del plan Premium.',
    'examenes': 'Los exámenes con hoja de respuestas están en los planes Estándar y Premium.',
    'grupos': 'Su plan Gratis permite 1 grupo. Con Estándar o Premium tiene grupos ilimitados.',
    'materiales': 'Su plan Gratis guarda hasta 10 materiales. Con Estándar o Premium son ilimitados.',
    'paginas': 'Llegó al límite de actividades publicadas de su plan.',
    'tableros': 'Llegó al límite de tableros guardados de su plan (Gratis: 5, Estándar: 50; Premium: ilimitados). Puede borrar los que ya no use.',
}


def cuenta_de(user):
    try:
        return user.cuenta_salon if user.is_authenticated else None
    except Exception:
        return None


def permite(user, cosa, colegio=None):
    """True si puede usar la función. Fuera del plan individual (colegios, superusuario) siempre True."""
    if colegio is not None or getattr(user, 'is_superuser', False):
        return True
    c = cuenta_de(user)
    return True if c is None else c.permite(cosa)


def cupo_materiales(user, colegio=None):
    if colegio is not None or getattr(user, 'is_superuser', False):
        return True
    c = cuenta_de(user)
    if c is None:
        return True
    tope = c.limite('materiales')
    if not tope:
        return True
    from materiales.models import Documento
    return Documento.objects.filter(propietario=user, colegio__isnull=True).count() < tope


def cupo_tableros(user):
    """¿Puede guardar otro tablero de clase? (Gratis 5, Estándar 50, Premium sin límite)"""
    if getattr(user, 'is_superuser', False):
        return True
    c = cuenta_de(user)
    tope = c.limite('tableros') if c is not None else 0
    if not tope:
        return True
    from aula.models import TableroClase
    return TableroClase.objects.filter(autor=user).count() < tope


def cupo_grupos(cuenta):
    tope = cuenta.limite('grupos')
    return not tope or cuenta.grupos.count() < tope


def a_planes(request, motivo, plan='premium'):
    """Avisa que la función es de otro plan y lleva a «Planes y pagos» con ese plan escogido."""
    messages.info(request, TEXTOS.get(motivo, 'Esta función es de un plan superior.') + ' Lo que ya tiene no se pierde.')
    return redirect(f'/salon_digital/pagos/?plan={plan}&para={motivo}')


def marca_pdf(doc):
    """Los PDF del plan Gratis llevan el pie «Hecho con mcolegio»."""
    if doc.colegio_id is not None:
        return False
    c = cuenta_de(doc.propietario)
    return bool(c and c.limite('marca'))
