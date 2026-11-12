"""Matemáticas 8.º: una guía y un taller por cada uno de los 12 DBA (V.2): irracionales, álgebra, ecuaciones y sistemas,
volumen, semejanza, Pitágoras, funciones lineales, datos agrupados y probabilidad. Borradores para que el docente revise."""
from fractions import Fraction as F

from .base import abierta, grafica, imagen, numerica, tabla, texto, unica, unidad, vf


def unidades():
    U = {}

    U[1] = unidad(
        tema='Los números irracionales',
        objetivo='Reconocer los números irracionales por su expansión decimal infinita no periódica y distinguirlos de los racionales.',
        explora=[texto('Un cuadrado tiene lado 1. ¿Cuánto mide su diagonal? Mídela con una regla en un cuadrado de 10 cm: ¿te da un número «exacto»?')],
        aprende=[texto('Por Pitágoras, la diagonal mide \\(\\sqrt{1^2 + 1^2} = \\sqrt{2} = 1{,}41421356…\\) Sus decimales <b>no terminan ni se repiten</b>: es <b>irracional</b>.'),
                 tabla([['Número', 'Expansión decimal', 'Tipo'], ['3/4', '0,75 (termina)', 'racional'], ['1/3', '0,333… (se repite)', 'racional'],
                        ['√2', '1,41421356… (ni termina ni se repite)', 'irracional'], ['π', '3,14159265…', 'irracional'], ['√9', '3', 'racional']]),
                 texto('Los <b>racionales</b> se pueden escribir como fracción a/b. Los <b>irracionales</b> no. Juntos forman los <b>números reales</b>.')],
        recuerda=['Decimal finito o periódico → racional.', 'Decimal infinito no periódico → irracional.'],
        practica=[unica('¿Cuál es irracional?', '√5', ['√16', '0,25', '2/3']), unica('0,121212… es…', 'racional', ['irracional'])],
        taller=[unica('¿Cuál es racional?', '√49', ['√7', 'π', '√3']), vf('π se puede escribir exactamente como 22/7.', False),
                unica('Los números reales son…', 'los racionales y los irracionales juntos', ['solo los enteros']),
                numerica('¿Entre qué entero y el siguiente está √20? Escribe el menor.', 4),
                abierta('Explica con tus palabras por qué √2 no se puede escribir como fracción (puedes buscar la demostración).', 6)])

    U[2] = unidad(
        tema='Construyo y ubico irracionales en la recta',
        objetivo='Construir geométricamente números irracionales y ubicarlos en la recta numérica.',
        explora=[texto('¿Cómo pondrías √2 en la recta numérica con regla y compás, sin calculadora?')],
        aprende=[texto('Dibujo un cuadrado de lado 1 sobre la recta, con un vértice en 0. Con el compás en 0 y abertura igual a la diagonal, trazo un arco hasta la recta: '
                       'el corte es <b>√2</b>.'),
                 grafica({'x': [-0.5, 2.5], 'y': [-0.3, 1.5], 'escala_igual': True, 'forma': 'ancha', 'elementos': [
                     {'t': 'poligono', 'puntos': [[0, 0], [1, 0], [1, 1], [0, 1]], 'relleno': False, 'nombre': ''},
                     {'t': 'segmento', 'a': [0, 0], 'b': [1, 1], 'nombre': '√2'},
                     {'t': 'funcion', 'expr': 'sqrt(2 - x^2)', 'desde': '1', 'hasta': '1.4142', 'nombre': '', 'estilo': 'guiones'},
                     {'t': 'punto', 'x': 1.4142, 'y': 0, 'nombre': '√2'}]}, 45, 'La diagonal del cuadrado de lado 1 llevada a la recta'),
                 texto('Con el mismo método: un rectángulo de 1 × 2 tiene diagonal <b>√5</b>; luego con lados 1 y √2 sale <b>√3</b> (espiral de Teodoro).')],
        recuerda=['La hipotenusa de un triángulo rectángulo de catetos 1 y 1 mide √2.'],
        practica=[unica('La diagonal de un rectángulo de 1 × 2 mide…', '√5', ['√3', '3', '√2']), unica('√2 está entre…', '1 y 2', ['2 y 3', '0 y 1'])],
        taller=[unica('Con catetos 1 y √2, la hipotenusa mide…', '√3', ['√2', '2', '3']),
                unica('¿Cuál está más cerca de 0?', '√2', ['√3', '√5']), numerica('Aproxima √2 a dos decimales.', F(141, 100)),
                abierta('Construye con regla y compás √2, √3 y √5 en tu cuaderno.', 6)])

    U[3] = unidad(
        tema='El signo igual, ecuaciones lineales y sistemas',
        objetivo='Usar el signo igual como equivalencia, resolver ecuaciones lineales y sistemas de dos ecuaciones y justificar los procedimientos.',
        explora=[texto('Dos entradas a cine y tres crispetas cuestan $36 000; una entrada y una crispeta, $14 000. ¿Cuánto cuesta cada cosa?')],
        aprende=[texto('Planteo: <b>2e + 3c = 36 000</b> y <b>e + c = 14 000</b>. De la segunda, e = 14 000 − c.'),
                 texto('Sustituyo: 2(14 000 − c) + 3c = 36 000 → 28 000 + c = 36 000 → <b>c = 8 000</b>, y e = <b>6 000</b>.'),
                 texto('Ecuación lineal: 3(x − 2) = 2x + 5 → 3x − 6 = 2x + 5 → <b>x = 11</b>. Lo que hago a un lado lo hago al otro: así se conserva la igualdad.'),
                 texto('«=» puede ser <b>equivalencia</b> (2(x + 3) = 2x + 6 vale para todo x) o <b>igualdad condicionada</b> (2x + 1 = 7 solo vale para x = 3).')],
        recuerda=['Sustitución: despejo una variable y la reemplazo en la otra ecuación.', 'Compruebo la solución en las dos ecuaciones.'],
        practica=[numerica('Resuelve 3(x − 2) = 2x + 5.', 11), numerica('Si x + y = 10 y x − y = 4, ¿cuánto vale x?', 7)],
        taller=[numerica('Resuelve 5x − 3 = 2x + 9.', 4), numerica('Si x + y = 10 y x − y = 4, ¿cuánto vale y?', 3),
                numerica('2x + y = 11 y x + y = 7. ¿Cuánto vale x?', 4),
                unica('2(x + 3) = 2x + 6 es…', 'una equivalencia (vale para todo x)', ['una ecuación con una sola solución']),
                abierta('Inventa un problema de la tienda que se resuelva con un sistema de dos ecuaciones.', 6)])

    U[4] = unidad(
        tema='Volumen del prisma con lenguaje algebraico',
        objetivo='Expresar el área y el volumen de prismas con expresiones algebraicas y representar su desarrollo plano.',
        explora=[imagen('d-desarrollo', 25), texto('Si la arista del cubo mide a, ¿cuánto mide su área total? ¿Y su volumen?')],
        aprende=[texto('Cubo de arista <b>a</b>: área total = 6a², volumen = a³.'),
                 texto('Prisma rectangular de aristas <b>a, b, c</b>: volumen = a · b · c; área total = 2(ab + bc + ac).'),
                 texto('Si duplico todas las aristas del cubo, el área se multiplica por 4 y el volumen por 8: (2a)³ = 8a³.')],
        recuerda=['V = área de la base × altura.', 'Duplicar las aristas multiplica el volumen por 8.'],
        practica=[numerica('Volumen de un cubo de arista 5 cm.', 125, 'cm³'), numerica('Área total de un cubo de arista 5 cm.', 150, 'cm²')],
        taller=[numerica('Volumen de un prisma de 4 × 3 × 10 cm.', 120, 'cm³'), numerica('Área total del prisma de 4 × 3 × 10 cm.', 2 * (12 + 30 + 40), 'cm²'),
                unica('Si triplico la arista de un cubo, su volumen se multiplica por…', '27', ['3', '9', '6']),
                abierta('Escribe la expresión del volumen de una caja de largo x, ancho x − 2 y alto 3.', 3)])

    U[5] = unidad(
        tema='Volumen de objetos regulares e irregulares',
        objetivo='Usar estrategias para hallar volúmenes de objetos regulares e irregulares y relacionar unidades de volumen y capacidad.',
        explora=[texto('¿Cómo medirías el volumen de una piedra, que no tiene forma de caja?')],
        aprende=[texto('<b>Desplazamiento de agua</b>: pongo agua en una probeta (300 mL), sumerjo la piedra y sube a 420 mL. La piedra tiene <b>120 mL = 120 cm³</b>.'),
                 tabla([['Volumen', 'Capacidad'], ['1 cm³', '1 mL'], ['1 dm³', '1 L'], ['1 m³', '1 000 L']]),
                 texto('Un tanque de 2 m × 1 m × 1,5 m tiene 3 m³ = <b>3 000 litros</b>.')],
        recuerda=['1 dm³ = 1 litro.', 'Objetos irregulares: método de desplazamiento de agua.'],
        practica=[numerica('El agua sube de 300 mL a 420 mL al meter una piedra. ¿Cuál es su volumen en cm³?', 120, 'cm³'),
                  numerica('¿Cuántos litros caben en 3 m³?', 3000, 'L')],
        taller=[numerica('¿Cuántos litros son 2,5 dm³?', F(5, 2), 'L'), numerica('Tanque de 2 × 1 × 1,5 m: ¿cuántos litros?', 3000, 'L'),
                unica('¿Qué método sirve para el volumen de una llave?', 'Sumergirla en agua y medir cuánto sube', ['Medir sus lados']),
                abierta('Mide en casa el volumen de un objeto irregular con un recipiente graduado. Describe el procedimiento.', 6)])

    U[6] = unidad(
        tema='Congruencia y semejanza de triángulos',
        objetivo='Argumentar la congruencia de triángulos con sus criterios y reconocer triángulos semejantes en situaciones reales.',
        explora=[texto('A las 9 a. m. un palo de 1 m hace una sombra de 1,5 m y un árbol una de 6 m. ¿Cuánto mide el árbol?')],
        aprende=[texto('<b>Congruentes</b>: misma forma y tamaño. Criterios: <b>LLL</b> (tres lados), <b>LAL</b> (dos lados y el ángulo entre ellos), <b>ALA</b>.'),
                 texto('<b>Semejantes</b>: misma forma, lados proporcionales. Criterio AA: dos ángulos iguales.'),
                 texto('Palo y árbol forman triángulos semejantes: altura/sombra = 1/1,5. Árbol = 6 × (1/1,5) = <b>4 m</b>.')],
        recuerda=['Congruente: igual forma y tamaño. Semejante: igual forma, tamaño proporcional.'],
        practica=[numerica('¿Cuánto mide el árbol?', 4, 'm'), unica('Dos triángulos con lados 3-4-5 y 6-8-10 son…', 'semejantes', ['congruentes', 'ninguno'])],
        taller=[unica('Si dos triángulos tienen sus tres lados iguales, son congruentes por…', 'LLL', ['AA', 'LAL']),
                numerica('Triángulos semejantes: lados 2 y 5 en uno; el lado de 2 corresponde a 6 en el otro. ¿Cuánto mide el que corresponde a 5?', 15),
                vf('Dos triángulos semejantes siempre tienen el mismo tamaño.', False),
                abierta('Mide la sombra de un compañero y la de un poste a la misma hora y calcula la altura del poste.', 6)])

    U[7] = unidad(
        tema='El teorema de Pitágoras',
        objetivo='Comprobar el teorema de Pitágoras con material concreto y aplicarlo en situaciones reales.',
        explora=[imagen('d-pitagoras-3-4', 35, '9 + 16 = 25'), texto('Cuenta los cuadritos de cada cuadrado. ¿Qué relación encuentras?')],
        aprende=[texto('En todo triángulo <b>rectángulo</b>: \\(a^2 + b^2 = c^2\\), donde c es la <b>hipotenusa</b> (el lado opuesto al ángulo recto).'),
                 texto('Catetos 3 y 4: 9 + 16 = 25 → c = <b>5</b>.'),
                 texto('Una escalera de 5 m apoyada a 3 m de la pared alcanza una altura de \\(\\sqrt{25 - 9} = 4\\) m.')],
        recuerda=['Solo vale en triángulos rectángulos.', 'c² = a² + b²; a² = c² − b².'],
        practica=[numerica('Catetos 6 y 8. ¿Cuánto mide la hipotenusa?', 10), numerica('Hipotenusa 13 y un cateto 5. ¿Cuánto mide el otro?', 12)],
        taller=[numerica('Diagonal de una cancha de 9 m × 12 m.', 15, 'm'), numerica('Escalera de 10 m a 6 m de la pared. ¿A qué altura llega?', 8, 'm'),
                unica('¿Cuál terna es pitagórica?', '5, 12, 13', ['4, 5, 6', '2, 3, 4']),
                abierta('Arma con papel cuadriculado los tres cuadrados de un triángulo 3-4-5 y comprueba el teorema recortando.', 6)])

    U[8] = unidad(
        tema='Expresiones algebraicas y sus gráficas',
        objetivo='Relacionar expresiones algebraicas con sus gráficas e interpretar cómo cambia la variable dependiente al cambiar la independiente.',
        explora=[texto('Un taxi cobra $4 000 de arranque y $1 000 por kilómetro. ¿Cuánto cuesta un viaje de 6 km?')],
        aprende=[texto('Costo = 1 000·x + 4 000. Para x = 6: <b>$10 000</b>. La <b>pendiente</b> (1 000) es cuánto sube el costo por kilómetro; el <b>intercepto</b> (4 000), el arranque.'),
                 grafica({'x': [-1, 10], 'y': [-1000, 15000], 'nombre_x': 'km', 'nombre_y': '$', 'elementos': [
                     {'t': 'funcion', 'expr': '1000x+4000', 'desde': '0', 'hasta': '10', 'nombre': 'taxi'}]}, 50, 'y = 1000x + 4000'),
                 texto('Si la pendiente es mayor, la recta sube más rápido. Si es negativa, baja.')],
        recuerda=['y = mx + b: m es la pendiente y b el intercepto con el eje y.'],
        practica=[numerica('¿Cuánto cuesta un viaje de 10 km?', 14000, 'pesos'), numerica('¿Cuál es la pendiente de y = 3x − 2?', 3)],
        taller=[numerica('¿Dónde corta y = 3x − 2 el eje y?', -2), unica('La recta y = −2x + 5…', 'baja', ['sube', 'es horizontal']),
                numerica('Con y = 1000x + 4000, ¿cuántos km recorrí si pagué $9 000?', 5, 'km'),
                abierta('Inventa una situación con la forma y = mx + b, haz la tabla y la gráfica.', 6)])

    U[9] = unidad(
        tema='Patrones y conjeturas con lenguaje algebraico',
        objetivo='Describir patrones con expresiones algebraicas, formular conjeturas y ponerlas a prueba.',
        explora=[texto('Suma dos números impares consecutivos: 3 + 5, 7 + 9, 11 + 13. ¿Qué observas?')],
        aprende=[texto('Conjetura: la suma de dos impares consecutivos es múltiplo de 4. Con álgebra: (2n + 1) + (2n + 3) = 4n + 4 = <b>4(n + 1)</b>. ¡Se cumple siempre!'),
                 tabla([['Figura', '1', '2', '3', 'n'], ['Puntos', '1', '4', '9', 'n²']]),
                 texto('Los números cuadrados siguen la regla n². La diferencia entre dos cuadrados consecutivos es (n + 1)² − n² = 2n + 1.')],
        recuerda=['Pruebo varios casos, conjeturo y demuestro con álgebra.'],
        practica=[numerica('¿Cuántos puntos tiene la figura 7 (n²)?', 49), numerica('Diferencia entre 8² y 7².', 15)],
        taller=[unica('La suma de dos pares consecutivos 2n + (2n + 2) es…', '4n + 2', ['4n', '2n + 2']),
                numerica('Si una secuencia es 3n + 2, ¿cuál es el término 20?', 62), numerica('Resuelve 3n + 2 = 50.', 16),
                abierta('Propón una conjetura sobre la suma de tres números consecutivos y demuéstrala.', 6)])

    U[10] = unidad(
        tema='Modelos funcionales: lineales y no lineales',
        objetivo='Proponer modelos funcionales entre variables, analizar su covariación y representarlos en gráficas.',
        explora=[texto('El área de un cuadrado depende de su lado; el perímetro, también. ¿Cambian de la misma forma?')],
        aprende=[grafica({'x': [0, 6], 'y': [0, 36], 'nombre_x': 'lado', 'nombre_y': '', 'elementos': [
                     {'t': 'funcion', 'expr': '4x', 'desde': '0', 'hasta': '6', 'nombre': 'perímetro'},
                     {'t': 'funcion', 'expr': 'x^2', 'desde': '0', 'hasta': '6', 'nombre': 'área', 'color': '#dc2626'}]}, 50, 'Perímetro (lineal) y área (cuadrática)'),
                 texto('El perímetro P = 4l es <b>lineal</b>: crece siempre igual. El área A = l² es <b>cuadrática</b>: crece cada vez más rápido.'),
                 texto('Un modelo <b>inverso</b>: repartir 24 dulces entre n niños → d = 24/n (si hay más niños, a cada uno le toca menos).')],
        recuerda=['Lineal: recta. Cuadrático: parábola. Inverso: curva que baja.'],
        practica=[numerica('Con A = l², ¿cuánto vale A si l = 6?', 36), numerica('Con d = 24/n, ¿cuántos dulces le tocan a cada uno si n = 8?', 3)],
        taller=[unica('d = 24/n es una relación…', 'inversa', ['lineal', 'cuadrática']), unica('P = 4l es…', 'lineal', ['cuadrática']),
                numerica('¿Para qué lado el área y el perímetro de un cuadrado son iguales (l² = 4l, l ≠ 0)?', 4),
                abierta('Busca una situación de la vida real que siga un modelo inverso y descríbela con una tabla.', 6)])

    U[11] = unidad(
        tema='Datos agrupados en intervalos',
        objetivo='Interpretar tablas y gráficos con datos agrupados y escoger la medida de tendencia central más representativa.',
        explora=[texto('Se midió el tiempo (en minutos) que 30 estudiantes tardan en llegar al colegio. ¿Cómo los organizamos?')],
        aprende=[tabla([['Minutos', 'Marca de clase', 'Frecuencia'], ['[0, 10)', '5', '6'], ['[10, 20)', '15', '12'], ['[20, 30)', '25', '8'], ['[30, 40)', '35', '4']]),
                 grafica({'x': [-2, 45], 'y': [0, 14], 'nombre_x': 'min', 'nombre_y': 'estudiantes', 'elementos': [
                     {'t': 'poligono', 'puntos': [[a, 0], [a + 10, 0], [a + 10, f], [a, f]], 'relleno': True, 'nombre': ''}
                     for a, f in ((0, 6), (10, 12), (20, 8), (30, 4))]}, 50, 'Histograma'),
                 texto('Media aproximada = (5·6 + 15·12 + 25·8 + 35·4) ÷ 30 = 550 ÷ 30 ≈ <b>18,3 min</b>. Intervalo modal: <b>[10, 20)</b>. La mediana está en [10, 20).'),
                 texto('Si hay datos extremos, la <b>mediana</b> representa mejor que la media.')],
        recuerda=['Marca de clase = punto medio del intervalo.', 'Media agrupada: Σ(marca × frecuencia) ÷ total.'],
        practica=[numerica('¿Cuál es la marca de clase de [20, 30)?', 25), unica('¿Cuál es el intervalo modal?', '[10, 20)', ['[0, 10)', '[20, 30)'])],
        taller=[numerica('¿Cuántos estudiantes tardan 20 minutos o más?', 12), numerica('¿Cuántos estudiantes se encuestaron?', 30),
                numerica('Media aproximada (redondea a un decimal).', F(183, 10), tolerancia='0,1'),
                abierta('Recolecta las estaturas de tu curso, agrúpalas en intervalos y haz el histograma.', 8)])

    U[12] = unidad(
        tema='Probabilidad de eventos compuestos',
        objetivo='Enumerar el espacio muestral de experimentos compuestos y calcular probabilidades usando sus propiedades básicas.',
        explora=[texto('Lanzas dos dados. ¿Es más probable que sumen 7 o que sumen 12?')],
        aprende=[texto('El espacio muestral tiene 6 × 6 = <b>36</b> resultados. Suman 7: (1,6), (2,5), (3,4), (4,3), (5,2), (6,1) → 6 casos. P(7) = 6/36 = <b>1/6</b>. '
                       'Suman 12: solo (6,6) → P(12) = 1/36.'),
                 texto('Propiedades: 0 ≤ P(A) ≤ 1; P(no A) = 1 − P(A). P(no sumar 7) = 1 − 1/6 = 5/6.'),
                 texto('Diagrama de árbol para dos monedas: CC, CS, SC, SS → P(al menos una cara) = 3/4.')],
        recuerda=['P = favorables ÷ posibles.', 'P(no A) = 1 − P(A).'],
        practica=[unica('P(sumar 7 con dos dados)', '1/6', ['1/12', '7/36', '1/36']), unica('P(al menos una cara con dos monedas)', '3/4', ['1/2', '1/4'])],
        taller=[numerica('¿Cuántos resultados hay al lanzar tres monedas?', 8), unica('P(sumar 2 con dos dados)', '1/36', ['1/6', '2/36']),
                unica('P(no sacar 6 con un dado)', '5/6', ['1/6', '1/2']),
                abierta('Lanza dos dados 50 veces, registra las sumas y compara la frecuencia del 7 con la probabilidad teórica.', 6)])
    return U
