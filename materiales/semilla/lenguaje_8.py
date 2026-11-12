"""Lenguaje 8.º: una guía y un taller por cada uno de los 8 DBA. Textos originales de mcolegio. Borradores para revisar."""
from .base import abierta, recuadro, tabla, texto, unica, unidad, vf


def _escribe(enunciado, renglones=6):
    return abierta(enunciado, renglones, puntos=2)


def unidades():
    U = {}

    U[1] = unidad(
        tema='Los discursos de los medios',
        objetivo='Caracterizar los discursos de los medios y otras fuentes según su contenido, la intención del autor y el contexto, e inferir el significado de palabras por el contexto.',
        explora=[texto('Un mismo hecho: «Paro de transportadores». ¿Cómo lo titularía un medio afín al gobierno y uno afín a los transportadores?')],
        aprende=[texto('Los medios cumplen una <b>función social</b>: informar, formar opinión, vigilar al poder y entretener. Pero cada uno tiene intereses: a veces se nota en los <b>verbos</b> '
                       'y <b>adjetivos</b> que eligen («bloquean» vs. «protestan»).'),
                 tabla([['Titular', 'Lo que sugiere'], ['«Transportadores bloquean la ciudad»', 'el paro es un problema'], ['«Transportadores protestan por el alza del ACPM»', 'el paro tiene causas justas']]),
                 texto('Las bibliotecas, los museos y los archivos también son <b>fuentes</b> de la cultura.')],
        recuerda=['Las palabras elegidas revelan la intención.', 'Comparo varios medios sobre un mismo hecho.'],
        practica=[unica('¿Qué palabra tiene una carga más negativa?', 'bloquean', ['protestan', 'se reúnen']),
                  unica('Una función social de los medios es…', 'vigilar al poder', ['vender siempre'])],
        taller=[_escribe('Busca una misma noticia en dos medios y compara los verbos y adjetivos que usan.', 8),
                vf('El contexto ayuda a inferir el significado de una palabra desconocida.', True)])

    U[2] = unidad(
        tema='El arte de los pueblos',
        objetivo='Relacionar las manifestaciones artísticas con las comunidades que las producen y valorarlas.',
        explora=[texto('¿Qué expresiones artísticas son propias de tu región: música, danza, artesanía, carnaval?')],
        aprende=[tabla([['Manifestación', 'Comunidad', 'Lo que expresa'], ['Carnaval de Barranquilla', 'Caribe', 'mezcla de culturas, alegría, crítica social'],
                        ['Mola', 'pueblo guna (gunadule)', 'su cosmovisión en capas de tela'], ['Currulao y marimba', 'afrodescendientes del Pacífico', 'memoria y resistencia'],
                        ['Carnaval de Negros y Blancos', 'Nariño', 'igualdad y convivencia'], ['Sombrero vueltiao', 'pueblo zenú', 'identidad y tejido de caña flecha']]),
                 texto('Para interpretar una obra me pregunto: ¿quién la hizo?, ¿para qué?, ¿qué materiales, colores, sonidos o movimientos usa? y ¿qué significan para su comunidad?')],
        recuerda=['El arte expresa la identidad de una comunidad.'],
        practica=[unica('El sombrero vueltiao es tradición del pueblo…', 'zenú', ['wayuu', 'muisca']), unica('El Carnaval de Negros y Blancos se celebra en…', 'Nariño', ['La Guajira'])],
        taller=[_escribe('Describe una manifestación artística de tu región: quién la hace, cómo es y qué expresa.', 8)])

    U[3] = unidad(
        tema='Narrativa e identidad cultural',
        objetivo='Reconocer la estructura formal de cuentos, relatos, fábulas y novelas, las estrategias narrativas del autor y la identidad cultural que recrean.',
        explora=[texto('Cuando alguien cuenta una historia, ¿por qué empieza a veces por el final?')],
        aprende=[texto('Estrategias narrativas: <b>tipo de narrador</b> (primera, segunda o tercera persona; omnisciente o testigo), <b>orden del tiempo</b> (lineal, retrospectivo o in media res), '
                       '<b>punto de vista</b> y <b>ritmo</b>.'),
                 texto('«Crónica de una muerte anunciada» empieza revelando el final: el lector ya sabe qué pasará, y la intriga está en cómo y por qué.'),
                 tabla([['Forma', 'Extensión', 'Rasgo'], ['Cuento', 'breve', 'un conflicto central'], ['Novela', 'extensa', 'varios conflictos y personajes'],
                        ['Fábula', 'breve', 'moraleja'], ['Relato corto', 'muy breve', 'efecto único']])],
        recuerda=['El autor elige cómo contar: narrador, tiempo y punto de vista.'],
        practica=[unica('Empezar la historia por el final es un orden…', 'retrospectivo / no lineal', ['lineal']),
                  unica('Un narrador que sabe lo que piensan todos los personajes es…', 'omnisciente', ['testigo'])],
        taller=[_escribe('Reescribe un cuento conocido empezando por el final.', 12)])

    U[4] = unidad(
        tema='El género lírico: música, rima y figuras',
        objetivo='Comprender el género lírico como construcción mediada por la musicalidad, la rima y las figuras retóricas.',
        explora=[texto('¿Por qué las canciones se quedan en la memoria más fácil que un texto cualquiera?')],
        aprende=[recuadro('Poema', '<p>Sobre el río duerme la tarde,<br>la garza escribe en el agua su nombre;<br>y mi pueblo, de tejas cansadas,<br>guarda en sus patios el olor del hombre.</p>',
                          estilo='nota'),
                 tabla([['Recurso', 'Ejemplo del poema'], ['Personificación', '«duerme la tarde»'], ['Metáfora', '«la garza escribe en el agua su nombre»'], ['Hipálage', '«tejas cansadas»'],
                        ['Rima consonante', 'nombre / hombre']]),
                 texto('La <b>musicalidad</b> nace del ritmo (acentos), la rima (consonante o asonante) y las repeticiones. Por eso la poesía y la música se parecen tanto.')],
        recuerda=['Rima consonante: coinciden vocales y consonantes. Asonante: solo vocales.'],
        practica=[unica('«nombre / hombre» es rima…', 'consonante', ['asonante']), unica('«duerme la tarde» es…', 'personificación', ['hipérbole'])],
        taller=[unica('«casa / mala» riman en forma…', 'asonante', ['consonante']), _escribe('Escribe un poema de dos estrofas sobre tu pueblo con una metáfora y una personificación.', 10)])

    U[5] = unidad(
        tema='Escucho y predigo en el diálogo',
        objetivo='Escuchar con atención en diálogos informales, comprender sus contenidos y predecir las ideas que pueden aparecer.',
        explora=[texto('Cuando un amigo empieza diciendo «No te vas a creer lo que pasó…», ¿qué esperas escuchar?')],
        aprende=[texto('En una conversación anticipamos el contenido por las <b>pistas</b>: palabras de inicio, el tono, el contexto y lo que sabemos del otro.'),
                 texto('Escuchar bien es: mirar al interlocutor, no interrumpir, hacer preguntas, parafrasear («O sea que…») y respetar los turnos.')],
        recuerda=['Escucho para entender, no solo para responder.'],
        practica=[unica('Parafrasear es…', 'repetir con mis palabras lo que entendí', ['interrumpir']), unica('«No te vas a creer…» anticipa…', 'algo sorprendente', ['algo aburrido'])],
        taller=[_escribe('Escucha una conversación (con permiso) y escribe qué pistas te permitieron predecir lo que se diría.', 6)])

    U[6] = unidad(
        tema='Las voces del texto y sus sentidos',
        objetivo='Inferir múltiples sentidos de los textos, identificar las voces que hablan en ellos y relacionarlos con su contexto.',
        explora=[texto('En una noticia aparecen la voz del periodista, la de un testigo y la de un experto. ¿Por qué el periodista las incluye?')],
        aprende=[texto('Un texto puede tener varias <b>voces</b>: el autor, los personajes, las citas de expertos, los testimonios. Identificar quién dice qué ayuda a ver la <b>intención</b> del texto.'),
                 texto('Hago <b>hipótesis</b> sobre el sentido global uniendo lo explícito (lo que dice) y lo implícito (lo que sugiere), y las confirmo o descarto al seguir leyendo.')],
        recuerda=['¿Quién habla? ¿Desde dónde? ¿Para qué?'],
        practica=[unica('Una cita entre comillas de un experto es…', 'otra voz en el texto', ['la voz del autor']),
                  unica('Una hipótesis de lectura se…', 'confirma o descarta al seguir leyendo', ['escribe al final sin leer'])],
        taller=[_escribe('En una noticia, identifica todas las voces y explica qué aporta cada una.', 8)])

    U[7] = unidad(
        tema='Argumento en mis intervenciones orales',
        objetivo='Exponer puntos de vista que apoyen o contradigan a mis interlocutores, precisando los conceptos que uso.',
        explora=[texto('¿Es mejor estudiar por la mañana o por la tarde? Escucha a dos compañeros y decide a quién apoyas y por qué.')],
        aprende=[texto('Estructura de una intervención: <b>postura</b> («Estoy de acuerdo con… porque…»), <b>argumentos</b> (datos, ejemplos, autoridad), <b>contraargumento</b> («Aunque…, …») y <b>conclusión</b>.'),
                 texto('Precisar conceptos evita malentendidos: «cuando digo <i>rendimiento</i>, me refiero a las notas del periodo».')],
        recuerda=['Apoyo o contradigo con razones, no con ataques personales.'],
        practica=[unica('«Aunque tienes razón en…, …» introduce…', 'un contraargumento', ['la conclusión']),
                  unica('Atacar a la persona en vez de a su idea es…', 'una falacia', ['un buen argumento'])],
        taller=[_escribe('Prepara una intervención de 2 minutos a favor o en contra de la jornada única, con postura, dos argumentos, contraargumento y conclusión.', 10)])

    U[8] = unidad(
        tema='Textos para lo privado y lo público, lo cotidiano y lo científico',
        objetivo='Componer textos adecuados a su ámbito de uso y evaluarlos según el género, el léxico y el propósito.',
        explora=[texto('¿En qué se diferencia una carta a un amigo de un informe de laboratorio?')],
        aprende=[tabla([['Ámbito', 'Ejemplos', 'Rasgos'], ['Privado / cotidiano', 'carta personal, diario, mensaje', 'tono cercano, primera persona'],
                        ['Público', 'carta abierta, columna, afiche', 'tono formal, dirigido a muchos'], ['Científico', 'informe de laboratorio, reseña', 'léxico técnico, objetividad, estructura fija']]),
                 texto('Informe de laboratorio: título, objetivo, materiales, procedimiento, resultados, análisis y conclusión.'),
                 texto('Evalúo mis textos con una lista: ¿cumple el género?, ¿el léxico es adecuado?, ¿logra el propósito?, ¿tiene errores?')],
        recuerda=['El ámbito determina el tono y el léxico.'],
        practica=[unica('Un informe de laboratorio pertenece al ámbito…', 'científico', ['privado']), unica('Un diario personal usa un tono…', 'cercano', ['técnico'])],
        taller=[_escribe('Escribe un informe de laboratorio de un experimento sencillo de Ciencias.', 14)])
    return U
