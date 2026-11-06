/* Cuatro cuadrantes (tipo Kadogemo): el tablero tiene 4 cuadros de 3×3 con puntos de colores fijos
 * (algunas casillas están en blanco). Hay 4 piezas de 3×3 con 2 huecos; cada una va en un cuadro,
 * girada o volteada, y por sus huecos se ven los puntos. La tarjeta dice cuántos puntos de cada color
 * deben quedar a la vista: la forma y el lugar no importan, solo la cuenta. Todas las tarjetas fueron
 * verificadas con un solucionador (aula/logica_generadores/kadogemo.py). */
Logica.registrar('kadogemo', {
    nombre: 'Cuatro cuadrantes',
    instrucciones: 'Ponga las 4 piezas, una en cada cuadro, para que a la vista queden exactamente los puntos que pide la tarjeta (ni más ni menos de cada color; las casillas en blanco no cuentan). Un toque gira la pieza; dos toques la voltean.',
    total: d => d.retos.length,
    titulo: (d, i) => `Tarjeta ${i + 1}`,
    iniciar(zona, datos, i, api) {
        const reto = datos.retos[i], CEL = 44, SEP = 14, TX = 30, TY = 40, W = 760, H = 380, L = api.lienzo(W, H), ctx = L.ctx;
        const nombres = Object.keys(datos.piezas), T = datos.tablero, PUNTOS = datos.puntos;
        const px = c => TX + c * CEL + (c >= 3 ? SEP : 0), py = f => TY + f * CEL + (f >= 3 ? SEP : 0);
        const bandeja = nombres.map((_, k) => ({x: 345 + (k % 2) * 108, y: 50 + Math.floor(k / 2) * 120}));
        let ayudas = 0, ganado = false;
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
                ctx.fillStyle = 'rgba(255,255,255,.18)'; ctx.fillRect(x + 2, y + 2, k - 4, 5);
                ctx.strokeStyle = 'rgba(0,0,0,.18)'; ctx.lineWidth = 1; ctx.strokeRect(x + .5, y + .5, k - 1, k - 1);
            },
            contorno: false,
            redibujar: () => L.dibujar(),
            alCambiar() {
                api.movimiento();
                if (!ganado && resuelto()) { ganado = true; api.gano({estrellas: ayudas ? 2 : 3}); }
            },
        });
        function aLaVista() {
            const occ = g.ocupadas(), cuenta = {};
            for (let f = 0; f < 6; f++) for (let c = 0; c < 6; c++) {
                const col = T[f][c];
                if (col !== '.' && !occ.has(f + ',' + c)) cuenta[col] = (cuenta[col] || 0) + 1;
            }
            return cuenta;
        }
        function resuelto() {
            if (!g.piezas.every(p => p.en)) return false;
            const v = aLaVista(), colores = new Set(Object.keys(v).concat(Object.keys(reto.cuenta)));
            return [...colores].every(c => (v[c] || 0) === (reto.cuenta[c] || 0));
        }
        function punto(x, y, r, col) {
            ctx.fillStyle = PUNTOS[col]; ctx.beginPath(); ctx.arc(x, y, r, 0, Math.PI * 2); ctx.fill();
            ctx.strokeStyle = col === 'B' ? '#868e96' : 'rgba(0,0,0,.35)'; ctx.lineWidth = 1.5; ctx.stroke();
            ctx.fillStyle = 'rgba(255,255,255,.45)'; ctx.beginPath(); ctx.arc(x - r * .3, y - r * .3, r * .3, 0, Math.PI * 2); ctx.fill();
        }
        L.dibujar = function () {
            L.limpiar('#fbf3e4');
            // tablero de madera con los puntos fijos
            ctx.fillStyle = '#8a5a2b'; Logica.redondo(ctx, TX - 12, TY - 12, 6 * CEL + SEP + 24, 6 * CEL + SEP + 24, 12); ctx.fill();
            for (let q = 0; q < 4; q++) {
                const x = px((q % 2) * 3), y = py(Math.floor(q / 2) * 3);
                ctx.fillStyle = '#d9a86c'; ctx.fillRect(x - 3, y - 3, 3 * CEL + 6, 3 * CEL + 6);
            }
            for (let f = 0; f < 6; f++) for (let c = 0; c < 6; c++) {
                ctx.fillStyle = (f + c) % 2 ? '#e2b77e' : '#e8c18c'; ctx.fillRect(px(c) + 1, py(f) + 1, CEL - 2, CEL - 2);
                if (T[f][c] !== '.') punto(px(c) + CEL / 2, py(f) + CEL / 2, CEL * .27, T[f][c]);
            }
            g.dibujar(ctx);
            // la tarjeta: los puntos que deben quedar a la vista
            const KX = 588, KY = 40, KW = 160, lista = [];
            Object.keys(PUNTOS).forEach(c => { for (let n = 0; n < (reto.cuenta[c] || 0); n++) lista.push(c); });
            const filas = Math.ceil(lista.length / 4), KH = 54 + filas * 36;
            ctx.fillStyle = '#fff'; Logica.redondo(ctx, KX, KY, KW, KH, 10); ctx.fill();
            ctx.strokeStyle = '#212529'; ctx.lineWidth = 4; ctx.stroke();
            L.texto(`NIVEL ${i + 1}`, KX + KW / 2, KY + 22, {tam: 15, negrita: true, alinear: 'center', color: '#212529'});
            lista.forEach((c, k) => {
                const fila = Math.floor(k / 4), enFila = Math.min(4, lista.length - fila * 4);
                punto(KX + KW / 2 + ((k % 4) - (enFila - 1) / 2) * 34, KY + 54 + fila * 36, 15, c);
            });
            // lo que se ve ahora, para comparar
            const v = aLaVista(), y0 = KY + KH + 26;
            L.texto('A la vista ahora:', KX + KW / 2, y0, {tam: 12, negrita: true, alinear: 'center', color: '#495057'});
            const cols = Object.keys(PUNTOS).filter(c => v[c] || reto.cuenta[c]);
            cols.forEach((c, k) => {
                const x = KX + 22 + (k % 2) * 80, y = y0 + 24 + Math.floor(k / 2) * 28, bien = (v[c] || 0) === (reto.cuenta[c] || 0);
                punto(x, y, 9, c);
                L.texto(`${v[c] || 0} de ${reto.cuenta[c] || 0}`, x + 14, y + 4, {tam: 12, negrita: true, color: bien ? '#2f9e44' : '#c92a2a'});
            });
        };
        return {
            girar: () => g.girarUltima(), voltear: () => g.voltearUltima(),
            ayuda() {
                // Dice en qué cuadro va una pieza que todavía no está en su lugar (según una solución verificada)
                const sol = reto.solucion || {}, lugares = ['de arriba a la izquierda', 'de arriba a la derecha', 'de abajo a la izquierda', 'de abajo a la derecha'];
                const colorNombre = {U: 'roja', H: 'amarilla', W: 'verde', S: 'azul'};
                for (const p of g.piezas) {
                    const q = sol[p.nombre];
                    if (q === undefined) continue;
                    if (!p.en || p.en.f !== Math.floor(q / 2) * 3 || p.en.c !== (q % 2) * 3) {
                        ayudas += 1;
                        api.aviso(`La pieza ${colorNombre[p.nombre] || ''} va en el cuadro ${lugares[q]}.`);
                        return;
                    }
                }
                ayudas += 1;
                api.aviso('Cada pieza está en su cuadro: gírelas o voltéelas hasta que la cuenta de colores coincida.');
            },
        };
    },
});
