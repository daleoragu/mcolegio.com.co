"""Ciencias Naturales 11.º: una guía y un taller por cada uno de los 5 DBA: ondas (sonido y luz), electricidad y magnetismo,
circuitos, química orgánica y problemas ambientales. Borradores para que el docente revise."""
from fractions import Fraction as F

from .base import abierta, grafica, imagen, numerica, tabla, texto, unica, unidad, vf


def unidades():
    U = {}

    U[1] = unidad(
        tema='Ondas: el sonido y la luz',
        objetivo='Clasificar las ondas de sonido y luz y aplicar las leyes de la reflexión y la refracción para explicar fenómenos cotidianos.',
        explora=[texto('En una tormenta ves el rayo y unos segundos después oyes el trueno. ¿Por qué no llegan al mismo tiempo?')],
        aprende=[tabla([['', 'Sonido', 'Luz'], ['Tipo', 'mecánica (necesita un medio)', 'electromagnética (viaja en el vacío)'],
                        ['Oscilación', 'longitudinal', 'transversal'], ['Rapidez', '≈ 340 m/s en el aire', '≈ 300 000 km/s']]),
                 grafica({'x': [0, 12.6], 'y': [-2.5, 2.5], 'elementos': [
                     {'t': 'funcion', 'expr': '2sen(x)', 'nombre': 'onda'},
                     {'t': 'segmento', 'a': [1.571, 0], 'b': [1.571, 2], 'nombre': 'amplitud'},
                     {'t': 'segmento', 'a': [1.571, 2.2], 'b': [7.854, 2.2], 'nombre': 'longitud de onda λ', 'estilo': 'guiones'}]}, 55, 'Amplitud y longitud de onda'),
                 texto('<b>v = λ·f</b>: rapidez = longitud de onda × frecuencia. Un sonido de 170 Hz en el aire tiene λ = 340 ÷ 170 = <b>2 m</b>.'),
                 texto('Cualidades: el <b>tono</b> depende de la frecuencia (agudo/grave); la <b>intensidad</b>, de la amplitud. En la luz, el <b>color</b> depende de la longitud de onda '
                       '(rojo ≈ 700 nm, violeta ≈ 400 nm).'),
                 texto('<b>Reflexión</b>: el ángulo de incidencia es igual al de reflexión. <b>Refracción</b>: la onda cambia de dirección al cambiar de medio porque cambia su rapidez '
                       '(el lápiz «quebrado» en un vaso de agua). También hay interferencia, difracción y polarización.')],
        recuerda=['v = λ f.', 'Sonido: mecánica y longitudinal. Luz: electromagnética y transversal.'],
        practica=[numerica('Distancia de un rayo si el trueno llega 3 s después (sonido a 340 m/s).', 1020, 'm'),
                  numerica('Longitud de onda de un sonido de 680 Hz (v = 340 m/s).', F(1, 2), 'm')],
        taller=[unica('Un sonido más agudo tiene mayor…', 'frecuencia', ['amplitud', 'longitud de onda']),
                unica('¿Qué onda puede viajar en el espacio vacío?', 'la luz', ['el sonido']),
                numerica('Un rayo de luz llega a un espejo con 35° de incidencia. Ángulo de reflexión.', 35, '°'),
                vf('La refracción ocurre porque la onda cambia de rapidez al pasar de un medio a otro.', True),
                abierta('Pon un lápiz en un vaso con agua y una moneda en el fondo de una taza que se ve al agregar agua. Explica ambos fenómenos con la refracción.', 6)])

    U[2] = unidad(
        tema='Cargas eléctricas, fuerzas eléctricas y magnéticas',
        objetivo='Explicar la electrización de los materiales, comparar las fuerzas eléctricas, magnéticas y gravitacionales y construir un electroimán.',
        explora=[texto('Frotas un globo en tu cabello y lo acercas a papelitos. ¿Por qué los atrae?')],
        aprende=[texto('Al frotar, los electrones pasan de un material a otro: el globo gana electrones (queda <b>negativo</b>) y el cabello los pierde (queda <b>positivo</b>). '
                       'Cargas iguales se repelen; distintas se atraen. También se carga por <b>contacto</b> e <b>inducción</b>.'),
                 texto('<b>Ley de Coulomb</b>: F = k·q₁·q₂ / r². Si la distancia se duplica, la fuerza se reduce a la <b>cuarta parte</b>.'),
                 tabla([['Fuerza', 'Atrae', 'Repele'], ['Gravitacional', 'sí', 'no'], ['Eléctrica', 'sí', 'sí'], ['Magnética', 'sí', 'sí']]),
                 texto('En 1820 Hans Christian Ørsted notó que una corriente eléctrica desviaba una brújula: <b>las cargas en movimiento producen magnetismo</b>.'),
                 texto('<b>Electroimán</b>: enrolla alambre de cobre esmaltado alrededor de un clavo y conecta los extremos a una pila. Más vueltas o más corriente → más fuerza.')],
        recuerda=['Iguales se repelen, distintas se atraen.', 'Corriente eléctrica → campo magnético.'],
        practica=[unica('Si un cuerpo gana electrones queda cargado…', 'negativamente', ['positivamente']),
                  numerica('Si la distancia entre dos cargas se duplica, la fuerza se divide entre…', 4)],
        taller=[unica('¿Qué fuerza solo puede atraer?', 'la gravitacional', ['la eléctrica', 'la magnética']),
                numerica('Si la distancia se triplica, la fuerza eléctrica se divide entre…', 9),
                unica('Para hacer más fuerte un electroimán puedo…', 'aumentar el número de vueltas', ['usar un clavo de madera']),
                abierta('Construye un electroimán con un clavo, alambre y una pila. Cuenta cuántos clips levanta con 10, 20 y 30 vueltas. Presenta tabla y conclusión.', 8)])

    U[3] = unidad(
        tema='Circuitos en serie, en paralelo y mixtos',
        objetivo='Calcular corrientes y voltajes con la ley de Ohm e identificar y predecir el comportamiento de circuitos en serie, en paralelo y mixtos.',
        explora=[texto('En una instalación navideña antigua, si se funde un bombillo se apagan todos. En tu casa, si se funde uno, los demás siguen. ¿Por qué?')],
        aprende=[texto('<b>Ley de Ohm</b>: V = I·R (voltaje en voltios, corriente en amperios, resistencia en ohmios). Con 12 V y 4 Ω: I = 3 A.'),
                 imagen('d-circuito', 35, 'Circuito sencillo'),
                 tabla([['', 'Serie', 'Paralelo'], ['Resistencia total', 'R = R₁ + R₂', '1/R = 1/R₁ + 1/R₂'], ['Corriente', 'la misma en todo', 'se reparte'],
                        ['Voltaje', 'se reparte', 'el mismo en cada rama'], ['Si un bombillo se funde', 'se apagan todos', 'los demás siguen']]),
                 texto('Serie: 2 Ω y 4 Ω con 12 V → R = 6 Ω, I = 2 A; en la de 4 Ω caen 8 V. Paralelo: 6 Ω y 3 Ω → R = 2 Ω; con 12 V la corriente total es 6 A.'),
                 texto('En serie, al agregar un bombillo todos alumbran <b>menos</b> (más resistencia, menos corriente). En paralelo, cada bombillo alumbra igual.')],
        recuerda=['V = I R.', 'Serie: se suman las resistencias. Paralelo: se suman los inversos.'],
        practica=[numerica('Corriente con 9 V y 3 Ω.', 3, 'A'), numerica('Resistencia total de 5 Ω y 10 Ω en serie.', 15, 'Ω')],
        taller=[numerica('Resistencia total de 6 Ω y 3 Ω en paralelo.', 2, 'Ω'), numerica('En serie, 2 Ω y 4 Ω con 12 V: voltaje en la resistencia de 2 Ω.', 4, 'V'),
                numerica('Mixto: 4 Ω en serie con (6 Ω ∥ 3 Ω). Resistencia total.', 6, 'Ω'),
                unica('Las casas se conectan en paralelo porque…', 'cada aparato funciona aunque otro se apague', ['así se gasta menos cable']),
                abierta('Arma con pilas y bombillos un circuito en serie y otro en paralelo. Desconecta un bombillo en cada uno y explica lo que observas.', 6)])

    U[4] = unidad(
        tema='Química orgánica: compuestos y reacciones',
        objetivo='Representar reacciones orgánicas, clasificar compuestos por sus grupos funcionales con pruebas químicas y explicar si una reacción es exotérmica o endotérmica.',
        explora=[texto('El gas de la estufa, el alcohol antiséptico, la acetona y el vinagre son compuestos orgánicos. ¿Qué tienen en común?')],
        aprende=[texto('Los compuestos orgánicos se basan en el <b>carbono</b>, que forma cuatro enlaces y cadenas. Hidrocarburos: metano CH₄, etano C₂H₆, propano C₃H₈, butano C₄H₁₀.'),
                 tabla([['Grupo funcional', 'Fórmula', 'Ejemplo'], ['Alcohol', '−OH', 'etanol (alcohol)'], ['Aldehído', '−CHO', 'metanal (formol)'],
                        ['Cetona', 'C=O en medio de la cadena', 'propanona (acetona)'], ['Ácido carboxílico', '−COOH', 'ácido acético (vinagre)'], ['Fenol', '−OH en un anillo bencénico', 'fenol']]),
                 tabla([['Prueba', 'Detecta', 'Resultado positivo'], ['Lugol (yodo)', 'almidón', 'azul oscuro'], ['Benedict', 'azúcares reductores', 'rojo ladrillo al calentar'],
                        ['Biuret', 'proteínas', 'violeta'], ['Sudán III', 'lípidos', 'gotas teñidas de rojo']]),
                 texto('Mecanismos: en la <b>homólisis</b> el enlace se rompe en partes iguales y se forman radicales; en la <b>heterólisis</b> un átomo se lleva los dos electrones y se forman iones.'),
                 texto('La combustión CH₄ + 2O₂ → CO₂ + 2H₂O es <b>exotérmica</b> (libera calor). Los <b>catalizadores</b> (en los seres vivos, las enzimas) aceleran las reacciones.')],
        recuerda=['Carbono: cuatro enlaces.', 'Grupo funcional → propiedades.', 'Exotérmica libera calor; endotérmica lo absorbe.'],
        practica=[unica('El grupo −OH caracteriza a los…', 'alcoholes', ['aldehídos', 'ácidos']), unica('El Lugol se vuelve azul oscuro con…', 'almidón', ['proteínas', 'lípidos'])],
        taller=[numerica('¿Cuántos átomos de hidrógeno tiene el propano (C₃H₈)?', 8), unica('La acetona es una…', 'cetona', ['alcohol', 'sal']),
                unica('Una reacción que absorbe calor del ambiente es…', 'endotérmica', ['exotérmica']),
                unica('El reactivo de Biuret detecta…', 'proteínas', ['almidón', 'grasas']),
                abierta('Prueba con Lugol una papa, pan, arroz, clara de huevo y azúcar. Registra los resultados en una tabla y explica qué contienen.', 6)])

    U[5] = unidad(
        tema='Calentamiento global y biodiversidad de Colombia',
        objetivo='Analizar el calentamiento global, la contaminación, la tala de bosques y la minería desde una visión sistémica y proponer acciones locales y globales.',
        explora=[texto('¿Por qué los glaciares de la Sierra Nevada del Cocuy se están derritiendo? ¿Qué tiene que ver eso con lo que consumimos?')],
        aprende=[texto('El <b>efecto invernadero</b> natural mantiene la Tierra habitable. Al quemar combustibles fósiles y talar bosques aumentan los gases (CO₂, metano): '
                       'el CO₂ pasó de unas 280 ppm antes de la Revolución Industrial a más de 400 ppm hoy, y la temperatura media sube.'),
                 imagen('n11-invernadero', 45),
                 texto('Colombia es un país <b>megadiverso</b>: es el primero del mundo en especies de aves y de orquídeas, y tiene buena parte de los páramos del planeta, '
                       'que regulan el agua de millones de personas.'),
                 tabla([['Actividad', 'Efecto sobre la biodiversidad'], ['Deforestación (ganadería, cultivos ilícitos)', 'pérdida de hábitat, sobre todo en la Amazonía'],
                        ['Minería ilegal', 'mercurio en ríos y peces'], ['Tráfico de fauna', 'disminuye poblaciones silvestres'], ['Carreteras y ciudades', 'fragmentan los ecosistemas']]),
                 texto('Visión <b>sistémica</b>: un problema ambiental también es económico (empleo), social (salud, desplazamiento) y cultural (territorios ancestrales).')],
        recuerda=['Más gases de invernadero → calentamiento global.', 'Colombia: megadiversa y vulnerable.'],
        practica=[unica('El principal gas de invernadero producido al quemar combustibles fósiles es…', 'CO₂', ['O₂', 'N₂']),
                  unica('Colombia es el primer país del mundo en especies de…', 'aves', ['leones', 'pingüinos'])],
        taller=[unica('La minería ilegal de oro contamina los ríos con…', 'mercurio', ['oxígeno', 'sal']), vf('Los páramos son importantes porque regulan el agua.', True),
                unica('Una acción local frente al calentamiento global es…', 'sembrar árboles nativos y reducir el consumo de energía', ['quemar la basura']),
                abierta('Investiga una especie amenazada de tu región. Propón un proyecto escolar para protegerla (acciones, responsables, indicadores).', 10)])
    return U
