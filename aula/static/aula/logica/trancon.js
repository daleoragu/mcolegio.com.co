/* Trancón (6×6) y Safari (7×7): saque el carro rojo (o el jeep) por la salida de la derecha.
 * Cada vehículo o animal se arrastra solo a lo largo de su dirección; el hipopótamo (2×2) se mueve
 * en las cuatro direcciones y las rocas no se mueven. Un movimiento = mover una pieza cualquier distancia. */
(function () {
    'use strict';
    const AUTOS = ['#4dabf7', '#69db7c', '#ffd43b', '#da77f2', '#ff922b', '#20c997', '#f783ac', '#748ffc', '#a9e34b', '#ffa94d', '#63e6be', '#e599f7'];
    const ANIM2 = ['🦓', '🦁', '🐆', '🐗', '🦌'], ANIM3 = ['🦒', '🐘', '🐊'];

    function leer(filas) {
        const N = filas.length, piezas = {}, orden = [];
        filas.forEach((fila, f) => [...fila].forEach((ch, c) => {
            if (ch === '.') return;
            const k = ch === '#' ? '#' + f + ',' + c : ch;
            if (!piezas[k]) { piezas[k] = {id: k, f, c, alto: 1, ancho: 1, letra: ch}; orden.push(k); }
            const p = piezas[k];
            p.alto = Math.max(p.alto, f - p.f + 1); p.ancho = Math.max(p.ancho, c - p.c + 1);
        }));
        const lista = orden.map(k => piezas[k]);
        lista.forEach(p => {
            p.tipo = p.letra === '#' ? 'fija' : p.letra === 'H' ? '4' : p.ancho > 1 ? 'h' : 'v';
            p.rojo = p.letra === 'x';
        });
        lista.sort((a, b) => (b.rojo ? 1 : 0) - (a.rojo ? 1 : 0));
        return {N, piezas: lista};
    }

    function crear(safari) {
        return {
            nombre: safari ? 'Safari' : 'Trancón',
            instrucciones: safari
                ? 'Saque el jeep por la salida de la derecha. Arrastre cada animal a lo largo de su dirección; el hipopótamo se mueve hacia los cuatro lados y las rocas no se mueven.'
                : 'Saque el carro rojo por la salida de la derecha. Arrastre cada carro o camión solo hacia adelante o hacia atrás (no puede girar).',
            total: d => d.length,
            titulo: (d, i) => `Nivel ${i + 1} · se puede en ${d[i][0]} movimientos`,
            iniciar(zona, datos, i, api) {
                const [minimo, filas] = datos[i], {N, piezas} = leer(filas);
                const CEL = safari ? 56 : 64, M = 30, W = N * CEL + M * 2 + 50, H = N * CEL + M * 2 + 24, L = api.lienzo(W, H), ctx = L.ctx;
                const filaSalida = piezas[0].f;
                let arrastre = null, movs = 0, saliendo = null;
                const historia = [];
                piezas.forEach((p, k) => {
                    p.color = p.rojo ? '#e03131' : AUTOS[k % AUTOS.length];
                    p.emoji = p.tipo === '4' ? '🦛' : p.tipo === 'fija' ? '🪨' : p.rojo ? '🚙' : (Math.max(p.alto, p.ancho) === 3 ? ANIM3 : ANIM2)[k % (Math.max(p.alto, p.ancho) === 3 ? 3 : 5)];
                });
                function libre(f, c, salvo) {
                    if (f < 0 || c < 0 || f >= N || c >= N) return false;
                    return !piezas.some(p => p !== salvo && f >= p.f && f < p.f + p.alto && c >= p.c && c < p.c + p.ancho);
                }
                // Hasta dónde puede ir la pieza en una dirección
                function alcance(p, df, dc) {
                    let n = 0;
                    while (true) {
                        const f = p.f + df * (n + 1), c = p.c + dc * (n + 1);
                        let ok = true;
                        for (let a = 0; a < p.alto && ok; a++) for (let b = 0; b < p.ancho && ok; b++) if (!libre(f + a, c + b, p)) ok = false;
                        if (!ok) return n;
                        n += 1;
                    }
                }
                const X = c => M + c * CEL, Y = f => M + f * CEL;
                L.dibujar = function () {
                    L.limpiar(safari ? '#e9d8a6' : '#dee2e6');
                    // el piso
                    ctx.fillStyle = safari ? '#b5c99a' : '#495057'; Logica.redondo(ctx, M - 8, M - 8, N * CEL + 16, N * CEL + 16, 14); ctx.fill();
                    for (let f = 0; f < N; f++) for (let c = 0; c < N; c++) {
                        ctx.fillStyle = safari ? ((f + c) % 2 ? '#c9d8a8' : '#bfd29a') : '#5c636a';
                        ctx.fillRect(X(c) + 1, Y(f) + 1, CEL - 2, CEL - 2);
                    }
                    // la salida
                    ctx.fillStyle = safari ? '#e9d8a6' : '#dee2e6'; ctx.fillRect(M + N * CEL, Y(filaSalida) + 4, 14, CEL - 8);
                    ctx.fillStyle = '#2f9e44'; ctx.beginPath(); const sy = Y(filaSalida) + CEL / 2;
                    ctx.moveTo(M + N * CEL + 20, sy - 12); ctx.lineTo(M + N * CEL + 40, sy); ctx.lineTo(M + N * CEL + 20, sy + 12); ctx.fill();
                    L.texto('SALIDA', M + N * CEL + 30, Y(filaSalida) - 6, {tam: 11, negrita: true, alinear: 'center', color: '#2f9e44'});
                    piezas.forEach(p => {
                        let x = X(p.c), y = Y(p.f);
                        if (arrastre && arrastre.p === p) { x += arrastre.dx; y += arrastre.dy; }
                        if (saliendo && p.rojo) x += saliendo.d;
                        pintar(p, x, y);
                    });
                    L.texto(`Movimientos: ${movs}`, M, H - 6, {tam: 13, color: '#495057'});
                };
                function pintar(p, x, y) {
                    const w = p.ancho * CEL - 8, h = p.alto * CEL - 8;
                    x += 4; y += 4;
                    if (p.tipo === 'fija') { ctx.fillStyle = '#868e96'; Logica.redondo(ctx, x + 4, y + 4, w - 8, h - 8, 14); ctx.fill(); }
                    else if (safari) {
                        ctx.fillStyle = p.rojo ? '#e03131' : p.tipo === '4' ? '#9775fa' : '#fff3bf'; Logica.redondo(ctx, x, y, w, h, 12); ctx.fill();
                        ctx.strokeStyle = 'rgba(0,0,0,.25)'; ctx.lineWidth = 2; ctx.stroke();
                    } else {
                        ctx.fillStyle = p.color; Logica.redondo(ctx, x, y, w, h, 10); ctx.fill();
                        ctx.fillStyle = 'rgba(255,255,255,.25)'; Logica.redondo(ctx, x + 4, y + 4, w - 8, 6, 3); ctx.fill();
                        // vidrios y luces
                        ctx.fillStyle = '#212529';
                        if (p.ancho > 1) { ctx.fillRect(x + w - 22, y + 8, 10, h - 16); ctx.fillRect(x + 10, y + 10, 8, h - 20); ctx.fillStyle = '#fff3bf'; ctx.fillRect(x + w - 5, y + 6, 4, 8); ctx.fillRect(x + w - 5, y + h - 14, 4, 8); }
                        else { ctx.fillRect(x + 8, y + 10, w - 16, 10); ctx.fillRect(x + 10, y + h - 20, w - 20, 8); ctx.fillStyle = '#fff3bf'; ctx.fillRect(x + 6, y + 2, 8, 4); ctx.fillRect(x + w - 14, y + 2, 8, 4); }
                        if (Math.max(p.ancho, p.alto) === 3) { ctx.fillStyle = 'rgba(0,0,0,.15)'; if (p.ancho > 1) ctx.fillRect(x + w / 3, y + 4, 3, h - 8); else ctx.fillRect(x + 4, y + h / 3, w - 8, 3); }
                    }
                    if (safari || p.tipo === 'fija') {
                        ctx.font = `${Math.min(w, h) * .62}px serif`; ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
                        ctx.fillText(p.emoji, x + w / 2, y + h / 2 + 2);
                    }
                }
                L.cv.addEventListener('pointerdown', ev => {
                    if (saliendo) return;
                    const {x, y} = L.punto(ev), c = Math.floor((x - M) / CEL), f = Math.floor((y - M) / CEL);
                    const p = piezas.find(p => p.tipo !== 'fija' && f >= p.f && f < p.f + p.alto && c >= p.c && c < p.c + p.ancho);
                    if (!p) return;
                    try { L.cv.setPointerCapture(ev.pointerId); } catch (e) { /* */ }
                    arrastre = {p, x0: x, y0: y, dx: 0, dy: 0, eje: p.tipo === 'h' ? 'x' : p.tipo === 'v' ? 'y' : null,
                                lim: {izq: alcance(p, 0, -1), der: alcance(p, 0, 1), arr: alcance(p, -1, 0), aba: alcance(p, 1, 0)}};
                });
                L.cv.addEventListener('pointermove', ev => {
                    if (!arrastre) return;
                    const {x, y} = L.punto(ev), a = arrastre;
                    let dx = x - a.x0, dy = y - a.y0;
                    if (!a.eje && Math.hypot(dx, dy) > 8) a.eje = Math.abs(dx) > Math.abs(dy) ? 'x' : 'y';
                    if (a.eje === 'x') { a.dx = Math.max(-a.lim.izq * CEL, Math.min((a.p.rojo ? a.lim.der + (a.p.c + a.p.ancho + a.lim.der === N ? 2 : 0) : a.lim.der) * CEL, dx)); a.dy = 0; }
                    else if (a.eje === 'y') { a.dy = Math.max(-a.lim.arr * CEL, Math.min(a.lim.aba * CEL, dy)); a.dx = 0; }
                    L.dibujar();
                });
                const soltar = () => {
                    if (!arrastre) return;
                    const a = arrastre, p = a.p; arrastre = null;
                    const dc = Math.max(-a.lim.izq, Math.min(a.lim.der, Math.round(a.dx / CEL))), df = Math.round(a.dy / CEL);
                    if (dc || df) {
                        historia.push([p, p.f, p.c]); p.c += dc; p.f += df; movs += 1; api.movimiento(); api.sonido('toque');
                    }
                    L.dibujar();
                    if (p.rojo && p.c + p.ancho === N) salir();
                };
                L.cv.addEventListener('pointerup', soltar); L.cv.addEventListener('pointercancel', soltar);
                function salir() {
                    saliendo = {d: 0};
                    const paso = () => { saliendo.d += 9; L.dibujar(); if (saliendo.d < CEL * 2.5) requestAnimationFrame(paso); else api.gano({estrellas: movs <= minimo ? 3 : movs <= minimo * 1.5 ? 2 : 1, detalle: `mínimo: ${minimo}`}); };
                    requestAnimationFrame(paso);
                }
                return {
                    deshacer() { if (saliendo) return; const u = historia.pop(); if (!u) return; u[0].f = u[1]; u[0].c = u[2]; movs -= 1; api.movimiento(-1); L.dibujar(); },
                };
            },
        };
    }
    Logica.registrar('trancon', crear(false));
    Logica.registrar('safari', crear(true));
})();
