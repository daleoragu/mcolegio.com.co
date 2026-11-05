/* Tangram: con las 7 piezas arme la figura de sombra. Arrastre las piezas; un toque las gira 45°;
 * el paralelogramo se voltea con doble toque (o el botón). Las piezas se acomodan solas cuando quedan cerca.
 * Gana cuando la sombra queda cubierta (se revisa por puntos, así vale cualquier solución). */
(function () {
    'use strict';
    const BASE = {   // el cuadrado clásico de 4×4
        G1: [[0, 0], [4, 0], [2, 2]], G2: [[0, 0], [2, 2], [0, 4]], M: [[4, 2], [4, 4], [2, 4]],
        P1: [[3, 1], [4, 0], [4, 2]], P2: [[2, 2], [3, 3], [1, 3]], C: [[2, 2], [3, 1], [4, 2], [3, 3]], R: [[0, 4], [1, 3], [3, 3], [2, 4]],
    };
    const COLOR = {G1: '#e03131', G2: '#1971c2', M: '#f59f00', P1: '#2f9e44', P2: '#ae3ec9', C: '#fab005', R: '#0ca678'};
    const centro = pol => [pol.reduce((s, p) => s + p[0], 0) / pol.length, pol.reduce((s, p) => s + p[1], 0) / pol.length];
    function dentro(x, y, pol) {
        let r = false;
        for (let i = 0, j = pol.length - 1; i < pol.length; j = i++) {
            const [xi, yi] = pol[i], [xj, yj] = pol[j];
            if ((yi > y) !== (yj > y) && x < (xj - xi) * (y - yi) / (yj - yi) + xi) r = !r;
        }
        return r;
    }

    Logica.registrar('tangram', {
        nombre: 'Tangram',
        instrucciones: 'Con las 7 piezas cubra toda la sombra. Arrastre las piezas; un toque las gira; el paralelogramo verde se voltea con doble toque. Las piezas se acomodan solas cuando quedan cerca de su sitio.',
        total: d => d.length,
        titulo: (d, i) => `Figura ${i + 1}: ${d[i].nombre}`,
        iniciar(zona, datos, i, api) {
            const fig = datos[i], W = 720, H = 440, L = api.lienzo(W, H), ctx = L.ctx;
            // La sombra a la izquierda, escalada para caber
            const todos = Object.values(fig.piezas).flat();
            const fw = Math.max(...todos.map(p => p[0])), fh = Math.max(...todos.map(p => p[1]));
            const U = Math.min(38, 380 / fw, 380 / fh), OX = 30 + (400 - fw * U) / 2, OY = 30 + (380 - fh * U) / 2;
            // Las piezas: forma base centrada en su centroide, posición en unidades de la figura
            const piezas = Object.keys(BASE).map((k, n) => {
                const c = centro(BASE[k]);
                return {k, forma: BASE[k].map(([x, y]) => [x - c[0], y - c[1]]), ang: (n * 2) % 8, esp: false,
                        x: 0, y: 0, color: COLOR[k]};
            });
            const BANDEJA = [[470, 90], [600, 90], [470, 210], [600, 210], [470, 320], [560, 320], [650, 320]];
            piezas.forEach((p, n) => { p.x = (BANDEJA[n][0] - OX) / U; p.y = (BANDEJA[n][1] - OY) / U; });
            let arrastre = null, ultima = null, ultimoToque = {k: '', t: 0}, ayudas = 0, movs = 0;
            function vertices(p) {
                const a = p.ang * Math.PI / 4, cs = Math.cos(a), sn = Math.sin(a);
                return p.forma.map(([x, y]) => { if (p.esp) x = -x; return [p.x + x * cs - y * sn, p.y + x * sn + y * cs]; });
            }
            // Acomodar: si un vértice queda cerca de un punto de la cuadrícula de la figura, se pega
            function acomodar(p) {
                let mejor = null;
                vertices(p).forEach(([x, y]) => {
                    const dx = Math.round(x) - x, dy = Math.round(y) - y, d = Math.hypot(dx, dy);
                    if (!mejor || d < mejor.d) mejor = {dx, dy, d};
                });
                if (mejor && mejor.d < .35) { p.x += mejor.dx; p.y += mejor.dy; }
            }
            // ¿Está cubierta la sombra? Puntos de muestra cada 1/4 de unidad
            function revisar() {
                let falta = 0, total = 0, fuera = 0;
                const polys = piezas.map(vertices), sombra = Object.values(fig.piezas);
                for (let y = .125; y < fh; y += .25) for (let x = .125; x < fw; x += .25) {
                    const enSombra = sombra.some(s => dentro(x, y, s)), cubierto = polys.some(s => dentro(x, y, s));
                    if (enSombra) { total += 1; if (!cubierto) falta += 1; } else if (cubierto) fuera += 1;
                }
                // fuera de la caja de la figura también cuenta
                const afuera = polys.flat().some(([x, y]) => x < -.2 || y < -.2 || x > fw + .2 || y > fh + .2);
                if (falta <= total * .015 && fuera <= total * .015 && !afuera) {
                    api.gano({estrellas: ayudas === 0 ? 3 : ayudas === 1 ? 2 : 1, detalle: ayudas ? `${ayudas} ayuda(s)` : 'sin ayudas'});
                }
            }
            let pista = null;
            L.dibujar = function () {
                L.limpiar('#fdf6e3');
                ctx.fillStyle = '#f1e3c6'; Logica.redondo(ctx, 14, 14, 432, 412, 18); ctx.fill();
                ctx.fillStyle = '#343a40';
                Object.values(fig.piezas).forEach(pol => {
                    ctx.beginPath(); pol.forEach(([x, y], j) => (j ? ctx.lineTo : ctx.moveTo).call(ctx, OX + x * U, OY + y * U)); ctx.closePath(); ctx.fill();
                    ctx.strokeStyle = '#343a40'; ctx.lineWidth = 1.5; ctx.stroke();
                });
                if (pista) {
                    ctx.strokeStyle = COLOR[pista]; ctx.lineWidth = 4; ctx.setLineDash([6, 4]);
                    ctx.beginPath(); fig.piezas[pista].forEach(([x, y], j) => (j ? ctx.lineTo : ctx.moveTo).call(ctx, OX + x * U, OY + y * U)); ctx.closePath(); ctx.stroke(); ctx.setLineDash([]);
                }
                L.texto(fig.nombre, 30, 412, {tam: 15, negrita: true, color: '#6b4423'});
                const orden = piezas.filter(p => !arrastre || arrastre.p !== p); if (arrastre) orden.push(arrastre.p);
                orden.forEach(p => {
                    ctx.save();
                    if (arrastre && arrastre.p === p) { ctx.shadowColor = 'rgba(0,0,0,.35)'; ctx.shadowBlur = 10; ctx.shadowOffsetY = 4; }
                    ctx.fillStyle = p.color; ctx.beginPath();
                    vertices(p).forEach(([x, y], j) => (j ? ctx.lineTo : ctx.moveTo).call(ctx, OX + x * U, OY + y * U)); ctx.closePath(); ctx.fill();
                    ctx.restore(); ctx.strokeStyle = 'rgba(255,255,255,.8)'; ctx.lineWidth = 1.5; ctx.stroke();
                });
            };
            L.cv.addEventListener('pointerdown', ev => {
                const {x, y} = L.punto(ev), ux = (x - OX) / U, uy = (y - OY) / U;
                const p = [...piezas].reverse().find(p => dentro(ux, uy, vertices(p)));
                if (!p) return;
                try { L.cv.setPointerCapture(ev.pointerId); } catch (e) { /* */ }
                piezas.splice(piezas.indexOf(p), 1); piezas.push(p);     // queda encima
                arrastre = {p, ox: ux - p.x, oy: uy - p.y, x0: x, y0: y, movio: false}; ultima = p; pista = null;
            });
            L.cv.addEventListener('pointermove', ev => {
                if (!arrastre) return;
                const {x, y} = L.punto(ev);
                if (Math.hypot(x - arrastre.x0, y - arrastre.y0) > 6) arrastre.movio = true;
                arrastre.p.x = (x - OX) / U - arrastre.ox; arrastre.p.y = (y - OY) / U - arrastre.oy; L.dibujar();
            });
            const soltar = () => {
                if (!arrastre) return;
                const {p, movio} = arrastre; arrastre = null;
                if (!movio) {
                    const ahora = performance.now();
                    if (p.k === 'R' && ultimoToque.k === 'R' && ahora - ultimoToque.t < 320) { p.ang = (p.ang + 7) % 8; p.esp = !p.esp; }
                    else p.ang = (p.ang + 1) % 8;
                    ultimoToque = {k: p.k, t: ahora};
                }
                acomodar(p); movs += 1; api.movimiento(); L.dibujar(); revisar();
            };
            L.cv.addEventListener('pointerup', soltar); L.cv.addEventListener('pointercancel', soltar);
            return {
                girar() { if (ultima) { ultima.ang = (ultima.ang + 1) % 8; acomodar(ultima); L.dibujar(); revisar(); } },
                voltear() { if (ultima && ultima.k === 'R') { ultima.esp = !ultima.esp; acomodar(ultima); L.dibujar(); revisar(); } },
                // Ayuda: muestra dónde va una pieza que todavía no está en su sitio
                ayuda() {
                    // los dos triángulos grandes (y los dos pequeños) son iguales: vale cualquiera de los dos
                    const esta = (q, s) => s.every(([x, y]) => vertices(q).some(([a, b]) => Math.hypot(a - x, b - y) < .1));
                    const mal = Object.keys(fig.piezas).find(k => !piezas.some(q => q.k[0] === k[0] && esta(q, fig.piezas[k])));
                    if (mal) { pista = mal; ayudas += 1; api.aviso('La pieza marcada con la línea punteada va ahí.'); L.dibujar(); }
                },
            };
        },
    });
})();
