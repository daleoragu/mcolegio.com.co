"""Banco de 10.º y 11.º: funciones, trigonometría, límites, derivadas y conceptos (SIN integrales).

Preguntas escritas a mano, de nivel básico, con distractores de los errores típicos. Las que se calculan se
verifican con SymPy (si está instalado): la respuesta correcta debe dar lo mismo que SymPy y ningún distractor.
Genera aula/bancos/calculo_10_11.json (mismo formato del banco de la olimpiada).

    python aula/bancos/generar_calculo.py
"""
import json
import os
import random

random.seed(1011)
NIVEL = 'expertos'
N, E, B = 'newton', 'euclides', 'bernoulli'

# (grado, categoría, tema, pregunta, correcta, [3 distractores], verificación)
# verificación: None (pregunta de concepto) o (expresión SymPy que se calcula, [forma SymPy de la correcta, de cada distractor…])
P = [
    # =============================== 10.º ===============================
    (10, N, 'Funciones', '¿Cuánto vale f(4) si f(x) = 3x − 5?', '7', ['17', '−7', '12'], ('3*4-5', ['7', '17', '-7', '12'])),
    (10, N, 'Funciones', 'Si f(x) = x² − 2x + 1, ¿cuánto vale f(−1)?', '4', ['0', '2', '−2'], ('(-1)**2-2*(-1)+1', ['4', '0', '2', '-2'])),
    (10, N, 'Funciones', '¿Cuál es el dominio de f(x) = √(x − 3)?', 'x ≥ 3', ['x > 3', 'x ≤ 3', 'Todos los números reales'], None),
    (10, N, 'Funciones', '¿Cuál es el dominio de f(x) = 1/(x − 2)?', 'Todos los reales excepto 2', ['Todos los reales excepto −2', 'x > 2', 'Todos los números reales'], None),
    (10, N, 'Funciones', '¿Cuál es el rango de f(x) = x²?', 'y ≥ 0', ['Todos los números reales', 'y > 0', 'y ≤ 0'], None),
    (10, N, 'Funciones', 'Una gráfica es función si toda recta vertical la corta en…', 'A lo sumo un punto', ['Exactamente dos puntos', 'Ningún punto', 'Infinitos puntos'], None),
    (10, N, 'Funciones', '¿Qué significa que una relación sea una función?', 'A cada valor de x le corresponde exactamente un valor de y', ['A cada y le corresponden dos valores de x', 'Su gráfica es siempre una recta', 'Tiene que pasar por el origen'], None),
    (10, N, 'Funciones', '¿Cuál de estas funciones es par?', 'f(x) = x² + 1', ['f(x) = x³', 'f(x) = x + 1', 'f(x) = 2x'], None),
    (10, N, 'Funciones', 'Si f(x) = 2x y g(x) = x + 3, ¿cuánto vale f(g(1))?', '8', ['5', '4', '7'], ('2*(1+3)', ['8', '5', '4', '7'])),
    (10, N, 'Funciones', '¿Cuál es la función inversa de f(x) = 2x + 4?', '(x − 4)/2', ['(x + 4)/2', '2x − 4', 'x/2 + 4'], None),
    (10, N, 'Funciones', '¿Cuál es la asíntota vertical de f(x) = 1/(x + 4)?', 'x = −4', ['x = 4', 'y = 0', 'x = 0'], None),
    (10, N, 'Funciones', 'Si f(x) = 5 para todo x, ¿cuánto vale f(100)?', '5', ['500', '100', '0'], None),
    (10, N, 'Función lineal', '¿Cuál es la pendiente de la recta que pasa por (1, 2) y (3, 8)?', '3', ['1/3', '6', '2'], ('Rational(8-2, 3-1)', ['3', '1/3', '6', '2'])),
    (10, N, 'Función lineal', '¿Cuál es la ecuación de la recta de pendiente 2 que corta al eje y en −3?', 'y = 2x − 3', ['y = −3x + 2', 'y = 2x + 3', 'y = −2x − 3'], None),
    (10, N, 'Función lineal', '¿Qué pendiente tiene una recta paralela a y = 4x + 1?', '4', ['−4', '−1/4', '1/4'], None),
    (10, N, 'Función lineal', '¿Qué pendiente tiene una recta perpendicular a y = 2x + 5?', '−1/2', ['2', '−2', '1/2'], ('-1/Integer(2)', ['-1/2', '2', '-2', '1/2'])),
    (10, N, 'Función lineal', 'Una función lineal es creciente cuando…', 'Su pendiente es positiva', ['Su pendiente es negativa', 'Su pendiente es cero', 'Corta al eje y en un número positivo'], None),
    (10, N, 'Función lineal', '¿Cuál es la pendiente de la recta 2x + y = 6?', '−2', ['2', '6', '1/2'], None),
    (10, N, 'Función lineal', '¿En qué punto corta al eje x la recta y = 2x − 8?', '(4, 0)', ['(0, −8)', '(−4, 0)', '(8, 0)'], ('solve(2*x-8, x)[0]', ['4', '-4', '8', '-8'])),
    (10, N, 'Función cuadrática', '¿Cuál es el vértice de f(x) = x² − 6x + 5?', '(3, −4)', ['(−3, 32)', '(3, 4)', '(6, 5)'], ('(3)**2-6*3+5', ['-4', '32', '4', '5'])),
    (10, N, 'Función cuadrática', '¿Cuáles son las soluciones de x² − 5x + 6 = 0?', 'x = 2 y x = 3', ['x = −2 y x = −3', 'x = 1 y x = 6', 'x = −1 y x = 6'], ('solve(x**2-5*x+6, x)', None)),
    (10, N, 'Función cuadrática', '¿Cuántas soluciones reales tiene x² + 2x + 5 = 0?', 'Ninguna', ['Una', 'Dos', 'Infinitas'], ('2**2-4*1*5', ['-16'])),
    (10, N, 'Función cuadrática', '¿Hacia dónde abre la parábola f(x) = −2x² + 3?', 'Hacia abajo', ['Hacia arriba', 'Hacia la derecha', 'No es una parábola'], None),
    (10, N, 'Álgebra', '¿A qué es igual (x² − 9)/(x − 3) para x ≠ 3?', 'x + 3', ['x − 3', 'x² − 3', '3'], ('cancel((x**2-9)/(x-3))', ['x+3', 'x-3', 'x**2-3', '3'])),
    (10, N, 'Álgebra', '¿Cuál es la solución de 2x − 3 > 7?', 'x > 5', ['x < 5', 'x > 2', 'x > 10'], None),
    (10, N, 'Álgebra', '¿Qué valores de x cumplen |x − 1| = 4?', 'x = 5 o x = −3', ['x = 5 o x = 3', 'x = −5 o x = 3', 'Solo x = 5'], None),
    (10, N, 'Álgebra', '¿Cuánto es |−7| + |3|?', '10', ['−4', '4', '−10'], ('Abs(-7)+Abs(3)', ['10', '-4', '4', '-10'])),
    (10, N, 'Álgebra', '¿A qué es igual 1/√2 sin raíz en el denominador?', '√2/2', ['1/2', '2√2', '√2/4'], ('1/sqrt(2)', ['sqrt(2)/2', '1/2', '2*sqrt(2)', 'sqrt(2)/4'])),
    (10, N, 'Potencias y logaritmos', '¿Cuánto es (2³)²?', '64', ['32', '36', '12'], ('(2**3)**2', ['64', '32', '36', '12'])),
    (10, N, 'Potencias y logaritmos', 'Si f(x) = 3^x, ¿cuánto vale f(−2)?', '1/9', ['−9', '−6', '9'], ('Integer(3)**(-2)', ['1/9', '-9', '-6', '9'])),
    (10, N, 'Potencias y logaritmos', '¿Cuánto es el logaritmo en base 2 de 8?', '3', ['4', '2', '16'], ('log(8, 2)', ['3', '4', '2', '16'])),
    (10, N, 'Potencias y logaritmos', '¿Cuánto es log 1000 (logaritmo en base 10)?', '3', ['100', '30', '4'], ('log(1000, 10)', ['3', '100', '30', '4'])),
    (10, N, 'Potencias y logaritmos', '¿Cuánto es ln e?', '1', ['0', 'e', '10'], ('log(E)', ['1', '0', 'E', '10'])),
    (10, N, 'Potencias y logaritmos', '¿Qué valor de x cumple 2^x = 16?', '4', ['8', '3', '32'], ('solve(2**x-16, x)[0]', ['4', '8', '3', '32'])),
    (10, N, 'Potencias y logaritmos', '¿Qué propiedad de los logaritmos es correcta?', 'log(a·b) = log a + log b', ['log(a·b) = log a · log b', 'log(a + b) = log a + log b', 'log(a/b) = log a / log b'], None),
    (10, N, 'Potencias y logaritmos', '¿Cómo se escribe 0,00045 en notación científica?', '4,5 × 10⁻⁴', ['4,5 × 10⁴', '4,5 × 10⁻³', '45 × 10⁻²'], None),
    (10, N, 'Sucesiones', '¿Cuál es el término 10 de la progresión 3, 7, 11, 15, …?', '39', ['43', '40', '35'], ('3+9*4', ['39', '43', '40', '35'])),
    (10, N, 'Sucesiones', '¿Cuánto es 1 + 2 + 3 + … + 100?', '5050', ['5000', '10100', '4950'], ('summation(k, (k, 1, 100))', ['5050', '5000', '10100', '4950'])),
    (10, N, 'Sucesiones', '¿Cuál es la razón de la progresión geométrica 5, 15, 45, …?', '3', ['10', '5', '1/3'], ('Rational(15, 5)', ['3', '10', '5', '1/3'])),
    (10, E, 'Trigonometría', '¿Cuánto vale sen 30°?', '1/2', ['√3/2', '√2/2', '1'], ('sin(pi/6)', ['1/2', 'sqrt(3)/2', 'sqrt(2)/2', '1'])),
    (10, E, 'Trigonometría', '¿Cuánto vale cos 60°?', '1/2', ['√3/2', '0', '1'], ('cos(pi/3)', ['1/2', 'sqrt(3)/2', '0', '1'])),
    (10, E, 'Trigonometría', '¿Cuánto vale tan 45°?', '1', ['0', '√2', '√3'], ('tan(pi/4)', ['1', '0', 'sqrt(2)', 'sqrt(3)'])),
    (10, E, 'Trigonometría', '¿A cuántos radianes equivalen 180°?', 'π', ['2π', 'π/2', '180π'], ('rad(180)', ['pi', '2*pi', 'pi/2', '180*pi'])),
    (10, E, 'Trigonometría', '¿A cuántos radianes equivalen 90°?', 'π/2', ['π', 'π/4', '2π'], ('rad(90)', ['pi/2', 'pi', 'pi/4', '2*pi'])),
    (10, E, 'Trigonometría', '¿A cuántos grados equivalen 2π/3 radianes?', '120°', ['60°', '240°', '150°'], ('deg(2*pi/3)', ['120', '60', '240', '150'])),
    (10, E, 'Trigonometría', '¿A qué es igual sen² x + cos² x?', '1', ['0', '2', 'tan x'], ('simplify(sin(x)**2+cos(x)**2)', ['1', '0', '2', 'tan(x)'])),
    (10, E, 'Trigonometría', 'En un triángulo rectángulo el cateto opuesto a θ mide 3 y la hipotenusa 5. ¿Cuánto vale sen θ?', '3/5', ['4/5', '3/4', '5/3'], ('Rational(3, 5)', ['3/5', '4/5', '3/4', '5/3'])),
    (10, E, 'Trigonometría', 'En un triángulo rectángulo el cateto opuesto a θ mide 3 y el adyacente 4. ¿Cuánto vale tan θ?', '3/4', ['4/3', '3/5', '5/4'], ('Rational(3, 4)', ['3/4', '4/3', '3/5', '5/4'])),
    (10, E, 'Trigonometría', '¿Cuál es el periodo de y = sen x?', '2π', ['π', 'π/2', '1'], ('periodicity(sin(x), x)', ['2*pi', 'pi', 'pi/2', '1'])),
    (10, E, 'Trigonometría', '¿Cuál es la amplitud de y = 3 sen x?', '3', ['1', '6', '3π'], None),
    (10, E, 'Trigonometría', '¿Qué signo tiene el coseno de un ángulo del segundo cuadrante?', 'Negativo', ['Positivo', 'Es cero', 'Depende del ángulo'], None),
    (10, E, 'Trigonometría', 'Conoce dos lados de un triángulo y el ángulo entre ellos. ¿Qué usa para hallar el tercer lado?', 'La ley del coseno', ['La ley del seno', 'El teorema de Tales', 'La suma de los ángulos'], None),
    (10, E, 'Geometría analítica', 'Los catetos de un triángulo rectángulo miden 6 y 8. ¿Cuánto mide la hipotenusa?', '10', ['14', '12', '48'], ('sqrt(6**2+8**2)', ['10', '14', '12', '48'])),
    (10, E, 'Geometría analítica', '¿Cuál es la distancia entre (0, 0) y (3, 4)?', '5', ['7', '1', '25'], ('sqrt(3**2+4**2)', ['5', '7', '1', '25'])),
    (10, E, 'Geometría analítica', '¿Cuál es el punto medio entre (2, 4) y (6, 8)?', '(4, 6)', ['(8, 12)', '(2, 2)', '(3, 4)'], None),
    (10, E, 'Geometría analítica', '¿Cuál es el radio de la circunferencia x² + y² = 25?', '5', ['25', '10', '625'], ('sqrt(25)', ['5', '25', '10', '625'])),
    (10, E, 'Geometría analítica', '¿Cuál es el centro de la circunferencia (x − 2)² + (y + 1)² = 9?', '(2, −1)', ['(−2, 1)', '(2, 1)', '(−2, −1)'], None),
    (10, E, 'Geometría analítica', '¿En qué punto corta al eje y la recta y = 3x − 7?', '(0, −7)', ['(7, 0)', '(0, 3)', '(7/3, 0)'], None),
    (10, B, 'Probabilidad', 'Al lanzar un dado, ¿cuál es la probabilidad de sacar un número par?', '1/2', ['1/3', '1/6', '2/3'], ('Rational(3, 6)', ['1/2', '1/3', '1/6', '2/3'])),
    (10, B, 'Conteo', '¿De cuántas formas se pueden ordenar 4 libros en un estante?', '24', ['16', '4', '10'], ('factorial(4)', ['24', '16', '4', '10'])),
    (10, B, 'Estadística', '¿Cuál es el promedio de 4, 6, 8 y 10?', '7', ['6', '8', '28'], ('Rational(4+6+8+10, 4)', ['7', '6', '8', '28'])),

    # =============================== 11.º ===============================
    (11, N, 'Límites', '¿Cuánto es lím (x→3) de (2x + 1)?', '7', ['6', '3', 'No existe'], ('limit(2*x+1, x, 3)', ['7', '6', '3'])),
    (11, N, 'Límites', '¿Cuánto es lím (x→2) de (x² − 4)/(x − 2)?', '4', ['0', 'No existe', '2'], ('limit((x**2-4)/(x-2), x, 2)', ['4', '0', '2'])),
    (11, N, 'Límites', '¿Cuánto es lím (x→1) de (x² − 1)/(x − 1)?', '2', ['0', '1', '∞'], ('limit((x**2-1)/(x-1), x, 1)', ['2', '0', '1', 'oo'])),
    (11, N, 'Límites', '¿Cuánto es lím (x→0) de (x² + 3x)/x?', '3', ['0', '∞', '1'], ('limit((x**2+3*x)/x, x, 0)', ['3', '0', 'oo', '1'])),
    (11, N, 'Límites', '¿Cuánto es lím (x→−1) de (x³ + 1)/(x + 1)?', '3', ['0', '1', '−3'], ('limit((x**3+1)/(x+1), x, -1)', ['3', '0', '1', '-3'])),
    (11, N, 'Límites', '¿Cuánto es lím (x→0) de (√(x + 9) − 3)/x?', '1/6', ['0', '1/3', '6'], ('limit((sqrt(x+9)-3)/x, x, 0)', ['1/6', '0', '1/3', '6'])),
    (11, N, 'Límites', '¿Cuánto es lím (x→4) de √x?', '2', ['4', '16', '−2'], ('limit(sqrt(x), x, 4)', ['2', '4', '16', '-2'])),
    (11, N, 'Límites', '¿Cuánto es lím (x→2) de 5?', '5', ['2', '10', '0'], ('limit(5, x, 2)', ['5', '2', '10', '0'])),
    (11, N, 'Límites', '¿Cuánto es lím (x→∞) de 1/x?', '0', ['1', '∞', 'No existe'], ('limit(1/x, x, oo)', ['0', '1', 'oo'])),
    (11, N, 'Límites', '¿Cuánto es lím (x→∞) de (3x² + 1)/(x² − 5)?', '3', ['0', '∞', '−1/5'], ('limit((3*x**2+1)/(x**2-5), x, oo)', ['3', '0', 'oo', '-1/5'])),
    (11, N, 'Límites', '¿Cuánto es lím (x→∞) de (2x + 1)/x²?', '0', ['2', '∞', '1'], ('limit((2*x+1)/x**2, x, oo)', ['0', '2', 'oo', '1'])),
    (11, N, 'Límites', '¿Qué pasa con 5x³/(2x²) cuando x → ∞?', 'Crece sin límite (∞)', ['Tiende a 5/2', 'Tiende a 0', 'Tiende a 1'], ('limit(5*x**3/(2*x**2), x, oo)', ['oo', '5/2', '0', '1'])),
    (11, N, 'Límites', '¿Cuánto es lím (x→0) de sen x / x?', '1', ['0', '∞', 'No existe'], ('limit(sin(x)/x, x, 0)', ['1', '0', 'oo'])),
    (11, N, 'Límites', 'Si el límite por la izquierda es 2 y por la derecha es 5, el límite…', 'No existe', ['Es 2', 'Es 5', 'Es 3,5'], None),
    (11, N, 'Límites', 'Al reemplazar en un límite da 0/0. ¿Qué significa?', 'Es una indeterminación: hay que simplificar antes', ['El límite es 0', 'El límite es 1', 'El límite nunca existe'], None),
    (11, N, 'Límites', '¿Cuál es la asíntota horizontal de f(x) = (2x + 3)/(x − 1)?', 'y = 2', ['y = 3', 'x = 1', 'y = −3'], ('limit((2*x+3)/(x-1), x, oo)', ['2', '3', '-3'])),
    (11, N, 'Límites', 'Cuando n → ∞, ¿a qué tiende la sucesión aₙ = (n + 1)/n?', '1', ['0', '∞', '2'], ('limit((n+1)/n, n, oo)', ['1', '0', 'oo', '2'])),
    (11, N, 'Continuidad', 'Una función f es continua en x = a cuando…', 'Existen f(a) y el límite en a, y son iguales', ['f(a) es un número positivo', 'Su derivada en a es cero', 'Su gráfica es una recta'], None),
    (11, N, 'Continuidad', 'f(x) = x + k si x < 1 y f(x) = 2x si x ≥ 1. ¿Qué valor de k la hace continua?', '1', ['2', '0', '−1'], ('solve(1+k-2*1, k)[0]', ['1', '2', '0', '-1'])),
    (11, N, 'Derivadas', '¿Qué representa la derivada f′(a)?', 'La pendiente de la recta tangente a la curva en x = a', ['El área bajo la curva hasta a', 'El valor de la función en a', 'El punto donde la curva corta al eje x'], None),
    (11, N, 'Derivadas', '¿Cuál es la definición de la derivada de f?', 'f′(x) = lím (h→0) de [f(x + h) − f(x)]/h', ['f′(x) = lím (h→0) de f(x + h)/h', 'f′(x) = f(x + 1) − f(x)', 'f′(x) = lím (h→∞) de [f(x + h) − f(x)]/h'], None),
    (11, N, 'Derivadas', '¿Cuál es la derivada de f(x) = x⁵?', '5x⁴', ['x⁴', '5x⁵', '4x⁵'], ('diff(x**5, x)', ['5*x**4', 'x**4', '5*x**5', '4*x**5'])),
    (11, N, 'Derivadas', '¿Cuál es la derivada de f(x) = 7?', '0', ['7', '1', '7x'], ('diff(7, x)', ['0', '7', '1', '7*x'])),
    (11, N, 'Derivadas', '¿Cuál es la derivada de f(x) = 3x² − 4x + 1?', '6x − 4', ['3x − 4', '6x + 1', '6x² − 4'], ('diff(3*x**2-4*x+1, x)', ['6*x-4', '3*x-4', '6*x+1', '6*x**2-4'])),
    (11, N, 'Derivadas', '¿Cuál es la derivada de f(x) = √x?', '1/(2√x)', ['2√x', '1/√x', '√x/2'], ('diff(sqrt(x), x)', ['1/(2*sqrt(x))', '2*sqrt(x)', '1/sqrt(x)', 'sqrt(x)/2'])),
    (11, N, 'Derivadas', '¿Cuál es la derivada de f(x) = 1/x?', '−1/x²', ['1/x²', 'ln x', '−1/x'], ('diff(1/x, x)', ['-1/x**2', '1/x**2', 'log(x)', '-1/x'])),
    (11, N, 'Derivadas', '¿Cuál es la derivada de f(x) = 2/x³?', '−6/x⁴', ['−6/x²', '6/x⁴', '−2/(3x⁴)'], ('diff(2/x**3, x)', ['-6/x**4', '-6/x**2', '6/x**4', '-2/(3*x**4)'])),
    (11, N, 'Derivadas', '¿Cuál es la derivada de f(x) = e^x?', 'e^x', ['x·e^(x − 1)', 'e', 'ln x'], ('diff(exp(x), x)', ['exp(x)', 'x*exp(x-1)', 'E', 'log(x)'])),
    (11, N, 'Derivadas', '¿Cuál es la derivada de f(x) = ln x?', '1/x', ['e^x', 'x', '1/ln x'], ('diff(log(x), x)', ['1/x', 'exp(x)', 'x', '1/log(x)'])),
    (11, N, 'Derivadas', '¿Cuál es la derivada de f(x) = sen x?', 'cos x', ['−cos x', 'sen x', '−sen x'], ('diff(sin(x), x)', ['cos(x)', '-cos(x)', 'sin(x)', '-sin(x)'])),
    (11, N, 'Derivadas', '¿Cuál es la derivada de f(x) = cos x?', '−sen x', ['sen x', 'cos x', '−cos x'], ('diff(cos(x), x)', ['-sin(x)', 'sin(x)', 'cos(x)', '-cos(x)'])),
    (11, N, 'Derivadas', '¿Cuál es la derivada de f(x) = tan x?', 'sec² x', ['cot x', '−sec² x', 'sen² x'], ('diff(tan(x), x)', ['sec(x)**2', 'cot(x)', '-sec(x)**2', 'sin(x)**2'])),
    (11, N, 'Derivadas', '¿Cuál es la derivada de f(x) = x · e^x? (regla del producto)', 'e^x + x·e^x', ['e^x', 'x·e^x', '2e^x'], ('diff(x*exp(x), x)', ['exp(x)+x*exp(x)', 'exp(x)', 'x*exp(x)', '2*exp(x)'])),
    (11, N, 'Derivadas', '¿Cuál es la derivada de f(x) = x/(x + 1)? (regla del cociente)', '1/(x + 1)²', ['1/(x + 1)', '−1/(x + 1)²', 'x/(x + 1)²'], ('diff(x/(x+1), x)', ['1/(x+1)**2', '1/(x+1)', '-1/(x+1)**2', 'x/(x+1)**2'])),
    (11, N, 'Derivadas', '¿Cuál es la derivada de f(x) = (2x + 1)³? (regla de la cadena)', '6(2x + 1)²', ['3(2x + 1)²', '6(2x + 1)', '2(2x + 1)³'], ('diff((2*x+1)**3, x)', ['6*(2*x+1)**2', '3*(2*x+1)**2', '6*(2*x+1)', '2*(2*x+1)**3'])),
    (11, N, 'Derivadas', '¿Cuál es la derivada de f(x) = sen(3x)?', '3 cos(3x)', ['cos(3x)', '−3 cos(3x)', '3 sen(3x)'], ('diff(sin(3*x), x)', ['3*cos(3*x)', 'cos(3*x)', '-3*cos(3*x)', '3*sin(3*x)'])),
    (11, N, 'Derivadas', '¿Cuál es la derivada de f(x) = e^(2x)?', '2e^(2x)', ['e^(2x)', '2x·e^(2x − 1)', 'e²'], ('diff(exp(2*x), x)', ['2*exp(2*x)', 'exp(2*x)', '2*x*exp(2*x-1)', 'exp(2)'])),
    (11, N, 'Derivadas', '¿Cuál es la derivada de f(x) = ln(x² + 1)?', '2x/(x² + 1)', ['1/(x² + 1)', '2x', '2/x'], ('diff(log(x**2+1), x)', ['2*x/(x**2+1)', '1/(x**2+1)', '2*x', '2/x'])),
    (11, N, 'Derivadas', 'Si f(x) = x³, ¿cuánto vale f′(2)?', '12', ['8', '6', '3'], ('diff(x**3, x).subs(x, 2)', ['12', '8', '6', '3'])),
    (11, N, 'Derivadas', '¿Cuál es la segunda derivada de f(x) = x⁴?', '12x²', ['4x³', '24x', '12x³'], ('diff(x**4, x, 2)', ['12*x**2', '4*x**3', '24*x', '12*x**3'])),
    (11, N, 'Aplicaciones de la derivada', '¿Cuál es la pendiente de la recta tangente a y = x² en x = 3?', '6', ['9', '3', '2'], ('diff(x**2, x).subs(x, 3)', ['6', '9', '3', '2'])),
    (11, N, 'Aplicaciones de la derivada', '¿Cuál es la recta tangente a y = x² en el punto (1, 1)?', 'y = 2x − 1', ['y = 2x + 1', 'y = x', 'y = 2x'], ('diff(x**2, x).subs(x, 1)*(x-1)+1', ['2*x-1', '2*x+1', 'x', '2*x'])),
    (11, N, 'Aplicaciones de la derivada', 'Un objeto recorre s(t) = 5t² metros. ¿Cuál es su velocidad en t = 2 s?', '20 m/s', ['10 m/s', '40 m/s', '5 m/s'], ('diff(5*t**2, t).subs(t, 2)', ['20', '10', '40', '5'])),
    (11, N, 'Aplicaciones de la derivada', '¿En qué x tiene f(x) = x² − 4x un punto crítico?', 'x = 2', ['x = 4', 'x = 0', 'x = −2'], ('solve(diff(x**2-4*x, x), x)[0]', ['2', '4', '0', '-2'])),
    (11, N, 'Aplicaciones de la derivada', '¿Dónde tiene f(x) = x³ − 3x un máximo local?', 'En x = −1', ['En x = 1', 'En x = 0', 'En x = 3'], ('[c for c in solve(diff(x**3-3*x, x), x) if diff(x**3-3*x, x, 2).subs(x, c) < 0][0]', ['-1', '1', '0', '3'])),
    (11, N, 'Aplicaciones de la derivada', 'Si f′(x) > 0 en un intervalo, entonces f en ese intervalo es…', 'Creciente', ['Decreciente', 'Constante', 'Cóncava hacia abajo'], None),
    (11, N, 'Aplicaciones de la derivada', 'Si f′′(x) > 0 en un intervalo, la gráfica de f es…', 'Cóncava hacia arriba', ['Cóncava hacia abajo', 'Decreciente', 'Una recta'], None),
    (11, N, 'Aplicaciones de la derivada', 'Dos números positivos suman 20 y su producto es el mayor posible. ¿Cuáles son?', '10 y 10', ['5 y 15', '1 y 19', '2 y 18'], ('solve(diff(x*(20-x), x), x)[0]', ['10', '5', '1', '2'])),
    (11, N, 'Aplicaciones de la derivada', 'El área de un cuadrado es A = l². ¿A qué ritmo cambia A respecto al lado cuando l = 3?', '6', ['9', '3', '12'], ('diff(l**2, l).subs(l, 3)', ['6', '9', '3', '12'])),
    (11, N, 'Aplicaciones de la derivada', '¿En qué punto NO es derivable f(x) = |x|?', 'En x = 0', ['En x = 1', 'En ningún punto', 'En todos los puntos'], None),
    (11, N, 'Funciones', '¿Cuál es el dominio de f(x) = ln(x − 1)?', 'x > 1', ['x ≥ 1', 'x > 0', 'Todos los números reales'], None),
    (11, N, 'Funciones', 'Si f(x) = x² y g(x) = x + 1, ¿cuál es g(f(x))?', 'x² + 1', ['(x + 1)²', 'x² + x', '2x + 1'], ('(x**2)+1', ['x**2+1', '(x+1)**2', 'x**2+x', '2*x+1'])),
    (11, N, 'Funciones', '¿Cuál es la función inversa de f(x) = e^x?', 'ln x', ['e^(−x)', '1/e^x', 'log en base 10 de x'], None),
    (11, N, 'Funciones', 'La función f(x) = x³ es…', 'Impar', ['Par', 'Ni par ni impar', 'Constante'], None),
    (11, N, 'Funciones', 'Una función es inyectiva (uno a uno) cuando…', 'Valores distintos de x dan valores distintos de y', ['Toda recta vertical la corta una vez', 'Pasa por el origen', 'Es creciente y decreciente a la vez'], None),
    (11, N, 'Funciones', '¿Qué valor de x cumple ln x = 0?', 'x = 1', ['x = 0', 'x = e', 'x = −1'], ('solve(log(x), x)[0]', ['1', '0', 'E', '-1'])),
    (11, N, 'Funciones', '¿Qué valor de x cumple e^x = 1?', 'x = 0', ['x = 1', 'x = e', 'No tiene solución'], ('solve(exp(x)-1, x)[0]', ['0', '1', 'E'])),
    (11, E, 'Trigonometría', '¿Qué valores de x en [0, 2π) cumplen sen x = 0?', 'x = 0 y x = π', ['x = π/2 y x = 3π/2', 'Solo x = π', 'x = 0, π/2 y π'], ('solveset(sin(x), x, Interval.Ropen(0, 2*pi))', None)),
    (11, B, 'Probabilidad', 'Si P(A) = 0,3, ¿cuánto vale la probabilidad de que NO ocurra A?', '0,7', ['0,3', '1,3', '0'], ('1-Rational(3, 10)', ['7/10', '3/10', '13/10', '0'])),
    (11, B, 'Conteo', '¿De cuántas formas se escogen 2 estudiantes de un grupo de 5? (sin importar el orden)', '10', ['20', '25', '7'], ('binomial(5, 2)', ['10', '20', '25', '7'])),
    (11, B, 'Estadística', '¿Cuál es la mediana de 3, 9, 1, 7 y 5?', '5', ['7', '25', '9'], ('sorted([3, 9, 1, 7, 5])[2]', ['5', '7', '25', '9'])),
    (11, B, 'Sumatorias', '¿Cuánto es 1² + 2² + 3² + 4²?', '30', ['16', '100', '20'], ('summation(k**2, (k, 1, 4))', ['30', '16', '100', '20'])),
]


def verificar():
    """Que cada respuesta calculada coincida con SymPy y que ningún distractor también sea correcto."""
    try:
        import sympy as sp
    except ImportError:
        print('(SymPy no está instalado: no se verificaron las respuestas)')
        return
    x, k, n, t, l = sp.symbols('x k n t l')
    entorno = {**{a: getattr(sp, a) for a in dir(sp) if not a.startswith('_')}, 'x': x, 'k': k, 'n': n, 't': t, 'l': l}
    errores, revisadas = [], 0
    for g, cat, tema, texto, correcta, malas, chk in P:
        if not chk:
            continue
        expr, formas = chk
        valor = eval(expr, entorno)                         # noqa: S307 — expresiones fijas de este archivo
        revisadas += 1
        if formas is None:                                  # conjuntos de soluciones: se revisan aparte
            esperado = {'solve(x**2-5*x+6, x)': {2, 3}}.get(expr) or {0, sp.pi}
            if set(valor) != set(esperado):
                errores.append(f'{texto}: SymPy da {valor}')
            continue
        bien = sp.simplify(sp.sympify(formas[0], locals=entorno) - valor) == 0 if valor not in (sp.oo,) else sp.sympify(formas[0]) == sp.oo
        if not bien:
            errores.append(f'{texto}: SymPy da {valor}, la respuesta dice {correcta}')
        for f in formas[1:]:
            m = sp.sympify(f, locals=entorno)
            if (m == valor) or (valor != sp.oo and m != sp.oo and sp.simplify(m - valor) == 0):
                errores.append(f'{texto}: el distractor {f} también es correcto')
    if errores:
        raise SystemExit('ERRORES:\n' + '\n'.join(errores))
    print(f'Verificadas con SymPy: {revisadas} preguntas calculadas, sin errores.')


def generar():
    banco, vistas = [], set()
    for g, cat, tema, texto, correcta, malas, _ in P:
        assert texto not in vistas, texto
        assert len(set(malas + [correcta])) == 4, texto
        vistas.add(texto)
        opciones = [{'texto': correcta, 'correcta': True}] + [{'texto': m, 'correcta': False} for m in malas]
        random.shuffle(opciones)
        banco.append({'grado': g, 'ciclo': NIVEL, 'categoria': cat, 'tema': tema, 'texto': texto, 'opciones': opciones,
                      'origen': f'Banco cálculo {g}.º'})
    return banco


if __name__ == '__main__':
    verificar()
    banco = generar()
    with open(os.path.join(os.path.dirname(__file__), 'calculo_10_11.json'), 'w', encoding='utf-8') as f:
        json.dump(banco, f, ensure_ascii=False, indent=0)
    from collections import Counter
    print(len(banco), 'preguntas ·', dict(Counter(p['grado'] for p in banco)), '·', dict(Counter(p['tema'] for p in banco)))
