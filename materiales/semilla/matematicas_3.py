"""Matemáticas 3.º: una guía y una ficha por cada uno de los 11 DBA (V.2). Multiplicación y división en contexto,
fracciones como parte de un todo, área y perímetro, transformaciones y datos. Borradores para que el docente revise."""
from .base import abierta, grafica, imagen, numerica, tabla, texto, unica, vf
from .matematicas_1 import u


def _barras(datos, maximo, nombre_y=''):
    """Gráfico de barras con el Graficador: datos = [(nombre, valor)]."""
    elementos = []
    for i, (n, v) in enumerate(datos):
        elementos.append({'t': 'poligono', 'puntos': [[i + 0.6, 0], [i + 1.4, 0], [i + 1.4, v], [i + 0.6, v]], 'relleno': True, 'nombre': ''})
        elementos.append({'t': 'texto', 'x': i + 0.62, 'y': -maximo * 0.07, 'texto': n})
    return {'x': [0, len(datos) + 1], 'y': [-maximo * 0.12, maximo * 1.1], 'nombre_x': '', 'nombre_y': nombre_y, 'elementos': elementos}


def unidades():
    U = {}

    U[1] = u(
        tema='Problemas de sumar, restar, multiplicar y dividir',
        objetivo='Resolver problemas con las cuatro operaciones, contar combinaciones y revisar si el resultado tiene sentido.',
        explora=[imagen('m3-paleta-helados', 50, 'El carrito de paletas'),
                 texto('Hay 3 sabores y 2 cubiertas. ¿Cuántas paletas diferentes se pueden pedir?')],
        aprende=[tabla([['', 'Chocolate', 'Coco'], ['Fresa', 'fresa-chocolate', 'fresa-coco'], ['Mango', 'mango-chocolate', 'mango-coco'],
                        ['Mora', 'mora-chocolate', 'mora-coco']]),
                 texto('Son <b>3 × 2 = 6</b> combinaciones. Multiplicar sirve para contar combinaciones.'),
                 imagen('d-arreglo-3-5', 25, '3 filas de 5: 3 × 5 = 15'),
                 texto('<b>Dividir</b> es repartir en partes iguales o ver cuántos grupos caben: 15 ÷ 5 = 3. La división es la operación <b>inversa</b> de la multiplicación.'),
                 texto('<b>¿Tiene sentido?</b> Si 4 amigos se reparten 20 mangos y me da que a cada uno le tocan 80, ¡algo está mal! Debe ser 20 ÷ 4 = 5.')],
        recuerda=['Multiplicar: grupos iguales o combinaciones. Dividir: repartir en partes iguales.', 'Siempre reviso si el resultado tiene sentido.'],
        practica=[numerica('3 camisetas y 4 pantalonetas. ¿Cuántas combinaciones de uniforme hay?', 12),
                  numerica('Se reparten 24 colores en 6 mesas por igual. ¿Cuántos por mesa?', 24 // 6)],
        taller=[numerica('Un bus lleva 45 pasajeros; en la parada bajan 18 y suben 9. ¿Cuántos van ahora?', 45 - 18 + 9),
                numerica('Un paquete trae 8 galletas. ¿Cuántas galletas hay en 7 paquetes?', 56),
                numerica('Tengo $5 000 y cada cuaderno vale $1 000. ¿Cuántos cuadernos puedo comprar?', 5),
                numerica('Sofi tiene 36 láminas y Tomás 19. ¿Cuántas más tiene Sofi?', 36 - 19),
                unica('Si reparto 30 dulces entre 5 niños y me da 150 por niño, ¿qué pasó?', 'Multipliqué en lugar de dividir', ['Está bien', 'Sumé']),
                abierta('Inventa un problema de combinaciones con la comida de tu casa y resuélvelo.', 4)])

    U[2] = u(
        tema='Estrategias para calcular y estimar',
        objetivo='Usar la descomposición, el redondeo y las propiedades de las operaciones para calcular y estimar.',
        explora=[texto('Para la excursión, el bus cuesta $198 000 y la comida $103 000. ¿Alcanza con $300 000? ¿Cómo lo sabes sin sumar exacto?')],
        aprende=[texto('<b>Redondear</b>: 198 000 es casi 200 000 y 103 000 es casi 100 000. Juntos son casi 300 000… pero un poquito más: 301 000. ¡No alcanza por $1 000!'),
                 texto('<b>Descomponer</b>: 46 × 3 = 40 × 3 + 6 × 3 = 120 + 18 = <b>138</b>.'),
                 texto('<b>Completar a la decena</b>: 57 + 8 = 57 + 3 + 5 = 60 + 5 = <b>65</b>.'),
                 texto('Algunas medidas se <b>calculan</b>: el borde de una mesa de 120 cm por 80 cm es 120 + 80 + 120 + 80 = 400 cm, sin medir todo.')],
        recuerda=['Estimar me ayuda a saber si mi respuesta es razonable.', 'Multiplicar por partes: decenas y unidades por separado.'],
        practica=[numerica('Calcula 46 × 3 descomponiendo.', 138), unica('¿Cuánto es más o menos 398 + 205?', '600', ['500', '700', '400'])],
        taller=[numerica('Calcula 57 + 8.', 65), numerica('Calcula 25 × 4.', 100), numerica('Calcula 34 × 5.', 170),
                numerica('Calcula 200 − 75.', 125),
                numerica('Una mesa mide 120 cm de largo y 80 cm de ancho. ¿Cuánto mide su borde completo?', 400, 'cm'),
                unica('¿Alcanzan $10 000 para comprar algo de $4 900 y algo de $5 300?', 'No', ['Sí', 'Sobra mucho'])])

    U[3] = u(
        tema='Las fracciones: partes de un todo',
        objetivo='Usar fracciones para expresar partes de un todo y para comparar cantidades.',
        explora=[imagen('m3-pizza', 30, 'Una pizza en 8 porciones'), texto('Ya se sirvieron 3 porciones. ¿Qué parte de la pizza se sirvió?')],
        aprende=[texto('Una <b>fracción</b> dice en cuántas partes iguales se partió el todo (abajo: <b>denominador</b>) y cuántas se toman (arriba: <b>numerador</b>).'),
                 texto('Se sirvieron \\(\\frac{3}{8}\\) de la pizza: 3 de 8 porciones.'),
                 imagen('d-fraccion-3-4', 45, 'Tres cuartos'), imagen('d-fraccion-1-2-circulo', 18, 'Un medio'),
                 texto('Las fracciones también <b>comparan</b>: en un salón hay 12 niñas y 15 niños; por cada 4 niñas hay 5 niños.'),
                 texto('Medir con unidades distintas da medidas equivalentes: un listón mide 2 cuartas o 8 dedos.')],
        recuerda=['Las partes deben ser iguales.', 'Denominador: en cuántas partes partí. Numerador: cuántas tomé.'],
        practica=[imagen('d-fraccion-2-5', 40), unica('¿Qué fracción está pintada?', '2/5', ['5/2', '2/3', '3/5']),
                  unica('Si parto una arepa en 4 partes iguales y me como 1, me comí…', '1/4', ['1/2', '4/1', '3/4'])],
        taller=[imagen('d-fraccion-3-8-circulo', 18), unica('¿Qué fracción está pintada?', '3/8', ['3/5', '5/8', '8/3']),
                unica('¿Qué es más: 1/2 o 1/4 de la misma pizza?', '1/2', ['1/4', 'Son iguales']),
                numerica('La mitad de 20 lápices son…', 10),
                numerica('Un cuarto de 12 huevos son…', 3),
                abierta('Dibuja una barra, pártela en 6 partes iguales y pinta 5/6.', 5)])

    U[4] = u(
        tema='Área y perímetro',
        objetivo='Diferenciar el área (lo que cubre) del perímetro (el borde), calcularlos en rectángulos y ver que igual perímetro no es igual área.',
        explora=[imagen('m3-baldosas', 45), texto('¿Cuántas baldosas cubre el tapete? ¿Cuánto mide su borde?')],
        aprende=[texto('El <b>perímetro</b> es la medida del borde. El <b>área</b> es lo que cubre la figura.'),
                 imagen('d-cuadros-4-3', 32, 'Rectángulo de 4 × 3'),
                 texto('Perímetro: 4 + 3 + 4 + 3 = <b>14</b> lados de cuadrito. Área: 4 × 3 = <b>12</b> cuadritos.'),
                 imagen('d-cuadros-6-1', 35, 'Rectángulo de 6 × 1'),
                 texto('Este también tiene perímetro 14 (6 + 1 + 6 + 1), ¡pero su área es solo 6! <b>Igual perímetro no significa igual área.</b>'),
                 texto('Para cercar un jardín necesito el <b>perímetro</b>; para comprar el pasto, el <b>área</b>.')],
        recuerda=['Perímetro = suma de los lados.', 'Área de un rectángulo = largo × ancho.'],
        practica=[imagen('d-cuadros-5-2', 30), numerica('¿Cuál es el área en cuadritos?', 10), numerica('¿Cuál es el perímetro?', 14)],
        taller=[numerica('Un rectángulo mide 7 m de largo y 3 m de ancho. ¿Cuál es su perímetro?', 20, 'm'),
                numerica('¿Y su área?', 21, 'm²'),
                unica('Para poner una cerca alrededor de la huerta calculo…', 'el perímetro', ['el área', 'el volumen']),
                unica('Para saber cuánta pintura necesito para una pared calculo…', 'el área', ['el perímetro']),
                vf('Dos rectángulos con el mismo perímetro siempre tienen la misma área.', False),
                abierta('Dibuja en cuadrícula dos rectángulos diferentes con perímetro 12 y escribe el área de cada uno.', 6)])

    U[5] = u(
        tema='Estimo y mido: longitud, capacidad, peso, volumen y tiempo',
        objetivo='Estimar y medir diferentes magnitudes y calcular cuántos objetos caben en una caja.',
        explora=[imagen('m3-cajas-empacar', 45), texto('¿Cuántos cubos caben en la caja? ¿Cómo lo puedes calcular sin llenarla?')],
        aprende=[texto('El <b>volumen</b> es el espacio que ocupa algo. Si en el fondo de la caja caben 4 × 3 = 12 cubos y la caja tiene 2 pisos, caben 12 × 2 = <b>24</b> cubos.'),
                 tabla([['Magnitud', 'Unidad', 'Estimo: …'], ['Longitud', 'metro, centímetro', 'la puerta mide 2 m'], ['Capacidad', 'litro', 'la olla tiene 5 litros'],
                        ['Peso', 'kilogramo, gramo', 'un bulto de papa pesa 50 kg'], ['Tiempo', 'hora, minuto', 'el recreo dura 30 min']]),
                 texto('Estimo primero, mido después y comparo: así entreno mi ojo.')],
        recuerda=['1 metro = 100 cm · 1 kilo = 1000 gramos · 1 hora = 60 minutos.'],
        practica=[numerica('En el fondo de una caja caben 5 × 2 cubos y tiene 3 pisos. ¿Cuántos cubos caben?', 30),
                  unica('¿Cuánto pesa más o menos un niño de 3.º?', '30 kilos', ['3 kilos', '300 kilos'])],
        taller=[numerica('¿Cuántos minutos hay en 2 horas?', 120, 'min'), numerica('¿Cuántos centímetros son 3 metros?', 300, 'cm'),
                unica('¿En qué unidad medimos el agua de un tanque?', 'Litros', ['Metros', 'Kilos']),
                unica('¿Cuánto mide más o menos la puerta del salón?', '2 metros', ['20 metros', '20 centímetros']),
                abierta('Estima cuántos lápices caben en tu cartuchera. Luego compruébalo.', 3)])

    U[6] = u(
        tema='Figuras y cuerpos: sus elementos',
        objetivo='Nombrar los elementos de figuras y cuerpos geométricos (lados, vértices, caras, aristas) y clasificarlos.',
        explora=[imagen('d-solidos-n', 70), texto('¿Cuáles cuerpos tienen caras planas? ¿Cuáles ruedan?')],
        aprende=[tabla([['Cuerpo', 'Caras', 'Aristas', 'Vértices'], ['Cubo', '6', '12', '8'], ['Prisma rectangular', '6', '12', '8'],
                        ['Pirámide de base cuadrada', '5', '8', '5']]),
                 texto('Las <b>caras</b> son las superficies planas; las <b>aristas</b>, donde se unen dos caras; los <b>vértices</b>, las esquinas.'),
                 texto('Los cuerpos <b>redondos</b> (esfera, cilindro, cono) tienen superficies curvas y pueden rodar.'),
                 imagen('d-poligonos', 60, 'Polígonos: triángulo, cuadrilátero, pentágono, hexágono')],
        recuerda=['Polígono: figura plana cerrada con lados rectos.', 'Un cubo tiene 6 caras, 12 aristas y 8 vértices.'],
        practica=[numerica('¿Cuántos vértices tiene un cubo?', 8), unica('¿Cuál cuerpo tiene superficie curva?', 'El cilindro', ['El cubo', 'La pirámide'])],
        taller=[numerica('¿Cuántas aristas tiene un cubo?', 12), numerica('¿Cuántas caras tiene una pirámide de base cuadrada?', 5),
                unica('Un balón tiene forma de…', 'esfera', ['cubo', 'prisma']),
                unica('¿Qué polígono tiene 5 lados?', 'Pentágono', ['Hexágono', 'Cuadrado']),
                abierta('Construye un cubo con palillos y plastilina. ¿Cuántos palillos y cuántas bolitas usaste?', 3)])

    reflejo = {'x': [-6, 6], 'y': [-1, 6], 'escala_igual': True, 'forma': 'ancha', 'elementos': [
        {'t': 'vertical', 'x': 0, 'nombre': 'espejo'},
        {'t': 'poligono', 'puntos': [[1, 1], [4, 1], [4, 3], [2, 4]], 'nombre': ''},
        {'t': 'poligono', 'puntos': [[-1, 1], [-4, 1], [-4, 3], [-2, 4]], 'color': '#dc2626', 'nombre': ''}]}
    U[7] = u(
        tema='Muevo figuras: trasladar, girar y reflejar',
        objetivo='Describir trayectorias y reconocer traslaciones, rotaciones y reflexiones, y qué cambia y qué se conserva.',
        explora=[imagen('m3-espejo-mariposa', 30), texto('Si doblas la mariposa por la mitad, ¿coinciden las dos alas?')],
        aprende=[texto('<b>Traslación</b>: la figura se desliza sin girar. <b>Rotación</b>: gira alrededor de un punto. <b>Reflexión</b>: es como verla en un espejo.'),
                 grafica(reflejo, 55, 'La figura y su reflejo en el espejo'),
                 texto('En los tres movimientos la figura <b>conserva</b> su forma y su tamaño; lo que cambia es su <b>posición</b> (y en la reflexión queda «al revés»).'),
                 imagen('d-cuadricula-RRUURR', 35, 'Una trayectoria: 2 derecha, 2 arriba, 2 derecha')],
        recuerda=['Los movimientos no cambian el tamaño ni la forma.', 'Una figura simétrica tiene dos mitades iguales como en un espejo.'],
        practica=[unica('Cuando una figura se desliza sin girar, es una…', 'traslación', ['rotación', 'reflexión']),
                  unica('Las alas de la mariposa muestran…', 'simetría (reflexión)', ['traslación', 'ampliación'])],
        taller=[unica('Las manecillas del reloj hacen una…', 'rotación', ['traslación', 'reflexión']),
                vf('Al trasladar una figura, se hace más grande.', False),
                unica('¿Cuál letra es simétrica?', 'A', ['F', 'R', 'G']),
                abierta('Dibuja en cuadrícula una figura y su reflejo con un espejo vertical.', 6)])

    U[8] = u(
        tema='Secuencias: lo que cambia y lo que se mantiene',
        objetivo='Descubrir la regla de una secuencia numérica o de figuras y predecir los siguientes términos.',
        explora=[texto('Con palillos se hacen cuadrados en fila: 1 cuadrado usa 4 palillos, 2 cuadrados usan 7, 3 cuadrados usan 10. ¿Cuántos palillos para 4 cuadrados?')],
        aprende=[tabla([['Cuadrados', '1', '2', '3', '4', '5'], ['Palillos', '4', '7', '10', '13', '16']]),
                 texto('Cada cuadrado nuevo agrega <b>3 palillos</b>: eso <b>cambia</b> igual cada vez. Lo que <b>se mantiene</b> es la regla: «sumar 3».'),
                 texto('Secuencias numéricas: 5, 10, 15, 20 (suma 5); 2, 4, 8, 16 (multiplica por 2); 100, 90, 80 (resta 10).')],
        recuerda=['Busco cuánto cambia de un término al siguiente.', 'Con la regla puedo predecir cualquier término.'],
        practica=[numerica('¿Cuántos palillos para 6 cuadrados?', 19), numerica('¿Qué sigue? 2, 4, 8, 16, ___', 32)],
        taller=[numerica('¿Qué sigue? 7, 14, 21, 28, ___', 35), numerica('¿Qué sigue? 100, 90, 80, ___', 70),
                numerica('¿Qué sigue? 1, 3, 9, 27, ___', 81),
                unica('¿Cuál es la regla de 5, 10, 15, 20?', 'Sumar 5', ['Multiplicar por 2', 'Restar 5']),
                abierta('Inventa una secuencia de figuras que crezca y escribe su regla.', 5)])

    U[9] = u(
        tema='Razono con datos que no conozco',
        objetivo='Tomar decisiones y resolver problemas aunque no conozca exactamente todos los números.',
        explora=[texto('En una bolsa hay menos de 20 canicas. Si las reparto de a 5, no sobra ninguna. ¿Cuántas canicas puede haber?')],
        aprende=[texto('Puede haber <b>5, 10 o 15</b>: las que se reparten exacto de a 5 y son menos de 20. ¡Hay varias respuestas posibles!'),
                 texto('A veces no sé el número, pero sí sé algo: «Tomás tiene 3 años más que Sofi». Si Sofi tiene 8, Tomás tiene 11; si tiene 9, Tomás tiene 12.'),
                 tabla([['Edad de Sofi', '7', '8', '9', '10'], ['Edad de Tomás (+3)', '10', '11', '12', '13']]),
                 texto('Un número escondido se puede llamar con una caja: ▢ + 7 = 15 → ▢ = 8.')],
        recuerda=['Leo las pistas y busco todos los números que cumplen.', 'Pruebo y compruebo.'],
        practica=[numerica('▢ × 4 = 28. ¿Cuánto vale ▢?', 7), unica('Si tengo «más de 10 y menos de 13» lápices, puedo tener…', '11 o 12', ['10', '13', '9'])],
        taller=[numerica('▢ − 15 = 30. ¿Cuánto vale ▢?', 45), numerica('Si Sofi tiene 10 años y Tomás 3 más, ¿cuántos tiene Tomás?', 13),
                unica('Un número par entre 11 y 15 puede ser…', '12 o 14', ['13', '11', '15']),
                numerica('Pienso un número, le sumo 6 y me da 20. ¿Qué número pensé?', 14),
                abierta('Escribe un acertijo con un número escondido para tu compañero.', 4)])

    U[10] = u(
        tema='Tablas y gráficos de barras',
        objetivo='Leer e interpretar tablas de frecuencia, gráficos de barras y pictogramas con escala, y hallar la moda.',
        explora=[texto('Preguntamos a 30 estudiantes de 3.º su deporte favorito. ¿Cómo mostramos los resultados para que se entiendan rápido?')],
        aprende=[tabla([['Deporte', 'Frecuencia'], ['Fútbol', '12'], ['Baloncesto', '6'], ['Voleibol', '5'], ['Natación', '7'], ['Total', '30']]),
                 grafica(_barras([('Fútbol', 12), ('Balonc.', 6), ('Voleibol', 5), ('Natación', 7)], 12, 'estudiantes'), 60, 'Deporte favorito de 3.º'),
                 texto('La <b>frecuencia</b> dice cuántas veces aparece cada dato. La <b>moda</b> es el dato que más se repite: <b>fútbol</b>.'),
                 texto('El <b>tamaño de la población</b> es el total de personas encuestadas: <b>30</b>.')],
        recuerda=['La moda es el dato con más frecuencia.', 'La barra más alta muestra la moda.'],
        practica=[numerica('¿Cuántos prefieren natación?', 7), unica('¿Cuál es la moda?', 'Fútbol', ['Natación', 'Voleibol'])],
        taller=[numerica('¿Cuántos más prefieren fútbol que baloncesto?', 6), numerica('¿Cuántos estudiantes respondieron?', 30),
                unica('¿Qué deporte tiene menos votos?', 'Voleibol', ['Baloncesto', 'Natación']),
                numerica('¿Cuántos prefieren baloncesto o voleibol?', 11),
                abierta('Haz una encuesta a 10 personas sobre su fruta favorita y dibuja el gráfico de barras.', 8)])

    U[11] = u(
        tema='¿Qué es más posible?',
        objetivo='Comparar la posibilidad de los eventos (imposible, menos posible, igual de posible, más posible, seguro) y anotar todos los resultados.',
        explora=[imagen('m3-ruleta', 28), texto('Si giras la ruleta, ¿en qué color es más posible que caiga? ¿Por qué?')],
        aprende=[texto('La ruleta tiene 8 partes: 5 rojas, 2 azules y 1 amarilla. Es <b>más posible</b> caer en rojo, <b>menos posible</b> en amarillo e '
                       '<b>imposible</b> caer en verde.'),
                 texto('Al lanzar una moneda, cara y sello son <b>igualmente posibles</b>. Al lanzar un dado, los resultados posibles son 1, 2, 3, 4, 5 y 6.'),
                 tabla([['Escala', 'Ejemplo'], ['Imposible', 'sacar 7 con un dado'], ['Menos posible', 'amarillo en la ruleta'],
                        ['Igualmente posible', 'cara o sello'], ['Más posible', 'rojo en la ruleta'], ['Seguro', 'sacar un número menor que 7 con un dado']])],
        recuerda=['Más partes de un color → más posible caer en él.', 'Anoto todos los resultados posibles antes de decidir.'],
        practica=[unica('En la ruleta, ¿qué es menos posible?', 'Amarillo', ['Rojo', 'Azul']), unica('Sacar par o impar con un dado es…', 'igualmente posible', ['imposible', 'seguro'])],
        taller=[unica('Sacar un 6 con un dado es… que sacar un número menor que 6.', 'menos posible', ['más posible', 'igual de posible']),
                numerica('¿Cuántos resultados posibles hay al lanzar un dado?', 6),
                unica('En una bolsa con 9 canicas verdes y 1 roja, sacar verde es…', 'más posible', ['menos posible', 'imposible']),
                abierta('Lanza una moneda 20 veces y anota cuántas caras y sellos salen. ¿Qué observas?', 4)])
    return U
