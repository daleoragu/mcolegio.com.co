/* Atrapa al ladrón (bloqueo de calles): el carro del ladrón quiere salir del barrio por cualquier borde.
 * Ponga TODAS las piezas de calle (cada una lleva una patrulla) sobre las calles para cerrarle el paso.
 * No se pueden poner sobre edificios ni sobre los túneles (por debajo de un túnel el ladrón sí pasa).
 * Los retos se generaron y se verificaron con un solucionador (aula/logica_generadores/bloqueo.py). */
(function () {
    'use strict';
    const V4 = [[0, 1], [0, -1], [1, 0], [-1, 0]];
    const ETAPA = i => i < 8 ? 'Iniciación' : i < 16 ? 'Principiante' : i < 24 ? 'Intermedio' : i < 32 ? 'Avanzado' : 'Experto';
    function ayudar(g, sol, api, L) {
        const k = sol.findIndex((celdas, n) => { const p = g.piezas[n]; if (!p.en) return true; const mias = new Set(p.celdas.map(([a, b]) => (p.en.f + a) + ',' + (p.en.c + b))); return !celdas.every(([a, b]) => mias.has(a + ',' + b)); });
        if (k < 0) return false;
        const celdas = sol[k], set = new Set(celdas.map(([a, b]) => a + ',' + b));
        g.piezas.forEach(p => { if (p.en && p.i !== k && p.celdas.some(([a, b]) => set.has((p.en.f + a) + ',' + (p.en.c + b)))) p.en = null; });
        // la patrulla queda en la misma celda de la pieza: se busca la orientación de la pieza que coincide con la solución
        const p = g.piezas[k], f0 = Math.min(...celdas.map(c => c[0])), c0 = Math.min(...celdas.map(c => c[1]));
        const objetivo = new Set(celdas.map(([a, b]) => (a - f0) + ',' + (b - c0)));
        for (let n = 0; n < 8; n++) {
            const forma = p.celdas.map(c => c[0] + ',' + c[1]);
            if (forma.length === objetivo.size && forma.every(x => objetivo.has(x))) break;
            if (n === 3) g.voltearPieza(p); else g.girarPieza(p);
        }
        g.colocarEn(p, p.celdas, f0, c0);
        api.aviso('Esa pieza ya quedó en su sitio.'); L.dibujar();
        return true;
    }
    Logica.registrar('ladron', {
        nombre: 'Atrapa al ladrón',
        instrucciones: 'El ladrón (carro rojo) quiere salir del barrio por cualquier borde. Ponga TODAS las piezas de calle, cada una con su patrulla, para cerrarle todos los caminos. No caben sobre los edificios ni sobre los túneles: por un túnel el ladrón sí pasa. Un toque gira la pieza y dos toques la voltean.',
        total: d => d.length,
        titulo: (d, i) => `${ETAPA(i)} · barrio ${d[i].N}×${d[i].N} · ${d[i].piezas.length} piezas${d[i].tuneles ? ' · ' + d[i].tuneles + ' túnel(es)' : ''}`,
        iniciar(zona, datos, i, api) {
            const R = datos[i], N = R.N, CEL = Math.min(66, Math.floor(400 / N)), TX = 26, TY = 34;
            const anchoTablero = N * CEL, W = Math.max(760, TX + anchoTablero + 40 + 3 * 120), H = Math.max(N * CEL + 80, 120 + Math.ceil(R.piezas.length / 3) * 125 + 40);
            const L = api.lienzo(W, H), ctx = L.ctx;
            const tipo = (f, c) => R.mapa[f][c];
            const bandeja = R.piezas.map((_, k) => ({x: TX + anchoTablero + 44 + (k % 3) * 118, y: 46 + Math.floor(k / 3) * 125}));
            const g = Logica.piezasGrilla(L, {
                tablero: {x: TX, y: TY, cel: CEL, filas: N, cols: N,
                          valida: (f, c) => tipo(f, c) === '.' && !(f === R.ladron[0] && c === R.ladron[1])},
                piezas: R.piezas.map((celdas, k) => ({nombre: k, celdas})),
                bandeja, escalaBandeja: .55,
                dibujarCelda(ctx, p, t, x, y, k) {
                    // calle gris con raya amarilla; la celda con la patrulla lleva el carro
                    ctx.fillStyle = '#5c636a'; ctx.fillRect(x + 1, y + 1, k - 2, k - 2);
                    ctx.strokeStyle = '#ffd43b'; ctx.lineWidth = Math.max(1, k * .05); ctx.setLineDash([k * .12, k * .1]);
                    ctx.beginPath(); ctx.moveTo(x + k * .5, y + k * .12); ctx.lineTo(x + k * .5, y + k * .88); ctx.stroke(); ctx.setLineDash([]);
                    if (t === 'p') { ctx.font = `${k * .62}px serif`; ctx.textAlign = 'center'; ctx.textBaseline = 'middle'; ctx.fillText('🚓', x + k / 2, y + k / 2 + 1); }
                },
                redibujar: () => L.dibujar(),
                alCambiar() { api.movimiento(); revisar(); },
            });
            // Para la ayuda: girar y voltear una pieza puntual
            g.girarPieza = p => { p.celdas = norm(p.celdas.map(([f, c, t]) => [c, -f, t])); };
            g.voltearPieza = p => { p.celdas = norm(p.celdas.map(([f, c, t]) => [f, -c, t])); };
            function norm(c) { const mf = Math.min(...c.map(a => a[0])), mc = Math.min(...c.map(a => a[1])); return c.map(([f, k, t]) => [f - mf, k - mc, t]); }
            let ayudas = 0, gano = false;
            function escapa() {
                const tapado = new Set(g.ocupadas().keys());
                const vis = new Set([R.ladron.join()]), q = [R.ladron];
                while (q.length) {
                    const [f, c] = q.pop();
                    if (f === 0 || c === 0 || f === N - 1 || c === N - 1) return true;
                    V4.forEach(([df, dc]) => {
                        const F = f + df, C = c + dc, k = F + ',' + C;
                        if (F >= 0 && C >= 0 && F < N && C < N && tipo(F, C) !== 'E' && !vis.has(k) && !tapado.has(k)) { vis.add(k); q.push([F, C]); }
                    });
                }
                return false;
            }
            const todas = () => g.piezas.every(p => p.en);
            function revisar() {
                if (gano) return;
                if (todas() && !escapa()) { gano = true; api.gano({estrellas: ayudas ? 1 : 3}); }
                else if (todas()) api.aviso('Están todas las piezas, pero el ladrón todavía tiene por dónde salir.');
                else if (!escapa()) api.aviso('¡Ya no tiene salida! Ponga también las piezas que faltan.');
            }
            const emoji = (t, x, y, tam) => { ctx.font = `${tam}px serif`; ctx.textAlign = 'center'; ctx.textBaseline = 'middle'; ctx.fillText(t, x, y); };
            function edificio(x, y, k, f, c) {
                const tonos = ['#868e96', '#748ffc', '#e599f7', '#ffa94d', '#69db7c'];
                ctx.fillStyle = tonos[(f * 7 + c * 3) % tonos.length]; Logica.redondo(ctx, x + 3, y + 3, k - 6, k - 6, 5); ctx.fill();
                ctx.fillStyle = '#fff3bf';
                for (let a = 0; a < 3; a++) for (let b = 0; b < 3; b++) ctx.fillRect(x + k * (.18 + b * .24), y + k * (.16 + a * .24), k * .14, k * .12);
            }
            L.dibujar = function () {
                L.limpiar('#e7f5ff');
                ctx.fillStyle = '#1864ab'; Logica.redondo(ctx, TX - 10, TY - 10, N * CEL + 20, N * CEL + 20, 14); ctx.fill();
                for (let f = 0; f < N; f++) for (let c = 0; c < N; c++) {
                    const x = TX + c * CEL, y = TY + f * CEL, t = tipo(f, c);
                    ctx.fillStyle = '#ced4da'; ctx.fillRect(x + 1, y + 1, CEL - 2, CEL - 2);
                    if (t === 'E') { edificio(x, y, CEL, f, c); continue; }
                    ctx.strokeStyle = '#f8f9fa'; ctx.setLineDash([6, 6]); ctx.lineWidth = 2;
                    ctx.beginPath(); ctx.moveTo(x + CEL / 2, y + 6); ctx.lineTo(x + CEL / 2, y + CEL - 6); ctx.moveTo(x + 6, y + CEL / 2); ctx.lineTo(x + CEL - 6, y + CEL / 2); ctx.stroke(); ctx.setLineDash([]);
                    if (t === 'T') {
                        // túnel: arco de piedra; por aquí pasa el ladrón y no se puede bloquear
                        ctx.fillStyle = '#495057'; ctx.beginPath(); ctx.arc(x + CEL / 2, y + CEL * .62, CEL * .34, Math.PI, 0); ctx.lineTo(x + CEL * .84, y + CEL * .9); ctx.lineTo(x + CEL * .16, y + CEL * .9); ctx.fill();
                        ctx.fillStyle = '#212529'; ctx.beginPath(); ctx.arc(x + CEL / 2, y + CEL * .66, CEL * .22, Math.PI, 0); ctx.lineTo(x + CEL * .72, y + CEL * .9); ctx.lineTo(x + CEL * .28, y + CEL * .9); ctx.fill();
                    }
                    if (f === 0 || c === 0 || f === N - 1 || c === N - 1) {
                        // salida por el borde
                        ctx.fillStyle = 'rgba(250,82,82,.22)'; ctx.fillRect(x + 1, y + 1, CEL - 2, CEL - 2);
                    }
                }
                L.texto('Las calles del borde (rojizas) son salidas', TX + N * CEL / 2, TY - 18, {tam: 11, negrita: true, alinear: 'center', color: '#1864ab'});
                emoji('🚗', TX + R.ladron[1] * CEL + CEL / 2, TY + R.ladron[0] * CEL + CEL / 2, CEL * .62);
                L.texto('Piezas por poner', TX + N * CEL + 44, 26, {tam: 12, negrita: true, color: '#495057'});
                g.dibujar(ctx);
                if (gano || (todas() && !escapa())) L.texto('¡ATRAPADO!', TX + N * CEL / 2, TY + N * CEL + 34, {tam: 20, negrita: true, alinear: 'center', color: '#e03131'});
            };
            return {
                girar: () => g.girarUltima(), voltear: () => g.voltearUltima(),
                ayuda() { if (ayudar(g, R.sol, api, L)) { ayudas++; api.movimiento(); } revisar(); },
            };
        },
    });
})();
