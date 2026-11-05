/* Puente seguro: cada fila del puente es una pregunta. Párese en la baldosa de la respuesta correcta
 * antes de que se acabe el tiempo: al llegar a cero, las demás baldosas se rompen. */
(function () {
    'use strict';
    const Y0 = 50, W = 480, ANCHO_PUENTE = 300, X_PUENTE = (480 - 300) / 2;

    Gamificacion.registrar('puente', {
        nombre: 'Puente seguro',
        instrucciones: 'Muévase con las flechas o toque una baldosa. Cuando el tiempo llegue a cero, solo la baldosa correcta aguanta.',
        conReloj: true,
        fondo: '#0c1a2b',
        nuevaPregunta(m, repetir) {
            m.s = {col: null, x: X_PUENTE + ANCHO_PUENTE / 2, rotas: [], cae: false, ok: null, avance: m.indice};
        },
        ancho(m) { return ANCHO_PUENTE / m.opciones.length; },
        ir(m, col) {
            if (m.s.cae || m.s.ok !== null) return;
            m.s.col = Math.max(0, Math.min(m.opciones.length - 1, col));
            m.sonidos.toque();
        },
        alTecla(m, t, crudo) {
            const k = 'ABCD'.indexOf(String(crudo || '').toUpperCase());
            if (k >= 0 && String(crudo).length === 1 && !['a', 'd'].includes(crudo)) return this.ir(m, k);
            if (t === 'izquierda') this.ir(m, m.s.col === null ? 0 : m.s.col - 1);
            if (t === 'derecha') this.ir(m, m.s.col === null ? m.opciones.length - 1 : m.s.col + 1);
        },
        alTocar(m, x, y) {
            if (y > Y0 + 95 && y < Y0 + 175 && x > X_PUENTE && x < X_PUENTE + ANCHO_PUENTE) this.ir(m, Math.floor((x - X_PUENTE) / this.ancho(m)));
        },
        alAcabarReloj(m) {
            const s = m.s;
            if (s.ok !== null) return;
            const col = s.col;
            const bien = col !== null && m.opciones[col].correcta;
            m.opciones.forEach((o, k) => { if (!o.correcta) s.rotas.push(k); });
            s.ok = bien; s.cae = !bien;
            m.responder(col);
        },
        actualizar(m, dt) {
            const s = m.s;
            const destino = s.col === null ? X_PUENTE + ANCHO_PUENTE / 2 : X_PUENTE + (s.col + .5) * this.ancho(m);
            s.x += (destino - s.x) * Math.min(1, dt * 12);
        },
        actualizarEnPausa(m, dt) { if (m.s) m.s.caida = (m.s.caida || 0) + dt; },
        dibujar(m, ctx) {
            // Agua al fondo
            for (let y = 0; y < 260; y += 8) { ctx.fillStyle = y % 16 ? '#0f2742' : '#12304f'; ctx.fillRect(0, Y0 + y, W, 8); }
            const s = m.s; if (!s) return;
            const n = m.opciones.length, aw = ANCHO_PUENTE / n;
            // Filas que vienen (arriba, más pequeñas) y las ya pasadas (abajo)
            for (let i = 1; i <= 3; i++) {
                if (m.indice + i >= m.total) break;
                const y = Y0 + 95 - i * 30, esc = 1 - i * .12, w = ANCHO_PUENTE * esc, x = (W - w) / 2;
                ctx.fillStyle = `rgba(200,220,255,${.35 - i * .08})`; ctx.fillRect(x, y, w, 20);
            }
            ctx.fillStyle = '#495057'; ctx.fillRect(X_PUENTE - 10, Y0 + 95, 6, 80); ctx.fillRect(X_PUENTE + ANCHO_PUENTE + 4, Y0 + 95, 6, 80);
            // Fila actual
            for (let k = 0; k < n; k++) {
                const x = X_PUENTE + k * aw + 3, y = Y0 + 100;
                if (s.rotas.includes(k)) {
                    const c = (s.caida || 0) * 180;
                    ctx.fillStyle = 'rgba(180,220,255,.5)';
                    for (let i = 0; i < 6; i++) ctx.fillRect(x + (i % 3) * aw / 3, y + 10 + c * (1 + i * .3) + Math.floor(i / 3) * 30, aw / 3 - 4, 12);
                    continue;
                }
                const g = ctx.createLinearGradient(x, y, x, y + 70);
                g.addColorStop(0, s.ok && m.opciones[k].correcta ? '#b2f2bb' : '#d0ebff'); g.addColorStop(1, s.ok && m.opciones[k].correcta ? '#40c057' : '#74c0fc');
                ctx.fillStyle = g; ctx.fillRect(x, y, aw - 6, 70);
                ctx.strokeStyle = 'rgba(255,255,255,.7)'; ctx.lineWidth = 1; ctx.strokeRect(x + .5, y + .5, aw - 7, 69);
                m.etiqueta(k, x + (aw - 6) / 2, y + 35, 11);
            }
            // Plataforma de espera y el jugador
            ctx.fillStyle = '#868e96'; ctx.fillRect(X_PUENTE, Y0 + 190, ANCHO_PUENTE, 26);
            m.texto(`FILA ${m.indice + 1} DE ${m.total}`, W / 2, Y0 + 225, {tam: 8, alinear: 'center', color: '#adb5bd'});
            const enBaldosa = s.col !== null;
            let px = s.x - 7, py = Y0 + (enBaldosa ? 120 : 192);
            if (s.cae) py += (s.caida || 0) * 300;
            ctx.fillStyle = '#ff6b6b'; ctx.fillRect(px, py, 14, 18);
            ctx.fillStyle = '#ffe3e3'; ctx.fillRect(px + 2, py - 10, 10, 10);
            ctx.fillStyle = '#111'; ctx.fillRect(px + 4, py - 6, 2, 2); ctx.fillRect(px + 8, py - 6, 2, 2);
            if (!enBaldosa && s.ok === null) m.texto('¡PÁRESE EN UNA BALDOSA!', W / 2, Y0 + 70, {tam: 8, alinear: 'center', color: '#ffd43b'});
            if (m.reloj > 0 && s.ok === null) m.texto(String(Math.ceil(m.reloj)), W - 30, Y0 + 12, {tam: 18, alinear: 'center', color: m.reloj < 4 ? '#ff6b6b' : '#fff'});
        },
    });
})();
