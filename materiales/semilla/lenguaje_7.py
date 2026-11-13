"""Lenguaje 7.º: una guía y un taller por cada uno de los 8 DBA. Textos originales de mcolegio. Borradores para revisar."""
from .base import abierta, recuadro, tabla, texto, unica, unidad, vf


def _escribe(enunciado, renglones=6):
    return abierta(enunciado, renglones, puntos=2)


def unidades():
    U = {}

    U[1] = unidad(
        tema='Clasifico la información de los medios',
        objetivo='Clasificar la información de los medios (hecho, opinión, publicidad, entretenimiento) y usarla como referente para argumentar.',
        explora=[texto('En 10 minutos de televisión o de redes sociales, ¿cuánto es noticia, cuánto es opinión y cuánto es publicidad?')],
        aprende=[tabla([['Tipo', 'Cómo reconocerlo', 'Ejemplo'], ['Hecho', 'se puede comprobar', '«El río creció 2 metros»'], ['Opinión', 'expresa un juicio', '«El alcalde actuó tarde»'],
                        ['Publicidad', 'busca que compremos o adoptemos algo', 'un comercial'], ['Entretenimiento', 'busca divertir', 'una telenovela']]),
                 texto('Para argumentar selecciono la <b>información principal</b>, verifico su fuente y la cito: «Según el IDEAM, …».')],
        recuerda=['Los hechos se comprueban; las opiniones se argumentan.', 'Cito la fuente de mis datos.'],
        practica=[unica('«La final fue el partido más emocionante de la historia» es…', 'una opinión', ['un hecho']),
                  unica('«El partido terminó 2 a 1» es…', 'un hecho', ['una opinión'])],
        taller=[unica('Un mensaje que busca que compres algo es…', 'publicidad', ['noticia']), vf('Toda la información en redes sociales es un hecho comprobado.', False),
                _escribe('Escribe tu punto de vista sobre un tema actual usando al menos un dato con su fuente.', 10)])

    U[2] = unidad(
        tema='Lo verbal y lo no verbal',
        objetivo='Comparar los sistemas verbales y no verbales y comprender textos que combinan ambos.',
        explora=[texto('Un semáforo, una bandera, un emoticón y un aviso de «No fumar»: ¿cuáles usan palabras y cuáles no?')],
        aprende=[texto('El sistema <b>verbal</b> usa palabras (orales o escritas). El <b>no verbal</b> usa imágenes, colores, gestos, sonidos, señales.'),
                 texto('Muchos textos combinan ambos: la <b>historieta</b>, la <b>infografía</b>, el <b>afiche</b>, el <b>meme</b>, el <b>video</b>. La imagen puede reforzar, complementar o contradecir las palabras.'),
                 tabla([['Texto', 'Parte verbal', 'Parte no verbal'], ['Infografía', 'títulos y datos', 'íconos, colores, gráficos'], ['Meme', 'frase', 'imagen que le da el sentido irónico']])],
        recuerda=['Leo juntas las palabras y las imágenes.', 'Lo no verbal también tiene intención.'],
        practica=[unica('Un semáforo comunica con un sistema…', 'no verbal', ['verbal']), unica('Una infografía combina…', 'texto e imágenes', ['solo texto'])],
        taller=[unica('En un meme, la imagen suele…', 'dar el sentido humorístico o irónico', ['no tener relación']),
                abierta('Diseña una infografía sobre el cuidado del agua (textos breves e íconos).', 8)])

    U[3] = unidad(
        tema='Literatura e historia',
        objetivo='Relacionar las obras literarias con los hechos históricos, culturales y sociales en que se produjeron.',
        explora=[texto('¿Conoces alguna novela, cuento o canción que hable de un hecho real de la historia de Colombia?')],
        aprende=[texto('La literatura dialoga con la historia: «Cien años de soledad» alude a la masacre de las bananeras (1928); muchos corridos y vallenatos narran hechos de su región.'),
                 texto('Al leer pregunto: ¿cuándo y dónde se escribió? ¿Qué pasaba entonces? ¿Qué conflicto social aparece? ¿Cómo lo representa el autor?'),
                 recuadro('Relato breve: «El tren»', '<p>Cuando el tren llegó a San Isidro, el abuelo dijo que el mundo se había vuelto pequeño. Por los rieles se fue el café y '
                          'llegaron los periódicos de la capital. Años después, cuando el tren dejó de pasar, el pueblo aprendió que el mundo también puede volver a ser grande.</p>',
                          estilo='nota')],
        recuerda=['Toda obra refleja su tiempo.', 'La literatura es memoria de los pueblos.'],
        practica=[unica('¿Qué hecho histórico aparece en el relato «El tren»?', 'La llegada y desaparición del ferrocarril', ['La independencia']),
                  unica('«Cien años de soledad» alude a…', 'la masacre de las bananeras', ['la llegada a la Luna'])],
        taller=[unica('Leer el contexto de una obra sirve para…', 'entender mejor su sentido', ['nada']),
                _escribe('Explica qué quiso decir el abuelo con «el mundo se había vuelto pequeño».', 6)])

    U[4] = unidad(
        tema='Clasifico las obras por géneros',
        objetivo='Clasificar las producciones literarias en géneros a partir de su contenido y su estructura.',
        explora=[texto('Una canción, un cuento y una obra de teatro: ¿qué tienen de distinto en su forma?')],
        aprende=[tabla([['Género', 'Subgéneros', 'Estructura'], ['Narrativo', 'cuento, novela, fábula, mito, leyenda, crónica', 'narrador, personajes, acciones'],
                        ['Lírico', 'poema, oda, elegía, canción', 'versos, estrofas, ritmo, figuras'], ['Dramático', 'tragedia, comedia, drama', 'diálogos, acotaciones, actos y escenas']]),
                 texto('Cada género expresa una <b>visión del mundo</b>: la tragedia muestra el destino que no se puede evitar; la comedia ridiculiza costumbres; la elegía llora una pérdida.')],
        recuerda=['Narrativo cuenta, lírico expresa, dramático representa.'],
        practica=[unica('Una elegía pertenece al género…', 'lírico', ['dramático']), unica('Las acotaciones aparecen en…', 'las obras de teatro', ['los poemas'])],
        taller=[unica('Una crónica pertenece al género…', 'narrativo', ['lírico']), vf('La comedia busca hacer reír criticando costumbres.', True),
                _escribe('Clasifica tres obras que hayas leído según su género y explica por qué.', 6)])

    U[5] = unidad(
        tema='Escucho con propósito',
        objetivo='Comprender discursos orales deduciendo su propósito, sus líneas temáticas y sus conclusiones.',
        explora=[texto('Escucha un discurso, una entrevista o un pódcast corto. ¿Qué quería lograr quien hablaba?')],
        aprende=[texto('Al escuchar identifico: <b>quién habla</b> y desde qué lugar, <b>qué propósito</b> tiene (informar, persuadir, criticar, motivar), las <b>ideas principales</b> y la <b>conclusión</b>.'),
                 texto('Tomo notas con palabras clave y flechas; al final reconstruyo el discurso con mis palabras.')],
        recuerda=['Escucho activamente: atiendo, anoto y pregunto.'],
        practica=[unica('Un discurso de campaña tiene el propósito de…', 'persuadir', ['entretener']), unica('Para recordar un discurso conviene…', 'tomar notas con palabras clave', ['copiar todo'])],
        taller=[_escribe('Escucha un noticiero de radio y escribe: tema, propósito, dos ideas principales y conclusión.', 8)])

    U[6] = unidad(
        tema='Leo distintos tipos de texto',
        objetivo='Interpretar textos informativos, expositivos, narrativos, líricos, argumentativos y descriptivos, reconociendo su destinatario, su léxico y su estilo.',
        explora=[texto('¿Un artículo científico y un cuento infantil sobre el mismo animal se escriben igual? ¿Para quién es cada uno?')],
        aprende=[recuadro('Dos textos sobre el jaguar', '<p><b>A.</b> El jaguar (<i>Panthera onca</i>) es el felino más grande de América; su población ha disminuido por la pérdida de hábitat.</p>'
                          '<p><b>B.</b> Con sus ojos de miel, el jaguar camina despacio por la selva, dueño del silencio.</p>', estilo='nota'),
                 texto('El texto A es <b>expositivo</b>: léxico especializado, datos, nombre científico; su destinatario busca información. El texto B es <b>lírico</b>: imágenes, metáforas; busca emocionar.'),
                 texto('El <b>destinatario</b> se reconoce por el vocabulario, la extensión y el tono.')],
        recuerda=['El estilo depende de la intención y el destinatario.'],
        practica=[unica('«Panthera onca» es un ejemplo de…', 'léxico especializado', ['metáfora']), unica('El texto B busca…', 'emocionar', ['dar datos científicos'])],
        taller=[unica('«Dueño del silencio» es una…', 'metáfora', ['definición']), _escribe('Escribe dos textos breves sobre tu animal favorito: uno expositivo y uno lírico.', 10)])

    U[7] = unidad(
        tema='Narraciones orales',
        objetivo='Construir narraciones orales con la estructura y el contenido del género que quiero relatar, atendiendo a mis oyentes.',
        explora=[texto('¿Quién cuenta las mejores historias en tu familia? ¿Qué hace para que todos escuchen?')],
        aprende=[texto('Para narrar oralmente: elijo el <b>género</b> (anécdota, leyenda, cuento de espantos, chiste), organizo <b>inicio, nudo y desenlace</b>, uso la <b>voz</b> y los <b>gestos</b> '
                       'para crear suspenso y miro las reacciones del público.'),
                 tabla([['Recurso', 'Efecto'], ['Pausas antes del clímax', 'suspenso'], ['Cambiar la voz de cada personaje', 'viveza'], ['Preguntas al público', 'participación']])],
        recuerda=['Narrar es un arte: voz, ritmo y gestos.'],
        practica=[unica('Una pausa antes del momento más importante crea…', 'suspenso', ['aburrimiento']), unica('Una leyenda se cuenta mejor si…', 'uso la voz y los gestos', ['la leo en voz baja'])],
        taller=[_escribe('Escribe el guion de una leyenda de tu región para contarla oralmente: inicio, nudo, desenlace y dónde harás pausas.', 10)])

    U[8] = unidad(
        tema='Planifico y escribo con un tema central',
        objetivo='Producir textos verbales y no verbales de una tipología seleccionada, con un tema central y subtemas, a partir de un plan.',
        explora=[texto('Vas a escribir un artículo para el periódico escolar sobre la basura en el colegio. ¿Por dónde empiezas?')],
        aprende=[tabla([['Paso', 'Qué hago'], ['1. Propósito y destinatario', 'para quién y para qué escribo'], ['2. Tema central', 'la basura en el colegio'],
                        ['3. Subtemas', 'causas, consecuencias, soluciones'], ['4. Fuentes', 'observación, entrevistas, datos'], ['5. Borrador', 'escribo sin miedo'],
                        ['6. Revisión', 'coherencia, cohesión, ortografía'], ['7. Versión final', 'con imágenes o gráficos si ayudan']]),
                 texto('Cada <b>subtema</b> será un párrafo, y todos deben girar alrededor del <b>tema central</b>.')],
        recuerda=['Un tema central, varios subtemas.', 'Revisar es parte de escribir.'],
        practica=[unica('En el plan, «causas, consecuencias, soluciones» son…', 'subtemas', ['el tema central']),
                  unica('¿Qué va antes de la versión final?', 'La revisión', ['La publicación'])],
        taller=[_escribe('Haz el plan de tu artículo sobre la basura en el colegio.', 6), _escribe('Escribe el artículo (mínimo 3 párrafos).', 16)])
    return U
