"""Ciencias Sociales 2.º: una guía y una ficha por cada uno de los 8 DBA, desde el municipio, la vereda o el barrio.
Borradores para que el docente revise y ajuste a su municipio (nombres de veredas, comunas y lugares)."""
from .base import abierta, imagen, recuadro, tabla, texto, unica, vf
from .matematicas_1 import u


def unidades():
    U = {}

    U[1] = u(
        tema='El paisaje cambia por lo que hacemos',
        objetivo='Reconocer las formas del relieve de mi municipio y explicar cómo las personas cambian el paisaje.',
        explora=[imagen('s2-antes-carretera', 40, 'Antes'), imagen('s2-despues-carretera', 40, 'Después'),
                 texto('¿Qué cambió en el paisaje? ¿Quién hizo esos cambios?')],
        aprende=[texto('El <b>relieve</b> son las formas de la tierra: <b>montaña</b>, <b>valle</b>, <b>llanura</b>, <b>meseta</b> e <b>isla</b>.'),
                 imagen('s1-montana', 25, 'Montaña'), imagen('s1-valle', 25, 'Valle'), imagen('s2-meseta', 25, 'Meseta'), imagen('s1-isla', 25, 'Isla'),
                 texto('Las personas cambian el paisaje con <b>cultivos</b>, <b>carreteras</b>, <b>casas</b>, <b>parques</b> y <b>puentes</b>. '
                       'Algunos cambios ayudan y otros dañan la naturaleza.'),
                 imagen('s2-maqueta', 35, 'Una maqueta con plastilina')],
        recuerda=['La meseta es alta y plana.', 'El paisaje cambia por la naturaleza y por las personas.'],
        practica=[unica('Una tierra alta y plana es una…', 'meseta', ['isla', 'llanura baja']),
                  unica('¿Qué cambio hicieron las personas en el valle?', 'Una carretera y casas', ['Las montañas', 'El cielo'])],
        taller=[unica('Una tierra rodeada de agua es una…', 'isla', ['montaña', 'meseta']),
                vf('Las personas pueden cambiar el paisaje.', True),
                abierta('Pregunta a un adulto qué ha cambiado en tu barrio o vereda en los últimos años. Dibuja el antes y el ahora.', 6),
                abierta('Con plastilina o barro haz una maqueta del paisaje de tu municipio. Dibújala aquí.', 6)])

    U[2] = u(
        tema='Me oriento con los puntos cardinales',
        objetivo='Usar los puntos cardinales y la lateralidad para ubicarme en el colegio y dar indicaciones para llegar a un lugar.',
        explora=[imagen('d-escuela', 60), texto('Si estás en el patio, ¿cómo le explicas a un compañero nuevo dónde queda la biblioteca?')],
        aprende=[imagen('d-rosa', 25),
                 texto('Para dar indicaciones uso: <b>adelante</b>, <b>atrás</b>, <b>a la derecha</b>, <b>a la izquierda</b> y los puntos cardinales: '
                       '<b>norte</b>, <b>sur</b>, <b>este</b> y <b>oeste</b>.'),
                 texto('Ejemplo: «Desde el patio, camina hacia el <b>sur</b> y la biblioteca queda a tu <b>derecha</b>, junto a los baños».'),
                 texto('Las distancias se pueden medir con <b>pasos</b>: del salón a la cafetería hay más pasos que del salón al patio. Está más <b>lejos</b>.'),
                 imagen('d-barrio', 55, 'Rutas en el barrio')],
        recuerda=['El sol sale por el este.', 'Para dar indicaciones digo hacia dónde camino y qué hay a los lados.'],
        practica=[imagen('d-escuela', 50), unica('¿Qué lugar está al norte del patio?', 'La coordinación', ['Los baños', 'La entrada']),
                  unica('¿Qué está más cerca del salón de 1.º: el patio o la biblioteca?', 'El patio', ['La biblioteca'])],
        taller=[imagen('d-barrio', 50), unica('Para ir de mi casa a la tienda camino hacia el…', 'sur', ['norte', 'este']),
                unica('Para ir de la tienda a la iglesia camino hacia el…', 'este', ['oeste', 'norte']),
                abierta('Cuenta en pasos la distancia de tu salón a la cafetería y al baño. ¿Cuál está más lejos?', 3),
                abierta('Dibuja la ruta que sigue un compañero para llegar a la escuela y escribe las indicaciones.', 6)])

    U[3] = u(
        tema='La historia de mi familia',
        objetivo='Usar fuentes como el registro civil, las fotos y los relatos para conocer la historia de mi familia y armar mi árbol genealógico.',
        explora=[imagen('s2-album', 45), texto('¿Qué podemos saber de una familia mirando sus fotos antiguas?')],
        aprende=[texto('Las <b>fuentes históricas</b> nos ayudan a conocer el pasado: documentos, fotos, objetos y los <b>relatos</b> de los mayores.'),
                 imagen('s2-registro', 22, 'El registro civil dice cuándo y dónde nací'),
                 texto('El <b>árbol genealógico</b> muestra quiénes son mis abuelos, mis padres y yo.'),
                 imagen('d-arbol', 55),
                 texto('Muchas familias llegaron de otros lugares: por trabajo, por estudio o porque tuvieron que salir de su tierra. '
                       'Preguntar de dónde venimos nos ayuda a entender quiénes somos.')],
        recuerda=['El registro civil es un documento importante: dice cuándo y dónde nací.', 'Los abuelos guardan la memoria de la familia.'],
        practica=[unica('¿Qué documento dice cuándo y dónde nací?', 'El registro civil', ['Un cuaderno', 'Una receta']),
                  unica('¿Quiénes van arriba en el árbol genealógico?', 'Los abuelos', ['Yo', 'Mis hermanos'])],
        taller=[unica('Una foto antigua es una…', 'fuente histórica', ['receta', 'señal de tránsito']),
                vf('Los relatos de los abuelos nos ayudan a conocer la historia de la familia.', True),
                abierta('Llena tu árbol genealógico con los nombres de tu familia.', 6),
                abierta('Pregunta de dónde vinieron tus abuelos y cómo llegaron a tu municipio. Escríbelo.', 5)])

    U[4] = u(
        tema='¿Cómo nos movemos? Los medios de transporte',
        objetivo='Clasificar los medios de transporte de mi municipio y comparar los de antes con los de ahora.',
        explora=[imagen('s2-mula', 20), imagen('s2-chiva', 25), texto('¿Cómo se movían los abuelos? ¿Cómo te mueves tú?')],
        aprende=[tabla([['Por tierra', 'Por agua', 'Por aire'], ['bus, chiva, moto, bicicleta, mula, a pie', 'canoa, lancha, barco', 'avión, cable aéreo']]),
                 imagen('s2-bus', 20), imagen('s2-moto', 18), imagen('s2-bicicleta', 18), imagen('s2-canoa', 20), imagen('s2-metrocable', 25),
                 texto('<b>Antes</b> muchas personas viajaban a pie o en mula por caminos de herradura. <b>Ahora</b> hay carreteras, buses y motos.'),
                 tabla([['Medio', 'Ventaja', 'Desventaja'], ['Bicicleta', 'no contamina y es ejercicio', 'es lenta para distancias largas'],
                        ['Moto', 'es rápida', 'es peligrosa sin casco'], ['Bus', 'lleva a muchas personas', 'hay que esperarlo']])],
        recuerda=['Hay transporte por tierra, por agua y por aire.', 'Los medios de transporte han cambiado con el tiempo.'],
        practica=[unica('La canoa es transporte por…', 'agua', ['tierra', 'aire']),
                  unica('¿Cómo se transportaba antes el café en las montañas?', 'En mula', ['En avión', 'En metro'])],
        taller=[unica('¿Qué medio de transporte no contamina?', 'La bicicleta', ['El bus', 'La moto']),
                unica('La chiva es típica de…', 'los pueblos y el campo', ['el mar', 'el aire']),
                abierta('¿Cómo llegas al colegio? Escribe una ventaja y una desventaja.', 3),
                abierta('Pregunta a tus abuelos cómo viajaban cuando eran niños. Dibújalo.', 6)])

    U[5] = u(
        tema='Los trabajos de mi comunidad',
        objetivo='Conocer los oficios de mi comunidad, cómo ayudan a las familias y por qué los niños no deben trabajar.',
        explora=[imagen('s2-campesino', 20), imagen('s2-panadera', 20), texto('¿En qué trabajan las personas de tu familia?')],
        aprende=[texto('Las personas trabajan para ganar su <b>sustento</b> y el de su familia. Cada oficio es importante para la comunidad.'),
                 imagen('s2-medica', 18, 'Médica'), imagen('s2-pescador', 18, 'Pescador'), imagen('s2-conductor', 18, 'Conductor'),
                 tabla([['En el campo (rural)', 'En la ciudad o el pueblo (urbano)'], ['agricultor, ganadero, pescador, arriero', 'comerciante, conductor, médico, profesor']]),
                 recuadro('Los niños no deben trabajar', '<p>Los niños tienen derecho a <b>estudiar, jugar y descansar</b>. Si un niño trabaja en lugar de ir a la '
                          'escuela, se le vulneran sus derechos. Ayudar en casa con tareas sencillas está bien; trabajar como un adulto, no.</p>', estilo='reto'),
                 imagen('s2-nino-trabajando', 45, 'Este niño debería estar en la escuela')],
        recuerda=['Todos los oficios son importantes.', 'Los niños deben estudiar y jugar, no trabajar.'],
        practica=[unica('¿Quién cultiva los alimentos?', 'El campesino', ['El conductor', 'La médica']),
                  unica('Un niño que carga bultos en vez de estudiar…', 'no está siendo protegido', ['está bien así'])],
        taller=[unica('¿Qué oficio es más común en el campo?', 'Agricultor', ['Conductor de metro']),
                vf('Los niños tienen derecho a estudiar y jugar.', True),
                abierta('Pregunta a un abuelo cómo era su trabajo antes y cómo es hoy. Escribe una diferencia.', 4),
                abierta('Dibuja el trabajo de alguien de tu familia y escribe cómo ayuda a todos.', 6)])

    U[6] = u(
        tema='Viviendas del campo, de la ciudad y de los pueblos étnicos',
        objetivo='Comparar las viviendas rurales y urbanas, y las de los pueblos indígenas y afrocolombianos.',
        explora=[imagen('s2-casa-rural', 35, 'Vivienda rural'), imagen('s1-edificio', 25, 'Vivienda urbana'),
                 texto('¿En qué se parecen y en qué se diferencian estas viviendas?')],
        aprende=[tabla([['Vivienda', 'Materiales', 'Ventajas'], ['Rural', 'tapia, bahareque, madera, teja', 'espacio, huerta, aire limpio'],
                        ['Urbana', 'ladrillo, cemento, vidrio', 'cerca de colegios, hospitales y tiendas']]),
                 texto('Los <b>pueblos indígenas y afrocolombianos</b> construyen según su cultura y su territorio:'),
                 imagen('s2-tambo', 25, 'Tambo emberá'), imagen('s1-maloca', 25, 'Maloca'), imagen('s1-palafito', 25, 'Palafito'),
                 texto('Las viviendas <b>cambian con el tiempo</b>: antes había más casas de bahareque; ahora hay más de ladrillo.')],
        recuerda=['Las viviendas se construyen según el clima, el lugar y la cultura.'],
        practica=[unica('¿Qué vivienda tiene huerta y gallinas, normalmente?', 'La rural', ['La urbana de un edificio']),
                  unica('El tambo es la vivienda de…', 'pueblos indígenas como los emberá', ['las ciudades grandes'])],
        taller=[unica('Una ventaja de vivir en la ciudad es…', 'estar cerca de hospitales y colegios', ['tener mucho espacio para cultivar']),
                unica('¿Con qué material se hace una casa de bahareque?', 'Barro y guadua', ['Vidrio']),
                abierta('Dibuja tu vivienda y escribe de qué materiales está hecha.', 6)])

    U[7] = u(
        tema='Mi municipio: veredas, corregimientos y comunas',
        objetivo='Reconocer cómo se organiza el territorio de mi municipio y ubicar sus partes con los puntos cardinales.',
        explora=[imagen('d-municipio', 60, 'Un municipio de ejemplo'), texto('¿Cómo se llama tu municipio? ¿Vives en el casco urbano o en una vereda?')],
        aprende=[texto('El municipio tiene un <b>casco urbano</b> (el pueblo o la ciudad, dividido en <b>barrios</b> o <b>comunas</b>) y una zona <b>rural</b> '
                       'con <b>veredas</b> y <b>corregimientos</b>. Algunos tienen <b>resguardos indígenas</b> o <b>territorios afrocolombianos</b>.'),
                 texto('Los nombres de los lugares se llaman <b>topónimos</b>: «Vereda El Alto», «Río Recio», «Barrio San José».'),
                 tabla([['Grupo pequeño', 'Grupo grande'], ['familia', 'municipio'], ['salón de clase', 'resguardo'], ['colegio', 'departamento']]),
                 texto('Pregunta a tu profe por el <b>croquis</b> (el dibujo del contorno) de tu municipio y búscalo en el mapa de tu departamento.')],
        recuerda=['El municipio tiene zona urbana y zona rural.', 'Las veredas son parte de la zona rural.'],
        practica=[imagen('d-municipio', 50), unica('¿Qué está al norte del río?', 'El casco urbano', ['La Vereda La Vega', 'El resguardo']),
                  unica('Las veredas están en la zona…', 'rural', ['urbana'])],
        taller=[imagen('d-municipio', 50), unica('¿Qué hay al oeste (izquierda) del casco urbano?', 'La Vereda El Alto', ['El corregimiento', 'El resguardo']),
                unica('Un «topónimo» es…', 'el nombre de un lugar', ['un medio de transporte', 'un oficio']),
                abierta('Escribe el nombre de tu municipio, de tu vereda o barrio y de un río o una montaña cercana.', 3),
                abierta('Dibuja el croquis de tu municipio con ayuda de tu profe.', 6)])

    U[8] = u(
        tema='Todos cabemos: no a la discriminación',
        objetivo='Reconocer y rechazar la exclusión y la discriminación en mi familia, con mis amigos y en el salón.',
        explora=[imagen('s2-excluido', 40), texto('¿Cómo se siente la niña que está sola? ¿Por qué crees que la dejaron por fuera?')],
        aprende=[texto('<b>Discriminar</b> es tratar mal o dejar por fuera a alguien por su color de piel, su edad, su religión, si es niño o niña, '
                       'de dónde viene o cómo habla. Eso <b>duele</b> y <b>no está bien</b>.'),
                 imagen('s2-incluido', 40, 'Cuando todos juegan, todos ganan'),
                 tabla([['Excluye', 'Incluye'], ['«Tú no juegas porque eres diferente»', '«¡Ven, juega con nosotros!»'],
                        ['Burlarse de cómo habla alguien', 'Preguntarle de dónde es y aprender de su región']]),
                 recuadro('Si me discriminan o veo que discriminan a alguien', '<p>Lo cuento a mi profesor, al orientador o a mi familia. '
                          'También existe la Línea 141 del ICBF.</p>', estilo='recuerda')],
        recuerda=['Todos somos diferentes y todos valemos lo mismo.', 'Incluir es invitar, escuchar y respetar.'],
        practica=[unica('¿Qué hacemos si alguien queda solo en el juego?', 'Lo invitamos a jugar', ['Lo ignoramos', 'Nos burlamos']),
                  vf('Dejar por fuera a alguien por su color de piel es discriminar.', True)],
        taller=[unica('¿Cómo se siente alguien a quien discriminan?', 'Triste y solo', ['Feliz']),
                unica('Si veo que discriminan a un compañero, debo…', 'ayudarlo y contarle a un adulto', ['reírme', 'no hacer nada']),
                abierta('Pregunta a tu familia cuál es su comida favorita y compárala con la de tus compañeros. ¿Son iguales?', 4),
                abierta('Escribe lo que más te gusta de tu salón y algo que cambiarías para que todos estén mejor.', 4)])
    return U
