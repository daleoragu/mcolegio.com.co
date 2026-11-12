"""Lenguaje 5.º: una guía y un taller por cada uno de los 8 DBA. Textos originales de mcolegio (una fábula, una versión
breve de un mito muisca, un texto de opinión). Borradores para que el docente revise."""
from .base import abierta, imagen, recuadro, tabla, texto, unica, unidad, vf


def _escribe(enunciado, renglones=6):
    return abierta(enunciado, renglones, puntos=2)


def unidades():
    U = {}

    U[1] = unidad(
        tema='Los medios y yo: informarme para opinar',
        objetivo='Reconocer los elementos de la comunicación y los roles en los medios, y usar lo que informan para dar mi opinión con argumentos.',
        explora=[texto('¿Qué noticia reciente te llamó la atención? ¿Qué opinas de ella? ¿Por qué?')],
        aprende=[tabla([['Elemento', 'Qué es', 'En un noticiero'], ['Emisor', 'quien produce el mensaje', 'periodistas, presentadores'], ['Receptor', 'quien lo recibe', 'la audiencia'],
                        ['Mensaje', 'lo que se comunica', 'la noticia'], ['Canal', 'por dónde viaja', 'la televisión, internet'], ['Código', 'el lenguaje que se usa', 'español, imágenes'],
                        ['Contexto', 'la situación en que ocurre', 'el país, la fecha']]),
                 texto('En los medios hay roles: el <b>reportero</b> investiga, el <b>presentador</b> cuenta, el <b>columnista</b> opina, el <b>entrevistado</b> aporta información.'),
                 texto('Para opinar: <b>informo</b> (¿qué pasó?), <b>tomo posición</b> (¿qué pienso?) y <b>argumento</b> (¿por qué?).')],
        recuerda=['Emisor, receptor, mensaje, canal, código y contexto.', 'Una opinión necesita razones.'],
        practica=[unica('En una noticia de radio, el canal es…', 'la radio', ['el oyente', 'la noticia']),
                  unica('¿Quién escribe su opinión en un periódico?', 'El columnista', ['El entrevistado', 'El lector'])],
        taller=[unica('La audiencia de un noticiero es el…', 'receptor', ['emisor', 'canal']),
                vf('Una opinión sin razones es un buen argumento.', False),
                _escribe('Escoge una noticia y escribe tu opinión con dos argumentos.', 8)])

    U[2] = unidad(
        tema='Mensajes directos e indirectos en imágenes y gestos',
        objetivo='Interpretar lo que dicen y lo que sugieren las imágenes, los símbolos, los emoticones y los gestos, y comparar manifestaciones artísticas.',
        explora=[texto('Si alguien te escribe «Qué bien 🙄», ¿está contento de verdad?')],
        aprende=[texto('Un mensaje <b>directo</b> dice las cosas tal cual. Un mensaje <b>indirecto</b> las sugiere: el emoticón 🙄 cambia el sentido de «qué bien» (es ironía).'),
                 tabla([['Señal', 'Mensaje que sugiere'], ['brazos cruzados', 'desacuerdo o cierre'], ['mirar a los ojos', 'atención y sinceridad'],
                        ['bostezar', 'aburrimiento o cansancio'], ['😂', 'algo muy gracioso']]),
                 texto('Las <b>manifestaciones artísticas</b> (un mural, una canción, una danza) expresan la visión del mundo de una comunidad: el carnaval de Barranquilla, '
                       'los murales de la Comuna 13 en Medellín, las mochilas arhuacas.'),
                 texto('En un texto con imágenes, las imágenes deben ser <b>coherentes</b> con lo que se dice.')],
        recuerda=['Lo indirecto se entiende por el contexto.', 'El arte cuenta cómo ve el mundo una comunidad.'],
        practica=[unica('«Qué bien 🙄» probablemente quiere decir…', 'que no está contento', ['que está feliz']),
                  unica('Cruzar los brazos en una conversación puede indicar…', 'desacuerdo', ['alegría'])],
        taller=[unica('Un mensaje que sugiere sin decirlo es…', 'indirecto', ['directo']),
                unica('Los murales de la Comuna 13 son una manifestación…', 'artística', ['deportiva']),
                _escribe('Describe una manifestación artística de tu región y lo que expresa.', 6)])

    U[3] = unidad(
        tema='Personajes, narrador, autor y géneros literarios',
        objetivo='Diferenciar autor y narrador, reconocer los roles de los personajes y las características de los géneros literarios.',
        explora=[texto('¿Quién cuenta la historia en tu libro favorito? ¿Es la misma persona que lo escribió?')],
        aprende=[texto('El <b>autor</b> es la persona real que escribe el libro. El <b>narrador</b> es la voz que cuenta la historia dentro del texto. Pueden ser diferentes: '
                       'un autor adulto puede crear un narrador que es un perro.'),
                 tabla([['Rol', 'Función'], ['Protagonista', 'el personaje principal'], ['Antagonista', 'se opone al protagonista'], ['Ayudante', 'apoya al protagonista'],
                        ['Secundario', 'participa sin ser central']]),
                 tabla([['Género', 'Características', 'Ejemplos'], ['Narrativo', 'cuenta una historia', 'cuento, novela, fábula, mito, leyenda'],
                        ['Lírico', 'expresa sentimientos, en versos', 'poema, canción'], ['Dramático', 'para representar, con diálogos', 'obra de teatro']])],
        recuerda=['Autor: persona real. Narrador: voz que cuenta.', 'Narrativo, lírico y dramático.'],
        practica=[unica('El personaje que se opone al protagonista es el…', 'antagonista', ['ayudante', 'narrador']),
                  unica('Una obra de teatro pertenece al género…', 'dramático', ['lírico', 'narrativo'])],
        taller=[unica('Un poema pertenece al género…', 'lírico', ['dramático']),
                vf('El narrador siempre es el autor.', False),
                _escribe('Escribe una escena de teatro corta con dos personajes (protagonista y antagonista).', 10)])

    U[4] = unidad(
        tema='Leo mitos, fábulas y leyendas de muchas culturas',
        objetivo='Ampliar mi visión del mundo leyendo distintos géneros y culturas, y comparar sus características.',
        explora=[imagen('l5-mito', 40), texto('¿Has oído historias sobre el origen del mundo o de un pueblo? ¿Quién te las contó?')],
        aprende=[recuadro('Bachué (versión breve del mito muisca)', '<p>Cuentan los muiscas que, al principio, de la laguna de Iguaque salió una mujer hermosa llamada Bachué, '
                          'con un niño en brazos. Juntos poblaron la tierra y enseñaron a la gente a cultivar, a vivir en paz y a respetar a los dioses. Cuando su tarea terminó, '
                          'regresaron a la laguna convertidos en serpientes.</p>', estilo='nota'),
                 tabla([['Género', 'Qué cuenta', 'Ejemplo'], ['Mito', 'el origen del mundo o de un pueblo, con seres sagrados', 'Bachué (muisca)'],
                        ['Leyenda', 'hechos con base real exagerados por la tradición', 'La Llorona, el Mohán'], ['Fábula', 'una historia con animales y una moraleja', 'La liebre y la tortuga']]),
                 texto('Leer textos de otras culturas nos ayuda a entender cómo piensan y qué valoran.')],
        recuerda=['El mito explica orígenes; la leyenda exagera hechos; la fábula enseña con animales.'],
        practica=[unica('El relato de Bachué es un…', 'mito', ['fábula', 'noticia']), unica('¿De dónde salió Bachué?', 'De la laguna de Iguaque', ['Del mar', 'De una montaña'])],
        taller=[unica('Una historia con animales y una moraleja es una…', 'fábula', ['leyenda', 'mito']),
                unica('¿Qué enseñó Bachué a la gente?', 'A cultivar y vivir en paz', ['A hacer guerras']),
                _escribe('Pregunta en tu familia por una leyenda de tu región y escríbela.', 10)])

    U[5] = unidad(
        tema='Lo que se dice y lo que se da a entender',
        objetivo='Comprender el sentido global de los mensajes relacionando lo explícito con lo implícito, y diferenciar mesa redonda, panel, foro y debate.',
        explora=[texto('«Tomás miró el reloj, guardó sus cosas y se paró junto a la puerta.» ¿Qué quiere Tomás, aunque no lo diga?')],
        aprende=[texto('Información <b>explícita</b>: lo que se dice. <b>Implícita</b>: lo que se deduce. Tomás quiere <b>irse</b>.'),
                 imagen('l5-mesa-redonda', 40, 'Mesa redonda'),
                 tabla([['Espacio', 'Cómo funciona'], ['Mesa redonda', 'varios expertos exponen puntos de vista sobre un tema, con un moderador'],
                        ['Panel', 'expertos conversan entre sí frente al público'], ['Foro', 'el público participa con preguntas y opiniones'],
                        ['Debate', 'dos posiciones opuestas argumentan, con turnos y tiempos']]),
                 texto('Asumo una postura <b>crítica y respetuosa</b>: no creo todo lo que escucho y respeto a quien piensa distinto.')],
        recuerda=['Explícito: lo dicho. Implícito: lo deducido.', 'En un debate hay posiciones opuestas.'],
        practica=[unica('¿Qué quiere Tomás?', 'Irse', ['Dormir', 'Comer']), unica('Dos grupos con posiciones contrarias que argumentan hacen un…', 'debate', ['panel', 'foro'])],
        taller=[unica('«Sofi llegó con el paraguas mojado.» Implícito:', 'está lloviendo', ['hace sol']),
                unica('En el foro…', 'el público participa', ['solo hablan los expertos']),
                _escribe('Escribe tus argumentos a favor o en contra de usar celulares en el salón para un debate.', 8)])

    U[6] = unidad(
        tema='¿Para qué fue escrito este texto?',
        objetivo='Identificar la intención comunicativa de los textos, su función social y organizar jerárquicamente sus ideas.',
        explora=[texto('Un aviso de «Se busca perro perdido», un cuento y una receta: ¿para qué fue escrito cada uno?')],
        aprende=[tabla([['Tipo de texto', 'Intención', 'Ejemplo'], ['Narrativo', 'contar', 'cuento'], ['Expositivo', 'informar o explicar', 'enciclopedia'],
                        ['Argumentativo', 'convencer', 'artículo de opinión'], ['Instructivo', 'indicar cómo hacer algo', 'receta, manual'], ['Descriptivo', 'decir cómo es algo', 'folleto turístico']]),
                 recuadro('La fábula de la hormiga y el colibrí', '<p>Un colibrí se burlaba de una hormiga que cargaba hojas todo el día. «¡Qué aburrida!», le decía. Llegaron las lluvias '
                          'y las flores se cerraron. El colibrí, con hambre, pidió ayuda. La hormiga le compartió su miel guardada. <b>Moraleja:</b> no te burles del esfuerzo de los demás; '
                          'algún día podrías necesitarlos.</p>', estilo='nota'),
                 texto('Para organizar un texto: <b>idea principal</b> → <b>ideas secundarias</b> → <b>detalles</b>.')],
        recuerda=['Pregunto: ¿para qué fue escrito?', 'Idea principal, ideas secundarias y detalles.'],
        practica=[unica('¿Cuál es la intención de la fábula?', 'Enseñar una moraleja', ['Vender algo', 'Dar instrucciones']),
                  unica('Un manual para armar un juguete es un texto…', 'instructivo', ['narrativo', 'lírico'])],
        taller=[unica('Un artículo de opinión busca…', 'convencer', ['dar una receta']),
                unica('¿Cuál es la moraleja?', 'No te burles del esfuerzo de los demás', ['Los colibríes son rápidos']),
                _escribe('Haz un esquema con la idea principal y las ideas secundarias de un texto de tu libro de Ciencias.', 6)])

    U[7] = unidad(
        tema='Hablo con propósito',
        objetivo='Construir textos orales adecuados al contexto, a los interlocutores y al tema, respetando los turnos y ordenando la información.',
        explora=[texto('¿Cómo le explicarías a un niño de primero por qué hay que lavarse las manos? ¿Y a un médico?')],
        aprende=[texto('Adapto lo que digo al <b>contexto</b> (dónde), a los <b>interlocutores</b> (a quién) y al <b>propósito</b> (para qué).'),
                 tabla([['Antes de hablar', 'Mientras hablo', 'Después'], ['¿para quién?, ¿para qué?, ¿qué ideas y en qué orden?', 'miro al público, hablo claro, uso ejemplos',
                                                                     'escucho preguntas y respondo']]),
                 texto('Respeto los <b>turnos</b>: intervengo cuando me dan la palabra y la cedo cuando termino. Construimos saberes compartiendo experiencias.')],
        recuerda=['Pienso en quién me escucha.', 'Ordeno mis ideas: inicio, desarrollo y cierre.'],
        practica=[unica('Para explicarle algo a un niño de primero uso…', 'palabras sencillas y ejemplos', ['palabras técnicas']),
                  unica('Cuando termino de hablar…', 'cedo la palabra', ['sigo hablando'])],
        taller=[unica('Antes de una exposición debo…', 'planear para quién y para qué hablo', ['improvisar todo']),
                _escribe('Prepara una exposición de 3 minutos sobre un tema de Ciencias Naturales: escribe tu inicio, desarrollo y cierre.', 10)])

    U[8] = unidad(
        tema='Planeo mis textos con esquemas y mapas mentales',
        objetivo='Elaborar planes textuales y usar esquemas y mapas mentales para organizar ideas antes de escribir.',
        explora=[imagen('l5-mapa-mental', 35), texto('¿Cómo te ayuda un mapa mental a ordenar tus ideas?')],
        aprende=[texto('Un <b>mapa mental</b> tiene una idea central y ramas con ideas relacionadas, palabras clave y dibujos.'),
                 tabla([['Plan textual', ''], ['Tema', ''], ['Intención', ''], ['Tipo de texto', ''], ['Ideas en orden (introducción, desarrollo, conclusión)', ''], ['Fuentes consultadas', '']]),
                 texto('La <b>coherencia</b>: todas las ideas hablan del mismo tema y avanzan en orden. La <b>cohesión</b>: uso conectores (además, sin embargo, por eso, finalmente).')],
        recuerda=['Planeo antes de escribir.', 'Los conectores unen las ideas.'],
        practica=[unica('¿Qué va en el centro de un mapa mental?', 'La idea principal', ['Un detalle', 'La conclusión']),
                  unica('«Sin embargo» sirve para…', 'mostrar una idea contraria', ['sumar ideas', 'terminar'])],
        taller=[_escribe('Haz un mapa mental sobre el agua (dibújalo en tu cuaderno) y escribe aquí sus 5 ramas.', 5),
                _escribe('Con tu mapa, escribe un texto expositivo de tres párrafos sobre el agua.', 14)])
    return U
