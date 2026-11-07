# App «Mi Salón Virtual» (plan individual)

La app propia de Mi Salón Virtual, separada de la app de cada colegio. Tiene su nombre, su ícono
y sus accesos directos (Mis aulas, Grupos, Eventos, Colegas).

| Equipo | Cómo se instala | ¿Qué hace falta? |
|---|---|---|
| **Android** | Botón «Instalar» en Chrome, **o** la APK, **o** Google Play | Nada para Chrome. Para la APK, generarla una vez (abajo). Para Play: cuenta de Google Play Console (USD 25, un solo pago) |
| **iPhone / iPad** | Safari → Compartir → «Agregar a inicio» | Nada. Para el App Store: cuenta de Apple Developer (USD 99 al año) y un Mac con Xcode |
| **Computador** | Chrome o Edge → «Instalar» | Nada |

Página para los docentes: **https://mcolegio.com.co/salon_digital/app/instalar/**
(tiene QR, los pasos de cada equipo, el botón de la APK y el de activar avisos).

---

## 1. App web instalable (ya está lista)

Al desplegar esta versión ya funciona; no hay que hacer nada más.

- Manifiesto propio: `/salon_digital/manifest.webmanifest` (id `/salon_digital/app/`, distinto del de los colegios).
- Íconos en `salon_digital/static/salon_digital/app/`.
- El ícono abre `/salon_digital/app/`: si el docente ya entró, lleva a Mis aulas; si no, al ingreso.
- Avisos al celular: los mismos de la plataforma (Web Push). En iPhone funcionan con la app agregada a inicio y iOS 16.4 o más nuevo.

## 2. APK de Android

La APK no es otra aplicación aparte: es la misma app web dentro de una «Trusted Web Activity» de Chrome.
Por eso cada mejora que se suba a la plataforma llega sola a la APK, sin publicar otra versión.

### Opción A — PWABuilder (la más fácil, sin instalar nada, unos 10 minutos)

1. Despliegue esta versión en DigitalOcean.
2. Entre a **https://www.pwabuilder.com** y escriba `https://mcolegio.com.co/salon_digital/app/instalar/`.
3. Toque **Package for stores → Android → Generate package** y llene:
   - **Package ID:** `co.com.mcolegio.misalon`
   - **App name:** `Mi Salón Virtual` · **Short name:** `Mi Salón`
   - **Start URL:** `/salon_digital/app/?fuente=apk`
   - **Signing key:** «Create new».
4. Descargue el .zip. Trae:
   - `*.apk`: para instalar directo o compartir.
   - `*.aab`: para Google Play.
   - `signing.keystore` y `signing-key-info.txt`: **la llave de la app. Guárdela para siempre, en dos lugares seguros.** Sin ella no se puede actualizar la app en Play.
   - `assetlinks.json`.
5. En DigitalOcean → App → Settings → Environment Variables, agregue:
   - `ANDROID_SHA256` = la huella SHA-256 que trae `signing-key-info.txt`, del tipo `AB:CD:…`.
     Si publica en Play, agregue también, separada por coma, la huella de **Play App Signing** (Play Console → Integridad de la app).
   - `ANDROID_PAQUETE` = `co.com.mcolegio.misalon` (solo si usó otro Package ID).
6. Revise que **https://mcolegio.com.co/.well-known/assetlinks.json** muestre la huella. Así la APK abre a pantalla completa; sin ese archivo, Android le pone arriba una barra con la dirección.
7. Para el botón **«Descargar la APK»** de la página de instalar, haga una de estas dos cosas:
   - Copie la APK a `salon_digital/static/salon_digital/app/MiSalon.apk` y súbala con el código.
   - Súbala a cualquier sitio y ponga su enlace en la variable `SALON_APK_URL`.
8. **Google Play** (opcional): cree la app en Play Console, suba el `.aab` y, cuando esté publicada, ponga su enlace
   en `SALON_PLAY_URL`. Así sale el botón «Descargar en Google Play».

### Opción B — Bubblewrap (en su computador, con Node y Java)

En esta carpeta está `twa-manifest.json` ya configurado:

```bash
npm install -g @bubblewrap/cli
```

```bash
cd apps/misalon
```

```bash
bubblewrap build
```

La primera vez, Bubblewrap ofrece descargar el kit de Android y le pide aceptar sus licencias.
Al final deja `app-release-signed.apk` y `app-release-bundle.aab`. Siga los pasos 5 a 8 de arriba.
Para ver la huella SHA-256 de la llave:

```bash
keytool -list -v -keystore misalon-firma.keystore -alias misalon
```

## 3. iPhone y iPad

- **Hoy, sin costo:** Safari → Compartir → «Agregar a inicio». Queda con el ícono de Mi Salón, a pantalla completa
  y con avisos (iOS 16.4 o más nuevo). Apple no permite instaladores por fuera del App Store; esta es la forma libre.
- **App Store (opcional):** hace falta la cuenta **Apple Developer Program** (USD 99 al año) y un **Mac con Xcode**.
  1. En PWABuilder → **iOS → Generate package** (Bundle ID `co.com.mcolegio.misalon`). Descarga un proyecto de Xcode.
  2. Ábralo en el Mac, firme con su cuenta de desarrollador y súbalo con Xcode («Archive → Distribute App»).
  3. Para probar antes de publicar: **TestFlight** (hasta 10 000 docentes con un enlace de invitación).
  4. Cuando esté publicada, ponga su enlace en `SALON_IOS_URL`. Así sale el botón «Descargar en el App Store».

  Ojo: Apple rechaza a veces las apps que «son solo una página web» (regla 4.2). Ayuda mostrar en la revisión
  lo propio de la app: avisos, el chat entre colegas y los juegos. Es mejor explicarlo en las notas para el revisor.

## Variables de entorno (todas opcionales)

| Variable | Para qué |
|---|---|
| `ANDROID_SHA256` | Huella(s) SHA-256 de la llave de la APK, separadas por coma (assetlinks) |
| `ANDROID_PAQUETE` | Package ID de la APK (por defecto `co.com.mcolegio.misalon`) |
| `SALON_APK_URL` | Enlace para descargar la APK |
| `SALON_PLAY_URL` | Enlace de la app en Google Play |
| `SALON_IOS_URL` | Enlace de la app en el App Store |
