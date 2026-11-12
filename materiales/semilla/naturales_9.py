"""Ciencias Naturales 9.º: una guía y un taller por cada uno de los 6 DBA. Borradores para que el docente revise."""
from fractions import Fraction as F

from .base import abierta, grafica, imagen, numerica, tabla, texto, unica, unidad, vf


def unidades():
    U = {}

    U[1] = unidad(
        tema='Describir y predecir el movimiento',
        objetivo='Describir el movimiento rectilíneo uniforme y uniformemente acelerado con gráficas y predecirlo con ecuaciones.',
        explora=[texto('Un bus avanza siempre a 20 m/s; un carro arranca desde 0 y acelera 2 m/s cada segundo. ¿Quién va adelante a los 10 s? ¿Y a los 30 s?')],
        aprende=[texto('<b>MRU</b>: velocidad constante, x = v·t. <b>MRUA</b>: aceleración constante desde el reposo, x = ½ a t², v = a t.'),
                 grafica({'x': [0, 30], 'y': [0, 900], 'nombre_x': 't (s)', 'nombre_y': 'x (m)', 'elementos': [
                     {'t': 'funcion', 'expr': '20x', 'desde': '0', 'hasta': '30', 'nombre': 'bus (MRU)'},
                     {'t': 'funcion', 'expr': 'x^2', 'desde': '0', 'hasta': '30', 'nombre': 'carro (MRUA)', 'color': '#dc2626'}]}, 50, 'Posición contra tiempo'),
                 texto('A los 10 s: bus 200 m, carro 100 m. A los 30 s: bus 600 m, carro 900 m. Se encuentran cuando 20t = t² → <b>t = 20 s</b> (400 m).')],
        recuerda=['MRU: recta en posición–tiempo. MRUA: parábola.'],
        practica=[numerica('¿Dónde está el bus a los 15 s?', 300, 'm'), numerica('¿Qué velocidad tiene el carro a los 10 s (v = a t)?', 20, 'm/s')],
        taller=[numerica('¿En qué segundo el carro alcanza al bus?', 20, 's'), numerica('Un objeto en MRU recorre 150 m en 5 s. ¿Velocidad?', 30, 'm/s'),
                unica('Una gráfica de posición–tiempo que es una parábola indica…', 'movimiento acelerado', ['reposo', 'velocidad constante'])])

    U[2] = unidad(
        tema='Ácidos y bases',
        objetivo='Reconocer la acidez y la basicidad como propiedades químicas, medirlas con indicadores y relacionarlas con la vida y la industria.',
        explora=[texto('El limón, el jabón, el vinagre y el bicarbonato: ¿cuáles son ácidos y cuáles básicos? ¿Cómo lo averiguarías?')],
        aprende=[texto('Según <b>Arrhenius</b>, los ácidos liberan H⁺ en agua y las bases OH⁻. Según <b>Brønsted-Lowry</b>, los ácidos donan protones y las bases los aceptan.'),
                 tabla([['pH', 'Carácter', 'Ejemplos'], ['0–6', 'ácido', 'limón (≈2), vinagre (≈3), café (≈5)'], ['7', 'neutro', 'agua pura'], ['8–14', 'básico', 'bicarbonato (≈8), jabón (≈10), lejía (≈13)']]),
                 texto('Indicador casero: el agua de <b>repollo morado</b> se vuelve roja con ácidos y verde-amarilla con bases.'),
                 texto('Importancia: el pH de la sangre (≈7,4), del suelo para los cultivos, de los productos de limpieza.')],
        recuerda=['pH < 7 ácido; = 7 neutro; > 7 básico.'],
        practica=[unica('El limón es…', 'ácido', ['básico']), unica('Un pH de 10 es…', 'básico', ['ácido', 'neutro'])],
        taller=[unica('Con agua de repollo morado, un ácido se vuelve…', 'rojo', ['verde']), unica('El pH de la sangre es aproximadamente…', '7,4', ['2', '12']),
                abierta('Prepara indicador de repollo morado y prueba 6 sustancias de tu casa. Haz una tabla con el color y si son ácidas o básicas.', 8)])

    U[3] = unidad(
        tema='Soluciones: soluto, solvente y concentración',
        objetivo='Calcular la concentración de soluciones y predecir qué pasa al cambiar la temperatura, la presión o las cantidades.',
        explora=[texto('Si echas 2 cucharadas de azúcar en un vaso de agua y luego 6, ¿cuál queda más dulce? ¿Hasta cuándo se disuelve?')],
        aprende=[texto('Una <b>solución</b> tiene <b>soluto</b> (lo que se disuelve) y <b>solvente</b> (lo que disuelve, casi siempre agua).'),
                 texto('<b>Porcentaje en masa</b> = masa de soluto ÷ masa de la solución × 100. 20 g de sal en 180 g de agua → 20 ÷ 200 × 100 = <b>10 %</b>.'),
                 texto('Factores: más temperatura disuelve más sólidos; agitar y triturar acelera; la presión aumenta la solubilidad de los gases (la gaseosa). Si ya no se disuelve más, está <b>saturada</b>.')],
        recuerda=['%m = soluto ÷ solución × 100.', 'Saturada: no admite más soluto.'],
        practica=[numerica('20 g de sal en 180 g de agua. ¿Porcentaje en masa?', 10, '%'), unica('En el agua azucarada, el azúcar es…', 'el soluto', ['el solvente'])],
        taller=[numerica('5 g de azúcar en 45 g de agua. ¿Porcentaje en masa?', 10, '%'), numerica('¿Cuántos gramos de sal hay en 300 g de una solución al 5 %?', 15, 'g'),
                unica('Si caliento una solución saturada de azúcar, puedo…', 'disolver más azúcar', ['disolver menos']), vf('Agitar acelera la disolución.', True)])

    U[4] = unidad(
        tema='Genética mendeliana',
        objetivo='Predecir con cuadros de Punnett y probabilidades las proporciones de características heredadas.',
        explora=[texto('¿Por qué dos padres de ojos cafés pueden tener un hijo de ojos azules?')],
        aprende=[texto('Cada característica la determinan dos <b>alelos</b> (uno de cada progenitor). El <b>dominante</b> (A) se expresa aunque haya uno solo; el <b>recesivo</b> (a) solo si hay dos (aa).'),
                 tabla([['', 'A', 'a'], ['A', 'AA', 'Aa'], ['a', 'Aa', 'aa']]),
                 texto('Cruce Aa × Aa: <b>3/4</b> muestran el rasgo dominante y <b>1/4</b> el recesivo (proporción 3 : 1). Genotipos: 1 AA : 2 Aa : 1 aa.'),
                 texto('Después de Mendel se descubrieron la <b>dominancia incompleta</b>, los alelos múltiples (grupos sanguíneos) y la herencia ligada al sexo (daltonismo).')],
        recuerda=['Genotipo: los alelos. Fenotipo: lo que se ve.', 'Aa × Aa → 3 : 1.'],
        practica=[unica('En Aa × Aa, ¿qué fracción será aa?', '1/4', ['1/2', '3/4']), unica('Un individuo Aa muestra el rasgo…', 'dominante', ['recesivo'])],
        taller=[unica('En AA × aa, los hijos serán…', 'todos Aa', ['la mitad aa']), unica('En Aa × aa, ¿qué fracción será aa?', '1/2', ['1/4', '3/4']),
                unica('Los grupos sanguíneos son un ejemplo de…', 'alelos múltiples', ['herencia mendeliana simple']), abierta('Explica con un cuadro de Punnett el caso de los padres de ojos cafés con un hijo de ojos azules.', 6)])

    U[5] = unidad(
        tema='El ADN y las proteínas',
        objetivo='Explicar cómo se expresa la información genética del ADN en proteínas y fenotipos, y cómo cambia por mutaciones.',
        explora=[imagen('n9-adn', 30), texto('¿Cómo puede una molécula tan pequeña determinar el color de tus ojos?')],
        aprende=[texto('El <b>ADN</b> es una doble hélice formada por nucleótidos con cuatro bases: <b>A, T, C, G</b> (A con T, C con G). Un <b>gen</b> es un fragmento de ADN con instrucciones.'),
                 texto('<b>Transcripción</b>: el ADN se copia en ARN mensajero. <b>Traducción</b>: los ribosomas leen el ARN de a tres bases (codones) y arman la <b>proteína</b>. Las proteínas '
                       'producen los rasgos (fenotipos), como el pigmento de los ojos.'),
                 texto('Una <b>mutación</b> es un cambio en el ADN; puede ser neutra, dañina o útil. Las mutaciones son fuente de variabilidad.')],
        recuerda=['ADN → ARN → proteína → rasgo.', 'A–T y C–G.'],
        practica=[unica('En el ADN, la adenina (A) se une con…', 'timina (T)', ['citosina (C)', 'guanina (G)']), unica('Los ribosomas hacen la…', 'traducción', ['transcripción'])],
        taller=[unica('Si una hebra es ATGC, la complementaria es…', 'TACG', ['ATGC', 'GCAT']), vf('Todas las mutaciones son dañinas.', False),
                abierta('Arma un modelo de ADN con materiales reciclables y explica el apareamiento de bases.', 6)])

    U[6] = unidad(
        tema='El origen de las especies',
        objetivo='Analizar la selección natural y el ancestro común como teorías científicas sustentadas en evidencias.',
        explora=[texto('¿Por qué algunas bacterias se vuelven resistentes a los antibióticos?')],
        aprende=[texto('<b>Selección natural</b> (Darwin y Wallace): en una población hay <b>variación</b>; los individuos con rasgos que les ayudan a sobrevivir y reproducirse en su ambiente dejan más '
                       'descendientes; con el tiempo, esos rasgos se vuelven más comunes.'),
                 texto('Ejemplo: al usar mal los antibióticos, sobreviven las bacterias resistentes y se multiplican.'),
                 tabla([['Evidencia', 'Qué muestra'], ['Fósiles', 'formas de vida que cambiaron a lo largo del tiempo'], ['Anatomía comparada', 'estructuras homólogas (el brazo humano y el ala del murciélago)'],
                        ['Embriología', 'semejanzas en los embriones'], ['Genética (ADN)', 'parentesco entre especies']]),
                 texto('Todas las especies comparten un <b>ancestro común</b> si retrocedemos lo suficiente en el tiempo.')],
        recuerda=['Variación + supervivencia diferencial + herencia = selección natural.'],
        practica=[unica('El brazo humano y el ala del murciélago son estructuras…', 'homólogas', ['iguales en función']),
                  unica('Las bacterias resistentes aumentan por…', 'selección natural', ['decisión de las bacterias'])],
        taller=[unica('¿Qué evidencia muestra el parentesco entre especies a nivel molecular?', 'El ADN', ['El color']), vf('La selección natural actúa sobre la variación existente.', True),
                abierta('Explica, con el ejemplo de los antibióticos, por qué hay que terminar el tratamiento que receta el médico.', 6)])
    return U
