/* Geoplano: toque los clavos para tender la banda elástica y ciérrela tocando el primer clavo.
 * Cada reto pide una figura (rectángulo, cuadrado, triángulo, polígono…) con cierta área o perímetro.
 * El área se cuenta en cuadritos (la distancia entre dos clavos vecinos es 1). */
(function () {
    'use strict';
    const RETOS = [
        // 5×5 clavos
        {forma: 'rectangulo', area: 6}, {forma: 'cuadrado', area: 4}, {forma: 'triangulo', area: 3}, {forma: 'rectangulo', area: 8},
        {forma: 'cuadrado', area: 9}, {forma: 'triangulo', area: 4}, {forma: 'rectangulo', area: 12}, {forma: 'triangulo', area: 6},
        {forma: 'cualquiera', area: 5}, {forma: 'cuadrado', area: 16},
        // 6×6 clavos
        {forma: 'triangulo_rect', area: 4.5}, {forma: 'rectangulo', area: 12, perimetro: 14}, {forma: 'rectangulo', area: 8, perimetro: 12},
        {forma: 'poligono', lados: 5, area: 6}, {forma: 'cuadrado', area: 2, inclinado: true}, {forma: 'triangulo', area: 7.5},
        {forma: 'poligono', lados: 6, area: 7}, {forma: 'triangulo_rect', area: 8}, {forma: 'rectangulo', area: 10, perimetro: 14}, {forma: 'poligono', lados: 4, area: 5},
        // 7×7 clavos
        {forma: 'cuadrado', area: 5, inclinado: true}, {forma: 'cuadrado', area: 8, inclinado: true}, {forma: 'cuadrado', area: 10, inclinado: true},
        {forma: 'rectangulo', area: 6, inclinado: true}, {forma: 'cuadrado', area: 13, inclinado: true}, {forma: 'poligono', lados: 6, area: 12},
        {forma: 'triangulo', area: 9.5}, {forma: 'poligono', lados: 8, area: 14}, {forma: 'cuadrado', area: 17, inclinado: true}, {forma: 'triangulo_rect', area: 10},
    ];
    const NOM = {rectangulo: 'un rectángulo', cuadrado: 'un cuadrado', triangulo: 'un triángulo', triangulo_rect: 'un triángulo rectángulo', cualquiera: 'una figura cerrada'};
    function texto(r) {
        let t = 'Forme ' + (r.forma === 'poligono' ? `un polígono de ${r.lados} lados` : NOM[r.forma]);
        if (r.inclinado) t += ' inclinado (sin lados horizontales)';
        t += ` de área ${String(r.area).replace('.', ',')}`;
        if (r.perimetro) t += ` y perímetro ${r.perimetro}`;
        return t + '.';
    }
    const area = P => Math.abs(P.reduce((s, [x, y], k) => { const [a, b] = P[(k + 1) % P.length]; return s + x * b - a * y; }, 0)) / 2;
    function limpiar(P) {   // quita los clavos que quedan en medio de un lado recto
        let Q = P.slice(), cambio = true;
        while (cambio && Q.length > 3) {
            cambio = false;
            for (let k = 0; k < Q.length; k++) {
                const a = Q[(k + Q.length - 1) % Q.length], b = Q[k], c = Q[(k + 1) % Q.length];
                if ((b[0] - a[0]) * (c[1] - b[1]) - (b[1] - a[1]) * (c[0] - b[0]) === 0) { Q.splice(k, 1); cambio = true; break; }
            }
        }
        return Q;
    }
    function cruzan(p1, p2, p3, p4) {
        const d = (a, b, c) => (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0]);
        const d1 = d(p3, p4, p1), d2 = d(p3, p4, p2), d3 = d(p1, p2, p3), d4 = d(p1, p2, p4);
        return ((d1 > 0) !== (d2 > 0)) && ((d3 > 0) !== (d4 > 0)) && d1 && d2 && d3 && d4;
    }
    function simple(P) {
        for (let a = 0; a < P.length; a++) for (let b = a + 2; b < P.length; b++) {
            if (a === 0 && b === P.length - 1) continue;
            if (cruzan(P[a], P[(a + 1) % P.length], P[b], P[(b + 1) % P.length])) return false;
        }
        return new Set(P.map(p => p.join())).size === P.length;
    }
    function revisar(r, P0) {
        if (!simple(P0)) return 'La banda se cruza: debe ser una figura sin cruces.';
        const P = limpiar(P0), n = P.length, A = area(P);
        const lados = P.map((p, k) => [P[(k + 1) % n][0] - p[0], P[(k + 1) % n][1] - p[1]]);
        const recto = k => { const u = lados[k], v = lados[(k + 1) % n]; return u[0] * v[0] + u[1] * v[1] === 0; };
        const largo = v => Math.hypot(v[0], v[1]);
        if ((r.forma === 'triangulo' || r.forma === 'triangulo_rect') && n !== 3) return `Eso no es un triángulo: tiene ${n} lados.`;
        if (r.forma === 'triangulo_rect' && ![0, 1, 2].some(recto)) return 'El triángulo no tiene un ángulo recto.';
        if ((r.forma === 'rectangulo' || r.forma === 'cuadrado') && (n !== 4 || ![0, 1, 2, 3].every(recto))) return 'Eso no es un rectángulo: necesita 4 ángulos rectos.';
        if (r.forma === 'cuadrado' && Math.abs(largo(lados[0]) - largo(lados[1])) > 1e-9) return 'Es un rectángulo, pero sus lados no son iguales.';
        if (r.forma === 'poligono' && n !== r.lados) return `La figura tiene ${n} lados y se piden ${r.lados}.`;
        if (r.inclinado && lados.some(v => v[0] === 0 || v[1] === 0)) return 'Debe quedar inclinada: ningún lado horizontal ni vertical.';
        if (Math.abs(A - r.area) > 1e-9) return `La forma está bien, pero el área es ${String(A).replace('.', ',')} y se pide ${String(r.area).replace('.', ',')}.`;
        if (r.perimetro && Math.abs(lados.reduce((s, v) => s + largo(v), 0) - r.perimetro) > 1e-9) return 'El área está bien, pero el perímetro no.';
        return '';
    }
    Logica.registrar('geoplano', {
        nombre: 'Geoplano',
        instrucciones: 'Toque los clavos uno por uno para tender la banda y toque el primero para cerrarla. El área se mide en cuadritos (entre dos clavos vecinos hay 1). Deshacer quita el último clavo.',
        total: () => RETOS.length,
        titulo: (d, i) => texto(RETOS[i]),
        iniciar(zona, datos, i, api) {
            const r = RETOS[i], N = i < 10 ? 5 : i < 20 ? 6 : 7, S = Math.floor(360 / (N - 1)), M = 40, W = M * 2 + S * (N - 1) + 230, H = M * 2 + S * (N - 1), L = api.lienzo(W, H), ctx = L.ctx;
            let P = [], cerrada = false;
            const X = x => M + x * S, Y = y => M + y * S;
            L.dibujar = function () {
                L.limpiar('#f3e9d2');
                ctx.fillStyle = '#d9b77a'; Logica.redondo(ctx, M - 24, M - 24, S * (N - 1) + 48, S * (N - 1) + 48, 16); ctx.fill();
                if (P.length) {
                    ctx.beginPath(); P.forEach(([x, y], k) => (k ? ctx.lineTo : ctx.moveTo).call(ctx, X(x), Y(y)));
                    if (cerrada) { ctx.closePath(); ctx.fillStyle = 'rgba(230,73,128,.25)'; ctx.fill(); }
                    ctx.strokeStyle = '#e64980'; ctx.lineWidth = 5; ctx.lineJoin = 'round'; ctx.stroke();
                    if (!cerrada && L.punteroX !== undefined) { ctx.setLineDash([5, 5]); ctx.lineWidth = 2; ctx.beginPath(); ctx.moveTo(X(P[P.length - 1][0]), Y(P[P.length - 1][1])); ctx.lineTo(L.punteroX, L.punteroY); ctx.stroke(); ctx.setLineDash([]); }
                }
                for (let y = 0; y < N; y++) for (let x = 0; x < N; x++) {
                    const usado = P.some(p => p[0] === x && p[1] === y);
                    ctx.fillStyle = 'rgba(0,0,0,.25)'; ctx.beginPath(); ctx.arc(X(x) + 2, Y(y) + 3, 7, 0, Math.PI * 2); ctx.fill();
                    ctx.fillStyle = usado ? '#c2255c' : '#868e96'; ctx.beginPath(); ctx.arc(X(x), Y(y), 7, 0, Math.PI * 2); ctx.fill();
                    ctx.fillStyle = 'rgba(255,255,255,.5)'; ctx.beginPath(); ctx.arc(X(x) - 2, Y(y) - 2, 2.5, 0, Math.PI * 2); ctx.fill();
                }
                const TX = M * 2 + S * (N - 1) + 10;
                ctx.fillStyle = '#fff'; Logica.redondo(ctx, TX, M - 20, 210, 150, 12); ctx.fill();
                L.texto('RETO', TX + 12, M + 2, {tam: 13, negrita: true, color: '#c2255c'});
                ctx.font = '14px system-ui'; let linea = '', yy = M + 24;
                texto(r).split(' ').forEach(w => { if (ctx.measureText(linea + w).width > 186) { L.texto(linea, TX + 12, yy, {tam: 14}); yy += 19; linea = ''; } linea += w + ' '; });
                L.texto(linea, TX + 12, yy, {tam: 14});
                if (cerrada) L.texto(`Área: ${String(area(P)).replace('.', ',')}`, TX + 12, M + 160, {tam: 16, negrita: true, color: '#495057'});
            };
            L.cv.addEventListener('pointermove', ev => { const p = L.punto(ev); L.punteroX = p.x; L.punteroY = p.y; if (P.length && !cerrada) L.dibujar(); });
            L.cv.addEventListener('pointerdown', ev => {
                if (cerrada) return;
                const {x, y} = L.punto(ev), cx = Math.round((x - M) / S), cy = Math.round((y - M) / S);
                if (cx < 0 || cy < 0 || cx >= N || cy >= N || Math.hypot(X(cx) - x, Y(cy) - y) > S * .4) return;
                if (P.length >= 3 && P[0][0] === cx && P[0][1] === cy) {
                    cerrada = true; api.movimiento(); L.dibujar();
                    const error = revisar(r, P);
                    if (!error) api.gano({estrellas: 3, detalle: texto(r)});
                    else api.aviso(error + ' Use Deshacer para abrir la banda.');
                    return;
                }
                if (P.some(p => p[0] === cx && p[1] === cy)) return;
                P.push([cx, cy]); api.sonido('toque'); L.dibujar();
            });
            return { deshacer() { if (cerrada) cerrada = false; else P.pop(); L.dibujar(); } };
        },
    });
})();
