/* Los tres cerditos — retos de día y de noche. Hay 3 piezas con casitas y jardines.
 * De día: cada cerdito queda en un jardín (afuera, jugando). De noche: cada cerdito queda dentro de una casita.
 * Siempre: el lobo se queda afuera (en el pasto, sin pieza encima). Tocar gira la pieza. */
Logica.registrar('cerditos', {
    nombre: 'Los tres cerditos',
    instrucciones: 'Ponga las 3 piezas en el tablero. ☀️ De día: los cerditos quedan en los jardines (cerquitas verdes). 🌙 De noche: los cerditos quedan dentro de las casitas. El lobo siempre se queda afuera, en el pasto. Un toque gira la pieza.',
    total: d => d.retos.length,
    etiqueta: (d, i) => (d.retos[i].modo === 'dia' ? '☀' : '☾') + (i + 1),
    titulo: (d, i) => d.retos[i].modo === 'dia' ? `Reto de día ${i + 1}: cerditos en el jardín` : `Reto de noche ${i + 1}: cerditos en las casitas`,
    iniciar(zona, datos, i, api) {
        const reto = datos.retos[i], noche = reto.modo === 'noche';
        const CEL = 76, TX = 30, TY = 40, W = 720, H = 400, L = api.lienzo(W, H), ctx = L.ctx;
        const bandeja = [{x: 380, y: 50}, {x: 540, y: 60}, {x: 420, y: 230}];
        const esta = (lista, f, c) => lista.some(([a, b]) => a === f && b === c);
        let ayudas = 0;
        const g = Logica.piezasGrilla(L, {
            tablero: {x: TX, y: TY, cel: CEL, filas: 4, cols: 4},
            piezas: datos.piezas.map((cel, k) => ({nombre: k, voltear: false, celdas: cel.map(([f, c, t]) => [f, c, t])})),
            bandeja, escalaBandeja: .7,
            dibujarCelda(ctx, p, t, x, y, k) {
                if (t === 'c') {
                    // casita: pared, techo, puerta y ventana (de noche, con luz)
                    ctx.fillStyle = '#f1c27d'; ctx.fillRect(x + k * .12, y + k * .38, k * .76, k * .58);
                    ctx.fillStyle = '#c92a2a'; ctx.beginPath(); ctx.moveTo(x + k * .04, y + k * .42); ctx.lineTo(x + k / 2, y + k * .06); ctx.lineTo(x + k * .96, y + k * .42); ctx.fill();
                    ctx.fillStyle = '#8b5a2b'; ctx.fillRect(x + k * .42, y + k * .62, k * .18, k * .34);
                    ctx.fillStyle = noche ? '#ffe066' : '#a5d8ff'; ctx.fillRect(x + k * .2, y + k * .5, k * .16, k * .14);
                    ctx.strokeStyle = 'rgba(0,0,0,.3)'; ctx.lineWidth = 1; ctx.strokeRect(x + 1, y + 1, k - 2, k - 2);
                } else {
                    // jardín con cerca: transparente para ver quién está adentro
                    ctx.fillStyle = 'rgba(64,192,87,.55)'; ctx.fillRect(x + 1, y + 1, k - 2, k - 2);
                    ctx.strokeStyle = '#f8f9fa'; ctx.lineWidth = Math.max(1.5, k * .04);
                    ctx.strokeRect(x + k * .08, y + k * .08, k * .84, k * .84);
                    for (let j = 1; j < 4; j++) { ctx.beginPath(); ctx.moveTo(x + k * .08 + j * k * .21, y + k * .02); ctx.lineTo(x + k * .08 + j * k * .21, y + k * .14); ctx.stroke(); }
                }
            },
            redibujar: () => L.dibujar(),
            alCambiar() { api.movimiento(); if (resuelto()) api.gano({estrellas: ayudas ? 2 : 3}); },
        });
        function resuelto() {
            if (!g.piezas.every(p => p.en)) return false;
            const occ = g.ocupadas();
            const cer = reto.cerditos.every(([f, c]) => { const o = occ.get(f + ',' + c); return o && o.t === (noche ? 'c' : 'j'); });
            const lob = reto.lobos.every(([f, c]) => !occ.has(f + ',' + c));
            return cer && lob;
        }
        function cerdito(x, y, k) {
            ctx.fillStyle = '#f783ac'; ctx.beginPath(); ctx.arc(x, y, k * .26, 0, Math.PI * 2); ctx.fill();
            ctx.beginPath(); ctx.moveTo(x - k * .2, y - k * .14); ctx.lineTo(x - k * .14, y - k * .32); ctx.lineTo(x - k * .04, y - k * .2); ctx.fill();
            ctx.beginPath(); ctx.moveTo(x + k * .2, y - k * .14); ctx.lineTo(x + k * .14, y - k * .32); ctx.lineTo(x + k * .04, y - k * .2); ctx.fill();
            ctx.fillStyle = '#e64980'; ctx.beginPath(); ctx.ellipse(x, y + k * .06, k * .1, k * .07, 0, 0, Math.PI * 2); ctx.fill();
            ctx.fillStyle = '#212529'; ctx.fillRect(x - k * .1, y - k * .08, k * .04, k * .05); ctx.fillRect(x + k * .06, y - k * .08, k * .04, k * .05);
        }
        function lobo(x, y, k) {
            ctx.fillStyle = '#6c757d';
            ctx.beginPath(); ctx.moveTo(x - k * .24, y - k * .1); ctx.lineTo(x - k * .18, y - k * .36); ctx.lineTo(x - k * .04, y - k * .18); ctx.fill();
            ctx.beginPath(); ctx.moveTo(x + k * .24, y - k * .1); ctx.lineTo(x + k * .18, y - k * .36); ctx.lineTo(x + k * .04, y - k * .18); ctx.fill();
            ctx.beginPath(); ctx.arc(x, y, k * .25, 0, Math.PI * 2); ctx.fill();
            ctx.fillStyle = '#ced4da'; ctx.beginPath(); ctx.ellipse(x, y + k * .1, k * .13, k * .1, 0, 0, Math.PI * 2); ctx.fill();
            ctx.fillStyle = '#ffd43b'; ctx.fillRect(x - k * .12, y - k * .08, k * .06, k * .05); ctx.fillRect(x + k * .06, y - k * .08, k * .06, k * .05);
            ctx.fillStyle = '#212529'; ctx.beginPath(); ctx.arc(x, y + k * .06, k * .04, 0, Math.PI * 2); ctx.fill();
        }
        L.dibujar = function () {
            L.limpiar(noche ? '#1c2541' : '#e7f5ff');
            L.texto(noche ? '🌙 RETO DE NOCHE: cerditos dentro de las casitas, lobo afuera' : '☀️ RETO DE DÍA: cerditos en los jardines, lobo afuera',
                    TX, 26, {tam: 15, negrita: true, color: noche ? '#ffe066' : '#1864ab'});
            ctx.fillStyle = noche ? '#2b5f3a' : '#8ce99a'; Logica.redondo(ctx, TX - 10, TY - 10, 4 * CEL + 20, 4 * CEL + 20, 12); ctx.fill();
            for (let f = 0; f < 4; f++) for (let c = 0; c < 4; c++) {
                ctx.fillStyle = (f + c) % 2 ? (noche ? '#2f6b40' : '#b2f2bb') : (noche ? '#336f44' : '#a9e8b4');
                ctx.fillRect(TX + c * CEL + 1, TY + f * CEL + 1, CEL - 2, CEL - 2);
            }
            reto.cerditos.forEach(([f, c]) => cerdito(TX + c * CEL + CEL / 2, TY + f * CEL + CEL / 2 + 6, CEL));
            reto.lobos.forEach(([f, c]) => lobo(TX + c * CEL + CEL / 2, TY + f * CEL + CEL / 2 + 6, CEL));
            g.dibujar(ctx);
            // un cerdito dentro de una casita se asoma por la ventana
            const occ = g.ocupadas();
            reto.cerditos.forEach(([f, c]) => { const o = occ.get(f + ',' + c); if (o && o.t === 'c') { ctx.fillStyle = '#f783ac'; ctx.beginPath(); ctx.arc(TX + c * CEL + CEL * .28, TY + f * CEL + CEL * .57, CEL * .06, 0, Math.PI * 2); ctx.fill(); } });
            reto.lobos.forEach(([f, c]) => { if (occ.has(f + ',' + c)) { ctx.fillStyle = 'rgba(224,49,49,.85)'; L.texto('¡lobo!', TX + c * CEL + CEL / 2, TY + f * CEL + 14, {tam: 12, negrita: true, alinear: 'center', color: '#ff6b6b'}); } });
        };
        return {
            girar: () => g.girarUltima(),
            ayuda() {
                // Pone una pieza de la solución en su sitio
                const s = reto.solucion.find(([k, celdas, f, c]) => { const p = g.piezas[k]; return !(p.en && p.en.f === f && p.en.c === c && JSON.stringify(p.celdas.map(a => a.slice(0, 2)).sort()) === JSON.stringify(celdas.map(a => a.slice(0, 2)).sort())); });
                if (!s) return;
                const [k, celdas, f, c] = s, set = new Set(celdas.map(([a, b]) => (f + a) + ',' + (c + b)));
                g.piezas.forEach(p => { if (p.en && p.i !== k && p.celdas.some(([a, b]) => set.has((p.en.f + a) + ',' + (p.en.c + b)))) { p.en = null; p.x = bandeja[p.i].x; p.y = bandeja[p.i].y; } });
                g.colocarEn(g.piezas[k], celdas, f, c); ayudas += 1; api.aviso('Esa pieza ya quedó en su sitio.'); L.dibujar();
                if (resuelto()) api.gano({estrellas: 1});
            },
        };
    },
});
