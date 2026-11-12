"""Matemáticas 9.º: una guía y un taller por cada uno de los 11 DBA (V.2): números reales y aproximación, desigualdades,
sucesiones, cuerpos redondos, Thales y Pitágoras, funciones, conjeturas, diagramas de caja y conteo. Borradores para revisar."""
from fractions import Fraction as F

from .base import abierta, grafica, imagen, numerica, tabla, texto, unica, unidad, vf


def unidades():
    U = {}

    U[1] = unidad(
        tema='Números reales: exactitud y aproximación',
        objetivo='Operar con números reales en expresiones polinómicas y estimar el error al aproximar un irracional con racionales.',
        explora=[texto('Si usas 3,14 en lugar de π para calcular el área de un círculo de radio 10 cm, ¿qué tanto te equivocas?')],
        aprende=[texto('Área exacta: 100π ≈ 314,159… cm². Con 3,14: 314 cm². <b>Error</b> ≈ 0,16 cm² (muy pequeño).'),
                 texto('Con √2 ≈ 1,41: (1,41)² = 1,9881, no 2. El error de la aproximación crece al operar.'),
                 texto('En expresiones polinómicas con reales: si x = √3, entonces x² − 2x + 1 = 3 − 2√3 + 1 = <b>4 − 2√3</b> (valor exacto) ≈ 0,536.')],
        recuerda=['Exacto: π, √3. Aproximado: 3,14; 1,73.', 'Más decimales → menor error.'],
        practica=[numerica('Área de un círculo de radio 10 usando π ≈ 3,14.', 314, 'cm²'), unica('¿Cuál es el valor exacto?', '√3', ['1,73', '1,7'])],
        taller=[numerica('Calcula (1,41)² (sin redondear).', F(19881, 10000)), unica('¿Cuál aproximación de π tiene menos error?', '3,1416', ['3,14', '3']),
                unica('Con x = √2, x² + 1 vale…', '3', ['√2 + 1', '2,41']),
                abierta('Calcula el perímetro de una rueda de 30 cm de diámetro con π ≈ 3, 3,14 y 3,1416. Compara los errores.', 5)])

    U[2] = unidad(
        tema='Expresiones algebraicas, igualdades y desigualdades',
        objetivo='Transformar expresiones algebraicas y usar las propiedades de la igualdad y del orden para hallar conjuntos solución.',
        explora=[texto('Un plan de celular cuesta $20 000 más $500 por cada GB extra. ¿Cuántos GB extra puedo usar si no quiero pagar más de $27 000?')],
        aprende=[texto('Planteo: 20 000 + 500x ≤ 27 000 → 500x ≤ 7 000 → <b>x ≤ 14</b> GB.'),
                 texto('Propiedades del orden: si a &lt; b, entonces a + c &lt; b + c. Si multiplico por un número <b>negativo</b>, la desigualdad <b>se invierte</b>: '
                       '−2x &lt; 6 → x &gt; −3.'),
                 texto('Productos notables: (a + b)² = a² + 2ab + b²; (a + b)(a − b) = a² − b².')],
        recuerda=['Multiplicar o dividir por negativo invierte la desigualdad.', 'El conjunto solución puede ser un intervalo.'],
        practica=[numerica('Resuelve 500x ≤ 7 000. Escribe el máximo valor de x.', 14), unica('−2x < 6 equivale a…', 'x > −3', ['x < −3', 'x > 3'])],
        taller=[unica('(x + 3)² es…', 'x² + 6x + 9', ['x² + 9', 'x² + 3x + 9']), unica('(x + 5)(x − 5) es…', 'x² − 25', ['x² + 25', 'x² − 10x − 25']),
                numerica('Resuelve 3x − 4 > 11. Escribe el valor que x debe superar.', 5),
                abierta('Escribe una situación de presupuesto que se resuelva con una desigualdad y resuélvela.', 5)])

    U[3] = unidad(
        tema='Sucesiones y procesos infinitos',
        objetivo='Encontrar la expresión general de sucesiones y analizar procesos infinitos.',
        explora=[texto('Caminas hacia una puerta: primero la mitad del camino, luego la mitad de lo que falta, y así. ¿Llegas alguna vez?')],
        aprende=[texto('Recorres 1/2 + 1/4 + 1/8 + … Cada vez te acercas más a <b>1</b> (todo el camino), aunque son infinitos pasos: la suma tiende a 1.'),
                 tabla([['Sucesión', 'Término general', 'Tipo'], ['3, 7, 11, 15…', 'aₙ = 4n − 1', 'aritmética (diferencia 4)'], ['2, 6, 18, 54…', 'aₙ = 2·3ⁿ⁻¹', 'geométrica (razón 3)'],
                        ['1, 1/2, 1/4, 1/8…', 'aₙ = (1/2)ⁿ⁻¹', 'geométrica (razón 1/2)']]),
                 texto('Con el término general calculo cualquier término: en 3, 7, 11…, a₅₀ = 4·50 − 1 = <b>199</b>.')],
        recuerda=['Aritmética: se suma una diferencia. Geométrica: se multiplica por una razón.'],
        practica=[numerica('a₅₀ de 3, 7, 11, 15…', 199), numerica('Quinto término de 2, 6, 18, 54…', 162)],
        taller=[unica('El término general de 5, 10, 15, 20… es…', 'aₙ = 5n', ['aₙ = n + 5', 'aₙ = 5ⁿ']),
                numerica('¿Cuánto suman 1/2 + 1/4 + 1/8 + 1/16? (escribe el decimal)', F(15, 16)), vf('La suma 1/2 + 1/4 + 1/8 + … nunca pasa de 1.', True),
                abierta('Dobla una hoja por la mitad muchas veces y registra cuántas partes hay. Escribe el término general.', 5)])

    U[4] = unidad(
        tema='Cuerpos redondos: cilindro, cono y esfera',
        objetivo='Calcular volúmenes y capacidades de cilindros, conos y esferas en situaciones reales.',
        explora=[texto('¿Cuánta agua cabe en un tanque cilíndrico de 1 m de radio y 2 m de alto?')],
        aprende=[tabla([['Cuerpo', 'Volumen'], ['Cilindro', 'V = π r² h'], ['Cono', 'V = (1/3) π r² h'], ['Esfera', 'V = (4/3) π r³']]),
                 texto('Tanque: V = π · 1² · 2 ≈ 6,28 m³ ≈ <b>6 280 litros</b>.'),
                 texto('Un cono con la misma base y altura que un cilindro tiene <b>un tercio</b> de su volumen: con 3 conos llenos se llena el cilindro.'),
                 imagen('d-solidos-n', 60)],
        recuerda=['1 m³ = 1 000 L.', 'Cono = 1/3 del cilindro de igual base y altura.'],
        practica=[numerica('Volumen de un cilindro de radio 1 m y altura 2 m (usa π ≈ 3,14).', F(628, 100), 'm³', tolerancia='0,01'),
                  numerica('Volumen de una esfera de radio 3 cm (usa π ≈ 3,14).', F(11304, 100), 'cm³', tolerancia='0,1')],
        taller=[numerica('Volumen de un cono de radio 3 cm y altura 4 cm (π ≈ 3,14).', F(3768, 100), 'cm³', tolerancia='0,1'),
                unica('¿Cuántos conos llenan un cilindro de igual base y altura?', '3', ['2', '4']),
                numerica('¿Cuántos litros caben en 2 m³?', 2000, 'L'),
                abierta('Mide una lata de gaseosa y calcula su capacidad. Compárala con lo que dice la etiqueta.', 5)])

    thales = {'x': [-0.5, 9], 'y': [-0.5, 6], 'escala_igual': True, 'forma': 'ancha', 'elementos': [
        {'t': 'segmento', 'a': [0, 0], 'b': [8, 0], 'nombre': ''}, {'t': 'segmento', 'a': [0, 0], 'b': [8, 5], 'nombre': ''},
        {'t': 'segmento', 'a': [4, 0], 'b': [4, 2.5], 'nombre': '', 'color': '#dc2626'}, {'t': 'segmento', 'a': [8, 0], 'b': [8, 5], 'nombre': '', 'color': '#dc2626'},
        {'t': 'texto', 'x': 1.8, 'y': -0.45, 'texto': '4'}, {'t': 'texto', 'x': 5.8, 'y': -0.45, 'texto': '4'}]}
    U[5] = unidad(
        tema='Thales y Pitágoras para medir',
        objetivo='Usar los teoremas de Thales y Pitágoras para proponer y justificar estrategias de medición de longitudes.',
        explora=[texto('¿Cómo medirías el ancho de un río sin cruzarlo?')],
        aprende=[grafica(thales, 50, 'Paralelas que cortan dos rectas: segmentos proporcionales'),
                 texto('<b>Teorema de Thales</b>: si varias paralelas cortan dos rectas, los segmentos que determinan son proporcionales.'),
                 texto('Ancho del río: formo triángulos semejantes con estacas en la orilla y mido distancias en tierra; por proporción hallo el ancho.'),
                 texto('<b>Pitágoras</b> para distancias inaccesibles: una cometa con 50 m de cuerda está sobre un punto a 30 m de mí → altura = √(50² − 30²) = <b>40 m</b>.')],
        recuerda=['Thales: rectas paralelas → segmentos proporcionales.', 'Pitágoras: c² = a² + b² en triángulos rectángulos.'],
        practica=[numerica('Altura de la cometa (cuerda 50 m, distancia horizontal 30 m).', 40, 'm'),
                  numerica('En el dibujo, la primera paralela mide 2,5 y está a 4 del origen. ¿Cuánto mide la de 8?', 5)],
        taller=[numerica('Por Thales: 3/x = 6/10. ¿Cuánto vale x?', 5), numerica('Diagonal de un televisor de 48 cm × 36 cm.', 60, 'cm'),
                vf('El teorema de Thales sirve para triángulos semejantes.', True),
                abierta('Diseña un procedimiento para medir la altura de tu colegio sin subir.', 6)])

    U[6] = unidad(
        tema='Semejanza, congruencia y regularidades',
        objetivo='Hacer conjeturas sobre regularidades de figuras planas y sólidos usando criterios de semejanza, congruencia y Thales.',
        explora=[texto('Si amplías un triángulo al doble, ¿qué pasa con sus ángulos? ¿Y con su área?')],
        aprende=[texto('En figuras semejantes con razón <b>k</b>: los ángulos se conservan, las longitudes se multiplican por k, las áreas por <b>k²</b> y los volúmenes por <b>k³</b>.'),
                 tabla([['Razón k', 'Longitudes', 'Áreas', 'Volúmenes'], ['2', '× 2', '× 4', '× 8'], ['3', '× 3', '× 9', '× 27'], ['1/2', '× 1/2', '× 1/4', '× 1/8']]),
                 texto('Criterios de semejanza de triángulos: AA, LAL (lados proporcionales y ángulo igual), LLL (tres lados proporcionales).')],
        recuerda=['Semejanza con razón k: áreas × k², volúmenes × k³.'],
        practica=[numerica('Si amplío al triple, ¿por cuánto se multiplica el área?', 9), numerica('Un cubo se amplía con k = 2. ¿Por cuánto se multiplica su volumen?', 8)],
        taller=[unica('Al ampliar un triángulo, sus ángulos…', 'se conservan', ['se duplican', 'cambian']),
                numerica('Un mapa a escala reduce longitudes a 1/1000. ¿Por cuánto se reduce el área? (escribe el denominador)', 1000000),
                abierta('Dibuja dos triángulos semejantes con razón 2 y verifica la relación entre sus áreas.', 6)])

    U[7] = unidad(
        tema='Trayectorias y movimiento',
        objetivo='Describir analíticamente trayectorias y desplazamientos y representar gráficamente la variación del movimiento.',
        explora=[texto('Un bus sale a 40 km/h y una moto 1 hora después a 60 km/h por la misma vía. ¿Cuándo la alcanza?')],
        aprende=[texto('Posición del bus: d = 40t. Posición de la moto: d = 60(t − 1). Se igualan: 40t = 60t − 60 → <b>t = 3 h</b>, a 120 km.'),
                 grafica({'x': [0, 5], 'y': [0, 200], 'nombre_x': 'horas', 'nombre_y': 'km', 'elementos': [
                     {'t': 'funcion', 'expr': '40x', 'desde': '0', 'hasta': '5', 'nombre': 'bus'},
                     {'t': 'funcion', 'expr': '60(x-1)', 'desde': '1', 'hasta': '4.3', 'nombre': 'moto', 'color': '#dc2626'},
                     {'t': 'punto', 'x': 3, 'y': 120, 'nombre': 'alcance'}]}, 50, 'Posición contra tiempo'),
                 texto('En la gráfica posición–tiempo, la <b>pendiente</b> es la velocidad: la recta de la moto es más empinada.')],
        recuerda=['Pendiente de posición–tiempo = velocidad.', 'Dos móviles se encuentran donde se cruzan sus rectas.'],
        practica=[numerica('¿A cuántas horas la moto alcanza al bus?', 3, 'h'), numerica('¿A cuántos km del inicio?', 120, 'km')],
        taller=[numerica('Un ciclista va a 15 km/h. ¿Qué distancia recorre en 2,5 h?', F(75, 2), 'km'), unica('Una recta horizontal en posición–tiempo indica que…', 'está quieto', ['va muy rápido']),
                abierta('Camina por el patio a distintas velocidades y dibuja la gráfica posición–tiempo de tu recorrido.', 6)])

    U[8] = unidad(
        tema='Modelar situaciones con expresiones y gráficas',
        objetivo='Usar expresiones numéricas, algebraicas y gráficas para describir situaciones y tomar decisiones.',
        explora=[texto('Plan A: $30 000 fijos al mes. Plan B: $10 000 más $2 000 por cada día de uso. ¿Cuál conviene?')],
        aprende=[texto('A = 30 000. B = 10 000 + 2 000d. Son iguales cuando 10 000 + 2 000d = 30 000 → <b>d = 10</b> días.'),
                 grafica({'x': [0, 20], 'y': [0, 55000], 'nombre_x': 'días', 'nombre_y': '$', 'elementos': [
                     {'t': 'funcion', 'expr': '30000', 'desde': '0', 'hasta': '20', 'nombre': 'Plan A'},
                     {'t': 'funcion', 'expr': '10000+2000x', 'desde': '0', 'hasta': '20', 'nombre': 'Plan B', 'color': '#dc2626'}]}, 50, 'Comparación de planes'),
                 texto('Decisión: si uso menos de 10 días, conviene <b>B</b>; si uso más, conviene <b>A</b>.')],
        recuerda=['Las letras representan cantidades que varían.', 'El punto de corte es donde las opciones cuestan lo mismo.'],
        practica=[numerica('¿Cuánto cuesta el plan B con 5 días?', 20000, 'pesos'), unica('Con 15 días de uso conviene…', 'el plan A', ['el plan B'])],
        taller=[numerica('Con 20 días, ¿cuánto se ahorra con el plan A?', 20000, 'pesos'), numerica('Resuelve 10 000 + 2 000d = 24 000.', 7),
                abierta('Compara dos tarifas reales de tu región (internet, transporte) con una gráfica y decide cuál conviene.', 6)])

    U[9] = unidad(
        tema='Procesos inductivos y conjeturas',
        objetivo='Explorar, organizar resultados, proponer patrones y expresar conjeturas verbal y simbólicamente.',
        explora=[texto('¿Cuántas diagonales tiene un pentágono? ¿Y un hexágono? ¿Y un polígono de n lados?')],
        aprende=[tabla([['Lados (n)', '3', '4', '5', '6', '7'], ['Diagonales', '0', '2', '5', '9', '14']]),
                 texto('Conjetura: desde cada vértice salen n − 3 diagonales, y cada diagonal se cuenta dos veces: <b>D = n(n − 3)/2</b>.'),
                 texto('Comprobación: n = 6 → 6·3/2 = 9 ✓. Para n = 10: 10·7/2 = <b>35</b>.')],
        recuerda=['Exploro casos, organizo en tabla, conjeturo y compruebo.'],
        practica=[numerica('¿Cuántas diagonales tiene un octágono?', 20), numerica('¿Cuántas diagonales tiene un polígono de 10 lados?', 35)],
        taller=[numerica('En una reunión de 6 personas todos se saludan una vez. ¿Cuántos saludos hay? (n(n−1)/2)', 15),
                numerica('Suma de los primeros 10 impares (conjetura: n²).', 100), unica('La suma de los ángulos internos de un polígono de n lados es…', '180(n − 2)', ['180n', '360']),
                abierta('Explora cuántos cuadrados (de todos los tamaños) hay en una cuadrícula de 3 × 3 y conjetura para n × n.', 6)])

    U[10] = unidad(
        tema='Comparo dos grupos: diagrama de caja',
        objetivo='Diseñar un estudio que compare dos grupos de datos usando diagramas de caja, medidas de tendencia central, de variación y de localización.',
        explora=[texto('¿Leen más libros al año los estudiantes de 9.º A o los de 9.º B?')],
        aprende=[imagen('d-caja-2-4-6-8-11-0-12-1', 55, '9.º A: mín 2, Q1 4, mediana 6, Q3 8, máx 11'),
                 texto('El <b>diagrama de caja</b> muestra el mínimo, el primer cuartil (Q1), la mediana, el tercer cuartil (Q3) y el máximo.'),
                 texto('<b>Rango</b> = máx − mín. <b>Rango intercuartílico</b> = Q3 − Q1 (el 50 % central de los datos). Si la caja es más ancha, los datos están más dispersos.'),
                 imagen('d-caja-1-2-3-5-12-0-12-1', 55, '9.º B: mediana 3, más dispersión arriba')],
        recuerda=['Mediana: el 50 % de los datos está por debajo.', 'Rango intercuartílico = Q3 − Q1.'],
        practica=[numerica('Rango intercuartílico de 9.º A.', 4), numerica('Rango de 9.º B.', 11)],
        taller=[unica('¿Qué grupo tiene mayor mediana?', '9.º A', ['9.º B']), numerica('Rango de 9.º A.', 9),
                unica('El 50 % central de los datos está entre…', 'Q1 y Q3', ['mín y Q1', 'Q3 y máx']),
                abierta('Diseña una encuesta para comparar dos grupos, define la población y la muestra, y construye los diagramas de caja.', 8)])

    U[11] = unidad(
        tema='Técnicas de conteo: con y sin reemplazo',
        objetivo='Contar los resultados posibles con y sin reemplazo usando diagramas de árbol, permutaciones y combinaciones, y calcular probabilidades.',
        explora=[texto('Con los dígitos 1, 2, 3 y 4, ¿cuántos números de dos cifras se forman si se pueden repetir? ¿Y si no?')],
        aprende=[texto('<b>Con reemplazo</b> (se pueden repetir): 4 × 4 = <b>16</b>. <b>Sin reemplazo</b>: 4 × 3 = <b>12</b>.'),
                 tabla([['Técnica', 'Cuándo', 'Fórmula'], ['Principio multiplicativo', 'elecciones sucesivas', 'm × n'], ['Permutación', 'importa el orden', 'n!/(n − r)!'],
                        ['Combinación', 'no importa el orden', 'n!/(r!(n − r)!)']]),
                 texto('Elegir 2 representantes entre 5: C(5,2) = 10. Elegir presidente y vicepresidente entre 5: P(5,2) = 20.')],
        recuerda=['¿Importa el orden? Permutación. ¿No importa? Combinación.', 'Sin reemplazo, las opciones disminuyen.'],
        practica=[numerica('Números de dos cifras sin repetir con 1, 2, 3, 4.', 12), numerica('Combinaciones de 5 elementos tomados de a 2.', 10)],
        taller=[numerica('Presidente y vicepresidente entre 5 candidatos.', 20), numerica('¿De cuántas formas se ordenan 4 libros en un estante? (4!)', 24),
                unica('Sacar 2 balotas de una bolsa sin devolver la primera es un experimento…', 'sin reemplazo', ['con reemplazo']),
                unica('Bolsa con 3 rojas y 2 azules, saco 2 sin reemplazo. P(dos rojas) =', '3/10', ['9/25', '1/2', '2/5']),
                abierta('¿Cuántas placas de carro de 3 letras y 3 números hay en Colombia (26 letras)? Explica tu cálculo.', 4)])
    return U
