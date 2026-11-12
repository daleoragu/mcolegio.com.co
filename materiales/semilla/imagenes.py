"""Banco de imágenes del material semilla.

Cada imagen tiene un id (que es también el nombre del archivo: «m1-manzana.png») para que las guías la usen y la carga
la reconozca sola. Dos orígenes:
  * «ia»:  la genera el docente con Nano Banana / Flow usando el prompt (estilo común: ESTILO). Objetos sueltos y escenas.
  * «svg»: la dibuja mcolegio en código: lo que debe ser exacto (cantidades, bloques de base 10, figuras, planos, balanzas,
           tablas de conteo). Una IA cuenta mal; por eso las colecciones se arman repitiendo el objeto suelto.
"""

ESTILO = ('Ilustración infantil plana para una ficha escolar de primer grado. Estilo vectorial con contorno grueso marrón '
          'oscuro, colores planos y vivos (rojo #E63946, amarillo #FFD166, verde #52B788, azul #4EA8DE, naranja #F4A261), '
          'sin sombras, sin degradados y sin texturas. Fondo blanco puro. Sin texto, sin letras y sin números. '
          'Formato cuadrado 1:1.')

OBJETO = 'Un solo objeto centrado, completo, de frente, ocupando el 80 % de la imagen.'
ESCENA = 'Escena sencilla y despejada, pocos elementos, que un niño de 6 años entienda de un vistazo.'
NINOS = ('Personajes: Sofi (niña colombiana de 6 años, piel trigueña, cabello negro con dos colitas, uniforme escolar '
         'de falda azul y camisa blanca) y Tomás (niño colombiano de 6 años, piel morena, cabello crespo corto, '
         'pantalón azul y camisa blanca). Caras alegres y amables.')

COLOREAR = ('Convierte la imagen adjunta en una página para colorear: solo contornos negros gruesos y limpios sobre fondo '
            'blanco, sin colores, sin grises y sin sombras. Mismo dibujo y misma composición.')


def _ia(id_, dba, nombre, uso, prompt, extra=OBJETO, colorear=True):
    return {'id': id_, 'area': 'Matemáticas', 'grado': 1, 'dba': dba, 'origen': 'ia', 'nombre': nombre, 'uso': uso,
            'prompt': f'{prompt} {extra} {ESTILO}', 'colorear': colorear}


def _svg(id_, dba, nombre, uso):
    return {'id': id_, 'area': 'Matemáticas', 'grado': 1, 'dba': dba, 'origen': 'svg', 'nombre': nombre, 'uso': uso,
            'prompt': '', 'colorear': True}


MATEMATICAS_1 = [
    # Personajes que acompañan todas las guías de 1.º (se generan primero y se adjuntan como referencia en las escenas)
    _ia('p1-sofi', 0, 'Sofi (personaje)', 'Narradora de las guías de 1.º', 'Sofi, ' + NINOS.split('Sofi (')[1].split(') y')[0]
        + ', de cuerpo entero, saludando con la mano.', 'Personaje de cuerpo entero centrado.'),
    _ia('p1-tomas', 0, 'Tomás (personaje)', 'Narrador de las guías de 1.º', 'Tomás, ' + NINOS.split('Tomás (')[1].split(').')[0]
        + ', de cuerpo entero, con un lápiz en la mano.', 'Personaje de cuerpo entero centrado.'),

    # Objetos sueltos para contar, sumar, restar y hacer pictogramas (DBA 1, 2, 3, 9 y 10)
    _ia('m1-manzana', 2, 'Manzana', 'Contar, sumar y restar', 'Una manzana roja con una hoja verde.'),
    _ia('m1-banano', 10, 'Banano', 'Pictograma de frutas', 'Un banano amarillo maduro.'),
    _ia('m1-naranja', 10, 'Naranja', 'Pictograma de frutas', 'Una naranja redonda con una hoja.'),
    _ia('m1-mango', 10, 'Mango', 'Pictograma de frutas', 'Un mango maduro, amarillo y rojo.'),
    _ia('m1-fresa', 10, 'Fresa', 'Pictograma de frutas', 'Una fresa roja con semillas amarillas y hojas verdes.'),
    _ia('m1-lapiz', 2, 'Lápiz', 'Contar de 1 en 1 y de 10 en 10', 'Un lápiz amarillo con borrador rosado, acostado en horizontal.'),
    _ia('m1-balon', 2, 'Balón de fútbol', 'Contar y sumar', 'Un balón de fútbol blanco y negro.'),
    _ia('m1-carrito', 2, 'Carrito de juguete', 'Contar y restar', 'Un carrito de juguete rojo visto de lado.'),
    _ia('m1-gallina', 2, 'Gallina', 'Problemas de la finca', 'Una gallina blanca con cresta roja, de lado.'),
    _ia('m1-huevo', 2, 'Huevo', 'Problemas de la finca (agrupar)', 'Un huevo de color crema.'),
    _ia('m1-vaca', 2, 'Vaca', 'Problemas de la finca', 'Una vaca blanca con manchas negras, de lado, de pie.'),
    _ia('m1-pez', 2, 'Pez', 'Contar y restar', 'Un pez naranja de río, de lado.'),
    _ia('m1-mariposa', 2, 'Mariposa', 'Contar de 2 en 2 (alas)', 'Una mariposa azul con las alas abiertas, vista de frente.'),
    _ia('m1-flor', 2, 'Flor', 'Contar de 5 en 5 (pétalos)', 'Una flor con exactamente cinco pétalos amarillos y centro naranja, con tallo.'),
    _ia('m1-pajaro', 2, 'Pájaro', 'Problema de quitar (se van volando)', 'Un pajarito azul posado, de lado.'),
    _ia('m1-canica', 2, 'Canica', 'Problema de juntar', 'Una canica de vidrio azul con un remolino blanco.'),
    _ia('m1-galleta', 9, 'Galleta', 'Igualdades (repartir)', 'Una galleta redonda con chispas de chocolate.'),

    # DBA 1 · Usos del número (escenas)
    _ia('m1-uso-camiseta', 1, 'Camiseta con número', 'Número como código', 'Una camiseta de fútbol amarilla vista de espalda, con un '
        'gran recuadro blanco vacío en el centro donde iría el número.', 'Objeto centrado. El recuadro debe quedar vacío.'),
    _ia('m1-uso-podio', 1, 'Podio de carrera', 'Número como orden (primero, segundo, tercero)', 'Tres niños colombianos felices sobre '
        'un podio de tres alturas después de una carrera, con medallas.', ESCENA + ' Los escalones del podio sin números.'),
    _ia('m1-uso-tienda', 1, 'Tienda escolar', 'Número en la compra (precios)', 'Mostrador de una tienda escolar colombiana con frutas, '
        'empanadas y jugos; en cada producto un letrero blanco vacío para el precio.', ESCENA + ' Los letreros deben quedar vacíos.'),
    _ia('m1-uso-medir', 1, 'Niña midiéndose', 'Número como medida', 'Sofi de pie contra una pared con una cinta de medir vertical a su '
        'lado, sin marcas legibles.', ESCENA + ' ' + NINOS),

    # DBA 2 · Juntar, quitar y completar (escenas sin cantidades: las cantidades se ponen con los objetos sueltos)
    _ia('m1-canicas-juego', 2, 'Jugando canicas', 'Problema de juntar', 'Sofi y Tomás arrodillados en el patio jugando canicas dentro '
        'de un círculo dibujado con tiza.', ESCENA + ' ' + NINOS),
    _ia('m1-cable-pajaros', 2, 'Cable de luz', 'Problema de quitar (pájaros que se van)', 'Un cable de luz entre dos postes, vacío, con '
        'cielo azul de fondo, para poner pájaros encima.', ESCENA + ' Sin pájaros.'),

    # DBA 4 y 5 · Comparar y medir
    _ia('m1-jirafa', 4, 'Jirafa', 'Alto y bajo', 'Una jirafa de pie, de lado.'),
    _ia('m1-conejo', 4, 'Conejo', 'Alto y bajo · rápido', 'Un conejo gris sentado, de lado.'),
    _ia('m1-elefante', 4, 'Elefante', 'Pesado y liviano', 'Un elefante gris de pie, de lado.'),
    _ia('m1-raton', 4, 'Ratón', 'Pesado y liviano', 'Un ratón gris pequeño, de lado.'),
    _ia('m1-tortuga', 4, 'Tortuga', 'Rápido y lento', 'Una tortuga verde caminando, de lado.'),
    _ia('m1-balde', 4, 'Balde', 'Capacidad (le cabe más)', 'Un balde azul de plástico con agua.'),
    _ia('m1-vaso', 4, 'Vaso', 'Capacidad (le cabe menos)', 'Un vaso transparente con agua.'),
    _ia('m1-medir-cuartas', 5, 'Midiendo con cuartas', 'Medir con la mano', 'Tomás midiendo el largo de su pupitre con la mano abierta '
        '(cuartas), visto desde arriba.', ESCENA + ' ' + NINOS),
    _ia('m1-medir-pasos', 5, 'Midiendo con pasos', 'Medir con pasos', 'Sofi caminando con pasos largos en el patio del colegio, con '
        'huellas marcadas en el piso.', ESCENA + ' ' + NINOS),

    # DBA 6 · Formas en el entorno (objetos reales; las figuras y los sólidos los dibuja mcolegio)
    _ia('m1-forma-lata', 6, 'Lata (cilindro)', 'Sólidos del entorno', 'Una lata de conservas cerrada, sin etiqueta con letras.'),
    _ia('m1-forma-caja', 6, 'Caja (prisma)', 'Sólidos del entorno', 'Una caja de cartón cerrada, vista en perspectiva.'),
    _ia('m1-forma-cono', 6, 'Cono de helado', 'Sólidos del entorno', 'Un cono de helado sin helado, con la punta hacia abajo.'),
    _ia('m1-forma-dado', 6, 'Dado (cubo)', 'Sólidos del entorno', 'Un dado rojo con puntos blancos, en perspectiva.', OBJETO.replace('de frente', 'en perspectiva')),

    # DBA 7 · Ubicación y recorridos
    _ia('m1-izq-der', 7, 'Izquierda y derecha', 'Lateralidad', 'Tomás de frente levantando la mano derecha, con una pulsera roja en '
        'esa muñeca.', 'Personaje de cuerpo entero centrado. ' + NINOS),
    _ia('m1-parque', 7, 'El parque', 'Arriba, abajo, dentro, fuera, cerca, lejos', 'Un parque con un árbol grande, un gato encima de una '
        'rama, un perro debajo del árbol, una caja con una pelota dentro y un banco.', ESCENA),

    # DBA 8 · Cambio y variación
    _ia('m1-planta-1', 8, 'Planta: semilla', 'Secuencia de crecimiento (1 de 4)', 'Una semilla en una matera de barro con tierra.'),
    _ia('m1-planta-2', 8, 'Planta: brote', 'Secuencia de crecimiento (2 de 4)', 'Un brote pequeño con dos hojas saliendo de una matera de barro.'),
    _ia('m1-planta-3', 8, 'Planta: mediana', 'Secuencia de crecimiento (3 de 4)', 'Una planta mediana con varias hojas en una matera de barro.'),
    _ia('m1-planta-4', 8, 'Planta: con flor', 'Secuencia de crecimiento (4 de 4)', 'Una planta grande con una flor roja en una matera de barro.'),
    _ia('m1-vela', 8, 'Vela que se gasta', 'Cambio en el tiempo', 'Tres velas encendidas en fila: una larga, una mediana y una corta.', ESCENA),

    # Lo que dibuja mcolegio (exacto)
    _svg('m1-bloques-10', 3, 'Bloques de base 10', 'Decenas (barras) y unidades (cubos)'),
    _svg('m1-paquete-10', 3, 'Paquetes de 10', 'Lápices amarrados de a 10'),
    _svg('m1-recta-20', 2, 'Recta numérica 0–20', 'Contar hacia adelante y hacia atrás'),
    _svg('m1-marco-10', 3, 'Marco de 10', 'Paso por el diez'),
    _svg('m1-tabla-100', 2, 'Tabla del 1 al 100', 'Diez más, diez menos'),
    _svg('m1-balanza', 9, 'Balanza en equilibrio', 'El signo igual'),
    _svg('m1-regla', 5, 'Regla en centímetros', 'Medir'),
    _svg('m1-lapices-largo', 4, 'Lápices largo y corto', 'Comparar longitudes'),
    _svg('m1-reloj', 4, 'Reloj', 'Duración'),
    _svg('m1-figuras', 6, 'Figuras planas', 'Círculo, cuadrado, triángulo, rectángulo'),
    _svg('m1-solidos', 6, 'Sólidos geométricos', 'Esfera, cubo, cilindro, cono, prisma'),
    _svg('m1-abierta-cerrada', 6, 'Líneas abiertas y cerradas', 'Curvo, recto, abierto, cerrado'),
    _svg('m1-plano-salon', 7, 'Plano del salón', 'Ubicarse en un plano y trazar recorridos'),
    _svg('m1-cuadricula', 7, 'Cuadrícula de recorridos', 'Flechas: arriba, abajo, izquierda, derecha'),
    _svg('m1-tabla-conteo', 10, 'Tabla de conteo', 'Palitos de 5 en 5'),
    _svg('m1-pictograma', 10, 'Pictograma', 'Frutas favoritas del salón (usa los objetos sueltos)'),
    _svg('m1-monedas', 1, 'Monedas', 'Comprar en la tienda (monedas de $50, $100, $200, $500)'),
]


def catalogo():
    return list(MATEMATICAS_1)


def por_id(id_):
    return next((x for x in catalogo() if x['id'] == id_), None)
