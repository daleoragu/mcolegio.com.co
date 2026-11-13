"""Ciencias Naturales 6.º: una guía y un taller por cada uno de los 5 DBA. Borradores para que el docente revise."""
from .base import abierta, imagen, recuadro, tabla, texto, unica, unidad, vf


def unidades():
    U = {}

    U[1] = unidad(
        tema='Cargas eléctricas: atracción y repulsión',
        objetivo='Cargar cuerpos por frotamiento, contacto e inducción y explicar la atracción y la repulsión entre cargas.',
        explora=[texto('Frota una bomba inflada en tu cabello y acércala a pedacitos de papel. ¿Qué pasa? ¿Por qué?')],
        aprende=[texto('La materia tiene cargas <b>positivas</b> (protones) y <b>negativas</b> (electrones). Al frotar, unos materiales ganan electrones y quedan negativos; otros los pierden y quedan positivos.'),
                 tabla([['Forma de cargar', 'Ejemplo'], ['Frotamiento', 'bomba contra el cabello, plástico con un paño'], ['Contacto', 'tocar un objeto cargado'], ['Inducción', 'acercar sin tocar: el papel se polariza y es atraído']]),
                 texto('Cargas <b>iguales se repelen</b>; cargas <b>contrarias se atraen</b>.'),
                 imagen('d-bohr-8', 22, 'Átomo de oxígeno: protones en el núcleo, electrones alrededor')],
        recuerda=['Iguales se repelen, contrarias se atraen.', 'Los electrones son los que se transfieren.'],
        practica=[unica('Dos bombas frotadas con el mismo paño se…', 'repelen', ['atraen']), unica('Al frotar se transfieren…', 'electrones', ['protones'])],
        taller=[unica('Una barra negativa y una positiva se…', 'atraen', ['repelen']), unica('Cargar un objeto sin tocarlo es por…', 'inducción', ['contacto']),
                abierta('Haz el experimento de la bomba con papel, sal y agua del grifo (un chorrito fino). Describe lo que pasa.', 6)])

    U[2] = unidad(
        tema='Temperatura, presión y propiedades de las sustancias',
        objetivo='Explicar cómo la temperatura y la presión influyen en la solubilidad, la viscosidad, la densidad y los puntos de ebullición y fusión.',
        explora=[texto('¿Por qué en Bogotá el agua hierve antes de llegar a 100 °C? ¿Por qué la miel fluye mejor caliente?')],
        aprende=[tabla([['Propiedad', 'Si sube la temperatura…'], ['Solubilidad de sólidos', 'suele aumentar (más azúcar se disuelve en agua caliente)'],
                        ['Solubilidad de gases', 'disminuye (la gaseosa caliente pierde gas)'], ['Viscosidad de líquidos', 'disminuye (la miel fluye mejor)'], ['Densidad', 'suele disminuir']]),
                 texto('<b>Presión</b>: a menor presión atmosférica, el agua hierve a menor temperatura. En Bogotá (unos 2 600 m) hierve a unos 92 °C; por eso los frijoles tardan más. '
                       'La olla a presión aumenta la presión y el agua hierve a más de 100 °C: cocina más rápido.'),
                 texto('Estas propiedades se aprovechan para <b>separar mezclas</b>: destilación (puntos de ebullición), cristalización (solubilidad).')],
        recuerda=['Más altura → menos presión → el agua hierve a menos temperatura.'],
        practica=[unica('La olla a presión cocina más rápido porque…', 'el agua hierve a más de 100 °C', ['el agua hierve a menos temperatura']),
                  unica('Una gaseosa caliente pierde gas porque…', 'la solubilidad de los gases disminuye con el calor', ['tiene más azúcar'])],
        taller=[unica('En una ciudad alta, el agua hierve…', 'a menos de 100 °C', ['a más de 100 °C']), unica('La destilación separa sustancias por su…', 'punto de ebullición', ['color']),
                abierta('Disuelve azúcar en agua fría y en agua caliente; cuenta cuántas cucharadas se disuelven en cada una.', 6)])

    U[3] = unidad(
        tema='Elementos, compuestos y mezclas',
        objetivo='Diferenciar sustancias puras (elementos y compuestos) de mezclas y reconocer los símbolos de sustancias cotidianas.',
        explora=[texto('El agua, la sal, el cobre de un cable, el aire y una ensalada: ¿cuáles son sustancias puras y cuáles mezclas?')],
        aprende=[tabla([['Clase', 'Qué es', 'Ejemplos'], ['Elemento', 'un solo tipo de átomo', 'cobre (Cu), oxígeno (O₂), hierro (Fe), oro (Au)'],
                        ['Compuesto', 'dos o más elementos unidos químicamente en proporción fija', 'agua (H₂O), sal (NaCl), dióxido de carbono (CO₂)'],
                        ['Mezcla homogénea', 'una sola fase', 'aire, agua con azúcar, bronce'], ['Mezcla heterogénea', 'varias fases', 'ensalada, agua con aceite, granito']]),
                 texto('Los compuestos solo se separan por <b>métodos químicos</b>; las mezclas, por <b>métodos físicos</b> (filtración, decantación, destilación).')],
        recuerda=['Elemento: un tipo de átomo. Compuesto: elementos unidos. Mezcla: sustancias juntas sin unirse químicamente.'],
        practica=[unica('La sal de cocina (NaCl) es…', 'un compuesto', ['un elemento', 'una mezcla']), unica('El aire es…', 'una mezcla homogénea', ['un elemento'])],
        taller=[unica('¿Cuál es el símbolo del hierro?', 'Fe', ['H', 'Hi', 'F']), unica('El agua con aceite es una mezcla…', 'heterogénea', ['homogénea']),
                unica('El oro es…', 'un elemento', ['un compuesto']), abierta('Clasifica 10 sustancias de tu casa en elementos, compuestos y mezclas.', 6)])

    U[4] = unidad(
        tema='La célula: membrana, energía y división',
        objetivo='Explicar funciones básicas de la célula (transporte de membrana, respiración celular, división) a partir de su estructura.',
        explora=[imagen('n6-celula', 40), texto('¿Qué partes reconoces? ¿Qué hace cada una?')],
        aprende=[tabla([['Estructura', 'Función'], ['Membrana plasmática', 'controla qué entra y qué sale'], ['Núcleo', 'guarda el ADN'], ['Mitocondria', 'obtiene energía (respiración celular)'],
                        ['Cloroplasto (plantas)', 'fotosíntesis'], ['Pared celular (plantas)', 'protección y forma']]),
                 texto('Transporte: <b>pasivo</b> (sin gasto de energía, como la ósmosis y la difusión) y <b>activo</b> (con gasto de energía).'),
                 texto('<b>Respiración celular</b>: glucosa + oxígeno → dióxido de carbono + agua + energía (en la mitocondria).'),
                 texto('<b>División celular</b>: la mitosis produce dos células iguales; sirve para crecer y reparar tejidos.')],
        recuerda=['La mitocondria es la «central de energía».', 'La membrana es selectiva.'],
        practica=[unica('¿Dónde ocurre la respiración celular?', 'En la mitocondria', ['En el núcleo']), unica('La ósmosis es transporte…', 'pasivo', ['activo'])],
        taller=[unica('La mitosis sirve para…', 'crecer y reparar tejidos', ['digerir']), unica('¿Qué estructura tienen las plantas y no los animales?', 'Cloroplastos', ['Membrana']),
                abierta('Pon una rodaja de papa en agua con sal y otra en agua pura. Después de una hora compara: ¿qué pasó y por qué (ósmosis)?', 6)])

    U[5] = unidad(
        tema='Clasificación de los seres vivos',
        objetivo='Clasificar los organismos en dominios y reinos según sus células, y reconocer la diversidad y el parentesco entre especies.',
        explora=[texto('¿Qué tienen en común un hongo, una bacteria, un helecho y un jaguar? ¿Cómo los agruparías?')],
        aprende=[tabla([['Dominio', 'Tipo de célula', 'Ejemplos'], ['Bacteria', 'procariota', 'bacterias del yogur'], ['Archaea', 'procariota', 'microorganismos de aguas termales'],
                        ['Eukarya', 'eucariota', 'protistas, hongos, plantas, animales']]),
                 texto('Las células <b>procariotas</b> no tienen núcleo definido; las <b>eucariotas</b> sí.'),
                 texto('Categorías taxonómicas: dominio → reino → filo → clase → orden → familia → género → especie. El nombre científico usa género y especie: <i>Tremarctos ornatus</i> (oso de anteojos).'),
                 texto('Colombia es uno de los países más biodiversos del mundo: primero en aves y orquídeas.')],
        recuerda=['Procariota: sin núcleo. Eucariota: con núcleo.', 'Nombre científico: Género especie.'],
        practica=[unica('Las bacterias tienen células…', 'procariotas', ['eucariotas']), unica('Los hongos pertenecen al dominio…', 'Eukarya', ['Bacteria'])],
        taller=[unica('En «Tremarctos ornatus», «Tremarctos» es…', 'el género', ['la especie', 'el reino']),
                vf('Colombia es uno de los países con más especies de aves del mundo.', True), abierta('Clasifica 8 seres vivos de tu entorno hasta el reino.', 6)])
    return U
