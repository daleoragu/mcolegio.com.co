/* Deslizables de colores: 15 fichas de 4 colores y un espacio vacío. Toque una ficha que esté al lado
 * del espacio para deslizarla. Gana cuando el tablero queda igual a la tarjeta. */
Logica.registrar('kiriku', {
    nombre: 'Deslizables de colores',
    instrucciones: 'Toque una ficha que esté junto al espacio vacío para deslizarla. Deje el tablero igual a la tarjeta de la derecha.',
    total: d => d.retos.length,
    titulo: (d, i) => `Tarjeta ${i + 1} · se puede en ${d.retos[i].minimo} movimientos`,
    iniciar(zona, datos, i, api) {
        const reto = datos.retos[i], W = 620, H = 380, L = api.lienzo(W, H), ctx = L.ctx, C = 78, TX = 40, TY = 40;
        const COL = {R: '#e64980', A: '#1098ad', V: '#40c057', N: '#fd7e14'};
        let g = reto.inicio.map(f => f.split('')), movs = 0;
        const historia = [];
        const meta = reto.meta.map(f => f.split(''));
        L.dibujar = function () {
            L.limpiar('#f1e3c6');
            ctx.fillStyle = '#c8a26b'; Logica.redondo(ctx, TX - 14, TY - 14, 4 * C + 28, 4 * C + 28, 16); ctx.fill();
            for (let f = 0; f < 4; f++) for (let c = 0; c < 4; c++) {
                ctx.fillStyle = '#b08850'; ctx.fillRect(TX + c * C + 4, TY + f * C + 4, C - 8, C - 8);
                const v = g[f][c]; if (v === '.') continue;
                ctx.fillStyle = 'rgba(0,0,0,.2)'; ctx.beginPath(); ctx.arc(TX + c * C + C / 2 + 2, TY + f * C + C / 2 + 4, C * .4, 0, Math.PI * 2); ctx.fill();
                ctx.fillStyle = COL[v]; ctx.beginPath(); ctx.arc(TX + c * C + C / 2, TY + f * C + C / 2, C * .4, 0, Math.PI * 2); ctx.fill();
                ctx.fillStyle = 'rgba(255,255,255,.3)'; ctx.beginPath(); ctx.arc(TX + c * C + C * .4, TY + f * C + C * .38, C * .12, 0, Math.PI * 2); ctx.fill();
            }
            const KX = 420, KY = 70, K = 34;
            ctx.fillStyle = '#fff'; Logica.redondo(ctx, KX - 16, KY - 40, 4 * K + 32, 4 * K + 60, 12); ctx.fill();
            L.texto('TARJETA', KX + 2 * K, KY - 16, {tam: 13, negrita: true, alinear: 'center', color: '#495057'});
            meta.forEach((fila, f) => fila.forEach((v, c) => {
                if (v === '.') { ctx.strokeStyle = '#ced4da'; ctx.beginPath(); ctx.arc(KX + c * K + K / 2, KY + f * K + K / 2, K * .36, 0, Math.PI * 2); ctx.stroke(); return; }
                ctx.fillStyle = COL[v]; ctx.beginPath(); ctx.arc(KX + c * K + K / 2, KY + f * K + K / 2, K * .38, 0, Math.PI * 2); ctx.fill();
            }));
            L.texto(`Movimientos: ${movs}`, KX - 10, KY + 4 * K + 48, {tam: 13, color: '#495057'});
        };
        function tocar(f, c) {
            const v = [[0, 1], [0, -1], [1, 0], [-1, 0]].find(([df, dc]) => g[f + df] && g[f + df][c + dc] === '.');
            if (!v || g[f][c] === '.') return;
            historia.push(g.map(r => r.slice()));
            g[f + v[0]][c + v[1]] = g[f][c]; g[f][c] = '.'; movs += 1; api.movimiento(); api.sonido('toque'); L.dibujar();
            if (g.every((r, a) => r.every((x, b) => x === meta[a][b]))) api.gano({estrellas: movs <= reto.minimo ? 3 : movs <= reto.minimo * 2 ? 2 : 1, detalle: `mínimo: ${reto.minimo}`});
        }
        L.cv.addEventListener('pointerdown', ev => {
            const {x, y} = L.punto(ev), c = Math.floor((x - TX) / C), f = Math.floor((y - TY) / C);
            if (f >= 0 && f < 4 && c >= 0 && c < 4) tocar(f, c);
        });
        return { deshacer() { const u = historia.pop(); if (!u) return; g = u; movs -= 1; api.movimiento(-1); L.dibujar(); } };
    },
});
