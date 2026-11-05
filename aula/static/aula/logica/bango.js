/* Tablero 36: el tablero tiene los números del 1 al 36. El reto dice qué número queda destapado;
 * todas las demás casillas se cubren con las 7 piezas. Tocar gira la pieza; doble toque la voltea. */
Logica.registrar('bango', {
    nombre: 'Tablero 36',
    instrucciones: 'Deje destapado solo el número del reto y cubra todas las demás casillas con las 7 piezas. Arrastre las piezas al tablero; un toque las gira y dos toques seguidos las voltean.',
    total: d => d.retos.length,
    etiqueta: (d, i) => d.retos[i],
    titulo: (d, i) => `Reto: dejar destapado el ${d.retos[i]}`,
    iniciar(zona, datos, i, api) {
        const n = datos.retos[i], hueco = [Math.floor((n - 1) / 6), (n - 1) % 6];
        const CEL = 54, TX = 30, TY = 40, W = 760, H = 420, L = api.lienzo(W, H), ctx = L.ctx;
        const COL = {I: '#c92a2a', L: '#74b816', P: '#d6336c', U: '#f76707', X: '#0ca678', Y: '#364fc7', N: '#fab005', T: '#7048e8', W: '#1098ad', Z: '#5c940d'};
        const nombres = Object.keys(datos.piezas);
        const bandeja = nombres.map((_, k) => ({x: 380 + (k % 3) * 125, y: 40 + Math.floor(k / 3) * 125}));
        let ayudas = 0;
        const g = Logica.piezasGrilla(L, {
            tablero: {x: TX, y: TY, cel: CEL, filas: 6, cols: 6, valida: (f, c) => !(f === hueco[0] && c === hueco[1])},
            piezas: nombres.map(k => ({nombre: k, color: COL[k], celdas: datos.piezas[k].map(([a, b]) => [a, b])})),
            bandeja, escalaBandeja: .42,
            dibujarCelda(ctx, p, t, x, y, k) {
                ctx.fillStyle = p.color; ctx.fillRect(x + .5, y + .5, k - 1, k - 1);
                ctx.fillStyle = 'rgba(255,255,255,.18)'; ctx.fillRect(x + 3, y + 3, k - 6, k * .18);
            },
            redibujar: () => L.dibujar(),
            alCambiar() {
                api.movimiento();
                const occ = g.ocupadas();
                if (g.piezas.every(p => p.en) && occ.size === 35) api.gano({estrellas: ayudas === 0 ? 3 : ayudas === 1 ? 2 : 1});
            },
        });
        L.dibujar = function () {
            L.limpiar('#f8f1e5');
            ctx.fillStyle = '#1b4332'; Logica.redondo(ctx, TX - 14, TY - 14, 6 * CEL + 28, 6 * CEL + 28, 12); ctx.fill();
            for (let f = 0; f < 6; f++) for (let c = 0; c < 6; c++) {
                const x = TX + c * CEL, y = TY + f * CEL, num = f * 6 + c + 1, esHueco = f === hueco[0] && c === hueco[1];
                ctx.fillStyle = esHueco ? '#fff3bf' : '#e9d5b5'; ctx.fillRect(x + 1, y + 1, CEL - 2, CEL - 2);
                L.texto(String(num), x + CEL / 2, y + CEL / 2 + 1, {tam: esHueco ? 22 : 18, negrita: esHueco, alinear: 'center', base: 'middle', color: esHueco ? '#c92a2a' : '#6b4f2c'});
            }
            L.texto('RETO', TX + 6 * CEL + 40, TY + 6 * CEL + 8, {tam: 12, color: '#6b4f2c'});
            L.texto(String(n), TX + 6 * CEL + 40, TY + 6 * CEL - 14, {tam: 28, negrita: true, color: '#c92a2a'});
            g.dibujar(ctx);
        };
        return {
            girar: () => g.girarUltima(), voltear: () => g.voltearUltima(),
            ayuda() {
                // Pone en su sitio una pieza de la solución que todavía no está bien puesta
                const sol = datos.soluciones[n];
                const k = Object.keys(sol).find(k => {
                    const p = g.piezas.find(p => p.nombre === k);
                    if (!p.en) return true;
                    const mias = new Set(p.celdas.map(([a, b]) => (p.en.f + a) + ',' + (p.en.c + b)));
                    return !sol[k].every(([a, b]) => mias.has(a + ',' + b));
                });
                if (!k) return;
                ayudas += 1;
                // quitar del tablero las piezas que estorban
                const celdas = sol[k], set = new Set(celdas.map(([a, b]) => a + ',' + b));
                g.piezas.forEach(p => { if (p.en && p.nombre !== k && p.celdas.some(([a, b]) => set.has((p.en.f + a) + ',' + (p.en.c + b)))) { p.en = null; p.x = bandeja[p.i].x; p.y = bandeja[p.i].y; } });
                const f0 = Math.min(...celdas.map(c => c[0])), c0 = Math.min(...celdas.map(c => c[1]));
                g.colocarEn(g.piezas.find(p => p.nombre === k), celdas.map(([a, b]) => [a - f0, b - c0]), f0, c0);
                api.aviso('Esa pieza ya quedó en su sitio.'); L.dibujar();
                if (g.piezas.every(p => p.en) && g.ocupadas().size === 35) api.gano({estrellas: 1});
            },
        };
    },
});
