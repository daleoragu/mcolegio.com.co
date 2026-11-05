/* Laberinto de colores: 4 columnas (caben 5 fichas en cada una) y un puesto de espera arriba.
 * Toque una columna para subir su ficha de arriba al corredor y luego la columna (o el puesto de espera)
 * a donde la lleva. Gana cuando las columnas quedan como en la tarjeta. */
Logica.registrar('laberinto', {
    nombre: 'Laberinto de colores',
    instrucciones: 'Toque una columna para subir la ficha de arriba al corredor; luego toque la columna a donde la lleva (o el puesto blanco de espera). Deje las columnas como en la tarjeta.',
    total: d => d.retos.length,
    titulo: (d, i) => `Tarjeta ${i + 1} · se puede en ${d.retos[i].minimo} movimientos`,
    iniciar(zona, datos, i, api) {
        const reto = datos.retos[i], W = 640, H = 430, L = api.lienzo(W, H), ctx = L.ctx;
        const COL = {R: '#e03131', A: '#1c7ed6', V: '#2f9e44', Y: '#fcc419'};
        let cols = reto.inicio.map(s => s.split('')), espera = null, mano = null, movs = 0;
        const historia = [];
        const meta = reto.meta.map(s => s.split(''));
        const CX = k => 110 + k * 80, FICHA = 30, BASE = 380;
        function ficha(x, y, v, r) {
            ctx.fillStyle = 'rgba(0,0,0,.2)'; ctx.beginPath(); ctx.ellipse(x + 2, y + 4, r, r * .9, 0, 0, Math.PI * 2); ctx.fill();
            ctx.fillStyle = COL[v]; ctx.beginPath(); ctx.ellipse(x, y, r, r * .9, 0, 0, Math.PI * 2); ctx.fill();
            ctx.fillStyle = 'rgba(255,255,255,.35)'; ctx.beginPath(); ctx.ellipse(x - r * .3, y - r * .35, r * .3, r * .18, 0, 0, Math.PI * 2); ctx.fill();
        }
        L.dibujar = function () {
            L.limpiar('#f8f0e3');
            ctx.fillStyle = '#e9d3ad'; Logica.redondo(ctx, 40, 30, 380, 380, 26); ctx.fill();
            // corredor de arriba y puesto de espera
            ctx.fillStyle = '#c8a26b'; Logica.redondo(ctx, 60, 60, 340, 44, 22); ctx.fill();
            ctx.fillStyle = '#fff'; ctx.beginPath(); ctx.arc(80, 82, 18, 0, Math.PI * 2); ctx.fill();
            if (espera) ficha(80, 82, espera, 16);
            for (let k = 0; k < 4; k++) {
                ctx.fillStyle = '#c8a26b'; Logica.redondo(ctx, CX(k) - 24, 104, 48, BASE - 96, 20); ctx.fill();
                cols[k].forEach((v, j) => ficha(CX(k), BASE - 24 - j * (FICHA + 22), v, FICHA * .78));
            }
            if (mano) ficha(CX(mano.de === 'e' ? 0 : mano.de) + (mano.de === 'e' ? -30 : 0), 82, mano.v, 24);
            // la tarjeta
            const KX = 470, KY = 80, K = 28;
            ctx.fillStyle = '#fff'; Logica.redondo(ctx, KX - 16, KY - 40, 4 * K + 34, 4 * K + 64, 12); ctx.fill();
            L.texto('TARJETA', KX + 2 * K, KY - 16, {tam: 13, negrita: true, alinear: 'center', color: '#495057'});
            meta.forEach((col, c) => col.forEach((v, j) => { ctx.fillStyle = COL[v]; ctx.beginPath(); ctx.arc(KX + c * K + K / 2, KY + (3 - j) * K + K / 2, K * .38, 0, Math.PI * 2); ctx.fill(); }));
            L.texto('(abajo = fondo de la columna)', KX + 2 * K, KY + 4 * K + 16, {tam: 10, alinear: 'center', color: '#868e96'});
            L.texto(`Movimientos: ${movs}`, KX - 10, KY + 4 * K + 50, {tam: 13, color: '#495057'});
        };
        function guardar() { historia.push({cols: cols.map(c => c.slice()), espera}); }
        function tocar(dest) {
            if (!mano) {
                if (dest === 'e') { if (espera) { mano = {v: espera, de: 'e'}; espera = null; } }
                else if (cols[dest].length) { guardar(); mano = {v: cols[dest].pop(), de: dest}; historia[historia.length - 1].tomada = true; }
                if (mano) api.sonido('toque');
                L.dibujar(); return;
            }
            if (dest === 'e') { if (espera) { api.aviso('El puesto de espera ya está ocupado.'); return; } espera = mano.v; }
            else { if (cols[dest].length >= 5) { api.aviso('Esa columna está llena.'); api.sonido('mal'); return; } cols[dest].push(mano.v); }
            const volvio = mano.de === dest; mano = null;
            if (!volvio) { movs += 1; api.movimiento(); }
            api.sonido('toque'); L.dibujar();
            if (!espera && cols.every((c, k) => c.join('') === meta[k].join(''))) api.gano({estrellas: movs <= reto.minimo ? 3 : movs <= reto.minimo * 1.6 ? 2 : 1, detalle: `mínimo: ${reto.minimo}`});
        }
        L.cv.addEventListener('pointerdown', ev => {
            const {x, y} = L.punto(ev);
            if (Math.hypot(x - 80, y - 82) < 24) return tocar('e');
            const k = [0, 1, 2, 3].find(k => Math.abs(x - CX(k)) < 34 && y > 50 && y < BASE + 20);
            if (k !== undefined) tocar(k);
        });
        return {
            deshacer() {
                if (mano) { if (mano.de === 'e') espera = mano.v; else cols[mano.de].push(mano.v); mano = null; historia.pop(); L.dibujar(); return; }
                const u = historia.pop(); if (!u) return; cols = u.cols; espera = u.espera; movs = Math.max(0, movs - 1); api.movimiento(-1); L.dibujar();
            },
        };
    },
});
