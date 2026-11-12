"""Ciencias Sociales 1.º: una guía y una ficha por cada uno de los 8 DBA, desde el propio cuerpo, la familia, la escuela
y el barrio o la vereda. Borradores para que el docente revise y ajuste a su municipio."""
from .base import abierta, imagen, recuadro, tabla, texto, unica, vf
from .matematicas_1 import u


def unidades():
    U = {}

    U[1] = u(
        tema='Me ubico: mi cuerpo y los puntos cardinales',
        objetivo='Ubicar lugares de mi escuela y de mi barrio o vereda usando derecha, izquierda, adelante, atrás y los puntos cardinales.',
        explora=[imagen('s1-sol-sale', 50, 'Por la mañana el sol sale por el oriente'),
                 texto('¿Por dónde sale el sol en tu casa? Señálalo con tu brazo derecho.')],
        aprende=[texto('Si señalo con mi brazo <b>derecho</b> por donde sale el sol, ese es el <b>Este</b> (oriente). A mi izquierda queda el <b>Oeste</b> '
                       '(occidente), al frente el <b>Norte</b> y atrás el <b>Sur</b>.'),
                 imagen('d-rosa', 30, 'La rosa de los vientos'),
                 imagen('d-escuela', 70, 'Plano de la escuela'),
                 texto('En el plano, la <b>coordinación</b> está al norte del patio y la <b>entrada</b> está al sur, abajo a la derecha.'),
                 imagen('d-barrio', 70, 'Mapa del barrio'),
                 imagen('s1-camino-escuela', 45, 'El camino de Sofi a la escuela')],
        recuerda=['El sol sale por el Este y se oculta por el Oeste.', 'En los mapas, el Norte casi siempre está arriba.'],
        practica=[imagen('d-escuela', 55), unica('¿Qué lugar está entre la cafetería y los salones?', 'El patio de recreo', ['La rectoría', 'La biblioteca']),
                  imagen('d-rosa-sin', 20), unica('¿Qué punto cardinal está arriba en la rosa?', 'Norte', ['Sur', 'Este', 'Oeste'])],
        taller=[imagen('d-barrio', 60), unica('En el mapa, ¿qué está al lado de mi casa?', 'El puesto de salud', ['La iglesia', 'El parque']),
                unica('¿Qué lugar está al sur (abajo) de la escuela?', 'La iglesia', ['Mi casa', 'El puesto de salud']),
                unica('¿Por dónde se oculta el sol?', 'Por el Oeste', ['Por el Este', 'Por el Norte']),
                abierta('Dibuja el camino de tu casa a la escuela con tres lugares que veas al pasar.', 8)])

    U[2] = u(
        tema='El paisaje donde vivo',
        objetivo='Describir el paisaje de mi barrio o vereda, el tiempo atmosférico y los problemas del ambiente.',
        explora=[imagen('s1-montana', 45), texto('¿Tu casa está en una montaña, en un valle, en una llanura o cerca del mar?')],
        aprende=[texto('Las formas de la tierra se llaman <b>relieve</b>:'),
                 imagen('s1-valle', 30, 'Valle'), imagen('s1-llanura', 30, 'Llanura'), imagen('s1-costa', 30, 'Costa'), imagen('s1-isla', 30, 'Isla'),
                 texto('El <b>tiempo atmosférico</b> cambia: hay días de <b>lluvia</b> y días <b>secos</b>, días de <b>calor</b> y días de <b>frío</b>.'),
                 imagen('s1-lluvia', 35, 'Tiempo de lluvia'), imagen('s1-sequia', 35, 'Tiempo seco'),
                 texto('Las personas hacen <b>obras</b> que ayudan a la comunidad, como puentes y escuelas. Pero también hay <b>problemas</b>, como la basura en el río.'),
                 imagen('s1-puente', 35, 'Un puente nuevo'), imagen('s1-rio-basura', 35, 'Basura en el río')],
        recuerda=['Montaña, valle, llanura, costa e isla son formas del relieve.', 'Cuidar el agua es tarea de todos.'],
        practica=[imagen('s1-isla', 25), unica('¿Cómo se llama la tierra rodeada de agua?', 'Isla', ['Montaña', 'Valle']),
                  unica('¿Qué podemos hacer para que el río esté limpio?', 'No tirar basura', ['Tirar botellas', 'Lavar carros en el río'])],
        taller=[imagen('s1-llanura', 30), unica('¿Qué forma del relieve es?', 'Llanura', ['Montaña', 'Isla', 'Costa']),
                unica('Cuando hace mucho calor me pongo…', 'ropa fresca y gorra', ['chaqueta gruesa y bufanda']),
                vf('Un puente es una obra que ayuda a la comunidad.', True),
                abierta('Dibuja el paisaje que ves desde tu casa o tu escuela.', 8)])

    U[3] = u(
        tema='Mi tiempo: ayer, hoy y mañana',
        objetivo='Ordenar los días de la semana y los meses, diferenciar ayer, hoy y mañana, y ubicar a mi familia de mayor a menor.',
        explora=[imagen('s1-cumpleanos', 40), texto('¿Cuándo es tu cumpleaños? ¿Cuántos años vas a cumplir?')],
        aprende=[texto('La semana tiene <b>7 días</b>:'), imagen('d-dias', 80),
                 texto('El año tiene <b>12 meses</b>:'), imagen('d-meses', 75),
                 tabla([['Ayer', 'Hoy', 'Mañana'], ['Ya pasó', 'Está pasando', 'Va a pasar']]),
                 imagen('d-reloj-7-0', 22, 'A las 7 entro al colegio'),
                 imagen('s1-familia', 55, 'La familia, del mayor al menor'),
                 texto('Los abuelos nacieron <b>antes</b> que los papás; los papás, antes que los hijos.')],
        recuerda=['Después del viernes viene el sábado.', 'Ayer ya pasó; mañana todavía no llega.'],
        practica=[imagen('d-dias-v3-v5', 75), unica('¿Qué día falta entre martes y jueves?', 'miércoles', ['lunes', 'viernes', 'domingo']),
                  unica('Si hoy es lunes, mañana es…', 'martes', ['domingo', 'jueves'])],
        taller=[unica('¿Cuántos días tiene la semana?', '7', ['5', '10', '12']),
                unica('¿Qué mes viene después de junio?', 'julio', ['mayo', 'agosto']),
                unica('¿Quién nació primero?', 'El abuelo', ['El papá', 'El hijo', 'La bebé']),
                imagen('d-reloj-12-0', 18), unica('¿Qué hora marca el reloj?', 'Las 12', ['Las 6', 'Las 3']),
                abierta('Escribe la fecha de tu cumpleaños y la de alguien de tu familia.', 2),
                abierta('Dibuja algo que hiciste ayer y algo que harás mañana.', 6)])

    U[4] = u(
        tema='Las cosas cambian: antes y ahora',
        objetivo='Contar cómo hemos cambiado yo, mi familia, mi colegio y mi barrio o vereda.',
        explora=[imagen('s1-primer-dia', 45, 'El primer día de clases'),
                 texto('¿Cómo te sentiste tu primer día en el colegio? ¿Cómo te sientes ahora?')],
        aprende=[texto('Las personas y los lugares <b>cambian</b> con el tiempo. Comparamos el <b>antes</b> y el <b>ahora</b>.'),
                 tabla([['Antes', 'Ahora'], ['No conocía a mis compañeros', 'Tengo amigos'], ['No sabía leer', 'Leo palabras'],
                        ['La calle era de tierra', 'La calle está pavimentada']]),
                 imagen('s1-izada', 45, 'Izada de bandera: un acontecimiento del colegio'),
                 texto('Pertenezco a varios grupos: mi <b>familia</b>, mi <b>colegio</b> y mi <b>barrio o vereda</b>.')],
        recuerda=['Para ver un cambio comparo el antes y el ahora.', 'Puedo preguntar a los mayores cómo era antes mi barrio o vereda.'],
        practica=[unica('¿Qué cambió en Tomás desde el primer día?', 'Ya conoce a sus compañeros', ['Nada', 'Ya no va al colegio']),
                  unica('¿A cuál grupo pertenezco?', 'A mi familia', ['A un equipo de otro país', 'A ninguno'])],
        taller=[unica('En la izada de bandera…', 'cantamos el himno y honramos a la bandera', ['jugamos fútbol', 'dormimos']),
                vf('Mi barrio o vereda siempre ha sido igual.', False),
                abierta('Pregunta a un adulto mayor cómo era tu barrio o vereda antes. Escribe o dibuja lo que te contó.', 6),
                abierta('Dibuja cómo eras cuando entraste al colegio y cómo eres ahora.', 6)])

    U[5] = u(
        tema='Soy único y hago parte de grupos',
        objetivo='Reconocer lo que me hace único, respetar lo que hace únicos a los demás y conocer las costumbres de mi comunidad.',
        explora=[imagen('s1-diversidad', 55), texto('¿En qué se parecen estos niños? ¿En qué son diferentes?')],
        aprende=[texto('Cada persona es <b>única</b>: su cara, su voz, lo que le gusta, lo que siente. ¡Y eso es valioso!'),
                 tabla([['Yo soy…', 'Me gusta…', 'Me pongo feliz cuando…'], ['', '', '']]),
                 texto('Tenemos <b>costumbres</b>: comidas, fiestas, música y juegos de nuestra región.'),
                 imagen('s1-abuelo-cuenta', 45, 'Los abuelos nos cuentan las tradiciones')],
        recuerda=['Ser diferentes nos hace únicos.', 'Escuchar a los mayores nos enseña nuestra historia.'],
        practica=[unica('Si a mi compañero le gusta otra comida, yo…', 'lo respeto', ['me burlo', 'me enojo']),
                  abierta('Escribe una cualidad tuya que te ayuda a estar bien con los demás.', 2)],
        taller=[vf('Todos los niños deben ser iguales en todo.', False),
                unica('¿Quién nos puede contar las tradiciones de antes?', 'Los abuelos', ['Un niño de 1 año']),
                abierta('Dibújate y escribe tres cosas que te hacen único.', 6),
                abierta('Pregunta en tu casa por una comida típica de tu región y dibújala.', 6)])

    U[6] = u(
        tema='Las viviendas de mi comunidad',
        objetivo='Conocer los tipos de vivienda de mi región, sus materiales y por qué la casa es un lugar de cuidado.',
        explora=[imagen('s1-casa-bahareque', 40), texto('¿De qué está hecha esta casa? ¿Cómo es la tuya?')],
        aprende=[texto('Hay muchas formas de <b>vivienda</b> según el clima y el lugar:'),
                 imagen('s1-edificio', 25, 'Edificio'), imagen('s1-casa-ladrillo', 25, 'Casa de ladrillo'),
                 imagen('s1-palafito', 25, 'Palafito'), imagen('s1-maloca', 25, 'Maloca'),
                 tabla([['Vivienda', 'Material', 'Dónde'], ['Casa de bahareque', 'barro, guadua y teja', 'campo de clima templado'],
                        ['Palafito', 'madera, sobre pilotes', 'cerca de ríos y ciénagas'], ['Maloca', 'madera y palma', 'selva'],
                        ['Edificio', 'ladrillo y cemento', 'ciudades']]),
                 texto('Mi casa tiene <b>partes</b>: sala, cocina, habitaciones y baño. Es donde mi familia me <b>cuida</b>.')],
        recuerda=['Las viviendas se construyen según el lugar y el clima.', 'Algunas casas antiguas son patrimonio: hay que cuidarlas.'],
        practica=[imagen('s1-palafito', 25), unica('¿Por qué el palafito está sobre pilotes?', 'Para que el agua no entre', ['Para que sea más bonito']),
                  unica('¿Dónde está la maloca?', 'En la selva', ['En el mar', 'En un edificio'])],
        taller=[unica('¿Qué material tiene la casa de bahareque?', 'Barro y guadua', ['Vidrio', 'Plástico']),
                unica('¿En qué parte de la casa cocinamos?', 'En la cocina', ['En el baño', 'En la habitación']),
                abierta('Pregunta de dónde vino tu familia y cómo llegó a la casa donde vives. Dibújalo.', 6),
                abierta('Dibuja tu casa por dentro y escribe el nombre de cada parte.', 8)])

    U[7] = u(
        tema='Hacemos acuerdos para convivir',
        objetivo='Participar en la construcción de acuerdos en el salón y en la familia, y cumplirlos para lograr metas comunes.',
        explora=[imagen('s1-turno', 45, 'Esperamos el turno'), texto('¿Qué pasaría si todos quisieran subir al rodadero al tiempo?')],
        aprende=[texto('Las <b>normas</b> y los <b>acuerdos</b> nos ayudan a vivir bien juntos. Los hacemos entre todos y todos los cumplimos.'),
                 imagen('s1-acuerdos', 45, 'Hacemos los acuerdos del salón'),
                 recuadro('Nuestros acuerdos del salón', '<ul><li>Levanto la mano para hablar.</li><li>Cuido los materiales.</li>'
                          '<li>Trato bien a mis compañeros.</li><li>Dejo el salón limpio.</li></ul>', estilo='nota'),
                 imagen('s1-equipo', 40, 'En equipo logramos más'),
                 texto('Cuando hay un <b>problema</b>, hablamos, escuchamos a todos y buscamos una solución juntos.')],
        recuerda=['Los acuerdos se hacen entre todos.', 'Trabajar en equipo nos ayuda a lograr metas.'],
        practica=[unica('Si dos niños quieren el mismo balón, pueden…', 'turnarse o jugar juntos', ['pelear', 'romperlo']),
                  vf('Las normas del salón solo las cumple el profesor.', False)],
        taller=[unica('¿Para qué sirven los acuerdos?', 'Para convivir bien', ['Para castigar', 'Para nada']),
                unica('Para lograr una meta en equipo…', 'todos ayudamos', ['uno hace todo', 'nadie hace nada']),
                abierta('Escribe un acuerdo para tu casa y otro para tu salón.', 4),
                abierta('Dibuja a tu equipo trabajando junto en algo.', 6)])

    U[8] = u(
        tema='Me respeto y respeto a los demás',
        objetivo='Valorarme y valorar a mis compañeros, reconocer situaciones de maltrato y saber a quién pedir ayuda.',
        explora=[imagen('s1-invitar', 45), texto('¿Cómo se siente el niño que estaba solo? ¿Qué hizo Tomás?')],
        aprende=[texto('Todos tenemos <b>derechos</b> y <b>deberes</b>. Somos diferentes, pero todos merecemos <b>respeto</b>.'),
                 imagen('s1-compartir', 40, 'Compartir'),
                 texto('El <b>maltrato</b> es cuando alguien golpea, insulta, humilla o hace sentir mal a otro. ¡Nadie debe maltratarnos!'),
                 imagen('s1-pedir-ayuda', 40, 'Si algo me pasa, se lo cuento a un adulto de confianza'),
                 recuadro('¿A quién le cuento?', '<p>A mi profesora o profesor, a mi mamá, mi papá o mi cuidador, al orientador del colegio. '
                          'También existe la Línea 141 del ICBF.</p>', estilo='recuerda')],
        recuerda=['Me respeto y respeto a los demás.', 'Si alguien me hace daño, lo cuento a un adulto de confianza.'],
        practica=[unica('Si veo que molestan a un compañero, yo…', 'aviso a un adulto y lo acompaño', ['me río', 'también lo molesto']),
                  unica('¿Qué es respetar?', 'Tratar bien a los demás aunque sean diferentes', ['Hacer lo que yo quiera'])],
        taller=[vf('Golpear a un compañero es maltrato.', True),
                unica('¿A quién le pido ayuda en el colegio?', 'A mi profesor', ['A nadie', 'A un desconocido']),
                unica('Si un niño está solo en el recreo, puedo…', 'invitarlo a jugar', ['ignorarlo', 'burlarme']),
                abierta('Escribe algo bonito de un compañero del salón.', 3),
                abierta('Dibuja una acción de buen trato en tu casa o en tu colegio.', 6)])
    return U
