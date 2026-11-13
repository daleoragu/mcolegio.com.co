"""Ciencias Sociales 7.º: una guía y un taller por cada uno de los 8 DBA: representaciones del mundo, población y ciudades,
Roma, Edad Media, Renacimiento, Conquista, derechos y mediación de conflictos. Borradores para que el docente revise."""
from .base import abierta, imagen, recuadro, tabla, texto, unica, unidad, vf


def unidades():
    U = {}

    U[1] = unidad(
        tema='Cómo hemos representado el mundo',
        objetivo='Explicar cómo las representaciones del mundo cambiaron con las visiones de quienes las hacían y con la tecnología.',
        explora=[imagen('s7-mapa-to', 35, 'Mapa medieval de T en O'), texto('¿Por qué crees que este mapa medieval pone a Jerusalén en el centro?')],
        aprende=[texto('En la Edad Media europea, los mapas de <b>T en O</b> mostraban el mundo influenciado por la Biblia: tres continentes (Asia, Europa, África) y Jerusalén en el centro.'),
                 texto('Los viajes de exploradores como <b>Marco Polo</b> y, más tarde, los navegantes portugueses y españoles ampliaron el conocimiento del mundo. La brújula, el astrolabio y la imprenta ayudaron.'),
                 texto('Hoy usamos <b>imágenes de satélite</b>, <b>GPS</b> y <b>fotografías aéreas</b>. Aun así, todo mapa elige qué mostrar: la proyección de Mercator agranda Europa y Norteamérica.')],
        recuerda=['Todo mapa refleja una visión del mundo.'],
        practica=[unica('En los mapas de T en O, el centro era…', 'Jerusalén', ['Roma', 'Londres']), unica('¿Qué tecnología actual usamos para mapas?', 'Imágenes de satélite', ['Mapas de T en O'])],
        taller=[unica('La proyección de Mercator…', 'agranda las zonas cercanas a los polos', ['muestra el tamaño real']),
                abierta('Dibuja el mapa de tu barrio o vereda tal como lo ves tú y compáralo con Google Maps. ¿Qué cambia?', 6)])

    U[2] = unidad(
        tema='Población y ciudades',
        objetivo='Interpretar la relación entre el crecimiento de la población, el desarrollo urbano y los problemas sociales.',
        explora=[texto('¿Tu municipio ha crecido en los últimos años? ¿Qué problemas trae ese crecimiento?')],
        aprende=[tabla([['Concepto', 'Significado'], ['Crecimiento urbano', 'aumento de población y área de una ciudad'], ['Conurbación', 'unión física de ciudades vecinas'],
                        ['Área metropolitana', 'municipios unidos a una gran ciudad que comparten servicios (el Valle de Aburrá)'], ['Periferia', 'zonas en el borde de la ciudad']]),
                 texto('El crecimiento sin planeación concentra en ciertas zonas la <b>pobreza</b>, la <b>falta de servicios</b>, la <b>contaminación</b> y la <b>inseguridad</b>. '
                       'Los planes de ordenamiento territorial (POT) buscan organizarlo.')],
        recuerda=['El POT organiza el uso del suelo en el municipio.'],
        practica=[unica('La unión física de ciudades vecinas se llama…', 'conurbación', ['periferia']), unica('El POT sirve para…', 'planear el uso del suelo', ['cobrar impuestos'])],
        taller=[unica('El Valle de Aburrá es un ejemplo de…', 'área metropolitana', ['zona rural']),
                abierta('Ubica en un mapa de tu municipio dónde hay más problemas sociales y explica por qué crees que ocurre.', 8)])

    U[3] = unidad(
        tema='El legado de Roma',
        objetivo='Reconocer el Imperio romano como sistema político, militar y económico y describir su legado en Occidente.',
        explora=[imagen('s7-acueducto', 40, 'Acueducto romano'), texto('¿Qué obra moderna se parece a este acueducto? ¿Para qué servía?')],
        aprende=[texto('Roma pasó de <b>monarquía</b> a <b>república</b> (con Senado) y luego a <b>imperio</b>, que dominó el Mediterráneo con su ejército y su red de caminos.'),
                 tabla([['Campo', 'Legado'], ['Lengua', 'el latín, origen del español'], ['Derecho', 'el derecho romano, base de nuestras leyes'], ['Ingeniería', 'acueductos, puentes, caminos'],
                        ['Política', 'la república, el Senado'], ['Vida cotidiana', 'calendario, baños públicos, numeración romana']]),
                 texto('El Imperio de Occidente cayó en el año <b>476</b> d. C.')],
        recuerda=['El español viene del latín.', 'Nuestro derecho tiene raíces romanas.'],
        practica=[unica('¿Qué lengua dio origen al español?', 'El latín', ['El griego', 'El árabe']), unica('El Imperio romano de Occidente cayó en…', '476 d. C.', ['1492', '1810'])],
        taller=[unica('Los romanos construyeron acueductos para…', 'llevar agua a las ciudades', ['defenderse']), vf('El Senado es una institución de origen romano.', True),
                abierta('Busca 5 palabras del español que vengan del latín y su significado original.', 5)])

    U[4] = unidad(
        tema='La Edad Media en Europa y América',
        objetivo='Analizar la Edad Media europea y compararla con las sociedades precolombinas del mismo período.',
        explora=[texto('Hacia el año 1000, ¿cómo vivía un campesino en Europa y cómo un agricultor maya o muisca?')],
        aprende=[texto('Europa medieval (siglos V–XV): <b>feudalismo</b> (señores dueños de la tierra, siervos que la trabajaban), poder de la <b>Iglesia</b>, castillos, cruzadas.'),
                 tabla([['Ciudad hacia el año 1000', 'Región', 'Rasgos'], ['París', 'Europa', 'ciudad medieval amurallada'], ['Tikal', 'Centroamérica (maya)', 'templos-pirámide, plazas'],
                        ['Damasco', 'Asia', 'centro comercial islámico'], ['El Cairo', 'África', 'capital islámica, mezquitas']]),
                 texto('En América, los mayas vivían su período clásico y posclásico, y en Colombia los muiscas y taironas tenían sociedades organizadas con caciques y comercio.')],
        recuerda=['Feudalismo: señores y siervos.', 'Mientras en Europa había castillos, en América había ciudades mayas.'],
        practica=[unica('En el feudalismo, la tierra era de…', 'los señores feudales', ['los siervos']), unica('Tikal fue una ciudad…', 'maya', ['romana'])],
        taller=[unica('La institución más poderosa en la Europa medieval fue…', 'la Iglesia', ['el parlamento']),
                abierta('Compara la vida de un siervo medieval con la de un muisca del mismo tiempo.', 6)])

    U[5] = unidad(
        tema='El Renacimiento',
        objetivo='Analizar el Renacimiento como una nueva forma de pensar en las ciencias, la política, las artes y la literatura.',
        explora=[texto('¿Por qué crees que una época se llama «Renacimiento»? ¿Qué «renació»?')],
        aprende=[texto('Entre los siglos XV y XVI, en ciudades italianas como <b>Florencia</b> y <b>Venecia</b>, renació el interés por la cultura griega y romana. El <b>humanismo</b> puso al ser humano en el centro.'),
                 tabla([['Campo', 'Figura', 'Aporte'], ['Arte', 'Leonardo da Vinci, Miguel Ángel', 'perspectiva, anatomía, la Capilla Sixtina'], ['Ciencia', 'Copérnico, Galileo', 'la Tierra gira alrededor del Sol'],
                        ['Política', 'Maquiavelo', '«El príncipe»'], ['Técnica', 'Gutenberg', 'imprenta de tipos móviles']]),
                 texto('La <b>Reforma protestante</b> (Lutero, 1517) dividió la Iglesia en Europa y cambió la política de América y Europa.')],
        recuerda=['Humanismo: el ser humano en el centro.', 'La imprenta difundió el conocimiento.'],
        practica=[unica('¿Quién propuso que la Tierra gira alrededor del Sol?', 'Copérnico', ['Maquiavelo']), unica('La imprenta de tipos móviles se atribuye a…', 'Gutenberg', ['Leonardo'])],
        taller=[unica('El Renacimiento nació en…', 'Italia', ['Inglaterra']), vf('La Reforma protestante empezó con Lutero.', True),
                abierta('Elige una obra de arte del Renacimiento y describe qué muestra de la vida de su época.', 6)])

    U[6] = unidad(
        tema='Conquista y colonización de América',
        objetivo='Evaluar las causas y consecuencias de la Conquista y la colonización europea en América.',
        explora=[texto('¿Por qué los europeos llegaron a América en 1492? ¿Qué consecuencias tuvo para los pueblos que ya vivían aquí?')],
        aprende=[tabla([['Causas', 'Consecuencias'], ['búsqueda de rutas comerciales y metales preciosos', 'muerte de gran parte de la población indígena (guerras, enfermedades, trabajo forzado)'],
                        ['expansión del cristianismo', 'esclavización de millones de africanos traídos a América'], ['avances en navegación', 'mestizaje e intercambio de plantas, animales y culturas']]),
                 texto('España, Portugal, Inglaterra, Francia y Holanda colonizaron América con formas distintas. En el territorio colombiano se fundaron ciudades como Santa Marta (1525), Cartagena (1533) y Santafé (1538).'),
                 texto('Muchas instituciones coloniales (la desigualdad en la tierra, el centralismo) dejaron huellas que todavía se discuten.')],
        recuerda=['La Conquista tuvo consecuencias profundas y desiguales.'],
        practica=[unica('¿En qué año llegó Colón a América?', '1492', ['1810', '1538']), unica('¿Qué ciudad colombiana se fundó en 1533?', 'Cartagena', ['Santa Marta', 'Santafé'])],
        taller=[unica('Una causa principal de la muerte de indígenas fue…', 'las enfermedades traídas de Europa', ['el clima']),
                abierta('Explica una continuidad entre la época colonial y la Colombia de hoy.', 6)])

    U[7] = unidad(
        tema='Una sociedad que protege los derechos',
        objetivo='Comparar la Declaración Universal de los Derechos Humanos con la Constitución y proponer soluciones a la discriminación.',
        explora=[texto('¿Qué pasa cuando un Estado no protege los derechos de sus ciudadanos? ¿Quién debe evitarlo?')],
        aprende=[tabla([['Declaración Universal (1948)', 'Constitución de 1991'], ['art. 3: derecho a la vida y a la libertad', 'art. 11: el derecho a la vida es inviolable'],
                        ['art. 7: igualdad ante la ley', 'art. 13: igualdad y no discriminación'], ['art. 19: libertad de opinión y expresión', 'art. 20: libertad de expresión']]),
                 texto('Una sociedad democrática tiene la <b>responsabilidad</b> de prevenir la violación de derechos: con leyes, instituciones (Defensoría, Personería, jueces) y ciudadanos que denuncian.')],
        recuerda=['La Constitución recoge los derechos de la Declaración Universal.'],
        practica=[unica('La Declaración Universal de los Derechos Humanos es de…', '1948', ['1991', '1810']), unica('El artículo 13 de la Constitución trata de…', 'igualdad', ['propiedad'])],
        taller=[abierta('Elige un caso de discriminación en Colombia (por noticias) y propón dos soluciones.', 8)])

    U[8] = unidad(
        tema='Mediación de conflictos y cultura de paz',
        objetivo='Aplicar técnicas de mediación de conflictos y reconocer los distintos puntos de vista para construir paz.',
        explora=[texto('Dos compañeros discuten porque uno publicó una foto del otro sin permiso. ¿Cómo los ayudarías?')],
        aprende=[tabla([['Paso de la mediación', 'Qué hace el mediador'], ['1. Presentación', 'explica las reglas: respeto, turnos, confidencialidad'], ['2. Cuéntame', 'cada parte narra su versión sin interrupción'],
                        ['3. Ubicarnos', 'identifica intereses y sentimientos de cada uno'], ['4. Arreglar', 'las partes proponen soluciones'], ['5. Acuerdo', 'se escribe y se firma un compromiso']]),
                 texto('El conflicto es normal; la <b>violencia</b> no. Mediar no es juzgar: el mediador ayuda a que las partes encuentren su propia solución.'),
                 recuadro('Ley 1620 de 2013', '<p>Crea el sistema de convivencia escolar: cada colegio tiene un comité de convivencia y rutas de atención.</p>', estilo='recuerda')]
        ,
        recuerda=['Escuchar ambas versiones es el primer paso.'],
        practica=[unica('El mediador…', 'ayuda a que las partes lleguen a un acuerdo', ['decide quién tiene la culpa']),
                  unica('¿Qué ley creó el sistema de convivencia escolar?', 'La 1620 de 2013', ['La 100 de 1993'])],
        taller=[vf('Todo conflicto debe terminar en violencia.', False), abierta('Representen con un compañero una mediación del caso de la foto y escriban el acuerdo final.', 8)])
    return U
