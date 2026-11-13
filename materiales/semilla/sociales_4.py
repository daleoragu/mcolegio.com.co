"""Ciencias Sociales 4.º: una guía y un taller por cada uno de los 8 DBA, centrados en Colombia. Los mapas son los oficiales
del IGAC (no se generan con IA). Borradores para que el docente revise."""
from .base import abierta, imagen, recuadro, tabla, texto, unica, unidad, vf


def unidades():
    U = {}

    U[1] = unidad(
        tema='Límites y fronteras de Colombia',
        objetivo='Reconocer los límites de Colombia en el mapa político y la importancia de las fronteras para el intercambio con los países vecinos.',
        explora=[imagen('s4-mapa-colombia-politico', 60, 'Mapa político de Colombia'), texto('¿Con qué países limita Colombia? ¿Con qué mares?')],
        aprende=[tabla([['Punto cardinal', 'Límite terrestre'], ['Oriente (este)', 'Venezuela y Brasil'], ['Sur', 'Perú y Ecuador'], ['Noroccidente', 'Panamá']]),
                 texto('Colombia también tiene <b>fronteras marítimas</b> en el mar Caribe y en el océano Pacífico con países como Panamá, Costa Rica, Nicaragua, Honduras, '
                       'Jamaica, Haití, República Dominicana, Ecuador y Venezuela.'),
                 texto('Las <b>fronteras</b> no solo separan: son lugares de <b>encuentro</b>, comercio, intercambio cultural y familias que viven a ambos lados. '
                       'También hay retos: el contrabando y la migración.')],
        recuerda=['Colombia limita por tierra con 5 países: Venezuela, Brasil, Perú, Ecuador y Panamá.'],
        practica=[unica('¿Con qué país limita Colombia al noroccidente?', 'Panamá', ['Brasil', 'Perú']),
                  unica('¿Cuántos países limitan con Colombia por tierra?', '5', ['3', '8', '2'])],
        taller=[unica('Venezuela está al… de Colombia.', 'oriente', ['occidente', 'sur']),
                unica('En la frontera se da…', 'comercio e intercambio cultural', ['solo guerra']),
                abierta('Elige un país vecino y escribe dos cosas que Colombia comparte con él.', 5)])

    U[2] = unidad(
        tema='Lo urbano y lo rural',
        objetivo='Diferenciar el medio urbano del rural por la concentración de población y el uso del suelo, y sus cambios recientes.',
        explora=[imagen('s4-ciudad-campo', 55), texto('¿Qué diferencias ves entre las dos mitades? ¿En cuál vives tú?')],
        aprende=[tabla([['', 'Urbano', 'Rural'], ['Población', 'mucha gente en poco espacio', 'poca gente en mucho espacio'],
                        ['Uso del suelo', 'comercial, industrial, residencial, educativo, deportivo', 'agrícola, ganadero, forestal, minero'],
                        ['Servicios', 'más hospitales, colegios y transporte', 'menos servicios, más lejos']]),
                 texto('En Colombia, cerca de <b>3 de cada 4 personas</b> viven en zonas urbanas. En las últimas décadas muchas personas se fueron del campo a la ciudad.'),
                 texto('El uso del suelo cambia: potreros que se vuelven barrios, bosques que se vuelven cultivos.')],
        recuerda=['Urbano: ciudad. Rural: campo.', 'La mayoría de los colombianos vive en ciudades.'],
        practica=[unica('El uso agrícola del suelo es típico de la zona…', 'rural', ['urbana']),
                  unica('¿Dónde hay más concentración de población?', 'En la zona urbana', ['En la zona rural'])],
        taller=[unica('Una zona industrial está en el medio…', 'urbano', ['rural']),
                vf('En Colombia la mayoría de la gente vive en el campo.', False),
                abierta('Escribe una ventaja y una desventaja de vivir en la ciudad y en el campo.', 6)])

    U[3] = unidad(
        tema='La tecnología cambió nuestra vida',
        objetivo='Comparar la vida antes y después de la electricidad, el acueducto y las comunicaciones, y relacionar la tecnología en salud con el bienestar.',
        explora=[imagen('s4-sin-luz', 45, 'Antes de la luz eléctrica'), texto('¿Cómo sería tu día sin luz eléctrica, sin agua en la llave y sin celular?')],
        aprende=[tabla([['Antes', 'Ahora'], ['velas y lámparas de petróleo', 'luz eléctrica'], ['agua del río o del pozo', 'acueducto'], ['letrinas', 'alcantarillado'],
                        ['cartas que tardaban semanas', 'mensajes instantáneos']]),
                 texto('Las <b>vacunas</b>, los <b>hospitales</b> y los <b>medicamentos</b> han hecho que la gente viva más años y con mejor salud.'),
                 texto('Los <b>medios de comunicación</b> permiten conocer lo que pasa en el país, opinar y participar en la vida política.')],
        recuerda=['La tecnología mejoró la salud y la comunicación.', 'Todavía hay comunidades sin acceso a estos servicios.'],
        practica=[unica('Antes del acueducto, el agua se traía…', 'del río o del pozo', ['de la llave']),
                  unica('Las vacunas ayudan a…', 'prevenir enfermedades', ['tener más tareas'])],
        taller=[unica('El alcantarillado sirve para…', 'llevar las aguas sucias', ['traer agua potable']),
                vf('Todas las veredas de Colombia tienen internet.', False),
                abierta('Entrevista a un adulto mayor: ¿cómo se comunicaba su familia cuando era niño?', 6)])

    U[4] = unidad(
        tema='Las culturas ancestrales de Colombia',
        objetivo='Conocer los pueblos que habitaban el territorio a la llegada de los españoles, su organización y sus legados.',
        explora=[imagen('s4-orfebreria', 25, 'Poporo quimbaya'), texto('¿Quién hizo esta pieza? ¿Qué nos dice de su cultura?')],
        aprende=[tabla([['Pueblo', 'Dónde vivían', 'Se destacaban en'], ['Muiscas', 'altiplano cundiboyacense', 'agricultura, comercio de sal y esmeraldas, orfebrería'],
                        ['Taironas', 'Sierra Nevada de Santa Marta', 'caminos y terrazas de piedra, orfebrería'],
                        ['Quimbayas', 'zona del Eje Cafetero', 'orfebrería en oro (el poporo quimbaya)'], ['Zenúes', 'llanuras del Caribe (Sinú)', 'canales para controlar las inundaciones'],
                        ['San Agustín', 'sur del Huila', 'esculturas monumentales en piedra']]),
                 texto('Las grandes <b>familias lingüísticas</b> de entonces incluían la chibcha, la caribe y la arawak.'),
                 texto('Su <b>legado</b>: el maíz, la papa, la yuca, el tejido, la cerámica, palabras como «chicha» o «totuma», y el respeto por la naturaleza.')],
        recuerda=['Muiscas, taironas, quimbayas, zenúes: grandes culturas ancestrales.', 'Sus descendientes viven hoy en Colombia.'],
        practica=[unica('El poporo quimbaya es una obra de…', 'orfebrería en oro', ['cerámica', 'tejido']),
                  unica('Los zenúes construyeron…', 'canales para controlar las inundaciones', ['pirámides de piedra'])],
        taller=[unica('Los taironas vivían en…', 'la Sierra Nevada de Santa Marta', ['los Llanos']),
                unica('¿Qué cultivo es herencia de los pueblos ancestrales?', 'El maíz', ['El trigo', 'El café']),
                abierta('Investiga cómo viven hoy los descendientes de uno de estos pueblos (por ejemplo, los kogui, arhuaco o wiwa).', 6)])

    U[5] = unidad(
        tema='Colombia, un país diverso',
        objetivo='Valorar la diversidad étnica y cultural: afrodescendientes, raizales, mestizos, indígenas, rom y blancos.',
        explora=[imagen('s1-diversidad', 45), texto('¿Qué grupos culturales conoces? ¿Qué aportan a tu vida diaria?')],
        aprende=[tabla([['Grupo', 'Aportes'], ['Indígenas', 'lenguas, conocimiento de plantas medicinales, agricultura'],
                        ['Afrodescendientes', 'música (currulao, champeta), cocina, medicina tradicional, San Basilio de Palenque'],
                        ['Raizales', 'lengua creole, música y tradiciones del Caribe insular'], ['Rom (gitanos)', 'oficios artesanales, lengua romaní'],
                        ['Mestizos y blancos', 'mezcla de tradiciones europeas, indígenas y africanas']]),
                 texto('La <b>Constitución de 1991</b> reconoce que Colombia es un país <b>pluriétnico y multicultural</b>. Las culturas han intercambiado saberes por siglos: '
                       'el sancocho, la cumbia y el vallenato son mezclas de varias herencias.')],
        recuerda=['Colombia es pluriétnica y multicultural.', 'La diversidad nos enriquece.'],
        practica=[unica('San Basilio de Palenque es una comunidad…', 'afrodescendiente', ['indígena', 'raizal']),
                  unica('La Constitución dice que Colombia es…', 'pluriétnica y multicultural', ['de una sola cultura'])],
        taller=[unica('Los raizales hablan…', 'creole', ['romaní', 'wayuunaiki']),
                vf('La cumbia mezcla herencias indígenas, africanas y europeas.', True),
                abierta('Escribe una costumbre de tu familia y averigua de qué cultura viene.', 5)])

    U[6] = unidad(
        tema='La división de poderes en Colombia',
        objetivo='Diferenciar las ramas del poder público y sus funciones, y la importancia del voto.',
        explora=[texto('¿Qué pasaría si una sola persona hiciera las leyes, gobernara y juzgara al mismo tiempo?')],
        aprende=[imagen('d-ramas', 65, 'Las tres ramas del poder público'),
                 imagen('s4-congreso', 40, 'El Congreso de la República'),
                 texto('La división de poderes evita que alguien abuse del poder: cada rama <b>controla</b> a las otras.'),
                 tabla([['Cargo de elección popular', 'Qué hace'], ['Presidente', 'gobierna el país'], ['Congresistas', 'hacen las leyes'], ['Gobernador', 'gobierna el departamento'],
                        ['Alcalde', 'gobierna el municipio'], ['Concejales', 'hacen los acuerdos del municipio'], ['Personero estudiantil', 'defiende los derechos de los estudiantes']]),
                 texto('El <b>voto</b> es el mecanismo para elegir a quienes nos representan.')],
        recuerda=['Legislativa: leyes. Ejecutiva: gobierna. Judicial: justicia.', 'Votar es participar en la democracia.'],
        practica=[unica('¿Qué rama hace las leyes?', 'Legislativa', ['Ejecutiva', 'Judicial']),
                  unica('El presidente pertenece a la rama…', 'ejecutiva', ['judicial', 'legislativa'])],
        taller=[unica('Los jueces pertenecen a la rama…', 'judicial', ['ejecutiva']),
                unica('La división de poderes sirve para…', 'evitar abusos de poder', ['que nadie gobierne']),
                abierta('Explica con tus palabras por qué es importante votar.', 4)])

    U[7] = unidad(
        tema='Los derechos de los niños y las niñas',
        objetivo='Conocer los derechos de la niñez, mis deberes y a quién acudir para proteger mis derechos.',
        explora=[imagen('s4-derechos-ninos', 50), texto('¿Qué derechos ves en las imágenes?')],
        aprende=[tabla([['Derecho', 'Deber que lo acompaña'], ['a la educación', 'estudiar y respetar a mis compañeros'], ['a la salud', 'cuidar mi cuerpo'],
                        ['al juego y la recreación', 'compartir y respetar las reglas'], ['a un nombre y una nacionalidad', 'respetar los símbolos patrios'],
                        ['a ser protegido contra el maltrato', 'no maltratar a otros']]),
                 texto('Los derechos de la niñez están en la Constitución (artículo 44) y en el Código de Infancia y Adolescencia.'),
                 recuadro('¿A quién acudo?', '<p>A mi familia, mis profesores, el orientador o el comité de convivencia del colegio, la Comisaría de Familia, '
                          'la Policía de Infancia y Adolescencia y el ICBF (Línea 141).</p>', estilo='recuerda')],
        recuerda=['Todos los niños y las niñas tienen derechos.', 'Con los derechos vienen deberes.'],
        practica=[unica('¿Qué artículo de la Constitución protege los derechos de los niños?', 'El 44', ['El 1', 'El 100']),
                  unica('Si un niño es maltratado, se puede acudir a…', 'la Comisaría de Familia o el ICBF', ['nadie'])],
        taller=[unica('El derecho a la educación va con el deber de…', 'estudiar y respetar', ['no ir al colegio']),
                vf('Los niños también tienen deberes.', True),
                abierta('Escribe un caso donde se vulnera un derecho de un niño y cómo se podría defender.', 6)])

    U[8] = unidad(
        tema='Necesidades básicas y bienestar',
        objetivo='Identificar las necesidades básicas (vivienda, alimentación, salud, educación y empleo) y los factores que influyen en su satisfacción.',
        explora=[texto('Haz una lista de lo que necesita una familia para vivir bien. ¿Qué es lo más importante?')],
        aprende=[tabla([['Necesidad básica', 'Se satisface con…'], ['Alimentación', 'comida suficiente y nutritiva'], ['Vivienda', 'una casa segura con servicios'],
                        ['Salud', 'acceso a médicos, vacunas y agua potable'], ['Educación', 'colegio cercano y de calidad'], ['Empleo', 'trabajo digno para los adultos']]),
                 texto('Cuando las necesidades básicas no se satisfacen hay <b>pobreza</b>. Influyen factores <b>económicos</b> (ingresos, empleo), <b>sociales</b> (educación, salud) y '
                       '<b>políticos</b> (las decisiones de los gobiernos).'),
                 texto('El Estado, las familias y las comunidades trabajan juntos para mejorar el bienestar.')],
        recuerda=['Las necesidades básicas son derechos.', 'El bienestar es individual, familiar y colectivo.'],
        practica=[unica('¿Cuál es una necesidad básica?', 'La alimentación', ['Un celular de último modelo']),
                  unica('Si los adultos no tienen empleo, la familia…', 'tiene dificultades para cubrir sus necesidades', ['no se afecta'])],
        taller=[unica('El agua potable se relaciona con la necesidad de…', 'salud', ['transporte']),
                abierta('Ordena de la más importante a la menos importante: vivienda, alimentación, salud, educación y empleo. Explica tu orden.', 6),
                abierta('Propón una acción para mejorar el bienestar en tu barrio o vereda.', 4)])
    return U
