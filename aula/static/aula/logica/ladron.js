/* Atrapa al ladrón: el carro del ladrón quiere salir de la ciudad por cualquier borde. Ponga las piezas de
 * edificios en las calles para encerrarlo; las patrullas ya están puestas y también le cierran el paso.
 * Gana cuando el ladrón ya no puede llegar a ningún borde. Tocar gira la pieza; dos toques la voltean. */
(function () {
    'use strict';
    function azar(semilla) { let s = semilla >>> 0; return () => { s = (s + 0x6D2B79F5) >>> 0; let t = s; t = Math.imul(t ^ t >>> 15, t | 1); t ^= t + Math.imul(t ^ t >>> 7, t | 61); return ((t ^ t >>> 14) >>> 0) / 4294967296; }; }
    const V4 = [[0, 1], [0, -1], [1, 0], [-1, 0]];
    function generar(i) {
        const r = azar(i * 4241 + 7), ent = n => Math.floor(r() * n);
        const N = i < 10 ? 5 : i < 20 ? 6 : 7;
        for (let intento = 0; intento < 400; intento++) {
            // la zona donde queda encerrado (no toca el borde) y el muro que la rodea
            const ini = [1 + ent(N - 2), 1 + ent(N - 2)], zonaE = new Set([ini.join()]), tam = 1 + ent(i < 10 ? 2 : i < 20 ? 4 : 6);
            let frontera = [ini];
            for (let paso = 0; paso < 300 && zonaE.size < tam; paso++) {
                const [f, c] = frontera[ent(frontera.length)], [df, dc] = V4[ent(4)], n = [f + df, c + dc];
                if (n[0] < 1 || n[1] < 1 || n[0] > N - 2 || n[1] > N - 2 || zonaE.has(n.join())) continue;
                zonaE.add(n.join()); frontera.push(n);
            }
            const muro = new Set();
            zonaE.forEach(k => { const [f, c] = k.split(',').map(Number); V4.forEach(([df, dc]) => { const n = (f + df) + ',' + (c + dc); if (!zonaE.has(n)) muro.add(n); }); });
            // el muro se parte en pedazos conectados; los sueltos son patrullas, los demás piezas de 2 a 4
            const resto = new Set(muro), piezas = [], patrullas = [];
            while (resto.size) {
                const primero = [...resto][ent(resto.size)], trozo = [primero]; resto.delete(primero);
                const meta = 2 + ent(3);
                while (trozo.length < meta) {
                    const vec = []; trozo.forEach(k => { const [f, c] = k.split(',').map(Number); V4.forEach(([df, dc]) => { const n = (f + df) + ',' + (c + dc); if (resto.has(n)) vec.push(n); }); });
                    if (!vec.length) break;
                    const n = vec[ent(vec.length)]; trozo.push(n); resto.delete(n);
                }
                if (trozo.length === 1) patrullas.push(trozo[0].split(',').map(Number)); else piezas.push(trozo.map(k => k.split(',').map(Number)));
            }
            if (piezas.length < 2 || piezas.length > 6 || patrullas.length > 3) continue;
            const ladron = [...zonaE][ent(zonaE.size)].split(',').map(Number);
            return {N, ladron, patrullas, piezas: piezas.map(pz => pz.map(([f, c]) => [f, c, 'e']))};
        }
    }
    function ayudar(g, sol, api, L) {
        const k = sol.findIndex((celdas, n) => { const p = g.piezas[n]; if (!p.en) return true; const mias = new Set(p.celdas.map(([a, b]) => (p.en.f + a) + ',' + (p.en.c + b))); return !celdas.every(([a, b]) => mias.has(a + ',' + b)); });
        if (k < 0) return;
        const celdas = sol[k], set = new Set(celdas.map(([a, b]) => a + ',' + b));
        g.piezas.forEach(p => { if (p.en && p.i !== k && p.celdas.some(([a, b]) => set.has((p.en.f + a) + ',' + (p.en.c + b)))) { p.en = null; } });
        const f0 = Math.min(...celdas.map(c => c[0])), c0 = Math.min(...celdas.map(c => c[1]));
        g.colocarEn(g.piezas[k], celdas.map(([a, b, t]) => [a - f0, b - c0, t]), f0, c0);
        api.aviso('Esa pieza ya quedó en su sitio.'); L.dibujar();
    }
    Logica.registrar('ladron', {
        nombre: 'Atrapa al ladrón',
        instrucciones: 'El ladrón (carro rojo) quiere escapar por cualquier borde de la ciudad. Ponga los edificios para cerrarle todas las calles; las patrullas ya le cierran el paso donde están. Un toque gira la pieza y dos toques la voltean.',
        total: () => 30,
        titulo: (d, i) => `Ciudad ${i + 1} · ${i < 10 ? '5×5' : i < 20 ? '6×6' : '7×7'}`,
        iniciar(zona, datos, i, api) {
            const R = generar(i), N = R.N, CEL = Math.min(70, Math.floor(340 / N)), TX = 26, TY = 30, L = api.lienzo(760, Math.max(N * CEL + 70, 420)), ctx = L.ctx;
            const fijas = new Set([R.ladron.join(), ...R.patrullas.map(p => p.join())]);
            const bandeja = R.piezas.map((_, k) => ({x: TX + N * CEL + 40 + (k % 3) * 120, y: 40 + Math.floor(k / 3) * 125}));
            const g = Logica.piezasGrilla(L, {
                tablero: {x: TX, y: TY, cel: CEL, filas: N, cols: N, valida: (f, c) => !fijas.has(f + ',' + c)},
                piezas: R.piezas.map((celdas, k) => ({nombre: k, celdas})),
                bandeja, escalaBandeja: .55,
                dibujarCelda(ctx, p, t, x, y, k) {
                    ctx.fillStyle = '#495057'; ctx.fillRect(x + 1, y + 1, k - 2, k - 2);
                    ctx.fillStyle = '#ffe066';
                    for (let a = 0; a < 3; a++) for (let b = 0; b < 2; b++) ctx.fillRect(x + k * (.18 + b * .38), y + k * (.14 + a * .28), k * .22, k * .14);
                },
                redibujar: () => L.dibujar(),
                alCambiar() { api.movimiento(); if (encerrado()) api.gano({estrellas: 3}); },
            });
            function encerrado() {
                const tapado = new Set([...g.ocupadas().keys(), ...R.patrullas.map(p => p.join())]);
                const vis = new Set([R.ladron.join()]), q = [R.ladron];
                while (q.length) {
                    const [f, c] = q.pop();
                    if (f === 0 || c === 0 || f === N - 1 || c === N - 1) return false;
                    V4.forEach(([df, dc]) => { const k = (f + df) + ',' + (c + dc); if (!vis.has(k) && !tapado.has(k)) { vis.add(k); q.push([f + df, c + dc]); } });
                }
                return true;
            }
            const emoji = (t, x, y, tam) => { ctx.font = `${tam}px serif`; ctx.textAlign = 'center'; ctx.textBaseline = 'middle'; ctx.fillText(t, x, y); };
            L.dibujar = function () {
                L.limpiar('#e7f5ff');
                ctx.fillStyle = '#1864ab'; Logica.redondo(ctx, TX - 10, TY - 10, N * CEL + 20, N * CEL + 20, 14); ctx.fill();
                for (let f = 0; f < N; f++) for (let c = 0; c < N; c++) {
                    const x = TX + c * CEL, y = TY + f * CEL;
                    ctx.fillStyle = '#adb5bd'; ctx.fillRect(x + 1, y + 1, CEL - 2, CEL - 2);
                    ctx.strokeStyle = '#f8f9fa'; ctx.setLineDash([6, 6]); ctx.lineWidth = 2;
                    ctx.beginPath(); ctx.moveTo(x + CEL / 2, y + 6); ctx.lineTo(x + CEL / 2, y + CEL - 6); ctx.moveTo(x + 6, y + CEL / 2); ctx.lineTo(x + CEL - 6, y + CEL / 2); ctx.stroke(); ctx.setLineDash([]);
                }
                L.texto('SALIDA POR CUALQUIER BORDE', TX + N * CEL / 2, TY - 16, {tam: 11, negrita: true, alinear: 'center', color: '#1864ab'});
                R.patrullas.forEach(([f, c]) => emoji('🚓', TX + c * CEL + CEL / 2, TY + f * CEL + CEL / 2, CEL * .62));
                emoji('🚗', TX + R.ladron[1] * CEL + CEL / 2, TY + R.ladron[0] * CEL + CEL / 2, CEL * .62);
                g.dibujar(ctx);
                if (encerrado()) L.texto('¡ATRAPADO!', TX + N * CEL / 2, TY + N * CEL + 30, {tam: 20, negrita: true, alinear: 'center', color: '#e03131'});
            };
            return {
                girar: () => g.girarUltima(), voltear: () => g.voltearUltima(),
                ayuda() { ayudar(g, R.piezas, api, L); if (encerrado()) api.gano({estrellas: 1}); },
            };
        },
    });
})();
