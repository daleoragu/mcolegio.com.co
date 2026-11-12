"""Matemáticas 4.º: una guía y un taller por cada uno de los 11 DBA (V.2). Fracciones y decimales, medida, transformaciones,
variación, secuencias, gráficos de barras agrupadas y de línea, y azar. Borradores para que el docente revise."""
from fractions import Fraction as F

from .base import abierta, frac, grafica, imagen, numerica, tabla, texto, unica, unidad, vf


def _lineas(puntos, x, y, nombre_x='', nombre_y=''):
    elementos = [{'t': 'segmento', 'a': a, 'b': b, 'nombre': ''} for a, b in zip(puntos, puntos[1:])]
    elementos += [{'t': 'punto', 'x': px, 'y': py, 'nombre': ''} for px, py in puntos]
    return {'x': x, 'y': y, 'nombre_x': nombre_x, 'nombre_y': nombre_y, 'elementos': elementos}


def _agrupadas(grupos, series, maximo):
    """Barras agrupadas: grupos = [nombre], series = [(nombre, [valores], color)]."""
    elementos, ancho = [], 0.8 / len(series)
    for i, g in enumerate(grupos):
        for j, (s, valores, color) in enumerate(series):
            x0 = i + 0.6 + j * ancho
            v = valores[i]
            elementos.append({'t': 'poligono', 'puntos': [[x0, 0], [x0 + ancho, 0], [x0 + ancho, v], [x0, v]], 'relleno': True,
                              'color': color, 'nombre': s if i == 0 else ''})
        elementos.append({'t': 'texto', 'x': i + 0.65, 'y': -maximo * 0.08, 'texto': g})
    return {'x': [0, len(grupos) + 1], 'y': [-maximo * 0.13, maximo * 1.15], 'nombre_x': '', 'nombre_y': '', 'elementos': elementos}


def unidades():
    U = {}

    U[1] = unidad(
        tema='Las fracciones y sus significados',
        objetivo='Usar fracciones como parte de un todo, como reparto (cociente), como razón y como operador.',
        explora=[imagen('m4-jugo-receta', 30), texto('Para una jarra de jugo se usan 3 lulos por cada 2 litros de agua. ¿Cuántos lulos para 4 litros?')],
        aprende=[tabla([['Significado', 'Ejemplo'], ['Parte de un todo', '3/4 de la barra está pintada'], ['Cociente (reparto)', '3 arepas entre 4 niños: 3/4 de arepa a cada uno'],
                        ['Razón', '3 lulos por cada 2 litros: 3 a 2'], ['Operador', '2/3 de 30 estudiantes = 30 ÷ 3 × 2 = 20']]),
                 imagen('d-fraccion-3-4', 40, 'Tres cuartos'),
                 texto('Las fracciones <b>covarían</b>: si duplico el agua, duplico los lulos: 4 litros → 6 lulos.'),
                 texto('Las fracciones decimales se escriben como decimales: \\(\\frac{1}{2}\\) = 0,5; \\(\\frac{1}{4}\\) = 0,25; \\(\\frac{3}{10}\\) = 0,3.')],
        recuerda=['Para hallar 2/3 de una cantidad: divido entre 3 y multiplico por 2.', 'Una fracción puede escribirse como decimal.'],
        practica=[numerica('¿Cuánto es 2/3 de 30?', 20), numerica('3 arepas se reparten entre 4 niños. ¿Qué parte le toca a cada uno? Escribe el decimal.', F(3, 4))],
        taller=[numerica('¿Cuánto es 3/5 de 40?', 24), numerica('¿Cuántos lulos para 6 litros de agua (3 lulos por cada 2 litros)?', 9),
                numerica('Escribe 1/4 como decimal.', F(1, 4)), numerica('Escribe 7/10 como decimal.', F(7, 10)),
                unica('«En el salón hay 2 niñas por cada 3 niños» es una fracción como…', 'razón', ['parte de un todo', 'operador']),
                abierta('Escribe una situación de tu casa donde uses fracciones o decimales.', 4)])

    U[2] = unidad(
        tema='Grandes números, fracciones y decimales: estrategias de cálculo',
        objetivo='Leer y operar números mayores que 10 000, sumar y restar decimales y fracciones con estrategias propias.',
        explora=[texto('Un municipio tiene 28 450 habitantes y otro 31 600. ¿Cuántos hay entre los dos? ¿Cuál tiene más y por cuánto?')],
        aprende=[texto('En <b>28 450</b> hay 2 decenas de mil, 8 unidades de mil, 4 centenas, 5 decenas y 0 unidades.'),
                 texto('Sumamos por partes: 28 450 + 31 600 = (28 000 + 31 000) + (450 + 600) = 59 000 + 1 050 = <b>60 050</b>.'),
                 texto('<b>Decimales</b>: alineo la coma. 2,75 + 1,5 = 4,25 (porque 2,75 + 1,50).'),
                 texto('<b>Fracciones con igual denominador</b>: sumo los numeradores: \\(\\frac{2}{7} + \\frac{3}{7} = \\frac{5}{7}\\).'),
                 texto('<b>Fracciones equivalentes</b>: \\(\\frac{1}{2} = \\frac{2}{4} = \\frac{4}{8}\\) (multiplico arriba y abajo por el mismo número).')],
        recuerda=['Para sumar decimales, alineo las comas.', 'Para sumar fracciones con igual denominador, sumo numeradores.'],
        practica=[numerica('Calcula 28 450 + 31 600.', 60050), numerica('Calcula 2,75 + 1,5.', F(17, 4))],
        taller=[numerica('Calcula 31 600 − 28 450.', 3150), numerica('Calcula 3,4 + 2,25.', F(565, 100)),
                unica('¿Cuánto es 2/7 + 3/7?', '5/7', ['5/14', '6/7', '1/7']),
                unica('¿Cuál es equivalente a 1/2?', '4/8', ['1/4', '2/3', '3/8']),
                numerica('Calcula 15 × 12 descomponiendo (15 × 10 + 15 × 2).', 180)])

    U[3] = unidad(
        tema='Comparo fracciones y decimales',
        objetivo='Comparar y ordenar fracciones y decimales con dibujos y con criterios propios.',
        explora=[imagen('d-fraccion-2-3', 40), imagen('d-fraccion-3-4', 40), texto('¿Qué es más: 2/3 o 3/4 de la misma barra?')],
        aprende=[texto('Con <b>igual denominador</b>, es mayor la de mayor numerador: 5/8 &gt; 3/8.'),
                 texto('Con <b>igual numerador</b>, es mayor la de menor denominador: 1/3 &gt; 1/5 (partes más grandes).'),
                 texto('Si no, busco fracciones equivalentes con el mismo denominador: 2/3 = 8/12 y 3/4 = 9/12 → <b>3/4 &gt; 2/3</b>.'),
                 texto('<b>Decimales</b>: comparo cifra por cifra después de la coma: 0,7 &gt; 0,65 porque 7 décimos &gt; 6 décimos.'),
                 imagen('m4-tienda-decimales', 22, 'En la tienda pesamos con decimales')],
        recuerda=['Mismo denominador: gana el numerador mayor.', 'Mismo numerador: gana el denominador menor.'],
        practica=[unica('¿Cuál es mayor?', '1/3', ['1/5', '1/8']), unica('¿Cuál es mayor?', '0,7', ['0,65', '0,07'])],
        taller=[unica('¿Cuál es mayor?', '5/8', ['3/8', '1/8']), unica('Ordena de menor a mayor: ¿cuál va primero?', '0,25', ['0,5', '0,75']),
                unica('¿Cuál es mayor: 2/3 o 3/4?', '3/4', ['2/3', 'Son iguales']),
                vf('0,5 es lo mismo que 1/2.', True),
                abierta('Dibuja dos barras iguales y compara 2/5 con 1/2.', 5)])

    U[4] = unidad(
        tema='Atributos que medimos: masa, capacidad, temperatura',
        objetivo='Diferenciar masa, capacidad, volumen y temperatura, sus instrumentos y unidades.',
        explora=[texto('¿Qué pesa más: un kilo de algodón o un kilo de piedras? ¿Qué ocupa más espacio?')],
        aprende=[tabla([['Atributo', 'Instrumento', 'Unidades'], ['Masa (peso)', 'balanza, gramera', 'kilogramo (kg), gramo (g)'], ['Capacidad', 'jarra medidora, probeta', 'litro (L), mililitro (mL)'],
                        ['Temperatura', 'termómetro', 'grados Celsius (°C)'], ['Volumen', 'cubos, regla', 'cm³']]),
                 texto('Pesan lo mismo (1 kg), pero el algodón <b>ocupa más</b>: es menos <b>denso</b>. La <b>dureza</b> y la <b>viscosidad</b> (la miel fluye lento) también son atributos.'),
                 texto('1 kg = 1 000 g · 1 L = 1 000 mL · Un litro de agua pesa más o menos 1 kg.')],
        recuerda=['Cada atributo tiene su instrumento y su unidad.'],
        practica=[numerica('¿Cuántos gramos hay en 2 kg?', 2000, 'g'), unica('¿Con qué medimos la fiebre?', 'Termómetro', ['Balanza', 'Probeta'])],
        taller=[numerica('¿Cuántos mililitros hay en 3 litros?', 3000, 'mL'), numerica('Medio kilo son…', 500, 'g'),
                unica('¿Qué es más viscoso?', 'La miel', ['El agua', 'El jugo']),
                unica('Para medir la capacidad de una botella uso…', 'mililitros', ['kilos', 'grados']),
                abierta('Busca 3 productos en tu cocina y escribe si su etiqueta dice gramos o mililitros.', 3)])

    U[5] = unidad(
        tema='Medidas, equivalencias y proporcionalidad',
        objetivo='Convertir unidades, operar con medidas y resolver problemas de proporcionalidad directa e inversa.',
        explora=[texto('Si 2 kg de arroz cuestan $6 000, ¿cuánto cuestan 5 kg? Si 2 personas pintan una pared en 6 horas, ¿cuánto tardan 3?')],
        aprende=[texto('<b>Proporcionalidad directa</b>: si una cantidad crece, la otra crece igual. 1 kg → $3 000; 5 kg → <b>$15 000</b>.'),
                 tabla([['kg de arroz', '1', '2', '3', '5'], ['Precio ($)', '3 000', '6 000', '9 000', '15 000']]),
                 texto('<b>Proporcionalidad inversa</b>: si una crece, la otra disminuye. 2 personas → 6 h; 3 personas → <b>4 h</b> (porque 2 × 6 = 3 × 4 = 12).'),
                 texto('Equivalencias: 1 m = 100 cm · 1 km = 1 000 m · 1 h = 60 min · 1 min = 60 s.')],
        recuerda=['Directa: las dos aumentan. Inversa: una aumenta y la otra disminuye.'],
        practica=[numerica('Si 2 kg cuestan $6 000, ¿cuánto cuestan 5 kg?', 15000, 'pesos'), numerica('¿Cuántos metros son 2,5 km?', 2500, 'm')],
        taller=[numerica('3 cuadernos cuestan $9 000. ¿Cuánto cuestan 7?', 21000, 'pesos'),
                numerica('4 obreros hacen un muro en 6 días. ¿Cuántos días tardan 8 obreros?', 3, 'días'),
                numerica('¿Cuántos minutos son 3 horas?', 180, 'min'),
                unica('Más velocidad y menos tiempo para el mismo viaje es proporcionalidad…', 'inversa', ['directa']),
                numerica('Un bus viaja a 60 km por hora. ¿Cuántos km recorre en 3 horas?', 180, 'km')])

    U[6] = unidad(
        tema='Del plano al espacio: desarrollos planos',
        objetivo='Armar y desarmar cuerpos geométricos y reconocer qué desarrollo plano corresponde a cada sólido.',
        explora=[imagen('d-desarrollo', 30), texto('Si recortas y doblas esta figura por las líneas punteadas, ¿qué cuerpo se arma?')],
        aprende=[texto('El <b>desarrollo plano</b> de un sólido es la figura que queda al «desdoblarlo». El cubo se arma con <b>6 cuadrados</b>.'),
                 tabla([['Sólido', 'Su desarrollo tiene…'], ['Cubo', '6 cuadrados'], ['Prisma rectangular', '6 rectángulos'], ['Pirámide de base cuadrada', '1 cuadrado y 4 triángulos'],
                        ['Cilindro', '2 círculos y 1 rectángulo'], ['Cono', '1 círculo y un sector circular']]),
                 imagen('d-solidos-n', 70)],
        recuerda=['El número de caras del sólido = número de figuras del desarrollo.'],
        practica=[unica('El desarrollo del cilindro tiene…', '2 círculos y 1 rectángulo', ['6 cuadrados', '4 triángulos']),
                  numerica('¿Cuántos triángulos tiene el desarrollo de una pirámide de base cuadrada?', 4)],
        taller=[unica('Con 6 cuadrados iguales armo un…', 'cubo', ['cono', 'cilindro']),
                unica('¿Qué sólido sale de 1 círculo y un sector circular?', 'Cono', ['Cubo', 'Prisma']),
                numerica('¿Cuántas caras tiene un prisma rectangular?', 6),
                abierta('Dibuja en cartulina el desarrollo de un cubo de 5 cm de lado, recórtalo y ármalo.', 4)])

    traslacion = {'x': [-1, 10], 'y': [-1, 7], 'escala_igual': True, 'forma': 'ancha', 'elementos': [
        {'t': 'poligono', 'puntos': [[1, 1], [3, 1], [2, 3]], 'vertices': 'A, B, C', 'nombre': ''},
        {'t': 'poligono', 'puntos': [[6, 3], [8, 3], [7, 5]], 'vertices': "A', B', C'", 'color': '#dc2626', 'nombre': ''},
        {'t': 'vector', 'a': [2, 2], 'b': [7, 4], 'nombre': ''}]}
    U[7] = unidad(
        tema='Movimientos en el plano y ampliaciones',
        objetivo='Aplicar traslaciones, rotaciones y simetrías a figuras y diferenciar los efectos de ampliar y reducir.',
        explora=[imagen('m4-ampliacion', 40), texto('¿Qué cambia y qué se mantiene cuando ampliamos una foto?')],
        aprende=[grafica(traslacion, 55, 'Traslación: 5 a la derecha y 2 arriba'),
                 texto('En la <b>traslación</b>, la <b>rotación</b> y la <b>simetría</b> la figura no cambia de forma ni de tamaño.'),
                 texto('En una <b>ampliación</b> al doble, cada lado mide el doble y la forma se conserva. En una <b>reducción</b> a la mitad, cada lado mide la mitad.'),
                 imagen('d-cuadros-2-2', 18, 'Cuadrado de 2'), imagen('d-cuadros-4-4', 25, 'Ampliado al doble: lado 4')],
        recuerda=['Mover no cambia el tamaño; ampliar y reducir sí.', 'Al ampliar al doble, los lados se duplican.'],
        practica=[unica('Si amplío al doble un rectángulo de 3 × 2, queda de…', '6 × 4', ['5 × 4', '6 × 2', '3 × 4']),
                  unica('Al trasladar una figura, su tamaño…', 'se mantiene', ['se duplica', 'se reduce'])],
        taller=[unica('Si reduzco a la mitad un cuadrado de lado 8, su lado mide…', '4', ['16', '2', '8']),
                unica('Girar una figura alrededor de un punto es una…', 'rotación', ['traslación', 'ampliación']),
                vf('En una ampliación la forma de la figura cambia.', False),
                abierta('Dibuja en cuadrícula una figura y amplíala al doble.', 6)])

    U[8] = unidad(
        tema='Variación: tablas y gráficas',
        objetivo='Registrar cómo cambia una cantidad cuando cambia otra, en tablas y gráficas, e interpretarlas.',
        explora=[texto('Medimos la altura de una planta de frijol cada semana. ¿Cómo mostramos que crece?')],
        aprende=[tabla([['Semana', '0', '1', '2', '3', '4'], ['Altura (cm)', '0', '3', '7', '12', '16']]),
                 grafica(_lineas([[0, 0], [1, 3], [2, 7], [3, 12], [4, 16]], [-0.5, 5], [-1, 18], 'semana', 'cm'), 55, 'Altura de la planta'),
                 texto('La altura <b>depende</b> del tiempo. Entre la semana 2 y la 3 creció más (5 cm).')],
        recuerda=['Una tabla y una gráfica muestran cómo una cantidad depende de otra.'],
        practica=[numerica('¿Cuánto medía la planta en la semana 3?', 12, 'cm'), numerica('¿Cuánto creció de la semana 3 a la 4?', 4, 'cm')],
        taller=[numerica('¿Cuánto creció entre la semana 0 y la 2?', 7, 'cm'),
                unica('¿En qué semana creció más?', 'De la 2 a la 3', ['De la 0 a la 1', 'De la 3 a la 4']),
                unica('La altura depende de…', 'el tiempo', ['el color de la matera']),
                abierta('Mide la temperatura de tu ciudad a 4 horas distintas del día y haz una tabla y una gráfica.', 8)])

    U[9] = unidad(
        tema='Patrones y secuencias',
        objetivo='Encontrar la regla de secuencias aditivas y multiplicativas y predecir términos lejanos.',
        explora=[texto('Con fósforos se forman triángulos en fila: 1 triángulo usa 3 fósforos, 2 usan 5, 3 usan 7. ¿Cuántos para 10 triángulos?')],
        aprende=[tabla([['Triángulos', '1', '2', '3', '4', '10'], ['Fósforos', '3', '5', '7', '9', '21']]),
                 texto('La regla: cada triángulo nuevo agrega 2. Para n triángulos: <b>2 × n + 1</b>. Para 10: 2 × 10 + 1 = <b>21</b>.'),
                 texto('<b>Aditiva</b>: se suma lo mismo (4, 7, 10, 13…). <b>Multiplicativa</b>: se multiplica por lo mismo (3, 6, 12, 24…).')],
        recuerda=['Busco qué se suma o se multiplica de un término al siguiente.'],
        practica=[numerica('¿Cuántos fósforos para 20 triángulos?', 41), numerica('¿Qué sigue? 3, 6, 12, 24, ___', 48)],
        taller=[numerica('¿Qué sigue? 4, 7, 10, 13, ___', 16), numerica('¿Qué sigue? 1, 4, 16, 64, ___', 256),
                numerica('En 4, 7, 10, 13…, ¿cuál es el término número 10?', 31),
                unica('La secuencia 2, 6, 18, 54 es…', 'multiplicativa', ['aditiva']),
                abierta('Inventa una secuencia de figuras y escribe la regla para cualquier posición.', 5)])

    U[10] = unidad(
        tema='Tablas de doble entrada, barras agrupadas y gráficos de línea',
        objetivo='Hacer encuestas, organizar datos en tablas de doble entrada y representarlos en barras agrupadas o líneas.',
        explora=[texto('¿Les gusta igual el fútbol y el baloncesto a niños y niñas de 4.º? ¿Cómo lo averiguamos?')],
        aprende=[tabla([['Deporte', 'Niñas', 'Niños'], ['Fútbol', '8', '12'], ['Baloncesto', '6', '5'], ['Voleibol', '7', '3']]),
                 grafica(_agrupadas(['Fútbol', 'Balonc.', 'Voleibol'], [('niñas', [8, 6, 7], '#e63946'), ('niños', [12, 5, 3], '#4ea8de')], 12), 60,
                         'Barras agrupadas: niñas (rojo) y niños (azul)'),
                 texto('Una <b>tabla de doble entrada</b> cruza dos variables (deporte y género). Las <b>barras agrupadas</b> permiten comparar los grupos.'),
                 texto('El <b>gráfico de línea</b> sirve para mostrar cambios en el tiempo (temperatura, crecimiento).')],
        recuerda=['Primero formulo la pregunta, luego encuesto, organizo y grafico.'],
        practica=[numerica('¿Cuántas niñas prefieren voleibol?', 7), numerica('¿Cuántos estudiantes prefieren fútbol en total?', 20)],
        taller=[unica('¿En qué deporte hay más niñas que niños?', 'Voleibol', ['Fútbol', 'Baloncesto']),
                numerica('¿Cuántos estudiantes respondieron en total?', 41),
                unica('Para mostrar la temperatura a lo largo del día uso un gráfico…', 'de línea', ['circular', 'de barras agrupadas']),
                abierta('Haz una encuesta a 10 niñas y 10 niños sobre su fruta favorita, organízala en una tabla de doble entrada y grafícala.', 8)])

    U[11] = unidad(
        tema='¿Azar o seguro? Situaciones aleatorias y deterministas',
        objetivo='Diferenciar situaciones aleatorias de deterministas y usar bien las palabras azar, posibilidad y aleatorio.',
        explora=[texto('¿Puedes saber con seguridad qué número saldrá en un dado? ¿Y a qué hora sale el sol mañana?')],
        aprende=[tabla([['Aleatoria (hay azar)', 'Determinista (se sabe el resultado)'], ['lanzar un dado', 'el agua hierve a 100 °C al nivel del mar'],
                        ['ganar una rifa', 'después del lunes viene el martes'], ['el color de una canica sacada sin mirar', 'una piedra soltada cae al piso']]),
                 texto('En una situación <b>aleatoria</b> conozco los resultados posibles pero no sé cuál saldrá. En una <b>determinista</b> el resultado ya se sabe.')],
        recuerda=['Aleatorio: no sé qué va a salir. Determinista: siempre pasa lo mismo.'],
        practica=[unica('Lanzar una moneda es una situación…', 'aleatoria', ['determinista']), unica('Soltar un vaso y que caiga al piso es…', 'determinista', ['aleatorio'])],
        taller=[unica('El resultado de un partido de fútbol es…', 'aleatorio', ['determinista']),
                unica('Que 2 + 2 = 4 es…', 'determinista', ['aleatorio']),
                vf('En una rifa sé con seguridad quién va a ganar.', False),
                abierta('Escribe 3 situaciones aleatorias y 3 deterministas de tu vida.', 6)])
    return U
