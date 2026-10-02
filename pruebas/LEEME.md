# Módulo de pruebas — mcolegio.com.co

Dos cosas en una sola app:

1. **Publicador de páginas.** Subes un `.html` suelto o un `.zip` con un sitio
   completo y queda publicado en `mcolegio.com.co/p/<nombre>/`. No hay que tocar
   el archivo. Reemplaza a Netlify para lo que necesitas.
2. **Banco de preguntas.** Un comando importa las pruebas que ya tienes en HTML
   a la base de datos: las preguntas quedan editables y las imágenes se suben
   al bucket de Spaces como archivos, en vez de ir incrustadas en base64.

Los resultados de las dos vías caen en la misma tabla y se ven en el mismo panel.

---

## Instalación

1. Copia la carpeta `pruebas/` a la raíz del proyecto (al lado de `notas/` y
   `elecciones/`).

2. En `config/settings.py`, dentro de `INSTALLED_APPS`:

   ```python
   'elecciones',
   'pruebas',     # <--- Módulo de pruebas y páginas publicadas
   ```

3. En `config/urls.py`, antes de las rutas de `notas`:

   ```python
   path('pruebas/', include('pruebas.urls', namespace='pruebas')),
   path('p/', include('pruebas.urls_publicas', namespace='paginas')),
   ```

   La ruta de `notas` es `path('', include(...))` y atrapa todo, por eso estas
   dos van **antes**.

4. Crea las tablas:

   ```bash
   python manage.py makemigrations pruebas
   python manage.py migrate
   ```

No hace falta instalar nada nuevo: usa `openpyxl` y `pillow`, que ya están en
`requirements.txt`.

---

## Publicar una página

Entra a `/pruebas/panel/` con tu usuario de administrador.

- **Publicar una página** — un archivo, con todos sus ajustes.
- **Publicar varios** — seleccionas o arrastras varios a la vez. El nombre de
  cada archivo se convierte en título y dirección, y al terminar sale la tabla
  con todos los enlaces y claves. Ojo: si subes tres archivos llamados
  `index.html`, los tres quedan como *Index*, *Index 2* e *Index 3*; conviene
  renombrarlos antes o corregir el título después.

### Un solo .html

Queda publicado tal cual en `/p/<nombre>/`.

### Un sitio completo en .zip

Se descomprime en el bucket respetando las carpetas, así que los enlaces
relativos a CSS, JavaScript e imágenes siguen funcionando. Si todo el zip
cuelga de una sola carpeta, esa carpeta se quita. Se abre por `index.html`, o
por el primer `.html` de la raíz si no hay ninguno con ese nombre.

Límites: 60 MB el zip, 200 MB ya descomprimido, 600 archivos. Solo se publican
extensiones web (html, css, js, imágenes, fuentes, audio, video, pdf); lo demás
se ignora. Las rutas que intentan salir de su carpeta hacen que se rechace el
zip completo.

Al volver a subir un zip, la versión nueva va a una carpeta con fecha y la
anterior se borra.

### Fechas y código QR

Cada página puede tener fecha de apertura y de cierre. Fuera de esa ventana el
estudiante ve un aviso de "todavía no abre" o "ya cerró"; tú como administrador
la sigues viendo para probarla.

El botón **QR** de la lista abre una hoja lista para imprimir con el código, la
dirección y los pasos para el estudiante. Se pega en el salón y entran con la
cámara del celular.

Si el archivo es una de las pruebas que envían resultados, la plataforma le
reescribe sola la línea `const ENDPOINT = '...'` para que apunte a
`/pruebas/api/<nombre>/` en vez de al script de Google. También le cambia la
`CLAVE_PANEL` por la clave que aparece en el panel.

La página se muestra dentro de un marco aislado: el HTML corre con el origen
del bucket, no con el de la plataforma, así que aunque algún día se suba un
archivo con código malicioso no puede tocar las sesiones de los usuarios.

**Para descargar informes**, los docentes entran a
`/pruebas/resultados/<nombre>/` y escriben la clave. No necesitan usuario.

---

## Importar una prueba al banco de preguntas

```bash
python manage.py importar_prueba_html "Prueba de nivelación 7.html" \
    --colegio general-santander \
    --codigo MAT7-2026
```

Opciones:

| Opción          | Para qué sirve                                                  |
|-----------------|-----------------------------------------------------------------|
| `--colegio`     | Slug del colegio. Obligatorio.                                   |
| `--codigo`      | Código de acceso. Si no lo pones, se arma con el área y el grado.|
| `--titulo`      | Por defecto usa el `<title>` del archivo.                        |
| `--area`        | `MAT`, `LEN`, `CIE`, `SOC`, `ING`, `OTR`. Se deduce del título.  |
| `--grado`       | Número del grado. También se deduce del título.                  |
| `--reemplazar`  | Si el código ya existe, borra sus preguntas y las vuelve a cargar.|

La prueba importada queda en `/pruebas/<slug>/` y sus resultados en el mismo
panel que las páginas subidas.

---

## Rutas

| Ruta                                | Quién entra                        |
|-------------------------------------|------------------------------------|
| `/p/<nombre>/`                      | Cualquiera. La página publicada.   |
| `/p/`                               | Lista pública (solo las marcadas). |
| `/pruebas/<slug>/`                  | Cualquiera. Prueba del banco.      |
| `/pruebas/resultados/<slug>/`       | Docentes, con clave.               |
| `/pruebas/resultados/<slug>/excel/` | Docentes, con clave.               |
| `/pruebas/panel/`                   | Administradores, con sesión.       |
| `/pruebas/panel/varias/`            | Administradores. Subida múltiple.  |
| `/pruebas/panel/<slug>/qr/`         | Administradores. Hoja con el QR.   |
| `/pruebas/api/<slug>/`              | Lo usan los HTML publicados.       |

---

## Notas

- El informe en Excel trae cinco hojas: resultados por estudiante, análisis por
  pregunta, competencias, respuesta por respuesta y un resumen.
- Cuando llega un resultado, la plataforma intenta amarrarlo sola con un
  estudiante matriculado comparando el nombre. Si hay dudas, lo deja
  "sin vincular" y se arregla a mano desde el panel.
- Al reescribir el ENDPOINT queda en el bucket una copia del archivo original.
  No estorba, pero puedes borrarla desde el panel de Spaces si quieres.
- Máximo 60 MB por archivo subido. Los HTML que pesen más conviene importarlos
  al banco de preguntas: las imágenes salen del archivo y se vuelven archivos
  del bucket.
- Con el Space que ya pagas (250 GiB de almacenamiento y 1.024 GiB de
  transferencia al mes) alcanzan unas 400.000 presentaciones mensuales de la
  prueba más pesada antes de generar cobro adicional.
