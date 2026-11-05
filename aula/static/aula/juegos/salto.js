/* Salto al vacío: salte a la plataforma con la respuesta correcta. Las otras se derrumban. */
(function () {
    'use strict';
    const Y0 = 50, W = 480;

    Gamificacion.registrar('salto', {
        nombre: 'Salto al vacío',
        instrucciones: 'Toque la plataforma con la respuesta correcta (o presione A, B, C o D) para saltar. Si escoge mal, la plataforma se derrumba.',
        conReloj: true,
        fondo: '#2b1d3a',
        nuevaPregunta(m) {
            const n = m.opciones.length;
            // Con cada nivel las plataformas son más angostas.
            const ancho = Math.max(44, 74 - m.nivel * 5);
            const alturas = [70, 120, 170, 95, 145].sort(() => Math.random() - .5);
            m.s = {
                yo: {x: 40, y: 200, vx: 0, vy: 0, estado: 'quieto'},
                plataformas: Array.from({length: n}, (_, k) => ({k, x: 140 + k * (300 / n) + 10, y: alturas[k], w: ancho, cae: 0})),
                elegida: null,
            };
        },
        saltar(m, k) {
            const s = m.s;
            if (s.yo.estado !== 'quieto') return;
            const p = s.plataformas.find(p => p.k === k); if (!p) return;
            s.elegida = p; s.yo.estado = 'saltando';
            const destinoX = p.x + p.w / 2 - 6, destinoY = p.y - 16, tiempo = 0.75;
            s.yo.vx = (destinoX - s.yo.x) / tiempo;
            s.yo.vy = (destinoY - s.yo.y - 0.5 * 600 * tiempo * tiempo) / tiempo;
            s.yo.aterriza = m.t + tiempo; s.yo.dx = destinoX; s.yo.dy = destinoY;
            m.sonidos.toque();
        },
        alTocar(m, x, y) {
            const p = m.s.plataformas.find(p => x > p.x - 6 && x < p.x + p.w + 6 && y > Y0 + p.y - 30 && y < Y0 + p.y + 20);
            if (p) this.saltar(m, p.k);
        },
        alTecla(m, t, crudo) {
            const k = 'ABCD'.indexOf(String(crudo || '').toUpperCase());
            if (k >= 0) this.saltar(m, k);
        },
        alAcabarReloj(m) { if (m.s.yo.estado === 'quieto') m.responder(null); },
        actualizar(m, dt) {
            const s = m.s, yo = s.yo;
            if (yo.estado === 'saltando') {
                yo.x += yo.vx * dt; yo.y += yo.vy * dt; yo.vy += 600 * dt;
                if (m.t >= yo.aterriza) {
                    yo.x = yo.dx; yo.y = yo.dy;
                    if (m.opciones[s.elegida.k].correcta) { yo.estado = 'arriba'; m.responder(s.elegida.k); }
                    else { yo.estado = 'cae'; s.elegida.cae = m.t; yo.vy = 0; m.responder(s.elegida.k); }
                }
            }
        },
        actualizarEnPausa(m, dt) {
            const s = m.s;
            if (s && s.yo.estado === 'cae') { s.yo.vy += 600 * dt; s.yo.y += s.yo.vy * dt; }
        },
        dibujar(m, ctx) {
            // Cielo nocturno con estrellas y el vacío abajo
            const g = ctx.createLinearGradient(0, Y0, 0, Y0 + 260); g.addColorStop(0, '#2b1d3a'); g.addColorStop(1, '#000');
            ctx.fillStyle = g; ctx.fillRect(0, Y0, W, 260);
            ctx.fillStyle = '#fff';
            for (let i = 0; i < 30; i++) ctx.fillRect((i * 97) % W, Y0 + (i * 53) % 150, 2, 2);
            const s = m.s; if (!s) return;
            // Punto de partida
            ctx.fillStyle = '#868e96'; ctx.fillRect(0, Y0 + 216, 80, 44); ctx.fillStyle = '#adb5bd'; ctx.fillRect(0, Y0 + 216, 80, 5);
            s.plataformas.forEach(p => {
                const caida = p.cae ? (m.t - p.cae) * 260 : 0;
                ctx.fillStyle = p.cae ? '#c92a2a' : m.COLORES[p.k];
                if (p.cae) { for (let i = 0; i < 5; i++) ctx.fillRect(p.x + i * p.w / 5, Y0 + p.y + caida * (1 + i * .2), p.w / 5 - 2, 10); }
                else { ctx.fillRect(p.x, Y0 + p.y, p.w, 10); ctx.fillStyle = 'rgba(0,0,0,.3)'; ctx.fillRect(p.x, Y0 + p.y + 7, p.w, 3); }
                if (!p.cae) m.etiqueta(p.k, p.x + p.w / 2, Y0 + p.y + 24, 9);
            });
            // El saltarín: un cubito con antenas
            const yo = s.yo, x = yo.x, y = Y0 + yo.y;
            ctx.fillStyle = '#ffd43b'; ctx.fillRect(x, y, 12, 14);
            ctx.fillStyle = '#111'; ctx.fillRect(x + 3, y + 4, 2, 2); ctx.fillRect(x + 7, y + 4, 2, 2);
            ctx.fillStyle = '#ffd43b'; ctx.fillRect(x + 2, y - 4, 2, 4); ctx.fillRect(x + 8, y - 4, 2, 4);
        },
    });
})();
