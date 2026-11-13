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
        if (e.accion === 'jugar') {                                                              // pelota que rebota y notas de alegría
            const by = 20 - Math.abs(Math.sin(t * 5)) * 12;
            ctx.fillStyle = '#f03e3e'; ctx.beginPath(); ctx.arc(27 * p, by * p, 2.4 * p, 0, Math.PI * 2); ctx.fill();
            ctx.fillStyle = '#fff'; ctx.fillRect(26 * p, (by - 1.2) * p, p, p);
            for (let i = 0; i < 2; i++) { const x = 3 + i * 4, y = 6 - ((t * 4 + i * 3) % 6); px(x, y, 1, 3, '#ae3ec9'); px(x + 1, y, 2, 1, '#ae3ec9'); px(x - 1, y + 3, 2, 1, '#ae3ec9'); }
        }
        // Burbuja de lo que más necesita
        if (!e.accion && animo !== 'desmayada' && animo !== 'feliz') {
            const div = e.diversion == null ? 100 : e.diversion + 10;
            const minimo = Math.min(e.hambre, e.sueno, e.higiene, div);
            px(23, 1, 9, 7, '#fff'); px(24, 8, 2, 1, '#fff');
            if (minimo === div) { ctx.fillStyle = '#ae3ec9'; ctx.beginPath(); ctx.arc(27.5 * p, (4.5 + salto) * p, 2.2 * p, 0, Math.PI * 2); ctx.fill(); }
            else if (minimo === e.hambre) { px(25, 3, 4, 3, '#e8590c'); px(28, 2, 2, 2, '#fff4e6'); }
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
            ['hambre', 'sueno', 'higiene', 'diversion'].forEach(k => {
                const b = document.getElementById('ms-' + k); if (!b) return;
                b.style.width = estado[k] + '%'; b.style.background = estado[k] < 20 ? '#e03131' : estado[k] < 45 ? '#f59f00' : '#2f9e44';
                b.parentElement.setAttribute('aria-valuenow', estado[k]);
            });
            const hu = document.getElementById('ms-humor');
            if (hu && estado.humor) hu.innerHTML = `<b class="${esc(estado.humor.clave)}">${esc(estado.humor.nombre.toUpperCase())}</b><br>${esc(estado.humor.frase)}`;
            const bj = document.getElementById('ms-jugar'); if (bj) bj.classList.toggle('d-none', !!estado.debil);
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
                const m = t => (window.Mate ? Mate.html(t) : esc(t));          // fórmulas con formato
                caja.innerHTML = `<div class="ms-q">${m(p.texto)}</div>` + p.opciones.map((o, k) =>
                    `<button type="button" class="ms-op" data-k="${k}"><b>${'ABCD'[k]}</b> ${m(o)}</button>`).join('');
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
                const delJuego = caja.dataset.accion === 'jugar';
                setTimeout(() => { caja.hidden = true; if (delJuego) Arcade.seguir(j.bien); }, 1600);
            } finally { ocupado = false; }
        });

        function cuadro() {
            if (accion && performance.now() > accionHasta) accion = null;
            dibujar(ctx, estado.especie, {animo: estado.animo, accion, t: performance.now() / 1000,
                                          hambre: estado.hambre, sueno: estado.sueno, higiene: estado.higiene, diversion: estado.diversion}, lienzo.width);
            requestAnimationFrame(cuadro);
        }
        // --- Jugar: menú, juegos de lógica y el minijuego «Atrapa estrellas» ----------------------------
        const panelJuegos = document.getElementById('ms-juegos'), panelArcade = document.getElementById('ms-arcade');
        document.getElementById('ms-logica-ir').href = cfg.urlLogica;
        document.getElementById('ms-jugar').addEventListener('click', () => {
            if (Arcade.activo()) return;
            panelJuegos.hidden = false; caja.hidden = true; panelJuegos.scrollIntoView({behavior: 'smooth', block: 'nearest'});
        });
        document.getElementById('ms-juegos-cerrar').addEventListener('click', () => { panelJuegos.hidden = true; });
        document.getElementById('ms-arcade-ir').addEventListener('click', () => { panelJuegos.hidden = true; Arcade.empezar(); });

        const Arcade = (() => {
            const lz = document.getElementById('ms-arcade-lienzo'), cx = lz.getContext('2d'), W = lz.width, H = lz.height;
            const mini = document.createElement('canvas'); mini.width = mini.height = 64; const mctx = mini.getContext('2d');
            const DURA = 40, TAM = 64;
            let corriendo = false, pausa = false, puntos = 0, restante = DURA, ultimo = 0, x = W / 2, meta = W / 2, objetos = [], aturdido = 0,
                proxEstrella = 0, proxNube = 2, proxPregunta = 8, izq = false, der = false, fondo = [];
            for (let i = 0; i < 40; i++) fondo.push([Math.random() * W, Math.random() * H, Math.random() * 1.5 + .5]);
            function empezar() {
                puntos = 0; restante = DURA; objetos = []; aturdido = 0; proxEstrella = 0; proxNube = 2; proxPregunta = 8; x = meta = W / 2;
                panelArcade.hidden = false; corriendo = true; pausa = false; ultimo = performance.now();
                panelArcade.scrollIntoView({behavior: 'smooth', block: 'nearest'}); lz.focus && lz.focus();
                requestAnimationFrame(paso);
            }
            function nuevo(tipo) { objetos.push({tipo, x: 20 + Math.random() * (W - 40), y: -20, v: tipo === 'nube' ? 120 : tipo === 'pregunta' ? 90 : 110 + Math.random() * 80}); }
            async function preguntar() {
                pausa = true;
                try {
                    const j = await post(cfg.urlPedir, {accion: 'jugar'});
                    if (!j.ok) { pausa = false; ultimo = performance.now(); requestAnimationFrame(paso); return; }
                    const p = j.pregunta, m = t => (window.Mate ? Mate.html(t) : esc(t));
                    caja.innerHTML = `<div class="small text-muted mb-1">¡Burbuja de pregunta! Si acierta: +5 estrellas.</div><div class="ms-q">${m(p.texto)}</div>` + p.opciones.map((o, k) =>
                        `<button type="button" class="ms-op" data-k="${k}"><b>${'ABCD'[k]}</b> ${m(o)}</button>`).join('');
                    caja.dataset.accion = 'jugar'; caja.hidden = false; caja.scrollIntoView({behavior: 'smooth', block: 'nearest'});
                } catch (e) { pausa = false; ultimo = performance.now(); requestAnimationFrame(paso); }
            }
            function seguir(bien) {
                if (!corriendo) return;
                if (bien) puntos += 5;
                pausa = false; ultimo = performance.now(); panelArcade.scrollIntoView({behavior: 'smooth', block: 'nearest'}); requestAnimationFrame(paso);
            }
            async function terminar() {
                corriendo = false; dibujarJuego(performance.now() / 1000);
                cx.fillStyle = 'rgba(0,0,0,.55)'; cx.fillRect(0, 0, W, H);
                cx.fillStyle = '#ffd43b'; cx.font = '16px "Press Start 2P", monospace'; cx.textAlign = 'center';
                cx.fillText('¡FIN!', W / 2, H / 2 - 20); cx.fillText(`★ ${puntos}`, W / 2, H / 2 + 14);
                try {
                    const j = await post(cfg.urlPartida, {estrellas: puntos});
                    if (j.ok) { estado = j.estado; pintarEstado(); avisar(j.mensaje + (j.subio ? ` Ánimo +${j.subio}.` : ''), 'bien');
                        accion = 'jugar'; accionHasta = performance.now() + 4000; }
                } catch (e) { /* sin conexión: la partida no cuenta */ }
                setTimeout(() => { panelArcade.hidden = true; }, 2500);
            }
            function paso(ahora) {
                if (!corriendo || pausa) return;
                const dt = Math.min(.05, (ahora - ultimo) / 1000); ultimo = ahora;
                restante -= dt;
                if (restante <= 0) { restante = 0; terminar(); return; }
                if (izq) meta -= 320 * dt; if (der) meta += 320 * dt;
                meta = Math.max(TAM / 2, Math.min(W - TAM / 2, meta));
                if (aturdido <= 0) x += (meta - x) * Math.min(1, dt * 12); else aturdido -= dt;
                proxEstrella -= dt; proxNube -= dt;
                if (proxEstrella <= 0) { nuevo('estrella'); proxEstrella = .45 + Math.random() * .4; }
                if (proxNube <= 0) { nuevo('nube'); proxNube = 1.8 + Math.random() * 1.5; }
                if (puntos >= proxPregunta && !objetos.some(o => o.tipo === 'pregunta')) { nuevo('pregunta'); proxPregunta += 10; }
                const py = H - TAM / 2 - 8;
                for (const o of objetos) {
                    o.y += o.v * dt;
                    if (!o.fuera && Math.abs(o.x - x) < TAM / 2 && Math.abs(o.y - py) < TAM / 2 - 6) {
                        o.fuera = true;
                        if (o.tipo === 'estrella') puntos += 1;
                        else if (o.tipo === 'nube') { aturdido = 1; puntos = Math.max(0, puntos - 2); }
                        else { objetos = objetos.filter(z => !z.fuera && z.y < H + 30); actualizarMarcador(); dibujarJuego(ahora / 1000); preguntar(); return; }
                    }
                }
                objetos = objetos.filter(o => !o.fuera && o.y < H + 30);
                actualizarMarcador(); dibujarJuego(ahora / 1000);
                requestAnimationFrame(paso);
            }
            function actualizarMarcador() {
                document.getElementById('ms-puntos').textContent = puntos;
                document.getElementById('ms-tiempo').textContent = Math.ceil(restante);
            }
            function estrella(xx, yy, r, color) {
                cx.fillStyle = color; cx.beginPath();
                for (let i = 0; i < 10; i++) { const a = -Math.PI / 2 + i * Math.PI / 5, rr = i % 2 ? r * .45 : r; cx.lineTo(xx + Math.cos(a) * rr, yy + Math.sin(a) * rr); }
                cx.closePath(); cx.fill();
            }
            function dibujarJuego(t) {
                cx.fillStyle = '#1b1f3b'; cx.fillRect(0, 0, W, H);
                fondo.forEach(([a, b, r]) => { cx.fillStyle = 'rgba(255,255,255,.5)'; cx.fillRect(a, (b + t * 15 * r) % H, r, r); });
                cx.fillStyle = '#2b8a3e'; cx.fillRect(0, H - 8, W, 8);
                for (const o of objetos) {
                    if (o.tipo === 'estrella') estrella(o.x, o.y, 11, '#ffd43b');
                    else if (o.tipo === 'nube') {
                        cx.fillStyle = '#868e96'; [[-10, 0, 11], [4, -5, 13], [14, 2, 9]].forEach(([a, b, r]) => { cx.beginPath(); cx.arc(o.x + a, o.y + b, r, 0, Math.PI * 2); cx.fill(); });
                        cx.strokeStyle = '#ffd43b'; cx.lineWidth = 3; cx.beginPath(); cx.moveTo(o.x, o.y + 10); cx.lineTo(o.x - 5, o.y + 20); cx.lineTo(o.x + 3, o.y + 20); cx.lineTo(o.x - 2, o.y + 30); cx.stroke();
                    } else {
                        cx.fillStyle = 'rgba(165,216,255,.35)'; cx.strokeStyle = '#a5d8ff'; cx.lineWidth = 2;
                        cx.beginPath(); cx.arc(o.x, o.y, 16, 0, Math.PI * 2); cx.fill(); cx.stroke();
                        cx.fillStyle = '#fff'; cx.font = '14px "Press Start 2P", monospace'; cx.textAlign = 'center'; cx.textBaseline = 'middle'; cx.fillText('?', o.x, o.y + 1);
                    }
                }
                dibujar(mctx, estado.especie, {animo: aturdido > 0 ? 'mal' : 'feliz', accion: aturdido > 0 ? 'mareo' : null, t, hambre: 100, sueno: 100, higiene: 100, diversion: 100}, TAM);
                cx.drawImage(mini, x - TAM / 2, H - TAM - 8);
                if (aturdido > 0) for (let i = 0; i < 3; i++) { const a = t * 6 + i * 2.1; estrella(x + Math.cos(a) * 18, H - TAM - 4 + Math.sin(a) * 4, 4, '#ffd43b'); }
            }
            function aX(ev) { const r = lz.getBoundingClientRect(); return (ev.clientX - r.left) * W / r.width; }
            lz.addEventListener('pointerdown', ev => { meta = aX(ev); lz.setPointerCapture(ev.pointerId); });
            lz.addEventListener('pointermove', ev => { if (ev.pointerType === 'mouse' || ev.buttons) meta = aX(ev); });
            document.addEventListener('keydown', ev => { if (!corriendo) return; if (ev.key === 'ArrowLeft') { izq = true; ev.preventDefault(); } if (ev.key === 'ArrowRight') { der = true; ev.preventDefault(); } });
            document.addEventListener('keyup', ev => { if (ev.key === 'ArrowLeft') izq = false; if (ev.key === 'ArrowRight') der = false; });
            return {empezar, seguir, activo: () => corriendo};
        })();

        pintarEstado(); cuadro();
        // Las necesidades bajan con el tiempo: se refresca cada minuto
        setInterval(async () => {
            if (document.hidden) return;
            const r = await fetch(cfg.urlEstado, {credentials: 'same-origin'}); const j = await r.json();
            if (j.ok) { estado = j.estado; pintarEstado(); }
        }, 60000);
    });
})();
