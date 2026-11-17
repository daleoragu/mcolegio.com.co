/* Familia Sudoku: un solo tablero para todas las variantes (clásico, mini, figuras, en X, ventanas, irregular, par/impar,
 * consecutivo, mayor que, puntos, sumas, termómetro, flechas, sándwich, sin caballo, sin rey y asesino).
 * Toque una casilla y luego un número (o use el teclado: 1-9, flechas, Supr; N para notas). Todos los niveles se
 * generaron con un solucionador y tienen UNA sola solución: se resuelven pensando, sin adivinar. */
(function () {
    'use strict';
    const INSTR = {
        sudoku: 'Llene el tablero para que cada fila, cada columna y cada caja de 3×3 tenga los números del 1 al 9 sin repetir. Toque una casilla y luego el número. Con el lápiz ✏️ anota posibilidades.',
        sudoku_mini: 'Sudoku pequeño: cada fila, columna y caja tiene los números sin repetir (del 1 al 4 en 4×4 y del 1 al 6 en 6×6). Ideal para empezar.',
        sudoku_figuras: 'Como el sudoku, pero con figuras: cada fila, columna y caja tiene todas las figuras sin repetir. Toque una casilla y luego la figura.',
        sudoku_x: 'Sudoku en X: además de filas, columnas y cajas, las dos diagonales marcadas tampoco repiten números.',
        sudoku_hiper: 'Sudoku de ventanas: además de lo normal, las cuatro ventanas sombreadas de 3×3 tampoco repiten números.',
        sudoku_irregular: 'Sudoku irregular: las cajas no son cuadradas; cada región de color tiene todos los números sin repetir, igual que filas y columnas.',
        sudoku_parimpar: 'Sudoku par e impar: en las casillas con círculo va un número PAR y en las del cuadrado un número IMPAR.',
        sudoku_consecutivo: 'Sudoku consecutivo: una barra blanca entre dos casillas quiere decir que sus números son seguidos (como 4 y 5). Donde NO hay barra, los números NO son seguidos.',
        sudoku_mayor: 'Sudoku mayor que: los signos < y > entre casillas de una misma caja dicen qué número es mayor. La punta señala al menor.',
        sudoku_kropki: 'Sudoku de puntos: un punto blanco une números seguidos (3 y 4); un punto negro, un número y su doble (3 y 6). Donde no hay punto no pasa ninguna de las dos cosas.',
        sudoku_xv: 'Sudoku de sumas: el número en la línea entre dos casillas es la suma de las dos. Donde no hay número, las dos vecinas no dan esa suma (ni 5 ni 10 en 9×9; ni 5 ni 7 en 6×6).',
        sudoku_termo: 'Sudoku termómetro: en cada termómetro los números suben desde el bulbo (la bolita) hacia la punta.',
        sudoku_flechas: 'Sudoku de flechas: el número del círculo es la suma de los números que recorre su flecha (en la flecha sí se pueden repetir números).',
        sudoku_sandwich: 'Sudoku sándwich: el número de afuera es la suma de los números que quedan ENTRE el 1 y el número más alto de esa fila o columna.',
        sudoku_caballo: 'Sudoku sin caballo: dos casillas a un salto de caballo de ajedrez (en L) no pueden tener el mismo número.',
        sudoku_rey: 'Sudoku sin rey: dos casillas que se tocan en diagonal (a un paso de rey) no pueden tener el mismo número.',
        sudoku_killer: 'Sudoku asesino: cada jaula punteada suma el número de su esquina y dentro de una jaula no se repiten números.',
    };
    const NOMBRES = {sudoku: 'Sudoku', sudoku_mini: 'Sudoku mini', sudoku_figuras: 'Sudoku de figuras', sudoku_x: 'Sudoku en X', sudoku_hiper: 'Sudoku de ventanas',
        sudoku_irregular: 'Sudoku irregular', sudoku_parimpar: 'Sudoku par e impar', sudoku_consecutivo: 'Sudoku consecutivo', sudoku_mayor: 'Sudoku mayor que',
        sudoku_kropki: 'Sudoku de puntos', sudoku_xv: 'Sudoku de sumas', sudoku_termo: 'Sudoku termómetro', sudoku_flechas: 'Sudoku de flechas',
        sudoku_sandwich: 'Sudoku sándwich', sudoku_caballo: 'Sudoku sin caballo', sudoku_rey: 'Sudoku sin rey', sudoku_killer: 'Sudoku asesino'};
    const CAJAS = {4: [2, 2], 6: [2, 3], 9: [3, 3]};
    const FIGURAS = [['●', '#e03131'], ['▲', '#1971c2'], ['■', '#2f9e44'], ['★', '#f08c00'], ['◆', '#7048e8'], ['♥', '#d6336c']];
    const TINTES = ['#fff5f5', '#f3f0ff', '#e7f5ff', '#ebfbee', '#fff9db', '#fff4e6', '#f8f0fc', '#e6fcf5', '#f1f3f5'];

    function crear(id) {
        return {
            nombre: NOMBRES[id],
            instrucciones: INSTR[id],
            total: d => d.length,
            titulo: (d, i) => `${NOMBRES[id]} ${i + 1} · ${d[i].n}×${d[i].n}`,
            iniciar(zona, datos, i, api) {
                const R = datos[i], n = R.n, N = n * n;
                const sol = R.sol.split('').map(Number), dados = R.dados.split('').map(Number);
                const reg = R.regiones ? R.regiones.split('').map(Number)
                    : Array.from({length: N}, (_, k) => { const f = Math.floor(k / n), c = k % n; return Math.floor(f / CAJAS[n][0]) * (n / CAJAS[n][1]) + Math.floor(c / CAJAS[n][1]); });
                // Grupos que no repiten y vecinos prohibidos (para marcar los choques en rojo)
                const grupos = [];
                for (let f = 0; f < n; f++) grupos.push([...Array(n)].map((_, c) => f * n + c));
                for (let c = 0; c < n; c++) grupos.push([...Array(n)].map((_, f) => f * n + c));
                for (let r = 0; r < n; r++) grupos.push([...Array(N).keys()].filter(k => reg[k] === r));
                if (id === 'sudoku_x') { grupos.push([...Array(n)].map((_, k) => k * n + k)); grupos.push([...Array(n)].map((_, k) => k * n + n - 1 - k)); }
                const ventanas = id === 'sudoku_hiper' ? [[1, 1], [1, 5], [5, 1], [5, 5]] : [];
                ventanas.forEach(([f0, c0]) => { const g = []; for (let a = 0; a < 3; a++) for (let b = 0; b < 3; b++) g.push((f0 + a) * n + c0 + b); grupos.push(g); });
                (R.jaulas || []).forEach(j => grupos.push(j.c));
                const saltos = id === 'sudoku_caballo' ? [[1, 2], [2, 1], [-1, 2], [-2, 1], [1, -2], [2, -1], [-1, -2], [-2, -1]] : id === 'sudoku_rey' ? [[1, 1], [1, -1], [-1, 1], [-1, -1]] : [];
                const vecinos = [...Array(N)].map(() => new Set());
                grupos.forEach(g => g.forEach(a => g.forEach(b => { if (a !== b) vecinos[a].add(b); })));
                for (let k = 0; k < N; k++) { const f = Math.floor(k / n), c = k % n; saltos.forEach(([a, b]) => { if (f + a >= 0 && f + a < n && c + b >= 0 && c + b < n) vecinos[k].add((f + a) * n + c + b); }); }

                // Medidas: margen arriba e izquierda para las sumas del sándwich
                const M = R.sandwich ? 30 : 8, C = Math.floor(Math.min(56, 470 / n)), X0 = M + 2, Y0 = M + 2;
                const W = X0 + n * C + 8, H = Y0 + n * C + 8;
                const L = api.lienzo(W, H), ctx = L.ctx;
                let g = dados.slice(), notas = [...Array(N)].map(() => new Set()), sel = dados.indexOf(0), lapiz = false;
                const historia = [];
                const fig = id === 'sudoku_figuras';

                function xy(k) { return [X0 + (k % n) * C, Y0 + Math.floor(k / n) * C]; }
                function choca(k) { const v = g[k]; return v && [...vecinos[k]].some(j => g[j] === v); }
                function simbolo(v, x, y, tam, color) {
                    if (fig) { const [s, col] = FIGURAS[v - 1]; L.texto(s, x, y, {tam: tam * 1.05, alinear: 'center', base: 'middle', color: col}); }
                    else L.texto(String(v), x, y, {tam, alinear: 'center', base: 'middle', negrita: true, color});
                }
                function borde(k, j) {     // punto medio del borde entre k y su vecina j (derecha o abajo)
                    const [x, y] = xy(k);
                    return j === k + 1 ? [x + C, y + C / 2, 'v'] : [x + C / 2, y + C, 'h'];
                }

                L.dibujar = function () {
                    L.limpiar('#fff');
                    const sf = Math.floor(sel / n), sc = sel % n, sv = g[sel];
                    // fondo de las casillas
                    for (let k = 0; k < N; k++) {
                        const [x, y] = xy(k), f = Math.floor(k / n), c = k % n;
                        let fondo = R.regiones ? TINTES[reg[k] % TINTES.length] : '#fff';
                        if (ventanas.some(([f0, c0]) => f >= f0 && f < f0 + 3 && c >= c0 && c < c0 + 3)) fondo = '#d0ebff';
                        if (id === 'sudoku_x' && (f === c || f + c === n - 1)) fondo = '#f3f0ff';
                        if (sel >= 0 && (f === sf || c === sc || reg[k] === reg[sel])) fondo = '#edf2ff';
                        if (sv && g[k] === sv) fondo = '#c5d8ff';
                        if (k === sel) fondo = '#ffe066';
                        ctx.fillStyle = fondo; ctx.fillRect(x, y, C, C);
                        // par (círculo) o impar (cuadrado)
                        const p = R.paridad && R.paridad[k];
                        if (p) {
                            ctx.fillStyle = '#dee2e6';
                            if (p === 'p') { ctx.beginPath(); ctx.arc(x + C / 2, y + C / 2, C * .38, 0, 7); ctx.fill(); }
                            else ctx.fillRect(x + C * .14, y + C * .14, C * .72, C * .72);
                        }
                    }
                    // termómetros y flechas (debajo de los números)
                    (R.termos || []).forEach(t => {
                        ctx.strokeStyle = '#ced4da'; ctx.lineWidth = C * .26; ctx.lineCap = 'round'; ctx.lineJoin = 'round'; ctx.beginPath();
                        t.forEach((k, q) => { const [x, y] = xy(k); q ? ctx.lineTo(x + C / 2, y + C / 2) : ctx.moveTo(x + C / 2, y + C / 2); }); ctx.stroke();
                        const [x, y] = xy(t[0]); ctx.fillStyle = '#ced4da'; ctx.beginPath(); ctx.arc(x + C / 2, y + C / 2, C * .36, 0, 7); ctx.fill();
                    });
                    (R.flechas || []).forEach(fl => {
                        ctx.strokeStyle = '#868e96'; ctx.lineWidth = 2; ctx.lineCap = 'round'; ctx.beginPath();
                        fl.forEach((k, q) => { const [x, y] = xy(k); q ? ctx.lineTo(x + C / 2, y + C / 2) : ctx.moveTo(x + C / 2, y + C / 2); }); ctx.stroke();
                        const [ax, ay] = xy(fl[fl.length - 2]), [bx, by] = xy(fl[fl.length - 1]), ang = Math.atan2(by - ay, bx - ax);
                        const px = bx + C / 2, py = by + C / 2; ctx.beginPath();
                        ctx.moveTo(px - Math.cos(ang - .5) * C * .25, py - Math.sin(ang - .5) * C * .25); ctx.lineTo(px, py);
                        ctx.lineTo(px - Math.cos(ang + .5) * C * .25, py - Math.sin(ang + .5) * C * .25); ctx.stroke();
                        const [x, y] = xy(fl[0]); ctx.fillStyle = '#fff'; ctx.beginPath(); ctx.arc(x + C / 2, y + C / 2, C * .4, 0, 7); ctx.fill(); ctx.stroke();
                    });
                    // jaulas del asesino
                    (R.jaulas || []).forEach(j => {
                        const s = new Set(j.c), d = C * .1; ctx.strokeStyle = '#495057'; ctx.lineWidth = 1; ctx.setLineDash([3, 3]);
                        j.c.forEach(k => {
                            const [x, y] = xy(k); ctx.beginPath();
                            if (!s.has(k - n)) { ctx.moveTo(x + d, y + d); ctx.lineTo(x + C - d, y + d); }
                            if (!s.has(k + n)) { ctx.moveTo(x + d, y + C - d); ctx.lineTo(x + C - d, y + C - d); }
                            if (k % n === 0 || !s.has(k - 1)) { ctx.moveTo(x + d, y + d); ctx.lineTo(x + d, y + C - d); }
                            if (k % n === n - 1 || !s.has(k + 1)) { ctx.moveTo(x + C - d, y + d); ctx.lineTo(x + C - d, y + C - d); }
                            ctx.stroke();
                        });
                        ctx.setLineDash([]);
                        const k0 = Math.min(...j.c), [x, y] = xy(k0);
                        ctx.fillStyle = '#fff'; ctx.fillRect(x + 2, y + 2, C * .34, C * .26);
                        L.texto(String(j.s), x + 3, y + C * .15 + 2, {tam: C * .22, negrita: true, base: 'middle', color: '#343a40'});
                    });
                    // líneas: delgadas entre casillas, gruesas entre cajas o regiones
                    for (let k = 0; k < N; k++) {
                        const [x, y] = xy(k), c = k % n;
                        ctx.strokeStyle = '#ced4da'; ctx.lineWidth = 1; ctx.strokeRect(x, y, C, C);
                    }
                    ctx.strokeStyle = '#212529'; ctx.lineWidth = 2.5; ctx.lineCap = 'square';
                    for (let k = 0; k < N; k++) {
                        const [x, y] = xy(k), c = k % n, f = Math.floor(k / n); ctx.beginPath();
                        if (c < n - 1 && reg[k] !== reg[k + 1]) { ctx.moveTo(x + C, y); ctx.lineTo(x + C, y + C); }
                        if (f < n - 1 && reg[k] !== reg[k + n]) { ctx.moveTo(x, y + C); ctx.lineTo(x + C, y + C); }
                        ctx.stroke();
                    }
                    ctx.strokeRect(X0, Y0, n * C, n * C);
                    // marcas en los bordes: barras, puntos, sumas y signos
                    Object.entries(R.marcas || {}).forEach(([par, m]) => {
                        const [a, b] = par.split('-').map(Number), [x, y, o] = borde(a, b);
                        if (m === 'c') { ctx.fillStyle = '#fff'; ctx.strokeStyle = '#212529'; ctx.lineWidth = 1.5; const w = o === 'v' ? C * .14 : C * .5, h = o === 'v' ? C * .5 : C * .14; ctx.fillRect(x - w / 2, y - h / 2, w, h); ctx.strokeRect(x - w / 2, y - h / 2, w, h); }
                        else if (m === 'b' || m === 'n') { ctx.fillStyle = m === 'n' ? '#212529' : '#fff'; ctx.strokeStyle = '#212529'; ctx.lineWidth = 1.5; ctx.beginPath(); ctx.arc(x, y, C * .11, 0, 7); ctx.fill(); ctx.stroke(); }
                        else { const t = {V: '5', X: '10', S: '7'}[m]; ctx.fillStyle = '#fff'; ctx.strokeStyle = '#c92a2a'; ctx.lineWidth = 1.2; ctx.beginPath(); ctx.arc(x, y, C * .22, 0, 7); ctx.fill(); ctx.stroke(); L.texto(t, x, y + 1, {tam: C * .27, alinear: 'center', base: 'middle', negrita: true, color: '#c92a2a'}); }
                    });
                    Object.entries(R.signos || {}).forEach(([par, s]) => {
                        const [a, b] = par.split('-').map(Number), [x, y, o] = borde(a, b);
                        const t = o === 'v' ? s : (s === '<' ? '∧' : '∨');
                        ctx.fillStyle = '#fff'; ctx.fillRect(x - C * .12, y - C * .12, C * .24, C * .24);
                        L.texto(t, x, y + 1, {tam: C * .3, alinear: 'center', base: 'middle', negrita: true, color: '#c92a2a'});
                    });
                    // sumas del sándwich
                    if (R.sandwich) {
                        for (let f = 0; f < n; f++) L.texto(String(R.sandwich[f]), X0 - 6, Y0 + f * C + C / 2, {tam: C * .32, alinear: 'right', base: 'middle', negrita: true, color: '#1864ab'});
                        for (let c = 0; c < n; c++) L.texto(String(R.sandwich[n + c]), X0 + c * C + C / 2, Y0 - 8, {tam: C * .32, alinear: 'center', negrita: true, color: '#1864ab'});
                    }
                    // números y notas
                    for (let k = 0; k < N; k++) {
                        const [x, y] = xy(k);
                        if (g[k]) {
                            const mal = choca(k);
                            simbolo(g[k], x + C / 2, y + C / 2 + 1, C * .56, mal ? '#e03131' : dados[k] ? '#212529' : '#1971c2');
                            if (mal && fig) { ctx.strokeStyle = '#e03131'; ctx.lineWidth = 2; ctx.strokeRect(x + 3, y + 3, C - 6, C - 6); }
                        } else if (notas[k].size) {
                            const cols = n === 4 ? 2 : 3, filas = Math.ceil(n / cols);
                            [...notas[k]].forEach(v => {
                                const q = v - 1, nx = x + (q % cols + .5) * C / cols, ny = y + (Math.floor(q / cols) + .5) * C / filas;
                                if (fig) { const [s, col] = FIGURAS[v - 1]; L.texto(s, nx, ny, {tam: C * .2, alinear: 'center', base: 'middle', color: col}); }
                                else L.texto(String(v), nx, ny, {tam: C * .21, alinear: 'center', base: 'middle', color: '#868e96'});
                            });
                        }
                    }
                };

                // Teclado de números (y figuras) debajo del tablero
                const pad = document.createElement('div');
                pad.className = 'sd-pad';
                pad.style.cssText = 'display:flex;flex-wrap:wrap;gap:6px;justify-content:center;margin-top:10px;user-select:none;max-width:520px';
                for (let v = 1; v <= n; v++) {
                    const b = document.createElement('button'); b.type = 'button'; b.className = 'btn btn-light border fw-bold';
                    b.style.cssText = 'min-width:46px;height:46px;font-size:1.3rem';
                    if (fig) { b.textContent = FIGURAS[v - 1][0]; b.style.color = FIGURAS[v - 1][1]; } else b.textContent = v;
                    b.addEventListener('click', () => escribir(v)); pad.appendChild(b);
                }
                const bl = document.createElement('button'); bl.type = 'button'; bl.className = 'btn btn-outline-secondary'; bl.style.height = '46px';
                const pintarLapiz = () => { bl.innerHTML = lapiz ? '✏️ Notas: sí' : '✏️ Notas'; bl.className = 'btn ' + (lapiz ? 'btn-warning' : 'btn-outline-secondary'); };
                bl.addEventListener('click', () => { lapiz = !lapiz; pintarLapiz(); }); pintarLapiz(); pad.appendChild(bl);
                const bb = document.createElement('button'); bb.type = 'button'; bb.className = 'btn btn-outline-danger'; bb.style.height = '46px'; bb.innerHTML = '⌫ Borrar';
                bb.addEventListener('click', () => escribir(0)); pad.appendChild(bb);
                zona.appendChild(pad);

                function guardar() { historia.push([g.slice(), notas.map(s => new Set(s))]); if (historia.length > 300) historia.shift(); }
                function escribir(v) {
                    if (sel < 0 || dados[sel]) return;
                    guardar();
                    if (v && lapiz) { notas[sel].has(v) ? notas[sel].delete(v) : notas[sel].add(v); }
                    else {
                        g[sel] = g[sel] === v ? 0 : v; notas[sel].clear();
                        if (v) [...vecinos[sel]].forEach(j => notas[j].delete(v));     // la nota ya no sirve en las vecinas
                        api.movimiento(); api.sonido && api.sonido(choca(sel) ? 'mal' : 'toque');
                    }
                    L.dibujar(); revisar();
                }
                function revisar() { if (g.every((v, k) => v === sol[k])) api.gano({estrellas: ayudas === 0 ? 3 : ayudas <= 2 ? 2 : 1}); }
                let ayudas = 0;

                L.cv.addEventListener('pointerdown', ev => {
                    const {x, y} = L.punto(ev), c = Math.floor((x - X0) / C), f = Math.floor((y - Y0) / C);
                    if (f >= 0 && f < n && c >= 0 && c < n) { sel = f * n + c; L.dibujar(); }
                });
                const tecla = ev => {
                    if (!L.cv.isConnected) { document.removeEventListener('keydown', tecla); return; }
                    if (['INPUT', 'TEXTAREA'].includes(document.activeElement.tagName)) return;
                    const k = ev.key;
                    if (/^[1-9]$/.test(k) && +k <= n) { ev.preventDefault(); escribir(+k); }
                    else if (k === 'Backspace' || k === 'Delete' || k === '0') { ev.preventDefault(); escribir(0); }
                    else if (k === 'n' || k === 'N') { lapiz = !lapiz; pintarLapiz(); }
                    else {
                        const d = {ArrowUp: -n, ArrowDown: n, ArrowLeft: -1, ArrowRight: 1}[k];
                        if (d !== undefined) {
                            ev.preventDefault(); if (sel < 0) sel = 0;
                            const f = Math.floor(sel / n), c = sel % n;
                            if ((d === -1 && c > 0) || (d === 1 && c < n - 1) || (d === -n && f > 0) || (d === n && f < n - 1)) sel += d;
                            L.dibujar();
                        }
                    }
                };
                document.addEventListener('keydown', tecla);
                return {
                    deshacer() { const u = historia.pop(); if (u) { g = u[0]; notas = u[1]; L.dibujar(); } },
                    ayuda() {
                        // Pone el número correcto en la casilla escogida (o en una vacía) y quita los que estén mal
                        ayudas += 1; guardar();
                        let k = sel >= 0 && !dados[sel] && g[sel] !== sol[sel] ? sel : g.findIndex((v, q) => v !== sol[q]);
                        if (k < 0) return;
                        g[k] = sol[k]; notas[k].clear(); sel = k;
                        api.aviso(ayudas <= 2 ? 'Le puse un número. Con más de 2 ayudas el nivel da menos estrellas.' : 'Le puse otro número.');
                        L.dibujar(); revisar();
                    },
                };
            },
        };
    }
    Object.keys(NOMBRES).forEach(id => Logica.registrar(id, crear(id)));
})();
