"""Ciencias Sociales 5.º: una guía y un taller por cada uno de los 8 DBA: territorio, posición geográfica, comunicación,
Colonia, Independencia, siglo XX, Constitución y Derechos Humanos. Mapas oficiales del IGAC. Borradores para que el docente revise."""
from .base import abierta, imagen, recuadro, tabla, texto, unica, unidad, vf


def unidades():
    U = {}

    U[1] = unidad(
        tema='La organización territorial y las regiones de Colombia',
        objetivo='Explicar cómo se divide el territorio colombiano y diferenciar las regiones naturales.',
        explora=[imagen('s5-regiones-naturales', 55, 'Regiones naturales de Colombia'), texto('¿En qué región natural está tu municipio?')],
        aprende=[tabla([['División', 'Qué es'], ['Vereda / corregimiento', 'partes rurales del municipio'], ['Municipio', 'unidad básica, con alcalde y concejo'],
                        ['Área metropolitana', 'municipios unidos a una gran ciudad'], ['Departamento', 'agrupa municipios; hay 32 departamentos'],
                        ['Distrito', 'municipios con régimen especial (Bogotá D. C., Barranquilla, Cartagena, Santa Marta, Buenaventura…)'],
                        ['Territorios indígenas', 'resguardos con autoridades propias']]),
                 tabla([['Región natural', 'Características'], ['Andina', 'montañas (tres cordilleras), la más poblada'], ['Caribe', 'llanuras, costa y la Sierra Nevada'],
                        ['Pacífica', 'selva muy lluviosa, costa del Pacífico'], ['Orinoquía', 'llanuras, ganadería'], ['Amazonía', 'selva húmeda, gran biodiversidad'],
                        ['Insular', 'islas: San Andrés, Providencia, Gorgona, Malpelo']])],
        recuerda=['Colombia tiene 32 departamentos y Bogotá, Distrito Capital.', 'Seis regiones naturales.'],
        practica=[unica('¿Cuál es la región más poblada?', 'Andina', ['Amazonía', 'Insular']), unica('San Andrés pertenece a la región…', 'Insular', ['Pacífica', 'Caribe continental'])],
        taller=[unica('¿Cuántos departamentos tiene Colombia?', '32', ['22', '50', '10']),
                unica('La región con llanuras y ganadería es la…', 'Orinoquía', ['Andina', 'Pacífica']),
                abierta('Escribe en qué región natural, departamento y municipio vives, y una característica de tu región.', 4)])

    U[2] = unidad(
        tema='La posición de Colombia en el mundo',
        objetivo='Ubicar a Colombia con latitud y longitud, y relacionar su posición, altitud y cercanía al mar con su diversidad de climas y su economía.',
        explora=[imagen('s5-mapa-coordenadas', 50), texto('Colombia está cerca de la línea del ecuador. ¿Por qué entonces hay páramos tan fríos?')],
        aprende=[texto('<b>Posición astronómica</b>: Colombia está en la zona ecuatorial (entre el trópico de Cáncer y el de Capricornio). La línea del ecuador cruza el sur del país.'),
                 texto('<b>Posición geográfica</b>: en la esquina noroccidental de Suramérica, con costas en dos océanos, cerca de Centroamérica y del canal de Panamá. '
                       'Eso favorece el comercio.'),
                 tabla([['Piso térmico', 'Altitud aproximada', 'Clima'], ['Cálido', '0 a 1 000 m', 'más de 24 °C'], ['Templado', '1 000 a 2 000 m', '17 a 24 °C'],
                        ['Frío', '2 000 a 3 000 m', '12 a 17 °C'], ['Páramo', 'más de 3 000 m', 'menos de 12 °C']]),
                 texto('La <b>órbita geoestacionaria</b> está sobre el ecuador: allí se ubican satélites de comunicaciones, por eso es importante para el país.')],
        recuerda=['Mientras más alto, más frío: los pisos térmicos.', 'Dos océanos y cerca de Panamá: ventajas para el comercio.'],
        practica=[unica('¿Por qué hay páramos en Colombia si está en el ecuador?', 'Por la altitud de las montañas', ['Por la nieve del polo']),
                  unica('Un municipio a 2 500 m de altura tiene clima…', 'frío', ['cálido', 'templado'])],
        taller=[unica('Colombia está en la esquina… de Suramérica.', 'noroccidental', ['suroriental']),
                unica('¿Qué piso térmico tiene más de 24 °C?', 'Cálido', ['Páramo', 'Frío']),
                abierta('Busca la altitud de tu municipio y di en qué piso térmico está.', 3)])

    U[3] = unidad(
        tema='Cómo nos comunicamos: de la carta al celular',
        objetivo='Explicar cómo los avances en la comunicación han cambiado la forma en que nos relacionamos y accedemos a la información.',
        explora=[imagen('s5-telegrafo', 55), texto('¿Cuál de estos aparatos conocen tus abuelos? ¿Cuál usas tú?')],
        aprende=[tabla([['Época', 'Medios'], ['Comienzos del siglo XX', 'cartas, telégrafo, periódicos'], ['Mediados del siglo XX', 'radio, teléfono fijo, televisión'],
                        ['Finales del siglo XX', 'computadores, internet'], ['Siglo XXI', 'celulares inteligentes, redes sociales, videollamadas']]),
                 texto('Hoy la información llega <b>al instante</b> y desde cualquier lugar. Ventajas: estudiar, trabajar y hablar con familiares lejanos. '
                       'Retos: noticias falsas, ciberacoso, poco contacto cara a cara.')],
        recuerda=['La comunicación cambió nuestra forma de relacionarnos.', 'Uso la tecnología con responsabilidad.'],
        practica=[unica('¿Qué medio usaban para comunicarse rápido a larga distancia a comienzos del siglo XX?', 'El telégrafo', ['El celular']),
                  unica('Un reto de las redes sociales es…', 'las noticias falsas', ['ver fotos'])],
        taller=[vf('Hoy podemos hablar con alguien en otro país al instante.', True),
                abierta('Entrevista a tus padres: ¿cómo se comunicaban cuando eran niños? Compáralo con cómo te comunicas tú.', 8)])

    U[4] = unidad(
        tema='La Colonia en la Nueva Granada',
        objetivo='Analizar la organización política, económica y social de la Nueva Granada durante la Colonia.',
        explora=[imagen('s5-colonia', 50), texto('¿Qué personas ves en la plaza? ¿Tenían todas los mismos derechos?')],
        aprende=[tabla([['Institución', 'Función'], ['Consejo de Indias (en España)', 'gobernaba las colonias de América'], ['Casa de Contratación (Sevilla)', 'controlaba el comercio'],
                        ['Virreinato', 'gobierno de la Nueva Granada, con un virrey'], ['Real Audiencia', 'impartía justicia'], ['Cabildo', 'gobierno de las ciudades']]),
                 tabla([['Forma de trabajo', 'Qué era'], ['Encomienda', 'un español recibía indígenas que debían trabajarle y pagarle tributo'],
                        ['Mita', 'trabajo obligatorio por turnos, sobre todo en minas'], ['Resguardo', 'tierras asignadas a las comunidades indígenas']]),
                 texto('La sociedad estaba dividida por origen: <b>españoles peninsulares</b> (los de más poder), <b>criollos</b>, <b>mestizos</b>, <b>indígenas</b> y <b>africanos esclavizados</b>. '
                       'Esa desigualdad dejó huellas que todavía existen.')],
        recuerda=['La Colonia fue una época de dominio español y gran desigualdad.'],
        practica=[unica('¿Quién gobernaba el virreinato?', 'El virrey', ['El cacique', 'El alcalde']), unica('El trabajo obligatorio por turnos en las minas era la…', 'mita', ['encomienda', 'resguardo'])],
        taller=[unica('¿Qué grupo tenía más poder en la Colonia?', 'Los españoles peninsulares', ['Los indígenas', 'Los esclavizados']),
                unica('Los resguardos eran…', 'tierras para comunidades indígenas', ['fábricas']),
                abierta('Explica con tus palabras por qué la sociedad colonial era desigual.', 6)])

    U[5] = unidad(
        tema='Nace la República de Colombia',
        objetivo='Explicar los antecedentes y los hechos de la Independencia, el nacimiento de la República y los cambios de las fronteras.',
        explora=[imagen('s5-independencia', 50, 'Puente de Boyacá, 1819'), texto('¿Por qué celebramos el 20 de julio y el 7 de agosto?')],
        aprende=[imagen('d-tiempo-1781.Revolución de los|Comuneros-1810.Grito de|Independencia-1819.Batalla de|Boyacá-1830.Fin de la|Gran Colombia-1903.Separación|de Panamá', 90,
                        'Línea de tiempo'),
                 texto('<b>Antecedentes</b>: la Revolución de los Comuneros (1781), las ideas de la Ilustración y la independencia de Estados Unidos y la Revolución francesa.'),
                 texto('El <b>20 de julio de 1810</b> se dio el Grito de Independencia en Santafé. El <b>7 de agosto de 1819</b>, con la Batalla de Boyacá, se consolidó la independencia.'),
                 texto('Nació la <b>Gran Colombia</b> (Colombia, Venezuela, Ecuador y Panamá), que se disolvió en 1830. En <b>1903</b> Panamá se separó de Colombia.')],
        recuerda=['20 de julio de 1810 y 7 de agosto de 1819.', 'Las fronteras de Colombia han cambiado con el tiempo.'],
        practica=[unica('¿Qué se celebra el 7 de agosto?', 'La Batalla de Boyacá', ['El Grito de Independencia', 'La Constitución de 1991']),
                  unica('¿En qué año se separó Panamá?', '1903', ['1810', '1991'])],
        taller=[unica('La Gran Colombia estaba formada por…', 'Colombia, Venezuela, Ecuador y Panamá', ['Colombia y Brasil']),
                unica('Un antecedente de la Independencia fue…', 'la Revolución de los Comuneros', ['la Constitución de 1991']),
                abierta('Elige un prócer o una prócer de la Independencia (por ejemplo, Policarpa Salavarrieta o Antonio Nariño) y escribe qué hizo.', 6)])

    U[6] = unidad(
        tema='Colombia en la primera mitad del siglo XX',
        objetivo='Analizar los cambios por la industria y las comunicaciones (radio, prensa, ferrocarriles) y las consecuencias de los conflictos políticos.',
        explora=[imagen('s5-ferrocarril', 45), texto('¿Cómo cambió la vida cuando llegó el tren a los pueblos?')],
        aprende=[texto('A comienzos del siglo XX llegaron los <b>ferrocarriles</b>, las fábricas de <b>telas</b> (telares), la <b>radio</b> y más <b>periódicos</b>. El café se volvió el principal producto de exportación.'),
                 texto('Los partidos <b>Liberal</b> y <b>Conservador</b> dominaban la política. Sus enfrentamientos llevaron a la época conocida como <b>La Violencia</b> (desde 1948), '
                       'que causó muchas muertes y desplazamientos del campo a la ciudad.'),
                 texto('Aprender de esa historia nos ayuda a valorar la <b>convivencia pacífica</b> y el respeto por quien piensa distinto.')],
        recuerda=['Ferrocarril, radio, prensa y fábricas transformaron el país.', 'La intolerancia política trajo violencia.'],
        practica=[unica('¿Qué producto se volvió el principal de exportación?', 'El café', ['El petróleo', 'El banano']),
                  unica('¿Qué partidos dominaban la política?', 'Liberal y Conservador', ['Ninguno'])],
        taller=[unica('La radio sirvió para…', 'informar y unir al país', ['viajar']),
                unica('Una consecuencia de La Violencia fue…', 'el desplazamiento del campo a la ciudad', ['más turismo']),
                abierta('Pregunta a un abuelo qué recuerda de su infancia sobre la radio o el tren.', 6)])

    U[7] = unidad(
        tema='La Constitución: derechos, deberes y convivencia',
        objetivo='Reconocer las ventajas de vivir en un Estado democrático, identificar los derechos fundamentales y compararlos con el manual de convivencia.',
        explora=[imagen('s5-constitucion', 30), texto('¿Qué es la Constitución? ¿Por qué se llama la «ley de leyes»?')],
        aprende=[texto('La <b>Constitución Política de 1991</b> es la norma más importante de Colombia. Dice cómo se organiza el Estado y cuáles son nuestros derechos y deberes.'),
                 tabla([['Algunos derechos fundamentales (Título II, cap. 1)', 'Artículo'], ['Derecho a la vida', '11'], ['Igualdad', '13'], ['Libre desarrollo de la personalidad', '16'],
                        ['Libertad de expresión', '20'], ['Derecho de petición', '23']]),
                 texto('En el colegio, el <b>manual de convivencia</b> concreta derechos y deberes: si tengo derecho a la educación, tengo el deber de respetar a mis compañeros.'),
                 texto('La <b>acción de tutela</b> protege los derechos fundamentales cuando se vulneran.')],
        recuerda=['La Constitución de 1991 es la ley de leyes.', 'Derechos y deberes van juntos.'],
        practica=[unica('¿En qué año se escribió la Constitución actual?', '1991', ['1886', '1810']), unica('El derecho a la vida está en el artículo…', '11', ['44', '1'])],
        taller=[unica('Para proteger un derecho fundamental se usa la…', 'acción de tutela', ['multa', 'votación']),
                unica('En el colegio, los derechos y deberes están en…', 'el manual de convivencia', ['el horario']),
                abierta('Elige un derecho del manual de convivencia de tu colegio y escribe el deber que lo acompaña.', 4)])

    U[8] = unidad(
        tema='Organizaciones que defienden los Derechos Humanos',
        objetivo='Conocer las organizaciones comunitarias y las instituciones que protegen los Derechos Humanos y los mecanismos para defenderlos.',
        explora=[imagen('s5-junta-accion', 45), texto('¿Qué hace la junta de acción comunal de tu barrio o vereda?')],
        aprende=[tabla([['Organización', 'Qué hace'], ['Junta de acción comunal', 'organiza proyectos para el barrio o la vereda'], ['Cabildo indígena', 'gobierna y protege a la comunidad indígena'],
                        ['Consejo comunitario', 'administra los territorios de comunidades negras'], ['Personería municipal', 'defiende los derechos de las personas en el municipio'],
                        ['Defensoría del Pueblo', 'vigila y protege los Derechos Humanos en todo el país']]),
                 texto('Los <b>Derechos Humanos</b> son de todas las personas, sin importar su origen, sexo, religión o forma de pensar.'),
                 texto('<b>Mecanismos de participación</b>: la tutela, el derecho de petición, el voto y la participación en juntas y cabildos.')],
        recuerda=['La Personería y la Defensoría protegen los Derechos Humanos.', 'Las organizaciones comunitarias fortalecen la comunidad.'],
        practica=[unica('¿Quién defiende los derechos de las personas en el municipio?', 'La Personería', ['El concejo de deportes']),
                  unica('Los cabildos son autoridades de…', 'comunidades indígenas', ['empresas'])],
        taller=[unica('La Defensoría del Pueblo actúa…', 'en todo el país', ['solo en un barrio']),
                vf('Los Derechos Humanos son solo para algunas personas.', False),
                abierta('Investiga un proyecto de la junta de acción comunal de tu barrio o vereda y descríbelo.', 6)])
    return U
