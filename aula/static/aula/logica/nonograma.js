/* Nonograma: los números de cada fila y columna dicen cuántos cuadros seguidos van pintados, en orden.
 * Toque para pintar; en modo ✗ (o con clic derecho) marca los que van vacíos. Todos tienen una sola solución. */
Logica.registrar('nonograma', {
    nombre: 'Nonograma',
    instrucciones: 'Los números de cada fila y columna dicen cuántos cuadros seguidos se pintan, en ese orden (con al menos un espacio entre grupos). Toque para pintar; use el modo ✗ (o clic derecho) para marcar los que van vacíos.',
    total: d => d.length,
    titulo: (d, i) => `Nonograma ${i + 1} · ${d[i].n}×${d[i].n}`,
    iniciar(zona, datos, i, api) {
        const R = datos[i], n = R.n, MF = Math.max(...R.filas.map(f => f.length)), MC = Math.max(...R.columnas.map(c => c.length));
        const C = Math.min(44, Math.floor(420 / (n + Math.max(MF, MC) * .62))), PX = Math.ceil(MF * C * .62) + 12, PY = Math.ceil(MC * C * .62) + 12;
        const W = PX + n * C + 20, H = PY + n * C + 60, L = api.lienzo(W, H), ctx = L.ctx;
        let g = Array.from({length: n}, () => Array(n).fill(0)), modoX = false, arrastre = null;
        const historia = [];
        const sol = R.solucion.map(f => f.split('').map(Number));
        function pistasDe(linea) { const r = []; let k = 0; linea.forEach(v => { if (v === 1) k++; else if (k) { r.push(k); k = 0; } }); if (k) r.push(k); return r.length ? r : [0]; }
        L.dibujar = function () {
            L.limpiar('#fff');
            for (let f = 0; f < n; f++) {
                const ok = pistasDe(g[f]).join() === R.filas[f].join();
                R.filas[f].slice().reverse().forEach((v, k) => L.texto(String(v), PX - 8 - k * C * .62, PY + f * C + C / 2 + 1, {tam: C * .42, alinear: 'right', base: 'middle', negrita: true, color: ok ? '#2f9e44' : '#343a40'}));
            }
            for (let c = 0; c < n; c++) {
                const ok = pistasDe(g.map(r => r[c])).join() === R.columnas[c].join();
                R.columnas[c].slice().reverse().forEach((v, k) => L.texto(String(v), PX + c * C + C / 2, PY - 8 - k * C * .62, {tam: C * .42, alinear: 'center', negrita: true, color: ok ? '#2f9e44' : '#343a40'}));
            }
            for (let f = 0; f < n; f++) for (let c = 0; c < n; c++) {
                const x = PX + c * C, y = PY + f * C;
                ctx.fillStyle = g[f][c] === 1 ? '#1c3d5a' : (f + c) % 2 ? '#f8f9fa' : '#f1f3f5'; ctx.fillRect(x, y, C, C);
                if (g[f][c] === 2) { ctx.strokeStyle = '#e03131'; ctx.lineWidth = 2; ctx.beginPath(); ctx.moveTo(x + C * .28, y + C * .28); ctx.lineTo(x + C * .72, y + C * .72); ctx.moveTo(x + C * .72, y + C * .28); ctx.lineTo(x + C * .28, y + C * .72); ctx.stroke(); }
            }
            ctx.strokeStyle = '#adb5bd'; ctx.lineWidth = 1;
            for (let k = 0; k <= n; k++) {
                ctx.lineWidth = k % 5 === 0 ? 2 : 1; ctx.strokeStyle = k % 5 === 0 ? '#495057' : '#adb5bd';
                ctx.beginPath(); ctx.moveTo(PX + k * C, PY); ctx.lineTo(PX + k * C, PY + n * C); ctx.moveTo(PX, PY + k * C); ctx.lineTo(PX + n * C, PY + k * C); ctx.stroke();
            }
            // botón de modo
            ctx.fillStyle = modoX ? '#e03131' : '#1c3d5a'; Logica.redondo(ctx, PX, PY + n * C + 14, 150, 34, 10); ctx.fill();
            L.texto(modoX ? 'Modo: marcar ✗' : 'Modo: pintar ■', PX + 75, PY + n * C + 31, {tam: 14, negrita: true, alinear: 'center', base: 'middle', color: '#fff'});
        };
        function celda(x, y) { const c = Math.floor((x - PX) / C), f = Math.floor((y - PY) / C); return f >= 0 && f < n && c >= 0 && c < n ? [f, c] : null; }
        function poner(f, c, v) { if (g[f][c] === v) return; g[f][c] = v; }
        L.cv.addEventListener('contextmenu', ev => ev.preventDefault());
        L.cv.addEventListener('pointerdown', ev => {
            const {x, y} = L.punto(ev);
            if (x >= PX && x <= PX + 150 && y >= PY + n * C + 14 && y <= PY + n * C + 48) { modoX = !modoX; L.dibujar(); return; }
            const k = celda(x, y); if (!k) return;
            try { L.cv.setPointerCapture(ev.pointerId); } catch (e) { /* */ }
            historia.push(g.map(r => r.slice()));
            const marca = (modoX || ev.button === 2) ? 2 : 1, v = g[k[0]][k[1]] === marca ? 0 : marca;
            arrastre = v; poner(k[0], k[1], v); api.movimiento(); L.dibujar(); revisar();
        });
        L.cv.addEventListener('pointermove', ev => { if (arrastre === null) return; const {x, y} = L.punto(ev), k = celda(x, y); if (k) { poner(k[0], k[1], arrastre); L.dibujar(); revisar(); } });
        const soltar = () => { arrastre = null; };
        L.cv.addEventListener('pointerup', soltar); L.cv.addEventListener('pointercancel', soltar);
        function revisar() { if (g.every((r, f) => r.every((v, c) => (v === 1) === (sol[f][c] === 1)))) api.gano({estrellas: 3}); }
        return { deshacer() { const u = historia.pop(); if (u) { g = u; L.dibujar(); } } };
    },
});
