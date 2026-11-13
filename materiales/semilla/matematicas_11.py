"""Matemáticas 11.º: una guía y un taller por cada uno de los 10 DBA: sistemas numéricos, inecuaciones, magnitudes y precisión,
derivada como razón de cambio y sus reglas, sistemas de coordenadas, modelos funcionales, correlación y probabilidad
condicional. Borradores para que el docente revise."""
from fractions import Fraction as F

from .base import abierta, grafica, numerica, tabla, texto, unica, unidad, vf


def unidades():
    U = {}

    U[1] = unidad(
        tema='Los sistemas numéricos: de ℕ a ℝ',
        objetivo='Comparar los sistemas numéricos por sus propiedades y operaciones, y usar la densidad para justificar nuevas notaciones.',
        explora=[texto('¿Por qué los naturales no bastan para restar 3 − 5? ¿Y los enteros para repartir 7 entre 2? ¿Qué número le sigue a 1/2?')],
        aprende=[tabla([['Sistema', 'Operación que se puede hacer siempre', 'Lo que falta'], ['ℕ', 'suma, multiplicación', 'restar 3 − 5'],
                        ['ℤ', '+, −, ×', 'dividir 7 ÷ 2'], ['ℚ', '+, −, ×, ÷ (no entre 0)', 'medir la diagonal √2'], ['ℝ', 'todas, y es completo (sin huecos)', '—']]),
                 texto('ℕ ⊂ ℤ ⊂ ℚ ⊂ ℝ. Cada ampliación conserva propiedades (conmutativa, asociativa, distributiva) y gana otras: en ℤ cada número tiene opuesto; en ℚ cada número no nulo tiene inverso.'),
                 texto('<b>Densidad</b>: entre dos racionales siempre hay otro (su promedio): entre 1/3 y 1/2 está 5/12. Por eso no hay «siguiente» de 1/2, y para describir '
                       'todos los números entre dos valores usamos <b>intervalos</b>: (1/3, 1/2).')],
        recuerda=['ℕ ⊂ ℤ ⊂ ℚ ⊂ ℝ.', 'ℤ es discreto; ℚ y ℝ son densos.'],
        practica=[unica('¿En cuál sistema 7 ÷ 2 tiene resultado?', 'ℚ', ['ℕ', 'ℤ']), numerica('Promedio de 1/3 y 1/2 (como fracción decimal con tres cifras).', F(5, 12), '', '0.001')],
        taller=[unica('¿Qué propiedad tiene ℤ que no tiene ℕ?', 'cada número tiene opuesto', ['cada número tiene inverso', 'es denso']),
                vf('Entre 0,1 y 0,2 hay infinitos números.', True), vf('Los enteros son densos.', False),
                unica('El inverso multiplicativo de −3/4 es…', '−4/3', ['3/4', '4/3']),
                abierta('Explica con ejemplos por qué la humanidad necesitó inventar los números negativos, las fracciones y los irracionales.', 6)])

    U[2] = unidad(
        tema='Inecuaciones y propiedades del orden',
        objetivo='Justificar las propiedades del orden de los reales y usarlas para resolver inecuaciones que modelan problemas.',
        explora=[texto('Una empresa gana G(x) = −x² + 10x − 16 millones al producir x miles de unidades. ¿Para qué producción no pierde dinero?')],
        aprende=[texto('Propiedades: si a &lt; b, entonces a + c &lt; b + c; si c &gt; 0, ac &lt; bc; si c &lt; 0, <b>ac &gt; bc</b> (se invierte).'),
                 texto('<b>Signo de un producto</b>: (x − 2)(x − 8) ≤ 0 cuando los factores tienen signos contrarios (o uno es 0): <b>2 ≤ x ≤ 8</b>. Como G(x) = −(x − 2)(x − 8), '
                       'la empresa no pierde si produce entre 2 000 y 8 000 unidades.'),
                 tabla([['', 'x &lt; 2', '2 &lt; x &lt; 8', 'x &gt; 8'], ['x − 2', '−', '+', '+'], ['x − 8', '−', '−', '+'], ['producto', '+', '−', '+']]),
                 grafica({'x': [0, 10], 'y': [-8, 10], 'elementos': [
                     {'t': 'funcion', 'expr': '-x^2+10x-16', 'nombre': 'G(x)'},
                     {'t': 'area', 'expr': '-x^2+10x-16', 'desde': '2', 'hasta': '8', 'nombre': 'G ≥ 0'}]}, 50, 'Zona de ganancia'),
                 texto('<b>Valor absoluto</b>: |x − 1| ≤ 3 significa que x está a 3 o menos de 1: −2 ≤ x ≤ 4.')],
        recuerda=['Tabla de signos para productos y cocientes.', '|x − a| ≤ r ⇔ a − r ≤ x ≤ a + r.'],
        practica=[numerica('¿Cuántos enteros cumplen (x − 2)(x + 3) &lt; 0?', 4), unica('|x − 1| ≤ 3 equivale a…', '−2 ≤ x ≤ 4', ['x ≤ 4', '−4 ≤ x ≤ 2'])],
        taller=[unica('x² − 9 &gt; 0 cuando…', 'x &lt; −3 o x &gt; 3', ['−3 &lt; x &lt; 3', 'x &gt; 9']), unica('Si −3x ≥ 12, entonces…', 'x ≤ −4', ['x ≥ −4', 'x ≤ 4']),
                numerica('Ganancia máxima de G(x) = −x² + 10x − 16 (en millones).', 9),
                numerica('¿Cuántos enteros cumplen |x| &lt; 4?', 7),
                abierta('Plantea y resuelve una inecuación para saber cuántas horas puedes trabajar a $8 000 la hora si necesitas al menos $200 000.', 4)])

    U[3] = unidad(
        tema='Magnitudes que son razones y la derivada',
        objetivo='Reconocer magnitudes definidas como razones (velocidad, aceleración, densidad) y usar la derivada como razón de cambio para resolver problemas.',
        explora=[texto('Un velocímetro marca 72 km/h. ¿Cuántos metros recorre el carro en un segundo?')],
        aprende=[texto('Muchas magnitudes son <b>razones</b>: velocidad (m/s), aceleración (m/s²), densidad (g/cm³), caudal (L/s). 72 km/h = 72 000 m ÷ 3 600 s = <b>20 m/s</b>.'),
                 texto('Si una piedra cae y su posición es x(t) = 4,9 t², la velocidad <b>en cada instante</b> es la derivada: v(t) = 9,8 t. A los 2 s: v = <b>19,6 m/s</b>. '
                       'La aceleración es la derivada de la velocidad: 9,8 m/s² (la gravedad).'),
                 tabla([['Magnitud', 'Razón', 'Unidad SI'], ['Velocidad', 'Δx / Δt', 'm/s'], ['Aceleración', 'Δv / Δt', 'm/s²'], ['Densidad', 'masa / volumen', 'kg/m³'],
                        ['Caudal', 'volumen / tiempo', 'm³/s']]),
                 texto('Juzgar la pertinencia: si un cálculo dice que una persona camina a 50 m/s (180 km/h), hay un error.')],
        recuerda=['km/h ÷ 3,6 = m/s.', 'v(t) = x′(t); a(t) = v′(t).'],
        practica=[numerica('Convierte 90 km/h a m/s.', 25, 'm/s'), numerica('Velocidad de la piedra a los 3 s (v = 9,8 t).', F(294, 10), 'm/s')],
        taller=[numerica('Densidad de un bloque de 540 g y 200 cm³.', F(27, 10), 'g/cm³'), numerica('Una llave llena un tanque de 1 200 L en 8 min. Caudal.', 150, 'L/min'),
                numerica('Si x(t) = 3t² + 2t, ¿velocidad en t = 2? (v = 6t + 2)', 14, 'm/s'),
                unica('Un resultado de «un estudiante pesa 6 000 kg» indica…', 'un error en el cálculo', ['un resultado posible']),
                abierta('Mide el caudal de una llave de tu casa con un balde y un cronómetro. Repite tres veces y justifica tu resultado.', 5)])

    U[4] = unidad(
        tema='Precisión y error en las mediciones',
        objetivo='Diseñar e interpretar técnicas de medición con precisión creciente: instrumentos, escalas, errores y mediciones indirectas.',
        explora=[texto('Mides tu escritorio con una cuarta, con una regla escolar y con un metro de carpintero. ¿Cuál medición es más confiable? ¿Por qué?')],
        aprende=[texto('La <b>apreciación</b> de un instrumento es la menor división que puede leer (regla: 1 mm; cronómetro de celular: 0,01 s). Ninguna medición es exacta.'),
                 texto('<b>Error absoluto</b> = |medido − real|. <b>Error relativo</b> = error absoluto ÷ real. Si mido 25,3 cm y el valor real es 25,0 cm: error absoluto 0,3 cm; '
                       'relativo 0,3 ÷ 25 = 0,012 = <b>1,2 %</b>.'),
                 texto('<b>Medición indirecta</b> por semejanza: un palo de 1 m da una sombra de 0,8 m; a la misma hora un árbol da 6 m de sombra. Altura del árbol: 6 ÷ 0,8 = <b>7,5 m</b>.'),
                 texto('La <b>rapidez</b> también es una razón: al medir distancia y tiempo, sus errores se combinan en el resultado. Repetir y promediar reduce el error aleatorio.')],
        recuerda=['Error relativo: compara la precisión de mediciones diferentes.', 'Repetir y promediar.'],
        practica=[numerica('Error absoluto si mides 48 cm y el valor real es 50 cm.', 2, 'cm'), numerica('Error relativo de esa medición (en %).', 4, '%')],
        taller=[numerica('Un poste da 4,5 m de sombra y un palo de 2 m da 1,5 m. Altura del poste.', 6, 'm'),
                unica('¿Qué medición es más precisa: 1 m ± 1 cm o 10 km ± 1 m?', '10 km ± 1 m', ['1 m ± 1 cm']),
                numerica('Promedio de las mediciones 12,1 s; 12,3 s; 12,2 s.', F(122, 10), 's'),
                abierta('Mide la altura de tu colegio de dos formas indirectas (sombra y otra que propongas). Compara los resultados y discute la precisión.', 6)])

    U[5] = unidad(
        tema='La derivada: pendiente de la tangente',
        objetivo='Interpretar la derivada como razón de cambio y pendiente de la tangente, y hallar derivadas de funciones básicas.',
        explora=[texto('En una montaña rusa, ¿cómo mides «qué tan empinada» está la vía justo en un punto?')],
        aprende=[texto('<b>Definición</b>: f′(a) = límite, cuando h → 0, de [f(a + h) − f(a)] ÷ h. Es la pendiente de la tangente en x = a.'),
                 tabla([['Función', 'Derivada'], ['c (constante)', '0'], ['xⁿ', 'n·xⁿ⁻¹'], ['sen x', 'cos x'], ['cos x', '−sen x'], ['eˣ', 'eˣ'], ['ln x', '1/x']]),
                 texto('Se deriva término a término: (3x² + 2x − 5)′ = 6x + 2. En x = 1, la pendiente es <b>8</b>.'),
                 grafica({'x': [-1, 3], 'y': [-2, 10], 'elementos': [
                     {'t': 'funcion', 'expr': 'x^3', 'nombre': 'y = x³'},
                     {'t': 'funcion', 'expr': '12x-16', 'desde': '1', 'hasta': '2.6', 'nombre': 'tangente en x = 2', 'color': '#dc2626'},
                     {'t': 'punto', 'x': 2, 'y': 8, 'nombre': '(2, 8)'}]}, 50, 'y = x³ y su tangente en x = 2 (pendiente 12)')],
        recuerda=['(xⁿ)′ = n xⁿ⁻¹.', 'Derivada = pendiente de la tangente = razón instantánea.'],
        practica=[numerica('Derivada de x³ en x = 2.', 12), numerica('Derivada de 3x² + 2x − 5 en x = 1.', 8)],
        taller=[unica('La derivada de 5x⁴ es…', '20x³', ['5x³', '20x⁴']), unica('La derivada de sen x es…', 'cos x', ['−cos x', '−sen x']),
                numerica('Pendiente de la tangente a y = x² − 4x en x = 3.', 2), numerica('Derivada de ln x en x = 4.', F(1, 4)),
                abierta('Calcula [f(1 + h) − f(1)] ÷ h para f(x) = x³ con h = 0,1; 0,01 y 0,001. ¿A qué número se acerca?', 5)])

    U[6] = unidad(
        tema='Sistemas de coordenadas: cartesiano, polar y esférico',
        objetivo='Modelar objetos geométricos en coordenadas cartesianas, polares y esféricas y comparar las ventajas de cada sistema.',
        explora=[texto('Un radar de un aeropuerto ubica un avión «a 30 km, en dirección 60°». Un GPS lo ubica por latitud y longitud. ¿Por qué no usan x e y?')],
        aprende=[texto('<b>Polares</b> (r, θ): distancia al origen y ángulo. De polar a cartesiana: x = r cos θ, y = r sen θ. De cartesiana a polar: r = √(x² + y²), tan θ = y/x.'),
                 texto('El punto (3, 4) está a r = 5 del origen, con θ ≈ 53,13°. El punto polar (2, 90°) es el cartesiano (0, 2).'),
                 grafica({'x': [-1, 5], 'y': [-1, 5], 'forma': 'cuadrada', 'elementos': [
                     {'t': 'vector', 'a': [0, 0], 'b': [3, 4], 'nombre': 'r = 5'},
                     {'t': 'punto', 'x': 3, 'y': 4, 'nombre': '(3, 4)', 'proyecciones': True}]}, 40, 'Coordenadas cartesianas y polares del mismo punto'),
                 texto('<b>Esféricas</b>: en la Tierra usamos latitud y longitud (y la altura). Bogotá está cerca de 4,6° N y 74,1° O.'),
                 texto('En el espacio cartesiano (x, y, z) la distancia al origen es √(x² + y² + z²): para (2, 3, 6) es √49 = <b>7</b>.')],
        recuerda=['Polar: (r, θ). Esféricas: distancia y dos ángulos.', 'Se elige el sistema que simplifica el problema.'],
        practica=[numerica('r del punto (6, 8).', 10), unica('El punto polar (3, 0°) en cartesianas es…', '(3, 0)', ['(0, 3)', '(3, 3)'])],
        taller=[numerica('Distancia de (0, 0, 0) a (1, 2, 2).', 3), unica('La circunferencia x² + y² = 9 en polares es…', 'r = 3', ['θ = 3', 'r = 9']),
                unica('Para ubicar una ciudad en la Tierra se usan coordenadas…', 'esféricas (latitud y longitud)', ['cartesianas en el plano']),
                numerica('Coordenada y del punto polar (4, 30°). (sen 30° = 0,5)', 2),
                abierta('Busca las coordenadas de tu municipio en un mapa digital y explica qué significan la latitud y la longitud.', 4)])

    U[7] = unidad(
        tema='Modelos funcionales y signo de la derivada',
        objetivo='Plantear modelos funcionales con sus variables y rangos, y usar el signo de la derivada para estudiar crecimiento, máximos y mínimos.',
        explora=[texto('Con 40 m de malla quieres cercar un corral rectangular. ¿Qué medidas dan el área más grande?')],
        aprende=[texto('Modelo: lados x y 20 − x; área A(x) = x(20 − x) = 20x − x², con 0 &lt; x &lt; 20. A′(x) = 20 − 2x = 0 → x = 10. El corral óptimo es un cuadrado de 10 m: '
                       '<b>100 m²</b>.'),
                 texto('<b>Signo de la derivada</b>: si f′ &gt; 0 la función crece; si f′ &lt; 0 decrece; donde cambia de signo hay un máximo o un mínimo.'),
                 texto('f(x) = x³ − 3x; f′(x) = 3x² − 3 = 0 en x = ±1. Crece en x &lt; −1 y x &gt; 1, decrece entre −1 y 1. Máximo local f(−1) = 2; mínimo local f(1) = −2.'),
                 grafica({'x': [-2.5, 2.5], 'y': [-4, 4], 'elementos': [
                     {'t': 'funcion', 'expr': 'x^3-3x', 'nombre': 'f(x) = x³ − 3x'},
                     {'t': 'funcion', 'expr': '3x^2-3', 'nombre': "f′(x)", 'estilo': 'guiones', 'color': '#dc2626'},
                     {'t': 'punto', 'x': -1, 'y': 2, 'nombre': 'máx.'}, {'t': 'punto', 'x': 1, 'y': -2, 'nombre': 'mín.'}]}, 55, 'Donde f′ cambia de signo, f tiene máximos y mínimos')],
        recuerda=['f′ &gt; 0: crece. f′ &lt; 0: decrece. f′ = 0: posible máximo o mínimo.'],
        practica=[numerica('Área máxima del corral.', 100, 'm²'), numerica('¿En qué x positivo tiene f(x) = x³ − 3x un mínimo local?', 1)],
        taller=[numerica('Valor de x que maximiza A(x) = 30x − x².', 15), unica('Si f′(x) &lt; 0 en un intervalo, f allí…', 'decrece', ['crece', 'es constante']),
                numerica('Altura máxima de una pelota con h(t) = 20t − 5t² (h′ = 20 − 10t).', 20, 'm'),
                unica('El dominio razonable de A(x) = x(20 − x) para el corral es…', '0 &lt; x &lt; 20', ['todos los reales', 'x &gt; 20']),
                abierta('Con una hoja de 20 × 20 cm se hace una caja sin tapa recortando cuadrados de lado x en las esquinas. Plantea V(x) y su dominio, y estima el x de volumen máximo.', 6)])

    U[8] = unidad(
        tema='Reglas de derivación y aproximaciones',
        objetivo='Hallar derivadas con las reglas del producto, el cociente y la cadena, y relacionarlas con las gráficas y con aproximaciones sucesivas.',
        explora=[texto('¿Cómo derivar (2x + 1)³ sin desarrollar el cubo?')],
        aprende=[tabla([['Regla', 'Fórmula'], ['Suma', '(f + g)′ = f′ + g′'], ['Producto', '(f·g)′ = f′g + fg′'], ['Cociente', '(f/g)′ = (f′g − fg′)/g²'],
                        ['Cadena', '[f(g(x))]′ = f′(g(x))·g′(x)']]),
                 texto('Cadena: [(2x + 1)³]′ = 3(2x + 1)² · 2 = 6(2x + 1)². En x = 0 vale <b>6</b>.'),
                 texto('Producto: (x² · eˣ)′ = 2x eˣ + x² eˣ.'),
                 tabla([['h', '0,1', '0,01', '0,001'], ['[(2 + h)² − 4] ÷ h', '4,1', '4,01', '4,001']]),
                 texto('Las aproximaciones sucesivas se acercan a la derivada de x² en x = 2, que es 4.')],
        recuerda=['Cadena: derivada de afuera por derivada de adentro.'],
        practica=[numerica('Derivada de (2x + 1)³ en x = 1.', 54), unica('(x·sen x)′ es…', 'sen x + x cos x', ['cos x', 'x cos x'])],
        taller=[numerica('Derivada de (x² + 1)⁵ en x = 1. (Cadena: 5(x² + 1)⁴·2x)', 160), unica('La derivada de e^(3x) es…', '3e^(3x)', ['e^(3x)', '3e^x']),
                numerica('Derivada de x/(x + 1) en x = 1. (Cociente: 1/(x + 1)²)', F(1, 4)),
                vf('Si f′(a) = 0, la tangente en a es horizontal.', True),
                abierta('Deriva f(x) = x²·ln x y explica cada regla que usaste.', 5)])

    U[9] = unidad(
        tema='Correlación entre variables',
        objetivo='Plantear y resolver problemas que exploran la asociación o correlación entre dos variables, con un plan de recolección de datos.',
        explora=[texto('¿Los estudiantes que duermen más sacan mejores notas? ¿Cómo lo investigarías?')],
        aprende=[texto('Un <b>diagrama de dispersión</b> muestra pares de datos (x, y). Si los puntos suben juntos hay correlación <b>positiva</b>; si uno sube y el otro baja, '
                       '<b>negativa</b>; si están dispersos, no hay correlación lineal.'),
                 grafica({'x': [0, 10], 'y': [0, 5.5], 'nombre_x': 'horas de estudio', 'nombre_y': 'nota', 'elementos': [
                     {'t': 'punto', 'x': 1, 'y': 2.1}, {'t': 'punto', 'x': 2, 'y': 2.8}, {'t': 'punto', 'x': 3, 'y': 2.6}, {'t': 'punto', 'x': 4, 'y': 3.4},
                     {'t': 'punto', 'x': 5, 'y': 3.3}, {'t': 'punto', 'x': 6, 'y': 3.9}, {'t': 'punto', 'x': 7, 'y': 4.1}, {'t': 'punto', 'x': 8, 'y': 4.6},
                     {'t': 'funcion', 'expr': '1.85+0.33x', 'desde': '0.5', 'hasta': '9', 'nombre': 'recta de tendencia', 'estilo': 'guiones'}]}, 55, 'Correlación positiva'),
                 texto('El coeficiente r va de −1 a 1: cerca de 1 o −1 la relación lineal es fuerte; cerca de 0, débil.'),
                 texto('<b>Correlación no es causalidad</b>: las ventas de helado y los ahogamientos suben juntos en verano, pero uno no causa el otro (los causa el calor).'),
                 texto('Plan: pregunta → variables → población y muestra → instrumento (encuesta, medición) → registro → gráfica → conclusión.')],
        recuerda=['r ≈ 1: positiva fuerte. r ≈ −1: negativa fuerte. r ≈ 0: sin relación lineal.', 'Correlación ≠ causa.'],
        practica=[unica('Edad de un carro y su precio de venta tienen correlación…', 'negativa', ['positiva', 'nula']),
                  unica('Con la recta de tendencia, ¿qué nota se espera con 6 horas?', 'cerca de 3,8', ['cerca de 2', 'cerca de 5'])],
        taller=[unica('Un r = −0,95 indica…', 'relación negativa fuerte', ['relación positiva fuerte', 'ninguna relación']),
                unica('Número de calzado y nota de matemáticas: correlación esperada…', 'nula', ['positiva fuerte']),
                vf('Si dos variables están correlacionadas, una causa la otra.', False),
                abierta('Plan de investigación: ¿hay relación entre horas de sueño y nota? Define población, muestra, variables, instrumento y cómo presentarás los datos.', 8)])

    U[10] = unidad(
        tema='Probabilidad condicional e independencia',
        objetivo='Reconocer cuándo dos eventos son o no independientes y usar la probabilidad condicional para comprobarlo.',
        explora=[texto('Si sabes que una carta sacada de la baraja es roja, ¿cambia la probabilidad de que sea un corazón?')],
        aprende=[texto('<b>Probabilidad condicional</b>: P(A | B) = P(A ∩ B) ÷ P(B), la probabilidad de A sabiendo que ocurrió B.'),
                 tabla([['', 'Hace deporte', 'No hace deporte', 'Total'], ['Mujeres', '30', '20', '50'], ['Hombres', '30', '20', '50'], ['Total', '60', '40', '100']]),
                 texto('P(deporte) = 60/100 = 0,6. P(deporte | mujer) = 30/50 = 0,6. Saber que es mujer no cambia la probabilidad: los eventos son <b>independientes</b>.'),
                 texto('A y B son independientes si P(A | B) = P(A), o sea, P(A ∩ B) = P(A)·P(B). Lanzar dos monedas: P(cara y cara) = 1/2 · 1/2 = 1/4.'),
                 texto('Sin reposición los eventos dependen: sacar dos ases seguidos de una baraja de 52: 4/52 · 3/51 = <b>1/221</b>.')],
        recuerda=['P(A | B) = P(A ∩ B)/P(B).', 'Independientes: P(A ∩ B) = P(A)·P(B).'],
        practica=[numerica('Baraja de 52: P(corazón | roja).', F(1, 2)), numerica('P(cara y cara) con dos monedas.', F(1, 4))],
        taller=[numerica('Dos dados: P(suma 8 | el primero es 3).', F(1, 6), '', '0.001'),
                unica('Sacar dos bolas de una urna sin devolver la primera son eventos…', 'dependientes', ['independientes']),
                numerica('Urna con 3 rojas y 2 azules, sin reposición: P(dos rojas).', F(3, 10)),
                numerica('Con la tabla: P(mujer | hace deporte).', F(1, 2)),
                abierta('Haz una tabla de doble entrada con datos de tu curso (por ejemplo, usa gafas / le gusta leer) y comprueba si los eventos son independientes.', 6)])
    return U
