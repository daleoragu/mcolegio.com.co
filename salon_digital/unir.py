"""Un mismo estudiante en las clases de varios docentes: se unen sus integrantes en una CuentaEstudiante con una sola
contraseña. Si su nombre ya está en la otra clase, se une con la contraseña (o el PIN) de esa clase; si no, queda una
solicitud que ese docente aprueba."""
from .models import CuentaEstudiante, Integrante


def asegurar_cuenta(integrante):
    """La cuenta del estudiante (se crea la primera vez que une una segunda clase)."""
    if integrante.cuenta_id:
        return integrante.cuenta
    cuenta = CuentaEstudiante.objects.create(nombre=integrante.completo, clave=integrante.clave)
    integrante.cuenta = cuenta
    integrante.save(update_fields=['cuenta'])
    return cuenta


def unir(actual, otro):
    """Une «otro» (su nombre en la clase de otro docente) a la cuenta del estudiante que está usando la plataforma.
    La contraseña que queda es la del estudiante (la que ya usaba)."""
    cuenta = asegurar_cuenta(actual)
    if otro.cuenta_id and otro.cuenta_id != cuenta.pk:          # ya tenía otras clases unidas: se juntan todas
        Integrante.objects.filter(cuenta_id=otro.cuenta_id).update(cuenta=cuenta)
    otro.cuenta = cuenta
    otro.save(update_fields=['cuenta'])
    Integrante.objects.filter(cuenta=cuenta).update(clave=actual.clave, clave_propia=actual.clave_propia)
    CuentaEstudiante.objects.filter(pk=cuenta.pk).update(clave=actual.clave)
    return cuenta


def solicitar(actual, grupo):
    """Pide entrar a la clase de otro docente: queda inactivo hasta que ese docente lo apruebe."""
    cuenta = asegurar_cuenta(actual)
    pedido = Integrante.objects.filter(grupo=grupo, cuenta=cuenta).first()
    if pedido is None:
        pedido = Integrante.objects.create(grupo=grupo, apellidos=actual.apellidos, nombres=actual.nombres, cuenta=cuenta,
                                           clave=actual.clave, clave_propia=actual.clave_propia, activo=False, solicitud=True)
    return pedido


def clases_de(integrante):
    """Todas las clases del estudiante (las unidas y las solicitudes), la actual primero."""
    if not integrante.cuenta_id:
        return [integrante]
    lista = list(Integrante.objects.filter(cuenta_id=integrante.cuenta_id).select_related('grupo__propietario')
                 .exclude(activo=False, solicitud=False))
    lista.sort(key=lambda i: (i.pk != integrante.pk, i.solicitud, i.grupo.nombre))
    return lista
