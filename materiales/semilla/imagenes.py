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


def _a(area):
    """Atajo para las demás áreas: _a('Lenguaje')(id, dba, nombre, uso, prompt, extra)."""
    def f(id_, dba, nombre, uso, prompt, extra=OBJETO, colorear=True):
        return dict(_ia(id_, dba, nombre, uso, prompt, extra, colorear), area=area)
    return f


_l, _n, _s = _a('Lenguaje'), _a('Ciencias Naturales'), _a('Ciencias Sociales')
CARA = 'Primer plano de la cara y los hombros, centrado.'

LENGUAJE_1 = [
    # DBA 1 · Medios de comunicación
    _l('l1-radio', 1, 'Radio', 'Medios de comunicación', 'Un radio antiguo de mesa con antena.'),
    _l('l1-televisor', 1, 'Televisor', 'Medios de comunicación', 'Un televisor con la pantalla mostrando un paisaje de montañas.'),
    _l('l1-periodico', 1, 'Periódico', 'Medios de comunicación', 'Un periódico doblado con columnas de rayitas grises en lugar de letras y una foto.'),
    _l('l1-celular', 1, 'Celular', 'Medios de comunicación (internet)', 'Un teléfono celular con la pantalla encendida mostrando íconos de colores sin letras.'),
    _l('l1-valla', 1, 'Valla publicitaria', 'Medios de comunicación', 'Una valla publicitaria grande junto a una carretera, con el dibujo de un vaso de jugo y sin letras.', ESCENA),
    _l('l1-afiche', 1, 'Afiche', 'Medios de comunicación', 'Un afiche pegado en una pared, con el dibujo de un balón y estrellas, sin letras.'),
    _l('l1-locutor', 1, 'Locutor de radio', 'Tipos de voz en la radio', 'Un locutor de radio colombiano hablando con emoción frente a un micrófono, con audífonos.', ESCENA),
    # DBA 2 · Gestos y lenguaje del cuerpo
    _l('l1-cara-feliz', 2, 'Tomás feliz', 'Gestos del rostro', 'Tomás sonriendo muy feliz. ' + NINOS, CARA),
    _l('l1-cara-triste', 2, 'Tomás triste', 'Gestos del rostro', 'Tomás triste, con una lágrima. ' + NINOS, CARA),
    _l('l1-cara-enojada', 2, 'Sofi enojada', 'Gestos del rostro', 'Sofi enojada, con el ceño fruncido. ' + NINOS, CARA),
    _l('l1-cara-sorpresa', 2, 'Sofi sorprendida', 'Gestos del rostro', 'Sofi sorprendida, con la boca abierta y los ojos grandes. ' + NINOS, CARA),
    _l('l1-gesto-silencio', 2, 'Gesto de silencio', 'Gestos de las manos', 'Sofi con el dedo índice sobre los labios pidiendo silencio. ' + NINOS, CARA),
    _l('l1-gesto-pulgar', 2, 'Pulgar arriba', 'Gestos de las manos', 'Tomás mostrando el pulgar arriba, contento. ' + NINOS, CARA),
    _l('l1-gesto-ven', 2, 'Gesto de «ven»', 'Gestos de las manos', 'Una mano haciendo el gesto de «ven aquí» con los dedos.'),
    # DBA 3 y 4 · Adivinanzas, rimas y un cuento
    _l('l1-luna', 3, 'Luna', 'Adivinanza', 'Una luna llena amarilla y sonriente con dos estrellas.'),
    _l('l1-gallo', 3, 'Gallo', 'Adivinanza', 'Un gallo de colores cantando, de lado.'),
    _l('l1-paraguas', 3, 'Paraguas', 'Adivinanza', 'Un paraguas rojo abierto con gotas de lluvia.'),
    _l('l1-tita-1', 4, 'Cuento: Tita y el río (1)', 'Cuento «Tita, la tortuga» · inicio', 'Una tortuga pequeña con una pañoleta roja caminando feliz '
       'a la orilla de un río de montaña colombiano, con un sol brillante.', ESCENA + ' La tortuga se llama Tita y aparece igual en las 4 escenas.'),
    _l('l1-tita-2', 4, 'Cuento: Tita y el río (2)', 'Cuento «Tita, la tortuga» · problema', 'La tortuga pequeña con pañoleta roja, asustada, '
       'porque un aguacero hizo crecer el río y la corriente se lleva su casita de hojas.', ESCENA + ' Misma tortuga de la escena anterior.'),
    _l('l1-tita-3', 4, 'Cuento: Tita y el río (3)', 'Cuento «Tita, la tortuga» · ayuda', 'Una garza blanca, un sapo verde y una ardilla ayudan a la '
       'tortuga pequeña con pañoleta roja a cargar ramas para hacer una casa nueva.', ESCENA + ' Misma tortuga de las escenas anteriores.'),
    _l('l1-tita-4', 4, 'Cuento: Tita y el río (4)', 'Cuento «Tita, la tortuga» · final', 'La tortuga pequeña con pañoleta roja celebrando con la '
       'garza, el sapo y la ardilla frente a su casita nueva en lo alto de una loma, con un arcoíris.', ESCENA + ' Misma tortuga de las escenas anteriores.'),
    # DBA 5, 6 y 8 · Sonidos, palabras sencillas y palabras parecidas
    _l('l1-mesa', 5, 'Mesa', 'Sonido inicial m', 'Una mesa de madera de cuatro patas.'),
    _l('l1-mano', 5, 'Mano', 'Sonido inicial m', 'Una mano abierta de niño, la palma de frente.'),
    _l('l1-pato', 5, 'Pato', 'Sonido inicial p', 'Un pato amarillo de lado.'),
    _l('l1-sapo', 5, 'Sapo', 'Sonido inicial s', 'Un sapo verde sentado, de frente.'),
    _l('l1-sol', 5, 'Sol', 'Sonido inicial s', 'Un sol amarillo sonriente con rayos.'),
    _l('l1-oso', 6, 'Oso', 'Leer palabras sencillas', 'Un oso de anteojos (oso andino) sentado, tierno.'),
    _l('l1-uva', 6, 'Uvas', 'Leer palabras sencillas', 'Un racimo de uvas moradas.'),
    _l('l1-mapa', 6, 'Mapa', 'Leer palabras sencillas', 'Un mapa del tesoro enrollado a medias, con una equis roja, sin letras.'),
    _l('l1-mono', 6, 'Mono', 'Leer palabras sencillas', 'Un mono tití colgado de una rama con la cola.'),
    _l('l1-lupa', 8, 'Lupa', 'Palabras parecidas (luna, lupa)', 'Una lupa con mango azul.'),
    _l('l1-casa', 8, 'Casa', 'Palabras parecidas (casa, taza)', 'Una casa campesina colombiana de colores con techo de teja.'),
    _l('l1-taza', 8, 'Taza', 'Palabras parecidas (casa, taza)', 'Una taza de chocolate caliente humeante.'),
    _l('l1-perro', 8, 'Perro', 'Palabras parecidas (perro, pera)', 'Un perro criollo café, sentado y contento.'),
    _l('l1-pera', 8, 'Pera', 'Palabras parecidas (perro, pera)', 'Una pera verde con una hoja.'),
    # DBA 7 · Hablar
    _l('l1-ronda', 7, 'Conversación en ronda', 'Hablar y escuchar por turnos', 'Seis niños colombianos sentados en círculo en el piso del salón; '
       'una niña habla con un peluche en la mano y los demás escuchan con atención.', ESCENA),
    _l('l1-biblioteca', 7, 'Voz baja en la biblioteca', 'Volumen de la voz (lugar cerrado)', 'Sofi y Tomás susurrando dentro de una biblioteca '
       'escolar con libros de colores.', ESCENA + ' ' + NINOS),
    _l('l1-patio', 7, 'Voz alta en el patio', 'Volumen de la voz (lugar abierto)', 'Tomás llamando con las manos alrededor de la boca a Sofi, '
       'que está lejos en el patio del colegio.', ESCENA + ' ' + NINOS),
]

NATURALES_1 = [
    # DBA 1 · Los sentidos
    _n('n1-ojo', 1, 'Ojo', 'La vista', 'Un ojo grande y expresivo de niño con pestañas.'),
    _n('n1-oreja', 1, 'Oreja', 'El oído', 'Una oreja de niño vista de lado.'),
    _n('n1-nariz', 1, 'Nariz', 'El olfato', 'Una nariz de niño de perfil oliendo una flor.'),
    _n('n1-lengua', 1, 'Boca y lengua', 'El gusto', 'Una boca de niño sacando la lengua, divertida.'),
    _n('n1-mano-tacto', 1, 'Mano que toca', 'El tacto', 'Una mano de niño tocando una mota de algodón.'),
    _n('n1-limon', 1, 'Limón', 'Sabor ácido', 'Un limón verde partido por la mitad.'),
    _n('n1-helado', 1, 'Helado', 'Frío y dulce', 'Un helado de fresa en cono.'),
    _n('n1-campana', 1, 'Campana', 'Sonido', 'Una campana dorada sonando, con líneas de sonido.'),
    _n('n1-piedra', 2, 'Piedra', 'Duro · objeto inerte', 'Una piedra gris de río.'),
    _n('n1-algodon', 1, 'Algodón', 'Suave', 'Una mota de algodón blanco esponjosa.'),
    # DBA 2 · Materiales
    _n('n1-silla-madera', 2, 'Silla de madera', 'Madera', 'Una silla de madera sencilla.'),
    _n('n1-botella-vidrio', 2, 'Botella de vidrio', 'Vidrio (transparente)', 'Una botella de vidrio transparente vacía.'),
    _n('n1-cuchara', 2, 'Cuchara de metal', 'Metal', 'Una cuchara de metal plateada.'),
    _n('n1-balde-plastico', 2, 'Balde de plástico', 'Plástico', 'Un balde de plástico verde vacío.'),
    _n('n1-esponja', 2, 'Esponja', 'Absorbe el agua', 'Una esponja amarilla de cocina mojada con gotas.'),
    _n('n1-impermeable', 2, 'Niña con impermeable', 'No deja pasar el agua', 'Sofi con impermeable amarillo y botas, bajo la lluvia, '
       'seca y contenta. ' + NINOS, 'Personaje de cuerpo entero centrado.'),
    _n('n1-caucho', 2, 'Banda de caucho', 'Flexible', 'Una banda de caucho de colores estirada entre dos dedos.'),
    # DBA 3 · Seres vivos
    _n('n1-planta-partes', 3, 'Planta completa', 'Partes de la planta', 'Una planta de frijol completa con raíz visible bajo la tierra '
       '(corte de la tierra), tallo, hojas, una flor y una vaina, sin letras.', 'Planta completa centrada, vista de frente.'),
    _n('n1-pollito', 3, 'Pollito', 'Ciclo de vida', 'Un pollito amarillo recién salido del cascarón.'),
    _n('n1-renacuajo', 3, 'Renacuajo', 'Ciclo de vida de la rana', 'Un renacuajo negro nadando en agua clara.'),
    _n('n1-rana', 3, 'Rana', 'Ciclo de vida de la rana', 'Una rana verde adulta sentada.'),
    _n('n1-arbol-guayacan', 3, 'Guayacán', 'Planta del entorno', 'Un árbol de guayacán amarillo florecido.'),
    _n('n1-regando', 3, 'Niños regando una planta', 'Cuidar los seres vivos', 'Sofi y Tomás regando una matera con una regadera '
       'en la huerta escolar.', ESCENA + ' ' + NINOS),
    # DBA 4 · Mi cuerpo cambia
    _n('n1-bebe', 4, 'Bebé', 'Etapas de la vida', 'Un bebé colombiano gateando y sonriendo.', 'Personaje de cuerpo entero centrado.'),
    _n('n1-nino', 4, 'Niño', 'Etapas de la vida', 'Un niño colombiano de 6 años de pie, sonriendo.', 'Personaje de cuerpo entero centrado.'),
    _n('n1-joven', 4, 'Joven', 'Etapas de la vida', 'Una joven colombiana de 16 años con morral, sonriendo.', 'Personaje de cuerpo entero centrado.'),
    _n('n1-adulto', 4, 'Adulto', 'Etapas de la vida', 'Un hombre colombiano adulto de 35 años, sonriendo.', 'Personaje de cuerpo entero centrado.'),
    _n('n1-abuela', 4, 'Abuela', 'Etapas de la vida', 'Una abuela colombiana de cabello blanco con bastón, sonriendo.', 'Personaje de cuerpo entero centrado.'),
    _n('n1-sofi-mama', 4, 'Sofi y su mamá', 'Parecidos de familia', 'Sofi abrazada con su mamá: las dos tienen el mismo cabello negro, '
       'la misma piel trigueña y la misma sonrisa. ' + NINOS, ESCENA),
    _n('n1-midiendo-estatura', 4, 'Midiendo la estatura', 'Registrar cómo crezco', 'Tomás de espaldas contra la pared mientras la profe '
       'le marca la estatura con un lápiz. ' + NINOS, ESCENA),
]

SOCIALES_1 = [
    # DBA 1 · Me ubico
    _s('s1-sol-sale', 1, 'Por donde sale el sol', 'El oriente (este)', 'Tomás señalando con el brazo derecho el sol que sale detrás de las '
       'montañas en la mañana. ' + NINOS, ESCENA),
    _s('s1-camino-escuela', 1, 'Camino a la escuela', 'Recorrido de la casa a la escuela', 'Sofi caminando con su morral por una calle de '
       'pueblo colombiano hacia la escuela, pasando por una tienda y un parque. ' + NINOS, ESCENA),
    # DBA 2 · El paisaje y el tiempo
    _s('s1-montana', 2, 'Montaña', 'Formas del relieve', 'Montañas verdes de los Andes colombianos con cultivos de café.', ESCENA),
    _s('s1-valle', 2, 'Valle con río', 'Formas del relieve', 'Un valle plano y verde con un río que lo atraviesa, entre dos montañas.', ESCENA),
    _s('s1-llanura', 2, 'Llanura', 'Formas del relieve', 'Una llanura de los Llanos Orientales con pasto, palmas de moriche y ganado a lo lejos.', ESCENA),
    _s('s1-costa', 2, 'Costa', 'Formas del relieve', 'Una playa del mar Caribe con palmeras de coco y olas.', ESCENA),
    _s('s1-isla', 2, 'Isla', 'Formas del relieve', 'Una isla pequeña con palmeras rodeada de mar azul.', ESCENA),
    _s('s1-lluvia', 2, 'Día de lluvia', 'Tiempo atmosférico', 'Un pueblo colombiano bajo un aguacero con charcos y nubes grises.', ESCENA),
    _s('s1-sequia', 2, 'Tiempo seco', 'Tiempo atmosférico', 'Un campo seco con la tierra agrietada y un sol muy fuerte.', ESCENA),
    _s('s1-rio-basura', 2, 'Río con basura', 'Problema ambiental', 'Un río con botellas y bolsas de plástico flotando y un pez triste.', ESCENA),
    _s('s1-puente', 2, 'Puente nuevo', 'Obras de la comunidad', 'Un puente de concreto nuevo sobre una quebrada, con gente pasando.', ESCENA),
    # DBA 3 y 4 · Mi tiempo y los cambios
    _s('s1-familia', 3, 'La familia', 'Quién nació antes y después', 'Una familia colombiana: abuelo, abuela, papá, mamá, un niño de 6 años '
       'y una bebé, de pie en fila del mayor al menor.', ESCENA),
    _s('s1-cumpleanos', 3, 'Cumpleaños', 'Fechas importantes', 'Sofi soplando las velas de una torta de cumpleaños con sus amigos. ' + NINOS, ESCENA),
    _s('s1-izada', 4, 'Izada de bandera', 'Acontecimientos del colegio', 'Niños en formación en el patio del colegio mientras se iza la '
       'bandera de Colombia (amarillo, azul y rojo).', ESCENA),
    _s('s1-primer-dia', 4, 'Primer día de clases', 'Antes y ahora', 'Tomás con morral nuevo de la mano de su mamá entrando por primera vez '
       'al colegio, un poco nervioso. ' + NINOS, ESCENA),
    # DBA 5 · Soy único
    _s('s1-diversidad', 5, 'Niños diferentes', 'Todos somos únicos', 'Cinco niños colombianos de diferentes regiones y rasgos (afro, indígena, '
       'mestizo, campesino con sombrero, niña en silla de ruedas) tomados de la mano y sonriendo.', ESCENA),
    _s('s1-abuelo-cuenta', 5, 'El abuelo cuenta historias', 'Costumbres y tradiciones', 'Un abuelo campesino con sombrero vueltiao contando '
       'una historia a Sofi y Tomás sentados en el corredor de una casa. ' + NINOS, ESCENA),
    # DBA 6 · Las viviendas
    _s('s1-casa-bahareque', 6, 'Casa de bahareque', 'Tipos de vivienda', 'Una casa campesina de bahareque y tejas de barro con corredor y matas.', ESCENA),
    _s('s1-edificio', 6, 'Edificio de apartamentos', 'Tipos de vivienda', 'Un edificio de apartamentos de ladrillo en una ciudad.', ESCENA),
    _s('s1-casa-ladrillo', 6, 'Casa de ladrillo', 'Tipos de vivienda', 'Una casa de ladrillo de dos pisos en un barrio de pueblo.', ESCENA),
    _s('s1-palafito', 6, 'Palafito', 'Tipos de vivienda', 'Una casa de madera sobre pilotes (palafito) en una ciénaga, con una canoa.', ESCENA),
    _s('s1-maloca', 6, 'Maloca', 'Tipos de vivienda', 'Una maloca indígena amazónica de techo de palma, en la selva.', ESCENA),
    # DBA 7 y 8 · Acuerdos y convivencia
    _s('s1-acuerdos', 7, 'Haciendo acuerdos', 'Normas del salón', 'Niños sentados en mesa redonda levantando la mano para opinar, con la '
       'profe escuchando y una cartelera en blanco en la pared.', ESCENA),
    _s('s1-equipo', 7, 'Trabajo en equipo', 'Metas comunes', 'Cuatro niños cargando juntos una caja grande para la huerta escolar.', ESCENA),
    _s('s1-turno', 7, 'Esperar el turno', 'Normas del juego', 'Niños haciendo fila para subir al rodadero del parque, esperando su turno.', ESCENA),
    _s('s1-compartir', 8, 'Compartir', 'Convivencia', 'Sofi compartiendo sus colores con un compañero en el salón. ' + NINOS, ESCENA),
    _s('s1-invitar', 8, 'Invitar a jugar', 'Respeto e inclusión', 'Tomás invitando a jugar a un niño que estaba solo y triste en el patio. ' + NINOS, ESCENA),
    _s('s1-pedir-ayuda', 8, 'Pedir ayuda', 'A quién acudir', 'Una niña contándole algo importante a su profesora, que la escucha agachada a su '
       'altura con cariño.', ESCENA),
]


def _g2(fn):
    """Las de 2.º: mismo estilo, grado 2."""
    def f(*a, **k):
        return dict(fn(*a, **k), grado=2)
    return f


_m2, _l2, _n2, _s2 = _g2(_a('Matemáticas')), _g2(_l), _g2(_n), _g2(_s)

GRADO_2 = [
    # Matemáticas 2.º (los objetos para contar se reusan de 1.º: manzana, naranja, lápiz, balón…)
    _m2('m2-bolsa-naranjas', 1, 'Bolsa de naranjas', 'Grupos iguales (multiplicar)', 'Una bolsa de malla con naranjas, cerrada con un nudo.'),
    _m2('m2-tienda-dona', 1, 'Tienda de doña Rosa', 'Problemas de compra', 'Una tienda de barrio colombiana con una tendera sonriente detrás del '
        'mostrador, con frascos de dulces, panes y frutas; letreros de precios en blanco.', ESCENA + ' Letreros vacíos.'),
    _m2('m2-alcancia', 3, 'Alcancía', 'Ahorrar y comparar cantidades', 'Una alcancía de cerdito de barro pintada a mano.'),
    _m2('m2-balanza-frutas', 4, 'Balanza de mercado', 'Peso', 'Una balanza de dos platos de plaza de mercado, con una piña en un plato y '
        'tres mangos en el otro, en equilibrio.'),
    _m2('m2-jarra', 4, 'Jarra de jugo', 'Capacidad', 'Una jarra transparente con jugo de mora.'),
    _m2('m2-metro-costura', 5, 'Metro de costura', 'Medir con el metro', 'Una cinta métrica de costura amarilla, enrollada a medias, sin números legibles.'),
    _m2('m2-rieles', 7, 'Rieles del tren', 'Líneas paralelas', 'Unos rieles de tren rectos que se pierden en el horizonte, sin tren, vistos desde arriba.', ESCENA),
    _m2('m2-cruce-calles', 7, 'Cruce de calles', 'Líneas perpendiculares', 'Dos calles que se cruzan en ángulo recto vistas desde arriba, '
        'con una cebra peatonal y árboles en las esquinas.', ESCENA),
    _m2('m2-ventana', 7, 'Ventana con reja', 'Horizontal y vertical', 'Una ventana con reja de barrotes verticales y horizontales.'),
    _m2('m2-collar', 8, 'Collar de cuentas', 'Patrones', 'Un collar de cuentas de colores que se repiten: rojo, azul, azul, rojo, azul, azul.'),
    _m2('m2-bolsa-canicas', 11, 'Bolsa de canicas', 'Posible e imposible', 'Una bolsa de tela abierta con canicas rojas adentro, solo rojas.'),
    _m2('m2-nubes', 11, 'Cielo nublado', '¿Va a llover?', 'Un cielo con nubes grises oscuras sobre un pueblo, a punto de llover.', ESCENA),
    _m2('m2-moneda-aire', 11, 'Lanzar una moneda', 'Cara o sello', 'La mano de Tomás lanzando una moneda dorada al aire. ' + NINOS, ESCENA),
    # Lenguaje 2.º
    _l2('l2-noticiero', 1, 'Noticiero de televisión', 'Medios masivos', 'Una presentadora de noticias en un estudio de televisión, con una '
        'pantalla detrás que muestra un mapa de Colombia sin letras.', ESCENA),
    _l2('l2-etiqueta', 2, 'Etiqueta de un producto', 'Imágenes en etiquetas', 'Una caja de cereal con dibujos de frutas y un sol en la etiqueta, '
        'sin letras.'),
    _l2('l2-cartel', 2, 'Cartel del colegio', 'Imágenes en carteles', 'Un cartel en la pared del colegio con dibujos de niños lavándose las '
        'manos, sin letras.'),
    _l2('l2-ramon-1', 3, 'Cuento: El sombrero de don Ramón (1)', 'Personajes y lugar', 'Un abuelo campesino colombiano (don Ramón) con un '
        'sombrero aguadeño grande, sentado frente a su casa de bahareque en la montaña, con su perro.', ESCENA + ' Don Ramón y el perro iguales en las 4 escenas.'),
    _l2('l2-ramon-2', 3, 'Cuento: El sombrero de don Ramón (2)', 'El problema', 'Un viento fuerte se lleva volando el sombrero de don Ramón '
        'montaña abajo; el abuelo y el perro miran sorprendidos.', ESCENA + ' Mismos personajes.'),
    _l2('l2-ramon-3', 3, 'Cuento: El sombrero de don Ramón (3)', 'Las acciones', 'Una vaca, una gallina y un niño del pueblo (Tomás) ven el '
        'sombrero colgado de un árbol de guayaba y tratan de bajarlo. ' + NINOS, ESCENA + ' Mismos personajes.'),
    _l2('l2-ramon-4', 3, 'Cuento: El sombrero de don Ramón (4)', 'El final', 'Tomás le devuelve el sombrero a don Ramón, que le regala '
        'guayabas; el perro mueve la cola. ' + NINOS, ESCENA + ' Mismos personajes.'),
    _l2('l2-receta', 6, 'Receta de arepas', 'Textos instructivos', 'Ingredientes para hacer arepas sobre una mesa: harina de maíz, agua, sal, '
        'mantequilla y un tazón.', ESCENA),
    _l2('l2-carta', 8, 'Una carta', 'Escribir cartas e invitaciones', 'Un sobre abierto con una carta escrita a mano (rayitas en lugar de letras) '
        'y un dibujo de corazón.'),
    _l2('l2-perro-ruido', 5, 'Sonido del ambiente', 'Sonidos de la lengua y del ambiente', 'Un perro ladrando junto a una campana que suena y un '
        'carro pitando, con líneas de sonido.', ESCENA),
    _l2('l2-rr', 7, 'El perro en la carretera', 'Practicar r y rr', 'Un perro corriendo detrás de un carro rojo por una carretera de montaña.', ESCENA),
    # Ciencias Naturales 2.º
    _n2('n2-estirar', 1, 'Estirar un resorte', 'Fuerza: estirar', 'Dos manos estirando un resorte metálico.'),
    _n2('n2-aplastar', 1, 'Aplastar plastilina', 'Fuerza: aplastar', 'Una mano aplastando una bola de plastilina verde sobre la mesa.'),
    _n2('n2-doblar', 1, 'Doblar papel', 'Fuerza: doblar', 'Dos manos doblando una hoja de papel por la mitad.'),
    _n2('n2-torcer', 1, 'Torcer un trapo', 'Fuerza: torcer', 'Dos manos torciendo un trapo mojado que suelta gotas.'),
    _n2('n2-arrugar', 1, 'Arrugar papel', 'Fuerza: arrugar', 'Una hoja de papel arrugada en forma de bola.'),
    _n2('n2-hielo', 2, 'Hielo', 'Estado sólido', 'Cubos de hielo en un plato.'),
    _n2('n2-agua-vaso', 2, 'Agua', 'Estado líquido', 'Un vaso de vidrio con agua.'),
    _n2('n2-vapor', 2, 'Vapor', 'Estado gaseoso', 'Una olla en la estufa hirviendo con vapor saliendo.'),
    _n2('n2-liquidos', 2, 'Agua, aceite y miel', 'Comparar líquidos', 'Tres frascos transparentes en fila: agua, aceite amarillo y miel espesa.'),
    _n2('n2-globo', 2, 'Globo inflado', 'El aire ocupa espacio', 'Un globo rojo inflado amarrado con una cinta.'),
    _n2('n2-molino', 2, 'Molino de viento', 'El aire se mueve', 'Un molino de papel de colores girando con el viento.'),
    _n2('n2-pato-patas', 3, 'Patas del pato', 'Adaptación al agua', 'Un pato nadando con las patas palmeadas visibles bajo el agua.'),
    _n2('n2-frailejon', 3, 'Frailejón', 'Plantas del páramo', 'Un frailejón del páramo colombiano con hojas peludas, entre niebla.'),
    _n2('n2-cactus', 3, 'Cactus', 'Plantas del desierto', 'Un cactus con espinas en el desierto de La Guajira.'),
    _n2('n2-mono-cola', 3, 'Mono aullador', 'Adaptación a los árboles', 'Un mono aullador rojo colgado de una rama con la cola.'),
    _n2('n2-chiguiro', 3, 'Chigüiro', 'Animales de los llanos', 'Un chigüiro (capibara) junto a un caño de los llanos.'),
    _n2('n2-planta-sin-luz', 3, 'Planta sin luz', 'Necesidades de las plantas', 'Dos materas: una planta verde y sana al sol y otra amarilla y '
        'débil dentro de una caja oscura.', ESCENA),
    _n2('n2-oruga', 4, 'Oruga', 'Ciclo de la mariposa', 'Una oruga verde comiendo una hoja.'),
    _n2('n2-crisalida', 4, 'Crisálida', 'Ciclo de la mariposa', 'Una crisálida verde colgada de una rama.'),
    _n2('n2-huevos-mariposa', 4, 'Huevos de mariposa', 'Ciclo de la mariposa', 'Huevitos de mariposa sobre una hoja verde.'),
    _n2('n2-flor-fruto', 4, 'De flor a fruto', 'Floración y fruto', 'Una rama de naranjo con flores blancas y una naranja pequeña verde creciendo.'),
    # Ciencias Sociales 2.º
    _s2('s2-antes-carretera', 1, 'El paisaje antes', 'El paisaje cambia', 'Un valle verde con un camino de herradura y una mula, sin casas.', ESCENA),
    _s2('s2-despues-carretera', 1, 'El paisaje después', 'El paisaje cambia', 'El mismo valle con una carretera pavimentada, casas, cultivos y '
        'postes de luz.', ESCENA + ' Mismo valle y mismas montañas de la imagen anterior.'),
    _s2('s2-meseta', 1, 'Meseta', 'Formas del relieve', 'Una meseta alta y plana con paredes de roca, vista de lejos.', ESCENA),
    _s2('s2-maqueta', 1, 'Maqueta del municipio', 'Representar el paisaje', 'Una maqueta escolar de plastilina con montañas, un río y casitas '
        'sobre una tabla.', ESCENA),
    _s2('s2-registro', 3, 'Registro civil', 'Fuentes de la historia familiar', 'Un documento de registro civil de nacimiento en una carpeta, con '
        'rayitas en lugar de letras y una huella.', 'Objeto centrado.'),
    _s2('s2-album', 3, 'Álbum de fotos', 'Memoria familiar', 'Sofi y su abuela mirando un álbum de fotos familiares antiguas. ' + NINOS, ESCENA),
    _s2('s2-chiva', 4, 'Chiva', 'Transporte rural', 'Una chiva (bus escalera) colombiana de colores con carga en el techo.'),
    _s2('s2-bus', 4, 'Bus', 'Transporte urbano', 'Un bus urbano moderno.'),
    _s2('s2-moto', 4, 'Moto', 'Transporte', 'Una moto roja con casco colgado.'),
    _s2('s2-bicicleta', 4, 'Bicicleta', 'Transporte', 'Una bicicleta azul.'),
    _s2('s2-mula', 4, 'Mula de carga', 'Transporte de antes', 'Una mula cargada con bultos de café.'),
    _s2('s2-canoa', 4, 'Canoa', 'Transporte por río', 'Una canoa de madera con un remo en un río.'),
    _s2('s2-metrocable', 4, 'Cable aéreo', 'Transporte por cable', 'Una cabina de cable aéreo sobre un barrio de montaña.', ESCENA),
    _s2('s2-campesino', 5, 'Campesino', 'Oficios', 'Un campesino colombiano recogiendo café con un canasto.', 'Personaje de cuerpo entero centrado.'),
    _s2('s2-panadera', 5, 'Panadera', 'Oficios', 'Una panadera sacando pan del horno.', 'Personaje de cuerpo entero centrado.'),
    _s2('s2-medica', 5, 'Médica', 'Oficios', 'Una médica con bata blanca y estetoscopio.', 'Personaje de cuerpo entero centrado.'),
    _s2('s2-pescador', 5, 'Pescador', 'Oficios', 'Un pescador con una atarraya en la orilla del río.', 'Personaje de cuerpo entero centrado.'),
    _s2('s2-conductor', 5, 'Conductor', 'Oficios', 'Un conductor de bus sonriente al volante.', 'Personaje de medio cuerpo centrado.'),
    _s2('s2-nino-trabajando', 5, 'Un niño que trabaja', 'Rechazar el trabajo infantil', 'Un niño de 8 años cargando un bulto pesado en una plaza '
        'de mercado, cansado, mientras otros niños pasan con morral hacia la escuela.', ESCENA),
    _s2('s2-casa-rural', 6, 'Vivienda rural', 'Rural y urbana', 'Una finca cafetera con casa de tapia, corredor, huerta y gallinas.', ESCENA),
    _s2('s2-tambo', 6, 'Tambo', 'Vivienda de grupos étnicos', 'Un tambo emberá de madera sobre pilotes con techo de palma, en la selva del Chocó.', ESCENA),
    _s2('s2-excluido', 8, 'Dejar a alguien por fuera', 'Reconocer la discriminación', 'Un grupo de niños jugando y una niña afrocolombiana '
        'sola mirando desde lejos, triste.', ESCENA),
    _s2('s2-incluido', 8, 'Jugamos todos', 'Aceptar a todos', 'Los mismos niños jugando a la ronda con la niña afrocolombiana, todos felices.', ESCENA),
]


def catalogo():
    return list(MATEMATICAS_1) + LENGUAJE_1 + NATURALES_1 + SOCIALES_1 + GRADO_2


def por_id(id_):
    return next((x for x in catalogo() if x['id'] == id_), None)
