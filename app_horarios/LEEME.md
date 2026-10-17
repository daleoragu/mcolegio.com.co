# Generador de horarios (app de Windows)

Aplicación de escritorio del plan Premium. Funciona sin internet.

- `generador_horarios.py`: la ventana (Tkinter).
- La lógica está en `../horarios/` (`motor.py`, `nucleo.py`, `proyecto.py`) y es la misma que usa la plataforma para revisar choques al importar.
- `prueba_ventana.py`: prueba automática de la ventana.
- `construir.bat`: arma `dist\GeneradorHorarios.exe` en un PC con Windows.
- `ejemplo_datos.mch`: datos de un colegio de prueba.

El .exe se sube en la plataforma (Horarios → «Subir una versión nueva de la app», solo el superusuario) y los colegios Premium lo descargan desde Horarios.

GitHub lo construye solo con `.github/workflows/app-horarios.yml` cada vez que cambia esta carpeta: el .exe queda en la pestaña Actions → la última ejecución → «Artifacts».
