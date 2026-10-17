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
