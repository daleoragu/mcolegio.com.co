"""Ciencias Sociales 11.º: una guía y un taller por cada uno de los 5 DBA: ambiente y calentamiento global, solución negociada
de los conflictos, conflictos geopolíticos contemporáneos, Guerra Fría y globalización. Borradores para que el docente revise."""
from .base import abierta, imagen, recuadro, tabla, texto, unica, unidad, vf


def unidades():
    U = {}

    U[1] = unidad(
        tema='El ambiente: responsabilidad de todos los actores',
        objetivo='Analizar cómo el bienestar de la humanidad depende de la protección del ambiente y evaluar las acciones de los Estados, la ONU y las organizaciones.',
        explora=[texto('Si el calentamiento global afecta a todos, ¿por qué es tan difícil que los países se pongan de acuerdo para frenarlo?')],
        aprende=[texto('Los países que más gases de efecto invernadero emiten hoy son China, Estados Unidos e India; históricamente, los países industrializados han emitido la mayor parte. '
                       'Reducir emisiones cuesta: cambiar la energía, la industria y el transporte afecta empleos e intereses económicos y políticos.'),
                 tabla([['Acuerdo o cumbre', 'Año', 'Qué buscó'], ['Protocolo de Montreal', '1987', 'proteger la capa de ozono'], ['Cumbre de la Tierra (Río)', '1992', 'desarrollo sostenible, convención sobre cambio climático'],
                        ['Protocolo de Kioto', '1997', 'metas de reducción para países industrializados'], ['Acuerdo de París', '2015', 'mantener el calentamiento muy por debajo de 2 °C y procurar 1,5 °C']]),
                 texto('En Colombia, la Ley 1931 de 2018 establece directrices para la gestión del cambio climático; el IDEAM, el Ministerio de Ambiente y las corporaciones autónomas '
                       'regionales proponen acciones como frenar la deforestación, la transición energética y la adaptación de las ciudades.'),
                 recuadro('Para pensar', 'Colombia emite menos del 1 % de los gases del mundo, pero es muy vulnerable al cambio climático. ¿Qué es más urgente para nosotros: reducir o adaptarnos?',
                          estilo='reto')],
        recuerda=['París 2015: meta de 1,5 °C.', 'El ambiente es un asunto político y económico.'],
        practica=[unica('El acuerdo de 2015 sobre el clima es el de…', 'París', ['Kioto', 'Montreal']), unica('El Protocolo de Montreal protege…', 'la capa de ozono', ['los océanos'])],
        taller=[unica('Uno de los mayores emisores actuales de gases de invernadero es…', 'China', ['Uruguay', 'Islandia']),
                vf('Reducir emisiones no tiene costos económicos.', False),
                unica('¿Qué ley colombiana orienta la gestión del cambio climático?', 'Ley 1931 de 2018', ['Ley 100 de 1993', 'Ley 115 de 1994']),
                abierta('Propón tres acciones concretas para disminuir las emisiones en tu colegio y en tu municipio. Explica quién debe ejecutarlas.', 8)])

    U[2] = unidad(
        tema='La solución negociada de los conflictos y la paz',
        objetivo='Evaluar la importancia de la solución negociada de los conflictos armados, la memoria histórica y los derechos de las víctimas en la búsqueda de la paz.',
        explora=[texto('La Constitución dice: «La paz es un derecho y un deber de obligatorio cumplimiento» (artículo 22). ¿Qué significa que la paz sea también un deber?')],
        aprende=[tabla([['Proceso', 'Año', 'Resultado'], ['Desmovilización del M-19', '1990', 'participó en la Asamblea Constituyente'], ['Constitución Política', '1991', 'nuevo pacto social'],
                        ['Ley de Víctimas (Ley 1448)', '2011', 'reparación y restitución de tierras'], ['Acuerdo de Paz con las FARC-EP', '2016', 'dejación de armas y reincorporación']]),
                 texto('En 2016 el plebiscito sobre el acuerdo ganó el «No» por un margen estrecho; el acuerdo se renegoció y se firmó en noviembre de ese año. Creó la Jurisdicción Especial '
                       'para la Paz (JEP), la Comisión de la Verdad (su informe final se entregó en 2022) y la Unidad de Búsqueda de Personas dadas por Desaparecidas.'),
                 texto('La <b>justicia transicional</b> se apoya en cuatro pilares: <b>verdad, justicia, reparación y garantías de no repetición</b>. La memoria histórica reconoce a las víctimas '
                       'y ayuda a que la violencia no se repita.'),
                 texto('Negociar no es renunciar a la justicia: es buscar el fin de la guerra respetando las diferencias políticas, étnicas, religiosas y de género.')],
        recuerda=['Verdad, justicia, reparación y no repetición.', 'Artículo 22: la paz es derecho y deber.'],
        practica=[unica('El acuerdo de paz con las FARC-EP se firmó en…', '2016', ['1991', '2002']), unica('La JEP es…', 'un tribunal de justicia transicional', ['un partido político'])],
        taller=[unica('Los cuatro pilares de la justicia transicional son…', 'verdad, justicia, reparación y no repetición', ['castigo, olvido, perdón y cárcel']),
                vf('El M-19 participó en la Asamblea Nacional Constituyente tras desmovilizarse.', True),
                unica('La ley que reconoce los derechos de las víctimas del conflicto es la…', 'Ley 1448 de 2011', ['Ley 1931 de 2018']),
                abierta('Escribe un ensayo corto: ¿por qué la paz es un deber ético, moral y constitucional de todos los ciudadanos? Usa al menos dos argumentos.', 12)])

    U[3] = unidad(
        tema='Conflictos geopolíticos contemporáneos',
        objetivo='Analizar las consecuencias políticas, económicas y sociales de conflictos geopolíticos desde finales del siglo XX y sus efectos en las poblaciones.',
        explora=[texto('¿Por qué hay guerras por el petróleo, el agua o un pedazo de territorio? ¿Quién paga las consecuencias?')],
        aprende=[tabla([['Conflicto', 'Inicio', 'Causas principales'], ['Guerra del Golfo', '1990–1991', 'invasión iraquí a Kuwait, petróleo'],
                        ['Guerras de la antigua Yugoslavia', '1991', 'nacionalismos y diferencias étnicas y religiosas'], ['Genocidio de Ruanda', '1994', 'odio étnico entre hutus y tutsis'],
                        ['Guerra en Siria', '2011', 'protestas reprimidas, intervención de potencias'], ['Invasión rusa de Ucrania', '2022', 'territorio, seguridad y zonas de influencia']]),
                 texto('Las grandes potencias defienden intereses <b>políticos</b> (zonas de influencia), <b>económicos</b> (recursos, rutas de comercio) e <b>ideológicos</b>.'),
                 texto('Consecuencias sociales: <b>desplazamiento forzado</b>, millones de <b>refugiados</b>, y en los peores casos <b>genocidio</b> (en Ruanda murieron cientos de miles de personas en unos cien días).'),
                 texto('Las fronteras sienten estas dinámicas: la crisis de Venezuela llevó a Colombia cerca de tres millones de migrantes, con retos para la salud, la educación y el empleo.')],
        recuerda=['Recursos + intereses + ideologías → conflictos.', 'Los civiles pagan las consecuencias.'],
        practica=[unica('La Guerra del Golfo comenzó por la invasión de Irak a…', 'Kuwait', ['Irán', 'Siria']),
                  unica('Una persona que huye de su país por la guerra es…', 'refugiada', ['turista'])],
        taller=[unica('El genocidio de Ruanda (1994) enfrentó a…', 'hutus y tutsis', ['serbios y croatas']), vf('Las guerras afectan sobre todo a la población civil.', True),
                unica('La migración venezolana a Colombia es un ejemplo de dinámica…', 'fronteriza', ['exclusivamente cultural']),
                abierta('Elige un conflicto actual. Explica sus causas, los intereses de las potencias y sus consecuencias para la población, citando dos fuentes confiables.', 10)])

    U[4] = unidad(
        tema='La Guerra Fría y América Latina',
        objetivo='Comprender las implicaciones de la Guerra Fría en el mundo y relacionarlas con lo vivido en América Latina.',
        explora=[texto('¿Cómo puede haber una «guerra» de más de 40 años en la que las dos potencias principales nunca se enfrentaron directamente?')],
        aprende=[imagen('d-tiempo-1949.Nace la|OTAN-1959.Revolución|cubana-1961.Muro de|Berlín-1962.Crisis de|los misiles-1989.Cae el|Muro-1991.Fin de|la URSS', 95),
                 tabla([['', 'Bloque capitalista', 'Bloque comunista'], ['Líder', 'Estados Unidos', 'Unión Soviética (URSS)'], ['Economía', 'mercado y propiedad privada', 'planificación estatal'],
                        ['Política', 'democracia liberal', 'partido único'], ['Alianza militar', 'OTAN (1949)', 'Pacto de Varsovia (1955)']]),
                 texto('Fue una competencia ideológica, militar (carrera nuclear), espacial y económica. La amenaza de las armas de destrucción masiva marcó la vida cotidiana, y en 1962 la crisis de '
                       'los misiles en Cuba puso al mundo al borde de una guerra nuclear.'),
                 texto('En América Latina: la <b>Revolución cubana</b> (1959), la Alianza para el Progreso de Estados Unidos (1961), guerrillas inspiradas en ella, y <b>dictaduras militares</b> '
                       '(Chile 1973, Argentina 1976) apoyadas en la lucha anticomunista. Colombia fue el único país latinoamericano que envió tropas a la Guerra de Corea (Batallón Colombia).')],
        recuerda=['1947–1991: dos bloques.', 'América Latina: revolución, dictaduras e intervencionismo.'],
        practica=[unica('El Muro de Berlín cayó en…', '1989', ['1961', '1945']), unica('La alianza militar del bloque capitalista era…', 'la OTAN', ['el Pacto de Varsovia'])],
        taller=[unica('La crisis de los misiles (1962) ocurrió en…', 'Cuba', ['Corea', 'Vietnam']), unica('La URSS se disolvió en…', '1991', ['1989', '1959']),
                vf('Colombia envió tropas a la Guerra de Corea.', True),
                abierta('Compara cómo vivía una familia en Berlín Occidental y en Berlín Oriental. Luego explica una consecuencia de la Guerra Fría en Colombia.', 8)])

    U[5] = unidad(
        tema='La globalización y los bloques económicos',
        objetivo='Analizar la globalización como proceso que redefine el territorio, los mercados, las gobernanzas y las identidades, y situar los bloques de integración.',
        explora=[texto('Tu celular fue diseñado en un país, armado en otro, con minerales de un tercero, y lo usas para ver series de todo el mundo. ¿Qué ganamos y qué perdemos con eso?')],
        aprende=[texto('La <b>globalización</b> intensifica los intercambios de mercancías, capitales, información y personas. Cambia el sentido del territorio (empresas sin fronteras), '
                       'reduce el margen de decisión de los gobiernos nacionales y mezcla identidades locales con culturas globales.'),
                 tabla([['Bloque o tratado', 'Año', 'Miembros (algunos)'], ['Comunidad Andina', '1969', 'Colombia, Ecuador, Perú, Bolivia'], ['Mercosur', '1991', 'Brasil, Argentina, Uruguay, Paraguay'],
                        ['ALBA', '2004', 'Venezuela, Cuba, Bolivia, Nicaragua'], ['Unasur', '2008', 'países de Suramérica'], ['Alianza del Pacífico', '2011', 'Chile, Colombia, México, Perú']]),
                 texto('Colombia tiene tratados de libre comercio, como el que tiene con Estados Unidos (vigente desde 2012). Sus efectos se discuten: más exportaciones e inversión, pero '
                       'dificultades para algunos productores agrícolas e industriales.'),
                 tabla([['Ventajas', 'Desventajas'], ['acceso a tecnología e información', 'desigualdad entre países y regiones'], ['más comercio e inversión', 'pérdida de empleos en sectores poco competitivos'],
                        ['intercambio cultural', 'homogeneización cultural y riesgo para lenguas y tradiciones']])],
        recuerda=['Globalización: económica, política y cultural.', 'Alianza del Pacífico: Chile, Colombia, México y Perú.'],
        practica=[unica('¿Cuál bloque integran Chile, Colombia, México y Perú?', 'la Alianza del Pacífico', ['el Mercosur', 'el ALBA']),
                  unica('El TLC de Colombia con Estados Unidos está vigente desde…', '2012', ['1991', '2020'])],
        taller=[unica('La Comunidad Andina nació en…', '1969', ['2011', '1991']), unica('Una desventaja de la globalización es…', 'la homogeneización cultural', ['el acceso a información']),
                vf('La globalización reduce el margen de decisión de los gobiernos nacionales.', True),
                abierta('Revisa las etiquetas de 10 productos de tu casa: ¿de dónde vienen? Haz un mapa y escribe una reflexión sobre la globalización en tu vida cotidiana.', 8)])
    return U
