"""Asesoría docente: el botón que guía al docente por la página en la que está.

Cada guía se busca por el nombre de la vista (``request.resolver_match.view_name``). Los pasos señalan
elementos de la página:

* ``c``: un texto que el elemento contiene (por ejemplo, el rótulo de un botón). Es lo más estable:
  si el rótulo cambia, el paso simplemente se salta.
* ``s``: un selector CSS, cuando no hay texto que sirva (una tabla, una barra).
* ``en``: un selector que limita dónde buscar el texto (por ejemplo, la barra de pestañas del aula).

Si un elemento no está en la página (porque ese docente no lo tiene), el paso se omite solo.
"""
from django.urls import NoReverseMatch, reverse


def P(titulo, texto, c=None, s=None, en=None):
    paso = {'t': titulo, 'x': texto}
    if c:
        paso['c'] = c
    if s:
        paso['s'] = s
    if en:
        paso['en'] = en
    return paso


# Las pestañas de cualquier aula (sirven en todas las páginas del aula)
PESTANAS_AULA = [
    P('Las pestañas de la clase', 'Todo lo de esta clase está en estas pestañas. Lo que pone aquí sí lo ven sus estudiantes.', s='.au-pestanas'),
    P('Muro', 'Avisos y publicaciones para la clase, como el tablero de anuncios del salón.', c='Muro', en='.au-pestanas'),
    P('Clase en vivo', 'Proyecte preguntas en el tablero y los estudiantes responden desde el celular en tiempo real.', c='Clase en vivo', en='.au-pestanas'),
    P('Material', 'Las guías y talleres que ven los estudiantes. Llegan desde Planeación con el botón de avión (Enviar a mis grupos).', c='Material', en='.au-pestanas'),
    P('Aula invertida', 'Un video de YouTube que se detiene en cada pregunta: los estudiantes lo ven antes de la clase y usted sabe quién lo vio y cómo respondió.', c='Aula invertida', en='.au-pestanas'),
    P('Gamificación', 'Juegos con sus preguntas, juegos de lógica y la mascota académica que los estudiantes cuidan respondiendo.', c='Gamificación', en='.au-pestanas'),
    P('Tareas', 'Asigne trabajos con fecha de entrega; los estudiantes suben archivos y usted califica con comentarios.', c='Tareas', en='.au-pestanas'),
    P('Actividades interactivas', 'Páginas o juegos HTML que publica para que los estudiantes los usen en pantalla completa.', c='Actividades interactivas', en='.au-pestanas'),
    P('Cuestionarios', 'Preguntas en línea que se califican solas.', c='Cuestionarios', en='.au-pestanas'),
    P('Exámenes', 'Exámenes de PuntoExacto: hoja de respuestas que se califica con la cámara del celular.', c='Exámenes', en='.au-pestanas'),
    P('Calificaciones', 'Las notas de la clase. Lo que califica en tareas, cuestionarios y exámenes llega aquí.', c='Calificaciones', en='.au-pestanas'),
    P('Planilla', 'Las notas de su grupo, con los componentes que usted define.', c='Planilla', en='.au-pestanas'),
]

GUIAS = {
    'materiales:lista': {
        'titulo': 'Planeación (Mis materiales)',
        'resumen': 'Su mesa de trabajo: aquí crea, guarda y organiza sus guías, talleres, evaluaciones y formatos. '
                   'Sus estudiantes NO ven esta página; lo que quiera que vean lo envía a sus clases.',
        'pasos': [
            P('Su mesa de trabajo', 'Aquí se crea y se guarda. Nada de esto lo ven los estudiantes hasta que usted lo envíe.', c='Estudio de Planeación'),
            P('Su mesa de trabajo', 'Aquí se crea y se guarda. Nada de esto lo ven los estudiantes hasta que usted lo envíe.', c='Mis materiales', s='h4'),
            P('Crear guía por momentos', 'La guía más usada: Exploro, Aprendo, Practico y Taller, con el encabezado del colegio.', c='Crear guía por momentos'),
            P('Rúbricas y listas de chequeo', 'Instrumentos para evaluar trabajos, exposiciones o proyectos.', c='Rúbrica / Lista de chequeo'),
            P('Examen PuntoExacto', 'Exámenes con hoja de respuestas que se califican con la cámara del celular.', c='Examen PuntoExacto'),
            P('Mis juegos', 'Juegos con sus preguntas para la clase o para jugar en vivo.', c='Mis juegos', s='a'),
            P('Importar material', 'Traiga material ya hecho: de la Biblioteca, de la Sala de Profesores, lo que le compartieron, una página HTML o preguntas desde Excel.', c='Importar material'),
            P('Plantillas', 'Escoja el tipo de documento: guía, taller, evaluación, ficha, cuadernillo… Se abre el editor con la estructura lista.', s='.mm-tipos'),
            P('Formatos para llenar', 'Planeación, plan de aula, PIAR y DUA. Puede cambiarles filas y columnas y llenarlos a mano o con IA.', c='Formatos para llenar'),
            P('Modelos pedagógicos', 'Plantillas para ABP, aprendizaje por retos, estudio de caso, aula invertida y trabajo cooperativo.', c='Modelos pedagógicos'),
            P('Sus documentos', 'Todo lo que ha creado o cargado. Debajo del título ve el área y el grado. Haga clic en el título para editarlo.', s='.mm-tarjeta table'),
            P('Enviar a mis grupos', 'El avión lleva el documento a la pestaña Material de las clases que escoja. Desde ese momento lo ven sus estudiantes.', s='.mm-enviar'),
            P('Las demás acciones', 'Descargar en PDF, duplicar (para hacer una versión nueva), marcar con estrella como formato y eliminar.', s='.mm-tarjeta table td.text-end'),
            P('Taller y aula', 'Recuerde la diferencia: aquí es su taller; en cada clase, la pestaña Material es lo que ven los estudiantes.', c='Mis materiales y Material del aula'),
        ],
    },
    'materiales:editor': {
        'titulo': 'Editor de documentos',
        'resumen': 'Aquí arma la guía por bloques: texto, títulos, tablas, imágenes, ecuaciones, gráficas y preguntas. Se guarda solo.',
        'pasos': [
            P('Deshacer y rehacer', 'Si se equivoca, deshaga con Ctrl+Z y rehaga con Ctrl+Y.', s='[title^="Deshacer"]'),
            P('Formato del texto', 'Negrilla, cursiva, subrayado, exponentes, subíndices, viñetas y numeración.', s='[title="Negrilla"]'),
            P('Ecuaciones', 'Escriba fórmulas matemáticas como en un libro (atajo Alt+=).', s='[title^="Insertar una ecuación"]'),
            P('Gráficas', 'Grafique funciones, puntos, segmentos y polígonos en un plano cartesiano.', s='[title^="Insertar una gráfica"]'),
            P('Bloques', 'Agregue bloques: texto, título, sección, tabla, recuadro, imagen, líneas para escribir, preguntas…', c='Recuadro'),
            P('Preguntas del banco', 'Traiga preguntas ya hechas del Banco de preguntas.', c='Del banco'),
            P('Asistente IA', 'Le ayuda a redactar, generar preguntas o adaptar el texto.', c='Asistente IA'),
            P('Adaptar para PIAR', 'Crea una versión ajustada para un estudiante con PIAR.', c='Adaptar para PIAR'),
            P('Acomodar', 'Escoja normal, compacto o máximo ahorro de papel antes de imprimir.', c='Acomodar'),
            P('Vista previa', 'Mire cómo queda la hoja antes de descargarla.', s='[title="Vista previa"]'),
            P('Con respuestas', 'La versión del docente, con las respuestas marcadas.', s='[title^="Versión del docente"]'),
            P('Enviar a mis grupos', 'Lleva el documento a la pestaña Material de sus clases.', c='Enviar a mis grupos'),
            P('Asignar como tarea', 'Lo convierte en una tarea con fecha de entrega.', c='Asignar como tarea'),
            P('Compartir', 'Invite a otros docentes a construirlo con usted o compártalo con un colega.', c='Compartir'),
        ],
    },
    'materiales:biblioteca': {
        'titulo': 'Biblioteca',
        'resumen': 'Material ya hecho para usar: el banco libre de mcolegio, lo que publican otros docentes y lo de su colegio. '
                   'Cuando algo le sirve, lo «usa» y se copia a sus materiales para editarlo.',
        'pasos': [
            P('Biblioteca', 'Aquí busca material hecho por otros. Lo que usa se copia a Planeación para que lo adapte.', c='Biblioteca', s='h4'),
            P('Todo', 'Muestra todo lo disponible.', c='Todo'),
            P('Banco libre', 'Las guías de mcolegio por DBA, área y grado, libres para todos.', c='Banco libre'),
            P('Comunidad', 'Lo que publican docentes de otros colegios.', c='Comunidad'),
            P('Mi colegio', 'Lo que comparten los docentes de su institución.', c='Mi colegio'),
            P('Lo que compartí', 'Lo que usted ha publicado, con sus valoraciones.', c='Lo que compartí'),
            P('Buscar', 'Escriba un tema, un área o un grado.', c='Buscar', s='button'),
        ],
    },
    'materiales:banco_pagina': {
        'titulo': 'Banco de preguntas',
        'resumen': 'Sus preguntas guardadas por tema, para reutilizarlas en guías, evaluaciones, juegos y exámenes. También se cargan desde Excel.',
        'pasos': [
            P('Banco de preguntas', 'Guarde aquí sus preguntas una vez y úselas muchas veces.', c='Banco de preguntas', s='h4'),
            P('Buscar', 'Encuentre preguntas por tema o texto.', c='Buscar', s='button'),
            P('Guardar en el banco', 'Agregue preguntas nuevas, escribiéndolas o pegándolas.', c='Guardar en el banco'),
        ],
    },
    'materiales:juegos': {
        'titulo': 'Mis juegos',
        'resumen': 'Juegos con sus preguntas: para enviarlos a las clases, compartirlos con colegas o jugarlos en vivo en el tablero.',
        'pasos': [
            P('Mis juegos', 'Los juegos que ha creado con sus preguntas.', c='Mis juegos', s='h6'),
            P('Probar', 'Juéguelo usted antes de enviarlo.', c='Probar'),
            P('Enviar a mis clases', 'Lo publica en la pestaña Gamificación de las clases que escoja.', c='Enviar a mis clases'),
            P('En vivo', 'Abre una partida para proyectar: los estudiantes entran desde el celular y compiten.', c='En vivo'),
            P('Compartir en la Sala', 'Otros docentes lo pueden importar a sus juegos.', c='Compartir en la Sala'),
            P('Conozca cada juego', 'Qué hace cada tipo de juego y para qué sirve.', c='Conozca cada juego'),
            P('Juegos de lógica', 'Rompecabezas sin preguntas (Tangram, Trancón, Empuja cajas…) para desarrollar el pensamiento lógico.', c='Juegos de lógica'),
            P('Nuevo juego', 'Pegue sus preguntas y escoja el juego.', c='Nuevo juego con mis preguntas'),
        ],
    },
    'salon_digital:inicio': {
        'titulo': 'Mi Salón Virtual',
        'resumen': 'Su inicio: desde aquí llega a todo. Está organizado en espacios: Sala de Profesores, Mi Espacio, Mis Estudiantes y Planeación.',
        'pasos': [
            P('Bienvenida', 'Este es su inicio. Siempre puede volver aquí desde el logo.', c='Hola, Profe'),
            P('Para hoy', 'Sus notas rápidas del día.', c='Para hoy'),
            P('Tableros', 'Su pizarra digital para la clase: escriba, pegue imágenes y compártala con los estudiantes.', c='Mis tableros para la clase'),
            P('Sala de Profesores', 'La comunidad de docentes: recursos, preguntas, eventos y colegas.', c='Sala de Profesores', s='h2'),
            P('Mi Espacio de Profe', 'Su portafolio público y lo que ha publicado o guardado.', c='Mi Espacio de Profe'),
            P('Mis Estudiantes', 'Sus grupos, los PIN y QR de ingreso, y PuntoExacto.', c='Mis Estudiantes'),
            P('Planeación', 'Donde crea guías, rúbricas, evaluaciones y juegos, o importa material.', c='Planeación', s='h2'),
            P('Mis clases activas', 'Entre a cada grupo para ver su muro, material, tareas, juegos y notas.', c='Mis clases activas'),
            P('Crear grupo', 'Cree un grupo nuevo y comparta el PIN o QR para que entren los estudiantes.', c='Crear grupo'),
        ],
    },
    'aula:mascota': {
        'titulo': 'Mascota académica',
        'resumen': 'Cada estudiante cuida una mascota respondiendo preguntas: comida, sueño, baño y ánimo bajan con las horas. '
                   'El ánimo sube jugando el minijuego o superando niveles de lógica.',
        'pasos': PESTANAS_AULA[:1] + [
            P('Mascotas de la clase', 'Vea cuántos días lleva viva cada mascota, sus aciertos y su estado de ánimo.', c='Mascotas de la clase'),
            P('Preguntas para las mascotas', 'Opcional: escriba las preguntas que quiere que respondan. Si lo deja vacío, se usan las de los juegos de la clase.', c='Preguntas para las mascotas'),
        ],
    },
}

# Las páginas del aula que no tienen guía propia usan la de las pestañas
GUIA_AULA = {
    'titulo': 'Su clase',
    'resumen': 'Cada clase tiene pestañas: lo que pone aquí sí lo ven sus estudiantes.',
    'pasos': PESTANAS_AULA,
}

# Glosario para el modo «¿Qué es esto?»: al tocar un botón o enlace se busca su rótulo aquí
GLOSARIO = {
    'enviar a mis grupos': 'Lleva el documento a la pestaña Material de las clases que escoja. Desde ese momento lo ven sus estudiantes.',
    'descargar pdf': 'Descarga el documento en PDF para imprimirlo o enviarlo.',
    'duplicar': 'Hace una copia para que arme otra versión sin dañar la original.',
    'usar como formato': 'Lo marca como formato: aparecerá en «Con el formato del colegio» para crear documentos con esa misma estructura.',
    'eliminar': 'Lo borra. Pida confirmación antes: no se puede deshacer.',
    'biblioteca': 'Material ya hecho por mcolegio y por otros docentes. Lo que usa se copia a sus materiales.',
    'banco de preguntas': 'Sus preguntas guardadas por tema, para reutilizarlas en guías, juegos y exámenes.',
    'guías de uso': 'Explicaciones paso a paso de cada herramienta de Planeación.',
    'mi encabezado': 'El encabezado (logo, nombre, datos) que sale en sus documentos.',
    'importar material': 'Traer material de la Biblioteca, de la Sala de Profesores, de lo que le compartieron, de una página HTML o de Excel.',
    'mis juegos': 'Juegos con sus preguntas para la clase o para jugar en vivo.',
    'examen puntoexacto': 'Examen con hoja de respuestas que se califica con la cámara del celular.',
    'rúbrica': 'Instrumento para evaluar con criterios y niveles de desempeño.',
    'compartir': 'Darle el material a un colega o invitarlo a construirlo con usted.',
    'asignar como tarea': 'Convierte el documento en una tarea con fecha de entrega.',
    'vista previa': 'Muestra cómo queda la hoja antes de imprimir.',
    'acomodar': 'Ajusta el espacio: normal, compacto o máximo ahorro de papel.',
    'asistente ia': 'Le ayuda a redactar, generar preguntas o adaptar textos.',
    'adaptar para piar': 'Crea una versión ajustada para un estudiante con PIAR.',
    'en vivo': 'Abre una partida para proyectar; los estudiantes juegan desde el celular.',
    'probar': 'Juega usted mismo para revisar antes de enviar.',
    'sala de profesores': 'La comunidad de docentes de mcolegio: recursos, preguntas y eventos.',
    'muro': 'Avisos y publicaciones para la clase.',
    'material': 'Lo que ven los estudiantes de esta clase.',
    'gamificación': 'Juegos, juegos de lógica y la mascota académica.',
    'tareas': 'Trabajos con fecha de entrega y calificación.',
    'cuestionarios': 'Preguntas en línea que se califican solas.',
    'calificaciones': 'Las notas de la clase.',
    'planilla': 'Las notas de su grupo.',
    'aula invertida': 'Video que se detiene en cada pregunta para que lo vean antes de la clase.',
    'clase en vivo': 'Preguntas proyectadas que los estudiantes responden en tiempo real.',
}


def _url(nombre, *args):
    try:
        return reverse(nombre, args=args)
    except NoReverseMatch:
        return ''


def mapa():
    """El mapa de mcolegio: dónde está cada cosa, en cinco ideas."""
    return [
        {'t': '1. Crear y planear', 'x': 'Planeación (Mis materiales): guías, talleres, evaluaciones, formatos, rúbricas, exámenes y juegos. Es su taller: los estudiantes no lo ven.',
         'url': _url('materiales:lista')},
        {'t': '2. Buscar lo que ya existe', 'x': 'Biblioteca (guías listas por DBA y de otros docentes) y Banco de preguntas.',
         'url': _url('materiales:biblioteca')},
        {'t': '3. Llevarlo a los estudiantes', 'x': 'En cada clase: Material, Tareas, Gamificación, Exámenes… Lo que pone allí sí lo ven.',
         'url': _url('aula:inicio')},
        {'t': '4. Compartir con colegas', 'x': 'Sala de Profesores: recursos, preguntas, eventos y Mis colegas.',
         'url': _url('chat:muro')},
        {'t': '5. Juegos y motivación', 'x': 'Mis juegos (con sus preguntas), juegos de lógica y la mascota académica.',
         'url': _url('materiales:juegos')},
    ]


def guia(view_name):
    """La guía de la página, o None si no tiene (entonces el botón ofrece el mapa y el modo «¿Qué es esto?»)."""
    if view_name in GUIAS:
        return GUIAS[view_name]
    if view_name and view_name.startswith('aula:') and view_name not in ('aula:inicio',):
        return GUIA_AULA
    return None


def datos(request):
    """Lo que necesita el botón en la página actual."""
    vista = getattr(getattr(request, 'resolver_match', None), 'view_name', '') or ''
    g = guia(vista)
    return {'vista': vista, 'guia': g, 'mapa': mapa(), 'glosario': GLOSARIO}


def es_para(user):
    """El botón es para docentes (del colegio o con cuenta individual) y administradores del colegio."""
    if not getattr(user, 'is_authenticated', False):
        return False
    if getattr(user, 'es_admin_colegio', False):
        return True
    try:
        if user.cuenta_salon:
            return True
    except Exception:
        pass
    from notas.permisos import es_docente_usuario
    return es_docente_usuario(user)
