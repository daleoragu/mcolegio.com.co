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
