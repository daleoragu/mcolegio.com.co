/* Juegos de lógica del aula: lo común (niveles, progreso, movimientos, tiempo y piezas que se arrastran).
 *
 *   Logica.registrar('hanoi', {nombre, instrucciones, total(datos), iniciar(zona, datos, i, api) → {deshacer?, ayuda?}})
 *   Logica.pagina({id, datos, clave, alGanar})     ← arma la página con la barra de niveles
 *   Logica.montar(zona, id, datos, i, api)         ← solo el juego (lo usan también las olimpiadas de Eventos)
 *
 * api: movimiento(n), gano(), lienzo(W, H), aviso(texto), sonido(tipo)
 */
(function () {
    'use strict';
    const JUEGOS = {};
    let audio = null;
    function sonido(tipo) {
        const notas = {toque: [[520, .05]], bien: [[660, .08], [990, .12]], mal: [[200, .25]], gano: [[523, .12], [659, .12], [784, .12], [1046, .25]]}[tipo] || [];
        try {
            audio = audio || new (window.AudioContext || window.webkitAudioContext)();
            notas.forEach(([f, d], i) => setTimeout(() => {
                const o = audio.createOscillator(), g = audio.createGain();
                o.type = 'triangle'; o.frequency.value = f; g.gain.value = .07; o.connect(g); g.connect(audio.destination);
                o.start(); g.gain.exponentialRampToValueAtTime(.0001, audio.currentTime + d); o.stop(audio.currentTime + d);
            }, i * 110));
        } catch (e) { /* sin sonido */ }
    }

    /* Un lienzo nítido de tamaño lógico W × H que se ajusta al ancho del contenedor. */
    function lienzo(contenedor, W, H) {
        const cv = document.createElement('canvas'); cv.className = 'lg-lienzo'; cv.style.touchAction = 'none';
        contenedor.appendChild(cv);
        const ctx = cv.getContext('2d');
        const L = {cv, ctx, W, H, escala: 1, dibujar: null};
        L.ajustar = function () {
            const caja = contenedor.getBoundingClientRect();
            let ancho = caja.width || W;
            const maxAlto = (document.fullscreenElement ? window.innerHeight - 90 : window.innerHeight * .78);
            if (ancho * H / W > maxAlto) ancho = maxAlto * W / H;
            const dpr = window.devicePixelRatio || 1;
            cv.style.width = ancho + 'px'; cv.style.height = (ancho * H / W) + 'px';
            cv.width = Math.round(ancho * dpr); cv.height = Math.round(ancho * H / W * dpr); L.escala = cv.width / W;
            if (L.dibujar) L.dibujar();
        };
        L.punto = ev => { const r = cv.getBoundingClientRect(); return {x: (ev.clientX - r.left) * W / r.width, y: (ev.clientY - r.top) * H / r.height}; };
        L.limpiar = fondo => { ctx.setTransform(L.escala, 0, 0, L.escala, 0, 0); ctx.fillStyle = fondo || '#fff'; ctx.fillRect(0, 0, W, H); };
        L.texto = (t, x, y, o) => {
            o = o || {}; ctx.font = `${o.negrita ? 'bold ' : ''}${o.tam || 14}px system-ui, sans-serif`; ctx.fillStyle = o.color || '#212529';
            ctx.textAlign = o.alinear || 'left'; ctx.textBaseline = o.base || 'alphabetic'; ctx.fillText(t, x, y);
        };
        window.addEventListener('resize', L.ajustar);
        document.addEventListener('fullscreenchange', () => setTimeout(L.ajustar, 50));
        requestAnimationFrame(L.ajustar);
        return L;
    }

    function redondo(ctx, x, y, w, h, r) { ctx.beginPath(); ctx.roundRect ? ctx.roundRect(x, y, w, h, r) : ctx.rect(x, y, w, h); }

    /* Piezas de cuadritos que se arrastran a un tablero (Tablero 36, Cuatro cuadrantes, Cerditos).
     * Tocar = girar 90°; doble toque (o el botón) = voltear. */
    function piezasGrilla(L, cfg) {
        const T = cfg.tablero, P = cfg.piezas.map((p, i) => ({...p, i, celdas: norm(p.celdas), x: cfg.bandeja[i].x, y: cfg.bandeja[i].y, en: null}));
        let arrastre = null, ultima = null, ultimoToque = {i: -1, t: 0};
        function norm(c) { const mf = Math.min(...c.map(a => a[0])), mc = Math.min(...c.map(a => a[1])); return c.map(([f, k, t]) => [f - mf, k - mc, t]); }
        function girar(p) { p.celdas = norm(p.celdas.map(([f, c, t]) => [c, -f, t])); }
        function voltear(p) { p.celdas = norm(p.celdas.map(([f, c, t]) => [f, -c, t])); }
        function cel(p) { return T.cel * (p.en ? 1 : (cfg.escalaBandeja || .6)); }
        function ocupadas(salvo) {
            const m = new Map();
            P.forEach(p => { if (p !== salvo && p.en) p.celdas.forEach(([f, c, t]) => m.set((p.en.f + f) + ',' + (p.en.c + c), {p, t})); });
            return m;
        }
        function cabe(p, f0, c0) {
            if (T.anclas && !T.anclas(f0, c0)) return false;
            const occ = ocupadas(p);
            return p.celdas.every(([f, c]) => {
                const F = f0 + f, C = c0 + c;
                return F >= 0 && C >= 0 && F < T.filas && C < T.cols && (!T.valida || T.valida(F, C)) && !occ.has(F + ',' + C);
            });
        }
        function aBandeja(p) { p.en = null; p.x = cfg.bandeja[p.i].x; p.y = cfg.bandeja[p.i].y; }
        function colocar(p) {
            // ¿Quedó sobre el tablero? Se ajusta a la celda más cercana si cabe.
            const f0 = Math.round((p.y - T.y) / T.cel), c0 = Math.round((p.x - T.x) / T.cel);
            const encima = p.x + 10 > T.x - T.cel && p.x < T.x + T.cols * T.cel && p.y + 10 > T.y - T.cel && p.y < T.y + T.filas * T.cel;
            if (encima && cabe(p, f0, c0)) { p.en = {f: f0, c: c0}; p.x = T.x + c0 * T.cel; p.y = T.y + f0 * T.cel; }
            else if (encima) aBandeja(p);
            else p.en = null;
        }
        function enPieza(p, x, y) {
            const k = cel(p);
            return p.celdas.some(([f, c]) => x >= p.x + c * k && x <= p.x + (c + 1) * k && y >= p.y + f * k && y <= p.y + (f + 1) * k);
        }
        function dibujar(ctx) {
            const orden = P.filter(p => p !== (arrastre && arrastre.p)).sort((a, b) => (a.en ? 0 : 1) - (b.en ? 0 : 1));
            if (arrastre) orden.push(arrastre.p);
            orden.forEach(p => {
                const k = arrastre && arrastre.p === p ? T.cel : cel(p);
                ctx.save();
                if (arrastre && arrastre.p === p) { ctx.shadowColor = 'rgba(0,0,0,.35)'; ctx.shadowBlur = 10; ctx.shadowOffsetY = 4; }
                p.celdas.forEach(([f, c, t]) => cfg.dibujarCelda(ctx, p, t, p.x + c * k, p.y + f * k, k));
                ctx.restore();
                if (cfg.contorno !== false) {
                    ctx.strokeStyle = 'rgba(0,0,0,.35)'; ctx.lineWidth = 1.5;
                    const s = new Set(p.celdas.map(([f, c]) => f + ',' + c));
                    p.celdas.forEach(([f, c]) => {
                        const x = p.x + c * k, y = p.y + f * k; ctx.beginPath();
                        if (!s.has((f - 1) + ',' + c)) { ctx.moveTo(x, y); ctx.lineTo(x + k, y); }
                        if (!s.has((f + 1) + ',' + c)) { ctx.moveTo(x, y + k); ctx.lineTo(x + k, y + k); }
                        if (!s.has(f + ',' + (c - 1))) { ctx.moveTo(x, y); ctx.lineTo(x, y + k); }
                        if (!s.has(f + ',' + (c + 1))) { ctx.moveTo(x + k, y); ctx.lineTo(x + k, y + k); }
                        ctx.stroke();
                    });
                }
            });
        }
        L.cv.addEventListener('pointerdown', ev => {
            const {x, y} = L.punto(ev);
            const p = [...P].reverse().sort((a, b) => (a.en ? 1 : 0) - (b.en ? 1 : 0)).find(p => enPieza(p, x, y));
            if (!p) return;
            ev.preventDefault(); try { L.cv.setPointerCapture(ev.pointerId); } catch (e) { /* */ }
            const k = cel(p), fx = (x - p.x) / k, fy = (y - p.y) / k;
            arrastre = {p, dx: fx * T.cel, dy: fy * T.cel, x0: x, y0: y, movio: false, estaba: p.en};
            p.en = null; p.x = x - arrastre.dx; p.y = y - arrastre.dy; ultima = p;
            cfg.redibujar();
        });
        L.cv.addEventListener('pointermove', ev => {
            if (!arrastre) return;
            const {x, y} = L.punto(ev);
            if (Math.hypot(x - arrastre.x0, y - arrastre.y0) > 6) arrastre.movio = true;
            arrastre.p.x = x - arrastre.dx; arrastre.p.y = y - arrastre.dy; cfg.redibujar();
        });
        const soltar = () => {
            if (!arrastre) return;
            const {p, movio, estaba} = arrastre; arrastre = null;
            if (!movio) {
                // Un toque gira; dos toques seguidos voltean (si la pieza se puede voltear)
                const ahora = performance.now();
                if (ultimoToque.i === p.i && ahora - ultimoToque.t < 320 && p.voltear !== false) { girar(p); girar(p); girar(p); voltear(p); }
                else girar(p);
                ultimoToque = {i: p.i, t: ahora};
                if (estaba) { p.x = T.x + estaba.c * T.cel; p.y = T.y + estaba.f * T.cel; }
                else { p.x = cfg.bandeja[p.i].x; p.y = cfg.bandeja[p.i].y; }
                if (estaba) { if (cabe(p, estaba.f, estaba.c)) p.en = estaba; else aBandeja(p); }
            } else colocar(p);
            cfg.redibujar(); if (cfg.alCambiar) cfg.alCambiar();
        };
        L.cv.addEventListener('pointerup', soltar); L.cv.addEventListener('pointercancel', soltar);
        return {
            piezas: P, dibujar, ocupadas: () => ocupadas(null),
            girarUltima() { if (ultima) { const e = ultima.en; girar(ultima); if (e && !cabe(ultima, e.f, e.c)) aBandeja(ultima); cfg.redibujar(); if (cfg.alCambiar) cfg.alCambiar(); } },
            voltearUltima() { if (ultima && ultima.voltear !== false) { const e = ultima.en; voltear(ultima); if (e && !cabe(ultima, e.f, e.c)) aBandeja(ultima); cfg.redibujar(); if (cfg.alCambiar) cfg.alCambiar(); } },
            colocarEn(p, celdas, f, c) { p.celdas = norm(celdas); p.en = {f, c}; p.x = T.x + c * T.cel; p.y = T.y + f * T.cel; },
        };
    }

    function montar(zona, id, datos, i, api) {
        const def = JUEGOS[id];
        zona.innerHTML = '';
        api.lienzo = (W, H) => lienzo(zona, W, H);
        api.sonido = api.sonido || sonido;
        return def.iniciar(zona, datos, i, api) || {};
    }

    /* La página: barra de niveles, contador, tiempo, botones y el mensaje de victoria. */
    function pagina(cfg) {
        const def = JUEGOS[cfg.id], datos = cfg.datos, total = def.total(datos);
        const $ = s => document.querySelector(s);
        let progreso = {};
        try { progreso = JSON.parse(localStorage.getItem(cfg.clave) || '{}'); } catch (e) { progreso = {}; }
        let nivel = Math.min(total - 1, Object.keys(progreso).length), ctrl = null, movs = 0, inicio = 0, reloj = null, ganado = false;
        $('#lg-instrucciones').textContent = def.instrucciones;
        function guardar() { try { localStorage.setItem(cfg.clave, JSON.stringify(progreso)); } catch (e) { /* sin almacenamiento */ } }
        function barra() {
            const caja = $('#lg-niveles'); caja.innerHTML = '';
            for (let i = 0; i < total; i++) {
                const b = document.createElement('button'); b.type = 'button';
                b.className = 'lg-nivel' + (i === nivel ? ' actual' : '') + (progreso[i] ? ' hecho' : '');
                b.textContent = (def.etiqueta ? def.etiqueta(datos, i) : i + 1);
                b.title = progreso[i] ? `Superado · ${'★'.repeat(progreso[i].estrellas || 1)}` : 'Nivel ' + (i + 1);
                b.addEventListener('click', () => cargar(i)); caja.appendChild(b);
            }
            const hechos = Object.keys(progreso).length;
            $('#lg-progreso').textContent = `${hechos} de ${total} niveles superados`;
            const actual = caja.querySelector('.actual'); if (actual) actual.scrollIntoView({block: 'nearest', inline: 'center'});
        }
        function tiempo() { const s = Math.floor((performance.now() - inicio) / 1000); return `${Math.floor(s / 60)}:${String(s % 60).padStart(2, '0')}`; }
        function cargar(i) {
            nivel = i; movs = 0; ganado = false; inicio = performance.now();
            $('#lg-final').hidden = true; $('#lg-movs').textContent = '0';
            clearInterval(reloj); reloj = setInterval(() => { if (!ganado) $('#lg-tiempo').textContent = tiempo(); }, 500);
            const api = {
                movimiento(n) { movs += (n === undefined ? 1 : n); $('#lg-movs').textContent = movs; },
                gano(info) {
                    if (ganado) return; ganado = true; sonido('gano');
                    const est = (info && info.estrellas) || 3;
                    const antes = progreso[nivel];
                    if (!antes || (antes.estrellas || 0) <= est) progreso[nivel] = {estrellas: est, movs, tiempo: tiempo()};
                    guardar(); barra();
                    $('#lg-final-titulo').textContent = (info && info.titulo) || '¡Lo logró!';
                    $('#lg-final-detalle').textContent = `${'★'.repeat(est)}${'☆'.repeat(3 - est)} · ${movs} movimiento(s) · ${tiempo()}${info && info.detalle ? ' · ' + info.detalle : ''}`;
                    $('#lg-sig').hidden = nivel >= total - 1;
                    setTimeout(() => { $('#lg-final').hidden = false; }, 450);
                    if (cfg.alGanar) cfg.alGanar(nivel, progreso[nivel]);
                },
                perdio(info) {
                    if (ganado) return; ganado = true; sonido('mal');
                    $('#lg-final-titulo').textContent = (info && info.titulo) || '¡Casi!';
                    $('#lg-final-detalle').textContent = (info && info.detalle) || 'Inténtelo de nuevo.';
                    $('#lg-sig').hidden = true;
                    setTimeout(() => { $('#lg-final').hidden = false; }, 450);
                },
                aviso(t) { const a = $('#lg-aviso'); a.textContent = t; a.hidden = !t; clearTimeout(a._t); if (t) a._t = setTimeout(() => { a.hidden = true; }, 2500); },
            };
            ctrl = montar($('#lg-zona'), cfg.id, datos, i, api);
            $('#lg-deshacer').hidden = !ctrl.deshacer; $('#lg-ayuda').hidden = !ctrl.ayuda;
            $('#lg-girar').hidden = !ctrl.girar; $('#lg-voltear').hidden = !ctrl.voltear;
            $('#lg-nivel-titulo').textContent = def.titulo ? def.titulo(datos, i) : `Nivel ${i + 1}`;
            barra();
        }
        $('#lg-reiniciar').addEventListener('click', () => cargar(nivel));
        $('#lg-deshacer').addEventListener('click', () => ctrl.deshacer && ctrl.deshacer());
        $('#lg-ayuda').addEventListener('click', () => ctrl.ayuda && ctrl.ayuda());
        $('#lg-girar').addEventListener('click', () => ctrl.girar && ctrl.girar());
        $('#lg-voltear').addEventListener('click', () => ctrl.voltear && ctrl.voltear());
        $('#lg-sig').addEventListener('click', () => cargar(Math.min(total - 1, nivel + 1)));
        $('#lg-repetir').addEventListener('click', () => cargar(nivel));
        $('#lg-completa').addEventListener('click', () => {
            const z = $('#lg-pantalla');
            if (document.fullscreenElement) document.exitFullscreen(); else if (z.requestFullscreen) z.requestFullscreen().catch(() => {});
        });
        cargar(nivel);
        window.logicaActual = {cargar, get nivel() { return nivel; }, get ctrl() { return ctrl; }};
    }

    window.Logica = {registrar: (id, def) => { JUEGOS[id] = def; }, juego: id => JUEGOS[id], montar, pagina, lienzo, piezasGrilla, sonido, redondo};
})();
