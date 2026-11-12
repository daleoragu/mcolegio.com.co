"""Matemáticas 7.º: una guía y un taller por cada uno de los 9 DBA (V.2). Borradores para que el docente revise."""
from fractions import Fraction as F
from math import gcd, isqrt

from .base import abierta, frac, grafica, num, numerica, tabla, texto, unica, vf


def unidades():
    U = {}

    # DBA 1 · Racionales en contexto; enteros y porcentajes ----------------------------------------------------
    U[1] = dict(
        tema='Números racionales en la vida diaria: signos y porcentajes',
        objetivo='Resolver problemas con números enteros y racionales, incluidos aumentos y descuentos en porcentaje.',
        explora=[texto('Unos tenis cuestan $120 000 y tienen 25 % de descuento. Una camiseta de $40 000 subió 10 %. ¿Cuánto cuesta cada una ahora?')],
        aprende=[
            texto('<b>Suma de enteros</b>: con igual signo se suman y se deja el signo; con signo distinto se restan y queda el signo del de mayor valor absoluto: (−8) + 5 = −3.',
                  '<b>Multiplicación y división</b>: signos iguales dan positivo, signos distintos dan negativo: (−3) × (−4) = 12; (−20) ÷ 5 = −4.',
                  f'<b>Porcentaje</b>: el 25 % de 120 000 es \\(\\frac{{25}}{{100}} \\times 120\\,000 = {num(120000 * 25 // 100)}\\). Con el descuento, los tenis cuestan {num(120000 - 30000)}.',
                  f'Un aumento del 10 % sobre 40 000 es 4 000: la camiseta queda en {num(44000)}.'),
            tabla([['Operación', 'Resultado'], ['(−8) + 5', '−3'], ['(−3) × (−4)', '12'], ['(−20) ÷ 5', '−4'], ['3/4 de 60', '45']]),
        ],
        recuerda=['Descuento: precio × (1 − porcentaje). Aumento: precio × (1 + porcentaje).', '«Menos por menos da más» es solo para multiplicar y dividir.'],
        practica=[
            numerica('Calcula (−8) + 5.', -3),
            numerica('¿Cuánto es el 20 % de $45 000?', 45000 * 20 // 100, 'pesos'),
        ],
        taller=[
            numerica('Calcula (−3) × (−4).', 12),
            numerica('Calcula (−20) ÷ 5.', -4),
            numerica('Un bolso de $45 000 tiene 20 % de descuento. ¿Cuánto se paga?', 45000 - 45000 * 20 // 100, 'pesos'),
            numerica('Un arriendo de $800 000 sube 5 %. ¿Cuánto queda?', 800000 + 800000 * 5 // 100, 'pesos'),
            numerica('¿Cuánto es \\(\\frac{3}{4}\\) de 60?', 60 * 3 // 4),
            unica('La temperatura bajó de 4 °C a −6 °C. ¿Cuál fue el cambio?', '−10 °C', ['−2 °C', '10 °C', '2 °C']),
            abierta('Busca en un volante de supermercado una oferta con descuento y comprueba si el precio final está bien calculado.'),
        ])

    # DBA 2 · Algoritmos con racionales ------------------------------------------------------------------------
    U[2] = dict(
        tema='Operaciones con fracciones y decimales',
        objetivo='Sumar, restar, multiplicar y dividir fracciones y decimales, y estimar raíces y potencias.',
        explora=[texto('Para una receta se usan \\(\\frac{1}{2}\\) taza de leche y \\(\\frac{1}{3}\\) de taza de agua. ¿Cuánto líquido es en total? ¿Cabe en una taza?')],
        aprende=[
            texto(f'<b>Suma y resta</b>: se busca un denominador común (el MCM). \\(\\frac{{1}}{{2}} + \\frac{{1}}{{3}} = \\frac{{3}}{{6}} + \\frac{{2}}{{6}} = \\frac{{5}}{{6}}\\). Sí cabe en una taza.',
                  f'<b>Multiplicación</b>: numerador por numerador y denominador por denominador: \\(\\frac{{2}}{{3}} \\times \\frac{{3}}{{4}} = \\frac{{6}}{{12}} = \\frac{{1}}{{2}}\\).',
                  '<b>División</b>: se multiplica por el inverso: \\(\\frac{3}{5} \\div \\frac{1}{2} = \\frac{3}{5} \\times \\frac{2}{1} = \\frac{6}{5}\\).',
                  '<b>Decimales</b>: 0,6 × 0,5 = 0,30 (se multiplica 6 × 5 y se corren dos cifras).',
                  f'<b>Estimar raíces</b>: \\(\\sqrt{{50}}\\) está entre 7 y 8, porque 7² = 49 y 8² = 64. MCM(6, 8) = {6 * 8 // gcd(6, 8)} y MCD(6, 8) = {gcd(6, 8)}.'),
        ],
        recuerda=['Para sumar fracciones el denominador debe ser el mismo; para multiplicar, no.', 'Simplifica siempre el resultado.'],
        practica=[
            unica('¿Cuánto es \\(\\frac{1}{4} + \\frac{1}{2}\\)?', '3/4', ['2/6', '1/6', '2/4']),
            numerica('Calcula 0,6 × 0,5.', F(3, 10)),
        ],
        taller=[
            unica('¿Cuánto es \\(\\frac{1}{2} + \\frac{1}{3}\\)?', frac(F(1, 2) + F(1, 3)), ['2/5', '1/5', '2/6']),
            unica('¿Cuánto es \\(\\frac{2}{3} \\times \\frac{3}{4}\\)?', frac(F(2, 3) * F(3, 4)), ['5/7', '6/7', '8/9']),
            unica('¿Cuánto es \\(\\frac{3}{5} \\div \\frac{1}{2}\\)?', frac(F(3, 5) / F(1, 2)), ['3/10', '4/7', '5/6']),
            numerica('Calcula 2,5 + 1,75.', F(5, 2) + F(7, 4)),
            unica('¿Entre qué números enteros está \\(\\sqrt{50}\\)?', 'Entre 7 y 8', ['Entre 6 y 7', 'Entre 8 y 9', 'Entre 24 y 26']),
            numerica('Calcula el MCM de 6 y 8.', 6 * 8 // gcd(6, 8)),
            abierta('Representa en una recta numérica −1,5; \\(\\frac{3}{4}\\); 2 y \\(-\\frac{1}{2}\\).'),
        ])

    # DBA 3 · Representaciones de los racionales y cantidades desconocidas -------------------------------------------
    U[3] = dict(
        tema='Fracción, decimal y propiedades para hallar valores desconocidos',
        objetivo='Pasar entre fracción y decimal, usar las propiedades de las operaciones y hallar valores desconocidos.',
        explora=[texto('En una tienda, 3 kg de arroz y una panela de $3 000 cuestan $15 000. ¿Cuánto vale el kilo de arroz?')],
        aprende=[
            texto('<b>Fracción a decimal</b>: se divide. \\(\\frac{3}{8} = 3 \\div 8 = 0{,}375\\). <b>Decimal a fracción</b>: 0,25 = \\(\\frac{25}{100} = \\frac{1}{4}\\).',
                  '<b>Propiedades</b>: conmutativa (a + b = b + a), asociativa ((a + b) + c = a + (b + c)), distributiva (4(x + 2) = 4x + 8), modulativa (a + 0 = a, a × 1 = a) e inverso (a + (−a) = 0).',
                  f'<b>Valor desconocido</b>: 3x + 3 000 = 15 000 → 3x = 12 000 → x = {num(12000 // 3)}. El kilo cuesta {num(4000)}.'),
        ],
        recuerda=['Transformar una expresión (sumar, restar, multiplicar o dividir a ambos lados) no cambia la solución.', '0,5 = 1/2; 0,25 = 1/4; 0,75 = 3/4; 0,2 = 1/5.'],
        practica=[
            numerica('Escribe \\(\\frac{3}{8}\\) como decimal.', F(3, 8)),
            numerica('Resuelve 2x − 3 = 9.', (9 + 3) // 2),
        ],
        taller=[
            unica('¿Qué fracción es igual a 0,25?', '1/4', ['1/25', '2/5', '25/10']),
            numerica('Resuelve \\(\\frac{x}{3} + 2 = 5\\).', (5 - 2) * 3),
            unica('¿Cuál propiedad se usó en 4(x + 2) = 4x + 8?', 'Distributiva', ['Conmutativa', 'Asociativa', 'Modulativa']),
            numerica('3 kg de arroz y una panela de $3 000 cuestan $15 000. ¿Cuánto vale el kilo de arroz?', (15000 - 3000) // 3, 'pesos'),
            numerica('Escribe \\(\\frac{7}{20}\\) como decimal.', F(7, 20)),
            abierta('Calcula 25 × 36 usando la propiedad asociativa (25 × 4 × 9) y explica por qué es más fácil.'),
        ])

    # DBA 4 · Escalas ------------------------------------------------------------------------------------------------
    U[4] = dict(
        tema='Escalas: planos, mapas y maquetas',
        objetivo='Interpretar y usar escalas para representar distancias reales en planos, mapas y maquetas.',
        explora=[texto('En el plano de una casa, la sala mide 5 cm de largo. Debajo dice «Escala 1:100». ¿Cuánto mide la sala en la realidad?')],
        aprende=[
            texto('Una <b>escala</b> 1 : 100 significa que 1 cm del plano son 100 cm (1 m) en la realidad. Sala: 5 cm × 100 = 500 cm = 5 m.',
                  f'En un mapa a escala 1 : 50 000, 4 cm son 4 × 50 000 = {num(200000)} cm = 2 km.',
                  '<b>Ampliación</b> (escala mayor que 1, como 3 : 1): todo se ve 3 veces más grande. <b>Reducción</b> (1 : 10): 10 veces más pequeño.',
                  'Conversiones: 1 km = 1 000 m = 100 000 cm; 1 m = 100 cm.'),
            tabla([['Escala', 'En el plano', 'En la realidad'], ['1 : 100', '5 cm', '5 m'], ['1 : 50 000', '4 cm', '2 km'], ['1 : 20', '3 cm', '60 cm']]),
        ],
        recuerda=['Real = medida en el plano × denominador de la escala.', 'Escoge la escala según el tamaño del papel: una cancha en una hoja carta necesita una escala pequeña (1 : 1 000).'],
        practica=[
            numerica('Escala 1 : 100. Una pared mide 7 cm en el plano. ¿Cuántos metros mide en la realidad?', 7, 'm'),
            numerica('¿Cuántos metros son 1,2 km?', 1200, 'm'),
        ],
        taller=[
            numerica('Mapa a escala 1 : 50 000. Dos pueblos están a 4 cm. ¿Cuántos kilómetros los separan?', 4 * 50000 // 100000, 'km'),
            numerica('Escala 1 : 20. Un mueble mide 3 cm en el dibujo. ¿Cuántos centímetros mide en la realidad?', 3 * 20, 'cm'),
            numerica('Una cancha real mide 40 m de largo. A escala 1 : 1 000, ¿cuántos centímetros mide en el plano?', 4000 // 1000, 'cm'),
            unica('Una foto de 4 cm de ancho se amplía con escala 3 : 1. ¿Qué ancho tiene la ampliación?', '12 cm', ['7 cm', '1,3 cm', '43 cm']),
            vf('En la escala 1 : 100, el plano es más grande que la realidad.', False),
            abierta('Haz el plano de tu cuarto o de tu salón a escala 1 : 50. Anota las medidas reales y las del plano.', 6),
        ])

    # DBA 5 · Vistas y transformaciones ----------------------------------------------------------------------------------
    trans = {'x': [-5, 5], 'y': [-4, 4], 'escala_igual': True, 'forma': 'cuadrada', 'elementos': [
        {'t': 'poligono', 'puntos': [[1, 1], [3, 1], [3, 2]], 'vertices': 'A, B, C', 'nombre': ''},
        {'t': 'poligono', 'puntos': [[-1, 1], [-3, 1], [-3, 2]], 'vertices': "A', B', C'", 'color': '#dc2626', 'nombre': ''},
        {'t': 'texto', 'x': 1.2, 'y': 3.3, 'texto': 'reflexión en el eje y'}]}
    U[5] = dict(
        tema='Vistas de objetos y transformaciones en el plano',
        objetivo='Representar las vistas de objetos tridimensionales y reconocer traslaciones, rotaciones y reflexiones.',
        explora=[texto('Mira un vaso de frente, desde arriba y de lado. ¿Qué figura ves en cada caso? ¿Por qué cambian?')],
        aprende=[
            texto('Las <b>vistas</b> de un objeto son lo que se ve de frente, de lado y desde arriba. Un cilindro: de frente un rectángulo, desde arriba un círculo.',
                  '<b>Traslación</b>: se mueve sin girar. (x, y) → (x + a, y + b). <b>Reflexión</b> en el eje y: (x, y) → (−x, y); en el eje x: (x, y) → (x, −y). <b>Rotación de 180°</b> alrededor del origen: (x, y) → (−x, −y).'),
            grafica(trans, 55, 'El triángulo ABC y su reflexión A′B′C′ en el eje y'),
        ],
        recuerda=['Las transformaciones conservan la forma y el tamaño de la figura (son congruentes).', 'En la reflexión, la figura queda «al revés», como en un espejo.'],
        practica=[
            unica('Reflexión de (3, 2) en el eje y:', '(−3, 2)', ['(3, −2)', '(−3, −2)', '(2, 3)']),
            unica('Vista desde arriba de un cilindro parado:', 'Un círculo', ['Un rectángulo', 'Un triángulo', 'Un cuadrado']),
        ],
        taller=[
            unica('Traslada (1, 1) con el vector (2, −3):', '(3, −2)', ['(−1, 4)', '(2, −3)', '(3, 4)']),
            unica('Rotación de 180° de (2, 1) alrededor del origen:', '(−2, −1)', ['(1, 2)', '(−1, −2)', '(2, −1)']),
            unica('Reflexión de (−4, 3) en el eje x:', '(−4, −3)', ['(4, 3)', '(4, −3)', '(3, −4)']),
            unica('Vista de frente de una pirámide de base cuadrada:', 'Un triángulo', ['Un cuadrado', 'Un círculo', 'Un pentágono']),
            vf('Una traslación cambia el tamaño de la figura.', False),
            abierta('Dibuja las vistas de frente, de lado y desde arriba de una caja de fósforos.', 6),
        ])

    # DBA 6 · Variación del área y el perímetro ---------------------------------------------------------------------
    var = {'x': [0, 6], 'y': [0, 36], 'forma': 'ancha', 'nombre_x': 'lado', 'nombre_y': '', 'elementos': [
        {'t': 'funcion', 'expr': '4x', 'desde': '0', 'hasta': '6', 'nombre': 'perímetro'},
        {'t': 'funcion', 'expr': 'x^2', 'desde': '0', 'hasta': '6', 'nombre': 'área', 'color': '#dc2626'}]}
    U[6] = dict(
        tema='Cómo cambian el perímetro y el área',
        objetivo='Representar en el plano cartesiano cómo varían el perímetro y el área de una figura al cambiar sus lados.',
        explora=[texto('Si el lado de un cuadrado se duplica, ¿el perímetro se duplica? ¿Y el área?')],
        aprende=[
            texto('En un cuadrado de lado l: perímetro P = 4l y área A = l².'),
            tabla([['Lado', '1', '2', '3', '4', '5'], ['Perímetro'] + [str(4 * l) for l in range(1, 6)], ['Área'] + [str(l * l) for l in range(1, 6)]]),
            grafica(var, 60, 'El perímetro crece en línea recta; el área, en curva (cada vez más rápido)'),
            texto('Si el lado se duplica, el perímetro se duplica (factor 2) pero el área se cuadruplica (factor 4): de lado 3 a lado 6, el área pasa de 9 a 36.'),
        ],
        recuerda=['Factor k en los lados: perímetro × k; área × k².', 'Una gráfica recta indica variación lineal; una curva, que no lo es.'],
        practica=[
            numerica('Área de un cuadrado de lado 3.', 9, 'u²'),
            numerica('Si el área de un cuadrado es 49, ¿cuánto mide su lado?', isqrt(49)),
        ],
        taller=[
            numerica('Perímetro de un cuadrado de lado 6.', 24),
            numerica('Área de un cuadrado de lado 6.', 36),
            numerica('Si el lado se triplica, ¿por cuánto se multiplica el área?', 9),
            unica('En la gráfica, ¿cuál magnitud se representa con una recta?', 'El perímetro', ['El área', 'Las dos', 'Ninguna']),
            numerica('Un rectángulo de 2 × 5 se amplía al doble. ¿Cuál es su nueva área?', 4 * 10),
            abierta('Con 20 m de malla se quiere encerrar un corral rectangular. Haz una tabla con varios largos y anchos posibles y su área. ¿Cuál da más área?', 6),
        ])

    # DBA 7 · Ecuaciones y variación -------------------------------------------------------------------------------------
    U[7] = dict(
        tema='Plantear y resolver ecuaciones',
        objetivo='Traducir situaciones a ecuaciones, resolverlas y representar la variación en tablas y gráficas.',
        explora=[texto('El largo de una cancha es el doble de su ancho y su perímetro es 36 m. ¿Cuánto mide de ancho?')],
        aprende=[
            texto('<b>Plantear</b>: se llama x a lo que no se sabe. Ancho = x, largo = 2x, perímetro = x + 2x + x + 2x = 6x. Entonces 6x = 36 y x = 6 m.',
                  '<b>Resolver</b> con variables a los dos lados: 5x − 2 = 3x + 8 → 5x − 3x = 8 + 2 → 2x = 10 → x = 5.',
                  '<b>Variación</b>: y = 2x + 1 es una regla; con x = 4, y = 9.'),
            tabla([['x', '0', '1', '2', '3', '4'], ['y = 2x + 1'] + [str(2 * x + 1) for x in range(5)]]),
        ],
        recuerda=['Lo que se pasa al otro lado cambia a la operación inversa.', 'Comprueba siempre la solución en la ecuación original.'],
        practica=[
            numerica('Resuelve 5x − 2 = 3x + 8.', 5),
            numerica('La edad de Ana más 7 es 20. ¿Qué edad tiene Ana?', 13, 'años'),
        ],
        taller=[
            numerica('Resuelve 4x + 6 = 2x + 20.', (20 - 6) // 2),
            numerica('El largo de una cancha es el doble del ancho y el perímetro es 36 m. ¿Cuánto mide el ancho?', 36 // 6, 'm'),
            numerica('Si y = 2x + 1, ¿cuánto vale y cuando x = 4?', 9),
            unica('«El triple de un número menos 4 es 11» se escribe:', '3x − 4 = 11', ['3(x − 4) = 11', 'x − 4 = 3 × 11', '4 − 3x = 11']),
            numerica('Resuelve 3x − 4 = 11.', 5),
            abierta('Escribe una situación que se represente con y = 3x y haz su tabla para x = 0, 1, 2, 3.'),
        ])

    # DBA 8 · Estadística con datos agrupados ----------------------------------------------------------------------------
    intervalos = [('[140, 150)', 4), ('[150, 160)', 9), ('[160, 170)', 6), ('[170, 180)', 1)]
    marcas = [145, 155, 165, 175]
    n = sum(f for _, f in intervalos)
    media = F(sum(m * f for m, (_, f) in zip(marcas, intervalos)), n)
    hist = {'x': [135, 185], 'y': [0, 10], 'nombre_x': 'cm', 'nombre_y': 'estudiantes', 'elementos': [
        {'t': 'poligono', 'puntos': [[a, 0], [a + 10, 0], [a + 10, f], [a, f]], 'relleno': True, 'nombre': ''}
        for a, (_, f) in zip((140, 150, 160, 170), intervalos)]}
    U[8] = dict(
        tema='Estudios estadísticos: tablas e histogramas',
        objetivo='Plantear preguntas, organizar datos agrupados en tablas e histogramas y calcular medidas de tendencia central.',
        explora=[texto(f'Se midió la estatura de {n} estudiantes de 7.º. ¿Cómo organizar tantos datos para responder «¿qué estatura es la más común?»?')],
        aprende=[
            texto('Con muchos datos se agrupan en <b>intervalos</b>. La <b>marca de clase</b> es el punto medio: en [150, 160) es 155.'),
            tabla([['Estatura (cm)', 'Marca de clase', 'Frecuencia']] + [[i, m, f] for (i, f), m in zip(intervalos, marcas)] + [['Total', '', n]]),
            grafica(hist, 60, 'Histograma de las estaturas'),
            texto(f'<b>Media aproximada</b>: Σ (marca × frecuencia) ÷ total = {num(sum(m * f for m, (_, f) in zip(marcas, intervalos)))} ÷ {n} = {num(media)} cm. El intervalo con más estudiantes (intervalo modal) es [150, 160).'),
        ],
        recuerda=['Un histograma tiene las barras pegadas porque los intervalos son continuos.', 'El rango en datos agrupados: límite superior − límite inferior.'],
        practica=[
            numerica('¿Cuál es la marca de clase de [10, 20)?', 15),
            numerica(f'¿Cuántos estudiantes miden entre 160 y 170 cm?', intervalos[2][1]),
        ],
        taller=[
            numerica('¿Cuántos estudiantes se midieron en total?', n),
            unica('¿Cuál es el intervalo modal?', '[150, 160)', ['[140, 150)', '[160, 170)', '[170, 180)']),
            numerica('Calcula la media aproximada de las estaturas (en cm).', media, 'cm', tolerancia='0,5'),
            numerica('Calcula la media de 12, 15, 18 y 15.', F(12 + 15 + 18 + 15, 4)),
            unica('¿Qué gráfico es el adecuado para datos agrupados en intervalos?', 'Histograma', ['Diagrama circular', 'Pictograma', 'Diagrama de árbol']),
            abierta('Plantea una pregunta sobre el tiempo que tus compañeros dedican al celular, diseña cómo recoger los datos y en qué intervalos los agruparías.', 6),
        ])

    # DBA 9 · Principio multiplicativo y probabilidad ---------------------------------------------------------------------------
    U[9] = dict(
        tema='Contar con el principio multiplicativo y calcular probabilidades',
        objetivo='Contar resultados con diagramas de árbol y el principio multiplicativo, y asignar probabilidades a eventos compuestos.',
        explora=[texto('Para el uniforme de educación física hay 3 camisetas y 4 sudaderas. ¿De cuántas maneras te puedes vestir?')],
        aprende=[
            texto('<b>Diagrama de árbol</b>: de cada camiseta salen 4 ramas (una por sudadera). En total 3 × 4 = 12 combinaciones.',
                  '<b>Principio multiplicativo</b>: si una cosa se puede hacer de m maneras y otra de n, juntas se pueden hacer de m × n maneras. Menú con 2 entradas, 3 platos y 2 postres: 2 × 3 × 2 = 12 menús.',
                  f'<b>Probabilidad de eventos compuestos</b>: al lanzar dos monedas hay 4 resultados (CC, CS, SC, SS); P(dos caras) = \\(\\frac{{1}}{{4}}\\). Con dos dados hay 36 resultados; suman 7 en 6 de ellos: P = \\(\\frac{{6}}{{36}} = \\frac{{1}}{{6}}\\).'),
        ],
        recuerda=['Cuando el orden no importa (la pareja Ana–Luis es la misma que Luis–Ana), no se cuenta dos veces.', 'Probabilidad = favorables ÷ posibles.'],
        practica=[
            numerica('¿De cuántas maneras se combinan 3 camisetas y 4 sudaderas?', 12),
            unica('Al lanzar dos monedas, ¿cuál es la probabilidad de dos caras?', '1/4', ['1/2', '1/3', '2/4']),
        ],
        taller=[
            numerica('Menú con 2 entradas, 3 platos fuertes y 2 postres. ¿Cuántos menús distintos hay?', 2 * 3 * 2),
            numerica('¿Cuántos resultados hay al lanzar dos dados?', 36),
            unica('Con dos dados, ¿cuál es la probabilidad de que sumen 7?', frac(F(6, 36)), ['7/36', '1/12', '1/2']),
            numerica('¿Cuántas placas de 2 letras (de 26) y 1 dígito se pueden hacer si se pueden repetir?', 26 * 26 * 10),
            numerica('En un torneo de 4 equipos, cada uno juega una vez con cada otro. ¿Cuántos partidos hay?', 4 * 3 // 2),
            abierta('Haz el diagrama de árbol de lanzar una moneda y un dado. ¿Cuál es la probabilidad de cara y número par?', 6),
        ])
    return U
