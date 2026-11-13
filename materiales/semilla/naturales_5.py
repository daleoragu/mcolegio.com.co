"""Ciencias Naturales 5.º: una guía y un taller por cada uno de los 4 DBA, con experimentos sencillos y seguros (pilas de 1,5 V).
Borradores para que el docente revise."""
from .base import abierta, imagen, recuadro, tabla, texto, unica, unidad, vf

SEGURIDAD = recuadro('Seguridad', '<p>Experimenta solo con pilas pequeñas (de 1,5 voltios). <b>Nunca</b> toques enchufes, cables pelados ni la corriente de la casa: '
                     '¡puede matar!</p>', estilo='reto')


def unidades():
    U = {}

    U[1] = unidad(
        tema='Circuitos eléctricos',
        objetivo='Construir circuitos simples con pila, cables, interruptor y bombillo, y solucionar fallas cuando no funcionan.',
        explora=[texto('¿Qué necesita una linterna para encender? Ábrela (sin romperla) y observa sus partes.')],
        aprende=[imagen('d-circuito', 50, 'Circuito cerrado: el bombillo enciende'), imagen('d-circuito-abierto', 50, 'Circuito abierto: no enciende'),
                 tabla([['Parte', 'Función'], ['Pila (generador)', 'da la energía'], ['Cables (conductores)', 'llevan la corriente'],
                        ['Interruptor', 'abre o cierra el circuito'], ['Bombillo, motor, timbre', 'transforman la energía en luz, movimiento o sonido']]),
                 texto('La corriente necesita un <b>camino cerrado</b> desde un polo de la pila hasta el otro. Si se interrumpe, el circuito está <b>abierto</b>.'),
                 SEGURIDAD],
        recuerda=['Circuito cerrado: funciona. Abierto: no funciona.', 'Los dispositivos deben conectarse por sus dos extremos.'],
        practica=[unica('Si el interruptor está abierto, el bombillo…', 'no enciende', ['enciende más']), unica('¿Qué parte da la energía?', 'La pila', ['El cable', 'El bombillo'])],
        taller=[unica('Un timbre transforma la energía eléctrica en…', 'sonido', ['luz', 'frío']),
                unica('Armé el circuito y no enciende. Primero reviso…', 'que los cables toquen bien los dos polos', ['el color del cable']),
                vf('Es seguro experimentar con la corriente de los enchufes de la casa.', False),
                abierta('Con una pila, dos cables y un bombillo de linterna arma un circuito. Dibújalo y señala sus partes.', 6)])

    U[2] = unidad(
        tema='Conductores y aislantes',
        objetivo='Comprobar qué materiales conducen la electricidad y cuáles son aislantes, y explicar por qué la corriente produce calor.',
        explora=[imagen('n5-materiales-conductores', 45), texto('¿Cuáles de estos objetos dejarán pasar la corriente?')],
        aprende=[texto('Abre el circuito y pon cada objeto entre los dos cables: si el bombillo enciende, el material es <b>conductor</b>; si no, es <b>aislante</b>.'),
                 tabla([['Conductores', 'Aislantes'], ['metales: cobre, hierro, aluminio (cuchara, clip, moneda)', 'plástico, caucho, madera seca, vidrio, papel']]),
                 texto('Por eso los cables son de <b>cobre</b> por dentro (conduce) y de <b>plástico</b> por fuera (aísla y nos protege).'),
                 texto('Al pasar la corriente, los materiales se <b>calientan</b>: por eso un bombillo de filamento se pone caliente y funcionan la plancha y la estufa eléctrica.'),
                 SEGURIDAD],
        recuerda=['Metales: conductores. Plástico y caucho: aislantes.', 'La corriente siempre produce algo de calor.'],
        practica=[unica('La cuchara de metal es…', 'conductora', ['aislante']), unica('¿Por qué los cables se recubren de plástico?', 'Para aislar y protegernos', ['Para que se vean bonitos'])],
        taller=[unica('El borrador es…', 'aislante', ['conductor']),
                unica('¿Qué aparato aprovecha el calor de la corriente?', 'La plancha', ['El radio de pilas apagado']),
                abierta('Prueba 6 materiales en tu circuito y haz una tabla de conductores y aislantes.', 6)])

    U[3] = unidad(
        tema='Células, tejidos, órganos y sistemas',
        objetivo='Explicar cómo se organiza el cuerpo (células → tejidos → órganos → sistemas) y relacionar la forma de las células con su función.',
        explora=[imagen('n5-celulas', 40), texto('¿Qué ves en el microscopio? ¿Sabías que tu cuerpo está hecho de millones de estas unidades?')],
        aprende=[texto('La <b>célula</b> es la unidad más pequeña de la vida. Células parecidas forman <b>tejidos</b>; los tejidos forman <b>órganos</b>; los órganos que trabajan juntos forman <b>sistemas</b>.'),
                 tabla([['Célula', 'Forma', 'Función'], ['Neurona', 'larga, con ramificaciones', 'transmitir mensajes'], ['Glóbulo rojo', 'disco pequeño y flexible', 'llevar oxígeno por la sangre'],
                        ['Célula muscular', 'alargada', 'contraerse para mover'], ['Célula de la piel', 'plana, muy unida', 'proteger']]),
                 tabla([['Sistema', 'Función'], ['Digestivo', 'transforma los alimentos'], ['Respiratorio', 'toma oxígeno y saca dióxido de carbono'],
                        ['Circulatorio', 'lleva sangre a todo el cuerpo'], ['Nervioso', 'controla y coordina'], ['Locomotor', 'permite el movimiento']]),
                 texto('Una buena <b>alimentación</b>, el <b>ejercicio</b>, el <b>descanso</b> y la <b>higiene</b> cuidan todos los sistemas.')],
        recuerda=['Célula → tejido → órgano → sistema.', 'La forma de la célula va con su función.'],
        practica=[unica('El corazón es un…', 'órgano', ['tejido', 'sistema', 'célula']), unica('¿Qué célula lleva el oxígeno?', 'El glóbulo rojo', ['La neurona'])],
        taller=[unica('Varios órganos que trabajan juntos forman un…', 'sistema', ['tejido']),
                unica('La neurona es larga y ramificada porque…', 'transmite mensajes a otras células', ['protege la piel']),
                abierta('Observa una capa delgada de cebolla con una lupa o un microscopio y dibuja lo que ves.', 6)])

    U[4] = unidad(
        tema='La nutrición: digestión, respiración y circulación',
        objetivo='Explicar el camino de los alimentos en el cuerpo y cómo trabajan juntos los sistemas digestivo, respiratorio y circulatorio.',
        explora=[imagen('n5-ejercicio', 35), texto('¿Por qué después de correr el corazón late más rápido y respiramos más rápido?')],
        aprende=[imagen('n5-digestivo', 30, 'El sistema digestivo'),
                 tabla([['Órgano', 'Qué hace'], ['Boca', 'los dientes trituran y la saliva empieza a digerir'], ['Esófago', 'lleva el alimento al estómago'],
                        ['Estómago', 'mezcla el alimento con jugos gástricos'], ['Intestino delgado', 'absorbe los nutrientes hacia la sangre'], ['Intestino grueso', 'absorbe agua y forma las heces']]),
                 texto('Los <b>dientes</b> tienen formas distintas: los incisivos cortan, los caninos desgarran y los molares trituran.'),
                 texto('La <b>sangre</b> lleva los nutrientes (de la digestión) y el <b>oxígeno</b> (de la respiración) a todas las células. Al hacer ejercicio, los músculos necesitan '
                       'más energía y oxígeno: por eso el corazón y la respiración se aceleran.')],
        recuerda=['Digestión: boca → esófago → estómago → intestinos.', 'Los tres sistemas trabajan juntos para nutrirnos.'],
        practica=[unica('¿Dónde se absorben los nutrientes?', 'En el intestino delgado', ['En el esófago', 'En la boca']),
                  unica('¿Qué dientes trituran?', 'Los molares', ['Los incisivos', 'Los caninos'])],
        taller=[unica('Después de correr el corazón late rápido porque…', 'los músculos necesitan más oxígeno', ['está enfermo']),
                unica('¿Qué sistema lleva los nutrientes a las células?', 'El circulatorio', ['El locomotor']),
                abierta('Cuenta tus pulsaciones en un minuto en reposo y después de saltar 2 minutos. Anota y explica la diferencia.', 6)])
    return U
