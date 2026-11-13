"""Lenguaje 4.º: una guía y un taller por cada uno de los 8 DBA. Textos originales de mcolegio (poemas, una noticia,
un texto expositivo). Borradores para que el docente revise."""
from .base import abierta, imagen, recuadro, tabla, texto, unica, unidad, vf


def _escribe(enunciado, renglones=5):
    return abierta(enunciado, renglones, puntos=2)


def unidades():
    U = {}

    U[1] = unidad(
        tema='Analizo la noticia en distintos medios',
        objetivo='Comparar cómo presentan una misma noticia la radio, la televisión y la prensa, y reconocer su estructura (qué, quién, cuándo, dónde, cómo, por qué).',
        explora=[imagen('l4-noticia-radio-tv', 45), texto('El abuelo y la niña escuchan la misma noticia. ¿Se enteran de lo mismo?')],
        aprende=[recuadro('Noticia', '<p><b>Estudiantes del Líbano siembran 500 árboles</b></p><p>El pasado sábado, 120 estudiantes de primaria sembraron 500 árboles nativos en '
                          'la ribera de la quebrada. La actividad, organizada por la junta de acción comunal, busca proteger el agua del municipio.</p>', estilo='nota'),
                 tabla([['Pregunta', 'Respuesta en la noticia'], ['¿Qué pasó?', 'se sembraron 500 árboles'], ['¿Quiénes?', '120 estudiantes de primaria'],
                        ['¿Cuándo?', 'el sábado pasado'], ['¿Dónde?', 'en la ribera de la quebrada'], ['¿Por qué?', 'para proteger el agua']]),
                 texto('La noticia tiene <b>titular</b>, <b>entrada</b> (lo más importante) y <b>cuerpo</b> (los detalles). En radio, la voz y los sonidos reemplazan las imágenes; '
                       'en televisión, el video muestra lo que pasó; en prensa, el texto da más detalles.')],
        recuerda=['Una noticia responde: qué, quién, cuándo, dónde, cómo y por qué.', 'Compara la misma noticia en varios medios.'],
        practica=[unica('¿Quiénes sembraron los árboles?', '120 estudiantes de primaria', ['La alcaldía', 'Los turistas']),
                  unica('El titular de una noticia…', 'resume lo más importante', ['va al final', 'es la firma'])],
        taller=[unica('¿Por qué sembraron los árboles?', 'Para proteger el agua', ['Para vender madera']),
                unica('¿Qué medio puede mostrar video de la siembra?', 'La televisión', ['La radio', 'El periódico impreso']),
                _escribe('Escribe una noticia de tu colegio con titular, entrada y cuerpo.', 8)])

    U[2] = unidad(
        tema='Escribo a partir de imágenes',
        objetivo='Escribir textos inspirados en fotografías, afiches, canciones y conversaciones, y usar elementos no verbales para reforzar el mensaje.',
        explora=[imagen('l4-afiche-lectura', 30), texto('¿Qué te invita a hacer este afiche aunque no tenga palabras?')],
        aprende=[texto('Las <b>imágenes</b>, los <b>colores</b>, el <b>tamaño de las letras</b> y los <b>emoticones</b> también comunican. En un afiche, la imagen atrae y '
                       'las pocas palabras dicen lo esencial.'),
                 texto('Para escribir a partir de una imagen: <b>observo</b> (qué veo), <b>imagino</b> (qué pasó antes y después) y <b>escribo</b> (describo o narro).'),
                 texto('Puedo completar mis escritos con una <b>secuencia de dibujos</b>, como en una historieta.')],
        recuerda=['Lo no verbal refuerza lo que escribo.', 'Observo, imagino y escribo.'],
        practica=[unica('¿Qué atrae la atención en un afiche?', 'La imagen y los colores', ['Un texto muy largo']),
                  _escribe('Escribe un título para el afiche de la feria del libro.', 2)],
        taller=[imagen('l3-tira-comica', 55), _escribe('Escribe la historia que cuentan las viñetas.', 8),
                unica('Un emoticón 😊 al final de un mensaje indica…', 'alegría o amabilidad', ['enojo', 'tristeza']),
                abierta('Diseña un afiche para invitar a cuidar el agua: imagen, título y una frase.', 8)])

    U[3] = unidad(
        tema='Creo textos literarios con lo que he leído',
        objetivo='Relacionar las obras con su contexto y sus temas, y usar figuras literarias al escribir.',
        explora=[texto('¿Qué cuentos, leyendas o canciones conoces de tu región? ¿De qué tratan?')],
        aprende=[texto('Toda obra se crea en un <b>contexto</b> (un lugar, una época, una cultura). Las leyendas de la Madremonte o el Mohán nacieron en el campo colombiano '
                       'y hablan de cuidar los ríos y los bosques.'),
                 texto('Las obras tratan <b>temas</b>: la amistad, el miedo, la naturaleza, la familia, la justicia.'),
                 tabla([['Figura literaria', 'Qué es', 'Ejemplo'], ['Comparación (símil)', 'compara con «como»', 'Sus ojos brillaban como luceros'],
                        ['Metáfora', 'nombra una cosa con otra', 'El río es una serpiente de plata'], ['Personificación', 'da cualidades humanas a algo', 'El viento cantaba entre los árboles'],
                        ['Hipérbole', 'exagera', 'Te lo he dicho un millón de veces']])],
        recuerda=['Una obra nace en un lugar y una época.', 'Las figuras literarias embellecen lo que escribo.'],
        practica=[unica('«El sol sonreía sobre el pueblo» es una…', 'personificación', ['comparación', 'hipérbole']),
                  unica('«Sus manos eran suaves como seda» es una…', 'comparación', ['metáfora', 'hipérbole'])],
        taller=[unica('«Me muero de hambre» es una…', 'hipérbole', ['personificación', 'comparación']),
                unica('La leyenda del Mohán habla de…', 'los ríos y el respeto a la naturaleza', ['las ciudades grandes']),
                _escribe('Escribe un párrafo sobre tu lugar favorito usando una comparación y una personificación.', 6)])

    U[4] = unidad(
        tema='Poemas: la realidad dicha con figuras',
        objetivo='Leer poemas, reconocer sus figuras literarias y escribir mis propios poemas.',
        explora=[imagen('l4-luna-poema', 45), texto('¿Qué sientes al ver esta imagen? Escribe tres palabras.')],
        aprende=[recuadro('Noche en el cafetal', '<p>La luna es una lámpara redonda<br>colgada sobre el cafetal dormido;<br>las luciérnagas, como chispas de fogón,<br>'
                          'le cuentan secretos al camino.</p>', estilo='nota'),
                 texto('Un poema se escribe en <b>versos</b> (renglones) que se agrupan en <b>estrofas</b>. Puede tener <b>rima</b> (sonidos iguales al final) o no.'),
                 tabla([['Verso', 'Figura'], ['La luna es una lámpara redonda', 'metáfora'], ['las luciérnagas, como chispas de fogón', 'comparación'],
                        ['le cuentan secretos al camino', 'personificación']]),
                 texto('Para escribir un poema: <b>observo</b> algo real, <b>siento</b> qué me produce y lo digo <b>con imágenes</b>.')],
        recuerda=['Verso: cada renglón. Estrofa: grupo de versos.', 'Los poemas dicen mucho con pocas palabras.'],
        practica=[unica('¿Cuántos versos tiene el poema?', '4', ['1', '2', '8']), unica('«La luna es una lámpara» es una…', 'metáfora', ['hipérbole', 'comparación'])],
        taller=[unica('Un grupo de versos se llama…', 'estrofa', ['párrafo', 'capítulo']),
                unica('¿Qué hacen las luciérnagas en el poema?', 'Le cuentan secretos al camino', ['Se apagan', 'Vuelan lejos']),
                _escribe('Escribe un poema de dos estrofas sobre tu municipio usando al menos una metáfora.', 10)])

    U[5] = unidad(
        tema='Escucho el tono de la voz',
        objetivo='Interpretar el tono de quien habla por su voz, sus pausas y su entonación, y reconocer las palabras que ordenan un discurso.',
        explora=[texto('Di la frase «Ya llegaste» con alegría, con enojo y con sorpresa. ¿Cambia el significado?')],
        aprende=[texto('El <b>tono</b> (alegre, serio, enojado, triste, irónico) se reconoce por el <b>volumen</b>, la <b>velocidad</b>, las <b>pausas</b> y la <b>entonación</b>.'),
                 tabla([['Parte del discurso', 'Palabras que la anuncian'], ['Introducción', 'Primero, para empezar, hoy les voy a hablar de…'],
                        ['Desarrollo', 'Además, luego, por otra parte, por ejemplo…'], ['Cierre', 'Finalmente, en conclusión, para terminar…']]),
                 texto('En una discusión escucho los argumentos de los demás para <b>apoyarlos</b> o <b>criticarlos</b> con respeto.')],
        recuerda=['La misma frase cambia según el tono.', 'Las palabras de enlace ordenan lo que digo.'],
        practica=[unica('«Para terminar…» anuncia…', 'el cierre', ['la introducción', 'el desarrollo']),
                  unica('Si alguien habla rápido, fuerte y con exclamaciones, su tono es…', 'emocionado o enojado', ['tranquilo', 'aburrido'])],
        taller=[unica('«Además…» se usa en…', 'el desarrollo', ['el cierre', 'el saludo']),
                unica('Para criticar una idea en una discusión debo…', 'dar razones con respeto', ['gritar', 'burlarme']),
                _escribe('Prepara un discurso de 1 minuto sobre por qué leer es importante. Usa palabras de introducción, desarrollo y cierre.', 8)])

    U[6] = unidad(
        tema='Organizo la información que leo',
        objetivo='Reconocer la intención y la estructura de los textos y organizar su información en esquemas.',
        explora=[texto('Cuando estudias para una evaluación, ¿cómo organizas lo que lees?')],
        aprende=[recuadro('El agua en Colombia', '<p>Colombia es uno de los países con más agua dulce del mundo. Tiene grandes ríos como el Magdalena, el Cauca, el Atrato y el '
                          'Amazonas, y miles de quebradas que nacen en los páramos. Sin embargo, muchas fuentes de agua están contaminadas por basuras, minería ilegal '
                          'y aguas residuales. Cuidar los páramos y los bosques es cuidar el agua.</p>', estilo='nota'),
                 texto('Es un texto <b>expositivo</b>: su intención es <b>informar</b>. Tiene una idea principal, datos y una conclusión.'),
                 tabla([['Idea principal', 'Colombia tiene mucha agua, pero debe cuidarla'], ['Datos', 'ríos Magdalena, Cauca, Atrato, Amazonas; nacen en los páramos'],
                        ['Problema', 'contaminación por basuras, minería ilegal y aguas residuales'], ['Conclusión', 'cuidar páramos y bosques es cuidar el agua']]),
                 texto('Técnicas para organizar: <b>subrayar</b> lo importante, hacer <b>esquemas</b>, <b>cuadros</b> y <b>resúmenes</b>.')],
        recuerda=['Identifico la intención del texto: narrar, informar, convencer, explicar.', 'Un esquema me ayuda a estudiar.'],
        practica=[unica('¿Cuál es la intención del texto?', 'Informar', ['Narrar un cuento', 'Vender algo']),
                  unica('¿Dónde nacen muchas quebradas?', 'En los páramos', ['En el mar', 'En las ciudades'])],
        taller=[unica('¿Cuál es un problema del agua según el texto?', 'La minería ilegal', ['Hay demasiados páramos']),
                unica('¿Qué técnica sirve para organizar ideas?', 'Hacer un esquema', ['Leer más rápido']),
                _escribe('Haz un resumen del texto en 3 oraciones.', 5)])

    U[7] = unidad(
        tema='Participo en discusiones y tertulias',
        objetivo='Participar en conversatorios, exposiciones y tertulias adaptando lo que digo al tema y al público.',
        explora=[imagen('l4-tertulia', 45), texto('¿Qué hace la niña del cuaderno? ¿Por qué es importante su papel?')],
        aprende=[tabla([['Espacio', 'Cómo es'], ['Conversatorio', 'varias personas conversan sobre un tema'], ['Exposición', 'una persona explica un tema preparado'],
                        ['Tertulia', 'reunión amistosa para hablar de libros, música o temas de interés']]),
                 texto('Roles: el <b>moderador</b> da la palabra y controla el tiempo; los <b>participantes</b> argumentan y escuchan; el <b>relator</b> toma nota.'),
                 texto('Adapto mi forma de hablar: no hablo igual en una exposición ante el rector que con mis amigos en el recreo.')],
        recuerda=['Pido la palabra y respeto el tiempo.', 'Me mantengo en el tema de la discusión.'],
        practica=[unica('¿Quién da la palabra en una discusión?', 'El moderador', ['El público', 'Nadie']),
                  unica('Explicar un tema preparado frente al grupo es una…', 'exposición', ['tertulia', 'conversación privada'])],
        taller=[unica('Si la discusión es sobre el reciclaje, debo hablar de…', 'el reciclaje', ['mi equipo de fútbol']),
                abierta('Organicen una tertulia sobre el libro que más les ha gustado. Escribe tus 3 ideas para participar.', 6)])

    U[8] = unidad(
        tema='Escribo pensando en mi lector',
        objetivo='Escoger el tipo de texto según el propósito y el público, consultar fuentes y hacer un plan de escritura.',
        explora=[texto('Quieres convencer al rector de hacer una huerta escolar. ¿Le escribes un cuento, una carta o un poema? ¿Por qué?')],
        aprende=[tabla([['Propósito', 'Tipo de texto'], ['contar una historia', 'cuento, relato'], ['convencer', 'carta, artículo de opinión'],
                        ['informar', 'noticia, informe'], ['explicar cómo se hace algo', 'instructivo, receta']]),
                 texto('Antes de escribir: <b>consulto fuentes</b> (libros, personas, páginas confiables) y hago un <b>plan</b>.'),
                 tabla([['Plan de escritura', ''], ['¿Para quién escribo?', ''], ['¿Para qué?', ''], ['¿Qué tipo de texto?', ''], ['¿Qué ideas pondré y en qué orden?', '']])],
        recuerda=['Escojo el texto según para qué y para quién escribo.', 'Planeo, escribo, reviso y corrijo.'],
        practica=[unica('Para convencer al rector, el mejor texto es…', 'una carta argumentativa', ['un poema', 'una adivinanza']),
                  unica('¿Qué va primero?', 'Hacer el plan', ['Pasar en limpio', 'Entregar'])],
        taller=[_escribe('Llena el plan de escritura para la carta de la huerta escolar.', 6),
                _escribe('Escribe la carta al rector con al menos dos razones.', 10)])
    return U
