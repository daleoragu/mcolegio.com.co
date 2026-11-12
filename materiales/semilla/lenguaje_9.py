"""Lenguaje 9.º: una guía y un taller por cada uno de los 8 DBA. Textos originales de mcolegio. Borradores para revisar."""
from .base import abierta, recuadro, tabla, texto, unica, unidad, vf


def _escribe(enunciado, renglones=6):
    return abierta(enunciado, renglones, puntos=2)


def unidades():
    U = {}

    U[1] = unidad(
        tema='Confronto los discursos de los medios',
        objetivo='Confrontar los discursos de los medios, inferir sus referentes ideológicos y plantear mi postura en medios escolares.',
        explora=[texto('¿Por qué una misma marcha puede verse como «vandalismo» en un medio y como «protesta legítima» en otro?')],
        aprende=[texto('Detrás de cada medio hay <b>referentes ideológicos</b>: ideas sobre la sociedad, la economía y la política que influyen en qué se cuenta y cómo.'),
                 texto('Para confrontar: comparo fuentes, distingo hechos de interpretaciones, busco quién financia el medio y qué voces faltan.'),
                 texto('En los <b>medios escolares</b> (periódico, emisora, redes del colegio) puedo publicar mi postura con argumentos y respeto.')],
        recuerda=['Ningún medio es neutral; contrasto antes de concluir.'],
        practica=[unica('Llamar «vandalismo» o «protesta» a lo mismo revela…', 'una postura ideológica', ['un error de ortografía']),
                  unica('Para confrontar un discurso debo…', 'comparar varias fuentes', ['creer al primero'])],
        taller=[_escribe('Escribe una columna para el periódico escolar sobre un tema actual, mostrando dos posturas y la tuya.', 14)])

    U[2] = unidad(
        tema='Los símbolos en mis discursos',
        objetivo='Incorporar con pertinencia símbolos deportivos, cívicos, políticos, religiosos, científicos o publicitarios en los discursos que produzco.',
        explora=[texto('La bandera, el escudo de tu equipo, la cruz, el símbolo de reciclaje, el logo de una marca: ¿qué significa cada uno?')],
        aprende=[tabla([['Ámbito', 'Símbolo', 'Sentido'], ['Cívico', 'bandera, himno', 'identidad nacional'], ['Deportivo', 'camiseta, escudo', 'pertenencia a un equipo'],
                        ['Científico', 'π, H₂O, ⚛', 'conceptos precisos'], ['Publicitario', 'logo', 'identidad de marca'], ['Político', 'colores de un partido', 'afinidad ideológica']]),
                 texto('En desfiles, carnavales y exposiciones los símbolos cuentan historias: los colores, las máscaras, las comparsas.'),
                 texto('Usarlos en mis discursos exige <b>respeto</b> y <b>contexto</b>: un símbolo religioso no se usa como chiste en una campaña escolar.')],
        recuerda=['Los símbolos condensan significados.', 'Su uso depende del contexto.'],
        practica=[unica('H₂O es un símbolo del ámbito…', 'científico', ['deportivo']), unica('El himno nacional pertenece al ámbito…', 'cívico', ['publicitario'])],
        taller=[abierta('Diseña el logo y el lema de una campaña escolar y explica el sentido de cada símbolo.', 8)])

    U[3] = unidad(
        tema='La literatura como memoria y arte',
        objetivo='Analizar el lenguaje literario como manifestación artística y reconocer la literatura como memoria de una región o un país.',
        explora=[texto('¿Puede una novela contar mejor la historia de un país que un libro de historia? ¿Por qué?')],
        aprende=[texto('La literatura crea <b>ficciones</b> y expresa <b>emociones</b>, pero también guarda la <b>memoria</b>: «La vorágine» (1924) denunció la explotación del caucho; '
                       '«Cien años de soledad» recrea la historia del Caribe; muchos relatos de los últimos años narran el conflicto armado.'),
                 texto('Cada obra pertenece a un <b>movimiento</b> o una época con su visión del mundo: el Romanticismo exalta los sentimientos y la naturaleza; el realismo mágico mezcla lo cotidiano '
                       'y lo maravilloso.')],
        recuerda=['La literatura es arte y memoria.'],
        practica=[unica('«La vorágine» denunció…', 'la explotación del caucho', ['la conquista de la Luna']),
                  unica('El realismo mágico mezcla…', 'lo cotidiano con lo maravilloso', ['solo datos históricos'])],
        taller=[_escribe('Elige una obra colombiana y explica qué memoria del país guarda.', 10)])

    U[4] = unidad(
        tema='De la página a la pantalla',
        objetivo='Comparar obras literarias y producciones audiovisuales y analizar sus estrategias narrativas.',
        explora=[texto('¿Has visto una película basada en un libro? ¿Qué cambió?')],
        aprende=[tabla([['Elemento', 'En el libro', 'En el audiovisual'], ['Narrador', 'voz que cuenta', 'cámara, voz en off'], ['Descripción', 'palabras', 'imagen, color, música'],
                        ['Tiempo', 'el lector marca el ritmo', 'el montaje marca el ritmo'], ['Pensamientos', 'monólogo interior', 'actuación, primer plano']]),
                 texto('Las adaptaciones <b>eligen</b>: suprimen personajes, cambian el orden, añaden escenas. Analizo qué se gana y qué se pierde.'),
                 texto('Las producciones sobre hechos reales usan estrategias como el documental, la reconstrucción o el testimonio.')],
        recuerda=['Libro y película narran con lenguajes distintos.'],
        practica=[unica('En el cine, lo que en el libro es el narrador puede ser…', 'la cámara o la voz en off', ['el índice']),
                  unica('Una adaptación siempre…', 'hace elecciones y cambios', ['es idéntica al libro'])],
        taller=[_escribe('Compara un libro y su adaptación (o un cuento y su versión en video): qué cambió y por qué crees que lo hicieron.', 12)])

    U[5] = unidad(
        tema='Debatir con respeto',
        objetivo='Comprender y respetar las opiniones en debates sobre temas de actualidad social.',
        explora=[texto('Tema: «¿Debería prohibirse el plástico de un solo uso en el colegio?» ¿Qué opinan tus compañeros?')],
        aprende=[tabla([['Rol', 'Función'], ['Moderador', 'presenta el tema, da la palabra, controla el tiempo'], ['Equipo a favor', 'defiende la propuesta'],
                        ['Equipo en contra', 'la refuta'], ['Relator', 'resume las conclusiones'], ['Público', 'escucha y pregunta']]),
                 texto('Reglas: respetar turnos y tiempos, argumentar con datos, rebatir ideas y no personas, reconocer cuando el otro tiene razón.')],
        recuerda=['Debatir no es pelear: es confrontar ideas.'],
        practica=[unica('¿Quién controla el tiempo en un debate?', 'El moderador', ['El público']), unica('Rebatir es…', 'contradecir una idea con argumentos', ['insultar'])],
        taller=[_escribe('Prepara tu intervención para el debate sobre el plástico: postura, 3 argumentos con datos y una réplica posible.', 12)])

    U[6] = unidad(
        tema='Estrategias de lectura crítica',
        objetivo='Interpretar textos atendiendo al interlocutor, al contexto y a los referentes ideológicos, sociales y culturales implícitos.',
        explora=[texto('Un anuncio dice: «Las mamás que aman a sus hijos les dan cereal X». ¿Qué está dando por hecho?')],
        aprende=[texto('El anuncio presupone que si no compras ese cereal no amas a tus hijos, y que el cuidado es tarea solo de las mamás: son <b>referentes</b> implícitos.'),
                 tabla([['Estrategia', 'Pregunta'], ['Antes de leer', '¿quién lo escribe, para quién, dónde se publica?'], ['Durante', '¿qué dice?, ¿qué supone?, ¿qué calla?'],
                        ['Después', '¿estoy de acuerdo?, ¿qué evidencias tengo?']])],
        recuerda=['Leer críticamente es leer lo que el texto da por hecho.'],
        practica=[unica('El anuncio presupone que…', 'el amor se demuestra comprando el producto', ['el cereal es caro']),
                  unica('Preguntar «¿qué calla el texto?» es una estrategia…', 'crítica', ['literal'])],
        taller=[_escribe('Analiza un anuncio publicitario: qué dice, qué supone y qué calla.', 10)])

    U[7] = unidad(
        tema='Expongo argumentos oralmente',
        objetivo='Producir textos orales empleando estrategias para exponer argumentos y proponer alternativas a un problema.',
        explora=[texto('En tu colegio hay un problema de convivencia en el recreo. ¿Cómo convencerías al consejo estudiantil de tu propuesta?')],
        aprende=[texto('Estrategias argumentativas: <b>datos y estadísticas</b>, <b>ejemplos</b>, <b>argumento de autoridad</b>, <b>comparación</b>, <b>causa y consecuencia</b>.'),
                 texto('Al final, haz una <b>síntesis</b> de las ideas más relevantes y precisa los conceptos clave.')],
        recuerda=['Argumento + evidencia + síntesis.'],
        practica=[unica('Citar a un experto es un argumento…', 'de autoridad', ['de ejemplo']), unica('La síntesis va…', 'al final', ['al comienzo'])],
        taller=[_escribe('Prepara una exposición de 3 minutos con tu propuesta para mejorar el recreo: problema, propuesta, 3 argumentos y síntesis.', 12)])

    U[8] = unidad(
        tema='Planes textuales y corrección sistemática',
        objetivo='Producir textos a partir de planes y corregirlos sistemáticamente, evaluando mi rol de enunciador y la progresión del tema.',
        explora=[texto('¿Cuántas veces revisas lo que escribes antes de entregarlo? ¿Qué buscas?')],
        aprende=[tabla([['Revisión', 'Qué reviso'], ['1. Global', '¿cumple el propósito?, ¿mi rol como enunciador es claro?'], ['2. Estructura', '¿hay introducción, desarrollo y conclusión?, ¿el tema progresa?'],
                        ['3. Párrafos', '¿cada uno tiene una idea principal?, ¿están conectados?'], ['4. Oraciones', 'concordancia, puntuación, repeticiones'], ['5. Palabras', 'ortografía, tildes, léxico preciso']]),
                 texto('<b>Progresión temática</b>: cada párrafo añade información nueva sobre el tema, sin repetir ni saltar.')],
        recuerda=['Corregir es reescribir.', 'Reviso de lo global a lo particular.'],
        practica=[unica('¿Qué se revisa primero?', 'Que el texto cumpla su propósito', ['Las tildes']),
                  unica('Si dos párrafos dicen lo mismo, falla…', 'la progresión temática', ['la ortografía'])],
        taller=[_escribe('Escribe un ensayo corto sobre un problema de tu comunidad y corrígelo con la tabla de revisión. Entrega borrador y versión final.', 18)])
    return U
