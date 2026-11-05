/* Laberinto comelón: la gota recorre el laberinto y se come la galleta de la respuesta correcta.
 * Los virus la persiguen: si la tocan, pierde una vida. */
(function () {
    'use strict';
    const C = 20, X0 = 0, Y0 = 50, COLS = 24, FILAS = 13;
    // # = pared · . = camino. Diseño propio, simétrico.
    const MAPA = [
        '########################',
        '#..........##..........#',
        '#.####.###.##.###.####.#',
        '#......................#',
        '#.####.#.########.#.####',
        '#......#....##....#....#',
        '######.####.##.####.####',
        '#......#..........#....#',
        '#.####.#.###..###.#.##.#',
        '#......................#',
        '#.###.####.##.####.###.#',
        '#..........##..........#',
        '########################',
    ];
    const ESQUINAS = [[1, 1], [22, 1], [1, 11], [22, 11]];
    const libre = (cx, cy) => cy >= 0 && cy < FILAS && cx >= 0 && cx < COLS && MAPA[cy][cx] !== '#';
    const DIRS = {arriba: [0, -1], abajo: [0, 1], izquierda: [-1, 0], derecha: [1, 0]};

    function ente(cx, cy, vel) { return {cx, cy, x: cx * C, y: cy * C, dir: null, quiere: null, vel}; }

    function mover(e, dt, elegir) {
        const tx = e.cx * C, ty = e.cy * C;
        if (Math.abs(e.x - tx) < 0.5 && Math.abs(e.y - ty) < 0.5) {
            e.x = tx; e.y = ty;
            if (elegir) elegir(e);
            if (e.quiere && libre(e.cx + DIRS[e.quiere][0], e.cy + DIRS[e.quiere][1])) e.dir = e.quiere;
            if (!e.dir || !libre(e.cx + DIRS[e.dir][0], e.cy + DIRS[e.dir][1])) { e.dir = null; return; }
            e.cx += DIRS[e.dir][0]; e.cy += DIRS[e.dir][1];
        }
        const ox = e.cx * C - e.x, oy = e.cy * C - e.y, d = Math.hypot(ox, oy), paso = e.vel * dt;
        if (d <= paso) { e.x = e.cx * C; e.y = e.cy * C; } else { e.x += ox / d * paso; e.y += oy / d * paso; }
    }

    function elegirVirus(m) {
        return function (e) {
            const opciones = Object.keys(DIRS).filter(k => libre(e.cx + DIRS[k][0], e.cy + DIRS[k][1]));
            const reversa = e.dir ? Object.keys(DIRS).find(k => DIRS[k][0] === -DIRS[e.dir][0] && DIRS[k][1] === -DIRS[e.dir][1]) : null;
            let validas = opciones.filter(k => k !== reversa);
            if (!validas.length) validas = opciones;
            // A veces persigue a la gota, a veces va al azar (así no es imposible).
            if (Math.random() < 0.55) {
                validas.sort((a, b) => Math.hypot(e.cx + DIRS[a][0] - m.s.gota.cx, e.cy + DIRS[a][1] - m.s.gota.cy) -
                                       Math.hypot(e.cx + DIRS[b][0] - m.s.gota.cx, e.cy + DIRS[b][1] - m.s.gota.cy));
                e.quiere = validas[0];
            } else { e.quiere = validas[Math.floor(Math.random() * validas.length)]; }
        };
    }

    Gamificacion.registrar('laberinto', {
        nombre: 'Laberinto comelón',
        instrucciones: 'Mueva la gota con las flechas y cómase la galleta de la respuesta correcta. ¡Cuidado con los virus!',
        controles: 'cruceta',
        // Barra lateral: la galleta de la opción, con su color y su letra
        icono(ctx, k, tam) {
            const r = tam * .4, c = tam / 2;
            ctx.fillStyle = Gamificacion.COLORES[k]; ctx.beginPath(); ctx.arc(c, c, r, 0, Math.PI * 2); ctx.fill();
            ctx.fillStyle = 'rgba(0,0,0,.25)'; [[-.4, -.3], [.35, -.1], [-.1, .4], [.3, .35]].forEach(([x, y]) => { ctx.beginPath(); ctx.arc(c + x * r, c + y * r, tam * .05, 0, Math.PI * 2); ctx.fill(); });
            ctx.fillStyle = '#111'; ctx.font = `bold ${Math.round(tam * .42)}px sans-serif`; ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
            ctx.fillText(Gamificacion.LETRAS[k], c, c + 1);
        },
        nuevaPregunta(m) {
            const n = m.opciones.length;
            const esquinas = ESQUINAS.slice().sort(() => Math.random() - .5).slice(0, n);
            m.s = {
                gota: ente(11, 9, 92),
                // Nivel 1: un virus lento; luego más virus y más rápidos.
                virus: [ente(10, 1, 50), ente(13, 1, 50), ente(1, 5, 50), ente(22, 5, 50)]
                    .slice(0, Math.min(4, m.nivel)).map(v => Object.assign(v, {vel: Math.min(85, 48 + m.nivel * 6)})),
                galletas: esquinas.map((p, k) => ({cx: p[0], cy: p[1], k})),
                elegir: elegirVirus(m),
                invencible: m.t + 2.5,
            };
        },
        alTecla(m, t) { if (DIRS[t]) m.s.gota.quiere = t; },
        actualizar(m, dt) {
            const s = m.s;
            mover(s.gota, dt);
            s.virus.forEach(v => mover(v, dt, s.elegir));
            const g = s.galletas.find(g => g.cx === s.gota.cx && g.cy === s.gota.cy &&
                                            Math.hypot(s.gota.x - g.cx * C, s.gota.y - g.cy * C) < 6);
            if (g) { m.responder(g.k); return; }
            if (m.t > s.invencible && s.virus.some(v => Math.hypot(v.x - s.gota.x, v.y - s.gota.y) < 13)) m.perderVida('¡UN VIRUS!');
        },
        dibujar(m, ctx) {
            const s = m.s;
            for (let y = 0; y < FILAS; y++) for (let x = 0; x < COLS; x++) {
                if (MAPA[y][x] === '#') {
                    ctx.fillStyle = '#1c2a6b'; ctx.fillRect(X0 + x * C, Y0 + y * C, C, C);
                    ctx.fillStyle = '#3b5bdb'; ctx.fillRect(X0 + x * C + 2, Y0 + y * C + 2, C - 4, C - 4);
                }
            }
            if (!s) return;
            s.galletas.forEach(g => {
                const pulso = 1 + Math.sin(m.t * 6) * .12;
                m.etiqueta(g.k, X0 + g.cx * C + C / 2, Y0 + g.cy * C + C / 2, 9 * pulso);
            });
            // La gota: una gota de agua sonriente
            const gx = X0 + s.gota.x + C / 2, gy = Y0 + s.gota.y + C / 2;
            if (m.t > s.invencible || Math.floor(m.t * 10) % 2) {
                ctx.fillStyle = '#7fe3ff';
                ctx.beginPath(); ctx.moveTo(gx, gy - 9); ctx.quadraticCurveTo(gx + 9, gy + 1, gx, gy + 8);
                ctx.quadraticCurveTo(gx - 9, gy + 1, gx, gy - 9); ctx.fill();
                ctx.fillStyle = '#0b1021'; ctx.fillRect(gx - 4, gy, 2, 2); ctx.fillRect(gx + 2, gy, 2, 2);
                ctx.fillRect(gx - 2, gy + 4, 4, 1);
            }
            // Los virus: esferas con puntas
            s.virus.forEach((v, i) => {
                const vx = X0 + v.x + C / 2, vy = Y0 + v.y + C / 2;
                ctx.fillStyle = i ? '#e64980' : '#94d82d';
                for (let a = 0; a < 8; a++) {
                    const ang = a * Math.PI / 4 + m.t * 2;
                    ctx.fillRect(vx + Math.cos(ang) * 8 - 1.5, vy + Math.sin(ang) * 8 - 1.5, 3, 3);
                }
                ctx.beginPath(); ctx.arc(vx, vy, 6, 0, Math.PI * 2); ctx.fill();
                ctx.fillStyle = '#fff'; ctx.fillRect(vx - 3, vy - 2, 2, 2); ctx.fillRect(vx + 1, vy - 2, 2, 2);
            });
        },
    });
})();
