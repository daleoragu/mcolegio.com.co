"""Ciencias Sociales 8.º: una guía y un taller por cada uno de los 8 DBA: cooperación entre Estados, migraciones,
capitalismo, imperialismo, independencias, tecnología en el siglo XIX, dignidad humana y organizaciones sociales."""
from .base import abierta, imagen, tabla, texto, unica, unidad, vf


def unidades():
    U = {}

    U[1] = unidad(
        tema='Cooperación entre Estados',
        objetivo='Evaluar la influencia de la cooperación económica y política entre Estados en la actualidad.',
        explora=[texto('¿Qué ganan los países cuando se unen? ¿Qué pierden?')],
        aprende=[tabla([['Organización', 'Miembros', 'Objetivo'], ['Unión Europea', '27 países de Europa', 'mercado común, moneda (euro) en muchos, libre circulación'],
                        ['MERCOSUR', 'países de Suramérica (Argentina, Brasil, Paraguay, Uruguay…)', 'integración comercial'], ['OTAN', 'Europa y Norteamérica', 'defensa militar común'],
                        ['Comunidad Andina', 'Colombia, Ecuador, Perú, Bolivia', 'integración andina'], ['Alianza del Pacífico', 'Colombia, Chile, México, Perú', 'comercio con Asia-Pacífico']]),
                 texto('Ventajas: más comercio, inversión, cooperación en salud y educación. Retos: pérdida de autonomía, desigualdad entre miembros.')],
        recuerda=['Colombia hace parte de la Comunidad Andina y de la Alianza del Pacífico.'],
        practica=[unica('¿Qué moneda usan muchos países de la Unión Europea?', 'El euro', ['El dólar']), unica('La OTAN es una alianza…', 'militar', ['comercial'])],
        taller=[unica('¿A qué organización pertenece Colombia?', 'Comunidad Andina', ['Unión Europea']), abierta('Investiga un beneficio y un reto para Colombia de pertenecer a la Alianza del Pacífico.', 6)])

    U[2] = unidad(
        tema='Las migraciones en el mundo',
        objetivo='Comprender las migraciones actuales y cómo afectan a los países de origen y a los receptores.',
        explora=[texto('¿Conoces personas que hayan llegado de otro país a tu municipio, o que se hayan ido? ¿Por qué migraron?')],
        aprende=[texto('Hoy hay grandes migraciones hacia Europa (desde África y Medio Oriente), hacia Estados Unidos (desde Centroamérica y México) y en Suramérica (desde Venezuela hacia Colombia y otros países).'),
                 tabla([['Causas', 'Efectos en el país receptor', 'Efectos en el país de origen'], ['económicas, violencia, persecución, clima', 'mano de obra, diversidad cultural; retos en servicios',
                                                                                                     'remesas; pérdida de población joven']]),
                 texto('El <b>Índice de Desarrollo Humano (IDH)</b> mide salud, educación e ingresos: muchos migrantes van hacia países con IDH más alto.')],
        recuerda=['Migrar es un derecho humano; la xenofobia es discriminación.'],
        practica=[unica('El dinero que los migrantes envían a sus familias se llama…', 'remesas', ['impuestos']), unica('El IDH mide…', 'salud, educación e ingresos', ['solo el tamaño del país'])],
        taller=[vf('Colombia ha recibido a muchos migrantes venezolanos en los últimos años.', True),
                abierta('Entrevista a una familia migrante (o lee un testimonio) y describe sus causas y retos.', 8)])

    U[3] = unidad(
        tema='El capitalismo',
        objetivo='Analizar los cambios que produjo el surgimiento del capitalismo en Europa y sus características actuales.',
        explora=[imagen('s8-fabrica', 45, 'Una fábrica de la Revolución Industrial'), texto('¿Cómo cambió el trabajo cuando aparecieron las fábricas?')],
        aprende=[texto('La <b>Revolución Industrial</b> (Inglaterra, finales del siglo XVIII) trajo la máquina de vapor, las fábricas y el ferrocarril. Muchos campesinos se volvieron obreros en las ciudades.'),
                 tabla([['Característica del capitalismo', 'Qué es'], ['Propiedad privada', 'los medios de producción tienen dueños particulares'], ['Libre competencia', 'empresas compiten por los clientes'],
                        ['Capital', 'dinero y bienes que se invierten para producir más'], ['Mercado', 'los precios dependen de la oferta y la demanda'], ['Trabajo asalariado', 'se trabaja a cambio de un salario']]),
                 texto('Sigue vigente porque se ha adaptado (Estado de bienestar, regulaciones), aunque genera debates por la desigualdad.')],
        recuerda=['Revolución Industrial → capitalismo industrial.'],
        practica=[unica('¿Dónde empezó la Revolución Industrial?', 'Inglaterra', ['Francia', 'Colombia']), unica('Si hay mucha oferta y poca demanda, el precio…', 'baja', ['sube'])],
        taller=[unica('Trabajar a cambio de un salario es…', 'trabajo asalariado', ['libre competencia']),
                abierta('Explica una ventaja y una desventaja del capitalismo con ejemplos de tu entorno.', 6)])

    U[4] = unidad(
        tema='Imperialismo: ayer y hoy',
        objetivo='Analizar la expansión territorial europea del siglo XIX y las nuevas formas de imperialismo.',
        explora=[texto('¿Por qué en muchos países de África se habla francés o inglés?')],
        aprende=[texto('En el siglo XIX, potencias europeas (Reino Unido, Francia, Alemania, Bélgica…) se repartieron <b>África</b> y gran parte de <b>Asia</b> (Conferencia de Berlín, 1884-1885) para obtener materias primas y mercados.'),
                 texto('El crecimiento económico europeo se apoyó en la explotación de esas colonias. Las fronteras trazadas sin tener en cuenta a los pueblos causaron conflictos que duran hasta hoy.'),
                 texto('<b>Imperialismo contemporáneo</b>: influencia económica, cultural y tecnológica de grandes potencias y corporaciones sobre otros países.')],
        recuerda=['La Conferencia de Berlín repartió África.'],
        practica=[unica('La Conferencia de Berlín (1884-1885) repartió…', 'África', ['América']), unica('Las potencias buscaban en las colonias…', 'materias primas y mercados', ['turismo'])],
        taller=[abierta('Busca un ejemplo actual de influencia de una gran potencia o empresa sobre otro país y explícalo.', 6)])

    U[5] = unidad(
        tema='Las independencias americanas',
        objetivo='Comprender cómo se produjeron las independencias de las colonias americanas y la influencia de las revoluciones Francesa e Industrial.',
        explora=[texto('¿Qué tienen en común el 4 de julio de 1776, el 14 de julio de 1789 y el 20 de julio de 1810?')],
        aprende=[imagen('d-tiempo-1776.Independencia de|Estados Unidos-1789.Revolución|Francesa-1804.Independencia|de Haití-1810.Grito de|Independencia-1819.Batalla de|Boyacá', 85),
                 texto('La <b>Revolución Francesa</b> difundió la <b>Declaración de los Derechos del Hombre y del Ciudadano</b>, la <b>soberanía popular</b> y la <b>división de poderes</b>. '
                       'La Revolución Industrial cambió el comercio y los intereses de Inglaterra en América.'),
                 texto('<b>Haití</b> (1804) fue la primera república independiente de América Latina y abolió la esclavitud. En la Nueva Granada, los criollos lideraron la independencia.')],
        recuerda=['Ilustración + revoluciones → independencias.'],
        practica=[unica('¿Cuál fue la primera república independiente de América Latina?', 'Haití', ['Colombia', 'Argentina']),
                  unica('La Revolución Francesa difundió…', 'la soberanía popular', ['el absolutismo'])],
        taller=[unica('La independencia de Estados Unidos fue en…', '1776', ['1810', '1789']), abierta('Explica cómo influyeron las ideas de la Revolución Francesa en los próceres neogranadinos.', 6)])

    U[6] = unidad(
        tema='Tecnología y cambio en la Colombia del siglo XIX',
        objetivo='Evaluar el impacto del telégrafo, el correo, el ferrocarril, el barco de vapor, la industria textil y la electricidad en la Colombia del siglo XIX.',
        explora=[texto('Un viaje de Bogotá a la costa podía tardar semanas en el siglo XIX. ¿Qué lo cambió?')],
        aprende=[tabla([['Avance', 'Impacto'], ['Barco de vapor', 'navegación por el río Magdalena, comercio con la costa'], ['Telégrafo', 'comunicación rápida entre ciudades (desde 1865)'],
                        ['Ferrocarril', 'transporte de café y mercancías; el de Panamá (1855)'], ['Industria textil', 'fábricas en Antioquia y Santander'], ['Electricidad', 'alumbrado en Bogotá a finales del siglo']]),
                 texto('La industrialización hizo crecer las ciudades, surgieron obreros asalariados y nuevas clases sociales.')],
        recuerda=['El río Magdalena fue la gran vía de comunicación del siglo XIX.'],
        practica=[unica('¿Por qué río navegaban los barcos de vapor?', 'El Magdalena', ['El Amazonas']), unica('El telégrafo permitió…', 'comunicación rápida a distancia', ['transportar café'])],
        taller=[unica('La industria textil creció en…', 'Antioquia y Santander', ['San Andrés']), abierta('Compara el transporte de tu región en el siglo XIX con el de hoy.', 6)])

    U[7] = unidad(
        tema='Hechos para la dignidad humana',
        objetivo='Evaluar hechos trascendentales como la abolición de la esclavitud y los derechos de las mujeres y las minorías, y describir las discriminaciones que persisten.',
        explora=[texto('¿Desde cuándo pueden votar las mujeres en Colombia? ¿Desde cuándo está abolida la esclavitud?')],
        aprende=[tabla([['Hecho', 'Año en Colombia'], ['Ley de libertad de vientres', '1821'], ['Abolición de la esclavitud', '1851 (vigente desde 1852)'], ['Voto femenino (aprobado)', '1954'],
                        ['Primera votación de las mujeres', '1957'], ['Constitución pluriétnica y multicultural', '1991']]),
                 texto('Aunque hay leyes, persisten la <b>discriminación</b> y la <b>exclusión</b> por género, etnia, orientación sexual, discapacidad u origen; generan pobreza y violencia.')],
        recuerda=['La esclavitud se abolió en 1851; las mujeres votaron por primera vez en 1957.'],
        practica=[unica('¿En qué año se abolió la esclavitud en Colombia?', '1851', ['1810', '1991']), unica('¿Cuándo votaron por primera vez las mujeres en Colombia?', '1957', ['1851', '1810'])],
        taller=[vf('La discriminación desapareció por completo con las leyes.', False), abierta('Investiga un caso actual de vulneración de derechos de una minoría y propón una acción.', 8)])

    U[8] = unidad(
        tema='Organizaciones sociales y derechos colectivos',
        objetivo='Comprender el papel de asociaciones, gremios, sindicatos y movimientos sociales en la defensa de los derechos colectivos.',
        explora=[texto('¿Qué organizaciones hay en tu comunidad: juntas, asociaciones de campesinos, sindicatos, grupos de jóvenes?')],
        aprende=[texto('Los movimientos <b>campesinos</b>, <b>obreros</b> y <b>estudiantiles</b> del siglo XX lucharon por la tierra, la jornada de 8 horas, la seguridad social y la educación.'),
                 tabla([['Organización', 'Defiende'], ['Sindicato', 'derechos de los trabajadores'], ['Gremio', 'intereses de un sector (cafeteros, comerciantes)'],
                        ['Asociación campesina', 'tierra y producción'], ['Movimiento estudiantil', 'educación pública y de calidad']]),
                 texto('Herramientas pacíficas: <b>diálogo</b>, <b>conciliación</b>, <b>mediación</b>, <b>arbitraje</b> y la protesta pacífica (derecho constitucional, art. 37).')],
        recuerda=['La organización social defiende derechos colectivos.', 'La protesta pacífica es un derecho.'],
        practica=[unica('Un sindicato defiende…', 'los derechos de los trabajadores', ['a los empresarios únicamente']), unica('La Federación Nacional de Cafeteros es un…', 'gremio', ['sindicato'])],
        taller=[unica('¿Qué artículo de la Constitución protege la reunión y manifestación pacífica?', 'El 37', ['El 1', 'El 44']),
                abierta('Investiga una organización social de tu municipio: qué defiende y cómo lo hace.', 6)])
    return U
