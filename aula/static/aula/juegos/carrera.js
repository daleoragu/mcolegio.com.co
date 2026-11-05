/* Carrera de carriles: se acerca una barrera con un solo hueco, el del carril de la respuesta correcta.
 * Cámbiese a ese carril (flechas, toque o A–D) antes de que la barrera llegue. Con cada nivel va más rápido. */
(function () {
    'use strict';
    const Y0 = 50, W = 480, VIA = {x: 100, w: 280}, CARRO_Y = Y0 + 220;

    Gamificacion.registrar('carrera', {
        nombre: 'Carrera de carriles',
        instrucciones: 'Llévese el carro al carril de la respuesta correcta antes de que llegue la barrera: es el único con hueco.',
        conReloj: true,
        controles: 'cruceta',
        fondo: '#495057',
        nuevaPregunta(m) {
            m.s = {carril: Math.floor(m.opciones.length / 2), x: null, choque: 0, paso: false, rayas: m.s ? m.s.rayas : 0};
        },
        ancho(m) { return VIA.w / m.opciones.length; },
        ir(m, c) { if (m.s.paso || m.s.choque) return; m.s.carril = Math.max(0, Math.min(m.opciones.length - 1, c)); m.sonidos.toque(); },
        alTecla(m, t, crudo) {
            const k = 'ABCD'.indexOf(String(crudo || '').toUpperCase());
            if (k >= 0 && !['a', 'd'].includes(crudo)) return this.ir(m, k);
            if (t === 'izquierda') this.ir(m, m.s.carril - 1);
            if (t === 'derecha') this.ir(m, m.s.carril + 1);
        },
        alTocar(m, x) { if (x > VIA.x && x < VIA.x + VIA.w) this.ir(m, Math.floor((x - VIA.x) / this.ancho(m))); },
        alAcabarReloj(m) {
            const s = m.s;
            if (s.paso || s.choque) return;
            if (m.opciones[s.carril].correcta) s.paso = true; else s.choque = m.t;
            m.responder(s.carril);
        },
        actualizar(m, dt) {
            const s = m.s, destino = VIA.x + (s.carril + .5) * this.ancho(m);
            s.x = s.x === null ? destino : s.x + (destino - s.x) * Math.min(1, dt * 10);
            s.rayas = (s.rayas + dt * (160 + m.nivel * 25)) % 40;
        },
        actualizarEnPausa(m, dt) { if (m.s && m.s.paso) m.s.rayas = (m.s.rayas + dt * 220) % 40; },
        dibujar(m, ctx) {
            ctx.fillStyle = '#2b8a3e'; ctx.fillRect(0, Y0, W, 260);
            ctx.fillStyle = '#343a40'; ctx.fillRect(VIA.x, Y0, VIA.w, 260);
            ctx.fillStyle = '#f8f9fa'; ctx.fillRect(VIA.x - 4, Y0, 4, 260); ctx.fillRect(VIA.x + VIA.w, Y0, 4, 260);
            const s = m.s; if (!s) return;
            const n = m.opciones.length, aw = this.ancho(m);
            ctx.fillStyle = '#ffd43b';
            for (let c = 1; c < n; c++) for (let y = -40 + s.rayas; y < 260; y += 40) ctx.fillRect(VIA.x + c * aw - 2, Y0 + y, 4, 20);
            // La barrera baja a medida que se acaba el tiempo
            const total = m.tiempoDeLaPregunta(), frac = 1 - Math.max(0, m.reloj) / total;
            const by = Y0 + 10 + frac * (CARRO_Y - Y0 - 30) + (s.paso ? 60 : 0);
            const correcta = m.opciones.findIndex(o => o.correcta);
            for (let c = 0; c < n; c++) {
                const x = VIA.x + c * aw;
                const hueco = s.paso || s.choque ? c === correcta : false;
                if (!hueco) {
                    for (let i = 0; i < aw; i += 16) { ctx.fillStyle = (i / 16) % 2 ? '#f8f9fa' : '#e03131'; ctx.fillRect(x + i, by, Math.min(16, aw - i), 12); }
                }
                m.etiqueta(c, x + aw / 2, Y0 + 14, 9);
            }
            // El carro
            const cx = s.x || VIA.x + VIA.w / 2, sacudida = s.choque ? Math.sin(m.t * 60) * 3 : 0;
            ctx.fillStyle = '#4dabf7'; ctx.fillRect(cx - 11 + sacudida, CARRO_Y, 22, 34);
            ctx.fillStyle = '#1c7ed6'; ctx.fillRect(cx - 8 + sacudida, CARRO_Y + 6, 16, 9);
            ctx.fillStyle = '#212529'; ctx.fillRect(cx - 14 + sacudida, CARRO_Y + 4, 3, 8); ctx.fillRect(cx + 11 + sacudida, CARRO_Y + 4, 3, 8);
            ctx.fillRect(cx - 14 + sacudida, CARRO_Y + 22, 3, 8); ctx.fillRect(cx + 11 + sacudida, CARRO_Y + 22, 3, 8);
            if (s.choque) m.texto('¡CRASH!', cx, CARRO_Y - 18, {tam: 10, alinear: 'center', color: '#ff6b6b'});
        },
    });
})();
