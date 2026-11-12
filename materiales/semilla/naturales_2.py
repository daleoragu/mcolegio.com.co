"""Ciencias Naturales 2.º: una guía y una ficha por cada uno de los 4 DBA, con experimentos sencillos y seguros.
Borradores para que el docente revise."""
from .base import abierta, imagen, recuadro, tabla, texto, unica, vf
from .matematicas_1 import u


def unidades():
    U = {}

    U[1] = u(
        tema='Fuerzas que cambian la forma de las cosas',
        objetivo='Observar cómo estirar, aplastar, doblar, torcer y arrugar cambian la forma de los objetos según su material.',
        explora=[imagen('n2-aplastar', 25), texto('¿Qué le pasa a la plastilina si la aplastas? ¿Y si aplastas una piedra?')],
        aprende=[texto('Una <b>fuerza</b> es un empujón o un jalón. Con las fuerzas podemos cambiar la forma de las cosas:'),
                 imagen('n2-estirar', 18, 'estirar'), imagen('n2-doblar', 18, 'doblar'), imagen('n2-torcer', 18, 'torcer'), imagen('n2-arrugar', 15, 'arrugar'),
                 tabla([['Material', 'Al aplicar fuerza…', 'Vuelve a su forma?'], ['Plastilina', 'se aplasta fácil', 'no'], ['Resorte', 'se estira', 'sí'],
                        ['Papel', 'se dobla y se arruga', 'no'], ['Madera', 'casi no cambia (o se parte)', 'no'], ['Hierro', 'muy difícil de deformar', 'no']]),
                 recuadro('Experimento', '<p>Aplica la misma fuerza a una bola de plastilina, una esponja y una piedra pequeña. Ordénalas de la más fácil '
                          'a la más difícil de deformar.</p>', estilo='reto')],
        recuerda=['Unos materiales se deforman fácil y otros resisten.', 'Algunos, como el resorte y el caucho, vuelven a su forma.'],
        practica=[unica('¿Qué acción usamos para escurrir un trapo?', 'Torcer', ['Aplastar', 'Estirar']),
                  unica('¿Cuál material se deforma más fácil?', 'La plastilina', ['El hierro', 'La piedra'])],
        taller=[unica('¿Cuál vuelve a su forma después de estirarlo?', 'El resorte', ['La plastilina', 'El papel arrugado']),
                unica('Para hacer una bola de papel debo…', 'arrugarlo', ['estirarlo', 'torcerlo']),
                vf('Una puerta de hierro se dobla fácil con las manos.', False),
                abierta('Haz una figura con plastilina y luego aplástala. Dibuja el antes y el después.', 6)])

    U[2] = u(
        tema='Sólidos, líquidos y gases',
        objetivo='Clasificar materiales como sólidos, líquidos o gases y comparar cómo fluyen algunos líquidos.',
        explora=[imagen('n2-hielo', 18), imagen('n2-agua-vaso', 15), imagen('n2-vapor', 22), texto('¿Qué tienen en común el hielo, el agua y el vapor?')],
        aprende=[tabla([['Estado', 'Forma', 'Ejemplos'], ['Sólido', 'tiene forma propia', 'hielo, piedra, lápiz'],
                        ['Líquido', 'toma la forma del recipiente y fluye', 'agua, aceite, leche'], ['Gas', 'ocupa todo el espacio, casi no se ve', 'aire, vapor']]),
                 imagen('n2-liquidos', 40, 'Agua, aceite y miel'),
                 texto('No todos los líquidos fluyen igual: el <b>agua</b> corre rápido, el <b>aceite</b> más despacio y la <b>miel</b> muy despacio (es <b>viscosa</b>).'),
                 texto('El <b>aire</b> no se ve, pero sabemos que está:'), imagen('n2-globo', 15, 'infla el globo'), imagen('n2-molino', 18, 'mueve el molino')],
        recuerda=['Los sólidos tienen forma propia; los líquidos toman la del recipiente.', 'El aire es un gas: no lo vemos, pero ocupa espacio.'],
        practica=[unica('¿Cuál es un líquido?', 'La leche', ['La piedra', 'El aire']),
                  unica('¿Cuál líquido fluye más despacio?', 'La miel', ['El agua', 'El jugo'])],
        taller=[unica('El hielo es…', 'sólido', ['líquido', 'gas']),
                unica('Si echo agua en un vaso y luego en una botella, el agua…', 'toma la forma de cada recipiente', ['no cambia de forma']),
                unica('¿Cómo sé que hay aire si no lo veo?', 'Porque mueve las hojas y llena el globo', ['No hay forma de saberlo']),
                vf('El vapor de la olla es un gas.', True),
                abierta('Dibuja 2 sólidos, 2 líquidos y 1 gas que haya en tu cocina.', 6)])

    U[3] = u(
        tema='Cada ser vivo en su ambiente',
        objetivo='Relacionar las características de plantas y animales con el lugar donde viven y con sus necesidades.',
        explora=[imagen('n2-frailejon', 20), imagen('n2-cactus', 18), texto('Uno vive en el páramo frío y el otro en el desierto caliente. ¿Cuál es cuál?')],
        aprende=[texto('Los seres vivos tienen <b>características</b> que les ayudan a vivir en su ambiente:'),
                 tabla([['Ser vivo', 'Característica', 'Le sirve para…'], ['Pato', 'patas palmeadas', 'nadar'], ['Mono aullador', 'cola larga y fuerte', 'colgarse de los árboles'],
                        ['Frailejón', 'hojas peludas', 'protegerse del frío del páramo'], ['Cactus', 'tallo grueso y espinas', 'guardar agua en el desierto'],
                        ['Chigüiro', 'patas con membranas', 'nadar en los caños de los llanos']]),
                 imagen('n2-pato-patas', 18), imagen('n2-mono-cola', 18), imagen('n2-chiguiro', 20),
                 texto('Según lo que comen, los animales son <b>herbívoros</b> (plantas), <b>carnívoros</b> (carne) u <b>omnívoros</b> (de todo).'),
                 imagen('n2-planta-sin-luz', 40, 'Sin luz, la planta se pone amarilla y débil')],
        recuerda=['Las plantas necesitan luz, agua, aire y suelo.', 'Cada animal tiene partes que le ayudan a vivir donde vive.'],
        practica=[unica('¿Para qué le sirven al pato sus patas palmeadas?', 'Para nadar', ['Para volar', 'Para cavar']),
                  unica('¿Qué le pasa a una planta sin luz?', 'Se pone amarilla y débil', ['Crece más verde', 'No le pasa nada'])],
        taller=[unica('El chigüiro come pasto. Es…', 'herbívoro', ['carnívoro']),
                unica('¿Dónde vive el frailejón?', 'En el páramo', ['En el mar', 'En el desierto']),
                unica('El cactus guarda agua en su…', 'tallo', ['flor', 'semilla']),
                abierta('Pon dos plantas iguales: una al sol y otra en la oscuridad. Dibuja cómo están después de una semana.', 6)])

    U[4] = u(
        tema='Ciclos de vida: nacer, crecer y reproducirse',
        objetivo='Representar los cambios en la vida de plantas y animales: germinación, floración, frutos, crecimiento y reproducción.',
        explora=[imagen('n2-flor-fruto', 30), texto('¿Qué hay en la rama del naranjo? ¿Qué pasará con las flores?')],
        aprende=[texto('<b>Ciclo de vida de una planta</b>: la semilla <b>germina</b>, crece, <b>florece</b>, la flor se vuelve <b>fruto</b> y el fruto guarda semillas.'),
                 imagen('m1-planta-1', 12), imagen('m1-planta-2', 12), imagen('m1-planta-3', 12), imagen('m1-planta-4', 12),
                 texto('<b>Ciclo de vida de la mariposa</b>: huevo → oruga → crisálida → mariposa. ¡Cambia totalmente de forma!'),
                 imagen('n2-huevos-mariposa', 12), imagen('n2-oruga', 14), imagen('n2-crisalida', 12), imagen('m1-mariposa', 14),
                 texto('Los animales <b>crecen</b> y cuando son adultos se <b>reproducen</b>: así la vida continúa.')],
        recuerda=['Las plantas: semilla, planta, flor, fruto.', 'La mariposa: huevo, oruga, crisálida, mariposa.'],
        practica=[unica('¿Qué sale del huevo de la mariposa?', 'Una oruga', ['Una mariposa', 'Una crisálida']),
                  unica('La flor del naranjo se convierte en…', 'una naranja', ['una hoja', 'una raíz'])],
        taller=[unica('¿Qué va primero en el ciclo de la planta?', 'La semilla', ['La flor', 'El fruto']),
                unica('La oruga se encierra en…', 'una crisálida', ['un huevo', 'una flor']),
                vf('Las plantas también tienen ciclo de vida.', True),
                abierta('Siembra una semilla de frijol y dibuja cómo cambia cada semana durante un mes.', 8)])
    return U
