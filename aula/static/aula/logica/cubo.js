/* Cubo del binomio y del trinomio (Montessori): arme el cubo (a+b)³ o (a+b+c)³ con sus piezas.
 * Izquierda: el cubo en 3D. Derecha: la capa que se está armando vista desde arriba.
 * Escoja una pieza, gírela y toque en la capa dónde va (su esquina de arriba a la izquierda). */
(function () {
    'use strict';
    const NIVELES = [
        {lados: [2, 1]}, {lados: [3, 1]}, {lados: [3, 2]}, {lados: [4, 2]}, {lados: [3, 2, 1]}, {lados: [4, 2, 1]},
    ];
    const LETRA = ['a', 'b', 'c'], COLOR = ['#e03131', '#1971c2', '#fab005'], NEGRO = '#343a40';
    const SUP = {2: '²', 3: '³'};
    function permutaciones(d) { const r = new Set(); [[0, 1, 2], [0, 2, 1], [1, 0, 2], [1, 2, 0], [2, 0, 1], [2, 1, 0]].forEach(p => r.add(p.map(k => d[k]).join(','))); return [...r].map(s => s.split(',').map(Number)); }
    function nombre(dims, lados) {     // [3,3,2] con a=3, b=2 → a²b
        const cuenta = {}; dims.forEach(v => { const k = lados.indexOf(v); cuenta[k] = (cuenta[k] || 0) + 1; });
        return Object.keys(cuenta).sort().map(k => LETRA[k] + (SUP[cuenta[k]] || '')).join('');
    }
    Logica.registrar('cubo', {
        nombre: 'Cubo del binomio y del trinomio',
        instrucciones: 'Arme el cubo con todas sus piezas. Escoja una pieza de la caja, gírela si hace falta y toque en la capa de la derecha dónde va su esquina de arriba a la izquierda. Con ▲▼ cambia de capa. Toque una pieza puesta para quitarla. Las caras de a² son rojas, las de b² azules, las de c² amarillas y las mezcladas negras.',
        total: () => NIVELES.length,
        titulo: (d, i) => NIVELES[i].lados.length === 2 ? `Binomio (a + b)³ con a = ${NIVELES[i].lados[0]}, b = ${NIVELES[i].lados[1]}` : `Trinomio (a + b + c)³ con a = ${NIVELES[i].lados[0]}, b = ${NIVELES[i].lados[1]}, c = ${NIVELES[i].lados[2]}`,
        iniciar(zona, datos, i, api) {
            const lados = NIVELES[i].lados, n = lados.reduce((s, v) => s + v, 0), m = lados.length;
            // Las piezas: una por cada combinación de segmentos (x, y, z); se agrupan por forma
            const huecos = [], inicios = [0]; lados.forEach((v, k) => inicios.push(inicios[k] + v));
            for (let a = 0; a < m; a++) for (let b = 0; b < m; b++) for (let c = 0; c < m; c++)
                huecos.push({pos: [inicios[a], inicios[b], inicios[c]], dims: [lados[a], lados[b], lados[c]]});
            const grupos = {};
            huecos.forEach(h => { const k = h.dims.slice().sort((p, q) => q - p).join(','); (grupos[k] = grupos[k] || {dims: h.dims.slice().sort((p, q) => q - p), total: 0, puestas: 0}).total += 1; });
            const claves = Object.keys(grupos).sort((p, q) => grupos[q].dims.reduce((s, v) => s * v, 1) - grupos[p].dims.reduce((s, v) => s * v, 1));
            let sel = claves[0], orient = 0, capa = 0, piezas = [], hover = null, ayudas = 0;
            const ocupa = new Map();     // 'x,y,z' → índice de la pieza
            const W = 820, H = 470, L = api.lienzo(W, H), ctx = L.ctx;
            const U = Math.min(44, 230 / n), OX = 220, OY = 90 + n * U * .5;
            const iso = (x, y, z) => [OX + (x - y) * U * .87, OY + (x + y) * U * .5 - z * U];
            const G = Math.min(40, 250 / n), GX = 520, GY = 110;
            const dimsActuales = () => permutaciones(grupos[sel].dims)[orient % permutaciones(grupos[sel].dims).length];
            function colorCara(d1, d2) { if (d1 !== d2) return NEGRO; const k = lados.indexOf(d1); return lados.filter(v => v === d1).length === 1 ? COLOR[k] : NEGRO; }
            function cabe(pos, dims) {
                for (let x = 0; x < dims[0]; x++) for (let y = 0; y < dims[1]; y++) for (let z = 0; z < dims[2]; z++) {
                    const X = pos[0] + x, Y = pos[1] + y, Z = pos[2] + z;
                    if (X >= n || Y >= n || Z >= n || ocupa.has(X + ',' + Y + ',' + Z)) return false;
                }
                return true;
            }
            function poner(pos, dims, clave) {
                const idx = piezas.length; piezas.push({pos, dims, clave});
                for (let x = 0; x < dims[0]; x++) for (let y = 0; y < dims[1]; y++) for (let z = 0; z < dims[2]; z++) ocupa.set((pos[0] + x) + ',' + (pos[1] + y) + ',' + (pos[2] + z), idx);
                grupos[clave].puestas += 1;
            }
            function quitar(idx) {
                const p = piezas[idx]; grupos[p.clave].puestas -= 1; piezas.splice(idx, 1);
                ocupa.clear(); const resto = piezas; piezas = []; Object.values(grupos).forEach(g => { g.puestas = 0; });
                resto.forEach(q => poner(q.pos, q.dims, q.clave));
            }
            L.dibujar = function () {
                L.limpiar('#f8f1e5');
                // la caja (piso y aristas)
                ctx.strokeStyle = '#c8a26b'; ctx.lineWidth = 1;
                for (let k = 0; k <= n; k++) { let a = iso(k, 0, 0), b = iso(k, n, 0); ctx.beginPath(); ctx.moveTo(...a); ctx.lineTo(...b); ctx.stroke(); a = iso(0, k, 0); b = iso(n, k, 0); ctx.beginPath(); ctx.moveTo(...a); ctx.lineTo(...b); ctx.stroke(); }
                // cubitos de atrás hacia adelante
                const celdas = [...ocupa.entries()].map(([k, idx]) => [k.split(',').map(Number), idx]).sort((p, q) => (p[0][0] + p[0][1] + p[0][2]) - (q[0][0] + q[0][1] + q[0][2]) || p[0][2] - q[0][2]);
                const fantasma = hover && cabe([hover[0], hover[1], capa], dimsActuales()) ? {pos: [hover[0], hover[1], capa], dims: dimsActuales()} : null;
                const lista = celdas.map(([c, idx]) => [c, piezas[idx], false]);
                if (fantasma) for (let x = 0; x < fantasma.dims[0]; x++) for (let y = 0; y < fantasma.dims[1]; y++) for (let z = 0; z < fantasma.dims[2]; z++) lista.push([[fantasma.pos[0] + x, fantasma.pos[1] + y, fantasma.pos[2] + z], fantasma, true]);
                lista.sort((p, q) => (p[0][0] + p[0][1] + p[0][2]) - (q[0][0] + q[0][1] + q[0][2]) || p[0][2] - q[0][2]);
                lista.forEach(([[x, y, z], p, esF]) => {
                    const mismo = (a, b, c) => { const X = x + a, Y = y + b, Z = z + c; return X >= p.pos[0] && X < p.pos[0] + p.dims[0] && Y >= p.pos[1] && Y < p.pos[1] + p.dims[1] && Z >= p.pos[2] && Z < p.pos[2] + p.dims[2]; };
                    ctx.globalAlpha = esF ? .45 : 1;
                    const cara = (pts, color) => { ctx.fillStyle = color; ctx.beginPath(); pts.forEach((q, k) => (k ? ctx.lineTo : ctx.moveTo).call(ctx, ...q)); ctx.closePath(); ctx.fill(); ctx.strokeStyle = 'rgba(255,255,255,.18)'; ctx.stroke(); };
                    if (!mismo(0, 1, 0)) cara([iso(x, y + 1, z), iso(x + 1, y + 1, z), iso(x + 1, y + 1, z + 1), iso(x, y + 1, z + 1)], sombra(colorCara(p.dims[0], p.dims[2]), .8));
                    if (!mismo(1, 0, 0)) cara([iso(x + 1, y, z), iso(x + 1, y + 1, z), iso(x + 1, y + 1, z + 1), iso(x + 1, y, z + 1)], sombra(colorCara(p.dims[1], p.dims[2]), .65));
                    if (!mismo(0, 0, 1)) cara([iso(x, y, z + 1), iso(x + 1, y, z + 1), iso(x + 1, y + 1, z + 1), iso(x, y + 1, z + 1)], colorCara(p.dims[0], p.dims[1]));
                    ctx.globalAlpha = 1;
                });
                // la capa vista desde arriba
                L.texto(`Capa ${capa + 1} de ${n} (vista desde arriba)`, GX, GY - 14, {tam: 13, negrita: true, color: '#495057'});
                for (let y = 0; y < n; y++) for (let x = 0; x < n; x++) {
                    const idx = ocupa.get(x + ',' + y + ',' + capa), p = idx !== undefined ? piezas[idx] : null;
                    ctx.fillStyle = p ? colorCara(p.dims[0], p.dims[1]) : '#fff'; ctx.fillRect(GX + x * G, GY + y * G, G - 2, G - 2);
                    if (fantasma && x >= fantasma.pos[0] && x < fantasma.pos[0] + fantasma.dims[0] && y >= fantasma.pos[1] && y < fantasma.pos[1] + fantasma.dims[1]) { ctx.fillStyle = 'rgba(250,176,5,.45)'; ctx.fillRect(GX + x * G, GY + y * G, G - 2, G - 2); }
                }
                ctx.strokeStyle = '#495057'; ctx.lineWidth = 2; ctx.strokeRect(GX - 2, GY - 2, n * G + 2, n * G + 2);
                // la fórmula, con lo que ya está puesto
                const formula = claves.map(k => `${grupos[k].total > 1 ? grupos[k].total : ''}${nombre(grupos[k].dims, lados)}`).join(' + ');
                L.texto((m === 2 ? '(a + b)³ = ' : '(a + b + c)³ = ') + formula, 20, H - 40, {tam: m === 2 ? 17 : 13, negrita: true, color: '#1f3a68'});
                L.texto(`Piezas puestas: ${piezas.length} de ${huecos.length}`, 20, H - 16, {tam: 13, color: '#495057'});
            };
            function sombra(hex, f) { const v = parseInt(hex.slice(1), 16); return `rgb(${(v >> 16) * f | 0},${(v >> 8 & 255) * f | 0},${(v & 255) * f | 0})`; }
            // La caja de piezas y los controles (botones de la página)
            const panel = document.createElement('div');
            panel.style.cssText = 'display:flex;flex-wrap:wrap;gap:6px;justify-content:center;margin-top:8px;max-width:820px';
            zona.appendChild(panel);
            function pintarPanel() {
                panel.innerHTML = claves.map(k => { const g = grupos[k], quedan = g.total - g.puestas; return `<button type="button" data-k="${k}" class="btn btn-sm ${k === sel ? 'btn-primary' : 'btn-outline-primary'}" ${quedan ? '' : 'disabled'}>${nombre(g.dims, lados)} <span class="badge bg-light text-dark">${quedan}</span></button>`; }).join('') +
                    `<button type="button" class="btn btn-sm btn-warning" data-a="girar">↻ Girar pieza</button><button type="button" class="btn btn-sm btn-secondary" data-a="sube">▲ Capa</button><button type="button" class="btn btn-sm btn-secondary" data-a="baja">▼ Capa</button>`;
                panel.querySelectorAll('[data-k]').forEach(b => b.addEventListener('click', () => { sel = b.dataset.k; orient = 0; pintarPanel(); L.dibujar(); }));
                panel.querySelector('[data-a="girar"]').addEventListener('click', () => { orient += 1; L.dibujar(); });
                panel.querySelector('[data-a="sube"]').addEventListener('click', () => { capa = Math.min(n - 1, capa + 1); L.dibujar(); });
                panel.querySelector('[data-a="baja"]').addEventListener('click', () => { capa = Math.max(0, capa - 1); L.dibujar(); });
            }
            function celdaCapa(ev) { const {x, y} = L.punto(ev), cx = Math.floor((x - GX) / G), cy = Math.floor((y - GY) / G); return cx >= 0 && cy >= 0 && cx < n && cy < n ? [cx, cy] : null; }
            L.cv.addEventListener('pointermove', ev => { hover = celdaCapa(ev); L.dibujar(); });
            L.cv.addEventListener('pointerdown', ev => {
                const c = celdaCapa(ev); if (!c) return;
                const idx = ocupa.get(c[0] + ',' + c[1] + ',' + capa);
                if (idx !== undefined) { quitar(idx); api.sonido('toque'); pintarPanel(); L.dibujar(); return; }
                const g = grupos[sel];
                if (g.puestas >= g.total) { api.aviso('Ya puso todas las piezas de ese tipo: escoja otra.'); return; }
                const dims = dimsActuales();
                if (!cabe([c[0], c[1], capa], dims)) { api.aviso('No cabe ahí: se sale del cubo o choca con otra pieza. Pruebe girarla.'); api.sonido('mal'); return; }
                poner([c[0], c[1], capa], dims, sel); api.movimiento(); api.sonido('toque');
                if (g.puestas >= g.total) { const otra = claves.find(k => grupos[k].puestas < grupos[k].total); if (otra) { sel = otra; orient = 0; } }
                pintarPanel(); L.dibujar(); revisar();
            });
            function revisar() { if (piezas.length === huecos.length) api.gano({estrellas: ayudas === 0 ? 3 : ayudas <= 2 ? 2 : 1, detalle: (m === 2 ? '(a + b)³' : '(a + b + c)³') + ' armado'}); }
            pintarPanel();
            return {
                // Ayuda: pone una pieza en su lugar del cubo clásico (si ese lugar está libre)
                ayuda() {
                    const h = huecos.find(h => cabe(h.pos, h.dims) && grupos[h.dims.slice().sort((p, q) => q - p).join(',')].puestas < grupos[h.dims.slice().sort((p, q) => q - p).join(',')].total);
                    if (!h) { api.aviso('Quite alguna pieza: así como está no se puede seguir el cubo clásico.'); return; }
                    poner(h.pos, h.dims, h.dims.slice().sort((p, q) => q - p).join(',')); ayudas += 1; capa = h.pos[2];
                    api.aviso(`Se puso una pieza ${nombre(h.dims, lados)} en la capa ${capa + 1}.`); pintarPanel(); L.dibujar(); revisar();
                },
            };
        },
    });
})();
