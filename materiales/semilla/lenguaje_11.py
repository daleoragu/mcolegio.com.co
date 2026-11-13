"""Lenguaje 11.º: una guía y un taller por cada uno de los 8 DBA. Textos originales de mcolegio. Borradores para revisar."""
from .base import abierta, recuadro, tabla, texto, unica, unidad, vf


def _escribe(enunciado, renglones=6):
    return abierta(enunciado, renglones, puntos=2)


def unidades():
    U = {}

    U[1] = unidad(
        tema='Verificar antes de compartir',
        objetivo='Participar en escenarios académicos, políticos y culturales con una posición crítica frente a los discursos de los medios institucionales, regionales y masivos.',
        explora=[texto('Te llega por un grupo de chat: «URGENTE: mañana cierran todos los colegios por orden del Ministerio». ¿Qué haces antes de reenviarlo?')],
        aprende=[texto('La <b>desinformación</b> circula rápido porque apela a las emociones (miedo, indignación). Los medios institucionales (alcaldía, colegio), regionales y masivos '
                       'responden a contextos e intereses distintos: hay que leerlos en relación con ellos.'),
                 tabla([['Paso para verificar', 'Pregunta'], ['Fuente', '¿quién lo dice? ¿existe? ¿es oficial?'], ['Fecha', '¿es actual o es una noticia vieja que reaparece?'],
                        ['Contraste', '¿otros medios confiables dicen lo mismo?'], ['Evidencia', '¿hay documentos, cifras, enlaces verificables?'], ['Intención', '¿busca informar, vender o manipular?']]),
                 texto('Ser propositivo es también <b>participar</b>: en el gobierno escolar, en foros, en medios comunitarios, con argumentos y datos verificados.')],
        recuerda=['Fuente, fecha, contraste, evidencia, intención.', 'Si no lo verifico, no lo comparto.'],
        practica=[unica('El primer paso ante un mensaje alarmante es…', 'verificar la fuente', ['reenviarlo rápido']),
                  unica('Una noticia vieja que reaparece como nueva se detecta revisando…', 'la fecha', ['el color de la imagen'])],
        taller=[vf('La desinformación suele apelar a emociones como el miedo.', True),
                _escribe('Analiza cómo un medio regional y uno nacional presentaron una noticia de tu región. ¿Qué intereses o contextos explican las diferencias?', 14)])

    U[2] = unidad(
        tema='Códigos verbales y no verbales en la publicidad y la política',
        objetivo='Explicar críticamente cómo se articulan los códigos verbales y no verbales en anuncios publicitarios, políticos y deportivos, y sus implicaciones culturales e ideológicas.',
        explora=[texto('Un anuncio de bebida muestra jóvenes felices en la playa y casi no habla de la bebida. ¿Qué te está vendiendo realmente?')],
        aprende=[texto('Los anuncios combinan el código <b>verbal</b> (eslogan, texto) y el <b>no verbal</b> (imagen, color, música, gestos). Juntos construyen un mensaje que muchas '
                       'veces vende un <b>estilo de vida</b> más que un producto.'),
                 tabla([['Anuncio', 'Intención', 'Recursos frecuentes'], ['Publicitario', 'vender, crear deseo', 'personas atractivas, colores vivos, humor'],
                        ['Político', 'ganar votos o apoyo', 'banderas, multitudes, colores del partido, promesas'], ['Deportivo', 'crear identidad y pertenencia', 'escudos, himnos, ídolos, épica']]),
                 texto('Los símbolos tienen sentido <b>literal</b> y <b>figurado</b>: una paloma es un ave, pero en un afiche significa paz; un león en un logo sugiere fuerza.'),
                 texto('Implicaciones: los anuncios pueden reforzar estereotipos (de género, de belleza, de clase) o cuestionarlos.')],
        recuerda=['Verbal + no verbal = mensaje.', 'Sentido literal y figurado de los símbolos.'],
        practica=[unica('La paloma blanca en un afiche tiene un sentido figurado de…', 'paz', ['comida', 'velocidad']),
                  unica('Un anuncio político busca principalmente…', 'ganar apoyo', ['vender ropa'])],
        taller=[unica('Mostrar siempre a mujeres en la cocina en los anuncios refuerza…', 'estereotipos de género', ['la igualdad']),
                _escribe('Analiza un anuncio (publicitario, político o deportivo): describe los códigos verbales y no verbales, su intención y sus implicaciones culturales.', 12)])

    U[3] = unidad(
        tema='Mi itinerario de lectura',
        objetivo='Decidir qué textos leer y cómo abordarlos según mis experiencias e inclinaciones, y conjugar la lectura individual con la discusión grupal.',
        explora=[texto('¿Cuál es el último libro que leíste porque quisiste, no porque te lo pidieron? ¿Qué te llevó a escogerlo?')],
        aprende=[texto('Un <b>itinerario lector</b> es un plan personal: elijo obras por temas, autores o géneros que me interesan y defino cómo leerlas (subrayar, tomar notas, '
                       'escribir preguntas).'),
                 tabla([['Obra', 'Año', 'Visión política o social que plantea'], ['«Un mundo feliz», Aldous Huxley', '1932', 'una sociedad controlada por el placer y la tecnología'],
                        ['«Rebelión en la granja», George Orwell', '1945', 'cómo una revolución se convierte en tiranía'], ['«1984», George Orwell', '1949', 'vigilancia total y manipulación del lenguaje'],
                        ['«El coronel no tiene quien le escriba», Gabriel García Márquez', '1961', 'la espera, la dignidad y el abandono del Estado']]),
                 texto('El <b>club de lectura</b> combina la lectura individual con la discusión: cada uno aporta su interpretación y la del grupo se enriquece.')],
        recuerda=['Leo por elección y con estrategia.', 'La discusión amplía mi interpretación.'],
        practica=[unica('«1984» trata sobre…', 'la vigilancia y la manipulación', ['un viaje a la Luna']),
                  unica('«Rebelión en la granja» fue escrita por…', 'George Orwell', ['Aldous Huxley', 'Gabriel García Márquez'])],
        taller=[_escribe('Diseña tu itinerario lector para este año: cinco obras, por qué las eliges, cómo las leerás y con quién las discutirás.', 12)])

    U[4] = unidad(
        tema='Los clásicos y su vigencia',
        objetivo='Identificar temas de los clásicos, compararlos con las visiones de mundo de otras épocas y con obras fuera del canon, y asumir una postura sobre su vigencia.',
        explora=[texto('¿Por qué seguimos leyendo historias escritas hace más de dos mil años?')],
        aprende=[tabla([['Clásico', 'Tema', 'Pregunta vigente'], ['«La Odisea», Homero', 'el regreso a casa', '¿qué significa el hogar para un migrante?'],
                        ['«Edipo rey», Sófocles', 'el destino y la verdad', '¿podemos escapar de lo que somos?'], ['«Hamlet», Shakespeare', 'la duda y la venganza', '¿actuar o no actuar ante la injusticia?'],
                        ['«Don Quijote», Cervantes', 'el idealismo frente a la realidad', '¿vale la pena luchar por los sueños?']]),
                 texto('Un <b>clásico</b> es una obra que cada generación vuelve a leer y en la que encuentra algo nuevo. El <b>canon</b> es la lista de obras consideradas esenciales, '
                       'pero también deja por fuera voces (mujeres, pueblos indígenas, literatura oral, novela gráfica).'),
                 texto('Comparar un clásico con una obra no canónica (una novela juvenil, un cómic, un relato oral) muestra cómo los temas se repiten y se transforman.')],
        recuerda=['Clásico: siempre dice algo nuevo.', 'El canon también excluye.'],
        practica=[unica('El tema central de «La Odisea» es…', 'el regreso a casa', ['la guerra de las galaxias']),
                  unica('«Hamlet» fue escrita por…', 'Shakespeare', ['Sófocles', 'Homero'])],
        taller=[vf('El canon literario incluye a todas las voces por igual.', False),
                _escribe('Compara un clásico con una obra que no pertenezca al canon (película, cómic, novela juvenil) que trate un tema parecido. ¿Sigue vigente el clásico? Argumenta.', 14)])

    U[5] = unidad(
        tema='Escuchar argumentos: comprensión, crítica y propuesta',
        objetivo='Comprender que los argumentos de los interlocutores implican procesos de comprensión, crítica y proposición, y reconocer sus implicaciones sociales e ideológicas.',
        explora=[texto('En una discusión, ¿escuchas para entender o para responder?')],
        aprende=[texto('Escuchar un argumento tiene tres momentos: <b>comprender</b> (¿qué dice y por qué?), <b>criticar</b> (¿es válido? ¿qué supone?) y <b>proponer</b> (¿qué alternativa planteo?).'),
                 tabla([['Falacia', 'En qué consiste', 'Ejemplo'], ['Ad hominem', 'atacar a la persona y no al argumento', '«No le creas, es muy joven»'],
                        ['Hombre de paja', 'deformar el argumento del otro', '«Quieres menos tareas, o sea, que no quieres estudiar»'],
                        ['Generalización apresurada', 'concluir mucho con pocos casos', '«Conocí a dos y son así: todos son así»'],
                        ['Falso dilema', 'presentar solo dos opciones', '«O estás conmigo o estás contra mí»']]),
                 texto('Todo discurso tiene <b>implicaciones</b>: sociales (a quién afecta), políticas (qué poder refuerza) e ideológicas (qué visión del mundo supone).')],
        recuerda=['Comprender → criticar → proponer.', 'Detecto falacias.'],
        practica=[unica('«No le creas, es muy joven» es una falacia…', 'ad hominem', ['de falso dilema']),
                  unica('«O estás conmigo o estás contra mí» es un…', 'falso dilema', ['argumento válido'])],
        taller=[unica('Deformar el argumento del otro para refutarlo fácilmente es…', 'hombre de paja', ['generalización apresurada']),
                _escribe('Escucha un debate o un discurso político. Resume la postura, identifica una falacia o un supuesto ideológico y propone una alternativa.', 12)])

    U[6] = unidad(
        tema='Comparar textos y contextos',
        objetivo='Comparar textos de diversos tipos con capacidad crítica, relacionando temáticas, características formales y los contextos en que fueron producidos.',
        explora=[texto('En 1928, en Ciénaga (Magdalena), el ejército disparó contra trabajadores bananeros en huelga. ¿Cómo lo contaría un historiador? ¿Y un novelista?')],
        aprende=[texto('La masacre de las bananeras aparece en «Cien años de soledad» (1967) de García Márquez, donde el número de muertos y el silencio oficial se vuelven parte de la '
                       'ficción. Un texto histórico la cuenta con fuentes, fechas y cifras discutidas.'),
                 tabla([['Aspecto', 'Novela', 'Texto histórico'], ['Propósito', 'crear sentido, conmover', 'explicar con evidencias'], ['Lenguaje', 'figurado, hipérboles', 'preciso, citas'],
                        ['Estructura', 'narrativa no lineal', 'expositiva y argumentativa'], ['Contexto de producción', 'boom latinoamericano, años 60', 'investigación académica']]),
                 texto('Para comparar: tema común → rasgos formales (estructura, léxico, estilo) → contexto social, cultural y político de cada texto → conclusión.')],
        recuerda=['Mismo tema, distintos textos, distintos sentidos.', 'El contexto explica la forma.'],
        practica=[unica('La masacre de las bananeras ocurrió en…', '1928', ['1948', '1991']),
                  unica('Un texto histórico se caracteriza por…', 'usar evidencias y fuentes', ['usar hipérboles'])],
        taller=[_escribe('Compara un poema o cuento con una noticia o crónica sobre el mismo tema. Escribe un texto con introducción, comparación por aspectos y conclusión.', 16)])

    U[7] = unidad(
        tema='Exponer con dominio: un tema, un texto, un autor',
        objetivo='Demostrar por medio de producciones orales el dominio de un tema, un texto o la obra de un autor, haciendo referencia a otros textos.',
        explora=[texto('¿Qué tema dominas tanto que podrías hablar de él diez minutos sin leer? ¿Cómo lo demostrarías?')],
        aprende=[texto('Una exposición con dominio <b>justifica la importancia</b> del tema, explica sus conceptos clave, responde preguntas y <b>cita otros textos</b> '
                       '(intertextualidad): «Como plantea…», «A diferencia de lo que dice…».'),
                 tabla([['Parte', 'Contenido'], ['Apertura', 'pregunta, dato o anécdota; por qué es importante'], ['Desarrollo', 'tres ideas con ejemplos y referencias a otros textos'],
                        ['Cierre', 'síntesis y una pregunta para el público'], ['Preguntas', 'escucho, agradezco, respondo con precisión']]),
                 recuadro('Consejo', 'Usa apoyos visuales con pocas palabras; el protagonista eres tú, no la diapositiva.', estilo='nota')],
        recuerda=['Importancia + conceptos + referencias.', 'Apoyos visuales sencillos.'],
        practica=[unica('Citar otros textos en una exposición se llama…', 'intertextualidad', ['improvisación']),
                  unica('Una buena apertura es…', 'una pregunta o un dato que despierte interés', ['leer la diapositiva completa'])],
        taller=[_escribe('Prepara una exposición de 7 minutos sobre un autor que admires: guion con apertura, tres ideas, dos referencias a otros textos y cierre.', 14)])

    U[8] = unidad(
        tema='El texto académico y su corrección',
        objetivo='Producir textos académicos con procedimientos sistemáticos de corrección lingüística, atendiendo al tipo de texto y al contexto comunicativo.',
        explora=[texto('¿En qué se diferencia escribir un mensaje a un amigo de escribir un ensayo para la universidad?')],
        aprende=[texto('El <b>ensayo académico</b> plantea una <b>tesis</b> y la sostiene con argumentos y fuentes. Su registro es formal y preciso, y se escribe pensando en un lector '
                       'experto o exigente (el enunciatario).'),
                 tabla([['Elemento', 'Ejemplo'], ['Tesis', '«La jornada única mejora el aprendizaje solo si se transforma la forma de enseñar».'],
                        ['Cita (normas APA)', '(Apellido, año) o (Apellido, año, p. 23)'], ['Conectores', 'en primer lugar, además, sin embargo, por consiguiente, en conclusión'],
                        ['Referencia', 'Apellido, N. (año). Título en cursiva. Editorial.']]),
                 recuadro('Plan de corrección', '1) ¿Se cumple el plan textual (tesis, argumentos, conclusión)? 2) ¿Cada párrafo tiene una idea? 3) ¿Los conectores son correctos? '
                          '4) ¿Ortografía y puntuación? 5) ¿Todas las citas tienen referencia?', estilo='recuerda')],
        recuerda=['Tesis + argumentos + fuentes.', 'Corregir es un proceso: plan, párrafos, conectores, ortografía, citas.'],
        practica=[unica('La idea que un ensayo defiende se llama…', 'tesis', ['anécdota', 'título']),
                  unica('«Por consiguiente» introduce…', 'una consecuencia', ['una oposición', 'un ejemplo'])],
        taller=[unica('Una cita en normas APA se escribe…', '(Apellido, año)', ['[Nombre: página]', '«Según internet»']),
                _escribe('Escribe un ensayo académico de 500 palabras sobre un problema de tu región, con tesis, tres argumentos, dos citas en APA y referencias. Corrígelo con el plan.', 18)])
    return U
