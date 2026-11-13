"""Matemáticas 10.º: una guía y un taller por cada uno de los 10 DBA: números reales e intervalos, magnitudes relacionales,
funciones trigonométricas, lugares geométricos, razón de cambio, muestreo, medidas de tendencia y dispersión y
experimentos aleatorios. Borradores para que el docente revise."""
from fractions import Fraction as F

from .base import abierta, grafica, imagen, numerica, tabla, texto, unica, unidad, vf


def unidades():
    U = {}

    U[1] = unidad(
        tema='Los números reales y los irracionales',
        objetivo='Argumentar la existencia de los números irracionales, representarlos geométricamente y ubicarlos en la recta numérica.',
        explora=[texto('Un cuadrado mide 1 m de lado. ¿Cuánto mide su diagonal? ¿Puedes escribir ese número como una fracción?')],
        aprende=[texto('Por el teorema de Pitágoras, la diagonal mide d² = 1² + 1² = 2, es decir, <b>d = √2</b> ≈ 1,41421… Sus decimales no terminan ni se repiten: '
                       '√2 es <b>irracional</b>.'),
                 texto('<b>Por qué √2 no es una fracción</b>: si √2 = a/b simplificada, entonces a² = 2b², así que a es par (a = 2c). Entonces 4c² = 2b², b² = 2c² y b también es par. '
                       'Pero la fracción estaba simplificada: contradicción.'),
                 texto('Para ubicar √2 en la recta: dibuja un cuadrado de lado 1 sobre la recta, pon el compás en 0 con abertura igual a la diagonal y marca el corte.'),
                 grafica({'x': [-0.5, 2.5], 'y': [-0.5, 1.5], 'forma': 'ancha', 'elementos': [
                     {'t': 'poligono', 'puntos': [[0, 0], [1, 0], [1, 1], [0, 1]], 'relleno': True},
                     {'t': 'segmento', 'a': [0, 0], 'b': [1, 1], 'nombre': 'diagonal √2'},
                     {'t': 'funcion', 'expr': 'sqrt(2 - x^2)', 'desde': '1', 'hasta': '1.4142', 'estilo': 'guiones'},
                     {'t': 'punto', 'x': 1.4142, 'y': 0, 'nombre': '√2'}]}, 50, 'Construcción de √2 en la recta numérica'),
                 tabla([['Conjunto', 'Ejemplos'], ['Naturales ℕ', '0, 1, 2, 3…'], ['Enteros ℤ', '−3, 0, 5'], ['Racionales ℚ', '3/4; −0,5; 0,333…'],
                        ['Irracionales 𝕀', '√2, √3, π, e'], ['Reales ℝ', 'todos los anteriores']])],
        recuerda=['Racional: decimal finito o periódico.', 'Irracional: decimal infinito no periódico.', 'ℝ = ℚ ∪ 𝕀.'],
        practica=[unica('¿Cuál de estos números es irracional?', '√5', ['√9', '0,333…', '7/3']),
                  numerica('Diagonal de un cuadrado de lado 1 (con tres decimales).', F(1414, 1000), '', '0.001')],
        taller=[unica('0,121212… es un número…', 'racional', ['irracional']), unica('√16 es…', 'racional', ['irracional']),
                numerica('Un rectángulo mide 1 × 2. Su diagonal es √d. ¿Cuánto vale d?', 5),
                vf('Entre dos números racionales siempre hay un irracional.', True),
                abierta('Construye √2 y √3 en la recta numérica con regla y compás. Explica cada paso.', 6)])

    U[2] = unidad(
        tema='Orden en los reales e intervalos',
        objetivo='Comparar y ordenar números reales y describir subconjuntos con intervalos, usando las propiedades de la equivalencia y del orden.',
        explora=[texto('¿Qué es mayor: −√5, −2,2 o −9/4? Piensa antes de usar la calculadora.')],
        aprende=[texto('Paso a decimales: −√5 ≈ −2,236; −9/4 = −2,25; −2,2. En los negativos, el que está más lejos del cero es el <b>menor</b>: −2,25 &lt; −2,236 &lt; −2,2.'),
                 tabla([['Intervalo', 'Desigualdad', 'Extremos'], ['[a, b]', 'a ≤ x ≤ b', 'incluidos (cerrado)'], ['(a, b)', 'a &lt; x &lt; b', 'excluidos (abierto)'],
                        ['[a, b)', 'a ≤ x &lt; b', 'incluye a, excluye b'], ['(a, +∞)', 'x &gt; a', 'sin cota superior']]),
                 texto('<b>Efecto de las operaciones</b>: multiplicar un positivo por un número entre 0 y 1 lo <b>achica</b>; por un número mayor que 1 lo agranda; por un negativo '
                       'le cambia el signo e invierte el orden.')],
        recuerda=['Corchete: incluye el extremo. Paréntesis: lo excluye.', 'Multiplicar por negativo invierte la desigualdad.'],
        practica=[unica('¿Cuál es el menor?', '−9/4', ['−√5', '−2,2']), numerica('¿Cuántos números enteros hay en el intervalo [−2, 5)?', 7)],
        taller=[unica('El intervalo de −1 &lt; x ≤ 4 es…', '(−1, 4]', ['[−1, 4)', '[−1, 4]']), unica('Si 0 &lt; a &lt; 1, entonces a² es…', 'menor que a', ['mayor que a', 'igual a a']),
                unica('Ordena de menor a mayor: π, 22/7, 3,14', '3,14 &lt; π &lt; 22/7', ['π &lt; 3,14 &lt; 22/7', '22/7 &lt; π &lt; 3,14']),
                numerica('¿Cuántos enteros cumplen −3 &lt; x &lt; 3?', 5),
                abierta('Representa en la recta numérica los intervalos [−2, 3) y (1, 6]. ¿Qué intervalo es su intersección?', 4)])

    U[3] = unidad(
        tema='Velocidad media y aceleración media',
        objetivo='Resolver problemas con magnitudes relacionales (velocidad media, aceleración media) a partir de tablas, gráficas y expresiones algebraicas.',
        explora=[texto('Un ciclista recorre 30 km en la primera hora y 10 km en la segunda. ¿Cuál fue su velocidad media? ¿Fue siempre la misma?')],
        aprende=[texto('<b>Velocidad media</b> = Δx ÷ Δt (cambio de posición ÷ tiempo). Ciclista: 40 km ÷ 2 h = 20 km/h, aunque una hora fue más rápido.'),
                 texto('<b>Aceleración media</b> = Δv ÷ Δt. Un bus pasa de 10 m/s a 30 m/s en 5 s: a = 20 ÷ 5 = <b>4 m/s²</b>.'),
                 tabla([['t (s)', '0', '1', '2', '3', '4'], ['x (m)', '0', '5', '20', '45', '80']]),
                 grafica({'x': [0, 4.5], 'y': [0, 90], 'nombre_x': 't (s)', 'nombre_y': 'x (m)', 'elementos': [
                     {'t': 'funcion', 'expr': '5x^2', 'desde': '0', 'hasta': '4.2', 'nombre': 'x = 5t²'},
                     {'t': 'segmento', 'a': [2, 20], 'b': [4, 80], 'nombre': 'secante'},
                     {'t': 'punto', 'x': 2, 'y': 20}, {'t': 'punto', 'x': 4, 'y': 80}]}, 50, 'La pendiente de la secante es la velocidad media'),
                 texto('Entre t = 2 s y t = 4 s: v<sub>m</sub> = (80 − 20) ÷ (4 − 2) = <b>30 m/s</b>. Es la pendiente del segmento que une los dos puntos.')],
        recuerda=['v media = Δx/Δt (m/s).', 'a media = Δv/Δt (m/s²).'],
        practica=[numerica('Con la tabla, velocidad media entre t = 0 y t = 2 s.', 10, 'm/s'), numerica('Un carro va de 0 a 24 m/s en 6 s. Aceleración media.', 4, 'm/s²')],
        taller=[numerica('Con la tabla, velocidad media entre t = 1 y t = 3 s.', 20, 'm/s'), numerica('Una moto frena de 20 m/s a 0 en 4 s. ¿Aceleración media? (con signo)', -5, 'm/s²'),
                numerica('Un bus recorre 180 km en 2,5 h. Velocidad media.', 72, 'km/h'),
                unica('En una gráfica posición–tiempo, la velocidad media entre dos instantes es…', 'la pendiente de la secante', ['el área bajo la curva', 'el valor de x']),
                abierta('Mide con un cronómetro el tiempo que tardas en recorrer 10 m, 20 m y 30 m caminando y corriendo. Calcula las velocidades medias.', 5)])

    U[4] = unidad(
        tema='Funciones trigonométricas y fenómenos periódicos',
        objetivo='Usar las razones trigonométricas y las funciones seno y coseno para modelar fenómenos periódicos.',
        explora=[texto('La altura de una silla de la rueda de Chicago sube y baja una y otra vez. ¿Qué forma tendrá la gráfica de la altura contra el tiempo?')],
        aprende=[texto('En un triángulo rectángulo con ángulo agudo A: <b>sen A</b> = opuesto/hipotenusa, <b>cos A</b> = adyacente/hipotenusa, <b>tan A</b> = opuesto/adyacente. '
                       'En el triángulo 3-4-5, con el ángulo opuesto al lado 3: sen A = 3/5 = 0,6; cos A = 4/5 = 0,8; tan A = 3/4 = 0,75.'),
                 tabla([['Ángulo', '0°', '30°', '45°', '60°', '90°'], ['sen', '0', '1/2', '√2/2', '√3/2', '1'], ['cos', '1', '√3/2', '√2/2', '1/2', '0']]),
                 grafica({'x': [0, 6.6], 'y': [-1.5, 1.5], 'pi': True, 'elementos': [
                     {'t': 'funcion', 'expr': 'sen(x)', 'nombre': 'y = sen x'},
                     {'t': 'funcion', 'expr': 'cos(x)', 'nombre': 'y = cos x', 'estilo': 'guiones'}]}, 60, 'Seno y coseno: se repiten cada 2π'),
                 texto('<b>Periodo</b>: lo que tarda en repetirse (2π para sen x; π para sen 2x). <b>Amplitud</b>: la mitad de la distancia entre el máximo y el mínimo (3 para y = 3 sen x).'),
                 texto('Rueda: h(t) = 10 + 8 sen(t). La altura máxima es 10 + 8 = <b>18 m</b> y la mínima 10 − 8 = <b>2 m</b>.')],
        recuerda=['sen² A + cos² A = 1.', 'y = a·sen(bx): amplitud |a|, periodo 2π/b.'],
        practica=[numerica('En el triángulo 3-4-5, cos A (decimal).', F(4, 5)), numerica('Amplitud de y = 3 sen x.', 3)],
        taller=[numerica('sen 30° (decimal).', F(1, 2)), unica('El periodo de y = sen 2x es…', 'π', ['2π', '4π']),
                numerica('Altura mínima de la silla si h(t) = 12 + 9 sen(t).', 3, 'm'),
                numerica('Una escalera de 5 m forma 60° con el piso. ¿A qué distancia de la pared está su base? (cos 60° = 0,5)', F(5, 2), 'm'),
                abierta('Busca un fenómeno periódico (mareas, latidos, horas de luz). Dibuja su gráfica aproximada y señala periodo y amplitud.', 5)])

    U[5] = unidad(
        tema='Lugares geométricos en el plano cartesiano',
        objetivo='Describir circunferencias, parábolas y otros lugares geométricos con ecuaciones y transformarlos en el plano.',
        explora=[texto('Una cabra está amarrada a una estaca con una cuerda de 3 m. ¿Qué figura forma el borde del pasto que se puede comer?')],
        aprende=[texto('Un <b>lugar geométrico</b> es el conjunto de puntos que cumplen una condición. La <b>circunferencia</b> son los puntos a distancia r de un centro (h, k): '
                       '(x − h)² + (y − k)² = r².'),
                 texto('<b>Distancia</b> entre (x₁, y₁) y (x₂, y₂): d = √((x₂ − x₁)² + (y₂ − y₁)²). Entre (1, 2) y (4, 6): √(9 + 16) = <b>5</b>.'),
                 grafica({'x': [-4, 6], 'y': [-4, 6], 'forma': 'cuadrada', 'elementos': [
                     {'t': 'circulo', 'cx': 1, 'cy': 1, 'r': 3, 'nombre': 'circunferencia'},
                     {'t': 'punto', 'x': 1, 'y': 1, 'nombre': 'centro'},
                     {'t': 'funcion', 'expr': '(x-3)^2+1', 'desde': '0.8', 'hasta': '5.2', 'nombre': 'parábola', 'color': '#dc2626'}]}, 50,
                         'Circunferencia (x − 1)² + (y − 1)² = 9 y parábola y = (x − 3)² + 1'),
                 tabla([['Lugar geométrico', 'Condición'], ['Circunferencia', 'distancia fija a un centro'], ['Parábola', 'igual distancia a un foco y a una recta (directriz)'],
                        ['Elipse', 'suma de distancias a dos focos constante'], ['Mediatriz', 'igual distancia a dos puntos']]),
                 texto('<b>Traslación</b>: y = (x − 3)² + 1 es la parábola y = x² movida 3 a la derecha y 1 arriba; su vértice es (3, 1).')],
        recuerda=['(x − h)² + (y − k)² = r²: centro (h, k), radio r.'],
        practica=[numerica('Distancia entre (0, 0) y (6, 8).', 10), numerica('Radio de x² + y² = 25.', 5)],
        taller=[unica('El centro de (x − 2)² + (y + 3)² = 16 es…', '(2, −3)', ['(−2, 3)', '(2, 3)']), numerica('Radio de (x − 2)² + (y + 3)² = 16.', 4),
                unica('El vértice de y = (x + 1)² − 4 es…', '(−1, −4)', ['(1, −4)', '(−1, 4)']),
                vf('Los planetas giran en órbitas elípticas con el Sol en uno de los focos.', True),
                abierta('Dibuja una elipse con dos chinches, una cuerda y un lápiz. Explica por qué la figura es una elipse.', 5)])

    U[6] = unidad(
        tema='Razón de cambio: promedio y en un punto',
        objetivo='Calcular el cambio promedio y estimar el cambio alrededor de un punto en representaciones gráficas, numéricas y algebraicas.',
        explora=[texto('El número de usuarios de una aplicación pasó de 1 000 a 9 000 en 4 meses. ¿Cuántos usuarios ganó por mes, en promedio? ¿Crees que creció igual todos los meses?')],
        aprende=[texto('<b>Razón de cambio promedio</b> de f entre a y b: [f(b) − f(a)] ÷ (b − a). Para f(x) = x² entre 1 y 3: (9 − 1) ÷ 2 = <b>4</b>.'),
                 tabla([['Intervalo', 'Razón promedio de x²'], ['[2; 3]', '5'], ['[2; 2,1]', '4,1'], ['[2; 2,01]', '4,01'], ['[2; 2,001]', '4,001']]),
                 texto('Al acercar el intervalo al punto x = 2, la razón se acerca a <b>4</b>: es la <b>razón de cambio instantánea</b> en ese punto.'),
                 texto('Las tendencias numéricas sirven para predecir: si una ciudad crece 3 % al año y hoy tiene 100 000 habitantes, el próximo año tendrá 103 000.')],
        recuerda=['Promedio: en un intervalo. Instantánea: en un punto (el intervalo se hace muy pequeño).'],
        practica=[numerica('Razón de cambio promedio de los usuarios (por mes).', 2000), numerica('Razón promedio de f(x) = x² entre 0 y 4.', 4)],
        taller=[numerica('Razón promedio de f(x) = 3x + 2 entre 1 y 5.', 3), numerica('Razón promedio de f(x) = x² entre 3 y 3,1.', F(61, 10)),
                unica('¿A qué valor se acerca la razón de x² en x = 3?', '6', ['9', '3']),
                numerica('Una ciudad de 100 000 habitantes crece 3 % anual. ¿Cuántos tendrá en 2 años?', 106090),
                abierta('Registra la temperatura cada hora durante una mañana. ¿En qué hora fue mayor la razón de cambio?', 5)])

    U[7] = unidad(
        tema='Funciones, variación y pendiente de la tangente',
        objetivo='Usar propiedades de las funciones (lineal, cuadrática, exponencial) y la pendiente de la recta tangente para estudiar la variación.',
        explora=[texto('Una colonia de bacterias se duplica cada hora. Si hay 1 000 a las 8:00, ¿cuántas habrá a las 11:00?')],
        aprende=[tabla([['Función', 'Ejemplo', 'Cómo varía'], ['Lineal', 'f(x) = 2x + 1', 'cambio constante (pendiente 2)'], ['Cuadrática', 'f(x) = x²', 'baja y luego sube'],
                        ['Exponencial', 'f(t) = 1000·2ᵗ', 'se multiplica por 2 en cada paso']]),
                 texto('Bacterias: f(3) = 1 000 · 2³ = <b>8 000</b>.'),
                 texto('La <b>recta tangente</b> toca la curva en un punto y tiene su misma inclinación allí. Su pendiente es la razón de cambio instantánea. En y = x², en x = 1, la pendiente es 2 '
                       'y la tangente es y = 2x − 1.'),
                 grafica({'x': [-2, 3], 'y': [-2, 6], 'elementos': [
                     {'t': 'funcion', 'expr': 'x^2', 'nombre': 'y = x²'},
                     {'t': 'funcion', 'expr': '2x-1', 'nombre': 'tangente y = 2x − 1', 'color': '#dc2626'},
                     {'t': 'punto', 'x': 1, 'y': 1, 'nombre': '(1, 1)'}]}, 50, 'Recta tangente en x = 1')],
        recuerda=['Pendiente de la tangente = razón de cambio en el punto.', 'Exponencial: cambio en proporción.'],
        practica=[numerica('Bacterias a las 11:00.', 8000), numerica('Pendiente de f(x) = 2x + 1.', 2)],
        taller=[unica('Si la tangente tiene pendiente negativa, la función en ese punto…', 'decrece', ['crece', 'es constante']),
                numerica('¿En qué valor de x la tangente a y = x² es horizontal?', 0),
                numerica('Un celular de $1 200 000 pierde la mitad de su valor cada año. ¿Valor a los 3 años?', 150000, '$'),
                unica('¿Qué función describe un ahorro que aumenta $50 000 cada mes?', 'lineal', ['exponencial', 'cuadrática']),
                abierta('Dibuja y = x² y traza a ojo las tangentes en x = −1, 0, 1 y 2. Estima sus pendientes y busca un patrón.', 5)])

    U[8] = unidad(
        tema='Muestras aleatorias e inferencias',
        objetivo='Seleccionar muestras aleatorias en poblaciones grandes para inferir el comportamiento de una variable y valorar críticamente los estudios estadísticos.',
        explora=[texto('Una encuesta en redes dice que «el 90 % de los colombianos prefiere el café negro». ¿A quiénes crees que le preguntaron?')],
        aprende=[texto('La <b>población</b> es el grupo completo que se quiere estudiar; la <b>muestra</b> es una parte de ella. Para que la muestra represente a la población debe '
                       'elegirse al <b>azar</b> y tener un tamaño suficiente.'),
                 tabla([['Muestreo', 'Cómo se hace'], ['Aleatorio simple', 'todos tienen la misma probabilidad (sorteo)'], ['Sistemático', 'uno de cada k en una lista'],
                        ['Estratificado', 'se divide en grupos (estratos) y se toma de cada uno en proporción']]),
                 texto('Ejemplo: un colegio de 600 estudiantes (240 de primaria, 360 de bachillerato) quiere una muestra de 60 (el 10 %). Estratificado: 24 de primaria y 36 de bachillerato.'),
                 texto('<b>Sesgo</b>: si solo preguntan a quienes siguen una página, la muestra no representa al país.')],
        recuerda=['Muestra aleatoria y suficiente → inferencia confiable.', 'Pregunta siempre: ¿cómo eligieron la muestra?'],
        practica=[numerica('Muestra estratificada del 10 %: ¿cuántos de bachillerato?', 36), unica('Sortear nombres en una bolsa es muestreo…', 'aleatorio simple', ['estratificado'])],
        taller=[numerica('En una muestra de 200 personas, 50 usan bicicleta. Si la población es de 40 000, ¿cuántas se estima que la usan?', 10000),
                unica('Preguntar solo a los que salen de un gimnasio sobre el ejercicio produce…', 'una muestra sesgada', ['una muestra aleatoria']),
                numerica('Muestreo sistemático: lista de 1 000 personas, muestra de 50. ¿Cada cuántas se elige una?', 20),
                abierta('Diseña una encuesta para conocer el tiempo de pantalla de los estudiantes del colegio: población, tamaño y método de muestreo.', 8)])

    U[9] = unidad(
        tema='Medidas de tendencia central y de dispersión',
        objetivo='Calcular e interpretar medidas de tendencia central y de dispersión, y complementarlas para leer mejor los datos.',
        explora=[texto('Dos grupos tienen promedio 5 en un examen. ¿Significa que les fue igual? Grupo A: 5, 5, 5, 5, 5. Grupo B: 1, 3, 5, 7, 9.')],
        aprende=[texto('<b>Media</b>: suma ÷ cantidad. <b>Mediana</b>: el dato central ordenado. <b>Moda</b>: el más frecuente.'),
                 texto('<b>Rango</b>: máximo − mínimo. <b>Varianza</b>: promedio de los cuadrados de las desviaciones a la media. <b>Desviación estándar</b>: raíz de la varianza.'),
                 tabla([['Grupo B', '1', '3', '5', '7', '9'], ['x − media', '−4', '−2', '0', '2', '4'], ['(x − media)²', '16', '4', '0', '4', '16']]),
                 texto('Varianza de B = 40 ÷ 5 = 8; desviación ≈ 2,83. En A la desviación es 0: misma media, distinta dispersión.'),
                 imagen('d-caja-1-2-5-8-9-0-10-1', 55, 'Grupo B: mínimo 1, Q1 = 2, mediana 5, Q3 = 8, máximo 9'),
                 texto('Un dato atípico mueve mucho la media y poco la mediana: 2, 3, 3, 7, 10 → media 5, mediana 3.')],
        recuerda=['Una medida central sola no basta: compleméntala con una de dispersión.'],
        practica=[numerica('Rango del grupo B.', 8), numerica('Varianza del grupo B.', 8)],
        taller=[numerica('Mediana de 4, 8, 6, 2, 10.', 6), numerica('Media de 2, 3, 3, 7, 10.', 5),
                unica('Los salarios de una empresa incluyen el del gerente, muy alto. ¿Qué medida representa mejor al trabajador típico?', 'la mediana', ['la media']),
                numerica('Desviación estándar de 2, 4, 6 (varianza poblacional; escribe con dos decimales).', F(163, 100), '', '0.01'),
                abierta('Recoge las estaturas de 10 compañeros. Calcula media, mediana, rango y desviación estándar, e interpreta.', 6)])

    U[10] = unidad(
        tema='Experimentos aleatorios y frecuencia relativa',
        objetivo='Proponer y realizar experimentos aleatorios para estimar probabilidades cuando el espacio muestral no es equiprobable o se desconoce.',
        explora=[texto('Al lanzar una tapa de gaseosa, ¿es igual de probable que caiga boca arriba o boca abajo? ¿Cómo lo averiguarías?')],
        aprende=[texto('Cuando no podemos contar casos igualmente probables, <b>experimentamos</b>: la <b>frecuencia relativa</b> = veces que ocurre ÷ total de ensayos.'),
                 tabla([['Lanzamientos', '10', '50', '100', '300'], ['Boca arriba', '6', '22', '41', '120'], ['Frecuencia relativa', '0,6', '0,44', '0,41', '0,40']]),
                 texto('<b>Ley de los grandes números</b>: con muchos ensayos la frecuencia relativa se estabiliza; aquí, cerca de 0,40. Esa es nuestra estimación de la probabilidad.'),
                 texto('Pasos: 1) pregunta, 2) variable y población, 3) diseño (cuántos ensayos, en qué condiciones), 4) registro, 5) conclusión y predicción.')],
        recuerda=['Más ensayos → estimación más confiable.'],
        practica=[numerica('Con la tabla, frecuencia relativa con 300 lanzamientos.', F(2, 5)), numerica('¿Cuántas veces boca arriba esperas en 1 000 lanzamientos?', 400)],
        taller=[unica('¿Qué estimación es más confiable?', 'la de 300 lanzamientos', ['la de 10 lanzamientos']),
                numerica('En 500 semillas sembradas germinaron 425. Frecuencia relativa de germinación.', F(17, 20)),
                numerica('Con esa frecuencia, ¿cuántas germinarán de 2 000?', 1700),
                abierta('Diseña y realiza un experimento con una chinche o una tapa (al menos 100 lanzamientos). Presenta la tabla y tu estimación.', 8)])
    return U
