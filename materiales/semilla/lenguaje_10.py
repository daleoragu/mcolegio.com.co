"""Lenguaje 10.º: una guía y un taller por cada uno de los 8 DBA. Textos originales de mcolegio. Borradores para revisar."""
from .base import abierta, imagen, recuadro, tabla, texto, unica, unidad, vf


def _escribe(enunciado, renglones=6):
    return abierta(enunciado, renglones, puntos=2)


def unidades():
    U = {}

    U[1] = unidad(
        tema='Los medios masivos y su influencia',
        objetivo='Asumir una posición crítica y propositiva frente a los medios de comunicación masiva y analizar su influencia en la sociedad actual.',
        explora=[texto('¿Cuántas horas al día pasas frente a una pantalla? ¿Quién decide lo que aparece primero en tu celular?')],
        aprende=[texto('Los medios masivos (televisión, radio, prensa, plataformas digitales) no solo informan: <b>seleccionan</b> qué es noticia, <b>encuadran</b> los hechos y '
                       'difunden visiones de mundo. Los algoritmos de las redes nos muestran lo que confirma lo que ya pensamos (<b>burbuja de filtro</b>).'),
                 tabla([['Pregunta crítica', 'Para qué sirve'], ['¿Quién es el dueño del medio?', 'detectar intereses económicos o políticos'], ['¿Qué voces aparecen y cuáles faltan?', 'ver la diversidad de posturas'],
                        ['¿Qué palabras e imágenes se usan?', 'reconocer el encuadre'], ['¿Cómo me hace sentir?', 'identificar la manipulación emocional']]),
                 texto('Una postura <b>propositiva</b> no solo critica: crea alternativas, como medios escolares o comunitarios que den voz a quienes no la tienen.')],
        recuerda=['Todo medio selecciona y encuadra.', 'Crítico y propositivo: analizo y propongo.'],
        practica=[unica('Que una red me muestre solo opiniones parecidas a las mías se llama…', 'burbuja de filtro', ['libertad de prensa']),
                  unica('Preguntar quién es el dueño de un medio ayuda a…', 'detectar sus intereses', ['saber su dirección'])],
        taller=[unica('Una postura propositiva frente a los medios implica…', 'crear alternativas de comunicación', ['dejar de informarse']),
                _escribe('Compara cómo dos medios distintos presentaron la misma noticia (titular, fotos, fuentes). Escribe tu análisis y tu postura.', 14)])

    U[2] = unidad(
        tema='El guion audiovisual',
        objetivo='Planear textos audiovisuales que articulen elementos verbales y no verbales para desarrollar un tema o una historia.',
        explora=[texto('Piensa en un video que te haya emocionado. ¿Qué lo hizo efectivo: la música, las imágenes, las palabras, el ritmo?')],
        aprende=[texto('Un texto audiovisual combina <b>imagen</b>, <b>sonido</b> (voces, música, efectos) y <b>palabra</b>. Antes de grabar se escribe el <b>guion</b>.'),
                 tabla([['Plano', 'Qué muestra', 'Efecto'], ['General', 'el lugar completo', 'ubica al espectador'], ['Medio', 'el personaje de la cintura hacia arriba', 'diálogo, acción'],
                        ['Primer plano', 'el rostro', 'emoción'], ['Detalle', 'un objeto o parte pequeña', 'resaltar algo importante']]),
                 tabla([['Escena', 'Imagen', 'Sonido', 'Texto o diálogo'], ['1. Exterior, día', 'plano general del río', 'agua y pájaros', 'Narrador: «Aquí empezó todo…»'],
                        ['2. Interior, cocina', 'primer plano de la abuela', 'música suave de marimba', 'Abuela: «Mi mamá cocinaba así…»']]),
                 texto('Al caracterizar culturas en un guion, evita los <b>estereotipos</b>: investiga y deja que las personas hablen con su propia voz.')],
        recuerda=['Guion: escena + imagen + sonido + palabra.', 'Plano general, medio, primer plano, detalle.'],
        practica=[unica('Para mostrar la emoción de un personaje se usa…', 'el primer plano', ['el plano general']),
                  unica('El guion audiovisual se escribe…', 'antes de grabar', ['después de publicar'])],
        taller=[_escribe('Escribe el guion de un video de 2 minutos sobre una tradición cultural de tu región (mínimo 5 escenas, con imagen, sonido y texto).', 16)])

    U[3] = unidad(
        tema='La literatura en su época',
        objetivo='Caracterizar la literatura de un momento histórico a partir de sus exponentes, textos, temáticas y recursos estilísticos.',
        explora=[texto('¿Por qué las historias de caballeros eran tan populares en la Edad Media y hoy lo son las de superhéroes?')],
        aprende=[tabla([['Época', 'Contexto', 'Exponentes y obras', 'Rasgos'], ['Edad Media', 'feudalismo, fe religiosa', 'Cantar de Mio Cid (anónimo)', 'héroe épico, juglares, verso'],
                        ['Renacimiento y Siglo de Oro', 'humanismo, imperio español', 'Garcilaso, Cervantes (Don Quijote, 1605 y 1615), Lope de Vega', 'el ser humano al centro, novela moderna'],
                        ['Barroco', 'crisis y desengaño', 'Quevedo, Góngora, Sor Juana Inés de la Cruz', 'juegos de palabras, contrastes'],
                        ['Romanticismo', 'revoluciones, nacionalismo', 'Bécquer (Rimas), Jorge Isaacs (María, 1867)', 'sentimiento, naturaleza, libertad'],
                        ['Modernismo', 'fin del siglo XIX', 'Rubén Darío (Azul…, 1888), José Asunción Silva', 'musicalidad, belleza, cosmopolitismo']]),
                 texto('La época influye en los <b>géneros</b>: la épica de la Edad Media, la novela con Cervantes, la lírica intimista en el Romanticismo.'),
                 texto('Para caracterizar una época pregunto: ¿qué pasaba en la sociedad? ¿Quiénes escribían y para quién? ¿Qué temas se repiten? ¿Qué recursos de estilo usan?')],
        recuerda=['La obra dialoga con su contexto.', 'Época → temas, géneros y estilo.'],
        practica=[unica('Don Quijote de la Mancha pertenece al…', 'Siglo de Oro', ['Romanticismo', 'Modernismo']),
                  unica('«María», de Jorge Isaacs, es una novela…', 'romántica', ['medieval', 'barroca'])],
        taller=[unica('Rubén Darío es la figura central del…', 'Modernismo', ['Barroco']), vf('El Cantar de Mio Cid tiene un autor conocido.', False),
                _escribe('Elige una época y escribe una ficha: contexto, dos autores, una obra, temas y dos recursos de estilo con ejemplos.', 12)])

    U[4] = unidad(
        tema='Literatura y artes plásticas',
        objetivo='Formular puntos de encuentro entre la literatura y las artes plásticas y visuales de una misma corriente.',
        explora=[imagen('l10-caminante', 40), texto('Observa la pintura: un hombre de espaldas frente a un mar de niebla. ¿Qué siente? ¿Qué poema podría acompañarla?')],
        aprende=[texto('Las corrientes artísticas atraviesan todas las artes. El <b>Romanticismo</b> se ve en «El caminante sobre el mar de nubes» de Caspar David Friedrich '
                       '(hacia 1818) y en las Rimas de Bécquer: el individuo solitario, la naturaleza inmensa, el sentimiento.'),
                 tabla([['Corriente', 'Pintura', 'Literatura', 'Punto de encuentro'], ['Barroco', 'Velázquez, «Las meninas»', 'Góngora, Quevedo', 'juego de apariencias, contraste'],
                        ['Romanticismo', 'Friedrich, Goya', 'Bécquer, Isaacs', 'emoción, naturaleza'], ['Surrealismo', 'Dalí, Magritte', 'André Breton', 'el sueño y el inconsciente'],
                        ['Realismo mágico', 'pintura latinoamericana del siglo XX', 'García Márquez', 'lo extraordinario como cotidiano']]),
                 texto('Para relacionar una obra literaria con una pictórica comparo: tema, emociones que transmite, recursos (color/metáfora, luz/ritmo) y contexto.')],
        recuerda=['Una corriente se expresa en varias artes.', 'Comparo tema, emoción, recursos y contexto.'],
        practica=[unica('El sueño y el inconsciente son centrales en el…', 'Surrealismo', ['Realismo mágico', 'Barroco']),
                  unica('Friedrich es un pintor del…', 'Romanticismo', ['Surrealismo'])],
        taller=[unica('El realismo mágico se asocia con…', 'García Márquez', ['Quevedo', 'Bécquer']),
                _escribe('Escoge una pintura y un poema de la misma corriente. Escribe un texto comparativo de tres párrafos.', 14)])

    U[5] = unidad(
        tema='El debate y la ponencia: voz, tono y punto de vista',
        objetivo='Participar en discursos orales evaluando la progresión temática, el manejo de la voz, el tono, el estilo y los puntos de vista.',
        explora=[texto('Una misma frase, «¡Qué buena idea!», puede ser un elogio o una burla. ¿Qué la cambia?')],
        aprende=[texto('En lo oral, el sentido depende también de la <b>voz</b>: volumen, velocidad, pausas, entonación. Una entonación irónica puede decir lo contrario de las palabras: '
                       'hay que interpretar <b>dobles sentidos</b> y ambigüedades.'),
                 tabla([['Aspecto', 'Qué evaluar'], ['Progresión temática', '¿avanza sin repetirse ni desviarse?'], ['Tono', '¿formal, irónico, conciliador, agresivo?'],
                        ['Estilo y vocabulario', '¿adecuados al público?'], ['Punto de vista', '¿qué postura defiende y con qué argumentos?']]),
                 texto('<b>Ponencia</b>: exposición preparada sobre un tema con introducción, desarrollo con evidencias y conclusión. <b>Debate</b>: dos o más posturas se confrontan con '
                       'argumentos y un moderador. Ambos exigen investigar el contexto del tema en diversas fuentes.')],
        recuerda=['La voz también significa.', 'Evalúo progresión, tono, estilo y punto de vista.'],
        practica=[unica('Decir «¡Qué puntual!» a quien llega tarde es un ejemplo de…', 'ironía', ['progresión temática']),
                  unica('En un debate, quien da la palabra y controla el tiempo es…', 'el moderador', ['el ponente'])],
        taller=[_escribe('Prepárate para un debate sobre «¿Deben prohibirse los celulares en el colegio?». Escribe tu postura, tres argumentos y las posibles objeciones.', 12),
                _escribe('Después del debate, evalúa una intervención propia y una de un compañero: progresión, tono, estilo, vocabulario.', 8)])

    U[6] = unidad(
        tema='Leer críticamente: las voces del texto',
        objetivo='Comprender diversos tipos de texto con actitud crítica, deducir sus referentes sociales e ideológicos y evaluar su plan de contenido.',
        explora=[texto('Lee: «El progreso llegó al pueblo: la carretera trajo camiones, el río trajo dragas y el monte se volvió potrero». ¿Qué piensa el autor del «progreso»? ¿Cómo lo sabes?')],
        aprende=[texto('Todo texto tiene <b>voces</b>: el autor, las fuentes que cita, los personajes. Detrás de ellas hay <b>referentes</b> sociales, culturales o ideológicos. '
                       'En el ejemplo, la enumeración y el cierre («el monte se volvió potrero») muestran una mirada crítica del progreso.'),
                 recuadro('Texto para analizar', '«Los jóvenes de hoy no leen», repiten muchos adultos. Sin embargo, nunca antes una generación había leído tanto: mensajes, foros, subtítulos, '
                          'reseñas. Quizá no leen lo que sus padres esperaban, pero leen. La pregunta no es si leen, sino cómo y qué.', estilo='nota'),
                 tabla([['Al evaluar un texto', 'Preguntas'], ['Plan de contenido', '¿cómo está organizado? ¿tesis, argumentos, conclusión?'], ['Relaciones de sentido', '¿qué conectores usa (sin embargo, por eso)?'],
                        ['Voces', '¿a quién cita? ¿con quién discute?'], ['Referentes', '¿qué ideas sobre la sociedad supone?']])],
        recuerda=['Identifico voces y referentes.', 'Evalúo el plan y las relaciones de sentido.'],
        practica=[unica('En el texto, la voz que el autor discute es la de…', 'los adultos que dicen que los jóvenes no leen', ['los padres de familia lectores']),
                  unica('El conector «Sin embargo» introduce…', 'una oposición', ['una consecuencia', 'un ejemplo'])],
        taller=[unica('La tesis del texto es que…', 'los jóvenes sí leen, pero de otras formas', ['los jóvenes no leen', 'los subtítulos son malos']),
                _escribe('Escribe un párrafo argumentativo que responda al texto: ¿estás de acuerdo? Usa al menos dos conectores y un ejemplo.', 10)])

    U[7] = unidad(
        tema='Ponencias, relatorías y entrevistas',
        objetivo='Producir textos orales (ponencias, comentarios, relatorías, entrevistas) atendiendo a la progresión temática, los interlocutores, el propósito y la situación.',
        explora=[texto('¿Qué diferencia hay entre contar lo que pasó en una reunión, dar tu opinión sobre ella y entrevistar a uno de sus participantes?')],
        aprende=[tabla([['Texto oral', 'Propósito', 'Clave'], ['Ponencia', 'exponer un tema con autoridad', 'dominio de conceptos y evidencias'], ['Comentario', 'opinar sobre un texto o hecho', 'postura argumentada y respetuosa'],
                        ['Relatoría', 'dar cuenta fiel de lo discutido', 'síntesis objetiva y ordenada'], ['Entrevista', 'obtener información u opiniones de alguien', 'preguntas abiertas y escucha activa']]),
                 texto('Al exponer, <b>explica los conceptos clave</b> con tus palabras y con ejemplos: así demuestras que dominas el tema. Adapta el registro a tu público.'),
                 texto('Las preguntas abiertas («¿Cómo vivió…?», «¿Por qué cree que…?») producen respuestas ricas; las cerradas («¿Sí o no?») las limitan.')],
        recuerda=['Propósito + interlocutor + situación.', 'Dominar el tema = explicar sus conceptos clave.'],
        practica=[unica('El texto que resume fielmente lo discutido en una sesión es…', 'la relatoría', ['el comentario', 'la entrevista']),
                  unica('¿Cuál es una pregunta abierta?', '¿Cómo empezó su interés por la música?', ['¿Le gusta la música?'])],
        taller=[_escribe('Prepara una entrevista de 8 preguntas abiertas a un líder de tu comunidad. Realízala y presenta una relatoría de lo conversado.', 14)])

    U[8] = unidad(
        tema='Escribir y corregir: divulgación científica',
        objetivo='Escribir textos de divulgación científica con procedimientos sistemáticos de corrección lingüística y estrategias de producción textual.',
        explora=[texto('¿Cómo le explicarías a un niño de 10 años por qué el cielo es azul, sin usar palabras difíciles y sin decir mentiras?')],
        aprende=[texto('La <b>divulgación científica</b> acerca el conocimiento a un público amplio: usa ejemplos cotidianos, comparaciones y preguntas, sin perder la exactitud.'),
                 tabla([['Etapa', 'Qué hago'], ['Planear', 'público, propósito, fuentes confiables, esquema'], ['Textualizar', 'escribir el borrador con párrafos claros'],
                        ['Revisar', 'coherencia, cohesión, exactitud de los datos'], ['Corregir', 'ortografía, tildes, puntuación, concordancia'], ['Publicar', 'compartir con los lectores']]),
                 recuadro('Lista de corrección', 'Tildes diacríticas: él/el, tú/tu, más/mas, sí/si. · Coma antes de «pero». · Concordancia sujeto-verbo. · Nada de repeticiones innecesarias. '
                          '· Cada dato con su fuente.', estilo='recuerda'),
                 texto('Para motivar al lector: empieza con una pregunta o un dato sorprendente y cierra con una aplicación en la vida diaria.')],
        recuerda=['Divulgar = claro y exacto.', 'Planear, textualizar, revisar, corregir, publicar.'],
        practica=[unica('¿Cuál está bien escrita?', 'Él dijo que tú tienes razón.', ['El dijo que tu tienes razón.', 'Él dijo que tu tienes razón.']),
                  unica('Un buen inicio para un texto de divulgación es…', 'una pregunta o un dato sorprendente', ['una lista de fórmulas'])],
        taller=[unica('Revisar si los datos son exactos y tienen fuente es parte de…', 'la revisión', ['la publicación']),
                _escribe('Escribe un artículo de divulgación (300 palabras) sobre un tema científico que te interese. Intercámbialo con un compañero y corrígelo con la lista.', 16)])
    return U
