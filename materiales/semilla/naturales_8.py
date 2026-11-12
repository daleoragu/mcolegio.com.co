"""Ciencias Naturales 8.º: una guía y un taller por cada uno de los 5 DBA. Borradores para que el docente revise."""
from .base import abierta, imagen, numerica, tabla, texto, unica, unidad, vf


def unidades():
    U = {}

    U[1] = unidad(
        tema='Máquinas térmicas y termodinámica',
        objetivo='Explicar el funcionamiento de motores y neveras con la primera y la segunda ley de la termodinámica.',
        explora=[texto('¿Por qué el motor de una moto se calienta tanto? ¿Cómo hace la nevera para enfriar si se conecta a la corriente?')],
        aprende=[texto('<b>Primera ley</b>: la energía se conserva. El cambio de energía interna de un sistema es el calor que recibe menos el trabajo que realiza: ΔU = Q − W.'),
                 texto('<b>Segunda ley</b>: el calor fluye espontáneamente de lo caliente a lo frío, y ninguna máquina convierte todo el calor en trabajo: siempre se pierde parte.'),
                 texto('<b>Motor de combustión</b>: quema combustible (calor), los gases empujan el pistón (trabajo) y expulsa calor. <b>Nevera</b>: usa trabajo del motor para sacar calor del interior y '
                       'expulsarlo por detrás.')],
        recuerda=['ΔU = Q − W.', 'Ninguna máquina térmica es 100 % eficiente.'],
        practica=[numerica('Un gas recibe 500 J de calor y hace 200 J de trabajo. ¿Cuánto cambia su energía interna?', 300, 'J'),
                  unica('El calor fluye espontáneamente…', 'de lo caliente a lo frío', ['de lo frío a lo caliente'])],
        taller=[unica('La nevera expulsa el calor…', 'por la parte de atrás', ['hacia los alimentos']), vf('Un motor puede convertir todo el calor en trabajo.', False),
                numerica('Un motor recibe 1 000 J y hace 250 J de trabajo. ¿Qué porcentaje es su eficiencia?', 25, '%')])

    U[2] = unidad(
        tema='Reacciones químicas y enlaces',
        objetivo='Explicar cómo se recombinan los átomos en una reacción química y diferenciar los enlaces iónicos y covalentes.',
        explora=[texto('Cuando se oxida un clavo o se quema leña, ¿desaparecen los átomos o se reorganizan?')],
        aprende=[texto('En una reacción los átomos de los <b>reactivos</b> se reorganizan para formar <b>productos</b>; ninguno se crea ni se destruye: 2H₂ + O₂ → 2H₂O.'),
                 tabla([['Enlace', 'Cómo se forma', 'Ejemplo', 'Propiedades'], ['Iónico', 'un átomo cede electrones a otro (gran diferencia de electronegatividad)', 'NaCl', 'sólidos, alto punto de fusión, conducen disueltos'],
                        ['Covalente', 'los átomos comparten electrones', 'H₂O, CO₂, CH₄', 'bajo punto de fusión, muchos no conducen']]),
                 texto('Señales de un cambio químico: cambio de color, desprendimiento de gas, formación de un sólido, liberación de calor o luz.')],
        recuerda=['En una reacción, los átomos se conservan.', 'Iónico: transfiere electrones. Covalente: comparte.'],
        practica=[unica('En el NaCl el enlace es…', 'iónico', ['covalente']), unica('¿Cuál es un cambio químico?', 'La oxidación de un clavo', ['Derretir hielo'])],
        taller=[unica('En el agua (H₂O) el enlace es…', 'covalente', ['iónico']), numerica('En 2H₂ + O₂ → 2H₂O, ¿cuántos átomos de hidrógeno hay en los productos?', 4),
                abierta('Mezcla bicarbonato con vinagre y describe las señales de reacción química que observas.', 6)])

    U[3] = unidad(
        tema='El comportamiento de los gases',
        objetivo='Explicar cómo se relacionan la presión, el volumen, la temperatura y la cantidad de un gas con la teoría cinético-molecular.',
        explora=[texto('¿Por qué una bomba inflada se encoge en la nevera? ¿Por qué no se deben calentar los aerosoles?')],
        aprende=[texto('Según la <b>teoría cinético-molecular</b>, el gas son partículas en movimiento que chocan con las paredes (presión). Si se calientan, se mueven más rápido.'),
                 tabla([['Ley', 'Relación', 'Ejemplo'], ['Boyle', 'a T constante, P · V = constante', 'al apretar una jeringa tapada, sube la presión'],
                        ['Charles', 'a P constante, V aumenta con T', 'la bomba en la nevera se encoge'], ['Gay-Lussac', 'a V constante, P aumenta con T', 'un aerosol caliente puede explotar']]),
                 texto('Los gases se <b>difunden</b> (el olor del perfume llena el cuarto), se <b>comprimen</b>, se <b>dilatan</b> y <b>fluyen</b>.')],
        recuerda=['Más temperatura → partículas más rápidas.', 'Boyle: P·V constante.'],
        practica=[numerica('Un gas ocupa 4 L a 1 atm. A temperatura constante, ¿qué volumen ocupa a 2 atm?', 2, 'L'),
                  unica('El olor del perfume llena el cuarto por…', 'difusión', ['compresión'])],
        taller=[unica('La bomba se encoge en la nevera porque…', 'baja la temperatura y disminuye el volumen', ['pierde aire por un hueco']),
                numerica('A temperatura constante, 6 L a 1 atm. ¿Volumen a 3 atm?', 2, 'L'), vf('Calentar un aerosol cerrado es seguro.', False)])

    U[4] = unidad(
        tema='Sistemas que regulan el cuerpo',
        objetivo='Relacionar los sistemas excretor, inmune, nervioso, endocrino, óseo y muscular con la regulación del organismo (homeostasis).',
        explora=[texto('¿Por qué sudas cuando haces ejercicio y tiemblas cuando tienes frío?')],
        aprende=[texto('La <b>homeostasis</b> es la capacidad del cuerpo de mantener su equilibrio interno (temperatura, agua, azúcar en la sangre).'),
                 tabla([['Sistema', 'Regula…'], ['Nervioso', 'respuestas rápidas: reflejos, coordinación'], ['Endocrino', 'respuestas lentas con hormonas (la insulina regula el azúcar)'],
                        ['Excretor', 'elimina desechos y regula el agua (riñones)'], ['Inmune', 'defiende de microorganismos'], ['Óseo y muscular', 'sostén, movimiento y producción de calor']]),
                 texto('Sudar enfría el cuerpo; temblar produce calor con los músculos: ambos son mecanismos de homeostasis.')],
        recuerda=['Homeostasis: equilibrio interno.', 'Nervioso: rápido. Endocrino: lento, con hormonas.'],
        practica=[unica('¿Qué hormona regula el azúcar en la sangre?', 'La insulina', ['La adrenalina']), unica('Los riñones pertenecen al sistema…', 'excretor', ['nervioso'])],
        taller=[unica('Las vacunas entrenan al sistema…', 'inmune', ['óseo']), unica('Temblar de frío sirve para…', 'producir calor', ['perder agua']),
                abierta('Explica qué sistemas trabajan cuando corres una carrera y cómo mantienen la homeostasis.', 6)])

    U[5] = unidad(
        tema='La reproducción de los seres vivos',
        objetivo='Diferenciar la reproducción asexual y sexual en plantas y animales y su importancia para la variabilidad y la preservación de la vida.',
        explora=[texto('¿Cómo se reproduce una mata de plátano? ¿Y una gallina? ¿Qué diferencia hay?')],
        aprende=[tabla([['Tipo', 'Cómo es', 'Ejemplos', 'Resultado'], ['Asexual', 'un solo progenitor', 'esquejes, bulbos, estolones, gemación, bipartición', 'hijos iguales al progenitor'],
                        ['Sexual', 'dos progenitores, gametos', 'flores, animales', 'hijos con variabilidad']]),
                 texto('En la agricultura colombiana se usa la reproducción asexual para propagar plátano (colinos), yuca (estacas) y caña. La <b>variabilidad</b> de la reproducción sexual '
                       'ayuda a las especies a adaptarse a cambios del ambiente.')],
        recuerda=['Asexual: copias. Sexual: variedad.'],
        practica=[unica('Sembrar un tallo de yuca es reproducción…', 'asexual', ['sexual']), unica('La reproducción sexual produce…', 'variabilidad', ['hijos idénticos'])],
        taller=[unica('La bipartición ocurre en…', 'bacterias', ['mamíferos']), vf('Las flores son órganos de reproducción sexual.', True),
                abierta('Siembra un esqueje de una planta de tu casa y registra su crecimiento.', 6)])
    return U
