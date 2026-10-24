"""Modelos de valoración pedagógica por nivel (los de la I.E.T. General Santander) y el del MEN.

Cómo se escribe un modelo (lo mismo que ve y edita la orientadora):
  ## NOMBRE          empieza un grupo (una tabla)
  # Subtítulo        un subtítulo dentro del grupo
  ? Pregunta         pregunta abierta (se responde con texto)
  * Pregunta: a | b  se escoge UNA opción
  + Pregunta: a | b  se pueden marcar VARIAS opciones
  cualquier otra     afirmación que se valora con la escala del modelo
"""

_FAMILIA = """## DINÁMICA FAMILIAR
+ Grupo poblacional o enfoque diferencial: Víctima del conflicto armado | Extranjero | Discapacidad | LGBTIQ+ | Medida de protección | Indígena | Afro / Palenquero | Raizal | Rom
* Tipo de familia: Nuclear | Extensa | Reconstituida | Protección | Homoparental | Monoparental | Otra
* Tipo de interacción entre padres o cuidadores y el estudiante: Permisivo | Asertivo | Autoritario | Sobreprotección
? Descripción de la dinámica familiar (roles, quién acompaña lo académico, con quién pasa la mayor parte del tiempo)
"""

_TRAYECTORIA = """## ASPECTOS RELEVANTES DE LA TRAYECTORIA EDUCATIVA
? Resumen de la trayectoria académica del estudiante
? ¿Ha repetido algún grado escolar? ¿Cuál y motivo?
? ¿Ha recibido algún tipo de apoyo escolar, tutorías o refuerzos? ¿Dónde?
? ¿Participa en actividades extracurriculares? ¿Inciden en su desempeño académico?
? ¿Cuáles son los hábitos de estudio y rutinas del estudiante?
"""

PREESCOLAR = _FAMILIA + """## ÁMBITO COGNOSCITIVO
Responde con interés a los estímulos del entorno (visual, auditivo, táctil).
Mantiene la atención en una actividad por un periodo adecuado para su edad.
Participa activamente en actividades grupales.
Inicia y finaliza las actividades de manera autónoma.
Comprende y sigue instrucciones simples sin necesidad de repetición constante.
Realiza sus trabajos con esfuerzo y muestra interés por la calidad de los mismos.
Recuerda y evoca información reciente en conversaciones y actividades.
Demuestra interés por las actividades de lectura y exploración de textos.
Observa los objetos a una distancia adecuada sin necesidad de acercarlos demasiado.
Identifica sonidos y responde de manera adecuada a ellos.
Interactúa verbalmente con docentes y compañeros utilizando frases completas.
Pronuncia los sonidos del habla de manera comprensible para su edad.
Usa el lenguaje verbal más que los gestos para comunicarse.
Presta atención cuando se le habla y responde de manera oportuna.
## ÁMBITO PSICOMOTOR
Se desplaza con seguridad sin caerse frecuentemente.
Corre y camina sin dificultad para su edad.
Sube y baja escaleras alternando los pies sin necesidad de apoyo.
Coordina sus movimientos para evitar tropiezos con objetos en su camino.
Cambia de una actividad a otra sin presentar resistencia excesiva.
Agarra objetos pequeños utilizando la pinza digital (pulgar e índice).
Controla sus trazos al dibujar, marcar líneas y unir figuras.
Sujeta correctamente el lápiz y herramientas para su edad.
## ÁMBITO PSICOSOCIAL
Se desenvuelve con autonomía sin requerir apoyo constante del maestro.
Se adapta con facilidad a cambios en la rutina o situaciones nuevas.
Respeta sus pertenencias y las de los demás sin morderlas o dañarlas.
Se muestra integrado al ambiente escolar sin signos de inadaptación prolongada.
Regula sus emociones y reacciones ante situaciones cotidianas.
Expresa verbalmente sus sentimientos y emociones.
Comparte y juega con otros niños en actividades grupales.
Interactúa con adultos, respondiendo cuando se le habla y buscando comunicación.
""" + _TRAYECTORIA

PRIMARIA = _FAMILIA + """## ÁMBITO COGNOSCITIVO
Mantiene la atención en actividades y clases sin distraerse con facilidad.
Regula su tiempo y esfuerzo en las actividades escolares, evitando fatiga excesiva o cambios bruscos de tarea.
Comprende y sigue instrucciones sin necesidad de repetición constante.
Recuerda la información reciente y la aplica en sus actividades.
Realiza tareas escolares de manera autónoma sin requerir asesoría constante.
Demuestra curiosidad y disposición para aprender y explorar su entorno.
Escribe de manera clara y organizada de acuerdo con su nivel escolar.
Lee textos cortos con fluidez y comprende lo que ha leído.
Comprende enunciados matemáticos y resuelve problemas con lógica.
Requiere pocas repeticiones para asimilar nuevos conocimientos.
Mantiene una postura adecuada al leer y escribir, sin necesidad de acercar excesivamente los objetos.
Se expresa verbalmente con claridad y usa un vocabulario adecuado a su edad.
Pronuncia correctamente los sonidos del habla sin dificultades evidentes de articulación.
Se comunica de manera fluida sin bloqueos o tartamudeo frecuente.
## ÁMBITO PSICOMOTOR
Se desplaza con seguridad sin tropezar o caer frecuentemente.
Corre, salta y camina alternando ambos pies de manera coordinada.
Mantiene una postura adecuada al estar de pie y sentado.
Controla sus movimientos al escribir, dibujar y realizar trazos.
Manipula objetos pequeños con precisión (lápiz, tijeras, cubiertos).
Presenta movilidad funcional en todas las partes del cuerpo.
Responde adecuadamente a estímulos auditivos y visuales en su entorno.
Se comunica de manera efectiva sin limitaciones físicas evidentes.
Percibe y reacciona adecuadamente ante sonidos fuertes y estímulos auditivos.
## ÁMBITO PSICOSOCIAL
Regula sus emociones y maneja el enojo sin recurrir a peleas constantes.
Se muestra sociable y participa en actividades grupales sin aislarse.
Expresa sus emociones sin recurrir a conductas autolesivas (morderse, golpearse).
Sigue normas y respeta la autoridad sin manifestar conductas oposicionistas persistentes.
Realiza sus actividades con autonomía sin depender en exceso de docentes o compañeros.
Se adapta con facilidad a situaciones nuevas y a cambios en la rutina escolar.
Juega e interactúa con sus compañeros sin aislarse ni evitar la interacción.
Se relaciona positivamente con niños de diferentes edades sin agresividad.
""" + _TRAYECTORIA

BACHILLERATO = _FAMILIA + """## ÁMBITO COGNOSCITIVO
Mantiene la atención en clases y se concentra en sus actividades escolares.
Organiza su tiempo y esfuerzo para completar sus trabajos sin fatiga excesiva.
Realiza sus actividades académicas con fluidez y en el tiempo esperado.
Trabaja de manera autónoma sin necesidad de asesoría constante.
Comprende instrucciones con facilidad sin necesidad de repetición constante.
Completa sus trabajos escolares de manera organizada y sin omitir partes importantes.
Se aproxima a los nuevos contenidos con confianza y sin temor a enfrentar desafíos.
Mantiene una postura adecuada al leer y escribir sin necesidad de acercarse excesivamente.
Percibe y distingue formas y detalles de manera clara en diferentes distancias.
Escribe con claridad y estructura adecuada a su nivel académico.
Lee con fluidez y comprensión, identificando ideas principales en textos.
Comprende el contenido de los textos y relaciona la información de manera adecuada.
Resuelve problemas matemáticos aplicando lógica y comprensión del enunciado.
Asimila nuevos conocimientos sin requerir una constante repetición.
Se comunica de manera clara y efectiva sin limitaciones físicas evidentes.
Utiliza un vocabulario variado y acorde a su edad en sus expresiones orales y escritas.
Se expresa con fluidez sin bloqueos o tartamudeo frecuente.
Pronuncia correctamente los sonidos del habla sin dificultades evidentes de articulación.
Transmite ideas y mensajes con claridad, siendo comprendido por sus interlocutores.
Redacta textos con coherencia y estructura clara.
## ÁMBITO PSICOMOTOR
Adopta una postura adecuada para el aprendizaje, con control y estabilidad en sus movimientos.
Se desplaza con seguridad sin tropezar o perder el equilibrio con frecuencia.
Realiza actividades físicas sin dificultades en la coordinación motriz.
Participa en ejercicios físicos y se desenvuelve con normalidad en educación física.
Se moviliza de manera independiente sin requerir apoyo de dispositivos.
Manipula objetos pequeños con precisión (lápiz, colores, cuaderno, herramientas).
Realiza actividades de motricidad fina como abrocharse botones o amarrarse los zapatos sin dificultad.
Ejecuta trabajos manuales con precisión y destreza.
## ÁMBITO PSICOSOCIAL
Mantiene estabilidad emocional y regula sus cambios de ánimo a lo largo del día.
Maneja el enojo de manera adecuada sin recurrir a la agresión física.
Se adapta con facilidad a diferentes situaciones de convivencia.
Interactúa con sus compañeros de manera positiva y participa en actividades grupales.
Respeta normas y reglas dentro del entorno escolar.
Expresa sus emociones y sentimientos de manera abierta y asertiva.
Reflexiona antes de actuar y evita conductas impulsivas.
Evalúa riesgos y consecuencias antes de involucrarse en actividades de alto peligro.
Se relaciona con otros de manera pacífica, sin recurrir a conductas agresivas.
Se muestra motivado e interesado en diversas actividades escolares y extracurriculares.
""" + _TRAYECTORIA
