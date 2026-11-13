"""Matemáticas 1.º: una guía y una ficha por cada uno de los 10 DBA (V.2). Lenguaje de primero: frases cortas, mucha
imagen, contar, encerrar, unir y colorear. Las cantidades se dibujan exactas (coleccion) con la imagen suelta del banco.
Borradores para que el docente revise."""
from .base import abierta, coleccion, imagen, numerica, pictograma, tabla, texto, unica, vf

MOMENTOS = (('1. Miro y converso', 'Observa la imagen y conversa con tu profe y tus compañeros.'),
            ('2. Aprendo con Sofi y Tomás', ''),
            ('3. Juego y practico', 'Resuelve con ayuda de tu profe.'))
FICHA = 'Escucha a tu profe, cuenta con tu dedo y escribe o marca la respuesta.'


def u(**k):
    return dict(k, momentos=MOMENTOS, nombre_taller='Mi ficha', indicacion_taller=FICHA)


def unidades():
    U = {}

    U[1] = u(
        tema='Los números están en todas partes',
        objetivo='Descubrir para qué sirven los números: para contar, para ordenar, para medir, para nombrar y para comprar.',
        explora=[imagen('m1-uso-tienda', 60, 'La tienda del colegio'),
                 texto('¿Qué números ves en la tienda del colegio? ¿Para qué sirven?')],
        aprende=[texto('Los números nos ayudan de muchas formas:'),
                 tabla([['Para…', 'Ejemplo'], ['Contar', 'Tengo 5 lápices'], ['Ordenar', 'Sofi llegó primero (1.º)'],
                        ['Medir', 'Tomás mide 115 centímetros'], ['Nombrar', 'El jugador número 10'], ['Comprar', 'El jugo cuesta $500']]),
                 coleccion('m1-lapiz', 5), texto('Contar: tengo <b>5</b> lápices.'),
                 imagen('m1-uso-medir', 30, 'Medir: Sofi mide su estatura'),
                 imagen('m1-uso-podio', 45, 'Primero, segundo y tercero'),
                 imagen('m1-uso-camiseta', 30, 'El número de la camiseta es un nombre: no se cuenta'),
                 imagen('d-monedas-100-200-500', 55, 'Con monedas compramos en la tienda')],
        recuerda=['Hay números para contar, para ordenar, para medir y para nombrar.', 'Si junto cosas, sumo. Si quito cosas, resto.'],
        practica=[coleccion('m1-manzana', 4), numerica('Sofi tiene estas manzanas. ¿Cuántas son?', 4),
                  unica('El número 10 en la camiseta del jugador sirve para…', 'nombrarlo', ['contar', 'medir', 'comprar'])],
        taller=[coleccion('m1-balon', 6), numerica('¿Cuántos balones hay?', 6),
                coleccion('m1-pez', 3), numerica('Había 3 peces y llegaron 2 más. ¿Cuántos peces hay ahora?', 3 + 2),
                unica('¿Quién llegó de primero a la meta en una carrera?', 'El que llegó antes que todos', ['El más alto', 'El último', 'El más rápido al salir']),
                imagen('d-monedas-100-100-200', 45), numerica('¿Cuántos pesos hay en estas monedas?', 100 + 100 + 200, 'pesos'),
                abierta('Dibuja un lugar de tu casa donde veas números (el reloj, el control, el calendario…).', 6)])

    U[2] = u(
        tema='Cuento, junto y quito',
        objetivo='Contar de 1 en 1, de 2 en 2 y de 5 en 5, y resolver problemas de juntar, quitar y completar.',
        explora=[imagen('m1-canicas-juego', 60, 'Sofi y Tomás juegan canicas'),
                 texto('Sofi tiene 4 canicas y Tomás tiene 3. Si las juntan, ¿cuántas tienen?')],
        aprende=[coleccion('m1-canica', 4), texto('<b>4</b> canicas de Sofi'), coleccion('m1-canica', 3), texto('<b>3</b> canicas de Tomás'),
                 texto('Juntamos: <b>4 + 3 = 7</b>. Contamos desde el 4: cinco, seis, siete.'),
                 imagen('d-recta-0-10-s4a7', 70, 'En la recta saltamos del 4 al 7'),
                 texto('Contar de 2 en 2 es más rápido: 2, 4, 6, 8, 10.'), coleccion('m1-mariposa', 3, 3),
                 texto('Cada mariposa tiene 2 alas: 2, 4, 6. ¡Son 6 alas!')],
        recuerda=['Juntar es sumar (+). Quitar es restar (−).', 'Puedo contar con mis dedos, con dibujos o con la recta numérica.'],
        practica=[imagen('m1-cable-pajaros', 45, 'El cable de luz'), coleccion('m1-pajaro', 6), numerica('En el cable hay 6 pájaros. Se van volando 2. ¿Cuántos quedan?', 6 - 2),
                  numerica('Cuenta de 5 en 5: 5, 10, 15, … ¿qué número sigue?', 20)],
        taller=[coleccion('m1-gallina', 5), numerica('En la finca hay 5 gallinas y llegan 4 más. ¿Cuántas hay?', 5 + 4),
                coleccion('m1-huevo', 8), numerica('Había 8 huevos y se rompieron 3. ¿Cuántos quedan?', 8 - 3),
                coleccion('m1-carrito', 6, 6), numerica('Tomás tiene 6 carritos. ¿Cuántos le faltan para tener 9?', 9 - 6),
                coleccion('m1-vaca', 4), numerica('En la finca hay 4 vacas y 5 gallinas. ¿Cuántos animales hay?', 4 + 5),
                coleccion('m1-flor', 3, 3), numerica('Cada flor tiene 5 pétalos. ¿Cuántos pétalos hay en total? (5, 10, …)', 15),
                numerica('Cuenta de 2 en 2: 2, 4, 6, 8, … ¿qué número sigue?', 10)])

    U[3] = u(
        tema='Decenas y unidades',
        objetivo='Armar y desarmar números de dos cifras con decenas (grupos de 10) y unidades.',
        explora=[imagen('d-paquetes-2-3', 55, 'Lápices amarrados de a 10 y lápices sueltos'),
                 texto('La profe amarró los lápices de 10 en 10. ¿Cuántos lápices hay en total?')],
        aprende=[texto('Un grupo de 10 es una <b>decena</b>. Los sueltos son <b>unidades</b>.'),
                 texto('2 paquetes de 10 y 3 sueltos: 10, 20, 21, 22, 23. Son <b>23</b> lápices.'),
                 imagen('d-bloques-3-4', 30, '3 decenas y 4 unidades = 34'),
                 tabla([['Decenas', 'Unidades', 'Número'], ['3', '4', '34'], ['2', '3', '23'], ['5', '0', '50']]),
                 texto('<b>Diez más</b>: del 34 al 44. <b>Diez menos</b>: del 34 al 24.'),
                 imagen('d-tabla100-24-34-44', 45, 'En la tabla, diez más es la casilla de abajo'),
                 imagen('d-marco-8-5', 35, 'Paso por el diez: 8 + 5 = 8 + 2 + 3 = 13')],
        recuerda=['10 unidades forman 1 decena.', 'En 47 hay 4 decenas y 7 unidades.'],
        practica=[imagen('d-bloques-2-6', 25), numerica('¿Qué número formaron los bloques?', 26),
                  numerica('¿Cuál es el número que está diez más que 52?', 62)],
        taller=[imagen('d-bloques-4-1', 30), numerica('¿Qué número es?', 41),
                imagen('d-paquetes-3-5', 55), numerica('¿Cuántos lápices hay?', 35),
                numerica('¿Cuántas decenas tiene el número 70?', 7),
                numerica('Diez menos que 38 es…', 28),
                imagen('d-marco-9-4', 35), numerica('Paso por el diez: 9 + 4 = ?', 13),
                unica('¿Qué pareja suma 10?', '6 y 4', ['5 y 4', '7 y 2', '8 y 3'])])

    U[4] = u(
        tema='Comparo: largo, alto, pesado y lleno',
        objetivo='Reconocer lo que se puede medir en los objetos y compararlos: más largo, más alto, más pesado, le cabe más.',
        explora=[imagen('m1-jirafa', 25), imagen('m1-conejo', 18),
                 texto('¿Quién es más alto, la jirafa o el conejo? ¿Cómo lo sabes?')],
        aprende=[imagen('d-lapices-8-5-11', 55, '¿Cuál lápiz es el más largo?'),
                 texto('Para comparar lo <b>largo</b>, ponemos los objetos uno al lado del otro, empezando en el mismo punto.'),
                 imagen('m1-elefante', 25), imagen('m1-raton', 12), texto('El elefante es <b>más pesado</b> que el ratón.'),
                 imagen('m1-balde', 20), imagen('m1-vaso', 12), texto('Al balde le <b>cabe más</b> agua que al vaso.'),
                 imagen('m1-tortuga', 20), texto('La tortuga es <b>más lenta</b> que el conejo.')],
        recuerda=['Podemos comparar lo largo, lo alto, lo pesado, lo que le cabe y lo rápido.', 'Para comparar el largo, empieza en la misma línea.'],
        practica=[imagen('d-lapices-8-5-11', 55), unica('¿Cuál lápiz es el más corto?', 'B', ['A', 'C']),
                  unica('¿Qué pesa más?', 'Una sandía', ['Una pluma', 'Una hoja', 'Un lápiz'])],
        taller=[unica('¿A cuál le cabe más agua?', 'A la olla', ['A la cuchara', 'A la tapa', 'Al pocillo pequeño']),
                unica('¿Qué es más largo?', 'Un bus', ['Un carro de juguete', 'Un zapato', 'Un lápiz']),
                imagen('d-lapices-6-9-4', 50), unica('Ordena del más largo al más corto: ¿cuál va primero?', 'B', ['A', 'C']),
                coleccion('m1-manzana', 5), coleccion('m1-fresa', 3),
                unica('¿Dónde hay más frutas: en las manzanas o en las fresas?', 'En las manzanas', ['En las fresas', 'Hay igual']),
                vf('Una tortuga es más rápida que un conejo.', False)])

    U[5] = u(
        tema='Mido con mi cuerpo y con la regla',
        objetivo='Medir largos con la mano, con los pasos y con la regla, y comparar las medidas.',
        explora=[imagen('m1-medir-cuartas', 50, 'Tomás mide su pupitre con cuartas'),
                 texto('¿Cuántas cuartas mide tu pupitre? ¿Te da lo mismo que a tu compañero?')],
        aprende=[texto('Podemos medir con la <b>mano</b> (cuartas), con los <b>pasos</b> o con los <b>pies</b>. Pero cada mano es distinta.'),
                 imagen('m1-medir-pasos', 45, 'Sofi mide el patio con pasos'),
                 texto('Por eso usamos la <b>regla</b>: mide igual para todos, en <b>centímetros</b>.'),
                 imagen('d-regla-12-7', 70, 'Este lápiz mide 7 centímetros'),
                 texto('Pon el lápiz en el <b>cero</b> y mira dónde termina.')],
        recuerda=['Para medir con la regla, empieza en el 0.', 'Una mano grande da menos cuartas que una mano pequeña.'],
        practica=[imagen('d-regla-12-9', 70), numerica('¿Cuántos centímetros mide el lápiz?', 9, 'cm'),
                  unica('Si mides la puerta con tus pasos y tu profe también, ¿a quién le dan más pasos?', 'A mí, porque mis pasos son más cortos',
                        ['A la profe', 'A los dos igual'])],
        taller=[imagen('d-regla-12-5', 70), numerica('¿Cuántos centímetros mide el lápiz?', 5, 'cm'),
                imagen('d-regla-12-11', 70), numerica('¿Y este lápiz?', 11, 'cm'),
                numerica('Un lápiz mide 11 cm y otro 5 cm. ¿Cuántos centímetros más largo es el primero?', 11 - 5, 'cm'),
                unica('¿Con qué medimos mejor el largo de un cuaderno?', 'Con la regla', ['Con el reloj', 'Con la balanza', 'Con un vaso']),
                abierta('Mide tu cuaderno con cuartas. ¿Cuántas te dieron? Dibuja tu mano.', 5)])

    U[6] = u(
        tema='Formas que veo a mi alrededor',
        objetivo='Reconocer figuras planas y sólidos en los objetos del entorno, y describir si son curvos o rectos, abiertos o cerrados.',
        explora=[imagen('m1-forma-lata', 15), imagen('m1-forma-caja', 18), imagen('m1-forma-cono', 12), imagen('m1-forma-dado', 15),
                 texto('¿Cuáles de estos objetos ruedan? ¿Cuáles tienen puntas?')],
        aprende=[imagen('d-figuras-n', 80, 'Figuras planas'),
                 texto('El <b>cuadrado</b> tiene 4 lados iguales. El <b>triángulo</b> tiene 3 lados. El <b>círculo</b> es curvo y no tiene puntas.'),
                 imagen('d-solidos-n', 85, 'Sólidos: tienen volumen y se pueden coger'),
                 texto('La lata es un <b>cilindro</b>, la caja es un <b>prisma</b>, el dado es un <b>cubo</b>, el balón es una <b>esfera</b>.'),
                 imagen('d-lineas', 75, 'Líneas cerradas (A y C) y abiertas (B y D)')],
        recuerda=['Las figuras planas se dibujan en el papel; los sólidos se pueden coger.', 'Una línea cerrada no tiene salida.'],
        practica=[unica('¿Cuántos lados tiene un triángulo?', '3', ['4', '2', '5']),
                  unica('¿Qué forma tiene un balón?', 'Esfera', ['Cubo', 'Cono', 'Cilindro'])],
        taller=[imagen('d-figuras', 75), unica('¿Cuál figura no tiene puntas?', 'El círculo', ['El cuadrado', 'El triángulo', 'El rectángulo']),
                numerica('¿Cuántos lados tiene un cuadrado?', 4),
                imagen('d-lineas', 70), unica('¿Cuál es una línea curva y cerrada?', 'A', ['B', 'C', 'D']),
                unica('¿Qué sólido se parece a una lata de atún?', 'Cilindro', ['Cubo', 'Cono', 'Esfera']),
                abierta('Busca en tu salón un objeto con forma de cubo y otro con forma de cilindro. Dibújalos.', 6)])

    U[7] = u(
        tema='¿Dónde está? Arriba, abajo, izquierda y derecha',
        objetivo='Describir dónde están los objetos y las personas, y dibujar recorridos para llegar a un lugar.',
        explora=[imagen('m1-parque', 60, 'El parque'),
                 texto('¿Dónde está el gato? ¿Dónde está el perro? ¿Qué hay dentro de la caja?')],
        aprende=[texto('Usamos palabras para decir dónde están las cosas: <b>arriba</b> y <b>abajo</b>, <b>dentro</b> y <b>fuera</b>, '
                       '<b>cerca</b> y <b>lejos</b>, <b>izquierda</b> y <b>derecha</b>.'),
                 imagen('m1-izq-der', 30, 'Tomás levanta su mano derecha'),
                 imagen('d-plano', 60, 'El plano del salón visto desde arriba'),
                 texto('En el plano, el tablero está <b>adelante</b> y la puerta está a la <b>izquierda</b>.'),
                 imagen('d-cuadricula-RRRUUURRUU', 45, 'La estrella llega a la casa: 3 a la derecha, 3 arriba, 2 a la derecha y 2 arriba')],
        recuerda=['Mi mano derecha es la que uso para… ¡pregúntale a tu profe!', 'Un plano es un dibujo visto desde arriba.'],
        practica=[unica('En el parque, el gato está…', 'arriba del árbol', ['debajo del banco', 'dentro de la caja', 'lejos del árbol']),
                  imagen('d-plano', 55), unica('En el plano, ¿en qué fila está el pupitre más cerca de la puerta?', 'C', ['A', 'B'])],
        taller=[imagen('d-cuadricula', 45),
                abierta('Dibuja con flechas un camino para que la estrella llegue a la casa. ¿Cuántos pasos diste?', 3),
                imagen('d-plano', 55), unica('¿Qué está más cerca del tablero?', 'La fila A', ['La fila B', 'La fila C', 'La puerta']),
                unica('Si miras el tablero, la ventana está a tu…', 'derecha', ['izquierda', 'espalda']),
                abierta('Dibuja el camino de tu casa al colegio. ¿Qué ves a la derecha y qué ves a la izquierda?', 6)])

    U[8] = u(
        tema='Las cosas cambian',
        objetivo='Observar cómo cambian las cosas con el tiempo y describir los cambios con dibujos y palabras.',
        explora=[imagen('m1-planta-1', 18), imagen('m1-planta-2', 18), imagen('m1-planta-3', 18), imagen('m1-planta-4', 18),
                 texto('¿Qué le pasó a la planta? ¿Qué necesitó para crecer?')],
        aprende=[texto('Las cosas <b>cambian</b>: la planta crece, la vela se gasta, nosotros crecemos.'),
                 imagen('m1-vela', 45, 'Mientras más tiempo encendida, más corta la vela'),
                 texto('Cuando una cosa cambia, otra también: <b>más días</b> → <b>planta más alta</b>; <b>más tiempo</b> → <b>vela más corta</b>.'),
                 tabla([['Semana', '1', '2', '3', '4'], ['Alto de la planta (cm)', '2', '5', '8', '11']]),
                 texto('Cada semana la planta creció <b>3 centímetros</b>.')],
        recuerda=['Para ver un cambio, comparo cómo era antes y cómo es ahora.'],
        practica=[unica('Mientras más tiempo está encendida una vela…', 'más corta queda', ['más larga queda', 'queda igual']),
                  numerica('Si la planta mide 11 cm y crece 3 cm más, ¿cuánto mide?', 14, 'cm')],
        taller=[unica('¿Qué va primero?', 'La semilla', ['La flor', 'La planta grande', 'El brote']),
                unica('Cuando llueve más, el río…', 'crece', ['se seca', 'queda igual']),
                numerica('Sofi tenía 3 dientes de leche flojos y se le cayó 1. ¿Cuántos le quedan flojos?', 2),
                abierta('Dibuja cómo eras cuando eras bebé y cómo eres ahora. ¿Qué cambió?', 6)])

    U[9] = u(
        tema='El signo igual: ¡la balanza en equilibrio!',
        objetivo='Entender que el signo = dice que los dos lados valen lo mismo.',
        explora=[imagen('d-balanza-3+2-5-0', 50, 'La balanza no se inclina'),
                 texto('¿Por qué la balanza no se inclina hacia ningún lado?')],
        aprende=[texto('El signo <b>=</b> es como una balanza en equilibrio: lo que hay a un lado vale lo mismo que lo del otro lado.'),
                 texto('<b>3 + 2 = 5</b> y también <b>5 = 4 + 1</b>.'),
                 imagen('d-balanza-4+3-5+2-0', 50, '4 + 3 = 5 + 2'),
                 texto('Las galletas se pueden repartir de varias formas y siguen siendo las mismas:'),
                 coleccion('m1-galleta', 6, 6), texto('6 = 3 + 3 = 4 + 2 = 5 + 1')],
        recuerda=['El signo = quiere decir «vale lo mismo que».', 'Si 2 + 3 = 5 y 5 = 4 + 1, entonces 2 + 3 = 4 + 1.'],
        practica=[numerica('Completa: 4 + ___ = 7', 3), numerica('Completa: 6 + 2 = 5 + ___', 3)],
        taller=[imagen('d-balanza-2+5-7-0', 45), vf('2 + 5 = 7. ¿La balanza está en equilibrio?', True),
                numerica('Completa: ___ + 3 = 8', 5), numerica('Completa: 9 = 4 + ___', 5),
                numerica('Completa: 3 + 4 = 2 + ___', 5),
                unica('¿Cuál vale lo mismo que 5 + 5?', '6 + 4', ['5 + 4', '3 + 3', '9 + 2'])])

    U[10] = u(
        tema='Cuento y organizo datos',
        objetivo='Recoger datos, contarlos en una tabla de conteo y mostrarlos en un pictograma para responder preguntas.',
        explora=[texto('En el salón preguntamos: <b>¿cuál es tu fruta favorita?</b> ¿Cómo podemos saber cuál ganó?')],
        aprende=[texto('Hacemos una <b>tabla de conteo</b>: una rayita por cada voto. Cada 5 rayitas se cierran con una raya cruzada.'),
                 imagen('d-conteo-mango.7-banano.4-fresa.6', 60, 'Tabla de conteo de la fruta favorita'),
                 texto('Con los mismos datos hacemos un <b>pictograma</b>: un dibujo por cada voto.'),
                 pictograma([('m1-mango', 7), ('m1-banano', 4), ('m1-fresa', 6)], 80, 'Pictograma de la fruta favorita'),
                 texto('El mango tiene más votos: 7. El banano tiene menos: 4. En total votaron 7 + 4 + 6 = 17 niños.')],
        recuerda=['En la tabla de conteo, cada 5 rayitas se agrupan.', 'En el pictograma, cada dibujo es un voto.'],
        practica=[numerica('¿Cuántos niños escogieron la fresa?', 6), unica('¿Cuál fruta tiene menos votos?', 'El banano', ['El mango', 'La fresa'])],
        taller=[pictograma([('m1-naranja', 5), ('m1-manzana', 3), ('m1-banano', 2)], 70, 'Fruta de la lonchera'),
                numerica('¿Cuántos niños llevaron naranja?', 5),
                unica('¿Cuál fruta llevaron más niños?', 'La naranja', ['La manzana', 'El banano']),
                numerica('¿Cuántos niños hay en total?', 5 + 3 + 2),
                imagen('d-conteo-azul.6-rojo.3-verde.5', 55, 'Color favorito'),
                numerica('¿Cuántos votos tiene el color verde?', 5),
                abierta('Pregunta a 5 compañeros su animal favorito y haz tu propia tabla de conteo.', 6)])
    return U
