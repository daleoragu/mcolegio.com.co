"""Ciencias Sociales 3.º: una guía y una ficha por cada uno de los 8 DBA, desde el departamento y el municipio.
Los mapas son los oficiales del IGAC (no se generan con IA). Borradores para que el docente revise y ajuste a su departamento."""
from .base import abierta, imagen, recuadro, tabla, texto, unica, vf
from .matematicas_1 import u


def unidades():
    U = {}

    U[1] = u(
        tema='Océanos, mares y pueblos costeros',
        objetivo='Nombrar los continentes y océanos, reconocer la vida en las costas y los problemas de los océanos.',
        explora=[imagen('s3-mapamundi', 70, 'Planisferio con continentes y océanos'), texto('¿Cuántos continentes ves? ¿Qué océanos tocan a Colombia?')],
        aprende=[tabla([['Continentes', 'Océanos'], ['América, Europa, Asia, África, Oceanía y Antártida', 'Pacífico, Atlántico, Índico, Ártico y Antártico']]),
                 texto('Los <b>mares</b> son partes de los océanos cerca de la tierra. Colombia tiene costas en el <b>mar Caribe</b> (océano Atlántico) y en el <b>océano Pacífico</b>.'),
                 imagen('s3-puerto', 40, 'En la costa: pesca, puertos y turismo'),
                 texto('En las costas la gente vive de la <b>pesca</b>, los <b>puertos</b> (por donde llegan y salen productos) y el <b>turismo</b>. Los mares también '
                       'marcan <b>límites</b> entre países.'),
                 imagen('s3-mar-plastico', 35, 'El plástico daña a los animales del mar')],
        recuerda=['Colombia es el único país de Suramérica con costas en dos océanos.', 'El plástico en el mar daña la vida marina y a los pescadores.'],
        practica=[unica('¿Qué dos mares u océanos bañan a Colombia?', 'El mar Caribe y el océano Pacífico', ['El Índico y el Ártico']),
                  unica('¿Cuál es una actividad de las zonas costeras?', 'La pesca', ['La minería de carbón en el páramo'])],
        taller=[unica('¿En qué continente está Colombia?', 'América', ['Europa', 'África']),
                unica('Un puerto sirve para…', 'que lleguen y salgan barcos con productos', ['cultivar café']),
                vf('El plástico en el mar no afecta a los pescadores.', False),
                abierta('¿Tu departamento tiene costa? Escribe una ventaja de tener costa o de no tenerla.', 4)])

    U[2] = u(
        tema='Recursos naturales y trabajo en mi región',
        objetivo='Relacionar el clima, el suelo, el agua, la flora y la fauna de mi región con las actividades económicas.',
        explora=[imagen('s3-mapa-colombia-fisico', 55, 'Mapa físico de Colombia'), texto('¿Tu municipio está en montaña, en valle, en llanura o en la costa?')],
        aprende=[texto('Los <b>recursos naturales</b> son lo que la naturaleza nos da: suelo, agua, clima, plantas, animales y minerales.'),
                 tabla([['Actividad', 'Qué se hace', 'Dónde es común'], ['Agricultura', 'cultivar alimentos', 'valles y montañas'], ['Ganadería', 'criar animales', 'llanuras'],
                        ['Pesca', 'sacar peces', 'ríos y costas'], ['Minería', 'sacar minerales', 'montañas y ríos'], ['Industria', 'transformar productos', 'ciudades'],
                        ['Servicios', 'comercio, salud, educación, turismo', 'pueblos y ciudades']]),
                 imagen('s3-mercado', 40, 'En la plaza hay productos de tierra fría y de tierra caliente'),
                 texto('En tierra fría no crece el banano y en tierra caliente no crece bien la papa: por eso los productos <b>viajan</b> de una región a otra. '
                       'Gracias al trabajo de los campesinos tenemos alimentos.')],
        recuerda=['El clima decide qué se puede cultivar.', 'Los campesinos producen los alimentos de todos.'],
        practica=[unica('¿Qué actividad es criar vacas?', 'Ganadería', ['Pesca', 'Industria']),
                  unica('La papa crece mejor en…', 'tierra fría', ['tierra caliente', 'el mar'])],
        taller=[unica('Sacar oro o carbón de la tierra es…', 'minería', ['agricultura', 'turismo']),
                unica('¿Por qué en el mercado hay frutas de otros climas?', 'Porque las traen de otras regiones', ['Porque crecen en todos lados']),
                abierta('Escribe 3 productos que se cultiven o produzcan en tu municipio.', 3),
                abierta('Entrevista a alguien que trabaje en el campo y escribe qué hace.', 5)])

    U[3] = u(
        tema='Mi territorio crece y cambia',
        objetivo='Explicar cómo las obras públicas y el crecimiento de la población transforman mi municipio y qué problemas trae el mal uso de los recursos.',
        explora=[texto('Pregunta a un adulto mayor: ¿cómo era la plaza principal cuando era niño? ¿Había acueducto en todas las casas?')],
        aprende=[texto('Las <b>obras públicas</b> son construcciones para todos: <b>carreteras</b>, <b>acueducto</b> (agua potable), <b>alcantarillado</b>, '
                       '<b>hospitales</b>, <b>escuelas</b> y <b>parques</b>.'),
                 imagen('s1-puente', 30, 'Una obra pública'),
                 texto('Cuando la <b>población</b> crece, se necesitan más casas, más agua y más servicios. Si no se planea, aparecen problemas: basura, ríos contaminados, falta de agua.'),
                 tabla([['Antes', 'Ahora', '¿Qué cambió?'], ['camino de herradura', 'carretera', 'se viaja más rápido'], ['pozo de agua', 'acueducto', 'agua en las casas']])],
        recuerda=['Las obras públicas mejoran la vida de la comunidad.', 'Más población necesita más servicios y más cuidado de los recursos.'],
        practica=[unica('El acueducto sirve para…', 'llevar agua potable a las casas', ['llevar la basura']),
                  unica('Si un pueblo crece mucho sin planear, puede haber…', 'falta de agua y basura', ['más bosques'])],
        taller=[unica('¿Cuál es una obra pública?', 'El hospital', ['Una casa privada']),
                vf('Cuando crece la población se necesitan más servicios.', True),
                abierta('Busca en internet o pregunta en la alcaldía cuántos habitantes tiene tu municipio hoy.', 2),
                abierta('Dibuja una obra pública de tu municipio y escribe para qué sirve.', 6)])

    U[4] = u(
        tema='Lo que heredamos: comida, música y fiestas',
        objetivo='Reconocer el legado de los grupos humanos en la gastronomía, la música, las fiestas y los objetos del pasado de mi región.',
        explora=[imagen('s3-fiesta', 50), texto('¿Qué fiestas se celebran en tu municipio? ¿Qué se come y qué música se escucha?')],
        aprende=[texto('El <b>legado cultural</b> es lo que recibimos de quienes vivieron antes: comidas, músicas, bailes, fiestas, palabras y costumbres.'),
                 tabla([['Región', 'Comida', 'Música'], ['Andina', 'tamal, ajiaco, lechona', 'bambuco, guabina'], ['Caribe', 'arroz con coco, arepa de huevo', 'cumbia, vallenato'],
                        ['Pacífica', 'pescado con coco, encocado', 'currulao'], ['Llanos', 'mamona (carne a la llanera)', 'joropo']]),
                 texto('Los <b>objetos</b> (herramientas, ollas de barro, fotos, documentos) y las <b>construcciones</b> antiguas nos cuentan cómo se vivía.'),
                 texto('La <b>historia oral</b> son los relatos que nos cuentan los abuelos.')],
        recuerda=['Las tradiciones nos unen como comunidad.', 'Cada región tiene su comida y su música.'],
        practica=[unica('El currulao es música de la región…', 'Pacífica', ['Andina', 'Llanos']), unica('El joropo es de…', 'los Llanos', ['el Caribe', 'el Pacífico'])],
        taller=[unica('¿Qué es la historia oral?', 'Los relatos que cuentan los mayores', ['Un libro de matemáticas']),
                unica('Una olla de barro antigua nos cuenta…', 'cómo se cocinaba antes', ['el clima de hoy']),
                abierta('Pregunta a tus abuelos por una receta típica de tu región y escríbela.', 6),
                abierta('Compara dos fiestas de tu departamento: ¿cuándo son?, ¿qué celebran?, ¿quiénes participan?', 6)])

    U[5] = u(
        tema='El tiempo organiza nuestra vida',
        objetivo='Organizar actividades personales y familiares con el calendario y analizar el tiempo de producción de un producto de mi región.',
        explora=[texto('Haz una lista de lo que haces en un día normal y cuánto tiempo le dedicas a cada cosa.')],
        aprende=[tabla([['Actividad', 'Horas al día (ejemplo)'], ['Dormir', '9'], ['Estudiar', '6'], ['Jugar', '2'], ['Comer', '2'], ['Ayudar en casa', '1'], ['Leer', '1']]),
                 texto('El <b>calendario</b> organiza los días, las semanas y los meses: ahí anotamos cumpleaños, exámenes, fiestas y vacaciones.'),
                 imagen('d-meses', 70),
                 texto('Los productos también tienen su tiempo. El <b>café</b>: se siembra, tarda unos 2 o 3 años en dar la primera cosecha, se recoge, se despulpa, '
                       'se fermenta, se lava y se seca antes de venderse.')],
        recuerda=['Organizar el tiempo me ayuda a cumplir.', 'Cada producto pasa por varios pasos y toma tiempo.'],
        practica=[unica('¿Dónde anotamos las fechas importantes?', 'En el calendario', ['En la regla']),
                  unica('Si duermo 9 horas, ¿cuántas me quedan despierto en un día?', '15', ['9', '24'])],
        taller=[unica('¿Qué mes viene después de septiembre?', 'Octubre', ['Agosto', 'Noviembre']),
                abierta('Haz un horario de tu semana con estudio, juego, descanso y ayuda en casa.', 8),
                abierta('Elige un producto de tu región y escribe sus pasos de producción en orden.', 6)])

    U[6] = u(
        tema='Somos diversos: los grupos humanos de mi región',
        objetivo='Caracterizar los grupos humanos de mi departamento y reconocer la diversidad cultural como riqueza de Colombia.',
        explora=[imagen('s3-tejedora', 45, 'Una tejedora wayuu'), texto('¿Qué pueblos o comunidades viven en tu departamento?')],
        aprende=[tabla([['Grupo', 'Algunas características'], ['Indígenas', 'pueblos originarios con lenguas propias (wayuu, nasa, embera, pijao…)'],
                        ['Afrodescendientes', 'descendientes de africanos: música, comidas y saberes propios'], ['Raizales', 'afrocaribeños de San Andrés, hablan creole'],
                        ['Rom (gitanos)', 'pueblo con lengua y tradiciones propias'], ['Mestizos y blancos', 'la mayoría de la población']]),
                 imagen('s1-diversidad', 40),
                 texto('Cada grupo aporta su <b>lengua</b>, su <b>organización social</b>, su <b>vivienda</b>, su forma de ver el mundo (<b>cosmovisión</b>) y su forma de usar la tierra.'),
                 texto('En Colombia se hablan unas <b>65 lenguas indígenas</b> además del español. ¡Somos un país diverso!')],
        recuerda=['La diversidad cultural es una riqueza.', 'Todos los grupos tienen los mismos derechos.'],
        practica=[unica('Los raizales viven en…', 'San Andrés y Providencia', ['La Guajira', 'Bogotá']),
                  unica('Los wayuu son un pueblo…', 'indígena', ['raizal', 'gitano'])],
        taller=[unica('¿Qué es la cosmovisión?', 'La forma de ver y explicar el mundo', ['Un tipo de vivienda']),
                vf('En Colombia solo se habla español.', False),
                abierta('Averigua qué grupos étnicos viven en tu departamento y escribe un aporte de uno de ellos.', 6)])

    U[7] = u(
        tema='El gobierno escolar: elegir y ser elegido',
        objetivo='Conocer cómo se elige el gobierno escolar, qué hacen sus representantes y comparar las propuestas de los candidatos a personero.',
        explora=[imagen('s3-votacion', 45), texto('¿Has votado alguna vez en el colegio? ¿Por quién y por qué?')],
        aprende=[tabla([['Cargo u órgano', 'Qué hace'], ['Personero estudiantil', 'defiende los derechos de los estudiantes (lo eligen todos)'],
                        ['Representante de grupo', 'lleva la voz de su salón'], ['Consejo estudiantil', 'reúne a los representantes de los grados'],
                        ['Consejo directivo', 'toma las decisiones importantes del colegio (rector, docentes, padres, estudiantes, exalumnos, sector productivo)']]),
                 texto('Para votar bien: leo las <b>propuestas</b>, pienso si se pueden cumplir y si benefician a todos, y voto en <b>secreto</b>.'),
                 recuadro('Propuestas de dos candidatos', '<p><b>Candidata A:</b> «Haré una campaña para cuidar los baños y pediré más canecas de reciclaje.»<br>'
                          '<b>Candidato B:</b> «Si gano, no habrá tareas nunca más.»</p>', estilo='nota')],
        recuerda=['Elegir y ser elegido es un derecho.', 'Una buena propuesta se puede cumplir y ayuda a todos.'],
        practica=[unica('¿Qué propuesta se puede cumplir?', 'La de la candidata A', ['La del candidato B']),
                  unica('¿Quién defiende los derechos de los estudiantes?', 'El personero', ['El celador', 'El tendero'])],
        taller=[unica('El voto debe ser…', 'secreto y libre', ['obligado por un amigo']),
                unica('¿Quién lleva la voz de mi salón?', 'El representante de grupo', ['El rector']),
                abierta('Escribe una propuesta que harías si fueras candidato a representante de tu salón.', 5)])

    U[8] = u(
        tema='Mi departamento y su gobierno',
        objetivo='Diferenciar las autoridades del departamento y del municipio y explicar cómo el gobierno departamental mejora la vida de la gente.',
        explora=[imagen('s3-gobernacion', 45), texto('¿Cómo se llama tu departamento? ¿Y su capital? ¿Quién es el gobernador?')],
        aprende=[tabla([['', 'Departamento', 'Municipio'], ['Gobierna', 'Gobernador', 'Alcalde'], ['Hace las ordenanzas / acuerdos', 'Asamblea (diputados)', 'Concejo (concejales)'],
                        ['Imparte justicia', 'Jueces y tribunales', 'Jueces']]),
                 texto('Los <b>resguardos indígenas</b> tienen sus propias autoridades: los <b>cabildos</b> y los gobernadores indígenas.'),
                 texto('El gobierno departamental apoya la <b>educación</b>, las <b>vías</b>, la <b>salud</b> y la <b>recreación</b> en los municipios.'),
                 texto('Al gobernador, los diputados, el alcalde y los concejales los elegimos con el <b>voto popular</b> cada 4 años.')],
        recuerda=['Departamento: gobernador y asamblea. Municipio: alcalde y concejo.', 'Votar es la forma de elegir a nuestras autoridades.'],
        practica=[unica('¿Quién gobierna el departamento?', 'El gobernador', ['El alcalde', 'El personero']),
                  unica('Los diputados forman la…', 'Asamblea departamental', ['Concejo municipal'])],
        taller=[unica('¿Quién gobierna el municipio?', 'El alcalde', ['El gobernador']),
                unica('Las autoridades de los resguardos son los…', 'cabildos', ['concejos']),
                abierta('Escribe el nombre de tu departamento, su capital y una obra que haya hecho la gobernación.', 4),
                abierta('Propón una acción que la gobernación podría hacer para la convivencia y la paz en tu municipio.', 4)])
    return U
