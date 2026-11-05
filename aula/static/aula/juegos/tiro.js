/* Tiro al vuelo: pasan aves con las opciones; toque (o haga clic en) la de la respuesta correcta antes de que se acabe el tiempo. */
(function () {
    'use strict';
    const Y0 = 50, W = 480;

    function ave(k, nivel) {
        const izq = Math.random() < .5;
        return {k, x: izq ? -30 - Math.random() * 120 : W + 30 + Math.random() * 120, y: 30 + Math.random() * 150,
                vx: (izq ? 1 : -1) * (45 + nivel * 12 + Math.random() * 25), fase: Math.random() * 6, amp: 10 + Math.random() * 18,
                cae: false, vy: 0};
    }

    Gamificacion.registrar('tiro', {
        nombre: 'Tiro al vuelo',
        instrucciones: 'Toque o haga clic en el ave que lleva la respuesta correcta. También puede presionar A, B, C o D.',
        conReloj: true,
        fondo: '#74c0fc',
        // Barra lateral: el ave con la letra de su opción
        icono(ctx, k, tam) {
            const e = tam / 28;
            ctx.fillStyle = '#5c3d2e'; ctx.fillRect(5 * e, 13 * e, 16 * e, 8 * e); ctx.fillRect(19 * e, 9 * e, 6 * e, 6 * e);
            ctx.fillStyle = '#7a5442'; ctx.fillRect(8 * e, 8 * e, 9 * e, 5 * e);
            ctx.fillStyle = '#f59f00'; ctx.fillRect(25 * e, 11 * e, 3 * e, 2 * e);
            ctx.fillStyle = Gamificacion.COLORES[k]; ctx.beginPath(); ctx.arc(8 * e, 22 * e, 6 * e, 0, Math.PI * 2); ctx.fill();
            ctx.fillStyle = '#111'; ctx.font = `bold ${Math.round(7 * e)}px sans-serif`; ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
            ctx.fillText(Gamificacion.LETRAS[k], 8 * e, 22.5 * e);
        },
        nuevaPregunta(m) { m.s = {aves: m.opciones.map((_, k) => ave(k, m.nivel)), disparos: []}; },
        alTocar(m, x, y) {
            m.s.disparos.push({x, y, t: m.t}); m.sonidos.toque();
            const a = m.s.aves.find(a => !a.cae && Math.hypot(a.x - x, Y0 + a.y - y) < 20);
            if (a) { a.cae = true; a.vy = -60; setTimeout(() => m.responder(a.k), 350); }
        },
        alTecla(m, t, crudo) {
            const k = 'ABCD'.indexOf(String(crudo || '').toUpperCase());
            const a = k >= 0 && m.s.aves.find(a => a.k === k && !a.cae);
            if (a) this.alTocar(m, a.x, Y0 + a.y);
        },
        actualizar(m, dt) {
            m.s.aves.forEach(a => {
                if (a.cae) { a.vy += 400 * dt; a.y += a.vy * dt; return; }
                a.x += a.vx * dt; a.fase += dt * 4;
                if (a.vx > 0 && a.x > W + 40) a.x = -40;
                if (a.vx < 0 && a.x < -40) a.x = W + 40;
            });
        },
        actualizarEnPausa(m, dt) { this.actualizar(m, dt); },
        dibujar(m, ctx) {
            // Cielo, nubes y pasto
            ctx.fillStyle = '#a5d8ff'; ctx.fillRect(0, Y0, W, 260);
            ctx.fillStyle = '#fff';
            [[60, 40], [260, 70], [400, 30]].forEach(([x, y], i) => {
                const dx = (x + m.t * 6 * (i + 1)) % (W + 80) - 40;
                ctx.fillRect(dx, Y0 + y, 50, 10); ctx.fillRect(dx + 10, Y0 + y - 8, 30, 10);
            });
            ctx.fillStyle = '#2f9e44'; ctx.fillRect(0, Y0 + 220, W, 40);
            ctx.fillStyle = '#2b8a3e'; for (let x = 0; x < W; x += 12) ctx.fillRect(x, Y0 + 214 + (x % 24 ? 0 : 3), 6, 8);
            const s = m.s; if (!s) return;
            s.aves.forEach(a => {
                const x = a.x, y = Y0 + a.y + (a.cae ? 0 : Math.sin(a.fase) * a.amp), alaArriba = Math.floor(a.fase * 2) % 2 === 0;
                const dir = a.vx > 0 ? 1 : -1;
                ctx.fillStyle = '#5c3d2e'; ctx.fillRect(x - 10, y - 4, 20, 9);                    // cuerpo
                ctx.fillStyle = '#7a5442'; ctx.fillRect(x - 6, y + (alaArriba ? -10 : 3), 12, 6);   // ala
                ctx.fillStyle = '#5c3d2e'; ctx.fillRect(x + dir * 9, y - 8, 7, 7);                  // cabeza
                ctx.fillStyle = '#f59f00'; ctx.fillRect(x + dir * 15, y - 6, 4 * dir, 3);           // pico
                if (!a.cae) m.etiqueta(a.k, x, y - 18, 8);
            });
            s.disparos = s.disparos.filter(d => m.t - d.t < .25);
            s.disparos.forEach(d => { ctx.strokeStyle = '#fff'; ctx.lineWidth = 2; ctx.beginPath(); ctx.arc(d.x, d.y, 10 + (m.t - d.t) * 40, 0, Math.PI * 2); ctx.stroke(); });
            if (m.puntero) {
                ctx.strokeStyle = '#e03131'; ctx.lineWidth = 2; const {x, y} = m.puntero;
                ctx.beginPath(); ctx.arc(x, y, 9, 0, Math.PI * 2); ctx.moveTo(x - 14, y); ctx.lineTo(x + 14, y); ctx.moveTo(x, y - 14); ctx.lineTo(x, y + 14); ctx.stroke();
            }
        },
    });
})();
