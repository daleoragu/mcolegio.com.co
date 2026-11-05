/* Cuatro cuadrantes: el tablero tiene 4 cuadros de 3×3 y hay 4 piezas con huecos. La tarjeta muestra
 * dónde deben quedar los huecos y de qué color (el color de la pieza que los rodea). Ponga cada pieza
 * en un cuadro, girándola o volteándola, para que el tablero quede igual a la tarjeta. */
Logica.registrar('kadogemo', {
    nombre: 'Cuatro cuadrantes',
    instrucciones: 'Ponga las 4 piezas en los 4 cuadros para que los huecos queden donde están los puntos de la tarjeta y del mismo color. Un toque gira la pieza; dos toques la voltean.',
    total: d => d.retos.length,
    titulo: (d, i) => `Tarjeta ${i + 1}`,
    iniciar(zona, datos, i, api) {
        const reto = datos.retos[i], CEL = 44, SEP = 14, TX = 30, TY = 40, W = 760, H = 380, L = api.lienzo(W, H), ctx = L.ctx;
        const nombres = Object.keys(datos.piezas);
        // tablero lógico de 6×6; cada pieza solo entra en la esquina de un cuadro
        const px = c => TX + c * CEL + (c >= 3 ? SEP : 0), py = f => TY + f * CEL + (f >= 3 ? SEP : 0);
        const bandeja = nombres.map((_, k) => ({x: 340 + (k % 2) * 110, y: 50 + Math.floor(k / 2) * 120}));
        let ayudas = 0;
        const g = Logica.piezasGrilla(L, {
            tablero: {x: TX, y: TY, cel: CEL, filas: 6, cols: 6, anclas: (f, c) => f % 3 === 0 && c % 3 === 0},
            piezas: nombres.map(k => {
                const huecos = new Set(datos.piezas[k].map(([f, c]) => f + ',' + c)), celdas = [];
                for (let f = 0; f < 3; f++) for (let c = 0; c < 3; c++) if (!huecos.has(f + ',' + c)) celdas.push([f, c]);
                return {nombre: k, color: datos.colores[k], celdas};
            }),
            bandeja, escalaBandeja: .75,
            dibujarCelda(ctx, p, t, x, y, k) {
                // con el espacio entre cuadros cuando la pieza está puesta
                if (p.en) { const f = p.en.f + Math.round((y - (TY + p.en.f * CEL)) / CEL), c = p.en.c + Math.round((x - (TX + p.en.c * CEL)) / CEL); x = px(c); y = py(f); }
                ctx.fillStyle = p.color; ctx.fillRect(x, y, k, k);
                ctx.fillStyle = 'rgba(255,255,255,.15)'; ctx.fillRect(x + 2, y + 2, k - 4, 5);
            },
            contorno: false,
            redibujar: () => L.dibujar(),
            alCambiar() { api.movimiento(); if (resuelto()) api.gano({estrellas: ayudas ? 2 : 3}); },
        });
        function piezaEn(q) { return g.piezas.find(p => p.en && p.en.f === Math.floor(q / 2) * 3 && p.en.c === (q % 2) * 3); }
        function resuelto() {
            if (!g.piezas.every(p => p.en)) return false;
            const occ = g.ocupadas(), puntos = new Set(reto.puntos.map(([f, c, n]) => `${f},${c},${n}`));
            for (let f = 0; f < 6; f++) for (let c = 0; c < 6; c++) {
                if (occ.has(f + ',' + c)) continue;
                const q = Math.floor(f / 3) * 2 + Math.floor(c / 3), p = piezaEn(q);
                if (!p || !puntos.has(`${f},${c},${p.nombre}`)) return false;
            }
            return true;
        }
        L.dibujar = function () {
            L.limpiar('#fbf3e4');
            ctx.fillStyle = '#7a4a24'; Logica.redondo(ctx, TX - 12, TY - 12, 6 * CEL + SEP + 24, 6 * CEL + SEP + 24, 12); ctx.fill();
            for (let f = 0; f < 6; f++) for (let c = 0; c < 6; c++) { ctx.fillStyle = '#e8c999'; ctx.fillRect(px(c) + 1, py(f) + 1, CEL - 2, CEL - 2); }
            g.dibujar(ctx);
            // en los huecos de las piezas puestas se ve una bolita del color de la pieza
            const occ = g.ocupadas();
            for (let f = 0; f < 6; f++) for (let c = 0; c < 6; c++) {
                const p = piezaEn(Math.floor(f / 3) * 2 + Math.floor(c / 3));
                if (p && !occ.has(f + ',' + c)) { ctx.fillStyle = p.color; ctx.beginPath(); ctx.arc(px(c) + CEL / 2, py(f) + CEL / 2, CEL * .3, 0, Math.PI * 2); ctx.fill(); ctx.strokeStyle = '#fff'; ctx.lineWidth = 2; ctx.stroke(); }
            }
            // la tarjeta
            const KX = 580, KY = 60, K = 26;
            ctx.fillStyle = '#fff'; Logica.redondo(ctx, KX - 14, KY - 34, 6 * K + 36, 6 * K + 64, 12); ctx.fill();
            ctx.strokeStyle = '#ced4da'; ctx.lineWidth = 2; ctx.stroke();
            L.texto('TARJETA', KX + 3 * K + 4, KY - 14, {tam: 13, negrita: true, alinear: 'center', color: '#495057'});
            for (let q = 0; q < 4; q++) { ctx.strokeStyle = '#dee2e6'; ctx.strokeRect(KX + (q % 2) * (3 * K + 8), KY + Math.floor(q / 2) * (3 * K + 8), 3 * K, 3 * K); }
            reto.puntos.forEach(([f, c, n]) => {
                ctx.fillStyle = datos.colores[n]; ctx.beginPath();
                ctx.arc(KX + c * K + (c >= 3 ? 8 : 0) + K / 2, KY + f * K + (f >= 3 ? 8 : 0) + K / 2, K * .32, 0, Math.PI * 2); ctx.fill();
            });
        };
        return {
            girar: () => g.girarUltima(), voltear: () => g.voltearUltima(),
            ayuda() {
                // Dice qué pieza va en el primer cuadro que está mal
                for (let q = 0; q < 4; q++) {
                    const n = (reto.puntos.find(([f, c]) => Math.floor(f / 3) * 2 + Math.floor(c / 3) === q) || [])[2];
                    const p = piezaEn(q);
                    if (n && (!p || p.nombre !== n)) {
                        ayudas += 1;
                        api.aviso(`En el cuadro ${['de arriba a la izquierda', 'de arriba a la derecha', 'de abajo a la izquierda', 'de abajo a la derecha'][q]} va la pieza del color de sus puntos.`);
                        return;
                    }
                }
                api.aviso('Las piezas están en su cuadro: gírelas o voltéelas hasta que los huecos coincidan.');
            },
        };
    },
});
