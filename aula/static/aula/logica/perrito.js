/* Perrito a su casita: rompecabezas deslizante de 4×4 con un espacio vacío. Las fichas tienen caminos;
 * deslícelas (toque una ficha junto al espacio) hasta que cada perrito llegue a su casita por el camino. */
Logica.registrar('perrito', {
    nombre: 'Perrito a su casita',
    instrucciones: 'Toque una ficha que esté junto al espacio vacío para deslizarla. Arme el camino para que cada perrito llegue a su casita del mismo color.',
    total: d => d.length,
    titulo: (d, i) => `Patio ${i + 1} · ${d[i].perros.length} perrito(s) · se puede en ${d[i].minimo} movimientos`,
    iniciar(zona, datos, i, api) {
        const R = datos[i], N = 4, C = 92, M = 70, L = api.lienzo(N * C + 2 * M, N * C + 2 * M + 10), ctx = L.ctx;
        const NB = 1, EB = 2, SB = 4, WB = 8, COLORES = ['#e8590c', '#1971c2'];
        let t = R.fichas.slice(), movs = 0, listo = false;
        const historia = [];
        const entrada = (lado, k) => ({arriba: [[0, k], NB], abajo: [[N - 1, k], SB], izq: [[k, 0], WB], der: [[k, N - 1], EB]}[lado]);
        const DIRS = [[NB, -1, 0, SB], [EB, 0, 1, WB], [SB, 1, 0, NB], [WB, 0, -1, EB]];
        function recorrido(perro) {     // las celdas a donde llega el perrito, y si llega a la casita
            const [[pl, pk], [cl, ck]] = perro, [[f, c], m] = entrada(pl, pk), [[gf, gc], gm] = entrada(cl, ck);
            const vis = new Set();
            if (t[f * N + c] < 0 || !(t[f * N + c] & m)) return {vis, llega: false};
            vis.add(f + ',' + c); const q = [[f, c]]; let llega = false;
            while (q.length) {
                const [a, b] = q.pop(), v = t[a * N + b];
                if (a === gf && b === gc && v & gm) llega = true;
                DIRS.forEach(([bit, df, dc, opu]) => { const na = a + df, nb = b + dc; if (v & bit && na >= 0 && nb >= 0 && na < N && nb < N && !vis.has(na + ',' + nb) && t[na * N + nb] >= 0 && t[na * N + nb] & opu) { vis.add(na + ',' + nb); q.push([na, nb]); } });
            }
            return {vis, llega};
        }
        const X = c => M + c * C, Y = f => M + f * C;
        function afuera(lado, k) {      // punto afuera del tablero frente a la entrada
            return {arriba: [X(k) + C / 2, M - 34], abajo: [X(k) + C / 2, M + N * C + 34], izq: [M - 34, Y(k) + C / 2], der: [M + N * C + 34, Y(k) + C / 2]}[lado];
        }
        function perro(x, y, col) {
            ctx.fillStyle = '#f1e0c5'; ctx.beginPath(); ctx.ellipse(x, y + 8, 16, 12, 0, 0, Math.PI * 2); ctx.fill();
            ctx.beginPath(); ctx.arc(x, y - 8, 14, 0, Math.PI * 2); ctx.fill();
            ctx.fillStyle = '#a0703c'; ctx.beginPath(); ctx.ellipse(x - 13, y - 6, 6, 11, .3, 0, Math.PI * 2); ctx.ellipse(x + 13, y - 6, 6, 11, -.3, 0, Math.PI * 2); ctx.fill();
            ctx.fillStyle = '#111'; ctx.beginPath(); ctx.arc(x - 5, y - 10, 2.2, 0, Math.PI * 2); ctx.arc(x + 5, y - 10, 2.2, 0, Math.PI * 2); ctx.arc(x, y - 3, 3, 0, Math.PI * 2); ctx.fill();
            ctx.fillStyle = col; ctx.fillRect(x - 12, y + 3, 24, 4);
        }
        function casita(x, y, col) {
            ctx.fillStyle = '#a0703c'; ctx.fillRect(x - 20, y - 6, 40, 28);
            ctx.fillStyle = col; ctx.beginPath(); ctx.moveTo(x - 26, y - 4); ctx.lineTo(x, y - 26); ctx.lineTo(x + 26, y - 4); ctx.fill();
            ctx.fillStyle = '#3b2a1a'; ctx.beginPath(); ctx.arc(x, y + 10, 9, Math.PI, 0); ctx.fill(); ctx.fillRect(x - 9, y + 10, 18, 12);
        }
        L.dibujar = function () {
            L.limpiar('#ebfbee');
            ctx.fillStyle = '#5c940d'; Logica.redondo(ctx, M - 10, M - 10, N * C + 20, N * C + 20, 16); ctx.fill();
            const brillo = new Set(); R.perros.forEach(p => { const r = recorrido(p); if (r.llega) r.vis.forEach(k => brillo.add(k)); });
            for (let f = 0; f < N; f++) for (let c = 0; c < N; c++) {
                const v = t[f * N + c], x = X(c), y = Y(f);
                if (v < 0) { ctx.fillStyle = '#2b5f12'; ctx.fillRect(x + 3, y + 3, C - 6, C - 6); continue; }
                ctx.fillStyle = '#c0eb75'; Logica.redondo(ctx, x + 3, y + 3, C - 6, C - 6, 10); ctx.fill();
                ctx.fillStyle = 'rgba(92,148,13,.35)'; [[.2, .2], [.75, .3], [.3, .8], [.8, .78]].forEach(([a, b]) => { ctx.beginPath(); ctx.arc(x + a * C, y + b * C, 3, 0, Math.PI * 2); ctx.fill(); });
                // el camino de tierra
                ctx.strokeStyle = brillo.has(f + ',' + c) ? '#f59f00' : '#c68b4e'; ctx.lineWidth = C * .28; ctx.lineCap = 'butt';
                const cx = x + C / 2, cy = y + C / 2;
                [[NB, cx, y + 3], [EB, x + C - 3, cy], [SB, cx, y + C - 3], [WB, x + 3, cy]].forEach(([bit, ex, ey]) => { if (v & bit) { ctx.beginPath(); ctx.moveTo(cx, cy); ctx.lineTo(ex, ey); ctx.stroke(); } });
                if (v) { ctx.fillStyle = ctx.strokeStyle; ctx.beginPath(); ctx.arc(cx, cy, C * .14, 0, Math.PI * 2); ctx.fill(); }
                ctx.strokeStyle = 'rgba(0,0,0,.15)'; ctx.lineWidth = 1; Logica.redondo(ctx, x + 3, y + 3, C - 6, C - 6, 10); ctx.stroke();
            }
            R.perros.forEach(([[pl, pk], [cl, ck]], k) => { const [px, py] = afuera(pl, pk), [cx, cy] = afuera(cl, ck); perro(px, py, COLORES[k]); casita(cx, cy, COLORES[k]); });
            L.texto(`Movimientos: ${movs}`, M, N * C + 2 * M + 2, {tam: 13, color: '#2b8a3e', negrita: true});
        };
        L.cv.addEventListener('pointerdown', ev => {
            if (listo) return;
            const {x, y} = L.punto(ev), c = Math.floor((x - M) / C), f = Math.floor((y - M) / C);
            if (f < 0 || c < 0 || f >= N || c >= N) return;
            const h = t.indexOf(-1), hf = Math.floor(h / N), hc = h % N;
            if (Math.abs(hf - f) + Math.abs(hc - c) !== 1) return;
            historia.push(t.slice());
            t[h] = t[f * N + c]; t[f * N + c] = -1; movs += 1; api.movimiento(); api.sonido('toque'); L.dibujar();
            if (R.perros.every(p => recorrido(p).llega)) { listo = true; api.gano({estrellas: movs <= R.minimo ? 3 : movs <= R.minimo * 1.6 ? 2 : 1, detalle: `mínimo: ${R.minimo}`}); }
        });
        return { deshacer() { const u = historia.pop(); if (!u || listo) return; t = u; movs -= 1; api.movimiento(-1); L.dibujar(); } };
    },
});
