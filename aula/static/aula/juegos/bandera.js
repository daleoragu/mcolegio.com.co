/* Captura la bandera: en el campo rival hay una bandera por opción. Tome la de la respuesta correcta y
 * tráigala hasta su base (a la izquierda). Las otras son trampas. Los guardias patrullan el campo rival:
 * si lo tocan, pierde una vida. En su mitad está a salvo. */
(function () {
    'use strict';
    const Y0 = 50, W = 480, ALTO = 260, MITAD = 240, BASE_X = 54, R = 7;

    function guardia(i, n, nivel) {
        const x = 280 + (i % 3) * 50 + Math.random() * 20;
        return {x, y: 20 + Math.random() * (ALTO - 40), vy: (Math.random() < .5 ? -1 : 1) * (40 + nivel * 10),
                vx: (Math.random() < .5 ? -1 : 1) * (10 + nivel * 4), mira: 0};
    }

    Gamificacion.registrar('bandera', {
        nombre: 'Captura la bandera',
        instrucciones: 'Muévase con las flechas. Tome la bandera de la respuesta correcta en el campo rival y tráigala a su base sin que lo atrapen los guardias.',
        controles: 'cruceta',
        fondo: '#2f9e44',
        icono(ctx, k, tam) {
            const e = tam / 28;
            ctx.fillStyle = '#495057'; ctx.fillRect(8 * e, 4 * e, 2 * e, 22 * e); ctx.fillRect(4 * e, 24 * e, 10 * e, 3 * e);
            ctx.fillStyle = Gamificacion.COLORES[k]; ctx.beginPath(); ctx.moveTo(10 * e, 4 * e); ctx.lineTo(26 * e, 9 * e); ctx.lineTo(10 * e, 14 * e); ctx.fill();
            ctx.fillStyle = '#111'; ctx.font = `bold ${Math.round(tam * .3)}px sans-serif`; ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
            ctx.fillText(Gamificacion.LETRAS[k], 16 * e, 9.5 * e);
        },
        nuevaPregunta(m, repetir) {
            const n = m.opciones.length, paso = ALTO / (n + 1);
            m.s = {
                yo: {x: 30, y: ALTO / 2, vel: 95, lleva: null},
                banderas: Array.from({length: n}, (_, k) => ({k, x: 440, y: paso * (k + 1), tomada: false})),
                guardias: Array.from({length: Math.min(5, 1 + m.nivel)}, (_, i) => guardia(i, n, m.nivel)),
                invencible: m.t + 1.5,
            };
        },
        actualizar(m, dt) {
            const s = m.s, yo = s.yo;
            let dx = 0, dy = 0;
            if (m.teclas.has('izquierda')) dx -= 1; if (m.teclas.has('derecha')) dx += 1;
            if (m.teclas.has('arriba')) dy -= 1; if (m.teclas.has('abajo')) dy += 1;
            if (dx || dy) {
                const d = Math.hypot(dx, dy), vel = yo.lleva !== null ? yo.vel * .85 : yo.vel;   // con la bandera va un poco más lento
                yo.x = Math.max(R, Math.min(W - R, yo.x + dx / d * vel * dt));
                yo.y = Math.max(R, Math.min(ALTO - R, yo.y + dy / d * vel * dt));
            }
            s.guardias.forEach(g => {
                g.y += g.vy * dt; g.x += g.vx * dt;
                if (g.y < 10 || g.y > ALTO - 10) g.vy *= -1;
                if (g.x < MITAD + 15 || g.x > W - 50) g.vx *= -1;
                // Si lo ve cerca, lo persigue un poco
                const dist = Math.hypot(yo.x - g.x, yo.y - g.y);
                g.mira = yo.x > MITAD && dist < 70;
                if (g.mira) { g.x += (yo.x - g.x) / dist * 30 * dt; g.y += (yo.y - g.y) / dist * 30 * dt; }
            });
            // Tomar una bandera
            if (yo.lleva === null) {
                const b = s.banderas.find(b => !b.tomada && Math.hypot(yo.x - b.x, yo.y - b.y) < 16);
                if (b) {
                    if (!m.opciones[b.k].correcta) { m.responder(b.k); return; }      // trampa
                    b.tomada = true; yo.lleva = b.k; m.sonidos.toque();
                }
            } else if (yo.x < BASE_X) { m.responder(yo.lleva); return; }            // ¡llegó a la base!
            // Atrapado
            if (m.t > s.invencible && yo.x > MITAD && s.guardias.some(g => Math.hypot(yo.x - g.x, yo.y - g.y) < 13)) {
                m.perderVida(yo.lleva !== null ? '¡LE QUITARON LA BANDERA!' : '¡LO ATRAPARON!');
            }
        },
        dibujar(m, ctx) {
            ctx.fillStyle = '#2b8a3e'; ctx.fillRect(0, Y0, MITAD, ALTO);
            ctx.fillStyle = '#5c940d'; ctx.fillRect(MITAD, Y0, W - MITAD, ALTO);
            for (let x = 0; x < W; x += 32) for (let y = 0; y < ALTO; y += 32) { ctx.fillStyle = 'rgba(255,255,255,.05)'; ctx.fillRect(x + ((y / 32) % 2) * 16, Y0 + y, 16, 16); }
            ctx.strokeStyle = '#fff'; ctx.lineWidth = 2; ctx.setLineDash([6, 6]);
            ctx.beginPath(); ctx.moveTo(MITAD, Y0); ctx.lineTo(MITAD, Y0 + ALTO); ctx.stroke(); ctx.setLineDash([]);
            // Base propia
            ctx.fillStyle = 'rgba(77,171,247,.35)'; ctx.fillRect(0, Y0, BASE_X, ALTO);
            m.texto('BASE', BASE_X / 2, Y0 + 6, {tam: 7, alinear: 'center', color: '#fff'});
            const s = m.s; if (!s) return;
            // Banderas
            s.banderas.forEach(b => {
                if (b.tomada) return;
                const x = b.x, y = Y0 + b.y, ondea = Math.sin(m.t * 6 + b.k) * 2;
                ctx.fillStyle = '#495057'; ctx.fillRect(x - 1, y - 16, 2, 22); ctx.fillRect(x - 6, y + 5, 12, 3);
                ctx.fillStyle = m.COLORES[b.k]; ctx.beginPath(); ctx.moveTo(x + 1, y - 16); ctx.lineTo(x + 18, y - 11 + ondea); ctx.lineTo(x + 1, y - 6); ctx.fill();
                m.etiqueta(b.k, x - 14, y - 8, 8);
            });
            // Guardias
            s.guardias.forEach(g => {
                const x = g.x, y = Y0 + g.y;
                ctx.fillStyle = '#c92a2a'; ctx.fillRect(x - 6, y - 6, 12, 14);
                ctx.fillStyle = '#ffc9a3'; ctx.fillRect(x - 4, y - 12, 8, 7);
                ctx.fillStyle = '#212529'; ctx.fillRect(x - 5, y - 14, 10, 3);
                if (g.mira) m.texto('!', x, y - 26, {tam: 9, alinear: 'center', color: '#ffd43b'});
            });
            // Jugador (con la bandera si la lleva)
            const yo = s.yo, x = yo.x, y = Y0 + yo.y;
            if (m.t > s.invencible || Math.floor(m.t * 10) % 2) {
                ctx.fillStyle = '#1c7ed6'; ctx.fillRect(x - 6, y - 6, 12, 14);
                ctx.fillStyle = '#ffc9a3'; ctx.fillRect(x - 4, y - 12, 8, 7);
                ctx.fillStyle = '#ffd43b'; ctx.fillRect(x - 5, y - 14, 10, 3);
                if (yo.lleva !== null) {
                    ctx.fillStyle = '#495057'; ctx.fillRect(x + 7, y - 20, 2, 22);
                    ctx.fillStyle = m.COLORES[yo.lleva]; ctx.beginPath(); ctx.moveTo(x + 9, y - 20); ctx.lineTo(x + 22, y - 15); ctx.lineTo(x + 9, y - 10); ctx.fill();
                }
            }
            if (yo.lleva !== null) m.texto('¡A SU BASE!', MITAD / 2, Y0 + 8, {tam: 8, alinear: 'center', color: '#ffd43b'});
        },
    });
})();
