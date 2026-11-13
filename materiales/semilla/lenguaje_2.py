"""Lenguaje 2.º: una guía y una ficha por cada uno de los 8 DBA. Textos originales de mcolegio (el cuento «El sombrero de
don Ramón», una receta, una carta). Borradores para que el docente revise."""
from .base import abierta, imagen, recuadro, tabla, texto, unica, vf
from .matematicas_1 import u


def _escribe(enunciado, renglones=3):
    return abierta(enunciado, renglones, puntos=1)


def unidades():
    U = {}

    U[1] = u(
        tema='Radio, televisión y prensa: ¿cómo nos informan?',
        objetivo='Comparar cómo informan la radio, la televisión y la prensa, y dar mi opinión sobre lo que veo y escucho.',
        explora=[imagen('l2-noticiero', 50, 'El noticiero'), texto('¿Qué noticias has visto o escuchado esta semana? ¿Dónde?')],
        aprende=[tabla([['Medio', 'Cómo informa', 'Ventaja'], ['Radio', 'con la voz y los sonidos', 'se escucha mientras hacemos otras cosas'],
                        ['Televisión', 'con imágenes en movimiento y sonido', 'vemos lo que pasa'],
                        ['Prensa (periódico)', 'con textos escritos y fotos', 'podemos leer despacio y volver a leer']]),
                 imagen('l1-radio', 15), imagen('l1-televisor', 15), imagen('l1-periodico', 18),
                 texto('Una misma noticia se cuenta distinto en cada medio. ¡Y yo puedo tener mi propia <b>opinión</b>!')],
        recuerda=['La radio usa la voz; la televisión, imagen y voz; la prensa, texto y fotos.', 'Opinar es decir lo que pienso con respeto.'],
        practica=[unica('¿Qué medio usa solo la voz y los sonidos?', 'La radio', ['La prensa', 'La televisión']),
                  _escribe('Escribe una noticia de tu barrio o vereda en una oración.', 2)],
        taller=[unica('¿En qué medio puedo volver a leer la noticia?', 'En la prensa', ['En la radio', 'En la televisión en vivo']),
                unica('Un noticiero de televisión muestra…', 'imágenes en movimiento y sonido', ['solo letras', 'solo sonidos']),
                vf('Todos los medios cuentan la noticia de la misma forma.', False),
                abierta('Prepara con tu familia una noticia corta como si fueras locutor de radio. Escríbela aquí.', 5)])

    U[2] = u(
        tema='Señales y símbolos que nos hablan',
        objetivo='Entender qué nos dicen las señales y los símbolos del entorno: informar, prevenir, prohibir y obligar.',
        explora=[imagen('d-senales', 85), texto('¿Has visto estas señales? ¿Dónde? ¿Qué te dicen?')],
        aprende=[tabla([['Señal', 'Nos dice', 'Sirve para'], ['A. PARE', 'Detente', 'obligar'], ['B. Paso peatonal', 'Por aquí cruzan las personas', 'informar'],
                        ['C. Prohibido el paso', 'No se puede pasar', 'prohibir'], ['D. Baños', 'Aquí están los baños', 'informar'],
                        ['E. Reciclaje', 'Separa la basura', 'instruir'], ['F. Salida de emergencia', 'Por aquí se sale si hay peligro', 'prevenir']]),
                 texto('Las <b>imágenes</b> también nos explican cosas en las etiquetas, los carteles y los manuales.'),
                 imagen('l2-etiqueta', 20, 'La etiqueta muestra lo que trae'), imagen('l2-cartel', 30, 'El cartel enseña a lavarse las manos')],
        recuerda=['Las señales hablan sin palabras.', 'El rojo casi siempre avisa peligro o prohibición.'],
        practica=[imagen('d-senales', 70), unica('¿Cuál señal nos dice que no podemos pasar?', 'C', ['A', 'D', 'E']),
                  unica('¿Qué nos pide la señal PARE?', 'Detenernos', ['Correr', 'Pitar'])],
        taller=[unica('¿Cuál señal buscamos si hay un temblor y debemos salir?', 'F', ['B', 'D', 'E']),
                unica('La señal de reciclaje nos pide…', 'separar la basura', ['hacer silencio', 'cruzar la calle']),
                unica('¿Para qué sirven los dibujos de una etiqueta?', 'Para saber qué trae el producto', ['Para adornar nada más', 'Para jugar']),
                abierta('Diseña una señal para tu salón (por ejemplo, «guardar silencio» o «cuidar las plantas»).', 6)])

    U[3] = u(
        tema='El sombrero de don Ramón: personajes, lugar y acciones',
        objetivo='Identificar los personajes, el lugar, el tiempo y las acciones de un cuento, y sus partes: inicio, nudo y desenlace.',
        explora=[imagen('l2-ramon-1', 50), texto('¿Quién crees que es el protagonista? ¿Dónde vive?')],
        aprende=[recuadro('El sombrero de don Ramón', '<p>En una vereda de la montaña vivía don Ramón con su perro Canelo. Don Ramón tenía un '
                          'sombrero aguadeño que quería mucho: se lo había regalado su papá.</p>', estilo='nota'),
                 imagen('l2-ramon-2', 45),
                 texto('Una mañana de agosto sopló un viento tan fuerte que el sombrero salió volando montaña abajo. «¡Mi sombrero!», gritó don Ramón.'),
                 imagen('l2-ramon-3', 45),
                 texto('El sombrero quedó colgado de un palo de guayaba. Una vaca lo miraba, una gallina cacareaba, y Tomás, el niño de la vereda, '
                       'trepó con cuidado y lo bajó.'),
                 imagen('l2-ramon-4', 45),
                 texto('Tomás subió la loma y le devolvió el sombrero. Don Ramón, feliz, le regaló una bolsa de guayabas. Canelo movía la cola.'),
                 tabla([['Personajes', 'Lugar', 'Tiempo'], ['don Ramón, Canelo, Tomás, la vaca y la gallina', 'una vereda de la montaña', 'una mañana de agosto']]),
                 tabla([['Inicio', 'Nudo (problema)', 'Desenlace (final)'], ['Don Ramón vive con su perro y su sombrero.', 'El viento se lleva el sombrero.',
                                                                              'Tomás lo encuentra y se lo devuelve.']])],
        recuerda=['Los personajes son quienes hacen las acciones.', 'El cuento tiene inicio, nudo y desenlace.'],
        practica=[unica('¿Cómo se llama el perro de don Ramón?', 'Canelo', ['Tito', 'Rayo']),
                  unica('¿Cuál es el nudo del cuento?', 'El viento se lleva el sombrero', ['Don Ramón regala guayabas', 'Don Ramón vive en la montaña'])],
        taller=[unica('¿Dónde quedó colgado el sombrero?', 'En un palo de guayaba', ['En el techo', 'En el río']),
                unica('¿Quién bajó el sombrero?', 'Tomás', ['La vaca', 'Canelo', 'Don Ramón']),
                unica('¿Por qué don Ramón quería tanto su sombrero?', 'Se lo regaló su papá', ['Era nuevo', 'Era de oro']),
                vf('El cuento pasa en una ciudad grande.', False),
                abierta('Dibuja el lugar donde pasa el cuento y a sus personajes.', 6)])

    U[4] = u(
        tema='Predigo, ordeno y leo en voz alta',
        objetivo='Anticipar de qué trata un cuento, ordenar sus hechos y leerlo en voz alta con buen ritmo y pausas.',
        explora=[texto('El título de un cuento es «<b>La gallina que quería volar</b>». ¿De qué crees que trata? Escríbelo o dilo antes de leer.')],
        aprende=[recuadro('La gallina que quería volar', '<p>Pinta era una gallina que miraba a los pájaros todos los días. «Yo también quiero volar», '
                          'decía. Saltaba desde la cerca, aleteaba fuerte… ¡y caía en el pasto!</p><p>Un día, un pájaro le dijo: «Tú no vuelas alto, '
                          'pero cuidas a tus pollitos como nadie». Pinta miró a sus pollitos, dormidos bajo sus alas, y sonrió.</p>', estilo='nota'),
                 imagen('m1-gallina', 18), imagen('n1-pollito', 15),
                 texto('Al leer en voz alta: hago una <b>pausa</b> en cada punto, cambio la voz cuando habla un personaje y no leo ni muy rápido ni muy lento.'),
                 texto('¿Acertaste lo que iba a pasar? Comparar lo que pensé con lo que leí me ayuda a entender.')],
        recuerda=['El título y las imágenes me ayudan a predecir.', 'En el punto hago una pausa.'],
        practica=[unica('¿Qué quería Pinta?', 'Volar como los pájaros', ['Nadar', 'Cantar']),
                  unica('¿Qué pasó primero?', 'Pinta miraba a los pájaros', ['El pájaro le habló', 'Pinta sonrió'])],
        taller=[unica('¿Qué aprendió Pinta?', 'Que es valiosa cuidando a sus pollitos', ['Que sí puede volar alto', 'Que los pájaros son malos']),
                unica('Ordena: ¿qué pasó de último?', 'Pinta miró a sus pollitos y sonrió', ['Saltaba desde la cerca', 'Miraba a los pájaros']),
                unica('Al leer en voz alta, en el punto…', 'hago una pausa', ['grito', 'leo más rápido']),
                abierta('Cambia el final: ¿qué pasaría si Pinta encontrara la forma de volar? Escríbelo o dibújalo.', 6)])

    U[5] = u(
        tema='Sonidos que cambian las palabras',
        objetivo='Entender el mensaje que escucho, reconocer sus palabras importantes y descubrir que al cambiar un sonido cambia la palabra.',
        explora=[imagen('l2-perro-ruido', 45), texto('¿Qué sonidos hay en la imagen? ¿Cuáles son de personas hablando y cuáles del ambiente?')],
        aprende=[texto('Los <b>sonidos de la lengua</b> son los que usamos para hablar. Los <b>sonidos del ambiente</b> son los ladridos, las campanas, los pitos.'),
                 texto('Si cambio un solo sonido, cambia la palabra: <b>mesa</b> → <b>masa</b> → <b>misa</b>; <b>pato</b> → <b>gato</b> → <b>rato</b>.'),
                 texto('En un mensaje busco las <b>palabras importantes</b>: «<u>Mañana</u> no hay <u>clase</u> porque hay <u>reunión</u> de padres».')],
        recuerda=['Un sonido distinto, una palabra distinta.', 'Las palabras importantes me dicen de qué trata el mensaje.'],
        practica=[unica('Si cambio la «p» de «pato» por «g», queda…', 'gato', ['rato', 'pito', 'gota']),
                  unica('¿Cuál es un sonido del ambiente?', 'El ladrido del perro', ['La voz de la profe', 'Una canción cantada'])],
        taller=[unica('«Mesa» y «masa» se diferencian en…', 'una vocal', ['todas las letras', 'nada']),
                unica('En «Mañana no hay clase», la palabra más importante es…', 'clase', ['hay', 'no']),
                unica('¿Qué palabra sale si cambio la «l» de «luna» por «c»?', 'cuna', ['pluma', 'lupa']),
                _escribe('Escribe dos palabras que cambien con una sola letra (como pato – gato).', 2)])

    U[6] = u(
        tema='Leo y entiendo: una receta de arepas',
        objetivo='Predecir de qué trata un texto por su forma, leerlo con fluidez, ordenar sus pasos y separar las palabras en sílabas.',
        explora=[imagen('l2-receta', 45), texto('Mira la imagen: ¿qué vamos a preparar? ¿Has ayudado a hacer arepas en tu casa?')],
        aprende=[recuadro('Arepas de mi casa', '<p><b>Ingredientes:</b> 2 tazas de harina de maíz, 2 tazas de agua tibia, sal y mantequilla.</p>'
                          '<p><b>Pasos:</b></p><ol><li>Mezcla la harina con la sal.</li><li>Agrega el agua poco a poco y amasa.</li>'
                          '<li>Haz bolitas y aplánalas con las manos.</li><li>Pídele a un adulto que las ase en el budare.</li>'
                          '<li>Úntales mantequilla y ¡a comer!</li></ol>', estilo='nota'),
                 texto('Una <b>receta</b> tiene título, ingredientes y pasos en orden. Por su forma ya sabemos qué tipo de texto es.'),
                 texto('Las palabras se separan en <b>sílabas</b>: a-re-pa (3), ha-ri-na (3), man-te-qui-lla (4). '
                       'La sílaba que suena más fuerte tiene el <b>acento</b>: a-<b>RE</b>-pa.')],
        recuerda=['Las recetas tienen ingredientes y pasos en orden.', 'La sílaba con más fuerza tiene el acento.'],
        practica=[unica('¿Qué se hace primero?', 'Mezclar la harina con la sal', ['Untar la mantequilla', 'Asar las arepas']),
                  unica('¿Cuántas sílabas tiene «harina»?', '3', ['2', '4'])],
        taller=[unica('¿Quién debe asar las arepas?', 'Un adulto', ['El niño solo', 'Nadie']),
                unica('¿Qué ingrediente NO está en la receta?', 'Azúcar', ['Agua', 'Sal', 'Harina de maíz']),
                unica('¿Cuál es la sílaba con acento en «mantequilla»?', 'qui', ['man', 'te', 'lla']),
                _escribe('Escribe los pasos para lavarte las manos.', 4)])

    U[7] = u(
        tema='Converso y me hago entender',
        objetivo='Participar en conversaciones respetando los turnos, escoger bien las palabras y pronunciar con claridad r, rr y q.',
        explora=[imagen('l1-ronda', 45), texto('¿Qué reglas tenemos para conversar en el salón?')],
        aprende=[texto('Para conversar: <b>pido la palabra</b>, <b>escucho</b> sin interrumpir y <b>hablo del tema</b> que estamos tratando.'),
                 texto('Practiquemos la <b>r</b> suave (pera, cara), la <b>rr</b> fuerte (perro, carro) y la <b>q</b> (queso, quiero).'),
                 imagen('l2-rr', 40, '«El perro corre detrás del carro rojo»'),
                 recuadro('Trabalenguas', '<p>Erre con erre, cigarro;<br>erre con erre, barril;<br>rápido ruedan los carros,<br>cargados de azúcar del ferrocarril.</p>',
                          estilo='reto'),
                 texto('Cambio el <b>ritmo de mi voz</b> para expresar: más lento para contar algo triste, más rápido para algo emocionante.')],
        recuerda=['Escucho y espero mi turno.', 'La r al principio de palabra suena fuerte: ratón, río.'],
        practica=[unica('¿Cuál palabra tiene «rr»?', 'carro', ['caro', 'cara', 'pera']),
                  unica('Si alguien está hablando, yo…', 'espero mi turno', ['lo interrumpo', 'hablo más duro'])],
        taller=[unica('¿Cuál palabra tiene «q»?', 'queso', ['casa', 'kilo']),
                unica('«Caro» y «carro» son…', 'palabras diferentes', ['la misma palabra']),
                unica('Para contar algo emocionante, mi voz va…', 'más rápida y alegre', ['muy lenta y baja']),
                abierta('Cuenta a tu familia el cuento de don Ramón con tus palabras. Escribe qué te dijeron.', 4)])

    U[8] = u(
        tema='Escribo para comunicar: cartas, invitaciones y autorretratos',
        objetivo='Escoger el tipo de texto según lo que quiero decir y escribir oraciones con buena ortografía (b, v, m, n, ñ, r, rr).',
        explora=[imagen('l2-carta', 25), texto('¿Alguna vez has recibido una carta o una invitación? ¿Qué decía?')],
        aprende=[tabla([['Quiero…', 'Escribo…'], ['contar cómo soy', 'un autorretrato'], ['invitar a una fiesta', 'una invitación'],
                        ['decirle algo a alguien que está lejos', 'una carta']]),
                 recuadro('Invitación', '<p>¡Hola, Sofi!<br>Te invito a mi cumpleaños el sábado 15 de marzo a las 3 de la tarde, en mi casa.<br>¡Te espero!<br>Tomás</p>',
                          estilo='nota'),
                 texto('<b>Ortografía</b>: antes de <b>p</b> y <b>b</b> se escribe <b>m</b>: ca<b>m</b>po, ca<b>m</b>bio. '
                       'Con <b>ñ</b>: niño, montaña. Con <b>rr</b> entre vocales para el sonido fuerte: pe<b>rr</b>o.'),
                 texto('Separo las palabras en <b>sílabas</b> con golpes de voz: ca-mi-se-ta (4).')],
        recuerda=['Antes de p y b va m.', 'Una invitación dice qué, cuándo, dónde y quién invita.'],
        practica=[unica('¿Cuál está bien escrita?', 'campo', ['canpo', 'kampo']),
                  unica('Para invitar a mi fiesta escribo…', 'una invitación', ['una receta', 'una noticia'])],
        taller=[unica('¿Cuál está bien escrita?', 'montaña', ['montana', 'montanya']),
                unica('¿Cuál está bien escrita?', 'tambor', ['tanbor', 'tamvor']),
                unica('¿Cuántas sílabas tiene «camiseta»?', '4', ['3', '5']),
                _escribe('Escribe una invitación para tu familia a una actividad del colegio.', 5),
                abierta('Haz tu autorretrato: dibújate y escribe tres oraciones sobre cómo eres.', 8)])
    return U
