"""Matemáticas 6.º: una guía y un taller por cada uno de los 12 DBA (V.2). Borradores para que el docente revise."""
from fractions import Fraction as F
from math import gcd

from .base import abierta, frac, grafica, lista, num, numerica, recuadro, tabla, texto, unica, vf


def _mcm(a, b):
    return a * b // gcd(a, b)


def unidades():
    U = {}

    # DBA 1 · Números enteros y racionales en contexto ---------------------------------------------------
    U[1] = dict(
        tema='Los números enteros y racionales a nuestro alrededor',
        objetivo='Usar números positivos, negativos, fracciones y decimales para describir situaciones reales y ubicarlos en la recta numérica.',
        explora=[texto('En Ibagué amaneció a 16 °C y en el páramo de Letras, a −2 °C. Al mediodía en el páramo subió 9 grados.',
                       '¿A qué temperatura llegó el páramo al mediodía? ¿Cuántos grados de diferencia había entre Ibagué y el páramo en la mañana?')],
        aprende=[
            texto('Los <b>números enteros</b> son los naturales, el cero y sus opuestos negativos: …, −3, −2, −1, 0, 1, 2, 3, … Sirven para temperaturas bajo cero, deudas, pisos bajo tierra o alturas bajo el nivel del mar.',
                  'Los <b>números racionales</b> se escriben como fracción \\(\\frac{a}{b}\\) con b ≠ 0, y también como decimal: \\(\\frac{3}{4} = 0{,}75\\) porque 3 ÷ 4 = 0,75.'),
            tabla([['Fracción', 'División', 'Decimal'], ['1/2', '1 ÷ 2', '0,5'], ['3/4', '3 ÷ 4', '0,75'], ['2/5', '2 ÷ 5', '0,4'], ['7/10', '7 ÷ 10', '0,7']]),
            texto('<b>En la recta numérica</b> los números crecen hacia la derecha. Por eso −5 &lt; −2: el −5 está más a la izquierda (hace más frío a −5 °C que a −2 °C).',
                  '<b>Ejemplo.</b> Si la temperatura pasa de −2 °C a 7 °C, el cambio es 7 − (−2) = 9 grados.'),
        ],
        recuerda=['Entre dos números negativos, es menor el que está más lejos del cero.', 'Para pasar una fracción a decimal se divide el numerador entre el denominador.'],
        practica=[
            numerica('Un buzo está a −12 m y sube 5 m. ¿A qué profundidad queda? (escribe el número con su signo)', -12 + 5, 'm'),
            unica('¿Cuál es el decimal de \\(\\frac{3}{5}\\)?', '0,6', ['0,35', '3,5', '0,53']),
        ],
        taller=[
            numerica('¿Cuántos grados subió la temperatura si pasó de −3 °C a 5 °C?', 5 - (-3), '°C'),
            unica('¿Cuál de estos números es el menor?', '−7', ['−3', '0', '2']),
            unica('¿Qué decimal corresponde a \\(\\frac{3}{4}\\)?', '0,75', ['0,34', '3,4', '0,43']),
            unica('¿Qué fracción es igual a 0,4?', '2/5', ['4/100', '1/4', '4/5']),
            numerica('Juan debía $8 000 y pagó $5 500. Escribe su saldo con signo (negativo si todavía debe).', -8000 + 5500, 'pesos'),
            vf('En la recta numérica, −1 está a la izquierda de −4.', False, 'Falso: −4 está más a la izquierda, porque −4 < −1.'),
            abierta('Ubica en una recta numérica −3, \\(\\frac{1}{2}\\), 1,5 y −0,5. Explica cómo decidiste dónde va cada uno.'),
        ])

    # DBA 2 · Propiedades de los números y estrategias de cálculo ----------------------------------------
    U[2] = dict(
        tema='Divisibilidad, primos, MCM, MCD y potencias',
        objetivo='Usar las propiedades de los números y de las operaciones para calcular de varias maneras y resolver problemas.',
        explora=[texto('Dos buses salen de la terminal: uno cada 4 minutos y otro cada 6 minutos. Si salen juntos a las 7:00 a. m., ¿a qué hora vuelven a salir juntos?')],
        aprende=[
            texto('<b>Criterios de divisibilidad.</b> Un número es divisible por 2 si termina en cifra par; por 3 si la suma de sus cifras es múltiplo de 3; por 5 si termina en 0 o 5; por 10 si termina en 0.',
                  'Un número es <b>primo</b> si solo tiene dos divisores: 1 y él mismo (2, 3, 5, 7, 11, 13…). Si tiene más, es <b>compuesto</b>: 91 = 7 × 13.'),
            texto(f'<b>Mínimo común múltiplo (MCM)</b>: el menor múltiplo que comparten. MCM(4, 6) = {_mcm(4, 6)}: los buses vuelven a salir juntos 12 minutos después, a las 7:12.',
                  f'<b>Máximo común divisor (MCD)</b>: el mayor número que divide a ambos. MCD(18, 24) = {gcd(18, 24)}.',
                  'Las <b>potencias</b> son multiplicaciones repetidas: \\(2^5 = 2 \\times 2 \\times 2 \\times 2 \\times 2 = 32\\).',
                  '<b>Propiedad distributiva</b> para calcular mentalmente: 7 × 13 = 7 × (10 + 3) = 70 + 21 = 91.'),
        ],
        recuerda=['MCM: para «cuándo vuelven a coincidir». MCD: para «repartir en partes iguales lo más grandes posible».', 'El 1 no es primo ni compuesto.'],
        practica=[
            numerica('¿Cuál es el MCM de 3 y 4?', _mcm(3, 4)),
            unica('¿Cuál de estos números es primo?', '29', ['27', '33', '39']),
        ],
        taller=[
            numerica('Calcula el MCM de 4 y 6.', _mcm(4, 6)),
            numerica('Calcula el MCD de 18 y 24.', gcd(18, 24)),
            unica('¿Por qué 91 no es un número primo?', 'Porque 91 = 7 × 13', ['Porque es impar', 'Porque termina en 1', 'Porque es mayor que 50']),
            numerica('¿Cuánto vale \\(2^5\\)?', 2 ** 5),
            unica('¿Cuál número es divisible por 3?', '1 236', ['1 234', '1 235', '1 237'], 'La suma de las cifras de 1 236 es 12, que es múltiplo de 3.'),
            numerica('Se reparten 36 mangos y 48 naranjas en bolsas iguales, sin mezclar ni sobrar. ¿Cuántas frutas, como máximo, lleva cada bolsa?', gcd(36, 48)),
            abierta('Calcula 8 × 25 de dos maneras diferentes y explica cuál te parece más fácil.'),
        ])

    # DBA 3 · Relaciones de orden y equivalencia -----------------------------------------------------------
    U[3] = dict(
        tema='Comparar y ordenar números; fracciones equivalentes',
        objetivo='Comparar, ordenar y encontrar números equivalentes, y argumentar los procedimientos.',
        explora=[texto('Ana comió \\(\\frac{2}{3}\\) de una arepa y Luis \\(\\frac{3}{4}\\) de otra igual. ¿Quién comió más? ¿Cómo lo sabes?')],
        aprende=[
            texto('Dos fracciones son <b>equivalentes</b> si representan la misma cantidad: \\(\\frac{2}{3} = \\frac{8}{12}\\) (se multiplicó arriba y abajo por 4).',
                  'Para <b>comparar fracciones</b> se pasan a igual denominador: \\(\\frac{2}{3} = \\frac{8}{12}\\) y \\(\\frac{3}{4} = \\frac{9}{12}\\); como 9 &gt; 8, Luis comió más.',
                  'También se pueden pasar a decimal: \\(\\frac{2}{5} = 0{,}4\\), \\(\\frac{1}{2} = 0{,}5\\), \\(\\frac{3}{4} = 0{,}75\\). Orden: 0,4 &lt; 0,5 &lt; 0,75.'),
            texto('<b>Igualdad y ecuaciones sencillas.</b> Si x + 5 = 12, el número que falta es 7, porque 7 + 5 = 12. La igualdad se conserva si se hace lo mismo a los dos lados.'),
        ],
        recuerda=['Multiplicar o dividir numerador y denominador por el mismo número da una fracción equivalente.', 'Con números negativos: −7 &lt; −3.'],
        practica=[
            numerica('Completa: \\(\\frac{2}{3} = \\frac{?}{12}\\)', 8),
            unica('¿Qué fracción es mayor?', '3/4', ['2/3', '1/2', '3/5']),
        ],
        taller=[
            numerica('Completa: \\(\\frac{3}{5} = \\frac{?}{20}\\)', 12),
            unica('¿Cuál está ordenado de menor a mayor?', '2/5 < 0,5 < 3/4', ['0,5 < 2/5 < 3/4', '3/4 < 0,5 < 2/5', '2/5 < 3/4 < 0,5']),
            vf('−7 es menor que −3.', True),
            numerica('¿Qué número hace verdadera la igualdad x + 5 = 12?', 12 - 5),
            unica('¿Qué fracción NO es equivalente a \\(\\frac{1}{2}\\)?', '3/5', ['2/4', '5/10', '6/12']),
            numerica('¿Qué número hace verdadera la igualdad 4 × x = 28?', 28 // 4),
            abierta('Explica con un dibujo por qué \\(\\frac{1}{2}\\) y \\(\\frac{2}{4}\\) son la misma cantidad.'),
        ])

    # DBA 4 · Construcción de figuras y cuerpos -----------------------------------------------------------------
    U[4] = dict(
        tema='Plantillas de cuerpos geométricos y construcciones con regla y compás',
        objetivo='Construir figuras planas con regla y compás y armar cuerpos geométricos a partir de sus plantillas.',
        explora=[texto('Si desarmas una caja de cartón de un medicamento y la extiendes sobre la mesa, ¿qué figuras ves? ¿Cuántas son?')],
        aprende=[
            texto('La <b>plantilla</b> (desarrollo plano) de un cuerpo es la figura que, doblada, lo arma. La del cubo tiene 6 cuadrados iguales; la de un prisma rectangular, 6 rectángulos (iguales de a dos).'),
            tabla([['Cuerpo', 'Caras', 'Vértices', 'Aristas'], ['Cubo', '6', '8', '12'], ['Prisma triangular', '5', '6', '9'],
                   ['Pirámide cuadrangular', '5', '5', '8'], ['Pirámide triangular', '4', '4', '6']]),
            texto('<b>Triángulo con regla y compás</b> (lados 5, 4 y 3 cm): 1) traza un segmento de 5 cm; 2) con el compás abierto a 4 cm haz un arco desde un extremo; 3) con 3 cm, otro arco desde el otro extremo; 4) une el punto donde se cortan con los extremos.'),
        ],
        recuerda=['En un poliedro: caras + vértices − aristas = 2 (fórmula de Euler).', 'El compás sirve para copiar medidas sin usar los números de la regla.'],
        practica=[
            numerica('¿Cuántas caras tiene un prisma triangular?', 5),
            unica('¿Cuántos cuadrados tiene la plantilla de un cubo?', '6', ['4', '5', '8']),
        ],
        taller=[
            numerica('¿Cuántos vértices tiene una pirámide de base cuadrada?', 5),
            numerica('¿Cuántas aristas tiene un cubo?', 12),
            unica('¿Qué figuras forman la plantilla de un prisma triangular?', '2 triángulos y 3 rectángulos', ['3 triángulos y 2 rectángulos', '6 cuadrados', '1 cuadrado y 4 triángulos']),
            numerica('Un poliedro tiene 6 caras y 8 vértices. ¿Cuántas aristas tiene? (caras + vértices − aristas = 2)', 6 + 8 - 2),
            vf('Con regla y compás se puede construir un triángulo de lados 2 cm, 3 cm y 7 cm.', False,
               'Falso: 2 + 3 = 5 es menor que 7; los arcos no se cortan.'),
            abierta('Describe paso a paso cómo construyes con regla y compás un triángulo de lados 6 cm, 5 cm y 4 cm.', 6),
        ])

    # DBA 5 · Estimación, medición y cálculo ----------------------------------------------------------------------
    U[5] = dict(
        tema='Medir y estimar: longitudes, áreas, volúmenes y ángulos',
        objetivo='Estimar y calcular perímetros, áreas, volúmenes y ángulos, escogiendo la unidad y el instrumento adecuados.',
        explora=[texto('Una huerta escolar rectangular mide 8 m de largo y 5 m de ancho. ¿Cuánta malla se necesita para encerrarla? ¿Cuánto terreno hay para sembrar?')],
        aprende=[
            texto(f'<b>Perímetro</b>: la medida del borde. Rectángulo: 8 + 5 + 8 + 5 = {2 * (8 + 5)} m de malla.',
                  f'<b>Área</b>: la superficie. Rectángulo: largo × ancho = 8 × 5 = {8 * 5} m².',
                  f'<b>Volumen</b>: el espacio que ocupa un cuerpo. Caja: largo × ancho × alto; una de 3 × 4 × 5 cm tiene {3 * 4 * 5} cm³.',
                  '<b>Ángulos</b>: se miden en grados con el transportador. Dos ángulos son complementarios si suman 90° y suplementarios si suman 180°.',
                  '<b>Unidades</b>: 1 m = 100 cm, 1 km = 1 000 m. Para pasar de m a cm se multiplica por 100.'),
        ],
        recuerda=['Perímetro en unidades de longitud (m), área en unidades cuadradas (m²), volumen en unidades cúbicas (m³).', 'Antes de medir, estima: así detectas errores.'],
        practica=[
            numerica('¿Cuál es el perímetro de un rectángulo de 7 cm por 3 cm?', 2 * (7 + 3), 'cm'),
            numerica('¿Cuántos centímetros son 2,5 m?', 250, 'cm'),
        ],
        taller=[
            numerica('Perímetro de la huerta de 8 m por 5 m.', 2 * (8 + 5), 'm'),
            numerica('Área de la huerta de 8 m por 5 m.', 8 * 5, 'm²'),
            numerica('Volumen de una caja de 3 cm × 4 cm × 5 cm.', 3 * 4 * 5, 'cm³'),
            numerica('¿Cuánto mide el complemento de un ángulo de 35°?', 90 - 35, '°'),
            numerica('¿Cuánto mide el suplemento de un ángulo de 120°?', 180 - 120, '°'),
            unica('¿Qué unidad es la más adecuada para medir el largo de un lápiz?', 'centímetros', ['kilómetros', 'metros cúbicos', 'litros']),
            abierta('Estima el área del tablero de tu salón. Luego mídelo y compara. ¿Cuánto te equivocaste?'),
        ])

    # DBA 6 · Formas bidimensionales y tridimensionales --------------------------------------------------------------
    U[6] = dict(
        tema='Figuras y cuerpos: propiedades, congruencia y semejanza',
        objetivo='Reconocer las propiedades de figuras y cuerpos, y describir cuándo son congruentes o semejantes.',
        explora=[texto('Una foto de 10 cm × 15 cm se amplía al doble. ¿Cuánto miden sus lados ahora? ¿Se ve igual la imagen?')],
        aprende=[
            texto('Los <b>triángulos</b> se clasifican por sus lados (equilátero: 3 iguales; isósceles: 2; escaleno: ninguno) y por sus ángulos (acutángulo, rectángulo, obtusángulo).',
                  f'Los ángulos internos de un triángulo suman 180°. Si dos miden 50° y 70°, el tercero mide 180 − 50 − 70 = {180 - 50 - 70}°.',
                  'Dos figuras son <b>congruentes</b> si tienen la misma forma y el mismo tamaño; son <b>semejantes</b> si tienen la misma forma y sus medidas son proporcionales (ampliación o reducción).',
                  'Ejemplo: un rectángulo de 2 × 3 ampliado al doble mide 4 × 6; es semejante al original.'),
        ],
        recuerda=['Semejantes: misma forma, otro tamaño. Congruentes: misma forma y mismo tamaño.', 'Suma de ángulos internos: triángulo 180°, cuadrilátero 360°.'],
        practica=[
            numerica('Dos ángulos de un triángulo miden 40° y 60°. ¿Cuánto mide el tercero?', 180 - 40 - 60, '°'),
            unica('Un triángulo con sus tres lados iguales es…', 'equilátero', ['isósceles', 'escaleno', 'rectángulo']),
        ],
        taller=[
            numerica('Dos ángulos de un triángulo miden 50° y 70°. ¿Cuánto mide el tercero?', 180 - 50 - 70, '°'),
            unica('Un triángulo con un ángulo de 90° se llama…', 'rectángulo', ['obtusángulo', 'acutángulo', 'equilátero']),
            numerica('Un rectángulo de 2 cm × 3 cm se amplía al triple. ¿Cuánto mide el lado más largo de la ampliación?', 3 * 3, 'cm'),
            vf('Dos cuadrados de distinto tamaño son semejantes.', True),
            numerica('Tres ángulos de un cuadrilátero miden 90°, 90° y 100°. ¿Cuánto mide el cuarto?', 360 - 90 - 90 - 100, '°'),
            unica('¿Cuántas caras tiene un prisma rectangular?', '6', ['4', '5', '8']),
            abierta('Dibuja dos triángulos semejantes y dos congruentes. Explica la diferencia.'),
        ])

    # DBA 7 · Plano cartesiano --------------------------------------------------------------------------------------
    plano = {'x': [-5, 5], 'y': [-4, 4], 'escala_igual': True, 'forma': 'cuadrada', 'elementos': [
        {'t': 'punto', 'x': 2, 'y': 3, 'nombre': 'A'}, {'t': 'punto', 'x': -3, 'y': 1, 'nombre': 'B', 'color': '#dc2626'},
        {'t': 'punto', 'x': -2, 'y': -2, 'nombre': 'C', 'color': '#16a34a'}, {'t': 'punto', 'x': 4, 'y': -3, 'nombre': 'D', 'color': '#9333ea'}]}
    U[7] = dict(
        tema='El plano cartesiano: ubicar puntos y describir trayectorias',
        objetivo='Ubicar puntos con coordenadas, reconocer los cuadrantes y describir desplazamientos en el plano.',
        explora=[texto('En el mapa del colegio, la tienda está «3 cuadras al oriente y 2 al norte» de la entrada. ¿Cómo lo dirías con dos números?')],
        aprende=[
            texto('El <b>plano cartesiano</b> tiene dos rectas numéricas perpendiculares: el eje x (horizontal) y el eje y (vertical). Se cortan en el origen (0, 0).',
                  'Cada punto tiene dos <b>coordenadas</b> (x, y): primero se avanza en x (derecha +, izquierda −) y luego en y (arriba +, abajo −).'),
            grafica(plano, 55, 'Puntos A(2, 3), B(−3, 1), C(−2, −2) y D(4, −3)'),
            texto('Los ejes dividen el plano en cuatro <b>cuadrantes</b>: I (+, +), II (−, +), III (−, −) y IV (+, −). B está en el II y D en el IV.',
                  'Un <b>desplazamiento</b> suma a las coordenadas: desde (1, 2), 3 a la derecha y 2 abajo llega a (1 + 3, 2 − 2) = (4, 0).'),
        ],
        recuerda=['El orden importa: (2, 3) no es el mismo punto que (3, 2).', 'Si un punto está sobre el eje x, su coordenada y es 0.'],
        practica=[
            unica('¿En qué cuadrante está el punto (−3, 1)?', 'II', ['I', 'III', 'IV']),
            unica('¿Cuáles son las coordenadas de A en la gráfica?', '(2, 3)', ['(3, 2)', '(−2, 3)', '(2, −3)']),
        ],
        taller=[
            unica('¿En qué cuadrante está (4, −3)?', 'IV', ['I', 'II', 'III']),
            unica('Desde (1, 2) te mueves 3 a la derecha y 2 hacia abajo. ¿A dónde llegas?', '(4, 0)', ['(3, 4)', '(−2, 0)', '(4, 4)']),
            vf('El punto (0, 5) está sobre el eje y.', True),
            unica('¿Qué punto está en el tercer cuadrante?', '(−2, −2)', ['(2, −2)', '(−2, 2)', '(2, 2)']),
            numerica('¿Cuántas unidades hay entre (−3, 1) y (4, 1)?', 4 - (-3)),
            abierta('Dibuja un plano, ubica (1, 1), (4, 1), (4, 3) y (1, 3) y únelos en orden. ¿Qué figura formaste? ¿Cuál es su perímetro?'),
        ])

    # DBA 8 · Covariación directa e inversa ---------------------------------------------------------------------------
    directa = {'x': [0, 6], 'y': [0, 14000], 'forma': 'ancha', 'nombre_x': 'cuadernos', 'nombre_y': 'pesos', 'elementos': [
        {'t': 'funcion', 'expr': '2000x', 'desde': '0', 'hasta': '6', 'nombre': 'precio'}] + [
        {'t': 'punto', 'x': k, 'y': 2000 * k, 'nombre': ''} for k in range(1, 7)]}
    U[8] = dict(
        tema='Variación directa e inversa',
        objetivo='Reconocer cuándo dos magnitudes varían de forma directa o inversa y representarlas en tablas y gráficas.',
        explora=[texto('Un cuaderno cuesta $2 000. ¿Cuánto cuestan 3? ¿Y 5? Si 4 trabajadores pintan el colegio en 12 días, ¿tardarán más o menos días 6 trabajadores?')],
        aprende=[
            texto('<b>Variación directa</b>: si una magnitud se duplica, la otra también; el cociente es constante. Precio = 2 000 × número de cuadernos.'),
            tabla([['Cuadernos', '1', '2', '3', '5'], ['Precio ($)'] + [num(2000 * k) for k in (1, 2, 3, 5)]]),
            grafica(directa, 55, 'Variación directa: la gráfica es una recta que pasa por el origen'),
            texto(f'<b>Variación inversa</b>: si una se duplica, la otra se reduce a la mitad; el producto es constante. 4 trabajadores × 12 días = 48; con 6 trabajadores: 48 ÷ 6 = {48 // 6} días.'),
        ],
        recuerda=['Directa: cociente constante (y ÷ x). Inversa: producto constante (x × y).', 'No todo lo que crece junto es directamente proporcional: revisa si el cociente es siempre el mismo.'],
        practica=[
            numerica('Si 3 cuadernos cuestan $6 000, ¿cuánto cuestan 5?', 6000 // 3 * 5, 'pesos'),
            numerica('Si 4 trabajadores tardan 12 días, ¿cuántos días tardan 6?', 4 * 12 // 6, 'días'),
        ],
        taller=[
            numerica('Un litro de leche cuesta $3 500. ¿Cuánto cuestan 4 litros?', 3500 * 4, 'pesos'),
            numerica('Un carro a 60 km/h tarda 4 horas en un viaje. ¿Cuántas horas tarda a 80 km/h?', 60 * 4 // 80, 'h'),
            unica('«A más estudiantes en la excursión, menos paga cada uno por el bus» es una variación…', 'inversa', ['directa', 'constante', 'ninguna']),
            unica('¿Qué tabla muestra variación directa?', 'x: 1, 2, 3 · y: 5, 10, 15', ['x: 1, 2, 3 · y: 6, 3, 2', 'x: 1, 2, 3 · y: 5, 7, 9', 'x: 1, 2, 3 · y: 1, 4, 9']),
            vf('La gráfica de una variación directa es una recta que pasa por (0, 0).', True),
            abierta('Inventa una situación de tu casa o tu barrio que sea de variación inversa y haz su tabla con 4 valores.'),
        ])

    # DBA 9 · Números desconocidos ---------------------------------------------------------------------------------------
    U[9] = dict(
        tema='Encontrar números desconocidos',
        objetivo='Plantear y resolver problemas con números desconocidos usando las operaciones inversas.',
        explora=[texto('«Pienso un número, lo multiplico por 2 y le resto 5. Me da 11.» ¿Qué número pensé?')],
        aprende=[
            texto('Se puede <b>deshacer</b> lo que se hizo, en orden contrario y con la operación inversa: al 11 le sumo 5 (16) y lo divido entre 2 (8). El número es 8. Comprobación: 8 × 2 − 5 = 11 ✓.',
                  'Con una letra: 2x − 5 = 11. Se resuelve igual: 2x = 16, x = 8.',
                  'Operaciones inversas: la suma deshace la resta, la división deshace la multiplicación.'),
            texto('<b>Ejemplo.</b> 3x + 4 = 19 → 3x = 15 → x = 5. <b>Ejemplo.</b> \\(\\frac{x}{4} = 7\\) → x = 28.'),
        ],
        recuerda=['Siempre comprueba reemplazando el número en el problema.', 'Lo que se hace a un lado de la igualdad se hace también al otro.'],
        practica=[
            numerica('Resuelve: x + 9 = 23', 23 - 9),
            numerica('Resuelve: 5x = 45', 45 // 5),
        ],
        taller=[
            numerica('Resuelve: 3x + 4 = 19', (19 - 4) // 3),
            numerica('Resuelve: \\(\\frac{x}{4} = 7\\)', 7 * 4),
            numerica('Pienso un número, lo multiplico por 2 y le resto 5; obtengo 11. ¿Qué número pensé?', (11 + 5) // 2),
            numerica('Resuelve: 2(x − 1) = 10', 10 // 2 + 1),
            numerica('Tres cuadernos iguales y un lapicero de $1 500 costaron $10 500. ¿Cuánto cuesta cada cuaderno?', (10500 - 1500) // 3, 'pesos'),
            abierta('Escribe un problema de tu vida diaria que se resuelva con la ecuación x + 15 = 40 y resuélvelo.'),
        ])

    # DBA 10 · Información estadística ------------------------------------------------------------------------------------
    datos = [('Mango', 8), ('Banano', 5), ('Fresa', 7)]
    total = sum(v for _, v in datos)
    barras = {'x': [0, 4], 'y': [0, 10], 'cuadricula': True, 'numeros': True, 'nombre_x': '', 'nombre_y': 'estudiantes', 'elementos': [
        {'t': 'poligono', 'puntos': [[i + 0.6, 0], [i + 1.4, 0], [i + 1.4, v], [i + 0.6, v]], 'relleno': True,
         'color': c, 'nombre': ''} for i, ((n, v), c) in enumerate(zip(datos, ('#f59e0b', '#eab308', '#dc2626')))] + [
        {'t': 'texto', 'x': i + 0.65, 'y': v + 0.4, 'texto': n} for i, (n, v) in enumerate(datos)]}
    U[10] = dict(
        tema='Leer y organizar información estadística',
        objetivo='Leer información de tablas y gráficos, organizar datos y plantear preguntas que se respondan con ellos.',
        explora=[texto(f'En 6.º A se preguntó la fruta favorita: mango {datos[0][1]}, banano {datos[1][1]}, fresa {datos[2][1]}. ¿Qué fruta conviene comprar más para el refrigerio?')],
        aprende=[
            texto('Una <b>tabla de frecuencias</b> organiza los datos: la frecuencia absoluta es cuántas veces aparece cada dato; la relativa, qué parte del total es (puede ir en porcentaje).'),
            tabla([['Fruta', 'Frecuencia', 'Porcentaje']] + [[n, v, f'{v * 100 // total} %'] for n, v in datos] + [['Total', total, '100 %']]),
            grafica(barras, 50, 'Diagrama de barras de la fruta favorita'),
            texto('Un buen estudio empieza con una <b>pregunta</b> clara («¿qué fruta prefieren?»), recoge los datos, los organiza y responde la pregunta.'),
        ],
        recuerda=['Porcentaje = frecuencia ÷ total × 100.', 'Revisa siempre el título y las escalas de un gráfico antes de sacar conclusiones.'],
        practica=[
            numerica('¿Cuántos estudiantes respondieron la encuesta?', total),
            numerica('¿Qué porcentaje prefiere mango?', datos[0][1] * 100 // total, '%'),
        ],
        taller=[
            unica('¿Cuál es la fruta preferida?', 'Mango', ['Banano', 'Fresa', 'Todas igual']),
            numerica('¿Cuántos estudiantes más prefieren fresa que banano?', datos[2][1] - datos[1][1]),
            numerica('¿Qué porcentaje prefiere banano?', datos[1][1] * 100 // total, '%'),
            unica('¿Qué gráfico es mejor para mostrar cómo cambió la temperatura durante una semana?', 'Gráfico de líneas', ['Diagrama circular', 'Tabla de frecuencias', 'Pictograma de frutas']),
            vf('Si en otra encuesta mango tiene 10 votos de 50, entonces mango es más popular allá que en 6.º A.', False,
               'Falso: 10 de 50 es el 20 %, y en 6.º A el mango tiene el 40 %.'),
            abierta('Plantea una pregunta para encuestar a tu curso, recoge los datos de 10 compañeros y organízalos en una tabla.', 6),
        ])

    # DBA 11 · Comparar poblaciones (tendencia central y rango) ----------------------------------------------------------------
    a6 = [4, 7, 7, 9, 8]
    b6 = [6, 6, 7, 7, 9]
    media = lambda d: F(sum(d), len(d))
    mediana = lambda d: sorted(d)[len(d) // 2]
    U[11] = dict(
        tema='Media, mediana, moda y rango para comparar grupos',
        objetivo='Comparar dos grupos de datos con la media, la mediana, la moda y el rango.',
        explora=[texto(f'Notas de un quiz (sobre 10). Grupo A: {", ".join(map(str, a6))}. Grupo B: {", ".join(map(str, b6))}. ¿Qué grupo le fue mejor? ¿Cuál fue más parejo?')],
        aprende=[
            texto(f'<b>Media</b> (promedio): se suman los datos y se divide entre cuántos son. A: {"+".join(map(str, a6))} = {sum(a6)}; {sum(a6)} ÷ 5 = {num(media(a6))}.',
                  f'<b>Mediana</b>: el dato del medio cuando se ordenan. A ordenado: {", ".join(map(str, sorted(a6)))} → {mediana(a6)}.',
                  '<b>Moda</b>: el dato que más se repite. En A es 7.',
                  f'<b>Rango</b>: mayor − menor. A: 9 − 4 = {max(a6) - min(a6)}; B: 9 − 6 = {max(b6) - min(b6)}. El grupo B fue más parejo (menor rango).'),
            tabla([['Grupo', 'Media', 'Mediana', 'Moda', 'Rango'], ['A', num(media(a6)), mediana(a6), 7, max(a6) - min(a6)],
                   ['B', num(media(b6)), mediana(b6), '6 y 7', max(b6) - min(b6)]]),
        ],
        recuerda=['La media se afecta mucho con un dato muy alto o muy bajo; la mediana no tanto.', 'El rango dice qué tan dispersos están los datos.'],
        practica=[
            numerica('Calcula la media de 3, 5, 7.', media([3, 5, 7])),
            numerica('¿Cuál es el rango de 12, 5, 9, 20?', 20 - 5),
        ],
        taller=[
            numerica(f'Calcula la media de {", ".join(map(str, a6))}.', media(a6)),
            numerica(f'¿Cuál es la mediana de {", ".join(map(str, a6))}?', mediana(a6)),
            numerica(f'¿Cuál es el rango de {", ".join(map(str, a6))}?', max(a6) - min(a6)),
            numerica('¿Cuál es la moda de 2, 3, 3, 5, 3, 8?', 3),
            unica(f'Grupo A: {", ".join(map(str, a6))}; grupo B: {", ".join(map(str, b6))}. ¿Qué grupo tiene los datos más parejos?', 'El B, porque su rango es menor', ['El A, porque su media es mayor', 'Los dos son iguales', 'El A, porque tiene un 4']),
            abierta('Pregunta la estatura (en cm) a 5 compañeros y a 5 compañeras. Compara los dos grupos con la media y el rango.', 6),
        ])

    # DBA 12 · Probabilidad: frecuencias esperadas y observadas -------------------------------------------------------------------
    U[12] = dict(
        tema='Experimentos aleatorios: lo que se espera y lo que pasa',
        objetivo='Enumerar resultados posibles, registrar repeticiones de un experimento y comparar lo observado con lo esperado.',
        explora=[texto('Si lanzas una moneda 50 veces, ¿cuántas caras esperas? Hazlo con un compañero y anota. ¿Salió exactamente lo que esperabas?')],
        aprende=[
            texto('Un <b>experimento aleatorio</b> es aquel cuyo resultado no se puede predecir con certeza: lanzar un dado, sacar una balota.',
                  'La <b>probabilidad</b> de un evento (si todos los resultados son igual de posibles) = casos favorables ÷ casos posibles. Sacar par en un dado: 3 ÷ 6 = \\(\\frac{1}{2}\\).',
                  'La <b>frecuencia relativa</b> es lo que pasó: si en 50 lanzamientos salieron 27 caras, es 27 ÷ 50 = 0,54. Con muchas repeticiones se acerca a la probabilidad (0,5).'),
            tabla([['Lanzamientos', 'Caras', 'Frecuencia relativa'], ['10', '6', '0,6'], ['50', '27', '0,54'], ['200', '103', '0,515']]),
        ],
        recuerda=['La probabilidad va de 0 (imposible) a 1 (seguro).', 'Con más repeticiones, lo observado se parece más a lo esperado.'],
        practica=[
            unica('¿Cuál es la probabilidad de sacar 5 en un dado?', '1/6', ['1/5', '5/6', '1/2']),
            numerica('¿Cuántos resultados posibles hay al lanzar dos monedas?', 4),
        ],
        taller=[
            unica('¿Cuál es la probabilidad de sacar un número par al lanzar un dado?', '1/2', ['1/3', '1/6', '2/3']),
            numerica('En 50 lanzamientos de una moneda salieron 27 caras. ¿Cuál es la frecuencia relativa de cara? (escribe el decimal)', F(27, 50)),
            unica('Una bolsa tiene 3 balotas rojas y 5 azules. ¿Cuál es la probabilidad de sacar una roja?', frac(F(3, 8)), ['3/5', '5/8', '1/3']),
            unica('¿Cuál evento es imposible al lanzar un dado común?', 'Sacar 7', ['Sacar 6', 'Sacar un número menor que 7', 'Sacar 1']),
            vf('Si una moneda cayó cara 3 veces seguidas, la próxima vez es más probable que caiga sello.', False,
               'Falso: cada lanzamiento es independiente; la probabilidad sigue siendo 1/2.'),
            abierta('Lanza un dado 30 veces y registra los resultados en una tabla. Compara cuántas veces salió el 6 con las que esperabas (30 ÷ 6 = 5).', 6),
        ])
    return U
