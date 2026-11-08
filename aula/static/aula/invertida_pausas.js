/* Aula invertida: el video de YouTube se pausa en cada pregunta con minuto.
 *
 * La página trae:
 *   #inv-config  (json_script) {video, pausas:[{i, segundo}], respondidas:[i], visto, urlProgreso, csrf}
 *   #inv-reproductor  donde va el video
 *   #inv-p-<i>        cada pregunta (dentro del formulario)
 *   #inv-capa         la ventana que aparece encima en la pausa
 *
 * Reglas: al llegar al minuto de una pregunta sin responder, el video se pausa y
 * la pregunta sale encima; al responder, sigue. No se puede adelantar más allá
 * de la siguiente pregunta pendiente (sí devolverse). Lo que va respondiendo y
 * hasta dónde vio se guardan solos, para retomar si cierra la página.
 */
(function () {
    'use strict';
    const cfg = JSON.parse(document.getElementById('inv-config').textContent);
    const pausas = cfg.pausas.slice().sort((a, b) => a.segundo - b.segundo);
    const respondidas = new Set(cfg.respondidas);
    const capa = document.getElementById('inv-capa');
    const hueco = document.getElementById('inv-capa-pregunta');
    const botonSeguir = document.getElementById('inv-seguir');
    const botonEnviar = document.getElementById('inv-enviar');
    const avisoEnviar = document.getElementById('inv-falta-video');
    let reproductor = null, visto = cfg.visto || 0, abierta = null, marcador = null, ultimoGuardado = 0;

    function bloque(i) { return document.getElementById('inv-p-' + i); }

    function pendiente() {
        return pausas.find(p => !respondidas.has(p.i)) || null;
    }

    function limite() {
        const p = pendiente();
        return p ? p.segundo : Infinity;
    }

    function respuesta(i) {
        const b = bloque(i);
        const marcada = b.querySelector('input[type=radio]:checked');
        if (marcada) return marcada.value;
        const texto = b.querySelector('textarea');
        return texto && texto.value.trim() ? texto.value.trim() : null;
    }

    function todasLasRespuestas() {
        const salida = {};
        document.querySelectorAll('[id^="inv-p-"]').forEach(b => {
            const v = respuesta(b.dataset.i);
            if (v !== null) salida[b.dataset.i] = v;
        });
        return salida;
    }

    function guardar(salida) {
        const duracion = reproductor && reproductor.getDuration ? reproductor.getDuration() : 0;
        ultimoGuardado = Date.now();
        return fetch(cfg.urlProgreso, {
            method: 'POST', credentials: 'same-origin', keepalive: !!salida,
            headers: {'Content-Type': 'application/json', 'X-CSRFToken': cfg.csrf},
            body: JSON.stringify({respuestas: todasLasRespuestas(), visto: Math.floor(visto), duracion: Math.floor(duracion)}),
        }).catch(() => {});
    }

    function actualizarEnvio() {
        const listo = pendiente() === null;
        if (botonEnviar) botonEnviar.disabled = !listo;
        if (avisoEnviar) avisoEnviar.hidden = listo;
    }

    function mostrarRespondida(i) {
        const b = bloque(i), espera = document.getElementById('inv-espera-' + i);
        if (b) b.classList.remove('d-none');
        if (espera) espera.remove();
    }

    function abrir(p) {
        if (abierta !== null) return;
        abierta = p.i;
        const b = bloque(p.i);
        marcador = document.createElement('div');
        b.before(marcador);
        b.classList.remove('d-none');
        hueco.appendChild(b);
        capa.classList.remove('d-none');
        const primero = b.querySelector('input, textarea');
        if (primero) setTimeout(() => primero.focus(), 50);
    }

    function seguir() {
        if (abierta === null) return;
        const i = abierta, b = bloque(i);
        if (respuesta(i) === null) {
            b.classList.remove('inv-sacudir'); void b.offsetWidth; b.classList.add('inv-sacudir');
            return;
        }
        respondidas.add(i);
        marcador.replaceWith(b);
        mostrarRespondida(i);
        capa.classList.add('d-none');
        abierta = null;
        actualizarEnvio();
        guardar();
        if (reproductor) reproductor.playVideo();
    }

    function vigilar() {
        if (!reproductor || !reproductor.getCurrentTime) return;
        const t = reproductor.getCurrentTime();
        const lim = limite();
        if (t > lim + 1) {                       // se adelantó: vuelve a la pregunta pendiente
            reproductor.seekTo(lim, true);
            return;
        }
        if (t > visto && t <= lim + 0.5) visto = t;
        const p = pendiente();
        if (p && t >= p.segundo - 0.3 && abierta === null) {
            reproductor.pauseVideo();
            visto = Math.max(visto, p.segundo);
            abrir(p);
        }
        if (Date.now() - ultimoGuardado > 15000 && reproductor.getPlayerState() === 1) guardar();
    }

    botonSeguir.addEventListener('click', seguir);
    // Al enviar, va también hasta dónde vio el video.
    const formulario = document.getElementById('inv-form');
    if (formulario) formulario.addEventListener('submit', () => {
        [['visto', Math.floor(visto)], ['duracion', Math.floor(reproductor && reproductor.getDuration ? reproductor.getDuration() : 0)]]
            .forEach(([nombre, valor]) => {
                const campo = document.createElement('input');
                campo.type = 'hidden'; campo.name = nombre; campo.value = valor;
                formulario.appendChild(campo);
            });
    });
    capa.addEventListener('keydown', ev => {
        if (ev.key === 'Enter' && ev.target.tagName !== 'TEXTAREA') { ev.preventDefault(); seguir(); }
    });
    window.addEventListener('pagehide', () => guardar(true));

    cfg.respondidas.forEach(mostrarRespondida);
    actualizarEnvio();

    window.onYouTubeIframeAPIReady = function () {
        reproductor = new YT.Player('inv-reproductor', {
            host: 'https://www.youtube-nocookie.com',
            videoId: cfg.video,
            // Sin pantalla completa: la pregunta tiene que poder salir encima.
            playerVars: {rel: 0, fs: 0, playsinline: 1, modestbranding: 1, origin: location.origin, widget_referrer: location.origin, start: Math.max(0, Math.floor(Math.min(visto, limite())) - 2)},
            events: {
                onReady: () => setInterval(vigilar, 250),
                onStateChange: ev => {
                    if (ev.data === 0) {               // terminó
                        visto = reproductor.getDuration();
                        guardar();
                    } else if (ev.data === 2) {
                        guardar();
                    }
                },
            },
        });
    };
    const api = document.createElement('script');
    api.src = 'https://www.youtube.com/iframe_api';
    document.head.appendChild(api);

    // Para las pruebas automáticas.
    window.InvPausas = {abrir, seguir, pendiente, limite, respondidas, guardar,
        estado: () => ({visto: visto, duracion: reproductor && reproductor.getDuration ? reproductor.getDuration() : 0,
                        abierta: abierta, ahora: reproductor && reproductor.getCurrentTime ? reproductor.getCurrentTime() : 0}),
        ir: s => { if (reproductor && s <= limite()) reproductor.seekTo(s, true); }};
})();
