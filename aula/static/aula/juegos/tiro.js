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

    /* Cuatro aves distintas, una por opción y del color de esa opción:
     * A pato (pico ancho) · B loro (cola larga) · C tucán (pico grande) · D colibrí (pequeño y de pico fino). */
    function oscuro(hex) { const n = parseInt(hex.slice(1), 16); return `rgb(${(n >> 16) * .6 | 0},${(n >> 8 & 255) * .6 | 0},${(n & 255) * .6 | 0})`; }
    function pintarAve(ctx, k, x, y, dir, alaArriba, e) {
        const col = Gamificacion.COLORES[k], ala = oscuro(col), especie = k % 4;
        ctx.save(); ctx.translate(x, y); ctx.scale(dir * e, e);
        const chico = especie === 3 ? .75 : 1;   // E–H repiten las especies con otro color ctx.scale(chico, chico);
        // cola
        ctx.fillStyle = ala;
        if (especie === 1) { ctx.fillRect(-20, -1, 10, 3); ctx.fillRect(-24, 1, 8, 3); } else ctx.fillRect(-15, -3, 6, 5);
        // cuerpo y pecho
        ctx.fillStyle = col; ctx.beginPath(); ctx.ellipse(0, 0, 11, 7, 0, 0, Math.PI * 2); ctx.fill();
        ctx.fillStyle = 'rgba(255,255,255,.45)'; ctx.beginPath(); ctx.ellipse(3, 3, 6, 3.5, 0, 0, Math.PI * 2); ctx.fill();
        // cabeza
        ctx.fillStyle = col; ctx.beginPath(); ctx.arc(10, -5, 5.5, 0, Math.PI * 2); ctx.fill();
        ctx.fillStyle = '#fff'; ctx.fillRect(11, -8, 3, 3); ctx.fillStyle = '#111'; ctx.fillRect(12, -7, 2, 2);
        // pico
        ctx.fillStyle = '#f59f00';
        if (especie === 0) ctx.fillRect(15, -5, 6, 3);                                   // pato: ancho y plano
        else if (especie === 1) { ctx.fillStyle = '#343a40'; ctx.beginPath(); ctx.moveTo(15, -7); ctx.lineTo(20, -4); ctx.lineTo(15, -2); ctx.fill(); }   // loro: curvo
        else if (especie === 2) { ctx.fillStyle = '#ff922b'; ctx.beginPath(); ctx.moveTo(14, -9); ctx.lineTo(26, -5); ctx.lineTo(14, -1); ctx.fill(); }  // tucán: enorme
        else { ctx.fillStyle = '#343a40'; ctx.fillRect(15, -5, 9, 1.5); }                  // colibrí: largo y fino
        // ala (aletea)
        ctx.fillStyle = ala; ctx.beginPath();
        if (alaArriba) { ctx.moveTo(-6, -3); ctx.lineTo(4, -3); ctx.lineTo(-2, -15); } else { ctx.moveTo(-6, 1); ctx.lineTo(4, 1); ctx.lineTo(-3, 11); }
        ctx.fill();
        ctx.restore();
    }

    Gamificacion.registrar('tiro', {
        nombre: 'Tiro al vuelo',
        instrucciones: 'Toque o haga clic en el ave que lleva la respuesta correcta. También puede presionar A, B, C o D.',
        conReloj: true,
        maxOpciones: 8,
        fondo: '#74c0fc',
        // Barra lateral: el ave con la letra de su opción
        icono(ctx, k, tam) {
            pintarAve(ctx, k, tam * .44, tam * .6, 1, true, tam / 38);
            const r = tam * .17;
            ctx.fillStyle = Gamificacion.COLORES[k]; ctx.beginPath(); ctx.arc(r + 1, r + 1, r, 0, Math.PI * 2); ctx.fill();
            ctx.strokeStyle = '#111'; ctx.lineWidth = 2; ctx.stroke();
            ctx.fillStyle = '#111'; ctx.font = `bold ${Math.round(r * 1.3)}px sans-serif`; ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
            ctx.fillText(Gamificacion.LETRAS[k], r + 1, r + 2);
        },
        nuevaPregunta(m) {
            // Desde el nivel 2 vuelan también aves sin letra que distraen (no cuentan como respuesta).
            const extra = Math.min(4, m.nivel - 1);
            m.s = {aves: m.opciones.map((_, k) => ave(k, m.nivel)), adorno: Array.from({length: extra}, () => Object.assign(ave(0, m.nivel), {k: -1})), disparos: []};
        },
        alTocar(m, x, y) {
            m.s.disparos.push({x, y, t: m.t}); m.sonidos.toque();
            const a = m.s.aves.find(a => !a.cae && Math.hypot(a.x - x, Y0 + a.y - y) < 20);
            if (a) { a.cae = true; a.vy = -60; setTimeout(() => m.responder(a.k), 350); }
        },
        alTecla(m, t, crudo) {
            const k = 'ABCDEFGH'.indexOf(String(crudo || '').toUpperCase());
            const a = k >= 0 && m.s.aves.find(a => a.k === k && !a.cae);
            if (a) this.alTocar(m, a.x, Y0 + a.y);
        },
        actualizar(m, dt) {
            m.s.aves.concat(m.s.adorno).forEach(a => {
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
            // Las aves de adorno son pardas y más lejanas (más pequeñas)
            s.adorno.forEach(a => {
                const y = Y0 + a.y + Math.sin(a.fase) * a.amp;
                ctx.globalAlpha = .55; ctx.save(); ctx.translate(a.x, y); ctx.scale(a.vx > 0 ? .6 : -.6, .6);
                ctx.fillStyle = '#5c3d2e'; ctx.fillRect(-10, -4, 20, 8); ctx.fillRect(8, -8, 7, 7);
                ctx.fillStyle = '#7a5442'; ctx.fillRect(-6, Math.floor(a.fase * 2) % 2 ? 3 : -10, 12, 6);
                ctx.restore(); ctx.globalAlpha = 1;
            });
            s.aves.forEach(a => {
                const x = a.x, y = Y0 + a.y + (a.cae ? 0 : Math.sin(a.fase) * a.amp), alaArriba = Math.floor(a.fase * (a.k === 3 ? 4 : 2)) % 2 === 0;
                pintarAve(ctx, a.k, x, y, a.vx > 0 ? 1 : -1, alaArriba, 1);
                if (!a.cae) m.etiqueta(a.k, x, y - 19, 8);
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
