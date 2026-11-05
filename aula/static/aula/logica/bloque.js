/* Bloque rodante (tipo Bloxorz): un bloque de 1×1×2 rueda por las baldosas. Hay que dejarlo PARADO
 * sobre el hueco. Si una parte queda en el aire, se cae y vuelve al comienzo. Vista en 3D (isométrica). */
Logica.registrar('bloque', {
    nombre: 'Bloque rodante',
    instrucciones: 'Haga rodar el bloque con las flechas (o deslizando el dedo) hasta dejarlo PARADO sobre el hueco oscuro. Al rodar, el bloque se acuesta o se para. Si una parte queda fuera de las baldosas, se cae y vuelve a empezar.',
    total: d => d.length,
    titulo: (d, i) => `Tablero ${i + 1} · se puede en ${d[i][0]} movimientos`,
    iniciar(zona, datos, i, api) {
        const [minimo, filas] = datos[i], H = filas.length, W = filas[0].length;
        const tiles = new Set(); let ini = null, meta = null;
        filas.forEach((f, y) => [...f].forEach((ch, x) => { if (ch !== '.') tiles.add(x + ',' + y); if (ch === 'S') ini = [x, y]; if (ch === 'G') meta = [x, y]; }));
        const TW = 52, TH = 26, HZ = 26, OX = H * TW / 2 + 30, OY = 70;
        const L = api.lienzo((W + H) * TW / 2 + 60, (W + H) * TH / 2 + 120), ctx = L.ctx;
        let b = {x: ini[0], y: ini[1], o: 0}, movs = 0, caidas = 0, cayendo = 0, listo = false;
        const iso = (x, y, z) => [OX + (x - y) * TW / 2, OY + (x + y) * TH / 2 - z * HZ];
        const celdas = s => s.o === 0 ? [[s.x, s.y]] : s.o === 1 ? [[s.x, s.y], [s.x + 1, s.y]] : [[s.x, s.y], [s.x, s.y + 1]];
        function mover(s, d) {
            const {x, y, o} = s;
            if (o === 0) return {derecha: {x: x + 1, y, o: 1}, izquierda: {x: x - 2, y, o: 1}, abajo: {x, y: y + 1, o: 2}, arriba: {x, y: y - 2, o: 2}}[d];
            if (o === 1) return {derecha: {x: x + 2, y, o: 0}, izquierda: {x: x - 1, y, o: 0}, abajo: {x, y: y + 1, o: 1}, arriba: {x, y: y - 1, o: 1}}[d];
            return {derecha: {x: x + 1, y, o: 2}, izquierda: {x: x - 1, y, o: 2}, abajo: {x, y: y + 2, o: 0}, arriba: {x, y: y - 1, o: 0}}[d];
        }
        function cara(pts, color) { ctx.fillStyle = color; ctx.beginPath(); pts.forEach(([a, c], k) => (k ? ctx.lineTo : ctx.moveTo).call(ctx, a, c)); ctx.closePath(); ctx.fill(); ctx.strokeStyle = 'rgba(0,0,0,.25)'; ctx.lineWidth = 1; ctx.stroke(); }
        function caja(x, y, z, dx, dy, dz, top, izq, der) {
            const P = (a, c, e) => iso(x + a, y + c, z + e);
            cara([P(0, dy, 0), P(dx, dy, 0), P(dx, dy, dz), P(0, dy, dz)], izq);          // frente (hacia abajo-izquierda)
            cara([P(dx, 0, 0), P(dx, dy, 0), P(dx, dy, dz), P(dx, 0, dz)], der);          // costado (hacia abajo-derecha)
            cara([P(0, 0, dz), P(dx, 0, dz), P(dx, dy, dz), P(0, dy, dz)], top);           // arriba
        }
        L.dibujar = function () {
            L.limpiar('#0b1f3a');
            // estrellas de fondo
            ctx.fillStyle = 'rgba(255,255,255,.4)'; for (let k = 0; k < 40; k++) ctx.fillRect((k * 97) % L.W, (k * 53) % L.H, 2, 2);
            const orden = [...tiles].map(k => k.split(',').map(Number)).sort((p, q) => (p[0] + p[1]) - (q[0] + q[1]));
            orden.forEach(([x, y]) => {
                const esMeta = meta && x === meta[0] && y === meta[1];
                if (esMeta) { cara([iso(x, y, 0), iso(x + 1, y, 0), iso(x + 1, y + 1, 0), iso(x, y + 1, 0)], '#111'); return; }
                caja(x, y, -.25, 1, 1, .25, (x + y) % 2 ? '#adb5bd' : '#ced4da', '#6c757d', '#868e96');
            });
            // el bloque (se cae hundiéndose si quedó en el aire)
            const dz = b.o === 0 ? 2 : 1, dx = b.o === 1 ? 2 : 1, dy = b.o === 2 ? 2 : 1;
            caja(b.x, b.y, -cayendo, dx, dy, dz, '#ffa94d', '#d9480f', '#f76707');
            L.texto(`Movimientos: ${movs}${caidas ? ` · caídas: ${caidas}` : ''}`, 14, L.H - 12, {tam: 13, color: '#ced4da'});
        };
        function intentar(d) {
            if (listo || cayendo) return;
            const n = mover(b, d); b = n; movs += 1; api.movimiento();
            const ok = celdas(n).every(([x, y]) => tiles.has(x + ',' + y));
            if (!ok) {
                caidas += 1; api.sonido('mal'); api.aviso('¡Se cayó! Vuelve al comienzo.');
                const anim = () => { cayendo += .25; L.dibujar(); if (cayendo < 4) requestAnimationFrame(anim); else { cayendo = 0; b = {x: ini[0], y: ini[1], o: 0}; L.dibujar(); } };
                requestAnimationFrame(anim); return;
            }
            api.sonido('toque'); L.dibujar();
            if (n.o === 0 && n.x === meta[0] && n.y === meta[1]) {
                listo = true;
                const anim = () => { cayendo += .12; L.dibujar(); if (cayendo < 2.2) requestAnimationFrame(anim); else api.gano({estrellas: movs <= minimo && !caidas ? 3 : movs <= minimo * 1.6 ? 2 : 1, detalle: `${movs} movimientos (mínimo ${minimo})`}); };
                requestAnimationFrame(anim);
            }
        }
        // En la vista isométrica las flechas siguen la pantalla: → baja a la derecha (+x), ↓ baja a la izquierda (+y)
        Logica.teclasYDedo(L, intentar, () => L.cv.isConnected);
        Logica.cruceta(zona, intentar);
        return {};
    },
});
