/* Batalla de tanques: dispárele al tanque que lleva la respuesta correcta y cuide la insignia de su base.
 * Los muros de ladrillo se rompen a balazos; los de acero no. Si una bala enemiga llega a la insignia,
 * se pierde una vida (y la base se reconstruye). */
(function () {
    'use strict';
    const Y0 = 50, W = 480, ALTO = 260, T = 20, L = 10;          // tamaño del tanque y de cada ladrillo
    const DIRS = {arriba: [0, -1], abajo: [0, 1], izquierda: [-1, 0], derecha: [1, 0]};
    const ACERO = [[60, 70, 40, 10], [380, 70, 40, 10], [220, 110, 40, 10], [30, 160, 10, 30], [440, 160, 10, 30]];
    const BASE = {x: 228, y: 226, w: 24, h: 24};

    function ladrillos() {
        const lista = [];
        const bloque = (x0, y0, ancho, alto) => { for (let x = x0; x < x0 + ancho; x += L) for (let y = y0; y < y0 + alto; y += L) lista.push({x, y}); };
        bloque(130, 60, 40, 20); bloque(310, 60, 40, 20); bloque(150, 150, 40, 20); bloque(290, 150, 40, 20); bloque(200, 180, 80, 10);
        // La muralla de la base (abierta por arriba en el centro para poder salir a disparar)
        bloque(BASE.x - 10, BASE.y - 10, 10, 34); bloque(BASE.x + BASE.w, BASE.y - 10, 10, 34);
        bloque(BASE.x - 10, BASE.y - 10, 14, 10); bloque(BASE.x + BASE.w - 4, BASE.y - 10, 14, 10);
        return lista;
    }

    const solapa = (a, b) => a.x < b.x + b.w && a.x + a.w > b.x && a.y < b.y + b.h && a.y + a.h > b.y;

    function bloquea(s, x, y, w, h) {
        if (x < 0 || y < 0 || x + w > W || y + h > ALTO) return true;
        const caja = {x, y, w, h};
        return ACERO.some(([ax, ay, aw, ah]) => solapa(caja, {x: ax, y: ay, w: aw, h: ah})) ||
               s.ladrillos.some(l => solapa(caja, {x: l.x, y: l.y, w: L, h: L})) || solapa(caja, BASE);
    }

    function dibujarTanque(ctx, t, color, oscuro, m, etiqueta) {
        const x = t.x, y = Y0 + t.y, [dx, dy] = DIRS[t.dir], horizontal = dx !== 0;
        const paso = Math.floor((t.recorrido || 0) / 3) % 2;
        ctx.save(); ctx.translate(x + T / 2, y + T / 2);
        ctx.rotate(Math.atan2(dy, dx) + Math.PI / 2);
        // Orugas con eslabones que se mueven
        ctx.fillStyle = '#1b1b1b'; ctx.fillRect(-T / 2, -T / 2, 5, T); ctx.fillRect(T / 2 - 5, -T / 2, 5, T);
        ctx.fillStyle = '#555';
        for (let i = -T / 2 + paso * 2; i < T / 2; i += 4) { ctx.fillRect(-T / 2, i, 5, 2); ctx.fillRect(T / 2 - 5, i, 5, 2); }
        // Casco
        ctx.fillStyle = oscuro; ctx.fillRect(-T / 2 + 4, -T / 2 + 2, T - 8, T - 4);
        ctx.fillStyle = color; ctx.fillRect(-T / 2 + 5, -T / 2 + 3, T - 10, T - 6);
        // Torreta y cañón
        ctx.fillStyle = oscuro; ctx.beginPath(); ctx.arc(0, 1, 5, 0, Math.PI * 2); ctx.fill();
        ctx.fillStyle = color; ctx.beginPath(); ctx.arc(0, 1, 3.5, 0, Math.PI * 2); ctx.fill();
        ctx.fillStyle = '#212529'; ctx.fillRect(-1.5, -T / 2 - 4, 3, T / 2 + 3);
        ctx.restore();
        // La letra encima del tanque (o debajo, si está pegado al borde de arriba)
        if (etiqueta !== undefined) m.etiqueta(etiqueta, x + T / 2, t.y < 14 ? y + T + 9 : y - 9, 7);
        void horizontal;
    }

    function dibujarInsignia(ctx, m, golpe) {
        const x = BASE.x, y = Y0 + BASE.y;
        ctx.fillStyle = golpe ? '#c92a2a' : '#1c3d5a'; ctx.fillRect(x, y, BASE.w, BASE.h);
        // Escudo con estrella
        ctx.fillStyle = '#ffd43b';
        ctx.beginPath(); ctx.moveTo(x + 4, y + 3); ctx.lineTo(x + BASE.w - 4, y + 3); ctx.lineTo(x + BASE.w - 4, y + 13);
        ctx.quadraticCurveTo(x + BASE.w / 2, y + BASE.h + 1, x + 4, y + 13); ctx.closePath(); ctx.fill();
        ctx.fillStyle = '#c92a2a'; ctx.beginPath();
        for (let i = 0; i < 10; i++) {
            const r = i % 2 ? 2.4 : 5.5, a = -Math.PI / 2 + i * Math.PI / 5;
            ctx.lineTo(x + BASE.w / 2 + Math.cos(a) * r, y + 11 + Math.sin(a) * r);
        }
        ctx.fill();
    }

    Gamificacion.registrar('tanques', {
        joystick: '4',
        nombre: 'Batalla de tanques',
        instrucciones: 'Flechas para moverse, espacio (o FUEGO) para disparar. Destruya el tanque con la respuesta correcta y no deje que le disparen a la insignia de su base.',
        controles: 'cruceta-fuego',
        fondo: '#1b2a1b',
        // Para la barra lateral: el tanque de la opción, de su color, con la letra
        icono(ctx, k, tam) {
            const OSC = ['#a61e1e', '#1864ab', '#b08900', '#2b8a3e'], esc = tam / 28;
            ctx.save(); ctx.scale(esc, esc); ctx.translate(14 - T / 2, 14 - T / 2 - Y0);   // el tanque, centrado
            dibujarTanque(ctx, {x: 0, y: 0, dir: 'arriba', recorrido: 0}, Gamificacion.COLORES[k], OSC[k], null);
            ctx.restore();
            ctx.fillStyle = '#111'; ctx.font = `bold ${Math.round(tam * .32)}px sans-serif`; ctx.textAlign = 'right'; ctx.textBaseline = 'bottom';
            ctx.fillStyle = '#fff'; ctx.fillText(Gamificacion.LETRAS[k], tam - 1, tam);
        },
        nuevaPregunta(m, repetir) {
            const n = m.opciones.length, salidas = [[10, 8], [450, 8], [120, 8], [340, 8]];
            if (!m.ladrillos || !repetir) m.ladrillos = ladrillos();
            m.s = {
                ladrillos: m.ladrillos,
                yo: {x: 190, y: 232, dir: 'arriba', vel: 82, recarga: 0, recorrido: 0},
                enemigos: Array.from({length: n}, (_, k) => ({x: salidas[k][0], y: salidas[k][1], dir: 'abajo', k, recorrido: 0,
                    vel: Math.min(70, 28 + m.nivel * 6), cambio: 1 + Math.random() * 2, disparo: 2 + Math.random() * 3,
                    vaALaBase: Math.random() < Math.min(.6, .15 + m.nivel * .08)})),
                balas: [], chispas: [], invencible: m.t + 1.5, golpeBase: 0,
            };
        },
        alTecla(m, t) { if (t === 'disparo') this.disparar(m); },
        disparar(m) {
            const yo = m.s.yo;
            if (yo.recarga > 0) return;
            const [dx, dy] = DIRS[yo.dir];
            m.s.balas.push({x: yo.x + T / 2 + dx * 12, y: yo.y + T / 2 + dy * 12, dx, dy, mia: true});
            yo.recarga = 0.4; m.sonidos.toque();
        },
        bala(m, b, dt) {
            const s = m.s;
            b.x += b.dx * 230 * dt; b.y += b.dy * 230 * dt;
            if (b.x < 0 || b.y < 0 || b.x > W || b.y > ALTO) return true;
            const caja = {x: b.x - 2, y: b.y - 2, w: 4, h: 4};
            if (ACERO.some(([ax, ay, aw, ah]) => solapa(caja, {x: ax, y: ay, w: aw, h: ah}))) return true;
            const li = s.ladrillos.findIndex(l => solapa(caja, {x: l.x, y: l.y, w: L, h: L}));
            if (li >= 0) { s.chispas.push({x: s.ladrillos[li].x + 5, y: s.ladrillos[li].y + 5, t: m.t}); s.ladrillos.splice(li, 1); return true; }
            if (solapa(caja, BASE)) {
                if (!b.mia) { s.golpeBase = m.t; m.perderVida('¡LE DIERON A LA INSIGNIA!'); m.ladrillos = null; }
                return true;
            }
            return false;
        },
        actualizar(m, dt) {
            const s = m.s, yo = s.yo;
            yo.recarga -= dt;
            const dir = ['arriba', 'abajo', 'izquierda', 'derecha'].find(d => m.teclas.has(d));
            if (dir) {
                yo.dir = dir;
                const nx = yo.x + DIRS[dir][0] * yo.vel * dt, ny = yo.y + DIRS[dir][1] * yo.vel * dt;
                if (!bloquea(s, nx, ny, T, T)) { yo.x = nx; yo.y = ny; yo.recorrido += yo.vel * dt; }
            }
            if (m.teclas.has('disparo')) this.disparar(m);
            s.enemigos.forEach(e => {
                e.cambio -= dt; e.disparo -= dt;
                const nx = e.x + DIRS[e.dir][0] * e.vel * dt, ny = e.y + DIRS[e.dir][1] * e.vel * dt;
                if (bloquea(s, nx, ny, T, T) || e.cambio <= 0) {
                    if (e.vaALaBase && Math.random() < .6) {
                        const ddx = BASE.x - e.x, ddy = BASE.y - e.y;
                        e.dir = Math.abs(ddx) > Math.abs(ddy) ? (ddx > 0 ? 'derecha' : 'izquierda') : (ddy > 0 ? 'abajo' : 'arriba');
                    } else { e.dir = Object.keys(DIRS)[Math.floor(Math.random() * 4)]; }
                    e.cambio = 1 + Math.random() * 2;
                } else { e.x = nx; e.y = ny; e.recorrido += e.vel * dt; }
                if (e.disparo <= 0) {
                    const objetivo = e.vaALaBase ? BASE : yo, ddx = objetivo.x - e.x, ddy = objetivo.y - e.y;
                    e.dir = Math.abs(ddx) > Math.abs(ddy) ? (ddx > 0 ? 'derecha' : 'izquierda') : (ddy > 0 ? 'abajo' : 'arriba');
                    const [dx, dy] = DIRS[e.dir];
                    s.balas.push({x: e.x + T / 2 + dx * 12, y: e.y + T / 2 + dy * 12, dx, dy, mia: false});
                    e.disparo = Math.max(1.2, 3.5 - m.nivel * .3) + Math.random() * 2.5;
                }
            });
            for (const b of s.balas) {
                if (this.bala(m, b, dt)) { b.fuera = true; if (m.estado !== 'jugando') return; continue; }
                if (b.mia) {
                    const e = s.enemigos.find(e => b.x > e.x && b.x < e.x + T && b.y > e.y && b.y < e.y + T);
                    if (e) { b.fuera = true; s.chispas.push({x: e.x + T / 2, y: e.y + T / 2, t: m.t, grande: true}); m.responder(e.k); return; }
                } else if (m.t > s.invencible && b.x > yo.x && b.x < yo.x + T && b.y > yo.y && b.y < yo.y + T) {
                    b.fuera = true; m.perderVida('¡LE DIERON!'); return;
                }
            }
            s.balas = s.balas.filter(b => !b.fuera);
        },
        dibujar(m, ctx) {
            for (let x = 0; x < W; x += 20) for (let y = 0; y < ALTO; y += 20) {
                ctx.fillStyle = ((x + y) / 20) % 2 ? '#24402a' : '#203a25'; ctx.fillRect(x, Y0 + y, 20, 20);
            }
            const s = m.s; if (!s) return;
            ACERO.forEach(([x, y, w, h]) => {
                ctx.fillStyle = '#adb5bd'; ctx.fillRect(x, Y0 + y, w, h);
                ctx.fillStyle = '#868e96'; for (let i = x; i < x + w; i += 10) for (let j = y; j < y + h; j += 10) ctx.fillRect(i + 3, Y0 + j + 3, 4, 4);
            });
            s.ladrillos.forEach(l => {
                ctx.fillStyle = '#b5651d'; ctx.fillRect(l.x, Y0 + l.y, L, L);
                ctx.fillStyle = '#8b4513'; ctx.fillRect(l.x, Y0 + l.y + 4, L, 1); ctx.fillRect(l.x + ((l.y / L) % 2 ? 2 : 6), Y0 + l.y, 1, 4);
                ctx.fillRect(l.x + ((l.y / L) % 2 ? 6 : 2), Y0 + l.y + 5, 1, 5);
            });
            dibujarInsignia(ctx, m, m.t - s.golpeBase < .6);
            const OSCURO = ['#a61e1e', '#1864ab', '#b08900', '#2b8a3e'];
            s.enemigos.forEach(e => dibujarTanque(ctx, e, m.COLORES[e.k], OSCURO[e.k], m, e.k));
            if (m.t > s.invencible || Math.floor(m.t * 10) % 2) dibujarTanque(ctx, s.yo, '#dee2e6', '#868e96', m);
            s.balas.forEach(b => {
                ctx.fillStyle = b.mia ? '#ffd43b' : '#ff6b6b'; ctx.fillRect(b.x - 2, Y0 + b.y - 2, 4, 4);
                ctx.fillStyle = 'rgba(255,255,255,.6)'; ctx.fillRect(b.x - 1 - b.dx * 4, Y0 + b.y - 1 - b.dy * 4, 2, 2);
            });
            s.chispas = s.chispas.filter(c => m.t - c.t < (c.grande ? .6 : .25));
            s.chispas.forEach(c => {
                const r = (m.t - c.t) * (c.grande ? 60 : 30);
                ctx.strokeStyle = c.grande ? '#ffa94d' : '#ffe066'; ctx.lineWidth = c.grande ? 3 : 2;
                ctx.beginPath(); ctx.arc(c.x, Y0 + c.y, r, 0, Math.PI * 2); ctx.stroke();
            });
        },
    });
})();
