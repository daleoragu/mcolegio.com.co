/* Baloncesto: hay un aro por opción. Lance el balón al aro de la respuesta correcta (toque o A–D).
 * Encestar seguido hace racha y suma más puntos. */
(function () {
    'use strict';
    const Y0 = 50, W = 480, BX = 240, BY = Y0 + 228;

    function aros(n) {
        const sep = W / (n + 1);
        return Array.from({length: n}, (_, k) => ({k, x: sep * (k + 1), y: Y0 + 70 + (k % 2) * 30}));
    }

    Gamificacion.registrar('baloncesto', {
        nombre: 'Baloncesto',
        instrucciones: 'Toque el aro con la respuesta correcta (o presione A, B, C o D) para lanzar. ¡Encestar seguido hace racha!',
        conReloj: true,
        fondo: '#5f3dc4',
        nuevaPregunta(m) { m.s = {aros: aros(m.opciones.length), tiro: null, racha: m.s ? m.s.racha : 0}; },
        lanzar(m, k) {
            const s = m.s; if (s.tiro || k < 0 || k >= s.aros.length) return;
            s.tiro = {k, t0: m.t, bien: m.opciones[k].correcta};
            m.sonidos.toque();
            setTimeout(() => {
                s.racha = s.tiro.bien ? s.racha + 1 : 0;
                if (s.tiro.bien && s.racha > 1) m.puntaje += 50 * (s.racha - 1);
                m.responder(k);
            }, 650);
        },
        alTocar(m, x, y) {
            const a = m.s.aros.find(a => Math.hypot(a.x - x, a.y - y) < 34);
            if (a) this.lanzar(m, a.k);
        },
        alTecla(m, t, crudo) { this.lanzar(m, 'ABCD'.indexOf(String(crudo || '').toUpperCase())); },
        actualizar() {},
        dibujar(m, ctx) {
            // Coliseo: tribuna y duela
            ctx.fillStyle = '#3b2a7a'; ctx.fillRect(0, Y0, W, 150);
            for (let i = 0; i < 60; i++) { ctx.fillStyle = ['#e64980', '#fab005', '#4dabf7', '#69db7c'][i % 4]; ctx.fillRect((i * 37) % W, Y0 + 8 + (i * 13) % 30, 4, 4); }
            ctx.fillStyle = '#d9a066'; ctx.fillRect(0, Y0 + 150, W, 110);
            ctx.fillStyle = '#c08552'; for (let x = 0; x < W; x += 30) ctx.fillRect(x, Y0 + 150, 2, 110);
            ctx.strokeStyle = '#fff'; ctx.lineWidth = 2; ctx.beginPath(); ctx.arc(BX, Y0 + 260, 70, Math.PI, 0); ctx.stroke();
            const s = m.s; if (!s) return;
            s.aros.forEach(a => {
                ctx.fillStyle = '#f1f3f5'; ctx.fillRect(a.x - 24, a.y - 40, 48, 32);
                ctx.strokeStyle = '#e03131'; ctx.lineWidth = 2; ctx.strokeRect(a.x - 10, a.y - 30, 20, 16);
                ctx.strokeStyle = '#fd7e14'; ctx.lineWidth = 3; ctx.beginPath(); ctx.ellipse(a.x, a.y - 6, 14, 4, 0, 0, Math.PI * 2); ctx.stroke();
                ctx.strokeStyle = 'rgba(255,255,255,.8)'; ctx.lineWidth = 1;
                for (let i = -12; i <= 12; i += 6) { ctx.beginPath(); ctx.moveTo(a.x + i, a.y - 4); ctx.lineTo(a.x + i * .6, a.y + 12); ctx.stroke(); }
                m.etiqueta(a.k, a.x, a.y + 26, 10);
            });
            // Balón en vuelo
            let x = BX, y = BY;
            if (s.tiro) {
                const a = s.aros[s.tiro.k], p = Math.min(1, (m.t - s.tiro.t0) / .6);
                x = BX + (a.x - BX) * p; y = BY + (a.y - 10 - BY) * p - Math.sin(p * Math.PI) * 70;
                if (p >= 1 && !s.tiro.bien) { x += 20; y += 10; }
            }
            ctx.fillStyle = '#e8590c'; ctx.beginPath(); ctx.arc(x, y, 9, 0, Math.PI * 2); ctx.fill();
            ctx.strokeStyle = '#212529'; ctx.lineWidth = 1; ctx.beginPath(); ctx.moveTo(x - 9, y); ctx.lineTo(x + 9, y); ctx.moveTo(x, y - 9); ctx.lineTo(x, y + 9); ctx.stroke();
            if (s.racha > 1) m.texto(`RACHA x${s.racha}`, 12, Y0 + 230, {tam: 9, color: '#ffd43b'});
        },
    });
})();
