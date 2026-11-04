/* Lector de QR con la cámara del equipo, para el kiosko de asistencia y el
 * celular del jurado de votación.
 *
 *   const lector = LectorQR({video, caja, boton, selector, alLeer, alAvisar});
 *
 * Usa BarcodeDetector donde exista (Chrome, Android) y si no, jsQR (debe estar
 * cargado antes: notas/vendor/jsQR.js). El mismo código seguido frente a la
 * cámara se entrega una sola vez cada 4 segundos.
 */
(function () {
    'use strict';

    function escapar(t) { const d = document.createElement('div'); d.textContent = t; return d.innerHTML; }

    window.LectorQR = function (op) {
        const video = op.video, caja = op.caja, boton = op.boton, selector = op.selector;
        const avisar = op.alAvisar || function () {};
        const textoEncender = op.textoEncender || '<i class="fas fa-camera me-1"></i>Leer con la cámara';
        const textoApagar = op.textoApagar || '<i class="fas fa-video-slash me-1"></i>Apagar la cámara';
        const lienzo = document.createElement('canvas');
        const ctx2d = lienzo.getContext('2d', {willReadFrequently: true});
        let flujo = null, detector = null, leyendo = false, ultimo = '', ultimoEn = 0;

        function entregar(texto) {
            const ahora = Date.now();
            if (texto === ultimo && ahora - ultimoEn < 4000) return;
            ultimo = texto; ultimoEn = ahora;
            op.alLeer(texto);
        }

        async function leerCuadro() {
            if (!leyendo) return;
            if (video.readyState >= 2) {
                try {
                    let texto = null;
                    if (detector) {
                        const codigos = await detector.detect(video);
                        if (codigos.length) texto = codigos[0].rawValue;
                    } else if (window.jsQR) {
                        const ancho = 480, alto = Math.round(480 * video.videoHeight / video.videoWidth) || 360;
                        lienzo.width = ancho; lienzo.height = alto;
                        ctx2d.drawImage(video, 0, 0, ancho, alto);
                        const img = ctx2d.getImageData(0, 0, ancho, alto);
                        const qr = window.jsQR(img.data, ancho, alto, {inversionAttempts: 'dontInvert'});
                        if (qr) texto = qr.data;
                    }
                    if (texto) entregar(texto);
                } catch (e) { /* siga intentando */ }
            }
            setTimeout(() => requestAnimationFrame(leerCuadro), 120);
        }

        async function encender(idCamara) {
            apagar();
            if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
                avisar('error', 'Este navegador no deja usar la cámara (abra la plataforma con https).');
                return;
            }
            try {
                flujo = await navigator.mediaDevices.getUserMedia({
                    video: idCamara ? {deviceId: {exact: idCamara}} : {facingMode: {ideal: 'environment'}}, audio: false});
            } catch (e) {
                avisar('error', 'No se pudo abrir la cámara. Dé permiso a la cámara en el navegador.');
                return;
            }
            video.srcObject = flujo;
            await video.play();
            if (caja) caja.style.display = 'block';
            if (boton) boton.innerHTML = textoApagar;
            if ('BarcodeDetector' in window) {
                try { detector = new window.BarcodeDetector({formats: ['qr_code']}); } catch (e) { detector = null; }
            }
            leyendo = true;
            leerCuadro();
            avisar('info', op.textoListo || 'Acerque el QR a la cámara.');
            if (!selector) return;
            try {
                const camaras = (await navigator.mediaDevices.enumerateDevices()).filter(d => d.kind === 'videoinput');
                if (camaras.length > 1) {
                    const actual = flujo.getVideoTracks()[0].getSettings().deviceId;
                    selector.innerHTML = camaras.map((c, i) =>
                        `<option value="${c.deviceId}" ${c.deviceId === actual ? 'selected' : ''}>${escapar(c.label || 'Cámara ' + (i + 1))}</option>`).join('');
                    selector.classList.remove('d-none');
                }
            } catch (e) { /* sin lista de cámaras */ }
        }

        function apagar() {
            leyendo = false;
            if (flujo) flujo.getTracks().forEach(t => t.stop());
            flujo = null;
            if (caja) caja.style.display = 'none';
            if (boton) boton.innerHTML = textoEncender;
        }

        if (boton) boton.addEventListener('click', () => flujo ? apagar() : encender());
        if (selector) selector.addEventListener('change', () => encender(selector.value));
        window.addEventListener('pagehide', apagar);
        return {encender, apagar, olvidar: () => { ultimo = ''; }};
    };

    /* Un pitido corto (bien) o largo y grave (mal). */
    window.LectorQR.pitar = function (bien) {
        try {
            const ctx = new (window.AudioContext || window.webkitAudioContext)();
            const o = ctx.createOscillator(); const g = ctx.createGain();
            o.frequency.value = bien ? 880 : 220; g.gain.value = 0.15;
            o.connect(g); g.connect(ctx.destination); o.start(); o.stop(ctx.currentTime + (bien ? 0.12 : 0.35));
        } catch (e) { /* sin sonido */ }
    };
})();
