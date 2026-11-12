"""Ciencias Naturales 4.º: una guía y un taller por cada uno de los 7 DBA, con experimentos sencillos y seguros.
Borradores para que el docente revise."""
from .base import abierta, imagen, recuadro, tabla, texto, unica, unidad, vf


def unidades():
    U = {}

    U[1] = unidad(
        tema='Las fuerzas cambian el movimiento',
        objetivo='Explicar cómo la magnitud y la dirección de una fuerza cambian el movimiento, y el efecto de la fricción.',
        explora=[texto('Empuja suavemente una pelota y luego con fuerza. ¿Qué cambia? ¿Y si la empujas hacia otro lado?')],
        aprende=[texto('Una <b>fuerza</b> tiene <b>magnitud</b> (qué tan fuerte) y <b>dirección</b> (hacia dónde). Puede poner en movimiento, frenar, acelerar o cambiar la dirección.'),
                 texto('Si dos fuerzas iguales empujan en sentidos contrarios (como en una cuerda bien tensada en un juego de tira y afloja empatado), el objeto <b>no se mueve</b>.'),
                 imagen('n4-friccion', 45, 'La rampa con lija frena más el carrito'),
                 texto('La <b>fricción</b> es la fuerza que aparece cuando dos superficies se rozan: frena el movimiento. Las superficies ásperas tienen más fricción que las lisas.')],
        recuerda=['Más fuerza → más cambio en el movimiento.', 'La fricción frena: por eso los zapatos tienen suela con dibujos.'],
        practica=[unica('¿En qué rampa baja más rápido el carrito?', 'En la de madera lisa', ['En la de lija']),
                  unica('Si empujo una caja hacia la derecha, se mueve hacia…', 'la derecha', ['la izquierda', 'arriba'])],
        taller=[unica('Las suelas de los tenis tienen dibujos para…', 'tener más fricción y no resbalar', ['verse bonitas']),
                vf('Si dos fuerzas iguales empujan en sentidos contrarios, el objeto no se mueve.', True),
                abierta('Lanza un carrito por el piso de baldosa, por un tapete y por el pasto. Mide hasta dónde llega en cada caso.', 6)])

    U[2] = unidad(
        tema='Máquinas simples',
        objetivo='Reconocer palancas, poleas, planos inclinados y ruedas en objetos cotidianos y explicar cómo facilitan el trabajo.',
        explora=[imagen('n4-maquinas', 50), texto('¿Cómo ayudan estos objetos a hacer menos fuerza?')],
        aprende=[imagen('d-palanca', 45, 'La palanca'),
                 texto('En una <b>palanca</b>, mientras más lejos del punto de apoyo hago la fuerza, menos fuerza necesito para levantar la carga.'),
                 tabla([['Máquina simple', 'Ejemplo', 'Ventaja'], ['Palanca', 'tijeras, balancín, destapador', 'levanta cargas con poca fuerza'],
                        ['Polea', 'pozo, grúa', 'cambia la dirección de la fuerza'], ['Plano inclinado', 'rampa, escalera', 'sube cargas con menos fuerza'],
                        ['Rueda y eje', 'carretilla, bicicleta', 'mueve cargas con poca fricción']])],
        recuerda=['Las máquinas simples no eliminan el trabajo: lo hacen más fácil.'],
        practica=[unica('Una rampa es un…', 'plano inclinado', ['polea', 'palanca']), unica('Las tijeras son…', 'palancas', ['poleas', 'ruedas'])],
        taller=[unica('Para sacar agua de un pozo se usa una…', 'polea', ['rampa', 'tijera']),
                unica('En la palanca, si hago la fuerza más lejos del apoyo, necesito…', 'menos fuerza', ['más fuerza', 'la misma fuerza']),
                abierta('Busca 3 máquinas simples en tu casa y explica para qué sirve cada una.', 6)])

    U[3] = unidad(
        tema='El día y la noche',
        objetivo='Explicar que el día y la noche se deben a la rotación de la Tierra, que solo tiene iluminada la mitad que mira al Sol.',
        explora=[texto('Si el Sol no se mueve alrededor de la Tierra, ¿por qué parece que sale y se oculta?')],
        aprende=[imagen('d-dianoche', 55, 'El Sol ilumina la mitad de la Tierra'),
                 texto('La Tierra <b>gira sobre su eje</b> (rotación) y da una vuelta completa en unas <b>24 horas</b>. La mitad que mira al Sol tiene <b>día</b>; la otra, <b>noche</b>.'),
                 texto('Por eso el Sol «sale» por el oriente y «se oculta» por el occidente. Las <b>sombras</b> cambian durante el día: son largas en la mañana y en la tarde, y cortas al mediodía.'),
                 recuadro('Experimento', '<p>En un cuarto oscuro, alumbra una pelota con una linterna y gírala despacio. Marca tu país con un punto: ¿cuándo tiene día y cuándo noche?</p>',
                          estilo='reto')],
        recuerda=['Rotación: la Tierra gira sobre sí misma en 24 horas.', 'Día: la mitad iluminada. Noche: la mitad oscura.'],
        practica=[unica('¿Cuánto tarda la Tierra en girar sobre su eje?', 'Unas 24 horas', ['Un año', 'Un mes']),
                  unica('¿Cuándo es más corta la sombra?', 'Al mediodía', ['En la mañana', 'Al atardecer'])],
        taller=[unica('El día y la noche se producen por…', 'la rotación de la Tierra', ['que el Sol se apaga', 'las nubes']),
                vf('Cuando en Colombia es de día, en todo el mundo también es de día.', False),
                abierta('Clava un palo en el patio y mide su sombra a las 8, 10, 12, 2 y 4. Haz una tabla.', 6)])

    U[4] = unidad(
        tema='Las fases de la Luna',
        objetivo='Observar y registrar las fases de la Luna y explicarlas por la posición del Sol, la Tierra y la Luna.',
        explora=[texto('¿La Luna siempre se ve igual? Dibújala hoy en la noche y vuelve a dibujarla en una semana.')],
        aprende=[imagen('d-lunas', 60, 'A. Luna nueva · B. Creciente · C. Luna llena · D. Menguante'),
                 texto('La Luna <b>no tiene luz propia</b>: refleja la luz del Sol. Mientras gira alrededor de la Tierra (en unos <b>29 días y medio</b>), vemos desde aquí '
                       'diferentes partes de su cara iluminada.'),
                 tabla([['Fase', 'Qué vemos', 'Posición'], ['Luna nueva', 'casi nada', 'la Luna está entre la Tierra y el Sol'], ['Creciente', 'la parte iluminada aumenta', '—'],
                        ['Luna llena', 'toda la cara iluminada', 'la Tierra está entre el Sol y la Luna'], ['Menguante', 'la parte iluminada disminuye', '—']])],
        recuerda=['La Luna refleja la luz del Sol.', 'El ciclo de fases dura casi un mes.'],
        practica=[unica('¿Qué fase es cuando vemos la Luna completa?', 'Luna llena', ['Luna nueva', 'Menguante']),
                  unica('La Luna brilla porque…', 'refleja la luz del Sol', ['tiene luz propia'])],
        taller=[unica('En luna nueva, la Luna está…', 'entre la Tierra y el Sol', ['detrás de la Tierra']),
                unica('¿Cuánto dura más o menos el ciclo de las fases?', 'Casi un mes', ['Un día', 'Un año']),
                abierta('Dibuja la Luna cada noche durante dos semanas y escribe la fecha de cada dibujo.', 8)])

    U[5] = unidad(
        tema='Mezclas y cómo separarlas',
        objetivo='Clasificar mezclas en homogéneas y heterogéneas y escoger la técnica para separarlas.',
        explora=[texto('Mezcla agua con sal y agua con arena en dos vasos. ¿En cuál ves los componentes? ¿Cómo los separarías?')],
        aprende=[tabla([['Mezcla', 'Cómo se ve', 'Ejemplos'], ['Homogénea', 'una sola fase: no se distinguen los componentes', 'agua con sal, aire, limonada colada'],
                        ['Heterogénea', 'se distinguen los componentes', 'agua con arena, arroz con frijoles, agua con aceite']]),
                 imagen('n4-filtrar', 50, 'Filtración y tamizado'),
                 tabla([['Técnica', 'Separa…', 'Ejemplo'], ['Filtración', 'un sólido de un líquido', 'agua con arena'], ['Tamizado', 'sólidos de diferente tamaño', 'arroz y piedritas'],
                        ['Decantación', 'líquidos que no se mezclan, o sólidos que se asientan', 'agua y aceite'], ['Evaporación', 'un sólido disuelto en un líquido', 'sal del agua de mar']])],
        recuerda=['Homogénea: una fase. Heterogénea: varias fases.', 'La técnica depende de lo que quiero separar.'],
        practica=[unica('El agua con aceite es una mezcla…', 'heterogénea', ['homogénea']), unica('Para sacar la sal del agua de mar uso…', 'evaporación', ['tamizado', 'filtración'])],
        taller=[unica('Para separar piedritas del arroz uso…', 'tamizado', ['evaporación', 'decantación']),
                unica('La limonada colada es una mezcla…', 'homogénea', ['heterogénea']),
                unica('Para separar arena del agua uso…', 'filtración', ['evaporación', 'tamizado']),
                abierta('Prepara agua con arena y fíltrala con un colador y una servilleta. Describe lo que pasó.', 6)])

    U[6] = unidad(
        tema='Cadenas y redes alimenticias',
        objetivo='Identificar productores, consumidores y descomponedores, y representar cadenas, redes y pirámides alimenticias.',
        explora=[imagen('n4-cadena', 60), texto('¿Quién se come a quién? ¿De dónde saca su energía el pasto?')],
        aprende=[tabla([['Nivel', 'Función', 'Ejemplo'], ['Productores', 'fabrican su alimento con la luz del sol', 'pasto, árboles, algas'],
                        ['Consumidores primarios', 'comen plantas (herbívoros)', 'saltamontes, vaca'], ['Consumidores secundarios', 'comen herbívoros', 'rana'],
                        ['Consumidores terciarios', 'comen otros carnívoros', 'garza'], ['Descomponedores', 'descomponen los restos y devuelven nutrientes al suelo', 'hongos, bacterias, lombrices']]),
                 texto('Pasto → saltamontes → rana → garza es una <b>cadena</b>. Varias cadenas unidas forman una <b>red</b>. La <b>pirámide</b> muestra que hay muchos productores abajo y pocos depredadores arriba.'),
                 texto('Si desaparecen las ranas, aumentan los saltamontes, comen más pasto y las garzas se quedan sin alimento: <b>todo está conectado</b>.')],
        recuerda=['Toda cadena empieza en un productor.', 'Los descomponedores reciclan los nutrientes.'],
        practica=[unica('¿Quién es el productor en la cadena?', 'El pasto', ['La rana', 'La garza']),
                  unica('Los hongos son…', 'descomponedores', ['productores', 'consumidores'])],
        taller=[unica('Si desaparecen las ranas, los saltamontes…', 'aumentan', ['disminuyen', 'no cambian']),
                unica('La vaca es un consumidor…', 'primario', ['secundario', 'terciario']),
                abierta('Dibuja una cadena alimenticia de un ecosistema de tu región con al menos 4 eslabones.', 6)])

    U[7] = unidad(
        tema='Ecosistemas terrestres y acuáticos de Colombia',
        objetivo='Diferenciar ecosistemas terrestres y acuáticos y explicar cómo la temperatura, la humedad, el suelo y la altitud deciden quién vive en ellos.',
        explora=[imagen('n4-paramo', 35, 'Páramo'), imagen('n4-manglar', 35, 'Manglar'), texto('¿Qué diferencias ves entre el páramo y el manglar?')],
        aprende=[tabla([['Ecosistema', 'Tipo', 'Condiciones', 'Seres vivos'], ['Páramo', 'terrestre', 'frío, alto, húmedo', 'frailejón, oso de anteojos'],
                        ['Bosque húmedo tropical', 'terrestre', 'caliente, muy lluvioso', 'monos, guacamayas, ceibas'], ['Desierto (La Guajira)', 'terrestre', 'caliente y seco', 'cactus, iguanas'],
                        ['Manglar', 'acuático', 'agua salada y dulce mezclada', 'mangle, cangrejos, garzas'], ['Arrecife de coral', 'acuático', 'mar cálido y claro', 'corales, peces de colores'],
                        ['Río', 'acuático', 'agua dulce en movimiento', 'bocachico, nutria']]),
                 texto('La <b>altitud</b> cambia la temperatura: mientras más alto, más frío. Por eso en Colombia tenemos de todo, del páramo a la playa.'),
                 texto('Algunas especies son <b>endémicas</b>: solo viven en un lugar del mundo.')],
        recuerda=['Terrestres y acuáticos.', 'La altitud, la temperatura y la humedad deciden qué vive en cada ecosistema.'],
        practica=[unica('El manglar es un ecosistema…', 'acuático', ['terrestre']), unica('El frailejón vive en el…', 'páramo', ['desierto', 'arrecife'])],
        taller=[unica('Mientras más alto es un lugar, más…', 'frío', ['caliente']),
                unica('¿Qué ecosistema es caliente y seco?', 'El desierto', ['El páramo', 'El manglar']),
                abierta('Investiga una especie endémica de tu región y descríbela.', 6)])
    return U
