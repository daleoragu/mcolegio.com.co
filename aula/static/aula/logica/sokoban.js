/* Empuja cajas (tipo Sokoban): lleve todas las cajas a las marcas. Las cajas solo se empujan (no se jalan)
 * y de a una. Flechas del teclado, deslizar el dedo o los botones de la pantalla. Deshacer vuelve un paso. */
(function () {
    'use strict';
    const DIR = {arriba: [0, -1], abajo: [0, 1], izquierda: [-1, 0], derecha: [1, 0]};

    Logica.registrar('sokoban', {
        nombre: 'Empuja cajas',
        instrucciones: 'Lleve todas las cajas a las marcas. Las cajas solo se pueden empujar, de a una, y no se pueden jalar: piense antes de empujar contra una pared. Use las flechas, deslice el dedo o los botones. Deshacer vuelve un paso.',
        total: d => d.length,
        titulo: (d, i) => `Bodega ${i + 1} · se puede con ${d[i][0]} empujones`,
        iniciar(zona, datos, i, api) {
            const [minimo, filas] = datos[i], H = filas.length, W = filas[0].length;
            const piso = new Set(), metas = new Set(); let cajas = new Set(), yo = null;
            filas.forEach((f, y) => [...f].forEach((ch, x) => {
                const k = x + ',' + y;
                if (ch !== '#') piso.add(k);
                if (ch === '.' || ch === '*' || ch === '+') metas.add(k);
                if (ch === '$' || ch === '*') cajas.add(k);
                if (ch === '@' || ch === '+') yo = [x, y];
            }));
            const C = Math.min(56, Math.floor(520 / W), Math.floor(420 / H)), L = api.lienzo(W * C + 20, H * C + 20), ctx = L.ctx;
            let empujes = 0, pasos = 0, mira = 'abajo', listo = false;
            const historia = [];
            const esPared = (x, y) => !piso.has(x + ',' + y) && [[0, 1], [0, -1], [1, 0], [-1, 0], [1, 1], [-1, -1], [1, -1], [-1, 1]].some(([a, b]) => piso.has((x + a) + ',' + (y + b)));
            L.dibujar = function () {
                L.limpiar('#2b2118');
                for (let y = 0; y < H; y++) for (let x = 0; x < W; x++) {
                    const X = 10 + x * C, Y = 10 + y * C, k = x + ',' + y;
                    if (piso.has(k)) { ctx.fillStyle = (x + y) % 2 ? '#e9d8a6' : '#e2cf98'; ctx.fillRect(X, Y, C, C); }
                    else if (esPared(x, y)) {
                        ctx.fillStyle = '#8f3b1b'; ctx.fillRect(X, Y, C, C);
                        ctx.strokeStyle = '#5e2611'; ctx.lineWidth = 2;
                        for (let f = 0; f < 3; f++) { ctx.beginPath(); ctx.moveTo(X, Y + f * C / 3); ctx.lineTo(X + C, Y + f * C / 3); ctx.stroke(); const o = f % 2 ? C / 4 : C * 3 / 4; ctx.beginPath(); ctx.moveTo(X + o, Y + f * C / 3); ctx.lineTo(X + o, Y + (f + 1) * C / 3); ctx.stroke(); }
                    }
                    if (metas.has(k)) { ctx.strokeStyle = '#e03131'; ctx.lineWidth = 3; ctx.beginPath(); ctx.arc(X + C / 2, Y + C / 2, C * .22, 0, Math.PI * 2); ctx.stroke(); ctx.beginPath(); ctx.moveTo(X + C * .3, Y + C * .3); ctx.lineTo(X + C * .7, Y + C * .7); ctx.moveTo(X + C * .7, Y + C * .3); ctx.lineTo(X + C * .3, Y + C * .7); ctx.stroke(); }
                    if (cajas.has(k)) {
                        const enMeta = metas.has(k), m = C * .08;
                        ctx.fillStyle = enMeta ? '#2f9e44' : '#c68b4e'; ctx.fillRect(X + m, Y + m, C - 2 * m, C - 2 * m);
                        ctx.strokeStyle = enMeta ? '#1b5e20' : '#7a4a24'; ctx.lineWidth = 3; ctx.strokeRect(X + m, Y + m, C - 2 * m, C - 2 * m);
                        ctx.beginPath(); ctx.moveTo(X + m, Y + m); ctx.lineTo(X + C - m, Y + C - m); ctx.moveTo(X + C - m, Y + m); ctx.lineTo(X + m, Y + C - m); ctx.stroke();
                    }
                }
                // el trabajador de la bodega
                const X = 10 + yo[0] * C + C / 2, Y = 10 + yo[1] * C + C / 2;
                ctx.fillStyle = '#1971c2'; ctx.beginPath(); ctx.ellipse(X, Y + C * .14, C * .24, C * .2, 0, 0, Math.PI * 2); ctx.fill();
                ctx.fillStyle = '#f1c27d'; ctx.beginPath(); ctx.arc(X, Y - C * .12, C * .18, 0, Math.PI * 2); ctx.fill();
                ctx.fillStyle = '#fab005'; ctx.beginPath(); ctx.arc(X, Y - C * .17, C * .19, Math.PI, 0); ctx.fill();
                const [mx, my] = DIR[mira]; ctx.fillStyle = '#111';
                if (mira !== 'arriba') { ctx.beginPath(); ctx.arc(X - C * .06 + mx * C * .06, Y - C * .1 + my * C * .03, C * .03, 0, Math.PI * 2); ctx.arc(X + C * .06 + mx * C * .06, Y - C * .1 + my * C * .03, C * .03, 0, Math.PI * 2); ctx.fill(); }
                L.texto(`Pasos: ${pasos} · Empujones: ${empujes} · Cajas en su sitio: ${[...cajas].filter(c => metas.has(c)).length}/${metas.size}`, 12, H * C + 16, {tam: 12, color: '#e9d8a6'});
            };
            function mover(d) {
                if (listo) return;
                const [dx, dy] = DIR[d], nx = yo[0] + dx, ny = yo[1] + dy, k = nx + ',' + ny;
                mira = d;
                if (!piso.has(k)) { L.dibujar(); return; }
                if (cajas.has(k)) {
                    const k2 = (nx + dx) + ',' + (ny + dy);
                    if (!piso.has(k2) || cajas.has(k2)) { L.dibujar(); return; }
                    historia.push({yo: yo.slice(), cajas: new Set(cajas), empujes, pasos});
                    cajas.delete(k); cajas.add(k2); empujes += 1; api.sonido('toque');
                } else historia.push({yo: yo.slice(), cajas: new Set(cajas), empujes, pasos});
                yo = [nx, ny]; pasos += 1; api.movimiento(); L.dibujar();
                if ([...cajas].every(c => metas.has(c))) { listo = true; api.gano({estrellas: empujes <= minimo ? 3 : empujes <= minimo * 1.6 ? 2 : 1, detalle: `${empujes} empujones (mínimo ${minimo})`}); }
            }
            Logica.teclasYDedo(L, mover, () => L.cv.isConnected);
            Logica.cruceta(zona, mover);
            return { deshacer() { const u = historia.pop(); if (!u || listo) return; yo = u.yo; cajas = u.cajas; empujes = u.empujes; pasos = u.pasos; api.movimiento(-1); L.dibujar(); } };
        },
    });
})();
