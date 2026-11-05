/* Torres de Hanói: pase todos los discos a la última torre. Se mueve un disco a la vez y nunca
 * un disco grande sobre uno pequeño. Toque una torre para tomar el disco de arriba y otra para dejarlo. */
Logica.registrar('hanoi', {
    nombre: 'Torres de Hanói',
    instrucciones: 'Pase todos los discos a la torre de la derecha. Se mueve un disco a la vez y nunca puede quedar uno grande sobre uno pequeño. Toque una torre para tomar el disco de arriba y otra para dejarlo.',
    total: () => 7,
    titulo: (d, i) => `${i + 3} discos · mínimo ${2 ** (i + 3) - 1} movimientos`,
    iniciar(zona, datos, i, api) {
        const n = i + 3, W = 640, H = 340, L = api.lienzo(W, H), ctx = L.ctx;
        const COL = ['#e03131', '#f76707', '#fab005', '#40c057', '#15aabf', '#4c6ef5', '#ae3ec9', '#e64980', '#868e96', '#495057'];
        let torres = [Array.from({length: n}, (_, k) => n - k), [], []], mano = null, desde = -1, movs = 0;
        const historia = [];
        const xT = t => 120 + t * 200, BASE = 290, ALTO = Math.min(26, 200 / n);
        L.dibujar = function () {
            L.limpiar('#fff8ec');
            ctx.fillStyle = '#8b5a2b'; Logica.redondo(ctx, 20, BASE, W - 40, 16, 6); ctx.fill();
            torres.forEach((t, k) => {
                ctx.fillStyle = desde === k ? '#c68b4e' : '#a0703c'; Logica.redondo(ctx, xT(k) - 6, BASE - 230, 12, 232, 6); ctx.fill();
                t.forEach((d, j) => disco(d, xT(k), BASE - (j + 1) * ALTO));
                L.texto(['A', 'B', 'C'][k], xT(k), BASE + 38, {tam: 16, negrita: true, alinear: 'center', color: '#6b4423'});
            });
            if (mano) disco(mano, xT(desde), 40);
            L.texto(`Movimientos: ${movs} · mínimo: ${2 ** n - 1}`, 20, 26, {tam: 14, color: '#495057'});
        };
        function disco(d, x, y) {
            const w = 40 + d * (130 / n);
            ctx.fillStyle = COL[(d - 1) % COL.length]; Logica.redondo(ctx, x - w / 2, y, w, ALTO - 2, 8); ctx.fill();
            ctx.fillStyle = 'rgba(255,255,255,.3)'; Logica.redondo(ctx, x - w / 2 + 4, y + 3, w - 8, 5, 3); ctx.fill();
        }
        function tocar(k) {
            if (mano === null) {
                if (!torres[k].length) return;
                mano = torres[k].pop(); desde = k; api.sonido('toque');
            } else {
                const arriba = torres[k][torres[k].length - 1];
                if (arriba !== undefined && arriba < mano) { api.aviso('No se puede poner un disco grande sobre uno pequeño.'); api.sonido('mal'); return; }
                torres[k].push(mano);
                if (k !== desde) { historia.push([desde, k]); movs += 1; api.movimiento(); }
                mano = null; desde = -1; api.sonido('toque');
                if (torres[2].length === n) {
                    const min = 2 ** n - 1;
                    api.gano({estrellas: movs === min ? 3 : movs <= min * 1.5 ? 2 : 1, detalle: `mínimo posible: ${min}`});
                }
            }
            L.dibujar();
        }
        L.cv.addEventListener('pointerdown', ev => { const {x} = L.punto(ev); tocar(x < 220 ? 0 : x < 420 ? 1 : 2); });
        const teclas = ev => { const k = {'1': 0, '2': 1, '3': 2, a: 0, b: 1, c: 2}[ev.key.toLowerCase()]; if (k !== undefined) tocar(k); };
        document.addEventListener('keydown', teclas);
        return {
            deshacer() {
                if (mano !== null) { torres[desde].push(mano); mano = null; desde = -1; L.dibujar(); return; }
                const u = historia.pop(); if (!u) return;
                torres[u[0]].push(torres[u[1]].pop()); movs -= 1; api.movimiento(-1); L.dibujar();
            },
        };
    },
});
