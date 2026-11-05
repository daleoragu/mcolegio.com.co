/* Conejos saltarines: los conejos saltan en línea recta por encima de una o más piezas seguidas
 * (conejos, hongos o zorros) y caen en la primera casilla vacía; no pueden saltar si al lado no hay nada.
 * Los zorros ocupan 2 casillas y se deslizan hacia adelante o hacia atrás. Gana cuando todos los conejos
 * están en los huecos. Toque una pieza y luego la casilla hacia donde va. */
Logica.registrar('conejos', {
    nombre: 'Conejos saltarines',
    instrucciones: 'Meta a todos los conejos en los huecos. Un conejo salta en línea recta por encima de piezas seguidas (hongos, zorros u otros conejos) y cae en la primera casilla vacía. Los zorros se deslizan a lo largo. Toque una pieza y luego la casilla hacia donde la quiere llevar.',
    total: d => d.length,
    titulo: (d, i) => `Pradera ${i + 1} · se puede en ${d[i].minimo} movimientos`,
    iniciar(zona, datos, i, api) {
        const R = datos[i], N = 5, C = 80, M = 24, L = api.lienzo(N * C + 2 * M, N * C + 2 * M + 24), ctx = L.ctx;
        const HUECOS = ['0,0', '0,4', '4,0', '4,4', '2,2'];
        const COL = ['#f8f9fa', '#adb5bd', '#d9a066'];
        let conejos = R.conejos.map(([f, c], k) => ({f, c, k})), zorros = R.zorros.map(([f, c, h]) => ({f, c, h: !!h}));
        const hongos = R.hongos.map(([f, c]) => ({f, c}));
        let sel = null, movs = 0, listo = false;
        const historia = [];
        const celdasZorro = z => z.h ? [[z.f, z.c], [z.f, z.c + 1]] : [[z.f, z.c], [z.f + 1, z.c]];
        function ocupada(f, c, salvo) {
            return conejos.some(r => r !== salvo && r.f === f && r.c === c) || hongos.some(h => h.f === f && h.c === c) ||
                   zorros.some(z => z !== salvo && celdasZorro(z).some(([a, b]) => a === f && b === c));
        }
        const X = c => M + c * C, Y = f => M + f * C;
        L.dibujar = function () {
            L.limpiar('#d3f9d8');
            ctx.fillStyle = '#2b8a3e'; Logica.redondo(ctx, M - 12, M - 12, N * C + 24, N * C + 24, 18); ctx.fill();
            for (let f = 0; f < N; f++) for (let c = 0; c < N; c++) {
                ctx.fillStyle = (f + c) % 2 ? '#69db7c' : '#8ce99a'; ctx.fillRect(X(c) + 2, Y(f) + 2, C - 4, C - 4);
                if (HUECOS.includes(f + ',' + c)) { ctx.fillStyle = '#5c3d2e'; ctx.beginPath(); ctx.ellipse(X(c) + C / 2, Y(f) + C / 2 + 6, C * .34, C * .26, 0, 0, Math.PI * 2); ctx.fill(); ctx.fillStyle = '#3b2a1a'; ctx.beginPath(); ctx.ellipse(X(c) + C / 2, Y(f) + C / 2 + 8, C * .26, C * .18, 0, 0, Math.PI * 2); ctx.fill(); }
            }
            hongos.forEach(h => {
                const x = X(h.c) + C / 2, y = Y(h.f) + C / 2;
                ctx.fillStyle = '#f8f9fa'; ctx.fillRect(x - 8, y, 16, 22);
                ctx.fillStyle = '#e03131'; ctx.beginPath(); ctx.arc(x, y + 2, 26, Math.PI, 0); ctx.fill();
                ctx.fillStyle = '#fff'; [[-12, -8], [4, -14], [14, -4]].forEach(([a, b]) => { ctx.beginPath(); ctx.arc(x + a, y + b, 4, 0, Math.PI * 2); ctx.fill(); });
            });
            zorros.forEach(z => {
                const [a, b] = celdasZorro(z)[0], x = X(b) + 8, y = Y(a) + 8, w = z.h ? 2 * C - 16 : C - 16, h = z.h ? C - 16 : 2 * C - 16;
                ctx.fillStyle = sel === z ? '#ffd43b' : '#f76707'; Logica.redondo(ctx, x, y, w, h, 24); ctx.fill();
                ctx.fillStyle = '#fff'; const cx = z.h ? x + w - 22 : x + w / 2, cy = z.h ? y + h / 2 : y + h - 22;
                ctx.beginPath(); ctx.arc(cx, cy + 6, 10, 0, Math.PI * 2); ctx.fill();
                ctx.fillStyle = '#111'; ctx.beginPath(); ctx.arc(cx - 6, cy - 4, 3, 0, Math.PI * 2); ctx.arc(cx + 6, cy - 4, 3, 0, Math.PI * 2); ctx.arc(cx, cy + 9, 3, 0, Math.PI * 2); ctx.fill();
                ctx.fillStyle = '#d9480f'; ctx.beginPath(); ctx.moveTo(cx - 14, cy - 8); ctx.lineTo(cx - 8, cy - 22); ctx.lineTo(cx - 2, cy - 10); ctx.moveTo(cx + 14, cy - 8); ctx.lineTo(cx + 8, cy - 22); ctx.lineTo(cx + 2, cy - 10); ctx.fill();
                const tx = z.h ? x + 14 : x + w / 2, ty = z.h ? y + h / 2 : y + 14;
                ctx.fillStyle = '#fff'; ctx.beginPath(); ctx.arc(tx, ty, 7, 0, Math.PI * 2); ctx.fill();
            });
            conejos.forEach(r => {
                const x = X(r.c) + C / 2, y = Y(r.f) + C / 2 + 6, enHueco = HUECOS.includes(r.f + ',' + r.c);
                if (sel === r) { ctx.strokeStyle = '#ffd43b'; ctx.lineWidth = 5; ctx.beginPath(); ctx.arc(x, y - 6, 34, 0, Math.PI * 2); ctx.stroke(); }
                ctx.fillStyle = COL[r.k % 3];
                ctx.beginPath(); ctx.ellipse(x - 8, y - 30, 6, 16, -.15, 0, Math.PI * 2); ctx.ellipse(x + 8, y - 30, 6, 16, .15, 0, Math.PI * 2); ctx.fill();
                if (!enHueco) { ctx.beginPath(); ctx.ellipse(x, y + 8, 18, 14, 0, 0, Math.PI * 2); ctx.fill(); }
                ctx.beginPath(); ctx.arc(x, y - 8, 15, 0, Math.PI * 2); ctx.fill();
                ctx.strokeStyle = 'rgba(0,0,0,.25)'; ctx.lineWidth = 1; ctx.stroke();
                ctx.fillStyle = '#f783ac'; ctx.beginPath(); ctx.ellipse(x - 8, y - 30, 2.5, 9, -.15, 0, Math.PI * 2); ctx.ellipse(x + 8, y - 30, 2.5, 9, .15, 0, Math.PI * 2); ctx.fill();
                ctx.fillStyle = '#111'; ctx.beginPath(); ctx.arc(x - 5, y - 10, 2.5, 0, Math.PI * 2); ctx.arc(x + 5, y - 10, 2.5, 0, Math.PI * 2); ctx.fill();
                ctx.fillStyle = '#e64980'; ctx.beginPath(); ctx.arc(x, y - 4, 2.5, 0, Math.PI * 2); ctx.fill();
            });
            const dentro = conejos.filter(r => HUECOS.includes(r.f + ',' + r.c)).length;
            L.texto(`Movimientos: ${movs} · Conejos a salvo: ${dentro}/${conejos.length}`, M, N * C + 2 * M + 12, {tam: 13, color: '#2b8a3e', negrita: true});
        };
        function guardar() { historia.push({conejos: conejos.map(r => ({...r})), zorros: zorros.map(z => ({...z})), movs}); }
        function hecho() {
            movs += 1; api.movimiento(); api.sonido('toque'); sel = null; L.dibujar();
            if (conejos.every(r => HUECOS.includes(r.f + ',' + r.c))) { listo = true; api.gano({estrellas: movs <= R.minimo ? 3 : movs <= R.minimo * 1.5 ? 2 : 1, detalle: `mínimo: ${R.minimo}`}); }
        }
        L.cv.addEventListener('pointerdown', ev => {
            if (listo) return;
            const {x, y} = L.punto(ev), c = Math.floor((x - M) / C), f = Math.floor((y - M) / C);
            if (f < 0 || c < 0 || f >= N || c >= N) return;
            const r = conejos.find(q => q.f === f && q.c === c), z = zorros.find(q => celdasZorro(q).some(([a, b]) => a === f && b === c));
            if (r || z) { sel = sel === (r || z) ? null : (r || z); L.dibujar(); return; }
            if (!sel) return;
            if (conejos.includes(sel)) {
                if (f !== sel.f && c !== sel.c) { api.aviso('Los conejos saltan en línea recta.'); return; }
                const df = Math.sign(f - sel.f), dc = Math.sign(c - sel.c);
                let k = 1; while (sel.f + df * k >= 0 && sel.f + df * k < N && sel.c + dc * k >= 0 && sel.c + dc * k < N && ocupada(sel.f + df * k, sel.c + dc * k, sel)) k++;
                const nf = sel.f + df * k, nc = sel.c + dc * k;
                if (k === 1) { api.aviso('Para saltar tiene que haber algo al lado (hongo, zorro u otro conejo).'); api.sonido('mal'); return; }
                if (nf < 0 || nc < 0 || nf >= N || nc >= N) { api.aviso('Ese salto se sale de la pradera.'); api.sonido('mal'); return; }
                guardar(); sel.f = nf; sel.c = nc; hecho();
            } else {
                const z = sel, eje = z.h ? c - z.c : f - z.f, mismo = z.h ? f === z.f : c === z.c;
                if (!mismo) { api.aviso('El zorro solo se desliza a lo largo.'); return; }
                const paso = Math.sign(eje), metaDesp = eje > 0 ? eje - 1 : eje;     // que la punta quede en la casilla tocada
                let d = 0;
                while (d !== metaDesp) {
                    const n = d + paso, celdas = z.h ? [[z.f, z.c + n], [z.f, z.c + n + 1]] : [[z.f + n, z.c], [z.f + n + 1, z.c]];
                    if (celdas.some(([a, b]) => a < 0 || b < 0 || a >= N || b >= N || ocupada(a, b, z))) break;
                    d = n;
                }
                if (!d) { api.aviso('El zorro no puede pasar por ahí.'); api.sonido('mal'); return; }
                guardar(); if (z.h) z.c += d; else z.f += d; hecho();
            }
        });
        return { deshacer() { const u = historia.pop(); if (!u || listo) return; conejos = u.conejos; zorros = u.zorros; movs = u.movs; sel = null; api.movimiento(-1); L.dibujar(); } };
    },
});
