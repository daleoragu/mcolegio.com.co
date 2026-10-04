# Salón Digital

Herramientas para docentes dentro de mcolegio.com.co. Un profesor —de cualquier
colegio, no solo de los que usan tu plataforma— crea su cuenta, acredita que es
docente, publica sus actividades y recibe los resultados de sus estudiantes.

Reemplaza a la app `pruebas`. Es la misma base, girada para que todo cuelgue de
un **usuario** y no de un colegio.

---

## Instalación

Esto cambia la estructura de la base de datos, así que el orden importa.

### 1. Borrar las tablas de la app vieja

Con el código actual todavía en su sitio, **antes de reemplazar nada**:

```bash
python manage.py migrate pruebas zero
```

Y lo mismo en producción, desde la consola de tu app en DigitalOcean. Las tablas
están vacías, así que no se pierde nada.

### 2. Reemplazar la carpeta

Borra `pruebas/` y copia `salon_digital/` en su lugar, al lado de `notas/`.

### 3. Actualizar la configuración

En `config/settings.py`, dentro de `INSTALLED_APPS`:

```python
'elecciones',
'salon_digital',   # <--- reemplaza a 'pruebas'
```

En `config/urls.py`, antes de las rutas de `notas`:

```python
path('salon_digital/', include('salon_digital.urls', namespace='salon_digital')),
path('p/', include('salon_digital.urls_publicas', namespace='paginas')),
```

### 4. Crear las tablas

```bash
python manage.py makemigrations salon_digital
python manage.py migrate
```

El archivo `salon_digital/migrations/0001_initial.py` que esto genera **tiene que
entrar en el commit**, igual que la vez pasada.

### 5. Variable de entorno

En el `.env` y en las variables de la app en DigitalOcean:

```
SALON_DOMINIO_PUBLICO=mcolegio.com.co
```

Fija el dominio que se graba dentro de las páginas publicadas. Si se deja vacía,
se usa la dirección desde la que entras — útil en local, peligroso en producción.

### 6. Tu propia cuenta

Entra a `/salon_digital/` con tu usuario de administrador. Como ya tienes sesión
pero no cuenta de Salón Digital, te pide los datos. Después, desde el admin de
Django, pon tu cuenta en estado `verificada` y plan `ilimitado`.

---

## Cómo funciona

### Para el docente

| Qué | Dónde |
|---|---|
| Página de entrada y planes | `/salon_digital/` |
| Crear cuenta | `/salon_digital/registro/` |
| Sus páginas | `/salon_digital/panel/` |
| Su cuenta, verificación y plan | `/salon_digital/panel/cuenta/` |
| Su página pública | `/p/<usuario>/` |
| Una actividad publicada | `/p/<usuario>/<pagina>/` |

### Para quien administra

| Qué | Dónde |
|---|---|
| Revisar documentos y activar planes | `/salon_digital/revision/` |

Solo entran usuarios con `is_staff`.

### Grupos (opcionales)

Un grupo es un curso: nombre, código de seis letras y lista de estudiantes. El
docente lo crea en `/salon_digital/grupos/` y pega la lista copiándola de su
planilla — acepta "Apellidos, Nombres" y también "Apellidos Nombres", y descarta
la numeración de la primera columna.

**No son obligatorios.** Cada página escoge cómo se identifica quien entra:

| Opción | Qué pasa |
|---|---|
| El estudiante escribe su nombre | Como antes. Sin grupos de por medio. |
| Puede entrar por grupo o escribir su nombre | Se le pide el código; si no lo tiene, entra a mano. |
| Solo quien esté en un grupo | Sin código no entra. |

Cuando entra por grupo, el nombre que llega al informe es el de la lista, no el
que escriba en la actividad. Eso acaba con el mismo estudiante apareciendo como
"Juan Pérez", "juan perez" y "JUAN P.".

El navegador recuerda quién es, así que solo se identifica la primera vez.

### Comentarios

Cada página puede llevar comentarios al pie, sin que el docente toque su HTML:
Salón Digital le pega el bloque al final cuando la sirve. Tres modos: apagados,
abiertos (se ven enseguida) o moderados (esperan aprobación). El dueño los
administra desde el panel.

Trae un campo señuelo contra robots y marca con una etiqueta los comentarios del
propio autor de la página.

### Botón de Google Classroom

Cada página publicada muestra el botón para compartirla en Classroom. No necesita
API ni permisos: es la etiqueta que publica Google. Un docente que ya usa
Classroom manda la actividad a su clase de un clic.

### Ayuda para los docentes

En `/salon_digital/ayuda/` hay tres caminos para que un docente prepare un archivo
que mande resultados:

1. **Una plantilla descargable** (`static/salon_digital/plantilla-prueba.html`):
   una prueba completa de tres preguntas, lista para cambiarle el contenido.
2. **Un prompt** para pedirle el archivo a ChatGPT, Claude o Gemini, con el
   contrato de envío escrito en detalle.
3. **El motor suelto** (`static/salon_digital/salon.js`) para conectar un archivo
   que el docente ya tenga.

El contrato es: el archivo declara `const ENDPOINT = '';` y `const CLAVE_PANEL = '';`
—que Salón Digital completa al subirlo— y envía por POST el mismo objeto que ya
usaban las pruebas originales. `SalonDigital.armar()` lo construye y
`SalonDigital.enviar()` lo manda, con cola en `localStorage` si no hay internet.

### Verificación

Al registrarse, la cuenta queda en prueba de 15 días pero **no puede publicar**
hasta que suba su constancia laboral, diploma o carné y una persona lo apruebe
desde la bandeja de revisión. Si se rechaza, el docente ve la observación y
puede volver a enviar.

### Planes y límites

| Plan | Páginas | Resultados/mes | Tamaño de archivo | Días |
|---|---|---|---|---|
| Prueba | 3 | 300 | 25 MB | 15 |
| Mensual | 30 | 5.000 | 60 MB | 30 |
| Anual | 60 | 15.000 | 60 MB | 365 |
| Ilimitado | sin tope | sin tope | 200 MB | sin vencimiento |

Se cambian en `LIMITES`, al principio de `models.py`.

No hay pasarela de pagos. Cuando llegue el Nequi, desde `/salon_digital/revision/`
escoges el plan y le das **Activar**: la fecha de vencimiento se extiende desde
la que tenía, así que renovar antes de tiempo no le quita días a nadie.

Al vencer, la cuenta deja de poder publicar y de recibir resultados nuevos, pero
sus páginas y sus datos siguen ahí.

---

## Seguridad del contenido subido

Tres capas, en orden de importancia:

**La verificación del docente.** Es la defensa principal. Quien publica tiene
nombre, documento y una persona que lo revisó. Nadie monta ese teatro para una
estafa.

**La política del navegador.** Las páginas se sirven desde Django con una
cabecera `Content-Security-Policy` que impide enviar datos a cualquier sitio que
no sea Salón Digital: `connect-src 'self'`, `form-action 'self'` e `img-src`
limitado. Aunque alguien copie la pantalla de un banco, lo que escriba la víctima
no tiene a dónde llegar.

Lo que esta capa **no** cubre: una página todavía puede navegar a otra dirección
llevando datos en la URL. Por eso la verificación va primero y esto va segundo.

**El escaneo automático.** Al subir, se busca en el HTML campos de contraseña,
menciones de entidades financieras, formularios que apunten afuera. No bloquea:
marca la página con una alerta para que la mires. Se evade con facilidad, así que
trátalo como un recordatorio, no como un filtro.

Los archivos que acompañan a un sitio `.zip` —imágenes, CSS, JavaScript— se
redirigen al bucket en vez de pasar por Django, para no cargar el servidor. Solo
el HTML se sirve directamente, que es donde importa la cabecera.

---

## Comandos

Importar una prueba HTML al banco de preguntas:

```bash
python manage.py importar_prueba_html "Prueba de nivelación 7.html" \
    --usuario davidramos --codigo MAT7-2026
```

Reapuntar el ENDPOINT de las páginas ya publicadas (si cambia el dominio):

```bash
python manage.py recalcular_endpoints --dominio mcolegio.com.co --simular
```

---

## Lo que queda pendiente

- Entrar con Google o Facebook.
- Los motores de juego, para que el docente arme actividades sin programar.
- Rúbricas y planilla.
- Reportes por correo (la plataforma todavía no tiene envío de correo configurado).
- Pasarela de pagos.
