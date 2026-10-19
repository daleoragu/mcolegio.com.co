# Generador de horarios (app de Windows)

Aplicación de escritorio del plan Premium. Funciona sin internet.

- `generador_horarios.py`: la ventana (Tkinter).
- La lógica está en `../horarios/` (`motor.py`, `nucleo.py`, `proyecto.py`) y es la misma que usa la plataforma para revisar choques al importar.
- `prueba_ventana.py`: prueba automática de la ventana.
- `construir.bat`: arma `dist\GeneradorHorarios.exe` en un PC con Windows.
- `ejemplo_datos.mch`: datos de un colegio de prueba.

El .exe se sube en la plataforma (Horarios → «Subir una versión nueva de la app», solo el superusuario) y los colegios Premium lo descargan desde Horarios.

GitHub lo construye solo con `.github/workflows/app-horarios.yml` cada vez que cambia esta carpeta: el .exe queda en la pestaña Actions → la última ejecución → «Artifacts».

## Versión 2.1 (ideas tomadas del manual de GHC)

- **Prioridades** (pestaña 2): cada criterio de 0 a 10 (5 = normal): huecos de docentes y de cursos, repetir materia, «mejor no», repartir parejo la semana, días con una sola clase, día libre, primeras y últimas horas.
- **«Mejor no» fuerte** (naranja) además de «no puede» y «mejor no»: el generador lo evita con más fuerza, pero sin volverlo prohibido.
- **Día libre**: el docente que lo pide queda con un día sin clases si la carga lo permite.
- **Horas sin clase de un curso** (pestaña 3, al final de la lista): por ejemplo, un curso que sale temprano.
- **Disponibilidad desde la plataforma**: si la coordinación la pidió en Horarios → «Pedir a los docentes su disponibilidad», viene en el .mch y se carga sola (✉ en la lista de docentes, con la nota de cada uno).
- **Actividades complementarias** (pestaña 5): atención a padres, planeación… se ubican en los huecos de cada docente, dentro de su permanencia.
- **Acompañamiento de descansos** (pestaña 5): zonas y cuántos docentes por zona; se reparten parejo entre los que tienen clase justo antes o después.
- **Revisión de datos** con ✖ errores, ⚠ avisos y ℹ información (espacios llenos, bloques que no caben, simultáneas con el mismo docente, demasiados «no puede»…).
- **Lo que más costó ubicar**: cuando quedan horas sin ubicar, la lista dice qué clases chocaron más, para revisar sus condiciones.
- **Intercambiar fichas**: arrastre una ficha sobre otra del mismo curso y se cambian de lugar si las dos caben.
- **Excel** con hojas nuevas: Docentes, Libres por hora (sirve para reemplazos), Descansos y Actividades.

## Versión 2.2

- **«Si tiene la 7.ª no tiene la 1.ª»** (pestaña 2): si un docente tiene la hora B un día, no tiene la hora A ese mismo día (dentro de la misma jornada). Puede ser obligatoria o «si se puede», y en la pestaña 3 se puede quitar a un docente en particular. Si la jornada tiene menos horas, la «7.ª» es la última.
- **Las reuniones de área cuentan dentro de la permanencia** y para esa regla: un docente con reunión a la última hora no queda con clase a la primera, y sus clases de ese día caben con la reunión dentro de sus horas de permanencia.

## Versión 2.3

- **Colores al escoger una ficha**: verde = libre; amarillo = ocupada por otra clase que se puede quitar (reemplazar, y la otra vuelve a «Fichas por ubicar», o intercambiar); rojo = no se puede (hay una ficha fijada 🔒 o una condición que no se rompe). Con la ficha escogida basta tocar una casilla verde para ponerla.
- **Varias pestañas** («➕ Otra pestaña») y **ventanas aparte** («🗗 Abrir en ventana aparte») para ver al tiempo cursos y docentes; todas muestran el mismo horario y se actualizan juntas.
- «Fijar 🔒 lo que ubico a mano» es ahora una casilla (apagada al empezar): así lo que se arma a mano se puede reemplazar sin quitar candados uno por uno.

## Versión 2.4

- **Prioridad a los bloques** (pestaña 2, Reglas generales): las materias de 2 horas o más (el número se puede cambiar) van en bloques de 2 horas seguidas (2+2+1…). Si un bloque no cabe, se parte y queda en el informe. Una materia con sus propios bloques (por ejemplo «1+1+1» o «3+2») usa los suyos.
- Nueva prioridad «Que las horas de una materia el mismo día queden seguidas»: si un bloque se tuvo que partir, el generador procura dejar las horas juntas.

## Versión 2.5

- **Bloques en cualquier orden**: si una clase de 3 horas es 2+1 y ya está puesta la hora suelta, lo que falta es el bloque de 2 (y al revés). Vale para el generador, «Completar lo que falta» y el armado a mano.
- **Botón «✂ Dividir en bloques automáticamente»** (pestaña 1): pone 2+2+1… a las clases que no tienen bloques; «Quitar todos los bloques» los borra.
- **Fichas de bloque**: en «Fichas por ubicar» sale una ficha por cada bloque que falta («Matemáticas · bloque 2 h», «Matemáticas · 1 h») y se ubican en el orden que usted quiera; el bloque se pone completo (los colores miran las dos horas). Clic derecho en la ficha: «Ubicar de a una hora».

## Versión 2.6

- **Filtros** por grado, área y docente (y «Buscar») en la tabla de clases; por área en Materias; por grado y área en la lista de Docentes y cursos; y en cada pestaña del horario (cursos por grado, docentes por área).
- **¿Bloques partidos por el descanso?** La primera vez que se genera con bloques, la app pregunta si un bloque puede quedar con una hora antes del descanso y otra después. Se cambia en Reglas.
- **Pantalla del horario a lo ancho**: sin barra lateral; arriba los botones (generar, completar, guardar, Excel, renombrar, quitar, pestañas, avisos) y abajo las cuadrículas, que ocupan toda la pantalla. La app abre maximizada.
- **Cada pestaña escoge su horario**: así se comparan alternativas lado a lado (o en ventanas aparte) y se edita cualquiera de ellas.
- Los avisos se muestran con el botón «⚠ Avisos».

## Versión 2.7

- **Multigrado (Escuela Nueva)** (pestaña 4): grupos de cursos que ven clase juntos con el mismo docente y en la misma aula. La misma materia del mismo docente va a la misma hora para todo el grupo; al armar a mano, poner, mover o quitar una ficha hace lo mismo con los otros cursos del grupo. La plataforma lo entiende al importar (no lo cuenta como choque).
- **Horario por días de ciclo**: si la jornada está «por días de ciclo» en la plataforma (Día 1… Día N, hasta 20), el generador trabaja con esos días. La plataforma lleva qué Día le toca a cada fecha y lo corre cuando no hay clase.

## Versión 2.8

- **Horas extra escogidas**: en la pestaña 1, doble clic en «Hora extra» y escriba cuántas de las horas de esa clase son extra (por ejemplo 2 de 5). Las extra no cuentan en la permanencia.
- **Permanencia mayor con horas extra** (pestaña 2): con horas extra, el día del docente puede alargarse hasta N horas más de su permanencia (2 por defecto; 0 = sin límite). En la pestaña 3 se puede poner otro valor para un docente.

## Versión 2.9

- **Días largos según las horas extra**: un docente con horas extra puede tener tantos días largos (que pasan de su permanencia, o con la 1.ª y la última hora cuando esa regla está) como horas extra tenga. Con 2 horas extra, máximo 2 días; con 4, máximo 4. El generador prefiere que las extra queden dentro de la jornada normal (nueva prioridad en Reglas).

## Versión 3.0

- **¿Por qué faltan horas?** Si al generar o completar quedan clases sin ubicar, se abre un asistente con tres caminos:
  1. **Más tiempo**: completar lo que falta o generar de nuevo con el doble de segundos.
  2. **Cambiar condiciones**: sugerencias concretas para las clases que faltan y las que más costó ubicar (pasar «no puede» a «mejor no», subir la permanencia de un docente, quitar el día libre o el máximo de horas seguidas, dejar partir un bloque, volver «si se puede» la regla de la 1.ª y la última, ampliar un espacio, soltar una reunión fija…). Se marcan las que se aceptan y se aplican con un clic; quedan en Reglas y Docentes, donde se pueden deshacer.
  3. **Consejos** generales y el botón **Ubicar a mano**, que abre las fichas.
- El asistente también se abre con el botón **🩺 ¿Por qué faltan horas?** de la pestaña 6.
- **Para solo cuando ya no mejora**: aunque se pongan muchos segundos, el generador termina cuando ya ubicó todo y lleva un rato sin mejorar el horario (más o menos un 10 % del tiempo, máximo 3 minutos). Si quedan clases por fuera, usa el tiempo para volver a intentarlo sacando otras, y se queda con el mejor intento.
- **⏹ Detener**: para en cualquier momento y se queda con lo mejor que llevaba.
- **Ver en vivo**: mientras genera, la cuadrícula va mostrando las materias que ya ubicó y cuántas horas faltan (solo se mira; al terminar ya se puede mover).
- **Tamaño (zoom)**: botones 🔍− / 100% / 🔍+ arriba (todas las cuadrículas), − / + en cada cuadrícula, o Ctrl + rueda del mouse encima de una cuadrícula. Si se agranda mucho, aparece la barra para correr de lado.
- **Varias cuadrículas en una ventana**: escoja 2, 4, 6 o 9 y toque «▦ en una ventana». Cada cuadrícula escoge su horario, curso o docente (arranca cada una con un curso distinto) y se puede arrastrar entre ellas si muestran el mismo horario.
- **↶ Deshacer** (o Ctrl+Z): deshace los últimos cambios hechos a mano (hasta 40).

## Versión 3.1

- **Compensar días largos** (pestaña 2, Reglas): un docente **sin horas extra** puede tener un día más largo que su permanencia (hasta 1 hora más, o lo que escoja; o con la 1.ª y la última hora) **si la semana no pasa de permanencia × días**. Ej.: 6 h × 5 días = 30 h: dos días de 7 h se pagan con un día de 4 h o con dos días de 5 h, como mejor encaje. Un día sin clases cuenta 0 h.
- En **⚠ Avisos** se ve cada docente con días largos: «29 h 10 de 30 h · largos: Lunes 6 h 55, Jueves 6 h 55 · cortos: Martes 4 h 10…». Si al armar a mano la semana se pasa, aparece como choque hasta que se acorte algún día.
- El asistente «¿Por qué faltan horas?» la sugiere cuando la permanencia está trabando el horario.
- **Docentes que no viven en el municipio** (pestaña 3, casilla 🚌 en cada docente): si les tocan días largos, el generador busca que la compensación les quede **entrando más tarde el lunes** (primeras horas libres) **o saliendo más temprano el viernes** (últimas horas libres). La primera vez que se genera con días largos, el programa pregunta si hay docentes así. En ⚠ Avisos se ve: «(viaja): días largos suman 2 h de más · Viernes sale después de la 4.ª hora». Su importancia se ajusta en Prioridades.

## Versión 3.2

- **Bloquear horas por área** (pestaña 3, al final de la lista, en verde): toque las casillas: rojo = las clases de las materias del área **no van** a esa hora; amarillo = mejor no. Vale para todos los cursos y docentes del área (ej.: que Educación Física no vaya a la 1.ª hora).
- **Docente que viaja: escoge su preferencia**: junto a la casilla 🚌, escoja si compensa **el lunes (entrar más tarde)**, **el viernes (salir más temprano)** o **lo que mejor encaje**.

## Versión 3.3

- **Filtros** en «3. Docentes y cursos» y en «1. Datos»: por **grado**, **área**, **materia** y **docente**.
- **Docente que viaja**: la compensación se escoge como **lunes: primeras horas libres**, **viernes: últimas horas libres**, o cualquiera de las dos.
- **Colores** en la cuadrícula del horario: en cada vista, «Color por área» o «Color por docente», con la leyenda arriba.
- **Reuniones de área**:
  - Al «Crear una por área» se abre la ventana **Jefes de área** para escoger el jefe de cada una (también con su botón).
  - **🤝 Buscar hora en el horario armado**: con el horario que se está viendo, busca la hora de cada reunión donde estén libres la mayoría (el jefe siempre) y dice qué clases habría que mover. **Acomodar** deja la reunión fija en esa hora, saca esas clases y las vuelve a ubicar en otra hora.
  - Si un docente queda con clase a la hora de su reunión, sale como choque. Al completar un horario, las reuniones automáticas esquivan las clases que ya están puestas.

## Versión 3.4

- **Reuniones de área a la misma hora**: en «4. Reuniones», la casilla «Todas las reuniones de área el mismo día y a la misma hora» busca una sola hora para todas (donde puedan todos los jefes y la mayoría). También vale para «Buscar hora en el horario armado».
- **Soltar fichas fijadas 🔒**: Ctrl + clic marca varias fichas (quedan con borde azul) → «🔓 Soltar marcadas» o «🔒 Fijar marcadas». «🔓 Soltar todo» suelta todas las del horario (siguen en su lugar, pero el generador ya las puede mover).
- **Completar ya no fija todo**: «Completar lo que falta» respeta lo que estaba puesto, pero solo deja fijadas 🔒 las que usted había fijado.
- **PDF**: «📄 PDF por separado (.zip)» guarda un .zip con un PDF por curso (carpeta Cursos) y uno por docente (carpeta Docentes). «📄 PDF todo junto» guarda dos PDF: todos los cursos y todos los docentes, una hoja cada uno. Con colores por área.
- La lista de «3. Docentes y cursos» ahora va pegada a la izquierda, más ancha y con barra.

## Versión 3.4.1

- La barra de la pestaña 6 va en **tres filas**: (1) generar · (2) **⚠ Avisos, 🩺 ¿Por qué faltan horas?, ↶ Deshacer, fijar/soltar** y los colores verde/amarillo/rojo · (3) guardar, Excel, PDF, pestañas y tamaño. Así nada queda por fuera de la pantalla.
- Si al generar quedan horas sin ubicar o choques, los avisos se abren solos.

## Versión 3.5

- **Cada docente va a una sola reunión de área.** «Crear una por área» pone a cada docente en la reunión de su área principal (donde dicta más horas).
- **👥 Reunión de cada docente** (pestaña 4): una fila por docente para escoger a qué reunión va, o «(ninguna)». Muestra sus áreas; la ★ marca la principal.
- **Participantes de cada reunión**: en «Editar», se marcan o desmarcan. Si se marca a uno que está en otra reunión, pasa a esta (y deja de ser jefe de la anterior).
- **Los que no pueden asistir reciben el acta** (el acta se maneja en la plataforma, no en este programa). Por eso la «segunda reunión con el jefe» queda apagada en las reuniones nuevas; se puede encender en «Editar».

## Versión 4.0 — ventanas nuevas, salones y estilo moderno

- **Estilo nuevo**: tema tipo Windows 11, menú lateral, tarjetas blancas y cuadrículas de bloqueo en verde (puede) y rojo (no). Arriba, el botón **Generar horario ⚡**.
- **Menú lateral** con las ventanas en orden:
  1. **Tiempos y marco**: las horas de cada jornada (vienen de la plataforma; no se cambian aquí) y una cuadrícula para dejar horas **sin clase para todo el colegio** (izada, jornada pedagógica…).
  2. **Materias**: la tabla de reglas de cada materia y, al escoger una, **su salón** y **sus horas bloqueadas**. Abajo, las **áreas** con su cuadrícula.
  3. **Grados y cursos**: horas sin clase y **salón propio** de cada curso.
  4. **Profesores**: disponibilidad, reglas propias y **salón propio**.
  5. **Salones**: cómo se usan (ninguno / cada curso con su salón / cada profesor con su salón), lista de salones, cuántos cursos caben a la vez, agrupaciones y **horas en que no se puede usar**. Botón «Crear un salón por curso».
  6. **Bloques y agrupaciones**: tarjetas con Bloque A, B… y salas especiales (sistemas, laboratorios, biblioteca, aula múltiple). A una materia, profesor o curso se le puede dar «cualquiera de» una agrupación.
  7. Asignación académica (con la columna **Salón** de cada clase) · 8. Reglas y prioridades · 9. Reuniones · 10. Actividades y descansos · 11. Horario.
- **Prioridad del salón**: el de la clase > el de la materia > el del profesor > el del curso. Ningún salón recibe más cursos a la vez de los que caben; cada clase queda con su salón (se ve en la cuadrícula, en el PDF y en el Excel). En el Horario hay una vista nueva **«Por salón»**.
- Si un salón traba el horario, el asistente «¿Por qué faltan horas?» sugiere ampliarlo.
