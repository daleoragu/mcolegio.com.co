"""Los espacios de Mi Salón Virtual: Inicio, Sala de Profesores, Mi Espacio, Mis Estudiantes y Planeación.

Cada página de la plataforma pertenece a uno de ellos; el menú de arriba (y la barra de abajo en el celular)
marca el espacio y, debajo, salen sus secciones como pestañas."""
from django.urls import reverse

ESPACIOS = [
    # id, nombre, icono, url
    ('inicio', 'Inicio', 'fa-house', 'salon_digital:inicio'),
    ('sala', 'Sala de Profesores', 'fa-comments', 'chat:muro'),
    ('espacio', 'Mi Espacio', 'fa-folder-open', 'salon_digital:mi_espacio'),
    ('estudiantes', 'Mis Estudiantes', 'fa-users', 'aula:inicio'),
    ('planeacion', 'Planeación', 'fa-wand-magic-sparkles', 'materiales:lista'),
]

SECCIONES = {
    'sala': [('Muro', 'fa-newspaper', '/chat/colegas/muro/', 'muro'),
             ('Mis colegas', 'fa-user-group', '/chat/colegas/?tab=colegas', 'colegas'),
             ('Eventos y olimpiadas', 'fa-trophy', 'aula:eventos', 'eventos'),
             ('Mensajes', 'fa-comment-dots', '/chat/colegas/', 'mensajes')],
    'espacio': [('Mi perfil', 'fa-id-badge', 'salon_digital:mi_espacio', 'perfil'),
                ('Mis páginas interactivas HTML', 'fa-code', 'salon_digital:panel', 'paginas'),
                ('Mis publicaciones', 'fa-pen', '/chat/colegas/muro/?ver=mias', 'mias'),
                ('Guardados', 'fa-bookmark', '/chat/colegas/muro/?ver=guardados', 'guardados'),
                ('Mi cuenta y plan', 'fa-gear', 'salon_digital:mi_cuenta', 'cuenta')],
    'estudiantes': [('Mis clases', 'fa-chalkboard-user', 'aula:inicio', 'clases'),
                    ('Grupos, PIN y tarjetas QR', 'fa-id-card', 'salon_digital:grupos', 'grupos'),
                    ('Escanear exámenes y notas (PuntoExacto)', 'fa-camera', 'puntoexacto:lista', 'examenes')],
    'planeacion': [('Mis materiales', 'fa-file-lines', 'materiales:lista', 'materiales'),
                   ('Mis juegos', 'fa-gamepad', 'materiales:juegos', 'juegos'),
                   ('Rúbricas', 'fa-list-check', 'aula:instrumentos', 'rubricas'),
                   ('Banco de preguntas', 'fa-box-archive', 'aula:banco', 'banco'),
                   ('Exámenes PuntoExacto', 'fa-barcode', 'puntoexacto:lista', 'examenes'),
                   ('Mi escala', 'fa-scale-balanced', 'aula:escala', 'escala'),
                   ('Compartido conmigo', 'fa-inbox', 'aula:compartidos', 'compartidos')],
}

_PLANEACION_AULA = {'instrumentos': 'rubricas', 'instrumento': 'rubricas', 'instrumento_accion': 'rubricas',
                    'escala': 'escala', 'banco': 'banco', 'banco_json': 'banco', 'banco_planilla': 'banco',
                    'compartidos': 'compartidos'}


def ubicar(request):
    """(espacio, sección) de la página que se está viendo."""
    m = getattr(request, 'resolver_match', None)
    if m is None:
        return '', ''
    app, nombre = m.app_name, m.url_name
    if app == 'salon_digital':
        if nombre == 'inicio':
            return 'inicio', ''
        if nombre in ('grupos', 'nuevo_grupo', 'ver_grupo', 'editar_grupo', 'tarjetas_grupo', 'editar_integrante'):
            return 'estudiantes', 'grupos'
        if nombre in ('mi_cuenta', 'planes', 'pago'):
            return 'espacio', 'cuenta'
        if nombre == 'mi_espacio':
            return 'espacio', 'perfil'
        if nombre.startswith('panel') or nombre in ('nueva_pagina', 'subir_varias', 'editar_pagina', 'eliminar_pagina',
                                                     'qr_hoja', 'moderar_comentarios'):
            return 'espacio', 'paginas'
        return '', ''
    if app == 'chat':
        ver = request.GET.get('ver')
        if nombre == 'muro' and ver in ('mias', 'guardados'):
            return 'espacio', ver
        if nombre and nombre.startswith('muro'):
            return 'sala', 'muro'
        if nombre == 'colegas' and request.GET.get('tab') in ('colegas', 'solicitudes', 'buscar'):
            return 'sala', 'colegas'
        return 'sala', 'mensajes'
    if app in ('materiales',):
        if nombre and (nombre.startswith('juego') or nombre == 'logica_probar'):
            return 'planeacion', 'juegos'
        return 'planeacion', 'materiales'
    if app == 'puntoexacto':
        return 'planeacion', 'examenes'
    if app == 'aula':
        if nombre and nombre.startswith('evento'):
            return 'sala', 'eventos'
        if nombre in _PLANEACION_AULA:
            return 'planeacion', _PLANEACION_AULA[nombre]
        return 'estudiantes', 'clases'
    return '', ''


def _url(destino):
    return destino if destino.startswith('/') else reverse(destino)


def espacios(request):
    """Procesador de contexto: solo para los docentes de Mi Salón Virtual (sin colegio)."""
    user = getattr(request, 'user', None)
    if not (user and user.is_authenticated and getattr(request, 'colegio', None) is None):
        return {}
    try:
        if user.cuenta_salon is None:
            return {}
    except Exception:
        return {}
    actual, seccion = ubicar(request)
    secciones = [{'nombre': n, 'icono': ic, 'url': _url(u), 'on': k == seccion} for n, ic, u, k in SECCIONES.get(actual, [])]
    extra = {}
    if actual == 'estudiantes':
        # Cambio rápido de grupo: cada grupo activo como una pestaña más (la del aula abierta, marcada)
        m = request.resolver_match
        aula_pk = m.kwargs.get('pk') if m and m.app_name == 'aula' else None
        grupo_abierto = None
        if aula_pk:
            from aula.models import Aula
            grupo_abierto = Aula.objects.filter(pk=aula_pk).values_list('grupo_id', flat=True).first()
        grupos = [{'nombre': g.nombre, 'codigo': g.codigo, 'icono': 'fa-circle-dot' if g.pk == grupo_abierto else 'fa-circle',
                   'url': reverse('aula:por_grupo', args=[g.pk]), 'on': g.pk == grupo_abierto, 'solo_movil': bool(grupo_abierto)}
                  for g in user.cuenta_salon.grupos.filter(activo=True).order_by('nombre')[:12]]
        if grupo_abierto:
            secciones[0]['on'] = False
            extra['grupos_menu'] = [dict(g) for g in grupos]     # dentro de un aula: la barra lateral oscura con los grupos (computador)
        for g in grupos:
            g['nombre'] = f"{g['nombre']} · {g['codigo']}"
        secciones = secciones[:1] + grupos + secciones[1:] + [{'nombre': 'Nuevo grupo', 'icono': 'fa-plus', 'url': reverse('salon_digital:nuevo_grupo'), 'on': False}]
    return {
        'espacio_actual': actual,
        'espacios_menu': [{'id': i, 'nombre': n, 'icono': ic, 'url': _url(u), 'on': i == actual} for i, n, ic, u in ESPACIOS],
        'secciones_menu': secciones,
        **extra,
    }
