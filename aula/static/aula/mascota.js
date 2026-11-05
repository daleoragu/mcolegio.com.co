/* Mascota académica: el dibujo (pixel art hecho con código, diseños propios) y el control de la página.
 *
 *   Mascota.dibujar(ctx, especie, {animo, accion, t, higiene, hambre, sueno}, tamano)
 *
 * La mascota se dibuja en una cuadrícula de 32 × 32 «píxeles».
 */
(function () {
    'use strict';
    const COLORES = {
        dragon: {cuerpo: '#69db7c', oscuro: '#2f9e44', panza: '#d8f5a2', extra: '#ffd43b'},
        gato: {cuerpo: '#ffa94d', oscuro: '#d9480f', panza: '#ffe8cc', extra: '#faa2c1'},
        robot: {cuerpo: '#adb5bd', oscuro: '#495057', panza: '#dee2e6', extra: '#22b8cf'},
        buho: {cuerpo: '#a9805b', oscuro: '#6b4f35', panza: '#e3c9a8', extra: '#fd7e14'},
        ajolote: {cuerpo: '#f783ac', oscuro: '#c2255c', panza: '#ffdeeb', extra: '#e64980'},
        perro: {cuerpo: '#e6c79c', oscuro: '#8d6e4a', panza: '#fff4e0', extra: '#212529'},
    };

    function dibujar(ctx, especie, e, tam) {
        const C = COLORES[especie] || COLORES.dragon, p = tam / 32, t = e.t || 0;
        const animo = e.animo || 'feliz', dormido = e.accion === 'dormir' || animo === 'desmayada';
        const salto = animo === 'desmayada' ? 0 : Math.round(Math.sin(t * (animo === 'feliz' ? 4 : 2)) * (animo === 'feliz' ? 1 : .5));
        const px = (x, y, w, h, c) => { ctx.fillStyle = c; ctx.fillRect(Math.round(x * p), Math.round((y + salto) * p), Math.ceil(w * p), Math.ceil(h * p)); };
        const elipse = (cx, cy, rx, ry, c) => {
            for (let y = -ry; y <= ry; y++) { const ancho = Math.round(rx * Math.sqrt(Math.max(0, 1 - (y * y) / (ry * ry)))); px(cx - ancho, cy + y, ancho * 2, 1, c); }
        };
        ctx.clearRect(0, 0, tam, tam);
        // Sombra
        ctx.fillStyle = 'rgba(0,0,0,.18)'; ctx.beginPath(); ctx.ellipse(16 * p, 29.5 * p, 9 * p, 1.6 * p, 0, 0, Math.PI * 2); ctx.fill();

        // --- Partes de atrás (cola, alas, orejas) ---------------------------------------
        if (especie === 'dragon') {
            px(25, 20, 4, 2, C.oscuro); px(28, 18, 2, 3, C.oscuro); px(29, 16, 2, 2, C.extra);               // cola
            px(4, 13, 3, 6, C.oscuro); px(3, 12, 2, 3, C.oscuro); px(25, 13, 3, 6, C.oscuro); px(27, 12, 2, 3, C.oscuro); // alas
        }
        if (especie === 'gato') {
            px(8, 5, 4, 5, C.cuerpo); px(9, 6, 2, 3, C.extra); px(20, 5, 4, 5, C.cuerpo); px(21, 6, 2, 3, C.extra);  // orejas
            px(25, 21, 3, 2, C.cuerpo); px(27, 17, 2, 5, C.cuerpo); px(27, 17, 2, 1, C.oscuro); px(27, 19, 2, 1, C.oscuro);
        }
        if (especie === 'buho') { px(8, 6, 3, 4, C.oscuro); px(21, 6, 3, 4, C.oscuro); }
        if (especie === 'ajolote') {
            [[4, 10], [3, 14], [4, 18]].forEach(([x, y]) => { px(x, y, 5, 2, C.extra); px(x - 1, y - 1, 2, 2, C.extra); });
            [[23, 10], [24, 14], [23, 18]].forEach(([x, y]) => { px(x, y, 5, 2, C.extra); px(x + 5, y - 1, 2, 2, C.extra); });
            px(25, 22, 4, 2, C.cuerpo);
        }
        if (especie === 'perro') { px(5, 9, 4, 9, C.oscuro); px(23, 9, 4, 9, C.oscuro); px(25, 21, 3, 2, C.oscuro); }
        if (especie === 'robot') {
            px(15, 2, 2, 5, C.oscuro);
            px(14, 0, 4, 3, Math.floor(t * 2) % 2 && !dormido ? '#ff6b6b' : '#c92a2a');
        }

        // --- Cuerpo ------------------------------------------------------------------
        if (especie === 'robot') {
            px(6, 7, 20, 21, C.oscuro); px(7, 8, 18, 19, C.cuerpo);
            px(9, 10, 14, 9, '#0b1021');                                                          // pantalla
            px(9, 21, 14, 4, C.panza); px(11, 22, 2, 2, '#ff6b6b'); px(15, 22, 2, 2, '#ffd43b'); px(19, 22, 2, 2, '#69db7c');
        } else {
            elipse(16, 18, 11, 10, C.oscuro); elipse(16, 18, 10, 9, C.cuerpo); elipse(16, 22, 6, 5, C.panza);
        }
        if (especie === 'dragon') { px(10, 8, 2, 3, C.extra); px(20, 8, 2, 3, C.extra); }
        if (especie === 'buho') { px(14, 9, 4, 2, C.oscuro); }
        // Patitas
        if (especie !== 'robot') { px(10, 27, 4, 2, C.oscuro); px(18, 27, 4, 2, C.oscuro); }
        else { px(9, 28, 5, 2, C.oscuro); px(18, 28, 5, 2, C.oscuro); }

        // --- Cara ----------------------------------------------------------------------
        const ojoY = especie === 'robot' ? 13 : 14, ojoIzq = 11, ojoDer = 19;
        const tinta = especie === 'robot' ? C.extra : '#212529';
        if (especie === 'buho' && !dormido) {
            px(ojoIzq - 2, ojoY - 2, 6, 6, '#fff'); px(ojoDer - 2, ojoY - 2, 6, 6, '#fff');
        }
        if (animo === 'desmayada') {
            [[ojoIzq, ojoY], [ojoDer, ojoY]].forEach(([x, y]) => { px(x, y, 1, 1, tinta); px(x + 2, y, 1, 1, tinta); px(x + 1, y + 1, 1, 1, tinta); px(x, y + 2, 1, 1, tinta); px(x + 2, y + 2, 1, 1, tinta); });
        } else if (dormido) {
            px(ojoIzq, ojoY + 1, 3, 1, tinta); px(ojoDer, ojoY + 1, 3, 1, tinta);
        } else {
            const parpadeo = Math.floor(t * 10) % 37 === 0;
            const alto = parpadeo ? 1 : 2;
            px(ojoIzq + 1, ojoY + (parpadeo ? 1 : 0), 2, alto, tinta); px(ojoDer + 1, ojoY + (parpadeo ? 1 : 0), 2, alto, tinta);
            if (!parpadeo && especie !== 'robot') { px(ojoIzq + 2, ojoY, 1, 1, '#fff'); px(ojoDer + 2, ojoY, 1, 1, '#fff'); }
            if (animo === 'mal') { px(ojoIzq, ojoY - 2, 3, 1, tinta); px(ojoDer, ojoY - 2, 3, 1, tinta); }
        }
        // Mejillas
        if (animo === 'feliz' && especie !== 'robot') { px(8, ojoY + 3, 2, 1, '#ff8787'); px(22, ojoY + 3, 2, 1, '#ff8787'); }
        // Boca / pico / nariz
        const bocaY = ojoY + 4;
        if (especie === 'buho') { px(15, ojoY + 2, 2, 2, C.extra); }
        else if (especie === 'perro') { px(15, ojoY + 2, 2, 1, C.extra); }
        if (e.accion === 'comer') { px(14, bocaY, 4, 2, '#212529'); px(15, bocaY + 1, 2, 1, '#ff8787'); }
        else if (animo === 'feliz') { px(13, bocaY, 1, 1, tinta); px(14, bocaY + 1, 4, 1, tinta); px(18, bocaY, 1, 1, tinta);
            if (especie === 'perro') px(15, bocaY + 2, 2, 2, '#ff8787'); }
        else if (animo === 'regular') { px(14, bocaY + 1, 4, 1, tinta); }
        else if (animo === 'mal') { px(14, bocaY, 4, 1, tinta); px(13, bocaY + 1, 1, 1, tinta); px(18, bocaY + 1, 1, 1, tinta); }
        else { px(15, bocaY, 2, 2, tinta); }
        if (especie === 'gato' && !dormido) {
            ['#212529'].forEach(c => { px(5, ojoY + 3, 4, 1, c); px(23, ojoY + 3, 4, 1, c); px(5, ojoY + 5, 4, 1, c); px(23, ojoY + 5, 4, 1, c); });
        }

        // --- Lo que le pasa --------------------------------------------------------------
        if ((e.higiene || 100) < 30 && e.accion !== 'banar' && animo !== 'desmayada') {
            for (let i = 0; i < 3; i++) { const ox = 4 + i * 11, oy = 4 + Math.sin(t * 3 + i) * 1.5; px(ox, oy, 1, 2, '#8ce99a'); px(ox + 1, oy + 2, 1, 2, '#8ce99a'); px(ox, oy + 4, 1, 2, '#8ce99a'); }
        }
        if (dormido && animo !== 'desmayada') {
            const z = Math.floor(t * 1.5) % 3;
            for (let i = 0; i <= z; i++) { const x = 23 + i * 3, y = 5 - i * 3; px(x, y, 3, 1, '#4dabf7'); px(x + 1, y + 1, 1, 1, '#4dabf7'); px(x, y + 2, 3, 1, '#4dabf7'); }
        }
        if (animo === 'desmayada') { for (let i = 0; i < 3; i++) { const a = t * 3 + i * 2.1; px(16 + Math.cos(a) * 8, 6 + Math.sin(a) * 2, 2, 2, '#ffd43b'); } }
        if (e.accion === 'banar') {
            for (let i = 0; i < 7; i++) { const x = 6 + (i * 37 % 20), y = 26 - ((t * 8 + i * 5) % 22); ctx.strokeStyle = '#a5d8ff'; ctx.lineWidth = p * .6;
                ctx.beginPath(); ctx.arc(x * p, (y + salto) * p, p * 1.2, 0, Math.PI * 2); ctx.stroke(); }
        }
        if (e.accion === 'comer') { px(20, 24, 6, 4, '#e8590c'); px(25, 25, 3, 2, '#fff4e6'); }
        // Burbuja de lo que más necesita
        if (!e.accion && animo !== 'desmayada' && animo !== 'feliz') {
            const minimo = Math.min(e.hambre, e.sueno, e.higiene);
            px(23, 1, 9, 7, '#fff'); px(24, 8, 2, 1, '#fff');
            if (minimo === e.hambre) { px(25, 3, 4, 3, '#e8590c'); px(28, 2, 2, 2, '#fff4e6'); }
            else if (minimo === e.sueno) { px(25, 3, 3, 1, '#4dabf7'); px(26, 4, 1, 1, '#4dabf7'); px(25, 5, 3, 1, '#4dabf7'); }
            else { px(26, 2, 2, 1, '#4dabf7'); px(25, 3, 4, 3, '#4dabf7'); }
        }
    }

    window.Mascota = {dibujar, COLORES};

    // --- Control de la página de la mascota ------------------------------------------------
    document.addEventListener('DOMContentLoaded', () => {
        // Las vistas previas de la adopción y del tablero
        document.querySelectorAll('canvas[data-especie]').forEach(c => {
            const ctx = c.getContext('2d'), tam = c.width;
            const animar = () => { dibujar(ctx, c.dataset.especie, {animo: c.dataset.animo || 'feliz', t: performance.now() / 1000, hambre: 100, sueno: 100, higiene: 100}, tam); requestAnimationFrame(animar); };
            animar();
        });
        const cfgEl = document.getElementById('ms-config');
        if (!cfgEl) return;
        const cfg = JSON.parse(cfgEl.textContent);
        let estado = cfg.estado, accion = null, accionHasta = 0, ocupado = false;
        const lienzo = document.getElementById('ms-lienzo'), ctx = lienzo.getContext('2d');
        const caja = document.getElementById('ms-pregunta'), aviso = document.getElementById('ms-aviso');
        function esc(t) { const d = document.createElement('div'); d.textContent = t == null ? '' : t; return d.innerHTML; }

        function pintarEstado() {
            ['hambre', 'sueno', 'higiene'].forEach(k => {
                const b = document.getElementById('ms-' + k); if (!b) return;
                b.style.width = estado[k] + '%'; b.style.background = estado[k] < 20 ? '#e03131' : estado[k] < 45 ? '#f59f00' : '#2f9e44';
                b.parentElement.setAttribute('aria-valuenow', estado[k]);
            });
            document.getElementById('ms-dias').textContent = estado.dias;
            document.getElementById('ms-mejor').textContent = estado.mejor_racha;
            document.getElementById('ms-aciertos').textContent = `${estado.aciertos}/${estado.respondidas}`;
            document.querySelectorAll('[data-accion]').forEach(b => {
                const rean = b.dataset.accion === 'reanimar';
                b.classList.toggle('d-none', rean ? !estado.debil : estado.debil);
            });
            const nota = document.getElementById('ms-reanimar');
            if (nota) nota.textContent = estado.debil ? `${estado.nombre} se desmayó. Responda bien ${estado.para_reanimar - estado.reanimar} pregunta(s) para despertarlo.` : '';
        }
        function avisar(t, tipo) { aviso.className = 'ms-aviso ' + (tipo || ''); aviso.textContent = t; }
        async function post(url, datos) {
            const f = new FormData(); Object.entries(datos).forEach(([k, v]) => f.append(k, v));
            const r = await fetch(url, {method: 'POST', body: f, headers: {'X-CSRFToken': cfg.csrf}, credentials: 'same-origin'});
            return r.json();
        }

        document.querySelectorAll('[data-accion]').forEach(b => b.addEventListener('click', async () => {
            if (ocupado) return; ocupado = true;
            try {
                const j = await post(cfg.urlPedir, {accion: b.dataset.accion});
                estado = j.estado; pintarEstado();
                if (!j.ok) { avisar(j.mensaje, 'info'); return; }
                const p = j.pregunta;
                caja.innerHTML = `<div class="ms-q">${esc(p.texto)}</div>` + p.opciones.map((o, k) =>
                    `<button type="button" class="ms-op" data-k="${k}"><b>${'ABCD'[k]}</b> ${esc(o)}</button>`).join('');
                caja.dataset.accion = p.accion; caja.hidden = false; avisar('');
                caja.querySelector('.ms-op').focus();
            } finally { ocupado = false; }
        }));

        caja.addEventListener('click', async ev => {
            const b = ev.target.closest('.ms-op'); if (!b || ocupado) return; ocupado = true;
            try {
                const j = await post(cfg.urlResponder, {opcion: b.dataset.k});
                caja.querySelectorAll('.ms-op').forEach((x, k) => { x.disabled = true; if (k === j.correcta) x.classList.add('bien'); });
                if (!j.bien) b.classList.add('mal');
                if (j.bien && caja.dataset.accion !== 'reanimar') { accion = caja.dataset.accion; accionHasta = performance.now() + 2500; }
                estado = j.estado; pintarEstado();
                avisar(j.mensaje, j.bien ? 'bien' : 'mal');
                setTimeout(() => { caja.hidden = true; }, 1600);
            } finally { ocupado = false; }
        });

        function cuadro() {
            if (accion && performance.now() > accionHasta) accion = null;
            dibujar(ctx, estado.especie, {animo: estado.animo, accion, t: performance.now() / 1000,
                                          hambre: estado.hambre, sueno: estado.sueno, higiene: estado.higiene}, lienzo.width);
            requestAnimationFrame(cuadro);
        }
        pintarEstado(); cuadro();
        // Las necesidades bajan con el tiempo: se refresca cada minuto
        setInterval(async () => {
            if (document.hidden) return;
            const r = await fetch(cfg.urlEstado, {credentials: 'same-origin'}); const j = await r.json();
            if (j.ok) { estado = j.estado; pintarEstado(); }
        }, 60000);
    });
})();
