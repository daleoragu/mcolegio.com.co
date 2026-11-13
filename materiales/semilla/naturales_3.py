"""Ciencias Naturales 3.º: una guía y una ficha por cada uno de los 6 DBA, con experimentos sencillos y seguros.
Borradores para que el docente revise."""
from .base import abierta, imagen, recuadro, tabla, texto, unica, vf
from .matematicas_1 import u


def unidades():
    U = {}

    U[1] = u(
        tema='La luz y los materiales',
        objetivo='Clasificar materiales en opacos, transparentes, translúcidos y reflectivos según cómo dejan pasar la luz, y cuidar mis ojos.',
        explora=[imagen('n3-materiales-luz', 50), texto('¿Por cuál lámina pasa toda la luz? ¿Por cuál no pasa nada?')],
        aprende=[tabla([['Material', 'La luz…', 'Ejemplos'], ['Transparente', 'pasa toda: vemos claro a través', 'vidrio, aire, agua limpia'],
                        ['Translúcido', 'pasa un poco: vemos borroso', 'papel mantequilla, vidrio esmerilado'], ['Opaco', 'no pasa', 'madera, cartón, metal'],
                        ['Reflectivo', 'rebota', 'espejo, papel aluminio']]),
                 imagen('n3-espejo', 18, 'El espejo refleja la luz'),
                 texto('La luz viaja en <b>línea recta</b> y se reparte en todas las direcciones desde la fuente: por eso un bombillo en el centro ilumina todo el cuarto.'),
                 recuadro('¡Cuida tus ojos!', '<p>Nunca mires directo al sol ni a una luz láser: pueden dañar tus ojos para siempre.</p>', estilo='reto')],
        recuerda=['Transparente, translúcido, opaco y reflectivo.', 'Nunca mires el sol directamente.'],
        practica=[unica('El papel mantequilla es…', 'translúcido', ['opaco', 'reflectivo']), unica('¿Qué material refleja la luz?', 'El espejo', ['La madera', 'El cartón'])],
        taller=[unica('Una puerta de madera es…', 'opaca', ['transparente', 'translúcida']),
                unica('Para que entre mucha luz a un salón, las ventanas deben ser…', 'transparentes', ['opacas']),
                vf('Es seguro mirar el sol directamente con los ojos.', False),
                abierta('Alumbra con una linterna diferentes materiales de tu casa y haz una tabla: opaco, translúcido o transparente.', 6)])

    U[2] = u(
        tema='¿Cómo se forma la sombra?',
        objetivo='Predecir dónde se forma una sombra y cómo cambia su tamaño al mover la fuente de luz o el objeto.',
        explora=[texto('¿Por qué tu sombra a veces es larga y a veces corta? ¿De dónde sale la sombra?')],
        aprende=[texto('La <b>sombra</b> se forma cuando un objeto <b>opaco</b> tapa la luz. Aparece del lado contrario a la fuente de luz.'),
                 imagen('d-sombra-1', 50, 'Linterna cerca del objeto: sombra grande'),
                 imagen('d-sombra-3', 50, 'Linterna lejos del objeto: sombra pequeña'),
                 tabla([['Distancia linterna–objeto', 'Tamaño de la sombra'], ['10 cm', 'grande'], ['30 cm', 'mediana'], ['60 cm', 'pequeña']])],
        recuerda=['Mientras más cerca esté la luz del objeto, más grande es la sombra.', 'La sombra queda del lado opuesto a la luz.'],
        practica=[unica('Si acerco la linterna al objeto, la sombra…', 'se agranda', ['se achica', 'desaparece']),
                  unica('Si la luz viene de la derecha, la sombra queda…', 'a la izquierda', ['a la derecha', 'encima'])],
        taller=[unica('¿Qué se necesita para que haya sombra?', 'Luz y un objeto opaco que la tape', ['Solo agua', 'Un objeto transparente']),
                vf('Un vidrio transparente hace una sombra muy oscura.', False),
                abierta('Con una linterna y un muñeco, mide la sombra a 3 distancias distintas y anótalas en una tabla.', 6)])

    U[3] = u(
        tema='El sonido: vibraciones que viajan',
        objetivo='Comprobar que el sonido es una vibración, describir sonidos graves y agudos, fuertes y débiles, y cómo viaja por distintos medios.',
        explora=[imagen('n3-instrumentos', 35), texto('Toca suavemente tu garganta mientras hablas. ¿Qué sientes?')],
        aprende=[texto('El sonido es una <b>vibración</b>: vibra la cuerda de la guitarra, el parche del tambor o el aire dentro de la flauta.'),
                 tabla([['Característica', 'Puede ser', 'Ejemplo'], ['Altura (tono)', 'grave o agudo', 'tambor grave, pito agudo'],
                        ['Intensidad', 'fuerte o débil', 'grito fuerte, susurro débil'], ['Timbre', 'la «voz» propia de cada fuente', 'reconozco la voz de mi mamá']]),
                 texto('El sonido viaja por el <b>aire</b>, por el <b>agua</b> y por los <b>sólidos</b>. Mientras más lejos, más débil se escucha.'),
                 recuadro('Experimento', '<p>Haz un teléfono con dos vasos y una cuerda tensa. ¿Se escucha mejor por la cuerda o por el aire?</p>', estilo='reto')],
        recuerda=['Sin vibración no hay sonido.', 'Grave–agudo es la altura; fuerte–débil es la intensidad.'],
        practica=[unica('El sonido de un pito es…', 'agudo', ['grave']), unica('Un susurro tiene intensidad…', 'débil', ['fuerte'])],
        taller=[unica('¿Qué vibra en el tambor?', 'El parche', ['La madera del piso', 'Nada']),
                unica('Si me alejo de un parlante, el sonido se escucha…', 'más débil', ['más fuerte', 'igual']),
                unica('¿Qué material atenúa mejor el ruido en un salón?', 'Cortinas y espuma', ['Vidrio', 'Metal']),
                abierta('Construye un instrumento con materiales reciclados y explica qué vibra en él.', 6)])

    U[4] = u(
        tema='El agua cambia con la temperatura',
        objetivo='Explicar los cambios de estado del agua por el calor y el frío, medir la temperatura y reconocer el ciclo del agua.',
        explora=[imagen('n3-termometro', 18), texto('¿Qué pasa con un cubo de hielo si lo dejas al sol? ¿Y con un charco?')],
        aprende=[texto('Con <b>calor</b>: el hielo se <b>derrite</b> (fusión, sólido → líquido) y el agua se <b>evapora</b> (líquido → gas). '
                       'Con <b>frío</b>: el vapor se <b>condensa</b> (gas → líquido) y el agua se <b>congela</b> (líquido → sólido).'),
                 tabla([['Temperatura del agua', 'Estado'], ['0 °C o menos', 'sólido (hielo)'], ['entre 0 °C y 100 °C', 'líquido'], ['100 °C (hierve)', 'pasa a gas (vapor)']]),
                 imagen('n3-ciclo-agua', 55, 'El ciclo del agua'),
                 texto('Medimos con instrumentos: <b>termómetro</b> (temperatura), <b>balanza</b> (masa) y <b>probeta</b> (volumen).')],
        recuerda=['El agua hierve a 100 °C y se congela a 0 °C.', 'En el ciclo del agua: evaporación, condensación y precipitación.'],
        practica=[unica('Cuando el charco desaparece al sol, el agua…', 'se evapora', ['se congela', 'se condensa']),
                  unica('¿A qué temperatura hierve el agua al nivel del mar?', '100 °C', ['0 °C', '50 °C'])],
        taller=[unica('Las gotitas en la parte de afuera de un vaso frío se forman por…', 'condensación', ['evaporación', 'fusión']),
                unica('¿Con qué medimos la temperatura?', 'Termómetro', ['Balanza', 'Regla']),
                unica('En el ciclo del agua, la lluvia es la…', 'precipitación', ['evaporación', 'fusión']),
                abierta('Pon un cubo de hielo en un plato y anota cada 10 minutos qué le pasa.', 6)])

    U[5] = u(
        tema='Lo vivo y lo no vivo en un ecosistema',
        objetivo='Diferenciar los factores bióticos y abióticos de un ecosistema de mi región y predecir qué pasa si uno cambia.',
        explora=[imagen('n3-ecosistema', 55, 'El bosque andino'), texto('Haz dos listas: lo que está vivo y lo que no está vivo en el bosque.')],
        aprende=[texto('Un <b>ecosistema</b> es un lugar donde los seres vivos se relacionan entre sí y con su ambiente.'),
                 tabla([['Factores bióticos (vivos)', 'Factores abióticos (no vivos)'], ['plantas, animales, hongos', 'luz, agua, temperatura, suelo, aire']]),
                 texto('Los abióticos influyen en los bióticos: sin <b>luz</b> las plantas no crecen; si el <b>agua</b> de la quebrada se seca, los animales se van o mueren; '
                       'si sube mucho la <b>temperatura</b>, algunas especies no sobreviven.')],
        recuerda=['Biótico: vivo. Abiótico: no vivo.', 'Si cambia un factor, todo el ecosistema se afecta.'],
        practica=[unica('¿Cuál es un factor abiótico?', 'La luz del sol', ['La pava', 'El musgo']),
                  unica('Si la quebrada se seca, los animales…', 'se quedan sin agua', ['no se afectan'])],
        taller=[unica('¿Cuál es un factor biótico?', 'La ardilla', ['La roca', 'El aire']),
                unica('Las plantas necesitan del suelo…', 'nutrientes y agua', ['nada']),
                vf('La temperatura no influye en los seres vivos.', False),
                abierta('Describe un ecosistema cerca de tu casa o colegio: escribe 3 factores bióticos y 3 abióticos.', 6)])

    U[6] = u(
        tema='Los seres vivos se relacionan',
        objetivo='Reconocer las relaciones entre seres vivos (competencia, depredación, mutualismo, parasitismo y otras) y el camuflaje.',
        explora=[imagen('n3-hormigas', 35, 'Hormigas arrieras'), texto('¿Por qué las hormigas trabajan en grupo? ¿Qué ganan?')],
        aprende=[tabla([['Relación', 'Qué pasa', 'Ejemplo'], ['Gregarismo', 'viven en grupo para protegerse', 'hormigas, peces en cardumen'],
                        ['Competencia', 'pelean por el mismo alimento o espacio', 'dos gallos por el maíz'], ['Depredación', 'uno caza y se come al otro', 'la garza y el pez'],
                        ['Mutualismo', 'los dos ganan', 'la abeja y la flor'], ['Parasitismo', 'uno gana y el otro pierde', 'la garrapata y el perro'],
                        ['Comensalismo', 'uno gana y al otro no le afecta', 'las orquídeas sobre los árboles'], ['Territorialidad', 'defienden su espacio', 'el perro que ladra en su casa']]),
                 imagen('n3-camaleon', 25, 'El insecto palo se camufla'),
                 texto('El <b>camuflaje</b> ayuda a esconderse de los depredadores o a cazar sin ser visto.')],
        recuerda=['En el mutualismo los dos ganan.', 'El camuflaje ayuda a sobrevivir.'],
        practica=[unica('La abeja toma el néctar y lleva el polen: es…', 'mutualismo', ['parasitismo', 'competencia']),
                  unica('La garrapata en el perro es…', 'parasitismo', ['mutualismo', 'gregarismo'])],
        taller=[unica('La garza que se come un pez es…', 'depredación', ['mutualismo', 'comensalismo']),
                unica('¿Para qué le sirve el camuflaje al insecto palo?', 'Para que no se lo coman', ['Para volar']),
                unica('Si desaparecen las abejas, las plantas…', 'tienen menos frutos', ['crecen más']),
                abierta('Busca en tu entorno un ejemplo de relación entre seres vivos y dibújalo.', 6)])
    return U
