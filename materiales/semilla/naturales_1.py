"""Ciencias Naturales 1.º: una guía y una ficha por cada uno de los 4 DBA, con experiencias sencillas para hacer en el
salón o en la casa. Borradores para que el docente revise."""
from .base import abierta, imagen, recuadro, tabla, texto, unica, vf
from .matematicas_1 import u


def unidades():
    U = {}

    U[1] = u(
        tema='Conozco el mundo con mis sentidos',
        objetivo='Usar mis cinco sentidos para descubrir colores, formas, sonidos, olores, sabores, texturas y temperaturas.',
        explora=[imagen('n1-limon', 20), imagen('n1-helado', 15), texto('¿A qué sabe el limón? ¿Y el helado? ¿Cuál está frío?')],
        aprende=[texto('Tenemos <b>cinco sentidos</b>:'),
                 tabla([['Sentido', 'Órgano', 'Descubro…'], ['Vista', 'ojos', 'colores, formas y la luz'], ['Oído', 'oídos', 'sonidos fuertes y suaves'],
                        ['Olfato', 'nariz', 'olores'], ['Gusto', 'lengua', 'sabores: dulce, salado, ácido, amargo'], ['Tacto', 'piel', 'texturas y si algo está frío o caliente']]),
                 imagen('n1-ojo', 15, 'vista'), imagen('n1-oreja', 13, 'oído'), imagen('n1-nariz', 15, 'olfato'), imagen('n1-lengua', 15, 'gusto'),
                 imagen('n1-mano-tacto', 15, 'tacto'),
                 recuadro('Experimento', '<p>Deja al sol una camiseta negra y una blanca durante media hora. Tócalas: ¿cuál está más caliente?</p>', estilo='reto'),
                 imagen('l1-lupa', 15, 'Con la lupa vemos más grandes las cosas pequeñas')],
        recuerda=['Nunca pruebo ni huelo algo desconocido sin permiso de un adulto.', 'Las cosas oscuras se calientan más al sol.'],
        practica=[imagen('n1-campana', 15), unica('¿Con qué sentido descubro que la campana suena?', 'El oído', ['El gusto', 'El olfato']),
                  imagen('n1-algodon', 15), unica('¿Cómo se siente el algodón?', 'Suave', ['Áspero', 'Duro', 'Caliente'])],
        taller=[unica('¿Qué sentido uso para saber si la sopa está caliente?', 'El tacto', ['La vista', 'El oído']),
                imagen('n1-limon', 15), unica('El limón es…', 'ácido', ['dulce', 'salado']),
                unica('¿Con qué órgano olemos?', 'La nariz', ['Los ojos', 'Las orejas', 'Las manos']),
                imagen('n1-piedra', 15), unica('La piedra es…', 'dura', ['blanda', 'suave como el algodón']),
                vf('Una camiseta negra al sol se calienta más que una blanca.', True),
                abierta('Mira con una lupa (o muy de cerca) una hoja o una hormiga y dibújala.', 6)])

    U[2] = u(
        tema='¿De qué están hechas las cosas?',
        objetivo='Clasificar materiales como madera, plástico, vidrio, metal y piedra, y escoger el mejor para cada uso.',
        explora=[imagen('n1-silla-madera', 18), imagen('n1-botella-vidrio', 12), imagen('n1-cuchara', 15),
                 texto('¿De qué está hecho cada objeto? ¿Cuál se rompe si se cae?')],
        aprende=[tabla([['Material', 'Cómo es', 'Ejemplo'], ['Madera', 'dura, viene de los árboles', 'silla, mesa'],
                        ['Vidrio', 'transparente, se rompe', 'botella, ventana'], ['Metal', 'duro, brilla', 'cuchara, olla'],
                        ['Plástico', 'liviano, no deja pasar el agua', 'balde, impermeable'], ['Caucho', 'flexible, se estira', 'banda, llanta']]),
                 imagen('n1-balde-plastico', 15), imagen('n1-caucho', 15),
                 texto('Unos materiales <b>dejan pasar el agua</b> (la tela, el papel, la esponja) y otros <b>no</b> (el plástico, el caucho).'),
                 imagen('n1-esponja', 15, 'La esponja chupa el agua'), imagen('n1-impermeable', 22, 'El impermeable no deja pasar el agua')],
        recuerda=['Escogemos el material según lo que necesitamos.', 'El vidrio se rompe: lo cogemos con cuidado.'],
        practica=[unica('¿Con qué material harías un paraguas?', 'Plástico', ['Papel', 'Esponja', 'Tela de algodón']),
                  unica('¿Cuál material es transparente?', 'El vidrio', ['La madera', 'El metal'])],
        taller=[imagen('n1-cuchara', 12), unica('La cuchara es de…', 'metal', ['madera', 'vidrio']),
                imagen('n1-caucho', 12), unica('La banda de caucho es…', 'flexible', ['dura como piedra', 'transparente']),
                unica('Para secar el agua de la mesa uso…', 'una esponja', ['una cuchara', 'una piedra']),
                vf('La madera viene de los árboles.', True),
                abierta('Busca en tu casa un objeto de cada material (madera, plástico, metal) y dibújalos.', 6)])

    U[3] = u(
        tema='Los seres vivos',
        objetivo='Diferenciar los seres vivos de los objetos, conocer las partes de las plantas y cuidar a plantas y animales.',
        explora=[imagen('m1-gallina', 15), imagen('n1-piedra', 12), imagen('n1-arbol-guayacan', 18),
                 texto('¿Cuáles están vivos? ¿Cómo lo sabes?')],
        aprende=[texto('Los <b>seres vivos</b> nacen, se alimentan, respiran, crecen, se reproducen y mueren. Las piedras, los carros y los balones '
                       'son <b>objetos inertes</b>: no están vivos.'),
                 imagen('n1-planta-partes', 40, 'Partes de la planta: raíz, tallo, hojas, flor y fruto'),
                 texto('La <b>raíz</b> toma el agua, el <b>tallo</b> la lleva, las <b>hojas</b> fabrican el alimento con la luz del sol, '
                       'la <b>flor</b> se convierte en <b>fruto</b>, y el fruto guarda las semillas.'),
                 texto('<b>Ciclo de vida</b> de la gallina:'), imagen('m1-huevo', 10), imagen('n1-pollito', 13), imagen('m1-gallina', 15),
                 texto('<b>Ciclo de vida</b> de la rana:'), imagen('n1-renacuajo', 15), imagen('n1-rana', 15),
                 tabla([['Animal', 'Cubierta del cuerpo', 'Patas'], ['Gallina', 'plumas', '2'], ['Vaca', 'pelo', '4'], ['Pez', 'escamas', '0 (aletas)'],
                        ['Mariposa', 'alas con escamitas', '6']])],
        recuerda=['Los seres vivos necesitan agua, alimento y aire.', 'Cuido las plantas y los animales: no los maltrato.'],
        practica=[unica('¿Cuál es un ser vivo?', 'El perro', ['La piedra', 'El balón', 'El carro']),
                  unica('¿Qué parte de la planta toma el agua de la tierra?', 'La raíz', ['La flor', 'El fruto'])],
        taller=[unica('¿Qué cubre el cuerpo de la gallina?', 'Plumas', ['Escamas', 'Pelo']),
                unica('¿Qué viene primero en la vida de la rana?', 'El renacuajo', ['La rana grande']),
                vf('Una piedra crece y se alimenta.', False),
                imagen('n1-regando', 35), unica('¿Qué hacen Sofi y Tomás?', 'Cuidan una planta', ['Pintan', 'Juegan fútbol']),
                abierta('Siembra un frijol en un vaso con algodón húmedo y dibuja cómo va cada tres días.', 6)])

    U[4] = u(
        tema='Mi cuerpo crece y cambia',
        objetivo='Registrar cómo crece mi cuerpo, comparar las etapas de la vida y reconocer en qué me parezco a mi familia.',
        explora=[imagen('n1-bebe', 15), imagen('n1-abuela', 15), texto('¿En qué se diferencian el bebé y la abuela? ¿Tú cómo eras de bebé?')],
        aprende=[texto('Las personas pasamos por <b>etapas</b>:'),
                 imagen('n1-bebe', 12, 'bebé'), imagen('n1-nino', 12, 'niño'), imagen('n1-joven', 12, 'joven'), imagen('n1-adulto', 12, 'adulto'),
                 imagen('n1-abuela', 12, 'adulta mayor'),
                 texto('Al crecer cambian la <b>estatura</b>, el <b>peso</b> y el tamaño de las manos y los pies. No cambian el color de los ojos '
                       'ni de la piel.'),
                 imagen('n1-midiendo-estatura', 30, 'Medimos la estatura cada mes'),
                 imagen('n1-sofi-mama', 35, 'Sofi se parece a su mamá'),
                 texto('Nos parecemos a nuestra familia, pero cada persona es <b>única</b>.')],
        recuerda=['Crecer es cambiar: mi cuerpo hoy es distinto al de cuando era bebé.', 'Todos somos diferentes y todos merecemos respeto.'],
        practica=[unica('¿Qué etapa viene después de niño?', 'Joven', ['Bebé', 'Adulto mayor']),
                  unica('¿Qué NO cambia al crecer?', 'El color de los ojos', ['La estatura', 'El peso', 'El tamaño de los pies'])],
        taller=[unica('¿Quién es más alto, normalmente?', 'Un adulto', ['Un bebé', 'Un niño de 6 años']),
                vf('Mis pies serán más grandes cuando sea adulto.', True),
                abierta('Con ayuda de tu familia, mídete y pésate. Escribe tu estatura y tu peso de hoy.', 2),
                abierta('Pon tu mano sobre la hoja, dibuja su contorno y compárala con la de un adulto.', 6),
                abierta('Dibuja a alguien de tu familia y escribe en qué te pareces.', 6)])
    return U
