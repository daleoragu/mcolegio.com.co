"""Ciencias Naturales 7.º: una guía y un taller por cada uno de los 4 DBA. Borradores para que el docente revise."""
from .base import abierta, grafica, imagen, numerica, tabla, texto, unica, unidad, vf


def unidades():
    U = {}

    U[1] = unidad(
        tema='Energía mecánica: cinética y potencial',
        objetivo='Identificar la energía cinética y potencial en un movimiento, sus transformaciones y cómo se disipa en calor y sonido.',
        explora=[texto('En un columpio, ¿en qué punto vas más rápido? ¿En cuál estás más alto? ¿Por qué el columpio se detiene si nadie lo empuja?')],
        aprende=[texto('<b>Energía cinética</b>: por el movimiento, Ec = ½ m v². <b>Energía potencial gravitatoria</b>: por la altura, Ep = m g h.'),
                 texto('En el columpio, arriba es máxima la Ep y abajo la Ec: la energía se <b>transforma</b> de una forma a otra.'),
                 texto('En la realidad, parte de la energía se <b>disipa</b> por fricción con el aire y en la cadena, como <b>calor</b> y <b>sonido</b>: por eso el columpio se va deteniendo.')],
        recuerda=['Ec depende de la velocidad; Ep de la altura.', 'La energía no se crea ni se destruye: se transforma.'],
        practica=[numerica('Ep de un cuerpo de 2 kg a 5 m de altura (g = 10 m/s²), en julios.', 100, 'J'), numerica('Ec de un cuerpo de 2 kg a 3 m/s, en julios.', 9, 'J')],
        taller=[unica('En el punto más bajo del columpio es máxima la energía…', 'cinética', ['potencial']), unica('La energía que se pierde por fricción se transforma en…', 'calor y sonido', ['más velocidad']),
                numerica('Si duplico la velocidad, ¿por cuánto se multiplica la Ec?', 4), abierta('Deja caer una pelota y mide qué altura alcanza en cada rebote. Explica la pérdida de energía.', 6)])

    U[2] = unidad(
        tema='El átomo y la tabla periódica',
        objetivo='Ubicar los elementos en la tabla periódica por su número atómico y másico y representar el átomo con los modelos de Bohr y Lewis.',
        explora=[texto('¿Por qué el sodio y el potasio reaccionan parecido con el agua? Busca dónde están en la tabla periódica.')],
        aprende=[texto('<b>Número atómico (Z)</b>: protones del núcleo. <b>Número másico (A)</b>: protones + neutrones. Neutrones = A − Z.'),
                 imagen('d-bohr-11', 22, 'Sodio (Z = 11): capas 2, 8, 1'),
                 texto('La tabla periódica ordena los elementos por Z. Los de una misma <b>columna (grupo)</b> tienen los mismos electrones de valencia y se comportan parecido; las <b>filas</b> son los períodos.'),
                 texto('<b>Estructura de Lewis</b>: el símbolo con puntos que representan los electrones de valencia: el sodio tiene 1, el oxígeno 6.')],
        recuerda=['Z = protones. A = protones + neutrones.', 'Mismo grupo → propiedades parecidas.'],
        practica=[numerica('El carbono tiene Z = 6 y A = 12. ¿Cuántos neutrones tiene?', 6), numerica('¿Cuántos electrones tiene un átomo neutro de sodio (Z = 11)?', 11)],
        taller=[numerica('El oxígeno tiene Z = 8 y A = 16. ¿Cuántos neutrones?', 8), unica('El sodio y el potasio están en el mismo…', 'grupo', ['período']),
                numerica('¿Cuántos electrones de valencia tiene el sodio?', 1), abierta('Dibuja el modelo de Bohr y la estructura de Lewis del magnesio (Z = 12).', 6)])

    U[3] = unidad(
        tema='Flujos de materia y energía: fotosíntesis y respiración',
        objetivo='Relacionar la nutrición autótrofa y heterótrofa, la fotosíntesis y la respiración celular con el flujo de materia y energía en las redes tróficas.',
        explora=[imagen('n7-fotosintesis', 35), texto('¿De dónde sacan su alimento las plantas si no comen?')],
        aprende=[texto('<b>Fotosíntesis</b> (cloroplastos): dióxido de carbono + agua + luz → glucosa + oxígeno. Las plantas son <b>autótrofas</b>: fabrican su materia orgánica.'),
                 texto('<b>Respiración celular</b> (mitocondrias): glucosa + oxígeno → dióxido de carbono + agua + energía. La hacen plantas y animales.'),
                 texto('En las redes tróficas la <b>materia se recicla</b> (los descomponedores la devuelven al suelo), pero la <b>energía fluye</b> y se pierde en cada nivel como calor: '
                       'solo pasa cerca del <b>10 %</b> al siguiente nivel.')],
        recuerda=['La fotosíntesis guarda energía; la respiración la libera.', 'La materia circula; la energía fluye y se pierde.'],
        practica=[unica('Las plantas son…', 'autótrofas', ['heterótrofas']), unica('¿Qué gas libera la fotosíntesis?', 'Oxígeno', ['Dióxido de carbono'])],
        taller=[numerica('Si los productores tienen 10 000 unidades de energía, ¿cuántas llegan aprox. al consumidor primario (10 %)?', 1000),
                unica('Los hongos son…', 'heterótrofos', ['autótrofos']), vf('Las plantas también respiran.', True),
                abierta('Pon una planta acuática (elodea) al sol en un vaso con agua y observa las burbujas. ¿Qué gas son?', 6)])

    U[4] = unidad(
        tema='Ciclos del carbono, el nitrógeno y el agua',
        objetivo='Explicar la relación entre los ciclos biogeoquímicos y los efectos de la intervención humana en los ecosistemas.',
        explora=[texto('¿Qué tiene que ver la quema de bosques con el clima? ¿Y el abono de los cultivos con los ríos?')],
        aprende=[tabla([['Ciclo', 'Procesos clave', 'Intervención humana'], ['Carbono', 'fotosíntesis, respiración, descomposición, combustión', 'quema de combustibles y bosques: más CO₂'],
                        ['Nitrógeno', 'bacterias fijadoras en el suelo, plantas, descomponedores', 'exceso de fertilizantes contamina ríos'],
                        ['Agua', 'evaporación, condensación, precipitación, escorrentía', 'deforestación: erosión y menos agua en las fuentes']]),
                 texto('Los tres ciclos mantienen los suelos fértiles y los ecosistemas en equilibrio. La <b>erosión</b>, la <b>contaminación</b> y la <b>deforestación</b> los alteran.')],
        recuerda=['Los ciclos reciclan la materia del planeta.', 'Proteger bosques y suelos protege los ciclos.'],
        practica=[unica('¿Qué proceso del ciclo del carbono hacen las plantas para tomar CO₂?', 'Fotosíntesis', ['Combustión']),
                  unica('Las bacterias del suelo intervienen en el ciclo del…', 'nitrógeno', ['agua'])],
        taller=[unica('Quemar combustibles fósiles aumenta el…', 'CO₂ en la atmósfera', ['nitrógeno en el suelo']), unica('La deforestación causa…', 'erosión', ['más lluvia en el suelo protegido']),
                abierta('Propón tres acciones de tu colegio para reducir la alteración de uno de estos ciclos.', 6)])
    return U
