"""Ciencias Sociales 9.º: una guía y un taller por cada uno de los 8 DBA: geosistemas, migraciones, crisis económicas,
siglo XX, Estado social de derecho, mujeres, conflicto y acuerdos, y desigualdad regional. Borradores para revisar."""
from .base import abierta, imagen, recuadro, tabla, texto, unica, unidad, vf


def unidades():
    U = {}

    U[1] = unidad(
        tema='Geosistemas biodiversos de Colombia en riesgo',
        objetivo='Analizar la importancia de selvas, páramos y arrecifes coralinos y los problemas que enfrentan por su explotación.',
        explora=[imagen('n4-paramo', 30, 'Páramo'), imagen('s9-arrecife', 30, 'Arrecife coralino'), texto('¿Qué beneficios recibimos de estos ecosistemas aunque vivamos lejos de ellos?')],
        aprende=[tabla([['Geosistema', 'Importancia', 'Amenazas'], ['Selvas (Amazonía, Chocó)', 'biodiversidad, regulación del clima, captura de carbono', 'deforestación, minería ilegal, ganadería extensiva'],
                        ['Páramos', 'nacen la mayoría de los ríos que abastecen las ciudades', 'agricultura y ganadería en zonas altas, minería'],
                        ['Arrecifes (San Andrés, Rosario)', 'refugio de peces, protección de costas', 'calentamiento del mar, contaminación, turismo masivo']]),
                 texto('La <b>ampliación de la frontera agrícola</b>, la <b>minería</b> y los <b>cultivos ilícitos</b> destruyen estos ecosistemas y la biodiversidad del país.')],
        recuerda=['Colombia tiene cerca de la mitad de los páramos del mundo.', 'Cuidar los páramos es cuidar el agua.'],
        practica=[unica('¿De dónde nace gran parte del agua de las ciudades andinas?', 'De los páramos', ['Del mar']), unica('Una amenaza para los arrecifes es…', 'el calentamiento del mar', ['la lluvia'])],
        taller=[unica('La deforestación de la Amazonía se relaciona con…', 'la ganadería extensiva y la minería ilegal', ['la pesca artesanal']),
                abierta('Propón un proyecto escolar para proteger un ecosistema de tu región.', 8)])

    U[2] = unidad(
        tema='Migraciones en la historia de Colombia',
        objetivo='Comprender las causas y consecuencias de las migraciones internas y externas en la Colombia del siglo XX y la actual.',
        explora=[texto('¿De dónde vinieron tus abuelos? ¿Por qué se movieron?')],
        aprende=[texto('En el siglo XX, la <b>colonización antioqueña</b>, la violencia de mediados de siglo y la industrialización movieron a millones del campo a la ciudad. El <b>conflicto armado</b> '
                       'causó millones de víctimas de <b>desplazamiento forzado</b>.'),
                 tabla([['Proceso', 'Significado', 'Ejemplo actual'], ['Emigración', 'salir del país', 'colombianos que se van a España o Estados Unidos'],
                        ['Inmigración', 'llegar al país', 'migrantes venezolanos en Colombia'], ['Migración interna', 'moverse dentro del país', 'del campo a las ciudades']])],
        recuerda=['Colombia ha vivido migraciones internas y externas.', 'El desplazamiento forzado es una violación de derechos.'],
        practica=[unica('Llegar a vivir a Colombia desde otro país es…', 'inmigración', ['emigración']), unica('El desplazamiento forzado lo causó principalmente…', 'el conflicto armado', ['el turismo'])],
        taller=[abierta('Haz un mapa de la migración de tu familia en las últimas tres generaciones y explica las causas.', 8)])

    U[3] = unidad(
        tema='Las crisis económicas',
        objetivo='Analizar crisis económicas de la Colombia contemporánea y sus repercusiones en la vida cotidiana.',
        explora=[texto('Cuando sube el precio de los alimentos o del dólar, ¿cómo afecta a tu familia?')],
        aprende=[tabla([['Momento', 'Qué pasó', 'Efectos'], ['Sustitución de importaciones (1950-1970)', 'se protegió la industria nacional', 'creció la industria, pero con poca competencia'],
                        ['Apertura económica (1990)', 'se bajaron aranceles y se abrió el mercado', 'productos más baratos; quiebra de algunos sectores agrícolas e industriales'],
                        ['Crisis de finales de los noventa (1998-1999)', 'crisis del sistema financiero y de vivienda (UPAC)', 'desempleo alto, pérdida de viviendas']]),
                 texto('Las crisis se relacionan con causas internas (deuda, gasto) y externas (precios del petróleo y del café, crisis mundiales como la de 2008). Afectan el empleo, los precios y la pobreza.')],
        recuerda=['Las crisis afectan el empleo y los precios.', 'La economía colombiana depende en parte de exportaciones como el petróleo y el café.'],
        practica=[unica('La apertura económica en Colombia fue en los años…', 'noventa', ['cincuenta', 'veinte']), unica('La crisis del UPAC afectó sobre todo…', 'la vivienda', ['la pesca'])],
        taller=[unica('Si cae el precio internacional del petróleo, Colombia…', 'recibe menos ingresos', ['recibe más ingresos']),
                abierta('Pregunta a tus padres o abuelos cómo vivieron una crisis económica y cómo la enfrentaron.', 8)])

    U[4] = unidad(
        tema='Colombia en el siglo XX',
        objetivo='Analizar los cambios sociales, políticos, económicos y culturales del siglo XX y su impacto en la vida de la población.',
        explora=[texto('Haz una lista de lo que había en Colombia en 1900 y en 2000. ¿Qué cambió más?')],
        aprende=[texto('Primera mitad: <b>modernización</b> (carreteras, ferrocarriles, bancos), crecimiento de la industria y aparición de los <b>sindicatos</b> (masacre de las bananeras, 1928).'),
                 texto('Mediados de siglo: <b>La Violencia</b> (desde 1948, tras el asesinato de Jorge Eliécer Gaitán) y el <b>Frente Nacional</b> (1958-1974), en el que liberales y conservadores se alternaron el poder.'),
                 texto('Segunda mitad: urbanización acelerada, surgimiento de guerrillas y narcotráfico, y la <b>Constitución de 1991</b>, que reconoció la diversidad y amplió los derechos.')],
        recuerda=['1948: el Bogotazo. 1958-1974: Frente Nacional. 1991: nueva Constitución.'],
        practica=[unica('El asesinato de Gaitán fue en…', '1948', ['1928', '1991']), unica('El Frente Nacional alternó el poder entre…', 'liberales y conservadores', ['militares y civiles'])],
        taller=[unica('La masacre de las bananeras fue en…', '1928', ['1948', '1958']), abierta('Haz una línea de tiempo de 5 hechos del siglo XX colombiano y explica uno.', 8)])

    U[5] = unidad(
        tema='El Estado social de derecho',
        objetivo='Evaluar el deber del Estado social de derecho de proteger y promover los derechos fundamentales, sociales y colectivos.',
        explora=[texto('La Constitución dice que Colombia es un «Estado social de derecho». ¿Qué crees que significa «social»?')],
        aprende=[tabla([['Generación de derechos', 'Ejemplos'], ['Fundamentales', 'vida, igualdad, libertad de expresión, debido proceso'], ['Sociales, económicos y culturales', 'salud, educación, vivienda, trabajo'],
                        ['Colectivos y del ambiente', 'ambiente sano, espacio público, patrimonio cultural']]),
                 texto('<b>Estado social de derecho</b>: además de respetar la ley, el Estado debe garantizar condiciones dignas de vida. Mecanismos de protección: <b>tutela</b> (fundamentales), '
                       '<b>acción popular</b> (colectivos), <b>acción de cumplimiento</b>.'),
                 texto('La vulneración de los Derechos Humanos debilita la democracia y la confianza en las instituciones.')],
        recuerda=['Tutela: derechos fundamentales. Acción popular: derechos colectivos.'],
        practica=[unica('Para proteger el derecho a un ambiente sano se usa la…', 'acción popular', ['tutela']), unica('La educación es un derecho…', 'social', ['solo colectivo'])],
        taller=[unica('Colombia es un Estado social de derecho desde la Constitución de…', '1991', ['1886']),
                abierta('Redacta un borrador de acción de tutela para un caso hipotético de vulneración del derecho a la salud.', 10)])

    U[6] = unidad(
        tema='Las mujeres en la historia y la igualdad de derechos',
        objetivo='Reconocer el papel de las mujeres en los cambios sociales, políticos y culturales y los avances en igualdad.',
        explora=[texto('Nombra tres mujeres importantes de la historia de Colombia. ¿Fue fácil o difícil?')],
        aprende=[tabla([['Mujer', 'Aporte'], ['Policarpa Salavarrieta', 'heroína de la Independencia'], ['Esmeralda Arboleda', 'primera senadora (1958) y líder del voto femenino'],
                        ['Débora Arango', 'pintora que retrató la realidad social'], ['Nubia Muñoz', 'epidemióloga; sus investigaciones sobre el virus del papiloma humano ayudaron a crear la vacuna'],
                        ['Francia Márquez', 'lideresa ambiental, primera vicepresidenta afrocolombiana (2022)']]),
                 texto('Formas de <b>violencia contra las mujeres</b>: psicológica, sexual, económica, doméstica, laboral, mediática y física. La Ley 1257 de 2008 las previene y sanciona.'),
                 recuadro('Línea 155', '<p>Orientación a mujeres víctimas de violencia, gratuita y nacional.</p>', estilo='recuerda')],
        recuerda=['La igualdad de derechos es un logro reciente que hay que defender.'],
        practica=[unica('¿Quién fue la primera senadora de Colombia?', 'Esmeralda Arboleda', ['Policarpa Salavarrieta']), unica('La Ley 1257 de 2008 trata sobre…', 'la violencia contra las mujeres', ['el tránsito'])],
        taller=[vf('La violencia económica contra las mujeres es una forma de violencia.', True), abierta('Investiga a una mujer de tu región que haya aportado a su comunidad y escribe su biografía breve.', 8)])

    U[7] = unidad(
        tema='Los conflictos se resuelven con acuerdos',
        objetivo='Evaluar cómo los conflictos pueden solucionarse mediante acuerdos y proponer alternativas a conflictos entre grupos.',
        explora=[texto('Dos veredas discuten por el agua de una quebrada. ¿Cómo podrían llegar a un acuerdo?')],
        aprende=[texto('Toda acción que causa sufrimiento tiene consecuencias. Resolver conflictos exige reconocer al otro, entender sus intereses y ceder.'),
                 tabla([['Mecanismo', 'Cómo funciona'], ['Negociación', 'las partes dialogan directamente'], ['Mediación', 'un tercero facilita el diálogo'], ['Conciliación', 'un conciliador propone fórmulas de arreglo'],
                        ['Arbitraje', 'un árbitro decide y las partes aceptan']]),
                 texto('El <b>Acuerdo de Paz de 2016</b> entre el Estado y las FARC-EP es un ejemplo de solución negociada a un conflicto armado; su implementación sigue siendo un reto.')],
        recuerda=['Los acuerdos requieren reconocer los intereses del otro.'],
        practica=[unica('Si un tercero decide y las partes aceptan, es…', 'arbitraje', ['negociación']), unica('El Acuerdo de Paz con las FARC-EP se firmó en…', '2016', ['1991', '2002'])],
        taller=[abierta('Propón una solución al conflicto del agua entre las dos veredas usando la mediación.', 8)])

    U[8] = unidad(
        tema='Crecimiento económico desigual entre regiones',
        objetivo='Comprender el impacto social del crecimiento económico desigual entre las regiones del país.',
        explora=[texto('¿Por qué Bogotá o Medellín tienen más hospitales y universidades que muchos municipios del Chocó o La Guajira?')],
        aprende=[texto('Las condiciones <b>geográficas</b> (selvas, montañas, lejanía), la <b>historia</b> (centralismo, conflicto) y las <b>decisiones políticas</b> influyen en la infraestructura y la inversión.'),
                 tabla([['Indicador', 'Regiones con más crecimiento', 'Regiones con menos'], ['Vías y servicios', 'más cobertura', 'menos cobertura'], ['Pobreza', 'menor', 'mayor'],
                        ['Acceso a educación superior', 'mayor', 'menor']]),
                 texto('Herramientas para reducir la brecha: el <b>Sistema General de Participaciones</b> y las <b>regalías</b> que el Estado distribuye a departamentos y municipios.')],
        recuerda=['La desigualdad regional tiene causas geográficas, históricas y políticas.'],
        practica=[unica('Una causa de la desigualdad regional es…', 'la lejanía y la falta de vías', ['el clima frío']), unica('Las regalías provienen de…', 'la explotación de recursos naturales', ['los impuestos de los estudiantes'])],
        taller=[abierta('Compara dos departamentos de Colombia (uno con más y otro con menos desarrollo) con datos del DANE.', 8)])
    return U
