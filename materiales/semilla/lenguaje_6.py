"""Lenguaje 6.º: una guía y un taller por cada uno de los 8 DBA. Textos originales de mcolegio (coplas, refranes, un relato
corto). Borradores para que el docente revise."""
from .base import abierta, recuadro, tabla, texto, unica, unidad, vf


def _escribe(enunciado, renglones=6):
    return abierta(enunciado, renglones, puntos=2)


def unidades():
    U = {}

    U[1] = unidad(
        tema='Los medios y la visión del mundo',
        objetivo='Interpretar los mensajes de los medios teniendo en cuenta quién habla, a quién, con qué intención y en qué contexto, para participar en mi entorno.',
        explora=[texto('Compara cómo dos medios distintos (un canal nacional y una emisora local) cuentan la misma noticia. ¿Qué destaca cada uno?')],
        aprende=[texto('Todo mensaje de los medios tiene un <b>emisor</b> con una <b>visión del mundo</b>, un <b>público</b> al que se dirige, una <b>intención</b> (informar, entretener, convencer, vender) '
                       'y un <b>contexto</b> de producción.'),
                 tabla([['Pregunta', 'Para qué me sirve'], ['¿Quién lo dice?', 'saber desde qué lugar habla'], ['¿A quién se dirige?', 'entender el lenguaje que usa'],
                        ['¿Para qué?', 'reconocer si informa u opina'], ['¿Qué omite?', 'detectar lo que no se cuenta']]),
                 texto('Participo en mi entorno cuando uso esa información para opinar en el periódico escolar, en la emisora o en el consejo estudiantil.')],
        recuerda=['Ningún medio es completamente neutral.', 'Comparo fuentes antes de formar mi opinión.'],
        practica=[unica('Un comercial de televisión tiene la intención principal de…', 'vender', ['informar con imparcialidad']),
                  unica('Preguntar «¿qué omite esta noticia?» me ayuda a…', 'leer críticamente', ['leer más rápido'])],
        taller=[unica('Una emisora local suele dirigirse a…', 'la comunidad de la región', ['todo el mundo']),
                vf('Todos los medios cuentan las noticias desde la misma visión del mundo.', False),
                _escribe('Escribe para el periódico escolar una nota de opinión sobre una noticia de tu municipio.', 10)])

    U[2] = unidad(
        tema='Organizadores gráficos',
        objetivo='Crear mapas conceptuales, cuadros sinópticos y líneas de tiempo que integren palabras, símbolos e imágenes para procesar y exponer información.',
        explora=[texto('Cuando estudias, ¿subrayas, haces resúmenes, esquemas o dibujos? ¿Qué te funciona mejor?')],
        aprende=[tabla([['Organizador', 'Sirve para'], ['Mapa conceptual', 'relacionar conceptos con palabras de enlace'], ['Cuadro sinóptico', 'clasificar de lo general a lo particular'],
                        ['Línea de tiempo', 'ordenar hechos en el tiempo'], ['Cuadro comparativo', 'ver semejanzas y diferencias'], ['Mapa mental', 'generar ideas alrededor de un tema']]),
                 texto('Un buen organizador usa pocas palabras, conectores claros (es, tiene, se divide en, produce) y símbolos o imágenes que ayuden a recordar.'),
                 texto('Ejemplo de mapa conceptual: <b>Seres vivos</b> → <i>se clasifican en</i> → <b>plantas</b> y <b>animales</b> → <i>los animales pueden ser</i> → '
                       '<b>vertebrados</b> e <b>invertebrados</b>.')],
        recuerda=['Escojo el organizador según lo que quiero mostrar.', 'Pocas palabras, bien conectadas.'],
        practica=[unica('Para ordenar hechos históricos uso…', 'una línea de tiempo', ['un mapa mental']),
                  unica('Para comparar dos animales uso…', 'un cuadro comparativo', ['una línea de tiempo'])],
        taller=[unica('En un mapa conceptual, «se clasifican en» es…', 'una palabra de enlace', ['un concepto']),
                _escribe('Haz en tu cuaderno un mapa conceptual de un tema de Ciencias y escribe aquí sus conceptos principales.', 6),
                abierta('Expón a tus compañeros un tema usando un organizador gráfico en una cartelera.', 4)])

    U[3] = unidad(
        tema='La literatura: conocimiento e imaginación',
        objetivo='Reconocer que las obras literarias circulan conocimientos de su cultura y su época, e interpretar sus temas para crear nuevos textos.',
        explora=[texto('¿Qué puedes aprender de una época leyendo un cuento escrito en ella? Piensa en «La María» de Jorge Isaacs o en los cuentos de Rafael Pombo.')],
        aprende=[texto('Las obras literarias nacen en un <b>contexto cultural e histórico</b>: muestran cómo se vivía, qué se pensaba y qué preocupaba. «La María» (1867) retrata la '
                       'vida en una hacienda del Valle del Cauca en el siglo XIX; las fábulas de Rafael Pombo enseñaban valores a los niños de su época.'),
                 texto('Leer literatura también desarrolla la <b>imaginación</b>: entramos a mundos posibles y vemos la realidad con otros ojos.'),
                 texto('A partir de los temas de una obra puedo <b>crear nuevos textos</b>: continuar la historia, contarla desde otro personaje o trasladarla a mi época.')],
        recuerda=['Toda obra tiene un contexto.', 'Leer me permite imaginar y crear.'],
        practica=[unica('«La María» refleja la vida en…', 'una hacienda del Valle del Cauca en el siglo XIX', ['una ciudad moderna']),
                  unica('Contar una historia desde otro personaje es…', 'crear un nuevo texto', ['copiar la obra'])],
        taller=[unica('¿Quién escribió fábulas como «El renacuajo paseador»?', 'Rafael Pombo', ['Gabriel García Márquez', 'Jorge Isaacs']),
                _escribe('Reescribe un cuento que conozcas trasladándolo a tu barrio o vereda en la actualidad.', 12)])

    U[4] = unidad(
        tema='Las regiones en la literatura',
        objetivo='Identificar expresiones de distintas regiones en las obras literarias y comprender su sentido.',
        explora=[texto('¿Qué palabras o expresiones usan en tu región que en otras no entienden? Por ejemplo: «¡qué pena!», «chévere», «ajá», «parce», «mijo».')],
        aprende=[texto('La literatura recrea la <b>cultura de las regiones</b>: su forma de hablar, sus comidas, sus paisajes y sus creencias.'),
                 tabla([['Región', 'Expresión', 'Significado'], ['Caribe', '«¡Ajá!, ¿y qué?»', 'saludo o muletilla para iniciar conversación'], ['Antioquia', '«¡Pues, claro!»', 'afirmación enfática'],
                        ['Pacífico', '«Ve, ¿y vos qué?»', 'llamar la atención del otro'], ['Llanos', '«Compadre»', 'trato de confianza']]),
                 texto('Gabriel García Márquez llenó sus novelas del habla y las creencias del Caribe; Tomás Carrasquilla, del habla antioqueña.')],
        recuerda=['Las expresiones regionales dan identidad a los textos.', 'El contexto ayuda a entender su sentido.'],
        practica=[unica('Las novelas de García Márquez recrean sobre todo la cultura…', 'del Caribe', ['de los Llanos']),
                  unica('Las expresiones regionales en un texto sirven para…', 'dar identidad a los personajes y al lugar', ['confundir al lector'])],
        taller=[_escribe('Escribe un diálogo corto entre dos personajes de tu región usando expresiones propias.', 8),
                abierta('Recopila 5 expresiones de tu región con su significado.', 5)])

    U[5] = unidad(
        tema='Coplas, trovas y refranes',
        objetivo='Interpretar coplas, trovas y refranes de la tradición popular y distinguir su sentido literal del figurado.',
        explora=[texto('¿Conoces algún refrán? «Camarón que se duerme se lo lleva la corriente.» ¿Qué quiere decir?')],
        aprende=[recuadro('Copla', '<p>Del Tolima traigo coplas<br>y del Huila traigo el son;<br>cada verso que les canto<br>me lo dicta el corazón.</p>', estilo='nota'),
                 texto('La <b>copla</b> es una estrofa de cuatro versos, con rima en el segundo y el cuarto. La <b>trova</b> es una copla improvisada en un duelo de ingenio (muy popular en Antioquia).'),
                 tabla([['Refrán', 'Sentido literal', 'Sentido figurado'], ['Camarón que se duerme se lo lleva la corriente', 'un camarón dormido es arrastrado', 'el que se descuida pierde oportunidades'],
                        ['Más vale pájaro en mano que cien volando', 'tener un pájaro es mejor que verlos volar', 'mejor algo seguro que mucho incierto']])],
        recuerda=['Copla: 4 versos, rima en 2.º y 4.º.', 'Los refranes enseñan con sentido figurado.'],
        practica=[unica('En la copla, ¿qué versos riman?', 'El segundo y el cuarto (son / corazón)', ['El primero y el tercero']),
                  unica('«Más vale pájaro en mano…» aconseja…', 'preferir lo seguro', ['cazar pájaros'])],
        taller=[unica('La trova es…', 'una copla improvisada', ['una novela']), vf('Los refranes se entienden solo en sentido literal.', False),
                _escribe('Escribe una copla sobre tu municipio (4 versos, rima en el 2.º y el 4.º).', 4),
                abierta('Pregunta en tu familia 3 refranes y explica su sentido figurado.', 6)])

    U[6] = unidad(
        tema='Tipos de texto y su estructura',
        objetivo='Inferir la intención de los textos (narrar, informar, exponer, argumentar, describir) y reconocer cómo se organizan sus párrafos.',
        explora=[texto('Lee el primer párrafo de una noticia, de un cuento y de una receta. ¿Cómo sabes qué tipo de texto es cada uno?')],
        aprende=[tabla([['Intención', 'Tipo', 'Rasgos'], ['narrar', 'narrativo', 'personajes, acciones en el tiempo'], ['informar', 'informativo', 'hechos, datos, fuentes'],
                        ['exponer', 'expositivo', 'explica un tema, definiciones, ejemplos'], ['argumentar', 'argumentativo', 'tesis y razones'], ['describir', 'descriptivo', 'cómo es algo, adjetivos']]),
                 texto('Un texto es un conjunto de <b>párrafos</b>. Cada párrafo tiene una <b>idea principal</b> y las demás ideas la apoyan. Los párrafos se relacionan entre sí por conectores: '
                       '<i>además, en cambio, por ejemplo, en conclusión</i>.')],
        recuerda=['Identifico la intención para entender el texto.', 'Cada párrafo desarrolla una idea principal.'],
        practica=[unica('Un texto que defiende una postura con razones es…', 'argumentativo', ['descriptivo', 'narrativo']),
                  unica('«En conclusión» introduce…', 'el cierre', ['un ejemplo', 'una contradicción'])],
        taller=[unica('Una enciclopedia que explica qué es un volcán es un texto…', 'expositivo', ['narrativo']),
                _escribe('Escribe un párrafo argumentativo con tesis y dos razones sobre el uso del uniforme.', 8)])

    U[7] = unidad(
        tema='Discursos orales adecuados al contexto',
        objetivo='Producir discursos orales adecuados al público, la intención y el tema, seleccionando bien las ideas.',
        explora=[texto('No hablas igual en la izada de bandera que con tus amigos. ¿Qué cambia?')],
        aprende=[texto('Antes de hablar analizo: <b>¿quién es mi público?</b> (edad, conocimientos), <b>¿cuál es mi intención?</b> (informar, convencer, entretener) y '
                       '<b>¿qué tan formal es la situación?</b>'),
                 tabla([['Situación', 'Registro'], ['Discurso en la izada de bandera', 'formal'], ['Conversación en el recreo', 'informal'], ['Exposición en clase', 'formal, claro y ordenado']]),
                 texto('Selecciono solo las ideas que sirven a mi propósito y las ordeno: apertura, desarrollo con ejemplos y cierre.')],
        recuerda=['Adapto mi registro al público y a la situación.'],
        practica=[unica('El discurso de la izada de bandera usa un registro…', 'formal', ['informal']),
                  unica('Antes de hablar en público debo pensar en…', 'mi público y mi intención', ['nada'])],
        taller=[_escribe('Prepara un discurso de 2 minutos para la izada de bandera sobre un valor. Escribe la apertura, el desarrollo y el cierre.', 10)])

    U[8] = unidad(
        tema='Escribo según el destinatario y el medio',
        objetivo='Escoger el tipo de texto adecuado al propósito, consultar fuentes y escribir pensando en el destinatario y el medio.',
        explora=[texto('Vas a invitar a la comunidad a la feria de ciencia. ¿Escribirías lo mismo en un afiche, en un mensaje de WhatsApp y en una carta al alcalde?')],
        aprende=[tabla([['Medio', 'Destinatario', 'Cómo escribo'], ['Afiche', 'toda la comunidad', 'título llamativo, pocos datos, imagen'], ['Mensaje', 'familias del curso', 'breve, claro, cordial'],
                        ['Carta', 'el alcalde', 'formal, con saludo, cuerpo, despedida y firma']]),
                 texto('Antes de escribir <b>consulto fuentes</b> confiables y cito de dónde saqué los datos. Después reviso <b>ortografía</b>, <b>concordancia</b> y <b>puntuación</b>.')],
        recuerda=['El destinatario y el medio cambian cómo escribo.', 'Planeo, consulto, escribo, reviso.'],
        practica=[unica('Para escribirle al alcalde uso…', 'una carta formal', ['un mensaje con emojis']),
                  unica('Un afiche debe tener…', 'un título llamativo y datos breves', ['párrafos muy largos'])],
        taller=[_escribe('Escribe la carta formal al alcalde invitándolo a la feria de ciencia.', 10),
                abierta('Diseña el afiche de la feria de ciencia.', 6)])
    return U
