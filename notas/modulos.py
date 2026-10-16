"""Módulos que se encienden o apagan por colegio.

El núcleo (notas, planillas, asistencia, boletines, sábana y observador) está
siempre. Lo demás lo activa el dueño de la plataforma según lo que contrató
cada colegio, desde /plataforma/modulos/. Al apagar un módulo desaparece de
menús y paneles, sus direcciones muestran «Este servicio no está activo en su
colegio» y sus datos se conservan: al encenderlo, todo sigue como estaba.
"""
from collections import OrderedDict

# código: (nombre, descripción, prefijos de dirección que bloquea)
MODULOS = OrderedDict([
    ('portal', ('Portal del colegio', 'Página pública con noticias, galería, videos, documentos y sedes.',
                ('/admin/portal/configuracion/', '/admin/portal/documentos/', '/admin/portal/galeria/',
                 '/admin/portal/recursos/', '/admin/portal/videos/', '/admin/portal/noticias/',
                 '/admin/portal/carrusel/', '/admin/portal/diseno/'))),
    ('puntoexacto', ('PuntoExacto', 'Exámenes de selección múltiple calificados con la cámara del celular.',
                     ('/puntoexacto/',))),
    ('certificados', ('Certificados y libro final', 'Certificados con QR, notas de años anteriores y libro final.',
                      ('/certificados/',))),
    ('circulares', ('Circulares', 'Circulares a familias y docentes con confirmación de lectura.',
                    ('/circulares/',))),
    ('actas', ('Actas', 'Actas de comisión de evaluación y actas libres.', ('/actas/',))),
    ('prematricula', ('Prematrícula', 'Inscripciones en línea desde el portal.', ('/prematricula/',))),
    ('estadisticas', ('Estadísticas y alertas tempranas', 'Estadísticas con conclusiones y alertas de pérdida.',
                      ('/estadisticas/', '/alertas-tempranas/', '/ajax/datos-graficos/'))),
    ('reporte_parcial', ('Reporte parcial con avisos', 'Reporte parcial, aviso a la familia e informe en PDF.',
                         ('/docente/reporte-parcial/', '/reporte-parcial/', '/familia/informe-parcial/'))),
    ('correo', ('Correo interno', 'Mensajería entre docentes, estudiantes y administración.', ('/mensajeria/',))),
    ('cartera', ('Cartera y pensiones', 'Cobros, pagos con recibo, morosos, estado de cuenta y paz y salvo.',
                 ('/cartera/',))),
    ('elecciones', ('Elecciones escolares', 'Votaciones de personero, contralor y consejo estudiantil.',
                    ('/elecciones2026/',))),
    # Salón Digital es un producto aparte con cuentas propias: aquí solo se
    # muestra u oculta el acceso desde el menú del colegio.
    ('salon', ('Salón Digital', 'Acceso a Salón Digital desde el menú de los docentes.', ())),
])

TODOS = list(MODULOS)

PLANES = OrderedDict([
    ('basico', ('Básico', ['circulares', 'certificados'])),
    # Colegios oficiales (matrícula cero): todo menos el módulo de cobros.
    ('publico', ('Público', [m for m in TODOS if m != 'cartera'])),
    ('completo', ('Completo', TODOS)),
])

# Direcciones que siguen funcionando aunque el módulo esté apagado: la
# verificación pública de un certificado ya entregado no puede dejar de servir.
SIEMPRE_ABIERTAS = ('/certificados/verificar/',)


def activos(colegio):
    """Conjunto de códigos de módulos activos. Sin colegio (o sin dato), todos."""
    if colegio is None:
        return set(TODOS)
    valor = getattr(colegio, 'modulos_activos', None)
    if valor is None:
        return set(TODOS)
    return {m for m in valor if m in MODULOS}


def esta_activo(colegio, codigo):
    return codigo in activos(colegio)


def modulo_de_ruta(ruta):
    """El módulo al que pertenece una dirección, o None si es del núcleo."""
    if ruta.startswith(SIEMPRE_ABIERTAS):
        return None
    for codigo, (_, _, prefijos) in MODULOS.items():
        if prefijos and ruta.startswith(prefijos):
            return codigo
    return None
