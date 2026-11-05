/* Sala de escape: cada respuesta abre un candado de la puerta. Hay un reloj para toda la sala:
 * una respuesta mala no quita vidas, pero resta 15 segundos. */
(function () {
    'use strict';
    const Y0 = 50, W = 480, CASTIGO = 15;

    function botones(m) {
        const n = m.opciones.length, w = 150, h = 34;
        return m.opciones.map((o, k) => ({k, x: 30 + (k % 2) * (w + 14), y: Y0 + 120 + Math.floor(k / 2) * (h + 12), w, h}));
    }

    Gamificacion.registrar('escape', {
        nombre: 'Sala de escape',
        instrucciones: 'Cada respuesta correcta abre un candado. Abra todos antes de que se acabe el tiempo. Una respuesta mala resta 15 segundos.',
        sinVidas: true,
        fondo: '#2b2118',
        nuevaPregunta(m) {
            if (!m.sala) {
                const total = Math.max(60, m.segundos * m.total);
                m.sala = {tiempo: total, total, candados: Array(m.total).fill(null)};
            }
            m.s = {botones: botones(m), elegido: null};
        },
        elegir(m, k) {
            const s = m.s; if (s.elegido !== null) return;
            s.elegido = k;
            const bien = m.opciones[k].correcta;
            m.sala.candados[m.indice] = bien ? 'abierto' : 'forzado';
            if (!bien) m.sala.tiempo = Math.max(0, m.sala.tiempo - CASTIGO);
            m.responder(k);
        },
        alTocar(m, x, y) {
            const b = m.s.botones.find(b => x > b.x && x < b.x + b.w && y > b.y && y < b.y + b.h);
            if (b) this.elegir(m, b.k);
        },
        alTecla(m, t, crudo) {
            const k = 'ABCD'.indexOf(String(crudo || '').toUpperCase());
            if (k >= 0 && k < m.opciones.length) this.elegir(m, k);
        },
        actualizar(m, dt) {
            m.sala.tiempo -= dt;
            if (m.sala.tiempo <= 0) {
                m.sala.tiempo = 0;
                for (let i = m.indice; i < m.total; i++) m.respuestas.push({i: m.preguntas[i].i !== undefined ? m.preguntas[i].i : i, opcion: null});
                m.vidas = 0; m.aviso('¡SE ACABÓ EL TIEMPO!', '#ff6b6b', 1.5);
                m.estado = 'pausa'; setTimeout(() => m.terminar(), 1500);
            }
        },
        dibujar(m, ctx) {
            // Pared de ladrillo y piso de madera
            for (let y = 0; y < 200; y += 14) for (let x = -(y % 28 ? 14 : 0); x < W; x += 28) {
                ctx.fillStyle = '#6b4226'; ctx.fillRect(x + 1, Y0 + y + 1, 26, 12);
            }
            ctx.fillStyle = '#8b5a2b'; ctx.fillRect(0, Y0 + 200, W, 60);
            ctx.fillStyle = '#7a4e25'; for (let x = 0; x < W; x += 40) ctx.fillRect(x, Y0 + 200, 2, 60);
            const sala = m.sala; if (!sala) return;
            // La puerta con un candado por pregunta
            const px = 360, py = Y0 + 40, pw = 90, ph = 160;
            const todo = sala.candados.every(c => c);
            ctx.fillStyle = todo ? '#ffe066' : '#3d2b1f'; ctx.fillRect(px, py, pw, ph);
            ctx.strokeStyle = '#1f150e'; ctx.lineWidth = 4; ctx.strokeRect(px, py, pw, ph);
            const porFila = 3, tam = 14, n = sala.candados.length, mostrar = Math.min(n, 18);
            for (let i = 0; i < mostrar; i++) {
                const cx = px + 15 + (i % porFila) * 26, cy = py + 14 + Math.floor(i / porFila) * 24, c = sala.candados[i];
                ctx.fillStyle = c === 'abierto' ? '#69db7c' : c === 'forzado' ? '#ff6b6b' : (i === m.indice ? '#ffd43b' : '#adb5bd');
                ctx.fillRect(cx, cy + 5, tam, tam - 4);
                ctx.strokeStyle = ctx.fillStyle; ctx.lineWidth = 2; ctx.beginPath();
                ctx.arc(cx + tam / 2, cy + 5 - (c === 'abierto' ? 3 : 0), 4, Math.PI, 0); ctx.stroke();
            }
            if (n > mostrar) m.texto(`+${n - mostrar}`, px + pw / 2, py + ph - 18, {tam: 8, alinear: 'center'});
            // Reloj de la sala
            const seg = Math.ceil(sala.tiempo), mm = Math.floor(seg / 60), ss = String(seg % 60).padStart(2, '0');
            ctx.fillStyle = '#111'; ctx.fillRect(30, Y0 + 20, 120, 34);
            m.texto(`${mm}:${ss}`, 90, Y0 + 30, {tam: 14, alinear: 'center', color: sala.tiempo < 20 ? '#ff6b6b' : '#69db7c'});
            m.texto('CANDADO ' + Math.min(m.indice + 1, m.total), 30, Y0 + 70, {tam: 8, color: '#ffd43b'});
            m.texto('Escoja la respuesta:', 30, Y0 + 95, {tam: 8, color: '#eee'});
            // Botones de respuesta
            (m.s ? m.s.botones : []).forEach(b => {
                const escogido = m.s.elegido === b.k, bien = m.opciones[b.k] && m.opciones[b.k].correcta;
                ctx.fillStyle = escogido ? (bien ? '#2f9e44' : '#c92a2a') : '#1f150e'; ctx.fillRect(b.x, b.y, b.w, b.h);
                ctx.strokeStyle = m.COLORES[b.k]; ctx.lineWidth = 2; ctx.strokeRect(b.x + 1, b.y + 1, b.w - 2, b.h - 2);
                m.etiqueta(b.k, b.x + 16, b.y + b.h / 2, 9);
                ctx.font = `7px ${m.FUENTE}`;
                let t = m.opciones[b.k] ? m.opciones[b.k].texto : '';
                while (ctx.measureText(t).width > b.w - 36 && t.length > 3) t = t.slice(0, -2);
                m.texto(t, b.x + 30, b.y + b.h / 2 - 3, {tam: 7});
            });
        },
    });
})();
