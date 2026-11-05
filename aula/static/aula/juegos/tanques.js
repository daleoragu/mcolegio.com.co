/* Batalla de tanques: dispárele al tanque que lleva la respuesta correcta y esquive sus balas. */
(function () {
    'use strict';
    const Y0 = 50, ALTO = 260, W = 480, T = 18;
    const DIRS = {arriba: [0, -1], abajo: [0, 1], izquierda: [-1, 0], derecha: [1, 0]};
    const MUROS = [[90, 60, 60, 14], [330, 60, 60, 14], [200, 120, 80, 14], [60, 170, 14, 50], [406, 170, 14, 50], [150, 205, 50, 14], [280, 205, 50, 14]];

    const choca = (x, y, w, h) => x < 0 || y < 0 || x + w > W || y + h > ALTO ||
        MUROS.some(([mx, my, mw, mh]) => x < mx + mw && x + w > mx && y < my + mh && y + h > my);

    function dibujarTanque(ctx, t, color, etiqueta, m) {
        const x = t.x, y = Y0 + t.y, [dx, dy] = DIRS[t.dir];
        ctx.fillStyle = '#222'; ctx.fillRect(x - 1, y - 1, T + 2, T + 2);
        ctx.fillStyle = color; ctx.fillRect(x + 2, y + 2, T - 4, T - 4);
        ctx.fillStyle = '#333';
        if (dx) { ctx.fillRect(x, y, T, 3); ctx.fillRect(x, y + T - 3, T, 3); } else { ctx.fillRect(x, y, 3, T); ctx.fillRect(x + T - 3, y, 3, T); }
        ctx.fillStyle = '#111';
        ctx.fillRect(x + T / 2 - 2 + dx * 7, y + T / 2 - 2 + dy * 7, 4 + Math.abs(dx) * 6, 4 + Math.abs(dy) * 6);
        if (etiqueta !== undefined) m.etiqueta(etiqueta, x + T / 2, y - 9, 7);
    }

    Gamificacion.registrar('tanques', {
        nombre: 'Batalla de tanques',
        instrucciones: 'Muévase con las flechas y dispare con la barra espaciadora (o el botón FUEGO) al tanque con la respuesta correcta.',
        controles: 'cruceta-fuego',
        fondo: '#1b2a1b',
        nuevaPregunta(m) {
            const n = m.opciones.length, pos = [[30, 20], [430, 20], [140, 20], [320, 20]];
            m.s = {
                yo: {x: 231, y: 236, dir: 'arriba', vel: 80, recarga: 0},
                enemigos: Array.from({length: n}, (_, k) => ({x: pos[k][0], y: pos[k][1], dir: 'abajo', k, vel: Math.min(70, 30 + m.nivel * 6),
                                                             cambio: 1 + Math.random() * 2, disparo: 2 + Math.random() * 3})),
                balas: [], explosiones: [], invencible: m.t + 1.2,
            };
        },
        alTecla(m, t) { if (t === 'disparo') this.disparar(m); },
        disparar(m) {
            const yo = m.s.yo;
            if (yo.recarga > 0) return;
            const [dx, dy] = DIRS[yo.dir];
            m.s.balas.push({x: yo.x + T / 2 + dx * 10, y: yo.y + T / 2 + dy * 10, dx, dy, mia: true});
            yo.recarga = 0.45; m.sonidos.toque();
        },
        actualizar(m, dt) {
            const s = m.s, yo = s.yo;
            yo.recarga -= dt;
            const dir = ['arriba', 'abajo', 'izquierda', 'derecha'].find(d => m.teclas.has(d));
            if (dir) {
                yo.dir = dir;
                const nx = yo.x + DIRS[dir][0] * yo.vel * dt, ny = yo.y + DIRS[dir][1] * yo.vel * dt;
                if (!choca(nx, ny, T, T)) { yo.x = nx; yo.y = ny; }
            }
            if (m.teclas.has('disparo')) this.disparar(m);
            s.enemigos.forEach(e => {
                e.cambio -= dt; e.disparo -= dt;
                const nx = e.x + DIRS[e.dir][0] * e.vel * dt, ny = e.y + DIRS[e.dir][1] * e.vel * dt;
                if (choca(nx, ny, T, T) || e.cambio <= 0) {
                    e.dir = Object.keys(DIRS)[Math.floor(Math.random() * 4)]; e.cambio = 1 + Math.random() * 2;
                } else { e.x = nx; e.y = ny; }
                if (e.disparo <= 0) {
                    // Apunta más o menos hacia el jugador
                    const ddx = yo.x - e.x, ddy = yo.y - e.y;
                    e.dir = Math.abs(ddx) > Math.abs(ddy) ? (ddx > 0 ? 'derecha' : 'izquierda') : (ddy > 0 ? 'abajo' : 'arriba');
                    const [dx, dy] = DIRS[e.dir];
                    s.balas.push({x: e.x + T / 2 + dx * 10, y: e.y + T / 2 + dy * 10, dx, dy, mia: false});
                    e.disparo = Math.max(1.2, 3.5 - m.nivel * .3) + Math.random() * 2.5;
                }
            });
            for (const b of s.balas) {
                b.x += b.dx * 220 * dt; b.y += b.dy * 220 * dt;
                if (choca(b.x - 2, b.y - 2, 4, 4)) { b.fuera = true; continue; }
                if (b.mia) {
                    const e = s.enemigos.find(e => b.x > e.x && b.x < e.x + T && b.y > e.y && b.y < e.y + T);
                    if (e) { b.fuera = true; s.explosiones.push({x: e.x + T / 2, y: e.y + T / 2, t: m.t}); m.responder(e.k); return; }
                } else if (m.t > s.invencible && b.x > yo.x && b.x < yo.x + T && b.y > yo.y && b.y < yo.y + T) {
                    b.fuera = true; m.perderVida('¡LE DIERON!'); return;
                }
            }
            s.balas = s.balas.filter(b => !b.fuera);
        },
        dibujar(m, ctx) {
            for (let x = 0; x < W; x += 24) for (let y = 0; y < ALTO; y += 24) {
                ctx.fillStyle = (x + y) % 48 ? '#223a22' : '#1f341f'; ctx.fillRect(x, Y0 + y, 24, 24);
            }
            MUROS.forEach(([x, y, w, h]) => {
                ctx.fillStyle = '#8d6e63'; ctx.fillRect(x, Y0 + y, w, h);
                ctx.fillStyle = '#6d4c41'; for (let i = x; i < x + w; i += 10) ctx.fillRect(i, Y0 + y, 1, h);
            });
            const s = m.s; if (!s) return;
            s.enemigos.forEach(e => dibujarTanque(ctx, e, m.COLORES[e.k], e.k, m));
            if (m.t > s.invencible || Math.floor(m.t * 10) % 2) dibujarTanque(ctx, s.yo, '#e9ecef', undefined, m);
            s.balas.forEach(b => { ctx.fillStyle = b.mia ? '#ffd43b' : '#ff6b6b'; ctx.fillRect(b.x - 2, Y0 + b.y - 2, 4, 4); });
            s.explosiones = s.explosiones.filter(x => m.t - x.t < .5);
            s.explosiones.forEach(x => {
                const r = (m.t - x.t) * 50; ctx.strokeStyle = '#ffa94d'; ctx.lineWidth = 3;
                ctx.beginPath(); ctx.arc(x.x, Y0 + x.y, r, 0, Math.PI * 2); ctx.stroke();
            });
        },
    });
})();
