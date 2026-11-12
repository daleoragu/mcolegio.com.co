"""Ciencias Sociales 6.º: una guía y un taller por cada uno de los 8 DBA: universo, Tierra, prehistoria, primeras
civilizaciones, sociedades prehispánicas, formas de gobierno, ciudadanía y no discriminación. Borradores para revisar."""
from .base import abierta, imagen, recuadro, tabla, texto, unica, unidad, vf


def unidades():
    U = {}

    U[1] = unidad(
        tema='El origen del universo y el sistema solar',
        objetivo='Interpretar teorías científicas sobre el origen del universo y describir los componentes del sistema solar.',
        explora=[imagen('s6-sistema-solar', 60), texto('¿Qué hay más allá de la Tierra? ¿Cómo crees que empezó todo?')],
        aprende=[texto('La teoría más aceptada es el <b>Big Bang</b>: hace unos <b>13 800 millones de años</b> el universo empezó a expandirse desde un estado muy denso y caliente. '
                       'La teoría <b>inflacionaria</b> propone una expansión rapidísima en el primer instante; la idea del <b>multiverso</b> plantea que podrían existir otros universos (aún sin comprobar).'),
                 tabla([['Componente', 'Descripción'], ['Sol', 'estrella en el centro del sistema'], ['Planetas', 'Mercurio, Venus, Tierra, Marte, Júpiter, Saturno, Urano, Neptuno'],
                        ['Satélites', 'giran alrededor de planetas (la Luna)'], ['Asteroides', 'rocas, sobre todo entre Marte y Júpiter'], ['Cometas', 'hielo y polvo con cola al acercarse al Sol']]),
                 texto('Los pueblos también explicaron el origen con <b>mitos</b> (como Bachué para los muiscas); la ciencia lo explica con evidencias.')],
        recuerda=['Big Bang: hace unos 13 800 millones de años.', 'Ocho planetas giran alrededor del Sol.'],
        practica=[unica('¿Cuál es el planeta más cercano al Sol?', 'Mercurio', ['Venus', 'Marte']), unica('¿Qué son los cometas?', 'Cuerpos de hielo y polvo', ['Estrellas apagadas'])],
        taller=[unica('El cinturón de asteroides está entre…', 'Marte y Júpiter', ['la Tierra y Marte']), unica('¿Cuál es el planeta más grande?', 'Júpiter', ['Saturno', 'la Tierra']),
                vf('El Sol es una estrella.', True), abierta('Haz una línea con escala de las distancias de los planetas al Sol (1 cm = 50 millones de km).', 6)])

    U[2] = unidad(
        tema='La Tierra cambia: relieve, clima y placas',
        objetivo='Explicar la deriva continental y la dinámica interna de la Tierra, y la relación entre el relieve, el clima y la vida.',
        explora=[texto('¿Por qué la costa de Suramérica y la de África parecen encajar como piezas de rompecabezas?')],
        aprende=[texto('Alfred <b>Wegener</b> propuso la <b>deriva continental</b>: hace unos 200 millones de años los continentes formaban uno solo, <b>Pangea</b>. La <b>tectónica de placas</b> explica que la '
                       'corteza está dividida en placas que se mueven sobre el manto.'),
                 texto('Cuando las placas chocan se forman <b>cordilleras</b> (los Andes), <b>volcanes</b> y <b>sismos</b>. Colombia está donde se encuentran las placas de Nazca, Suramericana y Caribe: '
                       'por eso tiene volcanes como el Nevado del Ruiz y temblores frecuentes.'),
                 tabla([['Zona', 'Temperatura', 'Vida'], ['Ecuatorial', 'cálida todo el año', 'selvas, gran biodiversidad'], ['Templadas', 'cuatro estaciones', 'bosques, praderas'], ['Polares', 'muy fría', 'poca vegetación']])],
        recuerda=['Los continentes se mueven unos centímetros al año.', 'Colombia está en una zona sísmica y volcánica.'],
        practica=[unica('El supercontinente antiguo se llamó…', 'Pangea', ['Atlántida', 'Gondwana-Andes']), unica('Las cordilleras se forman cuando…', 'chocan placas tectónicas', ['llueve mucho'])],
        taller=[unica('¿Qué volcán colombiano está en la cordillera Central?', 'Nevado del Ruiz', ['Sierra Nevada de Santa Marta']),
                vf('Colombia está en una zona de contacto entre placas.', True), abierta('Investiga el plan de evacuación de tu colegio en caso de sismo y descríbelo.', 6)])

    U[3] = unidad(
        tema='La hominización y la prehistoria',
        objetivo='Diferenciar las especies de homínidos y relacionar sus avances tecnológicos con las transformaciones del entorno.',
        explora=[imagen('s6-hominidos', 55), texto('¿Qué cambios ves de una figura a otra?')],
        aprende=[tabla([['Especie', 'Época aprox.', 'Rasgos', 'Tecnología'], ['Australopithecus', 'hace 4–2 millones de años', 'bípedo, cerebro pequeño', 'quizá piedras sin tallar'],
                        ['Homo habilis', 'hace 2,4–1,4 millones de años', 'cerebro más grande', 'primeras herramientas de piedra'],
                        ['Homo erectus', 'hace 1,9 millones – 110 000 años', 'cuerpo alto, migró fuera de África', 'hachas de mano, fuego'],
                        ['Homo sapiens', 'desde hace unos 300 000 años', 'cerebro grande, lenguaje complejo', 'arte rupestre, agujas, arcos']]),
                 texto('La <b>prehistoria</b> se divide en <b>Paleolítico</b> (piedra tallada, cazadores-recolectores nómadas), <b>Neolítico</b> (piedra pulida, agricultura, sedentarismo) y <b>Edad de los Metales</b>.'),
                 texto('En Colombia, los sitios de <b>El Abra</b> y <b>Tibitó</b> (Cundinamarca) muestran presencia humana desde hace más de 12 000 años, y Chiribiquete guarda arte rupestre muy antiguo.')],
        recuerda=['Paleolítico: nómadas. Neolítico: agricultura y sedentarismo.'],
        practica=[unica('¿Qué especie dominó el fuego?', 'Homo erectus', ['Australopithecus']), unica('En el Neolítico apareció…', 'la agricultura', ['la escritura alfabética'])],
        taller=[unica('Los cazadores-recolectores eran…', 'nómadas', ['sedentarios']), unica('Las pinturas en piedra se llaman…', 'arte rupestre', ['frescos']),
                abierta('Explica cómo cambió la vida humana con la agricultura.', 6)])

    U[4] = unidad(
        tema='Las primeras ciudades y los ríos',
        objetivo='Explicar cómo la agricultura, el comercio y los ríos permitieron el surgimiento de las primeras ciudades.',
        explora=[imagen('s6-rios-civilizaciones', 60, 'Ríos de las primeras civilizaciones'), texto('¿Por qué crees que las primeras ciudades nacieron junto a grandes ríos?')],
        aprende=[tabla([['Civilización', 'Río', 'Legado'], ['Mesopotamia', 'Tigris y Éufrates', 'escritura cuneiforme, Código de Hammurabi'], ['Egipto', 'Nilo', 'pirámides, jeroglíficos, calendario'],
                        ['India', 'Indo y Ganges', 'ciudades planificadas (Mohenjo-Daro), sistema decimal'], ['China', 'Huang He (Amarillo) y Yangtsé', 'papel, seda, brújula']]),
                 texto('Los ríos daban agua para <b>riego</b>, suelos fértiles por las crecientes y vías de <b>comercio</b>. Con los excedentes de comida surgieron la <b>división del trabajo</b>, '
                       'la <b>escritura</b> (para llevar cuentas) y el <b>Estado</b>.')],
        recuerda=['Agricultura + excedentes + comercio = ciudades.'],
        practica=[unica('La escritura cuneiforme nació en…', 'Mesopotamia', ['Egipto', 'China']), unica('El río de Egipto es el…', 'Nilo', ['Ganges'])],
        taller=[unica('El papel fue inventado en…', 'China', ['Mesopotamia']), vf('Los ríos fueron vías de comercio.', True),
                abierta('Compara una ciudad antigua con tu municipio: ¿qué río o fuente de agua lo abastece?', 6)])

    U[5] = unidad(
        tema='Legados de las sociedades prehispánicas de América',
        objetivo='Ubicar y analizar los aportes de mayas, aztecas, incas, muiscas y otros pueblos ancestrales.',
        explora=[texto('¿Qué alimentos de tu mesa existían en América antes de la llegada de los europeos?')],
        aprende=[tabla([['Pueblo', 'Ubicación', 'Aportes'], ['Mayas', 'sur de México y Centroamérica', 'calendario, el cero, escritura, astronomía'],
                        ['Aztecas (mexicas)', 'centro de México', 'Tenochtitlan, chinampas (cultivos flotantes)'], ['Incas', 'Andes (Perú)', 'caminos (Qhapaq Ñan), terrazas, quipus'],
                        ['Muiscas', 'altiplano cundiboyacense', 'orfebrería, comercio de sal y esmeraldas']]),
                 texto('América aportó al mundo el <b>maíz</b>, la <b>papa</b>, el <b>tomate</b>, el <b>cacao</b> y el <b>aguacate</b>, que hoy están en las cocinas de todo el planeta.')],
        recuerda=['Los mayas usaban el cero.', 'Papa, maíz y tomate son herencia americana.'],
        practica=[unica('El sistema de caminos de los incas se llama…', 'Qhapaq Ñan', ['chinampa']), unica('Los mayas desarrollaron…', 'un calendario preciso', ['la pólvora'])],
        taller=[unica('Las chinampas eran de los…', 'aztecas', ['incas']), unica('¿Qué alimento es originario de América?', 'El cacao', ['El trigo', 'El arroz']),
                abierta('Compara la organización social de los muiscas con la de tu comunidad actual.', 6)])

    U[6] = unidad(
        tema='Formas de gobierno de ayer y de hoy',
        objetivo='Comparar las formas de gobierno de la antigüedad con el ejercicio del poder en el mundo contemporáneo.',
        explora=[texto('¿Quién debería mandar: uno solo, unos pocos o todos? ¿Por qué?')],
        aprende=[tabla([['Forma', 'Quién gobierna', 'Ejemplo'], ['Monarquía', 'un rey', 'Egipto de los faraones'], ['Tiranía', 'uno que toma el poder por la fuerza', 'algunas ciudades griegas'],
                        ['Aristocracia', 'los «mejores» o nobles', 'Esparta'], ['Democracia ateniense', 'los ciudadanos (solo hombres libres)', 'Atenas, siglo V a. C.'],
                        ['Absolutismo', 'rey con poder total', 'Luis XIV de Francia'], ['Democracia participativa', 'el pueblo, por voto y participación', 'Colombia desde 1991']]),
                 texto('La democracia de Atenas era <b>directa</b> pero excluía a mujeres, esclavos y extranjeros. Hoy la democracia busca incluir a todos.')],
        recuerda=['Monarquía, aristocracia, democracia.', 'La democracia ateniense excluía a muchos.'],
        practica=[unica('El gobierno de un rey con poder total es…', 'absolutismo', ['democracia']), unica('¿Quiénes no votaban en Atenas?', 'Mujeres, esclavos y extranjeros', ['Los hombres libres'])],
        taller=[unica('Colombia es una democracia…', 'participativa', ['absolutista']), vf('En la democracia ateniense votaban todas las personas.', False),
                abierta('Organiza una «asamblea ateniense» en el salón para decidir algo y luego compárala con una votación de todos.', 6)])

    U[7] = unidad(
        tema='Ciudadanía y participación',
        objetivo='Explicar el origen y los cambios de la ciudadanía y la importancia de participar en las decisiones colectivas.',
        explora=[texto('¿Ser ciudadano es solo votar a los 18 años? ¿Qué puedes hacer tú desde ya?')],
        aprende=[texto('La ciudadanía nació en Grecia y Roma, pero era para pocos. Con las revoluciones y las luchas sociales se amplió: hoy en Colombia son ciudadanos todos los nacionales mayores de 18 años, '
                       'y los niños y jóvenes también participan.'),
                 texto('En democracia hay <b>intereses diferentes</b> (empresarios, campesinos, trabajadores, ambientalistas). Los ciudadanos los dirimen con el voto, el diálogo y la participación.'),
                 texto('Mecanismos: voto, consulta popular, cabildo abierto, tutela, derecho de petición; en el colegio: gobierno escolar.')],
        recuerda=['Participar es más que votar.'],
        practica=[unica('¿Desde qué edad se vota en Colombia?', '18 años', ['14 años', '21 años']), unica('Un mecanismo de participación es…', 'el cabildo abierto', ['el castigo'])],
        taller=[unica('En el colegio participo a través del…', 'gobierno escolar', ['comité de compras']),
                abierta('Identifica un problema de tu comunidad, los intereses en juego y una forma democrática de resolverlo.', 8)])

    U[8] = unidad(
        tema='Iguales en dignidad: no a la discriminación',
        objetivo='Argumentar que en una democracia no es aceptable la discriminación por origen étnico, creencias, género, discapacidad o apariencia.',
        explora=[texto('¿Has visto a alguien ser tratado distinto por su color de piel, su acento o su forma de vestir? ¿Cómo se sintió?')],
        aprende=[recuadro('Declaración Universal de los Derechos Humanos, art. 1', '<p>«Todos los seres humanos nacen libres e iguales en dignidad y derechos…»</p>', estilo='nota'),
                 texto('La Constitución (art. 13) dice que todas las personas son iguales ante la ley y prohíbe la discriminación. La <b>Ley 1482 de 2011</b> sanciona los actos de discriminación.'),
                 texto('<b>Igualdad</b> no es que todos seamos idénticos: es que, siendo diferentes, tenemos los mismos derechos. A veces se necesitan <b>acciones afirmativas</b> (rampas, cupos) para lograrla.')],
        recuerda=['Iguales en derechos, diversos en identidad.'],
        practica=[unica('El artículo 13 de la Constitución trata sobre…', 'la igualdad', ['el voto']), unica('Una rampa para silla de ruedas es…', 'una acción afirmativa', ['un privilegio injusto'])],
        taller=[vf('Discriminar a alguien por su apariencia es aceptable si es en broma.', False),
                abierta('Propón una campaña en tu colegio contra un tipo de discriminación que hayas observado.', 8)])
    return U
