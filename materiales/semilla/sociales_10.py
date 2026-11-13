"""Ciencias Sociales 10.º: una guía y un taller por cada uno de los 5 DBA: conflictos ambientales en Colombia, violencia en la
segunda mitad del siglo XX, diversidad cultural y discriminación, organismos internacionales y guerras mundiales.
Borradores para que el docente revise."""
from .base import abierta, imagen, recuadro, tabla, texto, unica, unidad, vf


def unidades():
    U = {}

    U[1] = unidad(
        tema='Agua, contaminación y conflictos ambientales en Colombia',
        objetivo='Analizar conflictos del territorio colombiano originados por la degradación ambiental, el escaso desarrollo económico y la inestabilidad política.',
        explora=[texto('El Chocó está entre las regiones más lluviosas del planeta y La Guajira sufre sequías. ¿Cómo puede un mismo país tener tanta agua y tanta escasez?')],
        aprende=[texto('Colombia tiene una gran riqueza hídrica, pero repartida de forma desigual: la mayoría de la población vive en la región Andina y el Caribe, donde hay menos agua '
                       'disponible por persona que en la Amazonía o el Pacífico.'),
                 tabla([['Tipo de contaminación', 'Causa', 'Ejemplo en Colombia'], ['Hídrica', 'aguas residuales, mercurio, agroquímicos', 'río Bogotá, ríos con minería ilegal'],
                        ['Atmosférica', 'vehículos, industria, quemas', 'alertas por calidad del aire en ciudades'], ['Del suelo', 'basureros a cielo abierto, derrames', 'derrames de petróleo por atentados'],
                        ['Sonora', 'tráfico, ruido industrial', 'centros de las ciudades']]),
                 texto('Los conflictos ambientales casi nunca son solo ambientales: la pobreza empuja a actividades extractivas; la débil presencia del Estado permite la minería ilegal y la '
                       'deforestación; y los grupos armados controlan recursos.'),
                 texto('Fuentes para estudiar la pérdida de biodiversidad: informes del Ministerio de Ambiente, del IDEAM, del Instituto Humboldt y de las corporaciones autónomas regionales.')],
        recuerda=['Agua abundante pero mal distribuida.', 'Ambiente, economía y política se entrelazan.'],
        practica=[unica('Una región colombiana con escasez de agua es…', 'La Guajira', ['el Chocó', 'la Amazonía']),
                  unica('El mercurio en los ríos proviene principalmente de…', 'la minería de oro', ['la pesca'])],
        taller=[unica('El ruido excesivo del tráfico es contaminación…', 'sonora', ['hídrica']),
                vf('La deforestación se relaciona con problemas económicos y con la presencia de grupos armados.', True),
                unica('¿Qué entidad estudia el clima y los recursos hídricos en Colombia?', 'el IDEAM', ['la Registraduría']),
                abierta('Identifica un conflicto ambiental de tu municipio. Explica sus causas ambientales, económicas y políticas, quiénes están involucrados y propón una acción.', 10)])

    U[2] = unidad(
        tema='La violencia en Colombia en la segunda mitad del siglo XX',
        objetivo='Evaluar las causas y consecuencias de la violencia en Colombia desde 1948 y su incidencia en lo social, político, económico y cultural.',
        explora=[texto('¿Qué conflictos han marcado la historia de tu familia o de tu municipio? ¿Qué te han contado tus abuelos?')],
        aprende=[imagen('d-tiempo-1948.El Bogotazo-1958.Frente|Nacional-1964.Nacen FARC|y ELN-1985.Toma del Palacio|de Justicia-1991.Nueva|Constitución', 95),
                 texto('El 9 de abril de 1948 asesinaron a Jorge Eliécer Gaitán y estalló el <b>Bogotazo</b>. Se agudizó <b>La Violencia</b> entre liberales y conservadores, con cientos '
                       'de miles de muertos y desplazados en el campo.'),
                 texto('El <b>Frente Nacional</b> (1958–1974) alternó el poder entre los dos partidos y redujo esa violencia, pero excluyó a otras fuerzas políticas. En los años 60 '
                       'surgieron guerrillas (FARC, ELN, EPL y luego el M-19); después, grupos paramilitares; y en los 80 el <b>narcotráfico</b> financió y agravó el conflicto.'),
                 tabla([['Tipo de violencia (Johan Galtung)', 'Qué es', 'Ejemplo'], ['Directa', 'agresión física visible', 'masacres, secuestros'],
                        ['Estructural', 'injusticia en la organización de la sociedad', 'falta de tierra, salud y educación para los campesinos'],
                        ['Cultural', 'ideas que justifican la violencia', 'estigmatizar a quien piensa distinto']])],
        recuerda=['1948: Bogotazo.', 'Frente Nacional: paz entre partidos, exclusión de otros.', 'Violencia directa, estructural y cultural.'],
        practica=[unica('El Bogotazo ocurrió tras el asesinato de…', 'Jorge Eliécer Gaitán', ['Simón Bolívar', 'Francisco de Paula Santander']),
                  unica('El Frente Nacional alternó el poder entre…', 'liberales y conservadores', ['guerrillas y paramilitares'])],
        taller=[unica('La falta de acceso a la tierra para los campesinos es un ejemplo de violencia…', 'estructural', ['directa', 'cultural']),
                unica('¿En qué década el narcotráfico se volvió un actor central del conflicto?', 'los años 80', ['los años 20', 'los años 40']),
                vf('El Frente Nacional incluyó a todos los partidos políticos.', False),
                abierta('Entrevista a un adulto mayor sobre cómo vivió la violencia en su región. Relaciona su relato con lo estudiado (con respeto y con su permiso).', 10)])

    U[3] = unidad(
        tema='Muchas culturas, una sola humanidad',
        objetivo='Comprender la diversidad cultural y étnica, identificar formas de discriminación y sus consecuencias, y valorar las acciones para superarlas.',
        explora=[texto('¿Alguna vez has visto que se burlen de alguien por su acento, su color de piel o su forma de vestir? ¿Cómo crees que se sintió?')],
        aprende=[texto('Colombia es un país <b>pluriétnico y multicultural</b>: la Constitución de 1991 (artículo 7) reconoce y protege la diversidad étnica y cultural. Conviven pueblos '
                       'indígenas, comunidades negras, afrocolombianas, raizales y palenqueras, el pueblo Rrom (gitano) y la población mestiza.'),
                 texto('En el país se hablan cerca de 68 lenguas nativas además del castellano, entre ellas el palenquero y el creole de San Andrés.'),
                 tabla([['Forma de discriminación', 'Ejemplo', 'Consecuencia'], ['Racismo', 'negar un empleo por el color de piel', 'pobreza y exclusión'],
                        ['Xenofobia', 'rechazo a migrantes', 'violencia y aislamiento'], ['Sexismo', 'pagar menos a una mujer por el mismo trabajo', 'desigualdad'],
                        ['Discriminación por discapacidad', 'no adaptar los espacios', 'pérdida de oportunidades']]),
                 texto('En el mundo, el <b>apartheid</b> en Sudáfrica (1948–1994) separó por ley a la población según su color de piel. Nelson Mandela, preso durante 27 años, fue '
                       'elegido presidente en 1994. En Colombia, la Ley 1482 de 2011 sanciona los actos de discriminación.')],
        recuerda=['Diversidad: riqueza, no amenaza.', 'La discriminación tiene consecuencias sociales y es sancionada por la ley.'],
        practica=[unica('El rechazo a los migrantes se llama…', 'xenofobia', ['sexismo', 'racismo']), unica('La Constitución de 1991 define a Colombia como…', 'pluriétnica y multicultural', ['de una sola cultura'])],
        taller=[unica('El apartheid fue un sistema de segregación en…', 'Sudáfrica', ['Brasil', 'Canadá']), vf('En Colombia solo se habla castellano.', False),
                unica('El palenquero es una lengua de…', 'San Basilio de Palenque', ['la Amazonía', 'Nariño']),
                abierta('Diseña una campaña contra una forma de discriminación que veas en tu colegio: mensaje, público y acciones.', 8)])

    U[4] = unidad(
        tema='Los organismos internacionales',
        objetivo='Interpretar el papel de los organismos internacionales como alianzas entre Estados y su influencia en las políticas económicas, jurídicas y ambientales.',
        explora=[texto('¿Por qué los países, que son soberanos, aceptan reglas comunes? ¿Qué ganan y qué ceden?')],
        aprende=[tabla([['Organismo', 'Año', 'Función'], ['ONU', '1945', 'paz y seguridad, derechos humanos, desarrollo'], ['OEA', '1948 (fundada en Bogotá)', 'cooperación entre los países de América'],
                        ['FMI', '1944', 'estabilidad financiera, préstamos'], ['Banco Mundial', '1944', 'préstamos para el desarrollo'], ['OMC', '1995', 'reglas del comercio internacional'],
                        ['OMS', '1948', 'salud mundial']]),
                 texto('Colombia es miembro fundador de la ONU y de la OEA, y desde 2020 hace parte de la OCDE.'),
                 texto('En el <b>Consejo de Seguridad</b> de la ONU, cinco miembros permanentes (Estados Unidos, Rusia, China, Francia y Reino Unido) tienen derecho a <b>veto</b>, lo que '
                       'muestra que estos organismos también reflejan las relaciones de poder entre los países.'),
                 recuadro('Para pensar', 'Los préstamos del FMI suelen venir con condiciones (recortes de gasto, reformas). ¿Quién decide la política económica de un país?', estilo='reto')],
        recuerda=['ONU (1945), OEA (1948), OMC (1995).', 'Cooperación + intereses de los países.'],
        practica=[unica('La OEA se fundó en…', 'Bogotá', ['Nueva York', 'Ginebra']), unica('¿Qué organismo regula el comercio internacional?', 'la OMC', ['la OMS', 'la OEA'])],
        taller=[unica('¿Cuántos miembros permanentes tiene el Consejo de Seguridad?', '5', ['3', '15']), vf('Colombia es miembro fundador de la ONU.', True),
                unica('El derecho a veto permite a un miembro permanente…', 'bloquear una decisión', ['expulsar a un país']),
                abierta('Investiga una acción de un organismo internacional en Colombia (ACNUR, UNICEF, OMS…). Explica qué hizo y evalúa su impacto.', 8)])

    U[5] = unidad(
        tema='Las guerras mundiales',
        objetivo='Analizar las causas, el desarrollo y las consecuencias de las guerras mundiales y su incidencia en la vida de los pueblos.',
        explora=[texto('¿Cómo pudo el asesinato de una persona en Sarajevo desatar una guerra entre decenas de países?')],
        aprende=[tabla([['', 'Primera Guerra Mundial', 'Segunda Guerra Mundial'], ['Años', '1914–1918', '1939–1945'],
                        ['Detonante', 'asesinato del archiduque Francisco Fernando en Sarajevo', 'invasión alemana a Polonia'],
                        ['Bandos', 'Triple Entente vs. Potencias Centrales', 'Aliados vs. Eje (Alemania, Italia, Japón)'],
                        ['Tecnología', 'trincheras, gas tóxico, tanques, aviones', 'radar, bombardeos masivos, bomba atómica']]),
                 texto('Causas de fondo de la Primera: nacionalismos, carrera armamentista, alianzas y competencia por las colonias. El Tratado de Versalles (1919) impuso duras condiciones a '
                       'Alemania; la crisis económica de 1929 y el ascenso del nazismo prepararon la Segunda.'),
                 texto('La Segunda Guerra dejó decenas de millones de muertos y el <b>Holocausto</b>: el asesinato sistemático de unos seis millones de judíos y de otros grupos. Terminó tras '
                       'las bombas atómicas sobre Hiroshima y Nagasaki (agosto de 1945).'),
                 texto('Colombia rompió relaciones con el Eje y en 1943 declaró el estado de beligerancia con Alemania tras el hundimiento de barcos colombianos en el Caribe.'),
                 texto('Consecuencias: creación de la ONU, la Declaración Universal de los Derechos Humanos (1948), la división del mundo en dos bloques y la descolonización.')],
        recuerda=['1914–1918 y 1939–1945.', 'Holocausto: nunca más.'],
        practica=[unica('La Segunda Guerra Mundial comenzó con la invasión a…', 'Polonia', ['Francia', 'Rusia']),
                  unica('El tratado que terminó la Primera Guerra fue el de…', 'Versalles', ['Tordesillas', 'Utrecht'])],
        taller=[unica('Las bombas atómicas cayeron sobre…', 'Hiroshima y Nagasaki', ['Tokio y Osaka', 'Berlín y Múnich']),
                unica('La guerra de trincheras caracterizó a…', 'la Primera Guerra Mundial', ['la Segunda Guerra Mundial']),
                vf('La Declaración Universal de los Derechos Humanos fue una respuesta a los horrores de la guerra.', True),
                abierta('Lee un fragmento del «Diario de Ana Frank» y escribe cómo la guerra cambió la vida cotidiana de una adolescente.', 8)])
    return U
