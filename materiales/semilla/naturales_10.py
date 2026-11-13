"""Ciencias Naturales 10.º: una guía y un taller por cada uno de los 4 DBA: dinámica (leyes de Newton), conservación de la
energía mecánica, reacciones inorgánicas y biotecnología. Borradores para que el docente revise."""
from .base import abierta, grafica, imagen, numerica, tabla, texto, unica, unidad, vf


def unidades():
    U = {}

    U[1] = unidad(
        tema='Fuerzas y movimiento: las leyes de Newton',
        objetivo='Predecir el equilibrio o el cambio de velocidad de un cuerpo a partir de las fuerzas que actúan sobre él.',
        explora=[texto('En un bus que frena de golpe, los pasajeros se van hacia adelante. ¿Alguien los empujó?')],
        aprende=[texto('<b>1.ª ley (inercia)</b>: si la fuerza neta es cero, el cuerpo sigue en reposo o en movimiento rectilíneo uniforme. Los pasajeros siguen moviéndose cuando el bus frena.'),
                 texto('<b>2.ª ley</b>: si la fuerza neta no es cero, el cuerpo acelera: <b>F = m·a</b>. Con 10 N sobre 2 kg: a = 5 m/s².'),
                 texto('<b>3.ª ley</b>: a toda acción corresponde una reacción igual y opuesta (el remo empuja el agua y el agua empuja la canoa).'),
                 tabla([['Fuerza', 'Qué es'], ['Peso', 'w = m·g (g ≈ 9,8 m/s²)'], ['Normal', 'la superficie empuja hacia afuera'], ['Fricción', 'se opone al deslizamiento'],
                        ['Tensión', 'la que hace una cuerda']]),
                 texto('<b>Diagrama de cuerpo libre</b>: dibuja el objeto como un punto y todas las fuerzas como flechas. Si dos fuerzas de 8 N (derecha) y 3 N (izquierda) actúan, '
                       'la neta es 5 N a la derecha.')],
        recuerda=['Fuerza neta 0 → reposo o MRU.', 'F = m·a.', 'Acción y reacción actúan en cuerpos distintos.'],
        practica=[numerica('Aceleración de 4 kg con una fuerza neta de 20 N.', 5, 'm/s²'), numerica('Peso de una persona de 50 kg (g = 9,8 m/s²).', 490, 'N')],
        taller=[numerica('Fuerzas de 12 N a la derecha y 7 N a la izquierda sobre 5 kg. Aceleración.', 1, 'm/s²'),
                numerica('Un carro parte del reposo con a = 3 m/s². ¿Velocidad a los 4 s?', 12, 'm/s'),
                unica('Un libro quieto sobre la mesa tiene fuerza neta…', 'cero', ['igual a su peso', 'hacia abajo']),
                unica('El cinturón de seguridad nos protege por la ley de…', 'inercia', ['acción y reacción', 'gravitación']),
                abierta('Haz el diagrama de cuerpo libre de una caja que empujas por el piso a velocidad constante. Explica por qué la fuerza neta es cero.', 6)])

    U[2] = unidad(
        tema='Conservación de la energía mecánica',
        objetivo='Usar la conservación de la energía mecánica para predecir movimientos (caída libre, péndulo, resorte, choques) e identificar las pérdidas en sistemas no conservativos.',
        explora=[texto('En un columpio, ¿dónde vas más rápido: arriba o abajo? ¿Por qué el columpio se detiene si nadie lo impulsa?')],
        aprende=[tabla([['Energía', 'Fórmula'], ['Cinética', 'Ec = ½ m v²'], ['Potencial gravitacional', 'Ep = m g h'], ['Potencial elástica', 'Ee = ½ k x²']]),
                 texto('Sin fricción, la <b>energía mecánica</b> (Ec + Ep) se conserva: lo que se pierde de una se gana en la otra. Una pelota de 2 kg a 5 m de altura tiene Ep = 2·10·5 = '
                       '<b>100 J</b> (con g = 10 m/s²). Al llegar al suelo, Ec = 100 J → v = √(2·100/2) = <b>10 m/s</b>.'),
                 grafica({'x': [0, 1.05], 'y': [0, 110], 'nombre_x': 't (s)', 'nombre_y': 'E (J)', 'elementos': [
                     {'t': 'funcion', 'expr': '100-100x^2', 'desde': '0', 'hasta': '1', 'nombre': 'Ep'},
                     {'t': 'funcion', 'expr': '100x^2', 'desde': '0', 'hasta': '1', 'nombre': 'Ec', 'color': '#dc2626'},
                     {'t': 'funcion', 'expr': '100', 'desde': '0', 'hasta': '1', 'nombre': 'Ec + Ep', 'estilo': 'guiones', 'color': '#16a34a'}]}, 50,
                         'Caída libre desde 5 m: la suma no cambia'),
                 texto('En el <b>péndulo</b> la energía pasa de potencial (arriba) a cinética (abajo). En los sistemas <b>no conservativos</b> (fricción, choques inelásticos, deformaciones) '
                       'parte de la energía se transforma en calor, sonido o deformación: por eso el columpio se detiene.')],
        recuerda=['Em = Ec + Ep se conserva sin fricción.', 'La energía no se destruye: se transforma.'],
        practica=[numerica('Ep de 3 kg a 4 m de altura (g = 10 m/s²).', 120, 'J'), numerica('Ec de 2 kg a 6 m/s.', 36, 'J')],
        taller=[numerica('Velocidad al caer desde 20 m sin fricción (v = √(2gh), g = 10).', 20, 'm/s'),
                numerica('Energía de un resorte con k = 200 N/m comprimido 0,1 m.', 1, 'J'),
                unica('En el punto más bajo del péndulo la energía es principalmente…', 'cinética', ['potencial']),
                unica('Un carro de juguete sube menos de lo que bajó porque…', 'la fricción transformó energía en calor', ['la energía se destruyó']),
                abierta('Suelta una pelota desde 1 m y mide la altura de los rebotes. Calcula qué porcentaje de energía se pierde en cada uno y explica a dónde va.', 6)])

    U[3] = unidad(
        tema='Reacciones químicas y compuestos inorgánicos',
        objetivo='Relacionar la configuración electrónica con el comportamiento químico, balancear ecuaciones y nombrar compuestos inorgánicos.',
        explora=[texto('¿Por qué el sodio reacciona violentamente con el agua y el neón no reacciona con nada?')],
        aprende=[texto('El sodio (Na: 1s² 2s² 2p⁶ 3s¹) tiene <b>un electrón de valencia</b> que pierde con facilidad. El neón tiene su última capa llena: es estable.'),
                 imagen('d-bohr-11', 30, 'Átomo de sodio: 2, 8, 1 electrones'),
                 tabla([['Tipo de reacción', 'Ejemplo'], ['Óxido-reducción', '4Fe + 3O₂ → 2Fe₂O₃ (oxidación del hierro)'], ['Descomposición', '2H₂O₂ → 2H₂O + O₂'],
                        ['Neutralización', 'HCl + NaOH → NaCl + H₂O'], ['Precipitación', 'AgNO₃ + NaCl → AgCl↓ + NaNO₃']]),
                 texto('<b>Balancear</b> = igual número de átomos de cada elemento a ambos lados (ley de conservación de la masa): 2H₂ + O₂ → 2H₂O. Los coeficientes dan las relaciones '
                       'molares: 2 mol de H₂ producen 2 mol de H₂O.'),
                 tabla([['Función', 'Ejemplo', 'Nombre (IUPAC tradicional)'], ['Óxido', 'CaO', 'óxido de calcio'], ['Ácido', 'H₂SO₄', 'ácido sulfúrico'],
                        ['Hidróxido', 'NaOH', 'hidróxido de sodio'], ['Sal', 'NaCl', 'cloruro de sodio']])],
        recuerda=['Electrones de valencia → comportamiento químico.', 'Ecuación balanceada = masa conservada.', 'Ácido + base → sal + agua.'],
        practica=[numerica('Coeficiente del NH₃ en N₂ + 3H₂ → __NH₃.', 2), unica('HCl + NaOH → NaCl + H₂O es una reacción de…', 'neutralización', ['descomposición', 'precipitación'])],
        taller=[numerica('En CH₄ + __O₂ → CO₂ + 2H₂O, ¿qué coeficiente lleva el O₂?', 2), unica('El nombre de NaOH es…', 'hidróxido de sodio', ['óxido de sodio', 'ácido sódico']),
                numerica('¿Cuántos moles de H₂O se forman con 4 mol de H₂ (2H₂ + O₂ → 2H₂O)?', 4, 'mol'),
                unica('¿Cuántos electrones de valencia tiene el sodio?', '1', ['2', '11']),
                abierta('Pon un clavo de hierro en agua con sal durante una semana. Describe lo que pasa y escribe la ecuación balanceada de la oxidación del hierro.', 6)])

    U[4] = unidad(
        tema='Biotecnología: técnicas, usos y bioética',
        objetivo='Describir técnicas biotecnológicas, explicar sus usos en salud, agricultura e industria y debatir sus implicaciones sociales, bioéticas y ambientales.',
        explora=[texto('Hoy la insulina que usan muchas personas con diabetes la producen bacterias. ¿Cómo puede una bacteria fabricar una proteína humana?')],
        aprende=[tabla([['Técnica', 'En qué consiste', 'Ejemplo'], ['Fertilización asistida', 'unir óvulo y espermatozoide en el laboratorio', 'fecundación in vitro'],
                        ['Clonación reproductiva', 'obtener un individuo con el mismo ADN de otro', 'la oveja Dolly (1996)'],
                        ['Clonación terapéutica', 'obtener células o tejidos para tratar enfermedades', 'investigación con células madre'],
                        ['Modificación genética', 'insertar un gen en otro organismo (transgénico)', 'bacterias que producen insulina humana'],
                        ['Terapia génica', 'corregir o reemplazar un gen defectuoso en el paciente', 'tratamientos de algunas enfermedades hereditarias']]),
                 texto('La técnica <b>CRISPR-Cas9</b> permite «cortar y pegar» ADN con precisión; sus creadoras, Emmanuelle Charpentier y Jennifer Doudna, recibieron el Nobel de Química en 2020.'),
                 texto('En Colombia se siembran algodón y maíz transgénicos, y se investiga en mejoramiento de cultivos como el café y el arroz.'),
                 texto('<b>Bioética</b>: ¿quién es dueño de las semillas modificadas? ¿Es aceptable editar embriones humanos? ¿Qué pasa si un transgénico se cruza con especies silvestres?')],
        recuerda=['Biotecnología = usar seres vivos o su información genética para obtener productos.', 'Todo avance trae preguntas éticas.'],
        practica=[unica('Producir insulina humana en bacterias es un ejemplo de…', 'modificación genética', ['clonación reproductiva', 'fertilización asistida']),
                  unica('La oveja Dolly fue el resultado de…', 'clonación reproductiva', ['terapia génica'])],
        taller=[unica('Corregir un gen defectuoso en un paciente es…', 'terapia génica', ['clonación', 'fecundación in vitro']),
                vf('Un organismo transgénico tiene genes de otra especie.', True),
                unica('CRISPR-Cas9 sirve para…', 'editar el ADN con precisión', ['clonar ovejas', 'medir el pH']),
                abierta('Debate: ¿deberían permitirse los cultivos transgénicos en Colombia? Escribe un argumento a favor, uno en contra y tu postura, considerando a los campesinos y el ambiente.', 10)])
    return U
