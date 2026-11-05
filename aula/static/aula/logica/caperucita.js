/* Caperucita: ponga las piezas de camino en el tablero para que Caperucita llegue a la casa de la abuela.
 * Los árboles y el lobo ocupan su casilla (no se puede poner pieza encima). Tocar gira la pieza.
 * Los niveles se arman solos (un camino al azar partido en piezas), así siempre tienen solución. */
(function () {
    'use strict';
    const NB = 1, EB = 2, SB = 4, WB = 8, DIRS = [[NB, -1, 0, SB], [EB, 0, 1, WB], [SB, 1, 0, NB], [WB, 0, -1, EB]];
    const rotar = m => ((m << 1) | (m >> 3)) & 15;     // girar el camino 90° a la derecha
    function azar(semilla) { let s = semilla >>> 0; return () => { s = (s + 0x6D2B79F5) >>> 0; let t = s; t = Math.imul(t ^ t >>> 15, t | 1); t ^= t + Math.imul(t ^ t >>> 7, t | 61); return ((t ^ t >>> 14) >>> 0) / 4294967296; }; }
    function generar(i) {
        const r = azar(i * 7907 + 101), ent = n => Math.floor(r() * n);
        const N = i < 10 ? 4 : i < 20 ? 5 : 6, L = N === 4 ? 5 + ent(3) : N === 5 ? 7 + ent(4) : 9 + ent(5);
        for (let intento = 0; intento < 500; intento++) {
            const ini = [ent(N), ent(N)], p = [ini], vis = new Set([ini.join()]);
            while (p.length < L) {
                const [f, c] = p[p.length - 1], ops = DIRS.map(([, df, dc]) => [f + df, c + dc]).filter(([a, b]) => a >= 0 && b >= 0 && a < N && b < N && !vis.has(a + ',' + b));
                if (!ops.length) break;
                const n = ops[ent(ops.length)]; p.push(n); vis.add(n.join());
            }
            if (p.length < L) continue;
            const mascara = k => { let m = 0; [p[k - 1], p[k + 1]].forEach(q => { if (!q) return; DIRS.forEach(([bit, df, dc]) => { if (p[k][0] + df === q[0] && p[k][1] + dc === q[1]) m |= bit; }); }); return m; };
            // el camino de en medio se parte en piezas de 1 a 3 casillas
            const piezas = []; let k = 1;
            while (k < L - 1) { const t = Math.min(L - 1 - k, 1 + ent(3)); piezas.push(p.slice(k, k + t).map((q, j) => [q[0], q[1], mascara(k + j)])); k += t; }
            if (piezas.length < 2) continue;
            const libres = []; for (let f = 0; f < N; f++) for (let c = 0; c < N; c++) if (!vis.has(f + ',' + c)) libres.push([f, c]);
            libres.sort(() => r() - .5);
            const cerca = libres.filter(([f, c]) => p.some(([a, b]) => Math.abs(a - f) + Math.abs(b - c) === 1));
            const lobo = cerca[0] || libres[0];
            const arboles = libres.filter(q => q !== lobo).slice(0, Math.min(libres.length - 1, 1 + ent(N - 1)));
            // pieza de más (para despistar) en los niveles altos
            const sol = piezas.map(pz => pz.map(q => q.slice()));     // para la ayuda
            if (i >= 15) piezas.push([[0, 0, [5, 10, 3, 6][ent(4)]], [0, 1, [5, 10, 12, 9][ent(4)]]]);
            // cada pieza empieza girada al azar
            const listas = piezas.map(pz => { let celdas = pz.map(([f, c, m]) => [f, c, m]); for (let g = ent(4); g > 0; g--) celdas = celdas.map(([f, c, m]) => [c, -f, rotar(m)]); return celdas; });
            return {N, cap: {f: p[0][0], c: p[0][1], m: mascara(0)}, casa: {f: p[L - 1][0], c: p[L - 1][1], m: mascara(L - 1)}, lobo, arboles, piezas: listas, sol};
        }
    }
    // Ayuda (también la usa Atrapa al ladrón): pone en su sitio una pieza de la solución
    function ayudar(g, sol, api, L) {
        const k = sol.findIndex((celdas, n) => { const p = g.piezas[n]; if (!p.en) return true; const mias = new Set(p.celdas.map(([a, b]) => (p.en.f + a) + ',' + (p.en.c + b))); return !celdas.every(([a, b]) => mias.has(a + ',' + b)); });
        if (k < 0) return;
        const celdas = sol[k], set = new Set(celdas.map(([a, b]) => a + ',' + b));
        g.piezas.forEach(p => { if (p.en && p.i !== k && p.celdas.some(([a, b]) => set.has((p.en.f + a) + ',' + (p.en.c + b)))) { p.en = null; } });
        const f0 = Math.min(...celdas.map(c => c[0])), c0 = Math.min(...celdas.map(c => c[1]));
        g.colocarEn(g.piezas[k], celdas.map(([a, b, t]) => [a - f0, b - c0, t]), f0, c0);
        api.aviso('Esa pieza ya quedó en su sitio.'); L.dibujar();
    }
    Logica.ayudarConSolucion = ayudar;
    Logica.registrar('caperucita', {
        nombre: 'Caperucita',
        instrucciones: 'Ponga las piezas de camino para que Caperucita llegue a la casa de la abuela. No se pueden poner piezas sobre los árboles ni sobre el lobo. Un toque gira la pieza. En los niveles altos sobra una pieza.',
        total: () => 30,
        titulo: (d, i) => `Bosque ${i + 1} · ${i < 10 ? '4×4' : i < 20 ? '5×5' : '6×6'}${i >= 15 ? ' · sobra una pieza' : ''}`,
        iniciar(zona, datos, i, api) {
            const R = generar(i), N = R.N, CEL = Math.min(76, Math.floor(330 / N)), TX = 26, TY = 30;
            const W = 760, H = Math.max(N * CEL + 70, 420), L = api.lienzo(W, H), ctx = L.ctx;
            const bloqueadas = new Set([R.lobo.join(), ...R.arboles.map(q => q.join()), R.cap.f + ',' + R.cap.c, R.casa.f + ',' + R.casa.c]);
            const bandeja = R.piezas.map((_, k) => ({x: TX + N * CEL + 40 + (k % 3) * 125, y: 40 + Math.floor(k / 3) * 125}));
            const g = Logica.piezasGrilla(L, {
                tablero: {x: TX, y: TY, cel: CEL, filas: N, cols: N, valida: (f, c) => !bloqueadas.has(f + ',' + c)},
                piezas: R.piezas.map((celdas, k) => ({nombre: k, voltear: false, celdas})),
                bandeja, escalaBandeja: .6, girarTipo: rotar,
                dibujarCelda(ctx, p, m, x, y, k) {
                    ctx.fillStyle = '#94d82d'; ctx.fillRect(x + 1, y + 1, k - 2, k - 2);
                    camino(x, y, k, m, '#c68b4e');
                },
                redibujar: () => L.dibujar(),
                alCambiar() { api.movimiento(); if (llega()) api.gano({estrellas: 3}); },
            });
            function camino(x, y, k, m, color) {
                ctx.strokeStyle = color; ctx.lineWidth = k * .3; ctx.lineCap = 'round';
                const cx = x + k / 2, cy = y + k / 2;
                [[NB, cx, y], [EB, x + k, cy], [SB, cx, y + k], [WB, x, cy]].forEach(([b, ex, ey]) => { if (m & b) { ctx.beginPath(); ctx.moveTo(cx, cy); ctx.lineTo(ex, ey); ctx.stroke(); } });
                ctx.lineCap = 'butt';
            }
            function mapa() {
                const M = new Map(); M.set(R.cap.f + ',' + R.cap.c, R.cap.m); M.set(R.casa.f + ',' + R.casa.c, R.casa.m);
                g.ocupadas().forEach((o, k) => M.set(k, o.t)); return M;
            }
            function llega() {
                const M = mapa(), vis = new Set([R.cap.f + ',' + R.cap.c]), q = [[R.cap.f, R.cap.c]];
                while (q.length) {
                    const [a, b] = q.pop(), v = M.get(a + ',' + b);
                    if (a === R.casa.f && b === R.casa.c) return true;
                    DIRS.forEach(([bit, df, dc, opu]) => { const k = (a + df) + ',' + (b + dc); if (v & bit && !vis.has(k) && M.has(k) && M.get(k) & opu) { vis.add(k); q.push([a + df, b + dc]); } });
                }
                return false;
            }
            const emoji = (t, x, y, tam) => { ctx.font = `${tam}px serif`; ctx.textAlign = 'center'; ctx.textBaseline = 'middle'; ctx.fillText(t, x, y); };
            L.dibujar = function () {
                L.limpiar('#f4fce3');
                ctx.fillStyle = '#5c940d'; Logica.redondo(ctx, TX - 10, TY - 10, N * CEL + 20, N * CEL + 20, 14); ctx.fill();
                for (let f = 0; f < N; f++) for (let c = 0; c < N; c++) { ctx.fillStyle = (f + c) % 2 ? '#b2f2bb' : '#a9e34b'; ctx.fillRect(TX + c * CEL + 1, TY + f * CEL + 1, CEL - 2, CEL - 2); }
                const X = c => TX + c * CEL, Y = f => TY + f * CEL;
                R.arboles.forEach(([f, c]) => emoji('🌲', X(c) + CEL / 2, Y(f) + CEL / 2, CEL * .7));
                emoji('🐺', X(R.lobo[1]) + CEL / 2, Y(R.lobo[0]) + CEL / 2, CEL * .62);
                [[R.cap, '👧'], [R.casa, '🏡']].forEach(([q, e]) => { camino(X(q.c), Y(q.f), CEL, q.m, '#c68b4e'); emoji(e, X(q.c) + CEL / 2, Y(q.f) + CEL / 2, CEL * .6); });
                ctx.fillStyle = '#e03131'; ctx.beginPath(); ctx.arc(X(R.cap.c) + CEL * .5, Y(R.cap.f) + CEL * .22, CEL * .12, Math.PI, 0); ctx.fill();   // la caperuza
                g.dibujar(ctx);
                if (llega()) { const M = mapa(); M.forEach((m, k) => { const [f, c] = k.split(',').map(Number); camino(X(c), Y(f), CEL, m, 'rgba(250,176,5,.75)'); }); }
            };
            return {
                girar: () => g.girarUltima(),
                ayuda() { ayudar(g, R.sol, api, L); if (llega()) api.gano({estrellas: 1}); },
            };
        },
    });
})();
