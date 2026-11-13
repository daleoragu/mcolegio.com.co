"""Lenguaje 1.º: una guía y una ficha por cada uno de los 8 DBA. Textos originales de mcolegio (adivinanzas, rimas y el
cuento «Tita, la tortuga»), cortos y con imagen. Borradores para que el docente revise."""
from .base import abierta, imagen, recuadro, tabla, texto, unica, vf
from .matematicas_1 import u


def _escribe(enunciado, renglones=2):
    return abierta(enunciado, renglones, puntos=1)


def unidades():
    U = {}

    U[1] = u(
        tema='Los medios de comunicación',
        objetivo='Reconocer los medios de comunicación de mi entorno y para qué sirve cada uno.',
        explora=[imagen('l1-radio', 22), imagen('l1-televisor', 22), imagen('l1-celular', 15),
                 texto('¿Cuáles de estos aparatos hay en tu casa? ¿Para qué los usa tu familia?')],
        aprende=[texto('Los <b>medios de comunicación</b> nos cuentan lo que pasa, nos enseñan y nos divierten.'),
                 tabla([['Medio', 'Lo puedo…'], ['Radio', 'escuchar'], ['Televisor', 'ver y escuchar'], ['Periódico', 'leer y mirar fotos'],
                        ['Celular con internet', 'ver, escuchar, leer y escribir'], ['Valla y afiche', 'ver y leer en la calle']]),
                 imagen('l1-periodico', 25), imagen('l1-valla', 40), imagen('l1-afiche', 22),
                 imagen('l1-locutor', 40, 'El locutor de radio cambia la voz: emocionado en el partido, serio en las noticias')],
        recuerda=['En la radio solo escuchamos; en el televisor vemos y escuchamos.', 'Los afiches y las vallas están en la calle.'],
        practica=[unica('¿En cuál medio solo podemos escuchar?', 'La radio', ['El periódico', 'El afiche', 'La valla']),
                  unica('¿Dónde está una valla publicitaria?', 'Junto a la carretera o en la calle', ['Dentro de un libro', 'En el radio'])],
        taller=[unica('¿Qué medio usamos para leer las noticias en papel?', 'El periódico', ['La radio', 'El televisor']),
                unica('¿Cómo habla el locutor cuando narra un gol?', 'Fuerte y emocionado', ['Muy bajito', 'Triste', 'Dormido']),
                vf('En el televisor podemos ver y escuchar.', True),
                imagen('l1-afiche', 25), unica('¿Para qué sirve un afiche?', 'Para invitar o avisar algo a la gente', ['Para escuchar música', 'Para llamar por teléfono']),
                abierta('Dibuja tu programa favorito de radio o de televisión.', 6)])

    U[2] = u(
        tema='Hablo con mi cara y con mis manos',
        objetivo='Entender lo que comunicamos con los gestos de la cara, las manos y el cuerpo.',
        explora=[imagen('l1-cara-feliz', 22), imagen('l1-cara-triste', 22), texto('¿Cómo se siente Tomás en cada dibujo? ¿Cómo lo sabes?')],
        aprende=[texto('Sin decir palabras también <b>comunicamos</b>: con la cara, con las manos y con el cuerpo.'),
                 imagen('l1-cara-enojada', 22, 'Enojada'), imagen('l1-cara-sorpresa', 22, 'Sorprendida'),
                 imagen('l1-gesto-silencio', 22, '¡Silencio!'), imagen('l1-gesto-pulgar', 22, '¡Muy bien!'), imagen('l1-gesto-ven', 18, '¡Ven!'),
                 texto('La <b>voz</b> también dice cosas: una pregunta sube al final, un grito asusta, un silencio nos pone atentos.')],
        recuerda=['Mira la cara de las personas para entender cómo se sienten.', 'Un gesto puede decir «sí», «no», «ven» o «silencio».'],
        practica=[imagen('l1-gesto-silencio', 20), unica('¿Qué nos pide Sofi?', 'Hacer silencio', ['Correr', 'Cantar', 'Gritar']),
                  imagen('l1-cara-sorpresa', 20), unica('¿Cómo está Sofi?', 'Sorprendida', ['Dormida', 'Triste', 'Enojada'])],
        taller=[imagen('l1-gesto-pulgar', 20), unica('¿Qué quiere decir Tomás?', '¡Muy bien!', ['Estoy triste', 'Ven acá', 'No me gusta']),
                imagen('l1-cara-triste', 20), unica('¿Cómo podemos ayudar a Tomás?', 'Preguntarle qué le pasa', ['Reírnos', 'Ignorarlo']),
                unica('¿Con qué gesto decimos «adiós»?', 'Moviendo la mano', ['Cerrando los ojos', 'Tapándonos la boca']),
                abierta('Dibuja tu cara cuando estás feliz y tu cara cuando tienes miedo.', 6)])

    U[3] = u(
        tema='Adivinanzas, rimas y juegos de palabras',
        objetivo='Jugar con las palabras: resolver adivinanzas, decir rimas y cantar.',
        explora=[recuadro('Adivina, adivinador', '<p>De noche salgo a pasear,<br>redonda o como una uña;<br>me miran desde la ventana…<br>¿quién soy? ¡Soy la ___!</p>',
                          estilo='reto'), imagen('l1-luna', 22)],
        aprende=[texto('Las <b>adivinanzas</b> dan pistas para descubrir algo. Las <b>rimas</b> son palabras que terminan con el mismo sonido: '
                       '<b>sol</b> – <b>caracol</b>, <b>gato</b> – <b>zapato</b>.'),
                 recuadro('Adivinanza', '<p>Tengo cresta colorada<br>y despierto a la vereda;<br>canto «¡quiquiriquí!»<br>antes de que el sol se vea.</p>', estilo='recuerda'),
                 imagen('l1-gallo', 22, 'El gallo'),
                 recuadro('Adivinanza', '<p>Cuando llueve me abren,<br>cuando hace sol me guardan;<br>sobre tu cabeza<br>las gotas no te alcanzan.</p>', estilo='recuerda'),
                 imagen('l1-paraguas', 22, 'El paraguas'),
                 recuadro('Retahíla para jugar', '<p>Un pato, dos patos,<br>tres patos con zapatos;<br>cuatro patos en la loma<br>y el quinto se asoma.</p>', estilo='nota')],
        recuerda=['Las adivinanzas tienen pistas.', 'Las palabras que riman terminan igual: pato – zapato.'],
        practica=[unica('¿Qué palabra rima con «sol»?', 'caracol', ['luna', 'mesa', 'perro']),
                  unica('¿Qué palabra rima con «gato»?', 'zapato', ['casa', 'gallo', 'oso'])],
        taller=[unica('¿Qué palabra rima con «ratón»?', 'botón', ['flor', 'pato', 'uva']),
                unica('«Cuando llueve me abren…». ¿Qué es?', 'El paraguas', ['La luna', 'El gallo', 'La mesa']),
                vf('«Mesa» y «fresa» riman.', True),
                _escribe('Escribe o dibuja la respuesta de la adivinanza de la luna.'),
                abierta('Inventa con tu familia una rima con tu nombre y dibújala.', 6)])

    U[4] = u(
        tema='Tita, la tortuga: leo un cuento con imágenes',
        objetivo='Comprender un cuento con ayuda de las imágenes y contar lo que pasa al inicio, en el problema y al final.',
        explora=[imagen('l1-tita-1', 50), texto('Mira la imagen: ¿quién crees que es la protagonista? ¿Dónde vive?')],
        aprende=[recuadro('Tita, la tortuga', '<p>Tita era una tortuga pequeña con una pañoleta roja. Vivía feliz en una casita de hojas, a la orilla del río.</p>',
                          estilo='nota'),
                 imagen('l1-tita-2', 50),
                 texto('Una tarde cayó un aguacero. El río creció y la corriente se llevó la casita de Tita. ¡Tita estaba muy asustada!'),
                 imagen('l1-tita-3', 50),
                 texto('La garza, el sapo y la ardilla la oyeron llorar. «¡Te ayudamos!», dijeron. Entre todos cargaron ramas y hojas.'),
                 imagen('l1-tita-4', 50),
                 texto('Hicieron una casita nueva en lo alto de la loma, donde el río no llega. Tita sonrió: «Con amigos, todo es más fácil».'),
                 tabla([['Inicio', 'Problema', 'Final'], ['Tita vive feliz junto al río.', 'El río se lleva su casita.', 'Sus amigos la ayudan a hacer otra.']])],
        recuerda=['Un cuento tiene inicio, problema y final.', 'Las imágenes nos ayudan a entender lo que leemos.'],
        practica=[unica('¿Qué le pasó a la casita de Tita?', 'Se la llevó el río', ['Se quemó', 'Se la comió el sapo']),
                  unica('¿Quiénes ayudaron a Tita?', 'La garza, el sapo y la ardilla', ['El gallo y el pato', 'Nadie'])],
        taller=[imagen('l1-tita-3', 35), unica('¿Esta imagen es del inicio, del problema o de cuando la ayudan?', 'De cuando la ayudan', ['Del inicio', 'Del final']),
                unica('¿Por qué hicieron la casa en la loma?', 'Porque allí no llega el río', ['Porque es más bonita', 'Porque hace frío']),
                unica('¿Cómo se sintió Tita al final?', 'Feliz', ['Triste', 'Enojada']),
                vf('Tita tenía una pañoleta azul.', False),
                abierta('Dibuja otro final para el cuento de Tita.', 6)])

    U[5] = u(
        tema='Escucho los sonidos de las palabras',
        objetivo='Escuchar y separar las palabras de una oración y reconocer el sonido con que empieza cada palabra.',
        explora=[texto('Escucha a tu profe: «<b>El sapo salta en la mesa</b>». ¿Cuántas palabras dijo? Da una palmada por cada una.')],
        aprende=[texto('Las oraciones están hechas de <b>palabras</b>, y las palabras de <b>sonidos</b>.'),
                 texto('Palabras que empiezan con el sonido <b>m</b>:'), imagen('l1-mesa', 18, 'mesa'), imagen('l1-mano', 16, 'mano'),
                 texto('Palabras que empiezan con el sonido <b>s</b>:'), imagen('l1-sapo', 18, 'sapo'), imagen('l1-sol', 18, 'sol'),
                 texto('Palabras que empiezan con el sonido <b>p</b>:'), imagen('l1-pato', 18, 'pato'),
                 texto('Separamos en golpes de voz (sílabas): <b>ma-no</b> (2), <b>pa-to</b> (2), <b>sol</b> (1), <b>ma-ri-po-sa</b> (4).')],
        recuerda=['Una palmada por cada palabra.', 'Escucha el primer sonido: «sssapo».'],
        practica=[imagen('l1-sapo', 15), unica('¿Con qué sonido empieza «sapo»?', 's', ['m', 'p', 'l']),
                  unica('¿Cuántas palabras tiene «Tita come hojas»?', '3', ['2', '4', '5'])],
        taller=[imagen('l1-pato', 15), unica('¿Con qué sonido empieza «pato»?', 'p', ['s', 'm', 't']),
                imagen('l1-mesa', 15), unica('¿Cuál empieza igual que «mesa»?', 'mano', ['sol', 'pato', 'luna']),
                unica('¿Cuántos golpes de voz tiene «pelota»?', '3', ['2', '4', '1']),
                unica('¿Cuántas palabras tiene «Mi gato duerme mucho»?', '4', ['3', '5', '2']),
                _escribe('Escribe o dibuja tres cosas de tu casa que empiecen con «m».', 4)])

    U[6] = u(
        tema='Leo palabras con imágenes',
        objetivo='Leer palabras sencillas con ayuda de las imágenes y relacionar cada letra con su sonido.',
        explora=[imagen('l1-oso', 22), texto('¿Qué animal es? ¿Puedes leer su nombre? <b>o – s – o</b>')],
        aprende=[texto('Unimos los sonidos para leer: <b>o</b> + <b>so</b> = <b>oso</b>.'),
                 tabla([['Imagen', 'Palabra'], ['oso de anteojos', 'oso'], ['racimo de uvas', 'uva'], ['mapa del tesoro', 'mapa'], ['mono tití', 'mono']]),
                 imagen('l1-uva', 18, 'uva'), imagen('l1-mapa', 20, 'mapa'), imagen('l1-mono', 20, 'mono'),
                 texto('El título y las imágenes de un texto nos dan pistas de lo que vamos a leer.')],
        recuerda=['Leo despacio, sonido por sonido, y luego todo junto.', 'Las imágenes me ayudan a adivinar la palabra.'],
        practica=[imagen('l1-mono', 18), unica('¿Qué dice?', 'mono', ['mesa', 'mapa', 'oso']),
                  imagen('l1-uva', 15), unica('¿Qué dice?', 'uva', ['oso', 'ala', 'mano'])],
        taller=[imagen('l1-mapa', 18), unica('Une la imagen con la palabra:', 'mapa', ['mono', 'mamá', 'mesa']),
                imagen('l1-oso', 18), unica('¿Cuál es la primera letra de «oso»?', 'o', ['a', 's', 'u']),
                unica('¿Qué palabra tiene la letra «u»?', 'uva', ['oso', 'mapa', 'sol']),
                _escribe('Copia la palabra «mamá» y dibuja a tu mamá o a quien te cuida.', 4)])

    U[7] = u(
        tema='Hablo y escucho',
        objetivo='Expresar mis ideas en orden, con la voz adecuada para cada lugar, y escuchar a los demás.',
        explora=[imagen('l1-ronda', 50, 'Conversamos en ronda'), texto('¿Quién está hablando? ¿Qué hacen los demás?')],
        aprende=[texto('Para conversar bien: <b>espero mi turno</b>, <b>miro</b> a quien habla y <b>digo mis ideas en orden</b>: primero, después y al final.'),
                 imagen('l1-biblioteca', 40, 'En la biblioteca hablamos bajito'),
                 imagen('l1-patio', 40, 'En el patio podemos hablar más fuerte'),
                 texto('Hay palabras difíciles de decir. ¡Practiquemos! <b>«Tres tristes tigres»</b>, <b>«Pablito clavó un clavito»</b>.')],
        recuerda=['En lugares cerrados hablo bajito; en lugares abiertos puedo hablar más fuerte.', 'Pido la palabra levantando la mano.'],
        practica=[unica('En la biblioteca hablamos…', 'bajito', ['gritando', 'cantando fuerte']),
                  unica('¿Qué hago para pedir la palabra?', 'Levanto la mano', ['Grito', 'Interrumpo'])],
        taller=[unica('Cuando mi compañero habla, yo…', 'lo escucho y lo miro', ['hablo al mismo tiempo', 'me voy']),
                unica('¿Dónde puedo hablar más fuerte?', 'En el patio', ['En la biblioteca', 'En el hospital']),
                abierta('Cuéntale a tu familia qué hiciste hoy en el colegio: primero, después y al final. Dibuja una parte.', 6)])

    U[8] = u(
        tema='Escribo mis primeras palabras',
        objetivo='Escribir palabras sencillas para contar lo que pienso y lo que me gusta, y notar las palabras que se parecen.',
        explora=[imagen('l1-luna', 18, 'luna'), imagen('l1-lupa', 18, 'lupa'), texto('¿En qué se parecen «luna» y «lupa»? ¿En qué son diferentes?')],
        aprende=[texto('Hay palabras que se parecen pero dicen cosas distintas. ¡Cambia una letra y cambia todo!'),
                 tabla([['luna', 'lupa'], ['casa', 'taza'], ['perro', 'pera']], encabezado=False),
                 imagen('l1-casa', 20, 'casa'), imagen('l1-taza', 18, 'taza'), imagen('l1-perro', 20, 'perro'), imagen('l1-pera', 15, 'pera'),
                 texto('Con palabras escribimos listas, mensajes y cartas: «Me gusta el mango», «Mamá, te quiero».')],
        recuerda=['Escucho cada sonido y escribo su letra.', 'Una letra distinta cambia la palabra.'],
        practica=[imagen('l1-taza', 15), unica('¿Cuál palabra es?', 'taza', ['casa', 'tapa', 'pasa']),
                  _escribe('Escribe tu nombre.', 1)],
        taller=[imagen('l1-perro', 15), unica('¿Cuál palabra es?', 'perro', ['pera', 'pelo', 'peso']),
                unica('¿Qué letra cambia entre «casa» y «taza»?', 'La primera y la del medio', ['Ninguna', 'La última']),
                _escribe('Escribe la lista de tres frutas que te gustan.', 3),
                _escribe('Escribe un mensaje corto para alguien que quieres.', 3),
                abierta('Dibuja lo que más te gusta hacer y escribe una palabra que lo diga.', 6)])
    return U
