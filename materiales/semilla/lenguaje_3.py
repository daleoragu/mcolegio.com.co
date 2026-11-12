"""Lenguaje 3.º: una guía y una ficha por cada uno de los 8 DBA. Textos originales de mcolegio (el cuento del colibrí,
una noticia, un afiche). Borradores para que el docente revise."""
from .base import abierta, imagen, recuadro, tabla, texto, unica, vf
from .matematicas_1 import u


def _escribe(enunciado, renglones=4):
    return abierta(enunciado, renglones, puntos=1)


def unidades():
    U = {}

    U[1] = u(
        tema='Los medios de comunicación de mi región',
        objetivo='Reconocer para qué sirven los medios de comunicación de mi entorno y comparar cómo presentan la información.',
        explora=[texto('¿Qué emisoras escucha tu familia? ¿Qué periódico, página de internet o canal de televisión conoces de tu región?')],
        aprende=[tabla([['Medio', 'Formato', 'Para qué lo usamos'], ['Periódico y revista', 'texto e imágenes impresas', 'informarnos con calma'],
                        ['Noticiero', 'imagen, sonido y texto', 'ver lo que pasa hoy'], ['Valla y afiche', 'imagen y pocas palabras', 'anunciar o invitar'],
                        ['Internet', 'de todo: texto, video, audio', 'buscar, comunicarnos y aprender']]),
                 imagen('l1-periodico', 18), imagen('l2-noticiero', 30),
                 texto('Una misma noticia aparece distinta en cada medio: el periódico da más detalles, la televisión muestra imágenes y la radio llega a '
                       'lugares donde no hay señal de televisión.'),
                 recuadro('Ojo con internet', '<p>No todo lo que circula en internet es cierto. Pregunto: ¿quién lo publicó? ¿Lo dicen otros medios?</p>', estilo='reto')],
        recuerda=['Cada medio tiene su formato.', 'Comparo la información en varios medios antes de creerla.'],
        practica=[unica('¿Qué medio da más detalles escritos de una noticia?', 'El periódico', ['La valla', 'El afiche']),
                  unica('¿Cuál medio usa imagen en movimiento?', 'El noticiero de televisión', ['La revista', 'El afiche'])],
        taller=[unica('Antes de creer algo de internet, debo…', 'revisar quién lo publicó y si lo dicen otros medios', ['compartirlo de una vez']),
                unica('La radio es útil porque…', 'llega a lugares lejanos y se escucha mientras trabajamos', ['tiene imágenes']),
                vf('Una valla publicitaria usa pocas palabras e imágenes llamativas.', True),
                _escribe('Escribe una noticia de tu colegio respondiendo: ¿qué pasó?, ¿cuándo?, ¿dónde? y ¿quiénes?', 5)])

    U[2] = u(
        tema='Textos con imágenes, sonidos y arte',
        objetivo='Leer historietas, tiras cómicas y anuncios, y reconocer la música, la pintura, la escultura y la danza como formas de comunicar.',
        explora=[imagen('l3-tira-comica', 80, 'Una tira cómica sin palabras'), texto('¿Qué pasa en cada viñeta? Cuenta la historia con tus palabras.')],
        aprende=[texto('Una <b>tira cómica</b> cuenta una historia en <b>viñetas</b>. Los <b>globos</b> traen lo que dicen los personajes; las imágenes muestran lo que pasa.'),
                 texto('Las <b>manifestaciones artísticas</b> también comunican: la <b>pintura</b> con colores y formas, la <b>escultura</b> con volumen, '
                       'la <b>danza</b> con movimientos y la <b>música</b> con sonidos.'),
                 imagen('l3-pintura-baile', 35, 'El bambuco: danza y música de nuestra tierra'),
                 texto('En un <b>anuncio</b> las imágenes, los colores y pocas palabras buscan que hagamos algo: comprar, cuidar, participar.')],
        recuerda=['En las historietas leo imágenes y palabras.', 'El arte también es un lenguaje.'],
        practica=[unica('¿Cómo se llaman los cuadros de una historieta?', 'Viñetas', ['Capítulos', 'Estrofas']),
                  unica('¿Con qué comunica la danza?', 'Con movimientos del cuerpo', ['Con letras', 'Con números'])],
        taller=[imagen('l3-tira-comica', 60), unica('¿Qué pasa en la última viñeta?', 'El niño celebra con la flor', ['Siembra la semilla', 'Riega la planta']),
                unica('¿Dónde va lo que dice un personaje de historieta?', 'En el globo', ['En el título', 'En el margen']),
                abierta('Escribe en los globos lo que dicen los personajes de la tira cómica, o haz tu propia tira de 4 viñetas.', 8)])

    U[3] = u(
        tema='El colibrí y el incendio: ¿quién narra la historia?',
        objetivo='Diferenciar textos de ficción y no ficción, identificar al narrador y la estructura de una narración.',
        explora=[imagen('l3-colibri', 45), texto('Por la imagen, ¿de qué crees que trata el cuento? ¿Es real o inventado?')],
        aprende=[recuadro('El colibrí y el incendio', '<p>Un día, el bosque empezó a quemarse. Todos los animales huyeron asustados. Solo un colibrí volaba '
                          'una y otra vez hasta la quebrada, tomaba una gota en el pico y la dejaba caer sobre el fuego.</p>'
                          '<p>—¿Qué haces? —le gritó el armadillo—. ¡Tu gota no va a apagar ese fuego!</p>'
                          '<p>—Ya lo sé —respondió el colibrí—, pero estoy haciendo mi parte.</p>'
                          '<p>Al verlo, el armadillo llevó tierra con sus patas, la danta trajo agua en la trompa y los pájaros batieron sus alas. Entre todos, '
                          'el fuego se apagó.</p>', estilo='nota'),
                 tabla([['Inicio', 'Nudo', 'Desenlace'], ['El bosque se quema y los animales huyen.', 'El colibrí lleva gotas; el armadillo se burla.',
                                                         'Todos ayudan y apagan el fuego.']]),
                 texto('El <b>narrador</b> es la voz que cuenta la historia. Aquí cuenta desde afuera (en tercera persona: «el colibrí volaba»). '
                       'Si un personaje contara su propia historia diría «yo volaba»: sería narrador en primera persona.'),
                 texto('Este cuento es <b>ficción</b> (inventado: los animales hablan). Una noticia o una enciclopedia son <b>no ficción</b> (cuentan hechos reales).')],
        recuerda=['Narrador en tercera persona: «él, ella». En primera persona: «yo».', 'Ficción: inventado. No ficción: real.'],
        practica=[unica('¿En qué persona está contado el cuento?', 'Tercera persona', ['Primera persona']),
                  unica('¿Qué enseña el cuento?', 'Cada uno debe hacer su parte', ['Hay que huir siempre', 'Los colibríes son rápidos'])],
        taller=[unica('¿Quién se burló del colibrí?', 'El armadillo', ['La danta', 'Los pájaros']),
                unica('Una noticia sobre un incendio real es un texto…', 'de no ficción', ['de ficción']),
                vf('En el desenlace, todos los animales ayudan.', True),
                _escribe('Vuelve a contar el cuento como si fueras el colibrí (en primera persona).', 6)])

    U[4] = u(
        tema='Escribo mis propias historias',
        objetivo='Planear y escribir un cuento con personajes, lugar, problema y solución, y leerlo en voz alta con buena entonación.',
        explora=[texto('Si pudieras inventar un personaje, ¿cómo sería? ¿Dónde viviría? ¿Qué problema tendría?')],
        aprende=[texto('Antes de escribir hago un <b>plan</b>:'),
                 tabla([['Plan de mi cuento', 'Mis ideas'], ['¿Quién es el personaje? ¿Cómo es?', ''], ['¿Dónde y cuándo pasa?', ''],
                        ['¿Qué problema tiene?', ''], ['¿Cómo lo soluciona?', ''], ['¿Cómo termina?', '']]),
                 texto('Los personajes, sus acciones y el lugar deben <b>corresponder</b>: un pez vive en el agua, un minero trabaja en una mina.'),
                 texto('Al leer en voz alta, cambio la voz cuando habla cada personaje y respeto los signos: ¿pregunta?, ¡exclamación!')],
        recuerda=['Primero planeo, después escribo y al final reviso.', 'Un cuento necesita un problema y una solución.'],
        practica=[unica('¿Qué va primero al escribir un cuento?', 'Hacer un plan', ['Pasar en limpio', 'Leerlo en voz alta']),
                  unica('Si mi personaje es un pescador, el lugar más lógico es…', 'un río o el mar', ['un desierto', 'la luna'])],
        taller=[_escribe('Llena el plan de tu cuento.', 6), _escribe('Escribe tu cuento con inicio, nudo y desenlace.', 12),
                abierta('Dibuja a tu personaje principal.', 6)])

    U[5] = u(
        tema='Emisor, receptor y lo que queremos comunicar',
        objetivo='Identificar quién habla (emisor), quién escucha (receptor) y para qué, e inferir palabras desconocidas por el contexto.',
        explora=[imagen('l3-telefono', 40), texto('¿Quién habla y quién escucha? ¿Pueden cambiar de papel?')],
        aprende=[texto('En la comunicación hay un <b>emisor</b> (quien envía el mensaje), un <b>receptor</b> (quien lo recibe), un <b>mensaje</b> y un <b>canal</b> (la voz, el papel, el celular).'),
                 texto('Cada mensaje tiene una <b>intención</b>: informar, pedir, convencer, saludar, dar una orden.'),
                 tabla([['Mensaje', 'Intención'], ['«Mañana no hay clase.»', 'informar'], ['«¿Me prestas tu borrador?»', 'pedir'],
                        ['«¡Compra la mejor arepa del pueblo!»', 'convencer']]),
                 texto('Si no conozco una palabra, uso el <b>contexto</b>: «El <b>cántaro</b> estaba lleno de agua fresca» → un cántaro es una vasija.')],
        recuerda=['Emisor envía; receptor recibe.', 'Las palabras de alrededor me ayudan a entender las desconocidas.'],
        practica=[unica('En una carta de Sofi para Tomás, Sofi es…', 'el emisor', ['el receptor', 'el canal']),
                  unica('«¿Me prestas tu borrador?» tiene la intención de…', 'pedir', ['informar', 'convencer'])],
        taller=[unica('«La anciana caminaba despacio apoyada en su bastón.» Un bastón es…', 'un palo para apoyarse', ['un perro', 'una silla']),
                unica('Un anuncio que dice «¡Compra ya!» quiere…', 'convencer', ['informar', 'saludar']),
                unica('Cuando hablamos por teléfono, el canal es…', 'el teléfono', ['el emisor', 'el mensaje']),
                _escribe('Escribe un mensaje para pedir algo y otro para informar algo.', 4)])

    U[6] = u(
        tema='Leo entre líneas',
        objetivo='Comprender lo que dice un texto y lo que da a entender, separar las ideas principales de las secundarias y reconocer distintos tipos de texto.',
        explora=[texto('«Tomás llegó empapado, con los zapatos llenos de barro y el paraguas roto.» ¿Qué pasó afuera, aunque el texto no lo dice?')],
        aprende=[texto('Hay información <b>literal</b> (lo que dice el texto) e <b>inferencial</b> (lo que deduzco): Tomás llegó empapado → <b>estaba lloviendo</b>.'),
                 recuadro('El oso de anteojos', '<p>El oso de anteojos es el único oso de Suramérica. Vive en los bosques de niebla y los páramos de los Andes. '
                          'Tiene manchas claras alrededor de los ojos que parecen gafas. Se alimenta sobre todo de plantas y frutos. Hoy está en peligro porque '
                          'se destruyen los bosques donde vive.</p>', estilo='nota'),
                 imagen('l1-oso', 18),
                 texto('<b>Idea principal</b>: el oso de anteojos es un oso andino en peligro. <b>Ideas secundarias</b>: sus manchas, lo que come, dónde vive.'),
                 texto('Este es un texto <b>informativo</b>: explica algo real. Un cuento es <b>narrativo</b>; una receta es <b>instructiva</b>.')],
        recuerda=['Leo lo que dice el texto y también lo que da a entender.', 'La idea principal resume todo el texto.'],
        practica=[unica('¿Por qué se llama «de anteojos»?', 'Por las manchas alrededor de los ojos', ['Porque usa gafas', 'Porque ve mal']),
                  unica('¿Qué tipo de texto es «El oso de anteojos»?', 'Informativo', ['Narrativo', 'Instructivo'])],
        taller=[unica('¿Qué podemos inferir? Si se destruyen los bosques…', 'el oso se queda sin casa ni comida', ['el oso crece más']),
                unica('¿Cuál es una idea secundaria?', 'Come plantas y frutos', ['Es un oso andino en peligro']),
                unica('«Sofi abrió el regalo y saltó de alegría.» Infiero que…', 'le gustó el regalo', ['no le gustó', 'estaba enferma']),
                _escribe('Escribe en una oración la idea principal de un texto que hayas leído esta semana.', 3)])

    U[7] = u(
        tema='Hablo en público: narro, describo y expongo',
        objetivo='Preparar intervenciones orales cortas ajustando el volumen, el tono, los gestos y las palabras al propósito y al público.',
        explora=[texto('¿Has presentado algo frente a tu salón? ¿Qué fue lo más difícil?')],
        aprende=[tabla([['Propósito', 'Qué hago', 'Ejemplo'], ['Narrar', 'cuento hechos en orden', 'lo que hice en vacaciones'], ['Describir', 'digo cómo es algo', 'mi mascota'],
                        ['Exponer', 'explico un tema', 'el oso de anteojos'], ['Argumentar', 'doy razones', 'por qué cuidar el agua'], ['Informar', 'doy un dato o aviso', 'el horario de la izada']]),
                 texto('Para hablar en público: <b>miro</b> al público, hablo <b>claro y con buen volumen</b>, uso <b>gestos</b> que acompañen y cambio el tono según lo que cuento.'),
                 recuadro('Juego de palabras', '<p>¿Cuántas palabras dices que empiecen con «pa»? Pato, papa, pala, palo, pasto… ¿Y que terminen en «ón»? Ratón, camión, corazón…</p>', estilo='reto')],
        recuerda=['Preparo lo que voy a decir.', 'Mi voz y mis gestos ayudan a que me entiendan.'],
        practica=[unica('Si explico cómo vive el oso de anteojos, estoy…', 'exponiendo', ['narrando un cuento', 'cantando']),
                  unica('Al hablar en público debo…', 'mirar al público y hablar claro', ['mirar el piso y hablar bajito'])],
        taller=[unica('Contar lo que hice el fin de semana es…', 'narrar', ['argumentar', 'describir']),
                unica('Dar razones para cuidar el agua es…', 'argumentar', ['narrar', 'describir']),
                abierta('Prepara una exposición de 1 minuto sobre tu animal favorito: escribe las 3 ideas que vas a decir.', 5)])

    U[8] = u(
        tema='Escribo para mi comunidad: cartas, afiches y plegables',
        objetivo='Escribir textos para opinar sobre un problema de mi entorno, cuidando la concordancia y la ortografía (c, s, z, k, q; diptongos e hiatos).',
        explora=[imagen('l3-afiche-rio', 30), texto('¿Qué problema de tu barrio o vereda te gustaría solucionar? ¿A quién le escribirías?')],
        aprende=[tabla([['Quiero…', 'Escribo…'], ['pedirle algo al alcalde', 'una carta'], ['invitar a cuidar el río', 'un afiche o una pancarta'],
                        ['explicar cómo reciclar', 'un plegable']]),
                 texto('<b>Concordancia</b>: «Los niños <b>juegan</b>» (no «los niños juega»). «Las flores <b>rojas</b>» (no «las flores rojo»).'),
                 texto('<b>Ortografía</b>: el sonido /s/ puede escribirse con <b>c</b> (cine), <b>s</b> (sapo) o <b>z</b> (zapato); el sonido /k/ con '
                       '<b>c</b> (casa), <b>qu</b> (queso) o <b>k</b> (kilo).'),
                 texto('<b>Diptongo</b>: dos vocales en una sílaba (<b>cie</b>-lo). <b>Hiato</b>: dos vocales en sílabas separadas (<b>dí-a</b>, <b>le-ón</b>).')],
        recuerda=['Escojo el texto según lo que quiero lograr.', 'Reviso que sujeto y verbo concuerden.'],
        practica=[unica('¿Cuál está bien escrita?', 'zapato', ['sapato', 'capato']), unica('¿Cuál oración tiene buena concordancia?', 'Los perros ladran', ['Los perros ladra', 'El perro ladran'])],
        taller=[unica('¿Cuál está bien escrita?', 'queso', ['keso', 'ceso']),
                unica('¿Cómo se separa «día»?', 'dí-a', ['día', 'd-ía']),
                unica('Para invitar al barrio a cuidar el río escribo…', 'un afiche', ['una receta', 'un cuento de hadas']),
                _escribe('Escribe una carta corta al alcalde sobre un problema de tu barrio o vereda y propón una solución.', 8)])
    return U
