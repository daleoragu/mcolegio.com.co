"""Matemáticas 5.º: una guía y un taller por cada uno de los 12 DBA (V.2). Fracciones, potenciación, factores primos,
área y volumen, plano cartesiano, gráficos, media y mediana, y probabilidad. Borradores para que el docente revise."""
from fractions import Fraction as F

from .base import abierta, grafica, imagen, numerica, tabla, texto, unica, unidad, vf


def unidades():
    U = {}

    U[1] = unidad(
        tema='Problemas con naturales, fracciones y potencias',
        objetivo='Resolver problemas aditivos, multiplicativos y de potenciación con números naturales y fraccionarios.',
        explora=[texto('En una granja hay 3 galpones, cada galpón tiene 3 jaulas y cada jaula 3 gallinas. ¿Cuántas gallinas hay?')],
        aprende=[texto('3 × 3 × 3 = <b>27</b>. Multiplicar un número por sí mismo varias veces es una <b>potencia</b>: \\(3^3 = 27\\) (base 3, exponente 3).'),
                 texto('Problemas con fracciones: de 60 estudiantes, \\(\\frac{2}{5}\\) van en bus. 60 ÷ 5 × 2 = <b>24</b> van en bus y 36 no.'),
                 texto('Para resolver: leo, identifico los datos y la pregunta, escojo las operaciones <b>suficientes y necesarias</b>, calculo y reviso.')],
        recuerda=['Potencia: base multiplicada por sí misma tantas veces como dice el exponente.', 'a/b de una cantidad: divido entre b y multiplico por a.'],
        practica=[numerica('¿Cuánto es \\(3^3\\)?', 27), numerica('De 60 estudiantes, 2/5 van en bus. ¿Cuántos van en bus?', 24)],
        taller=[numerica('¿Cuánto es \\(2^5\\)?', 32), numerica('¿Cuánto es \\(10^3\\)?', 1000),
                numerica('Un terreno de 1 200 m² se divide: 3/4 para cultivo. ¿Cuántos m² son de cultivo?', 900, 'm²'),
                numerica('Compré 3 kg de queso a $18 000 el kilo y pagué con $60 000. ¿Cuánto me devolvieron?', 60000 - 54000, 'pesos'),
                numerica('Una hoja se dobla por la mitad 4 veces. ¿En cuántas partes queda dividida?', 16)])

    U[2] = unidad(
        tema='Potencias y factores primos',
        objetivo='Usar las propiedades de la potenciación, descomponer números en factores primos y justificar estrategias de cálculo.',
        explora=[texto('¿De cuántas formas puedes escribir 36 como multiplicación? 4 × 9, 6 × 6, 2 × 18…')],
        aprende=[texto('Un número <b>primo</b> solo se divide por 1 y por sí mismo: 2, 3, 5, 7, 11, 13…'),
                 texto('Descomposición en factores primos: 36 = 2 × 2 × 3 × 3 = \\(2^2 \\times 3^2\\).'),
                 tabla([['36', '2'], ['18', '2'], ['9', '3'], ['3', '3'], ['1', '']], encabezado=False),
                 texto('Propiedades: \\(2^3 \\times 2^2 = 2^5\\) (se suman los exponentes); \\(a^1 = a\\); \\(a^0 = 1\\).')],
        recuerda=['Primo: solo dos divisores.', 'Producto de potencias de igual base: se suman los exponentes.'],
        practica=[unica('¿Cuál es primo?', '13', ['15', '21', '9']), unica('36 en factores primos es…', '2² × 3²', ['6²', '4 × 9', '2 × 3'])],
        taller=[unica('48 en factores primos es…', '2⁴ × 3', ['6 × 8', '2³ × 3', '2 × 24']),
                numerica('¿Cuánto es \\(2^3 \\times 2^2\\)?', 32), numerica('¿Cuánto es \\(7^0\\)?', 1),
                unica('¿Cuál NO es primo?', '1', ['2', '3', '5']),
                abierta('Descompón 60 y 90 en factores primos.', 4)])

    U[3] = unidad(
        tema='Ordeno fracciones y decimales en la recta',
        objetivo='Representar fracciones en la recta numérica y ordenar fracciones y decimales.',
        explora=[imagen('d-rectafr-4-m3', 60), texto('¿Qué fracción marca el punto rojo?')],
        aprende=[texto('Para ubicar \\(\\frac{3}{4}\\): divido el segmento de 0 a 1 en <b>4 partes iguales</b> y cuento 3.'),
                 imagen('d-rectafr-4-m5', 60, '5/4 está después del 1'),
                 texto('Ordenar: paso todo a decimales o a igual denominador. \\(\\frac{1}{2}\\) = 0,5; \\(\\frac{3}{5}\\) = 0,6; \\(\\frac{2}{5}\\) = 0,4 → 0,4 &lt; 0,5 &lt; 0,6.')],
        recuerda=['Las fracciones mayores que 1 quedan después del 1.', 'Pasar a decimales ayuda a ordenar.'],
        practica=[unica('¿Qué fracción marca el punto rojo de la primera recta?', '3/4', ['1/4', '4/3', '3/5']),
                  unica('Ordena de menor a mayor: ¿cuál va primero?', '2/5', ['1/2', '3/5'])],
        taller=[numerica('Escribe 3/5 como decimal.', F(3, 5)), unica('¿Cuál es mayor?', '0,8', ['3/4', '0,75']),
                unica('¿Dónde está 7/4 en la recta?', 'Entre 1 y 2', ['Entre 0 y 1', 'Después del 2']),
                unica('¿Cuál es la menor?', '1/8', ['1/4', '1/2']),
                abierta('Dibuja una recta del 0 al 2 y ubica 1/2, 3/4, 5/4 y 3/2.', 5)])

    U[4] = unidad(
        tema='Superficie y volumen; medidas a partir de planos',
        objetivo='Calcular áreas y volúmenes, elegir las unidades adecuadas y obtener medidas reales a partir de un plano a escala.',
        explora=[texto('En un plano, 1 cm representa 2 m. Un cuarto mide 3 cm por 2 cm en el plano. ¿Cuánto mide en la realidad?')],
        aprende=[texto('Escala 1 cm : 2 m. El cuarto mide 3 × 2 = <b>6 m</b> de largo y 2 × 2 = <b>4 m</b> de ancho. Su área es 6 × 4 = <b>24 m²</b>.'),
                 texto('<b>Área</b> (superficie): se mide en unidades cuadradas (cm², m²). <b>Volumen</b>: en unidades cúbicas (cm³, m³).'),
                 texto('Volumen de una caja (prisma rectangular) = largo × ancho × alto. Una caja de 5 × 4 × 3 cm tiene <b>60 cm³</b>.'),
                 imagen('d-cuadros-6-4', 30, 'Área por recubrimiento: 24 cuadritos')],
        recuerda=['Área: unidades cuadradas. Volumen: unidades cúbicas.', 'Volumen de la caja = largo × ancho × alto.'],
        practica=[numerica('Volumen de una caja de 5 × 4 × 3 cm.', 60, 'cm³'), numerica('Área de un patio de 12 m por 8 m.', 96, 'm²')],
        taller=[numerica('Escala 1 cm : 3 m. Una pared mide 4 cm en el plano. ¿Cuántos metros mide?', 12, 'm'),
                numerica('Volumen de un cubo de 4 cm de arista.', 64, 'cm³'),
                unica('¿En qué unidad medimos el agua que cabe en un tanque?', 'm³ o litros', ['m²', 'cm']),
                numerica('Un tanque mide 2 × 1 × 1 m. ¿Cuál es su volumen?', 2, 'm³'),
                abierta('Haz el plano de tu salón a escala (1 cm = 1 m) y calcula su área real.', 8)])

    U[5] = unidad(
        tema='Perímetro y área: no siempre cambian juntos',
        objetivo='Explicar que cambiar el perímetro no implica cambiar el área (y al revés), y calcular lados a partir del área.',
        explora=[texto('Con 24 m de malla, ¿qué corral rectangular encierra más espacio: uno de 10 × 2, de 8 × 4 o de 6 × 6?')],
        aprende=[tabla([['Corral', 'Perímetro', 'Área'], ['10 × 2', '24 m', '20 m²'], ['8 × 4', '24 m', '32 m²'], ['6 × 6', '24 m', '36 m²']]),
                 texto('¡Mismo perímetro, diferente área! El cuadrado encierra más.'),
                 texto('Al revés: un rectángulo de 12 × 1 y uno de 4 × 3 tienen la misma área (12) pero perímetros distintos (26 y 14).'),
                 texto('Si un cuadrado tiene área 49 m², su lado mide <b>7 m</b> (porque 7 × 7 = 49).')],
        recuerda=['Mismo perímetro no significa misma área.', 'Lado del cuadrado: el número que multiplicado por sí mismo da el área.'],
        practica=[numerica('Un cuadrado tiene área 64 cm². ¿Cuánto mide su lado?', 8, 'cm'), numerica('Perímetro de un rectángulo de 12 × 1.', 26)],
        taller=[numerica('Área de un rectángulo de 9 × 4.', 36), numerica('Un rectángulo tiene área 30 y un lado de 5. ¿Cuánto mide el otro lado?', 6),
                unica('Con el mismo perímetro, ¿qué rectángulo tiene más área?', 'El más parecido a un cuadrado', ['El más largo y delgado']),
                vf('Si dos figuras tienen la misma área, tienen el mismo perímetro.', False),
                abierta('Dibuja 3 rectángulos de área 24 cm² y calcula el perímetro de cada uno.', 6)])

    U[6] = unidad(
        tema='Cuerpos y sus desarrollos planos',
        objetivo='Relacionar cuerpos geométricos con sus desarrollos planos y reconocer relaciones entre sus partes.',
        explora=[imagen('d-desarrollo', 28), texto('¿Qué cuerpo se arma con este desarrollo? ¿Qué cara queda opuesta a la de arriba?')],
        aprende=[texto('En un desarrollo plano cada figura es una <b>cara</b>. En la cruz del cubo, las caras opuestas no se tocan en el plano.'),
                 tabla([['Cuerpo', 'Caras', 'Aristas', 'Vértices'], ['Cubo', '6', '12', '8'], ['Prisma triangular', '5', '9', '6'], ['Pirámide cuadrada', '5', '8', '5']]),
                 texto('Relación de Euler en estos cuerpos: <b>caras + vértices − aristas = 2</b>. En el cubo: 6 + 8 − 12 = 2.'),
                 imagen('d-solidos-n', 65)],
        recuerda=['Caras + vértices − aristas = 2 (en los poliedros).'],
        practica=[numerica('Prisma triangular: 5 caras y 6 vértices. ¿Cuántas aristas tiene? (C + V − A = 2)', 9),
                  unica('El desarrollo de una pirámide cuadrada tiene…', '1 cuadrado y 4 triángulos', ['6 cuadrados', '2 círculos'])],
        taller=[numerica('Pirámide cuadrada: 5 caras y 8 aristas. ¿Cuántos vértices tiene?', 5),
                unica('¿Cuál de estos se arma con 2 triángulos y 3 rectángulos?', 'Prisma triangular', ['Cubo', 'Cilindro']),
                abierta('Construye en cartulina el desarrollo de un prisma triangular y ármalo.', 4)])

    plano = {'x': [-6, 6], 'y': [-5, 5], 'escala_igual': True, 'forma': 'cuadrada', 'elementos': [
        {'t': 'punto', 'x': 3, 'y': 2, 'nombre': 'Cofre'}, {'t': 'punto', 'x': -4, 'y': 1, 'nombre': 'Cueva', 'color': '#16a34a'},
        {'t': 'punto', 'x': -2, 'y': -3, 'nombre': 'Palmera', 'color': '#9333ea'}, {'t': 'punto', 'x': 0, 'y': 0, 'nombre': 'Muelle', 'color': '#dc2626'},
        {'t': 'texto', 'x': 4.6, 'y': 4.4, 'texto': 'N ↑'}]}
    U[7] = unidad(
        tema='El plano cartesiano y los mapas',
        objetivo='Localizar puntos con coordenadas, interpretar ejes y cuadrantes y describir trayectorias con puntos cardinales.',
        explora=[imagen('m5-mapa-tesoro', 35), texto('¿Cómo le dirías a alguien exactamente dónde está el cofre?')],
        aprende=[grafica(plano, 50, 'Mapa del tesoro en el plano cartesiano'),
                 texto('Cada punto tiene <b>coordenadas</b> (x, y): primero se cuenta en el eje horizontal y luego en el vertical. El cofre está en <b>(3, 2)</b>.'),
                 texto('Los ejes dividen el plano en <b>4 cuadrantes</b>. Si el norte está arriba: del muelle al cofre hay 3 al <b>oriente</b> y 2 al <b>norte</b>.')],
        recuerda=['Coordenadas: (x, y), primero horizontal y luego vertical.', 'Arriba: norte · derecha: oriente.'],
        practica=[unica('¿Dónde está la cueva?', '(−4, 1)', ['(1, −4)', '(4, 1)', '(−4, −1)']), unica('¿En qué cuadrante está el cofre?', 'I', ['II', 'III', 'IV'])],
        taller=[unica('¿Dónde está la palmera?', '(−2, −3)', ['(2, 3)', '(−3, −2)', '(2, −3)']),
                unica('Desde el muelle, la cueva está hacia el…', 'occidente y un poco al norte', ['oriente', 'sur']),
                unica('El punto (0, 0) se llama…', 'origen', ['cuadrante', 'eje']),
                abierta('Dibuja el plano de tu barrio o vereda en un plano cartesiano y escribe las coordenadas de 4 lugares.', 8)])

    lineal = {'x': [-0.5, 7], 'y': [-2, 40], 'nombre_x': 'horas', 'nombre_y': 'km', 'elementos': [
        {'t': 'funcion', 'expr': '5x', 'desde': '0', 'hasta': '7', 'nombre': 'ciclista'}] + [
        {'t': 'punto', 'x': h, 'y': 5 * h, 'nombre': ''} for h in range(0, 8)]}
    U[8] = unidad(
        tema='Cantidades que dependen de otras',
        objetivo='Describir variaciones de dependencia entre cantidades con tablas y gráficas, e interpretarlas.',
        explora=[texto('Un ciclista recorre 5 km cada hora. ¿Cuánto recorre en 3 horas? ¿Y en 7?')],
        aprende=[tabla([['Horas', '0', '1', '2', '3', '7'], ['Kilómetros', '0', '5', '10', '15', '35']]),
                 grafica(lineal, 55, 'La distancia depende del tiempo'),
                 texto('La distancia <b>depende</b> del tiempo: cada hora suma 5 km. La gráfica es una <b>línea recta</b> porque el cambio es siempre igual.')],
        recuerda=['Si el cambio es constante, la gráfica es una recta.'],
        practica=[numerica('¿Cuántos km recorre en 4 horas?', 20, 'km'), numerica('¿Cuántas horas tarda en recorrer 30 km?', 6, 'h')],
        taller=[numerica('Un tanque se llena con 8 litros por minuto. ¿Cuántos litros tiene a los 6 minutos?', 48, 'L'),
                numerica('¿Cuántos minutos tarda en tener 80 litros?', 10, 'min'),
                unica('Si la gráfica es una recta que sube, la cantidad…', 'aumenta siempre igual', ['disminuye', 'no cambia']),
                abierta('Inventa una situación donde una cantidad dependa de otra, haz la tabla y la gráfica.', 8)])

    U[9] = unidad(
        tema='Operaciones inventadas',
        objetivo='Operar con operaciones no convencionales, buscar sus propiedades y compararlas con las de la suma y la multiplicación.',
        explora=[texto('Inventamos la operación ★: a ★ b = 2 × a + b. ¿Cuánto es 3 ★ 4?')],
        aprende=[texto('3 ★ 4 = 2 × 3 + 4 = <b>10</b>. Y 4 ★ 3 = 2 × 4 + 3 = <b>11</b>. ¡No da lo mismo! La operación ★ <b>no es conmutativa</b>.'),
                 texto('La suma y la multiplicación sí son conmutativas: 3 + 4 = 4 + 3 y 3 × 4 = 4 × 3.'),
                 texto('Ecuación con ★: x ★ 5 = 17 → 2x + 5 = 17 → 2x = 12 → <b>x = 6</b>.')],
        recuerda=['Aplico la regla de la operación paso a paso.', 'Pruebo si cambiar el orden cambia el resultado.'],
        practica=[numerica('Con a ★ b = 2a + b, ¿cuánto es 5 ★ 1?', 11), numerica('Con a ◆ b = a × b − 1, ¿cuánto es 4 ◆ 3?', 11)],
        taller=[numerica('Con a ★ b = 2a + b, ¿cuánto es 1 ★ 5?', 7), unica('¿La operación ★ es conmutativa?', 'No', ['Sí']),
                numerica('Con a ★ b = 2a + b, resuelve x ★ 5 = 17.', 6),
                unica('¿La operación ◆ (a × b − 1) es conmutativa?', 'Sí', ['No']),
                abierta('Inventa tu propia operación, da 3 ejemplos y di si es conmutativa.', 6)])

    U[10] = unidad(
        tema='Comparo dos grupos con gráficos',
        objetivo='Formular preguntas que comparen dos grupos, recolectar y organizar datos y escoger el gráfico adecuado (barras, circular o de línea).',
        explora=[imagen('m5-encuesta', 35), texto('¿Los estudiantes de 5.º y de 3.º prefieren los mismos deportes? ¿Cómo lo averiguamos?')],
        aprende=[tabla([['Deporte', '5.º', '3.º'], ['Fútbol', '8', '12'], ['Baloncesto', '4', '6'], ['Voleibol', '2', '5'], ['Natación', '2', '7']]),
                 imagen('d-circular-futbol.8-baloncesto.4-voleibol.2-natacion.2', 50, 'Gráfico circular de 5.º (16 estudiantes)'),
                 tabla([['Gráfico', 'Sirve para'], ['Barras', 'comparar cantidades'], ['Circular', 'ver partes de un todo (porcentajes)'], ['Línea', 'ver cambios en el tiempo']]),
                 texto('En 5.º, la mitad prefiere fútbol (8 de 16). En 3.º, 12 de 30.')],
        recuerda=['Escojo el gráfico según lo que quiero mostrar.', 'Para comparar grupos de distinto tamaño, uso fracciones o porcentajes.'],
        practica=[numerica('¿Cuántos estudiantes de 5.º respondieron?', 16), unica('¿Qué parte de 5.º prefiere fútbol?', '1/2', ['1/4', '3/4', '1/8'])],
        taller=[numerica('¿Cuántos estudiantes de 3.º respondieron?', 30), unica('Para mostrar partes de un todo uso un gráfico…', 'circular', ['de línea']),
                unica('En 5.º, ¿qué parte prefiere baloncesto?', '1/4', ['1/2', '1/8']),
                abierta('Haz una encuesta en dos grados sobre su comida favorita y compara los resultados con un gráfico.', 8)])

    U[11] = unidad(
        tema='Media y mediana',
        objetivo='Calcular la media y la mediana de un conjunto de datos y decidir cuál lo representa mejor.',
        explora=[texto('Las notas de Sofi en 5 evaluaciones fueron 3, 4, 4, 5 y 9 (sobre 10). ¿Qué nota representa mejor su desempeño?')],
        aprende=[texto('<b>Media</b> (promedio): sumo todos y divido entre cuántos son. (3 + 4 + 4 + 5 + 9) ÷ 5 = 25 ÷ 5 = <b>5</b>.'),
                 texto('<b>Mediana</b>: ordeno los datos y tomo el del medio: 3, 4, <b>4</b>, 5, 9 → la mediana es <b>4</b>.'),
                 texto('Si hay un dato muy diferente (el 9), la media se «jala» hacia él; la mediana no. Aquí la mediana representa mejor a Sofi.'),
                 texto('Si hay un número par de datos, la mediana es el promedio de los dos del medio: 2, 4, 6, 8 → (4 + 6) ÷ 2 = 5.')],
        recuerda=['Media: sumo y divido. Mediana: ordeno y tomo el del medio.'],
        practica=[numerica('Media de 6, 8 y 10.', 8), numerica('Mediana de 7, 2, 9, 4, 5.', 5)],
        taller=[numerica('Media de 10, 20, 30 y 40.', 25), numerica('Mediana de 2, 4, 6 y 8.', 5),
                numerica('Mediana de 3, 4, 4, 5 y 9.', 4),
                unica('Si hay un dato muy grande, la medida que menos cambia es…', 'la mediana', ['la media']),
                abierta('Anota las estaturas de 7 compañeros y calcula la media y la mediana.', 6)])

    U[12] = unidad(
        tema='La probabilidad: casos favorables y posibles',
        objetivo='Enumerar los resultados posibles de un experimento aleatorio y predecir la posibilidad de un evento.',
        explora=[texto('En una bolsa hay 3 balotas rojas, 2 azules y 1 verde. Si saco una sin mirar, ¿qué color es más probable?')],
        aprende=[texto('El <b>espacio muestral</b> son todos los resultados posibles: 6 balotas.'),
                 texto('La probabilidad de un evento = <b>casos favorables ÷ casos posibles</b>. Roja: \\(\\frac{3}{6} = \\frac{1}{2}\\). Verde: \\(\\frac{1}{6}\\).'),
                 tabla([['Experimento', 'Espacio muestral'], ['Lanzar una moneda', 'cara, sello'], ['Lanzar un dado', '1, 2, 3, 4, 5, 6'],
                        ['Lanzar dos monedas', 'CC, CS, SC, SS']])],
        recuerda=['Probabilidad = favorables ÷ posibles.', 'Un evento imposible tiene probabilidad 0; uno seguro, 1.'],
        practica=[unica('Probabilidad de sacar azul en la bolsa (3R, 2A, 1V):', '1/3', ['1/2', '2/3', '1/6']),
                  unica('Probabilidad de sacar un número par con un dado:', '1/2', ['1/6', '1/3', '2/3'])],
        taller=[numerica('¿Cuántos resultados tiene el espacio muestral de lanzar dos monedas?', 4),
                unica('Probabilidad de sacar dos caras con dos monedas:', '1/4', ['1/2', '1/3', '3/4']),
                unica('Probabilidad de sacar un 7 con un dado:', '0', ['1/6', '1/7']),
                unica('Probabilidad de sacar un número menor que 7 con un dado:', '1', ['1/6', '1/2']),
                abierta('Lanza un dado 30 veces, anota los resultados y compara cuántas veces salió cada número.', 6)])
    return U
