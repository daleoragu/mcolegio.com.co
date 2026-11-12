"""Matemáticas 2.º: una guía y una ficha por cada uno de los 11 DBA (V.2). Problemas de la tienda, la finca y el colegio;
la multiplicación como grupos iguales (cada fila de la colección es un grupo). Borradores para que el docente revise."""
from .base import abierta, coleccion, imagen, numerica, pictograma, recuadro, tabla, texto, unica, vf
from .matematicas_1 import u


def unidades():
    U = {}

    U[1] = u(
        tema='Problemas de juntar, quitar, comparar y repetir',
        objetivo='Resolver problemas de suma, resta y multiplicaciones sencillas con cantidades, medidas y tiempo.',
        explora=[imagen('m2-tienda-dona', 60, 'La tienda de doña Rosa'),
                 texto('Doña Rosa tenía 35 panes y vendió 12. ¿Cuántos le quedan? ¿Cómo lo sabes?')],
        aprende=[texto('<b>Juntar</b> (sumar): 23 + 14 = 37. <b>Quitar</b> (restar): 35 − 12 = 23. '
                       '<b>Comparar</b>: Sofi tiene 18 láminas y Tomás 12; Sofi tiene 18 − 12 = <b>6 más</b>.'),
                 texto('<b>Repetir</b> (multiplicar): 4 bolsas con 3 naranjas cada una.'),
                 imagen('m2-bolsa-naranjas', 15), coleccion('m1-naranja', 12, 3),
                 texto('3 + 3 + 3 + 3 = 12, y se escribe <b>4 × 3 = 12</b> (4 grupos de 3).'),
                 tabla([['¿Qué pasa?', 'Operación', 'Ejemplo'], ['Juntamos', '+', '23 + 14 = 37'], ['Quitamos', '−', '35 − 12 = 23'],
                        ['Comparamos', '−', '18 − 12 = 6'], ['Repetimos grupos iguales', '×', '4 × 3 = 12']])],
        recuerda=['Lee el problema dos veces y piensa: ¿junto, quito, comparo o repito?', 'Multiplicar es sumar grupos iguales.'],
        practica=[numerica('Doña Rosa tenía 35 panes y vendió 12. ¿Cuántos le quedan?', 35 - 12),
                  coleccion('m1-manzana', 10, 5), numerica('2 canastas con 5 manzanas cada una. ¿Cuántas manzanas son?', 2 * 5)],
        taller=[numerica('En el bus van 24 personas y se suben 15. ¿Cuántas van ahora?', 24 + 15),
                numerica('Sofi mide 118 cm y Tomás 125 cm. ¿Cuántos centímetros más mide Tomás?', 125 - 118, 'cm'),
                numerica('Una película dura 90 minutos. Ya vimos 40. ¿Cuántos minutos faltan?', 90 - 40, 'min'),
                coleccion('m1-huevo', 15, 5), numerica('3 nidos con 5 huevos cada uno. ¿Cuántos huevos hay?', 3 * 5),
                numerica('Tomás tenía algunas canicas, ganó 8 y ahora tiene 20. ¿Cuántas tenía?', 20 - 8),
                abierta('Inventa un problema de suma con las cosas de tu lonchera y resuélvelo.', 4)])

    U[2] = u(
        tema='Estrategias para calcular: agrupar, repartir y estimar',
        objetivo='Calcular y estimar sumas, restas, multiplicaciones y repartos usando dibujos, grupos y descomposiciones.',
        explora=[coleccion('m1-galleta', 12, 4), texto('Hay 12 galletas para 3 amigos. ¿Cuántas le tocan a cada uno si reparten igual?')],
        aprende=[texto('<b>Repartir</b>: damos una galleta a cada uno, luego otra, y así hasta que se acaben. A cada uno le tocan <b>4</b>. '
                       'Se escribe <b>12 ÷ 3 = 4</b>.'),
                 texto('<b>Descomponer</b> para sumar: 36 + 25 = 30 + 20 + 6 + 5 = 50 + 11 = <b>61</b>.'),
                 imagen('d-bloques-3-6', 18), imagen('d-bloques-2-5', 15),
                 texto('<b>Estimar</b> es calcular más o menos: 49 + 32 es cerca de 50 + 30 = 80.'),
                 texto('<b>Contar de 2 en 2, de 5 en 5 y de 10 en 10</b> ayuda a multiplicar: 5 × 4 = 5, 10, 15, 20.')],
        recuerda=['Repartir en partes iguales es dividir.', 'Puedo descomponer en decenas y unidades para sumar más fácil.'],
        practica=[numerica('Reparte 15 dulces entre 5 niños por igual. ¿Cuántos le tocan a cada uno?', 15 // 5),
                  numerica('Calcula 36 + 25 descomponiendo.', 36 + 25)],
        taller=[numerica('Calcula 47 + 28.', 47 + 28), numerica('Calcula 63 − 21.', 63 - 21),
                numerica('¿Cuánto es 5 × 3? (cuenta de 5 en 5)', 15),
                numerica('20 lápices se reparten en 4 cajas iguales. ¿Cuántos van en cada caja?', 20 // 4),
                unica('49 + 32 es más o menos…', '80', ['50', '60', '100']),
                abierta('Dibuja cómo repartirías 10 fresas entre 2 amigos.', 6)])

    U[3] = u(
        tema='Números hasta 999: comparo y ordeno',
        objetivo='Leer, escribir, comparar y ordenar números de tres cifras usando centenas, decenas y unidades, billetes y monedas.',
        explora=[imagen('m2-alcancia', 18), imagen('d-billetes-1000-2000-5000', 55),
                 texto('Sofi ahorró estos billetes en su alcancía. ¿Cuánto dinero tiene?')],
        aprende=[texto('10 decenas forman 1 <b>centena</b>. En <b>352</b> hay 3 centenas, 5 decenas y 2 unidades: 300 + 50 + 2.'),
                 tabla([['Centenas', 'Decenas', 'Unidades', 'Número'], ['3', '5', '2', '352'], ['4', '0', '7', '407'], ['1', '9', '0', '190']]),
                 texto('Para <b>comparar</b>, miramos primero las centenas: 352 <b>&gt;</b> 299 porque 3 centenas es más que 2. '
                       'Si las centenas son iguales, miramos las decenas: 352 <b>&lt;</b> 370.'),
                 texto('Si a dos números les sumamos lo mismo, el mayor sigue siendo el mayor: 15 &gt; 9 y también 15 + 5 &gt; 9 + 5.'),
                 imagen('d-billetes-1000-1000-2000', 50, '1000 + 1000 + 2000 = 4000 pesos')],
        recuerda=['&gt; es «mayor que»; &lt; es «menor que».', 'Las centenas son las que más pesan al comparar.'],
        practica=[unica('¿Cuál número es mayor?', '415', ['398', '409', '154']),
                  numerica('¿Cuántas decenas tiene el número 352? (la cifra del medio)', 5)],
        taller=[numerica('Escribe el número: 6 centenas, 2 decenas y 8 unidades.', 628),
                unica('Ordena de menor a mayor: ¿cuál va primero?', '209', ['290', '920', '902']),
                unica('¿Qué signo va? 506 ___ 560', '<', ['>', '=']),
                imagen('d-billetes-2000-2000-5000', 50), numerica('¿Cuánto dinero hay?', 2000 + 2000 + 5000, 'pesos'),
                vf('Si 20 > 15, entonces 20 + 3 > 15 + 3.', True),
                abierta('Escribe tres números de tres cifras y ordénalos de mayor a menor.', 3)])

    U[4] = u(
        tema='¿Qué medimos y con qué?',
        objetivo='Escoger el instrumento y la unidad adecuados para medir longitud, superficie, peso, capacidad y tiempo, y estimar medidas.',
        explora=[imagen('m2-balanza-frutas', 35, 'La balanza de la plaza'), texto('¿Qué pesa más, la piña o los tres mangos? ¿Cómo lo sabes?')],
        aprende=[tabla([['Quiero medir…', 'Uso…', 'Unidad'], ['lo largo', 'regla, metro', 'centímetros, metros'], ['lo pesado', 'balanza, pesa', 'kilos, gramos'],
                        ['lo que le cabe', 'jarra, vaso', 'litros'], ['cuánto dura', 'reloj', 'horas, minutos'], ['la superficie', 'cuadritos', 'cuadritos']]),
                 imagen('m2-jarra', 15, 'La jarra: 1 litro'), imagen('m2-metro-costura', 20, 'El metro de costura'),
                 texto('La <b>superficie</b> es lo que ocupa algo plano. La medimos contando cuadritos:'),
                 imagen('d-cuadros-4-3', 35, 'Esta figura ocupa 12 cuadritos'),
                 texto('<b>Estimar</b> es decir una medida aproximada: «la puerta mide como 2 metros».')],
        recuerda=['Cada magnitud tiene su instrumento.', 'Primero estimo, después mido y comparo.'],
        practica=[unica('¿Con qué medimos cuánto pesa un bulto de papa?', 'Con una balanza', ['Con una regla', 'Con un reloj']),
                  imagen('d-cuadros-4-3', 30), numerica('¿Cuántos cuadritos ocupa la figura?', 12)],
        taller=[unica('¿Con qué medimos cuánto dura el recreo?', 'Con un reloj', ['Con una jarra', 'Con una balanza']),
                unica('¿En qué unidad medimos el jugo de una jarra?', 'Litros', ['Metros', 'Kilos']),
                imagen('d-cuadros-5-2', 30), numerica('¿Cuántos cuadritos ocupa esta figura?', 10),
                unica('¿Cuánto mide más o menos un lápiz nuevo?', '19 centímetros', ['19 metros', '2 centímetros', '100 metros']),
                abierta('Estima cuántas cuartas mide tu mesa. Luego mídela. ¿Te acercaste?', 3)])

    U[5] = u(
        tema='Mido con el metro y leo el reloj',
        objetivo='Medir con unidades no convencionales y convencionales (centímetros, metros) y comparar duraciones leyendo el reloj.',
        explora=[imagen('m1-medir-pasos', 40), texto('Sofi midió el salón con pasos y le dio 12. Tomás midió con pasos y le dio 10. ¿Por qué?')],
        aprende=[texto('Los pasos y las cuartas cambian de persona a persona. Por eso usamos el <b>metro</b>: 1 metro = 100 centímetros.'),
                 imagen('d-regla-15-12', 70, 'Este lápiz mide 12 centímetros'),
                 texto('El <b>reloj</b>: la manecilla corta marca la <b>hora</b> y la larga marca los <b>minutos</b>.'),
                 imagen('d-reloj-8-0', 20, 'Las 8 en punto'), imagen('d-reloj-9-30', 20, 'Las 9 y media'),
                 texto('De las 8 a las 9 y media pasa <b>1 hora y media</b>.')],
        recuerda=['1 metro = 100 centímetros.', 'Media hora son 30 minutos.'],
        practica=[imagen('d-reloj-3-0', 18), unica('¿Qué hora marca?', 'Las 3 en punto', ['Las 12 y 15', 'Las 6']),
                  numerica('¿Cuántos centímetros tiene un metro?', 100, 'cm')],
        taller=[imagen('d-reloj-10-30', 18), unica('¿Qué hora marca?', 'Las 10 y media', ['Las 6 y 10', 'Las 10 en punto']),
                unica('¿Qué dura más?', 'Una clase de 1 hora', ['Lavarse los dientes', 'Un estornudo']),
                imagen('d-regla-15-9', 60), numerica('¿Cuánto mide el lápiz?', 9, 'cm'),
                numerica('El recreo empieza a las 10 y termina a las 10 y media. ¿Cuántos minutos dura?', 30, 'min'),
                abierta('Mide con una cuerda el largo de tu cuaderno y compáralo con la regla.', 3)])

    U[6] = u(
        tema='Figuras y cuerpos geométricos',
        objetivo='Reconocer figuras planas por su número de lados y diferenciarlas de los cuerpos geométricos.',
        explora=[imagen('d-poligonos', 70), texto('Cuenta los lados de cada figura. ¿Cuál tiene más lados?')],
        aprende=[tabla([['Figura', 'Lados', 'Puntas (vértices)'], ['Triángulo', '3', '3'], ['Cuadrado', '4', '4'], ['Pentágono', '5', '5'], ['Hexágono', '6', '6']]),
                 texto('Las <b>figuras planas</b> se dibujan en el papel. Los <b>cuerpos geométricos</b> ocupan espacio y tienen caras.'),
                 imagen('d-solidos-n', 80),
                 texto('El <b>cubo</b> tiene 6 caras cuadradas. La <b>pirámide</b> tiene caras triangulares. La esfera y el cilindro <b>ruedan</b>.')],
        recuerda=['La figura se nombra por su número de lados.', 'Las caras de los cuerpos son figuras planas.'],
        practica=[imagen('d-poligonos', 60), unica('¿Cuál figura es el pentágono?', 'C', ['A', 'B', 'D']),
                  numerica('¿Cuántas caras tiene un cubo?', 6)],
        taller=[numerica('¿Cuántos lados tiene un hexágono?', 6),
                unica('¿Qué cuerpo rueda?', 'La esfera', ['El cubo', 'El prisma']),
                unica('Las caras de un dado son…', 'cuadrados', ['triángulos', 'círculos']),
                vf('Un triángulo tiene 4 lados.', False),
                abierta('Busca en tu casa algo con forma de cubo, de cilindro y de esfera. Dibújalos y escribe su nombre.', 6)])

    U[7] = u(
        tema='Líneas horizontales, verticales, paralelas y perpendiculares',
        objetivo='Reconocer las posiciones de las líneas en objetos y lugares, y usarlas para describir desplazamientos.',
        explora=[imagen('m2-ventana', 25), texto('Mira la reja: ¿hay líneas acostadas? ¿Hay líneas de pie?')],
        aprende=[imagen('d-posiciones', 75),
                 texto('<b>A. Horizontal</b>: acostada, como el horizonte. <b>B. Vertical</b>: de pie, como un poste. '
                       '<b>C. Paralelas</b>: nunca se juntan, como los rieles. <b>D. Perpendiculares</b>: se cruzan formando una esquina recta.'),
                 imagen('m2-rieles', 35, 'Los rieles son paralelos'), imagen('m2-cruce-calles', 35, 'Las calles se cruzan perpendiculares'),
                 texto('Para llegar a la tienda: camino derecho por la calle (horizontal en el mapa), y en la esquina giro y subo (vertical).')],
        recuerda=['Paralelas: nunca se encuentran.', 'Perpendiculares: se cruzan haciendo una esquina recta.'],
        practica=[imagen('d-posiciones', 60), unica('¿Cuáles son paralelas?', 'C', ['A', 'B', 'D']),
                  unica('Un poste de la luz es una línea…', 'vertical', ['horizontal', 'curva'])],
        taller=[unica('Los bordes de arriba y abajo de tu cuaderno son…', 'paralelos', ['perpendiculares', 'curvos']),
                unica('La esquina de una hoja la forman dos líneas…', 'perpendiculares', ['paralelas', 'iguales']),
                unica('El piso es…', 'horizontal', ['vertical']),
                abierta('Dibuja un camino desde tu casa a la escuela con líneas horizontales y verticales y explica cómo se va.', 6)])

    U[8] = u(
        tema='Patrones y números escondidos',
        objetivo='Descubrir patrones y usar la relación entre la suma y la resta para hallar un número desconocido.',
        explora=[imagen('m2-collar', 35, 'El collar de Sofi'), texto('¿Qué color sigue en el collar? ¿Cómo lo sabes?')],
        aprende=[texto('Un <b>patrón</b> es algo que se repite con una regla: rojo, azul, azul, rojo, azul, azul…'),
                 texto('Patrones con números: 2, 4, 6, 8, … (suma 2). 50, 45, 40, … (resta 5).'),
                 texto('La suma y la resta son <b>operaciones inversas</b>: si 8 + 5 = 13, entonces 13 − 5 = 8.'),
                 texto('Para hallar el número escondido: ___ + 7 = 15 → 15 − 7 = <b>8</b>.'),
                 imagen('d-balanza-8+7-15-0', 40)],
        recuerda=['Para encontrar un patrón, busco qué se repite o cuánto cambia.', 'Lo que la suma hace, la resta lo deshace.'],
        practica=[numerica('¿Qué número sigue? 10, 20, 30, 40, ___', 50), numerica('Completa: ___ + 7 = 15', 8)],
        taller=[numerica('¿Qué número sigue? 3, 6, 9, 12, ___', 15), numerica('¿Qué número sigue? 50, 45, 40, ___', 35),
                numerica('Completa: 23 − ___ = 20', 3), numerica('Si 9 + 6 = 15, ¿cuánto es 15 − 6?', 9),
                abierta('Inventa un patrón con figuras o colores y dibújalo.', 4)])

    U[9] = u(
        tema='Secuencias y operaciones que faltan',
        objetivo='Encontrar números u operaciones que faltan en secuencias e igualdades, y escribir un número de varias formas.',
        explora=[texto('En una carrera de relevos cada niño corre 5 metros más que el anterior: 10, 15, 20, ___. ¿Cuánto corre el siguiente?')],
        aprende=[texto('Un número se puede escribir de muchas formas: <b>20</b> = 10 + 10 = 4 × 5 = 25 − 5.'),
                 texto('En una cadena de cálculos podemos descubrir la operación que falta: 6 → <b>+ 4</b> → 10 → <b>× 2</b> → 20.'),
                 texto('<b>Ensayo y error</b>: pruebo un número, miro si funciona y si no, pruebo otro.'),
                 tabla([['Entrada', '3', '5', '7', '9'], ['Salida (+ 4)', '7', '9', '11', '13']])],
        recuerda=['Pruebo, compruebo y corrijo.', 'Sumar en otro orden da lo mismo: 3 + 5 = 5 + 3.'],
        practica=[numerica('¿Qué número falta? 10, 15, 20, ___', 25), unica('¿Qué operación convierte 6 en 12?', '× 2', ['+ 2', '− 6', '× 6'])],
        taller=[numerica('Completa: 4 + 5 = 5 + ___', 4), numerica('Completa: 10 + 10 = ___ × 5', 4),
                unica('¿Cuál es otra forma de escribir 12?', '6 + 6', ['10 + 3', '15 − 2']),
                numerica('Si la regla es «suma 4», ¿qué sale cuando entra 9?', 13),
                abierta('Escribe el número 30 de tres formas diferentes.', 3)])

    U[10] = u(
        tema='Pictogramas con escala y gráficos de puntos',
        objetivo='Organizar datos en tablas de conteo, pictogramas donde cada dibujo vale varios y gráficos de puntos, y responder preguntas.',
        explora=[texto('En 2.º preguntamos: <b>¿qué fruta llevas en la lonchera?</b> Votaron 26 niños. ¿Cómo lo mostramos sin dibujar 26 frutas?')],
        aprende=[imagen('d-conteo-mango.10-banano.6-naranja.4-manzana.6', 55, 'Tabla de conteo'),
                 texto('En un pictograma <b>con escala</b>, cada dibujo vale más de uno. Aquí <b>cada dibujo vale 2 votos</b>:'),
                 pictograma([('m1-mango', 5), ('m1-banano', 3), ('m1-naranja', 2), ('m1-manzana', 3)], 70, 'Cada dibujo = 2 votos'),
                 texto('El mango tiene 5 dibujos: 5 × 2 = <b>10 votos</b>.'),
                 texto('En un <b>gráfico de puntos</b>, cada punto es un dato:'),
                 imagen('d-puntos-lunes.3-martes.5-miercoles.2-jueves.4-viernes.6', 60, 'Libros leídos en la semana')],
        recuerda=['Mira cuánto vale cada dibujo antes de contar.', 'En el gráfico de puntos, la columna más alta es la que más se repite.'],
        practica=[numerica('Si cada dibujo vale 2, ¿cuántos votos tiene el banano (3 dibujos)?', 6),
                  unica('En el gráfico de puntos, ¿qué día se leyeron más libros?', 'El viernes', ['El lunes', 'El miércoles'])],
        taller=[numerica('¿Cuántos votos tiene la naranja (2 dibujos de 2)?', 4),
                unica('¿Qué fruta tiene más votos?', 'El mango', ['La manzana', 'El banano']),
                numerica('En el gráfico de puntos, ¿cuántos libros se leyeron el martes?', 5),
                numerica('¿Cuántos libros se leyeron el lunes y el jueves juntos?', 3 + 4),
                abierta('Pregunta a 10 compañeros su color favorito y haz un gráfico de puntos.', 6)])

    U[11] = u(
        tema='¿Seguro, posible o imposible?',
        objetivo='Diferenciar situaciones seguras, posibles e imposibles y predecir lo que puede pasar a partir de lo que observo.',
        explora=[imagen('m2-nubes', 40), texto('¿Va a llover hoy? ¿Estás seguro? ¿Qué te hace pensar eso?')],
        aprende=[tabla([['Seguro', 'Posible', 'Imposible'], ['Mañana sale el sol', 'Hoy llueve por la tarde', 'Una vaca vuela sola'],
                        ['Después del lunes viene el martes', 'Me gane una rifa', 'Un pez camine en la calle']]),
                 imagen('m2-bolsa-canicas', 25, 'En la bolsa solo hay canicas rojas'),
                 texto('Si saco una canica: es <b>seguro</b> que sea roja e <b>imposible</b> que sea azul.'),
                 imagen('m2-moneda-aire', 35, 'Al lanzar una moneda puede caer cara o sello: no sabemos cuál')],
        recuerda=['Seguro: siempre pasa. Posible: puede pasar. Imposible: nunca pasa.'],
        practica=[unica('Sacar una canica azul de una bolsa con solo canicas rojas es…', 'imposible', ['seguro', 'posible']),
                  unica('Que llueva esta tarde es…', 'posible', ['seguro', 'imposible'])],
        taller=[unica('Al lanzar un dado, sacar un 7 es…', 'imposible', ['posible', 'seguro']),
                unica('Al lanzar un dado, sacar un número menor que 7 es…', 'seguro', ['imposible', 'posible']),
                unica('Al lanzar una moneda, que caiga cara es…', 'posible', ['seguro', 'imposible']),
                unica('Si el cielo está muy nublado, es más probable que…', 'llueva', ['nieve en Cartagena', 'salga el arcoíris de noche']),
                abierta('Escribe una cosa segura, una posible y una imposible de tu día.', 4)])
    return U
